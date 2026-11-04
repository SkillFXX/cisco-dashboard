import logging
import threading

from sqlalchemy.orm import joinedload

from ..database import SessionLocal
from ..models import User
from .cache_service import get_cached_data, moodle_cache_key, ical_cache_key
from .ical_service import fetch_timetable
from .moodle_service import fetch_moodle_data
from .scodoc_service import fetch_scodoc_data

logger = logging.getLogger(__name__)

CYCLE_SECONDS = 300
# Les caches vivent 15 min : on les renouvelle avant leur expiration pour que l'ouverture de l'app soit instantanee.
REFRESH_AFTER_SECONDS = 600


def _is_fresh(key: str) -> bool:
    return get_cached_data(key, max_age_seconds=REFRESH_AFTER_SECONDS) is not None


def prefetch_user(user: User) -> None:
    """Renouvelle les caches ScoDoc / Moodle / emploi du temps d'un utilisateur s'ils vieillissent.

    Le releve ScoDoc alimente aussi la courbe d'evolution (moyenne / rang).
    """
    creds = user.credentials
    if not creds:
        return

    jobs = []
    if creds.scodoc_username and creds.scodoc_password and not _is_fresh(f"scodoc:{user.id}"):
        jobs.append(("ScoDoc", lambda: fetch_scodoc_data(
            user_id=user.id, url=creds.scodoc_url, username=creds.scodoc_username,
            password=creds.scodoc_password, force_refresh=True,
        )))
    if creds.moodle_url and (creds.moodle_token or (creds.moodle_username and creds.moodle_password)):
        key = moodle_cache_key(creds.moodle_url, creds.moodle_username, creds.moodle_token)
        if not _is_fresh(key):
            jobs.append(("Moodle", lambda: fetch_moodle_data(
                url=creds.moodle_url, username=creds.moodle_username, password=creds.moodle_password,
                token=creds.moodle_token, force_refresh=True,
            )))
    if creds.ical_url and creds.ical_url.strip() and not _is_fresh(ical_cache_key(creds.ical_url)):
        jobs.append(("emploi du temps", lambda: fetch_timetable(ical_url=creds.ical_url, force_refresh=True)))

    for label, job in jobs:
        try:
            job()
        except Exception as e:
            logger.warning(f"Prechargement {label} ignore pour l'utilisateur {user.id}: {e}")


def run_prefetch_cycle() -> None:
    db = SessionLocal()
    try:
        users = db.query(User).options(joinedload(User.credentials)).all()
        for user in users:
            if _stop.is_set():
                return
            prefetch_user(user)
    except Exception as e:
        logger.warning(f"Cycle de prechargement en echec : {e}")
    finally:
        db.close()


_stop = threading.Event()


def _loop() -> None:
    _stop.wait(60)  # laisse l'application demarrer
    while not _stop.is_set():
        run_prefetch_cycle()
        _stop.wait(CYCLE_SECONDS)


def start_prefetch() -> threading.Thread:
    thread = threading.Thread(target=_loop, name="data-prefetch", daemon=True)
    thread.start()
    return thread


def stop_prefetch() -> None:
    _stop.set()
