# Security Guidelines

## Overview

This document outlines security best practices and guidelines for the ColonyCraft AI platform. Following these guidelines helps ensure that the application remains secure against common vulnerabilities and threats.

## Authentication and Authorization

### Password Storage

- **Never** store passwords in plaintext
- Use Argon2id for password hashing (preferred) or bcrypt as a fallback
- Implement proper password strength requirements:
  - Minimum 10 characters
  - Mixture of uppercase, lowercase, numbers, and special characters
  - Check against common password lists

```python
# Example password hashing with Argon2id
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,           # Number of iterations
    memory_cost=65536,     # Memory usage in kibibytes
    parallelism=4,         # Number of parallel threads
    hash_len=32,           # Length of the hash in bytes
    salt_len=16            # Length of the salt in bytes
)

# Hash a password
hash = ph.hash("user_secure_password")

# Verify a password
try:
    ph.verify(hash, "user_provided_password")
    is_valid = True
except VerifyMismatchError:
    is_valid = False
```

### JWT Implementation

- Use strong, randomly generated secrets for signing JWTs
- Set appropriate expiration times:
  - Short-lived access tokens (15-30 minutes)
  - Longer-lived refresh tokens (7-14 days)
- Include only necessary claims in tokens
- Implement refresh token rotation for enhanced security
- Store refresh tokens in secure HTTP-only cookies with SameSite=Strict

```python
# Example JWT implementation
import jwt
from datetime import datetime, timedelta
import secrets

# Generate a secure random secret key
JWT_SECRET_KEY = secrets.token_hex(32)
JWT_ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    
    # Default expiration of 30 minutes
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
```

### API Key Security

- Hash API keys before storing in the database
- Generate keys with sufficient entropy (at least 32 bytes)
- Implement automatic key rotation policies
- Allow keys to be scoped with specific permissions
- Include key usage auditing and monitoring

```python
# Example API key generation and storage
import secrets
import hashlib

def generate_api_key():
    # Generate a 48-character API key (32 bytes in base64)
    raw_key = secrets.token_urlsafe(32)
    # Add a prefix for easier identification
    api_key = f"apk_{raw_key}"
    
    # Hash the key for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, key_hash

def verify_api_key(provided_key, stored_hash):
    # Hash the provided key and compare with stored hash
    provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
    return secrets.compare_digest(provided_hash, stored_hash)
```

## Input Validation and Output Encoding

### Input Validation

- Validate all input data against expected types and formats
- Use Pydantic models for robust request validation
- Implement strict schema validation for API endpoints
- Apply length and format restrictions appropriate to each field
- Validate data both client-side and server-side

```python
# Example Pydantic model for input validation
from pydantic import BaseModel, Field, EmailStr, validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=10)
    name: str = Field(..., min_length=1, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        # Check for uppercase, lowercase, digit, and special char
        if not (re.search(r'[A-Z]', v) and 
                re.search(r'[a-z]', v) and 
                re.search(r'[0-9]', v) and 
                re.search(r'[^A-Za-z0-9]', v)):
            raise ValueError('Password must contain uppercase, lowercase, digit, and special character')
        return v
```

### Output Encoding

- Always encode data when rendering in HTML or templates
- Use context-appropriate encoding for different output channels
- Do not rely on client-side escaping alone
- Be cautious with data formats that can contain executable code (JSON, XML)

## API Security

### Rate Limiting

- Implement token bucket algorithm for rate limiting
- Set different limits for different endpoints based on sensitivity
- Include clear rate limit information in API responses
- Add exponential backoff for repeated violations

```python
# Rate limit headers in responses
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add rate limit headers if available in request state
    if hasattr(request.state, "rate_limit"):
        rate_limit = request.state.rate_limit
        response.headers["X-RateLimit-Limit"] = str(rate_limit.limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_limit.remaining)
        response.headers["X-RateLimit-Reset"] = str(rate_limit.reset)
    
    return response
```

### Security Headers

- Implement all recommended security headers:
  - Content-Security-Policy (CSP)
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection
  - Strict-Transport-Security (HSTS)
  - Referrer-Policy

```python
# Example security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Add security headers
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

### CORS Configuration

- Implement a restrictive CORS policy
- Allow only specific domains in production
- Avoid using wildcards (*) in production environments
- Be deliberate about allowed methods and headers

```python
# Example CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://colonycraft.ai",
        "https://www.colonycraft.ai",
        "https://staging.colonycraft.ai"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset"
    ],
    max_age=86400  # 24 hours
)
```

## LLM-Specific Security

### Prompt Injection Prevention

- Validate and sanitize user inputs before sending to LLM APIs
- Implement clear boundaries between system instructions and user input
- Monitor for attempts to override system instructions
- Apply content filtering to detect malicious prompts

```python
# Example prompt sanitization
def sanitize_prompt(user_input):
    # Remove control characters that might affect prompt structure
    sanitized = re.sub(r'[\x00-\x1F\x7F]', '', user_input)
    
    # Detect and prevent common prompt injection patterns
    injection_patterns = [
        r'ignore previous instructions',
        r'disregard (earlier|previous)',
        r'instead, (do|output|return)',
        # Add more patterns as needed
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            return None, "Potential prompt injection detected"
    
    return sanitized, None
```

### API Key Management for LLM Providers

- Never expose provider API keys in client-side code
- Store provider keys in secure environment variables
- Implement key rotation policies
- Use different keys for development, staging, and production
- Monitor usage to detect unusual patterns

### Content Filtering

- Implement content filtering for both inputs and outputs
- Scan for sensitive data patterns (PII, credentials, API keys)
- Apply moderation endpoints when available from providers
- Create fallback mechanisms when content is rejected

```python
# Example content filtering for PII
def filter_pii(text):
    patterns = {
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'
    }
    
    filtered_text = text
    for pii_type, pattern in patterns.items():
        filtered_text = re.sub(pattern, f"[REDACTED {pii_type.upper()}]", filtered_text)
    
    return filtered_text
```

## Data Security

### Database Security

- Use parameterized queries to prevent SQL injection
- Implement database-level access controls
- Apply column-level encryption for sensitive data
- Use row-level security for multi-tenant scenarios
- Regularly audit database access and operations

```python
# Example of using SQLAlchemy with parameterized queries
from sqlalchemy import text

async def safe_query(db, user_id):
    # Use parameterized query with named parameters
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    return result.fetchone()
```

### Data Encryption

- Encrypt sensitive data at rest
- Use industry-standard encryption algorithms (AES-256-GCM)
- Implement proper key management
- Store encryption keys separately from encrypted data
- Consider using a key management service (KMS)

```python
# Example data encryption using Fernet (AES-128-CBC)
from cryptography.fernet import Fernet
import base64
import os

def generate_key():
    return Fernet.generate_key()

def encrypt_data(data, key):
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode()

# For production, consider using a KMS service instead of handling keys directly
```

### Application Secrets

- Never commit secrets to version control
- Use environment variables or a secure vault for secrets
- Implement different secrets for each environment
- Automate secret rotation

## Secure Development Practices

### Code Reviews

- Require code reviews focused on security
- Use automated tools for security scanning
- Maintain a security checklist for reviews
- Implement four-eyes principle for critical code

### Dependency Management

- Regularly audit and update dependencies
- Use dependency scanning tools
- Monitor security advisories for used packages
- Pin dependency versions for consistency

```bash
# Example commands for dependency security
# Python
pip-audit

# npm
npm audit
```

### Security Testing

- Implement automated security testing in CI/CD
- Include security-focused unit and integration tests
- Perform regular penetration testing
- Use OWASP ZAP or similar tools for vulnerability scanning

## Infrastructure Security

### Network Security

- Implement network segmentation
- Configure web application firewall (WAF)
- Use private subnets for backend services
- Implement proper ingress and egress filtering

### Container Security

- Use minimal base images
- Run containers with least privilege
- Implement container image scanning
- Avoid running containers as root

```dockerfile
# Example secure Dockerfile
FROM python:3.9-slim-bullseye

# Create a non-root user
RUN useradd -m -s /bin/bash appuser

# Set working directory and ensure proper permissions
WORKDIR /app
COPY --chown=appuser:appuser . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Incident Response

### Logging and Monitoring

- Implement comprehensive logging
- Include contextual information in logs
- Be careful not to log sensitive data
- Set up log aggregation and analysis
- Configure alerts for suspicious activities

```python
# Example structured logging
import structlog
import logging
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Example usage
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = datetime.now()
    
    # Extract request info without sensitive data
    request_info = {
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
    }
    
    # Create a request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Add context for all subsequent log entries
    logger = structlog.get_logger().bind(
        request_id=request_id,
        **request_info
    )
    
    logger.info("Request received")
    
    try:
        response = await call_next(request)
        
        # Log response info
        logger.info(
            "Request completed",
            status_code=response.status_code,
            duration_ms=(datetime.now() - start_time).total_seconds() * 1000
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.exception("Request failed", error=str(e))
        raise
```

### Security Auditing

- Implement audit logging for security-relevant events
- Record authentication attempts (successful and failed)
- Log API key usage and administrative actions
- Track permission changes and security setting modifications

## Compliance

### Data Protection

- Implement data minimization principles
- Store only necessary data for the required period
- Provide clear data retention and deletion policies
- Ensure compliance with relevant regulations (GDPR, CCPA)

### Privacy Features

- Implement user data export functionality
- Provide account deletion capability
- Include data processing audit trails
- Obtain appropriate user consent for data processing

## Security Checklist for Deployment

### Pre-Deployment

1. Scan dependencies for vulnerabilities
2. Run automated security tests
3. Conduct code reviews with security focus
4. Verify proper configuration of security headers
5. Check for secrets in code or configuration
6. Validate rate limiting implementation
7. Ensure secure API key handling

### Post-Deployment

1. Run penetration tests against deployed application
2. Verify secure communication (TLS/SSL)
3. Check security headers in production
4. Test authentication and authorization controls
5. Monitor for unusual activity or errors
6. Validate backup and recovery procedures
7. Confirm logging and monitoring are working

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [LLM Security Best Practices](https://github.com/safetybelt/safetybelt/blob/main/LEARNABOUT.md)
