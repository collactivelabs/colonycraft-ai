import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import ValidationError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.database import get_db
from src.models.user import User as UserModel

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")

# API key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        JWT token as string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """Get current user from JWT token

    Args:
        token: JWT token
        db: Database session

    Returns:
        User model
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception
    print(f"payload: {payload}")
    user = db.query(UserModel).filter(UserModel.email == user_email).first()
    if user is None:
        raise credentials_exception

    return user

def get_optional_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[UserModel]:
    """Get current user from JWT token or API key if available, or None if not authenticated

    Args:
        request: FastAPI request
        token: Optional JWT token
        api_key: Optional API key
        db: Database session

    Returns:
        User model or None
    """
    try:
        if token:
            return get_current_user(token=token, db=db)
        elif api_key:
            from .api_key import get_current_user_from_api_key
            return get_current_user_from_api_key(api_key=api_key, db=db)
    except HTTPException:
        pass

    return None
