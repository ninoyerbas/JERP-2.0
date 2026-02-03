"""
JERP 2.0 - API Dependencies
Security dependencies for authentication and authorization
"""
from typing import List, Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.api.v1.exceptions import UnauthorizedException, ForbiddenException


# HTTPBearer for token extraction
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate JWT token, return User object.
    Raises 401 for invalid/expired tokens.
    """
    token = credentials.credentials
    
    # Decode token
    token_data = decode_token(token)
    if token_data is None or token_data.user_id is None:
        raise UnauthorizedException(detail="Invalid or expired token")
    
    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise UnauthorizedException(detail="User not found")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify user is active.
    Raises 403 if user is inactive.
    """
    if not current_user.is_active:
        raise ForbiddenException(detail="Inactive user")
    
    return current_user


async def require_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Require superuser access.
    Raises 403 for non-superusers.
    """
    if not current_user.is_superuser:
        raise ForbiddenException(detail="Superuser access required")
    
    return current_user


def require_permissions(*required_permissions: str) -> Callable:
    """
    Permission-based access control dependency.
    Returns a dependency function that checks if user has required permissions.
    
    Usage:
        @router.get("/endpoint", dependencies=[Depends(require_permissions("user.read", "user.write"))])
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Superusers bypass permission checks
        if current_user.is_superuser:
            return current_user
        
        # Get user's role and permissions
        if not current_user.role:
            raise ForbiddenException(detail="User has no role assigned")
        
        # Get permission codes from user's role
        user_permission_codes = {perm.code for perm in current_user.role.permissions}
        
        # Check if user has all required permissions
        missing_permissions = set(required_permissions) - user_permission_codes
        if missing_permissions:
            raise ForbiddenException(
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


# Re-export get_db for convenience
__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "require_superuser",
    "require_permissions",
]
