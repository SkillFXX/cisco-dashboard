import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base
from .crypto import EncryptedString

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    credentials = relationship("UserCredentials", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("PersonalTask", back_populates="user", cascade="all, delete-orphan")


class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # ScoDoc settings
    scodoc_url = Column(String(255), nullable=True)
    scodoc_username = Column(String(100), nullable=True)
    scodoc_password = Column(EncryptedString(512), nullable=True)

    # Moodle settings
    moodle_url = Column(String(255), nullable=True)
    moodle_username = Column(String(100), nullable=True)
    moodle_password = Column(EncryptedString(512), nullable=True)
    moodle_token = Column(EncryptedString(512), nullable=True)

    # Lien iCal (.ics) de l'emploi du temps
    ical_url = Column(Text, nullable=True)

    # Fallback simulation
    use_mock_fallback = Column(Boolean, default=False)

    # Verification status
    scodoc_verified = Column(Boolean, default=False)
    scodoc_last_error = Column(Text, nullable=True)

    moodle_verified = Column(Boolean, default=False)
    moodle_last_error = Column(Text, nullable=True)

    ical_verified = Column(Boolean, default=False)
    ical_last_error = Column(Text, nullable=True)

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="credentials")


class PersonalTask(Base):
    __tablename__ = "personal_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True) # e.g. "R101 Initiation aux réseaux"
    due_date = Column(DateTime, nullable=False)
    event_type = Column(String(50), default="ds") # "ds", "dm", "todo", "tp", "exam"
    status = Column(String(20), default="todo") # "todo", "done"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="tasks")


class KVCache(Base):
    __tablename__ = "kv_cache"

    key = Column(String(100), primary_key=True, index=True)
    value = Column(Text, nullable=False) # JSON encoded data
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    ttl_seconds = Column(Integer, default=900) # 15 minutes par defaut


class CompletedExternalTask(Base):
    __tablename__ = "completed_external_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(String(150), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)



class AppSetting(Base):
    """Parametres globaux de l'application (ex. serveur SMTP), valeur JSON."""
    __tablename__ = "app_settings"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class NotificationChannels(Base):
    """Canaux de notification d'un utilisateur (l'email utilise l'adresse du compte)."""
    __tablename__ = "notification_channels"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    webhook_url = Column(EncryptedString(512), nullable=True)  # Discord ou webhook compatible


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    trigger = Column(String(30), nullable=False)  # "new_grade", "deadline", "daily_digest", "new_week"
    params = Column(Text, nullable=False, default="{}")  # JSON
    channels = Column(Text, nullable=False, default="[]")  # JSON : ["email", "webhook"]
    baseline_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = (UniqueConstraint("rule_id", "dedupe_key", name="uq_notification_rule_key"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rule_id = Column(Integer, nullable=False, index=True)
    dedupe_key = Column(String(200), nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)


class AiSettings(Base):
    """Cle d'API Gemini d'un utilisateur (chiffree) et etat de la derniere verification."""
    __tablename__ = "ai_settings"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    api_key = Column(EncryptedString(512), nullable=True)
    model = Column(String(80), nullable=False, default="gemini-2.5-flash-lite")
    verified = Column(Boolean, default=False)
    last_error = Column(String(300), nullable=True)


class GradeSnapshot(Base):
    """Un point par jour de la moyenne generale et du rang, pour les courbes d'evolution."""
    __tablename__ = "grade_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_snapshot_user_day"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    day = Column(String(10), nullable=False)  # YYYY-MM-DD
    moyenne = Column(Float, nullable=True)
    rang = Column(Integer, nullable=True)
    total_promo = Column(Integer, nullable=True)
