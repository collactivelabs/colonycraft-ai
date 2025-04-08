from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from ....core.auth import *
from ....models.user import User
from ....core.config import get_settings

settings = get_settings()

router = APIRouter(tags=["Auth"])

class Token(BaseModel):
    status: str
    access_token: str
    token_type: str
    expires_at: int

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    # Use the SECRET_KEY from settings and ALGORITHM from auth
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt, int(expire.timestamp())

# Define explicit OPTIONS route handler for preflight requests
@router.options("/client-token")
async def options_client_token():
    """Handle OPTIONS preflight request for client-token endpoint"""
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
            "Access-Control-Max-Age": "86400",  # 24 hours
        },
    )

@router.post("/client-token", response_model=Token)
async def get_client_token(current_user: User = Depends(get_current_user)):
    """
    Get a temporary access token for client-side LLM API calls
    """
    # Create a token valid for 15 minutes
    access_token, expires_at = create_access_token(
        data={"sub": current_user.email, "uid": str(current_user.id)},
        expires_delta=timedelta(minutes=15)
    )

    # Check if the token was created successfully
    if not access_token:
        raise HTTPException(status_code=500, detail="Failed to create access token")

    # Log the token creation
    print(f"Access token created for user {current_user.email} with UID {current_user.id}")

    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at
    }