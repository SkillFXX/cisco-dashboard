from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserCredentials
from ..schemas import (
    CredentialsUpdate,
    CredentialsResponse,
    ServiceVerifyRequest,
    ServiceVerifyResponse
)
from ..auth import get_current_user
from ..services.verify_service import verify_scodoc, verify_moodle, verify_ical

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
        "scodoc_verified": bool(creds.scodoc_verified),
        "scodoc_last_error": creds.scodoc_last_error,
        "moodle_url": creds.moodle_url,
        "moodle_username": creds.moodle_username,
        "moodle_configured": bool(creds.moodle_token or (creds.moodle_username and creds.moodle_password)),
        "moodle_verified": bool(creds.moodle_verified),
        "moodle_last_error": creds.moodle_last_error,
        "ical_url": creds.ical_url,
        "ical_configured": bool(creds.ical_url),
        "ical_verified": bool(creds.ical_verified),
        "ical_last_error": creds.ical_last_error,
        "use_mock_fallback": creds.use_mock_fallback
    }

@router.put("/services", response_model=CredentialsResponse)
def update_service_settings(payload: CredentialsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    if not creds:
        creds = UserCredentials(user_id=current_user.id)
        db.add(creds)

    scodoc_changed = False
    if payload.scodoc_url is not None:
        creds.scodoc_url = payload.scodoc_url
        scodoc_changed = True
    if payload.scodoc_username is not None:
        creds.scodoc_username = payload.scodoc_username
        scodoc_changed = True
    if payload.scodoc_password is not None and payload.scodoc_password != "":
        creds.scodoc_password = payload.scodoc_password
        scodoc_changed = True

    moodle_changed = False
    if payload.moodle_url is not None:
        creds.moodle_url = payload.moodle_url
        moodle_changed = True
    if payload.moodle_username is not None:
        creds.moodle_username = payload.moodle_username
        moodle_changed = True
    if payload.moodle_password is not None and payload.moodle_password != "":
        creds.moodle_password = payload.moodle_password
        moodle_changed = True
    if payload.moodle_token is not None:
        creds.moodle_token = payload.moodle_token
        moodle_changed = True

    ical_changed = False
    if payload.ical_url is not None:
        creds.ical_url = payload.ical_url
        ical_changed = True

    if payload.use_mock_fallback is not None:
        creds.use_mock_fallback = payload.use_mock_fallback

    # Vérification automatique de ScoDoc si renseigné/modifié
    if scodoc_changed and creds.scodoc_username and creds.scodoc_password:
        sco_check = verify_scodoc(creds.scodoc_url, creds.scodoc_username, creds.scodoc_password)
        if sco_check["success"]:
            creds.scodoc_verified = True
            creds.scodoc_last_error = None
            if sco_check.get("student_name") and not current_user.full_name:
                current_user.full_name = sco_check["student_name"]
        else:
            creds.scodoc_verified = False
            creds.scodoc_last_error = sco_check["message"]

    # Vérification automatique de Moodle si renseigné/modifié
    if moodle_changed and (creds.moodle_token or (creds.moodle_username and creds.moodle_password)):
        mdl_check = verify_moodle(creds.moodle_url, creds.moodle_username, creds.moodle_password, creds.moodle_token)
        if mdl_check["success"]:
            creds.moodle_verified = True
            creds.moodle_last_error = None
            if mdl_check.get("token") and not creds.moodle_token:
                creds.moodle_token = mdl_check.get("token")
            if mdl_check.get("student_name") and not current_user.full_name:
                current_user.full_name = mdl_check["student_name"]
        else:
            creds.moodle_verified = False
            creds.moodle_last_error = mdl_check["message"]

    # Vérification automatique d'iCal si renseigné/modifié
    if ical_changed and creds.ical_url:
        ical_check = verify_ical(creds.ical_url)
        if ical_check["success"]:
            creds.ical_verified = True
            creds.ical_last_error = None
    # Invalidation du cache si modification des identifiants
    from ..services.cache_service import invalidate_cache
    if scodoc_changed:
        invalidate_cache(f"scodoc:{current_user.id}")
    if moodle_changed:
        invalidate_cache("moodle:")
    if ical_changed:
        invalidate_cache("ical:")

    db.commit()
    db.refresh(creds)

    return {
        "scodoc_url": creds.scodoc_url,
        "scodoc_username": creds.scodoc_username,
        "scodoc_configured": bool(creds.scodoc_username and creds.scodoc_password),
        "scodoc_verified": bool(creds.scodoc_verified),
        "scodoc_last_error": creds.scodoc_last_error,
        "moodle_url": creds.moodle_url,
        "moodle_username": creds.moodle_username,
        "moodle_configured": bool(creds.moodle_token or (creds.moodle_username and creds.moodle_password)),
        "moodle_verified": bool(creds.moodle_verified),
        "moodle_last_error": creds.moodle_last_error,
        "ical_url": creds.ical_url,
        "ical_configured": bool(creds.ical_url),
        "ical_verified": bool(creds.ical_verified),
        "ical_last_error": creds.ical_last_error,
        "use_mock_fallback": creds.use_mock_fallback
    }

@router.post("/verify", response_model=ServiceVerifyResponse)
def verify_service_endpoint(
    payload: ServiceVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    if not creds:
        creds = UserCredentials(user_id=current_user.id)
        db.add(creds)
        db.commit()
        db.refresh(creds)

    service = payload.service.lower()

    if service == "scodoc":
        url = payload.url or creds.scodoc_url or "https://wscodoc.iutbeziers.fr"
        user = payload.username or creds.scodoc_username
        pwd = payload.password or creds.scodoc_password

        result = verify_scodoc(url=url, username=user, password=pwd)

        if payload.save_if_valid or creds.scodoc_username:
            if result["success"]:
                creds.scodoc_url = url
                if payload.username:
                    creds.scodoc_username = payload.username
                if payload.password:
                    creds.scodoc_password = payload.password
                creds.scodoc_verified = True
                creds.scodoc_last_error = None
                if result.get("student_name") and not current_user.full_name:
                    current_user.full_name = result["student_name"]
            else:
                creds.scodoc_verified = False
                creds.scodoc_last_error = result["message"]
            db.commit()

        return {
            "success": result["success"],
            "service": "scodoc",
            "message": result["message"],
            "student_name": result.get("student_name"),
            "student_pic": result.get("student_pic"),
            "details": result.get("details")
        }

    elif service == "moodle":
        url = payload.url or creds.moodle_url or "https://moodle-but.iutbeziers.fr/moodle"
        user = payload.username or creds.moodle_username
        pwd = payload.password or creds.moodle_password
        tok = payload.token or creds.moodle_token

        result = verify_moodle(url=url, username=user, password=pwd, token=tok)

        if payload.save_if_valid or creds.moodle_username or creds.moodle_token:
            if result["success"]:
                creds.moodle_url = url
                if payload.username:
                    creds.moodle_username = payload.username
                if payload.password:
                    creds.moodle_password = payload.password
                if payload.token:
                    creds.moodle_token = payload.token
                elif result.get("token"):
                    creds.moodle_token = result.get("token")
                creds.moodle_verified = True
                creds.moodle_last_error = None
                if result.get("student_name") and not current_user.full_name:
                    current_user.full_name = result["student_name"]
            else:
                creds.moodle_verified = False
                creds.moodle_last_error = result["message"]
            db.commit()

        return {
            "success": result["success"],
            "service": "moodle",
            "message": result["message"],
            "student_name": result.get("student_name"),
            "token": result.get("token"),
            "details": result.get("details")
        }

    elif service in ["ical", "ade"]:
        url = payload.url or creds.ical_url
        result = verify_ical(url=url)

        if payload.save_if_valid or creds.ical_url:
            if result["success"]:
                creds.ical_url = url
                creds.ical_verified = True
                creds.ical_last_error = None
            else:
                creds.ical_verified = False
                creds.ical_last_error = result["message"]
            db.commit()

        return {
            "success": result["success"],
            "service": "ical",
            "message": result["message"],
            "details": {"event_count": result.get("event_count", 0)}
        }

    else:
        raise HTTPException(status_code=400, detail=f"Service inconnu : {payload.service}")


