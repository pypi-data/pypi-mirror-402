"""
FireFeed Core API Client

A robust HTTP client for inter-service communication with authentication,
retry policies, circuit breaker pattern, and rate limiting.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError as PydanticValidationError

from ..auth.token_manager import ServiceTokenManager
from ..exceptions.api_exceptions import (
    APIException,
    AuthenticationException,
    AuthorizationException,
    RateLimitException,
    ServiceUnavailableException,
    CircuitBreakerOpenException,
    BadRequestException,
    NotFoundException,
    ConflictException,
)
from .circuit_breaker import CircuitBreaker
from .retry import RetryPolicy
from .rate_limiter import RateLimiter


logger = logging.getLogger(__name__)


class APIClient:
    """
    HTTP client for FireFeed microservices communication.
    
    Features:
    - JWT token authentication
    - Automatic retry with exponential backoff
    - Circuit breaker pattern for fault tolerance
    - Rate limiting to prevent abuse
    - Request/response logging
    - Timeout management
    """
    
    def __init__(
        self,
        base_url: str,
        token: str,
        service_id: str,
        timeout: int = 30,
        max_retries: int = 3,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
        **httpx_kwargs
    ):
        """
        Initialize API Client.
        
        Args:
            base_url: Base URL for the API (e.g., http://firefeed-api:8000)
            token: JWT token for authentication
            service_id: Unique identifier for this service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            circuit_breaker_failure_threshold: Number of failures to open circuit
            circuit_breaker_timeout: Time in seconds before trying again
            rate_limit_requests: Maximum requests per window
            rate_limit_window: Time window in seconds for rate limiting
            **httpx_kwargs: Additional arguments for httpx.AsyncClient
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.service_id = service_id
        self.timeout = timeout
        
        # Initialize components
        self.token_manager = ServiceTokenManager(secret_key="", issuer="")  # Will be set by validator
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_failure_threshold,
            timeout=circuit_breaker_timeout
        )
        self.retry_policy = RetryPolicy(max_retries=max_retries)
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit_requests,
            window_seconds=rate_limit_window
        )
        
        # HTTP client configuration
        self.httpx_kwargs = {
            "timeout": httpx.Timeout(timeout),
            "headers": {
                "User-Agent": f"firefeed-{service_id}/1.0.0",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            **httpx_kwargs
        }
        
        # Create HTTP client
        self.client = httpx.AsyncClient(**self.httpx_kwargs)
        
        logger.info(f"Initialized APIClient for {service_id} -> {base_url}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
        logger.info("APIClient closed")
    
    def _validate_token(self) -> str:
        """
        Validate and refresh token if needed.
        
        Returns:
            Valid JWT token string
            
        Raises:
            AuthenticationException: If token is invalid or expired
        """
        try:
            # For now, assume token is valid if it exists
            # In production, you would validate JWT signature and expiry
            if not self.token:
                raise AuthenticationException("No authentication token provided")
            
            # TODO: Add JWT validation logic here
            # decoded_token = self.token_manager.verify_token(self.token)
            # Check expiry, issuer, etc.
            
            return self.token
            
        except Exception as e:
            raise AuthenticationException(f"Token validation failed: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers including authentication.
        
        Returns:
            Dictionary of headers
        """
        token = self._validate_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Service-ID": self.service_id,
            "X-Request-ID": f"{self.service_id}-{int(time.time() * 1000000)}",
        }
        
        return headers
    
    def _handle_response(self, response: httpx.Response) -> Any:
        """
        Handle HTTP response and convert to appropriate exceptions.
        
        Args:
            response: httpx.Response object
            
        Returns:
            Parsed JSON response data
            
        Raises:
            APIException: For various HTTP error codes
        """
        # Log response
        logger.debug(
            f"Response: {response.status_code} {response.request.url} "
            f"({len(response.content)} bytes)"
        )
        
        try:
            response_data = response.json() if response.content else {}
        except Exception:
            response_data = {"message": response.text}
        
        # Handle HTTP status codes
        if response.status_code == 200:
            return response_data
        
        elif response.status_code == 201:
            return response_data
        
        elif response.status_code == 400:
            error_details = response_data.get("details", [])
            raise BadRequestException(
                message=response_data.get("error", {}).get("message", "Bad request"),
                validation_errors=error_details
            )
        
        elif response.status_code == 401:
            raise AuthenticationException(
                message=response_data.get("error", {}).get("message", "Authentication failed")
            )
        
        elif response.status_code == 403:
            raise AuthorizationException(
                message=response_data.get("error", {}).get("message", "Forbidden")
            )
        
        elif response.status_code == 404:
            raise NotFoundException(
                message=response_data.get("error", {}).get("message", "Not found")
            )
        
        elif response.status_code == 409:
            raise ConflictException(
                message=response_data.get("error", {}).get("message", "Conflict")
            )
        
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitException(
                message=response_data.get("error", {}).get("message", "Rate limit exceeded"),
                retry_after=int(retry_after) if retry_after else None
            )
        
        elif response.status_code >= 500:
            raise ServiceUnavailableException(
                message=response_data.get("error", {}).get("message", "Service unavailable")
            )
        
        else:
            raise APIException(
                message=f"Unexpected response: {response.status_code}",
                status_code=response.status_code,
                response_data=response_data
            )
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Make HTTP request with retry and circuit breaker logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint (will be joined with base_url)
            params: Query parameters
            data: Form data
            json_data: JSON data
            **kwargs: Additional arguments for httpx request
            
        Returns:
            Parsed response data
            
        Raises:
            APIException: For various HTTP and network errors
        """
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        headers = self._get_headers()
        
        # Prepare request arguments
        request_kwargs = {
            "headers": headers,
            "params": params or {},
            **kwargs
        }
        
        if json_data is not None:
            request_kwargs["json"] = json_data
        elif data is not None:
            request_kwargs["data"] = data
        
        # Check rate limiting
        if not self.rate_limiter.allow_request():
            retry_after = self.rate_limiter.get_retry_after()
            raise RateLimitException(
                message="Rate limit exceeded",
                retry_after=retry_after
            )
        
        # Check circuit breaker
        if not self.circuit_breaker.allow_request():
            raise CircuitBreakerOpenException(
                message="Circuit breaker is open"
            )
        
        # Retry logic
        last_exception = None
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                logger.debug(f"Making request: {method} {url} (attempt {attempt + 1})")
                
                response = await self.client.request(method, url, **request_kwargs)
                
                # Record success for circuit breaker
                self.circuit_breaker.record_success()
                
                # Record rate limit usage
                self.rate_limiter.record_request()
                
                return self._handle_response(response)
            
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                last_exception = e
                self.circuit_breaker.record_failure()
                
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.get_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}): {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    break
            
            except APIException as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.status_code < 500:
                    self.circuit_breaker.record_failure()
                    raise
                else:
                    # Retry on server errors (5xx)
                    last_exception = e
                    self.circuit_breaker.record_failure()
                    
                    if attempt < self.retry_policy.max_retries:
                        delay = self.retry_policy.get_delay(attempt)
                        logger.warning(
                            f"Request failed (attempt {attempt + 1}): {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
        
        # All retries failed
        if last_exception:
            raise ServiceUnavailableException(
                f"Request failed after {self.retry_policy.max_retries + 1} attempts: {str(last_exception)}"
            )
    
    # HTTP method wrappers
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Make GET request."""
        return await self._make_request("GET", endpoint, params=params, **kwargs)
    
    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Make POST request."""
        return await self._make_request("POST", endpoint, json_data=json_data, data=data, **kwargs)
    
    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Make PUT request."""
        return await self._make_request("PUT", endpoint, json_data=json_data, data=data, **kwargs)
    
    async def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Make PATCH request."""
        return await self._make_request("PATCH", endpoint, json_data=json_data, data=data, **kwargs)
    
    async def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> Any:
        """Make DELETE request."""
        return await self._make_request("DELETE", endpoint, **kwargs)
    
    # Utility methods
    
    async def health_check(self) -> bool:
        """
        Perform health check against the service.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.get("/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with client statistics
        """
        return {
            "service_id": self.service_id,
            "base_url": self.base_url,
            "circuit_breaker": self.circuit_breaker.get_stats(),
            "rate_limiter": self.rate_limiter.get_stats(),
            "retry_policy": self.retry_policy.get_stats(),
        }