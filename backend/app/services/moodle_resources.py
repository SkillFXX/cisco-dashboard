"""Ressources Moodle (cours, sections, documents) pour l'onglet Ressources."""
import logging
import threading
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import requests

from ..models import User
from .cache_service import get_cached_data, set_cached_data
from .moodle_service import clean_html
from .moodle_url import find_moodle_base

logger = logging.getLogger(__name__)

COURSES_TTL = 900
CONTENT_TTL = 600
SESSION_TTL = 1800
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024
INLINE_MIMES = {"application/pdf", "image/png", "image/jpeg", "image/gif", "image/webp"}

_sessions: Dict[int, Tuple[float, Dict[str, Any]]] = {}
_lock = threading.Lock()


class MoodleError(Exception):
    pass


def _configured(user: User) -> bool:
    c = user.credentials
    return bool(c and c.moodle_url and (c.moodle_token or (c.moodle_username and c.moodle_password)))


def _session(user: User, refresh: bool = False) -> Dict[str, Any]:
    """Adresse racine, jeton et identifiant Moodle de l'utilisateur (gardes 30 min en memoire)."""
    with _lock:
        cached = _sessions.get(user.id)
        if cached and cached[0] > time.time() and not refresh:
            return cached[1]

    c = user.credentials
    base = find_moodle_base(c.moodle_url)
    if not base:
        raise MoodleError("Aucun Moodle trouvé à l'adresse configurée.")
    token = c.moodle_token
    if not token:
        try:
            data = requests.post(
                f"{base}/login/token.php",
                data={"username": c.moodle_username, "password": c.moodle_password, "service": "moodle_mobile_app"},
                timeout=12,
            ).json()
        except Exception as e:
            raise MoodleError(f"Connexion à Moodle impossible : {e}")
        token = data.get("token")
        if not token:
            raise MoodleError("Identifiants Moodle refusés.")

    ws = f"{base}/webservice/rest/server.php"
    info = _call(ws, token, "core_webservice_get_site_info")
    if not isinstance(info, dict) or not info.get("userid"):
        raise MoodleError("Jeton Moodle invalide.")
    sess = {"base": base, "ws": ws, "token": token, "userid": info["userid"]}
    with _lock:
        _sessions[user.id] = (time.time() + SESSION_TTL, sess)
    return sess


def _call(ws: str, token: str, function: str, **params) -> Any:
    try:
        resp = requests.get(
            ws,
            params={"wstoken": token, "wsfunction": function, "moodlewsrestformat": "json", **params},
            timeout=20,
        )
        data = resp.json()
    except Exception as e:
        raise MoodleError(f"Moodle ne répond pas ({e}).")
    if isinstance(data, dict) and (data.get("exception") or data.get("errorcode")):
        raise MoodleError(data.get("message") or "Erreur Moodle.")
    return data


def list_courses(user: User, force_refresh: bool = False) -> Dict[str, Any]:
    if not _configured(user):
        return {"configured": False, "courses": [], "error": None}
    key = f"moodle_courses:{user.id}"
    if not force_refresh:
        cached = get_cached_data(key)
        if cached:
            return cached
    try:
        s = _session(user, refresh=force_refresh)
        raw = _call(s["ws"], s["token"], "core_enrol_get_users_courses", userid=s["userid"])
        now = time.time()
        courses = []
        for c in raw if isinstance(raw, list) else []:
            end = c.get("enddate") or 0
            courses.append({
                "id": c["id"],
                "fullname": clean_html(c.get("fullname", "")),
                "shortname": clean_html(c.get("shortname", "")),
                "ended": bool(end and end < now),
                "hidden": bool(c.get("hidden")),
                "progress": c.get("progress"),
                "lastaccess": c.get("lastaccess") or 0,
            })
        courses.sort(key=lambda c: (c["ended"], c["hidden"], c["fullname"].lower()))
        result = {"configured": True, "courses": courses, "error": None}
        set_cached_data(key, result, ttl_seconds=COURSES_TTL)
        return result
    except MoodleError as e:
        stale = get_cached_data(key, allow_stale=True)
        if stale:
            return {**stale, "error": str(e)}
        return {"configured": True, "courses": [], "error": str(e)}


def _normalize(raw: Any) -> List[Dict[str, Any]]:
    sections = []
    for sec in raw if isinstance(raw, list) else []:
        modules = []
        for mod in sec.get("modules", []):
            if mod.get("uservisible") is False:
                continue
            modname = mod.get("modname", "")
            description = clean_html(mod.get("description", ""))[:1200]
            files, link = [], None
            for i, f in enumerate(mod.get("contents") or []):
                if f.get("type") == "url":
                    link = f.get("fileurl")
                elif f.get("type") == "file":
                    files.append({
                        "index": i,
                        "name": f.get("filename", "fichier"),
                        "size": f.get("filesize") or 0,
                        "mime": f.get("mimetype") or "application/octet-stream",
                        "modified": f.get("timemodified") or 0,
                        "_url": f.get("fileurl"),
                    })
            if modname == "label" and not description:
                continue
            modules.append({
                "id": mod.get("id"),
                "name": clean_html(mod.get("name", "")) or "Sans titre",
                "modname": modname,
                "url": mod.get("url"),
                "description": description,
                "files": files,
                "link": link,
            })
        summary = clean_html(sec.get("summary", ""))[:600]
        if modules or summary:
            sections.append({
                "id": sec.get("id"),
                "name": clean_html(sec.get("name", "")) or "Général",
                "summary": summary,
                "modules": modules,
            })
    return sections


def _course_content(user: User, course_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    key = f"moodle_course:{user.id}:{course_id}"
    if not force_refresh:
        cached = get_cached_data(key)
        if cached:
            return cached
    s = _session(user, refresh=force_refresh)
    sections = _normalize(_call(s["ws"], s["token"], "core_course_get_contents", courseid=course_id))
    result = {"sections": sections, "base": s["base"]}
    set_cached_data(key, result, ttl_seconds=CONTENT_TTL)
    return result


def get_course(user: User, course_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    """Sections et documents d'un cours (sans les adresses de telechargement internes)."""
    if not _configured(user):
        return {"configured": False, "sections": [], "error": None}
    try:
        if not any(c["id"] == course_id for c in list_courses(user)["courses"]):
            raise MoodleError("Cours introuvable.")
        data = _course_content(user, course_id, force_refresh)
        error = None
    except MoodleError as e:
        data = get_cached_data(f"moodle_course:{user.id}:{course_id}", allow_stale=True)
        error = str(e)
        if not data:
            return {"configured": True, "sections": [], "error": error}

    base = data.get("base", "")
    sections = []
    for sec in data["sections"]:
        mods = []
        for m in sec["modules"]:
            files = [{k: v for k, v in f.items() if k != "_url"} for f in m["files"]]
            mods.append({**m, "files": files})
        sections.append({**sec, "modules": mods})
    return {"configured": True, "sections": sections, "base": base, "error": error}


def open_file(user: User, course_id: int, cmid: int, index: int):
    """Ouvre un fichier Moodle en flux. Retourne (reponse requests, nom, mime). Le jeton ne quitte jamais le serveur."""
    if not _configured(user):
        raise MoodleError("Moodle n'est pas configuré.")
    data = _course_content(user, course_id)
    target = None
    for sec in data["sections"]:
        for m in sec["modules"]:
            if m["id"] == cmid:
                target = next((f for f in m["files"] if f["index"] == index), None)
    if not target or not target.get("_url"):
        raise MoodleError("Fichier introuvable.")

    s = _session(user)
    file_url = target["_url"]
    if urllib.parse.urlparse(file_url).netloc != urllib.parse.urlparse(s["base"]).netloc:
        raise MoodleError("Adresse de fichier non autorisée.")
    sep = "&" if "?" in file_url else "?"
    resp = requests.get(f"{file_url}{sep}token={urllib.parse.quote(s['token'])}", stream=True, timeout=(8, 30), allow_redirects=False)
    if resp.status_code != 200:
        resp.close()
        raise MoodleError(f"Moodle a refusé le téléchargement (HTTP {resp.status_code}).")
    length = int(resp.headers.get("Content-Length") or 0)
    if length > MAX_DOWNLOAD_BYTES:
        resp.close()
        raise MoodleError("Fichier trop volumineux pour être téléchargé ici.")
    return resp, target["name"], target["mime"]
