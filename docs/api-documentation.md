# API Documentation

## Overview

The ColonyCraft AI API provides a unified interface for interacting with multiple Large Language Models (LLMs). This document outlines the available endpoints, authentication mechanisms, and examples of API usage.

## Base URL

- **Development**: `http://localhost:8000`
- **Staging**: `https://staging-api.colonycraft.ai`
- **Production**: `https://api.colonycraft.ai`

## Authentication

The API supports two authentication methods:

### JWT Authentication

Used for authenticating users directly.

1. Obtain a token by logging in via the `/api/v1/auth/login` endpoint
2. Include the token in the `Authorization` header of subsequent requests:
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### API Key Authentication

Used for programmatic access.

1. Generate an API key in the user dashboard
2. Include the key in the `X-API-Key` header:
   ```
   X-API-Key: apk_12345abcdef67890...
   ```

## Rate Limiting

The API implements rate limiting using a token bucket algorithm. Rate limits are applied per user or API key.

- Default rate: 60 requests per minute
- Response headers include rate limit information:
  - `X-RateLimit-Limit`: Maximum requests per minute
  - `X-RateLimit-Remaining`: Remaining requests in the current window
  - `X-RateLimit-Reset`: Seconds until the rate limit resets

When rate limits are exceeded, the API returns a `429 Too Many Requests` response.

## Endpoints

### Authentication

#### Register a new user

```
POST /api/v1/auth/register
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "name": "John Doe"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2023-04-01T12:00:00Z"
}
```

#### Log in

```
POST /api/v1/auth/login
```

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "securePassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": 1680357600
}
```

#### Refresh token

```
POST /api/v1/auth/refresh
```

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": 1680361200
}
```

#### Get client token for Firebase Functions

```
POST /api/v1/auth/client-token
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": 1680358500
}
```

### LLM Interaction

#### Generate LLM Response

```
POST /api/v1/llm/generate
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**:
```json
{
  "provider": "anthropic",
  "model": "claude-3-sonnet-20240229",
  "prompt": "Explain the difference between a transformer and a recurrent neural network.",
  "options": {
    "temperature": 0.7,
    "max_tokens": 1024
  }
}
```

**Response** (200 OK):
```json
{
  "text": "Transformers and recurrent neural networks (RNNs) are both sequence processing architectures...",
  "model_info": {
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "version": "latest"
  },
  "metadata": {
    "usage": {
      "input_tokens": 14,
      "output_tokens": 542
    },
    "id": "msg_01234567890abcdef"
  }
}
```

#### List Available LLM Providers

```
GET /api/v1/llm/providers
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
[
  {
    "name": "anthropic",
    "models": [
      {
        "id": "claude-3-haiku-20240307",
        "name": "Claude 3 Haiku",
        "provider": "anthropic",
        "description": "Fastest and most compact Claude model"
      },
      {
        "id": "claude-3-sonnet-20240229",
        "name": "Claude 3 Sonnet",
        "provider": "anthropic",
        "description": "Balanced model for most tasks"
      },
      {
        "id": "claude-3-opus-20240229",
        "name": "Claude 3 Opus",
        "provider": "anthropic",
        "description": "Most powerful Claude model for complex tasks"
      }
    ]
  },
  {
    "name": "openai",
    "models": [
      {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "openai",
        "description": "Most capable GPT-4o model"
      },
      {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "provider": "openai",
        "description": "More efficient version of GPT-4"
      },
      {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "provider": "openai",
        "description": "Efficient model balancing cost and capability"
      }
    ]
  }
]
```

### API Key Management

#### List User's API Keys

```
GET /api/v1/api-keys
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (200 OK):
```json
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440000",
    "name": "Development Key",
    "scopes": ["read:llm", "write:llm"],
    "expires_at": "2024-04-01T12:00:00Z",
    "created_at": "2023-04-01T12:00:00Z",
    "last_used_at": "2023-04-02T15:30:00Z"
  },
  {
    "id": "750e8400-e29b-41d4-a716-446655440000",
    "name": "Production Key",
    "scopes": ["read:llm", "write:llm", "read:file", "write:file"],
    "expires_at": "2025-04-01T12:00:00Z",
    "created_at": "2023-04-01T12:00:00Z",
    "last_used_at": null
  }
]
```

#### Create API Key

```
POST /api/v1/api-keys
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body**:
```json
{
  "name": "Production Key",
  "scopes": ["read:llm", "write:llm", "read:file", "write:file"],
  "expires_at": "2025-04-01T12:00:00Z"
}
```

**Response** (201 Created):
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440000",
  "key": "apk_12345abcdefghijklmnopqrstuvwxyz", // Only shown once
  "name": "Production Key",
  "scopes": ["read:llm", "write:llm", "read:file", "write:file"],
  "expires_at": "2025-04-01T12:00:00Z",
  "created_at": "2023-04-01T12:00:00Z",
  "last_used_at": null
}
```

#### Delete API Key

```
DELETE /api/v1/api-keys/{key_id}
```

**Headers**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response** (204 No Content)

## Error Responses

The API uses standard HTTP status codes and returns error details in the response body:

```json
{
  "error": "Invalid credentials",
  "detail": "Incorrect email or password",
  "status_code": 401
}
```

Common error codes:

- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side error

## Versioning

The API uses URL versioning with the pattern `/api/v{version_number}/...`

- Current stable version: v1
- Testing version: v2 (if applicable)

## CORS

Cross-Origin Resource Sharing is enabled for the following origins:
- `http://localhost:3000`
- `http://localhost:3006`
- `https://colonycraft.ai`
- `https://www.colonycraft.ai`
- `https://staging.colonycraft.ai`

## SDK Examples

### Python

```python
import requests

class ColonyCraftClient:
    def __init__(self, api_key=None, access_token=None, base_url="https://api.colonycraft.ai"):
        self.base_url = base_url
        self.api_key = api_key
        self.access_token = access_token
        
    def authenticate(self, email, password):
        """Authenticate using email and password"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        return data
    
    def _get_headers(self):
        """Create headers based on authentication method"""
        if self.api_key:
            return {"X-API-Key": self.api_key}
        elif self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        raise ValueError("No authentication method provided")
    
    def generate_response(self, provider, model, prompt, options=None):
        """Generate a response from an LLM"""
        headers = self._get_headers()
        payload = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "options": options or {}
        }
        response = requests.post(
            f"{self.base_url}/api/v1/llm/generate",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def list_providers(self):
        """List available LLM providers"""
        headers = self._get_headers()
        response = requests.get(
            f"{self.base_url}/api/v1/llm/providers",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

# Example usage
client = ColonyCraftClient(api_key="apk_12345abcdefghijklmnopqrstuvwxyz")
response = client.generate_response(
    provider="anthropic",
    model="claude-3-sonnet-20240229",
    prompt="What is machine learning?",
    options={"temperature": 0.7, "max_tokens": 500}
)
print(response["text"])
```

### JavaScript

```javascript
class ColonyCraftClient {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || 'https://api.colonycraft.ai';
    this.apiKey = options.apiKey;
    this.accessToken = options.accessToken;
  }
  
  async authenticate(email, password) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: email,
        password: password
      })
    });
    
    if (!response.ok) {
      throw new Error(`Authentication failed: ${response.status}`);
    }
    
    const data = await response.json();
    this.accessToken = data.access_token;
    return data;
  }
  
  getHeaders() {
    if (this.apiKey) {
      return {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json'
      };
    } else if (this.accessToken) {
      return {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      };
    }
    throw new Error('No authentication method provided');
  }
  
  async generateResponse(provider, model, prompt, options = {}) {
    const response = await fetch(`${this.baseUrl}/api/v1/llm/generate`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        provider,
        model,
        prompt,
        options
      })
    });
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    
    return await response.json();
  }
  
  async listProviders() {
    const response = await fetch(`${this.baseUrl}/api/v1/llm/providers`, {
      headers: this.getHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }
    
    return await response.json();
  }
}

// Example usage
const client = new ColonyCraftClient({
  apiKey: 'apk_12345abcdefghijklmnopqrstuvwxyz'
});

client.generateResponse('anthropic', 'claude-3-sonnet-20240229', 'What is machine learning?', {
  temperature: 0.7,
  max_tokens: 500
})
  .then(response => console.log(response.text))
  .catch(error => console.error(error));
```

## Webhook Integration

ColonyCraft AI supports webhooks for event notifications. Configure webhooks in your user settings:

1. Go to the user dashboard
2. Navigate to Integrations > Webhooks
3. Add a new webhook URL and select events to subscribe to

Example webhook payload:

```json
{
  "event": "llm.response.generated",
  "timestamp": "2023-04-01T12:30:45Z",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "anthropic",
    "model": "claude-3-sonnet-20240229",
    "input_tokens": 20,
    "output_tokens": 350,
    "response_id": "resp_01234567890abcdef"
  }
}
```

## Support

For API support, please contact:
- Email: api-support@colonycraft.ai
- Documentation: https://docs.colonycraft.ai
- Status page: https://status.colonycraft.ai
