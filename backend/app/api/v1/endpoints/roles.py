"""
JERP 2.0 - Roles & Permissions Endpoints
RBAC management API
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, get_current_superuser
from app.models.user import User
from app.models.role import Role, Permission
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse
)
from app.services.auth_service import create_audit_log

router = APIRouter()


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all roles with pagination."""
    roles = db.query(Role).offset(skip).limit(limit).all()
    return roles


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    request: Request,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Create a new role (superuser only)."""
    # Check if role name already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )
    
    # Create role
    role = Role(
        name=role_data.name,
        description=role_data.description,
        is_active=role_data.is_active
    )
    
    # Add permissions
    if role_data.permission_ids:
        permissions = db.query(Permission).filter(
            Permission.id.in_(role_data.permission_ids)
        ).all()
        if len(permissions) != len(role_data.permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permissions not found"
            )
        role.permissions = permissions
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="role",
        resource_id=str(role.id),
        new_values={
            "name": role.name,
            "description": role.description,
            "permission_ids": role_data.permission_ids
        },
        description=f"Created role: {role.name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return role


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get role by ID."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    request: Request,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Update role by ID (superuser only)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Store old values
    old_values = {
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permission_ids": [p.id for p in role.permissions]
    }
    
    # Update fields
    if role_data.name is not None:
        # Check if name is already taken
        existing = db.query(Role).filter(
            Role.name == role_data.name,
            Role.id != role_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists"
            )
        role.name = role_data.name
    
    if role_data.description is not None:
        role.description = role_data.description
    
    if role_data.is_active is not None:
        role.is_active = role_data.is_active
    
    # Update permissions
    if role_data.permission_ids is not None:
        permissions = db.query(Permission).filter(
            Permission.id.in_(role_data.permission_ids)
        ).all()
        if len(permissions) != len(role_data.permission_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more permissions not found"
            )
        role.permissions = permissions
    
    db.commit()
    db.refresh(role)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    new_values = {
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "permission_ids": [p.id for p in role.permissions]
    }
    
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="UPDATE",
        resource_type="role",
        resource_id=str(role.id),
        old_values=old_values,
        new_values=new_values,
        description=f"Updated role: {role.name}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    request: Request,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete role by ID (superuser only)."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if role has users assigned
    users_count = db.query(User).filter(User.role_id == role_id).count()
    if users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role with {users_count} users assigned"
        )
    
    # Store old values for audit
    old_values = {
        "name": role.name,
        "description": role.description
    }
    
    db.delete(role)
    db.commit()
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="DELETE",
        resource_type="role",
        resource_id=str(role_id),
        old_values=old_values,
        description=f"Deleted role: {old_values['name']}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return None


@router.get("/permissions/list", response_model=List[PermissionResponse])
async def list_permissions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all permissions with pagination."""
    permissions = db.query(Permission).offset(skip).limit(limit).all()
    return permissions


@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    request: Request,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Create a new permission (superuser only)."""
    # Check if permission code already exists
    existing_permission = db.query(Permission).filter(
        Permission.code == permission_data.code
    ).first()
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission code already exists"
        )
    
    # Create permission
    permission = Permission(
        code=permission_data.code,
        name=permission_data.name,
        description=permission_data.description,
        module=permission_data.module
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    # Create audit log
    ip_address, user_agent = get_client_info(request)
    create_audit_log(
        db=db,
        user_id=current_user.id,
        user_email=current_user.email,
        action="CREATE",
        resource_type="permission",
        resource_id=str(permission.id),
        new_values={
            "code": permission.code,
            "name": permission.name,
            "module": permission.module
        },
        description=f"Created permission: {permission.code}",
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return permission
