from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Callable
import secrets
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from ..core.config import settings
from ..core.exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/token", auto_error=False)

# Ensure settings has the secret_key attribute
if not hasattr(settings, 'SECRET_KEY'):
    raise ValueError("settings module must have a 'SECRET_KEY' attribute")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None

    payload = decode_token(token)
    if payload is None:
        return None
    print(f"Decoded payload: {payload}")
    return payload

async def require_auth(current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise AuthenticationError()
    return current_user

# Generate a random nonce for CSP
def generate_nonce() -> str:
    return hashlib.sha256(secrets.token_bytes(32)).hexdigest()

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        server_name: str = "ColonyCraft-API",
        content_security_policy: Optional[Dict[str, List[str]]] = None,
        include_default_csp: bool = True,
        strict_transport_security_max_age_seconds: int = 31536000,  # 1 year
        custom_headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(app)
        self.server_name = server_name
        self.custom_headers = custom_headers or {}
        self.strict_transport_security_max_age = strict_transport_security_max_age_seconds

        # Default Content Security Policy with allowances for Swagger UI and ReDoc
        self.default_csp = {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],  # Required for Swagger UI
            "style-src": ["'self'", "'unsafe-inline'"],  # Required for Swagger UI and ReDoc
            "img-src": ["'self'", "data:", "validator.swagger.io"],
            "font-src": ["'self'"],
            "connect-src": ["'self'"],
            "frame-src": ["'self'"],  # Changed from 'none' to allow iframes
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'self'"],  # Changed to allow embedding
        }

        # Merge provided CSP with default if requested
        if include_default_csp:
            merged_csp = self.default_csp.copy()
            if content_security_policy:
                for key, values in content_security_policy.items():
                    if key in merged_csp:
                        merged_csp[key].extend(values)
                    else:
                        merged_csp[key] = values
            self.content_security_policy = merged_csp
        else:
            self.content_security_policy = content_security_policy or {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Skip security headers for documentation routes
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect", "/redoc/oauth2-redirect"]:
            # No security headers for documentation
            return response

        # Add default security headers for all other routes
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Server"] = self.server_name
        response.headers["X-Content-Security-Policy"] = "default-src 'self'"

        # Add HSTS header in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = f"max-age={self.strict_transport_security_max_age}; includeSubDomains; preload"

        # Build Content-Security-Policy header
        if self.content_security_policy:
            # Default CSP for other routes
            csp_parts = []
            for directive, sources in self.content_security_policy.items():
                if sources:
                    csp_parts.append(f"{directive} {' '.join(sources)}")
            if csp_parts:
                response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

        # Add custom headers
        for name, value in self.custom_headers.items():
            response.headers[name] = value

        return response

# Rate Limiter (token bucket algorithm)
class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float, time_function=None):
        """
        Initialize a token bucket for rate limiting.

        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Rate at which tokens are added (tokens per second)
            time_function: Optional function to get current time (for testing)
        """
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.time_function = time_function or (lambda: datetime.now(timezone.utc))
        self._tokens = {}  # Dict to store token counts for different clients
        self._timestamps = {}  # Dict to store last update times for different clients

    def take(self, client_id: str, tokens: int = 1) -> bool:
        """
        Consume tokens from the bucket for a specific client.
        Returns True if tokens were consumed, False otherwise.

        Args:
            client_id: Identifier for the client (e.g., IP address or API key)
            tokens: Number of tokens to consume

        Returns:
            True if tokens were successfully consumed, False if not enough tokens
        """
        self._refill(client_id)

        # Get current tokens for this client (default to capacity if new client)
        current_tokens = self._tokens.get(client_id, self.capacity)

        if tokens <= current_tokens:
            self._tokens[client_id] = current_tokens - tokens
            return True
        return False

    def _refill(self, client_id: str) -> None:
        """
        Refill the token bucket based on the time elapsed since the last refill.

        Args:
            client_id: Identifier for the client
        """
        now = self.time_function()

        # If this is a new client, initialize with full capacity
        if client_id not in self._timestamps:
            self._tokens[client_id] = self.capacity
            self._timestamps[client_id] = now
            return

        # Calculate time elapsed since last update
        last_update = self._timestamps[client_id]
        elapsed = (now - last_update).total_seconds()
        self._timestamps[client_id] = now

        # Calculate new tokens based on time elapsed
        current_tokens = self._tokens.get(client_id, 0.0)
        new_tokens = elapsed * self.refill_rate

        # Add new tokens to the bucket, but don't exceed capacity
        self._tokens[client_id] = min(self.capacity, current_tokens + new_tokens)

    def get_tokens(self, client_id: str) -> float:
        """
        Get the current number of tokens in the bucket for a specific client.

        Args:
            client_id: Identifier for the client

        Returns:
            Current token count
        """
        self._refill(client_id)
        return self._tokens.get(client_id, self.capacity)

    def time_until_tokens(self, client_id: str, tokens: int) -> float:
        """
        Calculate the time in seconds until 'tokens' tokens will be available.

        Args:
            client_id: Identifier for the client
            tokens: Number of tokens needed

        Returns:
            Time in seconds until tokens will be available
        """
        self._refill(client_id)
        current_tokens = self._tokens.get(client_id, self.capacity)

        if tokens <= current_tokens:
            return 0.0

        # Calculate time needed for enough tokens
        additional_tokens_needed = tokens - current_tokens
        seconds_needed = additional_tokens_needed / self.refill_rate

        return seconds_needed

    def get_next_refill_time(self, client_id: str) -> float:
        """
        Get the Unix timestamp when the next token will be added.

        Args:
            client_id: Identifier for the client

        Returns:
            Unix timestamp of the next token refill
        """
        # Time until a single token is added
        time_until_next = self.time_until_tokens(client_id,
                                               self._tokens.get(client_id, 0) + 1)

        # Current timestamp plus the wait time
        now = self.time_function()
        next_refill = now.timestamp() + time_until_next

        return next_refill