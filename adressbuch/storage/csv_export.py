"""Konfigurierbarer CSV-Export für Kontakte."""

from __future__ import annotations
import csv
from typing import Callable

from ..models.contact import Contact


def _join(values: list[str]) -> str:
    return "; ".join(v for v in values if v)


def _first_address(c: Contact):
    return c.addresses[0] if c.addresses else None


# (Feldschlüssel, Spaltenüberschrift, Wertextraktion)
FIELDS: list[tuple[str, str, Callable[[Contact], str]]] = [
    ("honorific_prefix", "Titel", lambda c: c.honorific_prefix),
    ("given_name", "Vorname", lambda c: c.given_name),
    ("additional_names", "Weitere Vornamen", lambda c: c.additional_names),
    ("family_name", "Nachname", lambda c: c.family_name),
    ("honorific_suffix", "Namenszusatz", lambda c: c.honorific_suffix),
    ("display_name", "Anzeigename", lambda c: c.get_display_name()),
    ("nickname", "Spitzname", lambda c: c.nickname),
    ("organization", "Firma", lambda c: c.organization),
    ("org_unit", "Abteilung", lambda c: c.org_unit),
    ("title", "Position", lambda c: c.title),
    ("role", "Funktion", lambda c: c.role),
    ("phone", "Telefon (bevorzugt)", lambda c: c.primary_phone()),
    ("phones_all", "Alle Telefonnummern", lambda c: _join([p.number for p in c.phones])),
    ("email", "E-Mail (bevorzugt)", lambda c: c.primary_email()),
    ("emails_all", "Alle E-Mail-Adressen", lambda c: _join([e.address for e in c.emails])),
    ("street", "Straße", lambda c: (a.street if (a := _first_address(c)) else "")),
    ("postal_code", "PLZ", lambda c: (a.postal_code if (a := _first_address(c)) else "")),
    ("city", "Ort", lambda c: (a.city if (a := _first_address(c)) else "")),
    ("region", "Bundesland/Kanton", lambda c: (a.region if (a := _first_address(c)) else "")),
    ("country", "Land", lambda c: (a.country if (a := _first_address(c)) else "")),
    ("urls", "Webseiten", lambda c: _join([u.url for u in c.urls])),
    ("im", "Instant Messaging", lambda c: _join([i.uri for i in c.instant_messaging])),
    ("categories", "Kategorien", lambda c: _join(c.categories)),
    ("birthday", "Geburtstag", lambda c: c.birthday.isoformat() if c.birthday else ""),
    ("anniversary", "Jahrestag", lambda c: c.anniversary.isoformat() if c.anniversary else ""),
    ("deathdate", "Todesdatum", lambda c: c.deathdate.isoformat() if c.deathdate else ""),
    ("gender", "Geschlecht", lambda c: c.gender),
    ("note", "Notiz", lambda c: c.note),
]

FIELD_LABELS = {key: label for key, label, _ in FIELDS}
_FIELD_GETTERS = {key: getter for key, _, getter in FIELDS}


class CsvExporter:
    """Exportiert Kontakte als CSV mit frei wählbaren und sortierbaren Spalten."""

    def export_contacts(
        self,
        contacts: list[Contact],
        path: str,
        field_keys: list[str],
        delimiter: str = ";",
    ) -> int:
        keys = [key for key in field_keys if key in FIELD_LABELS]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
            writer.writerow([FIELD_LABELS[key] for key in keys])
            for contact in contacts:
                writer.writerow([_FIELD_GETTERS[key](contact) or "" for key in keys])
        return len(contacts)
