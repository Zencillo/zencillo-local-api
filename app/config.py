import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.install_station_sql import StationSqlProfile

from dotenv import dotenv_values

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class Device(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    station: str = Field(min_length=1, max_length=128)
    secret_hash: SecretStr
    operations: frozenset[str]
    enabled: bool = True


@dataclass(frozen=True)
class Settings:
    jwt_key: str = field(repr=False)
    connection_string: str | None = field(repr=False)
    devices: dict[str, Device]
    issuer: str = "zencillo-local-api"
    audience: str = "zencillo-local-devices"
    token_seconds: int = 300
    sql_timeout: int = 5
    station: str = ""
    envelope_keys_path: Path | None = field(default=None, repr=False)
    sql_login_required: bool = False
    demo_cloud_refresh: bool = False
    sql_login_profile: "StationSqlProfile | None" = field(default=None, repr=False)

    def __post_init__(self):
        if len(self.jwt_key.encode()) < 32:
            raise ValueError("LOCAL_API_JWT_KEY requiere al menos 32 bytes.")
        if not 1 <= self.token_seconds <= 900 or not 1 <= self.sql_timeout <= 60:
            raise ValueError("TTL JWT o timeout SQL fuera de rango.")
        if self.sql_login_required and self.envelope_keys_path is None:
            raise ValueError("La autenticación SQL requiere el transporte cifrado local.")
        if not self.station or not self.devices or any(
            device.station != self.station for device in self.devices.values()
        ):
            raise ValueError("Todos los dispositivos deben pertenecer a la estación local.")

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        path = Path.cwd() / ".env" if env_file is None else env_file
        values = {**dotenv_values(path, encoding="utf-8-sig", interpolate=False), **os.environ}
        required = ("LOCAL_API_JWT_KEY", "LOCAL_API_STATION", "LOCAL_API_DEVICES")
        missing = [key for key in required if not values.get(key)]
        if missing:
            raise ValueError("Variables obligatorias faltantes: " + ", ".join(missing))
        try:
            devices = {
                key: Device.model_validate(value)
                for key, value in json.loads(values["LOCAL_API_DEVICES"]).items()
            }
            token_seconds = int(values.get("LOCAL_API_TOKEN_SECONDS", "300"))
            sql_timeout = int(values.get("LOCAL_API_SQL_TIMEOUT", "5"))
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Registro de dispositivos, TTL o timeout local inválido.") from None
        from app.core.security_zen import load_station_profile
        from app.install_station_sql import connection_string

        root = Path(values["LOCAL_API_CONFIG_DIR"]) if values.get("LOCAL_API_CONFIG_DIR") else path.parent
        profile = load_station_profile(root, values["LOCAL_API_STATION"])
        connection = connection_string(profile) if profile is not None else None
        return cls(
            jwt_key=values["LOCAL_API_JWT_KEY"],
            connection_string=connection,
            station=values["LOCAL_API_STATION"],
            envelope_keys_path=Path(values["LOCAL_API_ENVELOPE_KEYS_PATH"])
            if values.get("LOCAL_API_ENVELOPE_KEYS_PATH") else None,
            devices=devices,
            token_seconds=token_seconds,
            sql_timeout=sql_timeout,
        )
