from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Auth Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
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
    current_password: Optional[str] = None
    new_password: Optional[str] = None

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
    use_mock_fallback: Optional[bool] = False

class CredentialsResponse(BaseModel):
    scodoc_url: Optional[str]
    scodoc_username: Optional[str]
    scodoc_configured: bool
    moodle_url: Optional[str]
    moodle_username: Optional[str]
    moodle_configured: bool
    ical_url: Optional[str]
    ical_configured: bool
    use_mock_fallback: bool = False

# Tasks / DS Schemas
class PersonalTaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject: Optional[str] = None
    due_date: datetime
    event_type: str = "ds"
    status: str = "todo"

class PersonalTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    due_date: Optional[datetime] = None
    event_type: Optional[str] = None
    status: Optional[str] = None

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
    item_id: str
    status: str # "todo" or "done"

