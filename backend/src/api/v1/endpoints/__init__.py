# src/api/v1/endpoints/__init__.py
from .auth import router as auth_router
from .image import router as image_router
from .video import router as video_router
from .files import router as files_router

__all__ = ["auth_router", "image_router", "video_router", "files_router"]