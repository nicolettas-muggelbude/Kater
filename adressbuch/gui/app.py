"""Hauptfenster der Adressbuch-App (tkinter)."""

import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional

from .. import __version__
from ..models.contact import Contact
from ..storage.database import Database
from ..storage.vcard import VCardParser, VCardExporter
from .utils import resolve_asset
from .contact_form import ContactForm
from .qr_dialog import QRDialog


class AdressbuchApp(tk.Tk):
    """Hauptfenster."""

    def __init__(self, db_path: str | Path):
        super().__init__()
        self.title(f"Kater v{__version__}")
        self.geometry("1000x700+100+100")
        self.minsize(700, 500)
        self.update()
        self.deiconify()
        self.state('normal')
        self.lift()
        self.focus_force()

        self.db = Database(db_path)
        self._selected_uid: Optional[str] = None

        self._build_ui()
        self._load_contacts()
        self.after(3000, self._start_update_check)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Fenster-Icon
        try:
            from PIL import Image, ImageTk
            _icon = ImageTk.PhotoImage(Image.open(resolve_asset("kater-logo.png")).resize((32, 32)))
            self.iconphoto(True, _icon)
            self._icon_ref = _icon  # Referenz halten damit GC es nicht löscht
        except Exception:
            pass

        # Menüleiste
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Neuer Kontakt", command=self._new_contact, accelerator="Ctrl+N")
        file_menu.add_separator()

        tb_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Thunderbird / vCard", menu=tb_menu)
        tb_menu.add_command(label="Importieren...", command=self._import_vcard)
        tb_menu.add_separator()
        tb_menu.add_command(label="Aktuellen Kontakt exportieren...", command=self._export_vcard)
        tb_menu.add_command(label="Markierte Kontakte exportieren...", command=self._export_selected)
        tb_menu.add_command(label="Alle Kontakte exportieren...", command=self._export_all)

        file_menu.add_command(label="Als QR-Code anzeigen", command=self._show_qr, accelerator="Ctrl+Q")
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self._on_close)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Bearbeiten", menu=edit_menu)
        edit_menu.add_command(label="Als vCard kopieren", command=self._copy_to_clipboard, accelerator="Ctrl+Shift+C")
        edit_menu.add_separator()
        edit_menu.add_command(label="Kontakt löschen", command=self._delete_contact, accelerator="Del")

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        help_menu.add_command(label="Über Kater...", command=self._show_about)

        # Kopfzeile mit Logo und Titel
        self._build_header()

        # Tastenkürzel
        self.bind("<Control-n>", lambda e: self._new_contact())
        self.bind("<Control-q>", lambda e: self._show_qr())
        self.bind("<Control-C>", lambda e: self._copy_to_clipboard())
        self.bind("<Delete>", self._on_delete_key)

        # Hauptlayout: Seitenleiste links, Formular rechts
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # --- Linke Seite: Kontaktliste ---
        left = ttk.Frame(paned, width=260)
        paned.add(left, weight=0)

        # Suchfeld
        search_frame = ttk.Frame(left)
        search_frame.pack(fill="x", padx=4, pady=4)
        ttk.Label(search_frame, text="Suche:").pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._on_search())
        ttk.Entry(search_frame, textvariable=self._search_var).pack(
            side="left", fill="x", expand=True, padx=(4, 0)
        )
        ttk.Button(search_frame, text="✕", width=2,
                   command=lambda: self._search_var.set("")).pack(side="left", padx=2)

        # Kontaktliste
        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self._listbox = tk.Listbox(
            list_frame, selectmode="extended",
            font=("sans-serif", 11),
            activestyle="none",
            cursor="arrow",
        )
        scrollbar = ttk.Scrollbar(list_frame, command=self._listbox.yview)
        self._listbox.config(yscrollcommand=scrollbar.set)
        self._listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Double-Button-1>", self._on_select)

        # Statusleiste
        self._status_var = tk.StringVar()
        ttk.Label(left, textvariable=self._status_var, foreground="gray").pack(
            anchor="w", padx=4, pady=2
        )

        btn_row = ttk.Frame(left)
        btn_row.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(btn_row, text="+ Neuer Kontakt", command=self._new_contact).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(btn_row, text="QR", width=4, command=self._show_qr).pack(side="left", padx=(2, 0))

        # --- Rechte Seite: Kontaktformular ---
        right = ttk.Frame(paned)
        paned.add(right, weight=1)

        self._form = ContactForm(right, on_save=self._save_contact)
        self._form.pack(fill="both", expand=True)

        # Formular initial deaktivieren bis Kontakt ausgewählt
        self._set_form_enabled(False)

    def _build_header(self):
        header = tk.Frame(self, bg="#2c5f8a", height=48)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        try:
            from PIL import Image, ImageTk
            _hlogo = ImageTk.PhotoImage(Image.open(resolve_asset("kater-logo.png")).resize((36, 36)))
            lbl_img = tk.Label(header, image=_hlogo, bg="#2c5f8a")
            lbl_img.pack(side="left", padx=(10, 4), pady=6)
            self._header_logo_ref = _hlogo
        except Exception:
            pass

        tk.Label(
            header,
            text=f"Kater  –  v{__version__}",
            bg="#2c5f8a",
            fg="white",
            font=("sans-serif", 14, "bold"),
        ).pack(side="left", pady=6)

    def _show_about(self):
        from .about_dialog import AboutDialog
        AboutDialog(self)

    def _set_form_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for child in self._form.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def _on_delete_key(self, event):
        # Entf-Taste in Eingabefeldern nicht abfangen
        if isinstance(event.widget, (tk.Entry, tk.Text, ttk.Entry)):
            return
        self._delete_contact()

    # --- Kontaktverwaltung ---

    def _load_contacts(self, query: str = ""):
        self._contacts: list[Contact] = (
            self.db.search(query) if query else self.db.all()
        )
        self._listbox.delete(0, "end")
        for c in self._contacts:
            self._listbox.insert("end", c.get_display_name())
        count = self.db.count()
        self._status_var.set(
            f"{len(self._contacts)} von {count} Kontakten"
            if query else f"{count} Kontakte"
        )

    def _on_search(self):
        self._load_contacts(self._search_var.get().strip())

    def _check_unsaved(self) -> bool:
        """Prüft auf ungespeicherte Änderungen. Gibt False zurück wenn der Nutzer abbricht."""
        if not self._form.is_dirty():
            return True
        answer = messagebox.askyesnocancel(
            "Ungespeicherte Änderungen",
            "Es gibt ungespeicherte Änderungen.\nMöchten Sie diese speichern?",
        )
        if answer is None:
            return False
        if answer:
            self._form._save()
            if self._form.is_dirty():
                return False
        return True

    def _on_select(self, event=None):
        selection = self._listbox.curselection()
        if not selection:
            return
        # Bei Mehrfachauswahl: letzten Eintrag im Formular anzeigen
        idx = selection[-1]
        if idx >= len(self._contacts):
            return
        contact = self._contacts[idx]
        if contact.uid == self._selected_uid:
            return
        if not self._check_unsaved():
            # Auswahl zurücksetzen auf den aktuellen Kontakt
            for i, c in enumerate(self._contacts):
                if c.uid == self._selected_uid:
                    self._listbox.selection_clear(0, "end")
                    self._listbox.selection_set(i)
                    break
            return
        self._selected_uid = contact.uid
        self._set_form_enabled(True)
        self._form.load(contact)
        # Statuszeile bei Mehrfachauswahl aktualisieren
        if len(selection) > 1:
            self._status_var.set(f"{len(selection)} Kontakte markiert")

    def _new_contact(self):
        if not self._check_unsaved():
            return
        self._selected_uid = None
        self._listbox.selection_clear(0, "end")
        self._set_form_enabled(True)
        self._form.new_contact()

    def _save_contact(self, contact: Contact):
        self.db.save(contact)
        query = self._search_var.get().strip()
        self._load_contacts(query)
        # Gespeicherten Kontakt in der Liste markieren
        for i, c in enumerate(self._contacts):
            if c.uid == contact.uid:
                self._listbox.selection_clear(0, "end")
                self._listbox.selection_set(i)
                self._listbox.see(i)
                self._selected_uid = contact.uid
                break
        messagebox.showinfo("Gespeichert", f"Kontakt '{contact.get_display_name()}' gespeichert.")

    def _delete_contact(self):
        if not self._selected_uid:
            return
        contact = self.db.get(self._selected_uid)
        if not contact:
            return
        name = contact.get_display_name()
        if not messagebox.askyesno(
            "Kontakt löschen",
            f"Kontakt '{name}' wirklich löschen?"
        ):
            return
        self.db.delete(self._selected_uid)
        self._selected_uid = None
        self._form.new_contact()
        self._set_form_enabled(False)
        self._load_contacts(self._search_var.get().strip())

    # --- vCard Import/Export ---

    def _import_vcard(self):
        path = filedialog.askopenfilename(
            title="vCard importieren",
            filetypes=[("vCard Dateien", "*.vcf *.vcard"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        parser = VCardParser()
        try:
            contacts = parser.parse_file(path)
        except Exception as e:
            messagebox.showerror("Importfehler", str(e))
            return
        imported = 0
        for c in contacts:
            self.db.save(c)
            imported += 1
        self._load_contacts(self._search_var.get().strip())
        messagebox.showinfo(
            "Import abgeschlossen",
            f"{imported} Kontakt(e) importiert."
        )

    def _export_vcard(self):
        if not self._selected_uid:
            messagebox.showwarning("Kein Kontakt", "Bitte zuerst einen Kontakt auswählen.")
            return
        contact = self.db.get(self._selected_uid)
        if not contact:
            return
        path = filedialog.asksaveasfilename(
            title="vCard exportieren",
            defaultextension=".vcf",
            initialfile=f"{contact.get_display_name()}.vcf",
            filetypes=[("vCard Dateien", "*.vcf"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        exporter = VCardExporter()
        try:
            exporter.export_contacts([contact], path)
            messagebox.showinfo("Export", f"Kontakt nach '{path}' exportiert.")
        except Exception as e:
            messagebox.showerror("Exportfehler", str(e))

    def _export_selected(self):
        selection = self._listbox.curselection()
        if not selection:
            messagebox.showwarning(
                "Keine Auswahl",
                "Bitte zuerst Kontakte in der Liste markieren.\n"
                "(Strg+Klick für mehrere, Umschalt+Klick für Bereich)"
            )
            return
        contacts = [self._contacts[i] for i in selection if i < len(self._contacts)]
        if not contacts:
            return
        default_name = (
            f"{contacts[0].get_display_name()}.vcf"
            if len(contacts) == 1
            else f"{len(contacts)}_kontakte.vcf"
        )
        path = filedialog.asksaveasfilename(
            title=f"{len(contacts)} Kontakt(e) exportieren",
            defaultextension=".vcf",
            initialfile=default_name,
            filetypes=[("vCard Dateien", "*.vcf"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        exporter = VCardExporter()
        try:
            exporter.export_contacts(contacts, path)
            messagebox.showinfo(
                "Export",
                f"{len(contacts)} Kontakt(e) nach '{path}' exportiert."
            )
        except Exception as e:
            messagebox.showerror("Exportfehler", str(e))

    def _export_all(self):
        contacts = self.db.all()
        if not contacts:
            messagebox.showinfo("Export", "Keine Kontakte vorhanden.")
            return
        path = filedialog.asksaveasfilename(
            title="Alle Kontakte exportieren",
            defaultextension=".vcf",
            initialfile="adressbuch.vcf",
            filetypes=[("vCard Dateien", "*.vcf"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        exporter = VCardExporter()
        try:
            exporter.export_contacts(contacts, path)
            messagebox.showinfo(
                "Export",
                f"{len(contacts)} Kontakt(e) nach '{path}' exportiert."
            )
        except Exception as e:
            messagebox.showerror("Exportfehler", str(e))

    def _copy_to_clipboard(self):
        selection = self._listbox.curselection()
        if selection:
            contacts = [self._contacts[i] for i in selection if i < len(self._contacts)]
        elif self._selected_uid:
            contact = self.db.get(self._selected_uid)
            contacts = [contact] if contact else []
        else:
            messagebox.showwarning("Kein Kontakt", "Bitte zuerst einen Kontakt auswählen.")
            return
        if not contacts:
            return
        exporter = VCardExporter()
        text = "\r\n".join(exporter.contact_to_vcard(c) for c in contacts)
        self.clipboard_clear()
        self.clipboard_append(text)
        n = len(contacts)
        messagebox.showinfo("Kopiert", f"{n} Kontakt(e) als vCard in die Zwischenablage kopiert.")

    def _show_qr(self):
        if not self._selected_uid:
            messagebox.showwarning("Kein Kontakt", "Bitte zuerst einen Kontakt auswählen.")
            return
        contact = self.db.get(self._selected_uid)
        if contact:
            QRDialog(self, contact)

    # --- Update-Checker ---

    def _start_update_check(self):
        from ..updater import check_for_update_async
        check_for_update_async(self._on_update_result)

    def _on_update_result(self, info: dict | None):
        if info:
            self.after(0, lambda: self._show_update_dialog(info))

    def _show_update_dialog(self, info: dict):
        from ..updater import get_install_path, download_appimage

        version = info["version"]
        download_url = info.get("download_url")
        install_path = get_install_path()

        # In-App-Update nur wenn AppImage-Pfad bekannt und Download-URL vorhanden
        if download_url and install_path:
            self._run_in_app_update(version, download_url, install_path)
        else:
            # Fallback: Browser öffnen
            if messagebox.askyesno(
                "Update verfügbar",
                f"Kater {version} ist verfügbar!\n\nZur Download-Seite?",
                icon="info",
            ):
                webbrowser.open(info["url"])

    def _run_in_app_update(self, version: str, download_url: str, install_path):
        from ..updater import download_appimage
        import threading

        if not messagebox.askyesno(
            "Update verfügbar",
            f"Kater {version} ist verfügbar!\n\nJetzt aktualisieren?",
            icon="info",
        ):
            return

        # Fortschrittsdialog
        dlg = tk.Toplevel(self)
        dlg.title("Kater wird aktualisiert…")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # nicht schließbar

        tk.Label(dlg, text=f"Lade Kater {version} herunter…", padx=20, pady=12).pack()

        progress_var = tk.DoubleVar()
        bar = ttk.Progressbar(dlg, variable=progress_var, maximum=100, length=320)
        bar.pack(padx=20, pady=(0, 4))

        size_label = tk.Label(dlg, text="", foreground="gray", padx=20)
        size_label.pack(pady=(0, 12))

        def on_progress(done: int, total: int):
            if total:
                pct = done / total * 100
                mb_done = done / 1_048_576
                mb_total = total / 1_048_576
                self.after(0, lambda: (
                    progress_var.set(pct),
                    size_label.config(text=f"{mb_done:.1f} / {mb_total:.1f} MB"),
                ))
            else:
                bar.config(mode="indeterminate")
                self.after(0, bar.start)

        def do_download():
            try:
                download_appimage(download_url, install_path, on_progress)
                self.after(0, lambda: _on_success())
            except Exception as e:
                self.after(0, lambda: _on_error(str(e)))

        def _on_success():
            dlg.destroy()
            messagebox.showinfo(
                "Update erfolgreich",
                f"Kater {version} wurde installiert.\n\nBitte Kater neu starten."
            )

        def _on_error(msg: str):
            dlg.destroy()
            messagebox.showerror("Update fehlgeschlagen", f"Download fehlgeschlagen:\n{msg}")

        threading.Thread(target=do_download, daemon=True).start()
        self._center_window(dlg)

    def _center_window(self, win: tk.Toplevel):
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - win.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")

    def _on_close(self):
        if not self._check_unsaved():
            return
        self.db.close()
        self.destroy()

    def run(self):
        self.mainloop()
