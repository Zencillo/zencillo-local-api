"""Compare read-only SQL DEMO and HTTPS using the development or extracted runtime."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import secrets
import socket
import ssl
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Barrier
from time import monotonic, sleep
from urllib.request import urlopen

import pyodbc

from app.core.database import odbc_failure
from app.core.machine_secret import save
from app.core.security import hash_secret
from tools.demo_config import connection_string, require
from tools.run_concurrent_demo import post
from tools.run_flutter_windows_pilot import certificates
from tools.run_phase6_demo import REFERENCES, multiset, sql_reference

SAFE_TRACE = re.compile(
    r"ODBC stage=(?:connect|cursor|execute|fetch) sqlstate=[A-Z0-9]{5,7}"
    r"(?: request_id=(?:[a-f0-9]{32}|-) operation=(?:ListarTiposVehiculo|ListarTiposGasto|"
    r"ListarConfiguracionRedondeo|ListarCombustibles|-) connect_ms=\d+ elapsed_ms=\d+ "
    r"active_at_start=\d+ active=\d+ category=[a-z_]+ native=(?:-?\d+|-))?(?=\r?$)",
    re.MULTILINE,
)


def scenario(pool_size, waves, verify, *, pause=0):
    results = Counter()
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        for jobs in waves:
            barrier = Barrier(len(jobs))

            def read(job):
                barrier.wait(timeout=12)
                return verify(*job)

            results.update(executor.map(read, jobs))
            if pause:
                sleep(pause)
    return dict(results)


def run(executable, connection, reference, rounds, report, replay_phase10):
    devices = {f"pilot-{i}": secrets.token_urlsafe(32) for i in range(6)}
    names = list(reference)
    with TemporaryDirectory(prefix="zencillo-odbc-acceptance-") as tmp:
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
            "listen": "127.0.0.1", "port": port, "station": "demo-odbc",
            "devices": {device: {"secret_hash": hash_secret(secret), "operations": names}
                        for device, secret in devices.items()},
        }), encoding="utf8")
        is_dev = executable is None
        command = [sys.executable if is_dev else str(executable), "-B"]
        if not is_dev:
            command.append("-I")
        command.extend(("-m", "app.station_service", "--config", str(config)))
        cwd = Path(__file__).resolve().parents[1] if is_dev else root
        unexpected = 0
        for start in (1, 2):
            trace = root / "service.stderr"
            with trace.open("wb") as errors, subprocess.Popen(
                command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=errors,
                creationflags=subprocess.CREATE_NO_WINDOW,
            ) as server:
                try:
                    deadline = monotonic() + 15
                    while server.poll() is None and monotonic() < deadline:
                        try:
                            with urlopen(f"https://127.0.0.1:{port}/healthz", context=tls, timeout=1) as http:
                                if json.load(http) == {"status": "ok"}:
                                    break
                        except OSError:
                            sleep(.1)
                    else:
                        raise RuntimeError("El ejecutor HTTPS no inició.")
                    tokens = []
                    for device, secret in devices.items():
                        status, body = post(port, tls, "/v1/auth/token", {"device_id": device, "secret": secret})
                        if status != 200:
                            raise RuntimeError(f"Autenticación HTTP {status}")
                        tokens.append(body["data"]["access_token"])
                    if len(set(tokens)) != 6:
                        raise RuntimeError("Los JWT no son independientes.")

                    def verify(token, name):
                        try:
                            status, body = post(port, tls, "/v1/operations", {"Query": name, "parameters": {}}, token)
                            if status != 200:
                                return f"HTTP {status}"
                            return "equivalente" if multiset(body["data"]["items"]) == reference[name] else "diferente"
                        except OSError:
                            return "transporte HTTPS"

                    def jobs(n, wave):
                        return [(token, names[(index + wave) % len(names)]) for index, token in enumerate(tokens[:n])]

                    cases = [("individual", 1, 1, 0), ("secuencial", 1, 12, 0),
                             ("dos", 2, 12, 0), ("seis", 6, 8, 0),
                             ("rafagas", 6, 8, .20)]
                    if rounds:
                        cases.append(("aceptacion", 6, rounds * len(names), .01))
                    results = {}
                    for name, clients, waves, pause in cases:
                        results[name] = scenario(clients, (jobs(clients, w) for w in range(waves)), verify, pause=pause)
                        unexpected += sum(count for status, count in results[name].items() if status != "equivalente")
                        print(f"Arranque {start} | {name} | {results[name]}", flush=True)
                    if replay_phase10:
                        replay = {
                            "seis_mismo_catalogo": scenario(
                                6, ([(token, name) for token in tokens] for name in names), verify,
                            ),
                            "rafaga_24": scenario(24, [[(name_token, name) for name in names
                                                       for name_token in tokens]], verify),
                        }
                        for name, summary in replay.items():
                            results[name] = summary
                            unexpected += sum(count for label, count in summary.items() if label != "equivalente")
                            print(f"Arranque {start} | {name} | {summary}", flush=True)
                    with urlopen(f"https://127.0.0.1:{port}/healthz", context=tls, timeout=3) as http:
                        health = json.load(http)
                    if health != {"status": "ok"}:
                        raise RuntimeError("El servicio no respondió tras la carga.")
                finally:
                    if server.poll() is None:
                        server.terminate()
                        server.wait(timeout=8)
            failures = [match.group() for match in SAFE_TRACE.finditer(trace.read_text(encoding="utf8", errors="replace"))]
            report["starts"].append({"start": start, "devices": 6, "results": results, "health": health, "odbc": failures})
            print(f"Arranque {start} | ODBC: {len(failures)} eventos; estado final OK", flush=True)
    return 0 if not unexpected else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--rounds", type=int, choices=range(0, 26), default=22)
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    parser.add_argument("--replay-phase10", action="store_true")
    args = parser.parse_args()
    user, password = require()
    strict = connection_string(user, password)
    connection = strict
    report = {"runtime": "extraido" if args.bundle else "desarrollo", "starts": []}
    try:
        reference = sql_reference(strict)
    except pyodbc.Error as exc:
        sqlstate, kind, native = odbc_failure(exc)
        report["strict_failure"] = {"sqlstate": sqlstate, "category": kind, "native": native}
        print(f"SQL DEMO estricto: {sqlstate} {kind} {native}", flush=True)
        if not args.allow_demo_sql_exception or kind not in {"certificate", "certificate_trust", "certificate_identity"}:
            args.report.write_text(json.dumps(report, indent=2), encoding="utf8")
            return 2
        report["demo_certificate_exception"] = True
        connection = connection_string(user, password, verify=False)
        try:
            reference = sql_reference(connection)
        except pyodbc.Error as retry:
            report["demo_reference_failure"] = odbc_failure(retry)
            print(f"No se obtuvo la referencia SQL: {report['demo_reference_failure']}", flush=True)
            args.report.write_text(json.dumps(report, indent=2), encoding="utf8")
            return 2
    report["reference_counts"] = {name: sum(rows.values()) for name, rows in reference.items()}
    try:
        return run(args.bundle.resolve() / "runtime" / "python.exe" if args.bundle else None,
                   connection, reference, args.rounds, report, args.replay_phase10)
    finally:
        args.report.write_text(json.dumps(report, indent=2), encoding="utf8")


if __name__ == "__main__":
    raise SystemExit(main())
