"""
Security Utilities

Common security utilities for FireFeed microservices.
"""

import hashlib
import hmac
import logging
import secrets
import string
from typing import Optional, Union, Dict, Any, List
import base64
import json
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)


def hash_password(password: str, salt_length: int = 32) -> str:
    """
    Hash password with salt using SHA-256.
    
    Args:
        password: Plain text password
        salt_length: Length of salt in bytes
        
    Returns:
        Hashed password with salt (format: salt:hash)
    """
    try:
        # Generate salt
        salt = secrets.token_hex(salt_length)
        
        # Hash password with salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        )
        
        # Return salt and hash
        return f"{salt}:{password_hash.hex()}"
        
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError(f"Failed to hash password: {e}")


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed password.
    
    Args:
        password: Plain text password
        hashed_password: Hashed password with salt
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Split salt and hash
        if ':' not in hashed_password:
            return False
        
        salt, stored_hash = hashed_password.split(':', 1)
        
        # Hash the provided password with the stored salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        
        # Compare hashes
        return password_hash.hex() == stored_hash
        
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def generate_token(length: int = 32, include_symbols: bool = False) -> str:
    """
    Generate cryptographically secure token.
    
    Args:
        length: Token length
        include_symbols: Include symbols in token
        
    Returns:
        Generated token
    """
    try:
        if include_symbols:
            characters = string.ascii_letters + string.digits + "!@#$%^&*"
        else:
            characters = string.ascii_letters + string.digits
        
        return ''.join(secrets.choice(characters) for _ in range(length))
        
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        raise ValueError(f"Failed to generate token: {e}")


def validate_token(token: str, secret_key: str, algorithm: str = 'HS256') -> Optional[Dict[str, Any]]:
    """
    Validate JWT token.
    
    Args:
        token: JWT token string
        secret_key: Secret key for verification
        algorithm: JWT algorithm
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return None


def create_jwt_token(payload: Dict[str, Any], secret_key: str, 
                    expiration_minutes: int = 30, algorithm: str = 'HS256') -> str:
    """
    Create JWT token.
    
    Args:
        payload: Token payload
        secret_key: Secret key for signing
        expiration_minutes: Token expiration in minutes
        algorithm: JWT algorithm
        
    Returns:
        JWT token string
    """
    try:
        # Add expiration time
        expire_time = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        payload['exp'] = expire_time
        
        # Create token
        token = jwt.encode(payload, secret_key, algorithm=algorithm)
        
        # Return as string (not bytes)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token
        
    except Exception as e:
        logger.error(f"Error creating JWT token: {e}")
        raise ValueError(f"Failed to create JWT token: {e}")


def encrypt_data(data: Union[str, Dict, List], key: str, 
                algorithm: str = 'HS256') -> str:
    """
    Encrypt data using JWT.
    
    Args:
        data: Data to encrypt
        key: Encryption key
        algorithm: JWT algorithm
        
    Returns:
        Encrypted data as JWT token
    """
    try:
        # Convert data to payload
        if isinstance(data, (dict, list)):
            payload = {'data': data}
        else:
            payload = {'data': str(data)}
        
        # Create encrypted token
        return create_jwt_token(payload, key, expiration_minutes=1440)  # 24 hours
        
    except Exception as e:
        logger.error(f"Error encrypting data: {e}")
        raise ValueError(f"Failed to encrypt data: {e}")


def decrypt_data(token: str, key: str, algorithm: str = 'HS256') -> Optional[Any]:
    """
    Decrypt data from JWT token.
    
    Args:
        token: JWT token containing encrypted data
        key: Decryption key
        algorithm: JWT algorithm
        
    Returns:
        Decrypted data if valid, None otherwise
    """
    try:
        payload = validate_token(token, key, algorithm)
        if payload and 'data' in payload:
            return payload['data']
        return None
        
    except Exception as e:
        logger.error(f"Error decrypting data: {e}")
        return None


def generate_api_key(prefix: str = "ak", length: int = 32) -> str:
    """
    Generate API key.
    
    Args:
        prefix: Key prefix
        length: Key length
        
    Returns:
        Generated API key
    """
    try:
        random_part = generate_token(length, include_symbols=False)
        return f"{prefix}_{random_part}"
        
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        raise ValueError(f"Failed to generate API key: {e}")


def validate_api_key(api_key: str, prefix: str = "ak") -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        prefix: Expected key prefix
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not api_key or not isinstance(api_key, str):
            return False
        
        if not api_key.startswith(f"{prefix}_"):
            return False
        
        # Check key length (prefix + underscore + random part)
        if len(api_key) < len(prefix) + 1 + 10:  # At least 10 chars after prefix
            return False
        
        # Check for invalid characters
        valid_chars = set(string.ascii_letters + string.digits + '_')
        if not all(c in valid_chars for c in api_key):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return False


def create_hmac_signature(data: Union[str, Dict, List], secret: str, 
                         algorithm: str = 'sha256') -> str:
    """
    Create HMAC signature for data.
    
    Args:
        data: Data to sign
        secret: Secret key
        algorithm: Hash algorithm
        
    Returns:
        HMAC signature
    """
    try:
        # Convert data to string
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Create HMAC
        if algorithm.lower() == 'sha256':
            hash_func = hashlib.sha256
        elif algorithm.lower() == 'sha1':
            hash_func = hashlib.sha1
        elif algorithm.lower() == 'md5':
            hash_func = hashlib.md5
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        signature = hmac.new(
            secret.encode('utf-8'),
            data_str.encode('utf-8'),
            hash_func
        )
        
        return signature.hexdigest()
        
    except Exception as e:
        logger.error(f"Error creating HMAC signature: {e}")
        raise ValueError(f"Failed to create HMAC signature: {e}")


def verify_hmac_signature(data: Union[str, Dict, List], signature: str, 
                         secret: str, algorithm: str = 'sha256') -> bool:
    """
    Verify HMAC signature.
    
    Args:
        data: Data to verify
        signature: Expected signature
        secret: Secret key
        algorithm: Hash algorithm
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = create_hmac_signature(data, secret, algorithm)
        return hmac.compare_digest(expected_signature, signature)
        
    except Exception as e:
        logger.error(f"Error verifying HMAC signature: {e}")
        return False


def sanitize_input(input_str: str, max_length: int = 1000, 
                  allowed_chars: Optional[str] = None) -> str:
    """
    Sanitize user input.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        allowed_chars: Allowed characters (if None, use default)
        
    Returns:
        Sanitized string
    """
    try:
        if not input_str:
            return ""
        
        # Limit length
        if len(input_str) > max_length:
            input_str = input_str[:max_length]
        
        # Default allowed characters (alphanumeric, space, basic punctuation)
        if allowed_chars is None:
            allowed_chars = string.ascii_letters + string.digits + " .,!?:;-'\"()[]{}"
        
        # Remove disallowed characters
        sanitized = ''.join(c for c in input_str if c in allowed_chars)
        
        return sanitized.strip()
        
    except Exception as e:
        logger.error(f"Error sanitizing input: {e}")
        return ""


def generate_csrf_token(secret: str, user_id: Optional[str] = None) -> str:
    """
    Generate CSRF token.
    
    Args:
        secret: Secret key
        user_id: Optional user identifier
        
    Returns:
        CSRF token
    """
    try:
        # Create payload
        payload = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id or generate_token(16)
        }
        
        # Create token
        return create_jwt_token(payload, secret, expiration_minutes=60)
        
    except Exception as e:
        logger.error(f"Error generating CSRF token: {e}")
        raise ValueError(f"Failed to generate CSRF token: {e}")


def verify_csrf_token(token: str, secret: str, user_id: Optional[str] = None) -> bool:
    """
    Verify CSRF token.
    
    Args:
        token: CSRF token
        secret: Secret key
        user_id: Optional user identifier to verify
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        payload = validate_token(token, secret)
        if not payload:
            return False
        
        # Verify user ID if provided
        if user_id and payload.get('user_id') != user_id:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying CSRF token: {e}")
        return False


def is_safe_redirect_url(url: str, allowed_domains: Optional[List[str]] = None) -> bool:
    """
    Check if redirect URL is safe.
    
    Args:
        url: URL to check
        allowed_domains: List of allowed domains
        
    Returns:
        True if URL is safe, False otherwise
    """
    try:
        if not url:
            return False
        
        # Check for relative URLs
        if url.startswith('/') and not url.startswith('//'):
            return True
        
        # Check for allowed schemes
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check for allowed domains if specified
        if allowed_domains:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.netloc not in allowed_domains:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking redirect URL: {e}")
        return False


def mask_sensitive_data(data: Union[str, Dict, List], 
                       mask_char: str = '*') -> Union[str, Dict, List]:
    """
    Mask sensitive data.
    
    Args:
        data: Data to mask
        mask_char: Character to use for masking
        
    Returns:
        Masked data
    """
    try:
        if isinstance(data, str):
            if len(data) <= 4:
                return mask_char * len(data)
            return data[:2] + mask_char * (len(data) - 4) + data[-2:]
        elif isinstance(data, dict):
            return {k: mask_sensitive_data(v, mask_char) for k, v in data.items()}
        elif isinstance(data, list):
            return [mask_sensitive_data(item, mask_char) for item in data]
        else:
            return data
        
    except Exception as e:
        logger.error(f"Error masking sensitive data: {e}")
        return data