"""Inspect TLS during SQL Server PRELOGIN, without issuing LOGIN7."""
import hashlib
import socket
import ssl
import struct
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.compare_sql_clients import HOST, PORT

PRELOGIN = bytes.fromhex("00 000b 0006 01 0011 0001 ff 000000000000 01")


def read_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("El servidor cerró el socket durante PRELOGIN.")
        data.extend(chunk)
    return bytes(data)


def receive(sock):
    while True:
        kind, status, length, _, _, _ = struct.unpack("!BBHHBB", read_exact(sock, 8))
        if kind not in (4, 18) or length < 8:
            raise ValueError(f"Respuesta TDS inesperada: tipo={kind}, longitud={length}")
        yield read_exact(sock, length - 8)
        if status & 1:
            return


def send(sock, data):
    chunks = [data[i:i + 4088] for i in range(0, len(data), 4088)]
    for i, chunk in enumerate(chunks):
        sock.sendall(struct.pack("!BBHHBB", 18, int(i == len(chunks) - 1), len(chunk) + 8,
                                 0, (i + 1) % 256, 0) + chunk)


def handshake(context):
    incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
    tls = context.wrap_bio(incoming, outgoing, server_hostname=HOST)
    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        send(sock, PRELOGIN)
        reply = b"".join(receive(sock))
        encryption = None
        for i in range(0, len(reply) - 4, 5):
            if reply[i] == 255:
                break
            token, offset, length = struct.unpack_from("!BHH", reply, i)
            if token == 1 and length == 1 and offset < len(reply):
                encryption = reply[offset]
                break
        if encryption is None:
            raise ValueError("PRELOGIN no devolvió opción de cifrado.")
        if encryption not in (1, 3):
            raise ValueError(f"El servidor no negoció cifrado completo: {encryption}.")
        for _ in range(12):
            try:
                tls.do_handshake()
                return tls.version(), tls.getpeercert(binary_form=True)
            except ssl.SSLWantReadError:
                pending = outgoing.read()
                if pending:
                    send(sock, pending)
                for payload in receive(sock):
                    incoming.write(payload)
        raise TimeoutError("La negociación superó el límite de intercambios TLS.")


def main():
    strict = ssl.create_default_context()
    strict.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        version, der = handshake(strict)
        print(f"TLS verificado con la IP y el almacén de Python: {version}")
    except (OSError, ValueError) as exc:
        print(f"TLS estricto (Python, sin login): {type(exc).__name__}: {exc}")
        inspect = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        inspect.minimum_version = ssl.TLSVersion.TLSv1_2
        inspect.check_hostname = False
        inspect.verify_mode = ssl.CERT_NONE
        try:
            version, der = handshake(inspect)
        except (OSError, ValueError) as exc:
            raise SystemExit(f"No se pudo obtener certificado: {type(exc).__name__}: {exc}") from None
        print(f"TLS {version}: certificado observado sin autenticar el servidor; no se enviaron credenciales.")
    with TemporaryDirectory() as tmp:
        pem = Path(tmp) / "observed.pem"
        pem.write_text(ssl.DER_cert_to_PEM_cert(der), encoding="ascii")
        cert = ssl._ssl._test_decode_cert(str(pem))
    print(f"SHA-256: {hashlib.sha256(der).hexdigest()}")
    for field in ("subject", "issuer", "subjectAltName", "notBefore", "notAfter"):
        print(f"{field}: {cert.get(field, '(ausente)')}")


if __name__ == "__main__":
    main()
