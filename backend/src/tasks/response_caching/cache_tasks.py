import json
import hashlib
import logging
from redis import Redis
from src.core.celery import celery_app
from src.core.config import get_settings
import pickle
from typing import Dict, Any, Optional

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize Redis connection
def get_redis_client() -> Redis:
    """Get Redis client for caching"""
    return Redis.from_url(settings.REDIS_URL, decode_responses=False)

def compute_cache_key(provider: str, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
    """
    Compute a deterministic cache key for an LLM request
    
    Args:
        provider: LLM provider name
        model: Model name
        prompt: User prompt
        options: Optional request parameters
        
    Returns:
        A SHA-256 hash string to use as cache key
    """
    # Normalize options dict
    if options is None:
        options = {}
    
    # Only include parameters that affect the output
    filtered_options = {
        k: v for k, v in options.items() 
        if k in ['temperature', 'top_p', 'max_tokens', 'frequency_penalty', 'presence_penalty']
    }
    
    # Create a canonical string representation
    cache_data = {
        'provider': provider,
        'model': model,
        'prompt': prompt,
        'options': filtered_options
    }
    
    # Serialize to JSON and compute hash
    serialized = json.dumps(cache_data, sort_keys=True)
    return f"llm_response:{hashlib.sha256(serialized.encode()).hexdigest()}"

@celery_app.task(name="src.tasks.response_caching.cache_response")
def cache_response(provider: str, model: str, prompt: str, response_data: Dict[str, Any], 
                 options: Optional[Dict[str, Any]] = None, ttl: int = 3600) -> str:
    """
    Cache an LLM response
    
    Args:
        provider: LLM provider name
        model: Model name
        prompt: User prompt
        response_data: Response data to cache
        options: Optional request parameters
        ttl: Time-to-live in seconds (default: 1 hour)
        
    Returns:
        The cache key for the response
    """
    try:
        redis_client = get_redis_client()
        cache_key = compute_cache_key(provider, model, prompt, options)
        
        # Serialize response data
        serialized_data = pickle.dumps(response_data)
        
        # Store in Redis with expiration
        redis_client.setex(cache_key, ttl, serialized_data)
        logger.info(f"Cached response for key: {cache_key}, TTL: {ttl}s")
        return cache_key
    except Exception as e:
        logger.error(f"Error caching response: {str(e)}")
        return ""

@celery_app.task(name="src.tasks.response_caching.retrieve_from_cache")
def retrieve_from_cache(provider: str, model: str, prompt: str, 
                      options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve a cached LLM response if available
    
    Args:
        provider: LLM provider name
        model: Model name
        prompt: User prompt
        options: Optional request parameters
        
    Returns:
        Cached response data if found, None otherwise
    """
    try:
        redis_client = get_redis_client()
        cache_key = compute_cache_key(provider, model, prompt, options)
        
        # Attempt to retrieve from cache
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            # Deserialize and return
            response_data = pickle.loads(cached_data)
            logger.info(f"Cache hit for key: {cache_key}")
            return response_data
        
        logger.info(f"Cache miss for key: {cache_key}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving from cache: {str(e)}")
        return None

@celery_app.task(name="src.tasks.response_caching.invalidate_cache_entry")
def invalidate_cache_entry(provider: str, model: str, prompt: str, 
                         options: Optional[Dict[str, Any]] = None) -> bool:
    """
    Invalidate a specific cache entry
    
    Args:
        provider: LLM provider name
        model: Model name
        prompt: User prompt
        options: Optional request parameters
        
    Returns:
        True if cache entry was invalidated, False otherwise
    """
    try:
        redis_client = get_redis_client()
        cache_key = compute_cache_key(provider, model, prompt, options)
        
        # Delete the cache entry
        result = redis_client.delete(cache_key)
        if result > 0:
            logger.info(f"Invalidated cache entry: {cache_key}")
            return True
        
        logger.info(f"No cache entry found to invalidate: {cache_key}")
        return False
    except Exception as e:
        logger.error(f"Error invalidating cache entry: {str(e)}")
        return False
