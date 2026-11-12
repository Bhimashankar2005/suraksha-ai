from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NotificationItem(BaseModel):
    id: str
    title: str
    message: str
    category: str
    is_read: bool
    action_url: Optional[str] = None
    created_at: datetime

class NotificationListResponse(BaseModel):
    total: int
    unread_count: int
    items: List[NotificationItem]

class UnreadCountResponse(BaseModel):
    unread_count: int

class BroadcastNotificationRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=5, max_length=2000)
    category: str = Field(default="SECURITY_ALERT")
    action_url: Optional[str] = Field(default=None, max_length=255)

class BroadcastNotificationResponse(BaseModel):
    recipient_count: int
    title: str
    status: str

