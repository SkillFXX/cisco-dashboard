import logging
import datetime
from typing import Dict, Any, Optional, List
import requests
import icalendar
import recurring_ical_events

logger = logging.getLogger(__name__)

def generate_rt_week_schedule() -> List[Dict[str, Any]]:
    """Génère un emploi du temps BUT R&T dynamique pour la semaine actuelle."""
    today = datetime.date.today()
    # Trouver le lundi de cette semaine
    start_of_week = today - datetime.timedelta(days=today.weekday())

    schedule_template = [
        # Lundi
        (0, "08:00", "10:00", "R101 - Initiation aux Réseaux Informatiques", "CM", "Amphi Dumontet", "M. DELMAS", "Groupe Promo Entière"),
        (0, "10:15", "12:15", "R107 - Administration Système sous Linux", "TD", "Salle B102", "Mme MARTINEZ", "Groupe TD 1A"),
        (0, "13:45", "17:00", "R101 - TP Cisco : Câblage, Routeurs & Commutateurs", "TP", "Labo Cisco C04", "M. DELMAS", "Groupe TP 1A1"),

        # Mardi
        (1, "08:30", "10:00", "R102 - Principes des Télécommunications", "CM", "Amphi Dumontet", "M. LEROUX", "Groupe Promo Entière"),
        (1, "10:15", "12:15", "R103 - Bases de l'Électronique Numérique", "TD", "Salle B105", "M. FABRE", "Groupe TD 1A"),
        (1, "13:45", "17:00", "SAÉ 1.1 - Déploiement Réseau PME & Packet Tracer", "TP", "Salle Projets Info 2", "M. DELMAS & Mme MARTINEZ", "Groupe Projet"),

        # Mercredi
        (2, "08:00", "10:00", "R108 - Algorithmique et Sockets TCP en Python", "TP", "Salle Info 3", "M. ROUSTAN", "Groupe TP 1A1"),
        (2, "10:15", "12:15", "Anglais Technique Réseaux & Vocabulaire Cisco", "TD", "Salle A201", "Mme SMITH", "Groupe TD 1A"),
        (2, "14:00", "16:00", "Activités Sportives Universitaires (SUAPS)", "AUTRE", "Gymnase Universitaire", "Enseignants EPS", "Tous"),

        # Jeudi
        (3, "08:30", "11:45", "R102 - TP Télécoms : Bilan de liaison et Fibre Optique", "TP", "Labo Télécom T01", "M. LEROUX", "Groupe TP 1A1"),
        (3, "13:30", "15:30", "Mathématiques pour le Traitement du Signal", "TD", "Salle B204", "M. DUVAL", "Groupe TD 1A"),
        (3, "15:45", "17:45", "Communication Professionnelle & Gestion de projet", "TD", "Salle A103", "Mme BERTRAND", "Groupe TD 1A"),

        # Vendredi
        (4, "08:30", "10:30", "R107 - TP Scripting Shell & Automatisation Bash", "TP", "Salle Info 1", "Mme MARTINEZ", "Groupe TP 1A1"),
        (4, "10:45", "12:45", "SAÉ 1.1 - Soutenance intermédiaire de maquettage", "TP", "Amphi Dumontet", "Équipe Pédagogique R&T", "Promo"),
        (4, "14:00", "16:00", "DS Noté : Architecture des Réseaux Locaux (R101)", "DS", "Amphi Dumontet", "M. DELMAS", "Promo Entière")
    ]

    now = datetime.datetime.now()
    events = []

    for day_offset, start_str, end_str, title, event_type, location, teacher, group in schedule_template:
        day_date = start_of_week + datetime.timedelta(days=day_offset)
        
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))

        dt_start = datetime.datetime.combine(day_date, datetime.time(sh, sm))
        dt_end = datetime.datetime.combine(day_date, datetime.time(eh, em))

        is_current = (dt_start <= now <= dt_end)
        is_passed = (now > dt_end)

        events.append({
            "id": f"evt-{day_offset}-{start_str.replace(':', '')}",
            "title": title,
            "type": event_type, # "CM", "TD", "TP", "DS", "AUTRE"
            "date": day_date.isoformat(),
            "day_name": ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"][day_offset],
            "start_time": start_str,
            "end_time": end_str,
            "dt_start": dt_start.isoformat(),
            "dt_end": dt_end.isoformat(),
            "duration_minutes": int((dt_end - dt_start).total_seconds() / 60),
            "location": location,
            "teacher": teacher,
            "group": group,
            "is_current": is_current,
            "is_passed": is_passed
        })

    events.sort(key=lambda x: x["dt_start"])
    return events


def parse_ical_stream(ical_content: str) -> List[Dict[str, Any]]:
    """Parse un flux iCal (.ics) ADE Campus / UM Net."""
    cal = icalendar.Calendar.from_ical(ical_content)
    now = datetime.datetime.now()
    today = datetime.date.today()
    start_search = today - datetime.timedelta(days=7)
    end_search = today + datetime.timedelta(days=21)

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

        # Convert timezone to naive local if needed
        if dt_start.tzinfo is not None:
            dt_start = dt_start.replace(tzinfo=None)
        if dt_end.tzinfo is not None:
            dt_end = dt_end.replace(tzinfo=None)

        # Déterminer le type (CM, TD, TP, DS)
        upper_sum = summary.upper()
        if "DS" in upper_sum or "EXAMEN" in upper_sum or "EVALUATION" in upper_sum or "PARTIEL" in upper_sum:
            evt_type = "DS"
        elif " TP" in upper_sum or upper_sum.startswith("TP") or "/TP" in upper_sum:
            evt_type = "TP"
        elif " TD" in upper_sum or upper_sum.startswith("TD") or "/TD" in upper_sum:
            evt_type = "TD"
        elif " CM" in upper_sum or upper_sum.startswith("CM") or "AMPHI" in location.upper():
            evt_type = "CM"
        else:
            evt_type = "COURS"

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
            "teacher": description.split("\n")[0] if description else "",
            "group": description.split("\n")[1] if len(description.split("\n")) > 1 else "",
            "is_current": is_current,
            "is_passed": is_passed
        })

    parsed.sort(key=lambda x: x["dt_start"])
    return parsed


_ICAL_CACHE: Dict[str, Dict[str, Any]] = {}
ICAL_CACHE_TTL = 900  # 15 minutes

def fetch_timetable(ical_url: Optional[str] = None, use_mock_fallback: bool = True) -> Dict[str, Any]:
    """Récupère l'emploi du temps depuis l'URL iCal ou le simulateur BUT R&T avec cache."""
    if not ical_url or ical_url.strip() == "":
        if use_mock_fallback:
            events = generate_rt_week_schedule()
            return _format_timetable_response(events, is_mock=True)
        return _format_timetable_response([], is_mock=False)

    import time
    now_ts = time.time()
    cached = _ICAL_CACHE.get(ical_url)
    if cached and (now_ts - cached.get("timestamp", 0) < ICAL_CACHE_TTL):
        return cached["data"]

    try:
        resp = requests.get(ical_url, timeout=25)
        resp.raise_for_status()
        events = parse_ical_stream(resp.text)
        res = _format_timetable_response(events, is_mock=False)
        _ICAL_CACHE[ical_url] = {"timestamp": now_ts, "data": res}
        return res
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération iCal: {e}")
        if use_mock_fallback:
            events = generate_rt_week_schedule()
            res = _format_timetable_response(events, is_mock=True)
            res["connection_error"] = str(e)
            return res
        return _format_timetable_response([], is_mock=False)


def _format_timetable_response(events: List[Dict[str, Any]], is_mock: bool) -> Dict[str, Any]:
    today_str = datetime.date.today().isoformat()
    now = datetime.datetime.now()

    today_events = [e for e in events if e["date"] == today_str]
    current_course = next((e for e in events if e["is_current"]), None)
    
    # Prochain cours à venir
    upcoming = [e for e in events if datetime.datetime.fromisoformat(e["dt_start"]) > now]
    next_course = upcoming[0] if upcoming else None

    return {
        "is_mock": is_mock,
        "current_course": current_course,
        "next_course": next_course,
        "today_events": today_events,
        "all_events": events
    }

