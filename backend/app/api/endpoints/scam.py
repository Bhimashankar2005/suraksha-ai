from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.scans import ScamScan
from backend.app.schemas.scam import (
    ScamScanRequest, ScamScanResponse, ScamHistoryItem,
    ScamFeedbackRequest, ConvertToReportRequest, ConvertToReportResponse
)
from backend.app.services.scam_service import (
    process_message_scan, get_scam_history, record_scan_feedback, convert_scan_to_report
)
from backend.app.ml.scam_classifier import scam_classifier
from backend.app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()

@router.post("/scan", response_model=ScamScanResponse, status_code=status.HTTP_200_OK)
def scan_suspicious_message(
    payload: ScamScanRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Analyze suspicious SMS, WhatsApp, Email, or communication text.
    Provides explainable risk scoring, matched heuristic rules, ML probability, and safety advice.
    """
    user_id = current_user.id if current_user else None
    return process_message_scan(content=payload.content, user_id=user_id, db=db)

@router.get("/history", response_model=List[ScamHistoryItem])
def get_user_scam_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve historical scam scans for the authenticated user."""
    return get_scam_history(user_id=current_user.id, db=db)

@router.get("/model-evaluation")
def get_classifier_evaluation():
    """
    Returns empirical evaluation metrics (Precision, Recall, F1, Accuracy)
    evaluated on the scam test dataset.
    """
    eval_metrics = scam_classifier.evaluate_test_dataset()
    return {
        "model_name": "SURAKSHA_EXPLAINABLE_SCAM_CLASSIFIER",
        "architecture": "TF-IDF + Multinomial Naive Bayes + Heuristic Rules",
        "type": "Local Deterministic & Explainable ML",
        "metrics": eval_metrics,
        "disclaimer": "Detection scores are probabilistic risk assessments and do not claim 100% certainty. Always cross-verify with official bank channels."
    }

@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def submit_scam_feedback(
    payload: ScamFeedbackRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Submit user feedback and rating for a specific scam scan."""
    user_id = current_user.id if current_user else None
    feedback = record_scan_feedback(
        user_id=user_id,
        scan_id=payload.scan_id,
        rating=payload.rating,
        feedback_text=payload.feedback_text,
        db=db
    )
    return {"message": "Thank you for your feedback.", "feedback_id": feedback.id}

@router.post("/report", response_model=ConvertToReportResponse, status_code=status.HTTP_201_CREATED)
def report_scam_to_community(
    payload: ConvertToReportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Convert an analyzed scam scan directly into a community threat intelligence report."""
    user_id = current_user.id if current_user else None
    return convert_scan_to_report(
        user_id=user_id,
        scan_id=payload.scan_id,
        target_value=payload.target_value,
        custom_description=payload.description,
        region=payload.region,
        db=db
    )

