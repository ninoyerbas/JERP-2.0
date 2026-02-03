"""
JERP 2.0 - Database Initialization Service
Initialize database with default roles, permissions, and superuser
"""
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role, Permission
from app.core.security import get_password_hash
from datetime import datetime


class DatabaseInitService:
    """Initialize database with default roles, permissions, and superuser"""
    
    @staticmethod
    def create_default_roles(db: Session):
        """Create default roles"""
        roles = [
            {"name": "Super Administrator", "description": "Full system access"},
            {"name": "Administrator", "description": "Administrative access"},
            {"name": "Manager", "description": "Management access"},
            {"name": "Employee", "description": "Standard employee access"},
            {"name": "Guest", "description": "Read-only access"},
        ]
        
        for role_data in roles:
            exists = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not exists:
                role = Role(**role_data)
                db.add(role)
        
        db.commit()
    
    @staticmethod
    def create_default_permissions(db: Session):
        """Create default permissions"""
        modules = ["users", "roles", "audit", "compliance", "hr", "payroll", "finance"]
        actions = ["create", "read", "update", "delete"]
        
        for module in modules:
            for action in actions:
                code = f"{module}.{action}"
                exists = db.query(Permission).filter(Permission.code == code).first()
                if not exists:
                    permission = Permission(
                        code=code,
                        name=f"{action.title()} {module.title()}",
                        description=f"Permission to {action} {module}",
                        module=module
                    )
                    db.add(permission)
        
        db.commit()
    
    @staticmethod
    def create_superuser(db: Session, email: str, password: str, full_name: str):
        """Create initial superuser"""
        exists = db.query(User).filter(User.email == email).first()
        if exists:
            return exists
        
        # Get or create Super Administrator role
        super_role = db.query(Role).filter(Role.name == "Super Administrator").first()
        
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_superuser=True,
            role_id=super_role.id if super_role else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def initialize_database(db: Session):
        """Initialize entire database with defaults"""
        print("Creating default roles...")
        DatabaseInitService.create_default_roles(db)
        
        print("Creating default permissions...")
        DatabaseInitService.create_default_permissions(db)
        
        print("Creating default superuser...")
        DatabaseInitService.create_superuser(
            db=db,
            email="admin@jerp.local",
            password="Admin123!ChangeMe",
            full_name="System Administrator"
        )
        
        print("Database initialization complete!")
