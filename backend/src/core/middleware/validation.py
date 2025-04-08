from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI, status
import logging

logger = logging.getLogger(__name__)

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for basic request validation"""

    async def dispatch(self, request: Request, call_next):
        """Process the request with validation

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            The response from downstream handlers
        """
        # Validate content-type header for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "").lower()
            if request.url.path.startswith("/api") and "application/json" not in content_type:
                # For API endpoints, require JSON content-type
                if not (
                    "multipart/form-data" in content_type
                    or "application/x-www-form-urlencoded" in content_type
                ):
                    return Response(
                        content='{"detail":"Content-Type must bee application/json"}',
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        media_type="application/json"
                    )

        # Process the request
        response = await call_next(request)

        return response
