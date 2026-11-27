"""Run the vehicle types pilot on the fixed DEMO endpoint, without writes."""
import argparse
from contextlib import closing
from http.client import HTTPConnection
import json
from pathlib import Path
import secrets
import socket
import threading
import time

import pyodbc
import uvicorn

from app.config import Device, Settings
from app.main import create_app
from app.core.security import hash_secret
from tools.compare_sql_clients import DATABASE, TLS_FAILURE, category, sanitize
from tools.demo_config import accept_exception, add_tls_options, connection_string, require
from tools.validate_sql_pilot import (
    COLUMNS, LEGACY_SELECT, ValidationError, checked_rows, validate_http,
)


def inspect_demo(connection, emit):
    with closing(pyodbc.connect(connection, timeout=6, autocommit=True)) as conn:
        conn.timeout = 8
        with closing(conn.cursor()) as cursor:
            cursor.execute("""
                SELECT DB_NAME(), CONVERT(nvarchar(128), SERVERPROPERTY('ServerName')),
                       CONVERT(nvarchar(128), SERVERPROPERTY('ProductVersion'))
            """)
            db, _, version = cursor.fetchone()
            if db != DATABASE:
                raise ValidationError("La base efectiva no coincide con DEMO.")
            emit(f"Destino DEMO verificado | motor={version}")
            cursor.execute("""
                SELECT OBJECT_ID(N'tipo_vehiculo', N'U'),
                       OBJECT_ID(N'dbo.tipo_vehiculo', N'U')
            """)
            source, table = cursor.fetchone()
            if not table or source != table:
                raise ValidationError("El SELECT original no resuelve a dbo.tipo_vehiculo.")
            cursor.execute(LEGACY_SELECT)
            rows = checked_rows(cursor)
            emit(f"SELECT original OK | columnas={','.join(COLUMNS)} | tipos=int,str | filas={sum(rows.values())}")
            return rows


def http_pilot(connection, expected, emit, *, operations=None, check_http=None):
    secret = secrets.token_urlsafe(32)
    settings = Settings(
        jwt_key=secrets.token_urlsafe(48), connection_string=connection,
        devices={"demo-pilot": Device(station="demo", secret_hash=hash_secret(secret),
                                      operations=operations or {"ListarTiposVehiculo"})},
        station="demo",
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(
            create_app(settings), access_log=False, log_level="critical",
        ))
        worker = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 8
            while not server.started and worker.is_alive() and time.monotonic() < deadline:
                time.sleep(0.05)
            if not server.started:
                raise ValidationError("FastAPI temporal no inició.")
            with closing(HTTPConnection("127.0.0.1", port, timeout=12)) as conn:
                conn.request("POST", "/v1/auth/token",
                             json.dumps({"device_id": "demo-pilot", "secret": secret}),
                             {"Content-Type": "application/json"})
                with closing(conn.getresponse()) as response:
                    if response.status != 200:
                        raise ValidationError(f"Autenticación HTTP falló con {response.status}.")
                    token = json.load(response)["data"]["access_token"]
            emit("POST /v1/auth/token HTTP 200 | JWT temporal emitido")
            if check_http is not None:
                check_http(port, token, expected, emit)
                return
            validate_http(port, expected, token=token)
            count = sum(expected.values())
            emit(f"POST /v1/operations HTTP 200 | JSON equivalente | filas={count}")
            if not count:
                emit("Catálogo vacío: aún falta evidencia HTTP con registros reales.")
        finally:
            server.should_exit = True
            worker.join(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_tls_options(parser)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.confirm_demo_exception and not args.allow_unverified_demo:
        parser.error("--confirm-demo-exception requiere --allow-unverified-demo.")
    user, password = require()

    with args.report.open("x", encoding="utf-8") as report:
        events = []

        def emit(message):
            print(message, flush=True)
            if args.report.suffix.lower() == ".json":
                events.append(message)
                report.seek(0)
                json.dump({"events": events}, report, ensure_ascii=False, indent=2)
                report.truncate()
                report.flush()
            else:
                print(message, file=report, flush=True)

        try:
            connection = connection_string(user, password, verify=True)
            try:
                expected = inspect_demo(connection, emit)
                emit("ODBC 18 | cifrado con validación del certificado")
            except pyodbc.Error as exc:
                emit(f"ODBC 18 estricto | {category(exc)} | {sanitize(exc, user, password)}")
                if not args.allow_unverified_demo or category(exc) != TLS_FAILURE:
                    return 2
                if not accept_exception(args):
                    emit("Excepción no autorizada.")
                    return 2
                connection = connection_string(user, password, verify=False)
                emit("Excepción DEMO habilitada solo en memoria.")
                expected = inspect_demo(connection, emit)
            http_pilot(connection, expected, emit)
            if sum(expected.values()) != 19:
                emit("Conteo distinto de la referencia esperada de 19 filas; revisar DEMO.")
                return 4
            return 0
        except pyodbc.Error as exc:
            emit(f"ODBC | {category(exc)} | {sanitize(exc, user, password)}")
        except ValidationError as exc:
            emit(f"Validación detenida: {exc}")
        except Exception as exc:
            emit(f"Error local: {type(exc).__name__}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
