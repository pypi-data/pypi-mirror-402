"""
Permissions for FireFeed Core

Provides permission checking utilities for service authorization.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Permission:
    """Permission definition."""
    resource: str
    action: str
    description: str = ""
    
    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Permission):
            return self.resource == other.resource and self.action == other.action
        return False
    
    def __hash__(self) -> int:
        return hash((self.resource, self.action))


class PermissionChecker:
    """
    Permission checker for service authorization.
    
    Provides utilities for checking permissions and scopes.
    """
    
    # Common permissions
    RSS_READ = Permission("rss", "read", "Read RSS data")
    RSS_WRITE = Permission("rss", "write", "Write RSS data")
    RSS_ADMIN = Permission("rss", "admin", "Admin RSS operations")
    
    USERS_READ = Permission("users", "read", "Read user data")
    USERS_WRITE = Permission("users", "write", "Write user data")
    USERS_ADMIN = Permission("users", "admin", "Admin user operations")
    
    CATEGORIES_READ = Permission("categories", "read", "Read categories")
    CATEGORIES_WRITE = Permission("categories", "write", "Write categories")
    
    TRANSLATION_READ = Permission("translation", "read", "Read translation data")
    TRANSLATION_WRITE = Permission("translation", "write", "Write translation data")
    
    SYSTEM_READ = Permission("system", "read", "Read system status")
    SYSTEM_WRITE = Permission("system", "write", "Write system configuration")
    
    ADMIN_ALL = Permission("admin", "all", "Full administrative access")
    
    # Permission groups
    RSS_OPERATIONS = [RSS_READ, RSS_WRITE]
    USER_OPERATIONS = [USERS_READ, USERS_WRITE]
    CATEGORY_OPERATIONS = [CATEGORIES_READ, CATEGORIES_WRITE]
    TRANSLATION_OPERATIONS = [TRANSLATION_READ, TRANSLATION_WRITE]
    SYSTEM_OPERATIONS = [SYSTEM_READ, SYSTEM_WRITE]
    
    @classmethod
    def get_all_permissions(cls) -> List[Permission]:
        """Get all available permissions."""
        return [
            cls.RSS_READ, cls.RSS_WRITE, cls.RSS_ADMIN,
            cls.USERS_READ, cls.USERS_WRITE, cls.USERS_ADMIN,
            cls.CATEGORIES_READ, cls.CATEGORIES_WRITE,
            cls.TRANSLATION_READ, cls.TRANSLATION_WRITE,
            cls.SYSTEM_READ, cls.SYSTEM_WRITE,
            cls.ADMIN_ALL
        ]
    
    @classmethod
    def get_permission_by_scope(cls, scope: str) -> Optional[Permission]:
        """Get permission object by scope string."""
        scope_to_permission = {
            "rss:read": cls.RSS_READ,
            "rss:write": cls.RSS_WRITE,
            "rss:admin": cls.RSS_ADMIN,
            "users:read": cls.USERS_READ,
            "users:write": cls.USERS_WRITE,
            "users:admin": cls.USERS_ADMIN,
            "categories:read": cls.CATEGORIES_READ,
            "categories:write": cls.CATEGORIES_WRITE,
            "translation:read": cls.TRANSLATION_READ,
            "translation:write": cls.TRANSLATION_WRITE,
            "system:read": cls.SYSTEM_READ,
            "system:write": cls.SYSTEM_WRITE,
            "admin:all": cls.ADMIN_ALL,
        }
        return scope_to_permission.get(scope)
    
    @classmethod
    def has_permission(cls, scopes: List[str], permission: Permission) -> bool:
        """
        Check if scopes contain the required permission.
        
        Args:
            scopes: List of scope strings
            permission: Required permission
            
        Returns:
            True if permission is granted, False otherwise
        """
        # Check for admin permission
        if "admin:all" in scopes:
            return True
        
        # Check for specific permission
        required_scope = str(permission)
        return required_scope in scopes
    
    @classmethod
    def has_any_permission(cls, scopes: List[str], permissions: List[Permission]) -> bool:
        """
        Check if scopes contain any of the required permissions.
        
        Args:
            scopes: List of scope strings
            permissions: List of required permissions
            
        Returns:
            True if any permission is granted, False otherwise
        """
        # Check for admin permission
        if "admin:all" in scopes:
            return True
        
        # Check for any specific permission
        required_scopes = [str(p) for p in permissions]
        return any(scope in scopes for scope in required_scopes)
    
    @classmethod
    def has_all_permissions(cls, scopes: List[str], permissions: List[Permission]) -> bool:
        """
        Check if scopes contain all required permissions.
        
        Args:
            scopes: List of scope strings
            permissions: List of required permissions
            
        Returns:
            True if all permissions are granted, False otherwise
        """
        # Check for admin permission
        if "admin:all" in scopes:
            return True
        
        # Check for all specific permissions
        required_scopes = [str(p) for p in permissions]
        return all(scope in scopes for scope in required_scopes)
    
    @classmethod
    def get_missing_permissions(cls, scopes: List[str], permissions: List[Permission]) -> List[Permission]:
        """
        Get list of missing permissions.
        
        Args:
            scopes: List of scope strings
            permissions: List of required permissions
            
        Returns:
            List of missing permissions
        """
        # Check for admin permission
        if "admin:all" in scopes:
            return []
        
        # Find missing permissions
        required_scopes = [str(p) for p in permissions]
        missing_scopes = [scope for scope in required_scopes if scope not in scopes]
        
        return [cls.get_permission_by_scope(scope) for scope in missing_scopes if scope]
    
    @classmethod
    def validate_scopes(cls, scopes: List[str]) -> Dict[str, Any]:
        """
        Validate and analyze scopes.
        
        Args:
            scopes: List of scope strings
            
        Returns:
            Dictionary with validation results
        """
        valid_scopes = []
        invalid_scopes = []
        permissions = []
        
        for scope in scopes:
            permission = cls.get_permission_by_scope(scope)
            if permission:
                valid_scopes.append(scope)
                permissions.append(permission)
            else:
                invalid_scopes.append(scope)
        
        return {
            "valid_scopes": valid_scopes,
            "invalid_scopes": invalid_scopes,
            "permissions": permissions,
            "has_admin": "admin:all" in scopes,
            "scope_count": len(valid_scopes)
        }
    
    @classmethod
    def get_service_permissions(cls, service_type: str) -> List[Permission]:
        """
        Get default permissions for a service type.
        
        Args:
            service_type: Type of service (rss-parser, telegram-bot, etc.)
            
        Returns:
            List of default permissions for the service
        """
        service_permissions = {
            "rss-parser": cls.RSS_OPERATIONS + [cls.CATEGORIES_READ],
            "telegram-bot": cls.USER_OPERATIONS + cls.RSS_OPERATIONS,
            "api": cls.RSS_OPERATIONS + cls.USER_OPERATIONS + cls.CATEGORIES_READ + cls.SYSTEM_READ,
            "translation": cls.TRANSLATION_OPERATIONS,
        }
        
        return service_permissions.get(service_type, [])
    
    @classmethod
    def can_access_resource(cls, scopes: List[str], resource: str, action: str) -> bool:
        """
        Check if scopes allow access to a specific resource and action.
        
        Args:
            scopes: List of scope strings
            resource: Resource name
            action: Action name
            
        Returns:
            True if access is allowed, False otherwise
        """
        permission = Permission(resource, action)
        return cls.has_permission(scopes, permission)