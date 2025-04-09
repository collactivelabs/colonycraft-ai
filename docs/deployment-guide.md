# Deployment Guide

## Overview

This deployment guide provides instructions for setting up and deploying the ColonyCraft AI platform in different environments. The application consists of three main components:

1. Backend API (FastAPI)
2. Firebase Functions
3. Frontend (React)

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Environment](#development-environment)
3. [Staging Environment](#staging-environment)
4. [Production Environment](#production-environment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Ensure you have the following tools and accounts set up:

### Required Software

- Docker and Docker Compose
- Node.js (v16+)
- Python 3.9+
- Firebase CLI
- PostgreSQL
- Redis (optional for development, required for production)
- Git

### Required Accounts

- Firebase account
- OpenAI API account
- Anthropic API account
- (Optional) Cloud provider account (AWS, GCP, or Azure)

## Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/your-organization/colonycraft-ai.git
cd colonycraft-ai
```

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your configuration
# - Database connection strings
# - API keys for OpenAI and Anthropic
# - Secret keys for JWT
```

Update the `.env` file with the following:

```
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/colonycraft
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/colonycraft_test

# Authentication
SECRET_KEY=your_generated_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM Providers
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:3006
ALLOWED_HOSTS=localhost,127.0.0.1

# Environment
ENVIRONMENT=development
DEBUG=true
```

### 3. Firebase Functions Setup

```bash
# Navigate to firebase functions directory
cd backend/firebase-functions/functions

# Install dependencies
npm install

# Create environment files
cp .env.example .env
cp .env.example .env.yaml

# Edit .env and .env.yaml with appropriate values
```

Update the Firebase environment variables:

```
# .env and .env.yaml
SECRET_KEY=same_secret_key_as_backend
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 4. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env with appropriate values
```

Update the frontend environment variables:

```
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_FIREBASE_FUNCTIONS_URL=http://localhost:5001/colonycraft-ai/us-central1
```

### 5. Start Development Servers

Start all services using Docker Compose:

```bash
# From the project root
docker-compose up -d
```

Or start each component individually:

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

**Firebase Functions (Local Emulator):**
```bash
cd backend/firebase-functions/functions
firebase emulators:start
```

**Frontend:**
```bash
cd frontend
PORT=3006 npm start
```

### 6. Access the Application

- Frontend: http://localhost:3006
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Firebase Emulator UI: http://localhost:4000

## Staging Environment

Staging provides a testing environment that closely mirrors production.

### 1. Build Docker Images

```bash
# From project root
docker-compose -f docker-compose.staging.yml build
```

### 2. Deploy to Staging Server

```bash
# Deploy using Docker Compose
docker-compose -f docker-compose.staging.yml up -d

# Or deploy to your cloud provider using appropriate tools
```

### 3. Deploy Firebase Functions to Staging

```bash
cd backend/firebase-functions/functions

# Set environment to staging
firebase use staging

# Deploy functions
firebase deploy --only functions
```

## Production Environment

### 1. Create Production-Ready Environment Files

Create secure production environment files:

**Backend:**
```bash
cp backend/.env.example backend/.env.production
# Edit with production values
```

**Firebase:**
```bash
cp backend/firebase-functions/functions/.env.example backend/firebase-functions/functions/.env.production.yaml
# Edit with production values
```

**Frontend:**
```bash
cp frontend/.env.example frontend/.env.production
# Edit with production values
```

### 2. Build Production Docker Images

```bash
docker-compose -f docker-compose.production.yml build
```

### 3. Push Docker Images to Registry

```bash
docker-compose -f docker-compose.production.yml push
```

### 4. Deploy to Production Server

```bash
# SSH into production server
ssh user@production-server

# Pull the latest images
docker-compose -f docker-compose.production.yml pull

# Update and start the services
docker-compose -f docker-compose.production.yml up -d
```

### 5. Deploy Firebase Functions to Production

```bash
cd backend/firebase-functions/functions

# Set environment to production
firebase use production

# Deploy functions
firebase deploy --only functions
```

### 6. Configure Domain and SSL

Set up your domain with proper SSL certificates:

```bash
# Install certbot for Let's Encrypt
apt-get update
apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Kubernetes Deployment

For large-scale deployments, Kubernetes provides better scaling and management capabilities.

### 1. Prepare Kubernetes Manifests

Create Kubernetes manifests in the `k8s` directory:

- `namespace.yaml`: Define the namespace
- `secrets.yaml`: Store sensitive information
- `configmap.yaml`: Store configuration
- `deployment-backend.yaml`: Backend deployment
- `deployment-frontend.yaml`: Frontend deployment
- `service-backend.yaml`: Backend service
- `service-frontend.yaml`: Frontend service
- `ingress.yaml`: Ingress configuration

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets and config
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

# Deploy applications
kubectl apply -f k8s/deployment-backend.yaml
kubectl apply -f k8s/deployment-frontend.yaml

# Create services
kubectl apply -f k8s/service-backend.yaml
kubectl apply -f k8s/service-frontend.yaml

# Set up ingress
kubectl apply -f k8s/ingress.yaml
```

### 3. Verify Deployment

```bash
kubectl get pods -n colonycraft
kubectl get services -n colonycraft
kubectl get ingress -n colonycraft
```

## Monitoring and Maintenance

### Monitoring Setup

1. **Prometheus and Grafana:**
   
   Deploy Prometheus and Grafana for metrics:
   
   ```bash
   kubectl apply -f k8s/monitoring/prometheus.yaml
   kubectl apply -f k8s/monitoring/grafana.yaml
   ```

2. **ELK Stack for Logging:**
   
   Deploy Elasticsearch, Logstash, and Kibana:
   
   ```bash
   kubectl apply -f k8s/logging/elk-stack.yaml
   ```

### Database Backups

Set up automated PostgreSQL backups:

```bash
# Create a backup script
cat > /usr/local/bin/backup-postgres.sh << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/var/backups/postgres
mkdir -p $BACKUP_DIR
pg_dump -U postgres colonycraft > $BACKUP_DIR/colonycraft_$TIMESTAMP.sql
find $BACKUP_DIR -type f -mtime +7 -name "*.sql" -delete
EOF

# Make it executable
chmod +x /usr/local/bin/backup-postgres.sh

# Add to crontab
(crontab -l ; echo "0 2 * * * /usr/local/bin/backup-postgres.sh") | crontab -
```

### Update Procedure

To update the application:

1. Build and push new Docker images
2. Update Kubernetes deployments or Docker Compose services:

```bash
# For Kubernetes
kubectl set image deployment/backend-deployment backend=your-registry/colonycraft-backend:new-tag -n colonycraft
kubectl set image deployment/frontend-deployment frontend=your-registry/colonycraft-frontend:new-tag -n colonycraft

# For Docker Compose
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues:**
   ```bash
   # Check database logs
   kubectl logs -l app=postgres -n colonycraft
   
   # Verify connection settings
   kubectl describe configmap colonycraft-config -n colonycraft
   ```

2. **API Key Issues:**
   ```bash
   # Check for valid API keys in environment variables
   kubectl describe secret colonycraft-secrets -n colonycraft
   ```

3. **Firebase Function Errors:**
   ```bash
   # Check Firebase logs
   firebase functions:log
   ```

4. **Container Issues:**
   ```bash
   # Check container logs
   kubectl logs -l app=backend -n colonycraft
   kubectl logs -l app=frontend -n colonycraft
   ```

### Support and Resources

- GitHub Repository: [https://github.com/your-organization/colonycraft-ai](https://github.com/your-organization/colonycraft-ai)
- Issue Tracker: [https://github.com/your-organization/colonycraft-ai/issues](https://github.com/your-organization/colonycraft-ai/issues)
- Documentation: [https://docs.colonycraft.ai](https://docs.colonycraft.ai)
- Contact: [support@colonycraft.ai](mailto:support@colonycraft.ai)
