"""Compare the real station file with Dart over a private process pipe."""
from datetime import datetime
import hmac
import json
from pathlib import Path
import sys

from app.core.security_zen import read_security_zen


def main():
    try:
        data = json.loads(sys.stdin.buffer.read(16384))
        profile = read_security_zen(Path(data["path"]), data["key"].encode("utf8"))
        expected = data["dart"]
        same = (
            profile.user == expected["user"]
            and hmac.compare_digest(profile.password.get_secret_value().encode(), expected["pass"].encode())
            and profile.server == expected["server"]
            and profile.kind == expected["type"]
            and datetime.fromisoformat(profile.date) == datetime.fromisoformat(expected["date"])
            and profile.database == expected["database"]
        )
        if not same:
            return 1
        print(f"Campos equivalentes: 6. AES-{len(data['key'].encode('utf8')) * 8}.")
        return 0
    except (OSError, ValueError, TypeError, KeyError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
