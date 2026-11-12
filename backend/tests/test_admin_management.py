import pytest
import secrets
from fastapi import HTTPException
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.reports import Threat
from backend.app.core.security import get_password_hash
from backend.app.api.endpoints.admin_management import (
    list_system_users,
    update_user_role,
    toggle_user_active_status,
    list_security_audit_logs,
    get_system_telemetry,
    list_admin_threats,
    update_admin_threat,
    broadcast_threat_alert
)
from backend.app.schemas.admin import (
    AdminUserUpdateRoleRequest,
    AdminUserStatusToggleRequest,
    AdminThreatUpdateRequest
)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def admin_user(db):
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    email = f"lead_admin_{secrets.token_hex(4)}@suraksha.gov.in"
    admin = User(
        email=email,
        password_hash=get_password_hash("Suraksha@AdminPass2026"),
        role_id=admin_role.id,
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    yield admin

    # Teardown
    db.delete(admin)
    db.commit()

@pytest.fixture(scope="module")
def sample_citizen(db):
    user_role = db.query(Role).filter(Role.name == "USER").first()
    email = f"citizen_{secrets.token_hex(4)}@suraksha.gov.in"
    user = User(
        email=email,
        password_hash=get_password_hash("Suraksha@CitizenPass2026"),
        role_id=user_role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    yield user

    # Teardown
    db.delete(user)
    db.commit()

def test_list_system_users(admin_user, sample_citizen, db):
    users = list_system_users(
        search=None,
        role=None,
        is_active=None,
        limit=20,
        skip=0,
        db=db,
        admin_user=admin_user
    )
    assert len(users) >= 2
    emails = [u.email for u in users]
    assert admin_user.email in emails
    assert sample_citizen.email in emails

def test_update_user_role_success(admin_user, sample_citizen, db):
    res = update_user_role(
        user_id=sample_citizen.id,
        payload=AdminUserUpdateRoleRequest(role_name="COMMUNITY_MODERATOR"),
        db=db,
        admin_user=admin_user
    )
    assert res["status"] == "success"
    assert res["new_role"] == "COMMUNITY_MODERATOR"

    # Reset back to USER
    reset_res = update_user_role(
        user_id=sample_citizen.id,
        payload=AdminUserUpdateRoleRequest(role_name="USER"),
        db=db,
        admin_user=admin_user
    )
    assert reset_res["new_role"] == "USER"

def test_toggle_user_status_safeguard_self(admin_user, db):
    # Admin cannot deactivate their own account
    with pytest.raises(HTTPException) as exc:
        toggle_user_active_status(
            user_id=admin_user.id,
            payload=AdminUserStatusToggleRequest(is_active=False),
            db=db,
            admin_user=admin_user
        )
    assert exc.value.status_code == 400
    assert "cannot deactivate their own session" in exc.value.detail

def test_toggle_user_status_other_user(admin_user, sample_citizen, db):
    # Deactivate citizen
    deact = toggle_user_active_status(
        user_id=sample_citizen.id,
        payload=AdminUserStatusToggleRequest(is_active=False),
        db=db,
        admin_user=admin_user
    )
    assert deact["is_active"] is False

    # Reactivate citizen
    react = toggle_user_active_status(
        user_id=sample_citizen.id,
        payload=AdminUserStatusToggleRequest(is_active=True),
        db=db,
        admin_user=admin_user
    )
    assert react["is_active"] is True

def test_list_security_audit_logs(admin_user, db):
    logs = list_security_audit_logs(
        action=None,
        resource_type=None,
        user_id=None,
        limit=20,
        skip=0,
        db=db,
        admin_user=admin_user
    )
    assert isinstance(logs, list)
    assert len(logs) >= 1
    actions = [l.action for l in logs]
    assert any(a in actions for a in ["ACCOUNT_ACTIVATED", "ACCOUNT_DEACTIVATED", "UPDATE_USER_ROLE", "ADMIN_ACTION"])

def test_get_system_telemetry(admin_user, db):
    telemetry = get_system_telemetry(db=db, admin_user=admin_user)
    assert telemetry.total_users >= 2
    assert telemetry.active_users >= 1
    assert telemetry.uptime_status == "HEALTHY_ONLINE"
    assert telemetry.audit_logs_count >= 1

def test_admin_threats_crud_and_broadcast(admin_user, db):
    # 1. Create a threat indicator directly
    test_val = f"fake-bank-login-{secrets.token_hex(3)}.xyz"
    threat = Threat(
        indicator_type="URL",
        indicator_value=test_val,
        threat_level="HIGH",
        description="Active phishing portal stealing netbanking credentials",
        verified_by_admin_id=admin_user.id,
        incident_count=3,
        is_active=True
    )
    db.add(threat)
    db.commit()
    db.refresh(threat)

    # 2. List threats
    threats = list_admin_threats(active_only=True, limit=50, db=db, admin_user=admin_user)
    assert any(t.id == threat.id for t in threats)

    # 3. Update threat level to CRITICAL
    updated = update_admin_threat(
        threat_id=threat.id,
        payload=AdminThreatUpdateRequest(threat_level="CRITICAL", description="Escalated critical bank phishing kit"),
        db=db,
        admin_user=admin_user
    )
    assert updated.threat_level == "CRITICAL"

    # 4. Broadcast threat alert
    b_res = broadcast_threat_alert(
        threat_id=threat.id,
        db=db,
        admin_user=admin_user
    )
    assert b_res["status"] == "success"
    assert b_res["recipient_count"] >= 1

    # Cleanup
    db.delete(threat)
    db.commit()

