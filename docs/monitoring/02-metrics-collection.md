# Metrics Collection

## Core Metrics

| Category | Metric | Description | Collection Method |
|----------|--------|-------------|-------------------|
| **System** | CPU Usage | Percentage of CPU utilization | Prometheus node_exporter |
| **System** | Memory Usage | Amount of RAM in use | Prometheus node_exporter |
| **System** | Disk Space | Available disk space | Prometheus node_exporter |
| **System** | Network Traffic | Inbound/outbound network usage | Prometheus node_exporter |
| **Application** | Request Rate | Requests per second | FastAPI middleware, Prometheus |
| **Application** | Response Time | Average and percentile response times | FastAPI middleware, Prometheus |
| **Application** | Error Rate | Percentage of requests resulting in errors | FastAPI middleware, Prometheus |
| **Application** | Concurrent Users | Number of active users | Application metrics |
| **LLM** | Token Usage | Number of tokens consumed | LLM service metrics |
| **LLM** | Model Response Time | Time taken by LLM models to respond | LLM service metrics |
| **LLM** | Prompt Length | Average/max length of user prompts | Application metrics |
| **Database** | Query Time | Duration of database queries | SQLAlchemy metrics |
| **Database** | Connection Pool | Database connection usage | SQLAlchemy metrics |
| **Database** | Transaction Rate | Number of transactions per second | Database metrics |

## Prometheus Integration

Prometheus is used as the primary metrics collection system. Integration with FastAPI is implemented through the `PrometheusMiddleware`:

```python
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client.exposition import generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP Requests', 
    ['method', 'endpoint', 'status_code']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 
    'HTTP Request Latency', 
    ['method', 'endpoint']
)
REQUESTS_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'HTTP Requests currently in progress',
    ['method', 'endpoint']
)
LLM_TOKENS = Counter(
    'llm_tokens_total', 
    'Total LLM Tokens', 
    ['provider', 'model', 'type']
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        method = request.method
        path = request.url.path
        
        if path == '/metrics':
            # Serve metrics endpoint
            return Response(
                generate_latest(),
                media_type="text/plain"
            )
        
        # Track request in progress
        REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).inc()
        
        # Track request latency
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Record metrics
            status_code = response.status_code
            REQUEST_COUNT.labels(
                method=method, 
                endpoint=path, 
                status_code=status_code
            ).inc()
            
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(
                method=method, 
                endpoint=path
            ).observe(duration)
            
            return response
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=method, 
                endpoint=path, 
                status_code=500
            ).inc()
            raise e
        finally:
            # Decrease in-progress count
            REQUESTS_IN_PROGRESS.labels(method=method, endpoint=path).dec()
```

## Custom Metrics for LLM Services

For LLM-specific metrics, custom tracking is implemented in the LLM service classes:

```python
# In LLM service class
def track_tokens(self, input_tokens, output_tokens, provider, model):
    # Track input tokens
    LLM_TOKENS.labels(
        provider=provider,
        model=model,
        type='input'
    ).inc(input_tokens)
    
    # Track output tokens
    LLM_TOKENS.labels(
        provider=provider,
        model=model,
        type='output'
    ).inc(output_tokens)
```
