"""
FireFeed Core Configuration Validation

Validation functions for configuration objects.
"""

import re
from typing import Any, Dict, List, Optional, Union
from .base_config import (
    BaseConfig, ServiceConfig, RedisConfig,
    CacheConfig, QueueConfig, TranslationConfig, RSSConfig,
    TelegramConfig, MonitoringConfig, SecurityConfig
)


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


def validate_config(config: BaseConfig) -> List[str]:
    """
    Validate configuration object and return list of validation errors.
    
    Args:
        config: Configuration object to validate
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if isinstance(config, ServiceConfig):
        errors.extend(validate_service_config(config))
    elif isinstance(config, RedisConfig):
        errors.extend(validate_redis_config(config))
    elif isinstance(config, CacheConfig):
        errors.extend(validate_cache_config(config))
    elif isinstance(config, QueueConfig):
        errors.extend(validate_queue_config(config))
    elif isinstance(config, TranslationConfig):
        errors.extend(validate_translation_config(config))
    elif isinstance(config, RSSConfig):
        errors.extend(validate_rss_config(config))
    elif isinstance(config, TelegramConfig):
        errors.extend(validate_telegram_config(config))
    elif isinstance(config, MonitoringConfig):
        errors.extend(validate_monitoring_config(config))
    elif isinstance(config, SecurityConfig):
        errors.extend(validate_security_config(config))
    
    return errors


def validate_service_config(config: ServiceConfig) -> List[str]:
    """Validate service configuration"""
    errors = []
    
    # Validate service name
    if not config.service_name or not re.match(r'^[a-zA-Z0-9_-]+$', config.service_name):
        errors.append("Service name must be alphanumeric with underscores or hyphens only")
    
    # Validate log level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.log_level not in valid_log_levels:
        errors.append(f"Invalid log level: {config.log_level}. Must be one of: {valid_log_levels}")
    
    # Validate JWT settings
    if not config.jwt_secret_key or len(config.jwt_secret_key) < 32:
        errors.append("JWT secret key must be at least 32 characters long")
    
    if config.jwt_access_token_expire_minutes <= 0:
        errors.append("JWT access token expiration must be positive")
    
    # Validate API base URL
    if config.api_base_url and not config.api_base_url.startswith(('http://', 'https://')):
        errors.append("API base URL must start with http:// or https://")
    
    # Validate TTL settings
    if config.user_data_ttl_seconds <= 0:
        errors.append("User data TTL must be positive")
    
    # Validate cleanup interval
    if config.rss_parser_cleanup_interval_hours < 0:
        errors.append("RSS parser cleanup interval must be non-negative")
    
    return errors


def validate_redis_config(config: RedisConfig) -> List[str]:
    """Validate Redis configuration"""
    errors = []
    
    # Validate host
    if not config.host:
        errors.append("Redis host cannot be empty")
    
    # Validate port
    if not (1 <= config.port <= 65535):
        errors.append("Redis port must be between 1 and 65535")
    
    # Validate database number
    if config.db < 0:
        errors.append("Redis database number must be non-negative")
    
    # Validate timeout settings
    if config.socket_timeout <= 0:
        errors.append("Redis socket timeout must be positive")
    
    if config.socket_connect_timeout <= 0:
        errors.append("Redis socket connect timeout must be positive")
    
    if config.health_check_interval < 0:
        errors.append("Redis health check interval must be non-negative")
    
    if config.max_connections <= 0:
        errors.append("Redis max connections must be positive")
    
    return errors


def validate_cache_config(config: CacheConfig) -> List[str]:
    """Validate cache configuration"""
    errors = []
    
    # Validate TTL
    if config.default_ttl <= 0:
        errors.append("Cache default TTL must be positive")
    
    # Validate cache size
    if config.max_cache_size <= 0:
        errors.append("Cache max size must be positive")
    
    # Validate cleanup interval
    if config.cleanup_interval < 0:
        errors.append("Cache cleanup interval must be non-negative")
    
    # Validate compression level
    if config.compression_enabled and not (1 <= config.compression_level <= 9):
        errors.append("Cache compression level must be between 1 and 9")
    
    return errors


def validate_queue_config(config: QueueConfig) -> List[str]:
    """Validate queue configuration"""
    errors = []
    
    # Validate queue size
    if config.max_queue_size <= 0:
        errors.append("Queue max size must be positive")
    
    # Validate workers
    if config.default_workers <= 0:
        errors.append("Queue default workers must be positive")
    
    # Validate timeout
    if config.task_timeout <= 0:
        errors.append("Queue task timeout must be positive")
    
    # Validate retry settings
    if config.retry_attempts < 0:
        errors.append("Queue retry attempts must be non-negative")
    
    if config.retry_delay <= 0:
        errors.append("Queue retry delay must be positive")
    
    if config.max_retry_delay <= 0:
        errors.append("Queue max retry delay must be positive")
    
    if config.max_retry_delay < config.retry_delay:
        errors.append("Queue max retry delay must be greater than or equal to retry delay")
    
    return errors


def validate_translation_config(config: TranslationConfig) -> List[str]:
    """Validate translation configuration"""
    errors = []
    
    # Validate model name
    if not config.model_name:
        errors.append("Translation model name cannot be empty")
    
    # Validate concurrent translations
    if config.max_concurrent_translations <= 0:
        errors.append("Translation max concurrent must be positive")
    
    # Validate cached models
    if config.max_cached_models <= 0:
        errors.append("Translation max cached models must be positive")
    
    # Validate cleanup interval
    if config.model_cleanup_interval <= 0:
        errors.append("Translation model cleanup interval must be positive")
    
    # Validate device
    valid_devices = ['cpu', 'cuda', 'mps']
    if config.default_device not in valid_devices:
        errors.append(f"Invalid translation device: {config.default_device}. Must be one of: {valid_devices}")
    
    # Validate workers
    if config.max_workers <= 0:
        errors.append("Translation max workers must be positive")
    
    # Validate batch size
    if config.batch_size <= 0:
        errors.append("Translation batch size must be positive")
    
    # Validate context window
    if config.context_window < 0:
        errors.append("Translation context window must be non-negative")
    
    # Validate beam size
    if config.beam_size is not None and config.beam_size <= 0:
        errors.append("Translation beam size must be positive")
    
    # Validate cache TTL
    if config.cache_ttl <= 0:
        errors.append("Translation cache TTL must be positive")
    
    return errors


def validate_rss_config(config: RSSConfig) -> List[str]:
    """Validate RSS configuration"""
    errors = []
    
    # Validate concurrent feeds
    if config.max_concurrent_feeds <= 0:
        errors.append("RSS max concurrent feeds must be positive")
    
    # Validate entries per feed
    if config.max_entries_per_feed <= 0:
        errors.append("RSS max entries per feed must be positive")
    
    # Validate cache TTL
    if config.validation_cache_ttl <= 0:
        errors.append("RSS validation cache TTL must be positive")
    
    # Validate request timeout
    if config.request_timeout <= 0:
        errors.append("RSS request timeout must be positive")
    
    # Validate total items
    if config.max_total_rss_items <= 0:
        errors.append("RSS max total items must be positive")
    
    # Validate word lengths
    if config.min_item_title_words_length < 0:
        errors.append("RSS min item title words length must be non-negative")
    
    if config.min_item_content_words_length < 0:
        errors.append("RSS min item content words length must be non-negative")
    
    # Validate cleanup interval
    if config.cleanup_interval_hours < 0:
        errors.append("RSS cleanup interval must be non-negative")
    
    # Validate media type priority
    valid_media_types = ['image', 'video', 'audio']
    if config.media_type_priority not in valid_media_types:
        errors.append(f"Invalid RSS media type priority: {config.media_type_priority}. Must be one of: {valid_media_types}")
    
    # Validate similarity threshold
    if not (0.0 <= config.similarity_threshold <= 1.0):
        errors.append("RSS similarity threshold must be between 0.0 and 1.0")
    
    # Validate cooldown
    if config.max_feed_cooldown_minutes <= 0:
        errors.append("RSS max feed cooldown must be positive")
    
    return errors


def validate_telegram_config(config: TelegramConfig) -> List[str]:
    """Validate Telegram configuration"""
    errors = []
    
    # Validate bot token
    if not config.bot_token:
        errors.append("Telegram bot token cannot be empty")
    
    # Validate bot ID
    if config.bot_id <= 0:
        errors.append("Telegram bot ID must be positive")
    
    # Validate webhook URL
    if config.enable_webhook and config.webhook_url and not config.webhook_url.startswith(('http://', 'https://')):
        errors.append("Telegram webhook URL must start with http:// or https://")
    
    # Validate message length
    if config.max_message_length <= 0:
        errors.append("Telegram max message length must be positive")
    
    # Validate rate limiting
    if config.rate_limit_requests <= 0:
        errors.append("Telegram rate limit requests must be positive")
    
    if config.rate_limit_window <= 0:
        errors.append("Telegram rate limit window must be positive")
    
    # Validate polling timeout
    if config.polling_timeout <= 0:
        errors.append("Telegram polling timeout must be positive")
    
    # Validate allowed updates
    valid_update_types = ['message', 'edited_message', 'channel_post', 'edited_channel_post', 
                         'inline_query', 'chosen_inline_result', 'callback_query', 'shipping_query', 
                         'pre_checkout_query', 'poll', 'poll_answer', 'my_chat_member', 'chat_member']
    for update_type in config.allowed_updates:
        if update_type not in valid_update_types:
            errors.append(f"Invalid Telegram allowed update type: {update_type}")
    
    return errors


def validate_monitoring_config(config: MonitoringConfig) -> List[str]:
    """Validate monitoring configuration"""
    errors = []
    
    # Validate metrics port
    if config.enable_metrics and not (1 <= config.metrics_port <= 65535):
        errors.append("Monitoring metrics port must be between 1 and 65535")
    
    # Validate health check port
    if config.enable_health_check and not (1 <= config.health_check_port <= 65535):
        errors.append("Monitoring health check port must be between 1 and 65535")
    
    # Validate log level
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.log_level not in valid_log_levels:
        errors.append(f"Invalid monitoring log level: {config.log_level}. Must be one of: {valid_log_levels}")
    
    # Validate log format
    valid_log_formats = ['json', 'text']
    if config.log_format not in valid_log_formats:
        errors.append(f"Invalid monitoring log format: {config.log_format}. Must be one of: {valid_log_formats}")
    
    return errors


def validate_security_config(config: SecurityConfig) -> List[str]:
    """Validate security configuration"""
    errors = []
    
    # Validate JWT settings
    if not config.jwt_secret_key or len(config.jwt_secret_key) < 32:
        errors.append("Security JWT secret key must be at least 32 characters long")
    
    valid_jwt_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
    if config.jwt_algorithm not in valid_jwt_algorithms:
        errors.append(f"Invalid JWT algorithm: {config.jwt_algorithm}. Must be one of: {valid_jwt_algorithms}")
    
    if config.jwt_access_token_expire_minutes <= 0:
        errors.append("Security JWT access token expiration must be positive")
    
    if config.jwt_refresh_token_expire_days <= 0:
        errors.append("Security JWT refresh token expiration must be positive")
    
    # Validate bcrypt rounds
    if not (4 <= config.bcrypt_rounds <= 16):
        errors.append("Security bcrypt rounds must be between 4 and 16")
    
    # Validate rate limiting
    if config.enable_rate_limiting:
        if config.rate_limit_requests <= 0:
            errors.append("Security rate limit requests must be positive")
        
        if config.rate_limit_window <= 0:
            errors.append("Security rate limit window must be positive")
    
    # Validate SSL settings
    if config.enable_ssl:
        if not config.ssl_cert_path:
            errors.append("Security SSL cert path cannot be empty when SSL is enabled")
        
        if not config.ssl_key_path:
            errors.append("Security SSL key path cannot be empty when SSL is enabled")
    
    # Validate API key header
    if config.enable_api_key_auth and not config.api_key_header:
        errors.append("Security API key header cannot be empty when API key auth is enabled")
    
    return errors


def validate_all_configs() -> Dict[str, List[str]]:
    """
    Validate all configuration classes and return validation results.
    
    Returns:
        Dictionary with config class names as keys and validation errors as values
    """
    results = {}
    
    # Create sample configurations for validation
    configs = {
        'ServiceConfig': ServiceConfig.from_env(),
        'RedisConfig': RedisConfig.from_env(),
        'CacheConfig': CacheConfig.from_env(),
        'QueueConfig': QueueConfig.from_env(),
        'TranslationConfig': TranslationConfig.from_env(),
        'RSSConfig': RSSConfig.from_env(),
        'TelegramConfig': TelegramConfig.from_env(),
        'MonitoringConfig': MonitoringConfig.from_env(),
        'SecurityConfig': SecurityConfig.from_env(),
    }
    
    for name, config in configs.items():
        errors = validate_config(config)
        results[name] = errors
    
    return results