"""
JERP 2.0 - Authentication Service
Business logic for authentication operations
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.audit_log import AuditLog
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """Authenticate user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def create_user_tokens(user: User) -> Tuple[str, str]:
    """Generate access and refresh tokens for a user."""
    token_data = {
        "sub": user.id,
        "email": user.email,
        "role": user.role.name if user.role else None,
        "permissions": [p.code for p in user.role.permissions] if user.role else []
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})
    
    return access_token, refresh_token


def refresh_user_token(refresh_token: str, db: Session) -> Tuple[str, str]:
    """Validate refresh token and generate new tokens."""
    # Verify it's a refresh token
    if not verify_token_type(refresh_token, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Decode token
    token_data = decode_token(refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    return create_user_tokens(user)


def create_audit_log(
    db: Session,
    user_id: Optional[int],
    user_email: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """Create an audit log entry with proper hash chaining."""
    # Get the last audit log for hash chaining
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last_log.current_hash if last_log else None
    
    # Create the audit log entry
    audit_log = AuditLog.create_entry(
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_values=old_values,
        new_values=new_values,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        previous_hash=previous_hash
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log
