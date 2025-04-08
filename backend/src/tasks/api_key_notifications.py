import logging
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.notifications.api_key_notifications import run_notification_check

logger = logging.getLogger(__name__)

async def scheduled_api_key_check(interval_hours: int = 24):
    """
    Scheduled task to check for API keys that are about to expire
    and send notifications to users.
    
    Args:
        interval_hours: Interval in hours to run the check
    """
    while True:
        try:
            # Get a database session
            db = next(get_db())
            
            logger.info("Running scheduled API key expiry check")
            
            # Run notification check
            run_notification_check(db)
            
            # Close the database session
            db.close()
            
        except Exception as e:
            logger.error(f"Error in scheduled API key check: {str(e)}")
        
        # Sleep for the specified interval
        logger.info(f"Next API key check in {interval_hours} hours")
        await asyncio.sleep(interval_hours * 3600)

def start_api_key_check_background_task():
    """
    Start the background task for API key expiry checks
    """
    # Create a separate event loop for the background task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start the background task
    loop.create_task(scheduled_api_key_check())
    
    # Start the event loop
    loop.run_forever()
