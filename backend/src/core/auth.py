import os
import secrets
import hashlib
import hmac
import time
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from ..core.database import get_db
from ..core.config import get_settings
from ..core.exceptions import AuthenticationError, AuthorizationError

settings = get_settings()

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

class APIKey(BaseModel):
    id: str
    key_hash: str
    prefix: str
    name: str
    user_id: str
    scope: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True
    # Rotation related fields
    rotated_from_id: Optional[str] = None
    rotation_date: Optional[datetime] = None
    grace_period_days: Optional[int] = None
    grace_period_end: Optional[datetime] = None
    was_compromised: bool = False

    @classmethod
    def generate(cls, user_id: str, name: str, scope: List[str] = None,
                expires_in_days: Optional[int] = None, rotated_from_id: Optional[str] = None,
                grace_period_days: Optional[int] = None, was_compromised: bool = False) -> Tuple['APIKey', str]:
        """Generate a new API key"""
        key_id = secrets.token_hex(8)
        key_secret = secrets.token_hex(24)
        prefix = key_id[:8]

        # Create hash of the key for storage
        key_hash = hashlib.sha256(key_secret.encode()).hexdigest()

        # Calculate expiration date if provided
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Calculate grace period end if rotating a key
        grace_period_end = None
        if rotated_from_id and grace_period_days:
            grace_period_end = datetime.utcnow() + timedelta(days=grace_period_days)

        # Create the API key object
        api_key = cls(
            id=key_id,
            key_hash=key_hash,
            prefix=prefix,
            name=name,
            user_id=user_id,
            scope=scope or ["*"],
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True,
            rotated_from_id=rotated_from_id,
            rotation_date=datetime.utcnow() if rotated_from_id else None,
            grace_period_days=grace_period_days,
            grace_period_end=grace_period_end,
            was_compromised=was_compromised
        )

        # Return the API key object and the full key that should be provided to the user
        full_key = f"{prefix}.{key_secret}"
        return api_key, full_key

    @staticmethod
    def verify_key(api_key_obj: 'APIKey', provided_key: str) -> bool:
        """Verify if the provided key matches the stored API key"""
        try:
            prefix, secret = provided_key.split(".", 1)
            if prefix != api_key_obj.prefix:
                return False

            # Hash the provided secret and compare with stored hash
            provided_hash = hashlib.sha256(secret.encode()).hexdigest()
            return hmac.compare_digest(provided_hash, api_key_obj.key_hash)
        except ValueError:
            # Invalid format
            return False

    def is_valid(self) -> bool:
        """Check if the API key is still valid"""
        if not self.is_active:
            return False

        if self.expires_at and self.expires_at < datetime.utcnow():
            return False

        return True

    def is_in_grace_period(self) -> bool:
        """Check if the key is in its grace period after rotation"""
        if not self.grace_period_end:
            return False

        return self.grace_period_end > datetime.utcnow()

    @classmethod
    def rotate(cls, old_api_key: 'APIKey', name: Optional[str] = None, scope: Optional[List[str]] = None,
              expires_in_days: Optional[int] = None, grace_period_days: int = 7,
              was_compromised: bool = False) -> Tuple['APIKey', str]:
        """Generate a new API key by rotating an existing one"""
        # Keep the same name and scope if not provided
        new_name = name or old_api_key.name
        new_scope = scope or old_api_key.scope

        # Generate a new API key with reference to the old one
        return cls.generate(
            user_id=old_api_key.user_id,
            name=new_name,
            scope=new_scope,
            expires_in_days=expires_in_days,
            rotated_from_id=old_api_key.id,
            grace_period_days=grace_period_days,
            was_compromised=was_compromised
        )

# JWT authentication for user sessions
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token", auto_error=False)

class TokenData(BaseModel):
    user_id: Optional[str] = None
    scopes: List[str] = []

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Validate JWT token and return the user"""
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        token_scopes = payload.get("scopes", [])
        token_data = TokenData(user_id=user_id, scopes=token_scopes)
    except JWTError:
        return None

    # Here you would typically query your database to get the user
    # user = get_user_by_id(db, user_id=token_data.user_id)
    # if user is None:
    #     return None

    # For now, we'll just return the token data
    return token_data

# Context var for storing request information
from starlette.middleware.base import BaseMiddleware
from fastapi import Request, Response
from contextvars import ContextVar
from typing import Callable, Optional

_request_context_var: ContextVar[Optional[Request]] = ContextVar("request", default=None)

class RequestContextMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        token = _request_context_var.set(request)
        try:
            return await call_next(request)
        finally:
            _request_context_var.reset(token)

def get_request() -> Optional[Request]:
    """Get the current request from context"""
    return _request_context_var.get()

async def get_current_user_from_api_key(api_key: str = Security(API_KEY_HEADER), db: Session = Depends(get_db)):
    """Validate API key and return the associated user"""
    if not api_key:
        return None

    try:
        # Get the prefix from the API key
        prefix = api_key.split(".")[0]

        # Find the API key in the database
        from ..models.api_key import APIKey as APIKeyModel
        db_api_key = db.query(APIKeyModel).filter(APIKeyModel.prefix == prefix).first()

        if not db_api_key:
            return None

        # Verify the key matches
        if not APIKey.verify_key(APIKey(
            id=db_api_key.id,
            key_hash=db_api_key.key_hash,
            prefix=db_api_key.prefix,
            name=db_api_key.name,
            user_id=db_api_key.user_id,
            scope=db_api_key.scopes
        ), api_key):
            return None

        # Handle keys in grace period after rotation
        if not db_api_key.is_valid() and db_api_key.is_in_grace_period():
            # Find the new key that replaced this one
            new_key = db.query(APIKeyModel).filter(
                APIKeyModel.rotated_from_id == db_api_key.id,
                APIKeyModel.is_active == True
            ).first()

            if new_key:
                # Allow using the key but add a warning header in the response
                request = get_request()
                if request:
                    request.state.api_key_rotated = True
                    request.state.api_key_expiry = db_api_key.grace_period_end
                    request.state.new_key_prefix = new_key.prefix
        elif not db_api_key.is_valid():
            return None

        # Update last used timestamp
        db_api_key.update_last_used()
        db.commit()

        # Return the user associated with this key
        return db_api_key.user
    except Exception as e:
        # Log the error
        import logging
        logging.getLogger(__name__).error(f"API key authentication error: {str(e)}")
        return None

async def get_current_user(token_user = Depends(get_current_user_from_token),api_key_user = Depends(get_current_user_from_api_key)):
    """Get current user from either JWT token or API key"""
    if token_user:
        return token_user
    if api_key_user:
        return api_key_user
    raise AuthenticationError()

def require_scope(required_scope: str):
    """Dependency to check if user has the required scope"""
    async def scope_validator(current_user = Depends(get_current_user)):
        user_scopes = getattr(current_user, "scopes", [])

        if "*" in user_scopes:
            return current_user

        if required_scope in user_scopes:
            return current_user

        raise AuthorizationError(message=f"Insufficient permissions. Required scope: {required_scope}")

    return scope_validator
