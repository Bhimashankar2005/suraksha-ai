from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_user, require_admin, record_audit_log
from backend.app.models.user import User
from backend.app.services.notification_service import notification_service
from backend.app.schemas.notification import (
    NotificationItem,
    NotificationListResponse,
    UnreadCountResponse,
    BroadcastNotificationRequest,
    BroadcastNotificationResponse
)

router = APIRouter()

@router.get("", response_model=NotificationListResponse)
def get_user_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns the authenticated citizen's notification feed with pagination and unread counts.
    """
    items = notification_service.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        skip=skip
    )
    total = notification_service.get_total_count(db=db, user_id=current_user.id, unread_only=unread_only)
    unread_count = notification_service.get_unread_count(db=db, user_id=current_user.id)

    return NotificationListResponse(
        total=total,
        unread_count=unread_count,
        items=[
            NotificationItem(
                id=n.id,
                title=n.title,
                message=n.message,
                category=n.category,
                is_read=n.is_read,
                action_url=n.action_url,
                created_at=n.created_at
            )
            for n in items
        ]
    )

@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lightweight endpoint for polling or displaying unread notification badge counter.
    """
    count = notification_service.get_unread_count(db=db, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)

@router.post("/{notification_id}/read", response_model=NotificationItem)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks a single notification as read.
    """
    updated = notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    return NotificationItem(
        id=updated.id,
        title=updated.title,
        message=updated.message,
        category=updated.category,
        is_read=updated.is_read,
        action_url=updated.action_url,
        created_at=updated.created_at
    )

@router.post("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks all notifications for the authenticated citizen as read.
    """
    count = notification_service.mark_all_as_read(db=db, user_id=current_user.id)
    return {"status": "success", "marked_read_count": count}

@router.delete("/{notification_id}")
def delete_user_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a notification from the citizen's feed.
    """
    deleted = notification_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )

    return {"status": "success", "message": "Notification deleted."}

@router.post("/admin/broadcast", response_model=BroadcastNotificationResponse)
def broadcast_admin_notification(
    payload: BroadcastNotificationRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin)
):
    """
    Administrator endpoint to broadcast high-priority security warnings or announcements to all active platform users.
    """
    count = notification_service.broadcast_notification(
        db=db,
        title=payload.title,
        message=payload.message,
        category=payload.category,
        action_url=payload.action_url
    )

    record_audit_log(
        db=db,
        action="BROADCAST_NOTIFICATION",
        resource_type="NOTIFICATION",
        resource_id="ALL_ACTIVE_USERS",
        details={"title": payload.title, "recipients": count, "category": payload.category},
        user_id=admin_user.id
    )

    return BroadcastNotificationResponse(
        recipient_count=count,
        title=payload.title,
        status="broadcasted"
    )

