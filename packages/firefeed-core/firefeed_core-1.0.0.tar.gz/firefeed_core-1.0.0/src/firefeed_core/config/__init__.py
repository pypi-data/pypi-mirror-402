"""
Redis configuration module for FireFeed Core

This module provides Redis configuration classes and utilities
for consistent Redis usage across all FireFeed services.
"""

from .redis_config import RedisConfig, RedisConfiguration
from .redis_utils import (
    RedisClientFactory,
    RedisHealthChecker,
    RedisKeyBuilder,
    RedisFactory,
    RedisUtils
)

__all__ = [
    # Configuration classes
    'RedisConfig',
    'RedisConfiguration',
    
    # Factory and utilities
    'RedisClientFactory',
    'RedisHealthChecker',
    'RedisKeyBuilder',
    
    # Backward compatibility aliases
    'RedisFactory',
    'RedisUtils'
]