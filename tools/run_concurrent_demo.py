"""Exercise independent device sessions concurrently on one read-only DEMO API."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http.client import HTTPSConnection
import json
import secrets
import socket
import ssl
import tempfile
from pathlib import Path
from threading import Barrier, Thread
import time

import pyodbc
import uvicorn

from app.config import Device, Settings
from app.core.security import hash_secret
from app.main import create_app
from tools.compare_sql_clients import TLS_FAILURE, category
from tools.demo_config import connection_string, require
from tools.run_flutter_windows_pilot import certificates
from tools.run_phase6_demo import REFERENCES, multiset, sql_reference


def post(port, tls, endpoint, data, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with closing(HTTPSConnection("127.0.0.1", port, timeout=20, context=tls)) as connection:
        connection.request("POST", endpoint, json.dumps(data), headers)
        with closing(connection.getresponse()) as response:
            return response.status, json.load(response)


def run(connection, reference, clients, rounds):
    secrets_by_id = {f"device-{index}": secrets.token_urlsafe(32) for index in range(clients)}
    settings = Settings(
        jwt_key=secrets.token_urlsafe(48), station="demo",
        connection_string=connection,
        devices={key: Device(station="demo", operations=set(REFERENCES),
                             secret_hash=hash_secret(value))
                 for key, value in secrets_by_id.items()},
    )
    with tempfile.TemporaryDirectory(prefix="zencillo-concurrency-") as tmp, socket.socket() as sock:
        folder = Path(tmp)
        certificates(folder)
        tls = ssl.create_default_context(cafile=str(folder / "ca.pem"))
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(create_app(settings), access_log=False, log_level="critical",
                                               ssl_certfile=str(folder / "server.pem"),
                                               ssl_keyfile=str(folder / "server.key")))
        worker = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and worker.is_alive() and time.monotonic() < deadline:
                time.sleep(0.05)
            if not server.started:
                raise RuntimeError("FastAPI no inició.")
            with ThreadPoolExecutor(max_workers=clients * len(REFERENCES)) as pool:
                jobs = {key: pool.submit(post, port, tls, "/v1/auth/token",
                        {"device_id": key, "secret": value}) for key, value in secrets_by_id.items()}
                tokens = []
                for job in jobs.values():
                    status, body = job.result()
                    if status != 200:
                        raise RuntimeError(f"Autenticación HTTP {status}")
                    tokens.append(body["data"]["access_token"])
                if len(set(tokens)) != clients:
                    raise RuntimeError("JWT duplicados entre dispositivos.")
                counts = Counter()
                for _ in range(rounds):
                    barrier = Barrier(clients * len(REFERENCES))
                    def read(token, name):
                        barrier.wait(timeout=10)
                        status, body = post(port, tls, "/v1/operations", {"Query": name, "parameters": {}}, token)
                        if status != 200:
                            return f"HTTP {status}"
                        return "equivalente" if multiset(body["data"]["items"]) == reference[name] else "diferente"
                    reads = [pool.submit(read, token, name) for token in tokens for name in REFERENCES]
                    counts.update(job.result() for job in reads)
                print(f"JWT distintos={len(tokens)}; rondas={rounds}; resultados={dict(counts)}")
                return counts == {"equivalente": clients * len(REFERENCES) * rounds}
        finally:
            server.should_exit = True
            worker.join(timeout=10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    parser.add_argument("--clients", type=int, choices=range(2, 9), default=4)
    parser.add_argument("--rounds", type=int, choices=range(1, 11), default=3)
    args = parser.parse_args()
    user, password = require()
    connection = connection_string(user, password)
    try:
        reference = sql_reference(connection)
    except pyodbc.Error as exc:
        if not args.allow_demo_sql_exception or category(exc) != TLS_FAILURE:
            raise SystemExit("Falló SQL DEMO con TLS estricto.") from None
        connection = connection_string(user, password, verify=False)
        print("Excepción TLS autorizada únicamente hacia SQL DEMO.")
        try:
            reference = sql_reference(connection)
        except pyodbc.Error:
            raise SystemExit("No se pudo leer SQL DEMO.") from None
    return 0 if run(connection, reference, args.clients, args.rounds) else 2


if __name__ == "__main__":
    raise SystemExit(main())
