"""
Tests for Database Initialization

Tests the database initialization script to ensure:
- Default roles are created
- Default permissions are created
- Permissions are assigned to roles correctly
- Initial superuser is created
- Script is idempotent (can run multiple times)
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings
from app.models.user import User
from app.models.role import Role, Permission
from app.scripts.init_db import (
    create_default_roles,
    create_default_permissions,
    assign_permissions_to_roles,
    create_initial_superuser,
    DEFAULT_ROLES,
    DEFAULT_PERMISSIONS,
    ROLE_PERMISSION_MAPPING
)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test"""
    # Create test database engine
    test_db_url = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/test_jerp"
    engine = create_engine(test_db_url, echo=False)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_create_default_roles(test_db):
    """Test that default roles are created correctly"""
    # Create roles
    roles = create_default_roles(test_db)
    
    # Verify all default roles were created
    assert len(roles) == len(DEFAULT_ROLES)
    
    # Verify each role
    for role_data in DEFAULT_ROLES:
        role_name = role_data["name"]
        assert role_name in roles
        
        role = roles[role_name]
        assert role.name == role_name
        assert role.description == role_data["description"]
        assert role.is_active is True
    
    # Verify roles exist in database
    db_roles = test_db.query(Role).all()
    assert len(db_roles) == len(DEFAULT_ROLES)


def test_create_default_roles_idempotent(test_db):
    """Test that creating roles multiple times doesn't duplicate"""
    # Create roles first time
    roles1 = create_default_roles(test_db)
    count1 = test_db.query(Role).count()
    
    # Create roles second time
    roles2 = create_default_roles(test_db)
    count2 = test_db.query(Role).count()
    
    # Should have same count
    assert count1 == count2
    assert count1 == len(DEFAULT_ROLES)
    
    # Role IDs should be the same
    for role_name in roles1.keys():
        assert roles1[role_name].id == roles2[role_name].id


def test_create_default_permissions(test_db):
    """Test that default permissions are created correctly"""
    # Create permissions
    permissions = create_default_permissions(test_db)
    
    # Verify all default permissions were created
    assert len(permissions) == len(DEFAULT_PERMISSIONS)
    
    # Verify each permission
    for perm_data in DEFAULT_PERMISSIONS:
        perm_code = perm_data["code"]
        assert perm_code in permissions
        
        permission = permissions[perm_code]
        assert permission.code == perm_code
        assert permission.name == perm_data["name"]
        assert permission.module == perm_data["module"]
    
    # Verify permissions exist in database
    db_permissions = test_db.query(Permission).all()
    assert len(db_permissions) == len(DEFAULT_PERMISSIONS)


def test_create_default_permissions_idempotent(test_db):
    """Test that creating permissions multiple times doesn't duplicate"""
    # Create permissions first time
    perms1 = create_default_permissions(test_db)
    count1 = test_db.query(Permission).count()
    
    # Create permissions second time
    perms2 = create_default_permissions(test_db)
    count2 = test_db.query(Permission).count()
    
    # Should have same count
    assert count1 == count2
    assert count1 == len(DEFAULT_PERMISSIONS)
    
    # Permission IDs should be the same
    for perm_code in perms1.keys():
        assert perms1[perm_code].id == perms2[perm_code].id


def test_assign_permissions_to_roles(test_db):
    """Test that permissions are correctly assigned to roles"""
    # Create roles and permissions
    roles = create_default_roles(test_db)
    permissions = create_default_permissions(test_db)
    
    # Assign permissions to roles
    assign_permissions_to_roles(test_db, roles, permissions)
    
    # Verify assignments
    for role_name, permission_codes in ROLE_PERMISSION_MAPPING.items():
        role = roles.get(role_name)
        assert role is not None
        
        # Get role permissions
        role_perms = {p.code for p in role.permissions}
        
        # Verify all expected permissions are assigned
        for perm_code in permission_codes:
            assert perm_code in role_perms, f"Permission {perm_code} not assigned to role {role_name}"


def test_superadmin_has_all_permissions(test_db):
    """Test that Superadmin role has all permissions"""
    # Create roles and permissions
    roles = create_default_roles(test_db)
    permissions = create_default_permissions(test_db)
    
    # Assign permissions
    assign_permissions_to_roles(test_db, roles, permissions)
    
    # Get Superadmin role
    superadmin = roles.get("Superadmin")
    assert superadmin is not None
    
    # Verify has all permissions from mapping
    expected_perms = set(ROLE_PERMISSION_MAPPING["Superadmin"])
    actual_perms = {p.code for p in superadmin.permissions}
    
    assert expected_perms.issubset(actual_perms)


def test_create_initial_superuser(test_db):
    """Test that initial superuser is created correctly"""
    # Set environment variables
    os.environ["INITIAL_SUPERUSER_EMAIL"] = "test@example.com"
    os.environ["INITIAL_SUPERUSER_PASSWORD"] = "testpass123"
    os.environ["INITIAL_SUPERUSER_NAME"] = "Test Admin"
    
    # Create roles first
    roles = create_default_roles(test_db)
    
    # Create superuser
    superuser = create_initial_superuser(test_db, roles)
    
    # Verify superuser
    assert superuser is not None
    assert superuser.email == "test@example.com"
    assert superuser.full_name == "Test Admin"
    assert superuser.is_active is True
    assert superuser.is_superuser is True
    assert superuser.role_id == roles["Superadmin"].id
    
    # Verify password was hashed (not plain text)
    assert superuser.hashed_password != "testpass123"
    assert len(superuser.hashed_password) > 20  # Bcrypt hashes are long
    
    # Verify superuser exists in database
    db_user = test_db.query(User).filter(User.email == "test@example.com").first()
    assert db_user is not None
    assert db_user.id == superuser.id


def test_create_initial_superuser_idempotent(test_db):
    """Test that creating superuser multiple times doesn't duplicate"""
    # Set environment variables
    os.environ["INITIAL_SUPERUSER_EMAIL"] = "test@example.com"
    os.environ["INITIAL_SUPERUSER_PASSWORD"] = "testpass123"
    os.environ["INITIAL_SUPERUSER_NAME"] = "Test Admin"
    
    # Create roles
    roles = create_default_roles(test_db)
    
    # Create superuser first time
    superuser1 = create_initial_superuser(test_db, roles)
    count1 = test_db.query(User).count()
    
    # Create superuser second time
    superuser2 = create_initial_superuser(test_db, roles)
    count2 = test_db.query(User).count()
    
    # Should have same count (only 1 user)
    assert count1 == count2 == 1
    
    # Should be the same user
    assert superuser1.id == superuser2.id


def test_user_role_has_limited_permissions(test_db):
    """Test that User role has only read permissions"""
    # Create roles and permissions
    roles = create_default_roles(test_db)
    permissions = create_default_permissions(test_db)
    
    # Assign permissions
    assign_permissions_to_roles(test_db, roles, permissions)
    
    # Get User role
    user_role = roles.get("User")
    assert user_role is not None
    
    # Get permissions
    user_perms = {p.code for p in user_role.permissions}
    
    # Verify has only read permissions
    expected_perms = set(ROLE_PERMISSION_MAPPING["User"])
    assert user_perms == expected_perms
    
    # Verify doesn't have write/delete permissions
    assert "user:create" not in user_perms
    assert "user:update" not in user_perms
    assert "user:delete" not in user_perms


def test_all_roles_exist(test_db):
    """Test that all expected roles are created"""
    roles = create_default_roles(test_db)
    
    expected_roles = ["Superadmin", "Admin", "Manager", "User"]
    for role_name in expected_roles:
        assert role_name in roles
        assert roles[role_name].name == role_name


def test_all_permission_modules_exist(test_db):
    """Test that permissions cover all expected modules"""
    permissions = create_default_permissions(test_db)
    
    # Get all modules
    modules = set(p.module for p in permissions.values())
    
    # Verify expected modules
    expected_modules = {"users", "roles", "audit", "compliance", "system"}
    assert expected_modules.issubset(modules)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
