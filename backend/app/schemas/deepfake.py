from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class DeepfakeScanResponse(BaseModel):
    id: Optional[str] = None
    file_name: str
    file_hash: str
    media_type: str
    file_size_kb: float
    authenticity_score: int
    verdict: str
    forensic_flags: Dict[str, Any]
    limitations_disclaimer: str
    created_at: Optional[datetime] = None

class DeepfakeHistoryItem(BaseModel):
    id: str
    file_name: Optional[str] = None
    media_type: str
    file_hash: str
    verdict: str
    authenticity_score: int
    created_at: datetime

class DeepfakeReportRequest(BaseModel):
    scan_id: str
    description: Optional[str] = Field(default=None, max_length=1000)

class DeepfakeReportResponse(BaseModel):
    report_code: str
    threat_type: str
    target_value: str
    status: str
    message: str

