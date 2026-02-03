"""
JERP 2.0 - API v1 Router
Main router for API v1 endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import compliance

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    compliance.router,
    prefix="/compliance",
    tags=["compliance"]
)
