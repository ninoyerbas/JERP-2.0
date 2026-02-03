"""
JERP 2.0 - Audit Log Schemas
Pydantic models for audit trail and compliance
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Audit log entry response"""
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    previous_hash: Optional[str] = None
    current_hash: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response"""
    total: int
    items: List[AuditLogResponse]


class AuditLogQueryParams(BaseModel):
    """Query parameters for filtering audit logs"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = 0
    limit: int = 100
