"""Update-Checker: prüft GitHub Releases auf neue Versionen."""

import json
import os
import stat
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from . import __version__

GITHUB_REPO = "nicolettas-muggelbude/Kater"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
APPIMAGE_ASSET = "Kater-x86_64.AppImage"


def _parse_version(v: str) -> tuple[int, ...]:
    """'v1.2.3' oder '1.2.3' → (1, 2, 3)"""
    return tuple(int(x) for x in v.lstrip("v").split("."))


def _fetch_latest_release() -> Optional[dict]:
    try:
        req = urllib.request.Request(
            RELEASES_API,
            headers={"User-Agent": f"Kater/{__version__}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def get_install_path() -> Optional[Path]:
    """Gibt den Pfad der laufenden AppImage-Datei zurück."""
    appimage = os.environ.get("APPIMAGE")
    if appimage:
        return Path(appimage)
    candidate = Path.home() / ".local" / "bin" / APPIMAGE_ASSET
    if candidate.exists():
        return candidate
    return None


def check_for_update() -> Optional[dict]:
    """Gibt Update-Info zurück wenn eine neuere Version verfügbar ist, sonst None."""
    release = _fetch_latest_release()
    if not release:
        return None
    latest_tag = release.get("tag_name", "")
    try:
        if _parse_version(latest_tag) > _parse_version(__version__):
            # Download-URL des AppImage-Assets ermitteln
            download_url = None
            for asset in release.get("assets", []):
                if asset.get("name") == APPIMAGE_ASSET:
                    download_url = asset.get("browser_download_url")
                    break
            return {
                "version": latest_tag,
                "url": release.get("html_url", ""),
                "download_url": download_url,
            }
    except ValueError:
        pass
    return None


def check_for_update_async(callback: Callable[[Optional[dict]], None]) -> None:
    """Führt Update-Check in einem Hintergrund-Thread aus."""
    threading.Thread(target=lambda: callback(check_for_update()), daemon=True).start()


def download_appimage(
    download_url: str,
    dest: Path,
    on_progress: Callable[[int, int], None],
) -> None:
    """
    Lädt das AppImage herunter und ersetzt dest atomisch.
    on_progress(downloaded_bytes, total_bytes) wird laufend aufgerufen.
    Wirft bei Fehler eine Exception.
    """
    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": f"Kater/{__version__}"},
    )
    tmp = dest.parent / f".kater-update-{os.getpid()}.tmp"
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            with open(tmp, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    on_progress(downloaded, total)
        tmp.chmod(tmp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        tmp.rename(dest)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
