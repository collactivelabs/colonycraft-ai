from ..core.celery import celery
from celery.utils.log import get_task_logger
import os
import time
from datetime import datetime, timedelta
from ..core.config import get_settings

logger = get_task_logger(__name__)
settings = get_settings()

@celery.task
def cleanup_old_files():
    """
    Task to clean up old temporary files.
    Removes files that are older than specified retention period.
    """
    logger.info("Starting cleanup of old files")
    
    # Define directories to clean up
    cleanup_dirs = [
        os.path.join("static", "temp"),
        os.path.join("static", "uploads"),
    ]
    
    # Set retention period (default: 7 days)
    retention_days = 7
    retention_seconds = retention_days * 24 * 60 * 60
    current_time = time.time()
    
    total_removed = 0
    total_errors = 0
    
    for directory in cleanup_dirs:
        if not os.path.exists(directory):
            logger.warning(f"Directory {directory} does not exist, skipping")
            continue
            
        logger.info(f"Cleaning up directory: {directory}")
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip directories
            if os.path.isdir(file_path):
                continue
                
            # Check file age
            file_modified_time = os.path.getmtime(file_path)
            if current_time - file_modified_time > retention_seconds:
                try:
                    os.remove(file_path)
                    logger.debug(f"Removed old file: {file_path}")
                    total_removed += 1
                except Exception as e:
                    logger.error(f"Error removing file {file_path}: {str(e)}")
                    total_errors += 1
    
    logger.info(f"Cleanup completed: {total_removed} files removed, {total_errors} errors")
    return {"removed": total_removed, "errors": total_errors}
