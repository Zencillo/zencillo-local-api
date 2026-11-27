"""Compare Phase 6 SQL reads to a temporary FastAPI instance in DEMO."""
import argparse
from collections import Counter
from contextlib import closing
from datetime import datetime
from decimal import Decimal
from http.client import HTTPConnection
import json
from pathlib import Path

import pyodbc

from tools.compare_sql_clients import DATABASE, TLS_FAILURE, category, sanitize
from tools.demo_config import accept_exception, add_tls_options, connection_string, require
from tools.run_demo_pilot import http_pilot
from tools.validate_sql_pilot import ValidationError

REFERENCES = {
    "ListarTiposVehiculo": (
        "SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo",
        ("idtipovehiculo", "tipovehiculo"),
    ),
    "ListarTiposGasto": (
        "SELECT * FROM gasto_tipo WHERE estado = 1",
        ("idcompania", "idgastotipo", "gastotipo", "contabilidadcuenta", "estado",
         "fechacreacion", "fechamodificacion", "fechaultimomovimiento"),
    ),
    "ListarConfiguracionRedondeo": (
        "SELECT [Documento], [Posicion], [Descripcion], [AplicaRedondeo], [FactorRedondeo] "
        "FROM [ConfiguracionRedondeo]",
        ("Documento", "Posicion", "Descripcion", "AplicaRedondeo", "FactorRedondeo"),
    ),
    "ListarCombustibles": (
        "SELECT [IdCombustible], [IdArticulo], [Color], [Nombre], [CodigoArticulo] FROM [Combustible]",
        ("IdCombustible", "IdArticulo", "Color", "Nombre", "CodigoArticulo"),
    ),
}


def json_value(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def multiset(rows):
    return Counter(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)


def sql_reference(connection):
    with closing(pyodbc.connect(connection, timeout=6, autocommit=True)) as conn:
        conn.timeout = 8
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT DB_NAME()")
            if cursor.fetchone()[0] != DATABASE:
                raise ValidationError("La base efectiva no coincide con DEMO.")
            output = {}
            for name, (sql, fields) in REFERENCES.items():
                cursor.execute(sql)
                columns = [col[0].casefold() for col in cursor.description]
                if any(columns.count(field.casefold()) != 1 for field in fields):
                    raise ValidationError(f"Columnas SQL faltantes o duplicadas en {name}.")
                indexes = {field: columns.index(field.casefold()) for field in fields}
                output[name] = multiset(
                    {field: json_value(row[index]) for field, index in indexes.items()}
                    for row in cursor.fetchall()
                )
            return output


def validate_catalogs(port, token, reference, emit):
    for name, expected in reference.items():
        with closing(HTTPConnection("127.0.0.1", port, timeout=15)) as conn:
            conn.request("POST", "/v1/operations",
                         json.dumps({"Query": name, "parameters": {}}),
                         {"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            with closing(conn.getresponse()) as response:
                status = response.status
                if status != 200:
                    raise ValidationError(f"{name}: HTTP {status}.")
                body = json.load(response)
        items = body.get("data", {}).get("items")
        if (set(body) != {"success", "message", "data"} or body["success"] is not True
                or body["message"] != "Operación completada" or set(body["data"]) != {"items"}
                or not isinstance(items, list)
                or any(not isinstance(item, dict) or set(item) != set(REFERENCES[name][1]) for item in items)
                or multiset(items) != expected):
            raise ValidationError(f"{name}: contrato o filas diferentes entre ODBC y HTTP.")
        emit(f"{name} | HTTP 200 | filas={len(items)} | columnas y valores equivalentes")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_tls_options(parser)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.confirm_demo_exception and not args.allow_unverified_demo:
        parser.error("--confirm-demo-exception requiere --allow-unverified-demo.")
    user, password = require()
    with args.report.open("x", encoding="utf8") as report:
        events = []

        def emit(message):
            events.append(message)
            print(message, flush=True)
            report.seek(0)
            json.dump({"events": events}, report, ensure_ascii=False, indent=2)
            report.truncate()
            report.flush()

        try:
            connection = connection_string(user, password, verify=True)
            try:
                reference = sql_reference(connection)
                emit("DEMO | ODBC 18 | TLS validado")
            except pyodbc.Error as exc:
                emit(f"ODBC 18 estricto | {category(exc)} | {sanitize(exc, user, password)}")
                if category(exc) != TLS_FAILURE or not accept_exception(args):
                    return 2
                connection = connection_string(user, password, verify=False)
                emit("DEMO 10.1.10.15:1433 | TLS cifrado sin validar certificado | solo en memoria")
                reference = sql_reference(connection)
            for name, rows in reference.items():
                emit(f"{name} | SQL de solo lectura OK | filas={sum(rows.values())}")
            http_pilot(
                connection, reference, emit, operations=set(REFERENCES),
                check_http=validate_catalogs,
            )
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
