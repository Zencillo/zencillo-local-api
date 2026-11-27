import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import Device, Settings
from app.errors import ApiError


def hash_secret(secret: str, salt: bytes | None = None) -> str:
    salt = secrets.token_bytes(16) if salt is None else salt
    digest = hashlib.scrypt(secret.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt-v1${salt.hex()}${digest.hex()}"


def matches(secret: str, encoded: str) -> bool:
    try:
        version, salt, _ = encoded.split("$")
        if version != "scrypt-v1" or len(salt) != 32:
            return False
        return hmac.compare_digest(hash_secret(secret, bytes.fromhex(salt)), encoded)
    except ValueError:
        return False


class LocalAuth:
    def __init__(self, settings: Settings, instance_binding: str | None = None):
        self.settings = settings
        self.instance_binding = instance_binding
        self.dummy_hash = hash_secret(secrets.token_hex(32))

    def issue(self, device_id: str, secret: str, verify=None) -> str:
        device = self.settings.devices.get(device_id)
        encoded = device.secret_hash.get_secret_value() if device else self.dummy_hash
        if not matches(secret, encoded) or not device or not device.enabled:
            raise ApiError(401, "UNAUTHENTICATED", "Credenciales locales inválidas")
        if verify is not None:
            verify()
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": device_id, "station": device.station,
                **({"boot": self.instance_binding} if self.instance_binding is not None else {}),
                "iss": self.settings.issuer, "aud": self.settings.audience,
                "iat": now, "exp": now + timedelta(seconds=self.settings.token_seconds),
            },
            self.settings.jwt_key, algorithm="HS256",
        )

    def issue_validated(self, device_id: str, station: str) -> str:
        device = self.settings.devices.get(device_id)
        if not device or not device.enabled or device.station != station:
            raise ApiError(403, "STATION_MISMATCH", "Estación no autorizada")
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": device_id, "station": station,
                **({"boot": self.instance_binding} if self.instance_binding is not None else {}),
                "iss": self.settings.issuer, "aud": self.settings.audience,
                "iat": now, "exp": now + timedelta(seconds=self.settings.token_seconds),
            },
            self.settings.jwt_key, algorithm="HS256",
        )

    def authenticate(self, token: str) -> tuple[Device, str]:
        try:
            payload = jwt.decode(
                token, self.settings.jwt_key, algorithms=["HS256"],
                issuer=self.settings.issuer, audience=self.settings.audience,
                options={"require": ["sub", "station", "iat", "exp", "iss", "aud"]},
            )
        except jwt.InvalidTokenError as exc:
            raise ApiError(401, "UNAUTHENTICATED", "Token local inválido") from exc
        if self.instance_binding is not None and payload.get("boot") != self.instance_binding:
            raise ApiError(401, "UNAUTHENTICATED", "Token local inválido")
        device = self.settings.devices.get(payload["sub"])
        if not device or not device.enabled:
            raise ApiError(403, "FORBIDDEN", "Dispositivo no autorizado")
        if payload["station"] != device.station or device.station != self.settings.station:
            raise ApiError(403, "STATION_MISMATCH", "Estación no autorizada")
        return device, payload["sub"]
