import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_code = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    threat_type = Column(String(50), nullable=False)  # MESSAGE, PHONE, URL, SCREENSHOT, HARASSMENT
    target_value = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    region = Column(String(100), nullable=True)
    status = Column(String(30), default="PENDING", index=True)  # PENDING, UNDER_REVIEW, VERIFIED, REJECTED, DUPLICATE, RESOLVED
    is_public_alert = Column(Boolean, default=False)
    duplicate_of_id = Column(String(36), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="reports", foreign_keys=[user_id])
    reviews = relationship("ReportReview", back_populates="report", cascade="all, delete-orphan")
    evidence_files = relationship("EvidenceFile", back_populates="report")
    duplicates = relationship("Report", backref="original_report", remote_side=[id])

class ReportReview(Base):
    __tablename__ = "report_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_taken = Column(String(50), nullable=False)  # APPROVED_VERIFIED, REJECTED, MARKED_DUPLICATE, RESOLVED
    internal_notes = Column(Text, nullable=False)
    public_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    report = relationship("Report", back_populates="reviews")
    admin = relationship("User", foreign_keys=[admin_id])

class Threat(Base):
    __tablename__ = "threats"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    origin_report_id = Column(String(36), ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    indicator_type = Column(String(30), nullable=False)  # PHONE, URL, UPI_ID, SMS_SENDER
    indicator_value = Column(String(500), nullable=False, index=True)
    threat_level = Column(String(20), nullable=False)  # MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    verified_by_admin_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    incident_count = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    origin_report = relationship("Report", foreign_keys=[origin_report_id])
    verified_by_admin = relationship("User", foreign_keys=[verified_by_admin_id])

