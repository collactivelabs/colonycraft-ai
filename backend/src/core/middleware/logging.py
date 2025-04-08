from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import logging
import time
import uuid

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with logging
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain
            
        Returns:
            The response from downstream handlers
        """
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state for logging
        request.state.request_id = request_id
        
        # Log the request
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"
        
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_host} [id:{request_id}]"
        )
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log the response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[id:{request_id}] {response.status_code} "
                f"completed in {process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            # Log exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[id:{request_id}] failed in {process_time:.3f}s: {str(e)}"
            )
            raise
