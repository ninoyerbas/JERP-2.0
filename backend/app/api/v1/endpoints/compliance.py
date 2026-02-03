"""
JERP 2.0 - Compliance API Endpoints
REST API endpoints for compliance checking and violation management
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.compliance import ComplianceService, ViolationTracker
from app.models.compliance import ComplianceViolation, ComplianceRule


router = APIRouter()


# Pydantic models for request/response
class LaborComplianceCheck(BaseModel):
    """Labor compliance check request"""
    employee_id: int
    state: str = "CA"
    hours_worked: dict = Field(..., description="Dict of date -> hours")
    workweek: List[str] = Field(..., description="List of dates in workweek (YYYY-MM-DD)")
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    breaks: List[dict] = []
    regular_rate: float = 0
    total_pay: float = 0
    employee_type: str = "regular"
    employee_age: Optional[int] = None
    occupation: Optional[str] = None
    is_school_week: bool = True
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None


class FinancialComplianceCheck(BaseModel):
    """Financial compliance check request"""
    transaction_id: str
    type: str = Field(..., description="Transaction type: journal_entry, balance_sheet, revenue, etc.")
    standard: str = Field(..., description="GAAP or IFRS")
    data: dict = Field(..., description="Transaction data")


class ViolationResolution(BaseModel):
    """Violation resolution request"""
    resolution_notes: str = Field(..., min_length=10)


class ComplianceReportRequest(BaseModel):
    """Compliance report request"""
    start_date: str = Field(..., description="ISO format date")
    end_date: str = Field(..., description="ISO format date")
    violation_types: Optional[List[str]] = None


@router.post("/check/labor", tags=["compliance"])
async def check_labor_compliance(
    request: LaborComplianceCheck,
    db: Session = Depends(get_db)
):
    """
    Check labor law compliance for employee timesheet.
    
    Performs California Labor Code and FLSA compliance checks.
    """
    service = ComplianceService()
    
    # Convert string dates to datetime objects for workweek
    workweek = [datetime.fromisoformat(d) for d in request.workweek]
    
    # Build timesheet dict
    timesheet = {
        "state": request.state,
        "hours_worked": request.hours_worked,
        "workweek": workweek,
        "regular_rate": request.regular_rate,
        "total_pay": request.total_pay,
        "employee_type": request.employee_type,
    }
    
    # Add optional fields
    if request.shift_start:
        timesheet["shift_start"] = datetime.fromisoformat(request.shift_start)
    if request.shift_end:
        timesheet["shift_end"] = datetime.fromisoformat(request.shift_end)
    if request.breaks:
        # Convert break times to datetime
        breaks = []
        for brk in request.breaks:
            breaks.append({
                "type": brk.get("type"),
                "start": datetime.fromisoformat(brk["start"]) if brk.get("start") else None,
                "end": datetime.fromisoformat(brk["end"]) if brk.get("end") else None
            })
        timesheet["breaks"] = breaks
    
    if request.employee_age:
        timesheet["employee_age"] = request.employee_age
        timesheet["occupation"] = request.occupation or ""
        timesheet["is_school_week"] = request.is_school_week
        timesheet["work_start_time"] = request.work_start_time
        timesheet["work_end_time"] = request.work_end_time
    
    result = service.check_labor_compliance(
        employee_id=request.employee_id,
        timesheet=timesheet,
        db=db
    )
    
    return result


@router.post("/check/financial", tags=["compliance"])
async def check_financial_compliance(
    request: FinancialComplianceCheck,
    db: Session = Depends(get_db)
):
    """
    Check financial compliance according to GAAP or IFRS.
    
    Validates journal entries, balance sheets, revenue recognition, etc.
    """
    service = ComplianceService()
    
    # Build transaction dict
    transaction = {
        "id": request.transaction_id,
        "type": request.type,
        **request.data
    }
    
    result = service.check_financial_compliance(
        transaction=transaction,
        standard=request.standard,
        db=db
    )
    
    return result


@router.get("/violations", tags=["compliance"])
async def get_violations(
    violation_type: Optional[str] = Query(None, description="Filter by violation type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get compliance violations with optional filters.
    """
    query = db.query(ComplianceViolation)
    
    # Apply filters
    if violation_type:
        query = query.filter(ComplianceViolation.violation_type == violation_type)
    
    if severity:
        query = query.filter(ComplianceViolation.severity == severity)
    
    if resolved is not None:
        if resolved:
            query = query.filter(ComplianceViolation.resolved_at.isnot(None))
        else:
            query = query.filter(ComplianceViolation.resolved_at.is_(None))
    
    # Order by most recent
    query = query.order_by(ComplianceViolation.detected_at.desc())
    
    # Apply pagination
    violations = query.offset(offset).limit(limit).all()
    
    return {
        "total": query.count(),
        "limit": limit,
        "offset": offset,
        "violations": [
            {
                "id": v.id,
                "violation_type": v.violation_type,
                "severity": v.severity,
                "standard": v.standard,
                "resource_type": v.resource_type,
                "resource_id": v.resource_id,
                "description": v.description,
                "detected_at": v.detected_at.isoformat(),
                "resolved_at": v.resolved_at.isoformat() if v.resolved_at else None,
                "financial_impact": float(v.financial_impact) if v.financial_impact else None
            }
            for v in violations
        ]
    }


@router.get("/violations/{violation_id}", tags=["compliance"])
async def get_violation(
    violation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific violation.
    """
    violation = db.query(ComplianceViolation).filter(
        ComplianceViolation.id == violation_id
    ).first()
    
    if not violation:
        raise HTTPException(status_code=404, detail="Violation not found")
    
    return {
        "id": violation.id,
        "violation_type": violation.violation_type,
        "severity": violation.severity,
        "standard": violation.standard,
        "resource_type": violation.resource_type,
        "resource_id": violation.resource_id,
        "description": violation.description,
        "detected_at": violation.detected_at.isoformat(),
        "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
        "resolution_notes": violation.resolution_notes,
        "financial_impact": float(violation.financial_impact) if violation.financial_impact else None
    }


@router.post("/violations/{violation_id}/resolve", tags=["compliance"])
async def resolve_violation(
    violation_id: int,
    resolution: ViolationResolution,
    db: Session = Depends(get_db)
):
    """
    Mark a violation as resolved.
    """
    tracker = ViolationTracker(db)
    
    result = tracker.resolve_violation(
        violation_id=violation_id,
        resolution_notes=resolution.resolution_notes
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/violations/escalations", tags=["compliance"])
async def get_escalations(
    db: Session = Depends(get_db)
):
    """
    Get violations that need escalation based on age and severity.
    """
    tracker = ViolationTracker(db)
    escalations = tracker.check_escalations()
    
    return {
        "count": len(escalations),
        "escalations": escalations
    }


@router.get("/violations/resource/{resource_type}/{resource_id}", tags=["compliance"])
async def get_violations_by_resource(
    resource_type: str,
    resource_id: str,
    include_resolved: bool = Query(False),
    db: Session = Depends(get_db)
):
    """
    Get all violations for a specific resource.
    """
    tracker = ViolationTracker(db)
    violations = tracker.get_violations_by_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        include_resolved=include_resolved
    )
    
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "count": len(violations),
        "violations": violations
    }


@router.post("/reports/compliance", tags=["compliance"])
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive compliance report for specified period.
    """
    service = ComplianceService()
    
    start_date = datetime.fromisoformat(request.start_date)
    end_date = datetime.fromisoformat(request.end_date)
    
    report = service.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
        violation_types=request.violation_types or [],
        db=db
    )
    
    return report


@router.get("/analytics", tags=["compliance"])
async def get_violation_analytics(
    start_date: Optional[str] = Query(None, description="ISO format date"),
    end_date: Optional[str] = Query(None, description="ISO format date"),
    db: Session = Depends(get_db)
):
    """
    Get violation analytics and trends.
    """
    tracker = ViolationTracker(db)
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    analytics = tracker.get_violation_analytics(
        start_date=start,
        end_date=end
    )
    
    return analytics


@router.get("/rules", tags=["compliance"])
async def get_compliance_rules(
    rule_type: Optional[str] = Query(None, description="Filter by rule type (LABOR, FINANCIAL)"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get compliance rules.
    """
    query = db.query(ComplianceRule).filter(
        ComplianceRule.is_active == is_active
    )
    
    if rule_type:
        query = query.filter(ComplianceRule.rule_type == rule_type)
    
    rules = query.all()
    
    return {
        "count": len(rules),
        "rules": [
            {
                "id": r.id,
                "rule_code": r.rule_code,
                "rule_type": r.rule_type,
                "standard": r.standard,
                "description": r.description,
                "severity": r.severity,
                "parameters": r.parameters,
                "effective_date": r.effective_date.isoformat(),
                "expiration_date": r.expiration_date.isoformat() if r.expiration_date else None
            }
            for r in rules
        ]
    }


@router.get("/rules/{rule_code}", tags=["compliance"])
async def get_compliance_rule(
    rule_code: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific compliance rule.
    """
    rule = db.query(ComplianceRule).filter(
        ComplianceRule.rule_code == rule_code
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return {
        "id": rule.id,
        "rule_code": rule.rule_code,
        "rule_type": rule.rule_type,
        "standard": rule.standard,
        "description": rule.description,
        "is_active": rule.is_active,
        "severity": rule.severity,
        "parameters": rule.parameters,
        "effective_date": rule.effective_date.isoformat(),
        "expiration_date": rule.expiration_date.isoformat() if rule.expiration_date else None
    }
