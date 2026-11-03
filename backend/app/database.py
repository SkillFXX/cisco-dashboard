from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

# Activer SQLite WAL mode et les optimisations de lecture/ecriture concurrentes
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA cache_size=-2000") # 2MB cache par connexion
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from sqlalchemy import text
    Base.metadata.create_all(bind=engine)

    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(user_credentials);")).fetchall()
                col_names = [r[1] for r in res]
                cols_to_add = [
                    ("scodoc_verified", "BOOLEAN DEFAULT 0"),
                    ("scodoc_last_error", "TEXT"),
                    ("moodle_verified", "BOOLEAN DEFAULT 0"),
                    ("moodle_last_error", "TEXT"),
                    ("ical_verified", "BOOLEAN DEFAULT 0"),
                    ("ical_last_error", "TEXT"),
                ]
                for col_name, col_def in cols_to_add:
                    if col_name not in col_names:
                        conn.execute(text(f"ALTER TABLE user_credentials ADD COLUMN {col_name} {col_def};"))
                conn.commit()
            except Exception as e:
                print(f"Warning during DB column migration: {e}")

        with engine.connect() as conn:
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_personal_tasks_user_id ON personal_tasks (user_id)"))
            conn.commit()

        _encrypt_legacy_credentials()

        # Purge périodique du cache obsolète au démarrage
        try:
            from .services.cache_service import cleanup_expired_cache
            cleanup_expired_cache()
        except Exception:
            pass

def _encrypt_legacy_credentials():
    """Rechiffre les mots de passe/jetons de services encore stockes en clair."""
    from sqlalchemy import text
    from sqlalchemy.orm.attributes import flag_modified
    from .models import UserCredentials
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT id FROM user_credentials WHERE "
                "(scodoc_password IS NOT NULL AND scodoc_password != '' AND scodoc_password NOT LIKE 'enc:%') OR "
                "(moodle_password IS NOT NULL AND moodle_password != '' AND moodle_password NOT LIKE 'enc:%') OR "
                "(moodle_token IS NOT NULL AND moodle_token != '' AND moodle_token NOT LIKE 'enc:%')"
            )).fetchall()
        if not rows:
            return
        db = SessionLocal()
        try:
            for (cred_id,) in rows:
                creds = db.get(UserCredentials, cred_id)
                for field in ("scodoc_password", "moodle_password", "moodle_token"):
                    flag_modified(creds, field)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"Warning during credentials encryption migration: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
