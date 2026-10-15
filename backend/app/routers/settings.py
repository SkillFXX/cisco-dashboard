from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserCredentials
from ..schemas import CredentialsUpdate, CredentialsResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

@router.get("/services", response_model=CredentialsResponse)
def get_service_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    if not creds:
        creds = UserCredentials(user_id=current_user.id)
        db.add(creds)
        db.commit()
        db.refresh(creds)

    return {
        "scodoc_url": creds.scodoc_url,
        "scodoc_username": creds.scodoc_username,
        "scodoc_configured": bool(creds.scodoc_username and creds.scodoc_password),
        "moodle_url": creds.moodle_url,
        "moodle_username": creds.moodle_username,
        "moodle_configured": bool(creds.moodle_token or (creds.moodle_username and creds.moodle_password)),
        "ical_url": creds.ical_url,
        "ical_configured": bool(creds.ical_url),
        "use_mock_fallback": creds.use_mock_fallback
    }

@router.put("/services", response_model=CredentialsResponse)
def update_service_settings(payload: CredentialsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    if not creds:
        creds = UserCredentials(user_id=current_user.id)
        db.add(creds)

    if payload.scodoc_url is not None:
        creds.scodoc_url = payload.scodoc_url
    if payload.scodoc_username is not None:
        creds.scodoc_username = payload.scodoc_username
    if payload.scodoc_password is not None and payload.scodoc_password != "":
        creds.scodoc_password = payload.scodoc_password

    if payload.moodle_url is not None:
        creds.moodle_url = payload.moodle_url
    if payload.moodle_username is not None:
        creds.moodle_username = payload.moodle_username
    if payload.moodle_password is not None and payload.moodle_password != "":
        creds.moodle_password = payload.moodle_password
    if payload.moodle_token is not None:
        creds.moodle_token = payload.moodle_token

    if payload.ical_url is not None:
        creds.ical_url = payload.ical_url
    if payload.use_mock_fallback is not None:
        creds.use_mock_fallback = payload.use_mock_fallback

    db.commit()
    db.refresh(creds)

    return {
        "scodoc_url": creds.scodoc_url,
        "scodoc_username": creds.scodoc_username,
        "scodoc_configured": bool(creds.scodoc_username and creds.scodoc_password),
        "moodle_url": creds.moodle_url,
        "moodle_username": creds.moodle_username,
        "moodle_configured": bool(creds.moodle_token or (creds.moodle_username and creds.moodle_password)),
        "ical_url": creds.ical_url,
        "ical_configured": bool(creds.ical_url),
        "use_mock_fallback": creds.use_mock_fallback
    }

