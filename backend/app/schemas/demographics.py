from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Literal
from datetime import datetime

class HarassmentAnalysisRequest(BaseModel):
    content: str = Field(..., min_length=2, max_length=5000, description="Abusive message, threat text, or blackmail excerpt")
    context: Optional[str] = Field(default=None, max_length=1000, description="Platform context e.g. Instagram DM, WhatsApp, Telegram")

class HelplineRef(BaseModel):
    name: str
    number: str
    portal: Optional[str] = None
    description: str

class HarassmentAnalysisResponse(BaseModel):
    threat_severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL_EMERGENCY"]
    detected_patterns: List[str]
    risk_score: int
    immediate_actions: List[str]
    emergency_helplines: List[HelplineRef]
    evidence_checklist: List[str]
    official_filing_link: str

class SeniorSafetyRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Suspicious SMS, call pitch, or message received by senior citizen")
    language: Literal["en", "kn", "hi"] = Field(default="en", description="Preferred language for plain explanation")

class SeniorSafetyResponse(BaseModel):
    verdict: Literal["DANGEROUS SCAM", "SUSPICIOUS", "LIKELY LEGITIMATE"]
    plain_explanation: str
    voice_script: str
    scam_category: str
    what_to_do_now: List[str]
    emergency_helpline: str
    language: str

class TrustedContactCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    relationship_type: str = Field(..., description="parent, child, spouse, sibling, friend")
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    has_explicit_consent: bool = Field(default=False)
    notify_on_critical_scam: bool = Field(default=False)

    @field_validator("phone_number")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Phone number cannot be empty.")
        return cleaned

class TrustedContactItem(BaseModel):
    id: str
    name: str
    relationship_type: str
    phone_number: str
    email: Optional[str] = None
    has_explicit_consent: bool
    notify_on_critical_scam: bool
    created_at: datetime

class TrustedContactAlertRequest(BaseModel):
    contact_id: str
    incident_type: str
    incident_details: Optional[str] = None

class TrustedContactAlertResponse(BaseModel):
    contact_name: str
    phone_number: str
    draft_sms_text: str
    whatsapp_share_url: str

