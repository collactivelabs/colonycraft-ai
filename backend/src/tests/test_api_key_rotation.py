import pytest
from datetime import datetime, timedelta, UTC
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

# Import models from src directly to avoid circular imports
from src.models.api_key import APIKey
from src.models.api_key_rotation_history import APIKeyRotationHistory
from src.crud.api_key import (
    create_api_key,
    rotate_api_key,
    deactivate_api_key,
    get_api_keys_in_rotation
)
from src.core.auth import APIKey as APIKeyAuth
from src.schemas.api_key import APIKeyCreate, APIKeyRotate

# Use the fixtures from conftest.py instead of redefining them
# This prevents model metadata conflicts during testing

@pytest.fixture
def db_session():
    """Mock DB session for testing"""
    session = MagicMock()
    return session

@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return MagicMock(id="test-user-id", is_admin=False)

@pytest.fixture
def mock_api_key():
    """Create a mock API key for testing"""
    return APIKey(
        id="test-key-id",
        prefix="testpref",
        key_hash="test-hash",
        name="Test Key",
        user_id="test-user-id",
        scopes=["read", "write"],
        created_at=datetime.now(UTC),
        expires_at=None,
        is_active=True
    )

class TestAPIKeyRotation:
    def test_create_api_key(self, db_session, mock_user):
        """Test creating a new API key"""
        # Arrange
        key_data = APIKeyCreate(
            name="Test Key",
            scopes=["read", "write"],
            expires_in_days=30
        )
        
        # Set up mock for the APIKeyAuth.generate
        mock_key_value = "testpref.testsecret"
        mock_api_key = APIKeyAuth(
            id="test-key-id",
            key_hash="test-hash",
            prefix="testpref",
            name="Test Key",
            user_id=mock_user.id,
            scope=["read", "write"],
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30)
        )
        
        with patch('src.crud.api_key.APIKeyAuth.generate', return_value=(mock_api_key, mock_key_value)):
            # Act
            db_api_key, key_value = create_api_key(
                db=db_session,
                user_id=mock_user.id,
                name=key_data.name,
                scopes=key_data.scopes,
                expires_in_days=key_data.expires_in_days
            )
            
            # Assert
            assert db_api_key is not None
            assert key_value == mock_key_value
            assert db_api_key.user_id == mock_user.id
            assert db_api_key.name == key_data.name
            assert db_api_key.scopes == key_data.scopes
            assert db_api_key.is_active is True
            assert db_session.add.called
            assert db_session.commit.called
            assert db_session.refresh.called
    
    def test_rotate_api_key(self, db_session, mock_user, mock_api_key):
        """Test rotating an existing API key"""
        # Arrange
        rotation_data = APIKeyRotate(
            name="Rotated Key",
            scopes=["read"],
            expires_in_days=60,
            grace_period_days=14,
            was_compromised=False
        )
        
        # Set up mock for db.query
        db_session.query.return_value.filter.return_value.first.return_value = mock_api_key
        
        # Set up mock for APIKeyAuth.rotate
        mock_new_key_value = "newpref.newsecret"
        mock_new_api_key = APIKeyAuth(
            id="new-key-id",
            key_hash="new-hash",
            prefix="newpref",
            name="Rotated Key",
            user_id=mock_user.id,
            scope=["read"],
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=60),
            rotated_from_id=mock_api_key.id,
            rotation_date=datetime.now(UTC),
            grace_period_days=14,
            grace_period_end=datetime.now(UTC) + timedelta(days=14)
        )
        
        with patch('src.crud.api_key.APIKeyAuth.rotate', return_value=(mock_new_api_key, mock_new_key_value)):
            # Act
            new_key, old_key, key_value = rotate_api_key(
                db=db_session,
                api_key_id=mock_api_key.id,
                user_id=mock_user.id,
                name=rotation_data.name,
                scopes=rotation_data.scopes,
                expires_in_days=rotation_data.expires_in_days,
                grace_period_days=rotation_data.grace_period_days,
                was_compromised=rotation_data.was_compromised,
                rotated_by_user_id=mock_user.id
            )
            
            # Assert
            assert new_key is not None
            assert old_key is not None
            assert key_value == mock_new_key_value
            assert new_key.rotated_from_id == mock_api_key.id
            assert new_key.name == rotation_data.name
            assert new_key.scopes == rotation_data.scopes
            assert new_key.is_active is True
            assert old_key.grace_period_days == rotation_data.grace_period_days
            assert old_key.grace_period_end is not None
            assert db_session.add.call_count == 2  # New key and rotation history
            assert db_session.commit.called
            assert db_session.refresh.call_count == 2  # Refresh both keys
    
    def test_rotate_compromised_api_key(self, db_session, mock_user, mock_api_key):
        """Test rotating a compromised API key (immediate deactivation)"""
        # Arrange
        rotation_data = APIKeyRotate(
            name="Compromised Key Replacement",
            scopes=["read"],
            expires_in_days=60,
            grace_period_days=14,  # Should be ignored for compromised keys
            was_compromised=True
        )
        
        # Set up mock for db.query
        db_session.query.return_value.filter.return_value.first.return_value = mock_api_key
        
        # Set up mock for APIKeyAuth.rotate
        mock_new_key_value = "newpref.newsecret"
        mock_new_api_key = APIKeyAuth(
            id="new-key-id",
            key_hash="new-hash",
            prefix="newpref",
            name="Compromised Key Replacement",
            user_id=mock_user.id,
            scope=["read"],
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=60),
            rotated_from_id=mock_api_key.id,
            rotation_date=datetime.now(UTC),
            was_compromised=True
        )
        
        with patch('src.crud.api_key.APIKeyAuth.rotate', return_value=(mock_new_api_key, mock_new_key_value)):
            # Act
            new_key, old_key, key_value = rotate_api_key(
                db=db_session,
                api_key_id=mock_api_key.id,
                user_id=mock_user.id,
                name=rotation_data.name,
                scopes=rotation_data.scopes,
                expires_in_days=rotation_data.expires_in_days,
                grace_period_days=rotation_data.grace_period_days,
                was_compromised=rotation_data.was_compromised,
                rotated_by_user_id=mock_user.id
            )
            
            # Assert
            assert new_key is not None
            assert old_key is not None
            assert key_value == mock_new_key_value
            assert old_key.is_active is False  # Should be deactivated immediately
            assert old_key.was_compromised is True
            assert old_key.grace_period_end is None  # No grace period for compromised keys
            
    def test_get_api_keys_in_rotation(self, db_session, mock_user):
        """Test getting API keys that are in rotation grace period"""
        # Arrange
        now = datetime.now(UTC)
        
        # Set up mock for db.query
        db_session.query.return_value.filter.return_value.all.return_value = [
            APIKey(
                id="rotating-key-1",
                prefix="rotkey1",
                name="Rotating Key 1",
                user_id=mock_user.id,
                is_active=False,
                grace_period_end=now + timedelta(days=3)
            ),
            APIKey(
                id="rotating-key-2",
                prefix="rotkey2",
                name="Rotating Key 2",
                user_id=mock_user.id,
                is_active=False,
                grace_period_end=now + timedelta(days=5)
            )
        ]
        
        # Act
        keys_in_rotation = get_api_keys_in_rotation(db_session, mock_user.id)
        
        # Assert
        assert len(keys_in_rotation) == 2
        assert all(key.grace_period_end > now for key in keys_in_rotation)
        assert db_session.query.called
        
    def test_api_key_rotation_endpoint(self, client, db_session, mock_user, mock_api_key):
        """Integration test for the API key rotation endpoint"""
        # This would be implemented in a more comprehensive integration test
        # that uses a test database and/or more sophisticated mocking
        pass
