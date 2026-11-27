import base64
from dataclasses import replace
import hashlib
import json
import secrets
from time import time
from unittest.mock import MagicMock

import pyodbc
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Device, Settings
from app.core.security import hash_secret
from app.install_station_sql import StationSqlProfile
from app.main import create_app

DEVICE_SECRET = "controlled fixture"
OPERATION = "ListarTiposVehiculo"


@pytest.fixture(scope="module")
def rsa_keys():
    return [rsa.generate_private_key(public_exponent=65537, key_size=2048) for _ in range(3)]


@pytest.fixture
def profiles(tmp_path, rsa_keys):
    for kid, key in zip(("current", "previous"), rsa_keys):
        (tmp_path / f"{kid}.pem").write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
    profile = StationSqlProfile(station="1/2/3", server="fixture.local", port=1433,
                                database="Station", user="service", password=SecretStr("service-fixture"))
    settings = Settings(jwt_key="j"*40, connection_string="fixture", station=profile.station,
                        envelope_keys_path=tmp_path, sql_login_profile=profile,
                        devices={"dev": Device(station=profile.station, secret_hash=hash_secret(DEVICE_SECRET),
                                               operations={OPERATION})})
    connect = MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.description = [("idtipovehiculo",), ("tipovehiculo",)]
    cursor.fetchall.return_value = [(2, "AUTO")]
    return settings, connect


def request(key, kid, purpose, binding, body, **changes):
    payload = {"purpose":purpose, "binding":binding, "body":body,
               "requestId":secrets.token_urlsafe(16), "issuedAt":int(time()), **changes}
    secret = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    wrapped = key.public_key().encrypt(secret,
        padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    encrypted = AESGCM(secret).encrypt(nonce, json.dumps(payload).encode(), None)
    raw = b"\x01" + len(wrapped).to_bytes(2, "big") + wrapped + nonce + encrypted
    return {"kid":kid, "content":base64.urlsafe_b64encode(raw).decode().rstrip("=")}, secret


def unpack(response, secret):
    content = response.json()["content"]
    data = base64.urlsafe_b64decode(content + "=" * (-len(content) % 4))
    assert data[0] == 1
    return json.loads(AESGCM(secret).decrypt(data[1:13], data[13:], None))


def login(client, key, kid="current", **extras):
    challenge = client.get("/v1/auth/challenge").json()["data"]["challenge"]
    envelope, secret = request(key, kid, "login", challenge,
                               {"device_id":"dev", "secret":DEVICE_SECRET, **extras})
    response = client.post("/v1/auth/token", json=envelope)
    return response, secret, envelope


def test_encrypted_login_operations_replay_and_restart(profiles, rsa_keys):
    settings, connect = profiles
    traffic = {"Query":OPERATION,"parameters":{}}
    with TestClient(create_app(settings, connect=connect)) as client:
        response, secret, login_box = login(client, rsa_keys[0])
        token = unpack(response, secret)["data"]["access_token"]
        assert client.post("/v1/auth/token", json=login_box).status_code == 409
        auth = {"Authorization":f"Bearer {token}"}
        public_der = rsa_keys[0].public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        alias = f"rsa-{hashlib.sha256(public_der).hexdigest()[:32]}"
        for kid, key in (("current", rsa_keys[0]), ("previous", rsa_keys[1]), (alias, rsa_keys[0])):
            box, secret = request(key, kid, "operations", token, traffic)
            assert unpack(client.post("/v1/operations", headers=auth, json=box), secret)["data"]["items"] == [
                {"idtipovehiculo":2, "tipovehiculo":"AUTO"},
            ]
            assert client.post("/v1/operations", headers=auth, json=box).json()["error"]["code"] == "REPLAYED_REQUEST"
        assert connect.call_count == 3
    with TestClient(create_app(settings, connect=connect)) as restarted:
        assert restarted.post("/v1/auth/token", json=login_box).status_code == 400
        assert restarted.post("/v1/operations", headers=auth, json=box).status_code == 401
        response, secret, _ = login(restarted, rsa_keys[0])
        assert unpack(response, secret)["success"]


def test_rejects_bad_key_tag_purpose_binding_version_and_plaintext(profiles, rsa_keys):
    settings, connect = profiles
    with TestClient(create_app(settings, connect=connect)) as client:
        response, secret, _ = login(client, rsa_keys[0])
        token = unpack(response, secret)["data"]["access_token"]
        auth = {"Authorization":f"Bearer {token}"}
        body = {"Query":OPERATION,"parameters":{}}
        valid, _ = request(rsa_keys[0], "current", "operations", token, body)
        wire = valid["content"]
        raw = bytearray(base64.urlsafe_b64decode(wire + "=" * (-len(wire) % 4)))
        raw[-1] ^= 1
        tampered = {**valid, "content":base64.urlsafe_b64encode(raw).decode().rstrip("=")}
        raw[0] = 2
        version = {**valid, "content":base64.urlsafe_b64encode(raw).decode().rstrip("=")}
        for envelope in (
            body, tampered, version, {**valid,"kid":"absent"},
            request(rsa_keys[2], "current", "operations", token, body)[0],
            request(rsa_keys[0], "current", "login", token, body)[0],
            request(rsa_keys[0], "current", "operations", "another-session", body)[0],
            request(rsa_keys[0], "current", "operations", token, body, issuedAt=1)[0],
        ):
            response = client.post("/v1/operations", headers=auth, json=envelope)
            assert (response.status_code, response.json()["error"]["code"]) == (400, "INVALID_ENVELOPE")
        connect.assert_not_called()


def test_optional_sql_login_validates_fixed_target_and_sanitizes_errors(profiles, rsa_keys):
    settings, connect = profiles
    settings = replace(settings, sql_login_required=True)
    with TestClient(create_app(settings, connect=connect)) as client:
        extras = {"sqlUser":"operator", "sqlPassword":"synthetic"}
        response, secret, _ = login(client, rsa_keys[0], **extras)
        assert unpack(response, secret)["success"]
        provided = connect.call_args.args[0]
        assert "tcp:fixture.local,1433" in provided and "DATABASE={Station}" in provided
        connect.side_effect = pyodbc.Error("28000", "driver detail secret")
        response, _, _ = login(client, rsa_keys[0], **extras)
        assert response.status_code == 401 and response.json()["error"]["code"] == "SQL_LOGIN_REJECTED"
        assert "driver detail" not in response.text
        connect.side_effect = pyodbc.Error("08001", "driver detail secret")
        response, _, _ = login(client, rsa_keys[0], **extras)
        assert response.status_code == 503 and response.json()["error"]["code"] == "SQL_UNAVAILABLE"


def test_file_absent_leaves_encrypted_endpoint_available_but_sql_not_configured(profiles, rsa_keys):
    settings, connect = profiles
    settings = replace(settings, connection_string=None)
    with TestClient(create_app(settings, connect=connect)) as client:
        response, secret, _ = login(client, rsa_keys[0])
        token = unpack(response, secret)["data"]["access_token"]
        box, _ = request(rsa_keys[0], "current", "operations", token, {"Query":OPERATION,"parameters":{}})
        response = client.post("/v1/operations", headers={"Authorization":f"Bearer {token}"}, json=box)
        assert response.status_code == 503 and response.json()["error"]["code"] == "DATABASE_NOT_CONFIGURED"
        connect.assert_not_called()
