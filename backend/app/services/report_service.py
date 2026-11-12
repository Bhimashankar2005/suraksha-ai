import re
import secrets
import string
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.reports import Report, ReportReview, Threat
from backend.app.schemas.report import ReportCreate, ReportReviewAction

def normalize_target_value(threat_type: str, value: str) -> str:
    """Normalizes phone numbers, URLs, and indicators for duplicate detection."""
    clean = value.strip()
    if threat_type == "PHONE":
        digits = re.sub(r"\D", "", clean)
        if len(digits) == 12 and digits.startswith("91"):
            return digits[2:]
        if len(digits) == 11 and digits.startswith("0"):
            return digits[1:]
        return digits if digits else clean

    if threat_type == "URL":
        clean_url = re.sub(r"^https?://(www\.)?", "", clean, flags=re.IGNORECASE)
        return clean_url.rstrip("/").lower()

    if threat_type in ["MESSAGE", "HARASSMENT"]:
        return clean[:200].lower()

    return clean.lower()

def generate_unique_report_code(db: Session) -> str:
    """Generates a secure, human-readable report code (SUR-REP-XXXXXX)."""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(10):
        suffix = "".join(secrets.choice(alphabet) for _ in range(6))
        code = f"SUR-REP-{suffix}"
        exists = db.query(Report).filter(Report.report_code == code).first()
        if not exists:
            return code
    # Fallback timestamp
    import time
    return f"SUR-REP-{int(time.time())}"

def detect_duplicate(db: Session, threat_type: str, target_value: str) -> Tuple[bool, Optional[str], int]:
    """
    Checks if a matching report or threat already exists in the system.
    Returns (is_duplicate, original_report_id, incident_count).
    """
    normalized = normalize_target_value(threat_type, target_value)

    # 1. Check in verified threats table first
    existing_threat = db.query(Threat).filter(
        func.lower(Threat.indicator_value).contains(normalized)
    ).first()

    if existing_threat:
        return True, existing_threat.origin_report_id, (existing_threat.incident_count + 1)

    # 2. Check in reports table
    existing_report = db.query(Report).filter(
        Report.threat_type == threat_type,
        func.lower(Report.target_value).contains(normalized)
    ).order_by(Report.created_at.asc()).first()

    if existing_report:
        count = db.query(Report).filter(
            Report.threat_type == threat_type,
            func.lower(Report.target_value).contains(normalized)
        ).count()
        return True, existing_report.id, (count + 1)

    return False, None, 1

def create_community_report(
    db: Session,
    report_in: ReportCreate,
    user_id: Optional[str] = None
) -> Report:
    """Creates a new citizen threat report with duplicate checking and code generation."""
    is_dup, orig_id, _ = detect_duplicate(db, report_in.threat_type, report_in.target_value)
    report_code = generate_unique_report_code(db)

    report = Report(
        report_code=report_code,
        user_id=None if report_in.is_anonymous else user_id,
        threat_type=report_in.threat_type,
        target_value=report_in.target_value.strip(),
        description=report_in.description.strip(),
        region=report_in.region.strip() if report_in.region else None,
        status="PENDING",
        is_public_alert=False,
        duplicate_of_id=orig_id if is_dup else None
    )

    db.add(report)
    db.commit()
    db.refresh(report)
    return report

def review_community_report(
    db: Session,
    report_id: str,
    admin_id: str,
    review_in: ReportReviewAction
) -> Report:
    """
    Processes moderation action by an authorized security analyst.
    Updates report status, logs review record, and optionally publishes public Threat intel.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ValueError("Report not found")

    action_to_status = {
        "APPROVE_VERIFY": "VERIFIED",
        "REJECT": "REJECTED",
        "MARK_DUPLICATE": "DUPLICATE",
        "RESOLVE": "RESOLVED"
    }

    new_status = action_to_status.get(review_in.action, "UNDER_REVIEW")
    report.status = new_status

    if review_in.action == "APPROVE_VERIFY" and review_in.publish_as_public_alert:
        report.is_public_alert = True

        # Check if threat already tracked
        existing_threat = db.query(Threat).filter(
            Threat.indicator_value == report.target_value
        ).first()

        if existing_threat:
            existing_threat.incident_count += 1
            existing_threat.threat_level = review_in.threat_level or existing_threat.threat_level
            existing_threat.is_active = True
        else:
            new_threat = Threat(
                origin_report_id=report.id,
                indicator_type=report.threat_type,
                indicator_value=report.target_value,
                threat_level=review_in.threat_level or "HIGH",
                description=review_in.public_notes or report.description,
                verified_by_admin_id=admin_id,
                incident_count=1,
                is_active=True
            )
            db.add(new_threat)

    review_entry = ReportReview(
        report_id=report.id,
        admin_id=admin_id,
        action_taken=review_in.action,
        internal_notes=review_in.internal_notes,
        public_notes=review_in.public_notes
    )
    db.add(review_entry)
    db.commit()
    db.refresh(report)

    # Automatic In-App Notification Hook
    try:
        from backend.app.services.notification_service import notification_service
        if report.user_id:
            notification_service.create_notification(
                db=db,
                user_id=report.user_id,
                title=f"Report {report.report_code} Status: {new_status}",
                message=f"Your submitted incident report ({report.threat_type}) has been reviewed by the cyber defense team. Status: {new_status}. {review_in.public_notes or ''}".strip(),
                category="REPORT_UPDATE",
                action_url=f"/community-reports?tab=track&code={report.report_code}"
            )

        if review_in.action == "APPROVE_VERIFY" and review_in.publish_as_public_alert:
            notification_service.broadcast_notification(
                db=db,
                title=f"Verified Threat Alert: {report.threat_type}",
                message=f"New verified threat indicator: {report.target_value}. Review active safety recommendations.",
                category="SECURITY_ALERT",
                action_url="/community-reports?tab=alerts"
            )
    except Exception:
        pass  # Non-blocking notification dispatch

    return report

def get_threat_intelligence_stats(db: Session) -> Dict[str, Any]:
    """Computes real-time threat intelligence statistics from SQLite/PostgreSQL."""
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    pending_reviews = db.query(func.count(Report.id)).filter(Report.status == "PENDING").scalar() or 0
    verified_threats = db.query(func.count(Report.id)).filter(Report.status == "VERIFIED").scalar() or 0
    resolved_reports = db.query(func.count(Report.id)).filter(Report.status == "RESOLVED").scalar() or 0

    # Group by category
    type_counts = db.query(Report.threat_type, func.count(Report.id)).group_by(Report.threat_type).all()
    by_category = {t: c for t, c in type_counts}

    # Group by region
    region_counts = db.query(Report.region, func.count(Report.id)).filter(
        Report.region.isnot(None), Report.region != ""
    ).group_by(Report.region).limit(10).all()
    by_region = {r: c for r, c in region_counts if r}

    active_threats = db.query(func.count(Threat.id)).filter(Threat.is_active == True).scalar() or 0

    return {
        "total_reports": total_reports,
        "pending_reviews": pending_reviews,
        "verified_threats": verified_threats,
        "resolved_reports": resolved_reports,
        "by_category": by_category,
        "by_region": by_region,
        "active_threat_indicators": active_threats
    }

