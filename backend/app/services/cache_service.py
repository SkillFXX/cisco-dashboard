import json
import datetime
import logging
from typing import Any, Optional, Dict
from ..database import SessionLocal
from ..models import KVCache

logger = logging.getLogger(__name__)


def get_cached_data(key: str, allow_stale: bool = False, max_age_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Recupere des donnees depuis le cache SQLite persistant.
    Si allow_stale est False, retourne None si la duree de validite (TTL) est depassee.
    """
    db = SessionLocal()
    try:
        entry = db.query(KVCache).filter_by(key=key).first()
        if not entry:
            return None

        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ttl = max_age_seconds if max_age_seconds is not None else entry.ttl_seconds
        age = (now - entry.updated_at).total_seconds()

        if not allow_stale and age > ttl:
            return None

        parsed = json.loads(entry.value)
        return parsed
    except Exception as e:
        logger.warning(f"Erreur lecture kv_cache pour la cle '{key}': {e}")
        return None
    finally:
        db.close()


def set_cached_data(key: str, data: Any, ttl_seconds: int = 900) -> None:
    """Enregistre ou met a jour des donnees dans le cache SQLite persistant."""
    db = SessionLocal()
    try:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        serialized = json.dumps(data, default=str)

        entry = db.query(KVCache).filter_by(key=key).first()
        if entry:
            entry.value = serialized
            entry.updated_at = now
            entry.ttl_seconds = ttl_seconds
        else:
            entry = KVCache(
                key=key,
                value=serialized,
                updated_at=now,
                ttl_seconds=ttl_seconds
            )
            db.add(entry)

        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Erreur ecriture kv_cache pour la cle '{key}': {e}")
    finally:
        db.close()


def invalidate_cache(key_prefix: str) -> None:
    """Invalide les entrees de cache commencant par key_prefix."""
    db = SessionLocal()
    try:
        db.query(KVCache).filter(KVCache.key.like(f"{key_prefix}%")).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning(f"Erreur invalidation kv_cache pour prefixe '{key_prefix}': {e}")
    finally:
        db.close()

