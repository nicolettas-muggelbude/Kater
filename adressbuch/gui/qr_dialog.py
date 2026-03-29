"""QR-Code Dialog für den Export eines Kontakts auf Mobilgeräte."""

import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import qrcode
from PIL import Image, ImageTk

from ..models.contact import Contact
from ..storage.vcard import VCardExporter

# Maximale vCard-Größe für einen QR-Code (Version 40, binär: ~2953 Byte)
_QR_MAX_BYTES = 2900


class QRDialog(tk.Toplevel):
    """Zeigt den vCard-Inhalt eines Kontakts als QR-Code."""

    def __init__(self, parent, contact: Contact):
        super().__init__(parent)
        self.title(f"QR-Code – {contact.get_display_name()}")
        self.resizable(False, False)
        self.grab_set()  # Modal

        self._contact = contact
        self._exporter = VCardExporter()
        self._photo_ref = None  # Referenz gegen Garbage-Collection

        self._build_ui()
        self._generate()

        # Zentrieren relativ zum Elternfenster
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{px}+{py}")

    def _build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        # QR-Bild
        self._img_label = ttk.Label(main)
        self._img_label.pack()

        # Info-Text
        self._info_var = tk.StringVar()
        ttk.Label(main, textvariable=self._info_var, foreground="gray").pack(pady=(6, 0))

        # Größe wählen (Einfluss auf Scan-Abstand)
        size_frame = ttk.Frame(main)
        size_frame.pack(pady=6)
        ttk.Label(size_frame, text="Größe:").pack(side="left")
        self._size_var = tk.IntVar(value=300)
        for label, val in [("Klein", 200), ("Mittel", 300), ("Groß", 400)]:
            ttk.Radiobutton(
                size_frame, text=label, variable=self._size_var, value=val,
                command=self._generate
            ).pack(side="left", padx=4)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=(6, 0))
        ttk.Button(btn_frame, text="Als PNG speichern", command=self._save_png).pack(side="left")
        ttk.Button(btn_frame, text="Schließen", command=self.destroy).pack(side="right")

    def _make_vcard(self) -> str:
        """Erzeugt den vCard-String ohne eingebettetes Foto (spart Platz)."""
        # Temporär Foto ausblenden für kompaktere vCard
        photo_data = self._contact.photo_data
        self._contact.photo_data = None
        vcard = self._exporter.contact_to_vcard(self._contact)
        self._contact.photo_data = photo_data
        return vcard

    def _generate(self):
        vcard = self._make_vcard()
        data = vcard.encode("utf-8")

        if len(data) > _QR_MAX_BYTES:
            self._img_label.config(image="", text="⚠ vCard zu groß für QR-Code.\nBitte Felder reduzieren.", foreground="red")
            self._info_var.set("")
            return

        size = self._size_var.get()

        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img: Image.Image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        img = img.resize((size, size), Image.NEAREST)

        self._pil_img = img
        self._photo_ref = ImageTk.PhotoImage(img)
        self._img_label.config(image=self._photo_ref, text="")
        self._info_var.set(
            f"QR-Version {qr.version}  ·  {len(data)} Byte  ·  "
            f"Mit Kamera oder QR-Scanner-App scannen"
        )

    def _save_png(self):
        if not hasattr(self, "_pil_img"):
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="QR-Code speichern",
            defaultextension=".png",
            initialfile=f"qr_{self._contact.get_display_name()}.png",
            filetypes=[("PNG-Bild", "*.png"), ("Alle Dateien", "*.*")],
        )
        if path:
            self._pil_img.save(path)
            messagebox.showinfo("Gespeichert", f"QR-Code gespeichert:\n{path}", parent=self)
