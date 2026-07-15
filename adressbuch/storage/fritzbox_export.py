"""FRITZ!Box Telefonbuch-Export (phonebook.xml).

Format anhand eines echten Exports einer FRITZ!Box 7530 (FRITZ!OS 08.25)
abgeglichen: kein name-Attribut an <phonebook>, <setup/> bleibt leer,
jede <number> trägt immer ein prio-Attribut (0 oder 1).
"""

import time
from pathlib import Path
from xml.sax.saxutils import escape

from ..models.contact import Contact


class FritzboxExporter:
    """Exportiert Kontakte als FRITZ!Box-Telefonbuch-XML (Import über die Fritzbox-Weboberfläche)."""

    def export_contacts(self, contacts: list[Contact], path: str | Path) -> int:
        """Schreibt die Kontakte als phonebook.xml. Gibt die Anzahl exportierter Kontakte zurück.

        Kontakte ohne Telefonnummer werden übersprungen, da die Fritzbox
        sie sonst nicht sinnvoll darstellen kann.
        """
        exported = [c for c in contacts if any(p.number.strip() for p in c.phones)]
        xml = self._build_xml(exported)
        Path(path).write_text(xml, encoding="utf-8")
        return len(exported)

    def _build_xml(self, contacts: list[Contact]) -> str:
        lines = [
            '<?xml version="1.0" encoding="utf-8"?>',
            "<phonebooks>",
            "  <phonebook>",
        ]
        for contact in contacts:
            lines.append(self._contact_to_xml(contact))
        lines.append("  </phonebook>")
        lines.append("</phonebooks>")
        return "\n".join(lines)

    def _contact_to_xml(self, contact: Contact) -> str:
        numbers = [p for p in contact.phones if p.number.strip()]
        category = "1" if any(c.strip().lower() == "vip" for c in contact.categories) else "0"
        name = escape(contact.get_display_name())
        mod_time = (
            str(int(contact.revision.timestamp()))
            if contact.revision
            else str(int(time.time()))
        )

        parts = [
            "    <contact>",
            f"      <category>{category}</category>",
            "      <person>",
            f"        <realName>{name}</realName>",
            "      </person>",
            '      <telephony nid="1">',
        ]
        for idx, phone in enumerate(numbers):
            ftype = self._map_type(phone.types)
            prio = "1" if phone.preferred else "0"
            number = escape(phone.number.strip())
            parts.append(f'        <number type="{ftype}" prio="{prio}" id="{idx}">{number}</number>')
        parts.extend([
            "      </telephony>",
            "      <services/>",
            "      <setup/>",
            f"      <mod_time>{mod_time}</mod_time>",
            "    </contact>",
        ])
        return "\n".join(parts)

    def _map_type(self, types: list[str]) -> str:
        """Bildet vCard-Telefontypen auf die von der Fritzbox akzeptierten Typen ab."""
        lower = [t.lower() for t in types]
        if "fax" in lower:
            return "fax_work"
        if "cell" in lower or "mobile" in lower or "text" in lower:
            return "mobile"
        if "work" in lower:
            return "work"
        return "home"
