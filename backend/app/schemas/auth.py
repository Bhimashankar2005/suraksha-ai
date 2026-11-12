import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters with letters and numbers")
    full_name: str = Field(..., min_length=2, max_length=150)
    phone_number: Optional[str] = None
    preferred_language: str = Field(default="en", description="en, kn, or hi")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(EMAIL_REGEX, v.strip()):
            raise ValueError("Invalid email address format.")
        return v.lower().strip()

class UserLoginRequest(BaseModel):
    email: str = Field(..., description="Valid email address")
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(EMAIL_REGEX, v.strip()):
            raise ValueError("Invalid email address format.")
        return v.lower().strip()

class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    preferred_language: str
    senior_mode: bool = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary
