from typing import List, Optional, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status

from .user import get_current_user
from .api_key import get_current_user_from_api_key
from src.models.user import User

def require_scope(required_scopes: List[str] = None):
    """Dependency to check if the user has the required scopes
    
    Args:
        required_scopes: List of required scopes
        
    Returns:
        Dependency function
    """
    async def scope_dependency(current_user: User = Depends(get_current_user_from_api_key)) -> User:
        """Check if the user has the required scopes
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Current user if authorized
            
        Raises:
            HTTPException: If the user doesn't have the required scopes
        """
        # If no scopes required, just authenticate
        if not required_scopes:
            return current_user
            
        # Admin users have all scopes
        if current_user.is_admin:
            return current_user
            
        # Check for API key scopes (attached to the user)
        user_scopes = getattr(current_user, "scopes", [])
        if not user_scopes:
            # If no scopes are attached, check if the user has the default role
            # This is a simplified version - you might have a more complex role system
            user_scopes = ["read"]  # Default scope for authenticated users
            
        # Check if the user has all required scopes
        missing_scopes = [scope for scope in required_scopes if scope not in user_scopes]
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Missing scopes: {', '.join(missing_scopes)}",
            )
            
        return current_user
        
    return scope_dependency
