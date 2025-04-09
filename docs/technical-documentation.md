# Technical Documentation

## Backend API (FastAPI)

### Overview

The backend API is built with FastAPI, a modern Python web framework optimized for building high-performance APIs with type checking and automatic API documentation. The backend serves as the central hub for authentication, authorization, and access to multiple LLM providers.

### Project Structure

```
backend/
├── src/
│   ├── api/                 # API endpoints and routes
│   │   └── v1/              # API version 1
│   │       ├── endpoints/   # API endpoint modules
│   │       └── api_keys.py  # API key management
│   ├── core/                # Core functionality and middleware
│   │   ├── auth.py          # Authentication logic
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database connection
│   │   ├── exceptions.py    # Custom exceptions
│   │   ├── middleware/      # Middleware components
│   │   ├── metrics.py       # Metrics collection
│   │   └── security.py      # Security features
│   ├── crud/                # Database operations
│   ├── models/              # Database models (SQLAlchemy)
│   ├── routers/             # Additional route handlers
│   ├── schemas/             # Pydantic models for validation
│   ├── services/            # Business logic services
│   │   └── llm/             # LLM provider services
│   │       ├── anthropic.py # Anthropic API integration
│   │       ├── base.py      # Base LLM service interfaces
│   │       └── openai.py    # OpenAI API integration
│   ├── tasks/               # Background tasks
│   └── main.py              # Application entry point
├── tests/                   # Unit and integration tests
└── requirements.txt         # Python dependencies
```

### Key Components

#### API Endpoints

- **Auth**: User registration, login, and password management
- **LLM**: Unified API for multiple LLM providers
- **API Keys**: Generation and management of API keys
- **Files**: File upload and management
- **Image**: Image generation and manipulation
- **Video**: Video processing capabilities

#### Middleware

- **APIKeyMiddleware**: Authenticates requests with API key
- **DatabaseSessionMiddleware**: Manages database sessions
- **RateLimitMiddleware**: Implements token bucket algorithm for rate limiting
- **RequestLoggingMiddleware**: Logs request details for monitoring
- **RequestValidationMiddleware**: Validates incoming requests
- **SecurityHeadersMiddleware**: Adds security headers to responses
- **RequestContextMiddleware**: Stores request context for access in dependencies

#### LLM Service Factory

The LLM integration follows the Factory pattern to dynamically load and instantiate the appropriate service for each provider:

```python
class LLMServiceFactory:
    @staticmethod
    def get_service(provider: str) -> LLMService:
        if provider == "openai":
            return OpenAIService()
        elif provider == "anthropic":
            return AnthropicService()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
```

Each provider-specific service implements the common `LLMService` interface, ensuring consistent behavior across providers.

### Authentication Flow

1. User registers or logs in via the `/api/v1/auth/register` or `/api/v1/auth/login` endpoints
2. Server validates credentials and generates JWT access and refresh tokens
3. Client includes the access token in the `Authorization` header for subsequent requests
4. When the access token expires, client uses the refresh token to obtain a new access token
5. For API key access, client includes the API key in the `X-API-Key` header

### Rate Limiting

Rate limiting is implemented using a token bucket algorithm. Each user has a bucket with:

- A maximum capacity of tokens
- A refill rate (tokens per second)
- The current token count

Requests consume tokens based on their complexity. If a user's bucket has insufficient tokens, the request is rejected with a 429 Too Many Requests status code.

## Firebase Functions

### Overview

Firebase Cloud Functions provide a secure, serverless interface for client-side LLM access. These functions act as proxies to various LLM providers, validating client tokens and forwarding requests to the appropriate API.

### Project Structure

```
firebase-functions/
├── functions/
│   ├── src/                # TypeScript source files
│   ├── lib/                # Compiled JavaScript
│   ├── index.js            # Function definitions
│   ├── package.json        # Node.js dependencies
│   └── tsconfig.json       # TypeScript configuration
├── .firebaserc             # Firebase project configuration
└── firebase.json           # Firebase deployment configuration
```

### Key Functions

- **anthropicGenerate**: Proxies requests to Anthropic's Claude API
- **openaiGenerate**: Proxies requests to OpenAI's GPT API
- **listProviders**: Returns available LLM providers and models

### Authentication Flow

1. Client obtains a client token from the backend API
2. Client includes the token in the `Authorization` header when calling Firebase Functions
3. Function validates the token using the shared secret key
4. If valid, the function forwards the request to the appropriate LLM provider
5. Response is returned to the client

### Error Handling

Each function includes comprehensive error handling:

- Validation errors (400 Bad Request)
- Authentication errors (401 Unauthorized)
- Rate limiting errors (429 Too Many Requests)
- Server errors (500 Internal Server Error)

Error responses include detailed error messages and appropriate status codes.

## Frontend (React)

### Overview

The frontend is built with React, providing a responsive and intuitive user interface for interacting with LLMs through the backend API and Firebase Functions.

### Project Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── components/     # React components
│   │   ├── auth/       # Authentication components
│   │   └── layout/     # Layout components
│   ├── styles/         # CSS styles
│   ├── index.js        # Application entry point
│   └── index.css       # Global styles
├── package.json        # Node.js dependencies
└── nginx.conf          # Nginx configuration for production
```

### Key Components

- **App**: Main application component managing state and routing
- **AuthContainer**: Handles user authentication and registration
- **ModelSelector**: Displays available LLM providers and models
- **PromptInput**: Captures user prompts and handles form submission
- **ResponseDisplay**: Renders LLM responses with metadata

### Authentication Flow

1. User enters credentials in the login or registration form
2. Form submits credentials to the backend API
3. On successful authentication, the API returns a JWT token
4. Token is stored in localStorage for persistence across sessions
5. Subsequent requests include the token in the Authorization header
6. Token is refreshed automatically when approaching expiration

### API Integration

The frontend communicates with both the backend API and Firebase Functions:

- Backend API: User authentication and management
- Firebase Functions: LLM interaction

```javascript
// Example of calling a Firebase Function
const generateResponse = async () => {
  // Ensure valid token
  const token = await ensureValidToken();
  
  // Determine function URL based on provider
  let functionUrl;
  if (selectedProvider === 'anthropic') {
    functionUrl = `${FIREBASE_FUNCTIONS_URL}/anthropicGenerate`;
  } else if (selectedProvider === 'openai') {
    functionUrl = `${FIREBASE_FUNCTIONS_URL}/openaiGenerate`;
  }
  
  // Make request to Firebase Function
  const response = await axios.post(
    functionUrl,
    {
      model: selectedModel,
      prompt: prompt,
      maxTokens: 1024,
      temperature: 0.7
    },
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  setResponse(response.data);
};
```

## Database Schema

### Core Tables

#### Users
- id (UUID, primary key)
- email (string, unique)
- password_hash (string)
- is_active (boolean)
- is_verified (boolean)
- created_at (timestamp)
- updated_at (timestamp)

#### APIKeys
- id (UUID, primary key)
- key (string, unique)
- user_id (UUID, foreign key to Users)
- name (string)
- scopes (array of strings)
- expires_at (timestamp)
- created_at (timestamp)
- last_used_at (timestamp)

#### UsageMetrics
- id (UUID, primary key)
- user_id (UUID, foreign key to Users)
- api_key_id (UUID, foreign key to APIKeys)
- provider (string)
- model (string)
- input_tokens (integer)
- output_tokens (integer)
- cost (decimal)
- timestamp (timestamp)

#### RateLimitBuckets
- id (UUID, primary key)
- user_id (UUID, foreign key to Users)
- tokens (decimal)
- last_refill (timestamp)
- updated_at (timestamp)

## API Endpoints

### Authentication

- **POST /api/v1/auth/register**: Register a new user
- **POST /api/v1/auth/login**: Authenticate and get tokens
- **POST /api/v1/auth/refresh**: Refresh access token
- **POST /api/v1/auth/reset-password**: Request password reset
- **POST /api/v1/auth/reset-password-confirm**: Confirm password reset
- **POST /api/v1/auth/client-token**: Get client token for Firebase Functions

### LLM Interaction

- **POST /api/v1/llm/generate**: Generate LLM response
- **GET /api/v1/llm/providers**: List available LLM providers and models

### API Key Management

- **GET /api/v1/api-keys**: List user's API keys
- **POST /api/v1/api-keys**: Create new API key
- **DELETE /api/v1/api-keys/{key_id}**: Delete API key
- **PATCH /api/v1/api-keys/{key_id}**: Update API key

## Security Considerations

### API Key Security

- Keys are stored using secure hashing (bcrypt)
- Keys are transmitted over HTTPS only
- Keys can be scoped to specific operations
- Automatic key rotation is supported
- Usage auditing for all key operations

### Rate Limiting

The token bucket algorithm prevents abuse by:

- Limiting the number of requests per time period
- Allowing bursts of traffic up to a defined limit
- Providing clear feedback on rate limits via headers
- Supporting different rate limits for different user tiers

### Data Protection

- Authentication credentials are never stored in plaintext
- LLM provider API keys are stored securely in environment variables
- All API requests require authentication
- CORS policies restrict access to approved origins
- Security headers prevent common web vulnerabilities

## Testing

### Unit Tests

Unit tests cover core functionality:

- Authentication flows
- Rate limiting logic
- LLM service integration
- API key validation

### Integration Tests

Integration tests verify end-to-end functionality:

- User registration and login
- API key management
- LLM request handling

### Load Testing

Load tests ensure system stability under stress:

- Concurrent user simulation
- High-volume request handling
- Rate limiting effectiveness

## Extending the System

### Adding a New LLM Provider

1. Create a new service class implementing the `LLMService` interface
2. Add the provider to the `LLMServiceFactory` class
3. Create a corresponding Firebase Function for client-side access
4. Update the provider list in the frontend

### Implementing a New Feature

1. Define the feature requirements and API contract
2. Add necessary database models and schemas
3. Implement the service layer logic
4. Create API endpoints in the appropriate router
5. Add corresponding UI components in the frontend
6. Write tests to verify functionality
