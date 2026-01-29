# models/base_models.py - Base data models
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Generic, TypeVar, Dict, Set, Any
from datetime import datetime
from enum import Enum

# Define type parameter for Generic
T = TypeVar("T")

# Language enum for validation
class LanguageEnum(str, Enum):
    EN = "en"
    RU = "ru"
    DE = "de"
    FR = "fr"

# Recipient type enum for telegram bot
class RecipientTypeEnum(str, Enum):
    CHANNEL = "channel"
    USER = "user"

# Model for representing translation to a specific language
class LanguageTranslation(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

# Complete RSS Item Model - matches published_news_data table structure
class RSSItem(BaseModel):
    """Complete RSS Item model matching published_news_data table structure."""
    
    # Primary key
    news_id: str
    
    # Content fields
    original_title: str
    original_content: str
    original_language: str
    
    # Metadata fields
    category_id: Optional[int] = None
    image_filename: Optional[str] = None
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    # Foreign key to RSS feeds
    rss_feed_id: Optional[int] = None
    
    # Vector embedding (optional in microservices without pgvector)
    embedding: Optional[List[float]] = None
    
    # Additional metadata
    source_url: Optional[str] = None
    video_filename: Optional[str] = None
    
    # Translations
    translations: Optional[Dict[str, LanguageTranslation]] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Complete RSS Feed Model - matches rss_feeds table structure
class RSSFeed(BaseModel):
    """Complete RSS Feed model matching rss_feeds table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to sources
    source_id: int
    
    # Feed information
    url: str
    name: str
    
    # Optional category assignment
    category_id: Optional[int] = None
    
    # Language and status
    language: str = "en"
    is_active: bool = True
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    # Processing configuration
    cooldown_minutes: int = 10
    max_news_per_hour: int = 10
    
    # Optional source information (joined from sources table)
    source_name: Optional[str] = None
    source_alias: Optional[str] = None
    source_logo: Optional[str] = None
    source_site_url: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User RSS Feed Model - matches user_rss_feeds table structure
class UserRSSFeed(BaseModel):
    """User RSS Feed model matching user_rss_feeds table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to users
    user_id: int
    
    # Feed information
    url: str
    name: Optional[str] = None
    
    # Optional category assignment
    category_id: Optional[int] = None
    
    # Language and status
    language: str = "en"
    is_active: bool = True
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    # Optional category information (joined from categories table)
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Model - matches users table structure
class User(BaseModel):
    """Complete User model matching users table structure."""
    
    # Primary key
    id: int
    
    # User information
    email: EmailStr
    password_hash: str  # Note: This is for internal use, never exposed in API responses
    
    # Language preference
    language: str = "en"
    
    # Account status
    is_active: bool = False
    is_verified: bool = False
    is_deleted: bool = False
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Response Model - for API responses (excludes password_hash)
class UserResponse(BaseModel):
    """User response model for API endpoints."""
    
    # Primary key
    id: int
    
    # User information
    email: EmailStr
    language: str = "en"
    
    # Account status
    is_active: bool = False
    is_verified: bool = False
    is_deleted: bool = False
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Update Model - for updating user information
class UserUpdate(BaseModel):
    """User update model for API endpoints."""
    
    email: Optional[EmailStr] = None
    language: Optional[str] = None
    
    class Config:
        from_attributes = True

# Category Model - matches categories table structure
class Category(BaseModel):
    """Category model matching categories table structure."""
    
    # Primary key
    id: int
    
    # Category information
    name: str
    display_name: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Category Item Model - for API responses
class CategoryItem(BaseModel):
    """Category item model for API responses."""
    
    id: int
    name: str
    display_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Source Item Model - for API responses
class SourceItem(BaseModel):
    """Source item model for API responses."""
    
    id: int
    name: str
    description: Optional[str] = None
    alias: Optional[str] = None
    logo: Optional[str] = None
    site_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Language Item Model - for API responses
class LanguageItem(BaseModel):
    """Language item model for API responses."""
    
    code: str
    name: str
    native_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# Source Model - matches sources table structure
class Source(BaseModel):
    """Source model matching sources table structure."""
    
    # Primary key
    id: int
    
    # Source information
    name: str
    description: Optional[str] = None
    
    # Optional metadata
    alias: Optional[str] = None
    logo: Optional[str] = None
    site_url: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# News Translation Model - matches news_translations table structure
class NewsTranslation(BaseModel):
    """News translation model matching news_translations table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to published_news_data
    news_id: str
    
    # Translation information
    language: str
    translated_title: str
    translated_content: str
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Password Reset Token Model - matches password_reset_tokens table structure
class PasswordResetToken(BaseModel):
    """Password reset token model matching password_reset_tokens table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to users
    user_id: int
    
    # Token information
    token: str
    expires_at: str  # ISO date-time format
    
    # Optional usage tracking
    used_at: Optional[str] = None  # ISO date-time format
    
    # Timestamp
    created_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Verification Code Model - matches user_verification_codes table structure
class UserVerificationCode(BaseModel):
    """User verification code model matching user_verification_codes table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to users
    user_id: int
    
    # Verification information
    verification_code: str
    created_at: str  # ISO date-time format
    expires_at: str  # ISO date-time format
    
    # Optional usage tracking
    used_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User API Key Model - matches user_api_keys table structure
class UserAPIKey(BaseModel):
    """User API key model matching user_api_keys table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to users
    user_id: int
    
    # Key information
    key_hash: str
    limits: Dict[str, Any] = Field(default_factory=lambda: {"requests_per_day": 1000, "requests_per_hour": 100})
    is_active: bool = True
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    expires_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Preference Model - matches user_preferences table structure
class UserPreference(BaseModel):
    """User preference model matching user_preferences table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to users
    user_id: int
    
    # Preferences
    subscriptions: Optional[str] = None
    language: str = "en"
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# User Telegram Link Model - matches user_telegram_links table structure
class UserTelegramLink(BaseModel):
    """User telegram link model matching user_telegram_links table structure."""
    
    # Primary key
    id: int
    
    # Foreign key to users
    user_id: int
    
    # Telegram information
    telegram_id: Optional[int] = None
    link_code: Optional[str] = None
    
    # Timestamps
    created_at: Optional[str] = None  # ISO date-time format
    linked_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# RSS Items Telegram Bot Published Model - matches rss_items_telegram_bot_published table structure
class RSSItemsTelegramBotPublished(BaseModel):
    """RSS items telegram bot published model matching rss_items_telegram_bot_published table structure."""
    
    # Primary key
    id: int
    
    # Foreign keys
    news_id: Optional[str] = None
    translation_id: Optional[int] = None
    
    # Recipient information
    recipient_type: RecipientTypeEnum
    recipient_id: int
    
    # Message information
    message_id: Optional[int] = None
    language: Optional[str] = None
    
    # Timestamps
    sent_at: Optional[str] = None  # ISO date-time format
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# Source Category Model - matches source_categories table structure
class SourceCategory(BaseModel):
    """Source category model matching source_categories table structure."""
    
    # Composite primary key
    source_id: int
    category_id: int
    
    class Config:
        from_attributes = True

# User Category Model - matches user_categories table structure
class UserCategory(BaseModel):
    """User category model matching user_categories table structure."""
    
    # Composite primary key
    user_id: int
    category_id: int
    
    class Config:
        from_attributes = True

# Paginated Response Model - for all paginated endpoints
class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    
    count: int
    results: List[T]
    
    class Config:
        from_attributes = True

# Token Model - for JWT tokens
class Token(BaseModel):
    """Token model for JWT responses."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    
    class Config:
        from_attributes = True

# Success Response Model - for successful operations
class SuccessResponse(BaseModel):
    """Success response model."""
    
    message: str
    
    class Config:
        from_attributes = True

# Error Response Model - for error responses
class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None  # ISO date-time format
    service_id: Optional[str] = None
    request_id: Optional[str] = None
    
    class Config:
        from_attributes = True

# Health Check Response Model
class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str
    database: str
    redis: Optional[str] = None
    db_pool: Optional[Dict[str, int]] = None
    redis_pool: Optional[Dict[str, int]] = None
    
    class Config:
        from_attributes = True

# Metrics Response Model
class MetricsResponse(BaseModel):
    """Metrics response model."""
    
    service_id: str
    timestamp: str  # ISO date-time format
    requests_total: int
    requests_per_minute: float
    error_rate: float
    avg_response_time: float
    active_users: int
    rss_feeds_total: int
    rss_items_total: int
    categories_total: int
    sources_total: int
    translation_requests_total: int
    cache_hit_rate: float
    db_connections_active: int
    redis_connections_active: int
    
    class Config:
        from_attributes = True

# JWT Token Payload Model
class JWTPayload(BaseModel):
    """JWT token payload model."""
    
    sub: str  # Subject (user_id or service_id)
    exp: int  # Expiration time
    iat: int  # Issued at
    iss: str  # Issuer
    scopes: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

# Service Token Payload Model
class ServiceTokenPayload(BaseModel):
    """Service token payload model."""
    
    service_id: str
    service_name: str
    scopes: List[str]
    exp: int  # Expiration time
    iat: int  # Issued at
    iss: str  # Issuer
    
    class Config:
        from_attributes = True

# API Key Create Request Model
class APIKeyCreateRequest(BaseModel):
    """API key create request model."""
    
    name: str
    user_id: int
    
    class Config:
        from_attributes = True

# RSS Feed Create Request Model
class RSSFeedCreateRequest(BaseModel):
    """RSS feed create request model."""
    
    source_id: int
    url: str
    name: str
    category_id: Optional[int] = None
    language: str = "en"
    is_active: bool = True
    cooldown_minutes: int = 10
    max_news_per_hour: int = 10
    
    class Config:
        from_attributes = True

# User RSS Feed Create Request Model
class UserRSSFeedCreateRequest(BaseModel):
    """User RSS feed create request model."""
    
    url: str
    name: Optional[str] = None
    category_id: Optional[int] = None
    language: str = "en"
    
    class Config:
        from_attributes = True

# User Update Request Model
class UserUpdateRequest(BaseModel):
    """User update request model."""
    
    email: Optional[EmailStr] = None
    language: Optional[str] = None
    
    class Config:
        from_attributes = True

# User Create Request Model
class UserCreate(BaseModel):
    """User create request model."""
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    language: str = "en"
    
    class Config:
        from_attributes = True

# Password Reset Request Model
class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    
    email: EmailStr
    
    class Config:
        from_attributes = True

# Password Reset Confirm Model
class PasswordResetConfirm(BaseModel):
    """Password reset confirm model."""
    
    token: str
    new_password: str = Field(..., min_length=8)
    
    class Config:
        from_attributes = True

# Email Verification Request Model
class EmailVerificationRequest(BaseModel):
    """Email verification request model."""
    
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    
    class Config:
        from_attributes = True

# Resend Verification Request Model
class ResendVerificationRequest(BaseModel):
    """Resend verification request model."""
    
    email: EmailStr
    
    class Config:
        from_attributes = True

# Telegram Link Response Model
class TelegramLinkResponse(BaseModel):
    """Telegram link response model."""
    
    link_code: str
    instructions: str
    
    class Config:
        from_attributes = True

# Telegram Link Status Response Model
class TelegramLinkStatusResponse(BaseModel):
    """Telegram link status response model."""
    
    is_linked: bool
    telegram_id: Optional[int] = None
    linked_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True

# Translation Request Model
class TranslationRequest(BaseModel):
    """Translation request model."""
    
    text: str
    target_language: str
    source_language: Optional[str] = None
    model: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Translation Response Model
class TranslationResponse(BaseModel):
    """Translation response model."""
    
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True

# Duplicate Detection Request Model
class DuplicateDetectionRequest(BaseModel):
    """Duplicate detection request model."""
    
    text: str
    threshold: Optional[float] = 0.8
    language: Optional[str] = None
    
    class Config:
        from_attributes = True

# Duplicate Detection Response Model
class DuplicateDetectionResponse(BaseModel):
    """Duplicate detection response model."""
    
    is_duplicate: bool
    similarity_score: Optional[float] = None
    existing_news_id: Optional[str] = None
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True

# Media Extraction Request Model
class MediaExtractionRequest(BaseModel):
    """Media extraction request model."""
    
    url: str
    content: Optional[str] = None
    
    class Config:
        from_attributes = True

# Media Extraction Response Model
class MediaExtractionResponse(BaseModel):
    """Media extraction response model."""
    
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    extracted_text: Optional[str] = None
    processing_time: Optional[float] = None
    
    class Config:
        from_attributes = True

# RSS Item Processing Request Model
class RSSItemProcessingRequest(BaseModel):
    """RSS item processing request model."""
    
    title: str
    content: str
    link: str
    guid: str
    pub_date: str  # ISO date-time format
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str = "en"
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# RSS Item Processing Response Model
class RSSItemProcessingResponse(BaseModel):
    """RSS item processing response model."""
    
    news_id: str
    title: str
    content: str
    link: str
    guid: str
    pub_date: str  # ISO date-time format
    feed_id: int
    category_id: Optional[int] = None
    source_id: Optional[int] = None
    language: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: str  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    is_published: bool = False
    published_at: Optional[str] = None  # ISO date-time format
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Service Health Check Request Model
class ServiceHealthCheckRequest(BaseModel):
    """Service health check request model."""
    
    service_id: str
    check_database: bool = True
    check_redis: bool = True
    check_external_services: bool = False
    
    class Config:
        from_attributes = True

# Service Health Check Response Model
class ServiceHealthCheckResponse(BaseModel):
    """Service health check response model."""
    
    service_id: str
    status: str
    timestamp: str  # ISO date-time format
    checks: Dict[str, Dict[str, Any]]
    uptime: Optional[float] = None
    
    class Config:
        from_attributes = True

# Rate Limit Check Request Model
class RateLimitCheckRequest(BaseModel):
    """Rate limit check request model."""
    
    service_id: str
    endpoint: str
    client_id: Optional[str] = None
    
    class Config:
        from_attributes = True

# Rate Limit Check Response Model
class RateLimitCheckResponse(BaseModel):
    """Rate limit check response model."""
    
    allowed: bool
    limit: int
    remaining: int
    reset_time: str  # ISO date-time format
    retry_after: Optional[int] = None
    
    class Config:
        from_attributes = True

# Cache Operation Request Model
class CacheOperationRequest(BaseModel):
    """Cache operation request model."""
    
    key: str
    value: Optional[Any] = None
    ttl: Optional[int] = None  # Time to live in seconds
    
    class Config:
        from_attributes = True

# Cache Operation Response Model
class CacheOperationResponse(BaseModel):
    """Cache operation response model."""
    
    success: bool
    key: str
    value: Optional[Any] = None
    ttl: Optional[int] = None
    
    class Config:
        from_attributes = True

# Database Operation Request Model
class DatabaseOperationRequest(BaseModel):
    """Database operation request model."""
    
    query: str
    parameters: Optional[Dict[str, Any]] = None
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE
    
    class Config:
        from_attributes = True

# Database Operation Response Model
class DatabaseOperationResponse(BaseModel):
    """Database operation response model."""
    
    success: bool
    rows_affected: int
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    
    class Config:
        from_attributes = True

# Notification Request Model
class NotificationRequest(BaseModel):
    """Notification request model."""
    
    recipient_type: RecipientTypeEnum
    recipient_id: int
    message: str
    language: Optional[str] = None
    media_url: Optional[str] = None
    
    class Config:
        from_attributes = True

# Notification Response Model
class NotificationResponse(BaseModel):
    """Notification response model."""
    
    success: bool
    recipient_type: RecipientTypeEnum
    recipient_id: int
    message_id: Optional[int] = None
    sent_at: Optional[str] = None  # ISO date-time format
    error: Optional[str] = None
    
    class Config:
        from_attributes = True

# Subscription Request Model
class SubscriptionRequest(BaseModel):
    """Subscription request model."""
    
    user_id: int
    category_ids: List[int]
    source_ids: Optional[List[int]] = None
    languages: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

# Subscription Response Model
class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    
    user_id: int
    category_ids: List[int]
    source_ids: Optional[List[int]] = None
    languages: Optional[List[str]] = None
    updated_at: Optional[str] = None  # ISO date-time format
    
    class Config:
        from_attributes = True

# User State Model
class UserState(BaseModel):
    """User state model for telegram bot."""
    
    current_subs: List[int] = []
    language: str = "en"
    last_access: float
    
    class Config:
        from_attributes = True

# User Menu Model
class UserMenu(BaseModel):
    """User menu state model for telegram bot."""
    
    menu: str
    last_access: float
    
    class Config:
        from_attributes = True

# User Language Model
class UserLanguage(BaseModel):
    """User language state model for telegram bot."""
    
    language: str
    last_access: float
    
    class Config:
        from_attributes = True

# Telegram Bot State Model
class TelegramBotState(BaseModel):
    """Telegram bot state model."""
    
    user_states: Dict[int, UserState] = {}
    user_menus: Dict[int, UserMenu] = {}
    user_languages: Dict[int, UserLanguage] = {}
    last_cleanup: float = 0.0
    
    class Config:
        from_attributes = True

# RSS Parser State Model
class RSSParserState(BaseModel):
    """RSS parser state model."""
    
    last_processed_feeds: Dict[str, float] = {}
    processing_errors: Dict[str, int] = {}
    last_cleanup: float = 0.0
    
    class Config:
        from_attributes = True

# API Service State Model
class APIServiceState(BaseModel):
    """API service state model."""
    
    active_connections: int = 0
    request_count: int = 0
    error_count: int = 0
    last_cleanup: float = 0.0
    
    class Config:
        from_attributes = True

# Service Configuration Model
class ServiceConfiguration(BaseModel):
    """Service configuration model."""
    
    service_id: str
    service_name: str
    service_version: str
    database_url: str
    redis_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    log_level: str = "INFO"
    cors_allowed_origins: List[str] = []
    allowed_hosts: List[str] = []
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    translation_enabled: bool = True
    duplicate_detection_enabled: bool = True
    cache_enabled: bool = True
    
    class Config:
        from_attributes = True


# Redis Configuration Model
class RedisConfiguration(BaseModel):
    """Redis configuration model."""
    
    host: str
    port: int = 6379
    db: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    
    class Config:
        from_attributes = True

# Translation Configuration Model
class TranslationConfiguration(BaseModel):
    """Translation configuration model."""
    
    enabled: bool = True
    default_model: str = "facebook/m2m100_418M"
    supported_languages: List[str] = ["en", "ru", "de", "fr"]
    max_text_length: int = 10000
    timeout: int = 30
    
    class Config:
        from_attributes = True

# Duplicate Detection Configuration Model
class DuplicateDetectionConfiguration(BaseModel):
    """Duplicate detection configuration model."""
    
    enabled: bool = True
    threshold: float = 0.8
    max_age_hours: int = 24
    timeout: int = 10
    
    class Config:
        from_attributes = True

# Cache Configuration Model
class CacheConfiguration(BaseModel):
    """Cache configuration model."""
    
    enabled: bool = True
    default_ttl: int = 3600
    max_size: int = 1000
    timeout: int = 5
    
    class Config:
        from_attributes = True

# Rate Limiting Configuration Model
class RateLimitingConfiguration(BaseModel):
    """Rate limiting configuration model."""
    
    enabled: bool = True
    default_requests: int = 100
    default_window: int = 60
    burst_size: int = 10
    
    class Config:
        from_attributes = True

# Monitoring Configuration Model
class MonitoringConfiguration(BaseModel):
    """Monitoring configuration model."""
    
    enabled: bool = True
    metrics_enabled: bool = True
    health_check_enabled: bool = True
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    class Config:
        from_attributes = True

# Security Configuration Model
class SecurityConfiguration(BaseModel):
    """Security configuration model."""
    
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_minutes: int = 30
    
    class Config:
        from_attributes = True

# Application Configuration Model
class ApplicationConfiguration(BaseModel):
    """Application configuration model."""

    service: ServiceConfiguration
    redis: RedisConfiguration
    translation: TranslationConfiguration
    duplicate_detection: DuplicateDetectionConfiguration
    cache: CacheConfiguration
    rate_limiting: RateLimitingConfiguration
    monitoring: MonitoringConfiguration
    security: SecurityConfiguration
    
    class Config:
        from_attributes = True