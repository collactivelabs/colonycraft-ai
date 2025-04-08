import contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi import FastAPI

# Context variable to store the current request
request_var = contextvars.ContextVar("request", default=None)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to store the current request in context for access from anywhere"""
    
    async def dispatch(self, request: Request, call_next):
        """Store request in context variable"""
        # Set the request in the context variable
        token = request_var.set(request)
        try:
            # Process the request
            response = await call_next(request)
            return response
        finally:
            # Clean up the context variable
            request_var.reset(token)

def get_current_request() -> Request:
    """Get the current request from context"""
    request = request_var.get()
    if request is None:
        raise RuntimeError("No request found in context")
    return request
