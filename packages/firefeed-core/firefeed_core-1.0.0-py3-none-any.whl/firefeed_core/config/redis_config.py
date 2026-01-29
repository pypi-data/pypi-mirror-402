"""
Redis configuration for FireFeed Core

This module provides comprehensive Redis configuration including
connection settings, security options, and validation for
development and production environments.
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from .validation import validate_redis_config


@dataclass
class RedisConfig:
    """Configuration for Redis connection"""
    
    # Connection settings
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    # Connection timeouts and options
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, Any] = field(default_factory=dict)
    connection_pool_kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # Security and performance
    ssl: bool = False
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_cert_reqs: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    
    # Health check settings
    health_check_interval: int = 30
    max_connections: int = 50
    retry_on_timeout: bool = True
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Create RedisConfig from environment variables"""
        return cls(
            # Connection settings
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD'),
            
            # Connection timeouts and options
            socket_timeout=int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
            socket_connect_timeout=int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5')),
            socket_keepalive=os.getenv('REDIS_SOCKET_KEEPALIVE', 'true').lower() == 'true',
            
            # Security and performance
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            ssl_certfile=os.getenv('REDIS_SSL_CERTFILE'),
            ssl_keyfile=os.getenv('REDIS_SSL_KEYFILE'),
            ssl_cert_reqs=os.getenv('REDIS_SSL_CERT_REQS'),
            ssl_ca_certs=os.getenv('REDIS_SSL_CA_CERTS'),
            
            # Health check settings
            health_check_interval=int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30')),
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
            retry_on_timeout=os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
        )
    
    @classmethod
    def from_url(cls, redis_url: str) -> 'RedisConfig':
        """Create RedisConfig from Redis URL"""
        from urllib.parse import urlparse
        
        parsed = urlparse(redis_url)
        
        config = cls(
            host=parsed.hostname or 'localhost',
            port=parsed.port or 6379,
            db=int(parsed.path.lstrip('/')) if parsed.path else 0,
            password=parsed.password
        )
        
        # Handle SSL if specified in URL
        if parsed.scheme in ['rediss', 'redis+ssl']:
            config.ssl = True
        
        return config
    
    def to_url(self) -> str:
        """Convert RedisConfig to Redis URL"""
        scheme = "rediss" if self.ssl else "redis"
        password_part = f":{self.password}@" if self.password else ""
        
        return f"{scheme}://{password_part}{self.host}:{self.port}/{self.db}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RedisConfig to dictionary for Redis client"""
        config_dict = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'socket_timeout': self.socket_timeout,
            'socket_connect_timeout': self.socket_connect_timeout,
            'socket_keepalive': self.socket_keepalive,
            'max_connections': self.max_connections,
            'retry_on_timeout': self.retry_on_timeout
        }
        
        if self.password:
            config_dict['password'] = self.password
        
        if self.ssl:
            config_dict['ssl'] = True
            if self.ssl_certfile:
                config_dict['ssl_certfile'] = self.ssl_certfile
            if self.ssl_keyfile:
                config_dict['ssl_keyfile'] = self.ssl_keyfile
            if self.ssl_cert_reqs:
                config_dict['ssl_cert_reqs'] = self.ssl_cert_reqs
            if self.ssl_ca_certs:
                config_dict['ssl_ca_certs'] = self.ssl_ca_certs
        
        # Add socket keepalive options if provided
        if self.socket_keepalive_options:
            config_dict['socket_keepalive_options'] = self.socket_keepalive_options
        
        # Add connection pool kwargs if provided
        if self.connection_pool_kwargs:
            config_dict.update(self.connection_pool_kwargs)
        
        return config_dict
    
    def validate(self) -> List[str]:
        """Validate Redis configuration"""
        errors = []
        
        # Validate host
        if not self.host:
            errors.append("Redis host cannot be empty")
        
        # Validate port
        if not (1 <= self.port <= 65535):
            errors.append("Redis port must be between 1 and 65535")
        
        # Validate database number
        if self.db < 0:
            errors.append("Redis database number must be non-negative")
        
        # Validate timeouts
        if self.socket_timeout <= 0:
            errors.append("Redis socket timeout must be positive")
        
        if self.socket_connect_timeout <= 0:
            errors.append("Redis socket connect timeout must be positive")
        
        # Validate health check interval
        if self.health_check_interval < 0:
            errors.append("Redis health check interval must be non-negative")
        
        # Validate max connections
        if self.max_connections <= 0:
            errors.append("Redis max connections must be positive")
        
        # Security warnings for production
        if self.host in ['localhost', '127.0.0.1'] and self.password is None:
            errors.append("Using localhost without password - only for development!")
        
        # SSL validation
        if self.ssl:
            if self.ssl_cert_reqs and self.ssl_cert_reqs not in ['none', 'optional', 'required']:
                errors.append("Redis SSL cert_reqs must be 'none', 'optional', or 'required'")
        
        return errors
    
    def is_development(self) -> bool:
        """Check if this is a development configuration"""
        return (
            self.host in ['localhost', '127.0.0.1'] and
            self.port == 6379 and
            self.db == 0 and
            self.password is None
        )
    
    def get_health_check_config(self) -> Dict[str, Any]:
        """Get configuration for health checks"""
        return {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'password': self.password,
            'socket_timeout': self.socket_timeout,
            'interval': self.health_check_interval
        }
    
    def __str__(self) -> str:
        """String representation (safe for logging)"""
        password_display = "*****" if self.password else "None"
        return (f"RedisConfig(host={self.host}, port={self.port}, "
                f"db={self.db}, password={password_display}, ssl={self.ssl})")
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return self.__str__()


# Backward compatibility aliases
RedisConfiguration = RedisConfig