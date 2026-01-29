"""
Rate limiter implementation for FireFeed Core

Provides rate limiting functionality to prevent API abuse.
"""

import time
from collections import deque
from typing import Dict, Any, Optional


class RateLimiter:
    """
    Token bucket rate limiter implementation.
    
    Provides rate limiting to prevent API abuse and ensure fair usage.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            window_seconds: Time window in seconds
            burst_size: Maximum burst requests (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size or max_requests
        
        # Track request timestamps
        self.request_times = deque()
        self.total_requests = 0
        self.blocked_requests = 0
        self.last_request_time = None
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed.
        
        Returns:
            True if request should be allowed, False otherwise
        """
        current_time = time.time()
        
        # Remove old requests outside the time window
        while self.request_times and current_time - self.request_times[0] > self.window_seconds:
            self.request_times.popleft()
        
        # Check if we're under the rate limit
        if len(self.request_times) < self.max_requests:
            return True
        
        # Check burst limit
        if len(self.request_times) < self.burst_size:
            return True
        
        # Rate limit exceeded
        self.blocked_requests += 1
        return False
    
    def record_request(self) -> bool:
        """
        Record a request and check if it's allowed.
        
        Returns:
            True if request was recorded (allowed), False if rate limited
        """
        if self.allow_request():
            current_time = time.time()
            self.request_times.append(current_time)
            self.total_requests += 1
            self.last_request_time = current_time
            return True
        
        return False
    
    def get_retry_after(self) -> Optional[int]:
        """
        Get number of seconds to wait before next request.
        
        Returns:
            Seconds to wait, or None if can request now
        """
        if not self.request_times:
            return None
        
        current_time = time.time()
        
        # If we're under the limit, no wait needed
        if len(self.request_times) < self.max_requests:
            return None
        
        # Calculate when oldest request will expire
        oldest_request = self.request_times[0]
        wait_time = self.window_seconds - (current_time - oldest_request)
        
        return max(0, int(wait_time) + 1)
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current rate limiter usage.
        
        Returns:
            Dictionary with current usage statistics
        """
        current_time = time.time()
        
        # Remove old requests
        while self.request_times and current_time - self.request_times[0] > self.window_seconds:
            self.request_times.popleft()
        
        return {
            "current_requests": len(self.request_times),
            "max_requests": self.max_requests,
            "remaining_requests": max(0, self.max_requests - len(self.request_times)),
            "window_seconds": self.window_seconds,
            "utilization": len(self.request_times) / self.max_requests,
            "retry_after": self.get_retry_after(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with rate limiter stats
        """
        usage = self.get_current_usage()
        
        return {
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "burst_size": self.burst_size,
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": self.blocked_requests / max(1, self.total_requests + self.blocked_requests),
            "last_request_time": self.last_request_time,
            **usage
        }
    
    def reset(self):
        """Reset rate limiter counters."""
        self.request_times.clear()
        self.total_requests = 0
        self.blocked_requests = 0
        self.last_request_time = None


class SlidingWindowRateLimiter(RateLimiter):
    """
    Sliding window rate limiter with more precise timing.
    
    Uses a more accurate sliding window algorithm.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(max_requests, window_seconds)
        self.request_timestamps = []
    
    def allow_request(self) -> bool:
        """
        Check if request should be allowed using sliding window.
        """
        current_time = time.time()
        
        # Remove old requests from the window
        cutoff_time = current_time - self.window_seconds
        self.request_timestamps = [t for t in self.request_timestamps if t > cutoff_time]
        
        return len(self.request_timestamps) < self.max_requests
    
    def record_request(self) -> bool:
        """
        Record request using sliding window.
        """
        if self.allow_request():
            current_time = time.time()
            self.request_timestamps.append(current_time)
            self.total_requests += 1
            self.last_request_time = current_time
            return True
        
        return False
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current usage with sliding window calculation.
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        active_requests = len([t for t in self.request_timestamps if t > cutoff_time])
        
        return {
            "current_requests": active_requests,
            "max_requests": self.max_requests,
            "remaining_requests": max(0, self.max_requests - active_requests),
            "window_seconds": self.window_seconds,
            "utilization": active_requests / self.max_requests,
            "retry_after": self.get_retry_after(),
        }


class TokenBucketRateLimiter(RateLimiter):
    """
    Token bucket rate limiter with configurable refill rate.
    
    More sophisticated rate limiting with smooth request distribution.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        refill_rate: Optional[float] = None
    ):
        super().__init__(max_requests, window_seconds)
        self.refill_rate = refill_rate or (max_requests / window_seconds)
        self.tokens = max_requests
        self.last_refill_time = time.time()
    
    def allow_request(self) -> bool:
        """
        Check if request should be allowed using token bucket algorithm.
        """
        current_time = time.time()
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - self.last_refill_time
        tokens_to_add = time_elapsed * self.refill_rate
        self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
        self.last_refill_time = current_time
        
        if self.tokens >= 1:
            return True
        
        return False
    
    def record_request(self) -> bool:
        """
        Record request using token bucket algorithm.
        """
        if self.allow_request():
            self.tokens -= 1
            self.total_requests += 1
            self.last_request_time = time.time()
            return True
        
        return False
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current usage with token bucket information.
        """
        return {
            "current_tokens": self.tokens,
            "max_requests": self.max_requests,
            "refill_rate": self.refill_rate,
            "remaining_requests": int(self.tokens),
            "window_seconds": self.window_seconds,
            "utilization": (self.max_requests - self.tokens) / self.max_requests,
            "retry_after": self.get_retry_after(),
        }