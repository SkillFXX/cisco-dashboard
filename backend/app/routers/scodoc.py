from typing import Optional
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
        force_refresh=force_refresh
    )
    absences = data.get("absences", {})
    return {
        "configured": data.get("configured", False),
        "connection_error": data.get("connection_error"),
        "formation": data.get("formation"),
        "annee_universitaire": data.get("annee_universitaire"),
        "etudiant": data.get("etudiant"),
        "stats": data.get("stats"),
        "absences_summary": {
            "total_nb": absences.get("total_nb", 0),
            "total_heures": absences.get("total_heures", 0.0),
            "injustifiees_nb": absences.get("injustifiees_nb", 0),
            "injustifiees_heures": absences.get("injustifiees_heures", 0.0)
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
        force_refresh=force_refresh
    )
    return {
        "configured": data.get("configured", False),
        "connection_error": data.get("connection_error"),
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
        force_refresh=force_refresh
    )
    return data.get("absences", {})


@router.get("/evaluation/{evaluation_id}/distribution")
def get_evaluation_distribution(
    evaluation_id: int,
    min_promo: Optional[float] = Query(None, ge=0, le=20),
    moy_promo: Optional[float] = Query(None, ge=0, le=20),
    max_promo: Optional[float] = Query(None, ge=0, le=20),
    total_promo: Optional[int] = Query(None, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    from ..services.scodoc_service import fetch_evaluation_distribution
    return fetch_evaluation_distribution(
        user_id=current_user.id,
        url=creds.scodoc_url if creds else None,
        username=creds.scodoc_username if creds else None,
        password=creds.scodoc_password if creds else None,
        evaluation_id=evaluation_id,
        min_promo=min_promo,
        moy_promo=moy_promo,
        max_promo=max_promo,
        total_promo=total_promo
    )

