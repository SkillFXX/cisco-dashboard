"""Donnees de l'etudiant pour l'assistant IA, en format COMPACT (peu de tokens, quota gratuit).

- build_base_context : petit socle toujours envoye (heure, prochains cours, devoirs, moyenne).
- READ_TOOLS / run_read_tool : le modele va chercher lui-meme le detail dont il a besoin (notes, absences,
  emploi du temps plus lointain, documents Moodle), sans detection de mots-cles.
- build_full_context : tout en un seul bloc, pour les modeles qui ne gerent pas les outils.
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
from .moodle_resources import get_course, list_courses
from .scodoc_service import fetch_scodoc_data

PARIS = ZoneInfo("Europe/Paris")
DAYS_FR = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
DAYS_LONG = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


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


RESOURCE_STOPWORDS = {
    "cours", "moodle", "les", "des", "pour", "dans", "sur", "avec", "une", "the", "and", "course", "module", "ressource", "ressources",
}
MAX_RESOURCE_ENTRIES = 40


def _resources_section(user: User, course_query: str) -> str:
    """Noms des documents Moodle du cours demande (le contenu des fichiers n'est jamais lu)."""
    listing = list_courses(user)
    if not listing.get("configured"):
        return "Moodle n'est pas configuré."
    courses = listing.get("courses", [])
    if not courses:
        return "Aucun cours trouvé sur Moodle."

    words = {w for w in re.findall(r"[a-z0-9]{2,}", _norm(course_query)) if w not in RESOURCE_STOPWORDS}
    scored = []
    for c in courses:
        name = _norm(f"{c['fullname']} {c['shortname']}")
        score = sum(1 for w in words if w in name)
        if score:
            scored.append((score, not c.get("ended"), c))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)

    if not scored:
        names = "; ".join(c["fullname"] for c in courses[:20] if not c.get("ended"))
        return f"Aucun cours ne correspond. Cours disponibles: {names}"

    lines = []
    for _, _, c in scored[:2]:
        data = get_course(user, c["id"])
        lines.append(f"COURS {c['fullname']} (noms des documents, contenu non lisible; téléchargement dans l'onglet Ressources):")
        if data.get("error") and not data.get("sections"):
            lines.append(f"- indisponible ({data['error']})")
            continue
        count = 0
        for sec in data.get("sections", []):
            items = []
            for m in sec["modules"]:
                if m["files"]:
                    items.extend([f["name"] for f in m["files"]] if len(m["files"]) > 1 else [m["name"]])
                elif m.get("link"):
                    items.append(f"{m['name']} (lien)")
                elif m["modname"] in ("assign", "quiz"):
                    items.append(f"{m['name']} ({m['modname']})")
            if not items:
                continue
            room = MAX_RESOURCE_ENTRIES - count
            if room <= 0:
                break
            shown = [i[:70] for i in items[:room]]
            count += len(shown)
            extra = f" (+{len(items) - len(shown)})" if len(items) > len(shown) else ""
            lines.append(f"- {sec['name'][:50]}: " + "; ".join(shown) + extra)
    return "\n".join(lines)


# --- Chargement des donnees (toutes deja en cache, aucun appel externe supplementaire) ---

def _has_moodle(creds) -> bool:
    return bool(creds and creds.moodle_url and (creds.moodle_token or (creds.moodle_username and creds.moodle_password)))


def _scodoc(user: User) -> Dict[str, Any]:
    c = user.credentials
    if c and c.scodoc_username and c.scodoc_password:
        return fetch_scodoc_data(user_id=user.id, url=c.scodoc_url, username=c.scodoc_username, password=c.scodoc_password)
    return {"configured": False}


def _timetable(user: User) -> Dict[str, Any]:
    c = user.credentials
    return fetch_timetable(ical_url=c.ical_url) if c and c.ical_url else {"configured": False}


def _moodle(user: User) -> Dict[str, Any]:
    c = user.credentials
    if _has_moodle(c):
        return fetch_moodle_data(url=c.moodle_url, username=c.moodle_username, password=c.moodle_password, token=c.moodle_token)
    return {}


def _now() -> datetime.datetime:
    return datetime.datetime.now(PARIS).replace(tzinfo=None)


def _header(user: User, now: datetime.datetime) -> str:
    return f"Maintenant: {DAYS_LONG[now.weekday()]} {now.strftime('%d/%m/%Y %H:%M')} (Paris). Étudiant: {user.full_name or 'inconnu'}, BUT."


def _grades_summary(scodoc: Dict[str, Any]) -> str:
    if not scodoc.get("configured"):
        return ""
    st = scodoc.get("stats", {})
    return f"NOTES: moyenne générale {_num(st.get('moyenne_generale'))}/20, rang {st.get('rang') or '?'}/{st.get('total_promo') or '?'}."


def _subjects_line(scodoc: Dict[str, Any]) -> str:
    subjects = [f"{m.get('code')} {m.get('titre')}" for m in scodoc.get("matieres", []) if m.get("code")]
    return ("MATIÈRES: " + "; ".join(subjects)) if subjects else ""


def build_base_context(db: Session, user: User) -> str:
    """Socle toujours envoye : peu de tokens, le reste passe par les outils."""
    now = _now()
    scodoc = _scodoc(user)
    parts = [
        _header(user, now),
        _subjects_line(scodoc),
        _grades_summary(scodoc),
        _timetable_section(_timetable(user), now, 2),
        _tasks_section(db, user, _moodle(user), _timetable(user), now),
    ]
    return "\n".join(p for p in parts if p)


def build_full_context(db: Session, user: User) -> str:
    """Tout en un seul bloc, pour les modeles sans appel d'outils (plus de tokens)."""
    now = _now()
    scodoc, timetable, moodle = _scodoc(user), _timetable(user), _moodle(user)
    parts = [
        _header(user, now),
        _subjects_line(scodoc),
        _grades_section(scodoc, compact=False),
        _absences_section(scodoc),
        _timetable_section(timetable, now, 7),
        _tasks_section(db, user, moodle, timetable, now),
    ]
    if _has_moodle(user.credentials):
        courses = [c["fullname"] for c in list_courses(user).get("courses", []) if not c.get("ended")]
        if courses:
            parts.append("COURS MOODLE (liste des documents indisponible): " + "; ".join(courses[:20]))
    return "\n".join(p for p in parts if p)


# --- Execution des outils de lecture (declares dans gemini.py) ---

MAX_TOOL_RESULT_CHARS = 5000


def run_read_tool(name: str, args: Dict[str, Any], db: Session, user: User) -> str:
    args = args or {}
    try:
        if name == "get_grades":
            out = _grades_section(_scodoc(user), compact=False)
        elif name == "get_absences":
            out = _absences_section(_scodoc(user))
        elif name == "get_timetable":
            try:
                days = max(1, min(21, int(args.get("days") or 7)))
            except (TypeError, ValueError):
                days = 7
            out = _timetable_section(_timetable(user), _now(), days)
        elif name == "list_course_documents":
            out = _resources_section(user, str(args.get("course") or ""))
        else:
            out = f"Outil inconnu: {name}"
    except Exception as e:
        out = f"Données indisponibles ({e.__class__.__name__})."
    return out[:MAX_TOOL_RESULT_CHARS]
