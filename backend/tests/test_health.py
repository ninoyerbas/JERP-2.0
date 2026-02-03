"""
JERP 2.0 - Health Check Tests
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["app"] == "JERP 2.0"
    assert data["version"] == "2.0.0"
    assert "timestamp" in data
    assert "checks" in data


def test_health_check_has_database_check():
    """Test that health check includes database status"""
    response = client.get("/health")
    data = response.json()
    
    assert "checks" in data
    assert "database" in data["checks"]
