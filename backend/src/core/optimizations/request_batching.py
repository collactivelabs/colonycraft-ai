"""
Request Batching for LLM API Calls

This module provides functions for batching similar LLM requests to reduce 
the number of API calls and optimize performance under high load.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar

logger = logging.getLogger(__name__)

# Type definitions for better type hinting
T = TypeVar('T')  # Generic result type
RequestKey = Tuple[str, str, float, int]  # (provider, model, temperature, max_tokens)
RequestBatch = List[Tuple[str, Dict[str, Any], asyncio.Future]]  # [(prompt, options, future), ...]

# Global batching state
active_batches: Dict[RequestKey, RequestBatch] = {}
batch_locks: Dict[RequestKey, asyncio.Lock] = {}

async def batch_requests(
    provider: str,
    model: str,
    prompt: str,
    options: Dict[str, Any],
    batch_fn: Callable[[List[str], Dict[str, Any]], List[Dict[str, Any]]],
    max_batch_size: int = 20,
    max_wait_time: float = 0.1
) -> Dict[str, Any]:
    """
    Batch similar LLM requests together to optimize API usage
    
    Args:
        provider: LLM provider name
        model: Model name
        prompt: User prompt
        options: Request options
        batch_fn: Function to call with batched requests
        max_batch_size: Maximum number of requests to batch together
        max_wait_time: Maximum time to wait for more requests (seconds)
    
    Returns:
        LLM response for the request
    """
    # Create a key to group similar requests
    temperature = options.get('temperature', 0.7)
    max_tokens = options.get('max_tokens', 1024)
    batch_key = (provider, model, temperature, max_tokens)
    
    # Create a future for this request's result
    result_future = asyncio.Future()
    
    # Ensure each key has a lock
    if batch_key not in batch_locks:
        batch_locks[batch_key] = asyncio.Lock()
    
    # Get the lock for this batch key
    async with batch_locks[batch_key]:
        # Initialize batch if needed
        if batch_key not in active_batches:
            active_batches[batch_key] = []
            # Schedule batch processing
            asyncio.create_task(
                _process_batch(batch_key, batch_fn, max_batch_size, max_wait_time)
            )
        
        # Add request to batch
        active_batches[batch_key].append((prompt, options, result_future))
    
    # Wait for result
    return await result_future

async def _process_batch(
    batch_key: RequestKey,
    batch_fn: Callable[[List[str], Dict[str, Any]], List[Dict[str, Any]]],
    max_batch_size: int,
    max_wait_time: float
) -> None:
    """
    Process a batch of requests after collecting them
    
    Args:
        batch_key: Key identifying the batch
        batch_fn: Function to call with batched requests
        max_batch_size: Maximum batch size
        max_wait_time: Maximum wait time
    """
    provider, model, temperature, max_tokens = batch_key
    
    # Wait for more requests or until max_wait_time
    start_time = time.time()
    while (
        len(active_batches[batch_key]) < max_batch_size and 
        time.time() - start_time < max_wait_time
    ):
        await asyncio.sleep(0.01)  # Small sleep to prevent CPU spinning
    
    # Get the batch and clear it from active batches
    async with batch_locks[batch_key]:
        batch = active_batches[batch_key]
        del active_batches[batch_key]
    
    if not batch:
        return  # No requests in batch
    
    # Extract prompts and create a merged options dict
    prompts = [item[0] for item in batch]
    futures = [item[2] for item in batch]
    
    # Use the options from the first request as a base
    merged_options = batch[0][1].copy()
    merged_options['model'] = model
    merged_options['temperature'] = temperature
    merged_options['max_tokens'] = max_tokens
    
    # Log batch information
    logger.info(
        f"Processing batch: provider={provider}, model={model}, "
        f"size={len(batch)}, wait_time={time.time() - start_time:.3f}s"
    )
    
    try:
        # Process batch and get results
        results = await asyncio.to_thread(batch_fn, prompts, merged_options)
        
        # Ensure we have the right number of results
        if len(results) != len(futures):
            error_msg = f"Batch function returned {len(results)} results for {len(futures)} requests"
            logger.error(error_msg)
            # Set an error for all futures
            for future in futures:
                if not future.done():
                    future.set_exception(ValueError(error_msg))
            return
        
        # Set results for each future
        for i, future in enumerate(futures):
            if not future.done():
                future.set_result(results[i])
    
    except Exception as e:
        logger.exception(f"Error processing batch: {str(e)}")
        # Set the same error for all futures
        for future in futures:
            if not future.done():
                future.set_exception(e)
