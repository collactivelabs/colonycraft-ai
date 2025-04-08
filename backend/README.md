# ColonyCraft API Documentation

## Overview

ColonyCraft is a powerful SaaS API for image and video generation using AI models. It provides a robust, scalable backend service with features like authentication, rate limiting, asynchronous task processing, and more.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Configuration](#configuration)
5. [Task Queue System](#task-queue-system)
6. [Development](#development)
7. [Deployment](#deployment)

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- Google Cloud Storage (for production)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/saas-api.git
   cd saas-api
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying `.env.example` to `.env` and updating values:
   ```bash
   cp .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn src.main:app --reload
   ```

5. Start the Celery worker:
   ```bash
   celery -A src.core.celery:celery worker --loglevel=info
   ```

## Authentication

### Register User
- **Endpoint**: POST /api/v1/register
- **Description**: Create a new user account
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```

### Login
- **Endpoint**: POST /api/v1/login
- **Description**: Authenticate a user and get access token
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```

## API Endpoints

### Image Generation
- **Endpoint**: POST /api/v1/image/generate
- **Authentication**: Required
- **Description**: Generate images using AI models

### Video Generation
- **Endpoint**: POST /api/v1/video/generate
- **Authentication**: Required
- **Description**: Generate videos using AI models

### Files Management
- **Endpoint**: POST /api/v1/files/upload
- **Authentication**: Required
- **Description**: Upload files to storage

## Configuration

The application uses a robust configuration system based on Pydantic settings:

```python
# src/core/config.py (simplified)
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Basic Settings
    PROJECT_NAME: str = "ColonyCraft API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database settings
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Redis and Celery
    REDIS_URL: str

    # AI Services
    STABLE_DIFFUSION_MODEL: str

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Environment Variables

Create a `.env` file with the following variables:

```
# Basic
ENVIRONMENT=development
DEBUG=true

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=colonycraft

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
SECRET_KEY=your-secure-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Services
STABLE_DIFFUSION_MODEL=stabilityai/stable-diffusion-2-1
GCP_BUCKET_NAME=your-bucket-name
```

## Task Queue System

The application uses Celery for asynchronous task processing:

- **Image Generation**: Processes image generation requests
- **Video Generation**: Handles video creation tasks
- **Maintenance**: Performs scheduled cleanup and maintenance tasks

## Development

### Project Structure

```
src/
├── api/             # API routes and endpoints
│   └── v1/          # Version 1 API endpoints
├── core/            # Core functionality
│   ├── celery.py    # Celery configuration
│   ├── config.py    # Application configuration
│   └── metrics.py   # Prometheus metrics
├── models/          # Database models
├── schemas/         # Pydantic schemas
├── services/        # Business logic services
├── tasks/           # Celery tasks
└── main.py          # Application entry point
```

## Deployment

### Docker

Build and run the Docker container:

```bash
docker build -t colonycraft-api .
docker run -p 8000:8000 --env-file .env colonycraft-api
```