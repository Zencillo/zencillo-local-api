"""Run one HTTPS instance from station files protected by the Windows installer."""
import argparse
from importlib.metadata import version
import ipaddress
import json
import logging
from pathlib import Path
import ssl

import uvicorn

from app.config import Device, Settings
from app.core.machine_secret import read
from app.main import create_app


def build(config_file: Path):
    values = json.loads(config_file.read_text(encoding="utf-8-sig"))
    root = config_file.parent
    address = ipaddress.ip_address(values["listen"])
    if address.version != 4 or address.is_unspecified or address.is_multicast or not address.is_private:
        raise ValueError("Se requiere una IPv4 privada explícita.")
    port = values["port"]
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("Puerto HTTPS inválido.")
    cert, key = root / "server-chain.pem", root / "server-key.pem"
    ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER).load_cert_chain(cert, key)
    from app.core.security_zen import load_station_profile
    from app.install_station_sql import connection_string
    profile = load_station_profile(root, values["station"], values.get("sql_port"))
    sql_connection = None if profile is None else connection_string(profile)
    encrypted = values.get("encrypt_operations", False)
    sql_login = values.get("sql_login_required", False)
    if type(encrypted) is not bool or type(sql_login) is not bool:
        raise ValueError("Modo de autenticación inválido.")
    settings = Settings(
        station=values["station"],
        devices={device_id: Device.model_validate({**config, "station": values["station"]})
                 for device_id, config in values["devices"].items()},
        jwt_key=read(root / "jwt.dpapi"),
        connection_string=sql_connection,
        envelope_keys_path=root / "local-envelope-keys" if encrypted else None,
        sql_login_required=sql_login,
        sql_login_profile=profile,
    )
    application = create_app(settings)
    return application, str(address), port, cert, key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        app, address, port, cert, key = build(args.config.resolve())
    except Exception as error:
        logging.error("Configuración de estación inválida: %s", type(error).__name__)
        return 1
    if args.check:
        if not app.state.sql_configured:
            logging.error("Perfil SQL de estación no disponible.")
            return 1
        logging.info("Configuración de estación válida. API %s.", version("zencillo-local-api"))
        return 0
    # Error responses and ODBC diagnostics are sanitized by the application.
    uvicorn.run(app, host=address, port=port, ssl_certfile=str(cert), ssl_keyfile=str(key),
                access_log=False, proxy_headers=False, server_header=False,
                timeout_graceful_shutdown=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
