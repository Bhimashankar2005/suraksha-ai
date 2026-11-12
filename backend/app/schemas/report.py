from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Literal
from datetime import datetime

class ReportCreate(BaseModel):
    threat_type: Literal["MESSAGE", "PHONE", "URL", "SCREENSHOT", "HARASSMENT"] = Field(
        ..., description="Category of cyber threat: MESSAGE, PHONE, URL, SCREENSHOT, HARASSMENT"
    )
    target_value: str = Field(
        ..., min_length=2, max_length=500, description="The suspicious phone number, URL, SMS sender, UPI ID, or keyword"
    )
    description: str = Field(
        ..., min_length=5, max_length=2000, description="Description of the scam or malicious attempt"
    )
    region: Optional[str] = Field(
        default=None, max_length=100, description="Optional Indian state or city (e.g., Karnataka, Bengaluru)"
    )
    is_anonymous: bool = Field(
        default=False, description="Whether to mask user identity completely from public records"
    )

    @field_validator("target_value")
    @classmethod
    def clean_target_value(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Target value cannot be empty or blank")
        return cleaned

class ReviewHistoryItem(BaseModel):
    action_taken: str
    public_notes: Optional[str] = None
    created_at: datetime

class ReportTrackResponse(BaseModel):
    report_code: str
    threat_type: str
    target_value: str
    description: str
    region: Optional[str] = None
    status: str
    is_public_alert: bool
    is_duplicate: bool
    created_at: datetime
    updated_at: datetime
    reviews: List[ReviewHistoryItem] = []

class ReportListItem(BaseModel):
    id: str
    report_code: str
    threat_type: str
    target_value: str
    description: str
    region: Optional[str] = None
    status: str
    is_public_alert: bool
    is_duplicate: bool
    created_at: datetime

class ReportReviewAction(BaseModel):
    action: Literal["APPROVE_VERIFY", "REJECT", "MARK_DUPLICATE", "RESOLVE"] = Field(
        ..., description="Moderation action taken by authorized analyst"
    )
    internal_notes: str = Field(..., min_length=2, max_length=1000)
    public_notes: Optional[str] = Field(default=None, max_length=1000)
    publish_as_public_alert: bool = Field(default=False)
    threat_level: Optional[Literal["MEDIUM", "HIGH", "CRITICAL"]] = "HIGH"

class PublicThreatAlertItem(BaseModel):
    threat_id: str
    indicator_type: str
    indicator_value: str
    threat_level: str
    description: str
    incident_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ThreatIntelligenceStats(BaseModel):
    total_reports: int
    pending_reviews: int
    verified_threats: int
    resolved_reports: int
    by_category: Dict[str, int]
    by_region: Dict[str, int]
    active_threat_indicators: int

