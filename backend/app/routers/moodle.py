from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.moodle_service import fetch_moodle_data

router = APIRouter(prefix="/api/moodle", tags=["moodle"])

@router.get("/assignments")
def get_assignments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    data = fetch_moodle_data(
        url=creds.moodle_url if creds else None,
        username=creds.moodle_username if creds else None,
        password=creds.moodle_password if creds else None,
        token=creds.moodle_token if creds else None,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )
    return {
        "is_mock": data.get("is_mock", False),
        "site_name": data.get("site_name", "Moodle"),
        "assignments": data.get("upcoming_assignments", [])
    }

@router.get("/courses")
def get_courses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    data = fetch_moodle_data(
        url=creds.moodle_url if creds else None,
        username=creds.moodle_username if creds else None,
        password=creds.moodle_password if creds else None,
        token=creds.moodle_token if creds else None,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )
    return {
        "is_mock": data.get("is_mock", False),
        "site_name": data.get("site_name", "Moodle"),
        "courses": data.get("courses", [])
    }

