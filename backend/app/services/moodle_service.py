import logging
import datetime
import hashlib
import re
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup
from .cache_service import get_cached_data, set_cached_data, moodle_cache_key
from .url_guard import validate_service_url
from .moodle_url import find_moodle_base

logger = logging.getLogger(__name__)


def clean_html(raw_html: str) -> str:
    """Nettoie le HTML des descriptions Moodle pour affichage texte."""
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        return raw_html


def fetch_course_sections_hierarchy(ws_url: str, auth_token: str, course_id: int, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """
    Interroge core_course_get_contents pour mapper cmid et instance id
    vers la liste ordonnée des sections parentes.
    Ex: [ "Généralités", "Première séquence" ]
    """
    cmid_to_chain: Dict[int, List[str]] = {}
    instance_to_chain: Dict[int, List[str]] = {}
    try:
        http_client = session if session is not None else requests
        resp = http_client.get(
            ws_url,
            params={
                "wstoken": auth_token,
                "wsfunction": "core_course_get_contents",
                "courseid": course_id,
                "moodlewsrestformat": "json"
            },
            timeout=8
        )
        data = resp.json()
        if not isinstance(data, list):
            return {"cmid": cmid_to_chain, "instance": instance_to_chain}

        sec_info = {}
        for sec in data:
            s_id = sec.get("id")
            s_name = clean_html(sec.get("name", "")).strip()
            sec_info[s_id] = {
                "name": s_name,
                "parent_id": sec.get("parentsection")
            }

        for sec in data:
            s_id = sec.get("id")
            chain = []
            curr = s_id
            visited = set()
            while curr and curr not in visited:
                visited.add(curr)
                info = sec_info.get(curr)
                if not info:
                    break
                nm = info.get("name", "").strip()
                if nm and not re.match(r"^(section\s*\d+|topic\s*\d+|thème\s*\d+|général)$", nm, re.IGNORECASE):
                    chain.insert(0, nm)
                curr = info.get("parent_id")

            for mod in sec.get("modules", []):
                mid = mod.get("id")
                inst = mod.get("instance")
                if mid:
                    cmid_to_chain[mid] = chain
                if inst:
                    instance_to_chain[inst] = chain

    except Exception as e:
        logger.debug(f"Erreur recuperation sections cours {course_id}: {e}")

    return {"cmid": cmid_to_chain, "instance": instance_to_chain}


def build_moodle_title(
    course_shortname: Optional[str],
    course_fullname: Optional[str],
    section_chain: list,
    assignment_name: str
) -> str:
    """
    Construit un titre complet hiérarchique :
    [Nom / Code cours] - [Sections parentes] - [Nom du devoir]
    Exemple : R112 - Généralités - Première séquence - Fiches ROME
    """
    parts = []

    # 1. Code / nom du cours
    short_clean = (course_shortname or "").strip()
    full_clean = (course_fullname or "").strip()

    if short_clean:
        parts.append(short_clean)
    elif full_clean:
        parts.append(full_clean.split(" - ")[0].strip())

    # 2. Sections parentes
    if section_chain:
        for sec in section_chain:
            s_clean = sec.strip()
            if s_clean and not any(s_clean.lower() == p.lower() for p in parts):
                parts.append(s_clean)

    # 3. Nom du devoir
    a_clean = (assignment_name or "").strip()
    if a_clean and not any(a_clean.lower() == p.lower() for p in parts):
        parts.append(a_clean)

    return " - ".join(parts) if parts else a_clean


def fetch_moodle_data(
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    token: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Recupere les cours et devoirs reels depuis l'API Moodle avec cache SQLite."""
    if not url or (not token and (not username or not password)):
        return {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": "Identifiants Moodle non configurés."
        }

    url_err = validate_service_url(url)
    if url_err:
        return {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": url_err
        }

    cache_key = moodle_cache_key(url, username, token)

    if not force_refresh:
        cached = get_cached_data(cache_key)
        if cached:
            return cached

    effective_base_url = find_moodle_base(url)
    if not effective_base_url:
        err_res = {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": "Aucun Moodle trouvé à l'adresse configurée."
        }
        set_cached_data(cache_key, err_res, ttl_seconds=120)
        return err_res
    auth_token = token

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=1)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Sans jeton, on le genere via le service mobile
    if not auth_token and username and password:
        try:
            resp = session.post(
                f"{effective_base_url}/login/token.php",
                data={"username": username, "password": password, "service": "moodle_mobile_app"},
                timeout=10
            )
            if resp.status_code == 200:
                auth_token = resp.json().get("token")
        except Exception as e:
            logger.debug(f"Generation du token Moodle echouee: {e}")

    if not auth_token:
        err_res = {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": "Échec d'authentification Moodle (Token indisponible)."
        }
        set_cached_data(cache_key, err_res, ttl_seconds=120)
        return err_res

    # Interrogation des webservices Moodle
    ws_url = f"{effective_base_url}/webservice/rest/server.php"
    try:
        # 1. Site Info
        site_info_resp = session.get(
            ws_url,
            params={
                "wstoken": auth_token,
                "wsfunction": "core_webservice_get_site_info",
                "moodlewsrestformat": "json"
            },
            timeout=10
        )
        site_info = site_info_resp.json()
        user_id = site_info.get("userid")

        if not user_id:
            err_res = {
                "configured": False,
                "site_name": "Moodle",
                "courses": [],
                "upcoming_assignments": [],
                "connection_error": f"Erreur Moodle : {site_info.get('message', 'Utilisateur non identifié')}"
            }
            set_cached_data(cache_key, err_res, ttl_seconds=120)
            return err_res

        # 2. Courses
        courses_resp = session.get(
            ws_url,
            params={
                "wstoken": auth_token,
                "wsfunction": "core_enrol_get_users_courses",
                "userid": user_id,
                "moodlewsrestformat": "json"
            },
            timeout=10
        )
        raw_courses = courses_resp.json()
        if not isinstance(raw_courses, list):
            raw_courses = []

        course_ids = [c["id"] for c in raw_courses if "id" in c]

        # 3. Assignments across ALL enrolled courses
        upcoming = []
        seen_assign_ids = set()

        if course_ids:
            chunk_size = 25
            for start_idx in range(0, len(course_ids), chunk_size):
                chunk = course_ids[start_idx:start_idx + chunk_size]
                params = {
                    "wstoken": auth_token,
                    "wsfunction": "mod_assign_get_assignments",
                    "moodlewsrestformat": "json"
                }
                for i, cid in enumerate(chunk):
                    params[f"courseids[{i}]"] = cid

                try:
                    assign_resp = session.get(ws_url, params=params, timeout=12)
                    assign_data = assign_resp.json()
                    now = datetime.datetime.now()
                    now_ts = now.timestamp()
                    courses_assignments = assign_data.get("courses", [])

                    # Pré-récupération des sections STRICTEMENT pour les cours ayant de vrais devoirs futurs
                    sections_cache: Dict[int, Dict[str, Any]] = {}
                    for ca in courses_assignments:
                        ca_id = ca.get("id")
                        has_upcoming = any(a.get("duedate", 0) >= now_ts for a in ca.get("assignments", []))
                        if has_upcoming and ca_id and ca_id not in sections_cache:
                            sections_cache[ca_id] = fetch_course_sections_hierarchy(ws_url, auth_token, ca_id, session=session)

                    for ca in courses_assignments:
                        ca_id = ca.get("id")
                        c_name = ca.get("fullname", "Cours")
                        c_short = ca.get("shortname", "")
                        sec_maps = sections_cache.get(ca_id, {"cmid": {}, "instance": {}})

                        for a in ca.get("assignments", []):
                            aid = a.get("id")
                            if aid in seen_assign_ids:
                                continue
                            seen_assign_ids.add(aid)
                            due_ts = a.get("duedate")
                            if due_ts and due_ts > 0:
                                due_dt = datetime.datetime.fromtimestamp(due_ts)
                                days_left = (due_dt.date() - now.date()).days
                                if days_left >= 0:
                                    cmid = a.get("cmid")
                                    cid = a.get("course") or ca_id
                                    assign_url = f"{effective_base_url}/mod/assign/view.php?id={cmid}" if cmid else f"{effective_base_url}/course/view.php?id={cid}"
                                    
                                    # Hiérarchie des sections parentes
                                    chain = sec_maps["cmid"].get(cmid) or sec_maps["instance"].get(aid) or []
                                    hierarchical_title = build_moodle_title(c_short, c_name, chain, a.get("name", "Devoir"))
                                    intro_clean = clean_html(a.get("intro", "")).strip()
                                    desc = intro_clean if intro_clean else "Consignes et dépôt disponibles sur Moodle."

                                    upcoming.append({
                                        "id": aid,
                                        "course_id": cid,
                                        "course_name": c_name,
                                        "name": hierarchical_title,
                                        "raw_name": a.get("name"),
                                        "duedate": due_dt.isoformat(),
                                        "days_left": days_left,
                                        "status": "pending",
                                        "submission_allowed": True,
                                        "submitted": False,
                                        "description": desc,
                                        "url": assign_url
                                    })
                except Exception as e:
                    logger.warning(f"Erreur chunk Moodle assignments {start_idx}: {e}")

            # Événements du calendrier Moodle (quizz, devoirs spécifiques)
            try:
                cal_resp = session.get(
                    ws_url,
                    params={
                        "wstoken": auth_token,
                        "wsfunction": "core_calendar_get_action_events_by_timesort",
                        "moodlewsrestformat": "json"
                    },
                    timeout=8
                )
                cal_data = cal_resp.json()
                now = datetime.datetime.now()
                for ev in cal_data.get("events", []):
                    if ev.get("eventtype") == "due":
                        ev_name = ev.get("name", "")
                        clean_name = ev_name.replace(" doit être rendu", "").replace(" doit être effectué", "").strip()
                        # Éviter doublon si déjà présent
                        if any(clean_name.lower() in u["name"].lower() or u["name"].lower() in clean_name.lower() for u in upcoming):
                            continue
                        ts = ev.get("timesort")
                        if ts and ts > 0:
                            due_dt = datetime.datetime.fromtimestamp(ts)
                            days_left = (due_dt.date() - now.date()).days
                            if days_left >= 0:
                                ev_course = ev.get("course", {})
                                ev_course_id = ev_course.get("id")
                                c_short = ev_course.get("shortname", "")
                                c_name = ev_course.get("fullname", "Moodle")
                                ev_title = build_moodle_title(c_short, c_name, [], clean_name)
                                ev_url = ev.get("url") or (f"{effective_base_url}/course/view.php?id={ev_course_id}" if ev_course_id else effective_base_url)
                                intro_clean = clean_html(ev.get("description", "")).strip()
                                desc = intro_clean if intro_clean else "Consignes et dépôt disponibles sur Moodle."
                                upcoming.append({
                                    "id": ev.get("id"),
                                    "course_id": ev_course_id,
                                    "course_name": c_name,
                                    "name": ev_title,
                                    "raw_name": clean_name,
                                    "duedate": due_dt.isoformat(),
                                    "days_left": days_left,
                                    "status": "pending",
                                    "submission_allowed": True,
                                    "submitted": False,
                                    "description": desc,
                                    "url": ev_url
                                })
            except Exception as e:
                logger.debug(f"Action events calendrier Moodle: {e}")

        upcoming.sort(key=lambda x: (x["days_left"], x["duedate"]))

        parsed_courses = [
            {
                "id": c.get("id"),
                "fullname": c.get("fullname"),
                "shortname": c.get("shortname"),
                "category": c.get("categoryname", "Cours"),
                "teacher": "Enseignant",
                "assignments_count": 0
            }
            for c in raw_courses
        ]

        result = {
            "configured": True,
            "site_name": site_info.get("sitename", "Moodle"),
            "fullname": site_info.get("fullname"),
            "courses": parsed_courses,
            "upcoming_assignments": upcoming,
            "connection_error": None
        }
        set_cached_data(cache_key, result, ttl_seconds=900)
        return result

    except Exception as e:
        logger.error(f"Erreur Moodle API: {e}")
        stale = get_cached_data(cache_key, allow_stale=True)
        if stale:
            stale["connection_error"] = f"Avertissement actualisation Moodle ({e}). Affichage de la version enregistrée."
            return stale
        err_res = {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": str(e)
        }
        set_cached_data(cache_key, err_res, ttl_seconds=120)
        return err_res
