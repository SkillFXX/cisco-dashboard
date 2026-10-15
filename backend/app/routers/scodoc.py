from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.scodoc_service import fetch_scodoc_data

router = APIRouter(prefix="/api/scodoc", tags=["scodoc"])

@router.get("/summary")
def get_summary(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_scodoc_data(
        user_id=current_user.id,
        url=creds.scodoc_url if creds else None,
        username=creds.scodoc_username if creds else None,
        password=creds.scodoc_password if creds else None,
        force_refresh=force_refresh,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )
    return {
        "is_mock": data.get("is_mock", False),
        "formation": data.get("formation"),
        "annee_universitaire": data.get("annee_universitaire"),
        "etudiant": data.get("etudiant"),
        "stats": data.get("stats"),
        "absences_summary": {
            "total_nb": data["absences"]["total_nb"],
            "total_heures": data["absences"]["total_heures"],
            "injustifiees_nb": data["absences"]["injustifiees_nb"],
            "injustifiees_heures": data["absences"]["injustifiees_heures"]
        },
        "recent_grades": data.get("recent_grades", [])[:5]
    }

@router.get("/grades")
def get_grades(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_scodoc_data(
        user_id=current_user.id,
        url=creds.scodoc_url if creds else None,
        username=creds.scodoc_username if creds else None,
        password=creds.scodoc_password if creds else None,
        force_refresh=force_refresh,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )
    return {
        "stats": data.get("stats"),
        "ues": data.get("ues", []),
        "matieres": data.get("matieres", []),
        "grades": data.get("recent_grades", [])
    }

@router.get("/absences")
def get_absences(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_scodoc_data(
        user_id=current_user.id,
        url=creds.scodoc_url if creds else None,
        username=creds.scodoc_username if creds else None,
        password=creds.scodoc_password if creds else None,
        force_refresh=force_refresh,
        use_mock_fallback=creds.use_mock_fallback if creds else True
    )
    return data.get("absences", {})

