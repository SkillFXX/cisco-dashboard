import re
import logging
import datetime
from typing import Dict, Any, Optional, List
import requests
import icalendar
import recurring_ical_events

logger = logging.getLogger(__name__)


def detect_course_type(summary: str, description: str = "", location: str = "") -> str:
    """Détecte la catégorie de cours selon le nom du cours dans l'ordre spécifié."""
    title = (summary or "").upper()

    if "DS" in title:
        return "DS"
    if "SAE" in title or "SAÉ" in title:
        return "SAE"
    if "TP" in title:
        return "TP"
    if "TD" in title:
        return "TD"
    if "CM" in title:
        return "CM"

    return "COURS"


_STATUS_RE = re.compile(r"^(a\s+)?valid(é|ée|e|er)s?$", re.IGNORECASE)
_TEACHER_RE = re.compile(r"^[^a-zà-ÿ]+\S\s{2,}\S[^a-zà-ÿ]*$")


def parse_description(description: str) -> Dict[str, str]:
    """Extrait enseignants et groupes de la description ADE.

    Les lignes arrivent dans un ordre variable (groupe, enseignant, statut de validation, date d'export...),
    on les classe donc par leur forme plutot que par leur position.
    """
    teachers: List[str] = []
    groups: List[str] = []
    for raw in description.replace("\\n", "\n").split("\n"):
        line = " ".join(raw.split())
        if not line or line.startswith(("#", "(Exported")) or _STATUS_RE.match(line):
            continue
        if line.upper().startswith(("ZZ ", "SAE ")) or "A DEFINIR" in line.upper():
            continue
        if _TEACHER_RE.match(raw.strip()):
            name = line.title()
            if name not in teachers:
                teachers.append(name)
        elif line not in groups:
            groups.append(line)
    return {"teacher": ", ".join(teachers), "group": ", ".join(groups)}


def parse_ical_stream(ical_content: str) -> List[Dict[str, Any]]:
    """Parse un flux iCal (.ics) ADE, Hyperplanning...."""
    cal = icalendar.Calendar.from_ical(ical_content)
    now = datetime.datetime.now()
    today = datetime.date.today()
    # Depuis la rentrée (1er septembre) pour pouvoir consulter les semaines passées, jusqu'à 4 mois devant
    year = today.year if today.month >= 9 else today.year - 1
    start_search = datetime.date(year, 9, 1)
    end_search = today + datetime.timedelta(days=120)

    recurring_events = recurring_ical_events.of(cal).between(start_search, end_search)

    parsed = []
    for ev in recurring_events:
        summary = str(ev.get("SUMMARY", "Cours"))
        location = str(ev.get("LOCATION", "Salle non précisée"))
        description = str(ev.get("DESCRIPTION", ""))

        dt_start = ev.get("DTSTART").dt
        dt_end = ev.get("DTEND").dt

        # Ensure datetime
        if isinstance(dt_start, datetime.date) and not isinstance(dt_start, datetime.datetime):
            dt_start = datetime.datetime.combine(dt_start, datetime.time(8, 0))
        if isinstance(dt_end, datetime.date) and not isinstance(dt_end, datetime.datetime):
            dt_end = datetime.datetime.combine(dt_end, datetime.time(9, 30))

        # Convertir correctement le fuseau horaire vers Europe/Paris (heure locale française)
        from zoneinfo import ZoneInfo
        paris_tz = ZoneInfo("Europe/Paris")

        if dt_start.tzinfo is not None:
            dt_start = dt_start.astimezone(paris_tz).replace(tzinfo=None)
        if dt_end.tzinfo is not None:
            dt_end = dt_end.astimezone(paris_tz).replace(tzinfo=None)

        evt_type = detect_course_type(summary, description, location)
        people = parse_description(description)

        is_current = (dt_start <= now <= dt_end)
        is_passed = (now > dt_end)

        day_offset = dt_start.weekday()
        day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

        parsed.append({
            "id": str(ev.get("UID", f"ical-{dt_start.timestamp()}")),
            "title": summary,
            "type": evt_type,
            "date": dt_start.date().isoformat(),
            "day_name": day_names[day_offset] if day_offset < 7 else "",
            "start_time": dt_start.strftime("%H:%M"),
            "end_time": dt_end.strftime("%H:%M"),
            "dt_start": dt_start.isoformat(),
            "dt_end": dt_end.isoformat(),
            "duration_minutes": int((dt_end - dt_start).total_seconds() / 60),
            "location": location,
            "teacher": people["teacher"],
            "group": people["group"],
            "is_current": is_current,
            "is_passed": is_passed
        })

    parsed.sort(key=lambda x: x["dt_start"])
    return parsed


import hashlib
from .cache_service import get_cached_data, set_cached_data, ical_cache_key
from .url_guard import safe_get


def fetch_timetable(ical_url: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """Recupere l'emploi du temps depuis l'URL iCal avec cache SQLite persistant."""
    if not ical_url or ical_url.strip() == "":
        return _format_timetable_response([], configured=False)

    clean_url = ical_url.strip()
    cache_key = ical_cache_key(clean_url)

    if not force_refresh:
        cached = get_cached_data(cache_key)
        if cached:
            # Re-calculer dynamiquement is_current et is_passed pour les cours selon l'heure courante
            return _refresh_event_statuses(cached)

    try:
        status_code, content = safe_get(clean_url, timeout=20)
        if status_code != 200:
            raise ValueError(f"Code HTTP {status_code}")
        events = parse_ical_stream(content)
        res = _format_timetable_response(events, configured=True)
        set_cached_data(cache_key, res, ttl_seconds=900)
        return res
    except Exception as e:
        logger.warning(f"Erreur lors de la recuperation iCal: {e}")
        stale = get_cached_data(cache_key, allow_stale=True)
        if stale:
            stale["connection_error"] = f"Avertissement actualisation ({e}). Affichage de la version enregistree."
            return _refresh_event_statuses(stale)
        return _format_timetable_response([], configured=True, connection_error=str(e))


def _refresh_event_statuses(data: Dict[str, Any]) -> Dict[str, Any]:
    """Met a jour en direct is_current, is_passed et le prochain cours d'apres les evenements caches."""
    now = datetime.datetime.now()
    events = data.get("all_events", [])
    today_str = datetime.date.today().isoformat()

    today_events = []
    upcoming = []

    for e in events:
        try:
            dt_start = datetime.datetime.fromisoformat(e["dt_start"])
            dt_end = datetime.datetime.fromisoformat(e["dt_end"])
            e["is_current"] = (dt_start <= now <= dt_end)
            e["is_passed"] = (now > dt_end)
            e["type"] = detect_course_type(e.get("title", ""), e.get("description", ""), e.get("location", ""))
            if e.get("date") == today_str:
                today_events.append(e)
            if dt_start > now:
                upcoming.append(e)
        except Exception:
            pass

    current_course = next((e for e in events if e.get("is_current")), None)
    next_course = upcoming[0] if upcoming else None

    data["current_course"] = current_course
    data["next_course"] = next_course
    data["today_events"] = today_events
    return data


def _format_timetable_response(
    events: List[Dict[str, Any]], 
    configured: bool = True, 
    connection_error: Optional[str] = None
) -> Dict[str, Any]:
    today_str = datetime.date.today().isoformat()
    now = datetime.datetime.now()

    today_events = [e for e in events if e.get("date") == today_str]
    current_course = next((e for e in events if e.get("is_current")), None)
    
    # Prochain cours à venir
    upcoming = [e for e in events if datetime.datetime.fromisoformat(e["dt_start"]) > now]
    next_course = upcoming[0] if upcoming else None

    return {
        "configured": configured,
        "connection_error": connection_error,
        "current_course": current_course,
        "next_course": next_course,
        "today_events": today_events,
        "all_events": events
    }
