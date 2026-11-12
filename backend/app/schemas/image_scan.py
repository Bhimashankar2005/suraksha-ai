from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

class ImageIndicatorDetail(BaseModel):
    rule_id: str
    category: str
    description: str
    weight: int
    matched_terms: List[str]

class ImageScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_hash: str
    file_name: str
    file_size_bytes: int
    dimensions: List[int]
    mime_type: str
    extracted_text: str
    risk_score: int
    risk_level: str
    scam_category: str
    detected_entities: Dict[str, Any]
    matched_indicators: List[ImageIndicatorDetail]
    highlighted_tokens: List[str]
    explanation: str
    recommendations: List[str]
    ocr_engine: str
    created_at: datetime

class ImageHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    file_hash: str
    risk_score: int
    risk_level: str
    scam_category: str
    created_at: datetime

class ConvertImageToReportRequest(BaseModel):
    scan_id: str
    target_value: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None

