import pytest
import hashlib
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, Security
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from ..core.auth import APIKey, get_current_user_from_api_key, get_current_user, require_scope
from fastapi.security import APIKeyHeader

# Define the API key header for testing
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
from ..models.api_key import APIKey as APIKeyModel

# Test the APIKey class
class TestAPIKeyClass:
    def test_generate_api_key(self):
        """Test generating a new API key"""
        api_key, key_value = APIKey.generate(
            user_id="test_user",
            name="Test Key",
            scopes=["read", "write"]
        )
        
        # Check API key object properties
        assert api_key.id is not None
        assert len(api_key.id) == 16  # 8 bytes as hex
        assert api_key.prefix == api_key.id[:8]
        assert api_key.name == "Test Key"
        assert api_key.user_id == "test_user"
        assert api_key.scope == ["read", "write"]
        assert api_key.is_active is True
        assert isinstance(api_key.created_at, datetime)
        assert api_key.expires_at is None
        
        # Check the key value format
        assert len(key_value.split(".")) == 2
        prefix, secret = key_value.split(".")
        assert prefix == api_key.prefix
        assert len(secret) == 48  # 24 bytes as hex
        
        # Verify that the key hash matches the secret
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        assert api_key.key_hash == secret_hash

    def test_generate_with_expiration(self):
        """Test generating an API key with expiration"""
        api_key, _ = APIKey.generate(
            user_id="test_user",
            name="Expiring Key",
            scopes=["read"],
            expires_in_days=30
        )
        
        # Check expiration date
        assert api_key.expires_at is not None
        expiration_delta = api_key.expires_at - datetime.utcnow()
        assert 29 <= expiration_delta.days <= 30  # Allow for slight timing differences

    def test_verify_key(self):
        """Test verifying an API key"""
        api_key, key_value = APIKey.generate(
            user_id="test_user",
            name="Verify Test Key",
            scopes=["read"]
        )
        
        # Correct key should verify
        assert APIKey.verify_key(api_key, key_value) is True
        
        # Incorrect key should fail
        assert APIKey.verify_key(api_key, f"{api_key.prefix}.invalid") is False
        assert APIKey.verify_key(api_key, "invalid.key") is False
        assert APIKey.verify_key(api_key, "invalidkey") is False
    
    def test_is_valid(self):
        """Test API key validity checks"""
        # Active, non-expiring key
        api_key, _ = APIKey.generate(
            user_id="test_user",
            name="Valid Key",
            scopes=["read"]
        )
        assert api_key.is_valid() is True
        
        # Inactive key
        inactive_key, _ = APIKey.generate(
            user_id="test_user",
            name="Inactive Key",
            scope=["read"]
        )
        inactive_key.is_active = False
        assert inactive_key.is_valid() is False
        
        # Expired key
        expired_key, _ = APIKey.generate(
            user_id="test_user",
            name="Expired Key",
            scope=["read"]
        )
        expired_key.expires_at = datetime.utcnow() - timedelta(days=1)
        assert expired_key.is_valid() is False

# Test API key authentication in FastAPI
@pytest.fixture
def auth_app():
    """Create a test app with API key authentication"""
    app = FastAPI()
    
    @app.get("/api/public")
    async def public_endpoint():
        return {"message": "public"}
    
    @app.get("/api/protected")
    async def protected_endpoint(current_user = Depends(get_current_user)):
        return {"message": "authenticated", "user": current_user}
    
    @app.get("/api/read-scope")
    async def read_scope_endpoint(current_user = Depends(require_scope("read"))):
        return {"message": "read access", "user": current_user}
    
    @app.get("/api/write-scope")
    async def write_scope_endpoint(current_user = Depends(require_scope("write"))):
        return {"message": "write access", "user": current_user}
    
    return app

@pytest.fixture
def auth_client(auth_app):
    """Create a test client for the auth app"""
    return TestClient(auth_app)

def test_public_endpoint(auth_client):
    """Test accessing a public endpoint without authentication"""
    response = auth_client.get("/api/public")
    assert response.status_code == 200
    assert response.json() == {"message": "public"}

def test_protected_endpoint_no_auth(auth_client):
    """Test accessing a protected endpoint without authentication"""
    response = auth_client.get("/api/protected")
    assert response.status_code == 401
    
    data = response.json()
    assert "detail" in data
    # Modern FastAPI returns a simpler error structure
    assert data["detail"] == "Not authenticated"

def test_protected_endpoint_with_api_key(auth_client, monkeypatch):
    """Test accessing a protected endpoint with API key authentication"""
    # Mock the get_current_user_from_api_key function
    async def mock_get_user_from_api_key(*args, **kwargs):
        return {"user_id": "test_user", "scopes": ["read", "write"]}
    
    monkeypatch.setattr(
        "src.core.auth.get_current_user_from_api_key",
        mock_get_user_from_api_key
    )
    
    response = auth_client.get(
        "/api/protected",
        headers={"X-API-Key": "test.apikey"}
    )
    
    assert response.status_code == 200
    assert response.json() == {
        "message": "authenticated",
        "user": {"user_id": "test_user", "scopes": ["read", "write"]}
    }

def test_scope_authorization(auth_client, monkeypatch):
    """Test authorization with different scopes"""
    # Mock for user with read-only scope
    async def mock_read_only_user(*args, **kwargs):
        return {"user_id": "read_user", "scopes": ["read"]}
    
    # Test read access with read scope
    monkeypatch.setattr(
        "src.core.auth.get_current_user",
        mock_read_only_user
    )
    
    response = auth_client.get("/api/read-scope")
    assert response.status_code == 200
    
    # Test write access with read scope (should fail)
    response = auth_client.get("/api/write-scope")
    assert response.status_code == 403
    
    # Mock for user with write scope
    async def mock_write_user(*args, **kwargs):
        return {"user_id": "write_user", "scopes": ["write"]}
    
    monkeypatch.setattr(
        "src.core.auth.get_current_user",
        mock_write_user
    )
    
    # Test write access with write scope
    response = auth_client.get("/api/write-scope")
    assert response.status_code == 200
    
    # Test read access with write scope (should fail)
    response = auth_client.get("/api/read-scope")
    assert response.status_code == 403
    
    # Mock for user with wildcard scope
    async def mock_admin_user(*args, **kwargs):
        return {"user_id": "admin", "scopes": ["*"]}
    
    monkeypatch.setattr(
        "src.core.auth.get_current_user",
        mock_admin_user
    )
    
    # Test both endpoints with wildcard scope
    response = auth_client.get("/api/read-scope")
    assert response.status_code == 200
    
    response = auth_client.get("/api/write-scope")
    assert response.status_code == 200
