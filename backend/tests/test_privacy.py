import pytest
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.scans import PrivacyScan
from backend.app.ml.privacy_scanner import (
    privacy_scanner,
    validate_verhoeff,
    validate_luhn,
    VERHOEFF_D,
    VERHOEFF_P
)
from backend.app.schemas.privacy import PrivacyScanRequest
from backend.app.api.endpoints.privacy import (
    scan_text_privacy,
    get_privacy_scan_history,
    delete_privacy_scan
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

def generate_valid_aadhaar_sample(prefix11: str = "23456789012") -> str:
    """Generates a valid 12-digit Aadhaar number with correct Verhoeff check digit."""
    c = 0
    inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
    digits = [int(x) for x in prefix11]
    for i, digit in enumerate(reversed(digits)):
        c = VERHOEFF_D[c][VERHOEFF_P[(i + 1) % 8][digit]]
    check_digit = inv[c]
    return f"{prefix11}{check_digit}"

def test_verhoeff_checksum_validation():
    """Verify Verhoeff check digit validation for Aadhaar numbers."""
    valid_num = generate_valid_aadhaar_sample("34567890123")
    assert validate_verhoeff(valid_num) is True

    # Tampered last digit
    last_d = int(valid_num[-1])
    tampered = valid_num[:-1] + str((last_d + 1) % 10)
    assert validate_verhoeff(tampered) is False

def test_luhn_checksum_validation():
    """Verify Luhn algorithm validation for 16-digit cards."""
    # Known Luhn valid number
    valid_card = "4532015112830366"
    assert validate_luhn(valid_card) is True

    # Tampered card
    tampered_card = "4532015112830367"
    assert validate_luhn(tampered_card) is False

def test_detect_aadhaar_redaction():
    """Verify Aadhaar detection and masking (XXXX-XXXX-1234)."""
    valid_aadhaar = generate_valid_aadhaar_sample("28475938102")
    formatted = f"{valid_aadhaar[:4]}-{valid_aadhaar[4:8]}-{valid_aadhaar[8:]}"
    sample_text = f"My Aadhaar card number is {formatted} for KYC verification."

    res = privacy_scanner.scan_and_redact(sample_text)
    assert len(res["detected_entities"]) == 1
    assert res["detected_entities"][0]["type"] == "AADHAAR"
    assert res["detected_entities"][0]["is_checksum_valid"] is True
    assert f"XXXX-XXXX-{valid_aadhaar[-4:]}" in res["sanitized_text"]
    assert valid_aadhaar[:8] not in res["sanitized_text"]

def test_detect_pan_redaction():
    """Verify PAN detection and masking (XXXXX1234X)."""
    pan = "ABCDE1234F"
    text = f"Kindly note my PAN is {pan} for tax exemption."

    res = privacy_scanner.scan_and_redact(text)
    assert len(res["detected_entities"]) == 1
    assert res["detected_entities"][0]["type"] == "PAN"
    assert "XXXXX1234F" in res["sanitized_text"]
    assert "ABCDE" not in res["sanitized_text"]

def test_detect_phone_redaction():
    """Verify Indian phone detection and masking."""
    phone = "+91 98765 43210"
    text = f"Please contact citizen at {phone} urgently."

    res = privacy_scanner.scan_and_redact(text)
    assert len(res["detected_entities"]) == 1
    assert res["detected_entities"][0]["type"] == "PHONE_NUMBER"
    assert "+91 XXXXX 43210" in res["sanitized_text"]

def test_detect_email_redaction():
    """Verify email address masking."""
    email = "rajesh.kumar@example.com"
    text = f"Send bank statement to {email}."

    res = privacy_scanner.scan_and_redact(text)
    assert len(res["detected_entities"]) == 1
    assert res["detected_entities"][0]["type"] == "EMAIL"
    assert "r***r@example.com" in res["sanitized_text"]
    assert "rajesh.kumar" not in res["sanitized_text"]

def test_detect_upi_vpa_redaction():
    """Verify UPI handle detection and masking."""
    upi = "securepay@okhdfcbank"
    text = f"Transfer funds to {upi} via Google Pay."

    res = privacy_scanner.scan_and_redact(text)
    assert len(res["detected_entities"]) == 1
    assert res["detected_entities"][0]["type"] == "UPI_ID"
    assert "s***y@okhdfcbank" in res["sanitized_text"]

def test_risk_score_and_severity_levels():
    """Verify combined privacy risk scoring and severity bands."""
    # Text with multiple critical credentials: Aadhaar + PAN + Phone
    valid_aadhaar = generate_valid_aadhaar_sample("29876543210")
    text = f"Aadhaar: {valid_aadhaar}, PAN: BZRPK8974L, Mobile: 9811223344"
    res = privacy_scanner.scan_and_redact(text)

    # 35 (Aadhaar) + 30 (PAN) + 15 (Phone) = 80 -> HIGH
    assert res["risk_score"] >= 80
    assert res["risk_level"] in ["HIGH", "CRITICAL"]
    assert any("mAadhaar" in rec for rec in res["recommendations"])
    assert any("PAN" in rec for rec in res["recommendations"])

def test_api_scan_text_guest(db: Session):
    """Verify guest in-memory scanning does not create database rows."""
    req = PrivacyScanRequest(text="Contact me at support@suraksha.gov.in or 9876543210")
    res = scan_text_privacy(req, db=db, current_user=None)
    assert res.scan_id is None
    assert len(res.detected_entities) >= 1
    assert "sanitized_text" in res.model_dump()

def test_api_scan_text_authenticated(db: Session, test_user: User):
    """Verify authenticated scan records sanitized preview to privacy_scans table."""
    req = PrivacyScanRequest(text="Employee PAN: ABCDE5678G, Phone: 9845012345")
    res = scan_text_privacy(req, db=db, current_user=test_user)
    assert res.scan_id is not None
    assert res.risk_score >= 45

    # Check database
    db_scan = db.query(PrivacyScan).filter(PrivacyScan.id == res.scan_id).first()
    assert db_scan is not None
    assert db_scan.user_id == test_user.id
    # Assert raw PAN is NOT stored unredacted in database
    assert "ABCDE" not in db_scan.redacted_preview

def test_api_privacy_history(db: Session, test_user: User):
    """Verify retrieval of user's past privacy scan history."""
    history = get_privacy_scan_history(db=db, current_user=test_user)
    assert isinstance(history, list)
    assert len(history) >= 1
    assert any(h.risk_score > 0 for h in history)

def test_api_delete_privacy_history(db: Session, test_user: User):
    """Verify deleting a privacy scan record."""
    req = PrivacyScanRequest(text="Temporary scan: phone 9898989898")
    scan_res = scan_text_privacy(req, db=db, current_user=test_user)

    del_res = delete_privacy_scan(scan_res.scan_id, db=db, current_user=test_user)
    assert del_res["status"] == "deleted"

    # Verify deleted
    db_check = db.query(PrivacyScan).filter(PrivacyScan.id == scan_res.scan_id).first()
    assert db_check is None

