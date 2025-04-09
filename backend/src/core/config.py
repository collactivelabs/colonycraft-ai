from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import secrets
import json

class Settings(BaseSettings):
    # Basic Settings
    PROJECT_NAME: str = "ColonyCraftAPI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    SECRET_NAME: str = "colonycraft-api-key"
    API_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: List[str] = '["localhost", "127.0.0.1"]'
    ALLOWED_ORIGINS: List[str] = '["http://localhost:3006", "http://127.0.0.1:3006"]'

    # LLM Settings
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""  # Added for Gemini
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MISTRAL_API_BASE_URL: str = "https://api.mistral.ai/v1"

    # Google Cloud (Separate from Gemini API Key)
    GOOGLE_APPLICATION_CREDENTIALS: str = "${HOME}/.gcloud/keys/colonycraft-api.json"
    GOOGLE_CLOUD_PROJECT: str = ""
    GOOGLE_STORAGE_BUCKET: str = ""

    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 100

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "colonyCraft_apiUser"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "colonycraft_api"
    DATABASE_URL: str = ""

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # Services
    STABLE_DIFFUSION_MODEL: str = "stabilityai/stable-diffusion-2-1"
    GCP_BUCKET_NAME: str = ""
    GCS_BUCKET_NAME: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Python Path
    PYTHONPATH: str = ""

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Parse ALLOWED_HOSTS and ALLOWED_ORIGINS if they came as strings
        if isinstance(self.ALLOWED_HOSTS, str):
            try:
                self.ALLOWED_HOSTS = json.loads(self.ALLOWED_HOSTS)
            except json.JSONDecodeError:
                # Fallback to comma-separated format
                self.ALLOWED_HOSTS = [h.strip() for h in self.ALLOWED_HOSTS.replace('"', '').split(',')]

        if isinstance(self.ALLOWED_ORIGINS, str):
            try:
                self.ALLOWED_ORIGINS = json.loads(self.ALLOWED_ORIGINS)
            except json.JSONDecodeError:
                # Fallback to comma-separated format
                self.ALLOWED_ORIGINS = [o.strip() for o in self.ALLOWED_ORIGINS.replace('"', '').split(',')]

        # Set DATABASE_URL if not provided
        if not self.DATABASE_URL and self.POSTGRES_SERVER:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

        # Set Redis URL if not provided
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

        # Set Celery URLs if not provided
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL

        # Set Google Cloud credentials if not provided
        if self.ENVIRONMENT == "production" and not self.GOOGLE_APPLICATION_CREDENTIALS:
            self.GOOGLE_APPLICATION_CREDENTIALS = "/etc/secrets/gcp-credentials.json"

        # Extend allowed hosts and origins based on environment
        if self.ENVIRONMENT == "production":
            self.DEBUG = False
            self.ALLOWED_HOSTS.extend(["api.colonycraft.com"])
            self.ALLOWED_ORIGINS.extend(["https://colonycraft.com"])
        elif self.ENVIRONMENT == "staging":
            self.DEBUG = False
            self.ALLOWED_HOSTS.extend(["staging-api.colonycraft.com"])
            self.ALLOWED_ORIGINS.extend(["https://staging.colonycraft.com"])

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Create settings instance
settings = get_settings()