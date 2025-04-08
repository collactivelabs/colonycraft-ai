from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from typing import Callable
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)

class APIKeyWarningMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds warning headers when a user is using a rotated API key
    during its grace period. This encourages users to adopt the new key before
    the old one expires completely.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process the request and get the response
        response = await call_next(request)
        
        # Check if the request used a rotated API key
        if hasattr(request.state, "api_key_rotated") and request.state.api_key_rotated:
            # Add warning headers to notify the user
            expiry_date = request.state.api_key_expiry
            if expiry_date:
                days_left = (expiry_date - datetime.now(UTC)).days
                expiry_str = expiry_date.isoformat()
                
                # Add RFC 7234 compliant warning header
                warning_code = "299"  # Miscellaneous warning
                warning_text = f"API key is deprecated and will expire on {expiry_str}"
                if days_left <= 1:
                    warning_text = f"URGENT: API key expires in less than 24 hours on {expiry_str}"
                elif days_left <= 3:
                    warning_text = f"CRITICAL: API key expires in {days_left} days on {expiry_str}"
                
                response.headers["Warning"] = f'{warning_code} saas-api "{warning_text}"'
                
                # Add custom header with more details
                response.headers["X-API-Key-Expiry"] = expiry_str
                
                # Add recommended header with the prefix of the new key if available
                if hasattr(request.state, "new_key_prefix"):
                    new_key_prefix = request.state.new_key_prefix
                    response.headers["X-API-Key-Replacement-Prefix"] = new_key_prefix
                    
                    # Add header with link to documentation
                    docs_url = "/docs#section/Authentication/API-Key-Rotation"
                    response.headers["Link"] = f'<{docs_url}>; rel="help"; title="API Key Rotation Guide"'
                    
                logger.info(f"Added API key rotation warning headers for request {request.url.path}")
        
        return response
