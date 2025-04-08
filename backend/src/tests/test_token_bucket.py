import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from ..core.security import TokenBucket

class TestTokenBucket:
    def test_init(self):
        """Test TokenBucket initialization"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.fill_rate == 1
        assert isinstance(bucket.timestamp, datetime)
    
    def test_consume_success(self):
        """Test successfully consuming tokens"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        assert bucket.consume(1) is True
        assert bucket.tokens == 9
        
        # Consume multiple tokens
        assert bucket.consume(5) is True
        assert bucket.tokens == 4
    
    def test_consume_failure(self):
        """Test failing to consume tokens when not enough are available"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        
        # Consume most tokens
        assert bucket.consume(8) is True
        assert bucket.tokens == 2
        
        # Try to consume more than available
        assert bucket.consume(3) is False
        assert bucket.tokens == 2  # Tokens should remain unchanged
    
    def test_refill(self):
        """Test token refill based on elapsed time"""
        # Create bucket with 5 tokens, refill at 2 tokens/second
        bucket = TokenBucket(tokens=5, fill_rate=2)
        
        # Consume all tokens
        assert bucket.consume(5) is True
        assert bucket.tokens == 0
        
        # Mock the datetime to simulate time passing
        future_time = datetime.utcnow() + timedelta(seconds=2)
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = future_time
            
            # After 2 seconds with fill_rate=2, should have 4 new tokens
            assert bucket.get_tokens() == 4
            
            # Try consuming 3 tokens
            assert bucket.consume(3) is True
            assert bucket.tokens == 1
    
    def test_get_tokens(self):
        """Test getting current token count"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        
        # Consume some tokens
        bucket.consume(6)
        
        # Should return current token count
        assert bucket.get_tokens() == 4
    
    def test_time_until_tokens(self):
        """Test calculating time until tokens are available"""
        bucket = TokenBucket(tokens=10, fill_rate=2)  # 2 tokens per second
        
        # Consume all but 1 token
        bucket.consume(9)
        
        # Time until 1 more token available (already have 1)
        assert bucket.time_until_tokens(2) == 0.5  # Need 1 more token, at 2/sec = 0.5 sec
        
        # Time until 5 more tokens available
        assert bucket.time_until_tokens(6) == 2.5  # Need 5 more tokens, at 2/sec = 2.5 sec
        
        # Already have enough tokens
        assert bucket.time_until_tokens(1) == 0.0
    
    def test_max_capacity(self):
        """Test that tokens don't exceed capacity during refill"""
        bucket = TokenBucket(tokens=10, fill_rate=2)
        
        # Consume some tokens
        bucket.consume(5)
        assert bucket.tokens == 5
        
        # Move time forward so that more than capacity would be filled
        future_time = datetime.utcnow() + timedelta(seconds=10)  # Would add 20 tokens
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = future_time
            
            # Should be capped at capacity (10)
            bucket._refill()
            assert bucket.tokens == 10
