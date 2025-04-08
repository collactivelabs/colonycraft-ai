from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
import secrets

from ..models.api_key import APIKey
from ..models.api_key_rotation_history import APIKeyRotationHistory
from ..core.auth import APIKey as APIKeyAuth

def get_api_keys(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[APIKey]:
    """Get all API keys for a user"""
    return db.query(APIKey).filter(APIKey.user_id == user_id).offset(skip).limit(limit).all()

def get_api_key(db: Session, api_key_id: str, user_id: str) -> Optional[APIKey]:
    """Get a specific API key by ID for a user"""
    return db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user_id).first()

def get_api_key_by_prefix(db: Session, prefix: str) -> Optional[APIKey]:
    """Get an API key by its prefix"""
    return db.query(APIKey).filter(APIKey.prefix == prefix).first()

def create_api_key(
    db: Session, 
    user_id: str, 
    name: str, 
    scopes: Optional[List[str]] = None,
    expires_in_days: Optional[int] = None
) -> Tuple[APIKey, str]:
    """Create a new API key for a user"""
    # Generate a key using the APIKey auth class
    api_key_auth, key_value = APIKeyAuth.generate(
        user_id=user_id,
        name=name,
        scope=scopes,
        expires_in_days=expires_in_days
    )
    
    # Create the API key in the database
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
        
    db_api_key = APIKey(
        id=api_key_auth.id,
        key_hash=api_key_auth.key_hash,
        prefix=api_key_auth.prefix,
        name=name,
        user_id=user_id,
        scopes=scopes or ["*"],
        created_at=datetime.now(UTC),
        expires_at=expires_at,
        is_active=True
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    
    return db_api_key, key_value

def rotate_api_key(
    db: Session,
    api_key_id: str,
    user_id: str,
    name: Optional[str] = None,
    scopes: Optional[List[str]] = None,
    expires_in_days: Optional[int] = None,
    grace_period_days: int = 7,
    was_compromised: bool = False,
    rotated_by_user_id: Optional[str] = None
) -> Tuple[APIKey, APIKey, str]:
    """
    Rotate an API key by creating a new one and marking the old one for expiration.
    
    Returns:
        Tuple containing (new_api_key, old_api_key, new_key_value)
    """
    # Get the existing API key
    old_key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user_id).first()
    if not old_key:
        raise ValueError("API key not found")
    
    # Set the rotator ID (if not provided, use the key owner)
    if not rotated_by_user_id:
        rotated_by_user_id = user_id
    
    # Use provided values or defaults from the old key
    new_name = name or old_key.name
    new_scopes = scopes or old_key.scopes
    
    # If the key was compromised, immediately deactivate the old key
    if was_compromised:
        old_key.is_active = False
        old_key.was_compromised = True
        old_key.grace_period_days = 0
        old_key.grace_period_end = None
        grace_period_days = 0
    else:
        # Set the grace period for the old key
        old_key.grace_period_days = grace_period_days
        old_key.grace_period_end = datetime.now(UTC) + timedelta(days=grace_period_days)
    
    # Create a new API key
    api_key_auth, key_value = APIKeyAuth.rotate(
        old_api_key=APIKeyAuth(
            id=old_key.id,
            key_hash=old_key.key_hash,
            prefix=old_key.prefix,
            name=old_key.name,
            user_id=old_key.user_id,
            scope=old_key.scopes,
            created_at=old_key.created_at,
            expires_at=old_key.expires_at,
            is_active=old_key.is_active
        ),
        name=new_name,
        scope=new_scopes,
        expires_in_days=expires_in_days,
        grace_period_days=grace_period_days,
        was_compromised=was_compromised
    )
    
    # Calculate expiration date for the new key
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)
    
    # Create the new API key in the database
    new_key = APIKey(
        id=api_key_auth.id,
        key_hash=api_key_auth.key_hash,
        prefix=api_key_auth.prefix,
        name=new_name,
        user_id=user_id,
        scopes=new_scopes,
        created_at=datetime.now(UTC),
        expires_at=expires_at,
        is_active=True,
        rotated_from_id=old_key.id,
        rotation_date=datetime.now(UTC),
        grace_period_days=grace_period_days
    )
    
    # Create rotation history record
    rotation_history = APIKeyRotationHistory(
        api_key_id=old_key.id,
        previous_prefix=old_key.prefix,
        rotation_date=datetime.now(UTC),
        rotated_by_user_id=rotated_by_user_id,
        reason="Compromised key" if was_compromised else "Routine rotation",
        grace_period_days=grace_period_days,
        grace_period_end=old_key.grace_period_end,
        is_compromised=was_compromised
    )
    
    # Add new records to the database
    db.add(new_key)
    db.add(rotation_history)
    db.commit()
    db.refresh(new_key)
    db.refresh(old_key)
    
    return new_key, old_key, key_value

def deactivate_api_key(db: Session, api_key_id: str, user_id: str) -> Optional[APIKey]:
    """Deactivate (revoke) an API key"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user_id).first()
    if api_key:
        api_key.is_active = False
        db.commit()
        db.refresh(api_key)
    return api_key

def get_rotation_history(db: Session, api_key_id: str, user_id: str) -> List[APIKeyRotationHistory]:
    """Get the rotation history for an API key"""
    # First verify the user owns this key
    key = db.query(APIKey).filter(APIKey.id == api_key_id, APIKey.user_id == user_id).first()
    if not key:
        return []
    
    # Then fetch the rotation history
    return db.query(APIKeyRotationHistory).filter(APIKeyRotationHistory.api_key_id == api_key_id).all()

def get_api_keys_in_rotation(db: Session, user_id: str) -> List[APIKey]:
    """Get API keys that are currently in the grace period after rotation"""
    now = datetime.now(UTC)
    return db.query(APIKey).filter(
        APIKey.user_id == user_id,
        APIKey.grace_period_end.isnot(None),
        APIKey.grace_period_end > now
    ).all()

def get_expiring_api_keys(db: Session, days_until_expiry: int = 7) -> List[APIKey]:
    """Get API keys that are about to expire within the specified number of days"""
    expiry_threshold = datetime.now(UTC) + timedelta(days=days_until_expiry)
    return db.query(APIKey).filter(
        APIKey.is_active == True,
        APIKey.expires_at.isnot(None),
        APIKey.expires_at <= expiry_threshold
    ).all()
