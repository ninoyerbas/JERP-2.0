#!/usr/bin/env python3
"""
JERP 2.0 - Database Initialization Script
Run this script to initialize the database with default roles, permissions, and superuser
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.services.db_init_service import DatabaseInitService


def main():
    print("Initializing JERP 2.0 Database...")
    db = SessionLocal()
    try:
        DatabaseInitService.initialize_database(db)
        print("\nDefault Superuser Credentials:")
        print("  Email: admin@jerp.local")
        print("  Password: Admin123!ChangeMe")
        print("\nIMPORTANT: Change the password after first login!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
