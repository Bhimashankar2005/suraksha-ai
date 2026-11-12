import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.safety_education import TrustedContact
from backend.app.ml.demographic_safety_engine import demographic_safety_engine
from backend.app.schemas.demographics import (
    HarassmentAnalysisRequest,
    SeniorSafetyRequest,
    TrustedContactCreate,
    TrustedContactAlertRequest
)
from backend.app.api.endpoints.demographics import (
    analyze_women_safety_threat,
    explain_senior_scam,
    get_trusted_contacts,
    add_trusted_contact,
    delete_trusted_contact,
    generate_contact_alert
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

def test_women_safety_extortion_threat_critical():
    """Verify detection of image blackmail and extortion as CRITICAL_EMERGENCY."""
    threat_text = "Pay 50,000 in crypto or I will leak your private photos to your family and college friends."
    result = demographic_safety_engine.analyze_harassment(threat_text)
    assert result["threat_severity"] == "CRITICAL_EMERGENCY"
    assert result["risk_score"] >= 55
    assert any("Blackmail" in p for p in result["detected_patterns"])
    # Assert Women Helpline 1091 and NCW 7827170170 are included
    numbers = [h["number"] for h in result["emergency_helplines"]]
    assert any("1091" in n for n in numbers)
    assert any("7827170170" in n for n in numbers)
    assert any("DO NOT PAY" in act for act in result["immediate_actions"])

def test_women_safety_stalking_threat():
    """Verify detection of cyberstalking and physical threats."""
    stalking_text = "I know where you live, I am following you outside your college, answer my call or die."
    result = demographic_safety_engine.analyze_harassment(stalking_text)
    assert result["threat_severity"] in ["HIGH", "CRITICAL_EMERGENCY"]
    assert any("Cyberstalking" in p for p in result["detected_patterns"])

def test_women_safety_impersonation_defamation():
    """Verify detection of fake profiles and online defamation."""
    text = "Created a fake profile using your pictures on social media to defame you."
    result = demographic_safety_engine.analyze_harassment(text)
    assert any("Impersonation" in p for p in result["detected_patterns"])

def test_women_safety_api_endpoint(db: Session, test_user: User):
    """Test POST /api/v1/demographics/women-safety/analyze."""
    req = HarassmentAnalysisRequest(
        content="Pay 25000 or I will viral your private video.",
        context="Instagram Direct Message"
    )
    res = analyze_women_safety_threat(req, db=db, current_user=test_user)
    assert res.threat_severity == "CRITICAL_EMERGENCY"
    assert len(res.emergency_helplines) >= 3
    assert len(res.evidence_checklist) >= 3

def test_senior_safety_pension_scam_english():
    """Verify plain explanation of Jeevan Pramaan / Pension scam in English."""
    result = demographic_safety_engine.explain_senior_scam(
        "Pension account suspended. Update Jeevan Pramaan life certificate now by clicking link.",
        language="en"
    )
    assert result["verdict"] == "DANGEROUS SCAM"
    assert result["scam_category"] == "PENSION_KYC_SCAM"
    assert "AnyDesk" in result["plain_explanation"]
    assert len(result["voice_script"]) > 10

def test_senior_safety_pension_scam_kannada():
    """Verify plain explanation of pension scam in Kannada."""
    result = demographic_safety_engine.explain_senior_scam(
        "ಪಿಂಚಣಿ ಖಾತೆ ಸ್ಥಗಿತಗೊಂಡಿದೆ ಜೀವನ ಪ್ರಮಾಣ ಪತ್ರ ನವೀಕರಿಸಿ",
        language="kn"
    )
    assert result["verdict"] == "DANGEROUS SCAM"
    assert result["scam_category"] == "PENSION_KYC_SCAM"
    assert "ಪಿಂಚಣಿ" in result["plain_explanation"]
    assert "ಸುರಕ್ಷಿತವಾಗಿದೆ" in result["voice_script"]

def test_senior_safety_pension_scam_hindi():
    """Verify plain explanation of pension scam in Hindi."""
    result = demographic_safety_engine.explain_senior_scam(
        "पेंशन खाता बंद हो गया है जीवन प्रमाण पत्र तुरंत अपडेट करें",
        language="hi"
    )
    assert result["verdict"] == "DANGEROUS SCAM"
    assert "पेंशन" in result["plain_explanation"]
    assert "घोटाला" in result["plain_explanation"]

def test_senior_safety_electricity_scam():
    """Verify plain explanation of electricity bill scam."""
    result = demographic_safety_engine.explain_senior_scam(
        "Electricity will be cut tonight at 9:30 PM due to unpaid bill. Call officer immediately.",
        language="en"
    )
    assert result["verdict"] == "DANGEROUS SCAM"
    assert result["scam_category"] == "ELECTRICITY_BILL_SCAM"
    assert "not be disconnected" in result["voice_script"]

def test_senior_safety_otp_pin_fraud():
    """Verify plain explanation of OTP/PIN fraud."""
    result = demographic_safety_engine.explain_senior_scam(
        "Enter your UPI PIN to receive 50,000 cash reward from bank officer.",
        language="en"
    )
    assert result["verdict"] == "DANGEROUS SCAM"
    assert result["scam_category"] == "CREDENTIAL_THEFT"
    assert "NEVER need to enter a PIN to receive money" in result["plain_explanation"]

def test_senior_safety_api_endpoint():
    """Test POST /api/v1/demographics/senior-safety/explain."""
    req = SeniorSafetyRequest(
        message="KBC Lucky draw won 25 lakhs lottery",
        language="en"
    )
    res = explain_senior_scam(req)
    assert res.verdict == "DANGEROUS SCAM"
    assert res.scam_category == "LOTTERY_PRIZE_SCAM"
    assert "1930" in res.emergency_helpline

def test_trusted_contacts_no_consent_rejected(db: Session, test_user: User):
    """Verify explicit consent requirement."""
    payload = TrustedContactCreate(
        name="Sunil Kumar",
        relationship_type="child",
        phone_number="9876543210",
        has_explicit_consent=False
    )
    with pytest.raises(HTTPException) as exc:
        add_trusted_contact(payload, db=db, current_user=test_user)
    assert exc.value.status_code == 400
    assert "Explicit user consent is required" in exc.value.detail

def test_trusted_contacts_crud_and_alert_generation(db: Session, test_user: User):
    """Verify adding, listing, generating alert message, and deleting trusted contact."""
    payload = TrustedContactCreate(
        name="Dr. Anita Kumar",
        relationship_type="child",
        phone_number="9845098450",
        email="anita.kumar@example.com",
        has_explicit_consent=True,
        notify_on_critical_scam=True
    )
    contact = add_trusted_contact(payload, db=db, current_user=test_user)
    assert contact.id is not None
    assert contact.name == "Dr. Anita Kumar"

    # List contacts
    contacts = get_trusted_contacts(db=db, current_user=test_user)
    assert any(c.id == contact.id for c in contacts)

    # Generate SOS Alert
    alert_req = TrustedContactAlertRequest(
        contact_id=contact.id,
        incident_type="Digital Arrest Impersonation Call",
        incident_details="Suspicious Skype video caller posing as Mumbai Police."
    )
    alert_res = generate_contact_alert(alert_req, db=db, current_user=test_user)
    assert alert_res.contact_name == "Dr. Anita Kumar"
    assert "1930" in alert_res.draft_sms_text
    assert "whatsapp.com" in alert_res.whatsapp_share_url

    # Delete contact
    del_res = delete_trusted_contact(contact.id, db=db, current_user=test_user)
    assert del_res["status"] == "deleted"

    # Verify deleted
    db_check = db.query(TrustedContact).filter(TrustedContact.id == contact.id).first()
    assert db_check is None

