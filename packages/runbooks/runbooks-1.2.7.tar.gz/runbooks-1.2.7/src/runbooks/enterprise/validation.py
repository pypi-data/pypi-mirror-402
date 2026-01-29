"""
Enterprise Validation Module - Enhanced Logging and Validation

This module provides enterprise-grade logging and validation capabilities
for the Runbooks framework.

Features:
- Enhanced structured logging with performance monitoring
- Cross-module validation utilities
- Rich CLI integration with enterprise UX standards
- Enterprise compliance validation
"""

import logging
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.logging import RichHandler

# Rich console for enterprise logging
console = Console()


class EnhancedLogging:
    """Enhanced logging capabilities for enterprise operations."""

    def __init__(self, module_name: str = "runbooks"):
        self.module_name = module_name
        self.logger = self._setup_enhanced_logger()

    def _setup_enhanced_logger(self) -> logging.Logger:
        """Setup enhanced logger with Rich integration."""
        logger = logging.getLogger(f"runbooks.{self.module_name}")

        # Skip if already configured
        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)

        # Rich handler for beautiful console output
        rich_handler = RichHandler(console=console, show_time=True, show_path=True, rich_tracebacks=True)

        formatter = logging.Formatter(fmt="[%(name)s] %(message)s", datefmt="[%X]")
        rich_handler.setFormatter(formatter)

        logger.addHandler(rich_handler)
        logger.propagate = False

        return logger

    def info(self, message: str, **kwargs) -> None:
        """Log info message with Rich formatting."""
        self.logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with Rich formatting."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message with Rich formatting."""
        self.logger.error(message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with Rich formatting."""
        self.logger.debug(message, **kwargs)


class ConfigValidator:
    """Configuration validation utilities."""

    @staticmethod
    def validate_aws_profile(profile: str) -> bool:
        """Validate AWS profile configuration."""
        if not profile or not isinstance(profile, str):
            return False
        return len(profile.strip()) > 0

    @staticmethod
    def validate_region(region: str) -> bool:
        """Validate AWS region format."""
        if not region or not isinstance(region, str):
            return False
        # Basic AWS region format validation
        return len(region.split("-")) >= 3


class InputValidator:
    """Input validation utilities."""

    @staticmethod
    def validate_account_id(account_id: str) -> bool:
        """Validate AWS account ID format."""
        if not account_id or not isinstance(account_id, str):
            return False
        return account_id.isdigit() and len(account_id) == 12

    @staticmethod
    def validate_instance_id(instance_id: str) -> bool:
        """Validate EC2 instance ID format."""
        if not instance_id or not isinstance(instance_id, str):
            return False
        return instance_id.startswith("i-") and len(instance_id) >= 10


class TypeValidator:
    """Type validation utilities."""

    @staticmethod
    def validate_list_of_strings(value: Any) -> bool:
        """Validate that value is a list of strings."""
        if not isinstance(value, list):
            return False
        return all(isinstance(item, str) for item in value)

    @staticmethod
    def validate_dict(value: Any, required_keys: Optional[List[str]] = None) -> bool:
        """Validate dictionary structure."""
        if not isinstance(value, dict):
            return False

        if required_keys:
            return all(key in value for key in required_keys)

        return True


def validate_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration dictionary."""
    validator = ConfigValidator()
    errors = []

    # Validate profile if present
    if "profile" in config:
        if not validator.validate_aws_profile(config["profile"]):
            errors.append("Invalid AWS profile configuration")

    # Validate region if present
    if "region" in config:
        if not validator.validate_region(config["region"]):
            errors.append("Invalid AWS region format")

    return {"valid": len(errors) == 0, "errors": errors}


def validate_user_input(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user input data."""
    validator = InputValidator()
    errors = []

    # Validate account ID if present
    if "account_id" in user_input:
        if not validator.validate_account_id(user_input["account_id"]):
            errors.append("Invalid AWS account ID format")

    # Validate instance ID if present
    if "instance_id" in user_input:
        if not validator.validate_instance_id(user_input["instance_id"]):
            errors.append("Invalid EC2 instance ID format")

    return {"valid": len(errors) == 0, "errors": errors}


# Create default enhanced logger
enhanced_logger = EnhancedLogging("enterprise")
