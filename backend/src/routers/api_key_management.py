from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from src.core.database import get_db
from src.core.auth import get_current_user, require_scope
from src.models.user import User
from src.models.api_key import APIKey
from src.models.api_key_usage import APIKeyUsage
from src.schemas.api_key import (
    APIKeyResponse, 
    APIKeyCreate, 
    APIKeyRotate, 
    APIKeyWithValue, 
    APIKeyRotateResponse
)
from src.crud.api_key import (
    get_api_keys, 
    get_api_key, 
    create_api_key, 
    rotate_api_key, 
    deactivate_api_key,
    get_expiring_api_keys,
    get_api_keys_in_rotation
)

router = APIRouter(
    prefix="/api-key-management",
    tags=["API Key Management"],
)

@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

@router.get("/expiring-keys", response_model=List[APIKeyResponse])
async def list_expiring_keys(
    days: int = Query(7, ge=1, le=30, description="Number of days to look ahead for expiring keys"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List API keys that are about to expire within the specified number of days.
    Only an admin can see all expiring keys. Regular users will only see their own expiring keys.
    """
    if current_user.is_admin:
        # Admins can see all expiring keys
        expiring_keys = get_expiring_api_keys(db, days)
    else:
        # Regular users can only see their own expiring keys
        user_keys = get_api_keys(db, current_user.id)
        now = datetime.now()
        expiration_date = now + timedelta(days=days)
        expiring_keys = [
            key for key in user_keys 
            if key.expires_at and key.expires_at <= expiration_date
        ]
    
    return expiring_keys

@router.get("/keys-in-rotation", response_model=List[APIKeyResponse])
async def list_keys_in_rotation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List API keys that are currently in the grace period after rotation.
    Regular users will only see their own keys in rotation.
    """
    if current_user.is_admin:
        # Admins can see all keys in rotation
        return get_api_keys_in_rotation(db)
    else:
        # Regular users can only see their own keys in rotation
        return get_api_keys_in_rotation(db, current_user.id)

@router.get("/usage-stats/{api_key_id}")
async def get_api_key_usage_stats(
    api_key_id: str = Path(..., description="API key ID to get usage stats for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get usage statistics for a specific API key.
    This includes data like:
    - Total number of requests
    - Requests by endpoint
    - Success/failure rates
    - Average response times
    """
    # Verify the user has access to this key
    key = get_api_key(db, api_key_id, current_user.id)
    if not key and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # If user is admin and key wasn't found with their ID, try to find it without user filtering
    if not key and current_user.is_admin:
        key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
    
    # Query usage statistics
    usage_records = db.query(APIKeyUsage).filter(APIKeyUsage.api_key_id == api_key_id).all()
    
    if not usage_records:
        return {
            "total_requests": 0,
            "endpoints": {},
            "status_codes": {},
            "average_response_time_ms": 0
        }
    
    # Calculate statistics
    total_requests = len(usage_records)
    endpoints = {}
    status_codes = {}
    total_response_time = 0
    
    for record in usage_records:
        # Count by endpoint
        endpoint = f"{record.method} {record.endpoint}"
        endpoints[endpoint] = endpoints.get(endpoint, 0) + 1
        
        # Count by status code
        status = str(record.status_code)
        status_codes[status] = status_codes.get(status, 0) + 1
        
        # Sum response times
        if record.response_time_ms:
            total_response_time += record.response_time_ms
    
    # Calculate average response time
    avg_response_time = total_response_time / total_requests if total_requests > 0 else 0
    
    return {
        "total_requests": total_requests,
        "endpoints": endpoints,
        "status_codes": status_codes,
        "average_response_time_ms": avg_response_time
    }

@router.post("/rotation-recommendations")
async def get_rotation_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get recommendations for API key rotation based on:
    - Keys that are about to expire
    - Keys that haven't been rotated in a long time
    - Keys with high usage that might benefit from rotation
    """
    user_id = current_user.id if not current_user.is_admin else None
    
    # Get all keys or just user's keys
    if user_id:
        keys = get_api_keys(db, user_id)
    else:
        keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    
    recommendations = []
    now = datetime.now()
    
    for key in keys:
        reason = None
        
        # Check if key is expiring soon
        if key.expires_at and (key.expires_at - now).days <= 30:
            reason = "EXPIRING_SOON"
        
        # Check if key is old (over 90 days)
        elif key.created_at and (now - key.created_at).days >= 90:
            reason = "KEY_AGE"
            
        # Check key usage (high usage keys might benefit from rotation)
        if not reason:
            usage_count = db.query(APIKeyUsage).filter(APIKeyUsage.api_key_id == key.id).count()
            if usage_count > 10000:  # Arbitrary threshold
                reason = "HIGH_USAGE"
        
        if reason:
            recommendations.append({
                "key_id": key.id,
                "key_prefix": key.prefix,
                "name": key.name,
                "reason": reason,
                "user_id": key.user_id
            })
    
    return recommendations
