#!/usr/bin/env python
"""
Standalone test script for TokenBucket that uses our updated implementation
"""

import unittest
from datetime import datetime, timedelta, timezone

# Define the TokenBucket class directly from our updated implementation
class TokenBucket:
    def __init__(self, tokens: float, fill_rate: float, time_function=None):
        """
        Initialize a token bucket.
        
        :param tokens: Maximum number of tokens in the bucket
        :param fill_rate: Rate at which tokens are added (tokens per second)
        :param time_function: Optional function to get current time (for testing)
        """
        self.capacity = float(tokens)
        self.tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.time_function = time_function or (lambda: datetime.now(timezone.utc))
        self.timestamp = self.time_function()
        
    def consume(self, tokens: float = 1.0) -> bool:
        """
        Consume tokens from the bucket. Returns True if tokens were consumed, False otherwise.
        
        :param tokens: Number of tokens to consume
        :return: True if tokens were successfully consumed, False if not enough tokens
        """
        self._refill()
        if tokens <= self.tokens:
            self.tokens -= tokens
            return True
        return False
        
    def _refill(self) -> None:
        """
        Refill the token bucket based on the time elapsed since the last refill.
        """
        now = self.time_function()
        elapsed = (now - self.timestamp).total_seconds()
        self.timestamp = now
        
        # Calculate new tokens based on time elapsed
        new_tokens = elapsed * self.fill_rate
        
        # Add new tokens to the bucket, but don't exceed capacity
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        
    def get_tokens(self) -> float:
        """
        Get the current number of tokens in the bucket.
        
        :return: Current token count
        """
        self._refill()
        return self.tokens
        
    def time_until_tokens(self, tokens: float) -> float:
        """
        Calculate the time in seconds until 'tokens' tokens will be available.
        
        :param tokens: Number of tokens needed
        :return: Time in seconds until tokens will be available
        """
        self._refill()
        if tokens <= self.tokens:
            return 0.0
        
        # Calculate time needed for enough tokens
        additional_tokens_needed = tokens - self.tokens
        seconds_needed = additional_tokens_needed / self.fill_rate
        
        return seconds_needed


class TestTokenBucket(unittest.TestCase):
    def setUp(self):
        # Set initial time for testing
        self.current_time = datetime(2023, 1, 1, tzinfo=timezone.utc)
        
        # Create a time function that returns the current test time
        def get_test_time():
            return self.current_time
            
        self.get_test_time = get_test_time
    
    def advance_time(self, seconds):
        """Helper method to advance the test time by specified seconds"""
        self.current_time += timedelta(seconds=seconds)
        
    def test_init(self):
        """Test TokenBucket initialization"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        self.assertEqual(bucket.capacity, 10.0)
        self.assertEqual(bucket.tokens, 10.0)
        self.assertEqual(bucket.fill_rate, 1.0)
        self.assertEqual(bucket.timestamp, self.current_time)
    
    def test_consume_success(self):
        """Test successfully consuming tokens"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        self.assertTrue(bucket.consume(1))
        self.assertAlmostEqual(bucket.tokens, 9.0, delta=0.001)
        
        # Consume multiple tokens
        self.assertTrue(bucket.consume(5))
        self.assertAlmostEqual(bucket.tokens, 4.0, delta=0.001)
    
    def test_consume_failure(self):
        """Test failing to consume tokens when not enough are available"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        
        # Consume most tokens
        self.assertTrue(bucket.consume(8))
        self.assertAlmostEqual(bucket.tokens, 2.0, delta=0.001)
        
        # Try to consume more than available
        self.assertFalse(bucket.consume(3))
        self.assertAlmostEqual(bucket.tokens, 2.0, delta=0.001)  # Tokens should remain unchanged
    
    def test_refill(self):
        """Test token refill based on elapsed time"""
        # Create bucket with 5 tokens, refill at 2 tokens/second
        bucket = TokenBucket(tokens=5, fill_rate=2, time_function=self.get_test_time)
        
        # Consume all tokens
        self.assertTrue(bucket.consume(5))
        self.assertAlmostEqual(bucket.tokens, 0.0, delta=0.001)
        
        # Advance time by 2 seconds
        self.advance_time(2)
        
        # After 2 seconds with fill_rate=2, should have 4 new tokens (2 * 2 = 4)
        self.assertAlmostEqual(bucket.get_tokens(), 4.0, delta=0.001)
        
        # Consume 3 tokens
        self.assertTrue(bucket.consume(3))
        self.assertAlmostEqual(bucket.tokens, 1.0, delta=0.001)
        
        # Advance time by 3 more seconds
        self.advance_time(3)
        
        # Calculate expected tokens: starting with 1.0 token
        # Adding 3 seconds * 2 tokens/second = 6 more tokens
        # 1.0 + 6.0 = 7.0 tokens total, but max capacity is 5
        expected_tokens = min(5.0, 1.0 + (3.0 * 2.0))
        self.assertAlmostEqual(bucket.get_tokens(), expected_tokens, delta=0.001)
    
    def test_get_tokens(self):
        """Test getting current token count with refill"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        
        # Consume some tokens
        bucket.consume(6)
        self.assertAlmostEqual(bucket.tokens, 4.0, delta=0.001)
        
        # Advance time by 2 seconds
        self.advance_time(2)
        
        # Should have refilled 2 tokens (4 + 2 = 6)
        self.assertAlmostEqual(bucket.get_tokens(), 6.0, delta=0.001)
    
    def test_time_until_tokens(self):
        """Test calculating time until tokens are available"""
        bucket = TokenBucket(tokens=10, fill_rate=2, time_function=self.get_test_time)  # 2 tokens per second
        
        # Consume all but 1 token
        bucket.consume(9)
        self.assertAlmostEqual(bucket.tokens, 1.0, delta=0.001)
        
        # Time until 1 more token available (already have 1)
        self.assertAlmostEqual(bucket.time_until_tokens(2), 0.5, delta=0.001)  # Need 1 more token, at 2/sec = 0.5 sec
        
        # Time until 5 more tokens available
        self.assertAlmostEqual(bucket.time_until_tokens(6), 2.5, delta=0.001)  # Need 5 more tokens, at 2/sec = 2.5 sec
        
        # Already have enough tokens
        self.assertAlmostEqual(bucket.time_until_tokens(1), 0.0, delta=0.001)
    
    def test_max_capacity(self):
        """Test that tokens don't exceed capacity during refill"""
        bucket = TokenBucket(tokens=10, fill_rate=2, time_function=self.get_test_time)
        
        # Consume some tokens
        bucket.consume(5)
        self.assertAlmostEqual(bucket.tokens, 5.0, delta=0.001)
        
        # Advance time by 10 seconds (would add 20 tokens, but capacity is 10)
        self.advance_time(10)
        
        # Should be capped at capacity (10)
        self.assertAlmostEqual(bucket.get_tokens(), 10.0, delta=0.001)
    
    def test_multiple_refills(self):
        """Test multiple refill operations with partial consumption"""
        bucket = TokenBucket(tokens=10, fill_rate=1, time_function=self.get_test_time)
        
        # Consume 5 tokens
        bucket.consume(5)
        self.assertAlmostEqual(bucket.tokens, 5.0, delta=0.001)
        
        # Advance time by 2 seconds
        self.advance_time(2)
        
        # Should have 7 tokens (5 + 2)
        self.assertAlmostEqual(bucket.get_tokens(), 7.0, delta=0.001)
        
        # Consume 4 tokens
        bucket.consume(4)
        self.assertAlmostEqual(bucket.tokens, 3.0, delta=0.001)
        
        # Advance time by 3 more seconds
        self.advance_time(3)
        
        # Should have 6 tokens (3 + 3)
        self.assertAlmostEqual(bucket.get_tokens(), 6.0, delta=0.001)


if __name__ == "__main__":
    unittest.main()
