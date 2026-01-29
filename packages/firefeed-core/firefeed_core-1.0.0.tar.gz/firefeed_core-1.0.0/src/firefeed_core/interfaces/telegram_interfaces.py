"""
Telegram Bot Interfaces

Abstract interfaces for Telegram bot functionality in FireFeed microservices.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class TelegramMessage:
    """Telegram message data structure"""
    chat_id: int
    text: str
    message_id: Optional[int] = None
    reply_markup: Optional[Dict] = None
    parse_mode: Optional[str] = None


@dataclass
class TelegramUser:
    """Telegram user data structure"""
    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class ITelegramBot(ABC):
    """Interface for Telegram bot operations"""
    
    @abstractmethod
    async def send_message(self, chat_id: int, text: str, 
                          reply_markup: Optional[Dict] = None,
                          parse_mode: Optional[str] = None) -> bool:
        """Send message to user"""
        pass
    
    @abstractmethod
    async def send_photo(self, chat_id: int, photo_url: str, 
                        caption: Optional[str] = None) -> bool:
        """Send photo to user"""
        pass
    
    @abstractmethod
    async def send_video(self, chat_id: int, video_url: str,
                        caption: Optional[str] = None) -> bool:
        """Send video to user"""
        pass
    
    @abstractmethod
    async def set_webhook(self, url: str) -> bool:
        """Set webhook URL"""
        pass
    
    @abstractmethod
    async def delete_webhook(self) -> bool:
        """Delete webhook"""
        pass
    
    @abstractmethod
    async def get_webhook_info(self) -> Dict[str, Any]:
        """Get webhook information"""
        pass


class ITelegramUserService(ABC):
    """Interface for Telegram user management"""
    
    @abstractmethod
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        pass
    
    @abstractmethod
    async def link_telegram_to_user(self, telegram_id: int, user_id: int) -> bool:
        """Link Telegram account to web user"""
        pass
    
    @abstractmethod
    async def unlink_telegram_from_user(self, user_id: int) -> bool:
        """Unlink Telegram account from web user"""
        pass
    
    @abstractmethod
    async def generate_link_code(self, user_id: int) -> str:
        """Generate link code for Telegram account"""
        pass
    
    @abstractmethod
    async def verify_link_code(self, telegram_id: int, link_code: str) -> bool:
        """Verify Telegram link code"""
        pass


class ITelegramNotificationService(ABC):
    """Interface for Telegram notifications"""
    
    @abstractmethod
    async def send_rss_notification(self, chat_id: int, rss_item: Dict[str, Any],
                                   language: str = "en") -> bool:
        """Send RSS item notification"""
        pass
    
    @abstractmethod
    async def send_subscription_notification(self, chat_id: int, message: str) -> bool:
        """Send subscription notification"""
        pass
    
    @abstractmethod
    async def send_error_notification(self, chat_id: int, error_message: str) -> bool:
        """Send error notification"""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: str, user_ids: List[int]) -> int:
        """Broadcast message to multiple users"""
        pass


class ITelegramSubscriptionService(ABC):
    """Interface for Telegram subscriptions"""
    
    @abstractmethod
    async def get_user_subscriptions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user subscriptions"""
        pass
    
    @abstractmethod
    async def add_subscription(self, user_id: int, category_id: int) -> bool:
        """Add subscription to category"""
        pass
    
    @abstractmethod
    async def remove_subscription(self, user_id: int, category_id: int) -> bool:
        """Remove subscription from category"""
        pass
    
    @abstractmethod
    async def get_subscribed_categories(self, user_id: int) -> List[int]:
        """Get list of subscribed category IDs"""
        pass
    
    @abstractmethod
    async def is_subscribed_to_category(self, user_id: int, category_id: int) -> bool:
        """Check if user is subscribed to category"""
        pass


class ITelegramCacheService(ABC):
    """Interface for Telegram caching"""
    
    @abstractmethod
    async def set_user_state(self, user_id: int, state: str, data: Dict[str, Any] = None) -> bool:
        """Set user state"""
        pass
    
    @abstractmethod
    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user state"""
        pass
    
    @abstractmethod
    async def clear_user_state(self, user_id: int) -> bool:
        """Clear user state"""
        pass
    
    @abstractmethod
    async def set_temp_data(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set temporary data with TTL"""
        pass
    
    @abstractmethod
    async def get_temp_data(self, key: str) -> Optional[Any]:
        """Get temporary data"""
        pass
    
    @abstractmethod
    async def delete_temp_data(self, key: str) -> bool:
        """Delete temporary data"""
        pass


class ITelegramHealthChecker(ABC):
    """Interface for Telegram bot health checking"""
    
    @abstractmethod
    async def check_bot_health(self) -> Dict[str, Any]:
        """Check bot health status"""
        pass
    
    @abstractmethod
    async def check_webhook_status(self) -> Dict[str, Any]:
        """Check webhook status"""
        pass
    
    @abstractmethod
    async def check_api_connection(self) -> bool:
        """Check API connection"""
        pass
    
    @abstractmethod
    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information"""
        pass