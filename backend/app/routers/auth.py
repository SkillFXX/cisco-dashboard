from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserCredentials
from ..schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from ..auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    # Check if username or email exists
    existing_user = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet identifiant ou cet email existe déjà."
        )

    # Create user
    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name or payload.username
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create credentials entry
    creds = UserCredentials(
        user_id=new_user.id,
        scodoc_url=payload.scodoc_url or "https://wscodoc.iutbeziers.fr",
        scodoc_username=payload.scodoc_username,
        scodoc_password=payload.scodoc_password,
        moodle_url=payload.moodle_url or "https://moodle.umontpellier.fr",
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
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "full_name": new_user.full_name
        }
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect."
        )

    token = create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    creds = current_user.credentials
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "has_scodoc": bool(creds and creds.scodoc_username and creds.scodoc_password),
        "has_moodle": bool(creds and (creds.moodle_token or (creds.moodle_username and creds.moodle_password))),
        "has_ical": bool(creds and creds.ical_url),
        "use_mock_fallback": creds.use_mock_fallback if creds else False
    }

