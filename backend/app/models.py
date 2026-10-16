import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

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
    scodoc_url = Column(String(255), nullable=True, default="https://wscodoc.iutbeziers.fr")
    scodoc_username = Column(String(100), nullable=True)
    scodoc_password = Column(String(255), nullable=True)

    # Moodle settings
    moodle_url = Column(String(255), nullable=True, default="https://moodle.umontpellier.fr")
    moodle_username = Column(String(100), nullable=True)
    moodle_password = Column(String(255), nullable=True)
    moodle_token = Column(String(255), nullable=True)

    # UM Net / ADE Campus iCal URL
    ical_url = Column(Text, nullable=True)

    # Fallback simulation
    use_mock_fallback = Column(Boolean, default=False)

    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="credentials")


class PersonalTask(Base):
    __tablename__ = "personal_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    subject = Column(String(100), nullable=True) # e.g. "R101 Réseaux", "R102 Télécoms"
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

