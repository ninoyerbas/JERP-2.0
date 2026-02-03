"""
JERP 2.0 - Authentication Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_register_user(client: TestClient, db: Session):
    """Test user registration"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient, test_user: User):
    """Test registration with existing email"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "password123",
            "full_name": "Duplicate User"
        }
    )
    
    assert response.status_code == 409
    assert "already registered" in response.json()["error"]["message"].lower()


def test_login_success(client: TestClient, test_user: User):
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == test_user.email
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_credentials(client: TestClient, test_user: User):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent user"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401


def test_get_current_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting current user info"""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without auth"""
    response = client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # No credentials provided


def test_update_current_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test updating current user profile"""
    response = client.put(
        "/api/v1/auth/me",
        headers=auth_headers,
        json={
            "full_name": "Updated Name"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_change_password(client: TestClient, test_user: User, auth_headers: dict):
    """Test changing password"""
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "testpassword123",
            "new_password": "newpassword123"
        }
    )
    
    assert response.status_code == 200
    
    # Try logging in with new password
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "newpassword123"
        }
    )
    
    assert login_response.status_code == 200


def test_change_password_wrong_old_password(client: TestClient, auth_headers: dict):
    """Test changing password with wrong old password"""
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "old_password": "wrongpassword",
            "new_password": "newpassword123"
        }
    )
    
    assert response.status_code == 400


def test_refresh_token(client: TestClient, test_user: User):
    """Test token refresh"""
    # First login to get tokens
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_logout(client: TestClient, auth_headers: dict):
    """Test logout"""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    
    assert response.status_code == 200
    assert "message" in response.json()
