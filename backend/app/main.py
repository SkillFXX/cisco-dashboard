import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base, init_db
from .models import User, UserCredentials, PersonalTask
from .routers import auth, settings as settings_router, scodoc, moodle, timetable, tasks, dashboard

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize tables and schema updates
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API pour le tableau de bord étudiant Cisco BUT Réseaux & Télécoms",
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

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "description": "Agrégateur ScoDoc, Moodle & ADE Campus pour étudiants BUT Réseaux et Télécoms"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

