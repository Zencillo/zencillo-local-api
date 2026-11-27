"""Local request framing compatible with the existing Dart secure codec."""
import base64
from collections import OrderedDict
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
from threading import Lock
from time import monotonic, time

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.errors import ApiError


KEY_ID = re.compile(r"[a-zA-Z0-9_-]{1,48}")
BASE64URL = re.compile(r"[a-zA-Z0-9_-]+")
NONCE_ID = re.compile(r"[a-zA-Z0-9_-]{22}")
WINDOW_SECONDS = 60
MAX_CONTENT = 768 * 1024
MAX_REPLAY_ENTRIES = 16384


class LocalEnvelope:
    def __init__(self, path: Path):
        self.challenge = secrets.token_urlsafe(24)
        self.keys = {}
        self.public_ids = {}
        entries = list(path.glob("*.pem"))
        if not 1 <= len(entries) <= 8:
            raise ValueError("La estación requiere entre una y ocho claves locales.")
        for file in entries:
            if not KEY_ID.fullmatch(file.stem):
                raise ValueError("Identificador de clave local inválido.")
            key = serialization.load_pem_private_key(file.read_bytes(), password=None)
            if not isinstance(key, rsa.RSAPrivateKey) or key.key_size not in {2048, 3072, 4096}:
                raise ValueError("Clave RSA local incompatible.")
            self.keys[file.stem] = key
            public_der = key.public_key().public_bytes(
                serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
            fingerprint = hashlib.sha256(public_der).hexdigest()[:32]
            self.public_ids[f"rsa-{fingerprint}"] = key
        self._seen = OrderedDict()
        self._lock = Lock()

    def open(self, envelope, purpose: str, binding: str):
        try:
            if set(envelope) != {"kid", "content"}:
                raise ValueError()
            kid, content = envelope["kid"], envelope["content"]
            if not isinstance(kid, str) or not isinstance(content, str) or len(content) > MAX_CONTENT:
                raise ValueError()
            if not BASE64URL.fullmatch(content):
                raise ValueError()
            private_key = self.public_ids.get(kid) or self.keys[kid]
            data = base64.b64decode(content + "=" * (-len(content) % 4), altchars=b"-_", validate=True)
            wrapped_size = private_key.key_size // 8
            if len(data) < 3 + wrapped_size + 12 + 16 + 1 or data[0] != 1:
                raise ValueError()
            if int.from_bytes(data[1:3], "big") != wrapped_size:
                raise ValueError()
            offset = 3 + wrapped_size
            digest = hashes.SHA256()
            secret = private_key.decrypt(data[3:offset], padding.OAEP(
                mgf=padding.MGF1(digest), algorithm=digest, label=None))
            if len(secret) != 32:
                raise ValueError()
            payload = json.loads(AESGCM(secret).decrypt(data[offset:offset + 12], data[offset + 12:], None))
            if not isinstance(payload, dict) or set(payload) != {"purpose", "binding", "issuedAt", "requestId", "body"}:
                raise ValueError()
            if payload["purpose"] != purpose or not hmac.compare_digest(payload["binding"], binding):
                raise ValueError()
            issued = payload["issuedAt"]
            request_id = payload["requestId"]
            if type(issued) is not int or abs(time() - issued) > WINDOW_SECONDS:
                raise ValueError()
            if not isinstance(request_id, str) or not NONCE_ID.fullmatch(request_id) or not isinstance(payload["body"], dict):
                raise ValueError()
        except (KeyError, TypeError, ValueError, InvalidTag):
            raise ApiError(400, "INVALID_ENVELOPE", "Petición cifrada inválida.") from None
        return payload["body"], secret, request_id

    def accept(self, purpose: str, binding: str, request_id: str) -> None:
        key = (purpose, hashlib.sha256(binding.encode()).digest(), request_id)
        with self._lock:
            now = monotonic()
            while self._seen and next(iter(self._seen.values())) <= now:
                self._seen.popitem(last=False)
            if key in self._seen:
                raise ApiError(409, "REPLAYED_REQUEST", "Petición cifrada repetida.")
            if len(self._seen) >= MAX_REPLAY_ENTRIES:
                raise ApiError(503, "ENVELOPE_BUSY", "Capacidad de peticiones cifradas agotada.")
            self._seen[key] = now + 2 * WINDOW_SECONDS

    @staticmethod
    def seal(data, secret: bytes):
        nonce = secrets.token_bytes(12)
        encrypted = AESGCM(secret).encrypt(nonce, json.dumps(data, ensure_ascii=False).encode(), None)
        return {"content": base64.urlsafe_b64encode(b"\x01" + nonce + encrypted).decode().rstrip("=")}
