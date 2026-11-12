"""Construit un contexte texte COMPACT sur l'etudiant pour l'assistant IA.

Objectif : peu de tokens (quota gratuit). On ne joint que les rubriques utiles a la question,
dans un format dense, a partir des donnees deja en cache (aucun appel externe supplementaire).
"""
import datetime
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from ..models import User, PersonalTask, CompletedExternalTask
from .ical_service import fetch_timetable
from .moodle_service import fetch_moodle_data
from .scodoc_service import fetch_scodoc_data

PARIS = ZoneInfo("Europe/Paris")
DAYS_FR = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
DAYS_LONG = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "grades": ["note", "moyenne", " ue", "ue1", "ue2", "ue3", "rang", "classement", "ects", "resultat", "controle", "evaluation",
               "matiere", "ressource", "sae", "module", "point", "valide", "bulletin", "promo", "coef", "r10", "r11", "ds "],
    "absences": ["absen", "retard", "justif", "assidu", "manque"],
    "timetable": ["cours", "emploi", "planning", "salle", "prof", "enseignant", "demain", "aujourd", "semaine", "horaire", "heure",
                  "lundi", "mardi", "mercredi", "jeudi", "vendredi", "prochain", "libre", "edt", "amphi", "groupe", "finis", "commence"],
    "tasks": ["devoir", "rendre", "rendu", "deadline", "echeance", "dm ", "faire", "travail", "moodle", "reviser", "projet", "tp ", "ds ", "date limite"],
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def detect_topics(texts: List[str]) -> Set[str]:
    blob = " " + _norm(" ".join(texts)) + " "
    return {topic for topic, words in TOPIC_KEYWORDS.items() if any(w in blob for w in words)}


def _num(v: Any) -> str:
    try:
        return f"{float(v):.2f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return "?"


def _fmt_date(iso: str) -> str:
    d = datetime.date.fromisoformat(iso[:10])
    return f"{DAYS_FR[d.weekday()]} {d.day:02d}/{d.month:02d}"


def _grades_section(data: Dict[str, Any], compact: bool) -> str:
    if not data.get("configured"):
        return "NOTES: ScoDoc non configuré."
    st = data.get("stats", {})
    lines = [
        f"NOTES (/20): moyenne générale {_num(st.get('moyenne_generale'))}, rang {st.get('rang') or '?'}/{st.get('total_promo') or '?'}, "
        f"promo min {_num(st.get('min_promo'))} moy {_num(st.get('moy_promo'))} max {_num(st.get('max_promo'))}, "
        f"ECTS {st.get('ects_acquis', 0)}/{st.get('ects_total', 30)}."
    ]
    for ue in data.get("ues", []):
        lines.append(f"UE {ue.get('code')} {ue.get('titre')}: {_num(ue.get('moyenne'))}, rang {ue.get('rang') or '?'}/{ue.get('total_promo') or '?'}, promo moy {_num(ue.get('moy_promo'))}")
    evals: List[tuple] = []
    for mat in data.get("matieres", []):
        notes = [e for e in mat.get("evaluations", []) if e.get("note") is not None]
        if mat.get("moyenne") is not None:
            lines.append(f"{mat.get('code')} {mat.get('titre')}: moyenne {_num(mat['moyenne'])} ({len(notes)} éval.)")
        for e in notes:
            evals.append((e.get("date") or "", mat.get("code"), e))
    evals.sort(key=lambda t: t[0], reverse=True)
    limit = 12 if compact else 25
    for date, code, e in evals[:limit]:
        promo = f", promo moy {_num(e['moy_promo'])}" if e.get("moy_promo") is not None else ""
        lines.append(f"- {date[:10]} {code} {e.get('description') or 'éval'}: {_num(e.get('note'))} (coef {_num(e.get('coefficient'))}{promo})")
    return "\n".join(lines)


def _absences_section(data: Dict[str, Any]) -> str:
    ab = data.get("absences") or {}
    if not data.get("configured"):
        return "ABSENCES: ScoDoc non configuré."
    lines = [
        f"ABSENCES: non justifiées {ab.get('injustifiees_demi_journees', 0)} demi-j ({_num(ab.get('injustifiees_heures'))} h), "
        f"justifiées {ab.get('justifiees_demi_journees', 0)} demi-j, total {_num(ab.get('total_heures'))} h, retards {ab.get('retards_nb', 0)}."
    ]
    for c in (ab.get("creneaux") or [])[:8]:
        lines.append(f"- {c.get('date')} {c.get('heure_debut')}-{c.get('heure_fin')} {c.get('matiere')}: {c.get('statut')}")
    return "\n".join(lines)


def _timetable_section(data: Dict[str, Any], now: datetime.datetime, days: int) -> str:
    if not data.get("configured"):
        return "EMPLOI DU TEMPS: lien non configuré."
    start = now.date()
    end = start + datetime.timedelta(days=days)
    events = [e for e in data.get("all_events", []) if start.isoformat() <= e["date"] < end.isoformat()]
    if not events:
        return f"EMPLOI DU TEMPS ({days} prochains jours): aucun cours."
    now_iso = now.strftime("%Y-%m-%dT%H:%M")

    def status(e: Dict[str, Any]) -> str:
        if e["dt_end"][:16] <= now_iso:
            return " (terminé)"
        if e["dt_start"][:16] <= now_iso:
            return " (EN COURS)"
        return ""

    current = next((e for e in events if status(e) == " (EN COURS)"), None)
    upcoming = next((e for e in events if e["dt_start"][:16] > now_iso), None)
    lines = [f"EMPLOI DU TEMPS ({days} prochains jours, heures de Paris, il est {now.strftime('%H:%M')}):"]
    if current:
        lines.append(f"Cours en ce moment: {current['title']} jusqu'à {current['end_time']}.")
    if upcoming:
        lines.append(f"PROCHAIN COURS: {_fmt_date(upcoming['date'])} {upcoming['start_time']} {upcoming['title']}.")
    last_date = None
    for e in events[:45]:
        if e["date"] != last_date:
            lines.append(f"{_fmt_date(e['date'])}:")
            last_date = e["date"]
        extra = " | ".join(x for x in (e.get("location"), e.get("teacher")) if x)
        lines.append(f"  {e['start_time']}-{e['end_time']} {e['title']}" + (f" | {extra}" if extra else "") + status(e))
    return "\n".join(lines)


def _tasks_section(db: Session, user: User, moodle: Dict[str, Any], timetable: Dict[str, Any], now: datetime.datetime) -> str:
    done = {r.item_id for r in db.query(CompletedExternalTask).filter(CompletedExternalTask.user_id == user.id)}
    items: List[tuple] = []
    for t in db.query(PersonalTask).filter(PersonalTask.user_id == user.id, PersonalTask.status == "todo"):
        items.append((t.due_date, f"{t.title} ({t.subject or 'perso'}) [{t.event_type}]"))
    for a in moodle.get("upcoming_assignments", []):
        if f"moodle-{a.get('id')}" in done:
            continue
        try:
            items.append((datetime.datetime.fromisoformat(a["duedate"]), f"{a.get('name')} [Moodle]"))
        except (KeyError, ValueError):
            pass
    for e in timetable.get("all_events", []):
        if str(e.get("type", "")).upper() == "DS" and f"timetable-{e.get('id') or e['dt_start']}" not in done:
            items.append((datetime.datetime.fromisoformat(e["dt_start"]), f"{e['title']} [DS calendrier]"))
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    items = sorted((i for i in items if i[0] >= today), key=lambda i: i[0])[:20]
    if not items:
        return "DEVOIRS À FAIRE: aucun."
    lines = ["DEVOIRS À FAIRE (échéance):"]
    for due, label in items:
        lines.append(f"- {_fmt_date(due.isoformat())} {due.strftime('%H:%M')} {label}")
    courses = [c.get("fullname") or c.get("shortname") for c in moodle.get("courses", []) if c.get("fullname") or c.get("shortname")]
    if courses:
        lines.append("Cours Moodle: " + "; ".join(courses[:12]))
    return "\n".join(lines)


def build_context(db: Session, user: User, question_texts: List[str], with_subjects: bool = False) -> str:
    now = datetime.datetime.now(PARIS).replace(tzinfo=None)
    creds = user.credentials
    topics = detect_topics(question_texts)
    broad = not topics and not with_subjects
    wanted = set(TOPIC_KEYWORDS) if broad else (topics or {"tasks"})
    if with_subjects:
        wanted = wanted | {"subjects"}

    header = (
        f"Maintenant: {DAYS_LONG[now.weekday()]} {now.strftime('%d/%m/%Y %H:%M')} (Paris). "
        f"Étudiant: {user.full_name or 'inconnu'}, BUT Réseaux & Télécoms."
    )
    parts = [header]

    scodoc: Dict[str, Any] = {}
    if wanted & {"grades", "absences", "subjects"} and creds and creds.scodoc_username and creds.scodoc_password:
        scodoc = fetch_scodoc_data(user_id=user.id, url=creds.scodoc_url, username=creds.scodoc_username, password=creds.scodoc_password)
    elif wanted & {"grades", "absences", "subjects"}:
        scodoc = {"configured": False}

    timetable: Dict[str, Any] = {}
    if wanted & {"timetable", "tasks"} and creds and creds.ical_url:
        timetable = fetch_timetable(ical_url=creds.ical_url)
    elif wanted & {"timetable", "tasks"}:
        timetable = {"configured": False}

    moodle: Dict[str, Any] = {}
    if "tasks" in wanted and creds and creds.moodle_url and (creds.moodle_token or (creds.moodle_username and creds.moodle_password)):
        moodle = fetch_moodle_data(url=creds.moodle_url, username=creds.moodle_username, password=creds.moodle_password, token=creds.moodle_token)

    if with_subjects:
        subjects = [f"{m.get('code')} {m.get('titre')}" for m in scodoc.get("matieres", []) if m.get("code")]
        if subjects:
            parts.append("MATIÈRES: " + "; ".join(subjects))
    if "grades" in wanted:
        parts.append(_grades_section(scodoc, compact=broad))
    if "absences" in wanted:
        parts.append(_absences_section(scodoc))
    if "timetable" in wanted:
        blob = _norm(" ".join(question_texts))
        parts.append(_timetable_section(timetable, now, 14 if "prochaine" in blob or "quinzaine" in blob else (4 if broad else 7)))
    if "tasks" in wanted:
        parts.append(_tasks_section(db, user, moodle, timetable, now))
    return "\n".join(parts)


ACTION_WORDS = ["ajout", "rajout", "cree", "creer", "rappel", "planifi", "programme", "enregistr", "inscri", "mets", "mettre", "met "]


def wants_action(texts: List[str]) -> bool:
    """Vrai si la question demande d'ajouter quelque chose (les outils ne sont alors déclarés qu'à ce moment, pour économiser des tokens)."""
    blob = " " + _norm(" ".join(texts)) + " "
    return any(w in blob for w in ACTION_WORDS)
