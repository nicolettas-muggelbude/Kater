"""App-Einstellungen (JSON-Datei neben der Datenbank)."""

import json
from pathlib import Path


class Settings:
    """Persistente App-Einstellungen."""

    _DEFAULTS = {
        "groups_enabled": False,
    }

    def __init__(self, path: str | Path):
        self._path = Path(path)
        self._data: dict = dict(self._DEFAULTS)
        if self._path.exists():
            try:
                self._data.update(json.loads(self._path.read_text(encoding="utf-8")))
            except Exception:
                pass

    def _save(self):
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    @property
    def groups_enabled(self) -> bool:
        return bool(self._data.get("groups_enabled", False))

    @groups_enabled.setter
    def groups_enabled(self, value: bool):
        self._data["groups_enabled"] = value
        self._save()
