"""Detection de l'adresse racine d'un Moodle (certains sont servis sous /moodle)."""
from typing import Optional

import requests

from .url_guard import validate_service_url

_resolved: dict[str, str] = {}


def candidate_bases(url: str) -> list[str]:
    url = url.strip().rstrip("/")
    if url.endswith("/login") or url.endswith("/login/index.php"):
        url = url.rsplit("/login", 1)[0]
    candidates = [url]
    if not url.endswith("/moodle"):
        candidates.append(f"{url}/moodle")
    return candidates


def _is_moodle(base: str) -> bool:
    """Un Moodle repond toujours par un JSON sur /login/token.php, meme sans identifiants."""
    if validate_service_url(base):
        return False
    try:
        resp = requests.get(f"{base}/login/token.php", timeout=8)
        data = resp.json()
    except Exception:
        return False
    return isinstance(data, dict) and ("error" in data or "token" in data)


def find_moodle_base(url: str) -> Optional[str]:
    """Retourne l'adresse racine du Moodle (avec ou sans /moodle), ou None s'il est introuvable."""
    key = (url or "").strip().rstrip("/")
    if not key:
        return None
    if key in _resolved:
        return _resolved[key]
    for base in candidate_bases(key):
        if _is_moodle(base):
            _resolved[key] = base
            return base
    return None
