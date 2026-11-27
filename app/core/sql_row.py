from collections.abc import Iterable, Mapping
from typing import Any


class SqlRow(dict[str, Any]):
    """Raw SQL row; no response schema may remove or rename its columns."""

    def __init__(self, values: Mapping[str, Any] | Iterable[tuple[str, Any]] = ()):
        super().__init__(values)

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def model_dump(self, *, exclude: set[str] | None = None, **_ignored: Any) -> dict[str, Any]:
        excluded = exclude or set()
        return {key: value for key, value in self.items() if key not in excluded}
