"""
FireFeed Core Settings

Pydantic-based configuration management for FireFeed microservices.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FireFeedSettings(BaseModel):
    """
    Base configuration for FireFeed microservices.
    
    Uses Pydantic Settings for environment-based configuration management.
    """
    
    # Service Configuration
    service_id: str = Field(..., description="Unique service identifier")
    service_name: str = Field(..., description="Human-readable service name")
    service_version: str = Field("1.0.0", description="Service version")
    
    # API Configuration
    api_base_url: str = Field(..., description="Base URL for API calls")
    api_timeout: int = Field(30, description="API request timeout in seconds")
    api_max_retries: int = Field(3, description="Maximum API retry attempts")
    
    # Authentication Configuration
    jwt_secret_key: str = Field(..., description="JWT secret key for token signing")
    jwt_algorithm: str = Field("HS256", description="JWT signing algorithm")
    jwt_expiration_minutes: int = Field(30, description="JWT token expiration in minutes")
    
    
    # Redis Configuration
    redis_host: str = Field("localhost", description="Redis host")
    redis_port: int = Field(6379, description="Redis port")
    redis_password: Optional[str] = Field(None, description="Redis password")
    redis_db: int = Field(0, description="Redis database number")
    
    # Rate Limiting Configuration
    rate_limit_requests: int = Field(100, description="Rate limit requests per window")
    rate_limit_window: int = Field(60, description="Rate limit window in seconds")
    
    # Circuit Breaker Configuration
    circuit_breaker_failure_threshold: int = Field(5, description="Circuit breaker failure threshold")
    circuit_breaker_timeout: int = Field(60, description="Circuit breaker timeout in seconds")
    
    # Retry Configuration
    retry_max_attempts: int = Field(3, description="Maximum retry attempts")
    retry_base_delay: float = Field(1.0, description="Base delay for retry exponential backoff")
    retry_max_delay: float = Field(60.0, description="Maximum retry delay")
    retry_jitter: bool = Field(True, description="Enable jitter for retry delays")
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log message format")
    
    # Environment Configuration
    environment: str = Field("development", description="Environment (development, staging, production)")
    
    # Feature Flags
    translation_enabled: bool = Field(True, description="Enable translation features")
    duplicate_detection_enabled: bool = Field(True, description="Enable duplicate detection")
    cache_enabled: bool = Field(True, description="Enable caching")
    
    # Translation Configuration
    translation_model: str = Field("facebook/m2m100_418M", description="Translation model name")
    translation_max_concurrent: int = Field(3, description="Maximum concurrent translations")
    translation_device: str = Field("cpu", description="Translation model device (cpu/cuda)")
    
    # Duplicate Detection Configuration
    duplicate_detector_model: str = Field("paraphrase-multilingual-MiniLM-L12-v2", description="Duplicate detection model")
    duplicate_similarity_threshold: float = Field(0.9, description="Similarity threshold for duplicates")
    
    # Cache Configuration
    cache_ttl: int = Field(3600, description="Default cache TTL in seconds")
    cache_max_size: int = Field(10000, description="Maximum cache size")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Allow extra fields not defined in the model
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    @property
    def redis_url(self) -> str:
        """Generate Redis URL from configuration."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_service_scopes(self) -> List[str]:
        """Get service-specific scopes based on configuration."""
        scopes = []
        
        if self.translation_enabled:
            scopes.extend(["translation:read", "translation:write"])
        
        if self.duplicate_detection_enabled:
            scopes.extend(["duplicate:read", "duplicate:write"])
        
        if self.cache_enabled:
            scopes.extend(["cache:read", "cache:write"])
        
        return scopes
    
    def get_api_headers(self) -> Dict[str, str]:
        """Get default API headers."""
        return {
            "User-Agent": f"{self.service_name}/{self.service_version}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Service-ID": self.service_id,
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration as dictionary."""
        config = {
            "host": self.redis_host,
            "port": self.redis_port,
            "db": self.redis_db,
        }
        
        if self.redis_password:
            config["password"] = self.redis_password
        
        return config