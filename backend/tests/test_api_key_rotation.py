import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, UTC
import uuid

from src.models.api_key import APIKey
from src.models.api_key_rotation_history import APIKeyRotationHistory
from src.models.user import User
from src.core.auth.api_key import APIKey as APIKeyAuth
from src.crud.api_key import rotate_api_key


class TestAPIKeyRotation(unittest.TestCase):
    """Test API key rotation and history tracking"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock database session
        self.db = MagicMock()
        
        # Create a test user
        self.user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )
        
        # Create a test API key
        self.api_key = APIKey(
            id=str(uuid.uuid4()),
            prefix="testkey1",
            key_hash="hash_value",
            name="Test Key",
            user_id=self.user.id,
            scopes=["*"],
            created_at=datetime.now(UTC) - timedelta(days=30),
            is_active=True
        )
        
        # Mock the database query responses
        self.db.query.return_value.filter.return_value.first.return_value = self.api_key
        
    @patch('src.core.auth.api_key.APIKey.rotate')
    def test_rotate_api_key(self, mock_rotate):
        """Test rotating an API key creates a rotation history record"""
        # Set up mock for API key rotation
        new_key = APIKeyAuth(
            id=str(uuid.uuid4()),
            key_hash="new_hash_value",
            prefix="testkey2",
            name="New Test Key",
            user_id=self.user.id,
            scope=["*"],
            created_at=datetime.now(UTC)
        )
        mock_rotate.return_value = (new_key, "new_key_value")
        
        # Call rotate_api_key
        new_key_model, old_key_model, key_value = rotate_api_key(
            self.db,
            self.api_key.id,
            self.user.id,
            name="New Test Key",
            grace_period_days=7
        )
        
        # Verify rotation history record was created
        self.db.add.assert_any_call(new_key_model)
        
        # Get the rotation history record that was added
        # Find the call that added the APIKeyRotationHistory object
        for call in self.db.add.call_args_list:
            args, _ = call
            if isinstance(args[0], APIKeyRotationHistory):
                rotation_history = args[0]
                break
        else:
            self.fail("No APIKeyRotationHistory object was added")
            
        # Verify rotation history fields
        self.assertEqual(rotation_history.api_key_id, self.api_key.id)
        self.assertEqual(rotation_history.previous_prefix, self.api_key.prefix)
        self.assertEqual(rotation_history.reason, "Routine rotation")
        self.assertEqual(rotation_history.grace_period_days, 7)
        self.assertFalse(rotation_history.is_compromised)
        
        # Verify old key was updated
        self.assertEqual(old_key_model.grace_period_days, 7)
        self.assertIsNotNone(old_key_model.grace_period_end)
        
        # Verify new key has reference to old key
        self.assertEqual(new_key_model.rotated_from_id, self.api_key.id)
        
    @patch('src.core.auth.api_key.APIKey.rotate')
    def test_rotate_compromised_api_key(self, mock_rotate):
        """Test rotating a compromised API key immediately deactivates it"""
        # Set up mock for API key rotation
        new_key = APIKeyAuth(
            id=str(uuid.uuid4()),
            key_hash="new_hash_value",
            prefix="testkey2",
            name="New Test Key",
            user_id=self.user.id,
            scope=["*"],
            created_at=datetime.now(UTC)
        )
        mock_rotate.return_value = (new_key, "new_key_value")
        
        # Call rotate_api_key with was_compromised=True
        new_key_model, old_key_model, key_value = rotate_api_key(
            self.db,
            self.api_key.id,
            self.user.id,
            name="New Test Key",
            was_compromised=True
        )
        
        # Find the rotation history record
        for call in self.db.add.call_args_list:
            args, _ = call
            if isinstance(args[0], APIKeyRotationHistory):
                rotation_history = args[0]
                break
        else:
            self.fail("No APIKeyRotationHistory object was added")
            
        # Verify compromised key settings
        self.assertEqual(rotation_history.reason, "Compromised key")
        self.assertTrue(rotation_history.is_compromised)
        
        # Verify old key was immediately deactivated
        self.assertFalse(old_key_model.is_active)
        self.assertTrue(old_key_model.was_compromised)
        self.assertEqual(old_key_model.grace_period_days, 0)
        

if __name__ == "__main__":
    unittest.main()
