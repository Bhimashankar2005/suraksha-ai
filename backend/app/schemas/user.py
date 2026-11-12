import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    phone_number: Optional[str] = None
    preferred_language: str = "en"
    senior_mode: bool = False
    avatar_url: Optional[str] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    profile: Optional[ProfileResponse] = None

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferred_language: Optional[str] = None
    senior_mode: Optional[bool] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
