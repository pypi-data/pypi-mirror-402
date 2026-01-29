from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IMediaRepository(ABC):
    """Interface for media repository operations"""
    
    @abstractmethod
    async def get_media_by_id(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Get media by ID"""
        pass
    
    @abstractmethod
    async def create_media(self, media_data: Dict[str, Any]) -> bool:
        """Create new media entry"""
        pass
    
    @abstractmethod
    async def update_media(self, media_id: str, media_data: Dict[str, Any]) -> bool:
        """Update media entry"""
        pass
    
    @abstractmethod
    async def delete_media(self, media_id: str) -> bool:
        """Delete media entry"""
        pass
    
    @abstractmethod
    async def get_media_by_news_id(self, news_id: str) -> List[Dict[str, Any]]:
        """Get all media for a news item"""
        pass
    
    @abstractmethod
    async def get_media_by_type(self, media_type: str) -> List[Dict[str, Any]]:
        """Get all media of a specific type"""
        pass