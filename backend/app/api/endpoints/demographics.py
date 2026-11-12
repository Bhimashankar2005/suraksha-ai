from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, get_current_user_optional, record_audit_log
from backend.app.models.user import User
from backend.app.models.safety_education import TrustedContact
from backend.app.schemas.demographics import (
    HarassmentAnalysisRequest,
    HarassmentAnalysisResponse,
    SeniorSafetyRequest,
    SeniorSafetyResponse,
    TrustedContactCreate,
    TrustedContactItem,
    TrustedContactAlertRequest,
    TrustedContactAlertResponse,
    HelplineRef
)
from backend.app.ml.demographic_safety_engine import demographic_safety_engine

router = APIRouter()

@router.post("/women-safety/analyze", response_model=HarassmentAnalysisResponse)
def analyze_women_safety_threat(
    payload: HarassmentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Analyzes messages for extortion, morphing blackmail, cyberstalking, and gender-based harassment.
    Provides immediate emergency do's and don'ts, official hotlines (1091, NCW, 112), and legal checklist.
    """
    result = demographic_safety_engine.analyze_harassment(payload.content, payload.context)

    if current_user:
        record_audit_log(
            db=db,
            action="WOMEN_SAFETY_ASSESSMENT",
            resource_type="SAFETY_ANALYSIS",
            resource_id=current_user.id,
            details={
                "threat_severity": result["threat_severity"],
                "patterns": result["detected_patterns"],
                "risk_score": result["risk_score"]
            },
            user_id=current_user.id
        )

    helplines = [
        HelplineRef(
            name=h["name"],
            number=h["number"],
            portal=h.get("portal"),
            description=h["description"]
        )
        for h in result["emergency_helplines"]
    ]

    return HarassmentAnalysisResponse(
        threat_severity=result["threat_severity"],
        detected_patterns=result["detected_patterns"],
        risk_score=result["risk_score"],
        immediate_actions=result["immediate_actions"],
        emergency_helplines=helplines,
        evidence_checklist=result["evidence_checklist"],
        official_filing_link=result["official_filing_link"]
    )

@router.post("/senior-safety/explain", response_model=SeniorSafetyResponse)
def explain_senior_scam(payload: SeniorSafetyRequest):
    """
    Plain-Language, High-Accessibility Scam Explainer for Senior Citizens.
    Delivers zero-jargon explanation and TTS voice script in English, Kannada, or Hindi.
    """
    result = demographic_safety_engine.explain_senior_scam(payload.message, payload.language)
    return SeniorSafetyResponse(
        verdict=result["verdict"],
        plain_explanation=result["plain_explanation"],
        voice_script=result["voice_script"],
        scam_category=result["scam_category"],
        what_to_do_now=result["what_to_do_now"],
        emergency_helpline=result["emergency_helpline"],
        language=result["language"]
    )

@router.get("/trusted-contacts", response_model=List[TrustedContactItem])
def get_trusted_contacts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the list of trusted emergency family contacts saved by the citizen.
    """
    contacts = db.query(TrustedContact).filter(
        TrustedContact.user_id == current_user.id
    ).order_by(TrustedContact.created_at.desc()).all()

    return [
        TrustedContactItem(
            id=c.id,
            name=c.name,
            relationship_type=c.relationship_type,
            phone_number=c.phone_number,
            email=c.email,
            has_explicit_consent=c.has_explicit_consent,
            notify_on_critical_scam=c.notify_on_critical_scam,
            created_at=c.created_at
        )
        for c in contacts
    ]

@router.post("/trusted-contacts", response_model=TrustedContactItem, status_code=status.HTTP_201_CREATED)
def add_trusted_contact(
    payload: TrustedContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Registers a new trusted emergency contact with explicit consent verification.
    """
    if not payload.has_explicit_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit user consent is required before saving a trusted contact for emergency routing."
        )

    contact = TrustedContact(
        user_id=current_user.id,
        name=payload.name.strip(),
        relationship_type=payload.relationship_type.strip(),
        phone_number=payload.phone_number.strip(),
        email=payload.email.strip() if payload.email else None,
        has_explicit_consent=payload.has_explicit_consent,
        notify_on_critical_scam=payload.notify_on_critical_scam
    )

    db.add(contact)
    db.commit()
    db.refresh(contact)

    record_audit_log(
        db=db,
        action="TRUSTED_CONTACT_ADDED",
        resource_type="TRUSTED_CONTACT",
        resource_id=contact.id,
        details={"name": contact.name, "relationship": contact.relationship_type},
        user_id=current_user.id
    )

    return TrustedContactItem(
        id=contact.id,
        name=contact.name,
        relationship_type=contact.relationship_type,
        phone_number=contact.phone_number,
        email=contact.email,
        has_explicit_consent=contact.has_explicit_consent,
        notify_on_critical_scam=contact.notify_on_critical_scam,
        created_at=contact.created_at
    )

@router.delete("/trusted-contacts/{contact_id}", status_code=status.HTTP_200_OK)
def delete_trusted_contact(
    contact_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Removes a trusted contact.
    """
    contact = db.query(TrustedContact).filter(
        TrustedContact.id == contact_id,
        TrustedContact.user_id == current_user.id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trusted contact not found.")

    db.delete(contact)
    db.commit()

    record_audit_log(
        db=db,
        action="TRUSTED_CONTACT_DELETED",
        resource_type="TRUSTED_CONTACT",
        resource_id=contact_id,
        details={"name": contact.name},
        user_id=current_user.id
    )

    return {"status": "deleted", "id": contact_id}

@router.post("/trusted-contacts/generate-alert", response_model=TrustedContactAlertResponse)
def generate_contact_alert(
    payload: TrustedContactAlertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a pre-formatted emergency dispatch text and WhatsApp share URL.
    Ensures no unsolicited or automated messages are dispatched without user action.
    """
    contact = db.query(TrustedContact).filter(
        TrustedContact.id == payload.contact_id,
        TrustedContact.user_id == current_user.id
    ).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trusted contact not found.")

    user_name = current_user.profile.full_name if current_user.profile else "Your Family Member"

    alert_data = demographic_safety_engine.generate_trusted_contact_alert(
        contact_name=contact.name,
        phone_number=contact.phone_number,
        user_name=user_name,
        incident_type=payload.incident_type,
        incident_details=payload.incident_details
    )

    return TrustedContactAlertResponse(
        contact_name=alert_data["contact_name"],
        phone_number=alert_data["phone_number"],
        draft_sms_text=alert_data["draft_sms_text"],
        whatsapp_share_url=alert_data["whatsapp_share_url"]
    )

