"""Dialog zum Finden und Zusammenführen von Kontakt-Dubletten."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..models.contact import Contact
from ..storage.database import Database
from ..storage.duplicates import DuplicateCandidate, find_duplicate_candidates, merge_contacts

_FIELD_LABELS = {
    "family_name": "Nachname",
    "given_name": "Vorname",
    "additional_names": "Weitere Vornamen",
    "honorific_prefix": "Titel/Anrede",
    "honorific_suffix": "Namenszusatz",
    "display_name": "Anzeigename",
    "nickname": "Spitzname",
    "gender": "Geschlecht",
    "organization": "Firma",
    "org_unit": "Abteilung",
    "title": "Berufsbezeichnung",
    "role": "Funktion",
    "note": "Notiz",
    "birthday": "Geburtstag",
    "anniversary": "Jahrestag",
    "deathdate": "Todestag",
}

_LIST_FIELD_LABELS = {
    "phones": ("Telefon", lambda p: p.number),
    "emails": ("E-Mail", lambda e: e.address),
    "addresses": ("Adresse", lambda a: ", ".join(filter(None, [a.street, a.postal_code, a.city]))),
}


def _format_value(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")
    return str(value)


class DuplicateManagerDialog(tk.Toplevel):
    """Findet mögliche Kontakt-Dubletten und erlaubt den Vergleich/Merge."""

    def __init__(self, parent: tk.Tk, db: Database, on_change: Callable):
        super().__init__(parent)
        self.title("Dubletten finden")
        self.geometry("640x340")
        self.resizable(True, True)
        self.grab_set()

        self._db = db
        self._on_change = on_change
        self._candidates: list[DuplicateCandidate] = []

        self._build_ui()
        self._load()
        self.after(10, lambda: self._center(parent))

    def _build_ui(self):
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            frame,
            columns=("a", "b", "reason"),
            show="headings",
            selectmode="browse",
            height=10,
        )
        self._tree.heading("a", text="Kontakt A")
        self._tree.heading("b", text="Kontakt B")
        self._tree.heading("reason", text="Grund")
        self._tree.column("a", width=180, minwidth=120)
        self._tree.column("b", width=180, minwidth=120)
        self._tree.column("reason", width=240, minwidth=150)

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        btn_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        btn_frame.pack(fill="x")

        self._compare_btn = ttk.Button(btn_frame, text="Vergleichen...", command=self._compare, state="disabled")
        self._compare_btn.pack(side="left", padx=(0, 4))

        self._ignore_btn = ttk.Button(btn_frame, text="Ignorieren", command=self._ignore, state="disabled")
        self._ignore_btn.pack(side="left")

        ttk.Button(btn_frame, text="Schließen", command=self.destroy).pack(side="right")

    def _load(self):
        self._candidates = find_duplicate_candidates(self._db.all())
        self._tree.delete(*self._tree.get_children())
        for i, cand in enumerate(self._candidates):
            self._tree.insert("", "end", iid=str(i), values=(
                cand.contact_a.get_display_name(),
                cand.contact_b.get_display_name(),
                ", ".join(cand.reasons),
            ))
        self._compare_btn.config(state="disabled")
        self._ignore_btn.config(state="disabled")
        if not self._candidates:
            self._tree.insert("", "end", values=("Keine Dubletten gefunden", "", ""))

    def _on_select(self, _event=None):
        sel = self._tree.selection()
        has_sel = bool(sel) and sel[0].isdigit()
        state = "normal" if has_sel else "disabled"
        self._compare_btn.config(state=state)
        self._ignore_btn.config(state=state)

    def _selected_candidate(self) -> DuplicateCandidate | None:
        sel = self._tree.selection()
        if not sel or not sel[0].isdigit():
            return None
        return self._candidates[int(sel[0])]

    def _compare(self):
        candidate = self._selected_candidate()
        if not candidate:
            return
        dlg = _CompareDialog(self, candidate.contact_a, candidate.contact_b)
        self.wait_window(dlg)
        if dlg.result is None:
            return
        primary, other, field_choices = dlg.result
        merged = merge_contacts(primary, other, field_choices)
        self._db.save(merged)
        self._db.reassign_contact_groups(other.uid, primary.uid)
        self._db.delete(other.uid)
        self._load()
        self._on_change()

    def _ignore(self):
        candidate = self._selected_candidate()
        if not candidate:
            return
        self._candidates.remove(candidate)
        self._tree.delete(*self._tree.get_children())
        for i, cand in enumerate(self._candidates):
            self._tree.insert("", "end", iid=str(i), values=(
                cand.contact_a.get_display_name(),
                cand.contact_b.get_display_name(),
                ", ".join(cand.reasons),
            ))
        self._compare_btn.config(state="disabled")
        self._ignore_btn.config(state="disabled")

    def _center(self, parent: tk.Tk):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class _CompareDialog(tk.Toplevel):
    """Seite-an-Seite-Vergleich zweier Kontakte zur Zusammenführung."""

    def __init__(self, parent: tk.Toplevel, contact_a: Contact, contact_b: Contact):
        super().__init__(parent)
        self.title("Kontakte vergleichen")
        self.resizable(True, True)
        self.grab_set()
        self.result: tuple[Contact, Contact, dict[str, str]] | None = None

        self._a = contact_a
        self._b = contact_b
        self._primary_var = tk.StringVar(value="a")
        self._field_vars: dict[str, tk.StringVar] = {}
        self._manually_touched: set[str] = set()

        self._build_ui()
        self._apply_primary_defaults()
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        # Wer bleibt erhalten?
        head = ttk.Frame(outer)
        head.pack(fill="x", pady=(0, 12))
        ttk.Label(head, text="Kontakt behalten (Rest wird gelöscht):", font=("", 9, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Radiobutton(
            head, text=self._a.get_display_name(), variable=self._primary_var, value="a",
            command=self._on_primary_change
        ).grid(row=1, column=0, sticky="w", padx=(0, 24))
        ttk.Radiobutton(
            head, text=self._b.get_display_name(), variable=self._primary_var, value="b",
            command=self._on_primary_change
        ).grid(row=1, column=1, sticky="w")

        # Unterschiedliche Felder (auch wenn nur eine Seite ausgefüllt ist)
        diffs = [f for f in _FIELD_LABELS if getattr(self._a, f) != getattr(self._b, f)]
        if diffs:
            fields_frame = ttk.LabelFrame(outer, text="Abweichende Angaben – Wert auswählen", padding=8)
            fields_frame.pack(fill="x", pady=(0, 12))
            for row, field in enumerate(diffs):
                var = tk.StringVar(value="a")
                self._field_vars[field] = var
                ttk.Label(fields_frame, text=_FIELD_LABELS[field] + ":", width=18, anchor="w").grid(
                    row=row, column=0, sticky="w", pady=2)
                ttk.Radiobutton(
                    fields_frame, text=_format_value(getattr(self._a, field)) or "(leer)",
                    variable=var, value="a",
                    command=lambda f=field: self._manually_touched.add(f)
                ).grid(row=row, column=1, sticky="w", padx=(0, 16))
                ttk.Radiobutton(
                    fields_frame, text=_format_value(getattr(self._b, field)) or "(leer)",
                    variable=var, value="b",
                    command=lambda f=field: self._manually_touched.add(f)
                ).grid(row=row, column=2, sticky="w")
        else:
            ttk.Label(outer, text="Keine abweichenden Einzelangaben – nur Listenfelder werden zusammengeführt.").pack(
                anchor="w", pady=(0, 12))

        # Listenfelder informativ
        list_frame = ttk.LabelFrame(outer, text="Werden automatisch zusammengeführt", padding=8)
        list_frame.pack(fill="x", pady=(0, 12))
        row = 0
        any_list_shown = False
        for field, (label, fmt) in _LIST_FIELD_LABELS.items():
            items_a = [fmt(x) for x in getattr(self._a, field)]
            items_b = [fmt(x) for x in getattr(self._b, field)]
            if not items_a and not items_b:
                continue
            any_list_shown = True
            ttk.Label(list_frame, text=label + ":", width=18, anchor="w").grid(row=row, column=0, sticky="nw", pady=2)
            ttk.Label(list_frame, text="\n".join(items_a) or "–").grid(row=row, column=1, sticky="nw", padx=(0, 16))
            ttk.Label(list_frame, text="\n".join(items_b) or "–").grid(row=row, column=2, sticky="nw")
            row += 1
        if not any_list_shown:
            list_frame.destroy()

        btn = ttk.Frame(outer)
        btn.pack(fill="x", pady=(4, 0))
        ttk.Button(btn, text="Abbrechen", command=self.destroy).pack(side="right")
        ttk.Button(btn, text="Zusammenführen", command=self._confirm).pack(side="right", padx=(0, 4))

    def _apply_primary_defaults(self):
        """Setzt jede noch nicht manuell geänderte Feldauswahl auf die Seite des aktuell
        gewählten Hauptkontakts – unabhängig davon, ob dessen Wert leer ist. Manuell
        gewählte Felder bleiben beim Wechsel des Hauptkontakts erhalten."""
        primary_side = "a" if self._primary_var.get() == "a" else "b"
        for field, var in self._field_vars.items():
            if field not in self._manually_touched:
                var.set(primary_side)

    def _on_primary_change(self):
        self._apply_primary_defaults()

    def _confirm(self):
        primary_is_a = self._primary_var.get() == "a"
        primary, other = (self._a, self._b) if primary_is_a else (self._b, self._a)

        field_choices: dict[str, str] = {}
        for field, var in self._field_vars.items():
            chosen_is_a = var.get() == "a"
            field_choices[field] = "primary" if chosen_is_a == primary_is_a else "other"

        self.result = (primary, other, field_choices)
        self.destroy()
