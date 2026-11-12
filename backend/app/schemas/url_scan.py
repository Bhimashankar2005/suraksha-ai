from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

class UrlScanRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=2048, description="Web address or URL to verify")

class UrlIndicatorDetail(BaseModel):
    rule: str
    description: str
    weight: int

class UrlScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    domain: str
    risk_score: int
    risk_level: str
    is_ip_host: bool
    has_ssl: bool
    is_shortened: bool
    lookalike_target: Optional[str] = None
    matched_indicators: List[UrlIndicatorDetail]
    analysis_details: Dict[str, Any]
    explanation: str
    recommendations: List[str]
    created_at: datetime

class UrlHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    domain: str
    risk_score: int
    risk_level: str
    created_at: datetime

class ConvertUrlToReportRequest(BaseModel):
    scan_id: str
    target_value: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None

