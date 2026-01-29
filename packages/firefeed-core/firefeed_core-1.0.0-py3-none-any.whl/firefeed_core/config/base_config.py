"""
FireFeed Core Configuration Base Classes

Base configuration classes for centralized configuration management.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class BaseConfig(ABC):
    """Base configuration class with common functionality"""
    
    @classmethod
    @abstractmethod
    def from_env(cls) -> 'BaseConfig':
        """Create configuration from environment variables"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        import dataclasses
        return dataclasses.asdict(self)
    
    def get(self, key: str, default=None):
        """Dict-like get method for compatibility"""
        attr_name = key.lower().replace('-', '_')
        return getattr(self, attr_name, default)


@dataclass
class ServiceConfig(BaseConfig):
    """Main service configuration"""
    redis: 'RedisConfig'
    rss: 'RSSConfig'
    translation: 'TranslationConfig'
    cache: 'CacheConfig'
    queue: 'QueueConfig'
    telegram: 'TelegramConfig'
    monitoring: 'MonitoringConfig'
    security: 'SecurityConfig'
    
    # Additional config keys
    service_name: str = "firefeed-service"
    service_version: str = "1.0.0"
    log_level: str = "INFO"
    api_base_url: str = "http://localhost:8000"
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    http_images_root_dir: str = ""
    images_root_dir: str = ""
    videos_root_dir: str = ""
    http_videos_root_dir: str = ""
    site_api_key: Optional[str] = None
    user_data_ttl_seconds: int = 86400
    rss_parser_media_type_priority: str = "image"
    rss_parser_cleanup_interval_hours: int = 0  # 0 = disabled
    default_user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    
    def __post_init__(self):
        if not isinstance(self.redis, RedisConfig):
            self.redis = RedisConfig.from_env()
        if not isinstance(self.rss, RSSConfig):
            self.rss = RSSConfig.from_env()
        if not isinstance(self.translation, TranslationConfig):
            self.translation = TranslationConfig.from_env()
        if not isinstance(self.cache, CacheConfig):
            self.cache = CacheConfig.from_env()
        if not isinstance(self.queue, QueueConfig):
            self.queue = QueueConfig.from_env()
        if not isinstance(self.telegram, TelegramConfig):
            self.telegram = TelegramConfig.from_env()
        if not isinstance(self.monitoring, MonitoringConfig):
            self.monitoring = MonitoringConfig.from_env()
        if not isinstance(self.security, SecurityConfig):
            self.security = SecurityConfig.from_env()
    
    @classmethod
    def from_env(cls) -> 'ServiceConfig':
        return cls(
            redis=RedisConfig.from_env(),
            rss=RSSConfig.from_env(),
            translation=TranslationConfig.from_env(),
            cache=CacheConfig.from_env(),
            queue=QueueConfig.from_env(),
            telegram=TelegramConfig.from_env(),
            monitoring=MonitoringConfig.from_env(),
            security=SecurityConfig.from_env(),
            service_name=os.getenv('SERVICE_NAME', 'firefeed-service'),
            service_version=os.getenv('SERVICE_VERSION', '1.0.0'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            api_base_url=os.getenv('API_BASE_URL', 'http://localhost:8000'),
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
            jwt_access_token_expire_minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            http_images_root_dir=os.getenv('HTTP_IMAGES_ROOT_DIR', ''),
            images_root_dir=os.getenv('IMAGES_ROOT_DIR', ''),
            videos_root_dir=os.getenv('VIDEOS_ROOT_DIR', ''),
            http_videos_root_dir=os.getenv('HTTP_VIDEOS_ROOT_DIR', ''),
            site_api_key=os.getenv('SITE_API_KEY'),
            user_data_ttl_seconds=int(os.getenv('USER_DATA_TTL_SECONDS', '86400')),
            rss_parser_media_type_priority=os.getenv('RSS_PARSER_MEDIA_TYPE_PRIORITY', 'image'),
            default_user_agent=os.getenv('DEFAULT_USER_AGENT', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        )


@dataclass
class RedisConfig(BaseConfig):
    """Configuration for Redis connection"""
    host: str = "localhost"
    port: int = 6379
    username: Optional[str] = None
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, Any] = field(default_factory=dict)
    health_check_interval: int = 30
    retry_on_timeout: bool = True
    max_connections: int = 50
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            username=os.getenv('REDIS_USERNAME') or None,
            password=os.getenv('REDIS_PASSWORD') or None,
            db=int(os.getenv('REDIS_DB', '0')),
            ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            socket_timeout=int(os.getenv('REDIS_SOCKET_TIMEOUT', '5')),
            socket_connect_timeout=int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5')),
            socket_keepalive=os.getenv('REDIS_SOCKET_KEEPALIVE', 'true').lower() == 'true',
            health_check_interval=int(os.getenv('REDIS_HEALTH_CHECK_INTERVAL', '30')),
            retry_on_timeout=os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true',
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
        )


@dataclass
class CacheConfig(BaseConfig):
    """Configuration for caching services"""
    default_ttl: int = 3600  # 1 hour
    max_cache_size: int = 10000
    cleanup_interval: int = 300  # 5 minutes
    enable_cleanup: bool = True
    compression_enabled: bool = False
    compression_level: int = 6
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        return cls(
            default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', '3600')),
            max_cache_size=int(os.getenv('CACHE_MAX_SIZE', '10000')),
            cleanup_interval=int(os.getenv('CACHE_CLEANUP_INTERVAL', '300')),
            enable_cleanup=os.getenv('CACHE_ENABLE_CLEANUP', 'true').lower() == 'true',
            compression_enabled=os.getenv('CACHE_COMPRESSION_ENABLED', 'false').lower() == 'true',
            compression_level=int(os.getenv('CACHE_COMPRESSION_LEVEL', '6'))
        )


@dataclass
class QueueConfig(BaseConfig):
    """Configuration for queue services"""
    max_queue_size: int = 30
    default_workers: int = 1
    task_timeout: int = 300  # 5 minutes
    retry_attempts: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    enable_priority: bool = False
    enable_persistence: bool = False
    
    @classmethod
    def from_env(cls) -> 'QueueConfig':
        return cls(
            max_queue_size=int(os.getenv('QUEUE_MAX_SIZE', '30')),
            default_workers=int(os.getenv('QUEUE_DEFAULT_WORKERS', '1')),
            task_timeout=int(os.getenv('QUEUE_TASK_TIMEOUT', '300')),
            retry_attempts=int(os.getenv('QUEUE_RETRY_ATTEMPTS', '3')),
            retry_delay=float(os.getenv('QUEUE_RETRY_DELAY', '1.0')),
            max_retry_delay=float(os.getenv('QUEUE_MAX_RETRY_DELAY', '60.0')),
            enable_priority=os.getenv('QUEUE_ENABLE_PRIORITY', 'false').lower() == 'true',
            enable_persistence=os.getenv('QUEUE_ENABLE_PERSISTENCE', 'false').lower() == 'true'
        )


@dataclass
class TranslationConfig(BaseConfig):
    """Configuration for translation services"""
    model_name: str = "facebook/m2m100_418M"
    max_concurrent_translations: int = 3
    max_cached_models: int = 15
    model_cleanup_interval: int = 1800  # 30 minutes
    default_device: str = "cpu"
    max_workers: int = 4
    translation_enabled: bool = True
    batch_size: int = 10
    context_window: int = 2
    beam_size: Optional[int] = None
    enable_cache: bool = True
    cache_ttl: int = 3600
    
    @classmethod
    def from_env(cls) -> 'TranslationConfig':
        return cls(
            model_name=os.getenv('TRANSLATION_MODEL', 'facebook/m2m100_418M'),
            max_concurrent_translations=int(os.getenv('TRANSLATION_MAX_CONCURRENT', '3')),
            max_cached_models=int(os.getenv('TRANSLATION_MAX_CACHED_MODELS', '15')),
            model_cleanup_interval=int(os.getenv('TRANSLATION_CLEANUP_INTERVAL', '1800')),
            default_device=os.getenv('TRANSLATION_DEVICE', 'cpu'),
            max_workers=int(os.getenv('TRANSLATION_MAX_WORKERS', '4')),
            translation_enabled=os.getenv('TRANSLATION_ENABLED', 'true').lower() == 'true',
            batch_size=int(os.getenv('TRANSLATION_BATCH_SIZE', '10')),
            context_window=int(os.getenv('TRANSLATION_CONTEXT_WINDOW', '2')),
            beam_size=int(os.getenv('TRANSLATION_BEAM_SIZE', 'None')) if os.getenv('TRANSLATION_BEAM_SIZE') != 'None' else None,
            enable_cache=os.getenv('TRANSLATION_ENABLE_CACHE', 'true').lower() == 'true',
            cache_ttl=int(os.getenv('TRANSLATION_CACHE_TTL', '3600'))
        )


@dataclass
class RSSConfig(BaseConfig):
    """Configuration for RSS services"""
    max_concurrent_feeds: int = 10
    max_entries_per_feed: int = 50
    validation_cache_ttl: int = 300  # 5 minutes
    request_timeout: int = 15
    max_total_rss_items: int = 1000
    min_item_title_words_length: int = 0
    min_item_content_words_length: int = 0
    cleanup_interval_hours: int = 0  # 0 = disabled
    media_type_priority: str = "image"
    enable_duplicate_detection: bool = True
    similarity_threshold: float = 0.9
    max_feed_cooldown_minutes: int = 60
    
    @classmethod
    def from_env(cls) -> 'RSSConfig':
        return cls(
            max_concurrent_feeds=int(os.getenv('RSS_MAX_CONCURRENT_FEEDS', '10')),
            max_entries_per_feed=int(os.getenv('RSS_MAX_ENTRIES_PER_FEED', '50')),
            validation_cache_ttl=int(os.getenv('RSS_VALIDATION_CACHE_TTL', '300')),
            request_timeout=int(os.getenv('RSS_REQUEST_TIMEOUT', '15')),
            max_total_rss_items=int(os.getenv('RSS_MAX_TOTAL_ITEMS', '1000')),
            min_item_title_words_length=int(os.getenv('RSS_PARSER_MIN_ITEM_TITLE_WORDS_LENGTH', '0')),
            min_item_content_words_length=int(os.getenv('RSS_PARSER_MIN_ITEM_CONTENT_WORDS_LENGTH', '0')),
            cleanup_interval_hours=int(os.getenv('RSS_PARSER_CLEANUP_INTERVAL_HOURS', '0')),
            media_type_priority=os.getenv('RSS_PARSER_MEDIA_TYPE_PRIORITY', 'image'),
            enable_duplicate_detection=os.getenv('RSS_ENABLE_DUPLICATE_DETECTION', 'true').lower() == 'true',
            similarity_threshold=float(os.getenv('RSS_SIMILARITY_THRESHOLD', '0.9')),
            max_feed_cooldown_minutes=int(os.getenv('RSS_MAX_FEED_COOLDOWN_MINUTES', '60'))
        )


@dataclass
class TelegramConfig(BaseConfig):
    """Configuration for Telegram bot"""
    bot_token: str = ""
    bot_name: str = ""
    bot_username: str = ""
    bot_id: int = 0
    bot_first_name: str = ""
    bot_last_name: str = ""
    bot_language_code: str = "en"
    webhook_url: str = ""
    webhook_secret_token: str = ""
    max_message_length: int = 4096
    rate_limit_requests: int = 30
    rate_limit_window: int = 60
    enable_webhook: bool = True
    polling_timeout: int = 20
    allowed_updates: List[str] = field(default_factory=lambda: ["message", "callback_query"])
    
    @classmethod
    def from_env(cls) -> 'TelegramConfig':
        return cls(
            bot_token=os.getenv('TELEGRAM_BOT_TOKEN', ''),
            bot_name=os.getenv('TELEGRAM_BOT_NAME', ''),
            bot_username=os.getenv('TELEGRAM_BOT_USERNAME', ''),
            bot_id=int(os.getenv('TELEGRAM_BOT_ID', '0')),
            bot_first_name=os.getenv('TELEGRAM_BOT_FIRST_NAME', ''),
            bot_last_name=os.getenv('TELEGRAM_BOT_LAST_NAME', ''),
            bot_language_code=os.getenv('TELEGRAM_BOT_LANGUAGE_CODE', 'en'),
            webhook_url=os.getenv('TELEGRAM_WEBHOOK_URL', ''),
            webhook_secret_token=os.getenv('TELEGRAM_WEBHOOK_SECRET_TOKEN', ''),
            max_message_length=int(os.getenv('TELEGRAM_MAX_MESSAGE_LENGTH', '4096')),
            rate_limit_requests=int(os.getenv('TELEGRAM_RATE_LIMIT_REQUESTS', '30')),
            rate_limit_window=int(os.getenv('TELEGRAM_RATE_LIMIT_WINDOW', '60')),
            enable_webhook=os.getenv('TELEGRAM_ENABLE_WEBHOOK', 'true').lower() == 'true',
            polling_timeout=int(os.getenv('TELEGRAM_POLLING_TIMEOUT', '20')),
            allowed_updates=os.getenv('TELEGRAM_ALLOWED_UPDATES', 'message,callback_query').split(',')
        )


@dataclass
class MonitoringConfig(BaseConfig):
    """Configuration for monitoring and observability"""
    enable_metrics: bool = True
    metrics_port: int = 8080
    metrics_path: str = "/metrics"
    enable_health_check: bool = True
    health_check_port: int = 8081
    health_check_path: str = "/health"
    enable_tracing: bool = False
    tracing_endpoint: str = ""
    tracing_service_name: str = "firefeed-service"
    log_format: str = "json"
    log_level: str = "INFO"
    enable_access_log: bool = True
    access_log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def from_env(cls) -> 'MonitoringConfig':
        return cls(
            enable_metrics=os.getenv('MONITORING_ENABLE_METRICS', 'true').lower() == 'true',
            metrics_port=int(os.getenv('MONITORING_METRICS_PORT', '8080')),
            metrics_path=os.getenv('MONITORING_METRICS_PATH', '/metrics'),
            enable_health_check=os.getenv('MONITORING_ENABLE_HEALTH_CHECK', 'true').lower() == 'true',
            health_check_port=int(os.getenv('MONITORING_HEALTH_CHECK_PORT', '8081')),
            health_check_path=os.getenv('MONITORING_HEALTH_CHECK_PATH', '/health'),
            enable_tracing=os.getenv('MONITORING_ENABLE_TRACING', 'false').lower() == 'true',
            tracing_endpoint=os.getenv('MONITORING_TRACING_ENDPOINT', ''),
            tracing_service_name=os.getenv('MONITORING_TRACING_SERVICE_NAME', 'firefeed-service'),
            log_format=os.getenv('MONITORING_LOG_FORMAT', 'json'),
            log_level=os.getenv('MONITORING_LOG_LEVEL', 'INFO'),
            enable_access_log=os.getenv('MONITORING_ENABLE_ACCESS_LOG', 'true').lower() == 'true',
            access_log_format=os.getenv('MONITORING_ACCESS_LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )


@dataclass
class SecurityConfig(BaseConfig):
    """Configuration for security settings"""
    jwt_secret_key: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    enable_cors: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    enable_rate_limiting: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    enable_ssl: bool = False
    ssl_cert_path: str = ""
    ssl_key_path: str = ""
    enable_api_key_auth: bool = True
    api_key_header: str = "X-API-Key"
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        return cls(
            jwt_secret_key=os.getenv('JWT_SECRET_KEY', 'your-secret-key'),
            jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
            jwt_access_token_expire_minutes=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            jwt_refresh_token_expire_days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7')),
            bcrypt_rounds=int(os.getenv('BCRYPT_ROUNDS', '12')),
            enable_cors=os.getenv('SECURITY_ENABLE_CORS', 'true').lower() == 'true',
            allowed_origins=os.getenv('SECURITY_ALLOWED_ORIGINS', '*').split(','),
            enable_rate_limiting=os.getenv('SECURITY_ENABLE_RATE_LIMITING', 'true').lower() == 'true',
            rate_limit_requests=int(os.getenv('SECURITY_RATE_LIMIT_REQUESTS', '100')),
            rate_limit_window=int(os.getenv('SECURITY_RATE_LIMIT_WINDOW', '60')),
            enable_ssl=os.getenv('SECURITY_ENABLE_SSL', 'false').lower() == 'true',
            ssl_cert_path=os.getenv('SECURITY_SSL_CERT_PATH', ''),
            ssl_key_path=os.getenv('SECURITY_SSL_KEY_PATH', ''),
            enable_api_key_auth=os.getenv('SECURITY_ENABLE_API_KEY_AUTH', 'true').lower() == 'true',
            api_key_header=os.getenv('SECURITY_API_KEY_HEADER', 'X-API-Key')
        )