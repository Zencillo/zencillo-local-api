"""Prepare the hash-only device registry used by the Windows station installer."""
import argparse
import getpass
import json
from pathlib import Path
import re
import sys

from app.core.security import hash_secret
PILOT_CATALOGS = [
    "ListarTiposVehiculo", "ListarTiposGasto",
    "ListarConfiguracionRedondeo", "ListarCombustibles",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--device", required=True)
    args = parser.parse_args()
    if not sys.stdin.isatty() or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", args.device):
        return 2
    records = (json.loads(args.registry.read_text(encoding="utf-8-sig"))
               if args.registry.exists() else {})
    if args.device in records:
        print("El identificador ya existe.", file=sys.stderr)
        return 2
    secret = getpass.getpass("Secreto aleatorio del dispositivo (mínimo 32 caracteres): ")
    if len(secret) < 32 or secret != getpass.getpass("Confirme el secreto: "):
        return 2
    records[args.device] = {"secret_hash": hash_secret(secret), "operations": PILOT_CATALOGS}
    with args.registry.open("w", encoding="utf-8") as registry:
        json.dump(records, registry, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
