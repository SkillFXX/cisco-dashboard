from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.ical_service import fetch_timetable

router = APIRouter(prefix="/api/timetable", tags=["timetable"])

@router.get("/week")
def get_week_timetable(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    return fetch_timetable(
        ical_url=creds.ical_url if creds else None,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )

@router.get("/today")
def get_today_timetable(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    data = fetch_timetable(
        ical_url=creds.ical_url if creds else None,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )
    return {
        "is_mock": data.get("is_mock", False),
        "today_events": data.get("today_events", []),
        "current_course": data.get("current_course"),
        "next_course": data.get("next_course")
    }

