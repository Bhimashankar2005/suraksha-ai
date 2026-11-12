from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class ScamScanRequest(BaseModel):
    content: str = Field(..., min_length=5, max_length=5000, description="SMS, WhatsApp, Email, or suspicious text to analyze")

class IndicatorDetail(BaseModel):
    rule_id: str
    category: str
    description: str
    weight: int
    matched_terms: List[str]

class ScamScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_snippet: str
    risk_score: int
    risk_level: str
    scam_category: str
    ml_probability: float
    matched_indicators: List[IndicatorDetail]
    highlighted_tokens: List[str]
    explanation: str
    recommendations: List[str]
    created_at: datetime

class ScamHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_snippet: str
    risk_score: int
    risk_level: str
    scam_category: str
    created_at: datetime

class ScamFeedbackRequest(BaseModel):
    scan_id: str
    rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    feedback_text: Optional[str] = None

class ConvertToReportRequest(BaseModel):
    scan_id: str
    target_value: str = Field(..., min_length=3, max_length=500, description="Suspect phone number, SMS sender, or URL")
    description: Optional[str] = None
    region: Optional[str] = None

class ConvertToReportResponse(BaseModel):
    report_id: str
    report_code: str
    status: str
    message: str

