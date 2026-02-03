"""
Application Startup Tasks

Run database initialization and other startup tasks
"""
import logging
from app.core.database import Base, jerp_engine
from app.scripts.init_db import init_db as seed_initial_data

logger = logging.getLogger(__name__)


async def startup_event():
    """
    Run startup tasks when the application starts.
    
    Tasks:
    1. Ensure database tables exist
    2. Seed initial data (roles, permissions, superuser)
    """
    try:
        logger.info("Starting application startup tasks...")
        
        # Create all tables (if they don't exist)
        # This is a fallback - migrations should be run first
        logger.info("Ensuring database tables exist...")
        Base.metadata.create_all(bind=jerp_engine)
        
        # Seed initial data
        logger.info("Seeding initial data...")
        await seed_initial_data()
        
        logger.info("Application startup tasks completed successfully!")
        
    except Exception as e:
        logger.error(f"Startup tasks failed: {str(e)}")
        # Don't raise - allow app to start even if seeding fails
        # Admin can run init manually
