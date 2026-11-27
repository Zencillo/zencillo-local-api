"""Diagnóstico de solo lectura de la base DEMO. No ejecuta procedimientos."""
import argparse
from contextlib import closing

import pyodbc

from tools.compare_sql_clients import DATABASE, TLS_FAILURE, category, odbc_connect, sanitize
from tools.demo_config import accept_exception, add_tls_options, require


def probe(connect):
    with closing(connect()) as conn:
        conn.timeout = 10
        with closing(conn.cursor()) as cursor:
            cursor.execute("""
                SELECT DB_NAME(), SERVERPROPERTY('ServerName'),
                       SERVERPROPERTY('ProductVersion'), SERVERPROPERTY('Edition'),
                       compatibility_level
                FROM sys.databases WHERE database_id = DB_ID()
            """)
            db, server, version, edition, compat = cursor.fetchone()
            if db != DATABASE:
                raise SystemExit("La base efectiva no coincide con la DEMO esperada.")
            print(f"Base={db} servidor={server} versión={version} edición={edition} compatibilidad={compat}")
            cursor.execute("""
                SELECT OBJECT_ID(N'tipo_vehiculo', N'U'),
                       OBJECT_ID(N'dbo.tipo_vehiculo', N'U')
            """)
            legacy_table, dbo_table = cursor.fetchone()
            if not dbo_table or legacy_table != dbo_table:
                raise SystemExit("El nombre legado no resuelve a la tabla dbo esperada; revisar permisos y esquema.")
            cursor.execute("SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo")
            columns = tuple(column[0] for column in cursor.description)
            rows = list(cursor)
            valid = columns == ("idtipovehiculo", "tipovehiculo") and all(
                type(row[0]) is int and type(row[1]) is str for row in rows
            )
            print(f"SELECT legado: columnas={','.join(columns)} filas={len(rows)} tipos válidos={valid}")
            if not valid:
                raise SystemExit("El resultado difiere del contrato esperado.")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate-name", help="Nombre del certificado confirmado por el administrador")
    add_tls_options(parser)
    args = parser.parse_args()
    if args.confirm_demo_exception and not args.allow_unverified_demo:
        parser.error("--confirm-demo-exception requiere --allow-unverified-demo.")
    user, password = require()
    try:
        probe(lambda: odbc_connect(18, user, password, args.certificate_name))
    except pyodbc.Error as exc:
        print(f"ODBC 18 estricto | {category(exc)} | {sanitize(exc, user, password)}")
        if category(exc) != TLS_FAILURE or not accept_exception(args):
            return 2
        try:
            probe(lambda: odbc_connect(18, user, password, None, verify=False))
        except pyodbc.Error as retry:
            print(f"ODBC 18 DEMO | {category(retry)} | {sanitize(retry, user, password)}")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
