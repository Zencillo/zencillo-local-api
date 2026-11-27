"""Initialize service signing material without exposing the key."""
import argparse
import ctypes
from pathlib import Path
import secrets
import sys

from app.core.machine_secret import save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32" or not ctypes.windll.shell32.IsUserAnAdmin():
        return 2
    target = args.directory.resolve() / "jwt.dpapi"
    if not target.exists():
        save(target, secrets.token_urlsafe(48))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
