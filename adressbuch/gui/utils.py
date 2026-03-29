"""GUI-Hilfsfunktionen."""

import sys
from pathlib import Path


def resolve_asset(filename: str) -> Path:
    """Gibt den absoluten Pfad zu einer Asset-Datei zurück.
    Funktioniert sowohl im Entwicklungsmodus als auch im PyInstaller-Bundle.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / filename
    return Path(__file__).parent.parent.parent / "assets" / filename
