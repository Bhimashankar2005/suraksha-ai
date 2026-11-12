import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.scans import ScamScan, UrlScan
from backend.app.models.reports import Report
from backend.app.api.endpoints.dashboard import get_user_dashboard, get_admin_dashboard

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_user_dashboard_real_aggregates(db):
    """Test user dashboard returns real database statistics and recent activity."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    assert user is not None

    # Insert a test scan for this user
    test_scan = ScamScan(
        user_id=user.id,
        content_snippet="Urgent KYC verification required immediately",
        risk_score=85,
        risk_level="CRITICAL",
        scam_category="BANK_KYC",
        indicators=["urgency", "kyc_suspension"],
        recommendations=["Never share OTP", "Report to 1930"]
    )
    db.add(test_scan)
    db.commit()

    dashboard_data = get_user_dashboard(current_user=user, db=db)
    assert dashboard_data.total_scans >= 1
    assert dashboard_data.suspicious_detections >= 1
    assert len(dashboard_data.recent_activity) >= 1
    assert dashboard_data.recent_activity[0].risk_level == "CRITICAL"

def test_admin_dashboard_real_aggregates(db):
    """Test admin dashboard returns real system-wide metrics and threat breakdown."""
    admin = db.query(User).filter(User.email == "admin@suraksha.gov.in").first()
    assert admin is not None

    admin_data = get_admin_dashboard(admin_user=admin, db=db)
    assert admin_data.total_users >= 2
    assert admin_data.active_users >= 2
    assert admin_data.total_scans >= 1
    assert isinstance(admin_data.threat_categories, dict)
    assert len(admin_data.recent_admin_actions) >= 1

