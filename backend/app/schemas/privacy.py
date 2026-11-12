from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone

class PrivacyScanRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Raw text or document content to inspect for privacy leaks")

class DetectedEntityItem(BaseModel):
    type: str
    raw_preview: str
    start: int
    end: int
    confidence: float
    is_checksum_valid: Optional[bool] = None

class PrivacyScanResponse(BaseModel):
    scan_id: Optional[str] = None
    detected_entities: List[DetectedEntityItem]
    detected_counts: Dict[str, int]
    risk_score: int
    risk_level: str
    sanitized_text: str
    recommendations: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PrivacyHistoryItem(BaseModel):
    id: str
    redacted_preview: str
    detected_types: Dict[str, int]
    risk_score: int
    created_at: datetime

