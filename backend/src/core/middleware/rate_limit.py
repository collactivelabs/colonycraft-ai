from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI, status
from datetime import datetime
import logging
import time

from src.core.config import settings
from src.core.security import TokenBucket
from src.core.metrics import (
    rate_limit_exceeded_total,
    rate_limit_remaining_tokens,
    rate_limit_reset_seconds
)

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""
    
    def __init__(self, app: FastAPI):
        """Initialize the middleware
        
        Args:
            app: FastAPI application
        """
        super().__init__(app)
        # Create a token bucket with configurable rate limits
        # Use a time_function parameter for better testability
        self.token_bucket = TokenBucket(
            capacity=settings.RATE_LIMIT_MAX_REQUESTS,
            refill_rate=settings.RATE_LIMIT_MAX_REQUESTS / settings.RATE_LIMIT_WINDOW,
            time_function=datetime.now
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with rate limiting
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain
            
        Returns:
            The response or a 429 response if rate limited
        """
        # Get client identifier (e.g., IP address)
        client_id = self._get_client_id(request)
        
        # Check if the client has tokens available
        if not self.token_bucket.take(client_id):
            # Track rate limit exceeded metrics
            endpoint = request.url.path
            rate_limit_exceeded_total.labels(client_id=client_id, endpoint=endpoint).inc()
            
            # Set reset time metric
            reset_time = self.token_bucket.get_next_refill_time(client_id)
            rate_limit_reset_seconds.labels(client_id=client_id).set(reset_time - time.time())
            
            # Log rate limit exceeded
            logger.warning(f"Rate limit exceeded for client {client_id} on endpoint {endpoint}")
            
            # If no tokens available, return 429 Too Many Requests
            return Response(
                content="Rate limit exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": str(settings.RATE_LIMIT_WINDOW),
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_MAX_REQUESTS),
                    "X-RateLimit-Reset": str(int(reset_time))
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to the response
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_MAX_REQUESTS)
        
        # Track remaining tokens metric
        remaining = self.token_bucket.get_tokens(client_id)
        rate_limit_remaining_tokens.labels(client_id=client_id).set(remaining)
        response.headers["X-RateLimit-Remaining"] = str(int(self.token_bucket.get_tokens(client_id)))
        response.headers["X-RateLimit-Reset"] = str(int(self.token_bucket.get_next_refill_time(client_id)))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get a unique identifier for the client
        
        Args:
            request: The incoming request
            
        Returns:
            A string identifier for the client
        """
        # Use the client IP as the identifier, or API key if available
        client_id = request.client.host
        
        # If there's an API key, use that instead for more accurate rate limiting
        api_key = request.headers.get("X-API-Key")
        if api_key:
            try:
                # Extract just the prefix for rate limiting
                prefix = api_key.split(".", 1)[0]
                client_id = f"{client_id}:{prefix}"
            except (IndexError, ValueError):
                # If API key is malformed, fall back to IP-based limiting
                pass
                
        return client_id
