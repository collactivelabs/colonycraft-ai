import pytest
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ..core.exceptions import (
    BaseAPIException,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    RateLimitExceededError,
    ProcessingError,
    QuotaExceededError,
    InvalidInputError,
    add_exception_handlers,
    format_error_response
)

# Test all exception classes
def test_base_api_exception():
    exc = BaseAPIException(
        message="Test error",
        status_code=500,
        error_code="TEST_ERROR",
        details={"test": "detail"}
    )
    assert exc.message == "Test error"
    assert exc.status_code == 500
    assert exc.error_code == "TEST_ERROR"
    assert exc.details == {"test": "detail"}

def test_validation_error():
    exc = ValidationError(
        message="Validation failed",
        details={"field": "email", "error": "Invalid email format"}
    )
    assert exc.message == "Validation failed"
    assert exc.status_code == 400
    assert exc.error_code == "VALIDATION_ERROR"
    assert "field" in exc.details
    assert "error" in exc.details

def test_authentication_error():
    exc = AuthenticationError()
    assert exc.message == "Authentication failed"
    assert exc.status_code == 401
    assert exc.error_code == "AUTHENTICATION_ERROR"
    
    exc = AuthenticationError(message="Custom auth error")
    assert exc.message == "Custom auth error"

def test_authorization_error():
    exc = AuthorizationError()
    assert exc.message == "Not authorized"
    assert exc.status_code == 403
    assert exc.error_code == "AUTHORIZATION_ERROR"

def test_resource_not_found_error():
    exc = ResourceNotFoundError(resource_type="User", resource_id="123")
    assert exc.message == "User with id 123 not found"
    assert exc.status_code == 404
    assert exc.error_code == "RESOURCE_NOT_FOUND"
    assert exc.details["resource_type"] == "User"
    assert exc.details["resource_id"] == "123"

def test_database_error():
    exc = DatabaseError(message="DB connection failed")
    assert exc.message == "DB connection failed"
    assert exc.status_code == 500
    assert exc.error_code == "DATABASE_ERROR"
    assert "timestamp" in exc.details

def test_rate_limit_exceeded_error():
    reset_at = datetime.utcnow() + timedelta(seconds=60)
    exc = RateLimitExceededError(limit=100, window=60, reset_at=reset_at)
    assert "Rate limit exceeded" in exc.message
    assert exc.status_code == 429
    assert exc.error_code == "RATE_LIMIT_EXCEEDED"
    assert exc.details["limit"] == 100
    assert exc.details["window_seconds"] == 60
    assert "reset_at" in exc.details
    assert "retry_after" in exc.details

def test_processing_error():
    exc = ProcessingError(
        message="Image processing failed",
        task_id="task123",
        details={"reason": "Out of memory"}
    )
    assert exc.message == "Image processing failed"
    assert exc.status_code == 500
    assert exc.error_code == "PROCESSING_ERROR"
    assert exc.details["task_id"] == "task123"
    assert exc.details["reason"] == "Out of memory"

def test_quota_exceeded_error():
    exc = QuotaExceededError(
        quota_type="api_calls",
        limit=1000,
        usage=1001,
        user_id="user123"
    )
    assert "Quota exceeded for api_calls" in exc.message
    assert exc.status_code == 402
    assert exc.error_code == "QUOTA_EXCEEDED"
    assert exc.details["quota_type"] == "api_calls"
    assert exc.details["limit"] == 1000
    assert exc.details["current_usage"] == 1001
    assert exc.details["user_id"] == "user123"

def test_invalid_input_error():
    exc = InvalidInputError(
        message="Invalid prompt",
        field="prompt",
        details={"reason": "Contains prohibited content"}
    )
    assert exc.message == "Invalid prompt"
    assert exc.status_code == 400
    assert exc.error_code == "INVALID_INPUT"
    assert exc.details["field"] == "prompt"
    assert exc.details["reason"] == "Contains prohibited content"

# Test error response formatting
def test_format_error_response():
    exc = ValidationError(
        message="Validation failed",
        details={"field": "email", "error": "Invalid email format"}
    )
    response = format_error_response(exc)
    
    assert "error" in response
    assert response["error"]["code"] == "VALIDATION_ERROR"
    assert response["error"]["message"] == "Validation failed"
    assert response["error"]["status_code"] == 400
    assert "timestamp" in response["error"]
    assert "details" in response["error"]
    assert response["error"]["details"]["field"] == "email"

# Test exception handlers with FastAPI
@pytest.fixture
def test_app():
    app = FastAPI()
    add_exception_handlers(app)
    
    @app.get("/test-error")
    async def test_error():
        raise ValidationError(
            message="Test validation error",
            details={"field": "test"}
        )
    
    return app

def test_exception_handler(test_app, client):
    # Override the client fixture to use our test_app
    client = TestClient(test_app)
    
    response = client.get("/test-error")
    assert response.status_code == 400
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Test validation error"
    assert data["error"]["details"]["field"] == "test"

# Import for the FastAPI test client
from fastapi.testclient import TestClient
