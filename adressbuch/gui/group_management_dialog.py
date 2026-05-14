"""Dialog zur Verwaltung von Gruppen (Umbenennen, Löschen)."""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import askstring
from typing import Callable

from ..storage.database import Database


class GroupManagementDialog(tk.Toplevel):
    """Zeigt alle Gruppen mit Kontaktanzahl und erlaubt Umbenennen und Löschen."""

    def __init__(self, parent: tk.Tk, db: Database, on_change: Callable):
        super().__init__(parent)
        self.title("Gruppenverwaltung")
        self.resizable(False, False)
        self.grab_set()

        self._db = db
        self._on_change = on_change

        self._build_ui()
        self._load()
        self.after(10, lambda: self._center(parent))

    def _build_ui(self):
        # Tabelle
        frame = ttk.Frame(self, padding=8)
        frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            frame,
            columns=("name", "count"),
            show="headings",
            selectmode="browse",
            height=10,
        )
        self._tree.heading("name",  text="Gruppe")
        self._tree.heading("count", text="Kontakte")
        self._tree.column("name",  width=250, minwidth=150)
        self._tree.column("count", width=80,  minwidth=60, anchor="center")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Buttons
        btn_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        btn_frame.pack(fill="x")

        self._rename_btn = ttk.Button(btn_frame, text="Umbenennen", command=self._rename, state="disabled")
        self._rename_btn.pack(side="left", padx=(0, 4))

        self._merge_btn = ttk.Button(btn_frame, text="Zusammenführen...", command=self._merge, state="disabled")
        self._merge_btn.pack(side="left", padx=(0, 4))

        self._delete_btn = ttk.Button(btn_frame, text="Löschen", command=self._delete, state="disabled")
        self._delete_btn.pack(side="left")

        ttk.Button(btn_frame, text="Schließen", command=self.destroy).pack(side="right")

    def _load(self):
        self._tree.delete(*self._tree.get_children())
        for gid, name in self._db.get_all_groups():
            count = self._db.count_contacts_in_group(gid)
            self._tree.insert("", "end", iid=str(gid), values=(name, count))
        self._rename_btn.config(state="disabled")
        self._delete_btn.config(state="disabled")

    def _on_select(self, _event=None):
        has_sel = bool(self._tree.selection())
        has_multiple = len(self._tree.get_children()) > 1
        state = "normal" if has_sel else "disabled"
        self._rename_btn.config(state=state)
        self._delete_btn.config(state=state)
        self._merge_btn.config(state="normal" if has_sel and has_multiple else "disabled")

    def _selected_group(self) -> tuple[int, str] | None:
        sel = self._tree.selection()
        if not sel:
            return None
        iid = sel[0]
        name = self._tree.item(iid, "values")[0]
        return int(iid), name

    def _rename(self):
        result = self._selected_group()
        if not result:
            return
        gid, old_name = result
        new_name = askstring("Umbenennen", "Neuer Gruppenname:", initialvalue=old_name, parent=self)
        if not new_name or not new_name.strip() or new_name.strip() == old_name:
            return
        self._db.rename_group(gid, new_name.strip())
        self._load()
        self._on_change()

    def _merge(self):
        result = self._selected_group()
        if not result:
            return
        source_id, source_name = result

        other_groups = [
            (int(iid), self._tree.item(iid, "values")[0])
            for iid in self._tree.get_children()
            if int(iid) != source_id
        ]
        if not other_groups:
            return

        dlg = _MergeTargetDialog(self, source_name, other_groups)
        self.wait_window(dlg)
        if dlg.result is None:
            return

        target_id, target_name = dlg.result
        count = self._db.count_contacts_in_group(source_id)
        msg = f'Gruppe "{source_name}" ({count} Kontakte) in "{target_name}" zusammenführen?\n\n"{source_name}" wird anschließend gelöscht.'
        if not messagebox.askyesno("Zusammenführen", msg, parent=self):
            return
        self._db.merge_groups(source_id, target_id)
        self._load()
        self._on_change()

    def _delete(self):
        result = self._selected_group()
        if not result:
            return
        gid, name = result
        count = self._db.count_contacts_in_group(gid)
        msg = f'Gruppe "{name}" mit {count} Kontakt(en) wirklich löschen?\n\nDie Kontakte selbst bleiben erhalten.'
        if not messagebox.askyesno("Gruppe löschen", msg, parent=self):
            return
        self._db.delete_group(gid)
        self._load()
        self._on_change()

    def _center(self, parent: tk.Tk):
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


class _MergeTargetDialog(tk.Toplevel):
    """Auswahl der Zielgruppe beim Zusammenführen."""

    def __init__(self, parent: tk.Toplevel, source_name: str, groups: list[tuple[int, str]]):
        super().__init__(parent)
        self.title("Zielgruppe wählen")
        self.resizable(False, False)
        self.grab_set()
        self.result: tuple[int, str] | None = None

        ttk.Label(self, text=f'"{source_name}" zusammenführen mit:', padding=(12, 8)).pack()

        self._var = tk.StringVar(value=groups[0][1])
        self._groups = groups
        cb = ttk.Combobox(self, textvariable=self._var, state="readonly",
                          values=[n for _, n in groups], width=30)
        cb.pack(padx=12, pady=(0, 8))

        btn = ttk.Frame(self, padding=(12, 0, 12, 12))
        btn.pack(fill="x")
        ttk.Button(btn, text="Abbrechen", command=self.destroy).pack(side="right", padx=(4, 0))
        ttk.Button(btn, text="OK", command=self._ok).pack(side="right")

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _ok(self):
        name = self._var.get()
        for gid, gname in self._groups:
            if gname == name:
                self.result = (gid, gname)
                break
        self.destroy()
