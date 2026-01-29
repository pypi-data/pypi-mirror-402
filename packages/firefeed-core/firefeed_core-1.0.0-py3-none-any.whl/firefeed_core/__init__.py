"""
FireFeed Core - Core utilities and models for FireFeed microservices

This package contains shared components used across all FireFeed microservices:
- Common Pydantic models
- Exceptions and error handling
- API clients for inter-service communication
- Authentication and authorization utilities
- Configuration management
- Interface definitions
"""

from . import models
from . import exceptions
from . import config
from . import auth
from . import api_client
from . import interfaces
from . import utils

# Version
__version__ = "1.0.0"

# Main exports
from .api_client import APIClient
from .auth.token_manager import ServiceTokenManager
from .config.settings import FireFeedSettings
from .exceptions import FireFeedException, APIException, AuthenticationException

__all__ = [
    # Version
    "__version__",
    
    # Core components
    "APIClient",
    "ServiceTokenManager", 
    "FireFeedSettings",
    
    # Exceptions
    "FireFeedException",
    "APIException", 
    "AuthenticationException",
    
    # Submodules
    "models",
    "exceptions",
    "config", 
    "auth",
    "api_client",
    "interfaces",
    "utils",
]