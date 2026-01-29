"""
FinOps Configuration Management - API-Only Display Parameters

This module manages display and formatting parameters that have been removed from
the CLI interface to simplify enterprise usage, while maintaining full programmatic
access through the API.

MANAGER FEEDBACK INTEGRATION:
- "consider to depreciated configuration - in runbook APIs only, to simplify the CLI configurations"
- CLI focused on business value parameters only
- Full functionality preserved through API access
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DisplayConfiguration:
    """
    API-only display configuration parameters.

    These parameters were moved from CLI to API-only access to simplify
    enterprise CLI usage while maintaining full programmatic control.
    """

    # Profile display configuration (removed from CLI)
    profile_display_length: Optional[int] = None

    # Service name display configuration (removed from CLI)
    service_name_length: Optional[int] = None

    # Text summary configuration (removed from CLI)
    max_services_text: Optional[int] = None

    # Business cost thresholds (internalized with smart defaults)
    high_cost_threshold: float = 5000.0
    medium_cost_threshold: float = 1000.0

    @classmethod
    def get_default_config(cls) -> "DisplayConfiguration":
        """
        Get default configuration with smart business-appropriate defaults.

        Smart Defaults Strategy:
        - Profile Display: Auto-truncate based on terminal width
        - Service Names: Business-appropriate length limits
        - Text Summaries: Optimal service count for readability
        - Cost Thresholds: Industry-standard business thresholds
        """
        return cls(
            profile_display_length=50,  # Reasonable display length for terminals
            service_name_length=25,  # Business-friendly service name truncation
            max_services_text=10,  # Optimal readability for service summaries
            high_cost_threshold=5000.0,  # Industry standard high-cost threshold
            medium_cost_threshold=1000.0,  # Industry standard medium-cost threshold
        )

    @classmethod
    def from_environment(cls) -> "DisplayConfiguration":
        """
        Load configuration from environment variables for API access.

        Environment Variables:
        - FINOPS_PROFILE_DISPLAY_LENGTH: Max profile name display length
        - FINOPS_SERVICE_NAME_LENGTH: Max service name display length
        - FINOPS_MAX_SERVICES_TEXT: Max services in text summaries
        - FINOPS_HIGH_COST_THRESHOLD: High cost threshold for highlighting
        - FINOPS_MEDIUM_COST_THRESHOLD: Medium cost threshold for highlighting
        """
        return cls(
            profile_display_length=cls._get_int_env("FINOPS_PROFILE_DISPLAY_LENGTH"),
            service_name_length=cls._get_int_env("FINOPS_SERVICE_NAME_LENGTH"),
            max_services_text=cls._get_int_env("FINOPS_MAX_SERVICES_TEXT"),
            high_cost_threshold=cls._get_float_env("FINOPS_HIGH_COST_THRESHOLD", 5000.0),
            medium_cost_threshold=cls._get_float_env("FINOPS_MEDIUM_COST_THRESHOLD", 1000.0),
        )

    @staticmethod
    def _get_int_env(key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        return int(value) if value and value.isdigit() else default

    @staticmethod
    def _get_float_env(key: str, default: float) -> float:
        """Get float value from environment variable."""
        value = os.getenv(key)
        try:
            return float(value) if value else default
        except ValueError:
            return default

    def apply_smart_defaults(self, terminal_width: Optional[int] = None) -> "DisplayConfiguration":
        """
        Apply smart defaults based on terminal capabilities.

        Args:
            terminal_width: Terminal width for adaptive profile display

        Returns:
            Configuration with smart defaults applied
        """
        config = DisplayConfiguration(
            profile_display_length=self.profile_display_length,
            service_name_length=self.service_name_length,
            max_services_text=self.max_services_text,
            high_cost_threshold=self.high_cost_threshold,
            medium_cost_threshold=self.medium_cost_threshold,
        )

        # Smart profile display length based on terminal width
        if config.profile_display_length is None:
            if terminal_width and terminal_width > 120:
                config.profile_display_length = 60  # Wide terminal
            elif terminal_width and terminal_width > 80:
                config.profile_display_length = 40  # Standard terminal
            else:
                config.profile_display_length = 25  # Narrow terminal

        # Smart service name length for business readability
        if config.service_name_length is None:
            config.service_name_length = 25  # Business-appropriate length

        # Smart services count for optimal readability
        if config.max_services_text is None:
            config.max_services_text = 10  # Optimal for executive summaries

        return config


class FinOpsConfigManager:
    """
    FinOps Configuration Manager for API-only parameters.

    Provides centralized management of display parameters that were removed
    from CLI to maintain enterprise simplicity while preserving full API access.
    """

    def __init__(self, config: Optional[DisplayConfiguration] = None):
        """
        Initialize configuration manager.

        Args:
            config: Custom display configuration (defaults to smart defaults)
        """
        self._config = config or DisplayConfiguration.get_default_config()

    @property
    def config(self) -> DisplayConfiguration:
        """Get current display configuration."""
        return self._config

    def update_config(self, **kwargs) -> None:
        """
        Update configuration parameters programmatically.

        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

    def get_profile_display_length(self) -> int:
        """Get profile display length with smart default."""
        return self._config.profile_display_length or 50

    def get_service_name_length(self) -> int:
        """Get service name length with smart default."""
        return self._config.service_name_length or 25

    def get_max_services_text(self) -> int:
        """Get max services in text with smart default."""
        return self._config.max_services_text or 10

    def get_high_cost_threshold(self) -> float:
        """Get high cost threshold."""
        return self._config.high_cost_threshold

    def get_medium_cost_threshold(self) -> float:
        """Get medium cost threshold."""
        return self._config.medium_cost_threshold

    def is_high_cost(self, amount: float) -> bool:
        """Check if amount exceeds high cost threshold."""
        return amount > self._config.high_cost_threshold

    def is_medium_cost(self, amount: float) -> bool:
        """Check if amount exceeds medium cost threshold."""
        return amount > self._config.medium_cost_threshold

    def get_cost_category(self, amount: float) -> str:
        """Get cost category based on thresholds."""
        if self.is_high_cost(amount):
            return "Cost Review Required"
        elif self.is_medium_cost(amount):
            return "Right-sizing Review"
        else:
            return "Monitor & Optimize"


# Global configuration instance for backwards compatibility
_global_config = FinOpsConfigManager()


def get_global_config() -> FinOpsConfigManager:
    """Get global configuration manager instance."""
    return _global_config


def set_global_config(config: DisplayConfiguration) -> None:
    """Set global configuration."""
    global _global_config
    _global_config = FinOpsConfigManager(config)


# Backwards compatibility functions for existing code
def get_profile_display_length(args=None) -> int:
    """
    Get profile display length with backwards compatibility.

    DEPRECATION WARNING: This function is deprecated. Use FinOpsConfigManager.get_profile_display_length() instead.
    """
    if args and hasattr(args, "profile_display_length") and args.profile_display_length:
        return args.profile_display_length
    return _global_config.get_profile_display_length()


def get_service_name_length(args=None) -> int:
    """
    Get service name length with backwards compatibility.

    DEPRECATION WARNING: This function is deprecated. Use FinOpsConfigManager.get_service_name_length() instead.
    """
    if args and hasattr(args, "service_name_length") and args.service_name_length:
        return args.service_name_length
    return _global_config.get_service_name_length()


def get_max_services_text(args=None) -> int:
    """
    Get max services text with backwards compatibility.

    DEPRECATION WARNING: This function is deprecated. Use FinOpsConfigManager.get_max_services_text() instead.
    """
    if args and hasattr(args, "max_services_text") and args.max_services_text:
        return args.max_services_text
    return _global_config.get_max_services_text()


def get_high_cost_threshold(args=None) -> float:
    """
    Get high cost threshold with backwards compatibility.

    DEPRECATION WARNING: This function is deprecated. Use FinOpsConfigManager.get_high_cost_threshold() instead.
    """
    if args and hasattr(args, "high_cost_threshold") and args.high_cost_threshold:
        return args.high_cost_threshold
    return _global_config.get_high_cost_threshold()


def get_medium_cost_threshold(args=None) -> float:
    """
    Get medium cost threshold with backwards compatibility.

    DEPRECATION WARNING: This function is deprecated. Use FinOpsConfigManager.get_medium_cost_threshold() instead.
    """
    if args and hasattr(args, "medium_cost_threshold") and args.medium_cost_threshold:
        return args.medium_cost_threshold
    return _global_config.get_medium_cost_threshold()
