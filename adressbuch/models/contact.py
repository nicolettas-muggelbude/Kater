"""Kontaktmodell mit allen vCard 4.0 Feldern."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class Address:
    """Postadresse (vCard ADR)."""
    street: str = ""
    extended: str = ""        # Adresszusatz
    po_box: str = ""          # Postfach
    city: str = ""
    region: str = ""          # Bundesland / Kanton
    postal_code: str = ""
    country: str = ""
    label: str = ""           # Typ: home, work, ...
    preferred: bool = False


@dataclass
class Phone:
    """Telefonnummer (vCard TEL)."""
    number: str = ""
    # Typen: home, work, cell, fax, pager, voice, text, video, ...
    types: list[str] = field(default_factory=lambda: ["voice"])
    preferred: bool = False


@dataclass
class Email:
    """E-Mail-Adresse (vCard EMAIL)."""
    address: str = ""
    types: list[str] = field(default_factory=lambda: ["internet"])
    preferred: bool = False


@dataclass
class Url:
    """Webadresse (vCard URL)."""
    url: str = ""
    types: list[str] = field(default_factory=list)


@dataclass
class InstantMessaging:
    """Instant Messaging (vCard IMPP)."""
    uri: str = ""             # z.B. xmpp:user@server.de, matrix:@user:server
    types: list[str] = field(default_factory=list)
    preferred: bool = False


@dataclass
class Contact:
    """
    Vollständiges Kontaktmodell nach vCard 4.0 (RFC 6350).
    Erweitert um DEATHDATE (vCard 4.0 Section 6.2.5 / RFC 6474).
    """

    # --- Identifikation ---
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Strukturierter Name (vCard N)
    family_name: str = ""         # Nachname
    given_name: str = ""          # Vorname
    additional_names: str = ""    # Weitere Vornamen
    honorific_prefix: str = ""    # Titel (Dr., Prof., ...)
    honorific_suffix: str = ""    # Namenszusatz (Jr., Sr., ...)

    # Anzeigename (vCard FN) - wird automatisch generiert wenn leer
    display_name: str = ""

    # Spitzname (vCard NICKNAME)
    nickname: str = ""

    # --- Persönliche Daten ---
    gender: str = ""              # M, F, O, N, U (vCard GENDER)
    birthday: Optional[date] = None        # vCard BDAY
    anniversary: Optional[date] = None    # vCard ANNIVERSARY (Hochzeitstag)
    deathdate: Optional[date] = None      # vCard DEATHDATE (RFC 6474)

    # Sprache (vCard LANG)
    languages: list[str] = field(default_factory=list)

    # Zeitzone (vCard TZ)
    timezone: str = ""

    # Geolocation (vCard GEO)
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None

    # --- Organisation ---
    organization: str = ""        # vCard ORG (Firma)
    org_unit: str = ""            # Abteilung
    title: str = ""               # vCard TITLE (Berufsbezeichnung)
    role: str = ""                # vCard ROLE (Funktion)

    # --- Kontaktdaten ---
    phones: list[Phone] = field(default_factory=list)
    emails: list[Email] = field(default_factory=list)
    addresses: list[Address] = field(default_factory=list)
    urls: list[Url] = field(default_factory=list)
    instant_messaging: list[InstantMessaging] = field(default_factory=list)

    # --- Sonstiges ---
    categories: list[str] = field(default_factory=list)   # vCard CATEGORIES
    note: str = ""                # vCard NOTE
    photo_data: Optional[bytes] = None   # vCard PHOTO (eingebettet)
    photo_url: str = ""           # vCard PHOTO (URL)

    # --- Metadaten ---
    revision: Optional[datetime] = None  # vCard REV
    source: str = ""              # vCard SOURCE

    # Thunderbird-kompatible Erweiterungen
    x_thunderbird_categories: list[str] = field(default_factory=list)

    def get_display_name(self) -> str:
        """Gibt den Anzeigenamen zurück, generiert ihn falls nötig."""
        if self.display_name:
            return self.display_name
        parts = []
        if self.honorific_prefix:
            parts.append(self.honorific_prefix)
        if self.given_name:
            parts.append(self.given_name)
        if self.additional_names:
            parts.append(self.additional_names)
        if self.family_name:
            parts.append(self.family_name)
        if self.honorific_suffix:
            parts.append(self.honorific_suffix)
        if parts:
            return " ".join(parts)
        if self.organization:
            return self.organization
        if self.emails:
            return self.emails[0].address
        return "(Unbekannt)"

    def get_sort_key(self) -> str:
        """Sortierschlüssel: Nachname, Vorname."""
        return f"{self.family_name.lower()}, {self.given_name.lower()}"

    def primary_email(self) -> str:
        """Gibt die bevorzugte E-Mail-Adresse zurück."""
        for email in self.emails:
            if email.preferred:
                return email.address
        return self.emails[0].address if self.emails else ""

    def primary_phone(self) -> str:
        """Gibt die bevorzugte Telefonnummer zurück."""
        for phone in self.phones:
            if phone.preferred:
                return phone.number
        return self.phones[0].number if self.phones else ""
