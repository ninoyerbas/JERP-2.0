"""
JERP 2.0 - Authentication Dependencies Tests
"""
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.v1.dependencies import (
    get_current_user,
    get_current_active_user,
    require_superuser
)
from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_user_valid_token(db: Session, test_user: User):
    """Test getting current user with valid token"""
    token = create_access_token({
        "sub": test_user.id,
        "email": test_user.email
    })
    
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )
    
    user = await get_current_user(credentials, db)
    
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db: Session):
    """Test getting current user with invalid token"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid_token"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, db)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_active_user_active(test_user: User):
    """Test getting current active user when user is active"""
    user = await get_current_active_user(test_user)
    
    assert user.id == test_user.id
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_current_active_user_inactive(db: Session):
    """Test getting current active user when user is inactive"""
    inactive_user = User(
        email="inactive@example.com",
        hashed_password="hash",
        is_active=False
    )
    db.add(inactive_user)
    db.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_active_user(inactive_user)
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_superuser_valid(test_superuser: User):
    """Test require superuser with superuser"""
    user = await require_superuser(test_superuser)
    
    assert user.is_superuser is True


@pytest.mark.asyncio
async def test_require_superuser_invalid(test_user: User):
    """Test require superuser with non-superuser"""
    with pytest.raises(HTTPException) as exc_info:
        await require_superuser(test_user)
    
    assert exc_info.value.status_code == 403
