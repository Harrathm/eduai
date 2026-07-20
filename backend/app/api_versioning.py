"""API versioning and router utilities."""

from typing import Optional, Callable, Any
from fastapi import APIRouter, FastAPI
from functools import wraps


class APIVersionRouter:
    """Manage API versioned routers."""
    
    def __init__(self, prefix: str = "/api/v1", tags: list[str] = None):
        self.prefix = prefix
        self.tags = tags or []
        self.router = APIRouter(prefix=prefix, tags=tags)
        
        # Version info
        self.version = "1.0.0"
        self.api_name = "EDUAI Learning API"
    
    def add_router(
        self,
        router: APIRouter,
        *,
        prefix: str = "",
        tags: list[str] = None,
    ):
        """Add a sub-router with optional additional prefix."""
        full_prefix = self.prefix + prefix if prefix else self.prefix
        self.router.include_router(router, prefix=prefix)
    
    def get_router(self) -> APIRouter:
        """Get the configured router."""
        return self.router


def create_versioned_app(
    app: FastAPI,
    version: str = "v1",
    **router_kwargs
) -> FastAPI:
    """Create a versioned API application.
    
    Args:
        app: Base FastAPI app
        version: API version (v1, v2, etc.)
    
    Returns:
        Configured FastAPI app
    """
    # Add version to title if not present
    if version not in app.title:
        app.title = f"{app.title} ({version.upper()})"
    
    # Add version to OpenAPI
    app.openapi_version = version
    
    return app


# ---- DEPRECATION HANDLER ----
from fastapi import HTTPException, status


def deprecated(
    message: str = "This endpoint is deprecated",
   替代: Optional[str] = None,
):
    """Mark endpoint as deprecated.
    
    Args:
        message: Deprecation message
       替代: Alternative endpoint to use
    
    Raises:
        HTTPException: Always (endpoint should be removed)
    """
    detail = message
    if替代:
        detail += f" Use {替代} instead."
    
    # Note: In practice, you might just add a deprecation header
    # rather than raising an exception
    return {"deprecated": True, "message": message, "alternative":替代}


def add_deprecation_header(response,替代: Optional[str] = None):
    """Add deprecation header to response."""
    if替代:
        response.headers["Deprecation"] =替代
        response.headers["Link"] = f'<{替代}>; rel="successor-version"'


# ---- API RESPONSE FORMATTING ----
def api_response(
    data: Any = None,
    message: str = "Success",
    meta: dict = None,
    **kwargs
) -> dict:
    """Standard API response format.
    
    Args:
        data: Response data
        message: Status message
        meta: Additional metadata
    
    Returns:
        Standardized response dict
    """
    response = {
        "success": True,
        "message": message,
        "data": data,
    }
    
    if meta:
        response["meta"] = meta
    
    return response


def error_response(
    error: str,
    detail: str,
    code: str = None,
    **kwargs
) -> dict:
    """Standard error response format.
    
    Args:
        error: Error type
        detail: Error details
        code: Error code
    
    Returns:
        Standardized error dict
    """
    response = {
        "success": False,
        "error": error,
        "detail": detail,
    }
    
    if code:
        response["code"] = code
    
    return response