"""
JERP 2.0 - HR Schemas
Pydantic models for HR/HRIS module
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Employee Schemas
class EmployeeBase(BaseModel):
    employee_number: str = Field(..., max_length=50)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    hire_date: date
    employment_type: str = Field(..., max_length=50)  # FULL_TIME, PART_TIME, CONTRACT
    employment_status: str = Field(default="ACTIVE", max_length=50)  # ACTIVE, TERMINATED, ON_LEAVE
    pay_rate: Optional[Decimal] = None
    pay_frequency: Optional[str] = Field(None, max_length=20)  # HOURLY, SALARY, BIWEEKLY, MONTHLY
    flsa_status: Optional[str] = Field(None, max_length=20)  # EXEMPT, NON_EXEMPT
    is_california_employee: bool = False
    work_location_state: Optional[str] = Field(None, max_length=2)


class EmployeeCreate(EmployeeBase):
    user_id: Optional[int] = None
    ssn_encrypted: Optional[str] = None


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    termination_date: Optional[date] = None
    employment_type: Optional[str] = Field(None, max_length=50)
    employment_status: Optional[str] = Field(None, max_length=50)
    pay_rate: Optional[Decimal] = None
    pay_frequency: Optional[str] = Field(None, max_length=20)
    flsa_status: Optional[str] = Field(None, max_length=20)
    is_california_employee: Optional[bool] = None
    work_location_state: Optional[str] = Field(None, max_length=2)


class EmployeeResponse(EmployeeBase):
    id: int
    user_id: Optional[int] = None
    termination_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class EmployeeList(BaseModel):
    total: int
    items: List[EmployeeResponse]


# Department Schemas
class DepartmentBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    manager_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    id: int
    manager_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DepartmentList(BaseModel):
    total: int
    items: List[DepartmentResponse]


# Position Schemas
class PositionBase(BaseModel):
    code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    department_id: Optional[int] = None
    flsa_classification: Optional[str] = Field(None, max_length=20)  # EXEMPT, NON_EXEMPT
    minimum_salary: Optional[Decimal] = None
    maximum_salary: Optional[Decimal] = None
    requires_certification: bool = False
    is_active: bool = True


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    department_id: Optional[int] = None
    flsa_classification: Optional[str] = Field(None, max_length=20)
    minimum_salary: Optional[Decimal] = None
    maximum_salary: Optional[Decimal] = None
    requires_certification: Optional[bool] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PositionList(BaseModel):
    total: int
    items: List[PositionResponse]


# Employee Document Schemas
class EmployeeDocumentBase(BaseModel):
    employee_id: int
    document_type: str = Field(..., max_length=100)
    file_path: str = Field(..., max_length=500)
    expiration_date: Optional[date] = None


class EmployeeDocumentCreate(EmployeeDocumentBase):
    pass


class EmployeeDocumentResponse(EmployeeDocumentBase):
    id: int
    uploaded_at: datetime
    uploaded_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
