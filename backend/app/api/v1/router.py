"""
JERP 2.0 - API Router
Main router for all API endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import compliance

api_router = APIRouter()

# Include compliance endpoints
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
