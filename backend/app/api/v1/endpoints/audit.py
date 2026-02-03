"""
JERP 2.0 - Audit Log Endpoints
Immutable audit trail with hash chain verification
"""
import csv
import io
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse, AuditLogListResponse
from app.api.v1.dependencies import get_current_active_user, require_superuser
from app.api.v1.exceptions import NotFoundException


router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List audit logs with filtering and pagination.
    Requires superuser or audit_view permission.
    """
    # Permission check: superuser or has audit_view permission
    if not current_user.is_superuser:
        user_permissions = {p.code for p in current_user.role.permissions} if current_user.role else set()
        if "audit.view" not in user_permissions:
            from app.api.v1.exceptions import ForbiddenException
            raise ForbiddenException(detail="Insufficient permissions to view audit logs")
    
    # Build query
    query = db.query(AuditLog)
    
    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and order by most recent first
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return AuditLogListResponse(
        total=total,
        items=[AuditLogResponse.model_validate(log) for log in logs]
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get specific audit log entry.
    Requires superuser or audit_view permission.
    """
    # Permission check
    if not current_user.is_superuser:
        user_permissions = {p.code for p in current_user.role.permissions} if current_user.role else set()
        if "audit.view" not in user_permissions:
            from app.api.v1.exceptions import ForbiddenException
            raise ForbiddenException(detail="Insufficient permissions to view audit logs")
    
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise NotFoundException(detail="Audit log not found")
    
    return AuditLogResponse.model_validate(log)


@router.get("/verify/chain")
async def verify_audit_chain(
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Verify integrity of audit log hash chain.
    Returns status report of chain verification.
    Requires superuser access.
    """
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    
    if not logs:
        return {
            "status": "success",
            "message": "No audit logs to verify",
            "total_logs": 0,
            "verified_logs": 0,
            "integrity_errors": []
        }
    
    integrity_errors = []
    verified_count = 0
    
    for i, log in enumerate(logs):
        # Compute expected hash
        expected_hash = AuditLog.compute_hash(
            log.previous_hash,
            log.user_id,
            log.action,
            log.resource_type,
            log.resource_id,
            log.old_values,
            log.new_values,
            log.created_at
        )
        
        # Verify hash matches
        if log.current_hash != expected_hash:
            integrity_errors.append({
                "log_id": log.id,
                "error": "Hash mismatch",
                "expected": expected_hash,
                "actual": log.current_hash
            })
        else:
            verified_count += 1
        
        # Verify chain linkage (except for first log)
        if i > 0:
            previous_log = logs[i - 1]
            if log.previous_hash != previous_log.current_hash:
                integrity_errors.append({
                    "log_id": log.id,
                    "error": "Chain break",
                    "expected_previous": previous_log.current_hash,
                    "actual_previous": log.previous_hash
                })
    
    status = "success" if not integrity_errors else "failed"
    
    return {
        "status": status,
        "message": f"Chain verification {'passed' if status == 'success' else 'failed'}",
        "total_logs": len(logs),
        "verified_logs": verified_count,
        "integrity_errors": integrity_errors
    }


@router.get("/export/csv")
async def export_audit_logs_csv(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Export audit logs as CSV.
    Requires superuser access.
    """
    # Build query with filters
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    logs = query.order_by(AuditLog.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "User ID", "User Email", "Action", "Resource Type", "Resource ID",
        "Description", "IP Address", "Previous Hash", "Current Hash", "Created At"
    ])
    
    # Write data
    for log in logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.user_email,
            log.action,
            log.resource_type,
            log.resource_id,
            log.description,
            log.ip_address,
            log.previous_hash,
            log.current_hash,
            log.created_at.isoformat() if log.created_at else ""
        ])
    
    # Return as streaming response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/export/json")
async def export_audit_logs_json(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Export audit logs as JSON.
    Requires superuser access.
    """
    # Build query with filters
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    logs = query.order_by(AuditLog.created_at.desc()).all()
    
    return {
        "total": len(logs),
        "exported_at": datetime.utcnow().isoformat(),
        "logs": [AuditLogResponse.model_validate(log).model_dump() for log in logs]
    }
