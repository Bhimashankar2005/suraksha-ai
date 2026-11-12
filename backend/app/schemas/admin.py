from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AdminUserListItem(BaseModel):
    id: str
    email: str
    role: str
    role_id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    scans_count: int
    reports_count: int
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class AdminUserUpdateRoleRequest(BaseModel):
    role_name: str = Field(..., description="Role to assign: USER, ADMIN, or COMMUNITY_MODERATOR")

class AdminUserStatusToggleRequest(BaseModel):
    is_active: bool

class AuditLogListItem(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    created_at: datetime

class SystemHealthTelemetry(BaseModel):
    database: str
    total_users: int
    active_users: int
    total_scans: int
    total_reports: int
    verified_threats: int
    total_evidence_files: int
    evidence_vault_bytes: int
    active_threat_indicators: int
    recent_security_events: int
    audit_logs_count: int
    uptime_status: str

class AdminThreatItem(BaseModel):
    id: str
    indicator_type: str
    indicator_value: str
    threat_level: str
    description: str
    incident_count: int
    is_active: bool
    origin_report_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class AdminThreatUpdateRequest(BaseModel):
    threat_level: Optional[str] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

