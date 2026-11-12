import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.scans import ScamScan
from backend.app.models.reports import Report
from backend.app.ml.scam_classifier import scam_classifier
from backend.app.services.scam_service import (
    process_message_scan, get_scam_history, record_scan_feedback, convert_scan_to_report
)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_heuristic_rules_bank_kyc():
    """Verify bank KYC suspension triggers CRITICAL risk and appropriate category."""
    msg = "Dear customer your SBI account will be blocked today update pan card immediately click http://bit.ly/sbi-pan"
    res = scam_classifier.analyze_message(msg)
    assert res.risk_score >= 70
    assert res.risk_level in ["HIGH", "CRITICAL"]
    assert res.scam_category == "BANK_KYC"
    assert len(res.matched_indicators) >= 1
    assert any("KYC" in ind["category"] for ind in res.matched_indicators)
    assert len(res.recommendations) >= 2

def test_heuristic_rules_electricity_cutoff():
    """Verify urgent power cutoff threat triggers high/critical risk."""
    msg = "Dear consumer tonight 9:30 pm electricity power will be disconnected from power office contact officer at 9876543210"
    res = scam_classifier.analyze_message(msg)
    assert res.risk_score >= 65
    assert res.risk_level in ["HIGH", "CRITICAL"]
    assert res.scam_category in ["ELECTRICITY_BILL", "URGENCY"]

def test_heuristic_rules_upi_pin_demand():
    """Verify request to enter UPI PIN to receive cashback triggers high/critical risk."""
    msg = "To receive cashback of Rs 2500 enter your UPI PIN on PhonePe app now"
    res = scam_classifier.analyze_message(msg)
    assert res.risk_score >= 65
    assert res.risk_level in ["HIGH", "CRITICAL"]
    assert res.scam_category == "UPI_FRAUD"

def test_heuristic_rules_lottery_prize():
    """Verify fake lottery prizes trigger scam alerts."""
    msg = "Congratulations you have won 25 lakh in KBC whatsapp lucky draw contact officer"
    res = scam_classifier.analyze_message(msg)
    assert res.risk_score >= 60
    assert res.scam_category == "LOTTERY"

def test_legitimate_transactional_message():
    """Verify normal transactional notifications are classified as LOW risk."""
    msg = "Dear customer your account was debited by Rs 250 for grocery at metro mart. Avl bal Rs 14000."
    res = scam_classifier.analyze_message(msg)
    assert res.risk_score < 30
    assert res.risk_level == "LOW"
    assert res.scam_category == "LEGITIMATE"

def test_model_evaluation_metrics():
    """Verify model evaluation outputs precision, recall, f1, and accuracy above 0.8."""
    metrics = scam_classifier.evaluate_test_dataset()
    assert metrics["accuracy"] >= 0.8
    assert metrics["precision"] >= 0.7
    assert metrics["recall"] >= 0.8
    assert metrics["f1_score"] >= 0.8
    assert metrics["test_sample_count"] == 10

def test_process_message_scan_persistence(db):
    """Verify message scan is persisted in the database and returns a valid ID."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    uid = user.id if user else None

    msg = "Your Jio SIM verification pending. SIM deactivated within 24 hours. Call 9811223344"
    res = process_message_scan(content=msg, user_id=uid, db=db)

    assert res.id is not None
    assert res.risk_score >= 50
    assert "SIM" in res.content_snippet or "verification" in res.content_snippet

    # Verify directly from database
    db_scan = db.query(ScamScan).filter(ScamScan.id == res.id).first()
    assert db_scan is not None
    assert db_scan.risk_score == res.risk_score

def test_user_scam_history(db):
    """Verify scan history retrieval for authenticated users."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    assert user is not None

    history = get_scam_history(user_id=user.id, db=db)
    assert len(history) >= 1
    assert history[0].id is not None

def test_convert_scan_to_report(db):
    """Verify scan to community threat reporting workflow generates SUR-REP- code."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    uid = user.id if user else None

    # Get recent scan
    scan = db.query(ScamScan).order_by(ScamScan.created_at.desc()).first()
    assert scan is not None

    rep_res = convert_scan_to_report(
        user_id=uid,
        scan_id=scan.id,
        target_value="+919876543210",
        custom_description="Suspect calling about bank block",
        region="Karnataka",
        db=db
    )
    assert rep_res.report_code.startswith("SUR-REP-")
    assert rep_res.status == "PENDING"

    # Verify report in database
    db_rep = db.query(Report).filter(Report.id == rep_res.report_id).first()
    assert db_rep is not None
    assert db_rep.report_code == rep_res.report_code
    assert db_rep.status == "PENDING"

def test_scam_feedback_recording(db):
    """Verify user feedback is recorded in database."""
    scan = db.query(ScamScan).order_by(ScamScan.created_at.desc()).first()
    assert scan is not None

    fb = record_scan_feedback(
        user_id=None,
        scan_id=scan.id,
        rating=5,
        feedback_text="Accurate detection for the fake KYC message!",
        db=db
    )
    assert fb.id is not None
    assert fb.rating == 5
