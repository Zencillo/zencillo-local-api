"""Verify two specifically authorized mutations without retaining fixture data in DEMO."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import ssl
from tempfile import TemporaryDirectory
from threading import Barrier

import pyodbc

from app.config import Device, Settings
from app.core.database import request_context
from app.core.security import hash_secret
from app.main import create_app
from app.modules.license.operations import ECUADOR_KEYS
from tools.demo_config import DATABASE, HOST, PORT, connection_string, require
from tools.run_concurrent_demo import post
from tools.run_flutter_windows_pilot import TestServer, certificates


CONFIG = "GuardarConfiguracionEcuador"
PLATE = "GuardarPlacaOffline"
CONFIG_FIELDS = ("placaEnvases", "prefijoCuantias", "prefijoMaquinarias")
CONFIG_SQL = """
SELECT Llave, Valor FROM dbo.ConfiguracionCapturador
WHERE Llave IN (?,?,?) ORDER BY Llave
"""
PLATE_SQL = """
SELECT Identificacion, Placa, Identificador, Correo FROM dbo.ClientePlacaOffLine
WHERE Placa=? ORDER BY Identificacion
"""


def read_config(cursor):
    return dict(map(tuple, cursor.execute(CONFIG_SQL, *ECUADOR_KEYS).fetchall()))


def assert_safe(cursor):
    assert tuple(cursor.execute("""SELECT DB_NAME(),local_net_address,local_tcp_port,encrypt_option
        FROM sys.dm_exec_connections WHERE session_id=@@SPID""").fetchone()) == (DATABASE, HOST, PORT, "TRUE")
    assert cursor.execute("SELECT OBJECT_ID(N'dbo.sp_UpsertClientePlacaOffLine',N'P')").fetchval()
    for name in ("dbo.ConfiguracionCapturador", "dbo.ClientePlacaOffLine"):
        row = cursor.execute("""SELECT temporal_type, is_tracked_by_cdc,
            (SELECT COUNT(*) FROM sys.triggers WHERE parent_id=t.object_id AND is_disabled=0),
            (SELECT COUNT(*) FROM sys.change_tracking_tables WHERE object_id=t.object_id),
            (SELECT COUNT(*) FROM sys.foreign_keys WHERE is_disabled=0 AND
                (parent_object_id=t.object_id OR referenced_object_id=t.object_id))
            FROM sys.tables t WHERE t.object_id=OBJECT_ID(?)""", name).fetchone()
        assert tuple(row) == (0, False, 0, 0, 0), "Hay efectos secundarios sin evaluar"
    unique = cursor.execute("""SELECT c.name
        FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
        JOIN sys.columns c ON c.object_id=i.object_id AND c.column_id=ic.column_id
        WHERE i.object_id=OBJECT_ID('dbo.ClientePlacaOffLine') AND i.is_primary_key=1
        AND i.is_disabled=0 AND ic.key_ordinal>0 ORDER BY ic.key_ordinal""").fetchall()
    assert [row[0].lower() for row in unique] == ["identificacion", "placa"]


class GuardedCommit:
    def __init__(self, connection, inspect, reject=False):
        self.connection, self.inspect, self.reject = connection, inspect, reject

    def __getattr__(self, field):
        return getattr(self.connection, field)

    @property
    def timeout(self):
        return self.connection.timeout

    @timeout.setter
    def timeout(self, value):
        self.connection.timeout = value

    def commit(self):
        with closing(self.connection.cursor()) as cursor:
            self.inspect(cursor)
            if self.reject:
                cursor.execute("RAISERROR ('LAB rollback antes de commit',16,1);")
                raise AssertionError("El fallo SQL de laboratorio no se ejecutó.")
        return self.connection.commit()


def run(report_path):
    user, password = require()
    sql = connection_string(user, password, verify=False)
    suffix = secrets.token_hex(5).upper()
    plate = "ZS" + suffix
    identity = "LAB-" + suffix
    second_identity = "LAB2-" + suffix
    tag = "TAG-" + suffix
    email = "local@example.invalid"
    base_plate = dict(placa=plate, identificadorPlaca=tag, identificacion=identity, correoPlaca=email)
    staged_config = dict(zip(ECUADOR_KEYS, ("ZS"+suffix, "LABA", "LABB"), strict=True))
    config_rollback_seen = False
    plate_rollback_seen = False
    fail = None
    report = {"server": HOST, "database": DATABASE, "configuration": {}, "plate": {}}

    with closing(pyodbc.connect(sql, timeout=6, autocommit=True)) as reader, closing(reader.cursor()) as view:
        assert_safe(view)
        original = read_config(view)
        assert set(original) == set(ECUADOR_KEYS) and all(isinstance(value, str) for value in original.values())
        assert not view.execute(PLATE_SQL, plate).fetchall()
        assert not view.execute("SELECT 1 FROM dbo.ClientePlacaOffLine WHERE Identificacion=?", identity).fetchone()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = report_path.with_name("ecuador-restore-" + suffix + ".json")
        with snapshot.open("x", encoding="utf8") as file:
            json.dump({"settings": original, "synthetic_plate": plate, "synthetic_identifications": [identity, second_identity]}, file)
            file.flush()
            os.fsync(file.fileno())

        def connect(connection_string, *, timeout, autocommit):
            connection = pyodbc.connect(connection_string, timeout=timeout, autocommit=autocommit)
            _, operation = request_context.get()
            if autocommit:
                return connection
            try:
                if operation == CONFIG:
                    with closing(connection.cursor()) as cur:
                        actual = dict(map(tuple, cur.execute(CONFIG_SQL.replace(
                            "dbo.ConfiguracionCapturador", "dbo.ConfiguracionCapturador WITH(UPDLOCK,HOLDLOCK)"
                        ), *ECUADOR_KEYS).fetchall()))
                        assert actual == original, "La configuración cambió desde el respaldo"
                    def inspect(cur):
                        nonlocal config_rollback_seen
                        if fail == CONFIG:
                            assert read_config(cur) == staged_config
                            config_rollback_seen = True
                        else:
                            assert read_config(cur) == original
                    return GuardedCommit(connection, inspect, fail == CONFIG)
                if operation == PLATE:
                    with closing(connection.cursor()) as cur:
                        rows = cur.execute(PLATE_SQL.replace(
                            "dbo.ClientePlacaOffLine", "dbo.ClientePlacaOffLine WITH(UPDLOCK,HOLDLOCK)"
                        ), plate).fetchall()
                        assert all(row[0] in {identity, second_identity} for row in rows), "La placa de prueba tiene datos ajenos"
                    if fail == PLATE:
                        def inspect(cur):
                            nonlocal plate_rollback_seen
                            assert cur.execute(PLATE_SQL, plate).fetchone()[2] == "ROLLBACK"
                            plate_rollback_seen = True
                        return GuardedCommit(connection, inspect, True)
                return connection
            except Exception:
                connection.close()
                raise

        secret = secrets.token_urlsafe(32)
        settings = Settings(jwt_key=secrets.token_urlsafe(48), connection_string=sql, station="demo-write",
                            devices={"lab": Device(station="demo-write", secret_hash=hash_secret(secret),
                                                    operations={CONFIG, PLATE})})
        with TemporaryDirectory(prefix="demo-config-plate-") as temp:
            folder = Path(temp)
            certificates(folder)
            tls = ssl.create_default_context(cafile=str(folder / "ca.pem"))
            lab = TestServer(settings, folder)
            lab.server.config.app = create_app(settings, connect=connect)
            try:
                lab.start()
                status, login = post(lab.port, tls, "/v1/auth/token", {"device_id":"lab", "secret":secret})
                assert status == 200
                token = login["data"]["access_token"]

                def send(operation, params):
                    return post(lab.port, tls, "/v1/operations", {"Query":operation, "parameters":params}, token)

                def confirm(operation, params):
                    status, body = send(operation, params)
                    assert status == 200, (operation, status, body.get("error", {}).get("code"))
                    assert body["data"]["items"] == [{"applied": True}]

                assert send(CONFIG, {"llave":"CUALQUIERA", "valor":"LAB"})[0] == 400
                unchanged = dict(zip(CONFIG_FIELDS, (original[key] for key in ECUADOR_KEYS), strict=True))
                confirm(CONFIG, unchanged)
                assert read_config(view) == original
                report["configuration"]["unchanged_commit"] = True
                fail = CONFIG
                status, body = send(CONFIG, dict(zip(CONFIG_FIELDS, staged_config.values(), strict=True)))
                fail = None
                assert status == 503 and body["error"]["code"] == "WRITE_OUTCOME_UNKNOWN"
                assert config_rollback_seen and read_config(view) == original
                report["configuration"]["rollback_and_restore"] = True
                with closing(pyodbc.connect(sql, timeout=6, autocommit=False)) as before, closing(before.cursor()) as c:
                    assert read_config(c) == original
                    for key, value in staged_config.items():
                        c.execute("""IF EXISTS (SELECT 1 FROM dbo.ConfiguracionCapturador WHERE Llave=?)
                            UPDATE dbo.ConfiguracionCapturador SET Valor=? WHERE Llave=?;
                            ELSE INSERT dbo.ConfiguracionCapturador (Llave,Valor) VALUES (?,?);""",
                                  key, value, key, key, value)
                    assert read_config(c) == staged_config
                    before.rollback()
                assert read_config(view) == original
                report["configuration"]["legacy_compare"] = True

                gate = Barrier(2, timeout=5)
                def parallel():
                    gate.wait()
                    confirm(PLATE, base_plate)
                with ThreadPoolExecutor(2) as pool:
                    calls = [pool.submit(parallel) for _ in range(2)]
                    for call in calls:
                        call.result(timeout=20)
                assert [tuple(row) for row in view.execute(PLATE_SQL, plate)] == [(identity, plate, tag, email)]
                report["plate"]["concurrent_insert_single_row"] = True
                with closing(pyodbc.connect(sql, timeout=6, autocommit=False)) as legacy, closing(legacy.cursor()) as cur:
                    cur.execute("EXEC dbo.sp_UpsertClientePlacaOffLine @Placa=?, @IdentificadorPlaca=?, @Identificacion=?, @CorreoPlaca=?",
                                plate, "ACTUALIZADO", identity, "")
                    expected = [tuple(row) for row in cur.execute(PLATE_SQL, plate)]
                    legacy.rollback()
                confirm(PLATE, {**base_plate, "identificadorPlaca": "ACTUALIZADO", "correoPlaca": ""})
                assert expected == [(identity, plate, "ACTUALIZADO", email)]
                assert [tuple(row) for row in view.execute(PLATE_SQL, plate)] == expected
                report["plate"]["legacy_update_equivalent"] = True
                fail = PLATE
                status, body = send(PLATE, {**base_plate, "identificadorPlaca": "ROLLBACK"})
                fail = None
                assert status == 503 and body["error"]["code"] == "WRITE_OUTCOME_UNKNOWN"
                assert plate_rollback_seen and [tuple(row) for row in view.execute(PLATE_SQL, plate)] == expected
                report["plate"]["rollback"] = True
                with closing(pyodbc.connect(sql, timeout=6, autocommit=False)) as duplicate, closing(duplicate.cursor()) as cur:
                    cur.execute("""INSERT INTO dbo.ClientePlacaOffLine (Identificacion, Placa, Identificador, Correo)
                        VALUES (?, ?, ?, ?)""", second_identity, plate, tag, email)
                    duplicate.commit()
                before_ambiguity = [tuple(row) for row in view.execute(PLATE_SQL, plate)]
                assert len(before_ambiguity) == 2
                status, body = send(PLATE, {**base_plate, "identificadorPlaca": "AMBIGUA"})
                assert status == 503 and body["error"]["code"] == "SQL_WRITE_FAILED"
                assert [tuple(row) for row in view.execute(PLATE_SQL, plate)] == before_ambiguity
                report["plate"]["ambiguous_plate_kept_intact"] = True
            finally:
                try:
                    lab.close()
                finally:
                    with closing(pyodbc.connect(sql, timeout=6, autocommit=False)) as clean, closing(clean.cursor()) as cur:
                        cur.execute("DELETE FROM dbo.ClientePlacaOffLine WHERE Placa=? AND Identificacion IN (?,?)",
                                    plate, identity, second_identity)
                        clean.commit()
                    assert not view.execute(PLATE_SQL, plate).fetchall()
                    assert read_config(view) == original
                    report["cleanup_verified"] = True
                    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8")
        print(json.dumps(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not __debug__:
        raise SystemExit("El probador requiere las comprobaciones activas.")
    try:
        run(args.report)
    except pyodbc.Error as error:
        raise SystemExit(f"ODBC {error.args[0]}") from None


if __name__ == "__main__":
    main()
