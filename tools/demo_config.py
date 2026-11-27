"""Local .env configuration for the fixed DEMO diagnostics."""
import argparse
from getpass import GetPassWarning, getpass
from pathlib import Path
import re
import warnings

from dotenv import dotenv_values, set_key

HOST = "10.1.10.15"
PORT = 1433
DATABASE = "ZencilloAutomatizacion"
ENV = Path(__file__).resolve().parents[1] / ".env"
KEY = "LOCAL_API_SQL_CONNECTION"
FIXED = {
    "DRIVER": "ODBC Driver 18 for SQL Server", "SERVER": f"tcp:{HOST},{PORT}",
    "DATABASE": DATABASE, "Encrypt": "yes", "TrustServerCertificate": "no",
}
PAIR = re.compile(r"([A-Za-z]+)=\{((?:[^}]|}})*)\}(?:;|$)")


def quote(value):
    return "{" + value.replace("}", "}}") + "}"


def connection_string(user, password, verify=True):
    params = {**FIXED, "UID": user, "PWD": password}
    if not verify:
        params["TrustServerCertificate"] = "yes"
    return ";".join(f"{key}={quote(value)}" for key, value in params.items())


def require():
    raw = dotenv_values(ENV, interpolate=False, encoding="utf-8-sig").get(KEY)
    if not raw:
        raise SystemExit("Falta LOCAL_API_SQL_CONNECTION en el .env local.")
    parts, position = {}, 0
    while position < len(raw):
        match = PAIR.match(raw, position)
        if not match or match[1] in parts:
            raise SystemExit("El formato de la conexión DEMO en .env no es válido.")
        parts[match[1]] = match[2].replace("}}", "}")
        position = match.end()
    if set(parts) != set(FIXED) | {"UID", "PWD"} or any(
        parts.get(key) != value for key, value in FIXED.items()
    ) or not (parts["UID"] and parts["PWD"]):
        raise SystemExit("El .env no contiene la conexión fija de DEMO con TLS validado.")
    return parts["UID"], parts["PWD"]


def add_tls_options(parser):
    parser.add_argument("--allow-unverified-demo", action="store_true")
    parser.add_argument("--confirm-demo-exception", action="store_true")


def accept_exception(args):
    if not args.allow_unverified_demo:
        return False
    print("AVISO DEMO: conexión cifrada sin validar la identidad del servidor.")
    if args.confirm_demo_exception:
        return True
    try:
        return input("Para autorizar escribe DEMO SIN VALIDAR: ").strip() == "DEMO SIN VALIDAR"
    except EOFError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup-sa", action="store_true", required=True)
    parser.parse_args()
    if not ENV.is_file() or dotenv_values(ENV, interpolate=False).get(KEY):
        raise SystemExit("Se requiere un .env existente con la conexión SQL vacía.")
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        try:
            password = getpass("Contraseña DEMO (entrada privada): ")
        except GetPassWarning:
            raise SystemExit("No hay una consola que permita entrada oculta.") from None
    if not password or any(ch in password for ch in "\r\n\0"):
        raise SystemExit("La contraseña está vacía o contiene caracteres no admitidos.")
    set_key(ENV, KEY, connection_string("sa", password), quote_mode="always", encoding="utf-8")
    if require() != ("sa", password):
        raise SystemExit("No se pudo verificar la configuración escrita.")
    print("Conexión DEMO guardada y verificada; TLS validado por defecto.")


if __name__ == "__main__":
    main()
