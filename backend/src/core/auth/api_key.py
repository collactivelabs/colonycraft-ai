import hashlib
import hmac
import secrets
import logging
from datetime import datetime, timedelta, UTC
from typing import Tuple, Optional, Dict, Any, List, Union
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Header, Request
from pydantic import UUID4

from src.core.database import get_db
from src.models.user import User as UserModel
from src.models.api_key import APIKey as APIKeyModel

logger = logging.getLogger(__name__)

class APIKey:
    """API Key class for authentication and key management"""
    def __init__(
        self,
        id: str,
        key_hash: str,
        prefix: str,
        name: str = None,
        user_id: str = None,
        scope: List[str] = None,
        created_at: datetime = None,
        expires_at: Optional[datetime] = None,
        is_active: bool = True,
        rotated_from_id: Optional[str] = None,
        rotation_date: Optional[datetime] = None,
        grace_period_days: Optional[int] = None,
        grace_period_end: Optional[datetime] = None,
        was_compromised: bool = False
    ):
        self.id = id
        self.key_hash = key_hash
        self.prefix = prefix
        self.name = name
        self.user_id = user_id
        self.scope = scope or []
        self.created_at = created_at or datetime.now(UTC)
        self.expires_at = expires_at
        self.is_active = is_active
        self.rotated_from_id = rotated_from_id
        self.rotation_date = rotation_date
        self.grace_period_days = grace_period_days
        self.grace_period_end = grace_period_end
        self.was_compromised = was_compromised

    @classmethod
    def generate(
        cls,
        user_id: str,
        name: str,
        scopes: List[str] = None,
        expires_in_days: Optional[int] = None
    ) -> Tuple["APIKey", str]:
        """Generate a new API key

        Args:
            user_id: User ID
            name: Name of the API key
            scopes: List of scopes
            expires_in_days: Number of days until the key expires

        Returns:
            Tuple of (APIKey, key_value)
        """
        # Generate a random key with a prefix for identification
        prefix = secrets.token_hex(4)
        secret = secrets.token_urlsafe(32)
        key_value = f"{prefix}.{secret}"
        
        # Calculate a hash of the key for storage
        key_hash = hashlib.sha256(key_value.encode()).hexdigest()
        
        # Generate a unique ID for the key
        key_id = str(UUID4())
        
        # Calculate expiration date if provided
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        return cls(
            id=key_id,
            key_hash=key_hash,
            prefix=prefix,
            name=name,
            user_id=user_id,
            scope=scopes,
            expires_at=expires_at,
        ), key_value

    @classmethod
    def rotate(
        cls,
        old_key: "APIKey",
        new_name: str,
        new_scopes: List[str] = None,
        expires_in_days: Optional[int] = None,
        grace_period_days: int = 7,
        was_compromised: bool = False
    ) -> Tuple["APIKey", str]:
        """Rotate an API key by creating a new key and marking the old one as rotated

        Args:
            old_key: The existing API key to rotate
            new_name: Name for the new API key
            new_scopes: Scopes for the new API key
            expires_in_days: Number of days until the new key expires
            grace_period_days: Number of days the old key will continue to work
            was_compromised: Whether the key was rotated due to compromise

        Returns:
            Tuple of (new_api_key, key_value)
        """
        # Generate a new API key
        new_key, key_value = cls.generate(
            user_id=old_key.user_id,
            name=new_name,
            scopes=new_scopes or old_key.scope,
            expires_in_days=expires_in_days
        )
        
        # Set rotation properties on the new key
        now = datetime.now(UTC)
        new_key.rotated_from_id = old_key.id
        new_key.rotation_date = now
        
        # Update the old key based on whether it was compromised
        if was_compromised:
            # If key was compromised, mark it as inactive immediately
            old_key.is_active = False
            old_key.was_compromised = True
        else:
            # Otherwise set a grace period for the old key
            old_key.grace_period_days = grace_period_days
            old_key.grace_period_end = now + timedelta(days=grace_period_days)
            # The old key remains active during grace period
        
        return new_key, key_value

    @staticmethod
    def verify(key_value: str, key_hash: str) -> bool:
        """Verify if a key value matches the stored hash

        Args:
            key_value: The API key to verify
            key_hash: The stored hash to compare against

        Returns:
            True if the key is valid, False otherwise
        """
        calculated_hash = hashlib.sha256(key_value.encode()).hexdigest()
        return hmac.compare_digest(calculated_hash, key_hash)

    @staticmethod
    def parse_key(key_value: str) -> Tuple[str, str]:
        """Parse a key value into prefix and secret

        Args:
            key_value: API key in format "prefix.secret"

        Returns:
            Tuple of (prefix, secret)
        """
        try:
            prefix, secret = key_value.split(".", 1)
            return prefix, secret
        except ValueError:
            raise ValueError("Invalid API key format")

    def is_expired(self) -> bool:
        """Check if the API key is expired

        Returns:
            True if the key is expired, False otherwise
        """
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at

    def is_in_grace_period(self) -> bool:
        """Check if the API key is in its grace period after rotation

        Returns:
            True if the key is in grace period, False otherwise
        """
        if not self.grace_period_end:
            return False
        now = datetime.now(UTC)
        return now <= self.grace_period_end

    def is_valid(self) -> bool:
        """Check if the API key is valid for use

        Returns:
            True if the key is valid, False otherwise
        """
        return (self.is_active and 
                not self.is_expired() and 
                (not self.was_compromised))


def generate_api_key(
    user_id: str,
    name: str,
    scopes: List[str] = None,
    expires_in_days: Optional[int] = None
) -> Tuple[APIKeyModel, str]:
    """Generate a new API key and save it to the database

    Args:
        user_id: User ID
        name: Name of the API key
        scopes: List of scopes
        expires_in_days: Number of days until the key expires

    Returns:
        Tuple of (APIKeyModel, key_value)
    """
    api_key, key_value = APIKey.generate(
        user_id=user_id,
        name=name,
        scopes=scopes,
        expires_in_days=expires_in_days
    )
    
    # Create the database model
    db_api_key = APIKeyModel(
        id=api_key.id,
        prefix=api_key.prefix,
        key_hash=api_key.key_hash,
        name=api_key.name,
        user_id=api_key.user_id,
        scopes=api_key.scope,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
        is_active=api_key.is_active
    )
    
    return db_api_key, key_value


async def get_current_user_from_api_key(
    api_key: str = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> UserModel:
    """Get the current user from the API key

    Args:
        api_key: API key header
        db: Database session

    Returns:
        User model
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    
    try:
        # Parse the API key to get the prefix
        prefix, _ = APIKey.parse_key(api_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )
    
    # Look up the API key by prefix
    db_api_key = db.query(APIKeyModel).filter(
        APIKeyModel.prefix == prefix
    ).first()
    
    if not db_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Verify the API key
    if not APIKey.verify(api_key, db_api_key.key_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    # Check if the key is active
    if not db_api_key.is_active:
        # Check if this key is in grace period after rotation
        if db_api_key.grace_period_end and datetime.now(UTC) <= db_api_key.grace_period_end:
            # Allow usage during grace period
            logger.warning(f"API key {db_api_key.id} is in rotation grace period")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key is inactive",
            )
    
    # Check if the key is expired
    if db_api_key.expires_at and datetime.now(UTC) > db_api_key.expires_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is expired",
        )
    
    # Get the user associated with the API key
    user = db.query(UserModel).filter(UserModel.id == db_api_key.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
        
    # Check if the current request is available
    from .context import get_current_request
    request = get_current_request()
    
    # Set rotation warning flags if key is in grace period
    if request and db_api_key.grace_period_end and datetime.now(UTC) <= db_api_key.grace_period_end:
        # Set state for the middleware to add warning headers
        request.state.api_key_rotated = True
        request.state.api_key_expiry = db_api_key.grace_period_end
        
        # Find the key this one was rotated to
        rotated_to = db.query(APIKeyModel).filter(
            APIKeyModel.rotated_from_id == db_api_key.id,
            APIKeyModel.is_active == True
        ).first()
        
        if rotated_to:
            request.state.new_key_prefix = rotated_to.prefix
    
    # Update last used timestamp
    db_api_key.last_used_at = datetime.now(UTC)
    db.commit()
    
    return user
