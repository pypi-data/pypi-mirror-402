from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IEmailRepository(ABC):
    """Interface for email repository operations"""
    
    @abstractmethod
    async def get_email_by_id(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Get email by ID"""
        pass
    
    @abstractmethod
    async def create_email(self, email_data: Dict[str, Any]) -> bool:
        """Create new email entry"""
        pass
    
    @abstractmethod
    async def update_email(self, email_id: str, email_data: Dict[str, Any]) -> bool:
        """Update email entry"""
        pass
    
    @abstractmethod
    async def delete_email(self, email_id: str) -> bool:
        """Delete email entry"""
        pass
    
    @abstractmethod
    async def get_emails_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all emails for a user"""
        pass
    
    @abstractmethod
    async def get_emails_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get all emails with a specific status"""
        pass