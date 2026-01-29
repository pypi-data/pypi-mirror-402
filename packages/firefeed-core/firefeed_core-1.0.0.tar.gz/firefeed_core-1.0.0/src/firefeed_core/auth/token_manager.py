"""
Service Token Manager for FireFeed Core

Provides JWT token generation and validation for inter-service authentication.
"""

import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from ..exceptions.api_exceptions import AuthenticationException


@dataclass
class TokenPayload:
    """Standard JWT payload structure for FireFeed services."""
    iss: str  # Issuer (service name)
    sub: str  # Subject (service ID)
    aud: Union[str, List[str]]  # Audience
    iat: int  # Issued at
    exp: int  # Expires at
    jti: Optional[str] = None  # JWT ID
    scope: Optional[List[str]] = None  # Permissions/scopes
    service_type: Optional[str] = None  # Type of service
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


class ServiceTokenManager:
    """
    JWT token manager for FireFeed microservices.
    
    Handles token generation, validation, and rotation for secure
    inter-service communication.
    """
    
    # Default token expiration (1 hour)
    DEFAULT_EXPIRATION = 3600
    
    # Supported algorithms
    SUPPORTED_ALGORITHMS = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
    
    def __init__(
        self,
        secret_key: str,
        issuer: str,
        algorithm: str = "HS256",
        default_expiration: int = None
    ):
        """
        Initialize token manager.
        
        Args:
            secret_key: Secret key for JWT signing
            issuer: Issuer identifier (e.g., "firefeed-api")
            algorithm: JWT signing algorithm
            default_expiration: Default token expiration in seconds
        """
        self.secret_key = secret_key
        self.issuer = issuer
        self.algorithm = algorithm
        self.default_expiration = default_expiration or self.DEFAULT_EXPIRATION
        
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def generate_service_token(
        self,
        service_id: str,
        audience: Union[str, List[str]],
        scopes: Optional[List[str]] = None,
        expiration: Optional[int] = None,
        service_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        jti: Optional[str] = None
    ) -> str:
        """
        Generate JWT token for service authentication.
        
        Args:
            service_id: Unique service identifier
            audience: Target audience (service name(s))
            scopes: Permission scopes
            expiration: Token expiration in seconds
            service_type: Type of service (api, parser, bot, etc.)
            metadata: Additional metadata
            jti: JWT ID for token tracking
            
        Returns:
            JWT token string
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not service_id:
            raise ValueError("service_id is required")
        
        if not audience:
            raise ValueError("audience is required")
        
        # Set expiration
        exp_seconds = expiration or self.default_expiration
        
        # Calculate timestamps
        now = datetime.utcnow()
        iat = int(now.timestamp())
        exp = int((now + timedelta(seconds=exp_seconds)).timestamp())
        
        # Create payload
        payload = {
            "iss": self.issuer,
            "sub": service_id,
            "aud": audience,
            "iat": iat,
            "exp": exp,
            "jti": jti or f"{service_id}-{iat}",
        }
        
        # Add optional fields
        if scopes:
            payload["scope"] = scopes
        
        if service_type:
            payload["service_type"] = service_type
        
        if metadata:
            payload["metadata"] = metadata
        
        # Generate token
        try:
            token = jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.algorithm
            )
            return token
        
        except Exception as e:
            raise AuthenticationException(f"Token generation failed: {str(e)}")
    
    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenPayload object with decoded data
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        if not token:
            raise AuthenticationException("No token provided")
        
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Convert to TokenPayload
            return TokenPayload(
                iss=payload["iss"],
                sub=payload["sub"],
                aud=payload["aud"],
                iat=payload["iat"],
                exp=payload["exp"],
                jti=payload.get("jti"),
                scope=payload.get("scope"),
                service_type=payload.get("service_type"),
                metadata=payload.get("metadata")
            )
        
        except jwt.ExpiredSignatureError:
            raise AuthenticationException("Token has expired")
        
        except jwt.InvalidTokenError as e:
            raise AuthenticationException(f"Invalid token: {str(e)}")
        
        except Exception as e:
            raise AuthenticationException(f"Token verification failed: {str(e)}")
    
    def is_token_valid(self, token: str) -> bool:
        """
        Check if token is valid without raising exceptions.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            self.verify_token(token)
            return True
        except AuthenticationException:
            return False
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired.
        
        Args:
            token: JWT token string
            
        Returns:
            True if token is expired, False otherwise
        """
        try:
            payload = self.verify_token(token)
            current_time = int(time.time())
            return payload.exp < current_time
        except AuthenticationException:
            return True
    
    def get_token_remaining_time(self, token: str) -> Optional[int]:
        """
        Get remaining time until token expires.
        
        Args:
            token: JWT token string
            
        Returns:
            Seconds until expiration, or None if invalid
        """
        try:
            payload = self.verify_token(token)
            current_time = int(time.time())
            remaining = payload.exp - current_time
            return max(0, remaining)
        except AuthenticationException:
            return None
    
    def has_scope(self, token: str, required_scope: str) -> bool:
        """
        Check if token has required scope.
        
        Args:
            token: JWT token string
            required_scope: Required scope
            
        Returns:
            True if token has scope, False otherwise
        """
        try:
            payload = self.verify_token(token)
            scopes = payload.scope or []
            return required_scope in scopes
        except AuthenticationException:
            return False
    
    def has_any_scope(self, token: str, required_scopes: List[str]) -> bool:
        """
        Check if token has any of the required scopes.
        
        Args:
            token: JWT token string
            required_scopes: List of required scopes
            
        Returns:
            True if token has any scope, False otherwise
        """
        try:
            payload = self.verify_token(token)
            scopes = payload.scope or []
            return any(scope in scopes for scope in required_scopes)
        except AuthenticationException:
            return False
    
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
        try:
            payload = self.verify_token(token)
            
            # Check issuer
            if payload.iss != expected_issuer:
                return False
            
            # Check subject if provided
            if expected_subject and payload.sub != expected_subject:
                return False
            
            return True
        
        except AuthenticationException:
            return False
    
    def generate_refresh_token(
        self,
        service_id: str,
        audience: Union[str, List[str]],
        expiration: int = 86400  # 24 hours
    ) -> str:
        """
        Generate refresh token for long-lived access.
        
        Args:
            service_id: Service identifier
            audience: Target audience
            expiration: Token expiration in seconds
            
        Returns:
            Refresh token string
        """
        return self.generate_service_token(
            service_id=service_id,
            audience=audience,
            scopes=["refresh"],
            expiration=expiration,
            service_type="refresh"
        )
    
    def rotate_token(
        self,
        old_token: str,
        service_id: str,
        audience: Union[str, List[str]],
        scopes: Optional[List[str]] = None
    ) -> str:
        """
        Rotate token with updated expiration.
        
        Args:
            old_token: Current token
            service_id: Service identifier
            audience: Target audience
            scopes: Permission scopes
            
        Returns:
            New token string
        """
        try:
            # Verify old token and extract metadata
            old_payload = self.verify_token(old_token)
            
            # Generate new token with same metadata but new expiration
            return self.generate_service_token(
                service_id=service_id,
                audience=audience,
                scopes=scopes or old_payload.scope,
                service_type=old_payload.service_type,
                metadata=old_payload.metadata
            )
        
        except AuthenticationException as e:
            raise AuthenticationException(f"Token rotation failed: {str(e)}")
    
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
        try:
            # Decode without verification (not recommended for production)
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            return payload
        
        except Exception as e:
            raise AuthenticationException(f"Failed to decode token claims: {str(e)}")