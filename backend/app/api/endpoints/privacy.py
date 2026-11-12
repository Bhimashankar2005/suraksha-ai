from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user_optional, get_current_user, record_audit_log
from backend.app.models.user import User
from backend.app.models.scans import PrivacyScan
from backend.app.schemas.privacy import (
    PrivacyScanRequest,
    PrivacyScanResponse,
    PrivacyHistoryItem,
    DetectedEntityItem
)
from backend.app.ml.privacy_scanner import privacy_scanner

router = APIRouter()

@router.post("/scan-text", response_model=PrivacyScanResponse)
def scan_text_privacy(
    payload: PrivacyScanRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Scans in-memory text for sensitive Indian identifiers (Aadhaar, PAN, Cards, Phone, Email, UPI).
    Provides instant masking and redaction without storing unredacted sensitive credentials.
    """
    result = privacy_scanner.scan_and_redact(payload.text)

    scan_id = None
    if current_user:
        # Save only the sanitized redacted preview for citizen audit history
        preview_snippet = result["sanitized_text"][:500]
        db_scan = PrivacyScan(
            user_id=current_user.id,
            redacted_preview=preview_snippet,
            detected_types=result["detected_counts"],
            risk_score=result["risk_score"]
        )
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)
        scan_id = db_scan.id

        record_audit_log(
            db=db,
            action="PRIVACY_SCAN",
            resource_type="PRIVACY_SCAN",
            resource_id=scan_id,
            details={"risk_score": result["risk_score"], "detected_counts": result["detected_counts"]},
            user_id=current_user.id
        )

    entities = [
        DetectedEntityItem(
            type=e["type"],
            raw_preview=e["raw_preview"],
            start=e["start"],
            end=e["end"],
            confidence=e["confidence"],
            is_checksum_valid=e.get("is_checksum_valid")
        )
        for e in result["detected_entities"]
    ]

    return PrivacyScanResponse(
        scan_id=scan_id,
        detected_entities=entities,
        detected_counts=result["detected_counts"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        sanitized_text=result["sanitized_text"],
        recommendations=result["recommendations"]
    )

@router.post("/scan-file", response_model=PrivacyScanResponse)
async def scan_file_privacy(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    In-memory file scan for privacy redaction.
    Accepts text-based files (TXT, CSV, LOG).
    Raw files are processed in-memory and NEVER persisted to disk.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 5MB in-memory scanning limit.")

    try:
        text_content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text_content = file_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode file text. Please ensure the file is in UTF-8 or text format."
            )

    result = privacy_scanner.scan_and_redact(text_content)

    scan_id = None
    if current_user:
        preview_snippet = result["sanitized_text"][:500]
        db_scan = PrivacyScan(
            user_id=current_user.id,
            redacted_preview=preview_snippet,
            detected_types=result["detected_counts"],
            risk_score=result["risk_score"]
        )
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)
        scan_id = db_scan.id

        record_audit_log(
            db=db,
            action="PRIVACY_FILE_SCAN",
            resource_type="PRIVACY_SCAN",
            resource_id=scan_id,
            details={"filename": file.filename, "risk_score": result["risk_score"]},
            user_id=current_user.id
        )

    entities = [
        DetectedEntityItem(
            type=e["type"],
            raw_preview=e["raw_preview"],
            start=e["start"],
            end=e["end"],
            confidence=e["confidence"],
            is_checksum_valid=e.get("is_checksum_valid")
        )
        for e in result["detected_entities"]
    ]

    return PrivacyScanResponse(
        scan_id=scan_id,
        detected_entities=entities,
        detected_counts=result["detected_counts"],
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        sanitized_text=result["sanitized_text"],
        recommendations=result["recommendations"]
    )

@router.get("/history", response_model=List[PrivacyHistoryItem])
def get_privacy_scan_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns citizen's past privacy scan history with redacted previews.
    """
    scans = db.query(PrivacyScan).filter(
        PrivacyScan.user_id == current_user.id
    ).order_by(PrivacyScan.created_at.desc()).limit(20).all()

    return [
        PrivacyHistoryItem(
            id=s.id,
            redacted_preview=s.redacted_preview,
            detected_types=s.detected_types or {},
            risk_score=s.risk_score,
            created_at=s.created_at
        )
        for s in scans
    ]

@router.delete("/history/{scan_id}", status_code=status.HTTP_200_OK)
def delete_privacy_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a privacy scan entry from history.
    """
    scan = db.query(PrivacyScan).filter(
        PrivacyScan.id == scan_id,
        PrivacyScan.user_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan record not found.")

    db.delete(scan)
    db.commit()
    return {"status": "deleted", "id": scan_id}

