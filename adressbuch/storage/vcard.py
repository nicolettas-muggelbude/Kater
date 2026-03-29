"""vCard 4.0 Import und Export (RFC 6350 + RFC 6474 für DEATHDATE)."""

import base64
import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from ..models.contact import Contact, Address, Phone, Email, Url, InstantMessaging


class VCardParser:
    """Parst vCard 3.0 und 4.0 Dateien."""

    def parse_file(self, path: str | Path) -> list[Contact]:
        """Liest eine .vcf Datei und gibt alle enthaltenen Kontakte zurück."""
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return self.parse_string(text)

    def parse_string(self, text: str) -> list[Contact]:
        """Parst einen vCard-String (kann mehrere Karten enthalten)."""
        # Zeilenfortsetzungen zusammenführen (RFC 6350 §3.2)
        text = re.sub(r"\r?\n[ \t]", "", text)
        contacts = []
        blocks = re.findall(
            r"BEGIN:VCARD.*?END:VCARD", text, re.DOTALL | re.IGNORECASE
        )
        for block in blocks:
            try:
                contacts.append(self._parse_block(block))
            except Exception as e:
                print(f"Warnung: vCard-Block übersprungen: {e}")
        return contacts

    def _parse_block(self, block: str) -> Contact:
        contact = Contact()
        lines = block.splitlines()

        for line in lines:
            if not line or line.upper().startswith("BEGIN:") or line.upper().startswith("END:"):
                continue
            # Property-Name und Parameter trennen
            if ":" not in line:
                continue
            prop_part, _, value = line.partition(":")
            value = value.strip()
            prop_parts = prop_part.upper().split(";")
            prop_name = prop_parts[0].strip()
            params = self._parse_params(prop_part)

            self._apply_property(contact, prop_name, params, value)

        # Anzeigename generieren falls fehlt
        if not contact.display_name:
            contact.display_name = contact.get_display_name()

        return contact

    def _parse_params(self, prop_part: str) -> dict[str, list[str]]:
        """Extrahiert Parameter wie TYPE=home,work oder PREF=1."""
        params: dict[str, list[str]] = {}
        parts = prop_part.split(";")[1:]  # Ersten Teil (Name) überspringen
        for part in parts:
            if "=" in part:
                key, _, val = part.partition("=")
                params.setdefault(key.upper().strip(), []).extend(
                    v.strip().lower() for v in val.split(",")
                )
            else:
                # Typ ohne =, z.B. "HOME" in vCard 3.0
                params.setdefault("TYPE", []).append(part.strip().lower())
        return params

    def _get_types(self, params: dict) -> list[str]:
        return params.get("TYPE", [])

    def _is_preferred(self, params: dict) -> bool:
        types = self._get_types(params)
        return "pref" in types or params.get("PREF", [""])[0] == "1"

    def _parse_date(self, value: str) -> Optional[date]:
        """Parst ein Datum in verschiedenen vCard-Formaten."""
        value = value.strip().replace("-", "")
        for fmt in ("%Y%m%d", "%Y%m", "%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    def _unescape(self, value: str) -> str:
        """vCard-Escaping rückgängig machen."""
        return value.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")

    def _apply_property(self, contact: Contact, prop: str, params: dict, value: str):
        match prop:
            case "FN":
                contact.display_name = self._unescape(value)

            case "N":
                parts = value.split(";")
                while len(parts) < 5:
                    parts.append("")
                contact.family_name = self._unescape(parts[0])
                contact.given_name = self._unescape(parts[1])
                contact.additional_names = self._unescape(parts[2])
                contact.honorific_prefix = self._unescape(parts[3])
                contact.honorific_suffix = self._unescape(parts[4])

            case "NICKNAME":
                contact.nickname = self._unescape(value)

            case "GENDER":
                contact.gender = value.split(";")[0].strip().upper()

            case "BDAY":
                contact.birthday = self._parse_date(value)

            case "ANNIVERSARY":
                contact.anniversary = self._parse_date(value)

            case "DEATHDATE" | "X-DEATHDATE":
                contact.deathdate = self._parse_date(value)

            case "ORG":
                parts = value.split(";")
                contact.organization = self._unescape(parts[0])
                if len(parts) > 1:
                    contact.org_unit = self._unescape(parts[1])

            case "TITLE":
                contact.title = self._unescape(value)

            case "ROLE":
                contact.role = self._unescape(value)

            case "TEL":
                types = self._get_types(params)
                if not types:
                    types = ["voice"]
                contact.phones.append(Phone(
                    number=value,
                    types=types,
                    preferred=self._is_preferred(params)
                ))

            case "EMAIL":
                types = self._get_types(params)
                if not types:
                    types = ["internet"]
                contact.emails.append(Email(
                    address=value,
                    types=[t for t in types if t != "pref"],
                    preferred=self._is_preferred(params)
                ))

            case "ADR":
                parts = value.split(";")
                while len(parts) < 7:
                    parts.append("")
                types = self._get_types(params)
                contact.addresses.append(Address(
                    po_box=self._unescape(parts[0]),
                    extended=self._unescape(parts[1]),
                    street=self._unescape(parts[2]),
                    city=self._unescape(parts[3]),
                    region=self._unescape(parts[4]),
                    postal_code=self._unescape(parts[5]),
                    country=self._unescape(parts[6]),
                    label=",".join(types),
                    preferred=self._is_preferred(params)
                ))

            case "URL":
                types = self._get_types(params)
                contact.urls.append(Url(url=value, types=types))

            case "IMPP":
                types = self._get_types(params)
                contact.instant_messaging.append(InstantMessaging(
                    uri=value,
                    types=types,
                    preferred=self._is_preferred(params)
                ))

            case "LANG":
                contact.languages.append(value.strip())

            case "TZ":
                contact.timezone = value

            case "GEO":
                # vCard 4.0: geo:lat,lon  /  vCard 3.0: lat;lon
                geo = value.replace("geo:", "")
                parts = geo.replace(";", ",").split(",")
                if len(parts) >= 2:
                    try:
                        contact.geo_lat = float(parts[0])
                        contact.geo_lon = float(parts[1])
                    except ValueError:
                        pass

            case "CATEGORIES":
                cats = [self._unescape(c.strip()) for c in value.split(",")]
                contact.categories.extend(cats)

            case "NOTE":
                contact.note = self._unescape(value)

            case "PHOTO":
                if value.startswith("http://") or value.startswith("https://"):
                    contact.photo_url = value
                elif ";" in value or params.get("ENCODING"):
                    # Base64-kodiert
                    try:
                        contact.photo_data = base64.b64decode(value)
                    except Exception:
                        pass

            case "UID":
                contact.uid = value

            case "REV":
                try:
                    contact.revision = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

            case "SOURCE":
                contact.source = value

            case "X-THUNDERBIRD-CATEGORIES" | "X-MOZILLA-CATEGORIES":
                cats = [c.strip() for c in value.split(",")]
                contact.x_thunderbird_categories.extend(cats)


class VCardExporter:
    """Exportiert Kontakte als vCard 4.0."""

    def export_contacts(self, contacts: list[Contact], path: str | Path):
        """Schreibt mehrere Kontakte in eine .vcf Datei."""
        text = "\r\n".join(
            self.contact_to_vcard(c) for c in contacts
        )
        Path(path).write_text(text, encoding="utf-8")

    def contact_to_vcard(self, contact: Contact) -> str:
        """Gibt einen vCard 4.0 String für einen Kontakt zurück."""
        lines = ["BEGIN:VCARD", "VERSION:4.0"]

        # UID
        lines.append(f"UID:{contact.uid}")

        # Name
        fn = contact.get_display_name()
        lines.append(f"FN:{self._escape(fn)}")

        n = ";".join([
            self._escape(contact.family_name),
            self._escape(contact.given_name),
            self._escape(contact.additional_names),
            self._escape(contact.honorific_prefix),
            self._escape(contact.honorific_suffix),
        ])
        lines.append(f"N:{n}")

        if contact.nickname:
            lines.append(f"NICKNAME:{self._escape(contact.nickname)}")

        # Persönliche Daten
        if contact.gender:
            lines.append(f"GENDER:{contact.gender}")

        if contact.birthday:
            lines.append(f"BDAY:{contact.birthday.strftime('%Y%m%d')}")

        if contact.anniversary:
            lines.append(f"ANNIVERSARY:{contact.anniversary.strftime('%Y%m%d')}")

        if contact.deathdate:
            lines.append(f"DEATHDATE:{contact.deathdate.strftime('%Y%m%d')}")

        # Organisation
        if contact.organization:
            org = self._escape(contact.organization)
            if contact.org_unit:
                org += f";{self._escape(contact.org_unit)}"
            lines.append(f"ORG:{org}")

        if contact.title:
            lines.append(f"TITLE:{self._escape(contact.title)}")

        if contact.role:
            lines.append(f"ROLE:{self._escape(contact.role)}")

        # Telefon
        for phone in contact.phones:
            type_str = ",".join(t.upper() for t in phone.types if t != "pref")
            pref = ";PREF=1" if phone.preferred else ""
            if type_str:
                lines.append(f"TEL;TYPE={type_str}{pref}:{phone.number}")
            else:
                lines.append(f"TEL{pref}:{phone.number}")

        # E-Mail
        for email in contact.emails:
            type_str = ",".join(t.upper() for t in email.types if t != "pref")
            pref = ";PREF=1" if email.preferred else ""
            if type_str:
                lines.append(f"EMAIL;TYPE={type_str}{pref}:{email.address}")
            else:
                lines.append(f"EMAIL{pref}:{email.address}")

        # Adressen
        for addr in contact.addresses:
            type_str = addr.label.upper() if addr.label else ""
            pref = ";PREF=1" if addr.preferred else ""
            type_param = f";TYPE={type_str}" if type_str else ""
            adr_val = ";".join([
                self._escape(addr.po_box),
                self._escape(addr.extended),
                self._escape(addr.street),
                self._escape(addr.city),
                self._escape(addr.region),
                self._escape(addr.postal_code),
                self._escape(addr.country),
            ])
            lines.append(f"ADR{type_param}{pref}:{adr_val}")

        # URLs
        for url in contact.urls:
            type_str = ",".join(t.upper() for t in url.types)
            if type_str:
                lines.append(f"URL;TYPE={type_str}:{url.url}")
            else:
                lines.append(f"URL:{url.url}")

        # Instant Messaging
        for im in contact.instant_messaging:
            type_str = ",".join(t.upper() for t in im.types)
            pref = ";PREF=1" if im.preferred else ""
            if type_str:
                lines.append(f"IMPP;TYPE={type_str}{pref}:{im.uri}")
            else:
                lines.append(f"IMPP{pref}:{im.uri}")

        # Sprachen
        for lang in contact.languages:
            lines.append(f"LANG:{lang}")

        if contact.timezone:
            lines.append(f"TZ:{contact.timezone}")

        if contact.geo_lat is not None and contact.geo_lon is not None:
            lines.append(f"GEO:geo:{contact.geo_lat},{contact.geo_lon}")

        # Kategorien
        if contact.categories:
            cats = ",".join(self._escape(c) for c in contact.categories)
            lines.append(f"CATEGORIES:{cats}")

        if contact.note:
            lines.append(f"NOTE:{self._escape(contact.note)}")

        # Foto
        if contact.photo_url:
            lines.append(f"PHOTO:{contact.photo_url}")
        elif contact.photo_data:
            b64 = base64.b64encode(contact.photo_data).decode("ascii")
            # Zeilenumbruch alle 75 Zeichen (RFC 6350)
            b64_lines = [b64[i:i+75] for i in range(0, len(b64), 75)]
            lines.append("PHOTO;ENCODING=BASE64;TYPE=JPEG:" + b64_lines[0])
            for l in b64_lines[1:]:
                lines.append(f" {l}")

        # Revision
        if contact.revision:
            lines.append(f"REV:{contact.revision.strftime('%Y%m%dT%H%M%SZ')}")

        if contact.source:
            lines.append(f"SOURCE:{contact.source}")

        lines.append("END:VCARD")
        return "\r\n".join(lines)

    def _escape(self, value: str) -> str:
        """vCard-Sonderzeichen escapen."""
        return (value
                .replace("\\", "\\\\")
                .replace(",", "\\,")
                .replace(";", "\\;")
                .replace("\n", "\\n"))
