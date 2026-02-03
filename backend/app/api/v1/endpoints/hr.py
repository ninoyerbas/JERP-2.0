"""
JERP 2.0 - HR Management Endpoints
CRUD operations for HR/HRIS management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.hr import Employee, Department, Position, EmployeeDocument, EmploymentStatus
from app.schemas.hr import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    PositionCreate, PositionUpdate, PositionResponse,
    EmployeeCreate, EmployeeUpdate, EmployeeResponse, EmployeeWithDetails,
    EmployeeTermination, EmployeeHierarchy,
    EmployeeDocumentCreate, EmployeeDocumentUpdate, EmployeeDocumentResponse,
    DocumentExpirationAlert
)
from app.services.hr_service import (
    create_department, update_department,
    create_position, update_position,
    create_employee, update_employee, terminate_employee, get_employee_hierarchy,
    create_employee_document, update_employee_document, check_expiring_documents
)

router = APIRouter()


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


# Department Endpoints
@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_id: Optional[int] = Query(None, description="Filter by parent department"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all departments with pagination and filtering."""
    query = db.query(Department)
    
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    
    if parent_id is not None:
        query = query.filter(Department.parent_id == parent_id)
    
    departments = query.offset(skip).limit(limit).all()
    return departments


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_department(
    department_data: DepartmentCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new department."""
    ip_address, user_agent = get_client_info(request)
    department = create_department(department_data, current_user, db, ip_address, user_agent)
    return department


@router.get("/departments/{department_id}", response_model=DepartmentResponse)
async def get_department_by_id(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get department by ID."""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return department


@router.put("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department_by_id(
    department_id: int,
    department_data: DepartmentUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update department by ID."""
    ip_address, user_agent = get_client_info(request)
    department = update_department(department_id, department_data, current_user, db, ip_address, user_agent)
    return department


@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department_by_id(
    department_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Soft delete department by ID (deactivates it)."""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Soft delete by deactivating
    ip_address, user_agent = get_client_info(request)
    department_update = DepartmentUpdate(is_active=False)
    update_department(department_id, department_update, current_user, db, ip_address, user_agent)
    return None


# Position Endpoints
@router.get("/positions", response_model=List[PositionResponse])
async def list_positions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_exempt: Optional[bool] = Query(None, description="Filter by FLSA exemption status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all positions with pagination and filtering."""
    query = db.query(Position)
    
    if department_id is not None:
        query = query.filter(Position.department_id == department_id)
    
    if is_active is not None:
        query = query.filter(Position.is_active == is_active)
    
    if is_exempt is not None:
        query = query.filter(Position.is_exempt == is_exempt)
    
    positions = query.offset(skip).limit(limit).all()
    return positions


@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_position(
    position_data: PositionCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new position."""
    ip_address, user_agent = get_client_info(request)
    position = create_position(position_data, current_user, db, ip_address, user_agent)
    return position


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position_by_id(
    position_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get position by ID."""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    return position


@router.put("/positions/{position_id}", response_model=PositionResponse)
async def update_position_by_id(
    position_id: int,
    position_data: PositionUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update position by ID."""
    ip_address, user_agent = get_client_info(request)
    position = update_position(position_id, position_data, current_user, db, ip_address, user_agent)
    return position


@router.delete("/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position_by_id(
    position_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Soft delete position by ID (deactivates it)."""
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found"
        )
    
    # Soft delete by deactivating
    ip_address, user_agent = get_client_info(request)
    position_update = PositionUpdate(is_active=False)
    update_position(position_id, position_update, current_user, db, ip_address, user_agent)
    return None


# Employee Endpoints
@router.get("/employees", response_model=List[EmployeeResponse])
async def list_employees(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    status_filter: Optional[EmploymentStatus] = Query(None, alias="status", description="Filter by employment status"),
    department_id: Optional[int] = Query(None, description="Filter by department"),
    manager_id: Optional[int] = Query(None, description="Filter by manager"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all employees with pagination and filtering."""
    query = db.query(Employee)
    
    if status_filter is not None:
        query = query.filter(Employee.status == status_filter)
    
    if department_id is not None:
        query = query.filter(Employee.department_id == department_id)
    
    if manager_id is not None:
        query = query.filter(Employee.manager_id == manager_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Employee.first_name.like(search_pattern)) |
            (Employee.last_name.like(search_pattern)) |
            (Employee.email.like(search_pattern)) |
            (Employee.employee_number.like(search_pattern))
        )
    
    employees = query.offset(skip).limit(limit).all()
    return employees


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_employee(
    employee_data: EmployeeCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new employee."""
    ip_address, user_agent = get_client_info(request)
    employee = create_employee(employee_data, current_user, db, ip_address, user_agent)
    return employee


@router.get("/employees/{employee_id}", response_model=EmployeeWithDetails)
async def get_employee_by_id(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get employee by ID with related details."""
    employee = db.query(Employee).options(
        joinedload(Employee.position),
        joinedload(Employee.department),
        joinedload(Employee.manager)
    ).filter(Employee.id == employee_id).first()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    return employee


@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee_by_id(
    employee_id: int,
    employee_data: EmployeeUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update employee by ID."""
    ip_address, user_agent = get_client_info(request)
    employee = update_employee(employee_id, employee_data, current_user, db, ip_address, user_agent)
    return employee


@router.post("/employees/{employee_id}/terminate", response_model=EmployeeResponse)
async def terminate_employee_by_id(
    employee_id: int,
    termination_data: EmployeeTermination,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Terminate an employee."""
    ip_address, user_agent = get_client_info(request)
    employee = terminate_employee(employee_id, termination_data, current_user, db, ip_address, user_agent)
    return employee


@router.get("/employees/{employee_id}/hierarchy", response_model=List[EmployeeHierarchy])
async def get_employee_hierarchy_by_id(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get employee hierarchy (org chart) starting from specific employee."""
    hierarchy = get_employee_hierarchy(employee_id, db)
    return hierarchy


@router.get("/employees/hierarchy/all", response_model=List[EmployeeHierarchy])
async def get_all_employee_hierarchy(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get complete employee hierarchy (org chart) starting from top-level employees."""
    hierarchy = get_employee_hierarchy(None, db)
    return hierarchy


# Document Endpoints
@router.get("/employees/{employee_id}/documents", response_model=List[EmployeeDocumentResponse])
async def list_employee_documents(
    employee_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all documents for an employee."""
    # Verify employee exists
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    documents = db.query(EmployeeDocument).filter(
        EmployeeDocument.employee_id == employee_id
    ).offset(skip).limit(limit).all()
    
    return documents


@router.post("/employees/{employee_id}/documents", response_model=EmployeeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_employee_document_for_employee(
    employee_id: int,
    document_data: EmployeeDocumentCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new document for an employee."""
    # Ensure the employee_id in path matches the one in body
    if document_data.employee_id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID in path must match employee ID in body"
        )
    
    ip_address, user_agent = get_client_info(request)
    document = create_employee_document(document_data, current_user, db, ip_address, user_agent)
    return document


@router.get("/documents", response_model=List[EmployeeDocumentResponse])
async def list_all_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all employee documents."""
    documents = db.query(EmployeeDocument).offset(skip).limit(limit).all()
    return documents


@router.get("/documents/{document_id}", response_model=EmployeeDocumentResponse)
async def get_document_by_id(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document by ID."""
    document = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.put("/documents/{document_id}", response_model=EmployeeDocumentResponse)
async def update_document_by_id(
    document_id: int,
    document_data: EmployeeDocumentUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update document by ID."""
    ip_address, user_agent = get_client_info(request)
    document = update_employee_document(document_id, document_data, current_user, db, ip_address, user_agent)
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_by_id(
    document_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete document by ID."""
    document = db.query(EmployeeDocument).filter(EmployeeDocument.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create audit log for deletion
    from app.services.auth_service import create_audit_log
    ip_address, user_agent = get_client_info(request)
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="DELETE",
        resource_type="employee_document",
        resource_id=str(document.id),
        old_values={"title": document.title, "document_type": document.document_type.value},
        description=f"Deleted document {document.title}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.delete(document)
    db.commit()
    return None


@router.get("/documents/expiring/alerts", response_model=List[DocumentExpirationAlert])
async def get_expiring_documents(
    days: int = Query(30, ge=1, le=365, description="Days ahead to check for expiring documents"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get alerts for documents expiring within specified days."""
    alerts = check_expiring_documents(days, db)
    return alerts
