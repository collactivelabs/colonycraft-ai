# Logging

## Structured Logging

All logs are structured in JSON format for easier parsing and analysis:

```python
import structlog
import logging
import uuid
from datetime import datetime

# Configure Python's standard library logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

# Configure structlog
structlog.configure(
    processors=[
        # Add context from contextvars (e.g., request_id)
        structlog.contextvars.merge_contextvars,
        # Add log level
        structlog.processors.add_log_level,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Add exception info for errors
        structlog.processors.format_exc_info,
        # Format as JSON
        structlog.processors.JSONRenderer()
    ],
    # Use standard library logger
    logger_factory=structlog.stdlib.LoggerFactory(),
    # Cache loggers
    cache_logger_on_first_use=True,
)

def get_logger(name=None):
    """Get a logger with the specified name"""
    return structlog.get_logger(name)
```

## Log Levels and Usage

- **ERROR**: Application errors requiring immediate attention
- **WARNING**: Potential issues that don't cause system failure
- **INFO**: Normal operational events (requests, significant state changes)
- **DEBUG**: Detailed information for troubleshooting (only in development)

## Contextual Logging

Each log entry contains contextual information to aid in debugging and analysis:

```python
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Extract safe request details
    path = request.url.path
    method = request.method
    
    # Add context to all logs in this request
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=path,
        method=method,
        client_ip=request.client.host,
    )
    
    # If authenticated user, add user ID
    if hasattr(request.state, "user_id"):
        structlog.contextvars.bind_contextvars(user_id=request.state.user_id)
    
    # Log request
    logger = get_logger("api.request")
    logger.info("Request received")
    
    # Process request
    start_time = datetime.now()
    try:
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log response
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(
            "Request completed",
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
    except Exception as e:
        # Log unhandled exceptions
        logger.exception("Unhandled exception", error=str(e))
        raise
    finally:
        # Clean up context
        structlog.contextvars.unbind_contextvars(
            "request_id", "path", "method", "client_ip", "user_id"
        )
```

## Sensitive Data Handling

Care is taken to avoid logging sensitive information:

1. Passwords and tokens are never logged
2. PII is redacted or hashed when necessary
3. API keys are truncated (showing only first/last few characters)
4. Prompt and response contents are truncated to avoid excessive logging

## Log Storage and Retention

Logs are stored and managed according to the following guidelines:

1. **Short-term Storage**: 30 days of raw logs for detailed investigation
2. **Long-term Storage**: 1 year of aggregated logs for trend analysis 
3. **Retention Policy**: 
   - ERROR logs: 1 year
   - WARNING logs: 6 months
   - INFO logs: 30 days
   - DEBUG logs: 7 days in non-production only

## Log Analysis

The ELK Stack (Elasticsearch, Logstash, Kibana) is used for log aggregation and analysis:

1. **Logstash**: Collects, transforms, and forwards logs
2. **Elasticsearch**: Stores and indexes log data for efficient search
3. **Kibana**: Provides visualization and search capabilities

Example log parsing configuration:

```yaml
# Logstash configuration
input {
  kafka {
    bootstrap_servers => "kafka:9092"
    topics => ["app-logs"]
    codec => "json"
    consumer_threads => 4
  }
}

filter {
  if [level] == "ERROR" {
    mutate {
      add_tag => ["error"]
    }
  }
  
  # Extract JSON fields from log message
  json {
    source => "message"
  }
  
  # Parse timestamp
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
  
  # Enrich with geo data for client IPs
  geoip {
    source => "client_ip"
    target => "geoip"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{+YYYY.MM.dd}"
  }
}
```
