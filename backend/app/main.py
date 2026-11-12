import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base, init_db
from .models import User, UserCredentials, PersonalTask
from .services.notifier import start_scheduler, stop_scheduler
from .services.prefetch import start_prefetch, stop_prefetch
from .routers import auth, settings as settings_router, scodoc, moodle, timetable, tasks, dashboard, admin, notifications, ai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tables and schema updates
init_db()


def ensure_admin_account():
    """Cree/synchronise le compte administrateur defini par ADMIN_EMAIL (et ADMIN_PASSWORD)."""
    import secrets
    from .database import SessionLocal
    from .auth import get_password_hash, verify_password

    admin_email = (settings.ADMIN_EMAIL or "").strip().lower()
    if not admin_email:
        return
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == admin_email).first()
        if user is None:
            password = settings.ADMIN_PASSWORD or secrets.token_urlsafe(16)
            db.add(User(
                username=admin_email,
                email=admin_email,
                hashed_password=get_password_hash(password),
                full_name="Administrateur",
            ))
            db.commit()
            if not settings.ADMIN_PASSWORD:
                logger.warning(f"Compte admin {admin_email} créé avec le mot de passe temporaire : {password}")
        elif settings.ADMIN_PASSWORD and not verify_password(settings.ADMIN_PASSWORD, user.hashed_password):
            user.hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            db.commit()
    finally:
        db.close()


ensure_admin_account()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_scheduler()
    start_prefetch()
    yield
    stop_scheduler()
    stop_prefetch()


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description="API du tableau de bord étudiant Cisco Dashboard (BUT)",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.ENABLE_DOCS else None
)

# CORS Middleware to allow SvelteKit frontend securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(settings_router.router)
app.include_router(dashboard.router)
app.include_router(scodoc.router)
app.include_router(moodle.router)
app.include_router(timetable.router)
app.include_router(tasks.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(ai.router)

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "description": "Agrégateur ScoDoc, Moodle & emploi du temps pour étudiants en BUT"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

