"""
JERP 2.0 - Time & Attendance Schemas
Pydantic models for Time & Attendance module
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Break Entry Schemas
class BreakEntryBase(BaseModel):
    break_type: str = Field(..., max_length=20)  # MEAL, REST
    start_time: datetime
    end_time: datetime
    duration_minutes: Optional[int] = None


class BreakEntryCreate(BreakEntryBase):
    pass


class BreakEntryResponse(BreakEntryBase):
    id: int
    timesheet_entry_id: int
    
    model_config = ConfigDict(from_attributes=True)


# Timesheet Entry Schemas
class TimesheetEntryBase(BaseModel):
    work_date: date
    clock_in: Optional[datetime] = None
    clock_out: Optional[datetime] = None
    hours_worked: Optional[Decimal] = None
    break_minutes: int = 0
    notes: Optional[str] = None


class TimesheetEntryCreate(TimesheetEntryBase):
    breaks: List[BreakEntryCreate] = []


class TimesheetEntryResponse(TimesheetEntryBase):
    id: int
    timesheet_id: int
    breaks: List[BreakEntryResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


# Timesheet Schemas
class TimesheetBase(BaseModel):
    employee_id: int
    period_start: date
    period_end: date
    status: str = Field(default="DRAFT", max_length=20)  # DRAFT, SUBMITTED, APPROVED, REJECTED


class TimesheetCreate(TimesheetBase):
    entries: List[TimesheetEntryCreate] = []


class TimesheetUpdate(BaseModel):
    status: Optional[str] = Field(None, max_length=20)


class TimesheetResponse(TimesheetBase):
    id: int
    regular_hours: Decimal
    overtime_hours: Decimal
    double_time_hours: Decimal
    pto_hours: Decimal
    is_seventh_consecutive_day: bool
    meal_breaks_compliant: bool
    rest_breaks_compliant: bool
    submitted_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    entries: List[TimesheetEntryResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class TimesheetList(BaseModel):
    total: int
    items: List[TimesheetResponse]


# Clock In/Out Requests
class ClockInRequest(BaseModel):
    employee_id: int
    work_date: date


class ClockOutRequest(BaseModel):
    employee_id: int
    work_date: date


class ClockResponse(BaseModel):
    success: bool
    timesheet_entry_id: int
    message: str


# Break Start/End Requests
class BreakStartRequest(BaseModel):
    timesheet_entry_id: int
    break_type: str  # MEAL, REST


class BreakEndRequest(BaseModel):
    break_entry_id: int


class BreakResponse(BaseModel):
    success: bool
    break_entry_id: int
    duration_minutes: int


# Timesheet Submit/Approve Requests
class TimesheetSubmitRequest(BaseModel):
    timesheet_id: int


class TimesheetApproveRequest(BaseModel):
    timesheet_id: int
    notes: Optional[str] = None


class TimesheetSubmitResponse(BaseModel):
    success: bool
    compliance_checked: bool
    violations: List[str] = []


# Compliance Violations List
class ComplianceViolationSummary(BaseModel):
    employee_id: int
    employee_name: str
    violation_type: str
    violation_date: date
    description: str
    severity: str
