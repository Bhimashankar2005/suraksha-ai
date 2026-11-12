import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class ScamScan(Base):
    __tablename__ = "scam_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content_snippet = Column(Text, nullable=False)
    risk_score = Column(Integer, nullable=False)  # 0 to 100
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    scam_category = Column(String(50), nullable=False)
    indicators = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="scam_scans")

class UrlScan(Base):
    __tablename__ = "url_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    url = Column(String(2048), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    is_ip_host = Column(Boolean, default=False)
    has_ssl = Column(Boolean, default=False)
    lookalike_target = Column(String(100), nullable=True)
    redirect_chain = Column(JSON, nullable=False, default=list)
    analysis_details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="url_scans")

class ImageScan(Base):
    __tablename__ = "image_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    file_name = Column(String(255), nullable=False)
    extracted_text = Column(Text, nullable=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)
    detected_entities = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="image_scans")

class PrivacyScan(Base):
    __tablename__ = "privacy_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    redacted_preview = Column(Text, nullable=False)
    detected_types = Column(JSON, nullable=False, default=dict)
    risk_score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="privacy_scans")

class DeepfakeScan(Base):
    __tablename__ = "deepfake_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    media_type = Column(String(20), nullable=False)  # IMAGE, VIDEO, AUDIO
    file_name = Column(String(255), nullable=True)
    file_hash = Column(String(64), nullable=False)
    verdict = Column(String(50), nullable=False, default="INCONCLUSIVE")
    authenticity_score = Column(Integer, nullable=False)
    forensic_flags = Column(JSON, nullable=False, default=dict)
    limitations_disclaimer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="deepfake_scans")

