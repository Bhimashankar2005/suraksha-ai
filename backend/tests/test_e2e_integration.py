import io
import pytest
import secrets
from PIL import Image
from starlette.datastructures import UploadFile

from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Role, Profile
from backend.app.models.reports import Report, Threat
from backend.app.models.scans import ScamScan, UrlScan, ImageScan, DeepfakeScan, PrivacyScan
from backend.app.models.safety_education import Course, Lesson, Quiz, TrustedContact
from backend.app.core.security import get_password_hash, create_access_token, decode_access_token

# Module Services & Endpoints
from backend.app.ml.scam_classifier import scam_classifier
from backend.app.services.scam_service import process_message_scan, convert_scan_to_report
from backend.app.services.url_service import process_url_scan
from backend.app.ml.image_analyzer import analyze_screenshot_content
from backend.app.services.image_service import process_image_upload_and_scan
from backend.app.ml.assistant_engine import assistant_engine
from backend.app.services.report_service import create_community_report, review_community_report
from backend.app.schemas.report import ReportCreate, ReportReviewAction
from backend.app.services.evidence_service import save_evidence_file, create_incident_dossier, OFFICIAL_POLICE_DISCLAIMER
from backend.app.schemas.evidence import IncidentReportCreate
from backend.app.ml.privacy_scanner import privacy_scanner
from backend.app.ml.demographic_safety_engine import demographic_safety_engine
from backend.app.api.endpoints.demographics import add_trusted_contact, generate_contact_alert
from backend.app.schemas.demographics import TrustedContactCreate, TrustedContactAlertRequest
from backend.app.ml.media_authenticity_engine import media_authenticity_engine
from backend.app.api.endpoints.deepfake import analyze_media_authenticity
from backend.app.api.endpoints.education import (
    list_courses,
    get_course_detail,
    complete_lesson,
    submit_quiz,
    get_user_learning_progress
)
from backend.app.schemas.education import QuizSubmissionRequest
from backend.app.services.notification_service import notification_service
from backend.app.api.endpoints.notifications import get_user_notifications, mark_notification_as_read
from backend.app.api.endpoints.admin_management import get_system_telemetry, list_security_audit_logs

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def e2e_citizen(db):
    user_role = db.query(Role).filter(Role.name == "USER").first()
    email = f"e2e_citizen_{secrets.token_hex(4)}@suraksha.gov.in"
    user = User(
        email=email,
        password_hash=get_password_hash("Suraksha@CitizenSecure2026"),
        role_id=user_role.id,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = Profile(
        user_id=user.id,
        full_name="Radha Sharma",
        phone_number="9876543210",
        preferred_language="en",
        senior_mode=False
    )
    db.add(profile)
    db.commit()

    yield user

    # Teardown
    db.delete(user)
    db.commit()

@pytest.fixture(scope="module")
def e2e_admin(db):
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()
    email = f"e2e_admin_{secrets.token_hex(4)}@suraksha.gov.in"
    admin = User(
        email=email,
        password_hash=get_password_hash("Suraksha@AdminSecure2026"),
        role_id=admin_role.id,
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    yield admin

    # Teardown
    db.delete(admin)
    db.commit()

def test_e2e_citizen_registration_and_authentication_flow(e2e_citizen):
    """Verify citizen account creation, strict USER role assignment, and JWT session handling."""
    assert e2e_citizen.role.name == "USER"
    token = create_access_token(subject=e2e_citizen.id, role="USER")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == e2e_citizen.id
    assert payload["role"] == "USER"

def test_e2e_citizen_fraud_analysis_and_report_escalation(e2e_citizen, db):
    """
    Verify complete flow:
    1. Scan SMS scam message (Module 1)
    2. Scan phishing URL (Module 2)
    3. Scan screenshot fake receipt (Module 3)
    4. Escalate suspicious scam to community threat report (Module 5)
    """
    # 1. Scam Message Detection
    scam_text = "URGENT: Your SBI account has been suspended due to pending KYC. Click http://sbi-kyc-verify.top immediately to update PAN."
    scam_res = process_message_scan(content=scam_text, user_id=e2e_citizen.id, db=db)
    assert scam_res.risk_score >= 80
    assert scam_res.risk_level in ["HIGH", "CRITICAL"]
    assert "Bank KYC" in scam_res.scam_category or len(scam_res.matched_indicators) > 0

    # 2. Phishing URL Scanner
    phish_url = "http://sbi-kyc-update.xyz/login.php"
    url_res = process_url_scan(raw_url=phish_url, user_id=e2e_citizen.id, db=db)
    assert url_res.risk_score >= 70
    assert url_res.risk_level in ["HIGH", "CRITICAL"]
    assert "State Bank of India" in url_res.lookalike_target

    # 3. Screenshot Scanner
    img = Image.new("RGB", (150, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    fake_ocr = "Payment Successful to Ramesh. UTR: 928374928192. Amount Rs 25,000 sent."
    img_res = process_image_upload_and_scan(
        file_bytes=buf.getvalue(),
        file_name="fake_receipt.png",
        user_id=e2e_citizen.id,
        ocr_override=fake_ocr,
        db=db
    )
    assert img_res.risk_score >= 40
    assert img_res.risk_level in ["MEDIUM", "HIGH", "CRITICAL"]
    assert any("A payment screenshot NEVER proves money was received" in r for r in img_res.recommendations)

    # 4. Escalate scam scan to community threat report
    report_res = convert_scan_to_report(
        user_id=e2e_citizen.id,
        scan_id=scam_res.id,
        target_value="http://sbi-kyc-verify.top",
        custom_description="Bank KYC suspension phishing link received via SMS",
        region="Karnataka",
        db=db
    )
    assert report_res.report_code.startswith("SUR-REP-")
    assert report_res.status == "PENDING"

def test_e2e_multilingual_assistant_and_privacy_guardrail():
    """Verify trilingual dialogue tree and sensitive credential detection (Module 4)."""
    # Trilingual queries
    res_en = assistant_engine.get_assistant_reply("I got a call claiming my electricity will be cut off tonight at 9:30", language="en")
    assert "1930" in res_en["reply"] or len(res_en["emergency_contacts"]) > 0

    res_kn = assistant_engine.get_assistant_reply("ನನ್ನ ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ಕಡಿತಗೊಳಿಸಲಾಗುವುದು ಎಂದು ಸಂದೇಶ ಬಂದಿದೆ", language="kn")
    assert len(res_kn["reply"]) > 50

    res_hi = assistant_engine.get_assistant_reply("बिजली बिल काटने का मैसेज आया है क्या करूँ", language="hi")
    assert len(res_hi["reply"]) > 50

    # Inadvertent OTP guardrail trigger
    otp_leak = assistant_engine.get_assistant_reply("My OTP is 492810 sent by bank, should I give it?", language="en")
    assert otp_leak["safety_warning"] is not None
    assert "CRITICAL PRIVACY ALERT" in otp_leak["safety_warning"]
    assert "Never share OTPs or PINs" in otp_leak["safety_warning"]

def test_e2e_evidence_vault_and_incident_dossier_compilation(e2e_citizen, db):
    """Verify tamper-evident evidence uploads with SHA-256 and dossier generation (Module 6)."""
    from datetime import datetime, timezone
    content = b"Incident Log: Scammer contacted me from +91 9822334455 demanding Rs 15,000 via PhonePe."
    file_record = save_evidence_file(
        db=db,
        user_id=e2e_citizen.id,
        file_bytes=content,
        original_name="incident_log.txt",
        incident_category="MESSAGE_TRANSCRIPT",
        incident_date=datetime.now(timezone.utc)
    )
    assert file_record.file_code.startswith("EVD-")
    assert len(file_record.sha256_hash) == 64

    # Compile incident dossier
    dossier = create_incident_dossier(
        db=db,
        user_id=e2e_citizen.id,
        report_in=IncidentReportCreate(
            incident_title="Extortion attempt via PhonePe",
            category="UPI_FRAUD",
            total_financial_loss=15000.0,
            timeline_summary="Received threat call on 2026-11-01 demanding urgent transfer.",
            evidence_file_ids=[file_record.id]
        )
    )
    assert dossier.id is not None
    assert "cybercrime.gov.in" in dossier.official_portal_guidance
    assert "1930" in dossier.official_portal_guidance

def test_e2e_privacy_protection_pii_redaction(e2e_citizen):
    """Verify local zero-cloud PII redaction and Verhoeff checksum validation (Module 7)."""
    # Valid Aadhaar sample (Verhoeff checksum passed)
    aadhaar_sample = "298765432107"
    raw_text = f"My Aadhaar is {aadhaar_sample}, PAN is ABCDE1234F, and phone is 9876543210."

    res = privacy_scanner.scan_and_redact(raw_text)
    assert res["risk_score"] >= 70
    assert "XXXXXXXX2107" in res["sanitized_text"]
    assert "XXXXX1234F" in res["sanitized_text"]
    assert "+91 XXXXX 43210" in res["sanitized_text"]
    # Verify unredacted PII is completely absent from sanitized text
    assert aadhaar_sample not in res["sanitized_text"]
    assert "ABCDE1234F" not in res["sanitized_text"]

def test_e2e_demographic_safety_workflows(e2e_citizen, db):
    """Verify Women Safety threat analysis & SOS dispatch, and Senior Safety explainer (Modules 9 & 10)."""
    # Women Safety Threat Analysis
    threat_text = "I have your morphed photos. Pay Rs 30,000 to my UPI or I will share them with your college friends."
    harass_res = demographic_safety_engine.analyze_harassment(threat_text, "Instagram DM")
    assert harass_res["threat_severity"] in ["HIGH", "CRITICAL_EMERGENCY"]
    assert any(h["number"] == "1091" for h in harass_res["emergency_helplines"])

    # Register trusted contact with explicit consent
    contact_data = TrustedContactCreate(
        name="Sunita Sharma",
        relationship_type="parent",
        phone_number="9811223344",
        has_explicit_consent=True,
        notify_on_critical_scam=True
    )
    contact = add_trusted_contact(contact_data, db=db, current_user=e2e_citizen)
    assert contact.name == "Sunita Sharma"

    # Generate SOS alert
    alert_res = generate_contact_alert(
        payload=TrustedContactAlertRequest(
            contact_id=contact.id,
            incident_type="CYBER_EXTORTION",
            incident_details="Threatening blackmail messages received online"
        ),
        db=db,
        current_user=e2e_citizen
    )
    assert "whatsapp" in alert_res.whatsapp_share_url
    assert "1930" in alert_res.draft_sms_text

    # Senior Safety Trilingual Explainer
    senior_query = "Dear Pensioner, update your Jeevan Pramaan life certificate now or pension of Rs 35,000 stops."
    senior_res = demographic_safety_engine.explain_senior_scam(senior_query, language="en")
    assert senior_res["verdict"] == "DANGEROUS SCAM"
    assert "1930" in senior_res["emergency_helpline"]

def test_e2e_deepfake_forensics_workflow(e2e_citizen, db):
    """Verify deepfake image ELA and generative software tag inspection (Module 8)."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    # Simulate Midjourney generative signature in stream
    raw_bytes = buf.getvalue() + b"parameters: A photorealistic portrait, Midjourney v6"

    upload_file = UploadFile(file=io.BytesIO(raw_bytes), filename="synthetic_portrait.png")
    data = analyze_media_authenticity(
        file=upload_file,
        db=db,
        current_user=e2e_citizen
    )
    assert data.authenticity_score < 50
    assert data.verdict == "PROBABLE_SYNTHETIC_OR_MANIPULATED"
    assert any("Midjourney" in f for f in data.forensic_flags["suspicious_factors"])
    assert "Forensic media analysis provides probabilistic heuristic indicators" in data.limitations_disclaimer

def test_e2e_education_academy_learning_path(e2e_citizen, db):
    """Verify course reading, lesson completion, and quiz passing with badge award (Module 11)."""
    courses = list_courses(audience=None, db=db, current_user=e2e_citizen)
    assert len(courses) >= 6

    course_detail = get_course_detail(course_slug="upi-digital-payment-safety", db=db, current_user=e2e_citizen)
    assert len(course_detail.lessons) >= 2

    # Complete lesson 1
    comp_res = complete_lesson(
        lesson_id=course_detail.lessons[0].id,
        db=db,
        current_user=e2e_citizen
    )
    assert comp_res["status"] == "success"

    # Pass UPI Quiz
    quiz_id = course_detail.quiz.id
    quiz_res = submit_quiz(
        quiz_id=quiz_id,
        payload=QuizSubmissionRequest(answers={"1": 0, "2": 2, "3": 1}),
        db=db,
        current_user=e2e_citizen
    )
    assert quiz_res.score == 100
    assert quiz_res.passed is True
    assert quiz_res.badge_earned == "UPI Fraud Shield"

    # Verify progress stats reflect completion and earned badge
    stats = get_user_learning_progress(db=db, current_user=e2e_citizen)
    assert stats.lessons_completed >= 1
    assert stats.quizzes_passed >= 1
    assert any(b.title == "UPI Fraud Shield" for b in stats.badges)

def test_e2e_admin_moderation_verification_and_citizen_notification_loop(e2e_citizen, e2e_admin, db):
    """
    Verify complete admin moderation and citizen notification loop:
    1. Citizen submits threat report
    2. Admin reviews and approves report, publishing as public threat
    3. Citizen automatically receives in-app notification
    4. Citizen marks notification as read
    5. Admin queries system telemetry and audit logs
    """
    # 1. Citizen submits report
    phone_val = f"9823{secrets.randbelow(900000) + 100000}"
    rep = create_community_report(
        db=db,
        report_in=ReportCreate(
            threat_type="PHONE",
            target_value=phone_val,
            description="Fake electricity officer calling to cut power tonight",
            is_anonymous=False
        ),
        user_id=e2e_citizen.id
    )

    # 2. Admin reviews and approves report
    reviewed = review_community_report(
        db=db,
        report_id=rep.id,
        admin_id=e2e_admin.id,
        review_in=ReportReviewAction(
            action="APPROVE_VERIFY",
            internal_notes="Confirmed unauthorized extortion line",
            public_notes="Verified electricity scam line",
            publish_as_public_alert=True,
            threat_level="HIGH"
        )
    )
    assert reviewed.status == "VERIFIED"

    # 3. Citizen automatically receives in-app notification
    notifs = get_user_notifications(
        unread_only=True,
        limit=10,
        skip=0,
        db=db,
        current_user=e2e_citizen
    )
    matched = next((n for n in notifs.items if rep.report_code in n.title), None)
    assert matched is not None
    assert "VERIFIED" in matched.message

    # 4. Citizen marks notification as read
    read_item = mark_notification_as_read(
        notification_id=matched.id,
        db=db,
        current_user=e2e_citizen
    )
    assert read_item.is_read is True

    # 5. Admin queries system telemetry & audit trail
    telemetry = get_system_telemetry(db=db, admin_user=e2e_admin)
    assert telemetry.total_users >= 2
    assert telemetry.uptime_status == "HEALTHY_ONLINE"
    assert telemetry.total_reports >= 1

    audit_logs = list_security_audit_logs(
        action=None,
        resource_type=None,
        user_id=None,
        limit=10,
        skip=0,
        db=db,
        admin_user=e2e_admin
    )
    assert len(audit_logs) >= 1
