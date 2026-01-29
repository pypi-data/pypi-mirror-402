"""
FireFeed Core Service Exceptions

Extended exception classes for service-specific error handling.
"""

from .base_exceptions import ServiceException


class TelegramException(ServiceException):
    """Base exception for Telegram-related errors"""
    pass


class TelegramBotException(TelegramException):
    """Telegram bot operation failed"""
    pass


class TelegramUserException(TelegramException):
    """Telegram user operation failed"""
    pass


class TelegramNotificationException(TelegramException):
    """Telegram notification failed"""
    pass


class TelegramSubscriptionException(TelegramException):
    """Telegram subscription operation failed"""
    pass


class TelegramCacheException(TelegramException):
    """Telegram cache operation failed"""
    pass


class TelegramHealthException(TelegramException):
    """Telegram health check failed"""
    pass


class QueueException(ServiceException):
    """Base exception for queue-related errors"""
    pass


class QueueFullException(QueueException):
    """Queue is full"""
    pass


class QueueEmptyException(QueueException):
    """Queue is empty"""
    pass


class QueueTimeoutException(QueueException):
    """Queue operation timed out"""
    pass


class TaskFailedException(QueueException):
    """Task execution failed"""
    pass


class SystemException(ServiceException):
    """Base exception for system-related errors"""
    pass


class HealthCheckException(SystemException):
    """Health check failed"""
    pass


class ConfigurationException(SystemException):
    """Configuration error"""
    pass


class MonitoringException(SystemException):
    """Monitoring operation failed"""
    pass


class CacheServiceException(ServiceException):
    """Base exception for cache service errors"""
    pass


class CacheKeyNotFoundException(CacheServiceException):
    """Cache key not found"""
    pass


class CacheConnectionException(CacheServiceException):
    """Cache connection failed"""
    pass


class CacheSerializationException(CacheServiceException):
    """Cache serialization failed"""
    pass


class TranslationServiceException(ServiceException):
    """Base exception for translation service errors"""
    pass


class TranslationModelException(TranslationServiceException):
    """Translation model error"""
    pass


class TranslationTimeoutException(TranslationServiceException):
    """Translation operation timed out"""
    pass


class TranslationRateLimitException(TranslationServiceException):
    """Translation rate limit exceeded"""
    pass


class DuplicateDetectorException(ServiceException):
    """Base exception for duplicate detector errors"""
    pass


class EmbeddingException(DuplicateDetectorException):
    """Embedding operation failed"""
    pass


class SimilarityCalculationException(DuplicateDetectorException):
    """Similarity calculation failed"""
    pass


class MaintenanceServiceException(ServiceException):
    """Base exception for maintenance service errors"""
    pass


class CleanupException(MaintenanceServiceException):
    """Cleanup operation failed"""
    pass


class DataIntegrityException(MaintenanceServiceException):
    """Data integrity check failed"""
    pass


class InterServiceException(ServiceException):
    """Base exception for inter-service communication errors"""
    pass


class ServiceUnavailableException(InterServiceException):
    """Service is unavailable"""
    pass


class ServiceTimeoutException(InterServiceException):
    """Service operation timed out"""
    pass


class ServiceAuthenticationException(InterServiceException):
    """Service authentication failed"""
    pass


class ServiceAuthorizationException(InterServiceException):
    """Service authorization failed"""
    pass


__all__ = [
    # Telegram exceptions
    "TelegramException",
    "TelegramBotException",
    "TelegramUserException",
    "TelegramNotificationException",
    "TelegramSubscriptionException",
    "TelegramCacheException",
    "TelegramHealthException",
    
    # Queue exceptions
    "QueueException",
    "QueueFullException",
    "QueueEmptyException",
    "QueueTimeoutException",
    "TaskFailedException",
    
    # System exceptions
    "SystemException",
    "HealthCheckException",
    "ConfigurationException",
    "MonitoringException",
    
    # Cache exceptions
    "CacheServiceException",
    "CacheKeyNotFoundException",
    "CacheConnectionException",
    "CacheSerializationException",
    
    # Translation exceptions
    "TranslationServiceException",
    "TranslationModelException",
    "TranslationTimeoutException",
    "TranslationRateLimitException",
    
    # Duplicate detector exceptions
    "DuplicateDetectorException",
    "EmbeddingException",
    "SimilarityCalculationException",
    
    # Maintenance exceptions
    "MaintenanceServiceException",
    "CleanupException",
    "DataIntegrityException",
    
    # Inter-service exceptions
    "InterServiceException",
    "ServiceUnavailableException",
    "ServiceTimeoutException",
    "ServiceAuthenticationException",
    "ServiceAuthorizationException",
]