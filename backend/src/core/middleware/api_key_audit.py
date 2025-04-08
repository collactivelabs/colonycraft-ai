from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import time
import logging
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.api_key_usage import APIKeyUsage
from src.crud.api_key import get_api_key_by_prefix

logger = logging.getLogger(__name__)

class APIKeyAuditMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking API key usage and creating an audit trail"""
    
    def __init__(self, app: FastAPI):
        """Initialize the middleware
        
        Args:
            app: FastAPI application
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and track API key usage
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain
            
        Returns:
            The response
        """
        # Track response time
        start_time = time.time()
        
        # Extract API key if present
        api_key = request.headers.get("X-API-Key", None)
        api_key_id = None
        
        if api_key:
            try:
                # Extract the prefix from the API key
                prefix = api_key.split(".")[0]
                
                # Get a database session
                db = next(get_db())
                
                # Find the API key in the database
                db_api_key = get_api_key_by_prefix(db, prefix)
                if db_api_key:
                    api_key_id = db_api_key.id
            except Exception as e:
                logger.error(f"Error identifying API key: {str(e)}")
        
        # Process the request
        response = await call_next(request)
        
        # Calculate response time
        response_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
        
        # Only log if we have an API key
        if api_key_id:
            try:
                # Create audit record
                audit_record = APIKeyUsage(
                    api_key_id=api_key_id,
                    endpoint=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent"),
                    response_time_ms=response_time
                )
                
                # Get a database session
                db = next(get_db())
                
                # Save the audit record
                db.add(audit_record)
                db.commit()
            except Exception as e:
                logger.error(f"Error logging API key usage: {str(e)}")
        
        return response
