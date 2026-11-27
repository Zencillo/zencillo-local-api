"""Read-only HTTPS smoke test for the extracted Windows bundle. No SCM changes."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import secrets
import re
import socket
import ssl
import subprocess
from tempfile import TemporaryDirectory
from threading import Barrier
import time
from urllib.request import urlopen

import pyodbc

from app.core.machine_secret import save
from app.core.security import hash_secret
from tools.compare_sql_clients import TLS_FAILURE, category
from tools.demo_config import connection_string, require
from tools.run_concurrent_demo import post
from tools.run_flutter_windows_pilot import certificates
from tools.run_phase6_demo import REFERENCES, multiset, sql_reference


def check_bundle(executable, connection, reference):
    devices = {f"pilot-{i}": secrets.token_urlsafe(32) for i in range(6)}
    with TemporaryDirectory(prefix="zencillo-bundle-smoke-") as tmp:
        root = Path(tmp)
        certificates(root)
        (root / "server.pem").rename(root / "server-chain.pem")
        (root / "server.key").rename(root / "server-key.pem")
        save(root / "jwt.dpapi", secrets.token_urlsafe(48))
        save(root / "sql.dpapi", connection)
        tls = ssl.create_default_context(cafile=str(root / "ca.pem"))
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
        config = root / "service.json"
        config.write_text(json.dumps({
            "listen": "127.0.0.1", "port": port, "station": "demo-bundle",
            "devices": {key: {"secret_hash": hash_secret(secret), "operations": list(REFERENCES)}
                        for key, secret in devices.items()},
        }), encoding="utf8")
        command = [str(executable), "-B", "-I", "-m", "app.station_service", "--config", str(config)]
        subprocess.run([*command, "--check"], cwd=root, check=True, capture_output=True, timeout=15)
        jwt_tokens = []
        failed = False
        trace = root / "service.stderr"
        for attempt in range(2):
            with trace.open("wb") as errors, subprocess.Popen(
                command, cwd=root, stdout=subprocess.DEVNULL, stderr=errors,
                creationflags=subprocess.CREATE_NO_WINDOW,
            ) as server:
                try:
                    deadline = time.monotonic() + 15
                    while server.poll() is None and time.monotonic() < deadline:
                        try:
                            with urlopen(f"https://127.0.0.1:{port}/healthz", context=tls, timeout=1) as response:
                                if json.load(response) == {"status": "ok"}:
                                    break
                        except OSError:
                            time.sleep(0.1)
                    else:
                        raise RuntimeError("El ejecutor HTTPS del paquete no respondió.")
                    if attempt == 0:
                        for device, secret in devices.items():
                            status, result = post(port, tls, "/v1/auth/token", {"device_id": device, "secret": secret})
                            if status != 200:
                                raise RuntimeError(f"Autenticación HTTP {status}")
                            jwt_tokens.append(result["data"]["access_token"])
                        if len(set(jwt_tokens)) != len(devices):
                            raise RuntimeError("JWT duplicados.")
                    jobs = [(name, token) for name in reference for token in jwt_tokens]

                    def verify(job):
                        name, token = job
                        status, result = post(port, tls, "/v1/operations", {"Query": name, "parameters": {}}, token)
                        if status != 200:
                            return f"HTTP {status}"
                        return "equivalente" if multiset(result["data"]["items"]) == reference[name] else "diferente"

                    normal = Counter()
                    with ThreadPoolExecutor(max_workers=len(devices)) as pool:
                        for name in reference:
                            normal.update(pool.map(verify, [(name, token) for token in jwt_tokens]))
                    ready = Barrier(len(jobs))

                    def burst(job):
                        ready.wait(timeout=10)
                        return verify(job)

                    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
                        stress = Counter(pool.map(burst, jobs))
                    expected = {"equivalente": len(jobs)}
                    failed |= normal != expected or stress != expected
                    print(f"Arranque {attempt + 1}: seis clientes={dict(normal)}; ráfaga simultánea={dict(stress)}.")
                finally:
                    if server.poll() is None:
                        server.terminate()
                        server.wait(timeout=8)
            sanitized = Counter(re.findall(
                r"ODBC stage=(connect|cursor|execute|fetch) sqlstate=([A-Z0-9]{5}|UNKNOWN)",
                trace.read_text(encoding="utf8", errors="replace"),
            ))
            if sanitized:
                print(f"ODBC diagnóstico: {dict(sanitized)}")
        print(f"Sesiones JWT independientes: {len(jwt_tokens)}; conteos SQL: " +
              ", ".join(f"{name}={sum(rows.values())}" for name, rows in reference.items()))
        return not failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    args = parser.parse_args()
    user, password = require()
    connection = connection_string(user, password)
    try:
        reference = sql_reference(connection)
    except pyodbc.Error as exc:
        if not args.allow_demo_sql_exception or category(exc) != TLS_FAILURE:
            raise SystemExit("SQL DEMO no respondió con TLS verificado.") from None
        print("SQL DEMO: excepción autorizada para ODBC. HTTPS conserva validación.")
        connection = connection_string(user, password, verify=False)
        try:
            reference = sql_reference(connection)
        except pyodbc.Error:
            raise SystemExit("SQL DEMO no disponible.") from None
    return 0 if check_bundle(args.bundle.resolve() / "runtime" / "python.exe", connection, reference) else 2


if __name__ == "__main__":
    raise SystemExit(main())
