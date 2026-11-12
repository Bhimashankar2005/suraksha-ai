import pytest
import secrets
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.safety_education import Notification
from backend.app.core.security import get_password_hash
from backend.app.services.notification_service import notification_service
from backend.app.api.endpoints.notifications import (
    get_user_notifications,
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    delete_user_notification,
    broadcast_admin_notification
)
from backend.app.schemas.notification import BroadcastNotificationRequest
from backend.app.services.report_service import create_community_report, review_community_report
from backend.app.schemas.report import ReportCreate, ReportReviewAction

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def test_user(db):
    user_role = db.query(Role).filter(Role.name == "USER").first()
    email = f"notif_user_{secrets.token_hex(4)}@suraksha.gov.in"
    user = User(
        email=email,
        password_hash=get_password_hash("Suraksha@NotifPass2026"),
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

@pytest.fixture(scope="module")
def admin_user(db):
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    email = f"notif_admin_{secrets.token_hex(4)}@suraksha.gov.in"
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

def test_create_and_get_user_notifications(test_user, db):
    n1 = notification_service.create_notification(
        db=db,
        user_id=test_user.id,
        title="Security Alert: Unknown Device",
        message="A new login was recorded from Chrome on Windows.",
        category="SECURITY_ALERT"
    )
    assert n1.id is not None
    assert n1.is_read is False

    res = get_user_notifications(
        unread_only=False,
        limit=10,
        skip=0,
        db=db,
        current_user=test_user
    )
    assert res.total >= 1
    assert any(item.id == n1.id for item in res.items)

def test_get_unread_notification_count(test_user, db):
    count_res = get_unread_notification_count(db=db, current_user=test_user)
    assert count_res.unread_count >= 1

def test_mark_notification_as_read(test_user, db):
    n = notification_service.create_notification(
        db=db,
        user_id=test_user.id,
        title="Phishing Warning",
        message="A new SBI lookalike domain was reported in your region.",
        category="SECURITY_ALERT"
    )

    read_res = mark_notification_as_read(
        notification_id=n.id,
        db=db,
        current_user=test_user
    )
    assert read_res.id == n.id
    assert read_res.is_read is True

def test_mark_all_notifications_as_read(test_user, db):
    # Create two unread notifications
    notification_service.create_notification(db=db, user_id=test_user.id, title="Alert 1", message="Msg 1")
    notification_service.create_notification(db=db, user_id=test_user.id, title="Alert 2", message="Msg 2")

    res = mark_all_notifications_as_read(db=db, current_user=test_user)
    assert res["marked_read_count"] >= 2

    # Unread count should now be 0
    count_res = get_unread_notification_count(db=db, current_user=test_user)
    assert count_res.unread_count == 0

def test_delete_notification(test_user, db):
    n = notification_service.create_notification(
        db=db,
        user_id=test_user.id,
        title="Temporary Alert",
        message="Will be deleted"
    )

    del_res = delete_user_notification(
        notification_id=n.id,
        db=db,
        current_user=test_user
    )
    assert del_res["status"] == "success"

    # Verify deleted
    db_check = db.query(Notification).filter(Notification.id == n.id).first()
    assert db_check is None

def test_admin_broadcast_notification(admin_user, test_user, db):
    payload = BroadcastNotificationRequest(
        title="CRITICAL: New Electricity Cutoff Scam Wave",
        message="Fraudsters are sending urgent SMS messages claiming power cutoff at 9:30 PM. Do not call numbers in SMS.",
        category="SECURITY_ALERT",
        action_url="/scam-detection"
    )

    broadcast_res = broadcast_admin_notification(
        payload=payload,
        db=db,
        admin_user=admin_user
    )
    assert broadcast_res.recipient_count >= 2
    assert broadcast_res.status == "broadcasted"

    # User should have received the notification
    user_notifs = notification_service.get_user_notifications(db=db, user_id=test_user.id, limit=5)
    assert any("Electricity Cutoff Scam" in item.title for item in user_notifs)

def test_report_review_triggers_notification(test_user, admin_user, db):
    # 1. Citizen submits report
    phone_val = f"9822{secrets.randbelow(900000) + 100000}"
    report_in = ReportCreate(
        threat_type="PHONE",
        target_value=phone_val,
        description="Electricity cutoff scam caller demanding Google Pay",
        is_anonymous=False
    )
    report = create_community_report(db=db, report_in=report_in, user_id=test_user.id)
    assert report.user_id == test_user.id

    # 2. Admin reviews and verifies report
    review_in = ReportReviewAction(
        action="APPROVE_VERIFY",
        internal_notes="Confirmed scam number from state electricity helpline",
        public_notes="Verified electricity extortion number active in Bengaluru",
        publish_as_public_alert=True,
        threat_level="CRITICAL"
    )
    reviewed = review_community_report(
        db=db,
        report_id=report.id,
        admin_id=admin_user.id,
        review_in=review_in
    )
    assert reviewed.status == "VERIFIED"

    # 3. Check citizen received automated notification
    user_notifs = notification_service.get_user_notifications(db=db, user_id=test_user.id, limit=5)
    matched_notif = next((n for n in user_notifs if report.report_code in n.title), None)
    assert matched_notif is not None
    assert "VERIFIED" in matched_notif.message

