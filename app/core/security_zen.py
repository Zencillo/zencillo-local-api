"""Compatibility reader for station files created by the legacy product."""
import base64
import binascii
import json
from pathlib import Path

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from pydantic import BaseModel, SecretStr, ValidationError

from app.install_station_sql import StationSqlProfile, connection_string


class SecurityZenError(ValueError):
    pass


class LegacyCredentials(BaseModel):
    user: str
    password: SecretStr
    server: str
    kind: str
    date: str
    database: str


def decode_security_zen(content: str, key: bytes) -> LegacyCredentials:
    try:
        if len(key) not in (16, 24, 32):
            raise ValueError()
        compact = content.translate({ord(char): None for char in " \r\n"})
        ciphertext = base64.b64decode(compact, altchars=b"-_", validate=True)
        decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpad = padding.PKCS7(128).unpadder()
        data = json.loads((unpad.update(padded) + unpad.finalize()).decode("utf-8"))
        return LegacyCredentials(
            user=data["user"], password=data["pass"], server=data["server"],
            kind=data["type"], date=data["date"], database=data["database"],
        )
    except (TypeError, ValueError, KeyError, binascii.Error):
        raise SecurityZenError("Archivo de configuración SQL inválido.") from None


def read_security_zen(path: Path, key: bytes) -> LegacyCredentials:
    try:
        with path.open("rb") as stream:
            content = stream.read(65537)
        if len(content) > 65536:
            raise ValueError()
        return decode_security_zen(content.decode("utf-8-sig"), key)
    except (OSError, ValueError):
        raise SecurityZenError("Archivo de configuración SQL no disponible.") from None


def station_profile(credentials: LegacyCredentials, station: str, port: int | None = None) -> StationSqlProfile:
    server = credentials.server.strip()
    if server.lower().startswith("tcp:"):
        server = server[4:]
    server = server.replace("/", "\\").replace("\\\\", "\\")
    instance = None
    if "," in server:
        server, explicit = server.rsplit(",", 1)
        if port is not None or not explicit.isascii() or not explicit.isdecimal():
            raise SecurityZenError("Puerto SQL inválido.")
        port = int(explicit)
    elif "\\" in server:
        server, instance = server.split("\\", 1)
    else:
        if ":" in server:
            # Capturador strips a colon suffix and takes the port from setup.
            server = server.split(":", 1)[0]
        if port is None:
            port = 1433
    try:
        if not credentials.password.get_secret_value().strip():
            raise ValueError()
        profile = StationSqlProfile(station=station, server=server.strip(), port=port,
                                    instance=instance.strip() if instance is not None else None,
                                    database=credentials.database.strip(), user=credentials.user.strip(),
                                    password=credentials.password)
        connection_string(profile)
        return profile
    except (ValueError, ValidationError):
        raise SecurityZenError("Perfil del archivo SQL no habilitado para estación.") from None


def load_station_profile(root: Path, station: str, port: int | None = None) -> StationSqlProfile | None:
    from app.core.machine_secret import read
    try:
        key = read(root / "legacy-sql-key.dpapi").encode("utf-8")
        return station_profile(read_security_zen(root / "AUTOMATIZACION.security_zen", key), station, port)
    except (OSError, ValueError, TypeError, AttributeError):
        return None
