from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from backend.app.models.safety_education import Notification
from backend.app.models.user import User

class NotificationService:
    """Service handling in-app notifications, threat alert broadcasts, and status tracking."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        title: str,
        message: str,
        category: str = "SECURITY_ALERT",
        action_url: Optional[str] = None
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            category=category,
            is_read=False,
            action_url=action_url,
            created_at=datetime.now(timezone.utc)
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def broadcast_notification(
        db: Session,
        title: str,
        message: str,
        category: str = "SECURITY_ALERT",
        action_url: Optional[str] = None
    ) -> int:
        """Broadcasts a notification to all active citizens in the platform."""
        active_users = db.query(User.id).filter(User.is_active == True).all()
        now = datetime.now(timezone.utc)
        notifications = [
            Notification(
                user_id=u[0],
                title=title,
                message=message,
                category=category,
                is_read=False,
                action_url=action_url,
                created_at=now
            )
            for u in active_users
        ]
        if notifications:
            db.bulk_save_objects(notifications)
            db.commit()
        return len(notifications)

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        skip: int = 0
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_total_count(db: Session, user_id: str, unread_only: bool = False) -> int:
        query = db.query(func.count(Notification.id)).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.scalar() or 0

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        return db.query(func.count(Notification.id)).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).scalar() or 0

    @staticmethod
    def mark_as_read(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: str) -> int:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        db.commit()
        return count

    @staticmethod
    def delete_notification(db: Session, notification_id: str, user_id: str) -> bool:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False

notification_service = NotificationService()

