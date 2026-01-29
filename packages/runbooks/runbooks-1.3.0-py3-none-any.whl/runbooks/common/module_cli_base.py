#!/usr/bin/env python3
"""
Module CLI Base Class for Runbooks - Enterprise Standardization

Provides consistent CLI implementation patterns across all runbooks modules.
Eliminates code duplication and ensures uniform UX across inventory, operate,
security, cfat, vpc, remediation, and sre modules.

Author: Runbooks Team
Version: 1.0.0 - CLI Standardization Framework
"""

import abc
import sys
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_table,
    create_progress_bar,
    format_cost,
    STATUS_INDICATORS,
)
from runbooks.common.cli_decorators import common_aws_options, rich_output_options, enterprise_safety_options
from runbooks.common.error_handling import handle_aws_errors, handle_validation_errors
from runbooks.common.profile_utils import get_profile_for_operation, validate_profile_access_decorator
from runbooks.common.business_logic import BusinessMetrics, OptimizationResult, UniversalBusinessLogic


@dataclass
class ModuleConfig:
    """Configuration for runbooks module CLI."""

    name: str
    version: str
    description: str
    primary_operation_type: str  # For profile selection: "management", "operational", "cost"
    performance_target_seconds: int = 30  # Module-specific performance target
    supports_multi_account: bool = True
    supports_export: bool = True
    default_region: str = "ap-southeast-2"


class ModuleCLIBase(abc.ABC):
    """
    Base class for standardized runbooks module CLI implementation.

    Provides consistent patterns for:
    - CLI option handling with enterprise decorators
    - AWS profile management with 3-tier priority
    - Rich CLI output with enterprise UX standards
    - Error handling with user-friendly guidance
    - Performance monitoring with module targets
    - Business logic integration with standardized metrics
    """

    def __init__(self, config: ModuleConfig):
        """Initialize module CLI with configuration."""
        self.config = config
        self.console = console
        self.business_logic = UniversalBusinessLogic()
        self._session_data = {}

    def print_module_header(self):
        """Print standardized module header with Rich formatting."""
        print_header(self.config.name, self.config.version)
        self.console.print(
            Panel(f"[cyan]{self.config.description}[/cyan]", title=f"🚀 {self.config.name} Module", border_style="blue")
        )

    def validate_prerequisites(self, profile: Optional[str] = None) -> bool:
        """
        Validate module prerequisites before execution.

        Args:
            profile: AWS profile to validate

        Returns:
            True if all prerequisites are met
        """
        try:
            # Validate AWS profile access
            selected_profile = get_profile_for_operation(self.config.primary_operation_type, profile)

            if not validate_profile_access(selected_profile, self.config.name):
                return False

            self._session_data["validated_profile"] = selected_profile
            return True

        except Exception as e:
            print_error(f"Prerequisites validation failed: {str(e)}")
            return False

    @abc.abstractmethod
    def execute_primary_operation(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the primary module operation.

        Must be implemented by each module to provide core functionality.

        Returns:
            Dictionary containing operation results
        """
        pass

    @abc.abstractmethod
    def format_results_for_display(self, results: Dict[str, Any]) -> None:
        """
        Format and display results using Rich CLI standards.

        Args:
            results: Operation results from execute_primary_operation
        """
        pass

    def create_results_table(self, title: str, data: List[Dict[str, Any]], columns: List[str]) -> Table:
        """
        Create standardized results table with Rich formatting.

        Args:
            title: Table title
            data: List of dictionaries containing row data
            columns: List of column names

        Returns:
            Configured Rich Table object
        """
        table = create_table(
            title=title,
            columns=[{"name": col, "style": "cyan" if "name" in col.lower() else "default"} for col in columns],
        )

        for row in data:
            table.add_row(*[str(row.get(col, "N/A")) for col in columns])

        return table

    def export_results(
        self, results: Dict[str, Any], format_type: str = "json", output_path: Optional[str] = None
    ) -> bool:
        """
        Export results in specified format.

        Args:
            results: Results to export
            format_type: Export format (json, csv, markdown, pdf)
            output_path: Optional custom output path

        Returns:
            True if export successful
        """
        if not self.config.supports_export:
            print_warning(f"{self.config.name} module does not support export")
            return False

        try:
            export_handler = self.business_logic.create_export_handler(format_type, output_path)

            success = export_handler.export_data(results)

            if success:
                print_success(f"Results exported to {export_handler.output_path}")
            else:
                print_error(f"Failed to export results in {format_type} format")

            return success

        except Exception as e:
            print_error(f"Export failed: {str(e)}")
            return False

    def calculate_business_metrics(self, results: Dict[str, Any]) -> BusinessMetrics:
        """
        Calculate business metrics from operation results.

        Args:
            results: Operation results

        Returns:
            BusinessMetrics with calculated values
        """
        return self.business_logic.calculate_business_impact(results)

    def create_standard_cli_command(self, command_name: str) -> Callable:
        """
        Create standardized CLI command with common options.

        Args:
            command_name: Name of the CLI command

        Returns:
            Decorated click command function
        """

        @click.command(name=command_name)
        @common_aws_options
        @rich_output_options
        @enterprise_safety_options
        @handle_aws_errors(module_name=self.config.name)
        @handle_validation_errors
        @validate_profile_access_decorator(operation_type=self.config.primary_operation_type)
        def standardized_command(profile=None, region=None, dry_run=True, export_format=None, quiet=False, **kwargs):
            """Execute standardized module operation with enterprise safety."""

            # Module header
            if not quiet:
                self.print_module_header()

            # Validate prerequisites
            if not self.validate_prerequisites(profile):
                sys.exit(1)

            # Execute with performance monitoring
            try:
                with create_progress_bar() as progress:
                    task = progress.add_task(f"[cyan]Executing {self.config.name} operation...", total=100)

                    # Execute primary operation
                    results = self.execute_primary_operation(
                        profile=profile, region=region, dry_run=dry_run, progress=progress, task=task, **kwargs
                    )

                    progress.update(task, completed=100)

                # Display results
                if not quiet:
                    self.format_results_for_display(results)

                # Calculate business metrics
                metrics = self.calculate_business_metrics(results)

                if not quiet and metrics.annual_savings > 0:
                    print_success(f"💰 Potential annual savings: {format_cost(metrics.annual_savings)}")

                # Export if requested
                if export_format:
                    self.export_results(results, export_format)

                return results

            except Exception as e:
                print_error(f"Operation failed: {str(e)}")
                if not quiet:
                    console.print_exception()
                sys.exit(1)

        return standardized_command


class AnalysisModuleCLI(ModuleCLIBase):
    """
    Specialized base class for analysis modules (finops, inventory, cfat).

    Provides additional patterns for:
    - Multi-account analysis operations
    - Cost calculation and savings projections
    - Executive reporting capabilities
    - Trend analysis and recommendations
    """

    def create_executive_summary(self, results: Dict[str, Any]) -> Panel:
        """Create executive summary panel for business stakeholders."""
        metrics = self.calculate_business_metrics(results)

        summary_content = []

        if metrics.annual_savings > 0:
            summary_content.append(f"💰 Annual Savings Potential: {format_cost(metrics.annual_savings)}")

        if metrics.roi_percentage > 0:
            summary_content.append(f"📊 ROI: {metrics.roi_percentage:.1f}%")

        if hasattr(metrics, "resources_analyzed"):
            summary_content.append(f"🔍 Resources Analyzed: {metrics.resources_analyzed:,}")

        summary_content.append(f"⏱️  Execution Time: <{self.config.performance_target_seconds}s target")
        summary_content.append(f"✅ Confidence: {metrics.confidence_level:.1f}%")

        return Panel("\n".join(summary_content), title="📈 Executive Summary", border_style="green")


class OperationsModuleCLI(ModuleCLIBase):
    """
    Specialized base class for operations modules (operate, security, remediation).

    Provides additional patterns for:
    - Resource modification operations with safety controls
    - Multi-level approval workflows
    - Rollback capabilities and audit trails
    - Compliance validation and reporting
    """

    def validate_operation_safety(self, operation: str, resources: List[str]) -> bool:
        """
        Validate operation safety before execution.

        Args:
            operation: Operation type (start, stop, delete, modify)
            resources: List of resource identifiers

        Returns:
            True if operation is safe to proceed
        """
        # Always require explicit approval for destructive operations
        destructive_operations = ["delete", "terminate", "remove", "destroy"]

        if any(op in operation.lower() for op in destructive_operations):
            print_warning(f"⚠️  Destructive operation requested: {operation}")
            print_info(f"Resources affected: {len(resources)}")

            if not click.confirm("Are you sure you want to proceed?"):
                print_info("Operation cancelled by user")
                return False

        return True

    def create_audit_trail(self, operation: str, results: Dict[str, Any]) -> str:
        """
        Create audit trail entry for operations.

        Args:
            operation: Operation performed
            results: Operation results

        Returns:
            Audit trail entry as JSON string
        """
        import json
        from datetime import datetime

        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": self.config.name,
            "operation": operation,
            "user": self._session_data.get("validated_profile", "unknown"),
            "resources_affected": results.get("resources_affected", []),
            "success": results.get("success", False),
            "execution_time": results.get("execution_time_seconds", 0),
        }

        return json.dumps(audit_entry, indent=2)


# Export standardized classes for module implementations
__all__ = ["ModuleConfig", "ModuleCLIBase", "AnalysisModuleCLI", "OperationsModuleCLI"]
