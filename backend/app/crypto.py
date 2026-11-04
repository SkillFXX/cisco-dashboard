import base64
import hashlib
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.types import String, TypeDecorator
from .config import settings

logger = logging.getLogger(__name__)

PREFIX = "enc:"
_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256((settings.ENCRYPTION_KEY or settings.SECRET_KEY).encode("utf-8")).digest()))


class EncryptedString(TypeDecorator):
    """Chiffre la valeur en base. Les valeurs historiques en clair restent lisibles et sont rechiffrees a la prochaine ecriture."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None or value == "" or value.startswith(PREFIX):
            return value
        return PREFIX + _fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        if value is None or not value.startswith(PREFIX):
            return value
        try:
            return _fernet.decrypt(value[len(PREFIX):].encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.error("Impossible de dechiffrer un identifiant stocke (cle de chiffrement modifiee ?).")
            return None


def encrypt_value(value: str) -> str:
    return PREFIX + _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return value
    if not value.startswith(PREFIX):
        return value
    try:
        return _fernet.decrypt(value[len(PREFIX):].encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
