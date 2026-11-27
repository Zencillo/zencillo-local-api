import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.core.security import hash_secret


def test_dotenv_startup_without_sql(tmp_path, monkeypatch):
    for key in (
        "LOCAL_API_JWT_KEY", "LOCAL_API_STATION", "LOCAL_API_DEVICES",
        "LOCAL_API_SQL_CONNECTION", "LOCAL_API_TOKEN_SECONDS", "LOCAL_API_SQL_TIMEOUT",
    ):
        monkeypatch.delenv(key, raising=False)
    devices = json.dumps({
        "dev": {"station": "local", "secret_hash": hash_secret("test"),
                "operations": ["ListarTiposVehiculo"]},
    })
    env = tmp_path / ".env"
    env.write_text(
        "LOCAL_API_JWT_KEY=unit-test-key-only-abcdefghijklmnopqrstuvwxyz\n"
        "LOCAL_API_STATION=local\n"
        f"LOCAL_API_DEVICES='{devices}'\n"
        "LOCAL_API_TOKEN_SECONDS=300\n"
        "LOCAL_API_SQL_CONNECTION=forbidden-fallback\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("LOCAL_API_TOKEN_SECONDS", "180")
    monkeypatch.chdir(tmp_path)
    settings = Settings.from_env()
    assert settings.token_seconds == 180
    assert settings.connection_string is None
    connect = MagicMock()
    with TestClient(create_app(connect=connect)) as client:
        assert client.get("/openapi.json").status_code == 200
        assert client.get("/docs").status_code == 200
        auth = client.post("/v1/auth/token", json={"device_id": "dev", "secret": "test"})
        assert auth.status_code == 200
        headers = {"Authorization": "Bearer " + auth.json()["data"]["access_token"]}
        error = client.post("/v1/operations", json={}, headers=headers)
        assert error.json()["message"] == "Solicitud inv\u00e1lida"
        response = client.post(
            "/v1/operations", headers=headers,
            json={"Query": "ListarTiposVehiculo", "parameters": {}},
        )
        assert response.status_code == 503
        assert response.json()["error"] == {"code": "DATABASE_NOT_CONFIGURED"}
        connect.assert_not_called()
