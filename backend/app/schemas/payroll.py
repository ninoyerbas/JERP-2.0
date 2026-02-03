"""
JERP 2.0 - Payroll Schemas
Pydantic models for Payroll module
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Payroll Period Schemas
class PayrollPeriodBase(BaseModel):
    start_date: date
    end_date: date
    pay_date: date
    status: str = Field(default="DRAFT", max_length=20)  # DRAFT, PROCESSING, APPROVED, PAID


class PayrollPeriodCreate(PayrollPeriodBase):
    pass


class PayrollPeriodUpdate(BaseModel):
    pay_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)


class PayrollPeriodResponse(PayrollPeriodBase):
    id: int
    processed_by: Optional[int] = None
    processed_at: Optional[datetime] = None
    total_gross: Optional[Decimal] = None
    total_deductions: Optional[Decimal] = None
    total_net: Optional[Decimal] = None
    compliance_checked: bool
    compliance_violations_count: int
    
    model_config = ConfigDict(from_attributes=True)


class PayrollPeriodList(BaseModel):
    total: int
    items: List[PayrollPeriodResponse]


# Payslip Schemas
class PayslipBase(BaseModel):
    period_id: int
    employee_id: int
    regular_hours: Decimal = Field(default=Decimal("0"))
    overtime_hours: Decimal = Field(default=Decimal("0"))
    double_time_hours: Decimal = Field(default=Decimal("0"))
    regular_pay: Decimal = Field(default=Decimal("0"))
    overtime_pay: Decimal = Field(default=Decimal("0"))
    double_time_pay: Decimal = Field(default=Decimal("0"))
    bonus: Decimal = Field(default=Decimal("0"))
    commission: Decimal = Field(default=Decimal("0"))
    meal_break_penalty: Decimal = Field(default=Decimal("0"))
    rest_break_penalty: Decimal = Field(default=Decimal("0"))
    federal_tax: Decimal = Field(default=Decimal("0"))
    state_tax: Decimal = Field(default=Decimal("0"))
    social_security: Decimal = Field(default=Decimal("0"))
    medicare: Decimal = Field(default=Decimal("0"))
    gross_pay: Decimal
    total_deductions: Decimal
    net_pay: Decimal


class PayslipCreate(PayslipBase):
    california_labor_compliant: bool = True
    flsa_compliant: bool = True
    compliance_notes: Optional[str] = None


class PayslipResponse(PayslipBase):
    id: int
    california_labor_compliant: bool
    flsa_compliant: bool
    compliance_notes: Optional[str] = None
    created_at: datetime
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PayslipList(BaseModel):
    total: int
    items: List[PayslipResponse]


# Payroll Processing Request
class ProcessPayrollRequest(BaseModel):
    period_id: int


# Payroll Processing Response
class ProcessPayrollResponse(BaseModel):
    payslips_created: int
    violations_count: int
    total_gross: Decimal
    total_net: Decimal


# Payroll Compliance Report
class PayrollComplianceReport(BaseModel):
    period_id: int
    total_employees: int
    california_compliant: int
    california_violations: int
    flsa_compliant: int
    flsa_violations: int
    total_penalties: Decimal
