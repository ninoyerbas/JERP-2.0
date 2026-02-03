"""
JERP 2.0 - Role & Permission Schemas
Pydantic models for RBAC management
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PermissionBase(BaseModel):
    """Base permission fields"""
    code: str
    name: str
    description: Optional[str] = None
    module: str


class PermissionCreate(PermissionBase):
    """Permission creation request"""
    pass


class PermissionResponse(PermissionBase):
    """Permission response with all fields"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role fields"""
    name: str
    description: Optional[str] = None
    is_active: bool = True


class RoleCreate(RoleBase):
    """Role creation request"""
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    """Role update request - all fields optional"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(RoleBase):
    """Role response with permissions"""
    id: int
    created_at: datetime
    updated_at: datetime
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True
