"""
JERP 2.0 - Role & Permission Schemas
Pydantic models for RBAC (Role-Based Access Control)
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


class PermissionBase(BaseModel):
    """Base permission schema"""
    code: str
    name: str
    description: Optional[str] = None
    module: str


class PermissionResponse(PermissionBase):
    """Permission response with ID and timestamp"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema"""
    name: str
    description: Optional[str] = None
    is_active: bool = True


class RoleCreate(RoleBase):
    """Role creation schema with permissions"""
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    """Role update schema - all fields optional"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(RoleBase):
    """Role response with ID, timestamps, and permissions"""
    id: int
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True
