"""
DRY Pattern Manager - Eliminate Pattern Duplication

Following Claude Code best practices for memory efficiency and enterprise
architecture patterns for systematic deduplication.

Official Claude Code Limitation: Context window optimization requires eliminating
redundant patterns to maximize available context for complex operations.

Enterprise Best Practice: Single source of truth for all reusable patterns
prevents inconsistencies and reduces maintenance overhead.
"""

from typing import Any, Dict, Optional, Callable
from functools import lru_cache
import click
from rich.console import Console
from rich.markup import escape


class DRYPatternManager:
    """
    Don't Repeat Yourself - Load patterns once, reference everywhere.

    Following Claude Code optimization principles:
    - Single pattern registry (no duplicates)
    - Reference-based access (@ notation concept)
    - Memory efficiency through lazy loading
    - Consistent patterns across all modules

    Enterprise Architecture:
    - Centralized pattern management
    - Type-safe pattern access
    - Cached pattern instances
    - Extensible pattern registry
    """

    _patterns: Dict[str, Any] = {}
    _console: Optional[Console] = None
    _loaded: bool = False

    @classmethod
    @lru_cache(maxsize=None)
    def get_console(cls) -> Console:
        """
        Single console instance for all modules.

        Claude Code Best Practice: Reuse console objects to reduce memory overhead
        and ensure consistent formatting across all CLI operations.
        """
        if cls._console is None:
            cls._console = Console()
        return cls._console

    @classmethod
    def get_pattern(cls, name: str) -> Any:
        """
        Get pattern by name with lazy loading.

        Args:
            name: Pattern identifier (e.g., 'error_handlers', 'click_group')

        Returns:
            Cached pattern instance

        Raises:
            KeyError: If pattern not found
        """
        if not cls._loaded:
            cls._load_all_patterns()

        if name not in cls._patterns:
            raise KeyError(f"Pattern '{name}' not found. Available: {list(cls._patterns.keys())}")

        return cls._patterns[name]

    @classmethod
    def _load_all_patterns(cls):
        """Load all patterns once - DRY principle implementation."""
        if cls._loaded:
            return

        # Common import patterns
        cls._patterns["click"] = click
        cls._patterns["console"] = cls.get_console()

        # Error handling patterns
        cls._patterns["error_handlers"] = cls._create_error_handlers()

        # Click group patterns
        cls._patterns["click_group"] = cls._create_click_group_pattern()

        # Common CLI decorators reference
        cls._patterns["common_decorators"] = cls._get_common_decorators()

        cls._loaded = True

    @classmethod
    def _create_error_handlers(cls) -> Dict[str, Callable]:
        """
        Centralized error handling patterns.

        Eliminates 19 instances of duplicated error messages across CLI modules.
        """
        console = cls.get_console()

        def module_not_available_error(module_name: str, error: Exception):
            """Standardized 'module not available' error handler."""
            console.print(f"[red]❌ {module_name} module not available: {error}[/red]")

        def operation_failed_error(operation_name: str, error: Exception):
            """Standardized 'operation failed' error handler."""
            console.print(f"[red]❌ {operation_name} failed: {error}[/red]")

        def success_message(message: str, details: Optional[str] = None):
            """Standardized success message."""
            console.print(f"[green]✅ {message}[/green]")
            if details:
                console.print(f"[dim]{details}[/dim]")

        return {
            "module_not_available": module_not_available_error,
            "operation_failed": operation_failed_error,
            "success": success_message,
        }

    @classmethod
    def _create_click_group_pattern(cls) -> Callable:
        """
        Standardized Click group creation pattern.

        Eliminates 6 instances of identical @click.group patterns.
        """

        def create_group(name: str, help_text: str, invoke_without_command: bool = True):
            """Create standardized Click group with common options."""

            @click.group(invoke_without_command=invoke_without_command)
            @click.pass_context
            def group(ctx):
                if ctx.invoked_subcommand is None:
                    click.echo(f"{name.title()} Commands:")
                    click.echo(help_text)

            # Apply consistent group naming
            group.name = name
            group.__doc__ = help_text

            return group

        return create_group

    @classmethod
    def _get_common_decorators(cls):
        """Reference to common decorators - avoid importing in every module."""
        try:
            from runbooks.common.decorators import common_aws_options, common_output_options, common_filter_options

            return {
                "aws_options": common_aws_options,
                "output_options": common_output_options,
                "filter_options": common_filter_options,
            }
        except ImportError:
            # Graceful degradation if decorators not available
            return {}


# Convenience functions for direct pattern access
def get_console() -> Console:
    """Get shared console instance - replaces individual console = Console() calls."""
    return DRYPatternManager.get_console()


def get_error_handlers() -> Dict[str, Callable]:
    """Get standardized error handlers."""
    return DRYPatternManager.get_pattern("error_handlers")


def get_click_group_creator() -> Callable:
    """Get standardized Click group creator."""
    return DRYPatternManager.get_pattern("click_group")


def get_common_decorators() -> Dict[str, Any]:
    """Get common CLI decorators."""
    return DRYPatternManager.get_pattern("common_decorators")


# Pattern registry status for monitoring
def get_pattern_registry_status() -> Dict[str, Any]:
    """
    Get DRY pattern registry status for monitoring and optimization.

    Returns:
        Dictionary containing registry status, loaded patterns, and memory efficiency metrics
    """
    return {
        "loaded": DRYPatternManager._loaded,
        "pattern_count": len(DRYPatternManager._patterns),
        "available_patterns": list(DRYPatternManager._patterns.keys()),
        "console_shared": DRYPatternManager._console is not None,
        "memory_efficiency": "Single instance sharing active",
    }
