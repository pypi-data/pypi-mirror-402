"""
Token Validator for FireFeed Core

Provides token validation utilities for JWT tokens.
"""

import jwt
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime

from .token_manager import ServiceTokenManager
from ..exceptions.api_exceptions import AuthenticationException


class TokenValidator:
    """
    Token validator for JWT tokens.
    
    Provides validation utilities for JWT tokens with additional security checks.
    """
    
    def __init__(self, secret_key: str, issuer: str, algorithm: str = "HS256"):
        """
        Initialize token validator.
        
        Args:
            secret_key: Secret key for JWT verification
            issuer: Expected issuer
            algorithm: JWT algorithm
        """
        self.secret_key = secret_key
        self.issuer = issuer
        self.algorithm = algorithm
        self.token_manager = ServiceTokenManager(secret_key, issuer, algorithm)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationException: If token is invalid
        """
        return self.token_manager.verify_token(token)
    
    def is_token_valid(self, token: str) -> bool:
        """
        Check if token is valid.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is valid, False otherwise
        """
        return self.token_manager.is_token_valid(token)
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        return self.token_manager.is_token_expired(token)
    
    def get_token_remaining_time(self, token: str) -> Optional[int]:
        """
        Get remaining time until token expires.
        
        Args:
            token: JWT token string
            
        Returns:
            Seconds until expiration, or None if invalid
        """
        return self.token_manager.get_token_remaining_time(token)
    
    def has_scope(self, token: str, required_scope: str) -> bool:
        """
        Check if token has required scope.
        
        Args:
            token: JWT token string
            required_scope: Required scope
            
        Returns:
            True if token has scope, False otherwise
        """
        return self.token_manager.has_scope(token, required_scope)
    
    def has_any_scope(self, token: str, required_scopes: list) -> bool:
        """
        Check if token has any of the required scopes.
        
        Args:
            token: JWT token string
            required_scopes: List of required scopes
            
        Returns:
            True if token has any scope, False otherwise
        """
        return self.token_manager.has_any_scope(token, required_scopes)
    
    def validate_issuer_and_subject(
        self,
        token: str,
        expected_issuer: str,
        expected_subject: Optional[str] = None
    ) -> bool:
        """
        Validate token issuer and subject.
        
        Args:
            token: JWT token string
            expected_issuer: Expected issuer
            expected_subject: Expected subject (optional)
            
        Returns:
            True if validation passes, False otherwise
        """
        return self.token_manager.validate_issuer_and_subject(
            token, expected_issuer, expected_subject
        )
    
    def get_claims(self, token: str) -> Dict[str, Any]:
        """
        Get all claims from token without verification.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary of token claims
            
        Raises:
            AuthenticationException: If token is malformed
        """
        return self.token_manager.get_claims(token)
    
    def validate_service_token(
        self,
        token: str,
        expected_service_id: Optional[str] = None,
        required_scopes: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Validate service token with additional checks.
        
        Args:
            token: JWT token string
            expected_service_id: Expected service ID (optional)
            required_scopes: Required scopes (optional)
            
        Returns:
            Decoded token payload
            
        Raises:
            AuthenticationException: If token validation fails
        """
        try:
            # Basic token validation
            payload = self.validate_token(token)
            
            # Check service ID if provided
            if expected_service_id and payload.sub != expected_service_id:
                raise AuthenticationException(
                    f"Invalid service ID: expected {expected_service_id}, got {payload.sub}"
                )
            
            # Check scopes if provided
            if required_scopes:
                if not self.has_any_scope(token, required_scopes):
                    raise AuthenticationException(
                        f"Missing required scopes: {required_scopes}"
                    )
            
            return payload
        
        except AuthenticationException:
            raise
        except Exception as e:
            raise AuthenticationException(f"Token validation failed: {str(e)}")
    
    def is_token_about_to_expire(self, token: str, threshold_minutes: int = 5) -> bool:
        """
        Check if token is about to expire.
        
        Args:
            token: JWT token string
            threshold_minutes: Threshold in minutes
            
        Returns:
            True if token expires within threshold, False otherwise
        """
        remaining_time = self.get_token_remaining_time(token)
        if remaining_time is None:
            return True
        
        return remaining_time <= (threshold_minutes * 60)
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get comprehensive token information.
        
        Args:
            token: JWT token string
            
        Returns:
            Dictionary with token information
        """
        try:
            payload = self.get_claims(token)
            
            return {
                "valid": self.is_token_valid(token),
                "expired": self.is_token_expired(token),
                "issuer": payload.get("iss"),
                "subject": payload.get("sub"),
                "audience": payload.get("aud"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "scopes": payload.get("scope", []),
                "remaining_time": self.get_token_remaining_time(token),
                "about_to_expire": self.is_token_about_to_expire(token)
            }
        
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }