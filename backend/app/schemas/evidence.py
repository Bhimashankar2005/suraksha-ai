from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class EvidenceFileItem(BaseModel):
    id: str
    file_code: str
    original_name: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    incident_category: str
    incident_date: datetime
    description: Optional[str] = None
    created_at: datetime

class IncidentReportCreate(BaseModel):
    incident_title: str = Field(..., min_length=3, max_length=200, description="Title of the cyber incident")
    category: str = Field(..., description="Category: UPI_FRAUD, EXTORTION_BLACKMAIL, BANK_IMPERSONATION, IDENTITY_THEFT, OTHER")
    total_financial_loss: float = Field(default=0.0, ge=0, description="Documented financial loss in INR")
    timeline_summary: str = Field(..., min_length=10, max_length=5000, description="Chronological timeline of events")
    evidence_file_ids: List[str] = Field(default_factory=list, description="IDs of evidence files to attach")

class IncidentReportResponse(BaseModel):
    id: str
    incident_title: str
    category: str
    total_financial_loss: float
    timeline_summary: str
    evidence_files: List[EvidenceFileItem]
    official_portal_guidance: str
    disclaimer: str
    created_at: datetime

class EvidenceVaultStats(BaseModel):
    total_files: int
    total_size_bytes: int
    total_incident_reports: int
    total_documented_loss_inr: float

