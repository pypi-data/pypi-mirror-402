"""
Redis utilities for FireFeed Core

This module provides Redis client factory and utility functions
for consistent Redis usage across all FireFeed services.
"""

import redis
from typing import Optional, Dict, Any, Union
from .redis_config import RedisConfig


class RedisClientFactory:
    """Factory for creating Redis clients with consistent configuration"""
    
    @staticmethod
    def create_client(
        config: Optional[RedisConfig] = None,
        **kwargs: Any
    ) -> redis.Redis:
        """
        Create a Redis client with the given configuration
        
        Args:
            config: Redis configuration object
            **kwargs: Additional arguments to pass to Redis client
            
        Returns:
            Configured Redis client instance
        """
        if config is None:
            config = RedisConfig.from_env()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid Redis configuration: {', '.join(errors)}")
        
        # Get base configuration
        client_config = config.to_dict()
        
        # Override with any additional kwargs
        client_config.update(kwargs)
        
        try:
            # Create Redis client
            client = redis.Redis(**client_config)
            
            # Test connection
            client.ping()
            
            return client
            
        except redis.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to create Redis client: {e}")
    
    @staticmethod
    def create_from_url(
        redis_url: str,
        **kwargs: Any
    ) -> redis.Redis:
        """
        Create a Redis client from a Redis URL
        
        Args:
            redis_url: Redis connection URL
            **kwargs: Additional arguments to pass to Redis client
            
        Returns:
            Configured Redis client instance
        """
        config = RedisConfig.from_url(redis_url)
        return RedisClientFactory.create_client(config, **kwargs)
    
    @staticmethod
    def create_pool(
        config: Optional[RedisConfig] = None,
        **kwargs: Any
    ) -> redis.ConnectionPool:
        """
        Create a Redis connection pool with the given configuration
        
        Args:
            config: Redis configuration object
            **kwargs: Additional arguments to pass to connection pool
            
        Returns:
            Configured Redis connection pool
        """
        if config is None:
            config = RedisConfig.from_env()
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid Redis configuration: {', '.join(errors)}")
        
        # Get base configuration
        pool_config = config.to_dict()
        
        # Override with any additional kwargs
        pool_config.update(kwargs)
        
        try:
            # Create connection pool
            pool = redis.ConnectionPool(**pool_config)
            return pool
            
        except Exception as e:
            raise RuntimeError(f"Failed to create Redis connection pool: {e}")


class RedisHealthChecker:
    """Health checker for Redis connections"""
    
    @staticmethod
    def check_health(
        client: redis.Redis,
        timeout: int = 5
    ) -> Dict[str, Union[bool, str]]:
        """
        Check Redis connection health
        
        Args:
            client: Redis client instance
            timeout: Timeout for health check in seconds
            
        Returns:
            Health check result with status and details
        """
        try:
            # Test basic ping
            client.ping()
            
            # Get Redis info
            info = client.info()
            
            return {
                'status': True,
                'message': 'Redis connection is healthy',
                'version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown')
            }
            
        except redis.ConnectionError as e:
            return {
                'status': False,
                'message': f'Redis connection failed: {e}'
            }
        except Exception as e:
            return {
                'status': False,
                'message': f'Redis health check failed: {e}'
            }


class RedisKeyBuilder:
    """Utility class for building consistent Redis keys"""
    
    @staticmethod
    def build_key(
        namespace: str,
        *parts: str,
        separator: str = ':'
    ) -> str:
        """
        Build a Redis key with namespace and parts
        
        Args:
            namespace: Key namespace (e.g., 'firefeed', 'api', 'parser')
            *parts: Key parts to join
            separator: Separator to use between parts
            
        Returns:
            Formatted Redis key
        """
        # Clean and validate namespace
        if not namespace or not namespace.strip():
            raise ValueError("Namespace cannot be empty")
        
        # Clean and validate parts
        clean_parts = []
        for part in parts:
            if part is not None and str(part).strip():
                clean_parts.append(str(part).strip())
        
        # Build key
        key_parts = [namespace.strip()] + clean_parts
        return separator.join(key_parts)
    
    @staticmethod
    def build_user_key(
        user_id: Union[int, str],
        key_type: str = 'default',
        namespace: str = 'firefeed'
    ) -> str:
        """Build a user-specific Redis key"""
        return RedisKeyBuilder.build_key(namespace, 'user', str(user_id), key_type)
    
    @staticmethod
    def build_feed_key(
        feed_id: Union[int, str],
        key_type: str = 'default',
        namespace: str = 'firefeed'
    ) -> str:
        """Build a feed-specific Redis key"""
        return RedisKeyBuilder.build_key(namespace, 'feed', str(feed_id), key_type)
    
    @staticmethod
    def build_item_key(
        item_id: Union[int, str],
        key_type: str = 'default',
        namespace: str = 'firefeed'
    ) -> str:
        """Build an item-specific Redis key"""
        return RedisKeyBuilder.build_key(namespace, 'item', str(item_id), key_type)


# Backward compatibility aliases
RedisFactory = RedisClientFactory
RedisUtils = RedisKeyBuilder