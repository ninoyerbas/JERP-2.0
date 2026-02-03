"""
JERP 2.0 - Compliance API Endpoints
REST API endpoints for compliance management
"""
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.compliance_service import ComplianceService
from app.schemas.compliance import (
    ComplianceViolationCreate,
    ComplianceViolationUpdate,
    ComplianceViolationResponse,
    ComplianceViolationResolve,
    ComplianceViolationFilter,
    ComplianceRuleResponse,
    ComplianceReportCreate,
    ComplianceReportResponse,
    ComplianceDashboardResponse,
    ViolationStatistics,
    ViolationTrend,
    TimesheetValidationRequest,
    TimesheetValidationResponse,
    TransactionValidationRequest,
    TransactionValidationResponse,
)
from app.models.compliance_violation import (
    ViolationType,
    ViolationSeverity,
    ViolationStatus,
    RegulationType,
)

router = APIRouter()


# Dependency to get compliance service
def get_compliance_service(db: Session = Depends(get_db)) -> ComplianceService:
    return ComplianceService(db)


# Mock user for now (in production, this would come from JWT token)
def get_current_user():
    return {"id": 1, "email": "admin@jerp.local"}


# ============================================================================
# Violation Endpoints
# ============================================================================

@router.post("/violations", response_model=ComplianceViolationResponse, status_code=status.HTTP_201_CREATED)
def create_violation(
    violation: ComplianceViolationCreate,
    service: ComplianceService = Depends(get_compliance_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new compliance violation.
    
    - **violation_type**: Type of violation (LABOR_LAW, FINANCIAL, OTHER)
    - **regulation**: Regulation violated (e.g., "California Labor Code Section 510")
    - **severity**: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
    - **description**: Detailed description of violation
    - **entity_type**: Type of entity (e.g., "timesheet", "transaction")
    - **entity_id**: ID of the entity
    """
    created = service.log_violation(
        violation_data=violation,
        user_id=current_user["id"],
        user_email=current_user["email"]
    )
    return created


@router.get("/violations", response_model=List[ComplianceViolationResponse])
def list_violations(
    violation_type: Optional[ViolationType] = None,
    severity: Optional[ViolationSeverity] = None,
    status_filter: Optional[ViolationStatus] = Query(None, alias="status"),
    entity_type: Optional[str] = None,
    assigned_to: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    List compliance violations with optional filtering.
    
    - **violation_type**: Filter by violation type
    - **severity**: Filter by severity level
    - **status**: Filter by violation status
    - **entity_type**: Filter by entity type
    - **assigned_to**: Filter by assigned user ID
    - **start_date**: Filter violations detected after this date
    - **end_date**: Filter violations detected before this date
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    filters = ComplianceViolationFilter(
        violation_type=violation_type,
        severity=severity,
        status=status_filter,
        entity_type=entity_type,
        assigned_to=assigned_to,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return service.get_violations(filters)


@router.get("/violations/{violation_id}", response_model=ComplianceViolationResponse)
def get_violation(
    violation_id: int,
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    Get details of a specific compliance violation.
    """
    violation = service.get_violation_by_id(violation_id)
    if not violation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Violation with ID {violation_id} not found"
        )
    return violation


@router.put("/violations/{violation_id}", response_model=ComplianceViolationResponse)
def update_violation(
    violation_id: int,
    update_data: ComplianceViolationUpdate,
    service: ComplianceService = Depends(get_compliance_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a compliance violation.
    
    - **severity**: Update severity level
    - **description**: Update description
    - **status**: Update status
    - **assigned_to**: Assign to a user
    - **resolution_notes**: Add resolution notes
    - **financial_impact**: Update financial impact
    """
    updated = service.update_violation(
        violation_id=violation_id,
        update_data=update_data,
        user_id=current_user["id"],
        user_email=current_user["email"]
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Violation with ID {violation_id} not found"
        )
    return updated


@router.post("/violations/{violation_id}/resolve", response_model=ComplianceViolationResponse)
def resolve_violation(
    violation_id: int,
    resolve_data: ComplianceViolationResolve,
    service: ComplianceService = Depends(get_compliance_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Mark a compliance violation as resolved.
    
    - **resolution_notes**: Notes describing how the violation was resolved (minimum 10 characters)
    """
    resolved = service.resolve_violation(
        violation_id=violation_id,
        resolution_notes=resolve_data.resolution_notes,
        user_id=current_user["id"],
        user_email=current_user["email"]
    )
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Violation with ID {violation_id} not found"
        )
    return resolved


# ============================================================================
# Report Endpoints
# ============================================================================

@router.get("/reports", response_model=List[ComplianceReportResponse])
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List compliance reports.
    """
    from app.models.compliance_violation import ComplianceReport
    reports = db.query(ComplianceReport).offset(skip).limit(limit).order_by(
        ComplianceReport.generated_at.desc()
    ).all()
    return reports


@router.post("/reports", response_model=ComplianceReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    report_data: ComplianceReportCreate,
    service: ComplianceService = Depends(get_compliance_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Generate a compliance report for a specified date range.
    
    - **report_type**: Type of report (e.g., "weekly", "monthly", "quarterly")
    - **start_date**: Start date of reporting period
    - **end_date**: End date of reporting period
    """
    if report_data.end_date < report_data.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date"
        )
    
    report = service.generate_compliance_report(
        report_data=report_data,
        user_id=current_user["id"]
    )
    return report


# ============================================================================
# Rule Endpoints
# ============================================================================

@router.get("/rules", response_model=List[ComplianceRuleResponse])
def list_rules(
    regulation_type: Optional[RegulationType] = None,
    is_active: Optional[bool] = None,
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    List compliance rules.
    
    - **regulation_type**: Filter by regulation type (CALIFORNIA_LABOR, FLSA, GAAP, IFRS)
    - **is_active**: Filter by active status
    """
    return service.get_compliance_rules(
        regulation_type=regulation_type,
        is_active=is_active
    )


# ============================================================================
# Validation Endpoints
# ============================================================================

@router.post("/validate/timesheet/{timesheet_id}", response_model=TimesheetValidationResponse)
def validate_timesheet(
    timesheet_id: int,
    request: TimesheetValidationRequest,
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    Validate a timesheet against labor compliance rules.
    
    This endpoint checks:
    - California Labor Code compliance (if enabled)
    - FLSA compliance (if enabled)
    
    Returns violations found during validation.
    
    **Note**: In a full implementation, this would integrate with actual timesheet data
    and the compliance engines to perform real validation.
    """
    # Placeholder implementation
    # In production, this would:
    # 1. Fetch timesheet data
    # 2. Run California Labor Code checks
    # 3. Run FLSA checks
    # 4. Log any violations found
    # 5. Return results
    
    return TimesheetValidationResponse(
        timesheet_id=timesheet_id,
        is_compliant=True,
        violations=[],
        warnings=["Validation feature coming soon - placeholder response"]
    )


@router.post("/validate/transaction/{transaction_id}", response_model=TransactionValidationResponse)
def validate_transaction(
    transaction_id: int,
    request: TransactionValidationRequest,
    service: ComplianceService = Depends(get_compliance_service)
):
    """
    Validate a financial transaction against accounting standards.
    
    This endpoint checks:
    - GAAP compliance (if enabled)
    - IFRS compliance (if enabled)
    
    Returns violations found during validation.
    
    **Note**: In a full implementation, this would integrate with actual transaction data
    and the compliance engines to perform real validation.
    """
    # Placeholder implementation
    # In production, this would:
    # 1. Fetch transaction data
    # 2. Run GAAP validation
    # 3. Run IFRS validation
    # 4. Log any violations found
    # 5. Return results
    
    return TransactionValidationResponse(
        transaction_id=transaction_id,
        is_compliant=True,
        violations=[],
        warnings=["Validation feature coming soon - placeholder response"]
    )


# ============================================================================
# Dashboard Endpoint
# ============================================================================

@router.get("/dashboard", response_model=ComplianceDashboardResponse)
def get_dashboard(
    days_back: int = Query(30, ge=1, le=365),
    service: ComplianceService = Depends(get_compliance_service),
    db: Session = Depends(get_db)
):
    """
    Get compliance dashboard data including statistics and trends.
    
    - **days_back**: Number of days to look back for statistics (default: 30)
    """
    from datetime import timedelta
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    # Get statistics
    stats = service.get_violation_statistics(start_date, end_date)
    
    # Get recent violations
    filters = ComplianceViolationFilter(
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time()),
        skip=0,
        limit=10
    )
    recent_violations = service.get_violations(filters)
    
    # Calculate compliance score (simple algorithm)
    total = stats.total_violations
    if total == 0:
        compliance_score = 100.0
    else:
        # Weight violations by severity
        weighted_violations = (
            stats.critical_violations * 4 +
            stats.high_violations * 3 +
            stats.medium_violations * 2 +
            stats.low_violations * 1
        )
        max_possible = total * 4  # If all were critical
        compliance_score = max(0, 100 - (weighted_violations / max(max_possible, 1)) * 100)
    
    # Build top violation types
    from app.models.compliance_violation import ComplianceViolation
    from sqlalchemy import func
    
    top_types = db.query(
        ComplianceViolation.regulation,
        func.count(ComplianceViolation.id).label('count')
    ).filter(
        ComplianceViolation.detected_at >= datetime.combine(start_date, datetime.min.time())
    ).group_by(
        ComplianceViolation.regulation
    ).order_by(
        func.count(ComplianceViolation.id).desc()
    ).limit(10).all()
    
    top_violation_types = {reg: count for reg, count in top_types}
    
    # Build trends (simplified - one data point per week)
    trends = []
    current_date = start_date
    while current_date <= end_date:
        week_end = min(current_date + timedelta(days=7), end_date)
        week_violations = db.query(ComplianceViolation).filter(
            ComplianceViolation.detected_at >= datetime.combine(current_date, datetime.min.time()),
            ComplianceViolation.detected_at < datetime.combine(week_end, datetime.max.time())
        ).all()
        
        severity_breakdown = {
            "CRITICAL": sum(1 for v in week_violations if v.severity == ViolationSeverity.CRITICAL),
            "HIGH": sum(1 for v in week_violations if v.severity == ViolationSeverity.HIGH),
            "MEDIUM": sum(1 for v in week_violations if v.severity == ViolationSeverity.MEDIUM),
            "LOW": sum(1 for v in week_violations if v.severity == ViolationSeverity.LOW),
        }
        
        trends.append(ViolationTrend(
            date=current_date,
            count=len(week_violations),
            severity_breakdown=severity_breakdown
        ))
        
        current_date = week_end
    
    return ComplianceDashboardResponse(
        statistics=stats,
        recent_violations=recent_violations,
        trends=trends,
        top_violation_types=top_violation_types,
        compliance_score=compliance_score
    )
