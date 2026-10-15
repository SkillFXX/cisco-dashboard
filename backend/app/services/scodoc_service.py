import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid hammering ScoDoc / CAS server
_CACHE: Dict[int, Dict[str, Any]] = {}
CACHE_TTL = 300  # 5 minutes


def get_empty_scodoc_data(error_msg: Optional[str] = None) -> Dict[str, Any]:
    """Retourne une structure vide propre lorsque ScoDoc n'est pas encore configuré ou en erreur."""
    return {
        "configured": False,
        "connection_error": error_msg,
        "formation": None,
        "annee_universitaire": None,
        "etudiant": None,
        "stats": {
            "moyenne_generale": None,
            "rang": None,
            "total_promo": None,
            "min_promo": None,
            "max_promo": None,
            "moy_promo": None
        },
        "ues": [],
        "recent_grades": [],
        "matieres": [],
        "absences": {
            "total_nb": 0,
            "total_heures": 0.0,
            "injustifiees_nb": 0,
            "injustifiees_heures": 0.0,
            "justifiees_nb": 0,
            "justifiees_heures": 0.0,
            "retards_nb": 0,
            "creneaux": []
        }
    }


def fetch_scodoc_data(
    user_id: int,
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Interroge ScoDoc via le module scodoc_api et formate les données pour le dashboard."""
    # Vérification du cache mémoire
    now = time.time()
    cached = _CACHE.get(user_id)
    if not force_refresh and cached and (now - cached.get("timestamp", 0) < CACHE_TTL):
        return cached["data"]

    # Si pas d'identifiants renseignés
    if not url or not username or not password:
        empty = get_empty_scodoc_data("Identifiants ScoDoc non configurés.")
        _CACHE[user_id] = {"timestamp": now, "data": empty}
        return empty

    # Appel réel avec le module scodoc_api
    try:
        from scodoc_api import ScoDoc
        client = ScoDoc(base_url=url, username=username, password=password, auto_login=True)
        releve = client.get_releve(force_refresh=True)

        ues_list = []
        for code, ue in releve.ues.items():
            ues_list.append({
                "code": code,
                "titre": ue.titre,
                "moyenne": ue.moyenne,
                "rang": ue.rang,
                "total_promo": ue.total_promo,
                "ects": getattr(ue, "ects_total", None) or getattr(ue, "ects_acquis", None) or getattr(ue, "ects", 0),
                "status": "Validée" if (ue.moyenne and ue.moyenne >= 10) else ("Compensable" if (ue.moyenne and ue.moyenne >= 8) else "Non validée")
            })

        recent_grades = []
        for ev in releve.notes_avec_valeur[:15]:
            recent_grades.append({
                "id": ev.id,
                "code_matiere": ev.code_matiere,
                "titre_matiere": ev.titre_matiere,
                "description": ev.description,
                "note": ev.note,
                "coefficient": ev.coefficient,
                "date": ev.date,
                "min_promo": ev.min_promo,
                "moy_promo": ev.moy_promo,
                "max_promo": ev.max_promo
            })

        matieres_list = []
        for code, mat in list(releve.ressources.items()) + list(releve.saes.items()):
            matieres_list.append({
                "code": code,
                "titre": mat.titre,
                "type": mat.type,
                "moyenne": mat.moyenne,
                "evaluations_count": len(mat.evaluations)
            })

        creneaux_abs = []
        for c in releve.absences.creneaux:
            creneaux_abs.append({
                "id": c.id,
                "date": c.date,
                "heure_debut": c.heure_debut,
                "heure_fin": c.heure_fin,
                "duree_heures": c.duree_heures,
                "matiere": c.matiere,
                "enseignant": c.enseignant,
                "justifie": c.justifie,
                "statut": "Justifiée" if c.justifie else "Injustifiée"
            })

        result = {
            "configured": True,
            "connection_error": None,
            "formation": releve.formation,
            "annee_universitaire": releve.annee_universitaire,
            "etudiant": {
                "nom": releve.etudiant.nom,
                "prenom": releve.etudiant.prenom,
                "email": releve.etudiant.email,
                "departement": releve.etudiant.departement,
                "code_nip": releve.etudiant.code_nip
            },
            "stats": {
                "moyenne_generale": releve.moyenne_generale,
                "rang": releve.rang,
                "total_promo": releve.total_promo,
                "min_promo": releve.stats.min_promo,
                "max_promo": releve.stats.max_promo,
                "moy_promo": releve.stats.moy_promo
            },
            "ues": ues_list,
            "recent_grades": recent_grades,
            "matieres": matieres_list,
            "absences": {
                "total_nb": releve.absences.total_nb,
                "total_heures": releve.absences.total_heures,
                "injustifiees_nb": releve.absences.injustifiees_nb,
                "injustifiees_heures": releve.absences.injustifiees_heures,
                "justifiees_nb": releve.absences.justifiees_nb,
                "justifiees_heures": releve.absences.justifiees_heures,
                "retards_nb": releve.absences.retards_nb,
                "creneaux": creneaux_abs
            }
        }
        _CACHE[user_id] = {"timestamp": now, "data": result}
        return result

    except Exception as e:
        logger.warning(f"Erreur connexion ScoDoc pour user {user_id}: {e}")
        err_data = get_empty_scodoc_data(f"Erreur ScoDoc : {e}")
        _CACHE[user_id] = {"timestamp": now, "data": err_data}
        return err_data
