"""
JERP 2.0 - Payroll Service
Business logic for payroll management operations
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, or_
from fastapi import HTTPException, status

from app.models.payroll import PayPeriod, Payslip, PayPeriodStatus, PayslipStatus
from app.models.hr import Employee, Department, EmploymentStatus
from app.models.user import User
from app.schemas.payroll import (
    PayPeriodCreate, PayPeriodUpdate,
    PayslipCalculation, PayslipCreate, PayslipUpdate,
    PayrollSummary, DepartmentPayrollSummary
)
from app.services.auth_service import create_audit_log


# Pay Period Services
async def create_pay_period(
    db: Session,
    period_data: PayPeriodCreate,
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayPeriod:
    """Create a new pay period with audit logging."""
    # Validate dates
    if period_data.start_date >= period_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )
    
    if period_data.pay_date < period_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pay date must be on or after end date"
        )
    
    # Check for overlapping pay periods
    overlapping = db.query(PayPeriod).filter(
        or_(
            and_(
                PayPeriod.start_date <= period_data.start_date,
                PayPeriod.end_date >= period_data.start_date
            ),
            and_(
                PayPeriod.start_date <= period_data.end_date,
                PayPeriod.end_date >= period_data.end_date
            )
        )
    ).first()
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pay period overlaps with existing period #{overlapping.id}"
        )
    
    # Create pay period
    pay_period = PayPeriod(**period_data.model_dump())
    db.add(pay_period)
    db.commit()
    db.refresh(pay_period)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="pay_period",
        resource_id=str(pay_period.id),
        new_values=period_data.model_dump(),
        description=f"Created pay period {pay_period.start_date} to {pay_period.end_date}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return pay_period


async def update_pay_period(
    db: Session,
    pay_period_id: int,
    period_data: PayPeriodUpdate,
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayPeriod:
    """Update a pay period with audit logging."""
    pay_period = db.query(PayPeriod).filter(PayPeriod.id == pay_period_id).first()
    if not pay_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pay period not found"
        )
    
    # Store old values
    old_values = {
        "start_date": str(pay_period.start_date),
        "end_date": str(pay_period.end_date),
        "pay_date": str(pay_period.pay_date),
        "period_type": pay_period.period_type.value,
        "status": pay_period.status.value
    }
    
    # Update fields
    update_data = period_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pay_period, key, value)
    
    db.commit()
    db.refresh(pay_period)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="pay_period",
        resource_id=str(pay_period.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated pay period #{pay_period.id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return pay_period


async def calculate_payslip(
    db: Session,
    calculation_data: PayslipCalculation,
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Payslip:
    """
    Calculate payslip based on employee compensation.
    Supports both salaried and hourly employees with FLSA overtime rules.
    """
    # Get employee with position info
    employee = db.query(Employee).options(
        joinedload(Employee.position)
    ).filter(Employee.id == calculation_data.employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    if employee.status != EmploymentStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is not active"
        )
    
    # Get pay period
    pay_period = db.query(PayPeriod).filter(
        PayPeriod.id == calculation_data.pay_period_id
    ).first()
    
    if not pay_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pay period not found"
        )
    
    # Check for existing payslip
    existing_payslip = db.query(Payslip).filter(
        Payslip.employee_id == calculation_data.employee_id,
        Payslip.pay_period_id == calculation_data.pay_period_id,
        Payslip.status != PayslipStatus.VOIDED
    ).first()
    
    if existing_payslip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payslip already exists for this employee and pay period (ID: {existing_payslip.id})"
        )
    
    # Validate employee has compensation set
    if not employee.salary and not employee.hourly_rate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee must have salary or hourly_rate set"
        )
    
    # Calculate earnings
    regular_hours = Decimal(str(calculation_data.regular_hours or 0))
    overtime_hours = Decimal(str(calculation_data.overtime_hours or 0))
    bonus = Decimal(str(calculation_data.bonus or 0))
    commission = Decimal(str(calculation_data.commission or 0))
    
    regular_pay = Decimal("0")
    overtime_pay = Decimal("0")
    
    # Determine if exempt (salaried) or non-exempt (hourly)
    is_exempt = employee.position.is_exempt if employee.position else False
    
    if employee.salary and is_exempt:
        # Salaried employee - divide annual salary by pay periods
        annual_salary = Decimal(str(employee.salary))
        
        # Determine pay periods per year based on period type
        if pay_period.period_type.value == "WEEKLY":
            periods_per_year = 52
        elif pay_period.period_type.value == "BI_WEEKLY":
            periods_per_year = 26
        elif pay_period.period_type.value == "SEMI_MONTHLY":
            periods_per_year = 24
        else:  # MONTHLY
            periods_per_year = 12
        
        regular_pay = annual_salary / periods_per_year
        regular_hours = Decimal("0")  # Salaried employees don't track hours
        overtime_hours = Decimal("0")
        overtime_pay = Decimal("0")
        
    elif employee.hourly_rate:
        # Hourly employee - calculate with overtime rules (FLSA: 1.5x for > 40 hours/week)
        hourly_rate = Decimal(str(employee.hourly_rate))
        
        # Calculate regular pay
        regular_pay = hourly_rate * regular_hours
        
        # Calculate overtime pay (1.5x rate)
        overtime_rate = hourly_rate * Decimal("1.5")
        overtime_pay = overtime_rate * overtime_hours
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee compensation not properly configured"
        )
    
    # Calculate gross pay
    gross_pay = regular_pay + overtime_pay + bonus + commission
    
    # Calculate deductions
    # Federal tax (simplified - 15% for demonstration)
    federal_tax = gross_pay * Decimal("0.15")
    
    # State tax (simplified - 5% for demonstration)
    state_tax = gross_pay * Decimal("0.05")
    
    # Social Security (6.2% up to wage base limit)
    social_security = gross_pay * Decimal("0.062")
    
    # Medicare (1.45%)
    medicare = gross_pay * Decimal("0.0145")
    
    # Additional deductions from input
    health_insurance = Decimal(str(calculation_data.health_insurance or 0))
    retirement_401k = Decimal(str(calculation_data.retirement_401k or 0))
    other_deductions = Decimal(str(calculation_data.other_deductions or 0))
    
    # Total deductions
    total_deductions = (
        federal_tax + state_tax + social_security + medicare +
        health_insurance + retirement_401k + other_deductions
    )
    
    # Net pay
    net_pay = gross_pay - total_deductions
    
    # Create payslip
    payslip = Payslip(
        employee_id=calculation_data.employee_id,
        pay_period_id=calculation_data.pay_period_id,
        status=PayslipStatus.CALCULATED,
        regular_hours=regular_hours,
        overtime_hours=overtime_hours,
        regular_pay=regular_pay,
        overtime_pay=overtime_pay,
        bonus=bonus,
        commission=commission,
        gross_pay=gross_pay,
        federal_tax=federal_tax,
        state_tax=state_tax,
        social_security=social_security,
        medicare=medicare,
        health_insurance=health_insurance,
        retirement_401k=retirement_401k,
        other_deductions=other_deductions,
        total_deductions=total_deductions,
        net_pay=net_pay,
        notes=calculation_data.notes
    )
    
    db.add(payslip)
    db.commit()
    db.refresh(payslip)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="payslip",
        resource_id=str(payslip.id),
        new_values={
            "employee_id": payslip.employee_id,
            "pay_period_id": payslip.pay_period_id,
            "gross_pay": str(payslip.gross_pay),
            "net_pay": str(payslip.net_pay),
            "status": payslip.status.value
        },
        description=f"Calculated payslip for employee #{employee.employee_number}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return payslip


async def approve_payslip(
    db: Session,
    payslip_id: int,
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Payslip:
    """Approve a payslip and update status with audit log."""
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )
    
    if payslip.status == PayslipStatus.VOIDED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve a voided payslip"
        )
    
    if payslip.status == PayslipStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payslip is already approved"
        )
    
    old_status = payslip.status.value
    payslip.status = PayslipStatus.APPROVED
    
    db.commit()
    db.refresh(payslip)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="APPROVE",
        resource_type="payslip",
        resource_id=str(payslip.id),
        old_values={"status": old_status},
        new_values={"status": PayslipStatus.APPROVED.value},
        description=f"Approved payslip #{payslip.id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return payslip


async def process_pay_period(
    db: Session,
    pay_period_id: int,
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayPeriod:
    """Process entire pay period by calculating payslips for all active employees."""
    pay_period = db.query(PayPeriod).filter(PayPeriod.id == pay_period_id).first()
    
    if not pay_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pay period not found"
        )
    
    if pay_period.status != PayPeriodStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pay period is not open (current status: {pay_period.status.value})"
        )
    
    # Get all active employees with compensation
    employees = db.query(Employee).options(
        joinedload(Employee.position)
    ).filter(
        Employee.status == EmploymentStatus.ACTIVE,
        or_(
            Employee.salary.isnot(None),
            Employee.hourly_rate.isnot(None)
        )
    ).all()
    
    if not employees:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active employees with compensation found"
        )
    
    processed_count = 0
    errors = []
    
    # Process each employee
    for employee in employees:
        # Check if payslip already exists
        existing = db.query(Payslip).filter(
            Payslip.employee_id == employee.id,
            Payslip.pay_period_id == pay_period_id,
            Payslip.status != PayslipStatus.VOIDED
        ).first()
        
        if existing:
            continue  # Skip if already exists
        
        try:
            # Create calculation data with default hours for hourly employees
            calc_data = PayslipCalculation(
                employee_id=employee.id,
                pay_period_id=pay_period_id,
                regular_hours=Decimal("40") if employee.hourly_rate else Decimal("0"),
                overtime_hours=Decimal("0")
            )
            
            # Calculate payslip
            await calculate_payslip(db, calc_data, current_user, ip_address, user_agent)
            processed_count += 1
            
        except Exception as e:
            errors.append(f"Employee {employee.employee_number}: {str(e)}")
    
    # Update pay period status
    old_status = pay_period.status.value
    pay_period.status = PayPeriodStatus.PROCESSING
    pay_period.processed_by = current_user.id
    pay_period.processed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(pay_period)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="PROCESS",
        resource_type="pay_period",
        resource_id=str(pay_period.id),
        old_values={"status": old_status},
        new_values={
            "status": PayPeriodStatus.PROCESSING.value,
            "processed_count": processed_count,
            "errors": errors if errors else None
        },
        description=f"Processed pay period #{pay_period.id} - {processed_count} payslips created",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return pay_period


async def approve_pay_period(
    db: Session,
    pay_period_id: int,
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayPeriod:
    """Approve a pay period and all its payslips."""
    pay_period = db.query(PayPeriod).filter(PayPeriod.id == pay_period_id).first()
    
    if not pay_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pay period not found"
        )
    
    if pay_period.status not in [PayPeriodStatus.PROCESSING, PayPeriodStatus.OPEN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve pay period with status {pay_period.status.value}"
        )
    
    # Approve all calculated payslips in this period
    payslips = db.query(Payslip).filter(
        Payslip.pay_period_id == pay_period_id,
        Payslip.status.in_([PayslipStatus.CALCULATED, PayslipStatus.DRAFT])
    ).all()
    
    for payslip in payslips:
        payslip.status = PayslipStatus.APPROVED
    
    # Update pay period status
    old_status = pay_period.status.value
    pay_period.status = PayPeriodStatus.APPROVED
    pay_period.approved_by = current_user.id
    pay_period.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(pay_period)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="APPROVE",
        resource_type="pay_period",
        resource_id=str(pay_period.id),
        old_values={"status": old_status},
        new_values={
            "status": PayPeriodStatus.APPROVED.value,
            "payslips_approved": len(payslips)
        },
        description=f"Approved pay period #{pay_period.id} with {len(payslips)} payslips",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return pay_period


async def get_payroll_summary(
    db: Session,
    pay_period_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> PayrollSummary:
    """Get aggregated payroll statistics."""
    query = db.query(Payslip).join(PayPeriod)
    
    # Apply filters
    if pay_period_id:
        query = query.filter(Payslip.pay_period_id == pay_period_id)
    
    if start_date:
        query = query.filter(PayPeriod.start_date >= start_date)
    
    if end_date:
        query = query.filter(PayPeriod.end_date <= end_date)
    
    # Only include non-voided payslips
    query = query.filter(Payslip.status != PayslipStatus.VOIDED)
    
    payslips = query.all()
    
    if not payslips:
        return PayrollSummary()
    
    # Calculate totals
    total_gross_pay = sum(Decimal(str(p.gross_pay)) for p in payslips)
    total_deductions = sum(Decimal(str(p.total_deductions)) for p in payslips)
    total_net_pay = sum(Decimal(str(p.net_pay)) for p in payslips)
    total_regular_hours = sum(Decimal(str(p.regular_hours)) for p in payslips)
    total_overtime_hours = sum(Decimal(str(p.overtime_hours)) for p in payslips)
    
    # Get unique employees
    unique_employees = len(set(p.employee_id for p in payslips))
    
    # Calculate averages
    avg_gross = total_gross_pay / len(payslips) if payslips else Decimal("0")
    avg_net = total_net_pay / len(payslips) if payslips else Decimal("0")
    
    # Group by status
    by_status = {}
    for payslip in payslips:
        status = payslip.status.value
        by_status[status] = by_status.get(status, 0) + 1
    
    # Group by department
    dept_summary = {}
    for payslip in payslips:
        employee = db.query(Employee).filter(Employee.id == payslip.employee_id).first()
        if employee and employee.department:
            dept_id = employee.department_id
            if dept_id not in dept_summary:
                dept_summary[dept_id] = {
                    "department_id": dept_id,
                    "department_name": employee.department.name,
                    "employee_count": 0,
                    "employee_ids": set(),
                    "total_gross_pay": Decimal("0"),
                    "total_net_pay": Decimal("0"),
                    "total_deductions": Decimal("0")
                }
            
            dept_summary[dept_id]["employee_ids"].add(payslip.employee_id)
            dept_summary[dept_id]["total_gross_pay"] += Decimal(str(payslip.gross_pay))
            dept_summary[dept_id]["total_net_pay"] += Decimal(str(payslip.net_pay))
            dept_summary[dept_id]["total_deductions"] += Decimal(str(payslip.total_deductions))
    
    # Convert department summary to list
    by_department = []
    for dept in dept_summary.values():
        by_department.append(DepartmentPayrollSummary(
            department_id=dept["department_id"],
            department_name=dept["department_name"],
            employee_count=len(dept["employee_ids"]),
            total_gross_pay=dept["total_gross_pay"],
            total_net_pay=dept["total_net_pay"],
            total_deductions=dept["total_deductions"]
        ))
    
    return PayrollSummary(
        pay_period_id=pay_period_id,
        total_employees=unique_employees,
        total_payslips=len(payslips),
        total_gross_pay=total_gross_pay,
        total_deductions=total_deductions,
        total_net_pay=total_net_pay,
        total_regular_hours=total_regular_hours,
        total_overtime_hours=total_overtime_hours,
        average_gross_pay=avg_gross,
        average_net_pay=avg_net,
        by_department=by_department if by_department else None,
        by_status=by_status
    )
