from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from unittest.mock import MagicMock
import sys

from fastapi.testclient import TestClient
import pyodbc
import pytest

from app.config import Device, Settings
from app.core.machine_secret import read, save
from app.core.security import hash_secret
from app.main import create_app

QUERY = {"Query": "ListarTiposVehiculo", "parameters": {}}


def settings():
    return Settings(
        jwt_key="fixture-signing-key-for-tests-only", connection_string="fixture",
        station="pilot", devices={
            device: Device(station="pilot", secret_hash=hash_secret(device),
                           operations={"ListarTiposVehiculo"})
            for device in ("windows", "android-1", "android-2")
        },
    )


def login(client, device):
    response = client.post("/v1/auth/token", json={"device_id": device, "secret": device})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_concurrent_devices_use_independent_connections_and_sessions():
    config = settings()
    workers = len(config.devices)
    pending_queries = Barrier(workers)
    created = []
    lock = Lock()

    def connect(*_args, **_kwargs):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.description = [("idtipovehiculo",), ("tipovehiculo",)]
        cursor.execute.side_effect = lambda *_: pending_queries.wait(timeout=8)
        cursor.fetchall.return_value = [(1, "Auto")]
        with lock:
            created.append(connection)
        return connection

    app = create_app(config, connect=connect)

    def request(device):
        with TestClient(app) as client:
            jwt = login(client, device)
            response = client.post("/v1/operations", json=QUERY,
                                   headers={"Authorization": f"Bearer {jwt}"})
            assert response.status_code == 200
            assert response.json()["data"]["items"] == [{"idtipovehiculo": 1, "tipovehiculo": "Auto"}]
            return jwt

    with ThreadPoolExecutor(max_workers=workers) as executor:
        assert len(set(executor.map(request, config.devices))) == workers
    assert len(created) == workers
    for connection in created:
        connection.cursor.return_value.close.assert_called_once()
        connection.close.assert_called_once()


def test_timeout_then_recovery_uses_a_new_connection(caplog):
    broken, healthy = MagicMock(), MagicMock()
    broken.cursor.return_value.execute.side_effect = pyodbc.Error("HYT00", "DO NOT LOG")
    healthy.cursor.return_value.description = [("idtipovehiculo",), ("tipovehiculo",)]
    healthy.cursor.return_value.fetchall.return_value = [(1, "Auto")]
    connect = MagicMock(side_effect=[broken, healthy])
    with TestClient(create_app(settings(), connect=connect)) as client:
        headers = {"Authorization": f"Bearer {login(client, 'windows')}"}
        first = client.post("/v1/operations", json=QUERY, headers=headers)
        assert first.status_code == 504
        assert client.post("/v1/operations", json=QUERY, headers=headers).status_code == 200
    assert "stage=execute sqlstate=HYT00" in caplog.text
    assert "DO NOT LOG" not in caplog.text
    for connection in (broken, healthy):
        connection.cursor.return_value.close.assert_called_once()
        connection.close.assert_called_once()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows DPAPI")
def test_machine_secret_round_trip_and_atomic_replace(tmp_path):
    path = tmp_path / "profile.dpapi"
    save(path, "fixture-secret-one")
    assert b"fixture-secret-one" not in path.read_bytes()
    assert read(path) == "fixture-secret-one"
    save(path, "fixture-secret-two")
    assert read(path) == "fixture-secret-two"
    assert list(tmp_path.iterdir()) == [path]
