import json
from unittest.mock import MagicMock

import pyodbc

from tools import demo_config, run_demo_pilot


def test_missing_connection_does_not_prompt(monkeypatch, tmp_path):
    import pytest

    monkeypatch.setattr(demo_config, "ENV", tmp_path / ".env")
    monkeypatch.setattr("builtins.input", lambda *_: pytest.fail("No debe pedir credenciales"))
    with pytest.raises(SystemExit, match="LOCAL_API_SQL_CONNECTION"):
        demo_config.require()


def test_env_load_preserves_odbc_special_characters(monkeypatch, tmp_path):
    from dotenv import set_key
    path = tmp_path / ".env"
    path.touch()
    monkeypatch.setattr(demo_config, "ENV", path)
    password = "synthetic;pa}ss'$#"
    set_key(path, demo_config.KEY, demo_config.connection_string("demo", password))
    assert demo_config.require() == ("demo", password)
    assert "TrustServerCertificate={no}" in demo_config.connection_string("demo", password)


def test_unattended_demo_retry_and_json_report(monkeypatch, tmp_path):
    report = tmp_path / "pilot.json"
    monkeypatch.setattr("sys.argv", [
        "pilot", "--report", str(report), "--allow-unverified-demo", "--confirm-demo-exception",
    ])
    monkeypatch.setattr("builtins.input", MagicMock(side_effect=AssertionError("Unexpected prompt")))
    monkeypatch.setattr(run_demo_pilot, "require", lambda: ("local-user", "test-password"))
    rows = {(i, str(i)): 1 for i in range(19)}
    sql = MagicMock(side_effect=[pyodbc.Error("08001", "SSL Provider: certificate failed"), rows])
    http = MagicMock()
    monkeypatch.setattr(run_demo_pilot, "inspect_demo", sql)
    monkeypatch.setattr(run_demo_pilot, "http_pilot", http)
    assert run_demo_pilot.main() == 0
    assert "TrustServerCertificate={no}" in sql.call_args_list[0].args[0]
    assert "TrustServerCertificate={yes}" in sql.call_args_list[1].args[0]
    http.assert_called_once()
    assert "test-password" not in report.read_text(encoding="utf8")
    assert len(json.loads(report.read_text(encoding="utf8"))["events"]) == 2
