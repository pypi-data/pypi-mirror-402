"""Plugin registry for integrations."""

from typing import Callable
import logging

_REGISTRY: dict[str, type] = {}

logger = logging.getLogger(__name__)


def register_integration(name: str) -> Callable:
    """Decorator to register an integration plugin.

    This decorator adds the decorated class to the global integration registry,
    allowing it to be instantiated by name via `get_integration()`.

    Args:
        name: Unique identifier for the integration (e.g., "pagerduty", "servicenow")

    Returns:
        Decorator function that registers the class

    Example:
        >>> @register_integration("my-integration")
        >>> class MyIntegration(IntegrationBase):
        >>>     ...
    """

    def decorator(cls: type) -> type:
        """Register the class."""
        _REGISTRY[name] = cls
        logger.debug(f"Registered integration: {name} -> {cls.__name__}")
        return cls

    return decorator


def get_integration(name: str) -> type | None:
    """Get a registered integration class by name.

    Args:
        name: Integration name to look up

    Returns:
        Integration class if found, None otherwise

    Example:
        >>> cls = get_integration("pagerduty")
        >>> if cls:
        >>>     integration = cls(config)
    """
    return _REGISTRY.get(name)


def list_integrations() -> list[str]:
    """List all registered integration names.

    Useful for discovery (e.g., showing available integrations in a CLI).
    The list is sorted to ensure deterministic output.

    Returns:
        List of registered integration names (sorted)
    """
    return list(_REGISTRY.keys())


def clear_registry() -> None:
    """Clear all registered integrations.

    WARNING: This removes all integrations from the internal registry.
    Primarily used for testing isolation to ensure a clean state between tests.
    """
    _REGISTRY.clear()
