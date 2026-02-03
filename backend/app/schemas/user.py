"""
JERP 2.0 - User Schemas
Pydantic models for user management
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema with password"""
    password: str
    role_id: Optional[int] = None


class UserUpdate(BaseModel):
    """User update schema - all fields optional"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response with full details"""
    id: int
    is_active: bool
    is_superuser: bool
    role_id: Optional[int] = None
    role: Optional['RoleResponse'] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response"""
    total: int
    items: List[UserResponse]


# Import RoleResponse for forward reference
from app.schemas.role import RoleResponse  # noqa: E402
UserResponse.model_rebuild()
