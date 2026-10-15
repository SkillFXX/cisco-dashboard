import logging
import datetime
from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

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


def fetch_moodle_data(
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    token: Optional[str] = None
) -> Dict[str, Any]:
    """Récupère les cours et devoirs réels depuis l'API Moodle WebService."""
    if not url or (not token and (not username or not password)):
        return {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": "Identifiants Moodle non configurés."
        }

    raw_base_url = url.rstrip("/")
    auth_token = token
    effective_base_url = raw_base_url

    # Tester l'URL fournie ainsi que le sous-chemin /moodle courant sur les instances universitaires
    candidate_urls = [raw_base_url]
    if not raw_base_url.endswith("/moodle"):
        candidate_urls.append(f"{raw_base_url}/moodle")

    # Si token absent, on tente de le générer via le service mobile sur chaque URL candidate
    if not auth_token and username and password:
        for cand in candidate_urls:
            try:
                token_url = f"{cand}/login/token.php"
                resp = requests.post(
                    token_url,
                    data={
                        "username": username,
                        "password": password,
                        "service": "moodle_mobile_app"
                    },
                    timeout=12
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("token"):
                        auth_token = data.get("token")
                        effective_base_url = cand
                        break
            except Exception as e:
                logger.debug(f"Test token Moodle sur {cand} échoué: {e}")

    if not auth_token:
        return {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": "Échec d'authentification Moodle (Token indisponible)."
        }

    # Interrogation des webservices Moodle
    ws_url = f"{effective_base_url}/webservice/rest/server.php"
    try:
        # 1. Site Info
        site_info_resp = requests.get(
            ws_url,
            params={
                "wstoken": auth_token,
                "wsfunction": "core_webservice_get_site_info",
                "moodlewsrestformat": "json"
            },
            timeout=12
        )
        site_info = site_info_resp.json()
        user_id = site_info.get("userid")

        if not user_id:
            return {
                "configured": False,
                "site_name": "Moodle",
                "courses": [],
                "upcoming_assignments": [],
                "connection_error": f"Erreur Moodle : {site_info.get('message', 'Utilisateur non identifié')}"
            }

        # 2. Courses
        courses_resp = requests.get(
            ws_url,
            params={
                "wstoken": auth_token,
                "wsfunction": "core_enrol_get_users_courses",
                "userid": user_id,
                "moodlewsrestformat": "json"
            },
            timeout=12
        )
        raw_courses = courses_resp.json()
        if not isinstance(raw_courses, list):
            raw_courses = []

        course_ids = [c["id"] for c in raw_courses if "id" in c]

        # 3. Assignments
        upcoming = []
        if course_ids:
            params = {
                "wstoken": auth_token,
                "wsfunction": "mod_assign_get_assignments",
                "moodlewsrestformat": "json"
            }
            for i, cid in enumerate(course_ids[:20]):
                params[f"courseids[{i}]"] = cid

            assign_resp = requests.get(ws_url, params=params, timeout=15)
            assign_data = assign_resp.json()

            now = datetime.datetime.now()
            courses_assignments = assign_data.get("courses", [])

            for ca in courses_assignments:
                c_name = ca.get("fullname", "Cours")
                for a in ca.get("assignments", []):
                    due_ts = a.get("duedate")
                    if due_ts and due_ts > 0:
                        due_dt = datetime.datetime.fromtimestamp(due_ts)
                        days_left = (due_dt.date() - now.date()).days
                        if days_left >= 0:
                            upcoming.append({
                                "id": a.get("id"),
                                "course_id": a.get("course"),
                                "course_name": c_name,
                                "name": a.get("name"),
                                "duedate": due_dt.isoformat(),
                                "days_left": days_left,
                                "status": "pending",
                                "submission_allowed": True,
                                "submitted": False,
                                "description": clean_html(a.get("intro", ""))
                            })

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

        return {
            "configured": True,
            "site_name": site_info.get("sitename", "Moodle"),
            "courses": parsed_courses,
            "upcoming_assignments": upcoming,
            "connection_error": None
        }

    except Exception as e:
        logger.error(f"Erreur Moodle API: {e}")
        return {
            "configured": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": str(e)
        }
