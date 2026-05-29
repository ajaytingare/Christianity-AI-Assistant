"""
Enhanced exception handling and middleware for FastAPI.
"""

import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Callable
import time
import json

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception in {request.method} {request.url.path}",
        exc_info=exc,
        extra={"request_id": request_id}
    )
    
    # Don't expose internal details in production
    detail = "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": detail,
            "request_id": request_id,
            "type": type(exc).__name__
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"Validation error in {request.method} {request.url.path}",
        extra={"request_id": request_id, "errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": [
                {
                    "field": ".".join(str(x) for x in err["loc"][1:]),
                    "message": err["msg"]
                }
                for err in exc.errors()
            ],
            "request_id": request_id
        }
    )


async def request_middleware(request: Request, call_next: Callable):
    """Middleware to add request tracking and error handling."""
    from app.utils.helpers import IDGenerator
    
    # Generate request ID
    request_id = IDGenerator.generate_request_id()
    request.state.request_id = request_id
    
    # Record start time
    start_time = time.time()
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {e}", exc_info=e)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "request_id": request_id}
        )
    
    # Add request tracking headers
    elapsed_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "status": response.status_code,
            "duration_ms": elapsed_ms
        }
    )
    
    return response


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that safely handles various types and masks secrets."""
    
    def default(self, obj):
        # Handle common types
        if hasattr(obj, "__dict__"):
            return {k: self._mask_sensitive(k, v) for k, v in obj.__dict__.items()}
        return str(obj)
    
    @staticmethod
    def _mask_sensitive(key: str, value: str) -> str:
        """Mask sensitive values."""
        sensitive_keys = ["api_key", "secret", "password", "token", "key"]
        if any(s in key.lower() for s in sensitive_keys) and isinstance(value, str):
            return f"***{value[-4:]}" if len(value) > 4 else "***"
        return value
