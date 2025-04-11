"""
Connection Pooling for Database and Redis Connections

This module provides connection pool management for database and Redis connections,
optimizing resource usage in high-concurrency scenarios.
"""
import logging
from functools import lru_cache
from typing import Dict, Any

import redis
from redis import ConnectionPool as RedisPool
from sqlalchemy.engine import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker, Session

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database connection pooling
@lru_cache
def get_db_pool(pool_size: int = 20, max_overflow: int = 10, timeout: int = 30):
    """
    Get a database connection pool.
    
    Args:
        pool_size: The number of connections to keep open in the pool
        max_overflow: The maximum number of connections to open additionally
        timeout: The number of seconds to wait before timing out on connection acquire
    
    Returns:
        A SQLAlchemy Engine with connection pooling configured
    """
    logger.info(f"Creating database connection pool: size={pool_size}, max_overflow={max_overflow}")
    
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=pool_size,  # Number of connections to keep open
        max_overflow=max_overflow,  # Max extra connections when pool is fully used
        pool_timeout=timeout,  # Seconds to wait before timing out on connection acquire
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using them
        poolclass=QueuePool  # Use Queue pool for thread safety
    )
    
    return engine

@lru_cache
def get_session_factory():
    """Get a session factory for creating database sessions"""
    engine = get_db_pool()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """Get a database session from the pool"""
    session_factory = get_session_factory()
    return session_factory()

# Redis connection pooling
@lru_cache
def get_redis_pool(max_connections: int = 50) -> RedisPool:
    """
    Get a Redis connection pool
    
    Args:
        max_connections: Maximum number of connections to keep in the pool
    
    Returns:
        A Redis connection pool
    """
    logger.info(f"Creating Redis connection pool: max_connections={max_connections}")
    
    # Parse Redis URL for connection parameters
    connection_kwargs = {}
    
    # Create connection pool with sensible defaults for high concurrency
    pool = redis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=max_connections,
        socket_timeout=5.0,  # 5 second socket timeout
        socket_keepalive=True,  # Keep connections alive
        socket_connect_timeout=3.0,  # 3 second connect timeout
        health_check_interval=30,  # Check connections every 30 seconds
        retry_on_timeout=True,  # Retry operations if Redis times out
        **connection_kwargs
    )
    
    return pool

@lru_cache
def get_redis_client() -> redis.Redis:
    """Get a Redis client from the connection pool"""
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool, decode_responses=True)

# Reset connection pools (useful for testing)
def reset_pools():
    """Reset all connection pools"""
    # Clear LRU caches to rebuild pools
    get_db_pool.cache_clear()
    get_session_factory.cache_clear()
    get_redis_pool.cache_clear()
    get_redis_client.cache_clear()
    logger.info("Connection pools reset")
