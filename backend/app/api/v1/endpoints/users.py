"""
JERP 2.0 - User Management Endpoints
CRUD operations for user administration
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.api.v1.dependencies import get_current_active_user, require_superuser
from app.api.v1.exceptions import NotFoundException, ConflictException, BadRequestException


router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    email: Optional[str] = Query(None),
    role_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List users with pagination and filtering.
    Available to any authenticated user.
    """
    # Build query
    query = db.query(User)
    
    # Apply filters
    if email:
        query = query.filter(User.email.contains(email))
    if role_id is not None:
        query = query.filter(User.role_id == role_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    if hasattr(User, sort_by):
        sort_column = getattr(User, sort_by)
        if order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return UserListResponse(
        total=total,
        items=[UserResponse.model_validate(user) for user in users]
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    request: Request,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only).
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ConflictException(detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role_id=user_data.role_id,
        is_active=True,
        is_superuser=False
    )
    
    db.add(new_user)
    db.flush()
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="user",
        resource_id=str(new_user.id),
        old_values=None,
        new_values={
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role_id": new_user.role_id
        },
        description=f"Admin created user: {new_user.email}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    Available to any authenticated user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(detail="User not found")
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user.
    Admin can update any field. Users can update their own limited fields.
    """
    # Get user to update
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(detail="User not found")
    
    # Store old values for audit
    old_values = {
        "email": user.email,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "is_active": user.is_active
    }
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Permission check: users can only update themselves (limited fields)
    if user_id != current_user.id and not current_user.is_superuser:
        raise BadRequestException(detail="Cannot update other users")
    
    # Non-superusers can only update certain fields
    if not current_user.is_superuser:
        restricted_fields = ["role_id", "is_active"]
        for field in restricted_fields:
            if field in update_data:
                raise BadRequestException(detail=f"Cannot update field: {field}")
    
    # Check if email already exists (if being changed)
    if "email" in update_data and update_data["email"] != user.email:
        existing_user = db.query(User).filter(User.email == update_data["email"]).first()
        if existing_user:
            raise ConflictException(detail="Email already in use")
    
    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    new_values = {k: getattr(user, k) for k in update_data.keys()}
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="user",
        resource_id=str(user.id),
        old_values=old_values,
        new_values=new_values,
        description=f"User {user.email} updated",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Soft delete user (admin only).
    Sets is_active to False instead of deleting the record.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(detail="User not found")
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise BadRequestException(detail="Cannot delete your own account")
    
    # Store old value
    old_is_active = user.is_active
    
    # Soft delete by deactivating
    user.is_active = False
    db.commit()
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="DELETE",
        resource_type="user",
        resource_id=str(user.id),
        old_values={"is_active": old_is_active},
        new_values={"is_active": False},
        description=f"User {user.email} deactivated",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "User deactivated successfully"}


@router.get("/{user_id}/audit-logs", response_model=AuditLogListResponse)
async def get_user_audit_logs(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get audit log history for a specific user.
    Users can view their own logs. Admins can view any user's logs.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(detail="User not found")
    
    # Permission check: users can only view their own logs
    if user_id != current_user.id and not current_user.is_superuser:
        raise BadRequestException(detail="Cannot view other users' audit logs")
    
    # Query audit logs
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)
    total = query.count()
    
    # Apply pagination and order by most recent first
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        total=total,
        items=[AuditLogResponse.model_validate(log) for log in logs]
    )
