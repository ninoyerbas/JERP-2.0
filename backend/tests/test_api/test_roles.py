"""
JERP 2.0 - Role & Permission Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.role import Role, Permission


def test_list_roles(client: TestClient, auth_headers: dict):
    """Test listing roles"""
    response = client.get("/api/v1/roles", headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_role(client: TestClient, superuser_auth_headers: dict):
    """Test creating a role"""
    response = client.post(
        "/api/v1/roles",
        headers=superuser_auth_headers,
        json={
            "name": "New Role",
            "description": "A new test role",
            "is_active": True,
            "permission_ids": []
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Role"
    assert data["description"] == "A new test role"


def test_create_role_non_admin(client: TestClient, auth_headers: dict):
    """Test creating role as non-admin (should fail)"""
    response = client.post(
        "/api/v1/roles",
        headers=auth_headers,
        json={
            "name": "New Role",
            "description": "Test",
            "is_active": True
        }
    )
    
    assert response.status_code == 403


def test_create_role_duplicate_name(client: TestClient, test_role: Role, superuser_auth_headers: dict):
    """Test creating role with duplicate name"""
    response = client.post(
        "/api/v1/roles",
        headers=superuser_auth_headers,
        json={
            "name": test_role.name,
            "description": "Duplicate",
            "is_active": True
        }
    )
    
    assert response.status_code == 409


def test_get_role(client: TestClient, test_role: Role, auth_headers: dict):
    """Test getting a specific role"""
    response = client.get(f"/api/v1/roles/{test_role.id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_role.id
    assert data["name"] == test_role.name


def test_get_role_not_found(client: TestClient, auth_headers: dict):
    """Test getting non-existent role"""
    response = client.get("/api/v1/roles/99999", headers=auth_headers)
    
    assert response.status_code == 404


def test_update_role(client: TestClient, test_role: Role, superuser_auth_headers: dict):
    """Test updating a role"""
    response = client.put(
        f"/api/v1/roles/{test_role.id}",
        headers=superuser_auth_headers,
        json={
            "name": "Updated Role",
            "description": "Updated description"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Role"
    assert data["description"] == "Updated description"


def test_update_role_non_admin(client: TestClient, test_role: Role, auth_headers: dict):
    """Test updating role as non-admin (should fail)"""
    response = client.put(
        f"/api/v1/roles/{test_role.id}",
        headers=auth_headers,
        json={"name": "Hacked"}
    )
    
    assert response.status_code == 403


def test_delete_role(client: TestClient, db: Session, superuser_auth_headers: dict):
    """Test deleting a role"""
    # Create a role without users
    role = Role(name="To Delete", description="Test", is_active=True)
    db.add(role)
    db.commit()
    db.refresh(role)
    
    response = client.delete(
        f"/api/v1/roles/{role.id}",
        headers=superuser_auth_headers
    )
    
    assert response.status_code == 200


def test_delete_role_with_users(client: TestClient, test_role: Role, test_user: User, superuser_auth_headers: dict, db: Session):
    """Test deleting role with active users (should fail)"""
    # Assign role to user
    test_user.role_id = test_role.id
    db.commit()
    
    response = client.delete(
        f"/api/v1/roles/{test_role.id}",
        headers=superuser_auth_headers
    )
    
    assert response.status_code == 400


def test_get_role_users(client: TestClient, test_role: Role, test_user: User, auth_headers: dict, db: Session):
    """Test getting users with specific role"""
    # Assign role to user
    test_user.role_id = test_role.id
    db.commit()
    
    response = client.get(
        f"/api/v1/roles/{test_role.id}/users",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_list_permissions(client: TestClient, auth_headers: dict):
    """Test listing permissions"""
    response = client.get("/api/v1/roles/permissions/list", headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_permission(client: TestClient, superuser_auth_headers: dict):
    """Test creating a permission"""
    response = client.post(
        "/api/v1/roles/permissions/create",
        headers=superuser_auth_headers,
        json={
            "code": "test.permission",
            "name": "Test Permission",
            "description": "A test permission",
            "module": "test"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "test.permission"
    assert data["name"] == "Test Permission"


def test_create_permission_non_admin(client: TestClient, auth_headers: dict):
    """Test creating permission as non-admin (should fail)"""
    response = client.post(
        "/api/v1/roles/permissions/create",
        headers=auth_headers,
        json={
            "code": "test.permission",
            "name": "Test Permission",
            "module": "test"
        }
    )
    
    assert response.status_code == 403


def test_create_permission_duplicate_code(client: TestClient, db: Session, superuser_auth_headers: dict):
    """Test creating permission with duplicate code"""
    # Create first permission
    perm = Permission(
        code="duplicate.code",
        name="First",
        module="test"
    )
    db.add(perm)
    db.commit()
    
    response = client.post(
        "/api/v1/roles/permissions/create",
        headers=superuser_auth_headers,
        json={
            "code": "duplicate.code",
            "name": "Second",
            "module": "test"
        }
    )
    
    assert response.status_code == 409
