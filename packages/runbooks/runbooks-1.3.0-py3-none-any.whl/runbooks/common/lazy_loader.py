"""
Lazy Loading Architecture for Performance Optimization

This module implements deferred initialization to eliminate startup overhead
for basic CLI operations like --help and --version.

Performance Goals:
- Basic CLI operations < 0.5s
- Defer AWS/MCP initialization until needed
- Clean startup without warning pollution
"""

import threading
from typing import Any, Callable, Optional, Dict
from functools import wraps
import importlib
import sys


class LazyLoader:
    """Thread-safe lazy loader for expensive imports and initializations."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get_or_load(self, key: str, loader_func: Callable[[], Any]) -> Any:
        """Get cached value or load it if not present."""
        if key in self._cache:
            return self._cache[key]

        with self._lock:
            # Double-check pattern
            if key in self._cache:
                return self._cache[key]

            self._cache[key] = loader_func()
            return self._cache[key]


# Global lazy loader instance
_lazy_loader = LazyLoader()


def lazy_aws_session():
    """Lazy load AWS session creation."""

    def _load_aws():
        import boto3
        from runbooks.common.profile_utils import create_management_session

        return create_management_session()

    return _lazy_loader.get_or_load("aws_session", _load_aws)


def lazy_mcp_validator():
    """Lazy load MCP validator."""

    def _load_mcp():
        try:
            from runbooks.finops.mcp_validator import EmbeddedMCPValidator

            return EmbeddedMCPValidator()
        except ImportError:
            return None

    return _lazy_loader.get_or_load("mcp_validator", _load_mcp)


def lazy_rich_console():
    """Lazy load Rich console."""

    def _load_rich():
        try:
            from rich.console import Console

            return Console()
        except ImportError:
            # Fallback console
            class SimpleConsole:
                def print(self, *args, **kwargs):
                    print(*args)

            return SimpleConsole()

    return _lazy_loader.get_or_load("rich_console", _load_rich)


def lazy_performance_monitor():
    """Lazy load performance monitoring."""

    def _load_monitor():
        from runbooks.common.performance_monitor import get_performance_benchmark

        return get_performance_benchmark

    return _lazy_loader.get_or_load("performance_monitor", _load_monitor)


def lazy_pricing_api():
    """Lazy load pricing API without startup warnings."""

    def _load_pricing():
        try:
            from runbooks.common.aws_pricing_api import PricingAPI

            return PricingAPI()
        except Exception:
            # Return fallback pricing without warnings during basic operations
            class FallbackPricing:
                def get_nat_gateway_price(self, region="ap-southeast-2"):
                    return 32.4  # Standard fallback rate

            return FallbackPricing()

    return _lazy_loader.get_or_load("pricing_api", _load_pricing)


def lazy_inventory_collector():
    """Lazy load inventory collector."""

    def _load_collector():
        from runbooks.inventory.core.collector import InventoryCollector

        return InventoryCollector

    return _lazy_loader.get_or_load("inventory_collector", _load_collector)


def lazy_import(module_name: str, attribute: Optional[str] = None):
    """Lazy import a module or module attribute."""
    cache_key = f"{module_name}.{attribute}" if attribute else module_name

    def _load_module():
        module = importlib.import_module(module_name)
        if attribute:
            return getattr(module, attribute)
        return module

    return _lazy_loader.get_or_load(cache_key, _load_module)


def requires_aws(func):
    """Decorator to ensure AWS session is loaded before function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        lazy_aws_session()  # Ensure AWS is loaded
        return func(*args, **kwargs)

    return wrapper


def requires_mcp(func):
    """Decorator to ensure MCP validator is loaded before function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        lazy_mcp_validator()  # Ensure MCP is loaded
        return func(*args, **kwargs)

    return wrapper


def fast_startup_mode() -> bool:
    """Check if we're in fast startup mode (basic operations only)."""
    import sys

    # Basic operations that should be fast
    fast_operations = {"--help", "-h", "--version", "-V", "help"}

    # Check if any CLI args match fast operations
    return any(arg in fast_operations for arg in sys.argv)


def clear_lazy_cache():
    """Clear the lazy loading cache (useful for testing)."""
    global _lazy_loader
    _lazy_loader._cache.clear()


# Utility functions for deferred initialization
def defer_expensive_imports():
    """
    Replace expensive imports with lazy alternatives.
    Call this early in main.py to optimize startup.
    """
    # Only defer if we're not in fast startup mode
    if fast_startup_mode():
        return

    # Defer expensive imports for basic operations
    modules_to_defer = [
        "runbooks.finops.mcp_validator",
        "runbooks.common.aws_pricing_api",
        "runbooks.inventory.core.collector",
        "runbooks.cfat.runner",
    ]

    for module in modules_to_defer:
        if module in sys.modules:
            # Replace with lazy loader
            sys.modules[module] = lazy_import(module)
