import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, PersonalTask, CompletedExternalTask
from ..schemas import AdminUserUpdate, AdminPasswordSet, SmtpSettingsUpdate, SmtpTestRequest
from ..auth import require_admin, get_password_hash, is_admin_user, is_admin_email
from ..mailer import load_smtp, save_smtp, is_configured, send_mail
from ..services.cache_service import invalidate_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _serialize_user(user: User, task_count: int = 0) -> dict:
    creds = user.credentials
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "is_admin": is_admin_user(user),
        "has_scodoc": bool(creds and creds.scodoc_username and creds.scodoc_password),
        "has_moodle": bool(creds and (creds.moodle_token or (creds.moodle_username and creds.moodle_password))),
        "has_ical": bool(creds and creds.ical_url),
        "task_count": task_count,
    }


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return user


@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    from sqlalchemy import func
    counts = dict(db.query(PersonalTask.user_id, func.count(PersonalTask.id)).group_by(PersonalTask.user_id).all())
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [_serialize_user(u, counts.get(u.id, 0)) for u in users]


@router.put("/users/{user_id}")
def update_user(user_id: int, payload: AdminUserUpdate, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or None
    if payload.email is not None:
        new_email = str(payload.email).strip().lower()
        if new_email != user.email:
            if is_admin_user(user) or is_admin_email(new_email):
                raise HTTPException(status_code=400, detail="L'email de l'administrateur est défini par la configuration du serveur.")
            if db.query(User).filter(User.email == new_email, User.id != user.id).first():
                raise HTTPException(status_code=400, detail="Cette adresse email est déjà utilisée.")
            user.email = new_email
            user.username = new_email
    db.commit()
    db.refresh(user)
    return _serialize_user(user)


@router.post("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
def set_user_password(user_id: int, payload: AdminPasswordSet, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return None


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, current_admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    if user.id == current_admin.id or is_admin_user(user):
        raise HTTPException(status_code=400, detail="Le compte administrateur ne peut pas être supprimé.")

    from ..models import NotificationRule, NotificationLog, NotificationChannels, GradeSnapshot, PasswordResetToken
    for model in (CompletedExternalTask, NotificationLog, NotificationRule, NotificationChannels, GradeSnapshot, PasswordResetToken):
        db.query(model).filter(model.user_id == user.id).delete(synchronize_session=False)
    uid = user.id
    db.delete(user)
    db.commit()
    invalidate_cache(f"scodoc:{uid}:", exact=f"scodoc:{uid}")
    return None


def _smtp_response(cfg: dict) -> dict:
    return {
        "host": cfg["host"],
        "port": cfg["port"],
        "security": cfg["security"],
        "username": cfg["username"],
        "has_password": bool(cfg["password"]),
        "from_email": cfg["from_email"],
        "from_name": cfg["from_name"],
        "public_url": cfg["public_url"],
        "configured": is_configured(cfg),
    }


@router.get("/smtp")
def get_smtp(db: Session = Depends(get_db)):
    return _smtp_response(load_smtp(db))


@router.put("/smtp")
def update_smtp(payload: SmtpSettingsUpdate, db: Session = Depends(get_db)):
    current = load_smtp(db)
    new_cfg = payload.model_dump()
    if payload.password is None:
        new_cfg["password"] = current["password"]
    save_smtp(db, new_cfg)
    return _smtp_response(load_smtp(db))


@router.post("/smtp/test")
def test_smtp(payload: SmtpTestRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    cfg = load_smtp(db)
    if not is_configured(cfg):
        raise HTTPException(status_code=400, detail="Renseignez d'abord le serveur SMTP, le port et l'adresse d'expédition.")
    target = str(payload.to) if payload.to else admin.email
    try:
        send_mail(target, "Test SMTP - Cisco Dashboard", "Ce message confirme que la configuration SMTP fonctionne.", cfg)
    except Exception as e:
        logger.warning(f"Echec du test SMTP: {e}")
        raise HTTPException(status_code=400, detail=f"Échec de l'envoi : {e}")
    return {"success": True, "message": f"Email de test envoyé à {target}."}
