"""
JERP 2.0 - Audit Log Endpoints
Audit trail and compliance reporting API
"""
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse

router = APIRouter()


@router.get("/logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List audit logs with filtering and pagination."""
    query = db.query(AuditLog)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action == action)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    # Order by most recent first
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return logs


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit log by ID."""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    return log


@router.get("/verify")
async def verify_hash_chain(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify the integrity of the audit log hash chain."""
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    
    if not logs:
        return {
            "status": "success",
            "message": "No audit logs to verify",
            "total_logs": 0,
            "verified": 0
        }
    
    verification_errors = []
    verified_count = 0
    
    for i, log in enumerate(logs):
        # Verify hash chain
        if i == 0:
            # First log should have no previous hash or "GENESIS"
            expected_prev_hash = None
        else:
            expected_prev_hash = logs[i - 1].current_hash
        
        if log.previous_hash != expected_prev_hash:
            verification_errors.append({
                "log_id": log.id,
                "error": "Hash chain broken",
                "expected_previous_hash": expected_prev_hash,
                "actual_previous_hash": log.previous_hash
            })
        
        # Verify current hash computation
        computed_hash = AuditLog.compute_hash(
            log.previous_hash,
            log.user_id,
            log.action,
            log.resource_type,
            log.resource_id,
            log.old_values,
            log.new_values,
            log.created_at
        )
        
        if log.current_hash != computed_hash:
            verification_errors.append({
                "log_id": log.id,
                "error": "Hash mismatch",
                "expected_hash": computed_hash,
                "actual_hash": log.current_hash
            })
        else:
            verified_count += 1
    
    if verification_errors:
        return {
            "status": "error",
            "message": "Hash chain verification failed",
            "total_logs": len(logs),
            "verified": verified_count,
            "errors": verification_errors
        }
    
    return {
        "status": "success",
        "message": "All audit logs verified successfully",
        "total_logs": len(logs),
        "verified": verified_count
    }


@router.get("/stats")
async def get_audit_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit statistics and insights."""
    # Total logs
    total_logs = db.query(func.count(AuditLog.id)).scalar()
    
    # Actions per day (last 30 days)
    thirty_days_ago = datetime.utcnow().date() - __import__('datetime').timedelta(days=30)
    actions_per_day = db.query(
        func.date(AuditLog.created_at).label('date'),
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.created_at >= datetime.combine(thirty_days_ago, datetime.min.time())
    ).group_by(
        func.date(AuditLog.created_at)
    ).order_by(
        func.date(AuditLog.created_at).desc()
    ).limit(30).all()
    
    # Top users by activity
    top_users = db.query(
        AuditLog.user_email,
        func.count(AuditLog.id).label('action_count')
    ).filter(
        AuditLog.user_email.isnot(None)
    ).group_by(
        AuditLog.user_email
    ).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    # Most common actions
    common_actions = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(
        AuditLog.action
    ).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    # Most accessed resource types
    common_resources = db.query(
        AuditLog.resource_type,
        func.count(AuditLog.id).label('count')
    ).group_by(
        AuditLog.resource_type
    ).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    return {
        "total_logs": total_logs,
        "actions_per_day": [
            {"date": str(item[0]), "count": item[1]}
            for item in actions_per_day
        ],
        "top_users": [
            {"email": item[0], "action_count": item[1]}
            for item in top_users
        ],
        "common_actions": [
            {"action": item[0], "count": item[1]}
            for item in common_actions
        ],
        "common_resources": [
            {"resource_type": item[0], "count": item[1]}
            for item in common_resources
        ]
    }
