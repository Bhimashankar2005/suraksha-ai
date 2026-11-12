import io
import pytest
import secrets
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.user import User, Role
from backend.app.models.scans import DeepfakeScan
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.ml.media_authenticity_engine import media_authenticity_engine

client = TestClient(app)

@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def test_user(db):
    user_role = db.query(Role).filter(Role.name == "USER").first()
    email = f"deepfake_tester_{secrets.token_hex(4)}@suraksha.gov.in"
    user = User(
        email=email,
        password_hash=get_password_hash("Suraksha@SecurePass2026"),
        role_id=user_role.id,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role="USER")
    headers = {"Authorization": f"Bearer {token}"}
    yield {"user": user, "headers": headers}

    # Teardown
    db.delete(user)
    db.commit()

def test_detect_media_type():
    # JPEG
    assert media_authenticity_engine.detect_media_type(b"\xff\xd8\xff\xe0\x00\x10JFIF", "photo.jpg") == "IMAGE"
    # PNG
    assert media_authenticity_engine.detect_media_type(b"\x89PNG\r\n\x1a\n\x00\x00", "test.png") == "IMAGE"
    # WEBP
    assert media_authenticity_engine.detect_media_type(b"RIFF\x20\x00\x00\x00WEBPVP8 ", "graphic.webp") == "IMAGE"
    # WAV
    assert media_authenticity_engine.detect_media_type(b"RIFF\x24\x00\x00\x00WAVEfmt ", "voice.wav") == "AUDIO"
    # MP3
    assert media_authenticity_engine.detect_media_type(b"ID3\x03\x00\x00\x00", "speech.mp3") == "AUDIO"
    # MP4
    assert media_authenticity_engine.detect_media_type(b"\x00\x00\x00\x20ftypisom", "video.mp4") == "VIDEO"

def test_analyze_image_ela_uniform():
    # Create simple solid image
    img = Image.new("RGB", (120, 120), color=(100, 150, 200))
    ela = media_authenticity_engine.analyze_image_ela(img)
    assert "mean_error_level" in ela
    assert "regional_variance" in ela
    assert isinstance(ela["ela_anomaly_flag"], bool)

def test_inspect_metadata_ai_signature():
    # Byte stream containing Midjourney tag
    raw = b"RIFF\x20\x00\x00\x00WEBPVP8 " + b"Software: Midjourney v6.0 prompt: ultra realistic face"
    findings = media_authenticity_engine.inspect_metadata(raw, "IMAGE")
    assert "Midjourney" in findings["ai_signatures"]

def test_inspect_metadata_editing_signature():
    raw = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"Edited with Adobe Photoshop 2024 for Windows"
    findings = media_authenticity_engine.inspect_metadata(raw, "IMAGE")
    assert "Photoshop" in findings["editing_signatures"]

def test_audio_forensics_synthetic_tag():
    raw = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"Generated via ElevenLabs Speech Synthesis Engine"
    audio_findings = media_authenticity_engine.analyze_audio_forensics(raw, "call.wav")
    assert len(audio_findings["synthetic_voice_indicators"]) > 0

from starlette.datastructures import UploadFile
from backend.app.api.endpoints.deepfake import (
    analyze_media_authenticity,
    get_deepfake_history,
    report_deepfake_threat
)
from backend.app.schemas.deepfake import DeepfakeReportRequest

def test_api_analyze_media_anonymous(db):
    img = Image.new("RGB", (80, 80), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    upload_file = UploadFile(file=io.BytesIO(buf.getvalue()), filename="sample.jpg")

    data = analyze_media_authenticity(
        file=upload_file,
        db=db,
        current_user=None
    )
    assert data.media_type == "IMAGE"
    assert data.verdict in ["LIKELY_AUTHENTIC", "SUSPICIOUS_ANOMALIES_DETECTED", "PROBABLE_SYNTHETIC_OR_MANIPULATED"]
    assert data.forensic_flags is not None
    assert data.limitations_disclaimer is not None

def test_api_analyze_media_authenticated_and_history(test_user, db):
    img = Image.new("RGB", (80, 80), color="purple")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    upload_file = UploadFile(file=io.BytesIO(buf.getvalue()), filename="auth_scan.png")

    data = analyze_media_authenticity(
        file=upload_file,
        db=db,
        current_user=test_user["user"]
    )
    scan_id = data.id
    assert scan_id is not None

    history = get_deepfake_history(
        limit=10,
        db=db,
        current_user=test_user["user"]
    )
    assert any(h.id == scan_id for h in history)

def test_api_report_deepfake_threat(test_user, db):
    # First create a scan
    img = Image.new("RGB", (60, 60), color="yellow")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    upload_file = UploadFile(file=io.BytesIO(buf.getvalue()), filename="deepfake_threat.png")

    scan_res = analyze_media_authenticity(
        file=upload_file,
        db=db,
        current_user=test_user["user"]
    )
    scan_id = scan_res.id

    # Report scan
    rep_res = report_deepfake_threat(
        payload=DeepfakeReportRequest(
            scan_id=scan_id,
            description="Deepfake voice clone and morphed video received via WhatsApp"
        ),
        db=db,
        current_user=test_user["user"]
    )
    assert rep_res.report_code.startswith("SUR-REP-")
    assert rep_res.status == "PENDING"
