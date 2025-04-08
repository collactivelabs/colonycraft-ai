"""
Direct tests for TokenBucket that don't rely on conftest.py
This allows us to test the TokenBucket component in isolation
"""

import pytest
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Import the TokenBucket class directly to avoid app initialization issues
from src.core.security import TokenBucket

class TestTokenBucket:
    @pytest.fixture(autouse=True)
    def setup_time_function(self):
        # Set initial time for testing
        self.current_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        
        # Create a time function that returns the current test time
        def get_test_time():
            return self.current_time
            
        self.get_test_time = get_test_time
        
        # Helper method to advance time
        def advance_time(seconds):
            self.current_time += timedelta(seconds=seconds)
            
        # Make the helper method available to tests
        self.advance_time = advance_time
    def test_init(self):
        """Test TokenBucket initialization"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        assert bucket.capacity == 10.0
        assert bucket.tokens == 10.0
        assert bucket.fill_rate == 1.0
        assert bucket.timestamp == self.current_time
    
    def test_consume_success(self):
        """Test successfully consuming tokens"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        assert bucket.consume(1) is True
        assert pytest.approx(bucket.tokens) == 9.0
        
        # Consume multiple tokens
        assert bucket.consume(5) is True
        assert pytest.approx(bucket.tokens) == 4.0
    
    def test_consume_failure(self):
        """Test failing to consume tokens when not enough are available"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        
        # Consume most tokens
        assert bucket.consume(8) is True
        assert pytest.approx(bucket.tokens) == 2.0
        
        # Try to consume more than available
        assert bucket.consume(3) is False
        assert pytest.approx(bucket.tokens) == 2.0  # Tokens should remain unchanged
    
    def test_refill(self):
        """Test token refill based on elapsed time"""
        # Create bucket with 5 tokens, refill at 2 tokens/second
        bucket = TokenBucket(tokens=5, fill_rate=2, time_function=self.get_test_time)
        
        # Consume all tokens
        assert bucket.consume(5) is True
        assert pytest.approx(bucket.tokens) == 0.0
        
        # Advance time by 2 seconds
        self.advance_time(2)
        
        # After 2 seconds with fill_rate=2, should have 4 new tokens
        assert pytest.approx(bucket.get_tokens()) == 4.0
        
        # Try consuming 3 tokens
        assert bucket.consume(3) is True
        assert pytest.approx(bucket.tokens) == 1.0
    
    def test_get_tokens(self):
        """Test getting current token count"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        
        # Consume some tokens
        bucket.consume(6)
        
        # Should return current token count
        assert pytest.approx(bucket.get_tokens()) == 4.0
        
        # Advance time by 2 seconds
        self.advance_time(2)
        
        # Should now have 6 tokens (4 + 2)
        assert pytest.approx(bucket.get_tokens()) == 6.0
    
    def test_time_until_tokens(self):
        """Test calculating time until tokens are available"""
        bucket = TokenBucket(tokens=10, fill_rate=2, time_function=self.get_test_time)  # 2 tokens per second
        
        # Consume all but 1 token
        bucket.consume(9)
        assert pytest.approx(bucket.tokens) == 1.0
        
        # Time until 1 more token available (already have 1)
        assert pytest.approx(bucket.time_until_tokens(2)) == 0.5  # Need 1 more token, at 2/sec = 0.5 sec
        
        # Time until 5 more tokens available
        assert pytest.approx(bucket.time_until_tokens(6)) == 2.5  # Need 5 more tokens, at 2/sec = 2.5 sec
        
        # Already have enough tokens
        assert pytest.approx(bucket.time_until_tokens(1)) == 0.0
    
    def test_max_capacity(self):
        """Test that tokens don't exceed capacity during refill"""
        bucket = TokenBucket(tokens=10, fill_rate=2, time_function=self.get_test_time)
        
        # Consume some tokens
        bucket.consume(5)
        assert pytest.approx(bucket.tokens) == 5.0
        
        # Advance time by 10 seconds (would add 20 tokens at 2/sec)
        self.advance_time(10)  
        
        # Should be capped at capacity (10)
        assert pytest.approx(bucket.get_tokens()) == 10.0

    def test_multiple_refills(self):
        """Test multiple refill operations with partial consumption"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        
        # Consume half the tokens
        assert bucket.consume(5) is True
        assert pytest.approx(bucket.tokens) == 5.0
        
        # Advance time by 2 seconds
        self.advance_time(2)
        
        # Should have 7 tokens (5 + 2)
        assert pytest.approx(bucket.get_tokens()) == 7.0
        
        # Consume 4 tokens
        assert bucket.consume(4) is True
        assert pytest.approx(bucket.tokens) == 3.0
        
        # Advance time by 3 more seconds
        self.advance_time(3)
        
        # Should have 6 tokens (3 + 3)
        assert pytest.approx(bucket.get_tokens()) == 6.0
