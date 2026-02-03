"""
JERP 2.0 - User Service
Business logic for user management operations
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import create_audit_log


def create_user(
    user_data: UserCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """Create a new user with audit logging."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role if provided
    if user_data.role_id:
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        role_id=user_data.role_id
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="user",
        resource_id=str(user.id),
        new_values={
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "role_id": user.role_id
        },
        description=f"Created user {user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return user


def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> User:
    """Update user with audit logging."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store old values
    old_values = {
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role_id": user.role_id
    }
    
    # Update fields
    if user_data.email is not None:
        # Check if email is already taken
        existing = db.query(User).filter(
            User.email == user_data.email,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_data.email
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    if user_data.role_id is not None:
        # Validate role
        role = db.query(Role).filter(Role.id == user_data.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        user.role_id = user_data.role_id
    
    db.commit()
    db.refresh(user)
    
    # Create audit log
    new_values = {
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "role_id": user.role_id
    }
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="user",
        resource_id=str(user.id),
        old_values=old_values,
        new_values=new_values,
        description=f"Updated user {user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return user


def delete_user(
    user_id: int,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Delete user with audit logging (soft delete by deactivating)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store old values
    old_values = {
        "email": user.email,
        "is_active": user.is_active
    }
    
    # Soft delete by deactivating
    user.is_active = False
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="DELETE",
        resource_type="user",
        resource_id=str(user.id),
        old_values=old_values,
        new_values={"is_active": False},
        description=f"Deleted (deactivated) user {user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
