"""One-time local administrative import from a trusted Capturador installer."""
import argparse
import ctypes
import sys
from pathlib import Path

import pyodbc
from contextlib import closing
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from app.core.windows_credentials import read, save

MAX_PAYLOAD = 8192


class StationSqlProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    station: str = Field(pattern=r"^[1-9][0-9]*/[1-9][0-9]*/[1-9][0-9]*$")
    server: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$")
    port: int | None = Field(ge=1, le=65535)
    instance: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_]{1,128}$")
    database: str = Field(min_length=1, max_length=128)
    user: str = Field(min_length=1, max_length=128)
    password: SecretStr


def target(station):
    return f"ZencilloLocalApi/StationSQL/{station}"


def connection_string(profile):
    if profile.user.casefold() == "sa":
        raise ValueError("Provision a restricted SQL account for the station.")
    password = profile.password.get_secret_value()
    if not password or any(
        ch in value
        for value in (profile.database, profile.user, password)
        for ch in "\r\n\0"
    ):
        raise ValueError("Invalid SQL profile.")
    if (profile.port is None) == (profile.instance is None):
        raise ValueError("The profile requires a TCP port or an instance.")
    endpoint = (f"{profile.server},{profile.port}" if profile.port is not None
                else f"{profile.server}\\{profile.instance}")
    options = {
        "DRIVER": "ODBC Driver 18 for SQL Server",
        "SERVER": f"tcp:{endpoint}",
        "DATABASE": profile.database, "UID": profile.user, "PWD": password,
        "Encrypt": "yes", "TrustServerCertificate": "no",
    }
    return ";".join(key + "={" + value.replace("}", "}}") + "}" for key, value in options.items())


def install(data, confirmed_station, connect=pyodbc.connect, store=save, *, verify_service_access=False):
    if len(data) > MAX_PAYLOAD:
        raise ValueError("Invalid payload length.")
    profile = StationSqlProfile.model_validate_json(data)
    if profile.station != confirmed_station:
        raise ValueError("The station confirmation does not match.")
    connection = connection_string(profile)
    with closing(connect(connection, timeout=6, autocommit=True)) as sql:
        sql.timeout = 6
        with closing(sql.cursor()) as cursor:
            cursor.execute("SELECT DB_NAME()")
            if cursor.fetchone()[0] != profile.database:
                raise ValueError("The effective database does not match.")
            if verify_service_access:
                from app.modules.article.repository import ArticleQuery, load_query

                cursor.execute(
                    "SELECT IS_SRVROLEMEMBER('sysadmin'), IS_ROLEMEMBER('db_owner'), "
                    "HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'CONTROL')"
                )
                roles = cursor.fetchone()
                if not roles or any(role is None or role == 1 for role in roles):
                    raise ValueError("El perfil SQL requiere una cuenta de permisos limitados.")
                for query in (ArticleQuery.VEHICLE_TYPES, ArticleQuery.EXPENSE_TYPES,
                              ArticleQuery.ROUNDING_CONFIG, ArticleQuery.FUELS):
                    cursor.execute(f"SELECT TOP (0) * FROM ({load_query(query)}) AS catalog")
    store(profile.user, connection, target=target(profile.station))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-station", required=True)
    parser.add_argument("--service-directory", type=Path)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32" or not ctypes.windll.shell32.IsUserAnAdmin():
        print("El aprovisionamiento requiere el instalador Windows elevado.", file=sys.stderr)
        return 2
    if sys.stdin.isatty():
        print("Se requiere el canal privado del instalador.", file=sys.stderr)
        return 2
    try:
        if args.service_directory:
            from app.core.machine_secret import save as save_machine

            directory = args.service_directory.resolve()
            profile = directory / "sql.dpapi"
            if not (directory / "jwt.dpapi").is_file() or (profile.exists() and not args.replace):
                return 2

            def store(_user, connection, **_unused):
                save_machine(profile, connection)

            install(sys.stdin.buffer.read(MAX_PAYLOAD + 1), args.confirm_station,
                    store=store, verify_service_access=True)
            print("Perfil SQL del servicio validado y guardado.")
            return 0
        if read(target=target(args.confirm_station)):
            print('El perfil ya existe; el instalador no lo reemplaza.', file=sys.stderr)
            return 2
        install(sys.stdin.buffer.read(MAX_PAYLOAD + 1), args.confirm_station)
    except (ValidationError, ValueError, OSError, pyodbc.Error):
        print("No se pudo validar o guardar el perfil SQL autorizado.", file=sys.stderr)
        return 1
    print("Perfil SQL autorizado y guardado para este usuario Windows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
