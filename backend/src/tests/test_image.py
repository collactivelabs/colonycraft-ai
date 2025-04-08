import pytest
from fastapi.testclient import TestClient
from ..main import app
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from ..core.database import get_db, Base, engine
from src.services.image_service import ImageService

client = TestClient(app)

@pytest.fixture(scope="session")
def test_client():
    return TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def api_key_header():
    return {"X-API-Key": "test-api-key"}  # Updated header name to match middleware

@pytest.fixture
def test_image_data():
    return {
        "prompt": "a beautiful sunset over mountains",
        "n_images": 1,
        "size": "512x512"
    }

@pytest.fixture
def image_service():
    return ImageService()

class TestImageService:
    def test_generate_image_success(self, image_service):
        with patch('src.services.image_service.StableDiffusionPipeline') as mock_pipeline:
            mock_pipeline.return_value.generate.return_value = Mock(images=[Mock()])
            result = image_service.generate_image("test prompt")
            assert result is not None

    def test_generate_image_failure(self, image_service):
        with patch('src.services.image_service.StableDiffusionPipeline') as mock_pipeline:
            mock_pipeline.side_effect = Exception("Pipeline error")
            with pytest.raises(Exception):
                image_service.generate_image("test prompt")

@pytest.fixture(autouse=True)
def mock_google_cloud():
    with patch('google.cloud.secretmanager_v1.SecretManagerServiceClient') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.access_secret_version.return_value.payload.data.decode.return_value = "test-api-key"
        yield mock_client

def test_generate_image(test_image_data, api_key_header):
    response = client.post(
        "/api/v1/images/generate",
        json=test_image_data,
        headers=api_key_header
    )
    assert response.status_code == 200
    assert "images" in response.json()
    assert isinstance(response.json()["images"], list)
    assert len(response.json()["images"]) == test_image_data["n_images"]

def test_generate_image_without_api_key(test_image_data):
    response = client.post("/api/v1/images/generate", json=test_image_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "API Key is missing"

def test_generate_image_invalid_api_key(test_image_data):
    headers = {"X-API-Key": "invalid-key"}
    response = client.post(
        "/api/v1/images/generate",
        json=test_image_data,
        headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid API Key"

def test_generate_image_invalid_prompt(api_key_header):
    invalid_data = {
        "prompt": "",  # Empty prompt
        "n_images": 1,
        "size": "512x512"
    }
    response = client.post(
        "/api/v1/images/generate",
        json=invalid_data,
        headers=api_key_header
    )
    assert response.status_code == 400

def test_generate_image_invalid_size(api_key_header):
    invalid_data = {
        "prompt": "a beautiful sunset",
        "n_images": 1,
        "size": "invalid_size"  # Invalid size
    }
    response = client.post(
        "/api/v1/images/generate",
        json=invalid_data,
        headers=api_key_header
    )
    assert response.status_code == 400

def test_generate_multiple_images(test_image_data, api_key_header):
    test_image_data["n_images"] = 2
    response = client.post(
        "/api/v1/images/generate",
        json=test_image_data,
        headers=api_key_header
    )
    assert response.status_code == 200
    assert len(response.json()["images"]) == 2
