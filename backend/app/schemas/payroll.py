"""
JERP 2.0 - Payroll Schemas
Pydantic models for payroll API requests and responses
"""
from datetime import date, datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.payroll import PayPeriodStatus, PayPeriodType, PayslipStatus


# Pay Period Schemas
class PayPeriodBase(BaseModel):
    """Base pay period schema"""
    start_date: date = Field(..., description="Start date of the pay period")
    end_date: date = Field(..., description="End date of the pay period")
    pay_date: date = Field(..., description="Date when payment will be made")
    period_type: PayPeriodType = Field(..., description="Type of pay period")


class PayPeriodCreate(PayPeriodBase):
    """Schema for creating a new pay period"""
    pass


class PayPeriodUpdate(BaseModel):
    """Schema for updating a pay period"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pay_date: Optional[date] = None
    period_type: Optional[PayPeriodType] = None
    status: Optional[PayPeriodStatus] = None


class PayPeriodResponse(PayPeriodBase):
    """Schema for pay period response"""
    id: int
    status: PayPeriodStatus
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Payslip Schemas
class PayslipBase(BaseModel):
    """Base payslip schema"""
    employee_id: int = Field(..., description="Employee ID")
    pay_period_id: int = Field(..., description="Pay period ID")


class PayslipCalculation(PayslipBase):
    """Schema for payslip calculation request"""
    regular_hours: Optional[Decimal] = Field(default=Decimal("0"), description="Regular hours worked")
    overtime_hours: Optional[Decimal] = Field(default=Decimal("0"), description="Overtime hours worked")
    bonus: Optional[Decimal] = Field(default=Decimal("0"), description="Bonus amount")
    commission: Optional[Decimal] = Field(default=Decimal("0"), description="Commission amount")
    health_insurance: Optional[Decimal] = Field(default=Decimal("0"), description="Health insurance deduction")
    retirement_401k: Optional[Decimal] = Field(default=Decimal("0"), description="401k retirement deduction")
    other_deductions: Optional[Decimal] = Field(default=Decimal("0"), description="Other deductions")
    notes: Optional[str] = None


class PayslipCreate(BaseModel):
    """Schema for creating a payslip manually"""
    employee_id: int
    pay_period_id: int
    regular_hours: Decimal = Decimal("0")
    overtime_hours: Decimal = Decimal("0")
    regular_pay: Decimal = Decimal("0")
    overtime_pay: Decimal = Decimal("0")
    bonus: Decimal = Decimal("0")
    commission: Decimal = Decimal("0")
    gross_pay: Decimal
    federal_tax: Decimal = Decimal("0")
    state_tax: Decimal = Decimal("0")
    social_security: Decimal = Decimal("0")
    medicare: Decimal = Decimal("0")
    health_insurance: Decimal = Decimal("0")
    retirement_401k: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")
    total_deductions: Decimal
    net_pay: Decimal
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class PayslipUpdate(BaseModel):
    """Schema for updating a payslip"""
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    regular_pay: Optional[Decimal] = None
    overtime_pay: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    gross_pay: Optional[Decimal] = None
    federal_tax: Optional[Decimal] = None
    state_tax: Optional[Decimal] = None
    social_security: Optional[Decimal] = None
    medicare: Optional[Decimal] = None
    health_insurance: Optional[Decimal] = None
    retirement_401k: Optional[Decimal] = None
    other_deductions: Optional[Decimal] = None
    total_deductions: Optional[Decimal] = None
    net_pay: Optional[Decimal] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[PayslipStatus] = None


class PayslipResponse(BaseModel):
    """Schema for payslip response"""
    id: int
    employee_id: int
    pay_period_id: int
    status: PayslipStatus
    regular_hours: Decimal
    overtime_hours: Decimal
    regular_pay: Decimal
    overtime_pay: Decimal
    bonus: Decimal
    commission: Decimal
    gross_pay: Decimal
    federal_tax: Decimal
    state_tax: Decimal
    social_security: Decimal
    medicare: Decimal
    health_insurance: Decimal
    retirement_401k: Decimal
    other_deductions: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Summary Schemas
class DepartmentPayrollSummary(BaseModel):
    """Summary of payroll by department"""
    department_id: int
    department_name: str
    employee_count: int
    total_gross_pay: Decimal
    total_net_pay: Decimal
    total_deductions: Decimal


class PayrollSummary(BaseModel):
    """Aggregated payroll statistics"""
    pay_period_id: Optional[int] = None
    total_employees: int = 0
    total_payslips: int = 0
    total_gross_pay: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")
    total_net_pay: Decimal = Decimal("0")
    total_regular_hours: Decimal = Decimal("0")
    total_overtime_hours: Decimal = Decimal("0")
    average_gross_pay: Decimal = Decimal("0")
    average_net_pay: Decimal = Decimal("0")
    by_department: Optional[list[DepartmentPayrollSummary]] = None
    by_status: Optional[Dict[str, int]] = None
