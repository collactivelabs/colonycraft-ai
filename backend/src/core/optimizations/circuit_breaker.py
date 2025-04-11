"""
Circuit Breaker Pattern Implementation

This module provides a circuit breaker implementation to prevent cascading failures
when external services are experiencing issues. It automatically stops calls to failing
services and allows them to recover before resuming normal operation.
"""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast

logger = logging.getLogger(__name__)

# Type variable for better type hints
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class CircuitState(Enum):
    """Possible states for the circuit breaker"""
    CLOSED = 'closed'      # Normal operation, requests are allowed
    OPEN = 'open'          # Circuit is open, requests are blocked
    HALF_OPEN = 'half_open'  # Testing if service has recovered


class CircuitBreaker:
    """
    Circuit Breaker implementation for fault tolerance
    
    Tracks failures in external service calls and temporarily disables further calls
    after a threshold is reached, preventing cascading failures and allowing the
    service to recover.
    
    Attributes:
        name: Name of the circuit breaker for logging
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Seconds to wait before trying again (half-open state)
        expected_exceptions: Exception types that count as failures
        fallback_function: Optional function to call when circuit is open
    """
    
    # Shared registry of circuit breakers
    _circuit_breakers: Dict[str, 'CircuitBreaker'] = {}
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exceptions: tuple = (Exception,),
        fallback_function: Optional[Callable[..., Any]] = None
    ):
        """
        Initialize a circuit breaker
        
        Args:
            name: Unique name for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            expected_exceptions: Exception types that count as failures
            fallback_function: Function to call when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.fallback_function = fallback_function
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.last_success_time = time.time()
        
        # Track this breaker in the registry
        self._circuit_breakers[name] = self
        
        # Locks for thread safety
        self._state_lock = asyncio.Lock()
        
        logger.info(
            f"Created circuit breaker: name={name}, "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )
    
    @classmethod
    def get_circuit_breaker(cls, name: str) -> 'CircuitBreaker':
        """
        Get a circuit breaker by name, creating it if it doesn't exist
        
        Args:
            name: Name of the circuit breaker
            
        Returns:
            The CircuitBreaker instance
        """
        if name not in cls._circuit_breakers:
            return cls(name)
        return cls._circuit_breakers[name]
    
    async def __call__(self, func):
        """
        Decorator for functions that should use this circuit breaker
        
        Args:
            func: The function to wrap with circuit breaker functionality
            
        Returns:
            Wrapped function with circuit breaker behavior
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.execute(func, *args, **kwargs)
        
        return wrapper
    
    async def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            CircuitOpenError: If the circuit is open
            Exception: Any exception raised by the function
        """
        # Check if circuit is open
        await self._check_state()
        
        try:
            # Call the function
            result = await func(*args, **kwargs)
            
            # Update state on success
            await self._on_success()
            return result
        
        except self.expected_exceptions as e:
            # Update state on failure
            await self._on_failure(e)
            
            # Use fallback if provided
            if self.fallback_function:
                return await self.fallback_function(*args, **kwargs)
            
            # Re-raise the exception
            raise
    
    async def _check_state(self) -> None:
        """
        Check the current state and possibly transition to half-open
        
        Raises:
            CircuitOpenError: If the circuit is open
        """
        async with self._state_lock:
            current_time = time.time()
            
            # If open, check if we should try again
            if self.state == CircuitState.OPEN:
                if current_time - self.last_failure_time >= self.recovery_timeout:
                    logger.info(f"Circuit {self.name}: transitioning from OPEN to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                else:
                    # Still open, raise exception
                    remaining = self.recovery_timeout - (current_time - self.last_failure_time)
                    raise CircuitOpenError(
                        f"Circuit {self.name} is OPEN. Try again in {remaining:.1f}s"
                    )
    
    async def _on_success(self) -> None:
        """Update state after a successful call"""
        async with self._state_lock:
            self.last_success_time = time.time()
            
            # If half-open, transition to closed
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit {self.name}: transitioning from HALF_OPEN to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                self.failure_count = 0
    
    async def _on_failure(self, exception: Exception) -> None:
        """
        Update state after a failed call
        
        Args:
            exception: The exception that occurred
        """
        async with self._state_lock:
            current_time = time.time()
            self.last_failure_time = current_time
            
            if self.state == CircuitState.CLOSED:
                # Increment failure count
                self.failure_count += 1
                logger.warning(
                    f"Circuit {self.name}: failure {self.failure_count}/{self.failure_threshold} - {str(exception)}"
                )
                
                # Open circuit if threshold reached
                if self.failure_count >= self.failure_threshold:
                    logger.error(f"Circuit {self.name}: transitioning from CLOSED to OPEN")
                    self.state = CircuitState.OPEN
            
            elif self.state == CircuitState.HALF_OPEN:
                # Failure in half-open state means service still has issues
                logger.error(f"Circuit {self.name}: failed in HALF_OPEN, going back to OPEN - {str(exception)}")
                self.state = CircuitState.OPEN
    
    async def reset(self) -> None:
        """Reset the circuit breaker to closed state (for testing)"""
        async with self._state_lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_success_time = time.time()
            logger.info(f"Circuit {self.name}: manually reset to CLOSED")
    
    async def force_open(self) -> None:
        """Force the circuit to open state (for testing)"""
        async with self._state_lock:
            self.state = CircuitState.OPEN
            self.failure_count = self.failure_threshold
            self.last_failure_time = time.time()
            logger.info(f"Circuit {self.name}: manually forced to OPEN")
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing requests)"""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)"""
        return self.state == CircuitState.OPEN


class CircuitOpenError(Exception):
    """Exception raised when a circuit is open"""
    pass


# Decorator for applying circuit breaker to functions
def circuit_protected(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    expected_exceptions: tuple = (Exception,),
    fallback_function: Optional[Callable[..., Any]] = None
):
    """
    Decorator for applying circuit breaker to async functions
    
    Args:
        name: Name for the circuit breaker
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds to wait before trying again
        expected_exceptions: Exception types to count as failures
        fallback_function: Function to call when circuit is open
        
    Returns:
        Decorated function with circuit breaker protection
    """
    def decorator(func: F) -> F:
        circuit = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=expected_exceptions,
            fallback_function=fallback_function
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await circuit.execute(func, *args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator
