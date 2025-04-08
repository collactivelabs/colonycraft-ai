import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, UTC
import uuid

from src.models.api_key import APIKey
from src.models.user import User
from src.core.notifications.api_key_notifications import (
    generate_key_expiry_notification,
    generate_key_rotation_notification,
    check_expiring_api_keys
)


class TestAPIKeyNotifications(unittest.TestCase):
    """Test API key notification generation"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a test user
        self.user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )
        
        # Create a test API key set to expire soon
        self.expiring_key = APIKey(
            id=str(uuid.uuid4()),
            prefix="expkey1",
            key_hash="hash_value",
            name="Expiring Key",
            user_id=self.user.id,
            scopes=["*"],
            created_at=datetime.now(UTC) - timedelta(days=30),
            expires_at=datetime.now(UTC) + timedelta(days=3),
            is_active=True
        )
        
        # Create another test API key for rotation tests
        self.old_key = APIKey(
            id=str(uuid.uuid4()),
            prefix="oldkey1",
            key_hash="old_hash_value",
            name="Old Key",
            user_id=self.user.id,
            scopes=["*"],
            created_at=datetime.now(UTC) - timedelta(days=60),
            is_active=True,
            grace_period_days=7,
            grace_period_end=datetime.now(UTC) + timedelta(days=7)
        )
        
        self.new_key = APIKey(
            id=str(uuid.uuid4()),
            prefix="newkey1",
            key_hash="new_hash_value",
            name="New Key",
            user_id=self.user.id,
            scopes=["*"],
            created_at=datetime.now(UTC),
            is_active=True,
            rotated_from_id=self.old_key.id,
            rotation_date=datetime.now(UTC)
        )
    
    def test_generate_key_expiry_notification(self):
        """Test generating notifications for expiring keys"""
        # Use a real datetime object for testing
        current_time = datetime.now(UTC)
        
        # Create a mock now function that returns our fixed time
        def mock_now(tz):
            return current_time
            
        # Fix the expiry date to be exactly 3 days from now
        self.expiring_key.expires_at = current_time + timedelta(days=3)
        
        # Patch the datetime.now method to return our fixed time
        with patch('src.core.notifications.api_key_notifications.datetime') as mock_datetime:
            mock_datetime.now = mock_now
            
            notification = generate_key_expiry_notification(self.user, self.expiring_key)
            
            # Verify notification structure
            self.assertEqual(notification["type"], "api_key_expiry")
            self.assertEqual(notification["user_id"], self.user.id)
            self.assertIn("Expiring Key", notification["title"])
            self.assertIn("3 days", notification["message"])
            self.assertEqual(notification["urgency"], "high")  # High because 3 days left
            self.assertEqual(notification["action_text"], "Rotate Key")
        
        # Test urgency for very soon expiry
        with patch('src.core.notifications.api_key_notifications.datetime') as mock_datetime:
            # Set fixed time for testing critical urgency
            current_time = datetime.now(UTC)
            
            # Create a mock now function that returns our fixed time
            def mock_now(tz):
                return current_time
                
            mock_datetime.now = mock_now
            
            # Set expiry to less than 1 day away
            self.expiring_key.expires_at = current_time + timedelta(hours=12)
            notification = generate_key_expiry_notification(self.user, self.expiring_key)
            self.assertEqual(notification["urgency"], "critical")  # Critical when <= 1 day
    
    def test_generate_key_rotation_notification(self):
        """Test generating notifications for rotated keys"""
        notification = generate_key_rotation_notification(
            self.user, 
            self.old_key, 
            self.new_key, 
            grace_period_days=7
        )
        
        # Verify notification structure
        self.assertEqual(notification["type"], "api_key_rotated")
        self.assertEqual(notification["user_id"], self.user.id)
        self.assertIn("Old Key", notification["title"])
        self.assertIn("7 days", notification["message"])
        self.assertEqual(notification["urgency"], "normal")
        self.assertEqual(notification["action_text"], "View Keys")
        
        # Verify metadata
        self.assertEqual(notification["metadata"]["old_key_id"], self.old_key.id)
        self.assertEqual(notification["metadata"]["new_key_id"], self.new_key.id)
        self.assertEqual(notification["metadata"]["grace_period_days"], 7)
    
    @patch('src.core.notifications.api_key_notifications.get_expiring_api_keys')
    def test_check_expiring_api_keys(self, mock_get_expiring):
        """Test checking for expiring API keys"""
        mock_db = MagicMock()
        mock_get_expiring.return_value = [self.expiring_key]
        
        # Mock the database query to return our test user
        mock_db.query.return_value.filter.return_value.first.return_value = self.user
        
        # Run the check
        notifications = check_expiring_api_keys(mock_db)
        
        # We should have one notification
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]["type"], "api_key_expiry")
        self.assertEqual(notifications[0]["user_id"], self.user.id)
        

if __name__ == "__main__":
    unittest.main()
