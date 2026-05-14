"""Thunderbird-CSV-Import."""

import csv
from datetime import date
from pathlib import Path
from typing import Optional

from ..models.contact import Contact, Address, Email, Phone, Url


class ThunderbirdCsvParser:
    """Parst Thunderbird-CSV-Exporte (Adressbuch → Exportieren als CSV).

    Unterstützt englische und deutsche Thunderbird-Lokalisierung.
    """

    _DE_TO_EN: dict[str, str] = {
        "Vorname":                  "First Name",
        "Nachname":                 "Last Name",
        "Anzeigename":              "Display Name",
        "Spitzname":                "Nickname",
        "Primäre E-Mail-Adresse":   "Primary Email",
        "Sekundäre E-Mail-Adresse": "Secondary Email",
        "Messenger-Name":           "Screen Name",
        "Tel. dienstlich":          "Work Phone",
        "Tel. privat":              "Home Phone",
        "Fax-Nummer":               "Fax Number",
        "Pager-Nummer":             "Pager Number",
        "Mobil-Tel.-Nr.":           "Mobile Number",
        "Privat: Adresse":          "Home Address",
        "Privat: Adresse 2":        "Home Address 2",
        "Privat: Ort":              "Home City",
        "Privat: Bundesland":       "Home State",
        "Privat: PLZ":              "Home ZipCode",
        "Privat: Land":             "Home Country",
        "Dienstlich: Adresse":      "Work Address",
        "Dienstlich: Adresse 2":    "Work Address 2",
        "Dienstlich: Ort":          "Work City",
        "Dienstlich: Bundesland":   "Work State",
        "Dienstlich: PLZ":          "Work ZipCode",
        "Dienstlich: Land":         "Work Country",
        "Arbeitstitel":             "Job Title",
        "Abteilung":                "Department",
        "Organisation":             "Organization",
        "Webseite 1":               "Web Page 1",
        "Webseite 2":               "Web Page 2",
        "Geburtsjahr":              "Birth Year",
        "Geburtsmonat":             "Birth Month",
        "Geburtstag":               "Birth Day",
        "Notizen":                  "Notes",
    }

    _SIMPLE_FIELDS = {
        "First Name":   "given_name",
        "Last Name":    "family_name",
        "Display Name": "display_name",
        "Nickname":     "nickname",
        "Job Title":    "title",
        "Department":   "org_unit",
        "Organization": "organization",
        "Notes":        "note",
    }

    _PHONE_COLS = [
        ("Work Phone",    ["work", "voice"]),
        ("Home Phone",    ["home", "voice"]),
        ("Mobile Number", ["cell"]),
        ("Fax Number",    ["fax"]),
        ("Pager Number",  ["pager"]),
    ]

    def parse_file(self, path: str | Path) -> list[Contact]:
        # utf-8-sig entfernt BOM falls vorhanden
        text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
        reader = csv.DictReader(text.splitlines())
        contacts = []
        for row in reader:
            try:
                contacts.append(self._parse_row(self._normalize(row)))
            except Exception as e:
                print(f"Warnung: CSV-Zeile übersprungen: {e}")
        return contacts

    def _normalize(self, row: dict) -> dict:
        """Übersetzt deutsche Spaltenköpfe auf englische Bezeichnungen."""
        return {self._DE_TO_EN.get(k, k): v for k, v in row.items()}

    def _parse_row(self, row: dict) -> Contact:
        c = Contact()

        for csv_col, attr in self._SIMPLE_FIELDS.items():
            val = row.get(csv_col, "").strip()
            if val:
                setattr(c, attr, val)

        for col, pref in [("Primary Email", True), ("Secondary Email", False)]:
            addr = row.get(col, "").strip()
            if addr:
                c.emails.append(Email(address=addr, types=["internet"], preferred=pref))

        for col, types in self._PHONE_COLS:
            num = row.get(col, "").strip()
            if num:
                c.phones.append(Phone(number=num, types=types, preferred=False))

        home = self._parse_address(row, "Home")
        if home:
            home.label = "home"
            c.addresses.append(home)

        work = self._parse_address(row, "Work")
        if work:
            work.label = "work"
            c.addresses.append(work)

        for col in ("Web Page 1", "Web Page 2"):
            url = row.get(col, "").strip()
            if url:
                c.urls.append(Url(url=url, types=[]))

        bday = self._parse_birthday(row)
        if bday:
            c.birthday = bday

        if not c.display_name:
            c.display_name = c.get_display_name()

        return c

    def _parse_address(self, row: dict, prefix: str) -> Optional[Address]:
        street = row.get(f"{prefix} Address", "").strip()
        city   = row.get(f"{prefix} City", "").strip()
        if not street and not city:
            return None
        return Address(
            street=street,
            extended=row.get(f"{prefix} Address 2", "").strip(),
            city=city,
            region=row.get(f"{prefix} State", "").strip(),
            postal_code=row.get(f"{prefix} ZipCode", "").strip(),
            country=row.get(f"{prefix} Country", "").strip(),
        )

    def _parse_birthday(self, row: dict) -> Optional[date]:
        try:
            year  = int(row.get("Birth Year",  "0") or "0")
            month = int(row.get("Birth Month", "0") or "0")
            day   = int(row.get("Birth Day",   "0") or "0")
            if year > 0 and month > 0 and day > 0:
                return date(year, month, day)
        except (ValueError, TypeError):
            pass
        return None
