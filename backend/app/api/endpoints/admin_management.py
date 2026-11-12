import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from backend.app.core.database import get_db
from backend.app.api.deps import require_admin, record_audit_log
from backend.app.models.user import User, Role, Profile
from backend.app.models.reports import Report, Threat
from backend.app.models.scans import ScamScan, UrlScan, ImageScan, DeepfakeScan, PrivacyScan
from backend.app.models.evidence import EvidenceFile
from backend.app.models.audit_feedback import AuditLog
from backend.app.services.notification_service import notification_service
from backend.app.schemas.admin import (
    AdminUserListItem,
    AdminUserUpdateRoleRequest,
    AdminUserStatusToggleRequest,
    AuditLogListItem,
    SystemHealthTelemetry,
    AdminThreatItem,
    AdminThreatUpdateRequest
)

router = APIRouter()

@router.get("/users", response_model=List[AdminUserListItem])
def list_system_users(
    search: Optional[str] = Query(None, description="Search by email or name"),
    role: Optional[str] = Query(None, description="Filter by role name"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    List registered users with roles, profile information, and activity aggregates.
    """
    query = db.query(User).join(Role)

    if role:
        query = query.filter(Role.name == role.upper())

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if search:
        search_fmt = f"%{search.strip().lower()}%"
        query = query.outerjoin(Profile).filter(
            (func.lower(User.email).like(search_fmt)) |
            (func.lower(Profile.full_name).like(search_fmt))
        )

    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for u in users:
        # Calculate real user scans
        scams = db.query(func.count(ScamScan.id)).filter(ScamScan.user_id == u.id).scalar() or 0
        urls = db.query(func.count(UrlScan.id)).filter(UrlScan.user_id == u.id).scalar() or 0
        images = db.query(func.count(ImageScan.id)).filter(ImageScan.user_id == u.id).scalar() or 0
        deepfakes = db.query(func.count(DeepfakeScan.id)).filter(DeepfakeScan.user_id == u.id).scalar() or 0
        total_scans = scams + urls + images + deepfakes

        reports_count = db.query(func.count(Report.id)).filter(Report.user_id == u.id).scalar() or 0

        full_name = u.profile.full_name if u.profile else None
        phone_number = u.profile.phone_number if u.profile else None

        results.append(AdminUserListItem(
            id=u.id,
            email=u.email,
            role=u.role.name if u.role else "USER",
            role_id=u.role_id,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at,
            scans_count=total_scans,
            reports_count=reports_count,
            full_name=full_name,
            phone_number=phone_number
        ))

    return results

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: AdminUserUpdateRoleRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Updates a user's authorization role. Enforces safeguard preventing demotion of the last active administrator.
    """
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    new_role = db.query(Role).filter(Role.name == payload.role_name.upper()).first()
    if not new_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role_name}'. Available: USER, ADMIN, COMMUNITY_MODERATOR."
        )

    # Safeguard: Do not allow demoting the last admin
    if target_user.role and target_user.role.name == "ADMIN" and new_role.name != "ADMIN":
        admin_count = db.query(func.count(User.id)).join(Role).filter(
            Role.name == "ADMIN",
            User.is_active == True
        ).scalar() or 0
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Security Violation: Cannot demote the platform's last active Administrator."
            )

    old_role_name = target_user.role.name if target_user.role else "NONE"
    target_user.role_id = new_role.id
    db.commit()
    db.refresh(target_user)

    record_audit_log(
        db=db,
        action="UPDATE_USER_ROLE",
        resource_type="USER",
        resource_id=target_user.id,
        details={"old_role": old_role_name, "new_role": new_role.name},
        user_id=admin_user.id
    )

    return {
        "status": "success",
        "user_id": target_user.id,
        "email": target_user.email,
        "new_role": new_role.name
    }

@router.put("/users/{user_id}/status")
def toggle_user_active_status(
    user_id: str,
    payload: AdminUserStatusToggleRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Activates or deactivates a citizen or analyst user account.
    """
    if target_user_is_self := (user_id == admin_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security Violation: Administrators cannot deactivate their own session account."
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    target_user.is_active = payload.is_active
    db.commit()
    db.refresh(target_user)

    action_label = "ACCOUNT_ACTIVATED" if payload.is_active else "ACCOUNT_DEACTIVATED"
    record_audit_log(
        db=db,
        action=action_label,
        resource_type="USER",
        resource_id=target_user.id,
        details={"is_active": payload.is_active, "target_email": target_user.email},
        user_id=admin_user.id
    )

    return {
        "status": "success",
        "user_id": target_user.id,
        "email": target_user.email,
        "is_active": target_user.is_active
    }

@router.get("/audit-logs", response_model=List[AuditLogListItem])
def list_security_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action name"),
    resource_type: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Queries the append-only security audit log trail.
    """
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action.upper())

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type.upper())

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for l in logs:
        user_email = l.user.email if l.user else None
        results.append(AuditLogListItem(
            id=l.id,
            user_id=l.user_id,
            user_email=user_email,
            action=l.action,
            resource_type=l.resource_type,
            resource_id=l.resource_id,
            details=l.details or {},
            ip_address=l.ip_address,
            created_at=l.created_at
        ))

    return results

@router.get("/telemetry", response_model=SystemHealthTelemetry)
def get_system_telemetry(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Aggregates comprehensive system telemetry, storage vault bytes, and security metrics.
    """
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0

    scams = db.query(func.count(ScamScan.id)).scalar() or 0
    urls = db.query(func.count(UrlScan.id)).scalar() or 0
    images = db.query(func.count(ImageScan.id)).scalar() or 0
    deepfakes = db.query(func.count(DeepfakeScan.id)).scalar() or 0
    privacies = db.query(func.count(PrivacyScan.id)).scalar() or 0
    total_scans = scams + urls + images + deepfakes + privacies

    total_reports = db.query(func.count(Report.id)).scalar() or 0
    verified_threats = db.query(func.count(Report.id)).filter(Report.status == "VERIFIED").scalar() or 0
    active_threats = db.query(func.count(Threat.id)).filter(Threat.is_active == True).scalar() or 0

    total_evidence_files = db.query(func.count(EvidenceFile.id)).scalar() or 0

    # Calculate evidence storage vault bytes on disk
    vault_bytes = 0
    evidence_dir = os.path.join(os.getcwd(), "storage", "evidence")
    if os.path.exists(evidence_dir):
        for root, _, files in os.walk(evidence_dir):
            for f in files:
                fp = os.path.join(root, f)
                vault_bytes += os.path.getsize(fp)

    audit_logs_count = db.query(func.count(AuditLog.id)).scalar() or 0

    # Recent security actions
    recent_events = db.query(func.count(AuditLog.id)).filter(
        AuditLog.action.in_([
            "ADMIN_LOGIN", "FAILED_LOGIN", "BROADCAST_NOTIFICATION",
            "UPDATE_USER_ROLE", "ACCOUNT_DEACTIVATED", "WOMEN_SAFETY_ASSESSMENT"
        ])
    ).scalar() or 0

    return SystemHealthTelemetry(
        database="SQLite (suraksha.db) / PostgreSQL Ready",
        total_users=total_users,
        active_users=active_users,
        total_scans=total_scans,
        total_reports=total_reports,
        verified_threats=verified_threats,
        total_evidence_files=total_evidence_files,
        evidence_vault_bytes=vault_bytes,
        active_threat_indicators=active_threats,
        recent_security_events=recent_events,
        audit_logs_count=audit_logs_count,
        uptime_status="HEALTHY_ONLINE"
    )

@router.get("/threats", response_model=List[AdminThreatItem])
def list_admin_threats(
    active_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    List threat indicators from the SOC threat intelligence table with status filtering.
    """
    query = db.query(Threat)
    if active_only:
        query = query.filter(Threat.is_active == True)

    threats = query.order_by(Threat.created_at.desc()).limit(limit).all()

    return [
        AdminThreatItem(
            id=t.id,
            indicator_type=t.indicator_type,
            indicator_value=t.indicator_value,
            threat_level=t.threat_level,
            description=t.description,
            incident_count=t.incident_count,
            is_active=t.is_active,
            origin_report_id=t.origin_report_id,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in threats
    ]

@router.put("/threats/{threat_id}", response_model=AdminThreatItem)
def update_admin_threat(
    threat_id: str,
    payload: AdminThreatUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Modifies threat severity level, active broadcast status, or description.
    """
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat indicator not found.")

    if payload.threat_level is not None:
        threat.threat_level = payload.threat_level.upper()
    if payload.is_active is not None:
        threat.is_active = payload.is_active
    if payload.description is not None:
        threat.description = payload.description.strip()

    db.commit()
    db.refresh(threat)

    record_audit_log(
        db=db,
        action="UPDATE_THREAT_INDICATOR",
        resource_type="THREAT",
        resource_id=threat.id,
        details={
            "indicator_value": threat.indicator_value,
            "threat_level": threat.threat_level,
            "is_active": threat.is_active
        },
        user_id=admin_user.id
    )

    return AdminThreatItem(
        id=threat.id,
        indicator_type=threat.indicator_type,
        indicator_value=threat.indicator_value,
        threat_level=threat.threat_level,
        description=threat.description,
        incident_count=threat.incident_count,
        is_active=threat.is_active,
        origin_report_id=threat.origin_report_id,
        created_at=threat.created_at,
        updated_at=threat.updated_at
    )

@router.post("/threats/{threat_id}/broadcast")
def broadcast_threat_alert(
    threat_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Broadcasts a high-priority verified threat alert to all active citizens.
    """
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat indicator not found.")

    count = notification_service.broadcast_notification(
        db=db,
        title=f"URGENT: Verified {threat.indicator_type} Threat Alert",
        message=f"High risk indicator identified: {threat.indicator_value}. {threat.description}",
        category="SECURITY_ALERT",
        action_url="/community-reports?tab=alerts"
    )

    record_audit_log(
        db=db,
        action="BROADCAST_THREAT_ALERT",
        resource_type="THREAT",
        resource_id=threat.id,
        details={"indicator_value": threat.indicator_value, "recipients": count},
        user_id=admin_user.id
    )

    return {
        "status": "success",
        "threat_id": threat.id,
        "indicator_value": threat.indicator_value,
        "recipient_count": count
    }

