import ctypes as ct
from ctypes import wintypes as wt

GENERIC = 1
PERSIST_LOCAL_MACHINE = 2
NOT_FOUND = 1168


class Credential(ct.Structure):
    _fields_ = [
        ("Flags", wt.DWORD), ("Type", wt.DWORD), ("TargetName", wt.LPWSTR),
        ("Comment", wt.LPWSTR), ("LastWritten", wt.FILETIME),
        ("CredentialBlobSize", wt.DWORD), ("CredentialBlob", ct.POINTER(wt.BYTE)),
        ("Persist", wt.DWORD), ("AttributeCount", wt.DWORD), ("Attributes", ct.c_void_p),
        ("TargetAlias", wt.LPWSTR), ("UserName", wt.LPWSTR),
    ]


def _api():
    api = ct.WinDLL("Advapi32.dll", use_last_error=True)
    api.CredReadW.argtypes = (wt.LPCWSTR, wt.DWORD, wt.DWORD, ct.POINTER(ct.POINTER(Credential)))
    api.CredReadW.restype = wt.BOOL
    api.CredWriteW.argtypes = (ct.POINTER(Credential), wt.DWORD)
    api.CredWriteW.restype = wt.BOOL
    api.CredFree.argtypes = (ct.c_void_p,)
    api.CredFree.restype = None
    return api


def read(*, target):
    api = _api()
    pointer = ct.POINTER(Credential)()
    if not api.CredReadW(target, GENERIC, 0, ct.byref(pointer)):
        code = ct.get_last_error()
        if code == NOT_FOUND:
            return None
        raise OSError(f"Credential Manager no pudo leer la entrada local (Win32 {code}).")
    try:
        credential = pointer.contents
        return credential.UserName, ct.string_at(
            credential.CredentialBlob, credential.CredentialBlobSize
        ).decode("utf-16-le")
    finally:
        api.CredFree(pointer)


def save(user, password, *, target):
    raw = password.encode("utf-16-le")
    if not user or not raw or len(raw) > 2560:
        raise ValueError("Usuario o longitud de contraseña inválidos.")
    buffer = (wt.BYTE * len(raw)).from_buffer_copy(raw)
    credential = Credential(
        Type=GENERIC, TargetName=target, UserName=user,
        CredentialBlobSize=len(raw), CredentialBlob=buffer, Persist=PERSIST_LOCAL_MACHINE,
    )
    try:
        if not _api().CredWriteW(ct.byref(credential), 0):
            raise OSError(f"Credential Manager no pudo guardar la entrada local (Win32 {ct.get_last_error()}).")
    finally:
        ct.memset(ct.addressof(buffer), 0, len(raw))


