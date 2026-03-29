"""Wiederverwendbare Widget-Helfer für tkinter."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


def labeled_entry(
    parent,
    label: str,
    row: int,
    col: int = 0,
    width: int = 30,
    colspan: int = 1,
) -> tk.StringVar:
    """Erstellt Label + Entry und gibt die StringVar zurück."""
    ttk.Label(parent, text=label).grid(
        row=row, column=col, sticky="e", padx=(4, 2), pady=2
    )
    var = tk.StringVar()
    ttk.Entry(parent, textvariable=var, width=width).grid(
        row=row, column=col + 1, columnspan=colspan, sticky="ew", padx=(2, 4), pady=2
    )
    return var


def labeled_combo(
    parent,
    label: str,
    row: int,
    values: list[str],
    col: int = 0,
    width: int = 15,
) -> tk.StringVar:
    """Erstellt Label + Combobox und gibt die StringVar zurück."""
    ttk.Label(parent, text=label).grid(
        row=row, column=col, sticky="e", padx=(4, 2), pady=2
    )
    var = tk.StringVar()
    combo = ttk.Combobox(parent, textvariable=var, values=values, width=width)
    combo.grid(row=row, column=col + 1, sticky="ew", padx=(2, 4), pady=2)
    return var


class MultiEntryFrame(ttk.LabelFrame):
    """
    Rahmen für dynamische Listen (Telefon, E-Mail, ...).
    Jede Zeile hat ein Entry + Typ-Auswahl + Löschen-Button.
    """

    def __init__(
        self,
        parent,
        title: str,
        type_options: list[str],
        *,
        on_change: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(parent, text=title, **kwargs)
        self.type_options = type_options
        self.on_change = on_change
        self._rows: list[tuple[tk.StringVar, tk.StringVar, tk.BooleanVar]] = []
        self._frame = ttk.Frame(self)
        self._frame.pack(fill="x", expand=True)
        ttk.Button(self, text="+ Hinzufügen", command=self.add_row).pack(
            anchor="w", padx=4, pady=(0, 4)
        )

    def add_row(
        self,
        value: str = "",
        type_val: str = "",
        preferred: bool = False,
    ) -> tuple[tk.StringVar, tk.StringVar, tk.BooleanVar]:
        row_idx = len(self._rows)
        val_var = tk.StringVar(value=value)
        type_var = tk.StringVar(value=type_val or (self.type_options[0] if self.type_options else ""))
        pref_var = tk.BooleanVar(value=preferred)

        entry = ttk.Entry(self._frame, textvariable=val_var, width=28)
        entry.grid(row=row_idx, column=0, sticky="ew", padx=2, pady=1)

        combo = ttk.Combobox(
            self._frame, textvariable=type_var,
            values=self.type_options, width=10
        )
        combo.grid(row=row_idx, column=1, padx=2, pady=1)

        ttk.Checkbutton(
            self._frame, text="Bevorzugt", variable=pref_var
        ).grid(row=row_idx, column=2, padx=2)

        ttk.Button(
            self._frame, text="✕",
            command=lambda idx=row_idx: self._remove_row(idx)
        ).grid(row=row_idx, column=3, padx=2)

        self._frame.columnconfigure(0, weight=1)
        self._rows.append((val_var, type_var, pref_var))
        if self.on_change:
            self.on_change()
        return val_var, type_var, pref_var

    def _remove_row(self, idx: int):
        # Alle Widgets in der Zeile entfernen
        for widget in self._frame.grid_slaves(row=idx):
            widget.destroy()
        self._rows[idx] = None  # type: ignore
        if self.on_change:
            self.on_change()

    def get_values(self) -> list[tuple[str, str, bool]]:
        """Gibt (Wert, Typ, Bevorzugt) für alle nicht gelöschten Zeilen zurück."""
        result = []
        for row in self._rows:
            if row is None:
                continue
            val, typ, pref = row
            if val.get().strip():
                result.append((val.get().strip(), typ.get(), pref.get()))
        return result

    def clear(self):
        for widget in self._frame.winfo_children():
            widget.destroy()
        self._rows.clear()
