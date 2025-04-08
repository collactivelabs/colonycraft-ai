import logging
import os
from src.core.config import settings

logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables are set
    
    Raises:
        ValueError: If required environment variables are missing
    """
    missing_vars = []
    
    # Define required environment variables based on environment
    if settings.ENVIRONMENT == "production":
        required_vars = [
            "SECRET_KEY",
            "ALLOWED_HOSTS",
            "ALLOWED_ORIGINS"
        ]
        
        # Database vars - required if DATABASE_URL not provided
        if not settings.DATABASE_URL:
            required_vars.extend([
                "POSTGRES_SERVER",
                "POSTGRES_USER",
                "POSTGRES_PASSWORD",
                "POSTGRES_DB"
            ])
            
        # Check for required vars
        for var in required_vars:
            value = getattr(settings, var, None)
            if not value:
                missing_vars.append(var)
    
    # Raise error if missing required vars
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
