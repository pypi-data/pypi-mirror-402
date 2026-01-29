"""
Async Utilities

Common asynchronous utilities for FireFeed microservices.
"""

import asyncio
import logging
from typing import Callable, Any, List, Optional, Union, Coroutine, Generator, AsyncGenerator
from contextlib import asynccontextmanager
from functools import wraps

logger = logging.getLogger(__name__)


@asynccontextmanager
async def async_timeout(timeout: float):
    """
    Async context manager for timeouts.
    
    Args:
        timeout: Timeout in seconds
        
    Yields:
        None
        
    Raises:
        asyncio.TimeoutError: If operation times out
    """
    try:
        yield
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout} seconds")
        raise


@asynccontextmanager
async def async_semaphore(semaphore: asyncio.Semaphore):
    """
    Async context manager for semaphores.
    
    Args:
        semaphore: Asyncio semaphore
        
    Yields:
        None
    """
    async with semaphore:
        yield


async def async_batch_processor(
    items: List[Any],
    processor: Callable[[Any], Coroutine],
    batch_size: int = 10,
    max_concurrent: int = 5,
    delay: float = 0.1
) -> List[Any]:
    """
    Process items in batches with concurrency control.
    
    Args:
        items: List of items to process
        processor: Async function to process each item
        batch_size: Number of items per batch
        max_concurrent: Maximum concurrent operations
        delay: Delay between batches in seconds
        
    Returns:
        List of processed results
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_item(item):
        async with semaphore:
            return await processor(item)
    
    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_tasks = [process_item(item) for item in batch]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Handle exceptions
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
            else:
                results.append(result)
        
        # Delay between batches
        if i + batch_size < len(items) and delay > 0:
            await asyncio.sleep(delay)
    
    return results


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Optional[List[type]] = None
):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Backoff multiplier
        exceptions: List of exceptions to catch and retry on
        
    Returns:
        Decorated async function
    """
    if exceptions is None:
        exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    # Calculate delay
                    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    
    return decorator


async def async_wait_for_condition(
    condition: Callable[[], Coroutine],
    timeout: float = 30.0,
    check_interval: float = 1.0,
    error_message: str = "Condition not met"
) -> bool:
    """
    Wait for an async condition to become true.
    
    Args:
        condition: Async function that returns a boolean
        timeout: Maximum wait time in seconds
        check_interval: Interval between condition checks in seconds
        error_message: Error message if condition is not met
        
    Returns:
        True if condition was met, False otherwise
        
    Raises:
        asyncio.TimeoutError: If timeout is reached
    """
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if await condition():
            return True
        
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            raise asyncio.TimeoutError(f"{error_message} (timeout: {timeout}s)")
        
        await asyncio.sleep(check_interval)


async def async_race(*coroutines: Coroutine, timeout: Optional[float] = None) -> Any:
    """
    Race multiple coroutines and return the result of the first one to complete.
    
    Args:
        *coroutines: Coroutines to race
        timeout: Optional timeout in seconds
        
    Returns:
        Result of the first completed coroutine
        
    Raises:
        asyncio.TimeoutError: If timeout is reached
    """
    if timeout:
        return await asyncio.wait_for(
            asyncio.shield(asyncio.gather(*coroutines, return_exceptions=True)),
            timeout=timeout
        )
    else:
        done, pending = await asyncio.wait(
            coroutines,
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel remaining tasks
        for task in pending:
            task.cancel()
        
        # Return result of first completed task
        return done.pop().result()


async def async_throttle(
    func: Callable,
    *args,
    delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Throttle function calls with a delay.
    
    Args:
        func: Function to call
        *args: Function arguments
        delay: Delay in seconds
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    result = await func(*args, **kwargs)
    await asyncio.sleep(delay)
    return result


async def async_debounce(
    func: Callable,
    *args,
    delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Debounce function calls by delaying execution.
    
    Args:
        func: Function to call
        *args: Function arguments
        delay: Delay in seconds
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
    """
    await asyncio.sleep(delay)
    return await func(*args, **kwargs)


class AsyncQueue:
    """Enhanced async queue with additional features"""
    
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._closed = False
    
    async def put(self, item: Any) -> None:
        """Put item in queue"""
        if self._closed:
            raise asyncio.InvalidStateError("Queue is closed")
        await self._queue.put(item)
    
    async def get(self) -> Any:
        """Get item from queue"""
        return await self._queue.get()
    
    async def join(self) -> None:
        """Wait until all items are processed"""
        await self._queue.join()
    
    def task_done(self) -> None:
        """Mark task as done"""
        self._queue.task_done()
    
    def close(self) -> None:
        """Close the queue"""
        self._closed = True
    
    @property
    def empty(self) -> bool:
        """Check if queue is empty"""
        return self._queue.empty()
    
    @property
    def full(self) -> bool:
        """Check if queue is full"""
        return self._queue.full()
    
    @property
    def qsize(self) -> int:
        """Get queue size"""
        return self._queue.qsize()


async def async_generator_with_timeout(
    generator: Generator,
    timeout: float = 30.0
) -> AsyncGenerator:
    """
    Convert sync generator to async generator with timeout.
    
    Args:
        generator: Synchronous generator
        timeout: Timeout in seconds
        
    Yields:
        Generator items
    """
    for item in generator:
        try:
            yield await asyncio.wait_for(
                asyncio.to_thread(lambda: item),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Generator item processing timed out after {timeout} seconds")
            break


async def async_map(
    func: Callable,
    iterable: List[Any],
    max_concurrent: int = 10
) -> List[Any]:
    """
    Apply function to iterable with concurrency control.
    
    Args:
        func: Function to apply
        iterable: List of items
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def apply_func(item):
        async with semaphore:
            return await func(item)
    
    tasks = [apply_func(item) for item in iterable]
    return await asyncio.gather(*tasks)


async def async_filter(
    predicate: Callable,
    iterable: List[Any],
    max_concurrent: int = 10
) -> List[Any]:
    """
    Filter iterable with async predicate and concurrency control.
    
    Args:
        predicate: Async function that returns boolean
        iterable: List of items
        max_concurrent: Maximum concurrent operations
        
    Returns:
        List of filtered items
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def check_item(item):
        async with semaphore:
            return await predicate(item)
    
    results = await asyncio.gather(*[check_item(item) for item in iterable])
    return [item for item, should_include in zip(iterable, results) if should_include]


async def async_reduce(
    func: Callable,
    iterable: List[Any],
    initializer: Optional[Any] = None
) -> Any:
    """
    Reduce iterable with async function.
    
    Args:
        func: Async reduction function
        iterable: List of items
        initializer: Initial value
        
    Returns:
        Reduced value
    """
    if initializer is None:
        result = iterable[0]
        iterable = iterable[1:]
    else:
        result = initializer
    
    for item in iterable:
        result = await func(result, item)
    
    return result