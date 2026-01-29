"""
Runbooks - Enterprise AWS Automation & Cloud Foundations Toolkit (OPTIMIZED)

PERFORMANCE OPTIMIZATIONS:
- Removed automatic finops import (line 118) which triggered MCP loading
- Lazy loading for enterprise components
- Version-only import for basic CLI operations

This should reduce startup time from 5.6s to <0.5s for basic operations.
"""

# Centralized Version Management - Single Source of Truth
# This file is optimized variant - must sync with main __init__.py
__version__ = "1.1.9"

# Fallback for legacy importlib.metadata usage during transition
try:
    from importlib.metadata import version as _pkg_version

    _metadata_version = _pkg_version("runbooks")
    if _metadata_version != __version__:
        import warnings

        warnings.warn(
            f"Version mismatch detected: pyproject.toml has {_metadata_version}, "
            f"but centralized version is {__version__}. Please sync pyproject.toml.",
            UserWarning,
        )
except Exception:
    # Expected during development or when package metadata is unavailable
    pass


# Core module exports (lazy loading)
def _lazy_config():
    """Lazy load config modules."""
    from runbooks.config import RunbooksConfig, load_config, save_config

    return RunbooksConfig, load_config, save_config


def _lazy_utils():
    """Lazy load utility modules."""
    from runbooks.utils import ensure_directory, setup_logging, validate_aws_profile

    return ensure_directory, setup_logging, validate_aws_profile


# Enterprise module exports with graceful degradation (lazy loading)
def _lazy_enterprise():
    """Lazy load enterprise components only when needed."""
    try:
        # Assessment and Discovery
        from runbooks.cfat.runner import AssessmentRunner
        from runbooks.inventory.collectors.aws_management import OrganizationsManager
        from runbooks.inventory.core.collector import InventoryCollector
        from runbooks.operate.cloudformation_operations import CloudFormationOperations
        from runbooks.operate.cloudwatch_operations import CloudWatchOperations
        from runbooks.operate.dynamodb_operations import DynamoDBOperations

        # Operations and Automation
        from runbooks.operate.ec2_operations import EC2Operations
        from runbooks.operate.iam_operations import IAMOperations
        from runbooks.operate.s3_operations import S3Operations
        from runbooks.security.security_baseline_tester import SecurityBaselineTester

        return {
            "AssessmentRunner": AssessmentRunner,
            "InventoryCollector": InventoryCollector,
            "OrganizationsManager": OrganizationsManager,
            "SecurityBaselineTester": SecurityBaselineTester,
            "EC2Operations": EC2Operations,
            "S3Operations": S3Operations,
            "DynamoDBOperations": DynamoDBOperations,
            "CloudFormationOperations": CloudFormationOperations,
            "IAMOperations": IAMOperations,
            "CloudWatchOperations": CloudWatchOperations,
        }
    except ImportError:
        return {}


# FinOps exports (LAZY LOADING TO FIX STARTUP PERFORMANCE)
def _lazy_finops():
    """Lazy load FinOps modules only when needed."""
    try:
        from runbooks.finops import get_cost_data, get_trend, run_dashboard

        return get_cost_data, get_trend, run_dashboard
    except ImportError:
        return None, None, None


# Expose lazy loaders for core functionality
def get_config():
    """Get config utilities (lazy loaded)."""
    return _lazy_config()


def get_utils():
    """Get utility functions (lazy loaded)."""
    return _lazy_utils()


def get_enterprise():
    """Get enterprise components (lazy loaded)."""
    return _lazy_enterprise()


def get_finops():
    """Get FinOps functions (lazy loaded)."""
    return _lazy_finops()


# Minimal exports for fast startup
__all__ = [
    "__version__",
    "get_config",
    "get_utils",
    "get_enterprise",
    "get_finops",
]

# Only expose the lazy loaders by default
# The actual functions are loaded on-demand
