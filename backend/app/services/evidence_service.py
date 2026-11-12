import os
import hashlib
import secrets
import string
import uuid
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.config import settings
from backend.app.models.evidence import EvidenceFile, IncidentReport
from backend.app.schemas.evidence import IncidentReportCreate

OFFICIAL_POLICE_DISCLAIMER = (
    "STATUTORY NOTICE & POLICE REPORTING GUIDANCE: "
    "SURAKSHA AI is an automated digital safety and forensic packaging platform. "
    "This platform does NOT itself register a formal Police First Information Report (FIR). "
    "To initiate legal criminal proceedings or bank fund freezes under Section 43/66 of the Information Technology Act, "
    "citizens must immediately lodge this dossier at the National Cyber Crime Reporting Portal: "
    "https://cybercrime.gov.in or dial the National Cyber Crime Helpline: 1930 within the Golden Hour."
)

MAGIC_SIGNATURES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
    "application/pdf": [b"%PDF-"],
}

def validate_and_hash_file(file_bytes: bytes, filename: str) -> Tuple[str, str, int]:
    """
    Validates file magic bytes, enforces max size limits,
    and calculates SHA-256 cryptographic hash.
    """
    file_size = len(file_bytes)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    if file_size == 0:
        raise ValueError("File is empty (0 bytes).")
    if file_size > max_bytes:
        raise ValueError(f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    detected_mime = None
    for mime, signatures in MAGIC_SIGNATURES.items():
        for sig in signatures:
            if file_bytes.startswith(sig):
                if mime == "image/webp":
                    if len(file_bytes) > 12 and file_bytes[8:12] == b"WEBP":
                        detected_mime = mime
                        break
                else:
                    detected_mime = mime
                    break
        if detected_mime:
            break

    # Check for text/plain (UTF-8 readable, no binary null bytes)
    if not detected_mime:
        ext = os.path.splitext(filename.lower())[1]
        if ext in [".txt", ".log", ".csv"]:
            try:
                # Disallow binary null bytes
                if b"\x00" not in file_bytes[:1024]:
                    file_bytes.decode("utf-8")
                    detected_mime = "text/plain"
            except UnicodeDecodeError:
                pass

    if not detected_mime:
        raise ValueError(
            "Unsupported or corrupted file format. Allowed types: JPEG, PNG, WEBP, PDF, TXT."
        )

    # Compute tamper-evident SHA-256 hash
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    return detected_mime, sha256, file_size

def generate_unique_evidence_code(db: Session) -> str:
    """Generates a secure, human-readable evidence code (EVD-XXXXXX)."""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(10):
        suffix = "".join(secrets.choice(alphabet) for _ in range(6))
        code = f"EVD-{suffix}"
        exists = db.query(EvidenceFile).filter(EvidenceFile.file_code == code).first()
        if not exists:
            return code
    import time
    return f"EVD-{int(time.time())}"

def save_evidence_file(
    db: Session,
    user_id: str,
    original_name: str,
    file_bytes: bytes,
    incident_category: str,
    incident_date: datetime,
    description: Optional[str] = None
) -> EvidenceFile:
    """Saves evidence file to secure storage directory and records metadata."""
    mime_type, sha256_hash, file_size = validate_and_hash_file(file_bytes, original_name)
    file_code = generate_unique_evidence_code(db)

    # Storage filename uses isolated UUID to prevent path traversal or sensitive name leaks
    storage_filename = f"{uuid.uuid4().hex}.dat"
    storage_dir = os.path.join(settings.STORAGE_DIR, "evidence")
    os.makedirs(storage_dir, exist_ok=True)
    full_path = os.path.join(storage_dir, storage_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    evidence_entry = EvidenceFile(
        user_id=user_id,
        file_code=file_code,
        original_name=os.path.basename(original_name),
        stored_path=full_path,
        mime_type=mime_type,
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        incident_category=incident_category,
        incident_date=incident_date,
        description=description
    )

    db.add(evidence_entry)
    db.commit()
    db.refresh(evidence_entry)
    return evidence_entry

def delete_evidence_file(db: Session, evidence: EvidenceFile):
    """Deletes evidence file from disk and database."""
    if os.path.exists(evidence.stored_path):
        try:
            os.remove(evidence.stored_path)
        except OSError:
            pass
    db.delete(evidence)
    db.commit()

def create_incident_dossier(
    db: Session,
    user_id: str,
    report_in: IncidentReportCreate
) -> IncidentReport:
    """
    Compiles selected evidence files into an official structured incident dossier
    with tamper-evident hashes ready for submission to cybercrime.gov.in or police.
    """
    # Verify attached evidence files belong to the user
    valid_file_ids = []
    if report_in.evidence_file_ids:
        owned_files = db.query(EvidenceFile).filter(
            EvidenceFile.id.in_(report_in.evidence_file_ids),
            EvidenceFile.user_id == user_id
        ).all()
        valid_file_ids = [f.id for f in owned_files]

    incident_entry = IncidentReport(
        user_id=user_id,
        incident_title=report_in.incident_title.strip(),
        category=report_in.category,
        total_financial_loss=report_in.total_financial_loss,
        timeline_summary=report_in.timeline_summary.strip(),
        evidence_file_ids=valid_file_ids,
        official_portal_guidance=OFFICIAL_POLICE_DISCLAIMER
    )

    db.add(incident_entry)
    db.commit()
    db.refresh(incident_entry)
    return incident_entry

def get_vault_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """Aggregates user's personal evidence vault statistics."""
    total_files = db.query(func.count(EvidenceFile.id)).filter(
        EvidenceFile.user_id == user_id
    ).scalar() or 0

    total_size = db.query(func.sum(EvidenceFile.file_size_bytes)).filter(
        EvidenceFile.user_id == user_id
    ).scalar() or 0

    total_dossiers = db.query(func.count(IncidentReport.id)).filter(
        IncidentReport.user_id == user_id
    ).scalar() or 0

    total_loss = db.query(func.sum(IncidentReport.total_financial_loss)).filter(
        IncidentReport.user_id == user_id
    ).scalar() or 0.0

    return {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_incident_reports": total_dossiers,
        "total_documented_loss_inr": float(total_loss)
    }

