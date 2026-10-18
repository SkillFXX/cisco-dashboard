import logging
import urllib.parse
import ipaddress
import requests
from typing import Dict, Any, Optional
from scodoc_api import ScoDoc, ScoDocAuthError, ScoDocConnectionError

logger = logging.getLogger(__name__)


def validate_service_url(url: str) -> Optional[str]:
    """Valide le format d'URL et prévient les attaques SSRF vers les réseaux sensibles."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return "L'adresse doit commencer par http:// ou https://"
        host = parsed.hostname
        if not host:
            return "Nom d'hôte de l'URL invalide."
        if host in ("169.254.169.254", "metadata.google.internal", "instance-data"):
            return "Accès aux adresses de métadonnées interdit."
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_link_local or ip.is_reserved or (ip.is_private and not ip.is_loopback):
                return "L'accès aux adresses IP privées est restreint."
        except ValueError:
            pass
        return None
    except Exception as e:
        return f"Format d'URL invalide : {e}"


def verify_scodoc(url: str, username: str, password: str) -> Dict[str, Any]:
    """
    Verifie l'authenticite des identifiants ScoDoc / CAS en recuperant le releve de notes.
    Retourne { success: bool, message: str, student_name: Optional[str], student_pic: Optional[str] }
    """
    url = (url or "").strip().rstrip("/")
    username = (username or "").strip()
    password = (password or "").strip()

    if not url:
        return {"success": False, "message": "URL du serveur ScoDoc manquante."}
    
    url_err = validate_service_url(url)
    if url_err:
        return {"success": False, "message": url_err}

    if not username or not password:
        return {"success": False, "message": "Identifiant CAS ENT ou mot de passe manquant."}

    try:
        client = ScoDoc(base_url=url, username=username, password=password, auto_login=True)
        releve = client.get_releve(force_refresh=True)

        student_name = None
        student_pic_b64 = None

        if hasattr(releve, "etudiant") and releve.etudiant:
            prenom = getattr(releve.etudiant, "prenom", "") or ""
            nom = getattr(releve.etudiant, "nom", "") or ""
            student_name = f"{prenom} {nom}".strip() or None

        try:
            student_pic_b64 = client.get_student_pic_base64()
        except Exception:
            pass

        return {
            "success": True,
            "message": f"Authentification ScoDoc réussie{f' ({student_name})' if student_name else ''}.",
            "student_name": student_name,
            "student_pic": student_pic_b64,
            "details": {
                "formation": getattr(releve, "formation", None),
                "annee": getattr(releve, "annee_universitaire", None)
            }
        }
    except ScoDocAuthError as e:
        logger.warning(f"ScoDoc auth error: {e}")
        return {
            "success": False,
            "message": "Identifiant CAS ENT ou mot de passe ScoDoc incorrect."
        }
    except ScoDocConnectionError as e:
        logger.warning(f"ScoDoc connection error: {e}")
        return {
            "success": False,
            "message": f"Impossible de joindre le serveur ScoDoc ({url}). Vérifiez l'adresse."
        }
    except Exception as e:
        logger.warning(f"ScoDoc verification exception: {e}")
        err_str = str(e).lower()
        if any(w in err_str for w in ["expirée", "authentification", "invalid", "échec", "bad credentials"]):
            return {
                "success": False,
                "message": "Identifiant CAS ENT ou mot de passe ScoDoc incorrect."
            }
        return {
            "success": False,
            "message": f"Erreur lors de la vérification ScoDoc : {str(e)}"
        }


def verify_moodle(url: str, username: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Verifie l'authenticite des identifiants ou du token Moodle via les webservices officiels.
    Retourne { success: bool, message: str, student_name: Optional[str], token: Optional[str] }
    """
    url = (url or "").strip().rstrip("/")
    username = (username or "").strip()
    password = (password or "").strip()
    token = (token or "").strip()

    if not url:
        return {"success": False, "message": "URL Moodle manquante."}

    url_err = validate_service_url(url)
    if url_err:
        return {"success": False, "message": url_err}

    if not token and (not username or not password):
        return {"success": False, "message": "Veuillez renseigner un identifiant et mot de passe, ou un jeton d'accès Moodle."}

    effective_token = token
    effective_url = url
    candidate_urls = [url]
    if not url.endswith("/moodle"):
        candidate_urls.append(f"{url}/moodle")

    if not effective_token:
        found_token = None
        last_error = None

        for cand in candidate_urls:
            try:
                resp = requests.post(
                    f"{cand}/login/token.php",
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
                        found_token = data.get("token")
                        effective_url = cand
                        break
                    elif data.get("errorcode") == "invalidlogin":
                        return {
                            "success": False,
                            "message": "Identifiant ou mot de passe Moodle incorrect."
                        }
                    elif data.get("error"):
                        last_error = data.get("error")
            except Exception as e:
                last_error = str(e)

        if not found_token:
            if last_error:
                return {
                    "success": False,
                    "message": f"Échec de connexion Moodle : {last_error}"
                }
            return {
                "success": False,
                "message": "Identifiant ou mot de passe Moodle incorrect (ou application mobile non activée sur ce Moodle)."
            }
        effective_token = found_token

    try:
        ws_url = f"{effective_url}/webservice/rest/server.php"
        resp = requests.get(
            ws_url,
            params={
                "wstoken": effective_token,
                "wsfunction": "core_webservice_get_site_info",
                "moodlewsrestformat": "json"
            },
            timeout=12
        )
        if resp.status_code != 200:
            return {
                "success": False,
                "message": f"Erreur HTTP {resp.status_code} lors du contact avec Moodle."
            }

        info = resp.json()
        if not info.get("userid"):
            return {
                "success": False,
                "message": f"Jeton ou identifiants Moodle invalides : {info.get('message', 'Accès refusé')}"
            }

        student_name = info.get("fullname")
        return {
            "success": True,
            "message": f"Authentification Moodle réussie{f' ({student_name})' if student_name else ''}.",
            "student_name": student_name,
            "token": effective_token,
            "details": {
                "sitename": info.get("sitename"),
                "username": info.get("username")
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur de communication avec Moodle : {str(e)}"
        }


def verify_ical(url: str) -> Dict[str, Any]:
    """
    Verifie l'accessibilite et la validite d'un flux d'emploi du temps iCalendar (.ics).
    Retourne { success: bool, message: str, event_count: int }
    """
    url = (url or "").strip()
    if not url:
        return {"success": False, "message": "URL de l'emploi du temps manquante."}

    url_err = validate_service_url(url)
    if url_err:
        return {"success": False, "message": url_err}

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CiscoStudent/1.0"},
            timeout=12
        )
        if resp.status_code != 200:
            return {
                "success": False,
                "message": f"Impossible d'accéder au calendrier ADE (Code HTTP {resp.status_code})."
            }

        content = resp.text
        if "BEGIN:VCALENDAR" not in content.upper():
            return {
                "success": False,
                "message": "Le lien fourni ne contient pas un flux d'emploi du temps iCalendar valide (.ics)."
            }

        event_count = content.upper().count("BEGIN:VEVENT")
        return {
            "success": True,
            "message": f"Flux d'emploi du temps ADE validé ({event_count} créneaux détectés).",
            "event_count": event_count
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur lors de la lecture du calendrier : {str(e)}"
        }

