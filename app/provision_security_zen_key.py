"""Protect the existing station file's legacy key under the service directory."""
import argparse
import ctypes
from getpass import GetPassWarning, getpass
import json
from pathlib import Path
import sys
import warnings

from app.core.machine_secret import save
from app.core.security_zen import read_security_zen, station_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32" or not ctypes.windll.shell32.IsUserAnAdmin() or not sys.stdin.isatty():
        print("La clave requiere una consola Windows elevada con entrada oculta.", file=sys.stderr)
        return 2
    try:
        config = args.config.resolve()
        values = json.loads(config.read_text(encoding="utf-8-sig"))
        root = config.parent
        target = root / "legacy-sql-key.dpapi"
        if target.exists() or not (root / "jwt.dpapi").is_file():
            raise ValueError()
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            key = getpass("Clave existente del archivo de estación: ")
        credentials = read_security_zen(root / "AUTOMATIZACION.security_zen", key.encode("utf-8"))
        station_profile(credentials, values["station"], values.get("sql_port"))
        save(target, key)
    except (OSError, ValueError, KeyError, TypeError, GetPassWarning):
        print("No se pudo aprovisionar el archivo de estación.", file=sys.stderr)
        return 2
    print("Clave protegida para el servicio de estación.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
