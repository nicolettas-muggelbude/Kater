"""Kontaktformular - Alle vCard-Felder bearbeitbar."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable

from ..models.contact import Contact, Phone, Email, Address, Url, InstantMessaging
from .widgets import labeled_entry, labeled_combo, MultiEntryFrame


PHONE_TYPES = ["voice", "cell", "home", "work", "fax", "pager", "text", "video"]
EMAIL_TYPES = ["internet", "home", "work"]
GENDER_OPTIONS = ["", "M", "F", "O", "N", "U"]
IM_TYPES = ["xmpp", "matrix", "signal", "telegram", "other"]


class ContactForm(ttk.Frame):
    """
    Vollständiges Kontaktformular mit Tabs für alle vCard-Felder.
    Aufruf: form.load(contact) zum Befüllen, form.get_contact() zum Auslesen.
    """

    def __init__(self, parent, on_save: Callable[[Contact], None], **kwargs):
        super().__init__(parent, **kwargs)
        self.on_save = on_save
        self._contact: Optional[Contact] = None
        self._build_ui()

    def _build_ui(self):
        # Notebook mit Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=4, pady=4)

        self._build_tab_basis()
        self._build_tab_kontakt()
        self._build_tab_adressen()
        self._build_tab_organisation()
        self._build_tab_persoenlich()
        self._build_tab_notiz()

        # Speichern-Button
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=4, pady=4)
        ttk.Button(btn_frame, text="Speichern", command=self._save).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="Zurücksetzen", command=self._reset).pack(side="right")

    # --- Tabs ---

    def _build_tab_basis(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Name")

        f = ttk.Frame(tab)
        f.pack(fill="both", expand=True, padx=8, pady=8)
        f.columnconfigure(1, weight=1)

        self._v_prefix = labeled_entry(f, "Titel/Anrede:", 0, width=15)
        self._v_given = labeled_entry(f, "Vorname:", 1)
        self._v_additional = labeled_entry(f, "Weitere Vornamen:", 2)
        self._v_family = labeled_entry(f, "Nachname:", 3)
        self._v_suffix = labeled_entry(f, "Namenszusatz:", 4, width=15)
        self._v_display = labeled_entry(f, "Anzeigename:", 5)
        self._v_nickname = labeled_entry(f, "Spitzname:", 6)
        self._v_gender = labeled_combo(
            f, "Geschlecht:", 7, GENDER_OPTIONS, width=5
        )

        ttk.Label(f, text="(Anzeigename leer lassen für automatische Generierung)",
                  foreground="gray").grid(
            row=8, column=1, sticky="w", padx=4
        )

    def _build_tab_kontakt(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Kontakt")

        canvas = tk.Canvas(tab, borderwidth=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        self._kontakt_inner = ttk.Frame(canvas)

        self._kontakt_inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self._kontakt_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._phone_frame = MultiEntryFrame(
            self._kontakt_inner, "Telefon", PHONE_TYPES, padding=4
        )
        self._phone_frame.pack(fill="x", padx=4, pady=4)

        self._email_frame = MultiEntryFrame(
            self._kontakt_inner, "E-Mail", EMAIL_TYPES, padding=4
        )
        self._email_frame.pack(fill="x", padx=4, pady=4)

        self._url_frame = MultiEntryFrame(
            self._kontakt_inner, "Webseite", [], padding=4
        )
        self._url_frame.pack(fill="x", padx=4, pady=4)

        self._im_frame = MultiEntryFrame(
            self._kontakt_inner, "Instant Messaging (URI)", IM_TYPES, padding=4
        )
        self._im_frame.pack(fill="x", padx=4, pady=4)

    def _build_tab_adressen(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Adressen")

        addr_nb = ttk.Notebook(tab)
        addr_nb.pack(fill="both", expand=True, padx=4, pady=4)

        self._addr_vars: dict[str, dict] = {}
        for key, title in [("home", "Privat"), ("work", "Arbeit"), ("other", "Sonstige")]:
            sub = ttk.Frame(addr_nb)
            addr_nb.add(sub, text=title)
            sub.columnconfigure(1, weight=1)
            v_street   = labeled_entry(sub, "Straße:", 0)
            v_extended = labeled_entry(sub, "Adresszusatz:", 1)
            v_postal   = labeled_entry(sub, "PLZ:", 2, width=10)
            v_city     = labeled_entry(sub, "Ort:", 3)
            v_region   = labeled_entry(sub, "Bundesland:", 4)
            v_country  = labeled_entry(sub, "Land:", 5)
            v_pobox    = labeled_entry(sub, "Postfach:", 6)
            v_pref     = tk.BooleanVar()
            ttk.Checkbutton(sub, text="Bevorzugt", variable=v_pref).grid(
                row=7, column=1, sticky="w", pady=4
            )
            self._addr_vars[key] = {
                "street": v_street, "extended": v_extended, "postal": v_postal,
                "city": v_city, "region": v_region, "country": v_country,
                "pobox": v_pobox, "preferred": v_pref,
            }

    def _build_tab_organisation(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Organisation")

        f = ttk.Frame(tab)
        f.pack(fill="both", expand=True, padx=8, pady=8)
        f.columnconfigure(1, weight=1)

        self._v_org = labeled_entry(f, "Firma:", 0)
        self._v_org_unit = labeled_entry(f, "Abteilung:", 1)
        self._v_title = labeled_entry(f, "Berufsbezeichnung:", 2)
        self._v_role = labeled_entry(f, "Funktion:", 3)

    def _build_tab_persoenlich(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Persönlich")

        f = ttk.Frame(tab)
        f.pack(fill="both", expand=True, padx=8, pady=8)
        f.columnconfigure(1, weight=1)

        # Datumsfelder als Text (TT.MM.JJJJ)
        self._v_birthday = labeled_entry(f, "Geburtstag:", 0, width=12)
        ttk.Label(f, text="(Format: TT.MM.JJJJ)", foreground="gray").grid(
            row=0, column=2, sticky="w"
        )
        self._v_anniversary = labeled_entry(f, "Jahrestag:", 1, width=12)
        ttk.Label(f, text="(Format: TT.MM.JJJJ)", foreground="gray").grid(
            row=1, column=2, sticky="w"
        )
        self._v_deathdate = labeled_entry(f, "Sterbetag:", 2, width=12)
        ttk.Label(f, text="(Format: TT.MM.JJJJ)", foreground="gray").grid(
            row=2, column=2, sticky="w"
        )

        ttk.Separator(f, orient="horizontal").grid(
            row=3, column=0, columnspan=3, sticky="ew", pady=8
        )

        self._v_lang = labeled_entry(f, "Sprachen:", 4)
        ttk.Label(f, text="(kommagetrennt)", foreground="gray").grid(
            row=4, column=2, sticky="w"
        )
        self._v_tz = labeled_entry(f, "Zeitzone:", 5)
        self._v_categories = labeled_entry(f, "Kategorien:", 6)
        ttk.Label(f, text="(kommagetrennt)", foreground="gray").grid(
            row=6, column=2, sticky="w"
        )

    def _build_tab_notiz(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Notiz")

        ttk.Label(tab, text="Notiz:").pack(anchor="w", padx=8, pady=(8, 2))
        self._txt_note = tk.Text(tab, height=10, wrap="word")
        self._txt_note.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # --- Daten ---

    def load(self, contact: Contact):
        """Füllt das Formular mit einem Kontakt."""
        self._contact = contact
        self._reset_fields()

        # Name
        self._v_prefix.set(contact.honorific_prefix)
        self._v_given.set(contact.given_name)
        self._v_additional.set(contact.additional_names)
        self._v_family.set(contact.family_name)
        self._v_suffix.set(contact.honorific_suffix)
        self._v_display.set(contact.display_name)
        self._v_nickname.set(contact.nickname)
        self._v_gender.set(contact.gender)

        # Kontakt
        for phone in contact.phones:
            self._phone_frame.add_row(
                phone.number,
                phone.types[0] if phone.types else "voice",
                phone.preferred
            )
        for email in contact.emails:
            self._email_frame.add_row(
                email.address,
                email.types[0] if email.types else "internet",
                email.preferred
            )
        for url in contact.urls:
            self._url_frame.add_row(url.url, "", False)
        for im in contact.instant_messaging:
            self._im_frame.add_row(
                im.uri,
                im.types[0] if im.types else "xmpp",
                im.preferred
            )

        # Adressen (erste Adresse je Typ laden)
        for addr in contact.addresses:
            key = addr.label if addr.label in self._addr_vars else "other"
            d = self._addr_vars[key]
            if d["street"].get() or d["city"].get():
                continue  # bereits belegt, ersten Eintrag behalten
            d["street"].set(addr.street)
            d["extended"].set(addr.extended)
            d["postal"].set(addr.postal_code)
            d["city"].set(addr.city)
            d["region"].set(addr.region)
            d["country"].set(addr.country)
            d["pobox"].set(addr.po_box)
            d["preferred"].set(addr.preferred)

        # Organisation
        self._v_org.set(contact.organization)
        self._v_org_unit.set(contact.org_unit)
        self._v_title.set(contact.title)
        self._v_role.set(contact.role)

        # Persönlich
        if contact.birthday:
            self._v_birthday.set(contact.birthday.strftime("%d.%m.%Y"))
        if contact.anniversary:
            self._v_anniversary.set(contact.anniversary.strftime("%d.%m.%Y"))
        if contact.deathdate:
            self._v_deathdate.set(contact.deathdate.strftime("%d.%m.%Y"))
        self._v_lang.set(", ".join(contact.languages))
        self._v_tz.set(contact.timezone)
        self._v_categories.set(", ".join(contact.categories))

        # Notiz
        self._txt_note.delete("1.0", "end")
        self._txt_note.insert("1.0", contact.note)

    def _reset_fields(self):
        """Leert alle Formularfelder."""
        for var in [
            self._v_prefix, self._v_given, self._v_additional,
            self._v_family, self._v_suffix, self._v_display,
            self._v_nickname, self._v_gender,
            self._v_org, self._v_org_unit, self._v_title, self._v_role,
            self._v_birthday, self._v_anniversary, self._v_deathdate,
            self._v_lang, self._v_tz, self._v_categories,
        ]:
            var.set("")
        self._phone_frame.clear()
        self._email_frame.clear()
        self._url_frame.clear()
        self._im_frame.clear()
        for d in self._addr_vars.values():
            for key, var in d.items():
                var.set(False if key == "preferred" else "")
        self._txt_note.delete("1.0", "end")

    def _parse_date(self, value: str) -> Optional[date]:
        value = value.strip()
        if not value:
            return None
        # Deutsches Format TT.MM.JJJJ
        if "." in value:
            try:
                return date(
                    int(value[6:10]),
                    int(value[3:5]),
                    int(value[0:2]),
                )
            except (ValueError, IndexError):
                pass
        # ISO-Format YYYY-MM-DD als Fallback
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
        messagebox.showwarning(
            "Ungültiges Datum",
            f"'{value}' ist kein gültiges Datum.\nErwartet: TT.MM.JJJJ (z.B. 31.03.1990)"
        )
        return None

    def get_contact(self) -> Contact:
        """Liest das Formular aus und gibt einen Contact zurück."""
        c = self._contact or Contact()

        c.honorific_prefix = self._v_prefix.get().strip()
        c.given_name = self._v_given.get().strip()
        c.additional_names = self._v_additional.get().strip()
        c.family_name = self._v_family.get().strip()
        c.honorific_suffix = self._v_suffix.get().strip()
        c.display_name = self._v_display.get().strip()
        c.nickname = self._v_nickname.get().strip()
        c.gender = self._v_gender.get().strip()

        c.phones = [
            Phone(number=v, types=[t], preferred=p)
            for v, t, p in self._phone_frame.get_values()
        ]
        c.emails = [
            Email(address=v, types=[t], preferred=p)
            for v, t, p in self._email_frame.get_values()
        ]
        c.urls = [
            Url(url=v) for v, _, _ in self._url_frame.get_values()
        ]
        c.instant_messaging = [
            InstantMessaging(uri=v, types=[t], preferred=p)
            for v, t, p in self._im_frame.get_values()
        ]

        c.addresses = []
        for label, d in self._addr_vars.items():
            street = d["street"].get().strip()
            city   = d["city"].get().strip()
            if not street and not city:
                continue
            c.addresses.append(Address(
                label=label,
                street=street,
                extended=d["extended"].get().strip(),
                postal_code=d["postal"].get().strip(),
                city=city,
                region=d["region"].get().strip(),
                country=d["country"].get().strip(),
                po_box=d["pobox"].get().strip(),
                preferred=d["preferred"].get(),
            ))

        c.organization = self._v_org.get().strip()
        c.org_unit = self._v_org_unit.get().strip()
        c.title = self._v_title.get().strip()
        c.role = self._v_role.get().strip()

        c.birthday = self._parse_date(self._v_birthday.get())
        c.anniversary = self._parse_date(self._v_anniversary.get())
        c.deathdate = self._parse_date(self._v_deathdate.get())

        langs = self._v_lang.get().strip()
        c.languages = [l.strip() for l in langs.split(",") if l.strip()] if langs else []

        c.timezone = self._v_tz.get().strip()

        cats = self._v_categories.get().strip()
        c.categories = [x.strip() for x in cats.split(",") if x.strip()] if cats else []

        c.note = self._txt_note.get("1.0", "end").strip()

        return c

    def _save(self):
        contact = self.get_contact()
        if not contact.family_name and not contact.given_name and not contact.organization:
            messagebox.showwarning(
                "Unvollständig",
                "Bitte mindestens Name oder Firma angeben."
            )
            return
        self.on_save(contact)

    def _reset(self):
        if self._contact:
            self.load(self._contact)
        else:
            self._reset_fields()

    def new_contact(self):
        """Formular für neuen Kontakt leeren."""
        self._contact = None
        self._reset_fields()
