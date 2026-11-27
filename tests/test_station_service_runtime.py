import json
import socket
import ssl
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from app.core.machine_secret import save
from app.core.security import hash_secret
from tools.run_flutter_windows_pilot import OPENSSL, certificates


@pytest.mark.skipif(sys.platform != "win32" or not OPENSSL.is_file(),
                    reason="DPAPI Windows and OpenSSL lab fixture")
def test_service_runner_https_start_and_restart(tmp_path):
    certificates(tmp_path)
    (tmp_path / "server.pem").rename(tmp_path / "server-chain.pem")
    (tmp_path / "server.key").rename(tmp_path / "server-key.pem")
    save(tmp_path / "jwt.dpapi", "fixture-token-signing-key-not-for-station")
    save(tmp_path / "sql.dpapi", "fixture-no-sql-used")
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    config = tmp_path / "service.json"
    config.write_text(json.dumps({
        "listen": "127.0.0.1", "port": port, "station": "test",
        "devices": {"test": {"secret_hash": hash_secret("fixture"), "operations": []}},
    }), encoding="utf8")
    tls = ssl.create_default_context(cafile=str(tmp_path / "ca.pem"))
    command = [sys.executable, "-m", "app.station_service", "--config", str(config)]
    check = subprocess.run([*command, "--check"], capture_output=True, timeout=10)
    assert check.returncode == 1
    assert b"Perfil SQL" in check.stderr
    for _ in range(2):
        with subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                              creationflags=subprocess.CREATE_NO_WINDOW) as process:
            try:
                deadline = time.monotonic() + 12
                while process.poll() is None and time.monotonic() < deadline:
                    try:
                        with urlopen(f"https://127.0.0.1:{port}/healthz", context=tls,
                                     timeout=1) as response:
                            assert json.load(response) == {"status": "ok"}
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    pytest.fail("El ejecutor HTTPS no inició.")
            finally:
                process.terminate()
                process.wait(timeout=5)
