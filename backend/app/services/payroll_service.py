"""
JERP 2.0 - Payroll Service
Business logic for payroll management operations with FLSA/CA Labor Code compliance
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.payroll import PayrollPeriod, Payslip, PayrollStatus
from app.models.hr import Employee, Position
from app.models.user import User
from app.models.compliance_violation import ComplianceViolation
from app.schemas.payroll import (
    PayrollPeriodCreate, PayrollPeriodUpdate,
    PayslipCreate, PayslipUpdate
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


# Compliance Constants
# TODO: Move these to configuration/database for easier updates
CA_MINIMUM_WAGE = Decimal('16.00')  # California minimum wage as of 2024

# Tax Rates (Simplified)
# TODO: Implement proper tax table lookups based on filing status, income brackets, etc.
FEDERAL_TAX_RATE = Decimal('0.12')      # Example: 12% federal withholding
STATE_TAX_RATE = Decimal('0.06')        # Example: 6% CA state withholding
SOCIAL_SECURITY_RATE = Decimal('0.062')  # 6.2% Social Security (statutory)
MEDICARE_RATE = Decimal('0.0145')        # 1.45% Medicare (statutory)

# Payroll Frequency
ANNUAL_PAY_PERIODS = Decimal('24')  # Bi-weekly payroll assumption


def create_payroll_period(
    period_data: PayrollPeriodCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayrollPeriod:
    """Create a new payroll period with validation and audit logging."""
    # Validate dates
    if period_data.period_end <= period_data.period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period end date must be after period start date"
        )
    
    # Check for overlapping periods
    overlapping = db.query(PayrollPeriod).filter(
        PayrollPeriod.status != PayrollStatus.CANCELLED,
        PayrollPeriod.period_start <= period_data.period_end,
        PayrollPeriod.period_end >= period_data.period_start
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
            detail=f"Payroll period overlaps with existing period {overlapping.id}"
        )
    
    # Create period
    period = PayrollPeriod(**period_data.model_dump())
    db.add(period)
    db.commit()
    db.refresh(period)
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
        action="PAYROLL_PERIOD_CREATED",
        resource_type="payroll_period",
        resource_id=str(period.id),
        new_values=period_data.model_dump(),
        description=f"Created payroll period {period.period_start} to {period.period_end}",
        action="CREATE",
        resource_type="pay_period",
        resource_id=str(pay_period.id),
        new_values={
            "start_date": str(period_data.start_date),
            "end_date": str(period_data.end_date),
            "pay_date": str(period_data.pay_date),
            "period_type": period_data.period_type.value
        },
        description=f"Created pay period {pay_period.start_date} to {pay_period.end_date}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return period


def update_payroll_period(
    period_id: int,
    period_data: PayrollPeriodUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayrollPeriod:
    """Update payroll period with audit logging."""
    period = db.query(PayrollPeriod).filter(PayrollPeriod.id == period_id).first()
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll period not found"
        )
    
    # Capture old values for audit
    old_values = {
        "period_start": str(period.period_start),
        "period_end": str(period.period_end),
        "pay_date": str(period.pay_date),
        "status": period.status,
        "notes": period.notes
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
    for field, value in update_data.items():
        setattr(period, field, value)
    
    db.commit()
    db.refresh(period)
    for key, value in update_data.items():
        setattr(pay_period, key, value)
    
    db.commit()
    db.refresh(pay_period)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="PAYROLL_PERIOD_UPDATED",
        resource_type="payroll_period",
        resource_id=str(period.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated payroll period {period.id}",
        action="UPDATE",
        resource_type="pay_period",
        resource_id=str(pay_period.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated pay period #{pay_period.id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return period


def calculate_payslip(
    employee: Employee,
    payroll_period: PayrollPeriod,
    hours_data: PayslipCreate,
    db: Session
) -> Payslip:
    """
    Calculate payslip with automatic FLSA and CA Labor Code compliance validation.
    
    This function performs comprehensive payroll calculations including:
    - Regular, overtime, and double-time pay
    - Tax withholdings (federal, state, Social Security, Medicare)
    - Deductions (health insurance, 401k, etc.)
    - FLSA compliance (overtime for non-exempt employees)
    - CA Labor Code compliance (double-time, minimum wage)
    """
    # Get employee position for FLSA exempt status
    position = db.query(Position).filter(Position.id == employee.position_id).first()
    is_exempt = position.is_exempt if position else False
    
    # Determine hourly rate
    effective_hourly_rate = hours_data.hourly_rate or employee.hourly_rate or Decimal('0.00')
    
    # Calculate regular pay
    if employee.salary:
        # Salaried employee - bi-weekly assumption (24 periods per year)
        regular_pay = employee.salary / ANNUAL_PAY_PERIODS
    else:
        # Hourly employee
        regular_hours = hours_data.regular_hours or Decimal('0.00')
        regular_pay = regular_hours * effective_hourly_rate
    
    # Calculate overtime (FLSA compliance check)
    overtime_pay = Decimal('0.00')
    double_time_pay = Decimal('0.00')
    
    if not is_exempt:
        # Non-exempt: FLSA requires 1.5x for hours > 40/week
        if hours_data.overtime_hours:
            overtime_rate = effective_hourly_rate * Decimal('1.5')
            overtime_pay = hours_data.overtime_hours * overtime_rate
        
        # CA Labor Code: 2x for hours > 12/day or 8+ hours on 7th consecutive day
        if hours_data.double_time_hours:
            double_time_rate = effective_hourly_rate * Decimal('2.0')
            double_time_pay = hours_data.double_time_hours * double_time_rate
    
    # Calculate gross pay
    gross_pay = (
        regular_pay + 
        overtime_pay + 
        double_time_pay + 
        (hours_data.bonus or Decimal('0.00')) + 
        (hours_data.commission or Decimal('0.00')) + 
        (hours_data.other_earnings or Decimal('0.00'))
    )
    
    # Calculate taxes (using configured rates)
    federal_tax = gross_pay * FEDERAL_TAX_RATE
    state_tax = gross_pay * STATE_TAX_RATE
    social_security = gross_pay * SOCIAL_SECURITY_RATE
    medicare = gross_pay * MEDICARE_RATE
    
    # Total deductions
    total_deductions = (
        federal_tax + 
        state_tax + 
        social_security + 
        medicare + 
        (hours_data.health_insurance or Decimal('0.00')) + 
        (hours_data.retirement_401k or Decimal('0.00')) + 
        (hours_data.other_deductions or Decimal('0.00'))
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
    # NOTE: These are simplified tax calculations for demonstration purposes.
    # In production, replace with proper tax withholding calculations based on:
    # - Employee W-4 information (filing status, allowances, additional withholding)
    # - Current federal and state tax brackets
    # - Jurisdiction-specific requirements
    # - Year-to-date earnings for Social Security wage base limit
    
    # Federal tax (simplified - 15% flat rate for demonstration)
    # TODO: Replace with graduated tax bracket calculation based on W-4
    federal_tax = gross_pay * Decimal("0.15")
    
    # State tax (simplified - 5% flat rate for demonstration)
    # TODO: Replace with state-specific tax tables
    state_tax = gross_pay * Decimal("0.05")
    
    # Social Security (6.2% up to wage base limit)
    # TODO: Implement year-to-date tracking and wage base limit checking
    # Current wage base limit for 2024: $168,600
    social_security = gross_pay * Decimal("0.062")
    
    # Medicare (1.45%)
    # TODO: Add additional 0.9% Medicare tax for high earners (> $200k)
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
    
    # Compliance checks
    flsa_compliant = True
    ca_labor_code_compliant = True
    compliance_notes = []
    
    # Check minimum wage (using configured CA minimum wage)
    if not is_exempt:
        total_hours = (
            (hours_data.regular_hours or Decimal('0.00')) + 
            (hours_data.overtime_hours or Decimal('0.00')) + 
            (hours_data.double_time_hours or Decimal('0.00'))
        )
        
        if total_hours > 0:
            effective_rate = gross_pay / total_hours
            if effective_rate < CA_MINIMUM_WAGE:
                ca_labor_code_compliant = False
                compliance_notes.append(
                    f"Effective rate ${effective_rate:.2f} below CA minimum wage ${CA_MINIMUM_WAGE}"
                )
    
    # Create payslip
    payslip = Payslip(
        payroll_period_id=payroll_period.id,
        employee_id=employee.id,
        regular_hours=hours_data.regular_hours,
        overtime_hours=hours_data.overtime_hours,
        double_time_hours=hours_data.double_time_hours,
        hourly_rate=effective_hourly_rate,
        regular_pay=regular_pay,
        overtime_pay=overtime_pay,
        double_time_pay=double_time_pay,
        bonus=hours_data.bonus or Decimal('0.00'),
        commission=hours_data.commission or Decimal('0.00'),
        other_earnings=hours_data.other_earnings or Decimal('0.00'),
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
        health_insurance=hours_data.health_insurance or Decimal('0.00'),
        retirement_401k=hours_data.retirement_401k or Decimal('0.00'),
        other_deductions=hours_data.other_deductions or Decimal('0.00'),
        total_deductions=total_deductions,
        net_pay=net_pay,
        flsa_compliant=flsa_compliant,
        ca_labor_code_compliant=ca_labor_code_compliant,
        compliance_notes='; '.join(compliance_notes) if compliance_notes else None
    )
    
    db.add(payslip)
    db.flush()
    
    # Log compliance violations if any
    if not flsa_compliant or not ca_labor_code_compliant:
        violation_severity = "CRITICAL" if not ca_labor_code_compliant else "HIGH"
        violation = ComplianceViolation(
            violation_type="LABOR_LAW",
            regulation="PAYROLL_COMPLIANCE",
            severity=violation_severity,
            description='; '.join(compliance_notes),
            entity_type="payslip",
            entity_id=payslip.id,
            detected_at=datetime.utcnow()
        )
        db.add(violation)
    
    return payslip


def create_payslip(
    payslip_data: PayslipCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Payslip:
    """Create a new payslip with automatic calculation and audit logging."""
    # Get payroll period
    payroll_period = db.query(PayrollPeriod).filter(
        PayrollPeriod.id == payslip_data.payroll_period_id
    ).first()
    if not payroll_period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll period not found"
        )
    
    # Get employee
    employee = db.query(Employee).filter(
        Employee.id == payslip_data.employee_id
    ).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check for duplicate payslip
    existing = db.query(Payslip).filter(
        Payslip.payroll_period_id == payslip_data.payroll_period_id,
        Payslip.employee_id == payslip_data.employee_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payslip already exists for this employee and payroll period"
        )
    
    # Calculate payslip
    payslip = calculate_payslip(employee, payroll_period, payslip_data, db)
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
        action="PAYSLIP_CREATED",
        resource_type="payslip",
        resource_id=str(payslip.id),
        description=f"Created payslip for employee {employee.employee_number}",
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


def update_payslip(
    payslip_id: int,
    payslip_data: PayslipUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Payslip:
    """Update payslip and recalculate with audit logging."""
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
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
    
    # Get employee and payroll period
    employee = db.query(Employee).filter(Employee.id == payslip.employee_id).first()
    payroll_period = db.query(PayrollPeriod).filter(
        PayrollPeriod.id == payslip.payroll_period_id
    ).first()
    
    # Merge update data with existing payslip data
    update_data = payslip_data.model_dump(exclude_unset=True)
    merged_data = PayslipCreate(
        payroll_period_id=payslip.payroll_period_id,
        employee_id=payslip.employee_id,
        regular_hours=update_data.get('regular_hours', payslip.regular_hours),
        overtime_hours=update_data.get('overtime_hours', payslip.overtime_hours),
        double_time_hours=update_data.get('double_time_hours', payslip.double_time_hours),
        hourly_rate=update_data.get('hourly_rate', payslip.hourly_rate),
        bonus=update_data.get('bonus', payslip.bonus),
        commission=update_data.get('commission', payslip.commission),
        other_earnings=update_data.get('other_earnings', payslip.other_earnings),
        health_insurance=update_data.get('health_insurance', payslip.health_insurance),
        retirement_401k=update_data.get('retirement_401k', payslip.retirement_401k),
        other_deductions=update_data.get('other_deductions', payslip.other_deductions)
    )
    
    # Delete old payslip
    db.delete(payslip)
    db.flush()
    
    # Recalculate
    new_payslip = calculate_payslip(employee, payroll_period, merged_data, db)
    db.commit()
    db.refresh(new_payslip)
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
        action="PAYSLIP_UPDATED",
        resource_type="payslip",
        resource_id=str(new_payslip.id),
        description=f"Updated and recalculated payslip {payslip_id}",
        action="APPROVE",
        resource_type="payslip",
        resource_id=str(payslip.id),
        old_values={"status": old_status},
        new_values={"status": PayslipStatus.APPROVED.value},
        description=f"Approved payslip #{payslip.id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return new_payslip


def process_payroll_period(
    period_id: int,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> PayrollPeriod:
    """Process payroll period, calculating totals and updating status."""
    # Get period
    period = db.query(PayrollPeriod).filter(PayrollPeriod.id == period_id).first()
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll period not found"
        )
    
    # Check if already processed
    if period.status == PayrollStatus.PROCESSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payroll period already processed"
        )
    
    # Update status to processing
    period.status = PayrollStatus.PROCESSING
    db.commit()
    
    try:
        # Calculate totals from payslips
        payslips = db.query(Payslip).filter(Payslip.payroll_period_id == period_id).all()
        
        if not payslips:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payslips found for this payroll period"
            )
        
        total_gross = sum(p.gross_pay for p in payslips)
        total_deductions = sum(p.total_deductions for p in payslips)
        total_net = sum(p.net_pay for p in payslips)
        
        # Update period
        period.total_gross = total_gross
        period.total_deductions = total_deductions
        period.total_net = total_net
        period.status = PayrollStatus.PROCESSED
        period.processed_at = datetime.utcnow()
        period.processed_by = current_user.id
        
        db.commit()
        db.refresh(period)
        
        # Create audit log
        create_audit_log(
            db=db,
            user_id=current_user.id,
            user_email=current_user.email,
            action="PAYROLL_PROCESSED",
            resource_type="payroll_period",
            resource_id=str(period.id),
            description=f"Processed payroll period {period.period_start} to {period.period_end} with {len(payslips)} payslips",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return period
    
    except Exception as e:
        period.status = PayrollStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process payroll period: {str(e)}"
        )


def delete_payroll_period(
    period_id: int,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Delete payroll period (only if DRAFT status)."""
    period = db.query(PayrollPeriod).filter(PayrollPeriod.id == period_id).first()
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payroll period not found"
        )
    
    if period.status != PayrollStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete payroll periods in DRAFT status"
        )
    
    # Create audit log before deletion
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
            # NOTE: Using 40 hours as default for standard full-time work week.
            # For part-time or variable schedule employees, hours should be 
            # entered manually via the individual payslip calculation endpoint.
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
        action="PAYROLL_PERIOD_DELETED",
        resource_type="payroll_period",
        resource_id=str(period.id),
        description=f"Deleted payroll period {period.period_start} to {period.period_end}",
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
    
    db.delete(period)
    db.commit()


def delete_payslip(
    payslip_id: int,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Delete payslip with audit logging."""
    payslip = db.query(Payslip).filter(Payslip.id == payslip_id).first()
    if not payslip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payslip not found"
        )
    
    # Create audit log before deletion
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
        action="PAYSLIP_DELETED",
        resource_type="payslip",
        resource_id=str(payslip.id),
        description=f"Deleted payslip for employee {payslip.employee_id}",
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
    
    db.delete(payslip)
    db.commit()
    return pay_period


async def get_payroll_summary(
    db: Session,
    pay_period_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> PayrollSummary:
    """Get aggregated payroll statistics."""
    # Use eager loading to avoid N+1 query problem
    query = db.query(Payslip).join(PayPeriod).options(
        joinedload(Payslip.employee).joinedload(Employee.department)
    )
    
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
        # Employee and department are already loaded via eager loading
        if payslip.employee and payslip.employee.department:
            dept_id = payslip.employee.department_id
            if dept_id not in dept_summary:
                dept_summary[dept_id] = {
                    "department_id": dept_id,
                    "department_name": payslip.employee.department.name,
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
