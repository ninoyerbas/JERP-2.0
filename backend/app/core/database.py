"""
JERP 2.0 - Database Connection
SQLAlchemy engine and session management for MySQL
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create SQLAlchemy engine for MySQL
jerp_engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=settings.APP_DEBUG,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=jerp_engine)

# Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency that provides a database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables.
    Called on application startup.
    """
    from app.models import user, role, audit_log, compliance_violation  # noqa: F401
    Base.metadata.create_all(bind=jerp_engine)