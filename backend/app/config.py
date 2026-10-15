import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Cisco - Panel Étudiant BUT R&T"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "cisco-student-super-secret-key-but-rt-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cisco_student.db")

    class Config:
        env_file = ".env"

settings = Settings()

