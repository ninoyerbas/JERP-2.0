"""
JERP 2.0 - HR/HRIS Schemas
Pydantic models for HR management
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.models.hr import EmploymentStatus, EmploymentType, DocumentType


# Department Schemas
class DepartmentBase(BaseModel):
    """Base department fields"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    cost_center: Optional[str] = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    """Department creation request"""
    pass


class DepartmentUpdate(BaseModel):
    """Department update request - all fields optional"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    cost_center: Optional[str] = None
    is_active: Optional[bool] = None


class DepartmentResponse(DepartmentBase):
    """Department response with all fields"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Position Schemas
class PositionBase(BaseModel):
    """Base position fields"""
    title: str
    description: Optional[str] = None
    department_id: int
    is_exempt: bool = False
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None
    is_active: bool = True


class PositionCreate(PositionBase):
    """Position creation request"""
    pass


class PositionUpdate(BaseModel):
    """Position update request - all fields optional"""
    title: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None
    is_exempt: Optional[bool] = None
    min_salary: Optional[Decimal] = None
    max_salary: Optional[Decimal] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    """Position response with all fields"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Employee Schemas
class EmployeeBase(BaseModel):
    """Base employee fields"""
    employee_number: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    ssn_last_4: Optional[str] = Field(None, min_length=4, max_length=4)
    hire_date: date
    status: EmploymentStatus = EmploymentStatus.ACTIVE
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    position_id: int
    department_id: int
    manager_id: Optional[int] = None
    user_id: Optional[int] = None
    salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "USA"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    """Employee creation request"""
    pass


class EmployeeUpdate(BaseModel):
    """Employee update request - all fields optional"""
    employee_number: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    ssn_last_4: Optional[str] = Field(None, min_length=4, max_length=4)
    hire_date: Optional[date] = None
    status: Optional[EmploymentStatus] = None
    employment_type: Optional[EmploymentType] = None
    position_id: Optional[int] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    user_id: Optional[int] = None
    salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    notes: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    """Employee response with all fields"""
    id: int
    termination_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeWithDetails(EmployeeResponse):
    """Employee response with related entity details"""
    position: Optional[PositionResponse] = None
    department: Optional[DepartmentResponse] = None
    manager: Optional[EmployeeResponse] = None
    
    class Config:
        from_attributes = True


class EmployeeTermination(BaseModel):
    """Employee termination request"""
    termination_date: date
    reason: Optional[str] = None


class EmployeeHierarchy(BaseModel):
    """Employee hierarchy for org chart"""
    id: int
    employee_number: str
    first_name: str
    last_name: str
    email: str
    position_id: int
    department_id: int
    manager_id: Optional[int]
    direct_reports: List['EmployeeHierarchy'] = []
    
    class Config:
        from_attributes = True


# Document Schemas
class EmployeeDocumentBase(BaseModel):
    """Base employee document fields"""
    employee_id: int
    document_type: DocumentType
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None


class EmployeeDocumentCreate(EmployeeDocumentBase):
    """Employee document creation request"""
    pass


class EmployeeDocumentUpdate(BaseModel):
    """Employee document update request - all fields optional"""
    document_type: Optional[DocumentType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None


class EmployeeDocumentResponse(EmployeeDocumentBase):
    """Employee document response with all fields"""
    id: int
    uploaded_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentExpirationAlert(BaseModel):
    """Document expiration alert"""
    document_id: int
    employee_id: int
    employee_name: str
    document_type: DocumentType
    title: str
    expiration_date: date
    days_until_expiration: int
    
    class Config:
        from_attributes = True


# Update forward references for recursive models
EmployeeHierarchy.model_rebuild()
