from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_user_optional, require_admin, record_audit_log
from backend.app.models.user import User
from backend.app.models.reports import Report, Threat
from backend.app.schemas.report import (
    ReportCreate,
    ReportTrackResponse,
    ReportListItem,
    ReportReviewAction,
    PublicThreatAlertItem,
    ThreatIntelligenceStats,
    ReviewHistoryItem
)
from backend.app.services.report_service import (
    create_community_report,
    review_community_report,
    get_threat_intelligence_stats
)

router = APIRouter()

@router.post("/submit", response_model=ReportListItem, status_code=status.HTTP_201_CREATED)
def submit_threat_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Submits a suspicious message, phone number, phishing URL, or scam incident.
    Generates a unique tracking code (SUR-REP-XXXXXX) and checks for duplicates.
    Can be submitted anonymously or linked to an authenticated citizen account.
    """
    user_id = current_user.id if current_user else None
    report = create_community_report(db, report_in, user_id=user_id)

    record_audit_log(
        db=db,
        action="REPORT_SUBMISSION",
        resource_type="REPORT",
        resource_id=report.id,
        details={
            "report_code": report.report_code,
            "threat_type": report.threat_type,
            "is_duplicate": bool(report.duplicate_of_id)
        },
        user_id=user_id
    )

    return ReportListItem(
        id=report.id,
        report_code=report.report_code,
        threat_type=report.threat_type,
        target_value=report.target_value,
        description=report.description,
        region=report.region,
        status=report.status,
        is_public_alert=report.is_public_alert,
        is_duplicate=bool(report.duplicate_of_id),
        created_at=report.created_at
    )

@router.get("/track/{report_code}", response_model=ReportTrackResponse)
def track_report_status(
    report_code: str,
    db: Session = Depends(get_db)
):
    """
    Public tracking endpoint. Citizens can check verification progress,
    review feedback, and investigation timeline using their Report ID.
    Does not expose victim identity.
    """
    code = report_code.strip().upper()
    report = db.query(Report).filter(Report.report_code == code).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with code '{report_code}' was not found. Please verify your reference number."
        )

    reviews = [
        ReviewHistoryItem(
            action_taken=r.action_taken,
            public_notes=r.public_notes,
            created_at=r.created_at
        )
        for r in report.reviews
    ]

    return ReportTrackResponse(
        report_code=report.report_code,
        threat_type=report.threat_type,
        target_value=report.target_value,
        description=report.description,
        region=report.region,
        status=report.status,
        is_public_alert=report.is_public_alert,
        is_duplicate=bool(report.duplicate_of_id),
        created_at=report.created_at,
        updated_at=report.updated_at or report.created_at,
        reviews=reviews
    )

@router.get("/my-reports", response_model=List[ReportListItem])
def get_user_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all threat reports submitted by the logged-in citizen.
    """
    reports = db.query(Report).filter(
        Report.user_id == current_user.id
    ).order_by(Report.created_at.desc()).all()

    return [
        ReportListItem(
            id=r.id,
            report_code=r.report_code,
            threat_type=r.threat_type,
            target_value=r.target_value,
            description=r.description,
            region=r.region,
            status=r.status,
            is_public_alert=r.is_public_alert,
            is_duplicate=bool(r.duplicate_of_id),
            created_at=r.created_at
        )
        for r in reports
    ]

@router.get("/alerts", response_model=List[PublicThreatAlertItem])
def get_verified_threat_alerts(
    threat_type: Optional[str] = Query(None, description="Filter by category: PHONE, URL, MESSAGE"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Public Community Threat Intelligence Feed.
    Returns verified, active fraud indicators without exposing victim identities.
    """
    query = db.query(Threat).filter(Threat.is_active == True)
    if threat_type and isinstance(threat_type, str):
        query = query.filter(Threat.indicator_type == threat_type)

    max_records = limit if isinstance(limit, int) else 20
    threats = query.order_by(Threat.incident_count.desc(), Threat.updated_at.desc()).limit(max_records).all()

    return [
        PublicThreatAlertItem(
            threat_id=t.id,
            indicator_type=t.indicator_type,
            indicator_value=t.indicator_value,
            threat_level=t.threat_level,
            description=t.description,
            incident_count=t.incident_count,
            is_active=t.is_active,
            created_at=t.created_at,
            updated_at=t.updated_at or t.created_at
        )
        for t in threats
    ]

@router.get("/stats", response_model=ThreatIntelligenceStats)
def get_threat_stats(db: Session = Depends(get_db)):
    """
    Returns real-time database metrics for the threat intelligence dashboard.
    """
    stats = get_threat_intelligence_stats(db)
    return ThreatIntelligenceStats(
        total_reports=stats["total_reports"],
        pending_reviews=stats["pending_reviews"],
        verified_threats=stats["verified_threats"],
        resolved_reports=stats["resolved_reports"],
        by_category=stats["by_category"],
        by_region=stats["by_region"],
        active_threat_indicators=stats["active_threat_indicators"]
    )

# --- Admin Moderation Endpoints ---

@router.get("/admin/queue", response_model=List[ReportListItem])
def get_admin_report_queue(
    status_filter: Optional[str] = Query("PENDING", description="Filter queue by status"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Moderation queue for authorized security administrators.
    """
    query = db.query(Report)
    if status_filter and isinstance(status_filter, str):
        query = query.filter(Report.status == status_filter)
    reports = query.order_by(Report.created_at.asc()).limit(50).all()

    return [
        ReportListItem(
            id=r.id,
            report_code=r.report_code,
            threat_type=r.threat_type,
            target_value=r.target_value,
            description=r.description,
            region=r.region,
            status=r.status,
            is_public_alert=r.is_public_alert,
            is_duplicate=bool(r.duplicate_of_id),
            created_at=r.created_at
        )
        for r in reports
    ]

@router.post("/admin/{report_id}/review", response_model=ReportListItem)
def review_report(
    report_id: str,
    review_in: ReportReviewAction,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Authorized administrator review action (Approve, Reject, Mark Duplicate, Resolve).
    """
    try:
        report = review_community_report(db, report_id, admin_user.id, review_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    record_audit_log(
        db=db,
        action=f"REPORT_{review_in.action}",
        resource_type="REPORT",
        resource_id=report.id,
        details={
            "report_code": report.report_code,
            "action": review_in.action,
            "new_status": report.status,
            "is_public_alert": report.is_public_alert
        },
        user_id=admin_user.id
    )

    return ReportListItem(
        id=report.id,
        report_code=report.report_code,
        threat_type=report.threat_type,
        target_value=report.target_value,
        description=report.description,
        region=report.region,
        status=report.status,
        is_public_alert=report.is_public_alert,
        is_duplicate=bool(report.duplicate_of_id),
        created_at=report.created_at
    )
