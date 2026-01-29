from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ITextAnalysisRepository(ABC):
    """Interface for text analysis repository operations"""
    
    @abstractmethod
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID"""
        pass
    
    @abstractmethod
    async def create_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """Create new analysis entry"""
        pass
    
    @abstractmethod
    async def update_analysis(self, analysis_id: str, analysis_data: Dict[str, Any]) -> bool:
        """Update analysis entry"""
        pass
    
    @abstractmethod
    async def delete_analysis(self, analysis_id: str) -> bool:
        """Delete analysis entry"""
        pass
    
    @abstractmethod
    async def get_analyses_by_news_id(self, news_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a news item"""
        pass
    
    @abstractmethod
    async def get_analyses_by_type(self, analysis_type: str) -> List[Dict[str, Any]]:
        """Get all analyses of a specific type"""
        pass