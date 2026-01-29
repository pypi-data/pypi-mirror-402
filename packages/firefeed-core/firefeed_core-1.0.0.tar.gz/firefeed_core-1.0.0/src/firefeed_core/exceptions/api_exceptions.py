"""
API-related exception classes for FireFeed Core

These exceptions are specifically related to HTTP API communication,
authentication, and inter-service communication.
"""

from typing import Optional, Dict, Any
from .base_exceptions import FireFeedException


class APIException(FireFeedException):
    """
    Base exception for all API-related errors.
    
    This includes HTTP status errors, network errors, and API communication issues.
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}
        
        if "details" not in kwargs:
            self.details = {}
        self.details.update({
            "status_code": status_code,
            "response_data": response_data
        })


class AuthenticationException(APIException):
    """
    Raised when authentication fails.
    
    This includes invalid tokens, expired tokens, missing credentials,
    and authentication service unavailability.
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        token_type: Optional[str] = None,
        token_expiry: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, status_code=401, **kwargs)
        self.token_type = token_type
        self.token_expiry = token_expiry
        
        self.details.update({
            "token_type": token_type,
            "token_expiry": token_expiry
        })


class AuthorizationException(APIException):
    """
    Raised when authorization fails.
    
    This includes insufficient permissions, forbidden access,
    and scope validation failures.
    """
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_scopes: Optional[list] = None,
        provided_scopes: Optional[list] = None,
        **kwargs
    ):
        super().__init__(message, status_code=403, **kwargs)
        self.required_scopes = required_scopes or []
        self.provided_scopes = provided_scopes or []
        
        self.details.update({
            "required_scopes": self.required_scopes,
            "provided_scopes": self.provided_scopes
        })


class RateLimitException(APIException):
    """
    Raised when rate limit is exceeded.
    
    This includes HTTP 429 responses and rate limit validation failures.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset_time: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        
        self.details.update({
            "retry_after": retry_after,
            "limit": limit,
            "remaining": remaining,
            "reset_time": reset_time
        })


class ServiceUnavailableException(APIException):
    """
    Raised when a service is unavailable.
    
    This includes HTTP 503 responses, service discovery failures,
    and connection timeouts.
    """
    
    def __init__(
        self,
        message: str = "Service unavailable",
        service_name: Optional[str] = None,
        retry_count: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, status_code=503, **kwargs)
        self.service_name = service_name
        self.retry_count = retry_count
        
        self.details.update({
            "service_name": service_name,
            "retry_count": retry_count
        })


class CircuitBreakerOpenException(ServiceUnavailableException):
    """
    Raised when circuit breaker is open.
    
    This prevents requests from being sent to failing services.
    """
    
    def __init__(
        self,
        message: str = "Circuit breaker is open",
        service_name: Optional[str] = None,
        failure_count: Optional[int] = None,
        last_failure_time: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service_name=service_name, **kwargs)
        self.failure_count = failure_count
        self.last_failure_time = last_failure_time
        
        self.details.update({
            "failure_count": failure_count,
            "last_failure_time": last_failure_time
        })


class BadRequestException(APIException):
    """
    Raised for HTTP 400 Bad Request errors.
    
    This includes validation errors, malformed requests, and invalid parameters.
    """
    
    def __init__(
        self,
        message: str = "Bad request",
        validation_errors: Optional[list] = None,
        **kwargs
    ):
        super().__init__(message, status_code=400, **kwargs)
        self.validation_errors = validation_errors or []
        
        self.details.update({
            "validation_errors": self.validation_errors
        })


class NotFoundException(APIException):
    """
    Raised for HTTP 404 Not Found errors.
    
    This includes missing resources, invalid endpoints, and unknown identifiers.
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, status_code=404, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        self.details.update({
            "resource_type": resource_type,
            "resource_id": resource_id
        })


class ConflictException(APIException):
    """
    Raised for HTTP 409 Conflict errors.
    
    This includes duplicate resources, version conflicts, and state conflicts.
    """
    
    def __init__(
        self,
        message: str = "Resource conflict",
        conflict_type: Optional[str] = None,
        conflicting_resource: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        super().__init__(message, status_code=409, **kwargs)
        self.conflict_type = conflict_type
        self.conflicting_resource = conflicting_resource
        
        self.details.update({
            "conflict_type": conflict_type,
            "conflicting_resource": conflicting_resource
        })