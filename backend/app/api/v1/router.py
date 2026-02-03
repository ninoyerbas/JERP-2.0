"""API v1 Router"""
from fastapi import APIRouter

api_router = APIRouter()

@api_router.get("/")
async def root():
    """API root endpoint"""
    return {"message": "JERP 2.0 API v1"}
