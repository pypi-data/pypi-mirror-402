# di_container.py - Dependency Injection Container for FireFeed Core
import logging
from typing import Dict, Any, Type, TypeVar, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """Simple Dependency Injection Container for Core Services"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}

    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> None:
        """Register a service implementation"""
        if singleton:
            self._services[interface] = implementation
        else:
            self._factories[interface] = implementation

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance"""
        self._singletons[interface] = instance

    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """Register a factory function"""
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance"""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check services
        if interface in self._services:
            impl_class = self._services[interface]
            instance = self._instantiate(impl_class)
            self._singletons[interface] = instance  # Cache as singleton
            return instance

        # Check factories
        if interface in self._factories:
            factory = self._factories[interface]
            return factory()

        raise ValueError(f"No registration found for {interface}")

    def _instantiate(self, cls: Type[T]) -> T:
        """Instantiate a class with dependency injection"""
        import inspect

        # Get constructor parameters
        init_signature = inspect.signature(cls.__init__)
        params = {}

        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue

            # Skip *args and **kwargs parameters
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Try to resolve parameter type
            if param.annotation != inspect.Parameter.empty:
                try:
                    params[param_name] = self.resolve(param.annotation)
                except ValueError:
                    # If can't resolve, try to get default value
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        raise ValueError(f"Cannot resolve parameter {param_name} for {cls}")
            elif param.default != inspect.Parameter.empty:
                params[param_name] = param.default
            else:
                raise ValueError(f"Cannot resolve parameter {param_name} for {cls}")

        # If no parameters needed, just instantiate
        if not params:
            return cls()

        return cls(**params)

    def clear(self) -> None:
        """Clear all registrations and instances"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()


# Global DI container instance
di_container = DIContainer()


def get_service(interface: Type[T]) -> T:
    """Get a service instance from the global DI container"""
    return di_container.resolve(interface)


def resolve(interface: Type[T]) -> T:
    """Resolve a service instance from the global DI container"""
    return di_container.resolve(interface)