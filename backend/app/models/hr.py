"""
JERP 2.0 - HR/HRIS Models
Employee, Department, Position, and Document models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Numeric, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class EmploymentStatus(str, enum.Enum):
    """Employment status enumeration"""
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"


class EmploymentType(str, enum.Enum):
    """Employment type enumeration"""
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERN = "INTERN"


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    I9 = "I9"
    W4 = "W4"
    OFFER_LETTER = "OFFER_LETTER"
    NDA = "NDA"
    PERFORMANCE_REVIEW = "PERFORMANCE_REVIEW"
    DISCIPLINARY_ACTION = "DISCIPLINARY_ACTION"
    BENEFITS_ENROLLMENT = "BENEFITS_ENROLLMENT"
    OTHER = "OTHER"


class Department(Base):
    """Department model with hierarchy support"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Hierarchy support
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    parent = relationship("Department", remote_side=[id], backref="children")
    
    # Cost center for financial tracking
    cost_center = Column(String(50), nullable=True, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    employees = relationship("Employee", back_populates="department")
    positions = relationship("Position", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"


class Position(Base):
    """Position model with FLSA exemption status"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Department relationship
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    department = relationship("Department", back_populates="positions")
    
    # FLSA exemption status
    is_exempt = Column(Boolean, default=False, nullable=False)
    
    # Salary range
    min_salary = Column(Numeric(12, 2), nullable=True)
    max_salary = Column(Numeric(12, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    employees = relationship("Employee", back_populates="position")

    def __repr__(self):
        return f"<Position(id={self.id}, title='{self.title}')>"


class Employee(Base):
    """Employee model with comprehensive fields"""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Personal information
    employee_number = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    middle_name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Security - last 4 digits only
    ssn_last_4 = Column(String(4), nullable=True)
    
    # Employment details
    hire_date = Column(Date, nullable=False, index=True)
    termination_date = Column(Date, nullable=True, index=True)
    status = Column(SQLEnum(EmploymentStatus), default=EmploymentStatus.ACTIVE, nullable=False, index=True)
    employment_type = Column(SQLEnum(EmploymentType), default=EmploymentType.FULL_TIME, nullable=False, index=True)
    
    # Position and department
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)
    position = relationship("Position", back_populates="employees")
    
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    department = relationship("Department", back_populates="employees")
    
    # Manager relationship (self-referential)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    manager = relationship("Employee", remote_side=[id], backref="direct_reports")
    
    # User account linkage
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)
    user = relationship("User")
    
    # Compensation
    salary = Column(Numeric(12, 2), nullable=True)
    hourly_rate = Column(Numeric(8, 2), nullable=True)
    
    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="USA", nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(100), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    documents = relationship("EmployeeDocument", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee(id={self.id}, employee_number='{self.employee_number}', name='{self.first_name} {self.last_name}')>"

    __table_args__ = (
        Index('idx_employee_name', 'last_name', 'first_name'),
        Index('idx_employee_status_dept', 'status', 'department_id'),
    )


class EmployeeDocument(Base):
    """Employee document model for document management"""
    __tablename__ = "employee_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Employee relationship
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    employee = relationship("Employee", back_populates="documents")
    
    # Document details
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File storage
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Expiration tracking
    issue_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True, index=True)
    
    # Audit
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EmployeeDocument(id={self.id}, employee_id={self.employee_id}, type='{self.document_type}')>"

    __table_args__ = (
        Index('idx_document_expiration', 'expiration_date', 'document_type'),
    )
