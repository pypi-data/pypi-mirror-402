"""
Validation Utilities

Common validation utilities for FireFeed microservices.
"""

import re
import logging
from typing import Optional, Union, List, Dict, Any
import ipaddress
import validators

logger = logging.getLogger(__name__)


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Default allowed schemes
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https', 'ftp', 'ftps']
    
    try:
        # Check if URL is valid format
        if not validators.url(url):
            return False
        
        # Check scheme
        scheme = url.split('://')[0].lower()
        if scheme not in allowed_schemes:
            logger.warning(f"URL scheme '{scheme}' not allowed. Allowed: {allowed_schemes}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating URL: {e}")
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    try:
        if not re.match(email_pattern, email):
            return False
        
        # Additional validation using validators library
        if not validators.email(email):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating email: {e}")
        return False


def validate_phone(phone: str, country_code: Optional[str] = None) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        country_code: Country code for validation
        
    Returns:
        True if phone number is valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all non-digit characters except +
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    try:
        # Basic phone number pattern (allowing + and digits)
        phone_pattern = r'^\+?[\d]{6,15}$'
        
        if not re.match(phone_pattern, cleaned_phone):
            return False
        
        # Additional validation using validators library if available
        try:
            if not validators.phone(cleaned_phone):
                return False
        except:
            # If validators.phone is not available, use basic validation
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating phone: {e}")
        return False


def validate_username(username: str, min_length: int = 3, max_length: int = 30) -> bool:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        min_length: Minimum username length
        max_length: Maximum username length
        
    Returns:
        True if username is valid, False otherwise
    """
    if not username or not isinstance(username, str):
        return False
    
    # Username pattern: alphanumeric, underscore, hyphen
    username_pattern = r'^[a-zA-Z0-9_-]+$'
    
    try:
        # Check length
        if not (min_length <= len(username) <= max_length):
            return False
        
        # Check format
        if not re.match(username_pattern, username):
            return False
        
        # Check for reserved names
        reserved_names = ['admin', 'root', 'system', 'null', 'undefined']
        if username.lower() in reserved_names:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating username: {e}")
        return False


def validate_password(password: str, min_length: int = 8, require_complexity: bool = True) -> bool:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        require_complexity: Require uppercase, lowercase, digit, and special character
        
    Returns:
        True if password is valid, False otherwise
    """
    if not password or not isinstance(password, str):
        return False
    
    try:
        # Check minimum length
        if len(password) < min_length:
            return False
        
        if not require_complexity:
            return True
        
        # Check complexity requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        return all([has_upper, has_lower, has_digit, has_special])
        
    except Exception as e:
        logger.error(f"Error validating password: {e}")
        return False


def validate_domain(domain: str) -> bool:
    """
    Validate domain name format.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if domain is valid, False otherwise
    """
    if not domain or not isinstance(domain, str):
        return False
    
    # Domain pattern
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    
    try:
        # Check format
        if not re.match(domain_pattern, domain):
            return False
        
        # Check length
        if len(domain) > 253:
            return False
        
        # Check for consecutive dots
        if '..' in domain:
            return False
        
        # Additional validation using validators library
        if not validators.domain(domain):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating domain: {e}")
        return False


def validate_ip_address(ip: str, version: Optional[int] = None) -> bool:
    """
    Validate IP address format.
    
    Args:
        ip: IP address to validate
        version: IP version (4 or 6), None for any
        
    Returns:
        True if IP address is valid, False otherwise
    """
    if not ip or not isinstance(ip, str):
        return False
    
    try:
        # Validate using ipaddress module
        ip_obj = ipaddress.ip_address(ip)
        
        # Check version if specified
        if version is not None:
            if ip_obj.version != version:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating IP address: {e}")
        return False


def validate_slug(slug: str, max_length: int = 50) -> bool:
    """
    Validate slug format.
    
    Args:
        slug: Slug to validate
        max_length: Maximum slug length
        
    Returns:
        True if slug is valid, False otherwise
    """
    if not slug or not isinstance(slug, str):
        return False
    
    # Slug pattern: lowercase letters, numbers, hyphens
    slug_pattern = r'^[a-z0-9-]+$'
    
    try:
        # Check length
        if len(slug) > max_length:
            return False
        
        # Check format
        if not re.match(slug_pattern, slug):
            return False
        
        # Check for consecutive hyphens
        if '--' in slug:
            return False
        
        # Check for leading/trailing hyphens
        if slug.startswith('-') or slug.endswith('-'):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating slug: {e}")
        return False


def validate_uuid(uuid_string: str, version: Optional[int] = None) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
        version: UUID version (1-5), None for any
        
    Returns:
        True if UUID is valid, False otherwise
    """
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    # UUID pattern
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    try:
        # Check format
        if not re.match(uuid_pattern, uuid_string.lower()):
            return False
        
        # Additional validation using uuid module
        import uuid
        parsed_uuid = uuid.UUID(uuid_string)
        
        # Check version if specified
        if version is not None:
            if parsed_uuid.version != version:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating UUID: {e}")
        return False


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: File name to validate
        allowed_extensions: List of allowed file extensions
        
    Returns:
        True if file extension is valid, False otherwise
    """
    if not filename or not isinstance(filename, str):
        return False
    
    try:
        # Get file extension
        extension = filename.split('.')[-1].lower()
        
        # Check if extension is in allowed list
        return extension in [ext.lower() for ext in allowed_extensions]
        
    except Exception as e:
        logger.error(f"Error validating file extension: {e}")
        return False


def validate_json(json_data: Union[str, Dict, List]) -> bool:
    """
    Validate JSON data.
    
    Args:
        json_data: JSON data to validate
        
    Returns:
        True if JSON is valid, False otherwise
    """
    import json
    
    try:
        if isinstance(json_data, str):
            json.loads(json_data)
        elif isinstance(json_data, (dict, list)):
            json.dumps(json_data)
        else:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating JSON: {e}")
        return False


def validate_integer_range(value: Union[int, str], min_val: Optional[int] = None, 
                          max_val: Optional[int] = None) -> bool:
    """
    Validate integer value within range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        True if value is valid, False otherwise
    """
    try:
        # Convert to integer if string
        if isinstance(value, str):
            value = int(value)
        
        # Check if integer
        if not isinstance(value, int):
            return False
        
        # Check range
        if min_val is not None and value < min_val:
            return False
        
        if max_val is not None and value > max_val:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating integer range: {e}")
        return False


def validate_boolean(value: Union[bool, str, int]) -> bool:
    """
    Validate boolean value.
    
    Args:
        value: Value to validate
        
    Returns:
        True if value is valid boolean, False otherwise
    """
    try:
        if isinstance(value, bool):
            return True
        elif isinstance(value, str):
            return value.lower() in ['true', 'false', '1', '0', 'yes', 'no']
        elif isinstance(value, int):
            return value in [0, 1]
        else:
            return False
        
    except Exception as e:
        logger.error(f"Error validating boolean: {e}")
        return False