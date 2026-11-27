import json
from unittest.mock import MagicMock

import pytest

from app.install_station_sql import install, target


def payload(**overrides):
    return json.dumps({
        "station": "123/456/1", "server": "sql.demo.invalid", "port": 1433,
        "database": "demo", "user": "read_only", "password": "fixture;ap}ost",
        **overrides,
    }).encode()


def test_install_validates_only_db_name_then_stores_under_station():
    connect, store = MagicMock(), MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.fetchone.return_value = ("demo",)
    install(payload(), "123/456/1", connect, store)
    cursor.execute.assert_called_once_with("SELECT DB_NAME()")
    wire = connect.call_args.args[0]
    assert "Encrypt={yes};TrustServerCertificate={no}" in wire
    assert "PWD={fixture;ap}}ost}" in wire
    store.assert_called_once_with("read_only", wire, target=target("123/456/1"))
    connect.return_value.close.assert_called_once()


@pytest.mark.parametrize("data,confirmed", [
    (payload(), "123/456/2"),
    (payload(user="SA"), "123/456/1"),
    (payload(server="host;TrustServerCertificate=yes"), "123/456/1"),
    (payload(port=180000), "123/456/1"),
    (payload(password=""), "123/456/1"),
])
def test_install_rejects_invalid_unconfirmed_or_privileged_profiles(data, confirmed):
    connect, store = MagicMock(), MagicMock()
    with pytest.raises(ValueError):
        install(data, confirmed, connect, store)
    connect.assert_not_called()
    store.assert_not_called()


def test_install_does_not_store_if_actual_db_differs():
    connect, store = MagicMock(), MagicMock()
    connect.return_value.cursor.return_value.fetchone.return_value = ("another",)
    with pytest.raises(ValueError):
        install(payload(), "123/456/1", connect, store)
    store.assert_not_called()

def test_service_import_checks_read_access_before_writing():
    connect, store = MagicMock(), MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.fetchone.side_effect = [("demo",), (0, 0, 0)]
    install(payload(), "123/456/1", connect, store, verify_service_access=True)
    assert cursor.execute.call_count == 6
    assert all(call.args[0].startswith("SELECT TOP (0)") for call in cursor.execute.call_args_list[2:])
    store.assert_called_once()


def test_service_import_rejects_admin_alias():
    connect, store = MagicMock(), MagicMock()
    connect.return_value.cursor.return_value.fetchone.side_effect = [("demo",), (1, 0, 0)]
    with pytest.raises(ValueError):
        install(payload(), "123/456/1", connect, store, verify_service_access=True)
    store.assert_not_called()
