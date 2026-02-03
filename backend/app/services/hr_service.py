"""
JERP 2.0 - HR Service
Business logic for HR management operations
"""
from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from fastapi import HTTPException, status

from app.models.hr import Employee, Department, Position, EmployeeDocument, EmploymentStatus
from app.models.user import User
from app.schemas.hr import (
    EmployeeCreate, EmployeeUpdate, EmployeeTermination,
    DepartmentCreate, DepartmentUpdate,
    PositionCreate, PositionUpdate,
    EmployeeDocumentCreate, EmployeeDocumentUpdate,
    EmployeeHierarchy, DocumentExpirationAlert
)
from app.services.auth_service import create_audit_log


# Department Services
def create_department(
    department_data: DepartmentCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Department:
    """Create a new department with audit logging."""
    # Check if department name already exists
    existing = db.query(Department).filter(Department.name == department_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department name already exists"
        )
    
    # Validate parent department if provided
    if department_data.parent_id:
        parent = db.query(Department).filter(Department.id == department_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found"
            )
    
    # Create department
    department = Department(**department_data.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="department",
        resource_id=str(department.id),
        new_values=department_data.model_dump(),
        description=f"Created department {department.name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return department


def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Department:
    """Update department with audit logging."""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Store old values
    old_values = {
        "name": department.name,
        "description": department.description,
        "parent_id": department.parent_id,
        "cost_center": department.cost_center,
        "is_active": department.is_active
    }
    
    # Update fields
    update_data = department_data.model_dump(exclude_unset=True)
    
    # Check for name uniqueness if name is being updated
    if "name" in update_data and update_data["name"] != department.name:
        existing = db.query(Department).filter(
            Department.name == update_data["name"],
            Department.id != department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department name already exists"
            )
    
    # Validate parent if being updated
    if "parent_id" in update_data and update_data["parent_id"]:
        if update_data["parent_id"] == department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department cannot be its own parent"
            )
        parent = db.query(Department).filter(Department.id == update_data["parent_id"]).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found"
            )
    
    # Apply updates
    for key, value in update_data.items():
        setattr(department, key, value)
    
    db.commit()
    db.refresh(department)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="department",
        resource_id=str(department.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated department {department.name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return department


# Position Services
def create_position(
    position_data: PositionCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Position:
    """Create a new position with audit logging."""
    # Validate department
    department = db.query(Department).filter(Department.id == position_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Create position
    position = Position(**position_data.model_dump())
    db.add(position)
    db.commit()
    db.refresh(position)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="position",
        resource_id=str(position.id),
        new_values=position_data.model_dump(),
        description=f"Created position {position.title}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return position


def update_position(
    position_id: int,
    position_data: PositionUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Position:
    """Update position with audit logging."""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Store old values
    old_values = {
        "title": position.title,
        "description": position.description,
        "department_id": position.department_id,
        "is_exempt": position.is_exempt,
        "min_salary": str(position.min_salary) if position.min_salary else None,
        "max_salary": str(position.max_salary) if position.max_salary else None,
        "is_active": position.is_active
    }
    
    # Update fields
    update_data = position_data.model_dump(exclude_unset=True)
    
    # Validate department if being updated
    if "department_id" in update_data:
        department = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    
    # Apply updates
    for key, value in update_data.items():
        setattr(position, key, value)
    
    db.commit()
    db.refresh(position)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="position",
        resource_id=str(position.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated position {position.title}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return position


# Employee Services
def create_employee(
    employee_data: EmployeeCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Employee:
    """Create a new employee with audit logging."""
    # Check for duplicate employee number
    existing = db.query(Employee).filter(Employee.employee_number == employee_data.employee_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee number already exists"
        )
    
    # Check for duplicate email
    existing_email = db.query(Employee).filter(Employee.email == employee_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Validate position
    position = db.query(Position).filter(Position.id == employee_data.position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Validate department
    department = db.query(Department).filter(Department.id == employee_data.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Validate manager if provided
    if employee_data.manager_id:
        manager = db.query(Employee).filter(Employee.id == employee_data.manager_id).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found"
            )
    
    # Validate user if provided
    if employee_data.user_id:
        user = db.query(User).filter(User.id == employee_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        # Check if user is already linked to another employee
        existing_user = db.query(Employee).filter(Employee.user_id == employee_data.user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already linked to another employee"
            )
    
    # Create employee
    employee = Employee(**employee_data.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    # Create audit log (exclude sensitive data like SSN)
    audit_data = employee_data.model_dump()
    if audit_data.get("ssn_last_4"):
        audit_data["ssn_last_4"] = "****"
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="employee",
        resource_id=str(employee.id),
        new_values=audit_data,
        description=f"Created employee {employee.employee_number} - {employee.first_name} {employee.last_name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return employee


def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Employee:
    """Update employee with audit logging."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Store old values (sanitize SSN)
    old_values = {
        "employee_number": employee.employee_number,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "email": employee.email,
        "status": employee.status.value if employee.status else None,
        "position_id": employee.position_id,
        "department_id": employee.department_id,
        "manager_id": employee.manager_id
    }
    
    # Update fields
    update_data = employee_data.model_dump(exclude_unset=True)
    
    # Check for duplicate employee number if being updated
    if "employee_number" in update_data and update_data["employee_number"] != employee.employee_number:
        existing = db.query(Employee).filter(
            Employee.employee_number == update_data["employee_number"],
            Employee.id != employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee number already exists"
            )
    
    # Check for duplicate email if being updated
    if "email" in update_data and update_data["email"] != employee.email:
        existing = db.query(Employee).filter(
            Employee.email == update_data["email"],
            Employee.id != employee_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Validate position if being updated
    if "position_id" in update_data:
        position = db.query(Position).filter(Position.id == update_data["position_id"]).first()
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )
    
    # Validate department if being updated
    if "department_id" in update_data:
        department = db.query(Department).filter(Department.id == update_data["department_id"]).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    
    # Validate manager if being updated
    if "manager_id" in update_data and update_data["manager_id"]:
        if update_data["manager_id"] == employee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee cannot be their own manager"
            )
        manager = db.query(Employee).filter(Employee.id == update_data["manager_id"]).first()
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manager not found"
            )
    
    # Validate user if being updated
    if "user_id" in update_data and update_data["user_id"]:
        user = db.query(User).filter(User.id == update_data["user_id"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        # Check if user is already linked to another employee
        existing_user = db.query(Employee).filter(
            Employee.user_id == update_data["user_id"],
            Employee.id != employee_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already linked to another employee"
            )
    
    # Apply updates
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    db.commit()
    db.refresh(employee)
    
    # Create audit log (sanitize SSN)
    audit_update = update_data.copy()
    if "ssn_last_4" in audit_update:
        audit_update["ssn_last_4"] = "****"
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="employee",
        resource_id=str(employee.id),
        old_values=old_values,
        new_values=audit_update,
        description=f"Updated employee {employee.employee_number} - {employee.first_name} {employee.last_name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return employee


def terminate_employee(
    employee_id: int,
    termination_data: EmployeeTermination,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Employee:
    """Terminate an employee with audit logging."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    if employee.status == EmploymentStatus.TERMINATED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee is already terminated"
        )
    
    # Store old values
    old_values = {
        "status": employee.status.value,
        "termination_date": None
    }
    
    # Update employee
    employee.status = EmploymentStatus.TERMINATED
    employee.termination_date = termination_data.termination_date
    
    # Deactivate linked user account if exists
    if employee.user_id:
        user = db.query(User).filter(User.id == employee.user_id).first()
        if user:
            user.is_active = False
    
    db.commit()
    db.refresh(employee)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="TERMINATE",
        resource_type="employee",
        resource_id=str(employee.id),
        old_values=old_values,
        new_values={
            "status": EmploymentStatus.TERMINATED.value,
            "termination_date": str(termination_data.termination_date),
            "reason": termination_data.reason
        },
        description=f"Terminated employee {employee.employee_number} - {employee.first_name} {employee.last_name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return employee


def get_employee_hierarchy(
    employee_id: Optional[int],
    db: Session
) -> List[EmployeeHierarchy]:
    """Get employee hierarchy for org chart."""
    if employee_id:
        # Get specific employee and their direct reports
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        employees = [employee]
    else:
        # Get all employees without managers (top-level)
        employees = db.query(Employee).filter(Employee.manager_id == None).all()
    
    def build_hierarchy(emp: Employee) -> EmployeeHierarchy:
        """Recursively build employee hierarchy."""
        hierarchy = EmployeeHierarchy(
            id=emp.id,
            employee_number=emp.employee_number,
            first_name=emp.first_name,
            last_name=emp.last_name,
            email=emp.email,
            position_id=emp.position_id,
            department_id=emp.department_id,
            manager_id=emp.manager_id,
            direct_reports=[]
        )
        
        # Get direct reports
        direct_reports = db.query(Employee).filter(Employee.manager_id == emp.id).all()
        hierarchy.direct_reports = [build_hierarchy(report) for report in direct_reports]
        
        return hierarchy
    
    return [build_hierarchy(emp) for emp in employees]


# Document Services
def create_employee_document(
    document_data: EmployeeDocumentCreate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> EmployeeDocument:
    """Create a new employee document with audit logging."""
    # Validate employee
    employee = db.query(Employee).filter(Employee.id == document_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Create document
    document = EmployeeDocument(**document_data.model_dump())
    document.uploaded_by = current_user.id
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="employee_document",
        resource_id=str(document.id),
        new_values=document_data.model_dump(),
        description=f"Created document {document.title} for employee {employee.employee_number}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return document


def update_employee_document(
    document_id: int,
    document_data: EmployeeDocumentUpdate,
    current_user: User,
    db: Session,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> EmployeeDocument:
    """Update employee document with audit logging."""
    document = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Store old values
    old_values = {
        "document_type": document.document_type.value,
        "title": document.title,
        "expiration_date": str(document.expiration_date) if document.expiration_date else None
    }
    
    # Update fields
    update_data = document_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
    
    # Create audit log
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="employee_document",
        resource_id=str(document.id),
        old_values=old_values,
        new_values=update_data,
        description=f"Updated document {document.title}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return document


def check_expiring_documents(
    days_ahead: int,
    db: Session
) -> List[DocumentExpirationAlert]:
    """Check for documents expiring within specified days."""
    today = date.today()
    expiration_date = today + timedelta(days=days_ahead)
    
    # Query documents expiring within the period
    expiring_docs = db.query(EmployeeDocument).join(Employee).filter(
        and_(
            EmployeeDocument.expiration_date != None,
            EmployeeDocument.expiration_date >= today,
            EmployeeDocument.expiration_date <= expiration_date
        )
    ).all()
    
    alerts = []
    for doc in expiring_docs:
        days_until = (doc.expiration_date - today).days
        alert = DocumentExpirationAlert(
            document_id=doc.id,
            employee_id=doc.employee_id,
            employee_name=f"{doc.employee.first_name} {doc.employee.last_name}",
            document_type=doc.document_type,
            title=doc.title,
            expiration_date=doc.expiration_date,
            days_until_expiration=days_until
        )
        alerts.append(alert)
    
    return alerts
