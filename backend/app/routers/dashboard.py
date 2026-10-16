import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import datetime
from ..database import get_db
from ..models import User, PersonalTask
from ..auth import get_current_user
from ..services.scodoc_service import fetch_scodoc_data, get_empty_scodoc_data
from ..services.moodle_service import fetch_moodle_data
from ..services.ical_service import fetch_timetable

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/overview")
def get_dashboard_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials

    # 1. ScoDoc
    try:
        scodoc_data = fetch_scodoc_data(
            user_id=current_user.id,
            url=creds.scodoc_url if creds else None,
            username=creds.scodoc_username if creds else None,
            password=creds.scodoc_password if creds else None,
            force_refresh=False
        )
    except Exception as e:
        logger.warning(f"ScoDoc error in dashboard overview: {e}")
        scodoc_data = get_empty_scodoc_data(str(e))

    # 2. Moodle
    try:
        moodle_data = fetch_moodle_data(
            url=creds.moodle_url if creds else None,
            username=creds.moodle_username if creds else None,
            password=creds.moodle_password if creds else None,
            token=creds.moodle_token if creds else None
        )
    except Exception as e:
        logger.warning(f"Moodle error in dashboard overview: {e}")
        moodle_data = {
            "configured": bool(creds and creds.moodle_url),
            "site_name": "Moodle",
            "courses": [],
            "upcoming_assignments": [],
            "connection_error": str(e)
        }

    # 3. Timetable
    try:
        timetable_data = fetch_timetable(
            ical_url=creds.ical_url if creds else None
        )
    except Exception as e:
        logger.warning(f"Timetable error in dashboard overview: {e}")
        timetable_data = {
            "configured": bool(creds and creds.ical_url),
            "connection_error": str(e),
            "current_course": None,
            "next_course": None,
            "today_events": [],
            "all_events": []
        }

    # 4. Personal Tasks / DS from SQLite
    now = datetime.datetime.now()
    today_date = now.date()

    personal_tasks = db.query(PersonalTask).filter(
        PersonalTask.user_id == current_user.id,
        PersonalTask.status == "todo"
    ).order_by(PersonalTask.due_date.asc()).all()

    unified_assignments = []

    # Inject personal tasks (strictement aujourd'hui et à venir)
    for t in personal_tasks:
        if t.due_date.date() >= today_date:
            days_left = (t.due_date.date() - today_date).days
            unified_assignments.append({
                "id": f"personal-{t.id}",
                "task_id": t.id,
                "is_personal": True,
                "title": t.title,
                "subject": t.subject or "Personnel",
                "due_date": t.due_date.isoformat(),
                "days_left": days_left,
                "type": t.event_type, # "ds", "dm", "todo", "tp"
                "description": t.description
            })

    # Inject Moodle assignments (strictement aujourd'hui et à venir)
    for m in moodle_data.get("upcoming_assignments", []):
        days_left = m.get("days_left", -1)
        if days_left >= 0:
            unified_assignments.append({
                "id": f"moodle-{m['id']}",
                "is_personal": False,
                "title": m["name"],
                "subject": m["course_name"],
                "due_date": m["duedate"],
                "days_left": days_left,
                "type": "dm",
                "description": m["description"]
            })

    # Tri par date / urgence
    unified_assignments.sort(key=lambda x: (x.get("days_left", 99), x.get("due_date", "")))

    student_name = ""
    if current_user.full_name:
        student_name = current_user.full_name
    elif scodoc_data.get("etudiant"):
        student_name = f"{scodoc_data['etudiant'].get('prenom', '')} {scodoc_data['etudiant'].get('nom', '')}".strip()

    scodoc_connected = bool(scodoc_data.get("configured", False) and not scodoc_data.get("connection_error"))
    moodle_connected = bool(moodle_data.get("configured", False) and not moodle_data.get("connection_error"))
    ical_connected = bool(timetable_data.get("configured", False) and not timetable_data.get("connection_error"))

    return {
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "full_name": student_name or current_user.username,
            "photo_base64": scodoc_data.get("etudiant", {}).get("photo_base64") if scodoc_data.get("etudiant") else None
        },
        "stats": {
            "moyenne_generale": scodoc_data.get("stats", {}).get("moyenne_generale"),
            "rang": scodoc_data.get("stats", {}).get("rang"),
            "total_promo": scodoc_data.get("stats", {}).get("total_promo"),
            "min_promo": scodoc_data.get("stats", {}).get("min_promo"),
            "max_promo": scodoc_data.get("stats", {}).get("max_promo"),
            "moy_promo": scodoc_data.get("stats", {}).get("moy_promo"),
        },
        "absences": {
            "injustifiees_nb": scodoc_data.get("absences", {}).get("injustifiees_nb", 0),
            "injustifiees_heures": scodoc_data.get("absences", {}).get("injustifiees_heures", 0.0),
            "total_nb": scodoc_data.get("absences", {}).get("total_nb", 0),
            "total_heures": scodoc_data.get("absences", {}).get("total_heures", 0.0),
            "retards_nb": scodoc_data.get("absences", {}).get("retards_nb", 0)
        },
        "current_course": timetable_data.get("current_course"),
        "next_course": timetable_data.get("next_course"),
        "today_schedule": timetable_data.get("today_events", []),
        "timetable_events": timetable_data.get("all_events", []),
        "recent_grades": scodoc_data.get("recent_grades", [])[:6],
        "upcoming_tasks": unified_assignments[:8],
        "services_status": {
            "scodoc": scodoc_connected,
            "moodle": moodle_connected,
            "ical": ical_connected,
            "using_simulation": False
        }
    }
