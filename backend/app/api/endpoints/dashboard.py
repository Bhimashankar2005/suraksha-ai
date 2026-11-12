from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.scans import ScamScan, UrlScan, ImageScan
from backend.app.models.reports import Report
from backend.app.models.safety_education import Notification
from backend.app.models.audit_feedback import AuditLog
from backend.app.schemas.dashboard import (
    UserDashboardResponse, AdminDashboardResponse, ActivityItem, NotificationSummary, AdminActionSummary
)
from backend.app.api.deps import get_current_user, require_admin

router = APIRouter()

@router.get("/user", response_model=UserDashboardResponse)
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    uid = current_user.id

    # Real database aggregations for user
    scam_count = db.query(ScamScan).filter(ScamScan.user_id == uid).count()
    url_count = db.query(UrlScan).filter(UrlScan.user_id == uid).count()
    image_count = db.query(ImageScan).filter(ImageScan.user_id == uid).count()
    total_scans = scam_count + url_count + image_count

    suspicious_scams = db.query(ScamScan).filter(ScamScan.user_id == uid, ScamScan.risk_score >= 50).count()
    suspicious_urls = db.query(UrlScan).filter(UrlScan.user_id == uid, UrlScan.risk_score >= 50).count()
    suspicious_images = db.query(ImageScan).filter(ImageScan.user_id == uid, ImageScan.risk_score >= 50).count()
    suspicious_detections = suspicious_scams + suspicious_urls + suspicious_images

    submitted_reports = db.query(Report).filter(Report.user_id == uid).count()
    pending_reports = db.query(Report).filter(Report.user_id == uid, Report.status == "PENDING").count()
    verified_reports = db.query(Report).filter(Report.user_id == uid, Report.status == "VERIFIED").count()

    # Aggregate recent user activity
    recent_activity: List[ActivityItem] = []

    recent_scams = db.query(ScamScan).filter(ScamScan.user_id == uid).order_by(ScamScan.created_at.desc()).limit(5).all()
    for s in recent_scams:
        recent_activity.append(ActivityItem(
            id=s.id,
            activity_type="SCAM_MESSAGE",
            title=f"Message Scan: {s.scam_category}",
            risk_level=s.risk_level,
            created_at=s.created_at
        ))

    recent_urls = db.query(UrlScan).filter(UrlScan.user_id == uid).order_by(UrlScan.created_at.desc()).limit(5).all()
    for u in recent_urls:
        recent_activity.append(ActivityItem(
            id=u.id,
            activity_type="URL_SCAN",
            title=f"URL: {u.domain}",
            risk_level=u.risk_level,
            created_at=u.created_at
        ))

    recent_reps = db.query(Report).filter(Report.user_id == uid).order_by(Report.created_at.desc()).limit(5).all()
    for r in recent_reps:
        recent_activity.append(ActivityItem(
            id=r.id,
            activity_type="COMMUNITY_REPORT",
            title=f"Report: {r.report_code} ({r.threat_type})",
            status=r.status,
            created_at=r.created_at
        ))

    # Sort combined activity by created_at desc
    recent_activity.sort(key=lambda x: x.created_at, reverse=True)
    recent_activity = recent_activity[:10]

    # Fetch recent notifications
    db_notifs = db.query(Notification).filter(Notification.user_id == uid).order_by(Notification.created_at.desc()).limit(5).all()
    notifications = [
        NotificationSummary(
            id=n.id,
            title=n.title,
            message=n.message,
            category=n.category,
            is_read=n.is_read,
            created_at=n.created_at
        ) for n in db_notifs
    ]

    return UserDashboardResponse(
        total_scans=total_scans,
        suspicious_detections=suspicious_detections,
        submitted_reports=submitted_reports,
        pending_reports=pending_reports,
        verified_reports=verified_reports,
        recent_activity=recent_activity,
        notifications=notifications
    )

@router.get("/admin", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    # Real database aggregations for admin
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    suspended_users = db.query(User).filter(User.is_active == False).count()

    total_reports = db.query(Report).count()
    pending_reports = db.query(Report).filter(Report.status == "PENDING").count()
    verified_reports = db.query(Report).filter(Report.status == "VERIFIED").count()
    rejected_reports = db.query(Report).filter(Report.status == "REJECTED").count()
    duplicate_reports = db.query(Report).filter(Report.status == "DUPLICATE").count()

    total_scans = (
        db.query(ScamScan).count() +
        db.query(UrlScan).count() +
        db.query(ImageScan).count()
    )
    suspicious_urls = db.query(UrlScan).filter(UrlScan.risk_score >= 50).count()

    # Threat category breakdown
    category_counts = db.query(Report.threat_type, func.count(Report.id)).group_by(Report.threat_type).all()
    threat_categories: Dict[str, int] = {cat: count for cat, count in category_counts}

    # Recent admin actions / audit logs
    db_actions = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(10).all()
    recent_admin_actions = []
    for a in db_actions:
        admin_email = a.user.email if a.user else "System"
        recent_admin_actions.append(AdminActionSummary(
            id=a.id,
            action=a.action,
            resource_type=a.resource_type,
            resource_id=a.resource_id,
            details=a.details if isinstance(a.details, dict) else {},
            ip_address=a.ip_address,
            admin_email=admin_email,
            created_at=a.created_at
        ))

    return AdminDashboardResponse(
        total_users=total_users,
        active_users=active_users,
        suspended_users=suspended_users,
        total_reports=total_reports,
        pending_reports=pending_reports,
        verified_reports=verified_reports,
        rejected_reports=rejected_reports,
        duplicate_reports=duplicate_reports,
        total_scans=total_scans,
        suspicious_urls=suspicious_urls,
        threat_categories=threat_categories,
        recent_admin_actions=recent_admin_actions
    )

