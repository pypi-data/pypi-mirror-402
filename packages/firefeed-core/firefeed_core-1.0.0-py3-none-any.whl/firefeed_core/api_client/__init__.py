"""
FireFeed Core API Client

Provides HTTP client functionality for inter-service communication.
"""

from .client import APIClient
from .circuit_breaker import CircuitBreaker
from .retry import RetryPolicy
from .rate_limiter import RateLimiter

__all__ = [
    "APIClient",
    "CircuitBreaker", 
    "RetryPolicy",
    "RateLimiter",
]