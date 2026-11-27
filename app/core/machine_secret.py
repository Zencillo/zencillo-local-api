"""DPAPI machine scope for files readable only by the service and administrators."""
import ctypes as ct
from ctypes import wintypes as wt
import os
from pathlib import Path
import tempfile


class Blob(ct.Structure):
    _fields_ = [("size", wt.DWORD), ("data", ct.POINTER(ct.c_ubyte))]


def transform(data: bytes, *, protect: bool) -> bytes:
    if not data:
        raise ValueError("Secret input is empty.")
    crypt = ct.WinDLL("crypt32", use_last_error=True)
    kernel = ct.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ct.c_void_p]
    kernel.LocalFree.restype = ct.c_void_p
    buffer = (ct.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    target = Blob()
    operation = crypt.CryptProtectData if protect else crypt.CryptUnprotectData
    operation.argtypes = [
        ct.POINTER(Blob), ct.c_void_p, ct.POINTER(Blob), ct.c_void_p,
        ct.c_void_p, wt.DWORD, ct.POINTER(Blob),
    ]
    operation.restype = wt.BOOL
    try:
        # CRYPTPROTECT_UI_FORBIDDEN and, when encrypting, CRYPTPROTECT_LOCAL_MACHINE.
        if not operation(ct.byref(source), None, None, None, None,
                         5 if protect else 1, ct.byref(target)):
            raise OSError(f"DPAPI error {ct.get_last_error()}")
        return ct.string_at(target.data, target.size)
    finally:
        ct.memset(buffer, 0, len(data))
        if target.data:
            ct.memset(target.data, 0, target.size)
            kernel.LocalFree(target.data)


def save(path: Path, secret: str) -> None:
    encrypted = transform(secret.encode("utf-8"), protect=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            temp.write(encrypted)
            temp.flush()
            os.fsync(temp.fileno())
            temp.close()
            temporary.replace(path)
        finally:
            temp.close()
            temporary.unlink(missing_ok=True)


def read(path: Path) -> str:
    return transform(path.read_bytes(), protect=False).decode("utf-8")
