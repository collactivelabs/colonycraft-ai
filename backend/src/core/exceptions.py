from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Dict, Any, Optional
import logging
import traceback
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAPIException(Exception):
    """Base exception for all API errors"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(BaseAPIException):
    """Raised when request validation fails"""
    def __init__(self, message: str, details: Dict[str, Any]):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )

class AuthenticationError(BaseAPIException):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(BaseAPIException):
    """Raised when authorization fails"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )

class ResourceNotFoundError(BaseAPIException):
    """Raised when a requested resource is not found"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with id {resource_id} not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class RateLimitExceededError(BaseAPIException):
    """Raised when a client exceeds the rate limit"""
    def __init__(self, limit: int, window: int, reset_at: datetime):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests allowed per {window} seconds",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={
                "limit": limit,
                "window_seconds": window,
                "reset_at": reset_at.isoformat(),
                "retry_after": int((reset_at - datetime.utcnow()).total_seconds())
            }
        )

class DatabaseError(BaseAPIException):
    """Raised when a database operation fails"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        details = {
            "error_type": type(original_error).__name__ if original_error else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        super().__init__(
            message=message,
            status_code=500,
            error_code="DATABASE_ERROR",
            details=details
        )

class ProcessingError(BaseAPIException):
    """Raised when processing of media (image/video) fails"""
    def __init__(self, message: str, task_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if task_id:
            error_details["task_id"] = task_id
        
        super().__init__(
            message=message,
            status_code=500,
            error_code="PROCESSING_ERROR",
            details=error_details
        )

class QuotaExceededError(BaseAPIException):
    """Raised when a user exceeds their quota"""
    def __init__(self, quota_type: str, limit: int, usage: int, user_id: Optional[str] = None):
        super().__init__(
            message=f"Quota exceeded for {quota_type}",
            status_code=402,  # Payment Required
            error_code="QUOTA_EXCEEDED",
            details={
                "quota_type": quota_type,
                "limit": limit,
                "current_usage": usage,
                "user_id": user_id
            }
        )

class InvalidInputError(BaseAPIException):
    """Raised when input validation fails but in a way that's specific to business rules"""
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
            
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_INPUT",
            details=error_details
        )

class ServiceUnavailableError(BaseAPIException):
    """Raised when an external service is unavailable"""
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Service {service_name} is currently unavailable",
            status_code=503,  # Service Unavailable
            error_code="SERVICE_UNAVAILABLE",
            details=details or {"service_name": service_name}
        )

class LLMIntegrationError(BaseAPIException):
    """Raised when there is an error interacting with an LLM API"""
    def __init__(self, provider: str, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        error_details["provider"] = provider
        
        super().__init__(
            message=f"Error interacting with {provider}: {message}",
            status_code=status_code,
            error_code="LLM_INTEGRATION_ERROR",
            details=error_details
        )

def format_error_response(exc: BaseAPIException) -> Dict[str, Any]:
    """Format error response in a consistent structure"""
    response = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    if exc.details:
        response["error"]["details"] = exc.details
    return response

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(BaseAPIException)
    async def api_exception_handler(request: Request, exc: BaseAPIException):
        log_error(request, exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        api_exc = BaseAPIException(
            message=exc.detail,
            status_code=exc.status_code,
            error_code=f"HTTP_{exc.status_code}"
        )
        log_error(request, api_exc)
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(api_exc)
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        api_exc = BaseAPIException(
            message="Database integrity error",
            status_code=409,
            error_code="INTEGRITY_ERROR",
            details={"constraint": str(exc.orig)}
        )
        log_error(request, api_exc)
        return JSONResponse(
            status_code=409,
            content=format_error_response(api_exc)
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        api_exc = DatabaseError(
            message="Database error occurred",
            original_error=exc
        )
        log_error(request, api_exc)
        return JSONResponse(
            status_code=500,
            content=format_error_response(api_exc)
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        api_exc = BaseAPIException(
            message="Internal server error",
            status_code=500,
            error_code="INTERNAL_ERROR",
            details={"error_type": type(exc).__name__}
        )
        log_error(request, exc, include_traceback=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(api_exc)
        )

def log_error(
    request: Request,
    exc: Exception,
    include_traceback: bool = False
) -> None:
    """Log error with request context"""
    error_data = {
        "url": str(request.url),
        "method": request.method,
        "client_host": request.client.host,
        "headers": dict(request.headers),
        "error_type": type(exc).__name__,
        "error_message": str(exc)
    }
    
    if include_traceback:
        error_data["traceback"] = traceback.format_exc()
    
    if isinstance(exc, BaseAPIException):
        error_data["error_code"] = exc.error_code
        error_data["details"] = exc.details
    
    logger.error(
        f"Request failed: {exc}",
        extra={
            "error_context": error_data
        }
    )