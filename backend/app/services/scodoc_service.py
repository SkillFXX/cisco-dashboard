import logging
import datetime
from typing import Dict, Any, Optional, List
import time

logger = logging.getLogger(__name__)

# Simple in-memory cache to avoid hammering ScoDoc / CAS server
_CACHE: Dict[int, Dict[str, Any]] = {}
CACHE_TTL = 300 # 5 minutes

def get_rt_mock_scodoc() -> Dict[str, Any]:
    """Retourne un relevé réaliste BUT Réseaux et Télécoms pour démo ou fallback."""
    today = datetime.date.today()
    d1 = (today - datetime.timedelta(days=2)).isoformat()
    d2 = (today - datetime.timedelta(days=5)).isoformat()
    d3 = (today - datetime.timedelta(days=9)).isoformat()
    d4 = (today - datetime.timedelta(days=14)).isoformat()
    d5 = (today - datetime.timedelta(days=18)).isoformat()

    return {
        "is_mock": True,
        "formation": "BUT Réseaux et Télécommunications - Semestre 1",
        "annee_universitaire": "2026-2027",
        "etudiant": {
            "nom": "DUPONT",
            "prenom": "Alexandre",
            "email": "alexandre.dupont@etu.umontpellier.fr",
            "departement": "RT",
            "code_nip": "22401892"
        },
        "stats": {
            "moyenne_generale": 14.38,
            "rang": 6,
            "total_promo": 54,
            "min_promo": 7.45,
            "max_promo": 17.82,
            "moy_promo": 12.15
        },
        "ues": [
            {
                "code": "UE1.1",
                "titre": "Administrer les réseaux et l'Internet",
                "moyenne": 14.85,
                "rang": 5,
                "total_promo": 54,
                "ects": 10,
                "status": "Validée"
            },
            {
                "code": "UE1.2",
                "titre": "Connecter les entreprises et les usagers",
                "moyenne": 13.90,
                "rang": 8,
                "total_promo": 54,
                "ects": 10,
                "status": "Validée"
            },
            {
                "code": "UE1.3",
                "titre": "Créer des outils et applications informatiques",
                "moyenne": 14.40,
                "rang": 7,
                "total_promo": 54,
                "ects": 10,
                "status": "Validée"
            }
        ],
        "recent_grades": [
            {
                "id": 101,
                "code_matiere": "R101",
                "titre_matiere": "Initiation aux Réseaux Informatiques",
                "description": "DS 2 : Adressage IPv4, Masques & Sous-réseaux (VLSM)",
                "note": 16.5,
                "coefficient": 2.0,
                "date": d1,
                "min_promo": 6.0,
                "moy_promo": 12.8,
                "max_promo": 19.5
            },
            {
                "id": 102,
                "code_matiere": "R107",
                "titre_matiere": "Fondamentaux des Systèmes d'Exploitation (Linux)",
                "description": "TP Noté : Scripts Bash & Gestion des Permissions",
                "note": 15.0,
                "coefficient": 1.5,
                "date": d2,
                "min_promo": 8.0,
                "moy_promo": 13.2,
                "max_promo": 18.0
            },
            {
                "id": 103,
                "code_matiere": "R102",
                "titre_matiere": "Principes des Télécommunications",
                "description": "Contrôle Continu : Modulation & Analyse Spectrale",
                "note": 13.0,
                "coefficient": 1.0,
                "date": d3,
                "min_promo": 5.5,
                "moy_promo": 11.4,
                "max_promo": 17.5
            },
            {
                "id": 104,
                "code_matiere": "SAÉ 1.1",
                "titre_matiere": "Découverte d'un environnement réseau",
                "description": "Soutenance de projet & Rapport Packet Tracer",
                "note": 17.0,
                "coefficient": 3.0,
                "date": d4,
                "min_promo": 10.0,
                "moy_promo": 14.1,
                "max_promo": 18.5
            },
            {
                "id": 105,
                "code_matiere": "R108",
                "titre_matiere": "Initiation au développement (Python)",
                "description": "Projet Socket Client/Serveur TCP",
                "note": 14.5,
                "coefficient": 1.5,
                "date": d5,
                "min_promo": 7.0,
                "moy_promo": 12.6,
                "max_promo": 19.0
            }
        ],
        "matieres": [
            {
                "code": "R101",
                "titre": "Initiation aux Réseaux",
                "type": "ressource",
                "moyenne": 15.75,
                "evaluations_count": 3
            },
            {
                "code": "R102",
                "titre": "Principes des Télécoms",
                "type": "ressource",
                "moyenne": 13.00,
                "evaluations_count": 2
            },
            {
                "code": "R103",
                "titre": "Bases de l'électronique",
                "type": "ressource",
                "moyenne": 12.50,
                "evaluations_count": 2
            },
            {
                "code": "R107",
                "titre": "Systèmes d'exploitation (Linux)",
                "type": "ressource",
                "moyenne": 15.50,
                "evaluations_count": 3
            },
            {
                "code": "R108",
                "titre": "Initiation Dev (Python)",
                "type": "ressource",
                "moyenne": 14.50,
                "evaluations_count": 2
            },
            {
                "code": "SAÉ 1.1",
                "titre": "Découverte réseau local",
                "type": "sae",
                "moyenne": 17.00,
                "evaluations_count": 1
            }
        ],
        "absences": {
            "total_nb": 3,
            "total_heures": 4.5,
            "injustifiees_nb": 1,
            "injustifiees_heures": 1.5,
            "justifiees_nb": 2,
            "justifiees_heures": 3.0,
            "retards_nb": 1,
            "creneaux": [
                {
                    "id": 1,
                    "date": (today - datetime.timedelta(days=3)).strftime("%d/%m/%Y"),
                    "heure_debut": "08:00",
                    "heure_fin": "09:30",
                    "duree_heures": 1.5,
                    "matiere": "R102 - Principes des Télécommunications",
                    "enseignant": "M. LEROUX",
                    "justifie": False,
                    "statut": "Injustifiée"
                },
                {
                    "id": 2,
                    "date": (today - datetime.timedelta(days=12)).strftime("%d/%m/%Y"),
                    "heure_debut": "14:00",
                    "heure_fin": "17:00",
                    "duree_heures": 3.0,
                    "matiere": "R107 - TP Linux & Shell",
                    "enseignant": "Mme MARTINEZ",
                    "justifie": True,
                    "statut": "Justifiée (Certificat médical)"
                }
            ]
        }
    }


def fetch_scodoc_data(user_id: int, url: Optional[str], username: Optional[str], password: Optional[str], force_refresh: bool = False, use_mock_fallback: bool = True) -> Dict[str, Any]:
    """Interroge ScoDoc via le module scodoc_api ou renvoie le mock si non configuré."""
    # Check cache
    now = time.time()
    cached = _CACHE.get(user_id)
    if not force_refresh and cached and (now - cached.get("timestamp", 0) < CACHE_TTL):
        return cached["data"]

    # Si pas d'identifiants renseignés
    if not url or not username or not password:
        if use_mock_fallback:
            mock = get_rt_mock_scodoc()
            _CACHE[user_id] = {"timestamp": now, "data": mock}
            return mock
        raise ValueError("Identifiants ScoDoc non configurés.")

    # Tentative d'appel réel avec le module scodoc_api
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
            "is_mock": False,
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
        if use_mock_fallback:
            mock = get_rt_mock_scodoc()
            mock["connection_error"] = str(e)
            return mock
        raise

