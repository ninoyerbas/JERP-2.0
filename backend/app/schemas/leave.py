"""
JERP 2.0 - Leave Management Schemas
Pydantic models for Leave Management module
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Leave Policy Schemas
class LeavePolicyBase(BaseModel):
    name: str = Field(..., max_length=100)
    leave_type: str = Field(..., max_length=50)  # PTO, SICK, VACATION, UNPAID
    accrual_rate: Optional[Decimal] = None  # Hours per pay period
    max_balance: Optional[Decimal] = None
    carry_over_allowed: bool = True
    max_carry_over: Optional[Decimal] = None
    requires_approval: bool = True
    is_active: bool = True


class LeavePolicyCreate(LeavePolicyBase):
    pass


class LeavePolicyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    leave_type: Optional[str] = Field(None, max_length=50)
    accrual_rate: Optional[Decimal] = None
    max_balance: Optional[Decimal] = None
    carry_over_allowed: Optional[bool] = None
    max_carry_over: Optional[Decimal] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None


class LeavePolicyResponse(LeavePolicyBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LeavePolicyList(BaseModel):
    total: int
    items: List[LeavePolicyResponse]


# Leave Balance Schemas
class LeaveBalanceBase(BaseModel):
    employee_id: int
    policy_id: int
    available_hours: Decimal = Field(default=Decimal("0"))
    pending_hours: Decimal = Field(default=Decimal("0"))
    used_hours: Decimal = Field(default=Decimal("0"))
    last_accrual_date: Optional[date] = None


class LeaveBalanceCreate(LeaveBalanceBase):
    pass


class LeaveBalanceUpdate(BaseModel):
    available_hours: Optional[Decimal] = None
    pending_hours: Optional[Decimal] = None
    used_hours: Optional[Decimal] = None
    last_accrual_date: Optional[date] = None


class LeaveBalanceResponse(LeaveBalanceBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)


class LeaveBalanceList(BaseModel):
    total: int
    items: List[LeaveBalanceResponse]


# Leave Request Schemas
class LeaveRequestBase(BaseModel):
    employee_id: int
    policy_id: int
    start_date: date
    end_date: date
    hours_requested: Decimal
    reason: Optional[str] = None
    status: str = Field(default="PENDING", max_length=20)  # PENDING, APPROVED, REJECTED, CANCELLED


class LeaveRequestCreate(LeaveRequestBase):
    pass


class LeaveRequestUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hours_requested: Optional[Decimal] = None
    reason: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class LeaveRequestResponse(LeaveRequestBase):
    id: int
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LeaveRequestList(BaseModel):
    total: int
    items: List[LeaveRequestResponse]


# Leave Request Approve/Reject
class LeaveRequestReviewRequest(BaseModel):
    review_notes: Optional[str] = None


class LeaveRequestReviewResponse(BaseModel):
    success: bool
    message: str
    leave_request: LeaveRequestResponse


# Leave Calendar
class LeaveCalendarEntry(BaseModel):
    employee_id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    status: str


class LeaveCalendarResponse(BaseModel):
    start_date: date
    end_date: date
    entries: List[LeaveCalendarEntry]
