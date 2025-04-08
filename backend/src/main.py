from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from .api.v1.endpoints.auth import router as auth_router
from .api.v1.endpoints.auth_token import router as auth_llm_router
from .api.v1.endpoints.image import router as image_router
from .api.v1.endpoints.video import router as video_router
from .api.v1.endpoints.files import router as files_router
from .api.v1.endpoints.llm import router as llm_router
from .api.v1.api_keys import router as api_keys_router
from .routers.api_key_management import router as api_key_management_router
from .core.database import engine, Base
from .core.exceptions import add_exception_handlers, BaseAPIException
from .core.middleware import (
    APIKeyMiddleware,
    DatabaseSessionMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    RequestValidationMiddleware,
    validate_environment
)
from .core.middleware.api_key_warning import APIKeyWarningMiddleware
from .core.middleware.api_key_audit import APIKeyAuditMiddleware
from .core.auth import RequestContextMiddleware
from .core.metrics import PrometheusMiddleware
from .core.security import SecurityHeadersMiddleware
from .core.config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup - runs at startup
    import threading
    from .tasks.api_key_notifications import start_api_key_check_background_task

    # Run in a separate thread to not block the main thread
    task_thread = threading.Thread(
        target=start_api_key_check_background_task,
        daemon=True
    )
    task_thread.start()

    yield  # This line separates startup from shutdown logic

    # Cleanup - runs at shutdown
    # Add any cleanup code here if needed

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="API Service",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
        swagger_ui_parameters={"persistAuthorization": True}
    )

    # Create custom documentation templates
    from fastapi.openapi.docs import (
        get_redoc_html,
        get_swagger_ui_html,
        get_swagger_ui_oauth2_redirect_html,
    )
    from fastapi.responses import HTMLResponse

    # Override the default documentation routes
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )

    # Validate environment variables at startup
    validate_environment()

    # Initialize database
    Base.metadata.create_all(bind=engine)

    # Add middleware in order of execution (outside -> inside)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    app.add_middleware(PrometheusMiddleware)  # Metrics collection

    # Create a custom security middleware that skips documentation routes
    class ConditionalSecurityHeadersMiddleware(SecurityHeadersMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Skip all security for documentation
            if request.url.path in ['/docs', '/redoc', '/openapi.json', '/swagger-ui-bundle.js', '/swagger-ui.css']:
                return await call_next(request)
            return await super().dispatch(request, call_next)

    # Use conditional security middleware instead of the standard one
    app.add_middleware(ConditionalSecurityHeadersMiddleware)  # Security headers except for docs
    app.add_middleware(RequestLoggingMiddleware)  # First to log all requests
    app.add_middleware(RequestContextMiddleware)  # Store request in context var for access in dependencies
    app.add_middleware(RequestValidationMiddleware)  # Validate before processing
    app.add_middleware(RateLimitMiddleware)  # Rate limit before heavy processing
    app.add_middleware(APIKeyWarningMiddleware)  # Add warnings for rotated API keys
    app.add_middleware(APIKeyAuditMiddleware)  # Audit trail for API key usage
    app.add_middleware(APIKeyMiddleware)  # Authenticate after basic checks
    app.add_middleware(DatabaseSessionMiddleware)  # DB session for authenticated requests

    # Configure CORS with more restrictive settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Correlation-ID"
        ],
    )

    # Note: Security headers are now handled by SecurityHeadersMiddleware

    # Mount static files directory
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Add exception handlers
    add_exception_handlers(app)

    # Include routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(auth_llm_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(image_router, prefix="/api/v1")
    app.include_router(video_router, prefix="/api/v1")
    app.include_router(files_router, prefix="/api/v1")
    app.include_router(llm_router, prefix="/api/v1/llm", tags=["LLM"])
    app.include_router(api_keys_router, prefix="/api/v1/api-keys", tags=["API Keys"])
    app.include_router(api_key_management_router, prefix="/api/v1", tags=["API Key Management"])

    # Mount static files for favicon
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except RuntimeError:
        # Directory doesn't exist
        pass

    @app.get("/favicon.ico")
    async def favicon():
        # Return a 204 No Content response if favicon.ico is requested
        return Response(status_code=204)

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/")
    async def root():
        return {"message": "Welcome to ColonyCraft API"}

    @app.get("/debug/cors")
    async def debug_cors():
        return {
            "status": "ok",
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "allowed_origins": settings.ALLOWED_ORIGINS,
            "type": str(type(settings.ALLOWED_ORIGINS))
        }

    # Root endpoint

    return app

app = create_app()