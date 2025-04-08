import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from ..core.security import SecurityHeadersMiddleware
from ..core.config import get_settings

@pytest.fixture
def test_app():
    """Create a test app with security headers middleware"""
    app = FastAPI()
    app.add_middleware(
        SecurityHeadersMiddleware,
        server_name="TestServer",
        content_security_policy={
            "script-src": ["'self'", "example.com"]
        }
    )
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the app with security headers"""
    return TestClient(test_app)

def test_default_security_headers(test_client):
    """Test that default security headers are set correctly"""
    response = test_client.get("/test")
    assert response.status_code == 200
    
    # Check for required security headers
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"
    
    assert "X-XSS-Protection" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    assert "Referrer-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    assert "X-Permitted-Cross-Domain-Policies" in response.headers
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    
    assert "Server" in response.headers
    assert response.headers["Server"] == "TestServer"
    
    assert "X-Content-Security-Policy" in response.headers

def test_content_security_policy(test_client):
    """Test that Content-Security-Policy header is set correctly"""
    response = test_client.get("/test")
    assert response.status_code == 200
    
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    
    # Check for default-src directive
    assert "default-src 'self'" in csp
    
    # Check for script-src directive with custom domain
    assert "script-src 'self' example.com" in csp
    
    # Check for other CSP directives
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp

def test_hsts_header_in_production():
    """Test that HSTS header is set in production environment"""
    settings = get_settings()
    
    # Create a test app with production settings
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(settings, "ENVIRONMENT", "production")
        
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
        assert "preload" in response.headers["Strict-Transport-Security"]

def test_custom_headers():
    """Test that custom headers can be set"""
    app = FastAPI()
    app.add_middleware(
        SecurityHeadersMiddleware,
        custom_headers={
            "X-Custom-Header": "CustomValue",
            "X-API-Version": "1.0"
        }
    )
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 200
    assert "X-Custom-Header" in response.headers
    assert response.headers["X-Custom-Header"] == "CustomValue"
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "1.0"
