from contextlib import closing
import json
import socket
from http.client import HTTPSConnection
import ssl
from threading import Thread
import time
from unittest.mock import Mock

import pytest

from app import import_station_lan as receiver
from tools.run_flutter_windows_pilot import certificates


def test_receiver_rejects_outside_subnet_and_live_port(tmp_path):
    (tmp_path / "jwt.dpapi").touch()
    (tmp_path / "service.json").write_text(
        json.dumps({"listen": "192.168.2.4", "port": 8765, "subnet": "192.168.2.0/24"}),
        encoding="utf-8",
    )
    for port, source in [(8766, "192.168.3.4"), (8765, "192.168.2.8")]:
        with pytest.raises(ValueError):
            receiver.receive(tmp_path, port, source, "3/10/1", "fixture")


def test_one_use_tls_transfer_without_real_sql(tmp_path, monkeypatch):
    try:
        certificates(tmp_path)
    except FileNotFoundError:
        pytest.skip("OpenSSL lab utility unavailable")
    (tmp_path / "server.pem").rename(tmp_path / "server-chain.pem")
    (tmp_path / "server.key").rename(tmp_path / "server-key.pem")
    tls = ssl.create_default_context(cafile=str(tmp_path / "ca.pem"))
    install = Mock()
    monkeypatch.setattr(receiver, "install", install)
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    result = []
    listener = Thread(target=lambda: result.append(receiver._receive(
        tmp_path, "127.0.0.1", port, "127.0.0.1", "3/10/1", "fixture-invitation", 5,
    )), daemon=True)
    listener.start()

    def post(token):
        with closing(HTTPSConnection("127.0.0.1", port, context=tls, timeout=2)) as client:
            client.request("POST", "/import", b'{"test":true}', {"Authorization": f"Bearer {token}"})
            with closing(client.getresponse()) as response:
                return response.status

    for attempt in range(30):
        try:
            assert post("incorrect") == 403
            break
        except ConnectionRefusedError:
            if attempt == 29:
                raise
            time.sleep(0.05)
    assert post("fixture-invitation") == 204
    listener.join(timeout=3)
    assert result == [True]
    install.assert_called_once()
    assert install.call_args.args == (b'{"test":true}', "3/10/1")
    with pytest.raises(OSError):
        post("fixture-invitation")
