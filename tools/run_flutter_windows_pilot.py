"""Isolated Flutter to FastAPI TLS pilot. Does not change trust stores."""
import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
from threading import Thread
import time

import pyodbc
import uvicorn

from app.config import Device, Settings
from app.main import create_app
from app.core.security import hash_secret
from tools.compare_sql_clients import TLS_FAILURE, category, sanitize
from tools import flutter_android_fixture as android
from tools.demo_config import connection_string, require
from tools.run_phase6_demo import REFERENCES, sql_reference

FLUTTER = Path("C:/dev/capturador_mobile")
OPENSSL = Path("C:/Program Files/Git/usr/bin/openssl.exe")


def certificates(folder):
    def run(*args):
        subprocess.run([str(OPENSSL), *args], cwd=folder, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    not_before = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y%m%d%H%M%SZ")
    run("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
        "-not_before", not_before,
        "-subj", "/CN=Zencillo isolated pilot CA", "-keyout", "ca.key", "-out", "ca.pem",
        "-addext", "basicConstraints=critical,CA:TRUE")
    run("req", "-new", "-newkey", "rsa:2048", "-nodes", "-subj", "/CN=127.0.0.1",
        "-keyout", "server.key", "-out", "server.csr")
    (folder / "extensions.cnf").write_text(
        "subjectAltName=IP:127.0.0.1,IP:10.0.2.2\nextendedKeyUsage=serverAuth\nbasicConstraints=CA:FALSE\n",
        encoding="ascii",
    )
    run("x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
        "-CAcreateserial", "-days", "1", "-not_before", not_before,
        "-extfile", "extensions.cnf", "-out", "server.pem")


def wait_file(exists, process, failure=None, timeout=300):
    deadline = time.monotonic() + timeout
    while not exists():
        if failure and (stage := failure()):
            raise RuntimeError(f"El verificador Android falló en {stage}.")
        if (process and process.poll() is not None) or time.monotonic() >= deadline:
            raise RuntimeError("El cliente no confirmó una etapa del piloto.")
        time.sleep(0.25)


class TestServer:
    def __init__(self, settings, folder, port=0, *, connect=None):
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", port))
        self.port = self.sock.getsockname()[1]
        self.server = uvicorn.Server(uvicorn.Config(
            create_app(settings, connect=connect),
            access_log=False, timeout_keep_alive=20, log_level="critical",
            ssl_certfile=str(folder / "server.pem"), ssl_keyfile=str(folder / "server.key"),
        ))
        self.worker = Thread(target=self.server.run, kwargs={"sockets": [self.sock]}, daemon=True)

    def start(self):
        self.worker.start()
        deadline = time.monotonic() + 8
        while not self.server.started and self.worker.is_alive() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not self.server.started:
            raise RuntimeError("FastAPI temporal no inició.")

    def close(self):
        self.server.should_exit = True
        self.worker.join(timeout=5)
        self.sock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    platform = parser.add_mutually_exclusive_group()
    platform.add_argument("--native-windows", action="store_true")
    platform.add_argument("--android", action="store_true")
    args = parser.parse_args()
    user, password = require()
    connection = connection_string(user, password)
    try:
        reference = sql_reference(connection)
        print("SQL DEMO: certificado validado.")
    except pyodbc.Error as error:
        if not args.allow_demo_sql_exception or category(error) != TLS_FAILURE:
            raise SystemExit("No se pudo abrir SQL DEMO con TLS validado.") from None
        connection = connection_string(user, password, verify=False)
        print("SQL ODBC DEMO: excepción autorizada. Flutter HTTPS conserva validación.")
        try:
            reference = sql_reference(connection)
        except pyodbc.Error as retry:
            raise SystemExit(f"SQL DEMO: {sanitize(retry, user, password)}") from None
    def diagnostic_connect(*args, **kwargs):
        try:
            return pyodbc.connect(*args, **kwargs)
        except pyodbc.Error as exc:
            print(f"ODBC del backend piloto: {sanitize(exc, user, password)}", flush=True)
            raise

    credentials = secrets.token_urlsafe(32)
    device_id = "android-pilot" if args.android else "windows-pilot"
    settings = Settings(
        jwt_key=secrets.token_urlsafe(48), connection_string=connection,
        station="demo-windows", token_seconds=8,
        devices={device_id: Device(station="demo-windows",
            secret_hash=hash_secret(credentials), operations=set(REFERENCES))},
    )
    with tempfile.TemporaryDirectory(prefix="zencillo-https-pilot-") as tmp:
        folder = Path(tmp)
        certificates(folder)
        issued_at = int(time.time()) - 300
        for name, rows in reference.items():
            print(f"{name}: SQL referencia {sum(rows.values())} filas")
        fixtures = {name: [json.loads(row) for row in rows.elements()] for name, rows in reference.items()}
        (folder / "expected.json").write_text(json.dumps(fixtures), encoding="utf-8")
        server = TestServer(settings, folder, connect=diagnostic_connect)
        process = None
        try:
            server.start()
            host = "10.0.2.2" if args.android else "127.0.0.1"
            (folder / "origin.txt").write_text(f"https://{host}:{server.port}", encoding="ascii")
            flutter = shutil.which("flutter.bat")
            if not flutter:
                raise RuntimeError("Flutter no está disponible.")
            if args.android:
                subprocess.run(
                    [flutter, "build", "apk", "--debug", "--no-pub", "--flavor", "pos",
                     "-t", "integration_test/local_api_android_probe.dart"],
                    cwd=FLUTTER, check=True,
                )
                android.prepare(folder, credentials)
                android.wait_for_certificate_clock(issued_at)
                android.launch()
            elif args.native_windows:
                flutter_args = ["-d", "windows", "integration_test/local_api_platform_test.dart"]
            else:
                flutter_args = ["test/core/local_api_tls_live_test.dart"]

            def exists(name):
                return android.exists(name) if args.android else (folder / name).exists()

            def signal(name):
                if args.android:
                    android.send(name, b"ok")
                else:
                    (folder / name).touch()

            if not args.android:
                process = subprocess.Popen(
                    [flutter, "test", "--no-pub", *flutter_args],
                    cwd=FLUTTER, env={**os.environ, "ZENC_LOCAL_API_PILOT": str(folder),
                                      "ZENC_LOCAL_API_PILOT_SECRET": credentials},
                )
            failure = android.failure if args.android else None
            wait_file(lambda: exists("restart.request"), process, failure,
                      timeout=120 if args.android else 300)
            port = server.port
            server.close()
            signal("offline.ready")
            wait_file(lambda: exists("offline.checked"), process, failure)
            server = TestServer(replace(settings, jwt_key=secrets.token_urlsafe(48)), folder, port,
                                connect=diagnostic_connect)
            server.start()
            signal("restart.ready")
            if args.android:
                wait_file(lambda: exists("pilot.passed"), None, failure, timeout=30)
            elif process.wait(timeout=30):
                raise RuntimeError("La prueba Flutter devolvió un error.")
            platform = "Android emulado" if args.android else "Windows nativo" if args.native_windows else "Windows host Dart"
            print(f"{platform}: HTTPS, cuatro lecturas y batch, renovacion, red y reinicio aprobados.")
        finally:
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
            if args.android:
                android.clean()
            server.close()


if __name__ == "__main__":
    main()
