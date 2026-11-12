import os
import pytest
import io
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi.datastructures import UploadFile
from backend.app.core.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.evidence import EvidenceFile, IncidentReport
from backend.app.schemas.evidence import IncidentReportCreate
from backend.app.services.evidence_service import (
    validate_and_hash_file,
    generate_unique_evidence_code,
    save_evidence_file,
    delete_evidence_file,
    create_incident_dossier,
    get_vault_statistics,
    OFFICIAL_POLICE_DISCLAIMER
)
from backend.app.api.endpoints.evidence import (
    upload_evidence,
    get_user_vault,
    get_user_vault_stats,
    download_evidence,
    delete_evidence,
    compile_incident_report,
    get_incident_reports,
    get_incident_report_detail
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

def test_validate_and_hash_file_valid_png():
    """Verify PNG validation and SHA-256 calculation."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    mime, sha, size = validate_and_hash_file(png_bytes, "screenshot.png")
    assert mime == "image/png"
    assert len(sha) == 64
    assert sha == hashlib.sha256(png_bytes).hexdigest()
    assert size == len(png_bytes)

def test_validate_and_hash_file_valid_pdf():
    """Verify PDF validation."""
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    mime, sha, size = validate_and_hash_file(pdf_bytes, "bank_statement.pdf")
    assert mime == "application/pdf"
    assert len(sha) == 64

def test_validate_and_hash_file_valid_txt():
    """Verify TXT file validation."""
    txt_bytes = b"Payment UTR: 123456789012\nLost Rs 25,000 on Google Pay scam."
    mime, sha, size = validate_and_hash_file(txt_bytes, "chat_log.txt")
    assert mime == "text/plain"
    assert len(sha) == 64

def test_validate_and_hash_file_corrupt_rejected():
    """Verify rejection of unknown or malicious binary formats."""
    corrupt_bytes = b"\x00\x01\x02\x03\x04MALICIOUS_BINARY"
    with pytest.raises(ValueError) as exc:
        validate_and_hash_file(corrupt_bytes, "payload.bin")
    assert "Unsupported or corrupted file format" in str(exc.value)

def test_validate_and_hash_file_empty_rejected():
    """Verify rejection of 0-byte empty files."""
    with pytest.raises(ValueError) as exc:
        validate_and_hash_file(b"", "empty.txt")
    assert "empty" in str(exc.value).lower()

def test_evidence_code_generation(db: Session):
    """Verify unique code generation EVD-XXXXXX."""
    code = generate_unique_evidence_code(db)
    assert code.startswith("EVD-")
    assert len(code) == 10

def test_save_evidence_file_persistence(db: Session, test_user: User):
    """Verify evidence file is stored securely with UUID and DB metadata created."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    evd = save_evidence_file(
        db=db,
        user_id=test_user.id,
        original_name="gpay_receipt.png",
        file_bytes=png_bytes,
        incident_category="UPI_FRAUD",
        incident_date=datetime.now(timezone.utc),
        description="Screenshot of fake UPI transfer."
    )
    assert evd.id is not None
    assert evd.file_code.startswith("EVD-")
    assert evd.mime_type == "image/png"
    assert os.path.exists(evd.stored_path)
    # Ensure physical filename on disk does not leak original name
    assert "gpay_receipt" not in os.path.basename(evd.stored_path)

def test_get_user_vault_files(db: Session, test_user: User):
    """Verify retrieval of citizen's evidence files."""
    files = get_user_vault(db=db, current_user=test_user)
    assert isinstance(files, list)
    assert len(files) >= 1
    assert any(f.file_code.startswith("EVD-") for f in files)

def test_download_evidence_authorized(db: Session, test_user: User):
    """Verify authorized citizen can download their own evidence."""
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    evd = save_evidence_file(
        db=db,
        user_id=test_user.id,
        original_name="download_test.png",
        file_bytes=png_bytes,
        incident_category="UPI_FRAUD",
        incident_date=datetime.now(timezone.utc)
    )
    response = download_evidence(evd.id, db=db, current_user=test_user)
    assert response.status_code == 200
    assert response.media_type == "image/png"

def test_download_evidence_unauthorized(db: Session, test_user: User):
    """Verify unauthorized citizen cannot download another citizen's evidence."""
    # Create file belonging to admin
    admin = db.query(User).filter(User.email == "admin@suraksha.gov.in").first()
    txt_bytes = b"Admin private audit log data."
    evd = save_evidence_file(
        db=db,
        user_id=admin.id,
        original_name="admin_secret.txt",
        file_bytes=txt_bytes,
        incident_category="OTHER",
        incident_date=datetime.now(timezone.utc)
    )
    # Normal user attempts to download admin's file
    with pytest.raises(HTTPException) as exc:
        download_evidence(evd.id, db=db, current_user=test_user)
    assert exc.value.status_code == 403

def test_delete_evidence_file(db: Session, test_user: User):
    """Verify deleting evidence cleans up physical file and database row."""
    txt_bytes = b"Temporary evidence file to be deleted."
    evd = save_evidence_file(
        db=db,
        user_id=test_user.id,
        original_name="to_delete.txt",
        file_bytes=txt_bytes,
        incident_category="OTHER",
        incident_date=datetime.now(timezone.utc)
    )
    file_path = evd.stored_path
    assert os.path.exists(file_path)

    res = delete_evidence(evd.id, db=db, current_user=test_user)
    assert res["status"] == "deleted"
    assert not os.path.exists(file_path)

    # Check DB
    db_check = db.query(EvidenceFile).filter(EvidenceFile.id == evd.id).first()
    assert db_check is None

def test_compile_incident_report_dossier(db: Session, test_user: User):
    """Verify incident dossier compilation with police reporting instructions and hashes."""
    # Create 2 evidence files
    f1 = save_evidence_file(
        db=db,
        user_id=test_user.id,
        original_name="statement.pdf",
        file_bytes=b"%PDF-1.4\nStatement",
        incident_category="UPI_FRAUD",
        incident_date=datetime.now(timezone.utc)
    )
    f2 = save_evidence_file(
        db=db,
        user_id=test_user.id,
        original_name="fraud_sms.txt",
        file_bytes=b"Payment of 25000 debited",
        incident_category="UPI_FRAUD",
        incident_date=datetime.now(timezone.utc)
    )

    dossier_in = IncidentReportCreate(
        incident_title="Unauthorized UPI Debit via Phishing APK",
        category="UPI_FRAUD",
        total_financial_loss=25000.0,
        timeline_summary="Received SMS at 10 AM, clicked link, money debited at 10:15 AM.",
        evidence_file_ids=[f1.id, f2.id]
    )

    report_resp = compile_incident_report(dossier_in, db=db, current_user=test_user)
    assert report_resp.incident_title == "Unauthorized UPI Debit via Phishing APK"
    assert report_resp.total_financial_loss == 25000.0
    assert len(report_resp.evidence_files) == 2
    assert "1930" in report_resp.official_portal_guidance
    assert "cybercrime.gov.in" in report_resp.official_portal_guidance
    assert "STATUTORY NOTICE" in report_resp.disclaimer

def test_get_incident_reports(db: Session, test_user: User):
    """Verify listing of compiled incident dossiers."""
    reports = get_incident_reports(db=db, current_user=test_user)
    assert isinstance(reports, list)
    assert len(reports) >= 1
    assert any("UPI" in r.incident_title for r in reports)

def test_vault_statistics(db: Session, test_user: User):
    """Verify vault telemetry aggregation."""
    stats = get_user_vault_stats(db=db, current_user=test_user)
    assert stats.total_files >= 1
    assert stats.total_size_bytes > 0
    assert stats.total_incident_reports >= 1
    assert stats.total_documented_loss_inr >= 25000.0

