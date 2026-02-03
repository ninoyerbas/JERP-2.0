"""
JERP 2.0 - Audit Log Endpoint Tests
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def test_list_audit_logs_superuser(client: TestClient, superuser_auth_headers: dict):
    """Test listing audit logs as superuser"""
    response = client.get("/api/v1/audit", headers=superuser_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_list_audit_logs_non_superuser(client: TestClient, auth_headers: dict):
    """Test listing audit logs as non-superuser (should fail without permission)"""
    response = client.get("/api/v1/audit", headers=auth_headers)
    
    assert response.status_code == 403


def test_list_audit_logs_with_filters(client: TestClient, test_user: User, superuser_auth_headers: dict):
    """Test listing audit logs with filters"""
    response = client.get(
        "/api/v1/audit",
        headers=superuser_auth_headers,
        params={
            "user_id": test_user.id,
            "action": "CREATE"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_get_audit_log(client: TestClient, db: Session, superuser_auth_headers: dict):
    """Test getting a specific audit log"""
    # Create an audit log
    log = AuditLog.create_entry(
        user_id=1,
        user_email="test@example.com",
        action="TEST",
        resource_type="test",
        resource_id="1",
        old_values=None,
        new_values={"test": "value"},
        description="Test log",
        ip_address="127.0.0.1",
        user_agent="test-agent",
        previous_hash=None
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    response = client.get(f"/api/v1/audit/{log.id}", headers=superuser_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == log.id
    assert data["action"] == "TEST"


def test_get_audit_log_non_superuser(client: TestClient, db: Session, auth_headers: dict):
    """Test getting audit log as non-superuser (should fail)"""
    log = AuditLog.create_entry(
        user_id=1,
        user_email="test@example.com",
        action="TEST",
        resource_type="test",
        resource_id="1",
        previous_hash=None
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    response = client.get(f"/api/v1/audit/{log.id}", headers=auth_headers)
    
    assert response.status_code == 403


def test_verify_audit_chain_empty(client: TestClient, superuser_auth_headers: dict):
    """Test verifying empty audit chain"""
    response = client.get("/api/v1/audit/verify/chain", headers=superuser_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_logs"] == 0


def test_verify_audit_chain_valid(client: TestClient, db: Session, superuser_auth_headers: dict):
    """Test verifying valid audit chain"""
    # Create a chain of logs
    log1 = AuditLog.create_entry(
        user_id=1,
        user_email="test@example.com",
        action="TEST1",
        resource_type="test",
        resource_id="1",
        previous_hash=None
    )
    db.add(log1)
    db.commit()
    db.refresh(log1)
    
    log2 = AuditLog.create_entry(
        user_id=1,
        user_email="test@example.com",
        action="TEST2",
        resource_type="test",
        resource_id="2",
        previous_hash=log1.current_hash
    )
    db.add(log2)
    db.commit()
    
    response = client.get("/api/v1/audit/verify/chain", headers=superuser_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["total_logs"] == 2
    assert data["verified_logs"] == 2
    assert len(data["integrity_errors"]) == 0


def test_export_audit_logs_csv(client: TestClient, superuser_auth_headers: dict):
    """Test exporting audit logs as CSV"""
    response = client.get("/api/v1/audit/export/csv", headers=superuser_auth_headers)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]


def test_export_audit_logs_json(client: TestClient, superuser_auth_headers: dict):
    """Test exporting audit logs as JSON"""
    response = client.get("/api/v1/audit/export/json", headers=superuser_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "exported_at" in data
    assert "logs" in data


def test_export_audit_logs_non_superuser(client: TestClient, auth_headers: dict):
    """Test exporting audit logs as non-superuser (should fail)"""
    response = client.get("/api/v1/audit/export/csv", headers=auth_headers)
    
    assert response.status_code == 403
    
    response = client.get("/api/v1/audit/export/json", headers=auth_headers)
    
    assert response.status_code == 403
