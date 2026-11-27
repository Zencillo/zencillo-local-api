"""Authorized, one-use LAN import, separate from the operational FastAPI service."""
import argparse
import ctypes
import getpass
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import ipaddress
import json
from pathlib import Path
import re
import ssl
import sys
import time

from app.core.machine_secret import save
from app.install_station_sql import MAX_PAYLOAD, install


def receive(directory, port, source, station, invitation, replace=False, *, timeout=300):
    values = json.loads((directory / "service.json").read_text(encoding="utf-8-sig"))
    address = ipaddress.IPv4Address(values["listen"])
    peer = ipaddress.IPv4Address(source)
    network = ipaddress.IPv4Network(values["subnet"], strict=False)
    profile = directory / "sql.dpapi"
    if (not address.is_private or address.is_loopback or address not in network
            or peer not in network or port == values["port"]
            or not (directory / "jwt.dpapi").is_file() or (profile.exists() and not replace)):
        raise ValueError("Transferencia no permitida para esta configuración.")

    return _receive(directory, address, port, peer, station, invitation, timeout)


def _receive(directory, address, port, peer, station, invitation, timeout):
    profile = directory / "sql.dpapi"
    deadline = time.monotonic() + timeout
    accepted = None

    class ImportHandler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            return

        def setup(self):
            self.request.settimeout(5)
            super().setup()

        def do_POST(self):
            nonlocal accepted
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if (self.path != "/import" or not 0 < length <= MAX_PAYLOAD
                    or time.monotonic() >= deadline
                    or not hmac.compare_digest(
                        self.headers.get("Authorization", "").encode("utf8"),
                        ("Bearer " + invitation).encode("ascii"),
                    )):
                if 0 < length <= MAX_PAYLOAD:
                    self.rfile.read(length)
                self.send_error(403)
                return
            # A valid invitation is consumed even if validation subsequently fails.
            accepted = False
            try:
                def store(_user, connection, **_):
                    save(profile, connection)
                install(self.rfile.read(length), station, store=store, verify_service_access=True)
                accepted = True
            except Exception:
                self.send_error(422, "Perfil SQL no validado")
                return
            self.send_response(204)
            self.end_headers()

    class ImportServer(HTTPServer):
        def verify_request(self, _request, client_address):
            return client_address[0] == str(peer)

        def get_request(self):
            connection, client = self.socket.accept()
            try:
                if client[0] != str(peer):
                    raise ConnectionAbortedError
                connection.settimeout(5)
                return context.wrap_socket(connection, server_side=True), client
            except OSError:
                connection.close()
                raise

        def handle_error(self, *_):
            print("Error de receptor:", type(sys.exc_info()[1]).__name__, file=sys.stderr)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(directory / "server-chain.pem", directory / "server-key.pem")
    with ImportServer((str(address), port), ImportHandler) as server:
        server.timeout = 1
        while accepted is None and time.monotonic() < deadline:
            server.handle_request()
    return accepted is True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--source", required=True, help="IPv4 del Capturador autorizado")
    parser.add_argument("--confirm-station", required=True, help="compañía/centro/isla confirmada")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if (sys.platform != "win32" or not ctypes.windll.shell32.IsUserAnAdmin()
            or not 1 <= args.port <= 65535 or not sys.stdin.isatty()):
        return 2
    invitation = getpass.getpass("Invite aleatoria de un solo uso (32-128 caracteres URL-safe): ")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{32,128}", invitation):
        return 2
    try:
        return 0 if receive(args.directory.resolve(), args.port, args.source,
                            args.confirm_station, invitation, args.replace) else 1
    except (ValueError, OSError, KeyError):
        print("No se pudo iniciar o completar la transferencia autorizada.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
