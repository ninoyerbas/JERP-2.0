"""
JERP 2.0 - Main FastAPI Application
Enterprise Resource Planning System with Compliance Focus
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.startup import startup_event
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="JERP 2.0 - On-Premise Compliance ERP Suite",
    version="2.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def on_startup():
    """Run startup tasks"""
    await startup_event()

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint with database connectivity test.
    Returns application status and database health.
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app": settings.APP_NAME,
        "version": "2.0.0",
        "database": db_status,
        "environment": settings.APP_ENV
    }