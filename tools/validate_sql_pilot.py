"""Validación manual contra una estación de pruebas autorizada."""
import argparse
import json
import os
from collections import Counter
from contextlib import closing
from getpass import getpass
from http.client import HTTPConnection, HTTPException

import pyodbc


COLUMNS = ("idtipovehiculo", "tipovehiculo")
LEGACY_SELECT = "SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo"


class ValidationError(Exception):
    pass


def checked_rows(cursor):
    if tuple(col[0] for col in cursor.description or ()) != COLUMNS:
        raise ValidationError("Nombres u orden de columnas inesperados.")
    rows = [tuple(row) for row in cursor]
    check_types(rows)
    if cursor.nextset():
        raise ValidationError("Se devolvió un conjunto de resultados adicional.")
    return Counter(rows)


def check_types(rows):
    if any(type(row[0]) is not int or type(row[1]) is not str for row in rows):
        raise ValidationError("Se esperaba int y texto no nulos según el esquema de referencia.")


def validate_sql(args, connection_string):
    with closing(pyodbc.connect(connection_string, timeout=5, autocommit=True)) as conn:
        conn.timeout = 10
        with closing(conn.cursor()) as cursor:
            cursor.execute("""
                SELECT CONVERT(nvarchar(128), SERVERPROPERTY('ServerName')),
                       DB_NAME(),
                       CONVERT(nvarchar(128), SERVERPROPERTY('ProductVersion')),
                       CONVERT(nvarchar(128), SERVERPROPERTY('Edition')),
                       compatibility_level
                FROM sys.databases WHERE database_id = DB_ID()
            """)
            server, db, version, edition, compatibility = cursor.fetchone()
            if (server.casefold(), db.casefold()) != (args.server.casefold(), args.database.casefold()):
                raise ValidationError("El servidor o la base efectiva no coincide con el destino autorizado.")
            print(f"Destino verificado | versión={version} edición={edition} compatibilidad={compatibility}")

            cursor.execute(LEGACY_SELECT)
            legacy = checked_rows(cursor)
            print(f"SELECT legado OK | driver={conn.getinfo(pyodbc.SQL_DRIVER_NAME)} | filas={sum(legacy.values())}")
            return legacy


def validate_http(port, expected, *, token=None):
    token = token if token is not None else getpass("Token JWT local para la API de pruebas: ").strip()
    with closing(HTTPConnection("127.0.0.1", port, timeout=15)) as conn:
        conn.request(
            "POST", "/v1/operations",
            body=json.dumps({"Query": "ListarTiposVehiculo", "parameters": {}}),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        with closing(conn.getresponse()) as response:
            status = response.status
            if status != 200:
                raise ValidationError(f"La API local devolvió HTTP {status}.")
            body = json.load(response)
    if (status != 200 or set(body) != {"success", "message", "data"}
            or body["success"] is not True or body["message"] != "Operación completada"
            or not isinstance(body["data"], dict) or set(body["data"]) != {"items"}
            or not isinstance(body["data"]["items"], list)):
        raise ValidationError("El sobre de éxito HTTP no coincide con el contrato.")
    items = body["data"]["items"]
    if any(not isinstance(item, dict) or set(item) != set(COLUMNS) for item in items):
        raise ValidationError("Los nombres de los campos JSON no coinciden.")
    rows = [tuple(item[name] for name in COLUMNS) for item in items]
    check_types(rows)
    if Counter(rows) != expected:
        raise ValidationError("Los valores HTTP difieren del resultado ODBC.")
    print(f"HTTP 200 | nombres, tipos y valores equivalentes | filas={len(rows)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True, help="SERVERPROPERTY('ServerName') esperado")
    parser.add_argument("--database", required=True, help="DB_NAME() de pruebas esperado")
    parser.add_argument("--http-port", type=int, help="Validar también contra la API local ya configurada")
    args = parser.parse_args()
    if args.http_port is not None and not 1 <= args.http_port <= 65535:
        parser.error("Puerto fuera de rango.")
    connection = os.environ.get("LOCAL_API_VALIDATION_SQL_CONNECTION") or getpass(
        "Cadena ODBC de la base autorizada (entrada oculta): "
    )
    try:
        rows = validate_sql(args, connection)
        if args.http_port is not None:
            validate_http(args.http_port, rows)
    except ValidationError as exc:
        raise SystemExit(str(exc)) from None
    except pyodbc.Error as exc:
        state = str(exc.args[0]) if exc.args else ""
        safe_state = state if len(state) == 5 and state.isascii() and state.isalnum() else "desconocido"
        raise SystemExit(f"Falló ODBC (SQLSTATE={safe_state}).") from None
    except (HTTPException, ValueError, TypeError, OSError):
        raise SystemExit("No se pudo completar la validación. Revisa la configuración y el servicio.") from None


if __name__ == "__main__":
    main()
