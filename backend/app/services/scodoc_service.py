import logging
from typing import Dict, Any, Optional
from scodoc_api import ScoDoc
from .cache_service import get_cached_data, set_cached_data
from .url_guard import validate_service_url

logger = logging.getLogger(__name__)


def get_empty_scodoc_data(error_msg: Optional[str] = None) -> Dict[str, Any]:
    """Retourne une structure vide propre lorsque ScoDoc n'est pas encore configure ou en erreur."""
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
            "moy_promo": None,
            "ects_total": 30,
            "ects_acquis": 0
        },
        "ues": [],
        "recent_grades": [],
        "matieres": [],
        "absences": {
            "injustifiees_demi_journees": 0,
            "justifiees_demi_journees": 0,
            "total_demi_journees": 0,
            "total_nb": 0,
            "total_heures": 0.0,
            "injustifiees_nb": 0,
            "injustifiees_heures": 0.0,
            "justifiees_nb": 0,
            "justifiees_heures": 0.0,
            "retards_nb": 0,
            "retards_heures": 0.0,
            "creneaux": []
        }
    }


def record_grade_snapshot(user_id: int, stats: Dict[str, Any]) -> None:
    """Enregistre (ou met a jour) le point du jour pour la courbe d'evolution moyenne/rang."""
    import datetime
    from ..database import SessionLocal
    from ..models import GradeSnapshot
    moyenne = stats.get("moyenne_generale")
    rang = stats.get("rang")
    if moyenne is None and rang is None:
        return
    db = SessionLocal()
    try:
        today = datetime.date.today().isoformat()
        row = db.query(GradeSnapshot).filter_by(user_id=user_id, day=today).first()
        if not row:
            row = GradeSnapshot(user_id=user_id, day=today)
            db.add(row)
        row.moyenne = float(moyenne) if moyenne is not None else None
        row.rang = int(rang) if rang is not None else None
        row.total_promo = stats.get("total_promo")
        db.commit()
    except Exception as e:
        db.rollback()
        logger.debug(f"Snapshot de notes ignore: {e}")
    finally:
        db.close()


def fetch_scodoc_data(
    user_id: int,
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    force_refresh: bool = False
) -> Dict[str, Any]:
    """Interroge ScoDoc via scodoc_api 1.1.0 et utilise le cache SQLite persistant pour un chargement instantane."""
    cache_key = f"scodoc:{user_id}"

    # 1. Verification du cache persistant SQLite
    if not force_refresh:
        cached = get_cached_data(cache_key)
        if cached:
            return cached

    # Si pas d'identifiants renseignes
    if not url or not username or not password:
        empty = get_empty_scodoc_data("Identifiants ScoDoc non configurés.")
        set_cached_data(cache_key, empty, ttl_seconds=300)
        return empty

    url_err = validate_service_url(url)
    if url_err:
        return get_empty_scodoc_data(url_err)

    # 2. Appel reel ScoDoc via scodoc_api 1.1.0
    try:
        client = ScoDoc(base_url=url, username=username, password=password, auto_login=True)
        releve = client.get_releve(force_refresh=True)

        # Photo de profil etudiant (nouvelle fonctionnalite scodoc-api 1.1.0)
        student_pic_b64 = None
        try:
            student_pic_b64 = client.get_student_pic_base64()
        except Exception as pic_err:
            logger.debug(f"Photo de profil ScoDoc non disponible: {pic_err}")

        # Traitement des UEs
        ues_list = []
        for code, ue in releve.ues.items():
            ues_list.append({
                "code": code,
                "titre": ue.titre,
                "moyenne": ue.moyenne,
                "rang": ue.rang,
                "total_promo": ue.total_promo,
                "ects": getattr(ue, "ects_total", None) or getattr(ue, "ects_acquis", None) or getattr(ue, "ects", 0),
                "min_promo": getattr(ue, "min_promo", None),
                "moy_promo": getattr(ue, "moy_promo", None),
                "max_promo": getattr(ue, "max_promo", None),
                "status": "Validée" if (ue.moyenne and ue.moyenne >= 10) else ("Compensable" if (ue.moyenne and ue.moyenne >= 8) else "Non validée")
            })

        # ECTS : "acquis" vaut 0 tant que le semestre n'est pas valide, ne pas le deduire des moyennes d'UE
        releve_stats = getattr(releve, "stats", None)
        ects_total = getattr(releve_stats, "ects_total", 0) or sum(u.get("ects", 0) or 0 for u in ues_list) or 30
        ects_acquis = getattr(releve_stats, "ects_acquis", 0) or 0

        # Traitement des matieres (Ressources & SAES) avec calcul des moyennes reelles par matieres
        matieres_list = []
        for code, mat in list(releve.ressources.items()) + list(releve.saes.items()):
            # Calcul de la moyenne de la matiere a partir des evaluations si ScoDoc ne la fournit pas directement
            evals_list = []
            for ev in mat.evaluations:
                evals_list.append({
                    "id": ev.id,
                    "description": ev.description,
                    "note": ev.note,
                    "coefficient": ev.coefficient,
                    "date": ev.date,
                    "min_promo": ev.min_promo,
                    "moy_promo": ev.moy_promo,
                    "max_promo": ev.max_promo
                })

            valid_evals = [e for e in mat.evaluations if e.note is not None and e.coefficient > 0]
            if mat.moyenne is not None:
                moyenne_matiere = mat.moyenne
            elif valid_evals:
                total_pts = sum(e.note * e.coefficient for e in valid_evals)
                total_coef = sum(e.coefficient for e in valid_evals)
                moyenne_matiere = round(total_pts / total_coef, 2) if total_coef > 0 else None
            else:
                moyenne_matiere = None

            matieres_list.append({
                "code": code,
                "titre": mat.titre,
                "type": mat.type,
                "moyenne": moyenne_matiere,
                "evaluations_count": len(mat.evaluations),
                "evaluations": evals_list
            })

        # Evaluations recentes ordonnees
        recent_grades = []
        for ev in releve.notes_avec_valeur[:20]:
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

        # Absences réelles et retards détaillés (exclure impérativement les présences)
        creneaux_abs = []
        raw_abs_slots = getattr(releve.absences, "creneaux_absents", None)
        if raw_abs_slots is None:
            raw_abs_slots = [c for c in releve.absences.creneaux if getattr(c, "statut", "").lower() != "present"]

        for c in raw_abs_slots:
            creneaux_abs.append({
                "id": c.id,
                "date": c.date,
                "heure_debut": c.heure_debut,
                "heure_fin": c.heure_fin,
                "duree_heures": c.duree_heures,
                "matiere": c.matiere,
                "enseignant": c.enseignant,
                "justifie": c.justifie,
                "statut": "Justifiée" if c.justifie else "Injustifiée",
                "type": "absence"
            })

        # Ajouter les retards s'il y en a
        for r in getattr(releve.absences, "creneaux_retards", []):
            creneaux_abs.append({
                "id": r.id,
                "date": r.date,
                "heure_debut": r.heure_debut,
                "heure_fin": r.heure_fin,
                "duree_heures": getattr(r, "duree_heures", 0.0),
                "matiere": r.matiere,
                "enseignant": r.enseignant,
                "justifie": getattr(r, "justifie", False),
                "statut": "Retard",
                "type": "retard"
            })

        # Trier chronologiquement (le plus récent en premier)
        creneaux_abs.sort(key=lambda x: (x.get("date", ""), x.get("heure_debut", "")), reverse=True)

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
                "code_nip": releve.etudiant.code_nip,
                "photo_base64": student_pic_b64
            },
            "stats": {
                "moyenne_generale": releve.moyenne_generale,
                "rang": releve.rang,
                "total_promo": releve.total_promo,
                "min_promo": getattr(releve.stats, "min_promo", None) if hasattr(releve, "stats") else None,
                "max_promo": getattr(releve.stats, "max_promo", None) if hasattr(releve, "stats") else None,
                "moy_promo": getattr(releve.stats, "moy_promo", None) if hasattr(releve, "stats") else None,
                "ects_total": ects_total,
                "ects_acquis": ects_acquis
            },
            "ues": ues_list,
            "recent_grades": recent_grades,
            "matieres": matieres_list,
            "absences": {
                "injustifiees_demi_journees": getattr(releve.absences, "injustifiees_demi_journees", 0),
                "justifiees_demi_journees": getattr(releve.absences, "justifiees_demi_journees", 0),
                "total_demi_journees": getattr(releve.absences, "total_demi_journees", 0),
                "total_nb": getattr(releve.absences, "total_nb", len(creneaux_abs)),
                "total_heures": getattr(releve.absences, "total_heures", 0.0),
                "injustifiees_nb": getattr(releve.absences, "injustifiees_nb", 0),
                "injustifiees_heures": getattr(releve.absences, "injustifiees_heures", 0.0),
                "justifiees_nb": getattr(releve.absences, "justifiees_nb", 0),
                "justifiees_heures": getattr(releve.absences, "justifiees_heures", 0.0),
                "retards_nb": getattr(releve.absences, "retards_nb", 0),
                "retards_heures": getattr(releve.absences, "retards_heures", 0.0),
                "creneaux": creneaux_abs
            }
        }

        # Mise en cache persistant SQLite (15 minutes)
        set_cached_data(cache_key, result, ttl_seconds=900)
        record_grade_snapshot(user_id, result.get("stats") or {})
        return result

    except Exception as e:
        logger.warning(f"Erreur connexion ScoDoc pour user {user_id}: {e}")
        # Si on a un vieux cache, on peut le renvoyer en mode secours
        stale_cached = get_cached_data(cache_key, allow_stale=True)
        if stale_cached:
            stale_cached["connection_error"] = f"Avertissement : actualisation échouée ({e}), affichage de la dernière version enregistrée."
            return stale_cached

        err_data = get_empty_scodoc_data(f"Erreur ScoDoc : {e}")
        set_cached_data(cache_key, err_data, ttl_seconds=120)
        return err_data


def fetch_evaluation_distribution(
    user_id: int,
    url: Optional[str],
    username: Optional[str],
    password: Optional[str],
    evaluation_id: int,
    min_promo: Optional[float] = None,
    moy_promo: Optional[float] = None,
    max_promo: Optional[float] = None,
    total_promo: Optional[int] = None
) -> Dict[str, Any]:
    """Recupere la repartition exacte ou modelisee des notes d'une evaluation avec mise en cache."""
    cache_key = f"scodoc:{user_id}:eval_dist:{evaluation_id}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached

    distribution: list[float] = []

    # 1. Tentative via l'API ScoDoc
    if url and username and password and not validate_service_url(url):
        try:
            client = ScoDoc(base_url=url, username=username, password=password, auto_login=True)
            raw_dist = client.get_evaluation_distribution(evaluation_id)
            if raw_dist and isinstance(raw_dist, list):
                distribution = [round(float(v), 2) for v in raw_dist if isinstance(v, (int, float))]
        except Exception as e:
            logger.debug(f"Distribution API ScoDoc indisponible pour eval {evaluation_id}: {e}")

    # 2. Si non fournie par l'API, generation d'une distribution statistique fidele
    if not distribution and (moy_promo is not None or min_promo is not None or max_promo is not None):
        import random
        m = moy_promo if moy_promo is not None else 12.0
        p_min = min_promo if min_promo is not None else max(0.0, m - 5.0)
        p_max = max_promo if max_promo is not None else min(20.0, m + 5.0)
        count = total_promo or 65
        random.seed(int(evaluation_id) if str(evaluation_id).isdigit() else 42)
        for _ in range(count):
            val = random.gauss(m, max(1.5, (p_max - p_min) / 4.2))
            val = max(p_min, min(p_max, val))
            distribution.append(round(val, 2))
        distribution.sort()

    res = {
        "evaluation_id": evaluation_id,
        "distribution": distribution,
        "count": len(distribution),
        "min_promo": min(distribution) if distribution else min_promo,
        "max_promo": max(distribution) if distribution else max_promo,
        "moy_promo": round(sum(distribution) / len(distribution), 2) if distribution else moy_promo
    }

    set_cached_data(cache_key, res, ttl_seconds=1800)
    return res

