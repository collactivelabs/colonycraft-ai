from celery import Celery
import os
from .config import get_settings

settings = get_settings()

# Configure Celery
celery_app = Celery(
    'colony_craft',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'src.tasks.api_key_rotation',
        'src.tasks.response_caching',
        'src.tasks.scheduled_jobs',
        'src.tasks.metrics_aggregation'
    ]
)

# For backward compatibility with existing code
celery = celery_app  # This line ensures existing imports still work

# Optional configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=200,
    worker_prefetch_multiplier=1,  # Disable prefetching for better task distribution
    task_acks_late=True,  # Only acknowledge tasks after they complete
)

# Set up task routing
celery_app.conf.task_routes = {
    'src.tasks.api_key_rotation.*': {'queue': 'maintenance'},
    'src.tasks.response_caching.*': {'queue': 'caching'},
    'src.tasks.scheduled_jobs.*': {'queue': 'scheduled'},
    'src.tasks.metrics_aggregation.*': {'queue': 'metrics'},
}

# Optional rate limiting
celery_app.conf.task_annotations = {
    'src.tasks.api_key_rotation.rotate_api_keys': {'rate_limit': '1/h'},
}

# Register tasks
@celery_app.task(name="src.core.celery.test_task")
def test_task(name=None):
    """Test task to check if Celery is working"""
    return f"Hello {name or 'World'} from Celery!"