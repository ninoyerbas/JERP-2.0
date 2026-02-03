"""
JERP 2.0 - User Schemas
Pydantic models for user management
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user fields"""
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation request"""
    password: str
    role_id: Optional[int] = None


class UserUpdate(BaseModel):
    """User update request - all fields optional"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class UserResponse(UserBase):
    """User response with all fields"""
    id: int
    is_superuser: bool
    role_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True
