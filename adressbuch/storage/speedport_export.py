"""Speedport (Telekom) Telefonbuch-Export (CSV).

Format anhand eines echten Exports eines Speedport Smart 4 abgeglichen:
Komma-getrennt, alle Felder in Anführungszeichen, feste Spalten
Name, Vorname, Rufnummer Privat, Rufnummer Arbeit, Rufnummer Mobil,
Rufnummer Mobil 2, Strasse, Nr., PLZ, Ort, Geburtstag (TT.MM.JJJJ).
"""

import csv
from pathlib import Path

from ..models.contact import Contact, Address

_HEADER = [
    "Name", "Vorname", "Rufnummer Privat", "Rufnummer Arbeit",
    "Rufnummer Mobil", "Rufnummer Mobil 2", "Strasse, Nr.", "PLZ", "Ort", "Geburtstag",
]


class SpeedportExporter:
    """Exportiert Kontakte im Speedport-Telefonbuch-CSV-Format."""

    def export_contacts(self, contacts: list[Contact], path: str | Path) -> int:
        rows = [self._contact_to_row(c) for c in contacts]
        rows = [r for r in rows if any(r)]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_ALL, lineterminator="\r\n")
            writer.writerow(_HEADER)
            writer.writerows(rows)
        return len(rows)

    def _contact_to_row(self, contact: Contact) -> list[str]:
        name = contact.family_name
        vorname = contact.given_name
        if not name and not vorname and contact.display_name:
            vorname = contact.display_name

        mobiles = [
            p.number.strip() for p in contact.phones
            if p.number.strip() and self._is_mobile(p.types)
        ]

        return [
            name,
            vorname,
            self._number_by_type(contact, "home"),
            self._number_by_type(contact, "work"),
            mobiles[0] if mobiles else "",
            mobiles[1] if len(mobiles) > 1 else "",
            self._address_field(contact, "street"),
            self._address_field(contact, "postal_code"),
            self._address_field(contact, "city"),
            contact.birthday.strftime("%d.%m.%Y") if contact.birthday else "",
        ]

    def _number_by_type(self, contact: Contact, wanted: str) -> str:
        for phone in contact.phones:
            if not phone.number.strip() or self._is_mobile(phone.types):
                continue
            types = {t.lower() for t in phone.types}
            if "fax" in types:
                continue
            if wanted in types or (wanted == "home" and not types & {"work"}):
                return phone.number.strip()
        return ""

    def _is_mobile(self, types: list[str]) -> bool:
        lower = {t.lower() for t in types}
        return bool(lower & {"cell", "mobile", "text"})

    def _address_field(self, contact: Contact, field: str) -> str:
        addr = self._preferred_address(contact)
        return getattr(addr, field) if addr else ""

    def _preferred_address(self, contact: Contact) -> Address | None:
        for addr in contact.addresses:
            if addr.preferred:
                return addr
        return contact.addresses[0] if contact.addresses else None
