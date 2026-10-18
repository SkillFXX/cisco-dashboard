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
        cursor.execute("PRAGMA cache_size=-64000") # 64MB cache
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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
