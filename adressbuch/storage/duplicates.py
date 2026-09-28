"""Erkennung und Zusammenführung von Kontakt-Dubletten."""

import re
from dataclasses import dataclass, replace

from ..models.contact import Contact

_SCALAR_FIELDS = [
    "family_name", "given_name", "additional_names", "honorific_prefix",
    "honorific_suffix", "display_name", "nickname", "gender",
    "organization", "org_unit", "title", "role", "note",
    "birthday", "anniversary", "deathdate",
]

_LIST_FIELD_KEYS = {
    "phones": lambda p: _normalize_phone(p.number),
    "emails": lambda e: e.address.strip().lower(),
    "addresses": lambda a: (a.street.strip().lower(), a.city.strip().lower(), a.postal_code.strip().lower()),
    "urls": lambda u: u.url.strip().lower(),
    "instant_messaging": lambda im: im.uri.strip().lower(),
}


@dataclass
class DuplicateCandidate:
    """Ein Paar möglicher Dubletten mit den Gründen für den Treffer."""
    contact_a: Contact
    contact_b: Contact
    reasons: list[str]


def _normalize_name(contact: Contact) -> str:
    return f"{contact.family_name.strip().lower()} {contact.given_name.strip().lower()}".strip()


def _normalize_phone(number: str) -> str:
    return re.sub(r"[\s\-()]", "", number)


def find_duplicate_candidates(contacts: list[Contact]) -> list[DuplicateCandidate]:
    """Findet Kontaktpaare mit übereinstimmendem Namen, gemeinsamer E-Mail oder Telefonnummer."""
    reasons_by_pair: dict[tuple[str, str], list[str]] = {}

    def add_reason(uid_a: str, uid_b: str, reason: str):
        key = tuple(sorted((uid_a, uid_b)))
        pair_reasons = reasons_by_pair.setdefault(key, [])
        if reason not in pair_reasons:
            pair_reasons.append(reason)

    for i, a in enumerate(contacts):
        for b in contacts[i + 1:]:
            name_a = _normalize_name(a)
            if name_a and name_a == _normalize_name(b):
                add_reason(a.uid, b.uid, "gleicher Name")

            emails_a = {e.address.strip().lower() for e in a.emails if e.address.strip()}
            emails_b = {e.address.strip().lower() for e in b.emails if e.address.strip()}
            if emails_a & emails_b:
                add_reason(a.uid, b.uid, "gleiche E-Mail")

            phones_a = {_normalize_phone(p.number) for p in a.phones if p.number.strip()}
            phones_b = {_normalize_phone(p.number) for p in b.phones if p.number.strip()}
            if phones_a & phones_b:
                add_reason(a.uid, b.uid, "gleiche Telefonnummer")

    by_uid = {c.uid: c for c in contacts}
    return [
        DuplicateCandidate(by_uid[uid_a], by_uid[uid_b], reasons)
        for (uid_a, uid_b), reasons in reasons_by_pair.items()
    ]


def merge_contacts(primary: Contact, other: Contact, field_choices: dict[str, str]) -> Contact:
    """Führt `other` in `primary` zusammen.

    field_choices: Feldname -> "primary" oder "other" (die getroffene Auswahl).
    Ist der gewählte Wert leer, während die andere Seite einen Wert hat, gewinnt
    trotzdem die nicht-leere Seite – eine Auswahl kann nie dazu führen, dass eine
    vorhandene Angabe durch eine leere ersetzt wird.
    Listenfelder (Telefon/E-Mail/Adresse/...) werden automatisch vereinigt
    und nach Schlüsselattribut dedupliziert.
    """
    merged = replace(primary)

    for field in _SCALAR_FIELDS:
        choice = field_choices.get(field)
        chosen, fallback = (other, primary) if choice == "other" else (primary, other)
        chosen_val = getattr(chosen, field)
        setattr(merged, field, chosen_val if chosen_val else getattr(fallback, field))

    for field, key_fn in _LIST_FIELD_KEYS.items():
        primary_list = getattr(primary, field)
        seen = {key_fn(item) for item in primary_list}
        combined = list(primary_list)
        for item in getattr(other, field):
            key = key_fn(item)
            if key not in seen:
                combined.append(item)
                seen.add(key)
        setattr(merged, field, combined)

    merged.categories = list(dict.fromkeys(primary.categories + other.categories))
    merged.x_thunderbird_categories = list(dict.fromkeys(
        primary.x_thunderbird_categories + other.x_thunderbird_categories
    ))
    merged.uid = primary.uid
    return merged
