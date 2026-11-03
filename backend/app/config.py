import os
import secrets
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "cisco_student.db").as_posix()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")


def _load_secret_key() -> str:
    """SECRET_KEY depuis l'environnement, sinon cle aleatoire generee et conservee a cote de la base."""
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key

    if DATABASE_URL.startswith("sqlite:///"):
        key_file = Path(DATABASE_URL.replace("sqlite:///", "", 1)).resolve().parent / ".secret_key"
        try:
            if key_file.exists():
                return key_file.read_text().strip()
            key = secrets.token_hex(32)
            key_file.write_text(key)
            key_file.chmod(0o600)
            return key
        except OSError:
            pass
    return secrets.token_hex(32)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Cisco - Panel Étudiant BUT R&T"
    SECRET_KEY: str = _load_secret_key()
    # Cle de chiffrement des mots de passe ScoDoc/Moodle stockes (par defaut derivee de SECRET_KEY)
    ENCRYPTION_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = DATABASE_URL
    ENABLE_DOCS: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
