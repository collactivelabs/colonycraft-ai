# src/api/__init__.py
# This file marks the `api` directory as a Python package.
from src.api.v1.endpoints import auth, image, video, files

__all__ = ["auth", "image", "video", "files"]