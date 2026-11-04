import re
import hashlib
import secrets
import datetime
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..models import User, UserCredentials, PasswordResetToken
from ..schemas import ForgotPasswordRequest, ResetPasswordRequest, UserRegister, UserLogin, TokenResponse, UserResponse, UserProfileUpdate
from ..services.url_guard import validate_service_url
from ..ratelimit import login_limiter, register_limiter, FailureLimiter
from ..auth import get_password_hash, verify_password, create_access_token, get_current_user, is_admin_user, is_admin_email

router = APIRouter(prefix="/api/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8
reset_limiter = FailureLimiter(max_failures=20, window_seconds=15 * 60)
DUMMY_HASH = get_password_hash("dummy-password-for-timing")

def _cached_photo(user_id: int):
    try:
        from ..services.cache_service import get_cached_data
        cached_scodoc = get_cached_data(f"scodoc:{user_id}")
        if cached_scodoc and cached_scodoc.get("etudiant"):
            return cached_scodoc["etudiant"].get("photo_base64")
    except Exception:
        pass
    return None


def build_user_response(user: User) -> dict:
    creds = user.credentials
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "photo_base64": _cached_photo(user.id),
        "has_scodoc": bool(creds and creds.scodoc_username and creds.scodoc_password),
        "has_moodle": bool(creds and (creds.moodle_token or (creds.moodle_username and creds.moodle_password))),
        "has_ical": bool(creds and creds.ical_url),
        "is_admin": is_admin_user(user),
        "use_mock_fallback": creds.use_mock_fallback if creds else False
    }


@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    register_limiter.check("register")
    register_limiter.record("register")

    if len(payload.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le mot de passe doit comporter au moins {MIN_PASSWORD_LENGTH} caractères."
        )

    for url in (payload.scodoc_url, payload.moodle_url, payload.ical_url):
        if url:
            url_err = validate_service_url(url.strip())
            if url_err:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=url_err)

    if is_admin_email(email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cette adresse email existe déjà."
        )

    # Verifier si l'email existe deja
    existing_email = db.query(User).filter(User.email == email_clean).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cette adresse email existe déjà."
        )

    # Creer l'utilisateur
    new_user = User(
        username=email_clean,
        email=email_clean,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip() if payload.full_name else None
    )
    db.add(new_user)
    db.flush()

    # Creer les identifiants de services par defaut
    creds = UserCredentials(
        user_id=new_user.id,
        scodoc_url=payload.scodoc_url or "https://wscodoc.iutbeziers.fr",
        scodoc_username=payload.scodoc_username,
        scodoc_password=payload.scodoc_password,
        moodle_url=payload.moodle_url or "https://moodle-but.iutbeziers.fr/moodle",
        moodle_username=payload.moodle_username,
        moodle_password=payload.moodle_password,
        moodle_token=payload.moodle_token,
        ical_url=payload.ical_url,
        use_mock_fallback=False
    )
    db.add(creds)
    db.commit()

    token = create_access_token(data={"sub": str(new_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": build_user_response(new_user)
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    identifier = (payload.email or payload.username or "").strip().lower()
    login_limiter.check(identifier)
    user = db.query(User).filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    # Hash factice si l'utilisateur n'existe pas : evite de distinguer les comptes par le temps de reponse
    password_ok = verify_password(payload.password, user.hashed_password if user else DUMMY_HASH)
    if not user or not password_ok:
        login_limiter.record(identifier)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect."
        )

    login_limiter.reset(identifier)
    token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": build_user_response(user)
    }

@router.put("/profile", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Nom complet / prenom
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None

    # 2. Adresse email
    if payload.email is not None and str(payload.email).strip():
        new_email = str(payload.email).strip().lower()
        if new_email != current_user.email:
            if is_admin_user(current_user) or is_admin_email(new_email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="L'adresse email de l'administrateur est définie par la configuration du serveur."
                )
            existing = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cette adresse email est déjà associée à un autre compte."
                )
            current_user.email = new_email
            current_user.username = new_email

    # 3. Modification de mot de passe
    if payload.new_password and payload.new_password.strip():
        if not payload.current_password or not verify_password(payload.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le mot de passe actuel est incorrect."
            )
        if len(payload.new_password.strip()) < MIN_PASSWORD_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le nouveau mot de passe doit comporter au moins {MIN_PASSWORD_LENGTH} caractères."
            )
        current_user.hashed_password = get_password_hash(payload.new_password.strip())

    db.commit()
    db.refresh(current_user)

    return build_user_response(current_user)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_user_response(current_user)



logger = logging.getLogger(__name__)
RESET_TOKEN_TTL_MINUTES = 60
forgot_limiter = FailureLimiter(max_failures=5, window_seconds=60 * 60)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@router.get("/capabilities")
def get_capabilities():
    """Indique les fonctions optionnelles disponibles (ex. mot de passe oublie si un SMTP est configure)."""
    from ..mailer import load_smtp, is_configured, public_url
    db = SessionLocal()
    try:
        cfg = load_smtp(db)
        return {"password_reset": is_configured(cfg) and bool(public_url(cfg))}
    finally:
        db.close()


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    from ..mailer import load_smtp, is_configured, public_url, send_mail
    email = str(payload.email).strip().lower()
    forgot_limiter.check(email)
    forgot_limiter.record(email)

    cfg = load_smtp(db)
    base_url = public_url(cfg)
    if not is_configured(cfg) or not base_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La réinitialisation par email n'est pas disponible. Contactez l'administrateur."
        )

    # Reponse identique que le compte existe ou non (pas d'enumeration)
    generic = {"message": "Si un compte existe pour cette adresse, un email de réinitialisation vient d'être envoyé."}
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return generic

    token = secrets.token_urlsafe(32)
    db.query(PasswordResetToken).filter(PasswordResetToken.user_id == user.id, PasswordResetToken.used == False).delete()  # noqa: E712
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_token(token),
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=RESET_TOKEN_TTL_MINUTES),
    ))
    db.commit()

    link = f"{base_url}/?reset={token}"
    try:
        send_mail(
            user.email,
            "Réinitialisation de votre mot de passe - Cisco Dashboard",
            f"Bonjour,\n\nPour choisir un nouveau mot de passe, ouvrez ce lien (valable {RESET_TOKEN_TTL_MINUTES} minutes) :\n{link}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.",
            cfg,
        )
    except Exception as e:
        logger.warning(f"Envoi de l'email de réinitialisation impossible : {e}")
    return generic


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_limiter.check("reset")
    row = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == _hash_token(payload.token)).first()
    if not row or row.used or row.expires_at < datetime.datetime.utcnow():
        reset_limiter.record("reset")
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré. Refaites une demande.")

    user = db.get(User, row.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré. Refaites une demande.")
    user.hashed_password = get_password_hash(payload.new_password)
    row.used = True
    db.commit()
    login_limiter.reset(user.email)
    return {"message": "Mot de passe mis à jour. Vous pouvez vous connecter."}
