"""
Cache Utilities

Common cache utilities for FireFeed microservices.
"""

import json
import logging
import pickle
import zlib
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


def create_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Create a cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a string representation of all arguments
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    
    # Create hash of the key parts
    key_string = ":".join([prefix] + key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"{prefix}:{key_hash}"


def serialize_cache_data(data: Any, compression: bool = True, 
                        format: str = 'pickle') -> bytes:
    """
    Serialize data for cache storage.
    
    Args:
        data: Data to serialize
        compression: Whether to compress the data
        format: Serialization format ('pickle' or 'json')
        
    Returns:
        Serialized data as bytes
    """
    try:
        if format.lower() == 'json':
            serialized = json.dumps(data, default=str).encode()
        else:
            serialized = pickle.dumps(data)
        
        if compression:
            serialized = zlib.compress(serialized)
        
        return serialized
        
    except Exception as e:
        logger.error(f"Error serializing cache data: {e}")
        raise ValueError(f"Failed to serialize cache data: {e}")


def deserialize_cache_data(data: bytes, compression: bool = True,
                          format: str = 'pickle') -> Any:
    """
    Deserialize data from cache storage.
    
    Args:
        data: Serialized data as bytes
        compression: Whether data is compressed
        format: Serialization format ('pickle' or 'json')
        
    Returns:
        Deserialized data
    """
    try:
        if compression:
            data = zlib.decompress(data)
        
        if format.lower() == 'json':
            return json.loads(data.decode())
        else:
            return pickle.loads(data)
        
    except Exception as e:
        logger.error(f"Error deserializing cache data: {e}")
        raise ValueError(f"Failed to deserialize cache data: {e}")


def compress_cache_data(data: bytes) -> bytes:
    """
    Compress cache data using zlib.
    
    Args:
        data: Data to compress
        
    Returns:
        Compressed data
    """
    return zlib.compress(data)


def decompress_cache_data(data: bytes) -> bytes:
    """
    Decompress cache data using zlib.
    
    Args:
        data: Compressed data
        
    Returns:
        Decompressed data
    """
    return zlib.decompress(data)


def get_cache_ttl(expiration: Union[int, timedelta, datetime]) -> int:
    """
    Convert expiration to TTL in seconds.
    
    Args:
        expiration: Expiration time (seconds, timedelta, or datetime)
        
    Returns:
        TTL in seconds
    """
    if isinstance(expiration, int):
        return expiration
    elif isinstance(expiration, timedelta):
        return int(expiration.total_seconds())
    elif isinstance(expiration, datetime):
        return int((expiration - datetime.now()).total_seconds())
    else:
        raise ValueError("Expiration must be int, timedelta, or datetime")


def is_cache_expired(timestamp: float, ttl: int) -> bool:
    """
    Check if cache entry has expired.
    
    Args:
        timestamp: Cache entry creation timestamp
        ttl: Time to live in seconds
        
    Returns:
        True if expired, False otherwise
    """
    current_time = datetime.now().timestamp()
    return current_time - timestamp > ttl


def calculate_cache_size(data: Dict[str, Any]) -> int:
    """
    Calculate approximate cache size in bytes.
    
    Args:
        data: Cache data dictionary
        
    Returns:
        Size in bytes
    """
    try:
        return len(pickle.dumps(data))
    except:
        return len(str(data).encode())


def clean_expired_cache_entries(cache_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Remove expired entries from cache data.
    
    Args:
        cache_data: Cache data with metadata
        
    Returns:
        Cleaned cache data
    """
    current_time = datetime.now().timestamp()
    cleaned_data = {}
    
    for key, entry in cache_data.items():
        if 'ttl' in entry and 'timestamp' in entry:
            if current_time - entry['timestamp'] <= entry['ttl']:
                cleaned_data[key] = entry
        else:
            cleaned_data[key] = entry
    
    return cleaned_data


def create_cache_metadata(ttl: int, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create cache metadata.
    
    Args:
        ttl: Time to live in seconds
        tags: Optional list of cache tags
        
    Returns:
        Cache metadata dictionary
    """
    return {
        'timestamp': datetime.now().timestamp(),
        'ttl': ttl,
        'tags': tags or [],
        'size': 0  # Will be updated when data is stored
    }


def generate_cache_hash(data: Any) -> str:
    """
    Generate hash for cache data.
    
    Args:
        data: Data to hash
        
    Returns:
        Hash string
    """
    try:
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, list):
            data_str = json.dumps(sorted(data))
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating cache hash: {e}")
        return hashlib.md5(str(data).encode()).hexdigest()


def should_cache_data(data: Any, min_size: int = 100, max_size: int = 1024*1024) -> bool:
    """
    Determine if data should be cached based on size and type.
    
    Args:
        data: Data to evaluate
        min_size: Minimum size to cache in bytes
        max_size: Maximum size to cache in bytes
        
    Returns:
        True if data should be cached, False otherwise
    """
    try:
        # Don't cache None or empty data
        if data is None:
            return False
        
        # Calculate data size
        try:
            size = len(pickle.dumps(data))
        except:
            size = len(str(data).encode())
        
        # Check size constraints
        if size < min_size or size > max_size:
            return False
        
        # Don't cache certain types of data
        if isinstance(data, (Exception, type)):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error evaluating cache criteria: {e}")
        return False


def merge_cache_entries(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two cache entries.
    
    Args:
        old_data: Existing cache data
        new_data: New cache data
        
    Returns:
        Merged cache data
    """
    merged = old_data.copy()
    merged.update(new_data)
    return merged


def filter_cache_by_tags(cache_data: Dict[str, Dict[str, Any]], 
                         tags: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Filter cache entries by tags.
    
    Args:
        cache_data: Cache data with metadata
        tags: List of tags to filter by
        
    Returns:
        Filtered cache data
    """
    filtered_data = {}
    
    for key, entry in cache_data.items():
        if 'tags' in entry:
            entry_tags = set(entry['tags'])
            if entry_tags.intersection(set(tags)):
                filtered_data[key] = entry
    
    return filtered_data


def get_cache_stats(cache_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Args:
        cache_data: Cache data with metadata
        
    Returns:
        Cache statistics
    """
    total_entries = len(cache_data)
    total_size = 0
    expired_entries = 0
    current_time = datetime.now().timestamp()
    
    tag_counts = {}
    
    for entry in cache_data.values():
        if 'size' in entry:
            total_size += entry['size']
        
        if 'ttl' in entry and 'timestamp' in entry:
            if current_time - entry['timestamp'] > entry['ttl']:
                expired_entries += 1
        
        if 'tags' in entry:
            for tag in entry['tags']:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    return {
        'total_entries': total_entries,
        'total_size_bytes': total_size,
        'total_size_mb': total_size / (1024 * 1024),
        'expired_entries': expired_entries,
        'active_entries': total_entries - expired_entries,
        'tag_counts': tag_counts
    }


def validate_cache_key(key: str) -> bool:
    """
    Validate cache key format.
    
    Args:
        key: Cache key to validate
        
    Returns:
        True if key is valid, False otherwise
    """
    if not key or not isinstance(key, str):
        return False
    
    # Check for invalid characters
    invalid_chars = [' ', '\n', '\r', '\t', '\0', '\x0b', '/', '\\', '?', '&', '=', '#']
    for char in invalid_chars:
        if char in key:
            return False
    
    # Check length
    if len(key) > 250:
        return False
    
    return True


def sanitize_cache_key(key: str) -> str:
    """
    Sanitize cache key by removing invalid characters.
    
    Args:
        key: Cache key to sanitize
        
    Returns:
        Sanitized cache key
    """
    # Replace invalid characters with underscores
    invalid_chars = [' ', '\n', '\r', '\t', '\0', '\x0b', '/', '\\', '?', '&', '=', '#']
    for char in invalid_chars:
        key = key.replace(char, '_')
    
    # Remove multiple consecutive underscores
    while '__' in key:
        key = key.replace('__', '_')
    
    # Remove leading/trailing underscores
    key = key.strip('_')
    
    return key