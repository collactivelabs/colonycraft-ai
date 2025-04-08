import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, UTC

from starlette.middleware import Middleware
from src.core.middleware.api_key_warning import APIKeyWarningMiddleware


@pytest.fixture
def test_app():
    """Create a test FastAPI app with the warning middleware"""
    app = FastAPI()
    
    # Add middleware
    app.add_middleware(APIKeyWarningMiddleware)
    
    # Create test endpoints
    @app.get("/test")
    async def test_endpoint(request: Request):
        # Set rotated API key state for testing
        request.state.api_key_rotated = True
        request.state.api_key_expiry = datetime.now(UTC) + timedelta(days=5)
        request.state.new_key_prefix = "newkey123"
        return {"message": "Test endpoint"}
    
    @app.get("/test-critical")
    async def test_critical_endpoint(request: Request):
        # Set rotated API key state with urgent expiry
        request.state.api_key_rotated = True
        request.state.api_key_expiry = datetime.now(UTC) + timedelta(hours=12)
        request.state.new_key_prefix = "newkey456"
        return {"message": "Test critical endpoint"}
    
    @app.get("/test-normal")
    async def test_normal_endpoint(request: Request):
        # No rotated API key state
        return {"message": "Normal endpoint"}
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the app"""
    return TestClient(test_app)


def test_warning_headers_for_rotated_key(client):
    """Test that warning headers are added for rotated API keys"""
    response = client.get("/test")
    
    # Check warning header exists
    assert "Warning" in response.headers
    assert "API key is deprecated" in response.headers["Warning"]
    
    # Check custom headers
    assert "X-API-Key-Expiry" in response.headers
    assert "X-API-Key-Replacement-Prefix" in response.headers
    assert response.headers["X-API-Key-Replacement-Prefix"] == "newkey123"
    
    # Check documentation link
    assert "Link" in response.headers
    assert "API Key Rotation Guide" in response.headers["Link"]


def test_critical_warning_headers(client):
    """Test critical warning headers for soon-to-expire keys"""
    response = client.get("/test-critical")
    
    # Check urgent warning message
    assert "Warning" in response.headers
    assert "URGENT: API key expires in less than 24 hours" in response.headers["Warning"]


def test_no_warning_headers_for_normal_requests(client):
    """Test that no warning headers are added for normal requests"""
    response = client.get("/test-normal")
    
    # Check no warning headers
    assert "Warning" not in response.headers
    assert "X-API-Key-Expiry" not in response.headers
    assert "X-API-Key-Replacement-Prefix" not in response.headers
