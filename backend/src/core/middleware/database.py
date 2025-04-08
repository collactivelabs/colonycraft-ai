from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI
import logging
from sqlalchemy.orm import Session

from src.core.database import SessionLocal

logger = logging.getLogger(__name__)

class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """Middleware to provide a database session for each request"""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with a database session
        
        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain
            
        Returns:
            The response from downstream handlers
        """
        db = SessionLocal()
        try:
            # Add db session to request state
            request.state.db = db
            response = await call_next(request)
            return response
        finally:
            # Close the session
            db.close()
