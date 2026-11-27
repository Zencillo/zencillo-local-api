"""Compare SQL Server clients against the DEMO endpoint with validated TLS."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import re
import secrets
import socket
from tempfile import TemporaryDirectory

import pyodbc

from tools.demo_config import HOST, PORT, DATABASE, accept_exception, add_tls_options, quote, require

TLS_FAILURE = "TLS / negociación"
SQL = "SELECT DB_NAME(), @@VERSION"


def sanitize(exc, user, password):
    message = " | ".join(
        value.decode("utf-8", errors="backslashreplace") if isinstance(value, bytes) else str(value)
        for value in exc.args
    )
    message = re.sub(r"\b(?:PWD|PASSWORD|UID|USER ID)\s*=\s*(?:\{(?:[^}]|}})*\}|[^;\r\n]*)",
                     "[CREDENCIAL REDACTADA]", message, flags=re.IGNORECASE)
    for value in sorted({password, password.replace("}", "}}")}, key=len, reverse=True):
        if value:
            message = re.sub(re.escape(value), "[REDACTADO]", message, flags=re.IGNORECASE)
    if user and user != password:
        message = re.sub(r"(?<!\w)" + re.escape(user) + r"(?!\w)",
                         "[REDACTADO]", message, flags=re.IGNORECASE)
    return message.replace("\x1b", r"\x1b")


def odbc_connect(major, user, password, certificate_name, *, verify=True):
    host = HOST
    if major == 17 and certificate_name:
        addresses = {
            row[4][0] for row in socket.getaddrinfo(certificate_name, PORT, type=socket.SOCK_STREAM)
        }
        if addresses != {HOST}:
            raise ValueError("El nombre DNS indicado para ODBC 17 no resuelve exclusivamente al servidor DEMO.")
        host = certificate_name
    params = {
        "DRIVER": f"ODBC Driver {major} for SQL Server",
        "SERVER": f"tcp:{host},{PORT}", "DATABASE": DATABASE,
        "UID": user, "PWD": password, "Encrypt": "yes", "TrustServerCertificate": "no" if verify else "yes",
    }
    if major == 18 and certificate_name:
        params["HostNameInCertificate"] = certificate_name
    conn = pyodbc.connect(";".join(f"{k}={quote(v)}" for k, v in params.items()),
                          timeout=6, autocommit=True)
    conn.timeout = 8
    return conn


def query(connect):
    with closing(connect()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(SQL)
        db, version = cursor.fetchone()
        if str(db).casefold() != DATABASE.casefold():
            raise ValueError("La base efectiva no coincide con DEMO.")
        return " ".join(str(version).split())


def freetds_query(args, user, password, *, verify=True):
    # Reject inherited overrides and tracing, including an empty TDSDUMP value.
    if any(key.upper().startswith("TDS") or key.upper() in {"FREETDS", "FREETDSCONF"}
           for key in os.environ):
        raise ValueError("Quita las variables TDS* / FREETDS* de esta consola antes de la prueba.")
    tls_config = "ca file =\n"
    if verify:
        if args.ca_file is None:
            raise ValueError("FreeTDS requiere --ca-file con la CA de confianza en formato PEM.")
        ca_file = args.ca_file.resolve(strict=True)
        if (not ca_file.is_file() or any(ch in str(ca_file) for ch in "\r\n#;")
                or b"-----BEGIN CERTIFICATE-----" not in ca_file.read_bytes()):
            raise ValueError("La ruta PEM de la CA no es válida.")
        tls_config = (
            f"ca file = {ca_file.as_posix()}\n"
            f"certificate hostname = {args.certificate_name or HOST}\n"
            "check certificate hostname = yes\n"
        )
    alias = "zencillo-demo-" + secrets.token_hex(8)
    with TemporaryDirectory() as tmp:
        config = Path(tmp) / "freetds.conf"
        config.write_text(
            f"[{alias}]\nhost = {HOST}\nport = {PORT}\n"
            "encryption = require\n" + tls_config,
            encoding="utf-8",
        )
        os.environ["FREETDSCONF"] = str(config)
        try:
            import pymssql
            return query(lambda: pymssql.connect(
                server=alias, port=str(PORT), database=DATABASE, user=user, password=password,
                login_timeout=6, timeout=8, encryption="require",
                conn_properties=[], autocommit=True,
            ))
        finally:
            os.environ.pop("FREETDSCONF", None)


def category(exc):
    detail = " ".join(str(arg) for arg in exc.args).casefold()
    if re.search(r"\b(18456|18452|28000)\b|login failed|login incorrect", detail):
        return "Autenticación"
    if re.search(r"certificate|certificado|ssl provider|tls|handshake|pre.login", detail):
        return TLS_FAILURE
    if re.search(r"\b(4060|42000|229)\b|base efectiva", detail):
        return "Base / permisos"
    if re.search(r"\b(08001|08004|08s01|hyt00|hyt01|20009)\b|timeout|network", detail):
        return "Conexión (causa no confirmada)"
    return "Configuración u otro error"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true", help="Solo TCP y versiones locales")
    parser.add_argument("--certificate-name", help="Nombre DNS del certificado confirmado por el administrador")
    parser.add_argument("--ca-file", type=Path, help="PEM de CA confiable para FreeTDS")
    add_tls_options(parser)
    parser.add_argument("--report", type=Path, help="Guardar solo resultados redactados")
    args = parser.parse_args()
    if args.certificate_name and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]{0,252}",
                                                 args.certificate_name):
        parser.error("Nombre de certificado inválido.")
    try:
        with socket.create_connection((HOST, PORT), timeout=6):
            print(f"TCP {HOST}:{PORT} accesible")
    except OSError as exc:
        raise SystemExit(f"TCP falló: {type(exc).__name__}, código={exc.errno}") from None
    print("pyodbc", pyodbc.version, "|", ", ".join(pyodbc.drivers()))
    try:
        import pymssql
        print("pymssql", pymssql.__version__, "|", pymssql.get_dbversion())
    except ImportError:
        print("pymssql no disponible")
    if args.preflight:
        return 0

    if args.confirm_demo_exception and not args.allow_unverified_demo:
        parser.error("--confirm-demo-exception requiere --allow-unverified-demo.")
    user, password = require()
    tests = [
        ("pyodbc + ODBC 18", lambda: query(lambda: odbc_connect(18, user, password, args.certificate_name))),
        ("pyodbc + ODBC 17", lambda: query(lambda: odbc_connect(17, user, password, args.certificate_name))),
    ]
    if args.ca_file:
        tests.append(("pymssql + FreeTDS", lambda: freetds_query(args, user, password)))
    results = []
    retry = set()

    def record(name, run, mode):
        try:
            results.append((name, mode, "Conectó", run()))
            return None
        except Exception as exc:
            kind = category(exc)
            results.append((name, mode, kind, f"{type(exc).__name__}: {sanitize(exc, user, password)}"))
            return kind

    for name, run in tests:
        if record(name, run, "TLS validado") == TLS_FAILURE:
            retry.add(name)
    if not args.ca_file:
        results.append(("pymssql + FreeTDS", "TLS validado", "Omitido", "Falta PEM de CA confiable (--ca-file)."))
        retry.add("pymssql + FreeTDS")

    if retry and accept_exception(args):
        for major in (18, 17):
            name = f"pyodbc + ODBC {major}"
            if name in retry:
                record(name, lambda: query(lambda: odbc_connect(
                    major, user, password, None, verify=False,
                )), "TLS sin validar")
        if "pymssql + FreeTDS" in retry:
            record("pymssql + FreeTDS", lambda: freetds_query(args, user, password, verify=False),
                   "TLS sin validar")

    output = "Alternativa\tSeguridad\tResultado\tDetalle\n" + "\n".join(
        "\t".join(row) for row in results
    )
    print(output)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")
    return int(not any(status == "Conectó" for _, _, status, _ in results))


if __name__ == "__main__":
    raise SystemExit(main())
