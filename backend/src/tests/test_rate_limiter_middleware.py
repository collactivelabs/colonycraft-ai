"""
Tests for the rate limiter middleware with the enhanced TokenBucket
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request, Response, status
from fastapi.testclient import TestClient
from starlette.responses import PlainTextResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_200_OK

from src.core.middleware.rate_limit import RateLimitMiddleware
from src.core.security import TokenBucket

class CustomRateLimitMiddleware(RateLimitMiddleware):
    """Custom rate limit middleware with configurable token bucket"""
    
    def __init__(self, app: FastAPI, **kwargs):
        super().__init__(app)
        # Store custom parameters
        self.capacity = kwargs.get('capacity', 5)
        self.refill_rate = kwargs.get('refill_rate', 5/60)
        self.time_function = kwargs.get('time_function', datetime.now)
        
        # Override the token bucket with custom parameters
        self.token_bucket = TokenBucket(
            capacity=self.capacity,
            refill_rate=self.refill_rate,
            time_function=self.time_function
        )
    
    async def dispatch(self, request: Request, call_next):
        """Process the request with rate limiting"""
        # Get client identifier (e.g., IP address)
        client_id = self._get_client_id(request)
        
        # Check if the client has tokens available
        if not self.token_bucket.take(client_id):
            # If no tokens available, return 429 Too Many Requests
            return Response(
                content="Rate limit exceeded",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.capacity),
                    "X-RateLimit-Reset": str(int(self.token_bucket.get_next_refill_time(client_id)))
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to the response
        response.headers["X-RateLimit-Limit"] = str(self.capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(self.token_bucket.get_tokens(client_id)))
        response.headers["X-RateLimit-Reset"] = str(int(self.token_bucket.get_next_refill_time(client_id)))
        
        return response

def create_test_app(**kwargs):
    """Create a test FastAPI app with custom rate limiter middleware"""
    app = FastAPI()
    
    # Add a test endpoint
    @app.get("/test")
    def test_endpoint():
        return PlainTextResponse("OK")
    
    # Add custom rate limiter middleware with test settings
    app.add_middleware(CustomRateLimitMiddleware, **kwargs)
    
    return app

class TestRateLimiterMiddleware:
    def test_rate_limit_not_exceeded(self):
        """Test that requests below the rate limit succeed"""
        # Create app with controlled parameters
        app = create_test_app(capacity=5, refill_rate=5/60)
        client = TestClient(app)
        
        # Make 5 requests (the limit)
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == HTTP_200_OK
            
        # Check rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert int(response.headers["X-RateLimit-Limit"]) == 5
        # Remaining should be 0 after making all 5 requests
        assert int(response.headers["X-RateLimit-Remaining"]) == 0
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding the rate limit are rejected"""
        # Create app with controlled parameters
        app = create_test_app(capacity=5, refill_rate=5/60)
        client = TestClient(app)
        
        # Make 5 requests (the limit)
        for _ in range(5):
            response = client.get("/test")
            assert response.status_code == HTTP_200_OK
        
        # The 6th request should be rejected
        response = client.get("/test")
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response.headers
        
        # Check the response body
        assert response.text == "Rate limit exceeded"
    
    def test_time_function_usage(self):
        """Test that TokenBucket is initialized with expected parameters"""
        # Create a mock time function
        mock_time = MagicMock()
        mock_time.return_value = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Create app with mocked time function
        app = create_test_app(capacity=5, refill_rate=5/60, time_function=mock_time)
        client = TestClient(app)
        
        # Make a request to trigger the token bucket
        client.get("/test")
        
        # Verify the time function was called
        mock_time.assert_called()
        
    def test_direct_token_bucket_refill(self):
        """Test the TokenBucket refill mechanism directly"""
        # Initialize with a fixed time function
        current_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        def time_fn():
            nonlocal current_time
            return current_time
            
        # Create a token bucket directly (bypass middleware for this test)
        bucket = TokenBucket(capacity=5, refill_rate=5/60, time_function=time_fn)
        client_id = "test-client"
        
        # Initially we have 5 tokens
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        
        # Now we're out of tokens
        assert bucket.take(client_id) is False
        
        # Advance time by 60 seconds (should refill 5 tokens)
        current_time += timedelta(seconds=60)
        
        # We should now have tokens again
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        assert bucket.take(client_id) is True
        
        # Should be empty again
        assert bucket.take(client_id) is False
