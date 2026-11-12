from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.chat import ChatRequest, ChatResponse, AssistantStatus, HelplineContact
from backend.app.ml.assistant_engine import assistant_engine
from backend.app.core.config import settings

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
def send_chat_message(request: ChatRequest):
    """
    Multilingual AI Cyber Assistant endpoint.
    Processes user query in English, Kannada, or Hindi.
    Returns authoritative safety guidance with emergency helpline links.
    """
    result = assistant_engine.get_assistant_reply(
        message=request.message,
        language=request.language,
        conversation_history=[item.model_dump() for item in request.conversation_history] if request.conversation_history else None
    )

    emergency_contacts = [
        HelplineContact(
            name=c["name"],
            number=c["number"],
            portal=c.get("portal"),
            description=c["description"],
            operating_hours=c["operating_hours"]
        )
        for c in result["emergency_contacts"]
    ]

    return ChatResponse(
        reply=result["reply"],
        language=result["language"],
        provider=result["provider"],
        detected_topic=result["detected_topic"],
        safety_warning=result["safety_warning"],
        quick_actions=result["quick_actions"],
        emergency_contacts=emergency_contacts
    )

@router.get("/resources", response_model=List[HelplineContact])
def get_verified_resources():
    """
    Returns verified official Indian cyber crime reporting hotlines and safety portals.
    """
    return [
        HelplineContact(
            name=c["name"],
            number=c["number"],
            portal=c.get("portal"),
            description=c["description"],
            operating_hours=c["operating_hours"]
        )
        for c in assistant_engine.OFFICIAL_HELPLINES
    ]

@router.get("/status", response_model=AssistantStatus)
def get_assistant_status():
    """
    Returns runtime operational telemetry for the AI Assistant.
    Reports whether local Ollama engine is reachable or if the verified fallback rulebook is active.
    """
    is_available, model_name = assistant_engine.check_ollama_availability()
    return AssistantStatus(
        ollama_available=is_available,
        configured_model=model_name if is_available else "Deterministic Trilingual Fallback Engine",
        base_url=settings.OLLAMA_BASE_URL,
        fallback_active=not is_available,
        supported_languages=["en", "kn", "hi"]
    )

