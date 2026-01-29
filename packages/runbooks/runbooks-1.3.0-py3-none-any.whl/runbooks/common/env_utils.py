"""
Environment Variable Utilities - Enterprise Hardcoded Value Elimination

This module provides enterprise-compliant environment variable utilities
that enforce zero hardcoded defaults policy across the entire codebase.
"""

import os
from typing import Union


def get_required_env(var_name: str) -> str:
    """
    Get required string environment variable - NO hardcoded defaults.

    Args:
        var_name: Environment variable name

    Returns:
        Environment variable value

    Raises:
        ValueError: If environment variable is not set
    """
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} required - no hardcoded defaults allowed")
    return value


def get_required_env_int(var_name: str) -> int:
    """
    Get required integer environment variable - NO hardcoded defaults.

    Args:
        var_name: Environment variable name

    Returns:
        Environment variable value as integer

    Raises:
        ValueError: If environment variable is not set or not a valid integer
    """
    value = get_required_env(var_name)
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"Environment variable {var_name} must be a valid integer, got: {value}") from e


def get_required_env_float(var_name: str) -> float:
    """
    Get required float environment variable - NO hardcoded defaults.

    Args:
        var_name: Environment variable name

    Returns:
        Environment variable value as float

    Raises:
        ValueError: If environment variable is not set or not a valid float
    """
    value = get_required_env(var_name)
    try:
        return float(value)
    except ValueError as e:
        raise ValueError(f"Environment variable {var_name} must be a valid float, got: {value}") from e


def get_required_env_bool(var_name: str) -> bool:
    """
    Get required boolean environment variable - NO hardcoded defaults.

    Args:
        var_name: Environment variable name

    Returns:
        Environment variable value as boolean

    Raises:
        ValueError: If environment variable is not set
    """
    value = get_required_env(var_name).lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    else:
        raise ValueError(f"Environment variable {var_name} must be a valid boolean (true/false), got: {value}")


# Legacy compatibility function names for existing code
_get_required_env_float = get_required_env_float
_get_required_env_int = get_required_env_int
_get_required_env = get_required_env
