"""
JERP 2.0 - Payroll Management Endpoints
CRUD operations for payroll management
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.payroll import PayPeriod, Payslip, PayPeriodStatus, PayslipStatus
from app.models.hr import Employee
from app.schemas.payroll import (
    PayPeriodCreate, PayPeriodUpdate, PayPeriodResponse,
    PayslipCalculation, PayslipCreate, PayslipUpdate, PayslipResponse,
    PayrollSummary
)
from app.services.payroll_service import (
    create_pay_period, update_pay_period,
    calculate_payslip, approve_payslip,
    process_pay_period, approve_pay_period,
    get_payroll_summary
)
from app.services.auth_service import create_audit_log

router = APIRouter()


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# Pay Period Endpoints
@router.get("/pay-periods", response_model=List[PayPeriodResponse])
async def list_pay_periods(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: Optional[PayPeriodStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all pay periods with pagination and filtering."""
    query = db.query(PayPeriod)
    
    if status_filter:
        query = query.filter(PayPeriod.status == status_filter)
    
    pay_periods = query.order_by(PayPeriod.start_date.desc()).offset(skip).limit(limit).all()
    return pay_periods


@router.post("/pay-periods", response_model=PayPeriodResponse, status_code=status.HTTP_201_CREATED)
async def create_new_pay_period(
    period_data: PayPeriodCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new pay period."""
    ip_address, user_agent = get_client_info(request)
    pay_period = await create_pay_period(db, period_data, current_user, ip_address, user_agent)
    return pay_period


@router.get("/pay-periods/{pay_period_id}", response_model=PayPeriodResponse)
async def get_pay_period_by_id(
    pay_period_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get pay period by ID."""
    pay_period = db.query(PayPeriod).filter(PayPeriod.id == pay_period_id).first()
    if not pay_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pay period not found"
        )
    return pay_period


@router.put("/pay-periods/{pay_period_id}", response_model=PayPeriodResponse)
async def update_pay_period_by_id(
    pay_period_id: int,
    period_data: PayPeriodUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update pay period by ID."""
    ip_address, user_agent = get_client_info(request)
    pay_period = await update_pay_period(db, pay_period_id, period_data, current_user, ip_address, user_agent)
    return pay_period


@router.post("/pay-periods/{pay_period_id}/process", response_model=PayPeriodResponse)
async def process_pay_period_by_id(
    pay_period_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process pay period (calculate payslips for all active employees)."""
    ip_address, user_agent = get_client_info(request)
    pay_period = await process_pay_period(db, pay_period_id, current_user, ip_address, user_agent)
    return pay_period


@router.post("/pay-periods/{pay_period_id}/approve", response_model=PayPeriodResponse)
async def approve_pay_period_by_id(
    pay_period_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Approve pay period and all its payslips."""
    ip_address, user_agent = get_client_info(request)
    pay_period = await approve_pay_period(db, pay_period_id, current_user, ip_address, user_agent)
    return pay_period


# Payslip Endpoints
@router.get("/payslips", response_model=List[PayslipResponse])
async def list_payslips(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    pay_period_id: Optional[int] = Query(None, description="Filter by pay period ID"),
    status_filter: Optional[PayslipStatus] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all payslips with pagination and filtering."""
    query = db.query(Payslip)
    
    if employee_id:
        query = query.filter(Payslip.employee_id == employee_id)
    
    if pay_period_id:
        query = query.filter(Payslip.pay_period_id == pay_period_id)
    
    if status_filter:
        query = query.filter(Payslip.status == status_filter)
    
    payslips = query.order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()
    return payslips


@router.post("/payslips", response_model=PayslipResponse, status_code=status.HTTP_201_CREATED)
async def create_or_calculate_payslip(
    payslip_data: PayslipCalculation,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create/calculate a payslip for an employee."""
    ip_address, user_agent = get_client_info(request)
    payslip = await calculate_payslip(db, payslip_data, current_user, ip_address, user_agent)
    return payslip


@router.get("/payslips/{payslip_id}", response_model=PayslipResponse)
async def get_payslip_by_id(
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
    """Update payslip by ID."""
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )
    
    if payslip.status == PayslipStatus.VOIDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a voided payslip"
        )
    
    # Store old values
    old_values = {
        "gross_pay": str(payslip.gross_pay),
        "net_pay": str(payslip.net_pay),
        "status": payslip.status.value
    }
    
    # Update fields
    update_data = payslip_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(payslip, key, value)
    
    db.commit()
    db.refresh(payslip)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="payslip",
        resource_id=str(payslip.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated payslip #{payslip.id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return payslip


@router.post("/payslips/{payslip_id}/approve", response_model=PayslipResponse)
async def approve_payslip_by_id(
    payslip_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Approve a payslip."""
    ip_address, user_agent = get_client_info(request)
    payslip = await approve_payslip(db, payslip_id, current_user, ip_address, user_agent)
    return payslip


@router.delete("/payslips/{payslip_id}", response_model=PayslipResponse)
async def void_payslip(
    payslip_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Void a payslip (soft delete)."""
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )
    
    if payslip.status == PayslipStatus.VOIDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payslip is already voided"
        )
    
    if payslip.status == PayslipStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot void a paid payslip"
        )
    
    old_status = payslip.status.value
    payslip.status = PayslipStatus.VOIDED
    
    db.commit()
    db.refresh(payslip)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="VOID",
        resource_type="payslip",
        resource_id=str(payslip.id),
        old_values={"status": old_status},
        new_values={"status": PayslipStatus.VOIDED.value},
        description=f"Voided payslip #{payslip.id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return payslip


# Employee Payroll History
@router.get("/employees/{employee_id}/payslips", response_model=List[PayslipResponse])
async def get_employee_payslips(
    employee_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payroll history for a specific employee."""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    payslips = db.query(Payslip).filter(
        Payslip.employee_id == employee_id,
        Payslip.status != PayslipStatus.VOIDED
    ).order_by(Payslip.created_at.desc()).offset(skip).limit(limit).all()
    
    return payslips


# Summary Endpoint
@router.get("/summary", response_model=PayrollSummary)
async def get_payroll_summary_endpoint(
    pay_period_id: Optional[int] = Query(None, description="Filter by pay period ID"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payroll summary statistics."""
    summary = await get_payroll_summary(db, pay_period_id, start_date, end_date)
    return summary
