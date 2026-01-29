"""
Runbooks - Modular CLI Framework

KISS Principle: Simple, focused command modules for enterprise CLI architecture.
DRY Principle: Single source of truth for command registration and common utilities.

This modular CLI framework reduces main.py from 9,259 lines to ~200 lines while
preserving 100% functionality through intelligent command organization.
"""

from .registry import DRYCommandRegistry

__all__ = ["DRYCommandRegistry"]
