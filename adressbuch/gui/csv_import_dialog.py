"""Vorschau-Dialog für den CSV-Import mit Kontaktauswahl."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..models.contact import Contact


class CsvImportDialog(tk.Toplevel):
    """Zeigt importierte Kontakte zur Auswahl an, mit optionaler Gruppenzuweisung."""

    _CHECKED   = "☑"
    _UNCHECKED = "☐"

    def __init__(
        self,
        parent: tk.Tk,
        contacts: list[Contact],
        filename: str,
        on_import: Callable[[list[Contact], str], None],
    ):
        super().__init__(parent)
        self.title(f"CSV-Import: {filename}")
        self.resizable(True, True)
        self.geometry("680x500")
        self.grab_set()

        self._contacts  = contacts
        self._on_import = on_import
        self._checked: dict[str, bool] = {}

        self._build_ui()
        self._populate()
        self._update_count()
        self.after(10, lambda: self._center(parent))

    # --- UI-Aufbau ---

    def _build_ui(self):
        # Kopfzeile: Info + Alle/Keine
        top = ttk.Frame(self, padding=(8, 6))
        top.pack(fill="x")

        self._info_label = ttk.Label(top, text="")
        self._info_label.pack(side="left")

        ttk.Button(top, text="Keine", command=self._select_none).pack(side="right", padx=(2, 0))
        ttk.Button(top, text="Alle",  command=self._select_all).pack(side="right")

        # Kontakttabelle
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self._tree = ttk.Treeview(
            tree_frame,
            columns=("check", "name", "email"),
            show="headings",
            selectmode="none",
        )
        self._tree.heading("check", text="")
        self._tree.heading("name",  text="Name")
        self._tree.heading("email", text="E-Mail")
        self._tree.column("check", width=32,  minwidth=32,  stretch=False, anchor="center")
        self._tree.column("name",  width=230, minwidth=120)
        self._tree.column("email", width=280, minwidth=120)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<Button-1>", self._on_click)

        # Fußzeile: optionaler Gruppenname + Buttons
        bottom = ttk.Frame(self, padding=(8, 6))
        bottom.pack(fill="x")

        self._group_var = tk.StringVar()
        ttk.Label(bottom, text="Als Gruppe importieren (optional):").pack(side="left")
        ttk.Entry(bottom, textvariable=self._group_var, width=22).pack(side="left", padx=(4, 16))

        ttk.Button(bottom, text="Abbrechen",  command=self.destroy).pack(side="right", padx=(4, 0))
        self._import_btn = ttk.Button(bottom, text="Importieren", command=self._do_import)
        self._import_btn.pack(side="right")

    # --- Daten ---

    def _populate(self):
        for c in self._contacts:
            iid = self._tree.insert(
                "", "end",
                values=(self._CHECKED, c.get_display_name(), self._primary_email(c))
            )
            self._checked[iid] = True

    @staticmethod
    def _primary_email(c: Contact) -> str:
        for e in c.emails:
            if e.preferred:
                return e.address
        return c.emails[0].address if c.emails else ""

    # --- Interaktion ---

    def _on_click(self, event):
        if self._tree.identify_region(event.x, event.y) != "cell":
            return
        iid = self._tree.identify_row(event.y)
        if iid:
            self._toggle(iid)

    def _toggle(self, iid: str):
        self._checked[iid] = not self._checked[iid]
        vals = list(self._tree.item(iid, "values"))
        vals[0] = self._CHECKED if self._checked[iid] else self._UNCHECKED
        self._tree.item(iid, values=vals)
        self._update_count()

    def _select_all(self):
        for iid in self._checked:
            self._checked[iid] = True
            vals = list(self._tree.item(iid, "values"))
            vals[0] = self._CHECKED
            self._tree.item(iid, values=vals)
        self._update_count()

    def _select_none(self):
        for iid in self._checked:
            self._checked[iid] = False
            vals = list(self._tree.item(iid, "values"))
            vals[0] = self._UNCHECKED
            self._tree.item(iid, values=vals)
        self._update_count()

    def _update_count(self):
        total    = len(self._checked)
        selected = sum(1 for v in self._checked.values() if v)
        self._info_label.config(text=f"{selected} von {total} Kontakten ausgewählt")
        self._import_btn.config(state="normal" if selected > 0 else "disabled")

    def _do_import(self):
        iids = list(self._tree.get_children())
        selected = [
            self._contacts[i]
            for i, iid in enumerate(iids)
            if self._checked.get(iid, False)
        ]
        group_name = self._group_var.get().strip()
        self.destroy()
        self._on_import(selected, group_name)

    def _center(self, parent: tk.Tk):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
