"""Run native Windows and the dedicated Android emulator against one HTTPS API."""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
from tempfile import TemporaryDirectory
import time

import pyodbc

from app.config import Device, Settings
from app.core.security import hash_secret
from tools import flutter_android_fixture as android
from tools.compare_sql_clients import TLS_FAILURE, category
from tools.demo_config import connection_string, require
from tools.run_flutter_windows_pilot import FLUTTER, TestServer, certificates, wait_file
from tools.run_phase6_demo import REFERENCES, sql_reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    args = parser.parse_args()
    user, password = require()
    connection = connection_string(user, password)
    try:
        reference = sql_reference(connection)
    except pyodbc.Error as error:
        if not args.allow_demo_sql_exception or category(error) != TLS_FAILURE:
            raise SystemExit("SQL DEMO no disponible con TLS verificado.") from None
        print("Excepción TLS solo para SQL DEMO; ambos clientes validan HTTPS.", flush=True)
        connection = connection_string(user, password, verify=False)
        try:
            reference = sql_reference(connection)
        except pyodbc.Error:
            raise SystemExit("No se pudo leer SQL DEMO.") from None
    flutter = shutil.which("flutter.bat")
    if not flutter:
        raise SystemExit("Flutter no está disponible.")
    subprocess.run([flutter, "build", "apk", "--debug", "--no-pub", "--flavor", "pos",
                    "-t", "integration_test/local_api_android_probe.dart"],
                   cwd=FLUTTER, check=True)
    key_windows = secrets.token_urlsafe(32)
    key_android = secrets.token_urlsafe(32)
    settings = Settings(
        jwt_key=secrets.token_urlsafe(48), station="demo-windows",
        connection_string=connection, token_seconds=8,
        devices={name: Device(station="demo-windows", secret_hash=hash_secret(secret),
                              operations=set(REFERENCES))
                 for name, secret in (("windows-pilot", key_windows), ("android-pilot", key_android))},
    )
    with TemporaryDirectory(prefix="zencillo-two-clients-") as directory:
        folder = Path(directory)
        certificates(folder)
        issued_at = int(time.time()) - 300
        rows = {name: [json.loads(row) for row in entries.elements()]
                for name, entries in reference.items()}
        (folder / "expected.json").write_text(json.dumps(rows), encoding="utf8")
        (folder / "group").touch()
        server = TestServer(settings, folder)
        process = None
        android_installed = False
        try:
            server.start()
            (folder / "origin.txt").write_text(f"https://127.0.0.1:{server.port}", encoding="ascii")
            android_folder = folder / "android"
            android_folder.mkdir()
            for name in ("ca.pem", "expected.json"):
                shutil.copyfile(folder / name, android_folder / name)
            (android_folder / "origin.txt").write_text(f"https://10.0.2.2:{server.port}", encoding="ascii")
            android_installed = True
            android.prepare(android_folder, key_android)
            android.send("group", b"ok")
            android.wait_for_certificate_clock(issued_at)
            process = subprocess.Popen(
                [flutter, "test", "--no-pub", "-d", "windows", "integration_test/local_api_platform_test.dart"],
                cwd=FLUTTER, env={**os.environ, "ZENC_LOCAL_API_PILOT": str(folder),
                                 "ZENC_LOCAL_API_PILOT_SECRET": key_windows},
            )
            wait_file(lambda: (folder / "group.ready").is_file(), process)
            android.launch()
            wait_file(lambda: android.exists("group.ready"), process, android.failure, timeout=30)

            def signal(name):
                (folder / name).touch()
                android.send(name, b"ok")

            def wait_both(name):
                wait_file(lambda: (folder / name).is_file() and android.exists(name),
                          process, android.failure, timeout=35)

            signal("group.start")
            wait_both("restart.request")
            old_port = server.port
            server.close()
            signal("offline.ready")
            wait_both("offline.checked")
            server = TestServer(replace(settings, jwt_key=secrets.token_urlsafe(48)), folder, old_port)
            server.start()
            signal("restart.ready")
            wait_file(lambda: android.exists("pilot.passed"), None, android.failure, timeout=25)
            if process.wait(timeout=30):
                raise RuntimeError("La prueba de Windows devolvió un error.")
            print("Windows nativo y Android emulado: misma API, perfiles JWT distintos, catálogos equivalentes, batch y recuperación aprobados.")
        finally:
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            if android_installed:
                android.clean()
            server.close()


if __name__ == "__main__":
    main()
