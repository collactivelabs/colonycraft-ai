from prometheus_client import Counter, Histogram, Info, Gauge
from fastapi import FastAPI
from prometheus_client.openmetrics.exposition import CONTENT_TYPE_LATEST
from prometheus_client import generate_latest
from starlette.requests import Request
from starlette.responses import Response
import time

# Define metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

http_request_size_bytes = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

# Rate limiting metrics
rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total number of requests that exceeded rate limits',
    ['client_id', 'endpoint']
)

rate_limit_remaining_tokens = Gauge(
    'rate_limit_remaining_tokens',
    'Number of tokens remaining in the bucket for a client',
    ['client_id']
)

rate_limit_reset_seconds = Gauge(
    'rate_limit_reset_seconds',
    'Seconds until rate limit reset for a client',
    ['client_id']
)

http_response_size_bytes = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

api_info = Info('api_info', 'API information')

def init_metrics(app):
    """Initialize metrics with API information"""
    # Only collect info if this is a FastAPI app, not a middleware
    if hasattr(app, 'version') and hasattr(app, 'title'):
        api_info.info({
            'version': getattr(app, 'version', 'unknown'),
            'title': getattr(app, 'title', 'unknown'),
            'docs_url': getattr(app, 'docs_url', None) or 'disabled'
        })

async def metrics_endpoint():
    """Endpoint to expose metrics"""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

from starlette.middleware.base import BaseHTTPMiddleware

class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        init_metrics(app)
        # Add metrics endpoint if this is a FastAPI app
        if hasattr(app, 'add_route'):
            app.add_route("/metrics", metrics_endpoint)
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract endpoint from request
        endpoint = request.url.path
        method = request.method
        
        # Record request size
        content_length = request.headers.get('content-length')
        if content_length:
            http_request_size_bytes.labels(
                method=method,
                endpoint=endpoint
            ).observe(int(content_length))
        
        # Process request and capture any errors
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Record response size
            response_length = response.headers.get('content-length')
            if response_length:
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(int(response_length))
            
        except Exception as e:
            status_code = 500
            raise e
        finally:
            # Record duration and increment request counter
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
        
        return response
