from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication"""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and add API key authentication
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain
            
        Returns:
            The response from downstream handlers
        """
        # API key authentication is handled by dependencies in the routes
        # This middleware mainly exists for logging and metrics
        response = await call_next(request)
        return response
