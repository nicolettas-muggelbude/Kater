#!/bin/bash
# Kater AppImage Builder
# Verwendung: bash build-appimage.sh [VERSION]
set -e

VERSION="${1:-1.0.0}"
APPDIR="AppDir"
APPIMAGE_NAME="Kater-${VERSION}-x86_64.AppImage"

echo "=== Kater AppImage Builder v${VERSION} ==="

# appimagetool herunterladen falls nicht vorhanden
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Lade appimagetool herunter..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# AppDir aufräumen und neu erstellen
rm -rf "$APPDIR"
mkdir -p "$APPDIR"

# PyInstaller-Output direkt in AppDir kopieren (kater-Binary liegt im Wurzelverzeichnis)
echo "Kopiere PyInstaller-Build..."
cp -r dist/kater/. "$APPDIR/"

# Icon: SVG → PNG (256x256)
echo "Erstelle Icon..."
if command -v rsvg-convert &>/dev/null; then
    rsvg-convert -w 256 -h 256 assets/kater-logo.svg -o "$APPDIR/kater.png"
elif command -v inkscape &>/dev/null; then
    inkscape --export-type=png --export-filename="$APPDIR/kater.png" \
        --export-width=256 --export-height=256 assets/kater-logo.svg
else
    echo "Warnung: kein SVG-Konverter gefunden, erstelle Platzhalter-Icon"
    python3 - <<'PYEOF'
import os, sys
try:
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (256, 256), (74, 144, 217, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([28, 50, 228, 220], fill=(74, 144, 217))
    img.save(os.environ.get("APPDIR_ICON", "AppDir/kater.png"))
except Exception as e:
    print(f"Icon-Fehler: {e}", file=sys.stderr)
PYEOF
fi

# .desktop-Datei
cat > "$APPDIR/kater.desktop" << 'DESKTOP'
[Desktop Entry]
Name=Kater
Comment=Linux-Adressbuch mit vCard-Unterstützung
Exec=kater
Icon=kater
Type=Application
Categories=Office;ContactManagement;
Keywords=Adressbuch;Kontakte;vCard;
DESKTOP

# AppRun
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export LD_LIBRARY_PATH="$HERE:${LD_LIBRARY_PATH}"
exec "$HERE/kater" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# AppImage erzeugen
echo "Erzeuge AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage "$APPDIR" "$APPIMAGE_NAME"

echo ""
echo "Fertig: $(pwd)/$APPIMAGE_NAME"
