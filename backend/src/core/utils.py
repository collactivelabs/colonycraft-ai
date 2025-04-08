import hashlib
from datetime import datetime
from typing import Any
import json, os
from google.cloud import storage

def generate_file_hash(content: bytes) -> str:
    """Generate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()

def generate_unique_filename(original_name: str, content: bytes) -> str:
    """Generate unique filename based on content hash and timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_hash = generate_file_hash(content)[:8]
    ext = original_name.split('.')[-1]
    return f"{timestamp}_{file_hash}.{ext}"

def serialize_model(model: Any) -> dict:
    """Serialize SQLAlchemy model to dict."""
    return {
        column.name: getattr(model, column.name)
        for column in model.__table__.columns
    }

def upload_to_gcs(bucket_name: str, file_path: str) -> str:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    object_name = os.path.basename(file_path)
    blob = bucket.blob(object_name)

    # Use resumable uploads for large files
    blob.upload_from_filename(file_path, timeout=600)  # Timeout set to 10 minutes

    # Generate public URL
    gcs_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"
    return gcs_url