import logging
import datetime
from typing import Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def get_rt_mock_moodle() -> Dict[str, Any]:
    """Retourne des cours et devoirs Moodle réalistes pour un étudiant BUT R&T."""
    today = datetime.datetime.now()

    def future_iso(days: int, hours: int = 23, minutes: int = 59) -> str:
        d = today + datetime.timedelta(days=days)
        return d.replace(hour=hours, minute=minutes, second=0, microsecond=0).isoformat()

    return {
        "is_mock": True,
        "site_name": "Moodle Université de Montpellier",
        "courses": [
            {
                "id": 101,
                "fullname": "R101 - Initiation aux Réseaux Informatiques",
                "shortname": "BUT1-RT-R101",
                "category": "Ressources Réseaux",
                "teacher": "M. DELMAS",
                "assignments_count": 2
            },
            {
                "id": 102,
                "fullname": "R102 - Principes des Télécommunications & Signal",
                "shortname": "BUT1-RT-R102",
                "category": "Ressources Télécoms",
                "teacher": "M. LEROUX",
                "assignments_count": 1
            },
            {
                "id": 107,
                "fullname": "R107 - Fondamentaux des Systèmes Linux",
                "shortname": "BUT1-RT-R107",
                "category": "Systèmes & Outils",
                "teacher": "Mme MARTINEZ",
                "assignments_count": 1
            },
            {
                "id": 108,
                "fullname": "R108 - Initiation au Développement Python",
                "shortname": "BUT1-RT-R108",
                "category": "Développement",
                "teacher": "M. ROUSTAN",
                "assignments_count": 0
            },
            {
                "id": 110,
                "fullname": "SAÉ 1.1 - Découverte & Maquettage Réseau Local",
                "shortname": "BUT1-RT-SAE11",
                "category": "SAÉ Projets",
                "teacher": "Équipe R&T",
                "assignments_count": 1
            }
        ],
        "upcoming_assignments": [
            {
                "id": 201,
                "course_id": 101,
                "course_name": "R101 - Initiation aux Réseaux",
                "name": "DM 1 : Capture Wireshark et Analyse des trames ARP / ICMP",
                "duedate": future_iso(days=2, hours=23, minutes=59),
                "days_left": 2,
                "status": "pending",
                "submission_allowed": True,
                "submitted": False,
                "description": "Analyser le fichier pcap fourni. Compléter le rapport PDF et justifier les échanges de requêtes ARP et encapsulation Ethernet."
            },
            {
                "id": 202,
                "course_id": 107,
                "course_name": "R107 - Systèmes Linux",
                "name": "TP Noté : Script Bash de sauvegarde et parsing de logs",
                "duedate": future_iso(days=5, hours=18, minutes=0),
                "days_left": 5,
                "status": "pending",
                "submission_allowed": True,
                "submitted": False,
                "description": "Déposer votre script 'backup_logs.sh' documenté avec gestion des arguments et droits d'exécution."
            },
            {
                "id": 203,
                "course_id": 102,
                "course_name": "R102 - Principes Télécoms",
                "name": "Compte-Rendu : Bilan de liaison radio & Atténuation en espace libre",
                "duedate": future_iso(days=8, hours=23, minutes=59),
                "days_left": 8,
                "status": "pending",
                "submission_allowed": True,
                "submitted": False,
                "description": "Calculs de puissance reçue Pr, formule de Friis et graphes sous Python ou Excel."
            },
            {
                "id": 204,
                "course_id": 110,
                "course_name": "SAÉ 1.1 - Réseau d'entreprise",
                "name": "Dossier Technique SAÉ 1.1 & Fichier Cisco Packet Tracer (.pkt)",
                "duedate": future_iso(days=12, hours=12, minutes=0),
                "days_left": 12,
                "status": "pending",
                "submission_allowed": True,
                "submitted": False,
                "description": "Rapport complet de l'architecture réseau de la PME avec le plan d'adressage IPv4 VLSM et maquette opérationnelle."
            }
        ]
    }


def clean_html(raw_html: Optional[str]) -> str:
    """Nettoie le HTML d'une description Moodle pour n'en garder que le texte clair."""
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
    token: Optional[str] = None,
    use_mock_fallback: bool = True
) -> Dict[str, Any]:
    """Récupère les cours et devoirs depuis l'API Moodle WebService."""
    if not url or (not token and (not username or not password)):
        if use_mock_fallback:
            return get_rt_mock_moodle()
        return {
            "is_mock": False,
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
        if use_mock_fallback:
            mock = get_rt_mock_moodle()
            mock["connection_error"] = "Échec d'authentification Moodle (Token indisponible)."
            return mock
        return {
            "is_mock": False,
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
        userid = site_info.get("userid")

        # 2. Cours
        courses_resp = requests.get(
            ws_url,
            params={
                "wstoken": auth_token,
                "wsfunction": "core_enrol_get_users_courses",
                "userid": userid,
                "moodlewsrestformat": "json"
            },
            timeout=12
        )
        raw_courses = courses_resp.json() if isinstance(courses_resp.json(), list) else []
        course_ids = [c["id"] for c in raw_courses if "id" in c]

        # 3. Devoirs (assignments)
        upcoming = []
        if course_ids:
            assign_params = {
                "wstoken": auth_token,
                "wsfunction": "mod_assign_get_assignments",
                "moodlewsrestformat": "json"
            }
            # Prendre jusqu'à 30 cours
            for idx, cid in enumerate(course_ids[:30]):
                assign_params[f"courseids[{idx}]"] = cid

            assign_resp = requests.get(ws_url, params=assign_params, timeout=12)
            assign_data = assign_resp.json()
            courses_assignments = assign_data.get("courses", [])

            today_date = datetime.date.today()

            for c in courses_assignments:
                c_name = c.get("fullname", "")
                for a in c.get("assignments", []):
                    duedate = a.get("duedate", 0)
                    if duedate and duedate > 0:
                        due_dt = datetime.datetime.fromtimestamp(duedate)
                        # Ne conserver STRICTEMENT que les devoirs d'aujourd'hui et à venir
                        if due_dt.date() >= today_date:
                            days_left = (due_dt.date() - today_date).days
                            upcoming.append({
                                "id": a.get("id"),
                                "course_id": c.get("id"),
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
                "teacher": "Enseignant R&T",
                "assignments_count": 0
            }
            for c in raw_courses
        ]

        return {
            "is_mock": False,
            "site_name": site_info.get("sitename", "Moodle"),
            "courses": parsed_courses,
            "upcoming_assignments": upcoming
        }

    except Exception as e:
        logger.error(f"Erreur Moodle API: {e}")
        if use_mock_fallback:
            mock = get_rt_mock_moodle()
            mock["connection_error"] = str(e)
            return mock
        return {
            "is_mock": False,
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": str(e)
        }
