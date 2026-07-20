"""Standardized error responses for the API."""

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Single error detail."""
    field: Optional[str] = None
    message: str


class APIErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    detail: str
    code: Optional[str] = None
    field: Optional[str] = None
    request_id: Optional[str] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "validation_error",
            "detail": "Email format is invalid",
            "code": "INVALID_EMAIL",
            "field": "email",
            "request_id": "req_abc123"
        }
    })


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error: str = "validation_error"
    detail: str
    fields: list[ErrorDetail] = []
    request_id: Optional[str] = None


class NotFoundErrorResponse(BaseModel):
    """404 error response."""
    error: str = "not_found"
    detail: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None


class UnauthorizedErrorResponse(BaseModel):
    """401 error response."""
    error: str = "unauthorized"
    detail: str


class ForbiddenErrorResponse(BaseModel):
    """403 error response."""
    error: str = "forbidden"
    detail: str


class ConflictErrorResponse(BaseModel):
    """409 error response."""
    error: str = "conflict"
    detail: str


class RateLimitErrorResponse(BaseModel):
    """429 error response."""
    error: str = "rate_limit_exceeded"
    detail: str
    retry_after: Optional[int] = None


# ---- ERROR CODES ----
class ErrorCode:
    """Standard error codes."""
    # Authentication
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    # Authorization
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    MISSING_FIELD = "MISSING_FIELD"
    
    # Resource
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Internal
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"