"""Update-Checker: prüft GitHub Releases auf neue Versionen."""

import json
import threading
import urllib.error
import urllib.request
from typing import Callable, Optional

from . import __version__

GITHUB_REPO = "nicolettas-muggelbude/Kater"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


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


def check_for_update() -> Optional[dict]:
    """Gibt Update-Info zurück wenn eine neuere Version verfügbar ist, sonst None."""
    release = _fetch_latest_release()
    if not release:
        return None
    latest_tag = release.get("tag_name", "")
    try:
        if _parse_version(latest_tag) > _parse_version(__version__):
            return {
                "version": latest_tag,
                "url": release.get("html_url", ""),
                "notes": release.get("body", ""),
            }
    except ValueError:
        pass
    return None


def check_for_update_async(callback: Callable[[Optional[dict]], None]) -> None:
    """Führt Update-Check in einem Hintergrund-Thread aus."""
    threading.Thread(target=lambda: callback(check_for_update()), daemon=True).start()
