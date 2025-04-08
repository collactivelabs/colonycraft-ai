from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from datetime import datetime
import re

class APIKeyBase(BaseModel):
    name: str = Field(..., description="A descriptive name for the API key", min_length=3, max_length=100)
    scopes: Optional[List[str]] = Field(None, description="List of authorized scopes for this API key")
    expires_in_days: Optional[int] = Field(None, description="Number of days until the key expires", ge=1, le=365)
    
    @field_validator('name')
    def name_must_be_valid(cls, v):
        if not re.match(r'^[a-zA-Z0-9\-_\.\s]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, hyphens, underscores, and periods')
        return v
    
    @field_validator('scopes')
    def validate_scopes(cls, v):
        if v is not None:
            valid_scopes = ['read', 'write', 'admin', '*']
            for scope in v:
                if scope not in valid_scopes:
                    raise ValueError(f"Invalid scope: {scope}. Valid scopes are: {', '.join(valid_scopes)}")
        return v

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyRotate(BaseModel):
    name: Optional[str] = Field(None, description="New name for the rotated key (defaults to original name)")
    scopes: Optional[List[str]] = Field(None, description="New scopes for the rotated key (defaults to original scopes)")
    expires_in_days: Optional[int] = Field(None, description="Days until the new key expires", ge=1, le=365)
    grace_period_days: Optional[int] = Field(7, description="Days the old key remains valid after rotation", ge=1, le=30)
    was_compromised: bool = Field(False, description="Flag indicating if the key is being rotated due to compromise")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "New Production Key",
                "scopes": ["read", "write"],
                "expires_in_days": 90,
                "grace_period_days": 7,
                "was_compromised": False
            }
        }
    }

class APIKeyResponse(APIKeyBase):
    id: str
    prefix: str
    user_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool
    rotation_date: Optional[datetime] = None
    grace_period_days: Optional[int] = None
    grace_period_end: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True
    }

class APIKeyWithValue(APIKeyResponse):
    key: str = Field(..., description="The full API key to use for authentication")

class APIKeyRotateResponse(APIKeyWithValue):
    old_key_prefix: str = Field(..., description="Prefix of the old key that was rotated")
    old_key_expiry: Optional[datetime] = Field(None, description="When the old rotated key will expire")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "a1b2c3d4",
                "name": "New Production Key",
                "prefix": "e5f6g7h8",
                "key": "e5f6g7h8.i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",
                "user_id": "user123",
                "scopes": ["read", "write"],
                "created_at": "2023-01-01T00:00:00Z",
                "expires_at": "2023-04-01T00:00:00Z",
                "is_active": True,
                "old_key_prefix": "a1b2c3d4",
                "old_key_expiry": "2023-01-08T00:00:00Z"
            }
        },
        "from_attributes": True
    }
