import pytest
import uuid
import secrets
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.reports import Report, Threat, ReportReview
from backend.app.schemas.report import ReportCreate, ReportReviewAction
from backend.app.services.report_service import (
    normalize_target_value,
    generate_unique_report_code,
    detect_duplicate,
    create_community_report,
    review_community_report,
    get_threat_intelligence_stats
)
from backend.app.api.endpoints.community_reports import (
    submit_threat_report,
    track_report_status,
    get_user_reports,
    get_verified_threat_alerts,
    get_threat_stats,
    get_admin_report_queue,
    review_report
)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_user(db: Session):
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    return user

@pytest.fixture
def admin_user(db: Session):
    admin = db.query(User).filter(User.email == "admin@suraksha.gov.in").first()
    return admin

def test_normalize_target_value():
    """Verify normalization of phone numbers, URLs, and indicators."""
    assert normalize_target_value("PHONE", "+91 98765 43210") == "9876543210"
    assert normalize_target_value("PHONE", "09876543210") == "9876543210"
    assert normalize_target_value("PHONE", "9876543210") == "9876543210"

    assert normalize_target_value("URL", "https://www.sbi-kyc-update.xyz/") == "sbi-kyc-update.xyz"
    assert normalize_target_value("URL", "http://sbi-kyc-update.xyz") == "sbi-kyc-update.xyz"

def test_unique_report_code_generation(db: Session):
    """Verify generated report code format SUR-REP-XXXXXX."""
    code = generate_unique_report_code(db)
    assert code.startswith("SUR-REP-")
    assert len(code) == 14

def test_submit_threat_report_anonymous(db: Session):
    """Verify anonymous threat report submission."""
    unique_phone = f"+91 9811{secrets.randbelow(900000) + 100000}"
    report_in = ReportCreate(
        threat_type="PHONE",
        target_value=unique_phone,
        description="Scammer called claiming to be Mumbai Police for digital arrest parcel.",
        region="Karnataka",
        is_anonymous=True
    )
    res = submit_threat_report(report_in, db=db, current_user=None)
    assert res.report_code.startswith("SUR-REP-")
    assert res.threat_type == "PHONE"
    assert res.status == "PENDING"
    assert res.is_duplicate is False

    # Check in DB that user_id is None for anonymous reports
    db_report = db.query(Report).filter(Report.id == res.id).first()
    assert db_report.user_id is None

def test_submit_threat_report_authenticated(db: Session, test_user: User):
    """Verify authenticated citizen threat report submission."""
    unique_url = f"https://www.fake-{secrets.token_hex(4)}-pay.live"
    report_in = ReportCreate(
        threat_type="URL",
        target_value=unique_url,
        description="Phishing website sent via SMS threatening power cut tonight.",
        region="Maharashtra",
        is_anonymous=False
    )
    res = submit_threat_report(report_in, db=db, current_user=test_user)
    assert res.report_code.startswith("SUR-REP-")
    assert res.threat_type == "URL"

    db_report = db.query(Report).filter(Report.id == res.id).first()
    assert db_report.user_id == test_user.id

def test_duplicate_threat_report_detection(db: Session):
    """Verify duplicate detection for identical scam phone numbers."""
    phone = f"9822{secrets.randbelow(900000) + 100000}"
    # First submission
    rep1 = ReportCreate(
        threat_type="PHONE",
        target_value=phone,
        description="Electricity cutoff scam caller.",
        is_anonymous=True
    )
    res1 = submit_threat_report(rep1, db=db, current_user=None)

    # Second submission with formatting variance (+91)
    rep2 = ReportCreate(
        threat_type="PHONE",
        target_value=f"+91 {phone}",
        description="Same scam caller claiming electricity disconnect.",
        is_anonymous=True
    )
    res2 = submit_threat_report(rep2, db=db, current_user=None)
    assert res2.is_duplicate is True

    db_rep2 = db.query(Report).filter(Report.id == res2.id).first()
    assert db_rep2.duplicate_of_id == res1.id

def test_track_report_status_valid(db: Session):
    """Verify public report tracking by unique code."""
    unique_msg = f"Dear customer {secrets.token_hex(4)} your account will be suspended tonight click link"
    report_in = ReportCreate(
        threat_type="MESSAGE",
        target_value=unique_msg,
        description="Fake bank message.",
        is_anonymous=True
    )
    res = submit_threat_report(report_in, db=db, current_user=None)

    tracking = track_report_status(res.report_code, db=db)
    assert tracking.report_code == res.report_code
    assert tracking.status == "PENDING"
    assert tracking.threat_type == "MESSAGE"

def test_track_report_status_invalid_code(db: Session):
    """Verify 404 on invalid tracking code."""
    with pytest.raises(HTTPException) as exc_info:
        track_report_status("SUR-REP-NONEXISTENT", db=db)
    assert exc_info.value.status_code == 404

def test_get_user_reports(db: Session, test_user: User):
    """Verify retrieval of logged-in user's report history."""
    my_reports = get_user_reports(db=db, current_user=test_user)
    assert isinstance(my_reports, list)
    assert len(my_reports) >= 1
    for r in my_reports:
        db_r = db.query(Report).filter(Report.id == r.id).first()
        assert db_r.user_id == test_user.id

def test_admin_review_queue(db: Session, admin_user: User):
    """Verify admin moderation queue returns pending reports."""
    queue = get_admin_report_queue(status_filter="PENDING", db=db, admin_user=admin_user)
    assert isinstance(queue, list)
    assert len(queue) >= 1
    for item in queue:
        assert item.status == "PENDING"

def test_admin_approve_and_publish_threat(db: Session, admin_user: User):
    """Verify admin review verification and publishing to public Threat intelligence."""
    unique_phone = f"9899{secrets.randbelow(900000) + 100000}"
    rep_in = ReportCreate(
        threat_type="PHONE",
        target_value=unique_phone,
        description="Confirmed digital arrest extortionist posing as Mumbai Police officer.",
        region="Delhi",
        is_anonymous=True
    )
    created = submit_threat_report(rep_in, db=db, current_user=None)

    review_action = ReportReviewAction(
        action="APPROVE_VERIFY",
        internal_notes="Verified against cyber crime blacklist. Valid threat indicator.",
        public_notes="Confirmed scam number used in digital arrest impersonation.",
        publish_as_public_alert=True,
        threat_level="CRITICAL"
    )

    reviewed = review_report(created.id, review_action, db=db, admin_user=admin_user)
    assert reviewed.status == "VERIFIED"
    assert reviewed.is_public_alert is True

    # Verify public threat record was created
    threat = db.query(Threat).filter(Threat.origin_report_id == created.id).first()
    assert threat is not None
    assert threat.threat_level == "CRITICAL"
    assert threat.is_active is True

def test_public_threat_alerts_feed(db: Session):
    """Verify public threat alerts feed returns verified active indicators."""
    alerts = get_verified_threat_alerts(limit=10, db=db)
    assert isinstance(alerts, list)
    assert len(alerts) >= 1
    assert any(a.threat_level in ["MEDIUM", "HIGH", "CRITICAL"] for a in alerts)

def test_threat_intelligence_stats(db: Session):
    """Verify database aggregated metrics."""
    stats = get_threat_stats(db=db)
    assert stats.total_reports >= 1
    assert stats.verified_threats >= 1
    assert "PHONE" in stats.by_category or "URL" in stats.by_category
    assert stats.active_threat_indicators >= 1
