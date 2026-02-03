#!/usr/bin/env python3
"""
JERP 2.0 - Management CLI

Command-line interface for database management and administrative tasks.

Usage:
    python manage.py db:init          - Initialize database with default data
    python manage.py db:migrate       - Create a new migration
    python manage.py db:upgrade       - Upgrade to latest migration
    python manage.py db:downgrade     - Downgrade one migration
    python manage.py db:reset         - Reset database (development only)
    python manage.py user:create-superuser - Interactive superuser creation
"""
import os
import sys
import click
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import SessionLocal, Base, jerp_engine
from app.core.security import get_password_hash
from app.models.user import User
from app.models.role import Role


@click.group()
def cli():
    """JERP 2.0 Management CLI"""
    pass


@cli.group()
def db():
    """Database management commands"""
    pass


@cli.group()
def user():
    """User management commands"""
    pass


@db.command("init")
def db_init():
    """Initialize database with default data"""
    click.echo("Initializing database...")
    
    try:
        from app.scripts.init_db import init_db
        asyncio.run(init_db())
        click.echo(click.style("✓ Database initialized successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Database initialization failed: {str(e)}", fg="red"))
        sys.exit(1)


@db.command("migrate")
@click.option("--message", "-m", required=True, help="Migration message")
def db_migrate(message):
    """Create a new migration"""
    click.echo(f"Creating migration: {message}")
    
    try:
        os.system(f'cd backend && alembic revision --autogenerate -m "{message}"')
        click.echo(click.style("✓ Migration created successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Migration creation failed: {str(e)}", fg="red"))
        sys.exit(1)


@db.command("upgrade")
@click.option("--revision", "-r", default="head", help="Target revision (default: head)")
def db_upgrade(revision):
    """Upgrade database to a later version"""
    click.echo(f"Upgrading database to {revision}...")
    
    try:
        os.system(f"cd backend && alembic upgrade {revision}")
        click.echo(click.style("✓ Database upgraded successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Database upgrade failed: {str(e)}", fg="red"))
        sys.exit(1)


@db.command("downgrade")
@click.option("--revision", "-r", default="-1", help="Target revision (default: -1)")
def db_downgrade(revision):
    """Downgrade database to a previous version"""
    click.echo(f"Downgrading database to {revision}...")
    
    if settings.APP_ENV == "production":
        click.confirm("You are in production mode. Are you sure you want to downgrade?", abort=True)
    
    try:
        os.system(f"cd backend && alembic downgrade {revision}")
        click.echo(click.style("✓ Database downgraded successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Database downgrade failed: {str(e)}", fg="red"))
        sys.exit(1)


@db.command("reset")
def db_reset():
    """Reset database (drop all tables and recreate) - DEVELOPMENT ONLY"""
    if settings.APP_ENV == "production":
        click.echo(click.style("✗ Cannot reset database in production mode!", fg="red"))
        sys.exit(1)
    
    click.echo(click.style("⚠ WARNING: This will delete ALL data in the database!", fg="yellow", bold=True))
    click.confirm("Are you sure you want to continue?", abort=True)
    
    try:
        # Drop all tables
        click.echo("Dropping all tables...")
        Base.metadata.drop_all(bind=jerp_engine)
        
        # Recreate tables
        click.echo("Creating tables...")
        Base.metadata.create_all(bind=jerp_engine)
        
        # Initialize with default data
        click.echo("Initializing with default data...")
        from app.scripts.init_db import init_db
        asyncio.run(init_db())
        
        click.echo(click.style("✓ Database reset successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Database reset failed: {str(e)}", fg="red"))
        sys.exit(1)


@user.command("create-superuser")
def create_superuser():
    """Create a superuser interactively"""
    click.echo("Create Superuser")
    click.echo("=" * 50)
    
    # Get user input
    email = click.prompt("Email", type=str)
    full_name = click.prompt("Full Name", type=str)
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    
    try:
        db = SessionLocal()
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            click.echo(click.style(f"✗ User with email {email} already exists!", fg="red"))
            sys.exit(1)
        
        # Get Superadmin role
        superadmin_role = db.query(Role).filter(Role.name == "Superadmin").first()
        
        # Create user
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            is_superuser=True,
            role_id=superadmin_role.id if superadmin_role else None
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        click.echo(click.style(f"✓ Superuser created successfully!", fg="green"))
        click.echo(f"  Email: {user.email}")
        click.echo(f"  Name: {user.full_name}")
        click.echo(f"  ID: {user.id}")
        
    except Exception as e:
        click.echo(click.style(f"✗ Superuser creation failed: {str(e)}", fg="red"))
        sys.exit(1)
    finally:
        db.close()


@db.command("status")
def db_status():
    """Show current database migration status"""
    click.echo("Database Migration Status:")
    click.echo("=" * 50)
    
    try:
        os.system("cd backend && alembic current")
        click.echo("\nMigration History:")
        os.system("cd backend && alembic history --verbose")
    except Exception as e:
        click.echo(click.style(f"✗ Failed to get status: {str(e)}", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    cli()
