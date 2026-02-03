"""
Database Initialization Script

Initialize database with default data:
- Creates default roles (superadmin, admin, manager, user)
- Creates default permissions
- Creates initial superuser from environment variables
- Creates audit log entry for initialization
"""
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import SessionLocal, Base, jerp_engine
from app.models.user import User
from app.models.role import Role, Permission, role_permissions
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


# Default roles configuration
DEFAULT_ROLES = [
    {
        "name": "Superadmin",
        "description": "Full system access with all privileges"
    },
    {
        "name": "Admin",
        "description": "Administrative access to manage users and system settings"
    },
    {
        "name": "Manager",
        "description": "Management level access with department oversight"
    },
    {
        "name": "User",
        "description": "Basic user access with standard permissions"
    }
]


# Default permissions configuration
DEFAULT_PERMISSIONS = [
    # User permissions
    {"code": "user:read", "name": "Read Users", "module": "users", "description": "View user information"},
    {"code": "user:create", "name": "Create Users", "module": "users", "description": "Create new users"},
    {"code": "user:update", "name": "Update Users", "module": "users", "description": "Modify user information"},
    {"code": "user:delete", "name": "Delete Users", "module": "users", "description": "Delete users"},
    
    # Role permissions
    {"code": "role:read", "name": "Read Roles", "module": "roles", "description": "View role information"},
    {"code": "role:create", "name": "Create Roles", "module": "roles", "description": "Create new roles"},
    {"code": "role:update", "name": "Update Roles", "module": "roles", "description": "Modify role information"},
    {"code": "role:delete", "name": "Delete Roles", "module": "roles", "description": "Delete roles"},
    
    # Audit permissions
    {"code": "audit:read", "name": "Read Audit Logs", "module": "audit", "description": "View audit log entries"},
    
    # Compliance permissions
    {"code": "compliance:read", "name": "Read Compliance", "module": "compliance", "description": "View compliance violations and reports"},
    {"code": "compliance:write", "name": "Write Compliance", "module": "compliance", "description": "Create and modify compliance data"},
    
    # System permissions
    {"code": "system:admin", "name": "System Administration", "module": "system", "description": "Full system administration access"},
]


# Role-Permission mapping
ROLE_PERMISSION_MAPPING = {
    "Superadmin": [
        "user:read", "user:create", "user:update", "user:delete",
        "role:read", "role:create", "role:update", "role:delete",
        "audit:read", "compliance:read", "compliance:write",
        "system:admin"
    ],
    "Admin": [
        "user:read", "user:create", "user:update",
        "role:read", "audit:read",
        "compliance:read", "compliance:write"
    ],
    "Manager": [
        "user:read", "compliance:read", "compliance:write"
    ],
    "User": [
        "user:read", "compliance:read"
    ]
}


def create_default_roles(db: Session) -> dict:
    """Create default roles if they don't exist"""
    created_roles = {}
    
    for role_data in DEFAULT_ROLES:
        existing_role = db.query(Role).filter(Role.name == role_data["name"]).first()
        
        if not existing_role:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                is_active=True
            )
            db.add(role)
            db.flush()
            created_roles[role.name] = role
            logger.info(f"Created role: {role.name}")
        else:
            created_roles[existing_role.name] = existing_role
            logger.info(f"Role already exists: {existing_role.name}")
    
    db.commit()
    return created_roles


def create_default_permissions(db: Session) -> dict:
    """Create default permissions if they don't exist"""
    created_permissions = {}
    
    for perm_data in DEFAULT_PERMISSIONS:
        existing_perm = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
        
        if not existing_perm:
            permission = Permission(
                code=perm_data["code"],
                name=perm_data["name"],
                description=perm_data.get("description", ""),
                module=perm_data["module"]
            )
            db.add(permission)
            db.flush()
            created_permissions[permission.code] = permission
            logger.info(f"Created permission: {permission.code}")
        else:
            created_permissions[existing_perm.code] = existing_perm
            logger.info(f"Permission already exists: {existing_perm.code}")
    
    db.commit()
    return created_permissions


def assign_permissions_to_roles(db: Session, roles: dict, permissions: dict):
    """Assign permissions to roles based on mapping"""
    for role_name, permission_codes in ROLE_PERMISSION_MAPPING.items():
        role = roles.get(role_name)
        if not role:
            logger.warning(f"Role not found: {role_name}")
            continue
        
        # Get current permissions for this role
        current_perms = {p.code for p in role.permissions}
        
        # Add missing permissions
        for perm_code in permission_codes:
            if perm_code not in current_perms:
                permission = permissions.get(perm_code)
                if permission:
                    role.permissions.append(permission)
                    logger.info(f"Assigned permission {perm_code} to role {role_name}")
    
    db.commit()


def create_initial_superuser(db: Session, roles: dict) -> User:
    """Create initial superuser from environment variables"""
    # Get superuser credentials from environment
    email = os.getenv("INITIAL_SUPERUSER_EMAIL", "admin@jerp.local")
    password = os.getenv("INITIAL_SUPERUSER_PASSWORD", "admin123")
    full_name = os.getenv("INITIAL_SUPERUSER_NAME", "System Administrator")
    
    # Check if superuser already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        logger.info(f"Superuser already exists: {email}")
        return existing_user
    
    # Get superadmin role
    superadmin_role = roles.get("Superadmin")
    
    # Create superuser
    hashed_password = get_password_hash(password)
    superuser = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        is_superuser=True,
        role_id=superadmin_role.id if superadmin_role else None
    )
    
    db.add(superuser)
    db.commit()
    db.refresh(superuser)
    
    logger.info(f"Created initial superuser: {email}")
    return superuser


def create_initialization_audit_log(db: Session, superuser: User):
    """Create audit log entry for database initialization"""
    # Get the last audit log hash
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last_log.current_hash if last_log else None
    
    # Create audit log entry
    audit_entry = AuditLog.create_entry(
        user_id=superuser.id,
        user_email=superuser.email,
        action="SYSTEM_INIT",
        resource_type="database",
        resource_id="initial",
        old_values=None,
        new_values={"initialized": True, "timestamp": datetime.utcnow().isoformat()},
        description="Database initialized with default roles, permissions, and superuser",
        ip_address="127.0.0.1",
        user_agent="JERP-Init-Script",
        previous_hash=previous_hash
    )
    
    db.add(audit_entry)
    db.commit()
    logger.info("Created initialization audit log entry")


async def init_db():
    """
    Initialize database with default data.
    This function is idempotent - can be run multiple times safely.
    """
    logger.info("Starting database initialization...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        
        # Create default roles
        logger.info("Creating default roles...")
        roles = create_default_roles(db)
        
        # Create default permissions
        logger.info("Creating default permissions...")
        permissions = create_default_permissions(db)
        
        # Assign permissions to roles
        logger.info("Assigning permissions to roles...")
        assign_permissions_to_roles(db, roles, permissions)
        
        # Create initial superuser
        logger.info("Creating initial superuser...")
        superuser = create_initial_superuser(db, roles)
        
        # Create initialization audit log
        logger.info("Creating initialization audit log...")
        create_initialization_audit_log(db, superuser)
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    """Run initialization when script is executed directly"""
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
