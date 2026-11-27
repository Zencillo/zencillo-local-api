"""Test existing upsert and subsidy replacement against synthetic rows in fixed DEMO."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from decimal import Decimal
import json
import os
from pathlib import Path
import secrets
import ssl
from tempfile import TemporaryDirectory
from threading import Barrier, Event

import pyodbc

from app.config import Device, Settings
from app.core.database import request_context
from app.main import create_app
from app.core.security import hash_secret
from tools.demo_config import DATABASE, HOST, PORT, connection_string, require
from tools.run_concurrent_demo import post
from tools.run_flutter_windows_pilot import TestServer, certificates
from tools.run_phase13_demo import original, read_rows


SUBSIDIES = "ReemplazarSubsidiosEcuador"
CLIENT = "GuardarClienteOffline"
READ_CLIENT = "ConsultarClienteOffline"
READ_SUBSIDIES = "ListarSubsidiosEcuador"
READ_FACTOR = "ConsultarSubsidioEcuadorArticulo"


class FailBeforeCommit:
    def __init__(self, connection):
        self.connection = connection

    @property
    def timeout(self):
        return self.connection.timeout

    @timeout.setter
    def timeout(self, value):
        self.connection.timeout = value

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def commit(self):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute("RAISERROR ('LAB: rollback inducido antes de commit',16,1);")
        raise AssertionError("Error SQL de laboratorio no ejecutado")


def run(path):
    user, password = require()
    sql = connection_string(user, password, verify=False)
    marker = "LOCALAPI-" + secrets.token_hex(7)
    year = 2090
    report = {}
    fail_commit = Event()

    def record(label, data):
        report[label] = data
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix(path.suffix + ".tmp")
        with pending.open("w", encoding="utf8") as file:
            json.dump(report, file, default=str, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        pending.replace(path)
        print(label, flush=True)

    def connect(connection_string, *, timeout, autocommit):
        db = pyodbc.connect(connection_string, timeout=timeout, autocommit=autocommit)
        if autocommit:
            return db
        _, operation = request_context.get()
        try:
            if operation == SUBSIDIES:
                with closing(db.cursor()) as guard:
                    # The installed query deletes the entire catalog. Refuse the
                    # test if any row falls outside the exact synthetic scope.
                    rows = guard.execute(
                        "SELECT IdArticulo,Ano,Mes FROM dbo.SubsidioEcuador WITH(TABLOCKX,HOLDLOCK)"
                    ).fetchall()
                    if any(tuple(row) not in synthetic_keys for row in rows):
                        raise RuntimeError("El catálogo contiene datos ajenos a la prueba.")
            if fail_commit.is_set():
                return FailBeforeCommit(db)
            return db
        except Exception:
            db.close()
            raise

    with closing(pyodbc.connect(sql, timeout=6, autocommit=True)) as reader, closing(reader.cursor()) as c:
        c.execute("""SELECT DB_NAME(),local_net_address,local_tcp_port,encrypt_option
          FROM sys.dm_exec_connections WHERE session_id=@@SPID""")
        assert tuple(c.fetchone()) == (DATABASE, HOST, PORT, "TRUE")
        if c.execute("SELECT COUNT_BIG(*) FROM dbo.SubsidioEcuador").fetchval() != 0:
            raise SystemExit("DEMO tiene subsidios preexistentes: no se ejecutó ninguna escritura.")
        assert c.execute("SELECT OBJECT_ID(N'dbo.sp_UpsertClienteOffLine', N'P')").fetchval()
        assert not c.execute("""SELECT 1 FROM sys.triggers WHERE is_disabled=0 AND parent_id IN
          (OBJECT_ID('dbo.ClienteOffLine'),OBJECT_ID('dbo.SubsidioEcuador'))""").fetchone()
        assert not c.execute("SELECT 1 FROM dbo.ClienteOffLine WHERE Identificacion=?", marker).fetchone()
        ids = [row[0] for row in c.execute("SELECT TOP (2) IdArticulo FROM dbo.Articulo ORDER BY IdArticulo")]
        assert len(set(ids)) == 2
        synthetic_keys = {(id_, year, 11) for id_ in ids}

        def subsidies():
            return [tuple(row) for row in c.execute("""SELECT IdArticulo, SubsidioFactor, Ano, Mes
              FROM dbo.SubsidioEcuador WHERE Ano=? AND Mes=11 AND IdArticulo IN (?,?) ORDER BY IdArticulo""",
                                                    year, *ids).fetchall()]

        def client():
            return [tuple(row) for row in c.execute(
                "SELECT NombreCliente,Correo FROM dbo.ClienteOffLine WHERE Identificacion=?", marker).fetchall()]

        def payload(factor, article_ids):
            return {"items": [{"idArticulo": id_, "subsidioFactor": factor, "ano": year, "mes": 11}
                              for id_ in article_ids]}

        record("baseline", {
            "host": HOST, "port": PORT, "database": DATABASE, "sql_encrypted": True,
            "subsidies_original_rows": [], "client_original_rows": [],
            "synthetic_subsidy_keys": sorted(synthetic_keys), "synthetic_client": marker,
        })

        secret = secrets.token_urlsafe(32)
        settings = Settings(jwt_key=secrets.token_urlsafe(48), connection_string=sql, station="demo-catalog",
                            devices={"lab": Device(station="demo-catalog", secret_hash=hash_secret(secret),
                                                    operations={SUBSIDIES, CLIENT, READ_CLIENT, READ_SUBSIDIES, READ_FACTOR})})
        with TemporaryDirectory(prefix="demo-functional-") as temp:
            cert = Path(temp)
            certificates(cert)
            tls = ssl.create_default_context(cafile=str(cert / "ca.pem"))
            lab = TestServer(settings, cert)
            lab.server.config.app = create_app(settings, connect=connect)
            try:
                lab.start()
                code, result = post(lab.port,tls,"/v1/auth/token",{"device_id":"lab","secret":secret})
                assert code == 200
                token = result["data"]["access_token"]

                def send(operation, params):
                    return post(lab.port,tls,"/v1/operations",{"Query":operation,"parameters":params},token)

                def write(operation, params):
                    status, body = send(operation,params)
                    assert status == 200, (operation,status,body.get("error",{}).get("code"))
                    assert body["data"]["items"] == [{"applied": True}]

                status, body = send(SUBSIDIES, {"items": []})
                assert status == 400 and body["error"]["code"] == "INVALID_PARAMETERS"
                assert not subsidies()
                status, body = send(CLIENT, {"identificacion": ""})
                assert status == 400 and body["error"]["code"] == "INVALID_PARAMETERS"
                assert not client()
                record("invalid_payloads_no_changes", True)

                write(SUBSIDIES, payload(0.125, ids))
                first = [(id_, Decimal("0.125"), year, 11) for id_ in ids]
                assert subsidies() == first
                record("subsidy_commit", first)
                catalog = original("article/api/query_article.dart", r"\s*\x27\x27\x27",
                                   method="static String selectTop1000")
                _, expected_subsidies = read_rows(c.execute(catalog))
                status, body = send(READ_SUBSIDIES, {})
                assert status == 200 and sorted(body["data"]["items"], key=lambda item: item["IdArticulo"]) == sorted(
                    expected_subsidies, key=lambda item: item["IdArticulo"]
                )
                record("subsidy_catalog_direct_vs_https", {"rows": len(expected_subsidies), "columns": 4})
                factor = original("article/api/query_article.dart", r"\s*\x27\x27\x27",
                                  method="static String getSubsidioFactor(")
                article_code = f"{ids[0]:08d}"
                query = factor.replace("'$safeIdArticulo'", "?").replace("$ano", "?").replace("$mes", "?")
                _, expected = read_rows(c.execute(query, article_code, article_code, article_code, year, 11))
                status, body = send(READ_FACTOR, {"idArticulo": article_code, "ano": year, "mes": 11})
                assert status == 200 and body["data"]["items"] == expected and len(expected) == 1
                record("subsidy_factor_direct_vs_https", {"rows": 1, "columns": 4})


                fail_commit.set()
                try:
                    status, body = send(SUBSIDIES,payload(0.250, ids[:1]))
                    assert status == 503 and body["error"]["code"] == "WRITE_OUTCOME_UNKNOWN"
                finally:
                    fail_commit.clear()
                assert subsidies() == first
                record("subsidy_rollback", first)
                gate = Barrier(2, timeout=5)
                def parallel(operation, params):
                    gate.wait()
                    write(operation, params)
                with ThreadPoolExecutor(2) as pool:
                    pending = [pool.submit(parallel,SUBSIDIES,payload(0.250, ids[:1])) for _ in range(2)]
                    for task in pending:
                        task.result(timeout=20)
                assert subsidies() == [(ids[0], Decimal("0.250"), year, 11)]
                record("subsidy_concurrent_same_payload", subsidies())

                identity = {"identificacion":marker,"nombreCliente":"LAB SYNTHETIC A","correo":"local@example.invalid"}
                gate = Barrier(2, timeout=5)
                with ThreadPoolExecutor(2) as pool:
                    pending = [pool.submit(parallel,CLIENT,identity) for _ in range(2)]
                    for task in pending:
                        task.result(timeout=20)
                assert client() == [("LAB SYNTHETIC A","local@example.invalid")]
                record("client_concurrent_insert", {"rows":1})
                write(CLIENT,{**identity,"nombreCliente":"LAB SYNTHETIC B","correo":""})
                assert client() == [("LAB SYNTHETIC B","local@example.invalid")]
                record("client_update_preserves_inherited_value",{"rows":1})
                with closing(pyodbc.connect(sql, timeout=6, autocommit=False)) as legacy, closing(legacy.cursor()) as cur:
                    cur.execute("""EXEC dbo.sp_UpsertClienteOffLine
                        @Identificacion=?, @NombreCliente=?, @Correo=NULL;""",
                                marker, "LAB SYNTHETIC B")
                    direct = cur.execute(
                        "SELECT NombreCliente,Correo FROM dbo.ClienteOffLine WHERE Identificacion=?",
                        marker,
                    ).fetchall()
                    legacy.rollback()
                assert list(map(tuple, direct)) == client()
                record("client_legacy_upsert_equivalent", {"rows": 1})

                query = original("client/models/cliente_offline_bd.dart", r"\s*\x27\x27\x27",
                                 method="static String readQuerySingle(")
                _, expected = read_rows(c.execute(query.replace("'$identificacion'", "?"),marker))
                status, body = send(READ_CLIENT,{"key":marker})
                assert status == 200 and body["data"]["items"] == expected and len(expected) == 1
                record("client_lookup_direct_vs_https", {"rows":1, "columns":len(expected[0])})
                fail_commit.set()
                try:
                    status, body = send(CLIENT,{**identity,"nombreCliente":"LAB ROLLBACK"})
                    assert status == 503 and body["error"]["code"] == "WRITE_OUTCOME_UNKNOWN"
                finally:
                    fail_commit.clear()
                assert client() == [("LAB SYNTHETIC B","local@example.invalid")]
                record("client_rollback", {"rows":1,"persisted":"LAB SYNTHETIC B"})
            finally:
                lab.close()
                with closing(pyodbc.connect(sql,timeout=6,autocommit=False)) as cleanup, closing(cleanup.cursor()) as cur:
                    cur.execute("DELETE FROM dbo.ClienteOffLine WHERE Identificacion=? AND NombreCliente LIKE 'LAB %'",marker)
                    cur.execute("DELETE FROM dbo.SubsidioEcuador WHERE Ano=? AND Mes=11 AND IdArticulo IN (?,?)",year,*ids)
                    cleanup.commit()
                assert not client() and not subsidies()
                assert c.execute("SELECT COUNT_BIG(*) FROM dbo.SubsidioEcuador").fetchval() == 0
                record("cleanup_verified", {"synthetic_client_rows": 0, "subsidy_catalog_rows": 0})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exercise-test-data", action="store_true", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args=parser.parse_args()
    try:
        run(args.report)
    except pyodbc.Error as exc:
        raise SystemExit(str(exc.args[0])) from None
