"""
Retry Utilities

Common retry utilities for FireFeed microservices.
"""

import asyncio
import logging
import random
import time
from typing import Callable, Any, Optional, Type, Union, List
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0,
                 jitter: bool = True, exceptions: Optional[List[Type[Exception]]] = None):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.exceptions = exceptions or [Exception]


def exponential_backoff(attempt: int, base_delay: float = 1.0, 
                       max_delay: float = 60.0, backoff_factor: float = 2.0,
                       jitter: bool = True) -> float:
    """
    Calculate delay using exponential backoff with jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Backoff multiplier
        jitter: Add random jitter
        
    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (backoff_factor ** attempt), max_delay)
    
    if jitter:
        # Add jitter (random value between 0 and delay)
        delay = delay * random.uniform(0.5, 1.5)
    
    return delay


def constant_backoff(attempt: int, delay: float = 1.0, jitter: bool = True) -> float:
    """
    Calculate delay using constant backoff with jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        delay: Constant delay in seconds
        jitter: Add random jitter
        
    Returns:
        Delay in seconds
    """
    if jitter:
        # Add jitter (random value between 0 and delay)
        return delay * random.uniform(0.5, 1.5)
    else:
        return delay


def fibonacci_backoff(attempt: int, base_delay: float = 1.0,
                     max_delay: float = 60.0, jitter: bool = True) -> float:
    """
    Calculate delay using Fibonacci backoff with jitter.
    
    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay multiplier in seconds
        max_delay: Maximum delay in seconds
        jitter: Add random jitter
        
    Returns:
        Delay in seconds
    """
    # Calculate Fibonacci number
    if attempt <= 1:
        fib = 1
    else:
        a, b = 1, 1
        for _ in range(attempt - 1):
            a, b = b, a + b
        fib = b
    
    delay = min(fib * base_delay, max_delay)
    
    if jitter:
        delay = delay * random.uniform(0.5, 1.5)
    
    return delay


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Backoff multiplier
        jitter: Add random jitter to delays
        exceptions: List of exceptions to catch and retry on
        on_retry: Callback function called on each retry
        
    Returns:
        Decorated function
    """
    if exceptions is None:
        exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
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
                    delay = exponential_backoff(
                        attempt, base_delay, max_delay, backoff_factor, jitter
                    )
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    # Calculate delay
                    delay = exponential_backoff(
                        attempt, base_delay, max_delay, backoff_factor, jitter
                    )
                    
                    logger.warning(
                        f"Function {func.__name__} failed on attempt {attempt + 1}/{max_attempts}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e, delay)
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")
                    
                    # Wait before retry
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RetryManager:
    """Manager for retry operations with different strategies"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except tuple(self.config.exceptions) as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    logger.error(f"Function {func.__name__} failed after {self.config.max_attempts} attempts: {e}")
                    raise
                
                # Calculate delay
                delay = exponential_backoff(
                    attempt, self.config.base_delay, self.config.max_delay, 
                    self.config.backoff_factor, self.config.jitter
                )
                
                logger.warning(
                    f"Function {func.__name__} failed on attempt {attempt + 1}/{self.config.max_attempts}: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def create_retry_decorator(self) -> Callable:
        """Create a retry decorator with current configuration"""
        return retry_with_backoff(
            max_attempts=self.config.max_attempts,
            base_delay=self.config.base_delay,
            max_delay=self.config.max_delay,
            backoff_factor=self.config.backoff_factor,
            jitter=self.config.jitter,
            exceptions=self.config.exceptions
        )


def retry_on_network_errors(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying on network-related errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        
    Returns:
        Decorated function
    """
    network_exceptions = [
        ConnectionError,
        TimeoutError,
        asyncio.TimeoutError,
        OSError,
        ConnectionRefusedError,
        ConnectionResetError,
    ]
    
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        exceptions=network_exceptions
    )


def retry_on_database_errors(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for retrying on database-related errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        
    Returns:
        Decorated function
    """
    database_exceptions = [
        Exception,  # Generic exception for database errors
    ]
    
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        exceptions=database_exceptions
    )


def retry_on_rate_limit(max_attempts: int = 5, base_delay: float = 2.0):
    """
    Decorator for retrying on rate limit errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        
    Returns:
        Decorated function
    """
    rate_limit_exceptions = [
        Exception,  # Should be specific rate limit exceptions
    ]
    
    return retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=base_delay,
        backoff_factor=1.5,  # Slower backoff for rate limits
        exceptions=rate_limit_exceptions
    )