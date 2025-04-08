import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta, UTC
from sqlalchemy.orm import Session

from ...models.user import User
from ...models.api_key import APIKey
from ...crud.api_key import get_expiring_api_keys

logger = logging.getLogger(__name__)

def generate_key_expiry_notification(user: User, api_key: APIKey) -> Dict[str, Any]:
    """
    Generate a notification message for an expiring API key
    
    Args:
        user: The user who owns the key
        api_key: The API key that is expiring
        
    Returns:
        A notification message object
    """
    days_left = 0
    if api_key.expires_at:
        days_left = (api_key.expires_at - datetime.now(UTC)).days
    
    urgency = "normal"
    if days_left <= 1:
        urgency = "critical"
    elif days_left <= 3:
        urgency = "high"
    
    return {
        "type": "api_key_expiry",
        "user_id": user.id,
        "title": f"API Key Expiring Soon: {api_key.name}",
        "message": f"Your API key '{api_key.name}' will expire in {days_left} days. Please rotate it to avoid service disruption.",
        "urgency": urgency,
        "created_at": datetime.now(UTC),
        "action_url": f"/api/v1/keys/{api_key.id}/rotate",
        "action_text": "Rotate Key",
        "metadata": {
            "api_key_id": api_key.id,
            "api_key_name": api_key.name,
            "days_left": days_left,
            "expiry_date": api_key.expires_at.isoformat() if api_key.expires_at else None
        }
    }

def generate_key_rotation_notification(user: User, old_key: APIKey, new_key: APIKey, grace_period_days: int) -> Dict[str, Any]:
    """
    Generate a notification message for a rotated API key
    
    Args:
        user: The user who owns the key
        old_key: The old API key
        new_key: The new API key
        grace_period_days: Grace period in days
        
    Returns:
        A notification message object
    """
    return {
        "type": "api_key_rotated",
        "user_id": user.id,
        "title": f"API Key Rotated: {old_key.name}",
        "message": f"Your API key '{old_key.name}' has been rotated. The old key will continue to work for {grace_period_days} days.",
        "urgency": "normal",
        "created_at": datetime.now(UTC),
        "action_url": f"/api/v1/keys",
        "action_text": "View Keys",
        "metadata": {
            "old_key_id": old_key.id,
            "old_key_name": old_key.name,
            "new_key_id": new_key.id,
            "new_key_name": new_key.name,
            "grace_period_days": grace_period_days,
            "grace_period_end": old_key.grace_period_end.isoformat() if old_key.grace_period_end else None
        }
    }

def check_expiring_api_keys(db: Session) -> List[Dict[str, Any]]:
    """
    Check for API keys that will expire soon and generate notifications
    
    Args:
        db: Database session
        
    Returns:
        List of notification objects
    """
    notifications = []
    
    # Get keys expiring in the next 7 days
    expiring_keys = get_expiring_api_keys(db, days_until_expiry=7)
    
    for key in expiring_keys:
        # Get the user for this key
        user = db.query(User).filter(User.id == key.user_id).first()
        if not user:
            logger.warning(f"User not found for API key {key.id}")
            continue
        
        # Generate notification
        notification = generate_key_expiry_notification(user, key)
        notifications.append(notification)
        
    logger.info(f"Generated {len(notifications)} API key expiry notifications")
    return notifications

def send_notifications(notifications: List[Dict[str, Any]]) -> None:
    """
    Send notifications to users (placeholder function)
    
    In a real implementation, this would send emails, push notifications, etc.
    
    Args:
        notifications: List of notification objects
    """
    for notification in notifications:
        # Log the notification for now
        logger.info(f"NOTIFICATION: {notification['title']} - {notification['message']} - Urgency: {notification['urgency']}")
        
        # In a real system, would call appropriate notification services here
        # e.g., email_service.send(notification) or push_notification_service.send(notification)
    
    logger.info(f"Sent {len(notifications)} notifications")

def run_notification_check(db: Session) -> None:
    """
    Run a complete notification check for API keys
    
    Args:
        db: Database session
    """
    # Check for expiring keys
    notifications = check_expiring_api_keys(db)
    
    # Send notifications
    if notifications:
        send_notifications(notifications)
