"""SQLite-Datenbank für Kontakte."""

import sqlite3
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from ..models.contact import Contact, Address, Phone, Email, Url, InstantMessaging


class Database:
    """SQLite-Datenbankanbindung für Kontakte."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                uid             TEXT PRIMARY KEY,
                family_name     TEXT NOT NULL DEFAULT '',
                given_name      TEXT NOT NULL DEFAULT '',
                additional_names TEXT NOT NULL DEFAULT '',
                honorific_prefix TEXT NOT NULL DEFAULT '',
                honorific_suffix TEXT NOT NULL DEFAULT '',
                display_name    TEXT NOT NULL DEFAULT '',
                nickname        TEXT NOT NULL DEFAULT '',
                gender          TEXT NOT NULL DEFAULT '',
                birthday        TEXT,
                anniversary     TEXT,
                deathdate       TEXT,
                languages       TEXT NOT NULL DEFAULT '[]',
                timezone        TEXT NOT NULL DEFAULT '',
                geo_lat         REAL,
                geo_lon         REAL,
                organization    TEXT NOT NULL DEFAULT '',
                org_unit        TEXT NOT NULL DEFAULT '',
                title           TEXT NOT NULL DEFAULT '',
                role            TEXT NOT NULL DEFAULT '',
                phones          TEXT NOT NULL DEFAULT '[]',
                emails          TEXT NOT NULL DEFAULT '[]',
                addresses       TEXT NOT NULL DEFAULT '[]',
                urls            TEXT NOT NULL DEFAULT '[]',
                instant_messaging TEXT NOT NULL DEFAULT '[]',
                categories      TEXT NOT NULL DEFAULT '[]',
                note            TEXT NOT NULL DEFAULT '',
                photo_url       TEXT NOT NULL DEFAULT '',
                photo_data      BLOB,
                revision        TEXT,
                source          TEXT NOT NULL DEFAULT '',
                x_thunderbird_categories TEXT NOT NULL DEFAULT '[]'
            );

            CREATE INDEX IF NOT EXISTS idx_contacts_family_name
                ON contacts(family_name);
            CREATE INDEX IF NOT EXISTS idx_contacts_organization
                ON contacts(organization);
        """)
        self._conn.commit()

    # --- Serialisierung ---

    @staticmethod
    def _date_to_str(d: Optional[date]) -> Optional[str]:
        return d.isoformat() if d else None

    @staticmethod
    def _str_to_date(s: Optional[str]) -> Optional[date]:
        return date.fromisoformat(s) if s else None

    @staticmethod
    def _datetime_to_str(dt: Optional[datetime]) -> Optional[str]:
        return dt.isoformat() if dt else None

    @staticmethod
    def _str_to_datetime(s: Optional[str]) -> Optional[datetime]:
        return datetime.fromisoformat(s) if s else None

    @staticmethod
    def _phones_to_json(phones: list[Phone]) -> str:
        return json.dumps([{
            "number": p.number,
            "types": p.types,
            "preferred": p.preferred
        } for p in phones])

    @staticmethod
    def _json_to_phones(s: str) -> list[Phone]:
        return [Phone(**d) for d in json.loads(s)]

    @staticmethod
    def _emails_to_json(emails: list[Email]) -> str:
        return json.dumps([{
            "address": e.address,
            "types": e.types,
            "preferred": e.preferred
        } for e in emails])

    @staticmethod
    def _json_to_emails(s: str) -> list[Email]:
        return [Email(**d) for d in json.loads(s)]

    @staticmethod
    def _addresses_to_json(addresses: list[Address]) -> str:
        return json.dumps([{
            "street": a.street,
            "extended": a.extended,
            "po_box": a.po_box,
            "city": a.city,
            "region": a.region,
            "postal_code": a.postal_code,
            "country": a.country,
            "label": a.label,
            "preferred": a.preferred
        } for a in addresses])

    @staticmethod
    def _json_to_addresses(s: str) -> list[Address]:
        return [Address(**d) for d in json.loads(s)]

    @staticmethod
    def _urls_to_json(urls: list[Url]) -> str:
        return json.dumps([{"url": u.url, "types": u.types} for u in urls])

    @staticmethod
    def _json_to_urls(s: str) -> list[Url]:
        return [Url(**d) for d in json.loads(s)]

    @staticmethod
    def _im_to_json(ims: list[InstantMessaging]) -> str:
        return json.dumps([{
            "uri": im.uri,
            "types": im.types,
            "preferred": im.preferred
        } for im in ims])

    @staticmethod
    def _json_to_im(s: str) -> list[InstantMessaging]:
        return [InstantMessaging(**d) for d in json.loads(s)]

    def _contact_to_row(self, c: Contact) -> dict:
        return {
            "uid": c.uid,
            "family_name": c.family_name,
            "given_name": c.given_name,
            "additional_names": c.additional_names,
            "honorific_prefix": c.honorific_prefix,
            "honorific_suffix": c.honorific_suffix,
            "display_name": c.display_name,
            "nickname": c.nickname,
            "gender": c.gender,
            "birthday": self._date_to_str(c.birthday),
            "anniversary": self._date_to_str(c.anniversary),
            "deathdate": self._date_to_str(c.deathdate),
            "languages": json.dumps(c.languages),
            "timezone": c.timezone,
            "geo_lat": c.geo_lat,
            "geo_lon": c.geo_lon,
            "organization": c.organization,
            "org_unit": c.org_unit,
            "title": c.title,
            "role": c.role,
            "phones": self._phones_to_json(c.phones),
            "emails": self._emails_to_json(c.emails),
            "addresses": self._addresses_to_json(c.addresses),
            "urls": self._urls_to_json(c.urls),
            "instant_messaging": self._im_to_json(c.instant_messaging),
            "categories": json.dumps(c.categories),
            "note": c.note,
            "photo_url": c.photo_url,
            "photo_data": c.photo_data,
            "revision": self._datetime_to_str(c.revision),
            "source": c.source,
            "x_thunderbird_categories": json.dumps(c.x_thunderbird_categories),
        }

    def _row_to_contact(self, row: sqlite3.Row) -> Contact:
        return Contact(
            uid=row["uid"],
            family_name=row["family_name"],
            given_name=row["given_name"],
            additional_names=row["additional_names"],
            honorific_prefix=row["honorific_prefix"],
            honorific_suffix=row["honorific_suffix"],
            display_name=row["display_name"],
            nickname=row["nickname"],
            gender=row["gender"],
            birthday=self._str_to_date(row["birthday"]),
            anniversary=self._str_to_date(row["anniversary"]),
            deathdate=self._str_to_date(row["deathdate"]),
            languages=json.loads(row["languages"]),
            timezone=row["timezone"],
            geo_lat=row["geo_lat"],
            geo_lon=row["geo_lon"],
            organization=row["organization"],
            org_unit=row["org_unit"],
            title=row["title"],
            role=row["role"],
            phones=self._json_to_phones(row["phones"]),
            emails=self._json_to_emails(row["emails"]),
            addresses=self._json_to_addresses(row["addresses"]),
            urls=self._json_to_urls(row["urls"]),
            instant_messaging=self._json_to_im(row["instant_messaging"]),
            categories=json.loads(row["categories"]),
            note=row["note"],
            photo_url=row["photo_url"],
            photo_data=row["photo_data"],
            revision=self._str_to_datetime(row["revision"]),
            source=row["source"],
            x_thunderbird_categories=json.loads(row["x_thunderbird_categories"]),
        )

    # --- CRUD ---

    def save(self, contact: Contact):
        """Kontakt speichern oder aktualisieren (Upsert)."""
        row = self._contact_to_row(contact)
        cols = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row.keys())
        updates = ", ".join(f"{k}=:{k}" for k in row.keys() if k != "uid")
        self._conn.execute(
            f"INSERT INTO contacts ({cols}) VALUES ({placeholders}) "
            f"ON CONFLICT(uid) DO UPDATE SET {updates}",
            row
        )
        self._conn.commit()

    def get(self, uid: str) -> Optional[Contact]:
        """Kontakt nach UID laden."""
        row = self._conn.execute(
            "SELECT * FROM contacts WHERE uid=?", (uid,)
        ).fetchone()
        return self._row_to_contact(row) if row else None

    def delete(self, uid: str):
        """Kontakt löschen."""
        self._conn.execute("DELETE FROM contacts WHERE uid=?", (uid,))
        self._conn.commit()

    def all(self) -> list[Contact]:
        """Alle Kontakte sortiert nach Nachname, Vorname."""
        rows = self._conn.execute(
            "SELECT * FROM contacts ORDER BY family_name, given_name"
        ).fetchall()
        return [self._row_to_contact(r) for r in rows]

    def search(self, query: str) -> list[Contact]:
        """Volltextsuche in Namen, Organisation und E-Mail."""
        q = f"%{query}%"
        rows = self._conn.execute("""
            SELECT * FROM contacts
            WHERE family_name LIKE ?
               OR given_name LIKE ?
               OR display_name LIKE ?
               OR organization LIKE ?
               OR emails LIKE ?
               OR phones LIKE ?
            ORDER BY family_name, given_name
        """, (q, q, q, q, q, q)).fetchall()
        return [self._row_to_contact(r) for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]

    def close(self):
        self._conn.close()
