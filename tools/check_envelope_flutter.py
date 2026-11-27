"""Real HTTPS Dart/Python interoperability, optionally with the authorized read-only DEMO."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

import pyodbc
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import SecretStr

from app.config import Settings, Device
from app.core.database import odbc_failure
from app.core.security import hash_secret
from app.install_station_sql import StationSqlProfile
from app.main import create_app
from tools.demo_config import DATABASE, connection_string, require
from tools.run_flutter_windows_pilot import TestServer, certificates
from tools.run_phase13_demo import SOURCE, read_rows


def demo_read(allow_exception):
    user, password = require()
    def checked(verify):
        conn = connection_string(user, password, verify=verify)
        with closing(pyodbc.connect(conn, timeout=6, autocommit=True)) as sql:
            cursor = sql.cursor()
            assert cursor.execute("SELECT DB_NAME()").fetchval() == DATABASE
            return conn, read_rows(cursor.execute("SELECT idtipovehiculo,tipovehiculo FROM dbo.tipo_vehiculo"))[1]
    try:
        return checked(True)
    except pyodbc.Error as exc:
        if not allow_exception or odbc_failure(exc)[1] != "certificate_trust":
            raise SystemExit("Conexión DEMO no disponible.") from None
        print("Excepción TLS limitada al salto ODBC DEMO.", flush=True)
        return checked(False)


def run(use_demo=False, allow_exception=False, published_key=None, private_keys=None):
    profile = None
    connector = None
    if use_demo:
        connection, rows = demo_read(allow_exception)
    else:
        profile = StationSqlProfile(station="1/2/3", server="fixture.local", port=1433, database="Fixture",
                                    user="service", password=SecretStr("synthetic"))
        connector = MagicMock()
        cursor = connector.return_value.cursor.return_value
        cursor.description = [("idtipovehiculo",), ("tipovehiculo",)]
        cursor.fetchall.return_value = [(1,"AUTO"), (2,"MOTO")]
        connection = "fixture"
        rows = [{"idtipovehiculo":1,"tipovehiculo":"AUTO"}, {"idtipovehiculo":2,"tipovehiculo":"MOTO"}]
    secret = secrets.token_urlsafe(32)
    with TemporaryDirectory(prefix="local-encrypted-flutter-") as directory:
        folder = Path(directory)
        keys = private_keys or folder / "keys"
        if published_key is None:
            keys.mkdir()
            private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            (keys / "pilot.pem").write_bytes(private.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            pem = private.public_key().public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
            client_key = {"ZENC_ENVELOPE_TEST_PEM":pem}
        else:
            client_key = {"ZENC_ENVELOPE_PUBLISHED_KEY":str(published_key.resolve())}
        certificates(folder)
        settings = Settings(jwt_key=secrets.token_urlsafe(48), connection_string=connection, station="1/2/3",
                            sql_login_required=not use_demo, sql_login_profile=profile, envelope_keys_path=keys,
                            devices={"encrypted-pilot":Device(station="1/2/3",secret_hash=hash_secret(secret),
                                                              operations={"ListarTiposVehiculo"})})
        server = TestServer(settings, folder)
        server.server.config.app = create_app(settings, connect=connector)
        try:
            server.start()
            subprocess.run([shutil.which("flutter.bat"),"test","--no-pub","test/core/local_api_envelope_live_test.dart"],
                cwd=SOURCE.parents[3], timeout=120, check=True,
                env={**os.environ, "ZENC_ENVELOPE_ORIGIN":f"https://127.0.0.1:{server.port}",
                     "ZENC_ENVELOPE_CA":str(folder/"ca.pem"), "ZENC_ENVELOPE_ROWS":json.dumps(rows),
                     "ZENC_ENVELOPE_DEVICE":secret, "ZENC_ENVELOPE_SQL_FIXTURE":str(not use_demo).lower(),
                     **client_key})
            if connector is not None:
                assert connector.call_count == 2
            print(f"Interoperabilidad verificada: {len(rows)} filas.", flush=True)
        finally:
            server.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    parser.add_argument("--published-key", type=Path)
    parser.add_argument("--private-keys", type=Path)
    args = parser.parse_args()
    if (args.published_key is None) != (args.private_keys is None):
        parser.error("Indique ambas rutas de prueba o ninguna.")
    run(args.demo, args.allow_demo_sql_exception, args.published_key, args.private_keys)
