# ColonyCraft AI

A full-stack application that provides secure access to multiple Large Language Models (LLMs) through a unified API gateway.

## Project Overview

ColonyCraft AI offers a streamlined interface for interacting with various LLM providers including OpenAI and Anthropic. The application features secure authentication, API key management, rate limiting, and a modern React frontend.

## Architecture

The project consists of three main components:

1. **Backend API** - A FastAPI application that handles authentication, API key management, and direct LLM integration
2. **Firebase Functions** - Serverless functions for secure client-side LLM interactions
3. **Frontend** - A React application providing a user-friendly interface

## Features

- 🔒 **Secure Authentication** - User registration and login system
- 🔑 **API Key Management** - Generate and manage API keys with defined scopes
- 🤖 **Multiple LLM Providers** - Support for OpenAI (GPT models) and Anthropic (Claude models)
- ⚡ **Serverless Integration** - Firebase Functions for secure client-side API access
- 🚧 **Rate Limiting** - Token bucket algorithm for fair API usage
- 🛡️ **Security Headers** - Comprehensive security measures including CORS and CSP

## Getting Started

### Prerequisites

- Node.js (v16+)
- Python 3.9+
- Firebase CLI
- PostgreSQL
- Redis (optional, for production)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy the example environment file and update it:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

### Firebase Functions Setup

1. Navigate to the functions directory:
   ```bash
   cd backend/firebase-functions/functions
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment files:
   ```bash
   # For local development
   touch .env
   # For deployment
   touch .env.yaml
   ```

4. Add required environment variables:
   ```
   SECRET_KEY=<your_secret_key>
   OPENAI_API_KEY=<your_openai_api_key>
   MISTRAL_API_KEY=<your_mistral_api_key>
   GEMINI_API_KEY=<your_gemini_api_key>
   ANTHROPIC_API_KEY=<your_anthropic_api_key>
   ANTHROPIC_BASE_URL=<your_anthropic_base_url>
   ```

5. Deploy functions:
   ```bash
   npm run deploy
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   touch .env
   ```

4. Add required environment variables:
   ```
   REACT_APP_API_BASE_URL=http://localhost:8000
   REACT_APP_FIREBASE_FUNCTIONS_URL=https://us-central1-colonycraft-ai.cloudfunctions.net
   ```

5. Start the development server:
   ```bash
   PORT=3006 npm start
   ```

## Development

### Testing

#### Backend Tests
```bash
cd backend
pytest
```

#### Firebase Function Tests
```bash
cd backend/firebase-functions/functions
npm test
```

### API Documentation

When the backend is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

### Backend Deployment

The backend can be deployed as a Docker container:

```bash
cd backend
docker-compose up -d
```

### Firebase Functions Deployment

```bash
cd backend/firebase-functions/functions
npm run deploy
```

### Frontend Deployment

```bash
cd frontend
npm run build
# Deploy the build folder to your preferred hosting service
```

## Security Considerations

- Keep all API keys and secrets secure
- Never commit .env files to version control
- Rotate API keys periodically
- Use HTTPS in production
- Configure proper CORS settings for production

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
