"""
JERP 2.0 - Authentication Endpoints
User authentication, registration, and profile management
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
)
from app.schemas.user import UserResponse, UserUpdate
from app.api.v1.dependencies import get_current_active_user
from app.api.v1.exceptions import UnauthorizedException, ConflictException, BadRequestException


router = APIRouter()


def create_user_tokens(user: User) -> dict:
    """Helper function to create access and refresh tokens for a user"""
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "permissions": [perm.code for perm in user.role.permissions] if user.role else []
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    Returns JWT tokens and user information.
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
    db.flush()  # Get the user ID
    
    # Create audit log
    audit_log = AuditLog.create_entry(
        user_id=new_user.id,
        user_email=new_user.email,
        action="CREATE",
        resource_type="user",
        resource_id=str(new_user.id),
        old_values=None,
        new_values={"email": new_user.email, "full_name": new_user.full_name},
        description="User registration",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=None
    )
    db.add(audit_log)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    tokens = create_user_tokens(new_user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    Returns JWT tokens and user information.
    """
    # Find user by email
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise UnauthorizedException(detail="Invalid email or password")
    
    # Check if user is active
    if not user.is_active:
        raise UnauthorizedException(detail="Account is inactive")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=user.id,
        user_email=user.email,
        action="LOGIN",
        resource_type="auth",
        resource_id=str(user.id),
        old_values=None,
        new_values=None,
        description="User login",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    db.refresh(user)
    
    # Create tokens
    tokens = create_user_tokens(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    Returns new JWT tokens.
    """
    # Verify token is a refresh token
    if not verify_token_type(token_request.refresh_token, "refresh"):
        raise UnauthorizedException(detail="Invalid refresh token")
    
    # Decode refresh token
    token_data = decode_token(token_request.refresh_token)
    if token_data is None or token_data.user_id is None:
        raise UnauthorizedException(detail="Invalid or expired refresh token")
    
    # Get user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise UnauthorizedException(detail="User not found or inactive")
    
    # Create new tokens
    tokens = create_user_tokens(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user.
    Note: Token blacklisting not implemented yet - placeholder for future enhancement.
    """
    # Placeholder for token blacklisting implementation
    # In a production system, would add token to blacklist/cache
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    Users can only update their own limited fields (email, full_name).
    """
    # Store old values for audit
    old_values = {
        "email": current_user.email,
        "full_name": current_user.full_name
    }
    
    # Users can only update their own email and full_name
    # Other fields like role_id and is_active require admin privileges
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Restrict non-superusers from changing certain fields
    if not current_user.is_superuser:
        restricted_fields = ["role_id", "is_active"]
        for field in restricted_fields:
            if field in update_data:
                raise BadRequestException(detail=f"Cannot update field: {field}")
    
    # Check if email already exists (if being changed)
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = db.query(User).filter(User.email == update_data["email"]).first()
        if existing_user:
            raise ConflictException(detail="Email already in use")
    
    # Update user
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    new_values = {k: getattr(current_user, k) for k in update_data.keys()}
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="user",
        resource_id=str(current_user.id),
        old_values=old_values,
        new_values=new_values,
        description="User profile update",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change password for current user"""
    # Verify old password
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise BadRequestException(detail="Invalid old password")
    
    # Hash and update new password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="user",
        resource_id=str(current_user.id),
        old_values=None,
        new_values=None,
        description="Password changed",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Password changed successfully"}
