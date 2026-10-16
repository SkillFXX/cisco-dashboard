from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.moodle_service import fetch_moodle_data

router = APIRouter(prefix="/api/moodle", tags=["moodle"])

@router.get("/assignments")
def get_assignments(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_moodle_data(
        url=creds.moodle_url if creds else None,
        username=creds.moodle_username if creds else None,
        password=creds.moodle_password if creds else None,
        token=creds.moodle_token if creds else None,
        force_refresh=force_refresh
    )
    return {
        "configured": data.get("configured", False),
        "connection_error": data.get("connection_error"),
        "site_name": data.get("site_name", "Moodle"),
        "assignments": data.get("upcoming_assignments", [])
    }

@router.get("/courses")
def get_courses(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_moodle_data(
        url=creds.moodle_url if creds else None,
        username=creds.moodle_username if creds else None,
        password=creds.moodle_password if creds else None,
        token=creds.moodle_token if creds else None,
        force_refresh=force_refresh
    )
    return {
        "configured": data.get("configured", False),
        "connection_error": data.get("connection_error"),
        "site_name": data.get("site_name", "Moodle"),
        "courses": data.get("courses", [])
    }
