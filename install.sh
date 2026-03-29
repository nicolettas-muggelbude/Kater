#!/bin/bash
# Kater – Desktop-Integration für Linux
# Erstellt einen Starter in GNOME, KDE, XFCE und anderen Desktop-Umgebungen.
# Prüft und repariert automatisch fehlende Systemabhängigkeiten (libfuse2).
# Benötigt KEIN sudo für die Integration – nur optional für die Reparatur.
#
# Verwendung:
#   chmod +x install.sh
#   ./install.sh /pfad/zu/Kater-1.0.0-x86_64.AppImage
#
# Ohne Argument wird ~/Downloads/Kater*.AppImage gesucht.

set -e

ICON_URL="https://raw.githubusercontent.com/nicolettas-muggelbude/Kater/master/assets/kater-logo.png"

# ── AppImage finden ────────────────────────────────────────────────────────────
APPIMAGE="${1:-}"
if [ -z "$APPIMAGE" ]; then
  APPIMAGE="$(ls -t "$HOME/Downloads/Kater"*.AppImage 2>/dev/null | head -1)"
fi
if [ -z "$APPIMAGE" ] || [ ! -f "$APPIMAGE" ]; then
  echo "Fehler: AppImage nicht gefunden."
  echo "Verwendung: $0 /pfad/zu/Kater-x.y.z-x86_64.AppImage"
  exit 1
fi
APPIMAGE="$(realpath "$APPIMAGE")"
echo "AppImage: $APPIMAGE"

# ── AppImage in stabilen Pfad installieren ─────────────────────────────────────
INSTALL_DIR="$HOME/.local/bin"
APPIMAGE_INSTALLED="$INSTALL_DIR/Kater.AppImage"
mkdir -p "$INSTALL_DIR"
cp -f "$APPIMAGE" "$APPIMAGE_INSTALLED"
chmod +x "$APPIMAGE_INSTALLED"
echo "AppImage installiert nach: $APPIMAGE_INSTALLED"
APPIMAGE_ORIGINAL="$APPIMAGE"
APPIMAGE="$APPIMAGE_INSTALLED"

# ── Systemabhängigkeiten prüfen und ggf. reparieren ───────────────────────────
check_and_fix_deps() {
  local pkg_manager="" fuse_pkg=""

  if command -v apt &>/dev/null; then
    pkg_manager="apt";    fuse_pkg="libfuse2"
  elif command -v dnf &>/dev/null; then
    pkg_manager="dnf";    fuse_pkg="fuse"
  elif command -v zypper &>/dev/null; then
    pkg_manager="zypper"; fuse_pkg="fuse"
  elif command -v pacman &>/dev/null; then
    pkg_manager="pacman"; fuse_pkg="fuse2"
  fi

  local fuse_ok=true
  ldconfig -p 2>/dev/null | grep -q "libfuse\.so\.2" || fuse_ok=false

  echo ""
  echo "── Systemprüfung ──────────────────────────────────────────────────────"

  if $fuse_ok; then
    echo "  ✓ libfuse2 vorhanden"
  else
    echo "  ✗ libfuse2 fehlt  ← AppImage kann nicht gestartet werden"
  fi

  echo "────────────────────────────────────────────────────────────────────────"

  if $fuse_ok; then
    echo "  ✓ Alle Abhängigkeiten in Ordnung."
    echo ""
    return 0
  fi

  echo ""
  echo "  ⚠  libfuse2 fehlt – Kater wird sich nicht starten lassen."
  echo ""

  if [ -z "$pkg_manager" ]; then
    echo "  Kein bekannter Paketmanager gefunden."
    echo "  Bitte libfuse2 für deine Distribution manuell installieren."
    echo ""
    return 0
  fi

  _install_deps "$pkg_manager" "$fuse_pkg"
}

# ── Reparatur-Modus: Pakete neu installieren ──────────────────────────────────
repair_deps() {
  local pkg_manager="" fuse_pkg=""

  if command -v apt &>/dev/null; then
    pkg_manager="apt";    fuse_pkg="libfuse2"
  elif command -v dnf &>/dev/null; then
    pkg_manager="dnf";    fuse_pkg="fuse"
  elif command -v zypper &>/dev/null; then
    pkg_manager="zypper"; fuse_pkg="fuse"
  elif command -v pacman &>/dev/null; then
    pkg_manager="pacman"; fuse_pkg="fuse2"
  else
    echo "Kein bekannter Paketmanager gefunden."
    exit 1
  fi

  echo ""
  echo "── Reparatur-Modus ────────────────────────────────────────────────────"
  echo "  Installiert Systembibliotheken neu."
  echo "────────────────────────────────────────────────────────────────────────"
  echo ""

  _install_deps "$pkg_manager" "$fuse_pkg" "reinstall"
}

_install_deps() {
  local pkg_manager="$1" fuse_pkg="$2" mode="${3:-install}"

  local cmd_label="Installieren"
  [ "$mode" = "reinstall" ] && cmd_label="Neu installieren"

  echo "  $cmd_label mit sudo (Passwort erforderlich):"
  if [ "$pkg_manager" = "apt" ]; then
    if [ "$mode" = "reinstall" ]; then
      echo "    sudo apt install --reinstall $fuse_pkg"
    else
      echo "    sudo apt install $fuse_pkg"
    fi
  elif [ "$pkg_manager" = "dnf" ]; then
    if [ "$mode" = "reinstall" ]; then
      echo "    sudo dnf reinstall $fuse_pkg"
    else
      echo "    sudo dnf install $fuse_pkg"
    fi
  elif [ "$pkg_manager" = "zypper" ]; then
    echo "    sudo zypper install $fuse_pkg"
  elif [ "$pkg_manager" = "pacman" ]; then
    echo "    sudo pacman -S $fuse_pkg"
  fi
  echo ""
  printf "  Jetzt automatisch ausführen? [J/n] "
  read -r answer
  answer="${answer:-j}"

  if [[ "$answer" =~ ^[jJyY]$ ]]; then
    if [ "$pkg_manager" = "apt" ]; then
      if [ "$mode" = "reinstall" ]; then
        sudo apt install --reinstall -y "$fuse_pkg"
      else
        sudo apt install -y "$fuse_pkg"
      fi
    elif [ "$pkg_manager" = "dnf" ]; then
      if [ "$mode" = "reinstall" ]; then
        sudo dnf reinstall -y "$fuse_pkg" 2>/dev/null || sudo dnf install -y "$fuse_pkg"
      else
        sudo dnf install -y "$fuse_pkg"
      fi
    elif [ "$pkg_manager" = "zypper" ]; then
      sudo zypper install -y "$fuse_pkg"
    elif [ "$pkg_manager" = "pacman" ]; then
      sudo pacman -S --noconfirm "$fuse_pkg"
    fi
    echo ""
    echo "  ✓ Erledigt. Kater neu starten."
  else
    echo "  Übersprungen. Den Befehl oben manuell ausführen falls Kater nicht startet."
  fi
  echo ""
}

# ── Reparatur-Modus direkt aufrufen: ./install.sh --repair [AppImage] ─────────
if [ "${1:-}" = "--repair" ]; then
  shift
  APPIMAGE="${1:-}"
  if [ -z "$APPIMAGE" ]; then
    APPIMAGE="$(ls -t "$HOME/Downloads/Kater"*.AppImage 2>/dev/null | head -1)"
  fi
  repair_deps
  exit 0
fi

check_and_fix_deps

# ── Icon herunterladen ─────────────────────────────────────────────────────────
ICON_BASE="$HOME/.local/share/icons/hicolor"
ICON_DIR="$ICON_BASE/256x256/apps"
ICON_FILE="$ICON_DIR/kater.png"
mkdir -p "$ICON_DIR"

echo "Lade Icon herunter..."
if command -v wget &>/dev/null; then
  wget -qO "$ICON_FILE" "$ICON_URL" && echo "  Icon installiert." || echo "  Hinweis: Icon konnte nicht geladen werden – App-Icon fehlt ggf. im Starter."
elif command -v curl &>/dev/null; then
  curl -sSL "$ICON_URL" -o "$ICON_FILE" && echo "  Icon installiert." || echo "  Hinweis: Icon konnte nicht geladen werden – App-Icon fehlt ggf. im Starter."
else
  echo "  Hinweis: wget und curl nicht gefunden – Icon übersprungen."
fi

# ── .desktop-Datei anlegen ─────────────────────────────────────────────────────
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/kater.desktop"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Name=Kater
Comment=Linux-Adressbuch mit vCard-Unterstützung
Exec=$APPIMAGE %u
Icon=kater
Type=Application
Categories=Office;ContactManagement;
StartupWMClass=Kater
Keywords=Adressbuch;Kontakte;vCard;
Terminal=false
DESKTOP

echo "Desktop-Eintrag erstellt: $DESKTOP_FILE"

# ── Desktop-Datenbanken aktualisieren ──────────────────────────────────────────
gtk-update-icon-cache -f -t "$ICON_BASE" 2>/dev/null || true
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

echo ""
echo "✓ Kater wurde erfolgreich als Starter integriert!"
echo ""
echo "  Das App-Icon erscheint in:"
echo "  • GNOME Activities / Ubuntu-Anwendungsmenü"
echo "  • KDE Application Launcher"
echo "  • XFCE / MATE Anwendungsmenü"
echo ""
echo "  Falls der Eintrag noch nicht erscheint: Abmelden und neu anmelden."
echo ""
echo "  Kater startet nicht? Reparatur ausführen mit:"
echo "    ./install.sh --repair"
echo ""

# ── Original-AppImage löschen? ─────────────────────────────────────────────────
if [ "$APPIMAGE_ORIGINAL" != "$APPIMAGE_INSTALLED" ] && [ -f "$APPIMAGE_ORIGINAL" ]; then
  printf "Original-Datei löschen? (%s) [j/N] " "$APPIMAGE_ORIGINAL"
  read -r answer
  if [[ "${answer:-n}" =~ ^[jJyY]$ ]]; then
    rm -f "$APPIMAGE_ORIGINAL"
    echo "  Gelöscht."
  fi
fi
