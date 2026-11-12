import pytest
from backend.app.ml.assistant_engine import assistant_engine
from backend.app.schemas.chat import ChatRequest
from backend.app.api.endpoints.chat import send_chat_message, get_verified_resources, get_assistant_status

def test_sensitive_data_guardrail():
    """Verify assistant detects and warns if user inputs an OTP, PIN, or password."""
    warning = assistant_engine.detect_sensitive_data("Hello, my bank sent an OTP is 849201, is this safe?")
    assert warning is not None
    assert "CRITICAL PRIVACY ALERT" in warning
    assert "OTP" in warning

    # Should not trigger on normal non-sensitive messages
    normal = assistant_engine.detect_sensitive_data("How do I stay safe from phishing?")
    assert normal is None

def test_upi_fraud_guidance_english():
    """Verify UPI fraud guidance in English includes 1930 and Golden Hour instructions."""
    result = assistant_engine.get_assistant_reply(
        message="I lost money in a Google Pay UPI scam, please help!",
        language="en"
    )
    assert result["detected_topic"] == "upi_fraud"
    assert "1930" in result["reply"]
    assert "Golden Hour" in result["reply"]
    assert "cybercrime.gov.in" in result["reply"]
    assert len(result["quick_actions"]) > 0

def test_upi_fraud_guidance_kannada():
    """Verify UPI fraud guidance in Kannada contains native guidance and 1930."""
    result = assistant_engine.get_assistant_reply(
        message="ನನ್ನ ಯುಪಿಐ ಹಣ ವಂಚನೆಯಾಗಿದೆ, ಏನು ಮಾಡಬೇಕು?",
        language="kn"
    )
    assert result["detected_topic"] == "upi_fraud"
    assert result["language"] == "kn"
    assert "1930" in result["reply"]
    assert "ಗೋಲ್ಡನ್ ಅವರ್" in result["reply"]
    assert "ಬ್ಯಾಂಕ್" in result["reply"]

def test_upi_fraud_guidance_hindi():
    """Verify UPI fraud guidance in Hindi contains native guidance and 1930."""
    result = assistant_engine.get_assistant_reply(
        message="यूपीआई से पैसे कट गए, वापस कैसे पाएं?",
        language="hi"
    )
    assert result["detected_topic"] == "upi_fraud"
    assert result["language"] == "hi"
    assert "1930" in result["reply"]
    assert "गोल्डन ऑवर" in result["reply"]
    assert "शिकायत" in result["reply"]

def test_bank_kyc_freeze_guidance():
    """Verify KYC suspension scam detection and advice."""
    result = assistant_engine.get_assistant_reply(
        message="Got an SMS saying my SBI bank account is blocked due to KYC. Should I update?",
        language="en"
    )
    assert result["detected_topic"] == "bank_kyc_freeze"
    assert "Do NOT Click the Link" in result["reply"]
    assert "AnyDesk" in result["reply"]

def test_digital_arrest_impersonation_guidance():
    """Verify that digital arrest is properly clarified as non-existent under Indian law."""
    result = assistant_engine.get_assistant_reply(
        message="Police called on Skype saying digital arrest for parcel with drugs, what to do?",
        language="en"
    )
    assert result["detected_topic"] == "digital_arrest"
    assert "NO such concept as 'Digital Arrest'" in result["reply"]
    assert "1930" in result["reply"]
    assert "112" in result["reply"]

def test_cyber_harassment_women_safety():
    """Verify cyber harassment and blackmail guidance directs to NCW and 1091."""
    result = assistant_engine.get_assistant_reply(
        message="Someone is blackmailing me with morphed private photos on Instagram, please help!",
        language="en"
    )
    assert result["detected_topic"] == "cyber_harassment_women"
    assert "1091" in result["reply"]
    assert "7827170170" in result["reply"]
    assert "cybercrime.gov.in" in result["reply"]

def test_aadhaar_biometric_protection():
    """Verify Aadhaar identity theft and biometric lock advice."""
    result = assistant_engine.get_assistant_reply(
        message="How do I lock my Aadhaar biometrics and check fake SIMs?",
        language="en"
    )
    assert result["detected_topic"] == "identity_theft_aadhaar"
    assert "mAadhaar" in result["reply"]
    assert "sancharsaathi.gov.in" in result["reply"]

def test_electricity_bill_scam_guidance():
    """Verify electricity bill disconnection scam advice."""
    result = assistant_engine.get_assistant_reply(
        message="SMS says electricity power cut tonight at 9:30 PM due to unpaid bill.",
        language="en"
    )
    assert result["detected_topic"] == "electricity_bill"
    assert "Never Call" in result["reply"]

def test_job_lottery_scam_guidance():
    """Verify Telegram part-time job / lottery advice."""
    result = assistant_engine.get_assistant_reply(
        message="Telegram part time job offering 5000 per day for youtube likes.",
        language="en"
    )
    assert result["detected_topic"] == "job_lottery_scam"
    assert "No legitimate employer" in result["reply"]

def test_chat_message_endpoint():
    """Test POST /api/v1/chat/message endpoint handler."""
    req = ChatRequest(
        message="I lost money through PhonePe UPI payment",
        language="en"
    )
    response = send_chat_message(req)
    assert response.language == "en"
    assert response.detected_topic == "upi_fraud"
    assert "1930" in response.reply
    assert len(response.emergency_contacts) >= 4

def test_chat_resources_endpoint():
    """Test GET /api/v1/chat/resources endpoint handler."""
    resources = get_verified_resources()
    assert len(resources) >= 4
    names = [r.name for r in resources]
    assert any("Cyber Crime" in name for name in names)
    assert any("Emergency" in name for name in names)

def test_chat_status_endpoint():
    """Test GET /api/v1/chat/status endpoint handler."""
    status = get_assistant_status()
    assert "en" in status.supported_languages
    assert "kn" in status.supported_languages
    assert "hi" in status.supported_languages
    assert status.base_url is not None
