from celery import Celery, signals
from celery.signals import task_failure, worker_ready, worker_shutting_down
from ..core.config import get_settings
from celery.utils.log import get_task_logger
import logging
from typing import Any, Dict
from datetime import timedelta

# Configure logging
logger = get_task_logger(__name__)

# Get settings instance
settings = get_settings()

# Initialize Celery app
app = Celery(
    "colonycraft-worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'tasks.image_tasks',
        'tasks.video_tasks',
        'tasks.maintenance'
    ]
)

# Enhanced Celery configuration
app.conf.update(
    # Task execution settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,  # Prevent memory leaks

    # Task routing with queue priorities
    task_routes={
        'tasks.image_tasks.*': {
            'queue': 'image',
            'routing_key': 'image.process'
        },
        'tasks.video_tasks.*': {
            'queue': 'video',
            'routing_key': 'video.process'
        },
        'tasks.maintenance.*': {
            'queue': 'maintenance',
            'routing_key': 'maintenance.process'
        }
    },

    # Enhanced retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Result backend settings
    result_expires=timedelta(days=1),
    result_persistent=True,

    # Security settings
    security_key=settings.SECRET_KEY,
    
    # Logging
    worker_log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    worker_task_log_format='%(asctime)s - %(task_name)s[%(task_id)s] - %(levelname)s - %(message)s',
)

@signals.worker_ready.connect
def worker_ready_handler(**_: Dict[str, Any]):
    """Log when worker is ready"""
    logger.info("Celery worker is ready and accepting tasks")

@signals.worker_shutting_down.connect
def worker_shutdown_handler(**_: Dict[str, Any]):
    """Log when worker is shutting down"""
    logger.info("Celery worker is shutting down")

@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None,
                       args=None, kwargs=None, **_: Dict[str, Any]):
    """Enhanced task failure handling"""
    task_name = sender.name if sender else "Unknown Task"
    error_msg = str(exception) if exception else "No error message available"
    
    logger.error(
        f"Task {task_name}[{task_id}] failed: {error_msg}",
        extra={
            'task_id': task_id,
            'task_name': task_name,
            'args': args,
            'kwargs': kwargs,
            'exception': error_msg
        }
    )

# Create singleton instance
celery = app

# Optional: Configure periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-files': {
        'task': 'tasks.maintenance.cleanup_old_files',
        'schedule': timedelta(days=1),
        'options': {'queue': 'maintenance'}
    }
}