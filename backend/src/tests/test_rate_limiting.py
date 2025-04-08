import pytest
import time
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from ..core.middleware import RateLimitMiddleware
from ..core.config import get_settings

@pytest.fixture
def rate_limited_app():
    """Create a test app with rate limiting middleware"""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware)
    
    @app.get("/test-rate-limit")
    async def test_endpoint():
        return {"status": "success"}
    
    return app

@pytest.fixture
def rate_limit_client(rate_limited_app):
    """Create a test client for the rate limited app"""
    return TestClient(rate_limited_app)

def test_rate_limit_headers(rate_limit_client, test_settings):
    """Test that rate limit headers are included in responses"""
    response = rate_limit_client.get("/test-rate-limit")
    
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Verify the limit matches our test settings
    assert response.headers["X-RateLimit-Limit"] == str(test_settings.RATE_LIMIT_MAX_REQUESTS)
    
    # Check remaining is one less than the limit
    remaining = int(response.headers["X-RateLimit-Remaining"])
    assert remaining == test_settings.RATE_LIMIT_MAX_REQUESTS - 1

def test_rate_limit_enforcement(rate_limit_client, test_settings):
    """Test that rate limiting is enforced after exceeding the limit"""
    # Make requests up to the limit
    for _ in range(test_settings.RATE_LIMIT_MAX_REQUESTS):
        response = rate_limit_client.get("/test-rate-limit")
        assert response.status_code == 200
    
    # The next request should be rate limited
    response = rate_limit_client.get("/test-rate-limit")
    assert response.status_code == 429
    
    # Check error response format
    error_data = response.json()
    assert "error" in error_data
    assert error_data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "limit" in error_data["error"]["details"]
    assert "window_seconds" in error_data["error"]["details"]
    assert "reset_at" in error_data["error"]["details"]
    assert "retry_after" in error_data["error"]["details"]
    
    # Verify retry-after header
    assert "Retry-After" in response.headers

def test_rate_limit_reset(rate_limit_client, test_settings):
    """Test that rate limits reset after the window expires"""
    # Make requests up to the limit
    for _ in range(test_settings.RATE_LIMIT_MAX_REQUESTS):
        response = rate_limit_client.get("/test-rate-limit")
        assert response.status_code == 200
    
    # Verify we've hit the limit
    response = rate_limit_client.get("/test-rate-limit")
    assert response.status_code == 429
    
    # Wait for the rate limit window to expire
    time.sleep(test_settings.RATE_LIMIT_WINDOW + 1)
    
    # We should be able to make requests again
    response = rate_limit_client.get("/test-rate-limit")
    assert response.status_code == 200
    
    # And we should have a fresh limit
    remaining = int(response.headers["X-RateLimit-Remaining"])
    assert remaining == test_settings.RATE_LIMIT_MAX_REQUESTS - 1

def test_different_endpoints_separate_limits(rate_limited_app, test_settings):
    """Test that different endpoints have separate rate limits"""
    # Add a second endpoint
    @rate_limited_app.get("/another-endpoint")
    async def another_endpoint():
        return {"status": "success"}
    
    client = TestClient(rate_limited_app)
    
    # Use up the limit on the first endpoint
    for _ in range(test_settings.RATE_LIMIT_MAX_REQUESTS):
        response = client.get("/test-rate-limit")
        assert response.status_code == 200
    
    # First endpoint should be rate limited
    response = client.get("/test-rate-limit")
    assert response.status_code == 429
    
    # But the second endpoint should still be accessible
    response = client.get("/another-endpoint")
    assert response.status_code == 200
