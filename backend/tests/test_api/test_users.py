"""
JERP 2.0 - User Management Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User


def test_list_users(client: TestClient, test_user: User, auth_headers: dict):
    """Test listing users"""
    response = client.get("/api/v1/users", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) > 0


def test_list_users_with_filters(client: TestClient, test_user: User, auth_headers: dict):
    """Test listing users with filters"""
    response = client.get(
        "/api/v1/users",
        headers=auth_headers,
        params={"email": test_user.email, "is_active": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_create_user(client: TestClient, superuser_auth_headers: dict):
    """Test creating a user (admin only)"""
    response = client.post(
        "/api/v1/users",
        headers=superuser_auth_headers,
        json={
            "email": "created@example.com",
            "password": "password123",
            "full_name": "Created User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "created@example.com"
    assert data["full_name"] == "Created User"


def test_create_user_non_admin(client: TestClient, auth_headers: dict):
    """Test creating a user as non-admin (should fail)"""
    response = client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={
            "email": "created@example.com",
            "password": "password123",
            "full_name": "Created User"
        }
    )
    
    assert response.status_code == 403


def test_create_user_duplicate_email(client: TestClient, test_user: User, superuser_auth_headers: dict):
    """Test creating user with duplicate email"""
    response = client.post(
        "/api/v1/users",
        headers=superuser_auth_headers,
        json={
            "email": test_user.email,
            "password": "password123",
            "full_name": "Duplicate"
        }
    )
    
    assert response.status_code == 409


def test_get_user(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting a specific user"""
    response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


def test_get_user_not_found(client: TestClient, auth_headers: dict):
    """Test getting non-existent user"""
    response = client.get("/api/v1/users/99999", headers=auth_headers)
    
    assert response.status_code == 404


def test_update_user_self(client: TestClient, test_user: User, auth_headers: dict):
    """Test updating own user profile"""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        headers=auth_headers,
        json={"full_name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_update_user_other_non_admin(client: TestClient, test_superuser: User, auth_headers: dict):
    """Test updating other user as non-admin (should fail)"""
    response = client.put(
        f"/api/v1/users/{test_superuser.id}",
        headers=auth_headers,
        json={"full_name": "Hacked Name"}
    )
    
    assert response.status_code == 400


def test_update_user_admin(client: TestClient, test_user: User, superuser_auth_headers: dict):
    """Test updating user as admin"""
    response = client.put(
        f"/api/v1/users/{test_user.id}",
        headers=superuser_auth_headers,
        json={
            "full_name": "Admin Updated",
            "is_active": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Admin Updated"
    assert data["is_active"] is False


def test_delete_user(client: TestClient, test_user: User, superuser_auth_headers: dict):
    """Test soft deleting a user"""
    response = client.delete(
        f"/api/v1/users/{test_user.id}",
        headers=superuser_auth_headers
    )
    
    assert response.status_code == 200
    
    # Verify user is deactivated
    get_response = client.get(
        f"/api/v1/users/{test_user.id}",
        headers=superuser_auth_headers
    )
    assert get_response.json()["is_active"] is False


def test_delete_user_non_admin(client: TestClient, test_superuser: User, auth_headers: dict):
    """Test deleting user as non-admin (should fail)"""
    response = client.delete(
        f"/api/v1/users/{test_superuser.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 403


def test_get_user_audit_logs(client: TestClient, test_user: User, auth_headers: dict):
    """Test getting user's audit logs"""
    response = client.get(
        f"/api/v1/users/{test_user.id}/audit-logs",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_get_other_user_audit_logs_non_admin(client: TestClient, test_superuser: User, auth_headers: dict):
    """Test getting other user's audit logs as non-admin (should fail)"""
    response = client.get(
        f"/api/v1/users/{test_superuser.id}/audit-logs",
        headers=auth_headers
    )
    
    assert response.status_code == 400
