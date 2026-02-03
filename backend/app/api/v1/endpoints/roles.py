"""
JERP 2.0 - Role & Permission Management Endpoints
CRUD operations for RBAC (Role-Based Access Control)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.role import Role, Permission
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionBase,
    PermissionResponse,
)
from app.schemas.user import UserResponse, UserListResponse
from app.api.v1.dependencies import require_superuser, get_current_active_user
from app.api.v1.exceptions import NotFoundException, ConflictException, BadRequestException


router = APIRouter()


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all roles with optional filtering.
    Available to any authenticated user.
    """
    query = db.query(Role)
    
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)
    
    roles = query.offset(skip).limit(limit).all()
    return [RoleResponse.model_validate(role) for role in roles]


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Create a new role (admin only).
    """
    # Check if role name already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise ConflictException(detail="Role name already exists")
    
    # Create role
    new_role = Role(
        name=role_data.name,
        description=role_data.description,
        is_active=role_data.is_active
    )
    
    # Add permissions if specified
    if role_data.permission_ids:
        permissions = db.query(Permission).filter(
            Permission.id.in_(role_data.permission_ids)
        ).all()
        if len(permissions) != len(role_data.permission_ids):
            raise BadRequestException(detail="One or more permission IDs are invalid")
        new_role.permissions = permissions
    
    db.add(new_role)
    db.flush()
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="role",
        resource_id=str(new_role.id),
        old_values=None,
        new_values={
            "name": new_role.name,
            "description": new_role.description,
            "permission_ids": role_data.permission_ids
        },
        description=f"Role created: {new_role.name}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    db.refresh(new_role)
    
    return RoleResponse.model_validate(new_role)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get role by ID.
    Available to any authenticated user.
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise NotFoundException(detail="Role not found")
    
    return RoleResponse.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    request: Request,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Update role (admin only).
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise NotFoundException(detail="Role not found")
    
    # Store old values for audit
    old_values = {
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permission_ids": [p.id for p in role.permissions]
    }
    
    update_data = role_update.model_dump(exclude_unset=True)
    
    # Check if name already exists (if being changed)
    if "name" in update_data and update_data["name"] != role.name:
        existing_role = db.query(Role).filter(Role.name == update_data["name"]).first()
        if existing_role:
            raise ConflictException(detail="Role name already exists")
    
    # Update permissions if specified
    if "permission_ids" in update_data:
        permission_ids = update_data.pop("permission_ids")
        permissions = db.query(Permission).filter(
            Permission.id.in_(permission_ids)
        ).all()
        if len(permissions) != len(permission_ids):
            raise BadRequestException(detail="One or more permission IDs are invalid")
        role.permissions = permissions
    
    # Update other fields
    for field, value in update_data.items():
        setattr(role, field, value)
    
    db.commit()
    db.refresh(role)
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    new_values = {
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permission_ids": [p.id for p in role.permissions]
    }
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="role",
        resource_id=str(role.id),
        old_values=old_values,
        new_values=new_values,
        description=f"Role updated: {role.name}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    
    return RoleResponse.model_validate(role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    request: Request,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Delete role (admin only).
    Prevents deletion if role has active users.
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise NotFoundException(detail="Role not found")
    
    # Check if role has active users
    active_users_count = db.query(User).filter(
        User.role_id == role_id,
        User.is_active == True
    ).count()
    
    if active_users_count > 0:
        raise BadRequestException(
            detail=f"Cannot delete role with {active_users_count} active users"
        )
    
    # Create audit log before deletion
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="DELETE",
        resource_type="role",
        resource_id=str(role.id),
        old_values={
            "name": role.name,
            "description": role.description,
            "permission_ids": [p.id for p in role.permissions]
        },
        new_values=None,
        description=f"Role deleted: {role.name}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    
    # Delete role
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted successfully"}


@router.get("/{role_id}/users", response_model=UserListResponse)
async def get_role_users(
    role_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get users with specific role.
    Available to any authenticated user.
    """
    # Check if role exists
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise NotFoundException(detail="Role not found")
    
    # Query users with this role
    query = db.query(User).filter(User.role_id == role_id)
    total = query.count()
    
    users = query.offset(skip).limit(limit).all()
    
    return UserListResponse(
        total=total,
        items=[UserResponse.model_validate(user) for user in users]
    )


# Permission endpoints
@router.get("/permissions/list", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    module: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all permissions with optional filtering.
    Available to any authenticated user.
    """
    query = db.query(Permission)
    
    if module:
        query = query.filter(Permission.module == module)
    
    permissions = query.offset(skip).limit(limit).all()
    return [PermissionResponse.model_validate(perm) for perm in permissions]


@router.post("/permissions/create", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionBase,
    request: Request,
    current_user: User = Depends(require_superuser),
    db: Session = Depends(get_db)
):
    """
    Create a new permission (admin only).
    """
    # Check if permission code already exists
    existing_perm = db.query(Permission).filter(
        Permission.code == permission_data.code
    ).first()
    if existing_perm:
        raise ConflictException(detail="Permission code already exists")
    
    # Create permission
    new_permission = Permission(
        code=permission_data.code,
        name=permission_data.name,
        description=permission_data.description,
        module=permission_data.module
    )
    
    db.add(new_permission)
    db.flush()
    
    # Create audit log
    previous_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    audit_log = AuditLog.create_entry(
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="permission",
        resource_id=str(new_permission.id),
        old_values=None,
        new_values={
            "code": new_permission.code,
            "name": new_permission.name,
            "module": new_permission.module
        },
        description=f"Permission created: {new_permission.code}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        previous_hash=previous_log.current_hash if previous_log else None
    )
    db.add(audit_log)
    db.commit()
    db.refresh(new_permission)
    
    return PermissionResponse.model_validate(new_permission)
