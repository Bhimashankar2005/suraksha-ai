import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.sanitizer import validate_safe_path
from backend.app.api.deps import get_current_user, record_audit_log
from backend.app.models.user import User
from backend.app.models.evidence import EvidenceFile, IncidentReport
from backend.app.schemas.evidence import (
    EvidenceFileItem,
    IncidentReportCreate,
    IncidentReportResponse,
    EvidenceVaultStats
)
from backend.app.services.evidence_service import (
    save_evidence_file,
    delete_evidence_file,
    create_incident_dossier,
    get_vault_statistics,
    OFFICIAL_POLICE_DISCLAIMER
)

router = APIRouter()

@router.post("/upload", response_model=EvidenceFileItem, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    incident_category: str = Form(..., description="Category: UPI_FRAUD, FAKE_BANK, BLACKMAIL, DIGITAL_ARREST, OTHER"),
    incident_date: Optional[str] = Form(None, description="ISO formatted incident date e.g. 2026-11-01T14:30:00"),
    description: Optional[str] = Form(None, description="Citizen notes or narrative"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Secure evidence file vault upload.
    Validates magic bytes, calculates SHA-256 tamper-evident hash,
    and isolates storage in private directory using UUID filenames.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    parsed_date = datetime.now(timezone.utc)
    if incident_date:
        try:
            parsed_date = datetime.fromisoformat(incident_date.replace("Z", "+00:00"))
        except ValueError:
            parsed_date = datetime.now(timezone.utc)

    try:
        evidence = save_evidence_file(
            db=db,
            user_id=current_user.id,
            original_name=file.filename or "evidence.dat",
            file_bytes=file_bytes,
            incident_category=incident_category,
            incident_date=parsed_date,
            description=description
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    record_audit_log(
        db=db,
        action="EVIDENCE_UPLOAD",
        resource_type="EVIDENCE_FILE",
        resource_id=evidence.id,
        details={
            "file_code": evidence.file_code,
            "mime_type": evidence.mime_type,
            "sha256": evidence.sha256_hash,
            "file_size": evidence.file_size_bytes
        },
        user_id=current_user.id
    )

    return EvidenceFileItem(
        id=evidence.id,
        file_code=evidence.file_code,
        original_name=evidence.original_name,
        mime_type=evidence.mime_type,
        file_size_bytes=evidence.file_size_bytes,
        sha256_hash=evidence.sha256_hash,
        incident_category=evidence.incident_category,
        incident_date=evidence.incident_date,
        description=evidence.description,
        created_at=evidence.created_at
    )

@router.get("/my-vault", response_model=List[EvidenceFileItem])
def get_user_vault(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all cryptographic evidence files stored in user's vault.
    """
    files = db.query(EvidenceFile).filter(
        EvidenceFile.user_id == current_user.id
    ).order_by(EvidenceFile.created_at.desc()).all()

    return [
        EvidenceFileItem(
            id=f.id,
            file_code=f.file_code,
            original_name=f.original_name,
            mime_type=f.mime_type,
            file_size_bytes=f.file_size_bytes,
            sha256_hash=f.sha256_hash,
            incident_category=f.incident_category,
            incident_date=f.incident_date,
            description=f.description,
            created_at=f.created_at
        )
        for f in files
    ]

@router.get("/stats", response_model=EvidenceVaultStats)
def get_user_vault_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns real-time aggregates for the citizen's evidence repository.
    """
    stats = get_vault_statistics(db, current_user.id)
    return EvidenceVaultStats(
        total_files=stats["total_files"],
        total_size_bytes=stats["total_size_bytes"],
        total_incident_reports=stats["total_incident_reports"],
        total_documented_loss_inr=stats["total_documented_loss_inr"]
    )

@router.get("/{file_id}/download")
def download_evidence(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Secure evidence download with strict RBAC access control and audit logging.
    Only the owner or an authorized administrator can download evidence.
    """
    evidence = db.query(EvidenceFile).filter(EvidenceFile.id == file_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found.")

    # Authorization Check
    is_admin = current_user.role and current_user.role.name == "ADMIN"
    if evidence.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view or download this evidence file."
        )

    # Path traversal defense verification
    storage_root = os.path.join(settings.STORAGE_DIR, "evidence")
    if not validate_safe_path(storage_root, evidence.stored_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security violation: Invalid evidence file path traversal detected."
        )

    if not os.path.exists(evidence.stored_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical evidence file missing on disk.")

    record_audit_log(
        db=db,
        action="EVIDENCE_DOWNLOAD",
        resource_type="EVIDENCE_FILE",
        resource_id=evidence.id,
        details={"file_code": evidence.file_code, "original_name": evidence.original_name},
        user_id=current_user.id
    )

    return FileResponse(
        path=evidence.stored_path,
        media_type=evidence.mime_type,
        filename=evidence.original_name
    )

@router.delete("/{file_id}", status_code=status.HTTP_200_OK)
def delete_evidence(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes an evidence file from storage and database.
    Owner or Admin only.
    """
    evidence = db.query(EvidenceFile).filter(EvidenceFile.id == file_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found.")

    is_admin = current_user.role and current_user.role.name == "ADMIN"
    if evidence.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # Path traversal defense verification
    storage_root = os.path.join(settings.STORAGE_DIR, "evidence")
    if not validate_safe_path(storage_root, evidence.stored_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security violation: Invalid evidence file path traversal detected."
        )

    record_audit_log(
        db=db,
        action="EVIDENCE_DELETE",
        resource_type="EVIDENCE_FILE",
        resource_id=evidence.id,
        details={"file_code": evidence.file_code},
        user_id=current_user.id
    )

    delete_evidence_file(db, evidence)
    return {"status": "deleted", "id": file_id}

# --- Incident Dossier / Structured Police Report Endpoints ---

@router.post("/incident-reports", response_model=IncidentReportResponse, status_code=status.HTTP_201_CREATED)
def compile_incident_report(
    report_in: IncidentReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Packages selected evidence files into an official structured incident dossier
    with tamper-evident hashes ready for submission to cybercrime.gov.in or police.
    """
    incident = create_incident_dossier(db, current_user.id, report_in)

    # Fetch attached evidence file objects
    attached_files = []
    if incident.evidence_file_ids:
        db_files = db.query(EvidenceFile).filter(
            EvidenceFile.id.in_(incident.evidence_file_ids)
        ).all()
        attached_files = [
            EvidenceFileItem(
                id=f.id,
                file_code=f.file_code,
                original_name=f.original_name,
                mime_type=f.mime_type,
                file_size_bytes=f.file_size_bytes,
                sha256_hash=f.sha256_hash,
                incident_category=f.incident_category,
                incident_date=f.incident_date,
                description=f.description,
                created_at=f.created_at
            )
            for f in db_files
        ]

    record_audit_log(
        db=db,
        action="INCIDENT_DOSSIER_COMPILED",
        resource_type="INCIDENT_REPORT",
        resource_id=incident.id,
        details={
            "incident_title": incident.incident_title,
            "category": incident.category,
            "financial_loss": float(incident.total_financial_loss),
            "evidence_count": len(attached_files)
        },
        user_id=current_user.id
    )

    return IncidentReportResponse(
        id=incident.id,
        incident_title=incident.incident_title,
        category=incident.category,
        total_financial_loss=float(incident.total_financial_loss),
        timeline_summary=incident.timeline_summary,
        evidence_files=attached_files,
        official_portal_guidance=incident.official_portal_guidance,
        disclaimer=OFFICIAL_POLICE_DISCLAIMER,
        created_at=incident.created_at
    )

@router.get("/incident-reports", response_model=List[IncidentReportResponse])
def get_incident_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves all compiled incident dossiers for the authenticated citizen.
    """
    incidents = db.query(IncidentReport).filter(
        IncidentReport.user_id == current_user.id
    ).order_by(IncidentReport.created_at.desc()).all()

    results = []
    for inc in incidents:
        attached_files = []
        if inc.evidence_file_ids:
            db_files = db.query(EvidenceFile).filter(
                EvidenceFile.id.in_(inc.evidence_file_ids)
            ).all()
            attached_files = [
                EvidenceFileItem(
                    id=f.id,
                    file_code=f.file_code,
                    original_name=f.original_name,
                    mime_type=f.mime_type,
                    file_size_bytes=f.file_size_bytes,
                    sha256_hash=f.sha256_hash,
                    incident_category=f.incident_category,
                    incident_date=f.incident_date,
                    description=f.description,
                    created_at=f.created_at
                )
                for f in db_files
            ]

        results.append(
            IncidentReportResponse(
                id=inc.id,
                incident_title=inc.incident_title,
                category=inc.category,
                total_financial_loss=float(inc.total_financial_loss),
                timeline_summary=inc.timeline_summary,
                evidence_files=attached_files,
                official_portal_guidance=inc.official_portal_guidance,
                disclaimer=OFFICIAL_POLICE_DISCLAIMER,
                created_at=inc.created_at
            )
        )
    return results

@router.get("/incident-reports/{report_id}", response_model=IncidentReportResponse)
def get_incident_report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single incident dossier by ID.
    Enforces user ownership or Admin authorization.
    """
    inc = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident report not found.")

    is_admin = current_user.role and current_user.role.name == "ADMIN"
    if inc.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    attached_files = []
    if inc.evidence_file_ids:
        db_files = db.query(EvidenceFile).filter(
            EvidenceFile.id.in_(inc.evidence_file_ids)
        ).all()
        attached_files = [
            EvidenceFileItem(
                id=f.id,
                file_code=f.file_code,
                original_name=f.original_name,
                mime_type=f.mime_type,
                file_size_bytes=f.file_size_bytes,
                sha256_hash=f.sha256_hash,
                incident_category=f.incident_category,
                incident_date=f.incident_date,
                description=f.description,
                created_at=f.created_at
            )
            for f in db_files
        ]

    return IncidentReportResponse(
        id=inc.id,
        incident_title=inc.incident_title,
        category=inc.category,
        total_financial_loss=float(inc.total_financial_loss),
        timeline_summary=inc.timeline_summary,
        evidence_files=attached_files,
        official_portal_guidance=inc.official_portal_guidance,
        disclaimer=OFFICIAL_POLICE_DISCLAIMER,
        created_at=inc.created_at
    )

