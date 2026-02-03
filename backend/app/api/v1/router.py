"""
JERP 2.0 - API v1 Router
Main router that includes all API endpoints
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, roles, audit, compliance, hr, payroll

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & Permissions"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(hr.router, prefix="/hr", tags=["HR/HRIS"])
api_router.include_router(payroll.router, prefix="/payroll", tags=["Payroll"])

@api_router.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "JERP 2.0 API v1",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/auth",
            "users": "/users",
            "roles": "/roles",
            "audit": "/audit",
            "compliance": "/compliance",
            "hr": "/hr",
            "payroll": "/payroll"
        }
    }
