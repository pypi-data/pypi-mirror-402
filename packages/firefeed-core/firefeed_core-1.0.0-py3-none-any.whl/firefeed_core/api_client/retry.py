"""
Retry policy implementation for FireFeed Core

Provides configurable retry strategies with exponential backoff.
"""

import time
import random
from typing import Dict, Any, Optional


class RetryPolicy:
    """
    Retry policy with exponential backoff and jitter.
    
    Provides different retry strategies:
    - Fixed delay
    - Exponential backoff
    - Exponential backoff with jitter
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1
    ):
        """
        Initialize retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential calculation
            jitter: Whether to add random jitter to delays
            jitter_range: Range of jitter as fraction of delay (0.0 - 1.0)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_range = jitter_range
        
        self.retry_count = 0
        self.total_retries = 0
        self.last_retry_time = None
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        if attempt >= self.max_retries:
            return 0.0
        
        # Calculate exponential backoff
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.jitter:
            jitter_amount = delay * self.jitter_range
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.1, delay)  # Minimum delay
        
        return delay
    
    def should_retry(self, attempt: int, exception: Optional[Exception] = None) -> bool:
        """
        Determine if request should be retried.
        
        Args:
            attempt: Current attempt number (0-based)
            exception: Exception that caused the failure
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt > self.max_retries:
            return False
        
        # Don't retry certain types of exceptions
        if exception:
            exception_name = exception.__class__.__name__
            
            # Don't retry client errors (4xx)
            if hasattr(exception, 'status_code'):
                if 400 <= getattr(exception, 'status_code', 0) < 500:
                    return False
            
            # Don't retry authentication and authorization errors
            if exception_name in ['AuthenticationException', 'AuthorizationException']:
                return False
        
        return True
    
    def record_retry(self):
        """Record that a retry is being performed."""
        self.retry_count += 1
        self.total_retries += 1
        self.last_retry_time = time.time()
    
    def reset(self):
        """Reset retry counters."""
        self.retry_count = 0
        self.last_retry_time = None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get retry policy statistics.
        
        Returns:
            Dictionary with retry policy stats
        """
        return {
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "exponential_base": self.exponential_base,
            "jitter_enabled": self.jitter,
            "jitter_range": self.jitter_range,
            "current_retry_count": self.retry_count,
            "total_retries": self.total_retries,
            "last_retry_time": self.last_retry_time,
        }


class ExponentialBackoffRetry(RetryPolicy):
    """
    Specialized retry policy with exponential backoff.
    
    Default configuration optimized for API calls.
    """
    
    def __init__(self, max_retries: int = 3):
        super().__init__(
            max_retries=max_retries,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            jitter_range=0.1
        )


class LinearRetry(RetryPolicy):
    """
    Retry policy with linear (fixed) delay.
    
    Useful for predictable retry patterns.
    """
    
    def __init__(self, max_retries: int = 3, delay: float = 2.0):
        super().__init__(
            max_retries=max_retries,
            base_delay=delay,
            max_delay=delay,
            exponential_base=1.0,  # No exponential growth
            jitter=False
        )


class NoRetry(RetryPolicy):
    """
    Retry policy that never retries.
    
    Useful for testing or when immediate failure is preferred.
    """
    
    def __init__(self):
        super().__init__(max_retries=0)