# models/rss_models.py - RSS data models
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Model for representing RSS item
class RSSItem(BaseModel):
    """RSS item model matching published_news_data table structure."""
    
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
    translations: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# Model for representing RSS feed
@dataclass
class RSSFeed:
    """RSS feed model matching rss_feeds table structure."""
    id: int
    source_id: int
    url: str
    name: str
    category_id: Optional[int] = None
    language: str = "en"
    is_active: bool = True
    created_at: Optional[str] = None  # ISO date-time format
    updated_at: Optional[str] = None  # ISO date-time format
    cooldown_minutes: int = 10
    max_news_per_hour: int = 10

# Model for representing news in API
class NewsItem(BaseModel):
    """News item model for API responses."""
    news_id: str
    original_title: str
    original_content: str
    original_language: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None  # News source name
    source_alias: Optional[str] = None  # News source alias
    source_url: Optional[str] = None
    created_at: Optional[str] = None  # ISO date-time format
    feed_id: Optional[int] = None  # RSS feed ID for grouping and processing
    translations: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Model for representing user state
@dataclass
class UserState:
    """User state structure."""
    current_subs: list
    language: str
    last_access: float

# Model for representing user menu state
@dataclass
class UserMenu:
    """User menu state structure."""
    menu: str
    last_access: float

# Model for representing user language state
@dataclass
class UserLanguage:
    """User language state structure."""
    language: str
    last_access: float