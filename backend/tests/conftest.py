"""
JERP 2.0 - Test Configuration
Pytest fixtures and configuration for API testing
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.role import Role, Permission


# Test database URL (SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """
    Create a test user.
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_superuser(db: Session) -> User:
    """
    Create a test superuser.
    """
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_role(db: Session) -> Role:
    """
    Create a test role with permissions.
    """
    # Create permissions
    perm1 = Permission(
        code="user.read",
        name="Read Users",
        description="Can view user information",
        module="users"
    )
    perm2 = Permission(
        code="user.write",
        name="Write Users",
        description="Can create and update users",
        module="users"
    )
    
    db.add(perm1)
    db.add(perm2)
    db.commit()
    
    # Create role
    role = Role(
        name="Test Role",
        description="Test role with permissions",
        is_active=True
    )
    role.permissions = [perm1, perm2]
    
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture
def user_token(test_user: User) -> str:
    """
    Create an access token for test user.
    """
    token_data = {
        "sub": test_user.id,
        "email": test_user.email,
        "role": test_user.role.name if test_user.role else None,
        "permissions": []
    }
    return create_access_token(token_data)


@pytest.fixture
def superuser_token(test_superuser: User) -> str:
    """
    Create an access token for test superuser.
    """
    token_data = {
        "sub": test_superuser.id,
        "email": test_superuser.email,
        "role": None,
        "permissions": []
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(user_token: str) -> dict:
    """
    Create authorization headers for test user.
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def superuser_auth_headers(superuser_token: str) -> dict:
    """
    Create authorization headers for test superuser.
    """
    return {"Authorization": f"Bearer {superuser_token}"}
