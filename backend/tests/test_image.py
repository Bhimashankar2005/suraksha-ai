import pytest
import io
import os
from PIL import Image
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.scans import ImageScan
from backend.app.models.reports import Report
from backend.app.ml.image_analyzer import validate_and_hash_image, analyze_screenshot_content
from backend.app.services.image_service import (
    process_image_upload_and_scan, get_user_image_history, convert_image_scan_to_report
)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def create_sample_png_bytes(width=200, height=100, color="blue") -> bytes:
    """Helper to generate a valid in-memory PNG image."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_validate_image_valid_png():
    """Verify PNG format magic bytes, dimensions, and cryptographic hashing."""
    img_bytes = create_sample_png_bytes(300, 150)
    is_valid, err, meta = validate_and_hash_image(img_bytes, "test_screenshot.png")
    assert is_valid is True
    assert err is None
    assert meta["mime_type"] == "image/png"
    assert meta["dimensions"] == (300, 150)
    assert len(meta["file_hash"]) == 64

def test_validate_image_invalid_magic_bytes():
    """Verify non-image files are rejected with clear error messages."""
    fake_bytes = b"NOT_AN_IMAGE_FILE_JUST_PLAIN_TEXT"
    is_valid, err, meta = validate_and_hash_image(fake_bytes, "fake.jpg")
    assert is_valid is False
    assert "Unsupported file format" in err

def test_analyze_screenshot_fake_payment_receipt():
    """Verify fake payment confirmation screenshot text triggers detection and mandatory warning."""
    img_bytes = create_sample_png_bytes()
    fake_payment_text = (
        "Payment Successful. Rs 45,000 sent to Ramesh Kumar. "
        "Transferred from HDFC Bank. UTR: 928491028401. Paid Successfully."
    )
    res = analyze_screenshot_content(img_bytes, "payment_proof.png", fake_payment_text)
    assert res.detected_entities["is_payment_screenshot"] is True
    assert len(res.detected_entities["amounts_mentioned"]) >= 1
    assert any(ind["rule_id"] == "PAYMENT_CONFIRMATION_PATTERN" for ind in res.matched_indicators)
    # Verify mandatory safety disclaimer is present
    assert any("A payment screenshot NEVER proves money was received" in rec for rec in res.recommendations)

def test_analyze_screenshot_qr_receive_fraud():
    """Verify QR code claiming to receive money is flagged as CRITICAL risk."""
    img_bytes = create_sample_png_bytes()
    qr_fraud_text = "Scan QR code to credit cashback of Rs 2500 in your bank account now"
    res = analyze_screenshot_content(img_bytes, "qr_claim.png", qr_fraud_text)
    assert res.risk_score >= 60
    assert any(ind["rule_id"] in ["UPI_RECEIVE_DECEPTION_IMAGE", "UPI_RECEIVE_FRAUD"] for ind in res.matched_indicators)

def test_process_image_upload_and_scan_persistence(db):
    """Verify image scan is saved in database and file stored on disk."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    uid = user.id if user else None

    img_bytes = create_sample_png_bytes(250, 120, "green")
    ocr_text = "Dear customer your PNB debit card blocked today update KYC at http://pnb-verify.xyz"

    res = process_image_upload_and_scan(
        file_bytes=img_bytes,
        file_name="pnb_sms_screenshot.png",
        user_id=uid,
        ocr_override=ocr_text,
        db=db
    )

    assert res.id is not None
    assert res.file_name == "pnb_sms_screenshot.png"
    assert res.risk_score >= 60

    # Verify directly from database
    db_scan = db.query(ImageScan).filter(ImageScan.id == res.id).first()
    assert db_scan is not None
    assert db_scan.file_hash == res.file_hash

def test_get_user_image_history(db):
    """Verify scan history retrieval for authenticated users."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    assert user is not None

    history = get_user_image_history(user_id=user.id, db=db)
    assert len(history) >= 1
    assert history[0].file_hash is not None

def test_convert_image_scan_to_report(db):
    """Verify image scan escalates into a community threat report."""
    user = db.query(User).filter(User.email == "citizen.test@suraksha.gov.in").first()
    uid = user.id if user else None

    scan = db.query(ImageScan).order_by(ImageScan.created_at.desc()).first()
    assert scan is not None

    rep_res = convert_image_scan_to_report(
        user_id=uid,
        scan_id=scan.id,
        target_value=scan.file_name,
        custom_description="Fake payment receipt sent over WhatsApp",
        region="Delhi",
        db=db
    )
    assert rep_res.report_code.startswith("SUR-REP-")
    assert rep_res.status == "PENDING"

    db_rep = db.query(Report).filter(Report.id == rep_res.report_id).first()
    assert db_rep is not None
    assert db_rep.threat_type == "SCREENSHOT"

