"""
Base exception classes for FireFeed Core

These are the fundamental exception types that all other FireFeed exceptions inherit from.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class FireFeedException(Exception):
    """
    Base exception for all FireFeed-related errors.
    
    This is the parent class for all FireFeed-specific exceptions.
    Provides consistent error handling across all microservices.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "type": self.__class__.__name__,
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None
            }
        }
    
    def __str__(self) -> str:
        base_message = f"{self.error_code}: {self.message}"
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base_message} (details: {details_str})"
        return base_message


class ConfigurationException(FireFeedException):
    """
    Raised when there's an error in service configuration.
    
    This includes missing environment variables, invalid configuration values,
    or configuration file parsing errors.
    """
    pass


class ValidationException(FireFeedException):
    """
    Raised when data validation fails.
    
    This includes input validation, schema validation, and business rule validation.
    """
    pass


class NotFoundException(FireFeedException):
    """
    Raised when a requested resource is not found.
    
    This is used for consistent 404 responses across all APIs.
    """
    
    def __init__(
        self, 
        resource_type: str, 
        resource_id: str,
        message: Optional[str] = None
    ):
        if not message:
            message = f"{resource_type} with id '{resource_id}' not found"
        
        super().__init__(
            message=message,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class ConflictException(FireFeedException):
    """
    Raised when there's a conflict with the current state of a resource.
    
    This includes duplicate entries, version conflicts, or state validation errors.
    """
    pass


class TimeoutException(FireFeedException):
    """
    Raised when an operation exceeds its timeout.
    
    This includes database timeouts, API timeouts, and external service timeouts.
    """
    pass


class CircuitBreakerException(FireFeedException):
    """
    Raised when a circuit breaker is open and requests are being blocked.
    
    This prevents cascading failures in distributed systems.
    """
    pass


class ServiceException(FireFeedException):
    """
    Raised when a service operation fails.
    
    This is used for service-level errors that don't fit into other categories.
    """
    pass


class DatabaseException(FireFeedException):
    """
    Raised when a database operation fails.
    
    This includes connection errors, query failures, transaction errors,
    and other database-related issues that may occur during service operations.
    """
    pass