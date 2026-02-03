"""
JERP 2.0 - API Router v1
Aggregates all endpoint routers for API version 1
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, roles, audit

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & Permissions"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
