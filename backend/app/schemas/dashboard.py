from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ActivityItem(BaseModel):
    id: str
    activity_type: str  # SCAM_SCAN, URL_SCAN, IMAGE_SCAN, REPORT_SUBMISSION
    title: str
    risk_level: Optional[str] = None
    status: Optional[str] = None
    created_at: datetime

class NotificationSummary(BaseModel):
    id: str
    title: str
    message: str
    category: str
    is_read: bool
    created_at: datetime

class UserDashboardResponse(BaseModel):
    total_scans: int
    suspicious_detections: int
    submitted_reports: int
    pending_reports: int
    verified_reports: int
    recent_activity: List[ActivityItem]
    notifications: List[NotificationSummary]

class AdminActionSummary(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    admin_email: Optional[str] = None
    created_at: datetime

class AdminDashboardResponse(BaseModel):
    total_users: int
    active_users: int
    suspended_users: int
    total_reports: int
    pending_reports: int
    verified_reports: int
    rejected_reports: int
    duplicate_reports: int
    total_scans: int
    suspicious_urls: int
    threat_categories: Dict[str, int]
    recent_admin_actions: List[AdminActionSummary]

