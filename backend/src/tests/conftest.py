import pytest
import os
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis
from unittest.mock import patch, MagicMock
from ..core.database import Base, get_db
from ..core.config import get_settings, Settings
from ..main import create_app

# Test settings override
model_config = {"extra": "ignore"}
@pytest.fixture(scope="session")
def test_settings():
    """Override application settings for testing"""
    return Settings(
        ENVIRONMENT="test",
        DEBUG=True,
        POSTGRES_SERVER="test_server",
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_DB="test_db",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/1",  # Use different DB for testing
        SECRET_KEY="test_secret_key",
        RATE_LIMIT_WINDOW=1,
        RATE_LIMIT_MAX_REQUESTS=5,
        GOOGLE_CLOUD_PROJECT="test-project",  # Mock project ID for testing
        SECRET_NAME="test-secret",  # Mock secret name for testing
        GCS_BUCKET_NAME="test-bucket"  # Mock bucket name for testing
    )

# Override config settings and environment variables
@pytest.fixture(scope="session", autouse=True)
def override_settings(test_settings):
    # Set environment variable for test environment
    os.environ["ENVIRONMENT"] = "test"

    # Mock get_settings to return our test settings
    with patch("src.core.config.get_settings", return_value=test_settings):
        # Mock the settings object that might already be initialized
        with patch("src.core.config.settings", test_settings):
            yield

# In-memory SQLite database for testing
@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create a test database session
    db = TestingSessionLocal()

    # Override get_db function to use our test database
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    # Yield the override function
    yield override_get_db

    # Teardown: drop all tables
    Base.metadata.drop_all(bind=engine)

# Test file storage fixture
@pytest.fixture(scope="function")
def test_file_storage():
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    upload_dir = os.path.join(temp_dir, "uploads")
    temp_dir = os.path.join(temp_dir, "temp")

    # Create directories
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    yield {
        "base_dir": temp_dir,
        "upload_dir": upload_dir,
        "temp_dir": temp_dir
    }

    # Cleanup after tests
    shutil.rmtree(temp_dir, ignore_errors=True)

# Mock Redis fixture
@pytest.fixture(scope="function")
def mock_redis():
    mock = MagicMock(spec=redis.Redis)
    with patch("src.core.middleware.get_redis_client", return_value=mock):
        yield mock

# Mock Celery fixture
@pytest.fixture(scope="function")
def mock_celery_app():
    mock = MagicMock()
    with patch("src.core.celery.celery", mock):
        yield mock

# Mock task fixtures
@pytest.fixture(scope="function")
def mock_image_task():
    mock = MagicMock()
    mock.delay.return_value = MagicMock(id="test_task_id")
    with patch("src.tasks.image_tasks.generate_image_task", mock):
        yield mock

@pytest.fixture(scope="function")
def mock_video_task():
    mock = MagicMock()
    mock.delay.return_value = MagicMock(id="test_task_id")
    with patch("src.tasks.video_tasks.generate_video_task", mock):
        yield mock

@pytest.fixture
def app(test_db):
    app = create_app()
    app.dependency_overrides[get_db] = test_db
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

# Auth token fixture
@pytest.fixture
def auth_token(client):
    # Create a test user and return a valid token
    response = client.post(
        "/api/v1/register",
        json={"email": "test@example.com", "password": "testpassword123"}
    )
    return response.json()["access_token"]