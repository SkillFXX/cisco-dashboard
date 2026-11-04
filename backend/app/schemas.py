from typing import Optional, List, Dict, Any
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field

# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)
    full_name: Optional[str] = None
    # Optional credentials during signup
    scodoc_url: Optional[str] = None
    scodoc_username: Optional[str] = None
    scodoc_password: Optional[str] = None
    moodle_url: Optional[str] = None
    moodle_username: Optional[str] = None
    moodle_password: Optional[str] = None
    moodle_token: Optional[str] = None
    ical_url: Optional[str] = None

class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    current_password: Optional[str] = Field(default=None, max_length=128)
    new_password: Optional[str] = Field(default=None, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    photo_base64: Optional[str] = None
    has_scodoc: bool
    has_moodle: bool
    has_ical: bool
    is_admin: bool = False
    use_mock_fallback: bool = False

# Credentials Schemas
class CredentialsUpdate(BaseModel):
    scodoc_url: Optional[str] = None
    scodoc_username: Optional[str] = None
    scodoc_password: Optional[str] = None
    moodle_url: Optional[str] = None
    moodle_username: Optional[str] = None
    moodle_password: Optional[str] = None
    moodle_token: Optional[str] = None
    ical_url: Optional[str] = None
    use_mock_fallback: Optional[bool] = None

class CredentialsResponse(BaseModel):
    scodoc_url: Optional[str] = None
    scodoc_username: Optional[str] = None
    scodoc_configured: bool = False
    scodoc_verified: bool = False
    scodoc_last_error: Optional[str] = None
    moodle_url: Optional[str] = None
    moodle_username: Optional[str] = None
    moodle_configured: bool = False
    moodle_verified: bool = False
    moodle_last_error: Optional[str] = None
    ical_url: Optional[str] = None
    ical_configured: bool = False
    ical_verified: bool = False
    ical_last_error: Optional[str] = None
    use_mock_fallback: bool = False

# Service Verification Schemas
class ServiceVerifyRequest(BaseModel):
    service: str # "scodoc", "moodle", "ical"
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    save_if_valid: Optional[bool] = False

class ServiceVerifyResponse(BaseModel):
    success: bool
    service: str
    message: str
    student_name: Optional[str] = None
    student_pic: Optional[str] = None
    token: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Tasks / DS Schemas
EventType = Literal["ds", "dm", "tp", "todo", "exam"]
TaskStatus = Literal["todo", "done"]

class PersonalTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    subject: Optional[str] = Field(default=None, max_length=100)
    due_date: datetime
    event_type: EventType = "ds"
    status: TaskStatus = "todo"

class PersonalTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    subject: Optional[str] = Field(default=None, max_length=100)
    due_date: Optional[datetime] = None
    event_type: Optional[EventType] = None
    status: Optional[TaskStatus] = None

class PersonalTaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    subject: Optional[str]
    due_date: datetime
    event_type: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ItemStatusToggle(BaseModel):
    item_id: str = Field(min_length=1, max_length=150)
    status: str # "todo" or "done"


# Admin Schemas
class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None

class AdminPasswordSet(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)

class SmtpSettingsUpdate(BaseModel):
    host: str = Field(default="", max_length=255)
    port: int = Field(default=587, ge=1, le=65535)
    security: Literal["starttls", "ssl", "none"] = "starttls"
    username: str = Field(default="", max_length=255)
    # None = conserver le mot de passe existant
    password: Optional[str] = Field(default=None, max_length=512)
    from_email: str = Field(default="", max_length=255)
    from_name: str = Field(default="Cisco Dashboard", max_length=100)
    public_url: str = Field(default="", max_length=255)

class SmtpTestRequest(BaseModel):
    to: Optional[EmailStr] = None

# Password reset
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)
