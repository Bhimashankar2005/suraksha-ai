import uuid
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.ml.scam_classifier import scam_classifier, ScamAnalysisResult
from backend.app.models.scans import ScamScan
from backend.app.models.reports import Report
from backend.app.models.audit_feedback import UserFeedback
from backend.app.schemas.scam import (
    ScamScanResponse, IndicatorDetail, ScamHistoryItem, ConvertToReportResponse
)
from backend.app.api.deps import record_audit_log

def generate_report_code() -> str:
    """Generate unique tracking code: SUR-REP-XXXXXX"""
    code_num = random.randint(100000, 999999)
    return f"SUR-REP-{code_num}"

def process_message_scan(
    content: str,
    user_id: Optional[str],
    db: Session
) -> ScamScanResponse:
    # 1. Run explainable hybrid analysis
    analysis: ScamAnalysisResult = scam_classifier.analyze_message(content)

    # 2. Sanitize and store snippet
    snippet = content[:300] + ("..." if len(content) > 300 else "")

    # 3. Persist scan in database
    db_scan = ScamScan(
        id=str(uuid.uuid4()),
        user_id=user_id,
        content_snippet=snippet,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        scam_category=analysis.scam_category,
        indicators=analysis.matched_indicators,
        recommendations=analysis.recommendations
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)

    # 4. Map to response schema
    indicators_list = [
        IndicatorDetail(
            rule_id=ind["rule_id"],
            category=ind["category"],
            description=ind["description"],
            weight=ind["weight"],
            matched_terms=ind["matched_terms"]
        )
        for ind in analysis.matched_indicators
    ]

    return ScamScanResponse(
        id=db_scan.id,
        content_snippet=snippet,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        scam_category=analysis.scam_category,
        ml_probability=analysis.ml_probability,
        matched_indicators=indicators_list,
        highlighted_tokens=analysis.highlighted_tokens,
        explanation=analysis.explanation,
        recommendations=analysis.recommendations,
        created_at=db_scan.created_at
    )

def get_scam_history(user_id: str, db: Session, limit: int = 20) -> List[ScamHistoryItem]:
    scans = (
        db.query(ScamScan)
        .filter(ScamScan.user_id == user_id)
        .order_by(ScamScan.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        ScamHistoryItem(
            id=s.id,
            content_snippet=s.content_snippet,
            risk_score=s.risk_score,
            risk_level=s.risk_level,
            scam_category=s.scam_category,
            created_at=s.created_at
        )
        for s in scans
    ]

def record_scan_feedback(
    user_id: Optional[str],
    scan_id: str,
    rating: int,
    feedback_text: Optional[str],
    db: Session
) -> UserFeedback:
    feedback_entry = UserFeedback(
        id=str(uuid.uuid4()),
        user_id=user_id,
        scan_type="SCAM_MESSAGE",
        scan_id=scan_id,
        rating=rating,
        feedback_text=feedback_text
    )
    db.add(feedback_entry)
    db.commit()
    return feedback_entry

def convert_scan_to_report(
    user_id: Optional[str],
    scan_id: str,
    target_value: str,
    custom_description: Optional[str],
    region: Optional[str],
    db: Session
) -> ConvertToReportResponse:
    scan = db.query(ScamScan).filter(ScamScan.id == scan_id).first()
    description = custom_description or (
        f"Suspicious Message Scan (Category: {scan.scam_category if scan else 'UNKNOWN'}, "
        f"Risk Score: {scan.risk_score if scan else 'N/A'}/100). Snippet: {scan.content_snippet if scan else ''}"
    )

    report_code = generate_report_code()
    # Check code uniqueness
    while db.query(Report).filter(Report.report_code == report_code).first():
        report_code = generate_report_code()

    new_report = Report(
        id=str(uuid.uuid4()),
        report_code=report_code,
        user_id=user_id,
        threat_type="MESSAGE",
        target_value=target_value.strip(),
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
        action="REPORT_SUBMITTED_FROM_SCAM_SCAN",
        resource_type="REPORT",
        resource_id=new_report.id,
        details={"report_code": report_code, "scan_id": scan_id},
        user_id=user_id
    )

    return ConvertToReportResponse(
        report_id=new_report.id,
        report_code=report_code,
        status=new_report.status,
        message="Threat report submitted successfully and placed in admin verification queue."
    )

