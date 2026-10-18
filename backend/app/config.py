import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "cisco_student.db").as_posix()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cisco - Panel Étudiant BUT R&T"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cisco-student-super-secret-key-but-rt-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

    class Config:
        env_file = ".env"

settings = Settings()

