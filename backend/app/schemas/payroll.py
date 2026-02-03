"""
JERP 2.0 - Payroll Schemas
Pydantic models for payroll management
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from decimal import Decimal

from app.models.payroll import PayrollStatus


# PayrollPeriod Schemas
class PayrollPeriodBase(BaseModel):
    """Base payroll period fields"""
    period_start: date
    period_end: date
    pay_date: date
    notes: Optional[str] = None


class PayrollPeriodCreate(PayrollPeriodBase):
    """Payroll period creation request"""
    pass


class PayrollPeriodUpdate(BaseModel):
    """Payroll period update request - all fields optional"""
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    pay_date: Optional[date] = None
    status: Optional[PayrollStatus] = None
    notes: Optional[str] = None


class PayrollPeriodResponse(PayrollPeriodBase):
    """Payroll period response with all fields"""
    id: int
    status: PayrollStatus
    total_gross: Optional[Decimal] = None
    total_deductions: Optional[Decimal] = None
    total_net: Optional[Decimal] = None
    processed_at: Optional[datetime] = None
    processed_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Payslip Schemas
class PayslipBase(BaseModel):
    """Base payslip fields"""
    payroll_period_id: int
    employee_id: int
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    double_time_hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    bonus: Optional[Decimal] = Decimal('0.00')
    commission: Optional[Decimal] = Decimal('0.00')
    other_earnings: Optional[Decimal] = Decimal('0.00')
    health_insurance: Optional[Decimal] = Decimal('0.00')
    retirement_401k: Optional[Decimal] = Decimal('0.00')
    other_deductions: Optional[Decimal] = Decimal('0.00')


class PayslipCreate(PayslipBase):
    """Payslip creation request"""
    pass


class PayslipUpdate(BaseModel):
    """Payslip update request - all fields optional"""
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    double_time_hours: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    other_earnings: Optional[Decimal] = None
    health_insurance: Optional[Decimal] = None
    retirement_401k: Optional[Decimal] = None
    other_deductions: Optional[Decimal] = None


class PayslipResponse(PayslipBase):
    """Payslip response with all calculated fields"""
    id: int
    regular_pay: Decimal
    overtime_pay: Decimal
    double_time_pay: Decimal
    gross_pay: Decimal
    federal_tax: Decimal
    state_tax: Decimal
    social_security: Decimal
    medicare: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    flsa_compliant: bool
    ca_labor_code_compliant: bool
    compliance_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PayslipWithDetails(PayslipResponse):
    """Payslip response with related entity details"""
    employee: Optional[dict] = None
    payroll_period: Optional[PayrollPeriodResponse] = None
    
    class Config:
        from_attributes = True
