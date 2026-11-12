import uuid
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.ml.url_analyzer import url_scanner, UrlAnalysisResult
from backend.app.models.scans import UrlScan
from backend.app.models.reports import Report
from backend.app.schemas.url_scan import (
    UrlScanResponse, UrlIndicatorDetail, UrlHistoryItem
)
from backend.app.schemas.scam import ConvertToReportResponse
from backend.app.api.deps import record_audit_log

def generate_report_code() -> str:
    """Generate unique tracking code: SUR-REP-XXXXXX"""
    code_num = random.randint(100000, 999999)
    return f"SUR-REP-{code_num}"

def process_url_scan(
    raw_url: str,
    user_id: Optional[str],
    db: Session
) -> UrlScanResponse:
    # 1. Execute intelligent URL scan with SSRF protections
    analysis: UrlAnalysisResult = url_scanner.analyze_url(raw_url)

    # 2. Persist in database (url_scans table)
    db_scan = UrlScan(
        id=str(uuid.uuid4()),
        user_id=user_id,
        url=analysis.url,
        domain=analysis.domain,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        is_ip_host=analysis.is_ip_host,
        has_ssl=analysis.has_ssl,
        lookalike_target=analysis.lookalike_target,
        redirect_chain=[],
        analysis_details=analysis.analysis_details
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)

    indicators_list = [
        UrlIndicatorDetail(
            rule=ind["rule"],
            description=ind["description"],
            weight=ind["weight"]
        )
        for ind in analysis.matched_indicators
    ]

    return UrlScanResponse(
        id=db_scan.id,
        url=analysis.url,
        domain=analysis.domain,
        risk_score=analysis.risk_score,
        risk_level=analysis.risk_level,
        is_ip_host=analysis.is_ip_host,
        has_ssl=analysis.has_ssl,
        is_shortened=analysis.is_shortened,
        lookalike_target=analysis.lookalike_target,
        matched_indicators=indicators_list,
        analysis_details=analysis.analysis_details,
        explanation=analysis.explanation,
        recommendations=analysis.recommendations,
        created_at=db_scan.created_at
    )

def get_user_url_history(user_id: str, db: Session, limit: int = 20) -> List[UrlHistoryItem]:
    scans = (
        db.query(UrlScan)
        .filter(UrlScan.user_id == user_id)
        .order_by(UrlScan.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        UrlHistoryItem(
            id=s.id,
            url=s.url,
            domain=s.domain,
            risk_score=s.risk_score,
            risk_level=s.risk_level,
            created_at=s.created_at
        )
        for s in scans
    ]

def convert_url_scan_to_report(
    user_id: Optional[str],
    scan_id: str,
    target_value: Optional[str],
    custom_description: Optional[str],
    region: Optional[str],
    db: Session
) -> ConvertToReportResponse:
    scan = db.query(UrlScan).filter(UrlScan.id == scan_id).first()
    target = target_value or (scan.url if scan else "Reported Phishing URL")

    description = custom_description or (
        f"Phishing URL Threat: {scan.url if scan else target} "
        f"(Risk: {scan.risk_score if scan else 'N/A'}/100, Lookalike: {scan.lookalike_target if scan else 'None'})"
    )

    report_code = generate_report_code()
    while db.query(Report).filter(Report.report_code == report_code).first():
        report_code = generate_report_code()

    new_report = Report(
        id=str(uuid.uuid4()),
        report_code=report_code,
        user_id=user_id,
        threat_type="URL",
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
        action="REPORT_SUBMITTED_FROM_URL_SCAN",
        resource_type="REPORT",
        resource_id=new_report.id,
        details={"report_code": report_code, "url": target},
        user_id=user_id
    )

    return ConvertToReportResponse(
        report_id=new_report.id,
        report_code=report_code,
        status=new_report.status,
        message="Phishing URL threat report submitted successfully and placed in admin verification queue."
    )

