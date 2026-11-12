import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # ADMIN_LOGIN, REPORT_REVIEW, EVIDENCE_DOWNLOAD, etc.
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", foreign_keys=[user_id])

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), unique=True, nullable=False)
    version = Column(String(30), nullable=False)
    model_type = Column(String(50), nullable=False)  # SCIKIT_LEARN_TFIDF, HEURISTIC_RULESET, OLLAMA_LLM
    is_active = Column(Boolean, default=True)
    parameters = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=utc_now)

    evaluations = relationship("ModelEvaluation", back_populates="model", cascade="all, delete-orphan")

class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(36), ForeignKey("model_registry.id", ondelete="CASCADE"), nullable=False)
    dataset_name = Column(String(100), nullable=False)
    accuracy = Column(Float, nullable=False)
    precision_score = Column(Float, nullable=False)
    recall_score = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    evaluation_notes = Column(Text, nullable=True)
    evaluated_at = Column(DateTime, default=utc_now)

    model = relationship("ModelRegistry", back_populates="evaluations")

class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    scan_type = Column(String(50), nullable=False)  # SCAM_MESSAGE, URL, SCREENSHOT
    scan_id = Column(String(36), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", foreign_keys=[user_id])

