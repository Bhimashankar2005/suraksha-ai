from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_user_optional, record_audit_log
from backend.app.models.user import User
from backend.app.models.scans import DeepfakeScan
from backend.app.models.reports import Report
from backend.app.schemas.report import ReportCreate
from backend.app.services.report_service import create_community_report
from backend.app.schemas.deepfake import (
    DeepfakeScanResponse,
    DeepfakeHistoryItem,
    DeepfakeReportRequest,
    DeepfakeReportResponse
)
from backend.app.ml.media_authenticity_engine import media_authenticity_engine

router = APIRouter()

MAX_MEDIA_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB limit for local processing

@router.post("/analyze", response_model=DeepfakeScanResponse)
def analyze_media_authenticity(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Analyzes uploaded image, audio, or video for deepfake and synthetic media indicators.
    Executes local Error Level Analysis (ELA), EXIF software metadata inspection,
    and returns a transparent confidence score with statutory disclaimers.
    """
    file_bytes = file.file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded media file is empty."
        )

    if len(file_bytes) > MAX_MEDIA_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Media file exceeds maximum allowed limit of {MAX_MEDIA_SIZE_BYTES // (1024*1024)}MB."
        )

    analysis = media_authenticity_engine.analyze_media(
        file_bytes=file_bytes,
        filename=file.filename or "unknown_media"
    )

    scan_id = None
    created_at = datetime.now(timezone.utc)

    # Persist scan record if authenticated
    if current_user:
        deepfake_scan = DeepfakeScan(
            user_id=current_user.id,
            media_type=analysis["media_type"],
            file_name=analysis["file_name"],
            file_hash=analysis["file_hash"],
            verdict=analysis["verdict"],
            authenticity_score=analysis["authenticity_score"],
            forensic_flags=analysis["forensic_flags"],
            limitations_disclaimer=analysis["limitations_disclaimer"],
            created_at=created_at
        )
        db.add(deepfake_scan)
        db.commit()
        db.refresh(deepfake_scan)
        scan_id = deepfake_scan.id

        record_audit_log(
            db=db,
            action="DEEPFAKE_MEDIA_SCAN",
            resource_type="DEEPFAKE_SCAN",
            resource_id=scan_id,
            details={
                "file_hash": analysis["file_hash"],
                "verdict": analysis["verdict"],
                "authenticity_score": analysis["authenticity_score"]
            },
            user_id=current_user.id
        )

    return DeepfakeScanResponse(
        id=scan_id,
        file_name=analysis["file_name"],
        file_hash=analysis["file_hash"],
        media_type=analysis["media_type"],
        file_size_kb=analysis["file_size_kb"],
        authenticity_score=analysis["authenticity_score"],
        verdict=analysis["verdict"],
        forensic_flags=analysis["forensic_flags"],
        limitations_disclaimer=analysis["limitations_disclaimer"],
        created_at=created_at
    )

@router.get("/history", response_model=List[DeepfakeHistoryItem])
def get_deepfake_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns authenticated user's past deepfake media analysis history.
    """
    scans = db.query(DeepfakeScan).filter(
        DeepfakeScan.user_id == current_user.id
    ).order_by(DeepfakeScan.created_at.desc()).limit(limit).all()

    return [
        DeepfakeHistoryItem(
            id=s.id,
            file_name=s.file_name,
            media_type=s.media_type,
            file_hash=s.file_hash,
            verdict=s.verdict or "INCONCLUSIVE",
            authenticity_score=s.authenticity_score,
            created_at=s.created_at
        )
        for s in scans
    ]

@router.post("/report", response_model=DeepfakeReportResponse)
def report_deepfake_threat(
    payload: DeepfakeReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Escalates a detected synthetic media / deepfake scam into a Community Cyber Threat Report.
    """
    scan = db.query(DeepfakeScan).filter(
        DeepfakeScan.id == payload.scan_id,
        DeepfakeScan.user_id == current_user.id
    ).first()

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deepfake analysis scan record not found."
        )

    target_val = f"File Hash: {scan.file_hash[:16]}... ({scan.file_name or scan.media_type})"
    desc = payload.description or f"Suspicious synthetic media detected (Verdict: {scan.verdict}, Authenticity Score: {scan.authenticity_score}/100)"

    report_in = ReportCreate(
        threat_type="SCREENSHOT",
        target_value=target_val,
        description=desc,
        is_anonymous=False
    )
    new_report = create_community_report(
        db=db,
        report_in=report_in,
        user_id=current_user.id
    )

    return DeepfakeReportResponse(
        report_code=new_report.report_code,
        threat_type=new_report.threat_type,
        target_value=new_report.target_value,
        status=new_report.status,
        message="Synthetic media incident reported to community intelligence queue."
    )
