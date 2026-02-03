"""
JERP 2.0 - Custom Exceptions
Custom exception classes and handlers for consistent error responses
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class NotFoundException(HTTPException):
    """Exception for 404 Not Found errors"""
    def __init__(self, detail: str = "Resource not found", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)


class BadRequestException(HTTPException):
    """Exception for 400 Bad Request errors"""
    def __init__(self, detail: str = "Bad request", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)


class UnauthorizedException(HTTPException):
    """Exception for 401 Unauthorized errors"""
    def __init__(self, detail: str = "Unauthorized", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers=headers)


class ForbiddenException(HTTPException):
    """Exception for 403 Forbidden errors"""
    def __init__(self, detail: str = "Forbidden", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)


class ConflictException(HTTPException):
    """Exception for 409 Conflict errors"""
    def __init__(self, detail: str = "Conflict", headers: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail, headers=headers)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Global exception handler for HTTPException instances.
    Returns a consistent error response format.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.
    Returns a consistent 500 error response.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {}
            }
        }
    )
