"""
FireFeed Core Exceptions

Common exception classes used across all FireFeed microservices.
"""

from .base_exceptions import (
    FireFeedException,
    ConfigurationException,
    ValidationException,
    NotFoundException,
    ConflictException,
)

from .api_exceptions import (
    APIException,
    AuthenticationException,
    AuthorizationException,
    RateLimitException,
    ServiceUnavailableException,
)

from .service_exceptions import (
    ServiceException,
    TelegramException,
    TelegramBotException,
    TelegramUserException,
    TelegramNotificationException,
    TelegramSubscriptionException,
    TelegramCacheException,
    TelegramHealthException,
    QueueException,
    QueueFullException,
    QueueEmptyException,
    QueueTimeoutException,
    TaskFailedException,
    SystemException,
    HealthCheckException,
    MonitoringException,
    CacheServiceException,
    CacheKeyNotFoundException,
    CacheConnectionException,
    CacheSerializationException,
    TranslationServiceException,
    TranslationModelException,
    TranslationTimeoutException,
    TranslationRateLimitException,
    DuplicateDetectorException,
    EmbeddingException,
    SimilarityCalculationException,
    MaintenanceServiceException,
    CleanupException,
    DataIntegrityException,
    InterServiceException,
    ServiceUnavailableException,
    ServiceTimeoutException,
    ServiceAuthenticationException,
    ServiceAuthorizationException,
)

from .rss_exceptions import (
    RSSException,
    RSSParseException,
    RSSFetchError as RSSFetchException,
)

from .database_exceptions import (
    DatabaseException,
    DatabaseConnectionError,
    DatabaseQueryError,
)

__all__ = [
    # Base exceptions
    "FireFeedException",
    "ConfigurationException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
    
    # API exceptions
    "APIException",
    "AuthenticationException",
    "AuthorizationException",
    "RateLimitException",
    "ServiceUnavailableException",
    
    # Service exceptions
    "ServiceException",
    
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
    
    # RSS exceptions
    "RSSException",
    "RSSParseException",
    "RSSFetchException",
    "RSSValidationException",
    "RSSStorageException",
    "RSSConfigurationException",
    "RSSFeedException",
    "RSSItemException",
    "RSSSourceException",
    "RSSDuplicateException",
    "RSSRateLimitException",
    "RSSCacheException",
    "RSSNetworkException",
    "RSSValidationError",

    # Database exceptions
    "DatabaseException",
    "DatabaseConnectionError",
    "DatabaseQueryError",
]