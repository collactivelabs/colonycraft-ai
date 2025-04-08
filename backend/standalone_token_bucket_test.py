"""
Standalone test for TokenBucket that doesn't require loading the entire app configuration
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
import time

# Define the TokenBucket class directly to avoid imports
class TokenBucket:
    """
    Implements the token bucket algorithm for rate limiting.
    
    This algorithm allows for rate limiting with bursts:
    - The bucket has a capacity of tokens
    - Tokens fill at a constant rate (fill_rate tokens per second)
    - When a request is made, tokens are consumed
    - If there are not enough tokens, the request is denied
    - Tokens may accumulate up to the bucket's capacity
    """
    
    def __init__(self, tokens: float, fill_rate: float):
        """
        Initialize a token bucket.
        
        Args:
            tokens: Initial number of tokens in the bucket.
            fill_rate: Rate at which tokens fill (tokens per second).
        """
        self.capacity = float(tokens)
        self.tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = datetime.now(timezone.utc)
    
    def _refill(self):
        """
        Refill tokens based on time elapsed since last refill.
        """
        now = datetime.now(timezone.utc)
        time_passed = (now - self.timestamp).total_seconds()
        self.timestamp = now
        
        # Add tokens based on time passed and fill rate
        new_tokens = time_passed * self.fill_rate
        self.tokens = min(
            self.capacity,
            self.tokens + new_tokens
        )
    
    def consume(self, tokens: float) -> bool:
        """
        Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume.
            
        Returns:
            bool: True if tokens were consumed, False if not enough tokens were available.
        """
        self._refill()  # Make sure we have the latest token count
        if tokens <= self.tokens:
            self.tokens -= tokens
            return True
        return False
    
    def get_tokens(self) -> float:
        """
        Get the current number of tokens in the bucket.
        
        Returns:
            float: Number of tokens currently available.
        """
        self._refill()
        return self.tokens
    
    def time_until_tokens(self, tokens: float) -> float:
        """
        Calculate time until the specified number of tokens are available.
        
        Args:
            tokens: Number of tokens needed.
            
        Returns:
            float: Time in seconds until the specified tokens are available.
                   Returns 0.0 if tokens are already available.
        """
        self._refill()
        
        # If we already have enough tokens, return 0
        if tokens <= self.tokens:
            return 0.0
        
        # Calculate time to wait for tokens to fill
        additional_tokens_needed = tokens - self.tokens
        seconds_to_wait = additional_tokens_needed / self.fill_rate
        return seconds_to_wait


class TestTokenBucket(unittest.TestCase):
    def setUp(self):
        # Create a patcher for datetime.now
        self.datetime_patcher = patch('datetime.datetime')
        self.mock_datetime = self.datetime_patcher.start()
        
        # Set a fixed initial time
        self.fixed_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        self.mock_datetime.now.return_value = self.fixed_time
    
    def tearDown(self):
        # Stop the patcher
        self.datetime_patcher.stop()
    def test_init(self):
        """Test TokenBucket initialization"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        self.assertEqual(bucket.capacity, 10.0)
        self.assertEqual(bucket.tokens, 10.0)
        self.assertEqual(bucket.fill_rate, 1.0)
        self.assertEqual(bucket.timestamp, self.fixed_time)
    
    def test_consume_success(self):
        """Test successfully consuming tokens"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        
        # First consumption should work
        self.assertTrue(bucket.consume(1))
        self.assertEqual(bucket.tokens, 9.0)
        
        # Second consumption should also work
        self.assertTrue(bucket.consume(5))
        self.assertEqual(bucket.tokens, 4.0)
    
    def test_consume_failure(self):
        """Test failing to consume tokens when not enough are available"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        
        # Consume most tokens
        self.assertTrue(bucket.consume(8))
        self.assertEqual(bucket.tokens, 2.0)
        
        # Try to consume more than available
        self.assertFalse(bucket.consume(3))
        # Tokens should remain unchanged when consumption fails
        self.assertEqual(bucket.tokens, 2.0)
    
    def test_refill(self):
        """Test token refill based on elapsed time"""
        # Create bucket with 5 tokens, refill at 2 tokens/second
        bucket = TokenBucket(tokens=5, fill_rate=2)
        
        # Consume all tokens
        self.assertTrue(bucket.consume(5))
        self.assertEqual(bucket.tokens, 0.0)
        
        # Advance time by 2 seconds
        future_time = self.fixed_time + timedelta(seconds=2)
        self.mock_datetime.now.return_value = future_time
        
        # After 2 seconds with fill_rate=2, should have 4 new tokens
        self.assertEqual(bucket.get_tokens(), 4.0)
        
        # Consume 3 tokens
        self.assertTrue(bucket.consume(3))
        self.assertEqual(bucket.tokens, 1.0)
        
        # Advance time by 3 more seconds (6 more tokens)
        new_time = future_time + timedelta(seconds=3)
        self.mock_datetime.now.return_value = new_time
        
        # Should now have 1 + 6 = 7 tokens
        self.assertEqual(bucket.get_tokens(), 7.0)
    
    def test_get_tokens(self):
        """Test getting current token count with refill"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        
        # Consume some tokens
        bucket.consume(6)
        self.assertEqual(bucket.tokens, 4.0)
        
        # Advance time by 2 seconds
        self.mock_datetime.now.return_value = self.fixed_time + timedelta(seconds=2)
        
        # Should have refilled 2 tokens (4 + 2 = 6)
        self.assertEqual(bucket.get_tokens(), 6.0)
    
    def test_time_until_tokens(self):
        """Test calculating time until tokens are available"""
        bucket = TokenBucket(tokens=10, fill_rate=2)  # 2 tokens per second
        
        # Consume all but 1 token
        bucket.consume(9)
        self.assertEqual(bucket.tokens, 1.0)
        
        # Time until 1 more token available (already have 1)
        self.assertAlmostEqual(bucket.time_until_tokens(2), 0.5, delta=0.001)  # Need 1 more token, at 2/sec = 0.5 sec
        
        # Time until 5 more tokens available
        self.assertAlmostEqual(bucket.time_until_tokens(6), 2.5, delta=0.001)  # Need 5 more tokens, at 2/sec = 2.5 sec
        
        # Already have enough tokens
        self.assertEqual(bucket.time_until_tokens(1), 0.0)
    
    def test_max_capacity(self):
        """Test that tokens don't exceed capacity during refill"""
        bucket = TokenBucket(tokens=10, fill_rate=2)
        
        # Consume some tokens
        bucket.consume(5)
        self.assertEqual(bucket.tokens, 5.0)
        
        # Advance time by 10 seconds (would add 20 tokens, but capacity is 10)
        self.mock_datetime.now.return_value = self.fixed_time + timedelta(seconds=10)
        
        # Should be capped at capacity (10)
        self.assertEqual(bucket.get_tokens(), 10.0)
    
    def test_multiple_refills(self):
        """Test multiple refill operations with partial consumption"""
        bucket = TokenBucket(tokens=10, fill_rate=1)
        
        # Consume 5 tokens
        bucket.consume(5)
        self.assertEqual(bucket.tokens, 5.0)
        
        # Advance time by 2 seconds
        self.mock_datetime.now.return_value = self.fixed_time + timedelta(seconds=2)
        
        # Should have 7 tokens (5 + 2)
        self.assertEqual(bucket.get_tokens(), 7.0)
        
        # Consume 4 tokens
        bucket.consume(4)
        self.assertEqual(bucket.tokens, 3.0)
        
        # Advance time by 3 more seconds
        self.mock_datetime.now.return_value = self.fixed_time + timedelta(seconds=5)  # 2 + 3 = 5 seconds total
        
        # Should have 6 tokens (3 + 3)
        self.assertEqual(bucket.get_tokens(), 6.0)


if __name__ == '__main__':
    unittest.main()
