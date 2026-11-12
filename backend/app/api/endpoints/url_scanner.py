from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.url_scan import (
    UrlScanRequest, UrlScanResponse, UrlHistoryItem, ConvertUrlToReportRequest
)
from backend.app.schemas.scam import ConvertToReportResponse
from backend.app.services.url_service import (
    process_url_scan, get_user_url_history, convert_url_scan_to_report
)
from backend.app.api.deps import get_current_user, get_current_user_optional

router = APIRouter()

@router.post("/scan", response_model=UrlScanResponse, status_code=status.HTTP_200_OK)
def scan_url(
    payload: UrlScanRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Scan a URL for phishing indicators, domain lookalike typo-squatting,
    SSRF vulnerabilities, raw IP hosts, and suspicious TLD patterns.
    """
    user_id = current_user.id if current_user else None
    return process_url_scan(raw_url=payload.url, user_id=user_id, db=db)

@router.get("/history", response_model=List[UrlHistoryItem])
def get_user_url_history_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve historical URL scans for the authenticated user."""
    return get_user_url_history(user_id=current_user.id, db=db)

@router.post("/report", response_model=ConvertToReportResponse, status_code=status.HTTP_201_CREATED)
def report_phishing_url_to_community(
    payload: ConvertUrlToReportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Escalate a flagged phishing URL directly into the community threat intelligence queue."""
    user_id = current_user.id if current_user else None
    return convert_url_scan_to_report(
        user_id=user_id,
        scan_id=payload.scan_id,
        target_value=payload.target_value,
        custom_description=payload.description,
        region=payload.region,
        db=db
    )

