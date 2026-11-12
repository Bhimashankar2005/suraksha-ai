from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime, timezone

class ChatMessageItem(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's query or statement")
    language: Literal["en", "kn", "hi"] = Field(default="en", description="Preferred response language: en, kn, or hi")
    conversation_history: Optional[List[ChatMessageItem]] = Field(default=None, description="Previous conversation turns")

class HelplineContact(BaseModel):
    name: str
    number: str
    portal: Optional[str] = None
    description: str
    operating_hours: str

class ChatResponse(BaseModel):
    reply: str
    language: str
    provider: Literal["ollama", "deterministic_fallback"]
    detected_topic: str
    safety_warning: Optional[str] = None
    quick_actions: List[str] = []
    emergency_contacts: List[HelplineContact] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AssistantStatus(BaseModel):
    ollama_available: bool
    configured_model: str
    base_url: str
    fallback_active: bool
    supported_languages: List[str] = ["en", "kn", "hi"]

