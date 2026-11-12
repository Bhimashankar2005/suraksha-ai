import uuid
import os
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.ml.image_analyzer import analyze_screenshot_content, ImageAnalysisResult
from backend.app.models.scans import ImageScan
from backend.app.models.reports import Report
from backend.app.schemas.image_scan import (
    ImageScanResponse, ImageIndicatorDetail, ImageHistoryItem
)
from backend.app.schemas.scam import ConvertToReportResponse
from backend.app.core.config import settings
from backend.app.api.deps import record_audit_log

def generate_report_code() -> str:
    """Generate unique tracking code: SUR-REP-XXXXXX"""
    code_num = random.randint(100000, 999999)
    return f"SUR-REP-{code_num}"

def process_image_upload_and_scan(
    file_bytes: bytes,
    file_name: str,
    user_id: Optional[str],
    ocr_override: Optional[str],
    db: Session
) -> ImageScanResponse:
    # 1. Execute image validation, OCR extraction & scam analysis
    analysis: ImageAnalysisResult = analyze_screenshot_content(
        file_bytes=file_bytes,
        file_name=file_name,
        ocr_text_override=ocr_override
    )

    # 2. Store image securely on disk in storage/temp with randomized UUID filename
    storage_dir = os.path.join(settings.STORAGE_DIR, "temp")
    os.makedirs(storage_dir, exist_ok=True)
    ext = os.path.splitext(file_name)[1] or ".png"
    safe_storage_name = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(storage_dir, safe_storage_name)

    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    # 3. Persist record in database (image_scans table)
    db_scan = ImageScan(
        id=str(uuid.uuid4()),
        user_id=user_id,
        file_hash=analysis.file_hash,
        file_name=file_name,
        extracted_text=analysis.extracted_text,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        detected_entities=analysis.detected_entities
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)

    indicators_list = [
        ImageIndicatorDetail(
            rule_id=ind["rule_id"],
            category=ind["category"],
            description=ind["description"],
            weight=ind["weight"],
            matched_terms=ind["matched_terms"]
        )
        for ind in analysis.matched_indicators
    ]

    return ImageScanResponse(
        id=db_scan.id,
        file_hash=analysis.file_hash,
        file_name=analysis.file_name,
        file_size_bytes=analysis.file_size_bytes,
        dimensions=list(analysis.dimensions),
        mime_type=analysis.mime_type,
        extracted_text=analysis.extracted_text,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        scam_category=analysis.scam_category,
        detected_entities=analysis.detected_entities,
        matched_indicators=indicators_list,
        highlighted_tokens=analysis.highlighted_tokens,
        explanation=analysis.explanation,
        recommendations=analysis.recommendations,
        ocr_engine=analysis.ocr_engine,
        created_at=db_scan.created_at
    )

def get_user_image_history(user_id: str, db: Session, limit: int = 20) -> List[ImageHistoryItem]:
    scans = (
        db.query(ImageScan)
        .filter(ImageScan.user_id == user_id)
        .order_by(ImageScan.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        ImageHistoryItem(
            id=s.id,
            file_name=s.file_name,
            file_hash=s.file_hash,
            risk_score=s.risk_score,
            risk_level=s.risk_level,
            scam_category="SCREENSHOT_FRAUD",
            created_at=s.created_at
        )
        for s in scans
    ]

def convert_image_scan_to_report(
    user_id: Optional[str],
    scan_id: str,
    target_value: Optional[str],
    custom_description: Optional[str],
    region: Optional[str],
    db: Session
) -> ConvertToReportResponse:
    scan = db.query(ImageScan).filter(ImageScan.id == scan_id).first()
    target = target_value or (scan.file_name if scan else "Suspicious Screenshot")

    description = custom_description or (
        f"Suspicious Screenshot Scam: {scan.file_name if scan else ''} "
        f"(Risk Score: {scan.risk_score if scan else 'N/A'}/100, SHA-256: {scan.file_hash if scan else 'N/A'}). "
        f"Extracted: {scan.extracted_text[:200] if scan and scan.extracted_text else 'N/A'}"
    )

    report_code = generate_report_code()
    while db.query(Report).filter(Report.report_code == report_code).first():
        report_code = generate_report_code()

    new_report = Report(
        id=str(uuid.uuid4()),
        report_code=report_code,
        user_id=user_id,
        threat_type="SCREENSHOT",
        target_value=target.strip(),
        description=description.strip(),
        region=region.strip() if region else None,
        status="PENDING",
        is_public_alert=False
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    record_audit_log(
        db=db,
        action="REPORT_SUBMITTED_FROM_IMAGE_SCAN",
        resource_type="REPORT",
        resource_id=new_report.id,
        details={"report_code": report_code, "file_hash": scan.file_hash if scan else "N/A"},
        user_id=user_id
    )

    return ConvertToReportResponse(
        report_id=new_report.id,
        report_code=report_code,
        status=new_report.status,
        message="Screenshot scam threat report submitted successfully and placed in admin verification queue."
    )

