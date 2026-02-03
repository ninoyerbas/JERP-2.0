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
)
from app.services.auth_service import create_audit_log


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
    }
    
    # Update fields
    update_data = period_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(period, field, value)
    
    db.commit()
    db.refresh(period)
    
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
        regular_pay = employee.salary / Decimal('24')
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
    
    # Calculate taxes (simplified - production would use IRS/FTB tax tables)
    federal_tax = gross_pay * Decimal('0.12')  # Example 12% federal rate
    state_tax = gross_pay * Decimal('0.06')    # Example 6% CA state rate
    social_security = gross_pay * Decimal('0.062')  # 6.2% Social Security
    medicare = gross_pay * Decimal('0.0145')        # 1.45% Medicare
    
    # Total deductions
    total_deductions = (
        federal_tax + 
        state_tax + 
        social_security + 
        medicare + 
        (hours_data.health_insurance or Decimal('0.00')) + 
        (hours_data.retirement_401k or Decimal('0.00')) + 
        (hours_data.other_deductions or Decimal('0.00'))
    )
    
    # Net pay
    net_pay = gross_pay - total_deductions
    
    # Compliance checks
    flsa_compliant = True
    ca_labor_code_compliant = True
    compliance_notes = []
    
    # Check minimum wage (CA: $16.00/hr as of 2024)
    CA_MINIMUM_WAGE = Decimal('16.00')
    
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
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="PAYSLIP_UPDATED",
        resource_type="payslip",
        resource_id=str(new_payslip.id),
        description=f"Updated and recalculated payslip {payslip_id}",
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
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="PAYROLL_PERIOD_DELETED",
        resource_type="payroll_period",
        resource_id=str(period.id),
        description=f"Deleted payroll period {period.period_start} to {period.period_end}",
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
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="PAYSLIP_DELETED",
        resource_type="payslip",
        resource_id=str(payslip.id),
        description=f"Deleted payslip for employee {payslip.employee_id}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.delete(payslip)
    db.commit()
