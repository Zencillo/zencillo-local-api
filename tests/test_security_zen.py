import base64
import json

import pytest
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.core.security_zen import SecurityZenError, read_security_zen, station_profile

KEY = b"0123456789abcdef"


def test_legacy_compatibility_and_fixed_server_parsing(tmp_path):
    fixture = {"user":"fixture", "pass":"conto}", "server":"fixture.local,1544", "type":"MSSQL",
               "date":"2026-11-26T12:00:00", "database":"Station"}
    pad = padding.PKCS7(128).padder()
    cipher = Cipher(algorithms.AES(KEY), modes.ECB()).encryptor()
    data = cipher.update(pad.update(json.dumps(fixture).encode())+pad.finalize()) + cipher.finalize()
    encoded = base64.b64encode(data).decode()
    path = tmp_path / "AUTOMATIZACION.security_zen"
    path.write_text(encoded[:12] + " \r\n" + encoded[12:], encoding="utf-8")
    profile = station_profile(read_security_zen(path, KEY), "1/2/3")
    assert (profile.server, profile.port, profile.user, profile.database) == ("fixture.local",1544,"fixture","Station")


@pytest.mark.parametrize("payload", [None, b"not-a-file!", bytes(65537), b"AAAA"],
                         ids=["missing", "invalid_base64", "oversized", "invalid_ciphertext"])
def test_missing_and_invalid_file_fail_closed(tmp_path, payload):
    path = tmp_path / "AUTOMATIZACION.security_zen"
    if payload is not None:
        path.write_bytes(payload)
    with pytest.raises(SecurityZenError):
        read_security_zen(path, KEY)
