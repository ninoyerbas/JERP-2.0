"""
JERP 2.0 - HR/HRIS Models
Employee master data with compliance tracking
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from app.core.database import Base


class Employee(Base):
    """Employee master data with compliance tracking"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to auth user
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    ssn_encrypted = Column(String(255))  # Encrypted SSN
    
    # Employment Details
    department_id = Column(Integer, ForeignKey("departments.id"))
    position_id = Column(Integer, ForeignKey("positions.id"))
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    employment_type = Column(String(50))  # FULL_TIME, PART_TIME, CONTRACT
    employment_status = Column(String(50))  # ACTIVE, TERMINATED, ON_LEAVE
    
    # Compensation
    pay_rate = Column(DECIMAL(15, 2))
    pay_frequency = Column(String(20))  # HOURLY, SALARY, BIWEEKLY, MONTHLY
    flsa_status = Column(String(20))  # EXEMPT, NON_EXEMPT
    
    # Compliance & Tracking
    is_california_employee = Column(Boolean, default=False)  # For CA Labor Code
    work_location_state = Column(String(2))  # State code for compliance
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    position = relationship("Position", back_populates="employees")
    manager = relationship("Employee", remote_side=[id], foreign_keys=[manager_id], back_populates="subordinates")
    subordinates = relationship("Employee", back_populates="manager", foreign_keys=[manager_id])
    timesheets = relationship("Timesheet", back_populates="employee")
    leave_requests = relationship("LeaveRequest", back_populates="employee")
    documents = relationship("EmployeeDocument", back_populates="employee")


class Department(Base):
    """Organizational departments"""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")
    manager = relationship("Employee", foreign_keys=[manager_id], post_update=True)
    parent = relationship("Department", remote_side=[id], foreign_keys=[parent_id], back_populates="children")
    children = relationship("Department", back_populates="parent", foreign_keys=[parent_id])


class Position(Base):
    """Job positions with FLSA classification"""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"))
    flsa_classification = Column(String(20))  # EXEMPT, NON_EXEMPT
    minimum_salary = Column(DECIMAL(15, 2))
    maximum_salary = Column(DECIMAL(15, 2))
    requires_certification = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    department = relationship("Department")
    employees = relationship("Employee", back_populates="position")


class EmployeeDocument(Base):
    """Employee documents and certifications"""
    __tablename__ = "employee_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    document_type = Column(String(100))  # W4, I9, CERTIFICATION, etc.
    file_path = Column(String(500))
    expiration_date = Column(Date, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    
    employee = relationship("Employee", back_populates="documents")
    uploader = relationship("User")
