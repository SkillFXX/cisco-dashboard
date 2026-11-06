import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import datetime
from ..database import get_db
from ..models import User, PersonalTask, CompletedExternalTask
from ..auth import get_current_user
from ..services.scodoc_service import fetch_scodoc_data, get_empty_scodoc_data
from ..services.moodle_service import fetch_moodle_data
from ..services.ical_service import fetch_timetable

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

def _service_state(configured: bool, data: dict) -> dict:
    if not configured:
        return {"state": "unconfigured", "message": "Non configuré"}
    error = data.get("connection_error")
    if error:
        return {"state": "error", "message": error}
    return {"state": "ok", "message": None}


@router.get("/services-status")
def get_services_status(current_user: User = Depends(get_current_user)):
    """Etat reel de chaque service (identifiants renseignes + derniere reponse, servie depuis le cache)."""
    import concurrent.futures
    c = current_user.credentials
    scodoc_cfg = bool(c and c.scodoc_username and c.scodoc_password)
    moodle_cfg = bool(c and c.moodle_url and (c.moodle_token or (c.moodle_username and c.moodle_password)))
    ical_cfg = bool(c and c.ical_url and c.ical_url.strip())

    def run(configured, fn, **kwargs):
        if not configured:
            return {}
        try:
            return fn(**kwargs)
        except Exception as e:
            return {"connection_error": str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_sc = ex.submit(run, scodoc_cfg, fetch_scodoc_data, user_id=current_user.id, url=c.scodoc_url if c else None,
                         username=c.scodoc_username if c else None, password=c.scodoc_password if c else None)
        f_mo = ex.submit(run, moodle_cfg, fetch_moodle_data, url=c.moodle_url if c else None,
                         username=c.moodle_username if c else None, password=c.moodle_password if c else None,
                         token=c.moodle_token if c else None)
        f_ic = ex.submit(run, ical_cfg, fetch_timetable, ical_url=c.ical_url if c else None)
        return {
            "scodoc": _service_state(scodoc_cfg, f_sc.result()),
            "moodle": _service_state(moodle_cfg, f_mo.result()),
            "ical": _service_state(ical_cfg, f_ic.result()),
        }


@router.get("/overview")
def get_dashboard_overview(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials

    # Exécution concurrente des 3 services externes pour un chargement 3x plus rapide
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        fut_scodoc = executor.submit(
            fetch_scodoc_data,
            user_id=current_user.id,
            url=creds.scodoc_url if creds else None,
            username=creds.scodoc_username if creds else None,
            password=creds.scodoc_password if creds else None,
            force_refresh=force_refresh
        )
        fut_moodle = executor.submit(
            fetch_moodle_data,
            url=creds.moodle_url if creds else None,
            username=creds.moodle_username if creds else None,
            password=creds.moodle_password if creds else None,
            token=creds.moodle_token if creds else None,
            force_refresh=force_refresh
        )
        fut_timetable = executor.submit(
            fetch_timetable,
            ical_url=creds.ical_url if creds else None,
            force_refresh=force_refresh
        )

        try:
            scodoc_data = fut_scodoc.result()
        except Exception as e:
            logger.warning(f"ScoDoc error in dashboard overview: {e}")
            scodoc_data = get_empty_scodoc_data(str(e))

        try:
            moodle_data = fut_moodle.result()
        except Exception as e:
            logger.warning(f"Moodle error in dashboard overview: {e}")
            moodle_data = {
                "configured": bool(creds and creds.moodle_url),
                "site_name": "Moodle",
                "courses": [],
                "upcoming_assignments": [],
                "connection_error": str(e)
            }

        try:
            timetable_data = fut_timetable.result()
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

    # 4. Personal Tasks / DS & External completed items
    now = datetime.datetime.now()
    today_date = now.date()

    completed_ext_ids = set(
        r.item_id for r in db.query(CompletedExternalTask).filter(CompletedExternalTask.user_id == current_user.id).all()
    )

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
                "source": "personal",
                "title": t.title,
                "subject": t.subject or "Personnel",
                "due_date": t.due_date.isoformat(),
                "days_left": days_left,
                "type": t.event_type, # "ds", "dm", "todo", "tp"
                "description": t.description
            })

    # Inject Moodle assignments (strictement aujourd'hui et à venir, non cochés)
    for m in moodle_data.get("upcoming_assignments", []):
        m_id = f"moodle-{m['id']}"
        if m_id in completed_ext_ids:
            continue
        days_left = m.get("days_left", -1)
        if days_left >= 0:
            unified_assignments.append({
                "id": m_id,
                "is_personal": False,
                "source": "moodle",
                "title": m["name"],
                "subject": m["course_name"],
                "due_date": m["duedate"],
                "days_left": days_left,
                "type": "dm",
                "description": m["description"],
                "url": m.get("url")
            })

    # Inject Timetable DS events (contrôles ADE aujourd'hui et à venir, non cochés)
    for ev in timetable_data.get("all_events", []):
        if ev.get("type") == "DS":
            tt_id = f"timetable-{ev.get('id', ev['dt_start'])}"
            if tt_id in completed_ext_ids:
                continue
            try:
                dt_start = datetime.datetime.fromisoformat(ev["dt_start"])
                if dt_start.date() >= today_date:
                    days_left = (dt_start.date() - today_date).days
                    raw_loc = (ev.get("location") or "").strip()
                    room = f"Salle {raw_loc}" if raw_loc and not raw_loc.lower().startswith("salle") else (raw_loc or "Salle non précisée")
                    course_title = ev.get("title", "Contrôle DS").strip()
                    unified_assignments.append({
                        "id": tt_id,
                        "is_personal": False,
                        "source": "timetable",
                        "title": course_title,
                        "subject": "DS",
                        "due_date": ev.get("dt_start"),
                        "days_left": days_left,
                        "type": "ds",
                        "description": room,
                        "location": room
                    })
            except Exception:
                pass

    # Tri par date / urgence
    unified_assignments.sort(key=lambda x: (x.get("days_left", 99), x.get("due_date", "")))

    student_name = current_user.full_name or ""
    if not student_name:
        if scodoc_data.get("etudiant"):
            student_name = f"{scodoc_data['etudiant'].get('prenom', '')} {scodoc_data['etudiant'].get('nom', '')}".strip()
        elif moodle_data.get("fullname"):
            student_name = moodle_data.get("fullname", "").strip()

        if student_name:
            current_user.full_name = student_name
            db.commit()

    scodoc_connected = bool(scodoc_data.get("configured", False) and not scodoc_data.get("connection_error"))
    moodle_connected = bool(moodle_data.get("configured", False) and not moodle_data.get("connection_error"))
    ical_connected = bool(timetable_data.get("configured", False) and not timetable_data.get("connection_error"))

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": student_name or current_user.email.split("@")[0],
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
            "injustifiees_demi_journees": scodoc_data.get("absences", {}).get("injustifiees_demi_journees", 0),
            "justifiees_demi_journees": scodoc_data.get("absences", {}).get("justifiees_demi_journees", 0),
            "total_demi_journees": scodoc_data.get("absences", {}).get("total_demi_journees", 0),
            "injustifiees_nb": scodoc_data.get("absences", {}).get("injustifiees_nb", 0),
            "injustifiees_heures": scodoc_data.get("absences", {}).get("injustifiees_heures", 0.0),
            "justifiees_nb": scodoc_data.get("absences", {}).get("justifiees_nb", 0),
            "justifiees_heures": scodoc_data.get("absences", {}).get("justifiees_heures", 0.0),
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
