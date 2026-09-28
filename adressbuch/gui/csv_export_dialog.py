"""Dialog zur Konfiguration des CSV-Exports (Feldauswahl und Reihenfolge)."""

import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..storage.csv_export import FIELDS, FIELD_LABELS

_DEFAULT_SELECTED = ["given_name", "family_name", "phone", "email"]


class CsvExportDialog(tk.Toplevel):
    """Lässt den Benutzer Felder für den CSV-Export auswählen und anordnen."""

    def __init__(self, parent: tk.Tk, contact_count: int, on_export: Callable[[list[str], str], None]):
        super().__init__(parent)
        self.title("CSV-Export konfigurieren")
        self.resizable(True, True)
        self.geometry("620x460")
        self.grab_set()

        self._on_export = on_export
        self._contact_count = contact_count
        self._selected: list[str] = [k for k in _DEFAULT_SELECTED if k in FIELD_LABELS]
        self._delimiter_var = tk.StringVar(value=";")

        self._build_ui()
        self._refresh_lists()
        self.after(10, lambda: self._center(parent))

    def _build_ui(self):
        info = ttk.Label(self, text=f"{self._contact_count} Kontakt(e) werden exportiert.", padding=(8, 6))
        info.pack(fill="x")

        body = ttk.Frame(self, padding=(8, 0))
        body.pack(fill="both", expand=True)

        # Verfügbare Felder
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Verfügbare Felder").pack(anchor="w")
        self._available_list = tk.Listbox(left, selectmode="extended", exportselection=False)
        self._available_list.pack(fill="both", expand=True)

        # Mittlere Buttons
        mid = ttk.Frame(body, padding=(6, 20, 6, 0))
        mid.pack(side="left", fill="y")
        ttk.Button(mid, text="Alle →", command=self._add_all).pack(pady=2, fill="x")
        ttk.Button(mid, text="→", command=self._add_selected).pack(pady=2, fill="x")
        ttk.Button(mid, text="←", command=self._remove_selected).pack(pady=2, fill="x")
        ttk.Button(mid, text="← Alle", command=self._remove_all).pack(pady=2, fill="x")
        ttk.Separator(mid, orient="horizontal").pack(pady=8, fill="x")
        ttk.Button(mid, text="↑", command=self._move_up).pack(pady=2, fill="x")
        ttk.Button(mid, text="↓", command=self._move_down).pack(pady=2, fill="x")

        # Ausgewählte Felder (Exportreihenfolge)
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Ausgewählte Felder (Spaltenreihenfolge)").pack(anchor="w")
        self._selected_list = tk.Listbox(right, selectmode="extended", exportselection=False)
        self._selected_list.pack(fill="both", expand=True)

        # Trennzeichen
        delim_frame = ttk.Frame(self, padding=(8, 6))
        delim_frame.pack(fill="x")
        ttk.Label(delim_frame, text="Trennzeichen:").pack(side="left")
        ttk.Radiobutton(delim_frame, text="Semikolon (Excel, Deutschland)", value=";", variable=self._delimiter_var).pack(side="left", padx=(4, 0))
        ttk.Radiobutton(delim_frame, text="Komma", value=",", variable=self._delimiter_var).pack(side="left", padx=(8, 0))

        # Unten
        bottom = ttk.Frame(self, padding=(8, 6))
        bottom.pack(fill="x")
        ttk.Button(bottom, text="Abbrechen", command=self.destroy).pack(side="right", padx=(4, 0))
        self._export_btn = ttk.Button(bottom, text="Exportieren...", command=self._do_export)
        self._export_btn.pack(side="right")

    def _refresh_lists(self):
        self._available_list.delete(0, "end")
        for key, label, _ in FIELDS:
            if key not in self._selected:
                self._available_list.insert("end", label)
        self._available_list.field_keys = [k for k, _, _ in FIELDS if k not in self._selected]

        self._selected_list.delete(0, "end")
        for key in self._selected:
            self._selected_list.insert("end", FIELD_LABELS[key])
        self._export_btn.config(state="normal" if self._selected else "disabled")

    def _add_selected(self):
        keys = getattr(self._available_list, "field_keys", [])
        for i in self._available_list.curselection():
            key = keys[i]
            if key not in self._selected:
                self._selected.append(key)
        self._refresh_lists()

    def _add_all(self):
        for key, _, _ in FIELDS:
            if key not in self._selected:
                self._selected.append(key)
        self._refresh_lists()

    def _remove_selected(self):
        for i in self._selected_list.curselection():
            self._selected[i] = None
        self._selected = [k for k in self._selected if k is not None]
        self._refresh_lists()

    def _remove_all(self):
        self._selected = []
        self._refresh_lists()

    def _move_up(self):
        sel = list(self._selected_list.curselection())
        if not sel or sel[0] == 0:
            return
        for i in sel:
            self._selected[i - 1], self._selected[i] = self._selected[i], self._selected[i - 1]
        self._refresh_lists()
        for i in sel:
            self._selected_list.selection_set(i - 1)

    def _move_down(self):
        sel = list(self._selected_list.curselection())
        if not sel or sel[-1] == len(self._selected) - 1:
            return
        for i in reversed(sel):
            self._selected[i + 1], self._selected[i] = self._selected[i], self._selected[i + 1]
        self._refresh_lists()
        for i in sel:
            self._selected_list.selection_set(i + 1)

    def _do_export(self):
        field_keys = list(self._selected)
        delimiter = self._delimiter_var.get()
        self.destroy()
        self._on_export(field_keys, delimiter)

    def _center(self, parent: tk.Tk):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
