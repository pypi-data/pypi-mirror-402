"""
Base interfaces for FireFeed Core

Abstract base classes for common system components.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class ITelegramRepository(ABC):
    """Interface for Telegram repository operations"""
    
    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        pass
    
    @abstractmethod
    async def link_telegram_to_user(self, telegram_id: int, user_id: int) -> bool:
        """Link Telegram account to web user"""
        pass
    
    @abstractmethod
    async def unlink_telegram_from_user(self, user_id: int) -> bool:
        """Unlink Telegram account from web user"""
        pass
    
    @abstractmethod
    async def generate_link_code(self, user_id: int) -> str:
        """Generate link code for Telegram account"""
        pass
    
    @abstractmethod
    async def verify_link_code(self, telegram_id: int, link_code: str) -> bool:
        """Verify Telegram link code"""
        pass


class ILogger(ABC):
    """Interface for logging operations"""
    
    @abstractmethod
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message"""
        pass
    
    @abstractmethod
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message"""
        pass
    
    @abstractmethod
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message"""
        pass
    
    @abstractmethod
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message"""
        pass
    
    @abstractmethod
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message"""
        pass


class IDatabasePool(ABC):
    """Interface for database connection pool"""
    
    @abstractmethod
    async def acquire(self):
        """Acquire database connection"""
        pass
    
    @abstractmethod
    async def release(self, conn) -> None:
        """Release database connection"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close pool"""
        pass


class IRedisClient(ABC):
    """Interface for Redis client operations"""
    
    @abstractmethod
    def ping(self) -> bool:
        """Ping Redis server"""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis"""
        pass
    
    @abstractmethod
    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close Redis connection"""
        pass


class IMaintenanceService(ABC):
    """Interface for maintenance operations"""
    
    @abstractmethod
    async def cleanup_duplicates(self) -> None:
        """Clean up duplicate RSS items"""
        pass
    
    @abstractmethod
    async def cleanup_old_data(self, days: int) -> None:
        """Clean up old data"""
        pass
    
    @abstractmethod
    async def optimize_database(self) -> None:
        """Optimize database performance"""
        pass


class IDuplicateDetector(ABC):
    """Interface for duplicate content detection"""
    
    @abstractmethod
    async def is_duplicate(self, title: str, content: str, link: str, lang: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if content is duplicate"""
        pass
    
    @abstractmethod
    async def process_rss_item(self, rss_item_id: str, title: str, content: str, lang_code: str) -> bool:
        """Process RSS item for duplicate detection and embedding generation"""
        pass
    
    @abstractmethod
    async def get_similar_items(self, rss_item_id: str, threshold: float = 0.9) -> List[Dict[str, Any]]:
        """Get similar items based on embeddings"""
        pass


class ICache(ABC):
    """Interface for caching operations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries"""
        pass


class IHealthChecker(ABC):
    """Interface for health checking"""
    
    @abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        pass
    
    @abstractmethod
    async def check_dependencies(self) -> Dict[str, Any]:
        """Check dependency health"""
        pass


class IMetricCollector(ABC):
    """Interface for metrics collection"""
    
    @abstractmethod
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment counter metric"""
        pass
    
    @abstractmethod
    def record_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record gauge metric"""
        pass
    
    @abstractmethod
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record histogram metric"""
        pass
    
    @abstractmethod
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record timing metric"""
        pass