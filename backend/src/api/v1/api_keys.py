from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, UTC
import logging

from ...core.database import get_db
from ...core.auth import get_current_user, get_current_user_from_api_key, require_scope
from ...models.api_key import APIKey as APIKeyModel
from ...models.api_key_rotation_history import APIKeyRotationHistory
from ...core.exceptions import ResourceNotFoundError, AuthorizationError
from ...schemas.api_key import (
    APIKeyBase,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithValue,
    APIKeyRotate,
    APIKeyRotateResponse
)
from ...crud.api_key import (
    get_api_keys,
    get_api_key,
    create_api_key as crud_create_api_key,
    rotate_api_key as crud_rotate_api_key,
    deactivate_api_key,
    get_rotation_history,
    get_api_keys_in_rotation,
    get_expiring_api_keys
)

logger = logging.getLogger(__name__)
router = APIRouter()

# API endpoints


@router.post("", response_model=APIKeyWithValue)
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:write"))
):
    """
    Create a new API key for the current user
    """
    try:
        # Create the API key using our CRUD function
        db_api_key, key_value = crud_create_api_key(
            db=db,
            user_id=current_user.id,
            name=key_data.name,
            scopes=key_data.scopes,
            expires_in_days=key_data.expires_in_days
        )
        
        # Return the key value along with the API key data
        return APIKeyWithValue(
            id=db_api_key.id,
            prefix=db_api_key.prefix,
            name=db_api_key.name,
            scopes=db_api_key.scopes,
            created_at=db_api_key.created_at,
            expires_at=db_api_key.expires_at,
            last_used_at=db_api_key.last_used_at,
            is_active=db_api_key.is_active,
            key=key_value
        )
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating API key: {str(e)}"
        )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:read")),
    include_rotated: bool = Query(False, description="Include keys that have been rotated but are still in grace period")
):
    """
    List all API keys for the current user
    """
    if include_rotated:
        # Include active keys plus those in grace period after rotation
        now = datetime.utcnow()
        api_keys = db.query(APIKeyModel).filter(
            APIKeyModel.user_id == current_user.id,
            (
                (APIKeyModel.is_active == True) | 
                (
                    APIKeyModel.grace_period_end.isnot(None) &
                    (APIKeyModel.grace_period_end > now)
                )
            )
        ).all()
    else:
        # Only include active keys
        api_keys = db.query(APIKeyModel).filter(
            APIKeyModel.user_id == current_user.id,
            APIKeyModel.is_active == True
        ).all()
    
    return api_keys


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:read"))
):
    """
    Get a specific API key by ID
    """
    api_key = get_api_key(db, key_id, current_user.id)
    if not api_key:
        raise ResourceNotFoundError(resource_type="APIKey", resource_id=key_id)
        
    # Ensure user can only access their own API keys (unless admin)
    if api_key.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError()
        
    return api_key


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:write"))
):
    """
    Revoke an API key (set is_active to false)
    """
    api_key = get_api_key(db, key_id, current_user.id)
    if not api_key:
        raise ResourceNotFoundError(resource_type="APIKey", resource_id=key_id)
        
    # Ensure user can only revoke their own API keys (unless admin)
    if api_key.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError()
        
    # Revoke the key
    deactivated_key = deactivate_api_key(db, key_id, current_user.id)
    if not deactivated_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate API key"
        )
    
    return None

@router.post("/{key_id}/rotate", response_model=APIKeyRotateResponse)
async def rotate_api_key(
    key_id: str,
    rotation_data: APIKeyRotate,
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:write")),
    response: Response = None
):
    """
    Rotate an API key by creating a new one and marking the old one for expiration after a grace period.
    The old key will continue to work during the grace period to allow for seamless transition.
    
    When using a rotated key in its grace period, warning headers will be included in API responses.
    """
    # First check if the key exists and belongs to the user
    api_key = get_api_key(db, key_id, current_user.id)
    if not api_key:
        raise ResourceNotFoundError(resource_type="APIKey", resource_id=key_id)
        
    # Ensure user can only rotate their own API keys (unless admin)
    if api_key.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError()
    
    try:
        # Rotate the key
        new_key, old_key, key_value = crud_rotate_api_key(
            db=db,
            api_key_id=key_id,
            user_id=current_user.id,
            name=rotation_data.name,
            scopes=rotation_data.scopes,
            expires_in_days=rotation_data.expires_in_days,
            grace_period_days=rotation_data.grace_period_days,
            was_compromised=rotation_data.was_compromised,
            rotated_by_user_id=current_user.id
        )
        
        # If the key was compromised, set security headers
        if rotation_data.was_compromised and response:
            response.headers["X-API-Key-Compromised"] = "true"
            response.headers["X-Security-Alert"] = "A potentially compromised API key has been rotated"
        
        # Return the response with both new and old key information
        return APIKeyRotateResponse(
            # New key information
            id=new_key.id,
            prefix=new_key.prefix,
            name=new_key.name,
            scopes=new_key.scopes,
            created_at=new_key.created_at,
            expires_at=new_key.expires_at,
            last_used_at=new_key.last_used_at,
            is_active=new_key.is_active,
            key=key_value,
            # Original key information
            old_key_prefix=old_key.prefix,
            old_key_expiry=old_key.grace_period_end
        )
    except Exception as e:
        logger.error(f"Error rotating API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rotating API key: {str(e)}"
        )

@router.get("/{key_id}/rotation-history", response_model=List[Dict[str, Any]])
async def api_key_rotation_history(
    key_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:read"))
):
    """
    Get the rotation history for an API key
    """
    # First check if the key exists and belongs to the user
    api_key = get_api_key(db, key_id, current_user.id)
    if not api_key:
        raise ResourceNotFoundError(resource_type="APIKey", resource_id=key_id)
        
    # Ensure user can only access their own API key history (unless admin)
    if api_key.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError()
        
    history = get_rotation_history(db, key_id, current_user.id)
    
    # Format the history for API response
    formatted_history = []
    for record in history:
        formatted_history.append({
            "id": record.id,
            "rotation_date": record.rotation_date,
            "rotated_by": record.rotated_by_user_id,
            "reason": record.reason,
            "grace_period_days": record.grace_period_days,
            "grace_period_end": record.grace_period_end,
            "was_compromised": record.is_compromised,
            "previous_key_prefix": record.previous_prefix
        })
    
    return formatted_history

@router.get("/expiring/soon", response_model=List[APIKeyResponse])
async def get_soon_expiring_keys(
    db: Session = Depends(get_db),
    current_user = Depends(require_scope("api_keys:read")),
    days: int = Query(7, description="Number of days to look ahead for expiring keys", ge=1, le=30)
):
    """
    Get API keys that will expire within the specified number of days
    """
    # Get expiring keys for this user
    expiry_threshold = datetime.utcnow() + timedelta(days=days)
    expiring_keys = db.query(APIKeyModel).filter(
        APIKeyModel.user_id == current_user.id,
        APIKeyModel.is_active == True,
        APIKeyModel.expires_at.isnot(None),
        APIKeyModel.expires_at <= expiry_threshold
    ).all()
    
    return expiring_keys
