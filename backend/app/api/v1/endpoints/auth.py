"""
JERP 2.0 - Authentication Endpoints
User authentication and authorization API
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest
)
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_user_tokens,
    refresh_user_token,
    create_audit_log
)

router = APIRouter()


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user account."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=user.id,
        user_email=user.email,
        action="REGISTER",
        resource_type="user",
        resource_id=str(user.id),
        new_values={"email": user.email, "full_name": user.full_name},
        description=f"User registered: {user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""
    user = authenticate_user(login_data.email, login_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate tokens
    access_token, refresh_token = create_user_tokens(user)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=user.id,
        user_email=user.email,
        action="LOGIN",
        resource_type="auth",
        description=f"User logged in: {user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/login/form", response_model=TokenResponse)
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible login endpoint for Swagger UI."""
    user = authenticate_user(form_data.username, form_data.password, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate tokens
    access_token, refresh_token = create_user_tokens(user)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=user.id,
        user_email=user.email,
        action="LOGIN",
        resource_type="auth",
        description=f"User logged in: {user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    access_token, new_refresh_token = refresh_user_token(refresh_data.refresh_token, db)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout current user (creates audit log entry)."""
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="LOGOUT",
        resource_type="auth",
        description=f"User logged out: {current_user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {"message": "Successfully logged out"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CHANGE_PASSWORD",
        resource_type="auth",
        resource_id=str(current_user.id),
        description=f"User changed password: {current_user.email}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information."""
    return current_user
