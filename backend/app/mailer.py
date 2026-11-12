import json
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from .config import settings
from .crypto import encrypt_value, decrypt_value
from .database import SessionLocal
from .models import AppSetting

logger = logging.getLogger(__name__)

SMTP_KEY = "smtp"
DEFAULT_SMTP: Dict[str, Any] = {
    "host": "",
    "port": 587,
    "security": "starttls",  # "starttls", "ssl" ou "none"
    "username": "",
    "password": "",
    "from_email": "",
    "from_name": "Cisco Dashboard",
    "public_url": "",
}


def load_smtp(db: Session) -> Dict[str, Any]:
    row = db.get(AppSetting, SMTP_KEY)
    data = dict(DEFAULT_SMTP)
    if row:
        try:
            stored = json.loads(row.value)
            data.update({k: stored.get(k, v) for k, v in DEFAULT_SMTP.items()})
            data["password"] = decrypt_value(stored.get("password")) or ""
        except (ValueError, TypeError):
            pass
    return data


def save_smtp(db: Session, data: Dict[str, Any]) -> None:
    to_store = dict(data)
    to_store["password"] = encrypt_value(data["password"]) if data.get("password") else ""
    row = db.get(AppSetting, SMTP_KEY)
    if row:
        row.value = json.dumps(to_store)
    else:
        db.add(AppSetting(key=SMTP_KEY, value=json.dumps(to_store)))
    db.commit()


def is_configured(cfg: Dict[str, Any]) -> bool:
    return bool(cfg.get("host") and cfg.get("port") and cfg.get("from_email"))


def mail_available() -> bool:
    db = SessionLocal()
    try:
        return is_configured(load_smtp(db))
    finally:
        db.close()


def public_url(cfg: Optional[Dict[str, Any]] = None) -> str:
    """URL publique du site : variable d'environnement, sinon valeur saisie par l'admin."""
    url = settings.PUBLIC_URL or (cfg or {}).get("public_url") or ""
    return url.strip().rstrip("/")


def send_mail(to: str, subject: str, body: str, cfg: Optional[Dict[str, Any]] = None, attachment: Optional[Tuple[str, bytes, str]] = None) -> None:
    """Envoie un email via le serveur SMTP configure. Leve une exception en cas d'echec."""
    if cfg is None:
        db = SessionLocal()
        try:
            cfg = load_smtp(db)
        finally:
            db.close()
    if not is_configured(cfg):
        raise RuntimeError("Serveur SMTP non configuré.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg.get("from_name") or "", cfg["from_email"]))
    msg["To"] = to
    msg.set_content(body)
    if attachment:
        filename, data, mime = attachment
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    host, port, security = cfg["host"], int(cfg["port"]), cfg.get("security", "starttls")
    context = ssl.create_default_context()
    if security == "ssl":
        server = smtplib.SMTP_SSL(host, port, timeout=15, context=context)
    else:
        server = smtplib.SMTP(host, port, timeout=15)
    try:
        server.ehlo()
        if security == "starttls":
            server.starttls(context=context)
            server.ehlo()
        if cfg.get("username"):
            server.login(cfg["username"], cfg.get("password", ""))
        server.send_message(msg)
    finally:
        try:
            server.quit()
        except Exception:
            pass
