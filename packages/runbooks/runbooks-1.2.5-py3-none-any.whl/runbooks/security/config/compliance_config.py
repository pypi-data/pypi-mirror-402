#!/usr/bin/env python3
"""
Universal Compliance Configuration Management
============================================

This module provides enterprise-grade compliance configuration management
that eliminates hardcoded values and supports dynamic configuration across
all compliance frameworks.

Features:
- Environment variable configuration
- Configuration file support
- Framework-specific defaults
- Universal profile compatibility
- No hardcoded compliance weights or thresholds

Author: DevOps Security Engineer (Claude Code Enterprise Team)
Version: 1.0.0 - Universal Compliance Configuration
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from runbooks.common.rich_utils import console


@dataclass
class ComplianceConfiguration:
    """Universal compliance configuration container."""

    control_weights: Dict[str, float] = field(default_factory=dict)
    framework_thresholds: Dict[str, float] = field(default_factory=dict)
    assessment_frequencies: Dict[str, str] = field(default_factory=dict)
    remediation_priorities: Dict[str, int] = field(default_factory=dict)


class UniversalComplianceConfig:
    """
    Universal compliance configuration manager that works with ANY AWS setup.

    Configuration Priority Order:
    1. Environment variables (highest priority)
    2. Configuration file (COMPLIANCE_CONFIG_PATH)
    3. Framework defaults (fallback)

    No hardcoded values - fully configurable for any enterprise environment.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize universal compliance configuration."""
        self.config_path = config_path or os.getenv("COMPLIANCE_CONFIG_PATH")
        self.config = self._load_configuration()

    def _load_configuration(self) -> ComplianceConfiguration:
        """Load compliance configuration from all sources."""
        config = ComplianceConfiguration()

        # Load from configuration file if available
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    file_config = json.load(f)

                config.control_weights.update(file_config.get("control_weights", {}))
                config.framework_thresholds.update(file_config.get("framework_thresholds", {}))
                config.assessment_frequencies.update(file_config.get("assessment_frequencies", {}))
                config.remediation_priorities.update(file_config.get("remediation_priorities", {}))

                console.log(f"[green]Loaded compliance configuration from: {self.config_path}[/]")

            except Exception as e:
                console.log(f"[yellow]Warning: Failed to load compliance config from {self.config_path}: {e}[/]")

        # Override with environment variables (highest priority)
        self._load_environment_overrides(config)

        return config

    def _load_environment_overrides(self, config: ComplianceConfiguration) -> None:
        """Load configuration overrides from environment variables."""

        # Load control weights from environment
        for env_var in os.environ:
            if env_var.startswith("COMPLIANCE_WEIGHT_"):
                control_id = env_var.replace("COMPLIANCE_WEIGHT_", "").replace("_", "-").lower()
                try:
                    weight = float(os.environ[env_var])
                    config.control_weights[control_id] = weight
                    console.log(f"[dim cyan]Environment override: {control_id} weight = {weight}[/]")
                except ValueError:
                    console.log(f"[yellow]Warning: Invalid weight in {env_var}: {os.environ[env_var]}[/]")

        # Load framework thresholds from environment
        for env_var in os.environ:
            if env_var.startswith("COMPLIANCE_THRESHOLD_"):
                framework = env_var.replace("COMPLIANCE_THRESHOLD_", "").lower().replace("_", "-")
                try:
                    threshold = float(os.environ[env_var])
                    config.framework_thresholds[framework] = threshold
                    console.log(f"[dim cyan]Environment override: {framework} threshold = {threshold}[/]")
                except ValueError:
                    console.log(f"[yellow]Warning: Invalid threshold in {env_var}: {os.environ[env_var]}[/]")

    def get_control_weight(self, control_id: str, framework_default: float = 1.0) -> float:
        """
        Get compliance weight for control with universal fallback.

        Args:
            control_id: Control identifier (e.g., "SEC-1", "CC6.1")
            framework_default: Framework-specific default weight

        Returns:
            float: Compliance weight for the control
        """
        # Normalize control ID for lookup
        normalized_id = control_id.lower().replace(".", "-")

        # Check configuration sources in priority order
        if normalized_id in self.config.control_weights:
            return self.config.control_weights[normalized_id]

        # Use framework default
        return framework_default

    def get_framework_threshold(self, framework: str, default_threshold: float = 90.0) -> float:
        """
        Get compliance threshold for framework with universal fallback.

        Args:
            framework: Framework identifier (e.g., "aws-well-architected", "soc2-type-ii")
            default_threshold: Default threshold if not configured

        Returns:
            float: Compliance threshold for the framework
        """
        # Normalize framework name for lookup
        normalized_framework = framework.lower().replace("_", "-")

        # Check configuration sources in priority order
        if normalized_framework in self.config.framework_thresholds:
            return self.config.framework_thresholds[normalized_framework]

        # Use default threshold
        return default_threshold

    def get_assessment_frequency(self, control_id: str, default_frequency: str = "monthly") -> str:
        """
        Get assessment frequency for control with universal fallback.

        Args:
            control_id: Control identifier
            default_frequency: Default frequency if not configured

        Returns:
            str: Assessment frequency for the control
        """
        normalized_id = control_id.lower().replace(".", "-")

        if normalized_id in self.config.assessment_frequencies:
            return self.config.assessment_frequencies[normalized_id]

        return default_frequency

    def get_remediation_priority(self, control_id: str, default_priority: int = 3) -> int:
        """
        Get remediation priority for control with universal fallback.

        Args:
            control_id: Control identifier
            default_priority: Default priority if not configured (1=highest, 5=lowest)

        Returns:
            int: Remediation priority for the control
        """
        normalized_id = control_id.lower().replace(".", "-")

        if normalized_id in self.config.remediation_priorities:
            return self.config.remediation_priorities[normalized_id]

        return default_priority

    def export_configuration_template(self, output_path: str) -> None:
        """
        Export a configuration template for enterprise customization.

        Args:
            output_path: Path to save the configuration template
        """
        template = {
            "control_weights": {
                "sec-1": 2.0,
                "sec-2": 1.5,
                "cc6-1": 3.0,
                "cc6-2": 2.5,
                "pci-1": 2.0,
                "hipaa-164-312-a-1": 2.5,
            },
            "framework_thresholds": {
                "aws-well-architected": 90.0,
                "soc2-type-ii": 95.0,
                "pci-dss": 100.0,
                "hipaa": 95.0,
                "nist-cybersecurity": 90.0,
                "iso-27001": 85.0,
                "cis-benchmarks": 88.0,
            },
            "assessment_frequencies": {
                "critical-controls": "weekly",
                "high-controls": "monthly",
                "medium-controls": "quarterly",
                "low-controls": "annually",
            },
            "remediation_priorities": {
                "critical-controls": 1,
                "high-controls": 2,
                "medium-controls": 3,
                "low-controls": 4,
            },
        }

        try:
            with open(output_path, "w") as f:
                json.dump(template, f, indent=2)
            console.log(f"[green]Configuration template exported to: {output_path}[/]")
        except Exception as e:
            console.log(f"[red]Failed to export configuration template: {e}[/]")


# Global configuration instance
_universal_config = None


def get_universal_compliance_config() -> UniversalComplianceConfig:
    """Get the global universal compliance configuration instance."""
    global _universal_config
    if _universal_config is None:
        _universal_config = UniversalComplianceConfig()
    return _universal_config


def reset_compliance_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _universal_config
    _universal_config = None


# Export public interface
__all__ = [
    "ComplianceConfiguration",
    "UniversalComplianceConfig",
    "get_universal_compliance_config",
    "reset_compliance_config",
]
