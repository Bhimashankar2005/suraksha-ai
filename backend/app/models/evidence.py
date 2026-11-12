import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    file_code = Column(String(30), unique=True, nullable=False, index=True)  # EVD-XXXXXX
    original_name = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    incident_category = Column(String(50), nullable=False)
    incident_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="evidence_files")
    report = relationship("Report", back_populates="evidence_files")

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    incident_title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)
    total_financial_loss = Column(Numeric(12, 2), default=0.00)
    timeline_summary = Column(Text, nullable=False)
    evidence_file_ids = Column(JSON, nullable=False, default=list)
    official_portal_guidance = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", foreign_keys=[user_id])

