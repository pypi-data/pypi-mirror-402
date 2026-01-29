"""
Time utilities for FireFeed Core

Time formatting and parsing utilities.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Dict
import logging

logger = logging.getLogger(__name__)


class TimeUtils:
    """Time formatting and parsing utilities."""
    
    # Common time formats
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    ISO_FORMAT_NO_MS = "%Y-%m-%dT%H:%M:%SZ"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    
    @staticmethod
    def get_utc_now() -> datetime:
        """
        Get current UTC datetime.
        
        Returns:
            Current UTC datetime
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def get_utc_now_iso() -> str:
        """
        Get current UTC datetime in ISO format.
        
        Returns:
            Current UTC datetime as ISO string
        """
        return TimeUtils.get_utc_now().isoformat()
    
    @staticmethod
    def parse_datetime(dt_str: str) -> Optional[datetime]:
        """
        Parse datetime string to datetime object.
        
        Args:
            dt_str: Datetime string
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not dt_str:
            return None
        
        formats = [
            TimeUtils.ISO_FORMAT,
            TimeUtils.ISO_FORMAT_NO_MS,
            TimeUtils.DATETIME_FORMAT,
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                # If no timezone info, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        logger.warning(f"Failed to parse datetime: {dt_str}")
        return None
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = ISO_FORMAT) -> str:
        """
        Format datetime object to string.
        
        Args:
            dt: Datetime object
            format_str: Format string
            
        Returns:
            Formatted datetime string
        """
        if dt is None:
            return ""
        
        # Ensure timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.strftime(format_str)
    
    @staticmethod
    def format_utc_datetime(dt: datetime) -> str:
        """
        Format datetime as UTC ISO string.
        
        Args:
            dt: Datetime object
            
        Returns:
            UTC ISO formatted string
        """
        return TimeUtils.format_datetime(dt, TimeUtils.ISO_FORMAT)
    
    @staticmethod
    def time_since(dt: datetime) -> str:
        """
        Get human-readable time since datetime.
        
        Args:
            dt: Datetime object
            
        Returns:
            Human-readable time string
        """
        if dt is None:
            return "unknown"
        
        now = TimeUtils.get_utc_now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds // 60)} minutes ago"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        elif seconds < 2592000:  # 30 days
            return f"{int(seconds // 86400)} days ago"
        elif seconds < 31536000:  # 365 days
            return f"{int(seconds // 2592000)} months ago"
        else:
            return f"{int(seconds // 31536000)} years ago"
    
    @staticmethod
    def add_time(dt: datetime, **kwargs) -> datetime:
        """
        Add time to datetime.
        
        Args:
            dt: Datetime object
            **kwargs: Time to add (days, hours, minutes, seconds, etc.)
            
        Returns:
            New datetime object
        """
        if dt is None:
            return None
        
        return dt + timedelta(**kwargs)
    
    @staticmethod
    def subtract_time(dt: datetime, **kwargs) -> datetime:
        """
        Subtract time from datetime.
        
        Args:
            dt: Datetime object
            **kwargs: Time to subtract (days, hours, minutes, seconds, etc.)
            
        Returns:
            New datetime object
        """
        if dt is None:
            return None
        
        return dt - timedelta(**kwargs)
    
    @staticmethod
    def is_expired(dt: datetime, grace_period: Optional[timedelta] = None) -> bool:
        """
        Check if datetime is expired.
        
        Args:
            dt: Datetime object
            grace_period: Optional grace period
            
        Returns:
            True if expired, False otherwise
        """
        if dt is None:
            return True
        
        now = TimeUtils.get_utc_now()
        
        if grace_period:
            dt = dt + grace_period
        
        return now > dt
    
    @staticmethod
    def get_start_of_day(dt: Optional[datetime] = None) -> datetime:
        """
        Get start of day (00:00:00) for given datetime.
        
        Args:
            dt: Datetime object (defaults to now)
            
        Returns:
            Start of day datetime
        """
        if dt is None:
            dt = TimeUtils.get_utc_now()
        
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_day(dt: Optional[datetime] = None) -> datetime:
        """
        Get end of day (23:59:59) for given datetime.
        
        Args:
            dt: Datetime object (defaults to now)
            
        Returns:
            End of day datetime
        """
        if dt is None:
            dt = TimeUtils.get_utc_now()
        
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    @staticmethod
    def get_start_of_month(dt: Optional[datetime] = None) -> datetime:
        """
        Get start of month (01-01 00:00:00) for given datetime.
        
        Args:
            dt: Datetime object (defaults to now)
            
        Returns:
            Start of month datetime
        """
        if dt is None:
            dt = TimeUtils.get_utc_now()
        
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def get_end_of_month(dt: Optional[datetime] = None) -> datetime:
        """
        Get end of month for given datetime.
        
        Args:
            dt: Datetime object (defaults to now)
            
        Returns:
            End of month datetime
        """
        if dt is None:
            dt = TimeUtils.get_utc_now()
        
        # Get first day of next month
        if dt.month == 12:
            next_month = dt.replace(year=dt.year + 1, month=1)
        else:
            next_month = dt.replace(month=dt.month + 1)
        
        # Subtract one day
        return next_month - timedelta(days=1)
    
    @staticmethod
    def get_age(dt: datetime) -> timedelta:
        """
        Get age of datetime (time since).
        
        Args:
            dt: Datetime object
            
        Returns:
            Age as timedelta
        """
        if dt is None:
            return timedelta(0)
        
        return TimeUtils.get_utc_now() - dt
    
    @staticmethod
    def to_timestamp(dt: datetime) -> int:
        """
        Convert datetime to Unix timestamp.
        
        Args:
            dt: Datetime object
            
        Returns:
            Unix timestamp
        """
        if dt is None:
            return 0
        
        return int(dt.timestamp())
    
    @staticmethod
    def from_timestamp(timestamp: Union[int, float]) -> datetime:
        """
        Convert Unix timestamp to datetime.
        
        Args:
            timestamp: Unix timestamp
            
        Returns:
            Datetime object
        """
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    
    @staticmethod
    def round_to_minutes(dt: datetime, minutes: int = 5) -> datetime:
        """
        Round datetime to nearest minutes.
        
        Args:
            dt: Datetime object
            minutes: Minutes to round to
            
        Returns:
            Rounded datetime
        """
        rounded = dt - timedelta(
            minutes=dt.minute % minutes,
            seconds=dt.second,
            microseconds=dt.microsecond
        )
        return rounded
    
    @staticmethod
    def get_business_hours(start_time: str = "09:00", end_time: str = "17:00") -> Dict[str, datetime]:
        """
        Get business hours for current day.
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            
        Returns:
            Dictionary with start and end datetimes
        """
        now = TimeUtils.get_utc_now()
        
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        start_dt = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_dt = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        return {
            "start": start_dt,
            "end": end_dt
        }