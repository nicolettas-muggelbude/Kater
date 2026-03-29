#!/usr/bin/env python3
"""Startpunkt der Adressbuch-App."""

from pathlib import Path
from adressbuch.gui.app import AdressbuchApp

DB_PATH = Path.home() / ".local" / "share" / "adressbuch" / "kontakte.db"


def main():
    app = AdressbuchApp(DB_PATH)
    app.run()


if __name__ == "__main__":
    main()
