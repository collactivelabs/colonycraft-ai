# Tracing

## Distributed Tracing with OpenTelemetry

OpenTelemetry is used for distributed tracing across services:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Set up tracer provider
trace.set_tracer_provider(TracerProvider())

# Configure exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="otel-collector:4317",
    insecure=True
)

# Add span processor to the tracer provider
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Get tracer
tracer = trace.get_tracer("colonycraft.api")

# Example usage in code
@app.post("/api/v1/llm/generate")
async def generate_llm_response(request: LLMRequest):
    with tracer.start_as_current_span("llm_generate") as span:
        # Add attributes to the span
        span.set_attribute("provider", request.provider)
        span.set_attribute("model", request.model)
        span.set_attribute("prompt_length", len(request.prompt))
        
        # Call LLM service
        response = await llm_service.generate_response(
            provider=request.provider,
            model=request.model,
            prompt=request.prompt,
            options=request.options
        )
        
        # Add response info to span
        span.set_attribute("response_length", len(response.text))
        span.set_attribute("input_tokens", response.metadata.usage.input_tokens)
        span.set_attribute("output_tokens", response.metadata.usage.output_tokens)
        
        return response
```

## Trace Context Propagation

Trace context is propagated across services to maintain end-to-end visibility:

1. Between backend API and Firebase Functions
2. Between API and database queries
3. Across asynchronous operations (background tasks)

## Trace Sampling

To balance performance and observability, a sampling strategy is implemented:

1. **Always Sample**:
   - Error responses (4xx, 5xx)
   - Critical business flows
   - Low-volume endpoints

2. **Sample Rate**:
   - 100% in development/staging
   - 10% in production for standard requests
   - 1% for high-volume endpoints

## Trace Visualization

Traces are visualized in Jaeger UI, providing:

1. Service dependency diagrams
2. End-to-end request timelines
3. Span details with custom attributes
4. Latency breakdowns and bottleneck identification

## Trace Storage and Retention

Trace data is managed with the following retention periods:

1. **Raw Trace Data**: 7 days for detailed investigation
2. **Aggregated Trace Data**: 30 days for trend analysis
3. **Error Traces**: 30 days for root cause analysis

## Application Performance Management (APM)

Traces are integrated with APM tools providing:

1. **Transaction Monitoring**: End-to-end visibility of business transactions
2. **Service Maps**: Visualizing service dependencies and interactions
3. **Performance Hotspots**: Identifying bottlenecks in the request path
4. **Correlation**: Linking traces with logs and metrics

Example trace augmentation:

```python
# Add business context to spans
async def process_colony_creation(colony_data: dict):
    with tracer.start_as_current_span("colony_creation") as span:
        # Add business attributes
        span.set_attribute("colony.name", colony_data["name"])
        span.set_attribute("colony.template", colony_data["template"])
        span.set_attribute("colony.resource_level", colony_data["resources"]["compute"])
        
        # Track user context
        span.set_attribute("user.id", context.get_user_id())
        span.set_attribute("organization.id", context.get_org_id())
        
        # Process the creation
        try:
            colony_id = await colony_service.create_colony(colony_data)
            span.set_attribute("colony.id", colony_id)
            span.set_status(Status(StatusCode.OK))
            return colony_id
        except Exception as e:
            # Record error details in span
            span.set_status(Status(StatusCode.ERROR))
            span.record_exception(e)
            raise
```
