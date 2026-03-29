"""Über-Dialog für Kater."""

import tkinter as tk
import webbrowser
from tkinter import ttk

from .. import __version__
from .utils import resolve_asset

GITHUB_URL = "https://github.com/nicolettas-muggelbude/Kater"


class AboutDialog(tk.Toplevel):
    """Zeigt App-Informationen an."""

    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Über Kater")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build()

        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width()  - self.winfo_width())  // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{px}+{py}")

    def _build(self):
        outer = ttk.Frame(self, padding=24)
        outer.pack(fill="both", expand=True)

        # Logo
        try:
            from PIL import Image, ImageTk
            img = Image.open(resolve_asset("kater-logo.png")).resize((80, 80))
            self._photo = ImageTk.PhotoImage(img)
            ttk.Label(outer, image=self._photo).pack(pady=(0, 8))
        except Exception:
            ttk.Label(outer, text="=^.^=", font=("monospace", 28, "bold")).pack(pady=(0, 8))

        # Name + Version
        ttk.Label(outer, text="Kater", font=("sans-serif", 20, "bold")).pack()
        ttk.Label(outer, text=f"Version {__version__}", foreground="gray").pack(pady=(2, 12))

        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=(0, 12))

        ttk.Label(
            outer,
            text="Linux-Adressbuch mit vollständiger vCard 4.0-Unterstützung.\n"
                 "Kontakte verwalten, importieren und exportieren.",
            justify="center",
            wraplength=280,
        ).pack()

        link = ttk.Label(outer, text=GITHUB_URL, foreground="#4a90d9", cursor="hand2")
        link.pack(pady=(12, 0))
        link.bind("<Button-1>", lambda _: webbrowser.open(GITHUB_URL))

        ttk.Separator(outer, orient="horizontal").pack(fill="x", pady=12)

        ttk.Label(outer, text="Lizenz: MIT", foreground="gray").pack()

        ttk.Button(outer, text="Schließen", command=self.destroy).pack(pady=(16, 0))
