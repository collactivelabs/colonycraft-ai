from fastapi import Security, HTTPException, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_429_TOO_MANY_REQUESTS, HTTP_500_INTERNAL_SERVER_ERROR
from google.cloud import secretmanager_v1
from google.api_core import exceptions as google_exceptions
from .database import get_db_context
from .config import get_settings
from .security import TokenBucket
from typing import Optional, List, Final, Dict
import os
import logging
import json
import time
import uuid
from datetime import datetime, timedelta
from ..models.credentials import CredentialManager

# Constants
LOGGER_NAME: Final[str] = "saas-api"
LOG_FORMAT: Final[str] = '%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s'
LOG_FILE: Final[str] = 'combined.log'
CACHE_DURATION: Final[timedelta] = timedelta(minutes=30)
RATE_LIMIT_WINDOW: Final[int] = 60  # 60 seconds window
RATE_LIMIT_MAX_REQUESTS: Final[int] = 100  # Max requests per window
EXEMPT_PATHS: Final[List[str]] = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/health",
    "/metrics"
]

# Configure logger with correlation ID filter
class CorrelationIDFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.correlation_id = None

    def filter(self, record):
        record.correlation_id = getattr(record, 'correlation_id', self.correlation_id or 'no-correlation-id')
        return True

logger = logging.getLogger(LOGGER_NAME)
correlation_filter = CorrelationIDFilter()
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(correlation_filter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def validate_environment() -> None:
    # Skip validation in test environment
    if os.getenv("ENVIRONMENT") == "test":
        return
        
    required_vars = ["GOOGLE_CLOUD_PROJECT", "SECRET_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

class APIKeyValidator:
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            self.secret_name = os.getenv("SECRET_NAME", "api-key")
            self._api_key: Optional[str] = None
            self._last_fetched: Optional[datetime] = None

            try:
                # Use CredentialsManager to get credentials
                credentials = CredentialsManager().credentials
                self.client = secretmanager_v1.SecretManagerServiceClient(
                    credentials=credentials
                )
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {str(e)}")
                raise RuntimeError(f"Failed to initialize Secret Manager client: {str(e)}")

            self.initialized = True

class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.validator = APIKeyValidator()

    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            logger.warning(f"Missing API key for request to {request.url.path}")
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="API Key is missing",
                headers={"WWW-Authenticate": "ApiKey"},
            )

        try:
            valid_api_key = await self.validator.get_api_key()
            if api_key != valid_api_key:
                logger.warning(f"Invalid API key attempt for {request.url.path}")
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="Invalid API Key"
                )
            return await call_next(request)
        except RuntimeError as e:
            logger.error(f"API key validation error: {str(e)}")
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Validate content type for POST/PUT/PATCH requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if not content_type.startswith(("application/json", "multipart/form-data")):
                    return HTTPException(
                        status_code=415,
                        detail="Unsupported media type. Use 'application/json' or 'multipart/form-data'"
                    )

            # Validate request size
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                return HTTPException(
                    status_code=413,
                    detail="Request too large. Maximum size is 10MB"
                )

            response = await call_next(request)
            return response
        except ValueError as e:
            logger.error(f"Request validation error: {str(e)}")
            return HTTPException(
                status_code=400,
                detail=f"Invalid request format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in request validation: {str(e)}")
            return HTTPException(
                status_code=500,
                detail="Internal server error during request validation"
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_filter.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "request": {
                    "method": request.method,
                    "url": str(request.url),
                    "client_host": request.client.host,
                    "headers": dict(request.headers),
                }
            }
        )

        try:
            # Add correlation ID to response headers
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": correlation_id,
                    "response": {
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "headers": dict(response.headers),
                    }
                }
            )

            return response

        except Exception as e:
            # Log error
            logger.error(
                "Request failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                    }
                }
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rate_limit_max_requests: int = None, rate_limit_window: int = None):
        super().__init__(app)
        
        # Get settings from environment or use defaults
        settings_obj = get_settings()
        self.rate_limit_max_requests = rate_limit_max_requests or getattr(settings_obj, 'RATE_LIMIT_MAX_REQUESTS', RATE_LIMIT_MAX_REQUESTS)
        self.rate_limit_window = rate_limit_window or getattr(settings_obj, 'RATE_LIMIT_WINDOW', RATE_LIMIT_WINDOW)
        
        # Store token buckets for each client
        self.buckets: Dict[str, TokenBucket] = {}
        
        # Calculate fill rate (tokens per second)
        self.fill_rate = self.rate_limit_max_requests / self.rate_limit_window

    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Get client identifier (IP address or API key)
        client_id = request.headers.get("X-API-Key") or request.client.host

        # Get or create token bucket for this client
        if client_id not in self.buckets:
            self.buckets[client_id] = TokenBucket(
                tokens=self.rate_limit_max_requests,
                fill_rate=self.fill_rate,
                # Using the default time function (datetime.now with UTC timezone)
                time_function=None
            )
            
        bucket = self.buckets[client_id]
        
        # Check if rate limit exceeded
        if not bucket.consume(1):  # Try to consume 1 token
            # Calculate time until next token available
            retry_after = int(max(1, bucket.time_until_tokens(1)))
            reset_time = datetime.utcnow() + timedelta(seconds=retry_after)
            
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            
            # Create rate limit exceeded error for structured response
            from ..core.exceptions import RateLimitExceededError
            rate_limit_error = RateLimitExceededError(
                limit=self.rate_limit_max_requests,
                window=self.rate_limit_window,
                reset_at=reset_time
            )
            
            # Format the error response
            from ..core.exceptions import format_error_response
            error_response = format_error_response(rate_limit_error)
            
            # Return rate limit exceeded response
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content=error_response,
                headers={
                    "Retry-After": str(retry_after)
                }
            )
        
        # Calculate rate limit headers
        remaining_tokens = int(bucket.get_tokens())
        time_to_full = bucket.time_until_tokens(self.rate_limit_max_requests)
        reset_time = int((datetime.utcnow() + timedelta(seconds=time_to_full)).timestamp())
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limit_max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining_tokens)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response

class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            with get_db_context() as db:
                request.state.db = db
                response = await call_next(request)
                return response
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection error"
            )