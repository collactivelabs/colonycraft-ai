"""
API Key Rotation Tasks

This module contains tasks related to API key rotation.
"""

from celery import shared_task
from sqlalchemy.orm import Session
import logging
from ..core.database import get_db
from ..models.api_key_rotation_history import APIKeyRotationHistory

logger = logging.getLogger(__name__)

@shared_task(name="src.tasks.api_key_rotation.rotate_api_keys")
def rotate_api_keys():
    """
    Task to rotate API keys that are due for rotation.
    """
    logger.info("Starting scheduled API key rotation task")
    # Implementation will be added later
    return "API key rotation task executed"


@shared_task(name="src.tasks.api_key_rotation.log_rotation")
def log_rotation(api_key_id: str, rotation_type: str):
    """
    Log an API key rotation event to the history table.
    
    Args:
        api_key_id: The ID of the API key that was rotated
        rotation_type: The type of rotation (scheduled, manual, emergency)
    """
    logger.info(f"Logging API key rotation: {api_key_id}, type: {rotation_type}")
    
    # Get DB session
    db = next(get_db())
    
    try:
        # Create rotation history entry
        rotation_record = APIKeyRotationHistory(
            api_key_id=api_key_id,
            rotation_type=rotation_type
        )
        
        # Add and commit to DB
        db.add(rotation_record)
        db.commit()
        
        return f"Rotation logged for API key {api_key_id}"
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log API key rotation: {str(e)}")
        raise
    finally:
        db.close()
