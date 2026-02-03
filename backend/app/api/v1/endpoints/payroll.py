"""
JERP 2.0 - Payroll Endpoints
RESTful API endpoints for payroll management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.payroll import PayrollPeriod, Payslip, PayrollStatus
from app.models.hr import Employee
from app.schemas.payroll import (
    PayrollPeriodCreate, PayrollPeriodUpdate, PayrollPeriodResponse,
    PayslipCreate, PayslipUpdate, PayslipResponse, PayslipWithDetails
)
from app.services.payroll_service import (
    create_payroll_period, update_payroll_period, delete_payroll_period, process_payroll_period,
    create_payslip, update_payslip, delete_payslip
)

router = APIRouter()


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# ==================== Payroll Period Endpoints ====================

@router.get("/periods", response_model=List[PayrollPeriodResponse])
async def list_payroll_periods(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    status: Optional[PayrollStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all payroll periods with pagination and filtering."""
    query = db.query(PayrollPeriod)
    
    if status is not None:
        query = query.filter(PayrollPeriod.status == status)
    
    periods = query.order_by(PayrollPeriod.period_start.desc()).offset(skip).limit(limit).all()
    return periods


@router.post("/periods", response_model=PayrollPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_new_payroll_period(
    period_data: PayrollPeriodCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new payroll period."""
    ip_address, user_agent = get_client_info(request)
    period = create_payroll_period(period_data, current_user, db, ip_address, user_agent)
    return period


@router.get("/periods/{period_id}", response_model=PayrollPeriodResponse)
async def get_payroll_period(
    period_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payroll period by ID."""
    period = db.query(PayrollPeriod).filter(PayrollPeriod.id == period_id).first()
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll period not found"
        )
    return period


@router.put("/periods/{period_id}", response_model=PayrollPeriodResponse)
async def update_payroll_period_by_id(
    period_id: int,
    period_data: PayrollPeriodUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update payroll period by ID."""
    ip_address, user_agent = get_client_info(request)
    period = update_payroll_period(period_id, period_data, current_user, db, ip_address, user_agent)
    return period


@router.delete("/periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payroll_period_by_id(
    period_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete payroll period (only if DRAFT status)."""
    ip_address, user_agent = get_client_info(request)
    delete_payroll_period(period_id, current_user, db, ip_address, user_agent)
    return None


@router.post("/periods/{period_id}/process", response_model=PayrollPeriodResponse)
async def process_payroll_period_by_id(
    period_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process payroll period, calculating totals and updating status."""
    ip_address, user_agent = get_client_info(request)
    period = process_payroll_period(period_id, current_user, db, ip_address, user_agent)
    return period


# ==================== Payslip Endpoints ====================

@router.get("/payslips", response_model=List[PayslipResponse])
async def list_payslips(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    payroll_period_id: Optional[int] = Query(None, description="Filter by payroll period"),
    employee_id: Optional[int] = Query(None, description="Filter by employee"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all payslips with pagination and filtering."""
    query = db.query(Payslip)
    
    if payroll_period_id is not None:
        query = query.filter(Payslip.payroll_period_id == payroll_period_id)
    
    if employee_id is not None:
        query = query.filter(Payslip.employee_id == employee_id)
    
    payslips = query.order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()
    return payslips


@router.post("/payslips", response_model=PayslipResponse, status_code=status.HTTP_201_CREATED)
async def create_new_payslip(
    payslip_data: PayslipCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new payslip with automatic calculation."""
    ip_address, user_agent = get_client_info(request)
    payslip = create_payslip(payslip_data, current_user, db, ip_address, user_agent)
    return payslip


@router.get("/payslips/{payslip_id}", response_model=PayslipResponse)
async def get_payslip(
    payslip_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payslip by ID."""
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )
    return payslip


@router.put("/payslips/{payslip_id}", response_model=PayslipResponse)
async def update_payslip_by_id(
    payslip_id: int,
    payslip_data: PayslipUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update payslip (recalculates all values)."""
    ip_address, user_agent = get_client_info(request)
    payslip = update_payslip(payslip_id, payslip_data, current_user, db, ip_address, user_agent)
    return payslip


@router.delete("/payslips/{payslip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payslip_by_id(
    payslip_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete payslip."""
    ip_address, user_agent = get_client_info(request)
    delete_payslip(payslip_id, current_user, db, ip_address, user_agent)
    return None


@router.get("/payslips/employee/{employee_id}", response_model=List[PayslipResponse])
async def get_employee_payslip_history(
    employee_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payslip history for a specific employee."""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    payslips = db.query(Payslip).filter(
        Payslip.employee_id == employee_id
    ).order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()
    
    return payslips


@router.get("/payslips/employee/{employee_id}", response_model=List[PayslipResponse])
async def list_non_compliant_payslips(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all non-compliant payslips (FLSA or CA Labor Code violations)."""
    payslips = db.query(Payslip).filter(
        (Payslip.flsa_compliant == False) | (Payslip.ca_labor_code_compliant == False)
    ).order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()
    
    return payslips
