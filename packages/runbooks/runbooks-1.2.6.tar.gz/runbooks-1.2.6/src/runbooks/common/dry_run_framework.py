#!/usr/bin/env python3
"""
Universal --dry-run Safety Framework for Runbooks

This module provides a comprehensive, enterprise-grade dry-run framework that ensures
safety-first operations across all runbooks modules. It implements consistent behavior,
logging, and safety controls for all operation types.

Strategic Alignment:
- "Move Fast, But Not So Fast We Crash" - Safety-first with explicit confirmation
- Enterprise safety controls with comprehensive audit trails
- Consistent UX across all 7 core modules

Author: Runbooks Team
Version: 1.0.0 - Enterprise Safety Framework
"""

import functools
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_warning,
    print_error,
    STATUS_INDICATORS,
)


class OperationType(Enum):
    """Classification of operation types for appropriate dry-run behavior."""

    # READ-ONLY Operations (inherently safe)
    DISCOVERY = "discovery"  # inventory collect, scan
    ANALYSIS = "analysis"  # finops dashboard, security assess, vpc analyze
    ASSESSMENT = "assessment"  # cfat assess
    REPORTING = "reporting"  # generate reports, export data

    # STATE-CHANGING Operations (require safety controls)
    RESOURCE_CREATE = "create"  # EC2 instances, S3 buckets, VPCs
    RESOURCE_MODIFY = "modify"  # Update configurations, scaling
    RESOURCE_DELETE = "delete"  # Terminate, delete resources
    CONFIGURATION = "config"  # Change settings, policies
    REMEDIATION = "remediation"  # Security fixes, compliance actions

    # HIGH-RISK Operations (explicit confirmation required)
    BULK_OPERATIONS = "bulk"  # Multi-resource operations
    CROSS_ACCOUNT = "cross_account"  # Operations affecting multiple accounts
    FINANCIAL = "financial"  # Budget modifications, billing changes


@dataclass
class DryRunContext:
    """Context information for dry-run operations."""

    enabled: bool
    operation_type: OperationType
    module_name: str
    operation_name: str
    target_resources: List[str]
    estimated_impact: Optional[str] = None
    safety_level: str = "standard"  # standard, high, critical
    requires_confirmation: bool = False
    audit_trail: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []


class DryRunSafetyFramework:
    """
    Universal dry-run safety framework for enterprise operations.

    Provides consistent dry-run behavior, safety controls, and audit trails
    across all runbooks modules.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)

        # Safety configuration
        self.safety_configs = {
            OperationType.DISCOVERY: {
                "default_dry_run": False,  # Discovery is inherently safe
                "requires_confirmation": False,
                "simulation_mode": True,  # Can simulate API calls
                "warning_message": None,
            },
            OperationType.ANALYSIS: {
                "default_dry_run": False,  # Analysis is read-only
                "requires_confirmation": False,
                "simulation_mode": False,  # Real API calls for analysis
                "warning_message": None,
            },
            OperationType.ASSESSMENT: {
                "default_dry_run": False,  # Assessment is read-only
                "requires_confirmation": False,
                "simulation_mode": False,
                "warning_message": None,
            },
            OperationType.REPORTING: {
                "default_dry_run": False,  # Reporting is read-only
                "requires_confirmation": False,
                "simulation_mode": False,  # Real API calls for report generation
                "warning_message": None,
            },
            OperationType.RESOURCE_CREATE: {
                "default_dry_run": True,  # Safety-first for resource creation
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "⚠️  RESOURCE CREATION: This will create new AWS resources and incur costs",
            },
            OperationType.RESOURCE_MODIFY: {
                "default_dry_run": True,  # Safety-first for modifications
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "⚠️  RESOURCE MODIFICATION: This will modify existing AWS resources",
            },
            OperationType.RESOURCE_DELETE: {
                "default_dry_run": True,  # Safety-first for deletion
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "🚨 RESOURCE DELETION: This will permanently delete AWS resources",
            },
            OperationType.CONFIGURATION: {
                "default_dry_run": True,  # Safety-first for configuration changes
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "⚙️  CONFIGURATION CHANGE: This will modify settings and policies",
            },
            OperationType.REMEDIATION: {
                "default_dry_run": True,  # Safety-first for remediation
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "🔧 SECURITY REMEDIATION: This will apply security fixes to resources",
            },
            OperationType.BULK_OPERATIONS: {
                "default_dry_run": True,  # Safety-first for bulk operations
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "🔥 BULK OPERATION: This will affect multiple resources simultaneously",
            },
            OperationType.CROSS_ACCOUNT: {
                "default_dry_run": True,  # Safety-first for cross-account
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "🌐 CROSS-ACCOUNT OPERATION: This will affect multiple AWS accounts",
            },
            OperationType.FINANCIAL: {
                "default_dry_run": True,  # Safety-first for financial operations
                "requires_confirmation": True,
                "simulation_mode": True,
                "warning_message": "💰 FINANCIAL OPERATION: This will modify budgets or billing configurations",
            },
        }

    def create_context(
        self,
        dry_run: bool,
        operation_type: OperationType,
        module_name: str,
        operation_name: str,
        target_resources: Optional[List[str]] = None,
        estimated_impact: Optional[str] = None,
    ) -> DryRunContext:
        """
        Create a dry-run context for an operation.

        Args:
            dry_run: User-specified dry-run flag
            operation_type: Type of operation being performed
            module_name: Name of the module (finops, security, etc.)
            operation_name: Specific operation name
            target_resources: List of resources that will be affected
            estimated_impact: Human-readable impact description

        Returns:
            DryRunContext with appropriate safety settings
        """
        config = self.safety_configs.get(operation_type, self.safety_configs[OperationType.RESOURCE_MODIFY])

        # Determine actual dry-run state
        if dry_run is None:
            actual_dry_run = config["default_dry_run"]
        else:
            actual_dry_run = dry_run

        # Determine safety level
        safety_level = "standard"
        if operation_type in [OperationType.RESOURCE_DELETE, OperationType.BULK_OPERATIONS]:
            safety_level = "high"
        elif operation_type in [OperationType.CROSS_ACCOUNT, OperationType.FINANCIAL]:
            safety_level = "critical"

        context = DryRunContext(
            enabled=actual_dry_run,
            operation_type=operation_type,
            module_name=module_name,
            operation_name=operation_name,
            target_resources=target_resources or [],
            estimated_impact=estimated_impact,
            safety_level=safety_level,
            requires_confirmation=config["requires_confirmation"] and not actual_dry_run,
        )

        # Log context creation
        self._add_audit_entry(
            context,
            "context_created",
            {
                "dry_run_enabled": actual_dry_run,
                "safety_level": safety_level,
                "requires_confirmation": context.requires_confirmation,
            },
        )

        return context

    def display_dry_run_banner(self, context: DryRunContext) -> None:
        """
        Display appropriate dry-run banner based on operation type.

        Args:
            context: Dry-run context with operation details
        """
        if context.enabled:
            # Dry-run mode banner
            title = f"{STATUS_INDICATORS['info']} DRY-RUN MODE ENABLED"

            if context.operation_type in [OperationType.DISCOVERY, OperationType.ANALYSIS, OperationType.ASSESSMENT]:
                message = f"[cyan]Simulation mode: No AWS API calls will be made[/cyan]\n"
                message += f"[dim]Operation: {context.module_name} {context.operation_name}[/dim]"
            else:
                message = f"[yellow]Preview mode: No resources will be modified[/yellow]\n"
                message += f"[dim]Operation: {context.module_name} {context.operation_name}[/dim]\n"
                if context.target_resources:
                    message += f"[dim]Target resources: {len(context.target_resources)} items[/dim]"

            panel = Panel(message, title=title, border_style="cyan", title_align="left")

        else:
            # Live mode banner with warnings
            config = self.safety_configs.get(context.operation_type)
            if config and config.get("warning_message"):
                title = f"{STATUS_INDICATORS['warning']} LIVE MODE - CHANGES WILL BE APPLIED"

                message = f"[red]{config['warning_message']}[/red]\n"
                message += f"[dim]Operation: {context.module_name} {context.operation_name}[/dim]"
                if context.estimated_impact:
                    message += f"\n[yellow]Estimated impact: {context.estimated_impact}[/yellow]"

                panel = Panel(message, title=title, border_style="red", title_align="left")
            else:
                # Standard live mode for read-only operations
                title = f"{STATUS_INDICATORS['success']} LIVE MODE - REAL DATA ANALYSIS"
                message = f"[green]Real AWS API calls will be made for analysis[/green]\n"
                message += f"[dim]Operation: {context.module_name} {context.operation_name}[/dim]"

                panel = Panel(message, title=title, border_style="green", title_align="left")

        self.console.print(panel)
        self.console.print()  # Add spacing

    def confirm_operation(self, context: DryRunContext) -> bool:
        """
        Request confirmation for operations that require it.

        Args:
            context: Dry-run context

        Returns:
            True if user confirms, False otherwise
        """
        if not context.requires_confirmation:
            return True

        # Show operation details
        table = Table(title="Operation Confirmation Required")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Module", context.module_name)
        table.add_row("Operation", context.operation_name)
        table.add_row("Safety Level", context.safety_level.upper())

        if context.target_resources:
            table.add_row("Resources Affected", str(len(context.target_resources)))

        if context.estimated_impact:
            table.add_row("Estimated Impact", context.estimated_impact)

        self.console.print(table)
        self.console.print()

        # Request confirmation
        try:
            import click

            confirmed = click.confirm(
                f"Are you sure you want to proceed with this {context.operation_type.value} operation?", default=False
            )
        except ImportError:
            # Fallback for environments without click
            response = input(
                f"Are you sure you want to proceed with this {context.operation_type.value} operation? [y/N]: "
            )
            confirmed = response.lower().startswith("y")

        # Log confirmation
        self._add_audit_entry(
            context, "confirmation_requested", {"user_confirmed": confirmed, "safety_level": context.safety_level}
        )

        if not confirmed:
            print_warning("Operation cancelled by user")

        return confirmed

    def log_operation_start(self, context: DryRunContext, details: Optional[Dict[str, Any]] = None) -> None:
        """Log the start of an operation with full context."""
        mode = "DRY-RUN" if context.enabled else "LIVE"

        log_entry = {
            "mode": mode,
            "operation_type": context.operation_type.value,
            "operation_module": context.module_name,
            "operation": context.operation_name,
            "target_count": len(context.target_resources),
            "safety_level": context.safety_level,
        }

        if details:
            log_entry.update(details)

        self._add_audit_entry(context, "operation_started", log_entry)

        # Console output
        status = STATUS_INDICATORS.get("running", "🔄")
        self.console.print(f"{status} Starting {mode} operation: {context.operation_name}")

    def log_operation_complete(
        self,
        context: DryRunContext,
        success: bool = True,
        results: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log the completion of an operation."""
        mode = "DRY-RUN" if context.enabled else "LIVE"

        log_entry = {
            "mode": mode,
            "success": success,
            "duration": self._calculate_duration(context),
        }

        if results:
            log_entry["results"] = results

        if error:
            log_entry["error"] = error

        self._add_audit_entry(context, "operation_completed", log_entry)

        # Console output
        if success:
            status = STATUS_INDICATORS.get("success", "✅")
            print_success(f"Operation completed successfully in {mode} mode")

            if context.enabled and context.operation_type not in [
                OperationType.DISCOVERY,
                OperationType.ANALYSIS,
                OperationType.ASSESSMENT,
            ]:
                self.console.print(f"[dim]💡 To execute changes, run the same command with --no-dry-run[/dim]")
        else:
            status = STATUS_INDICATORS.get("error", "❌")
            print_error(f"Operation failed in {mode} mode: {error}")

    def _add_audit_entry(self, context: DryRunContext, event: str, data: Dict[str, Any]) -> None:
        """Add an entry to the audit trail."""
        entry = {"timestamp": datetime.utcnow().isoformat(), "event": event, "data": data}
        context.audit_trail.append(entry)

        # Log to system logger
        self.logger.info(
            f"DryRun {event}",
            extra={
                "operation_module": context.module_name,
                "operation": context.operation_name,
                "dry_run": context.enabled,
                **data,
            },
        )

    def _calculate_duration(self, context: DryRunContext) -> Optional[str]:
        """Calculate operation duration from audit trail."""
        start_time = None
        end_time = datetime.utcnow()

        for entry in context.audit_trail:
            if entry["event"] == "operation_started":
                start_time = datetime.fromisoformat(entry["timestamp"])
                break

        if start_time:
            duration = end_time - start_time
            return f"{duration.total_seconds():.2f}s"

        return None


def dry_run_operation(
    operation_type: OperationType, requires_confirmation: Optional[bool] = None, estimated_impact: Optional[str] = None
):
    """
    Decorator for operations that support dry-run mode.

    Args:
        operation_type: Type of operation for appropriate safety controls
        requires_confirmation: Override default confirmation requirement
        estimated_impact: Description of operation impact

    Usage:
        @dry_run_operation(OperationType.RESOURCE_DELETE, estimated_impact="Delete 5 VPCs")
        def delete_vpcs(dry_run: bool = True, **kwargs):
            # Function receives dry_run_context as first argument
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract dry_run parameter
            dry_run = kwargs.pop("dry_run", None)

            # Get module and operation names
            module_name = (
                getattr(func, "__module__", "unknown").split(".")[-2]
                if "." in getattr(func, "__module__", "")
                else "unknown"
            )
            operation_name = func.__name__

            # Create dry-run framework instance
            framework = DryRunSafetyFramework()

            # Create context
            context = framework.create_context(
                dry_run=dry_run,
                operation_type=operation_type,
                module_name=module_name,
                operation_name=operation_name,
                estimated_impact=estimated_impact,
            )

            # Override confirmation requirement if specified
            if requires_confirmation is not None:
                context.requires_confirmation = requires_confirmation and not context.enabled

            # Display banner
            framework.display_dry_run_banner(context)

            # Request confirmation if required
            if not framework.confirm_operation(context):
                return None

            # Log operation start
            framework.log_operation_start(context)

            try:
                # Call the original function with context as first argument
                result = func(context, *args, **kwargs)

                # Log success
                framework.log_operation_complete(context, success=True, results={"completed": True})

                return result

            except Exception as e:
                # Log failure
                framework.log_operation_complete(context, success=False, error=str(e))
                raise

        return wrapper

    return decorator


# Convenience functions for common operation types
def discovery_operation(func: Callable) -> Callable:
    """Decorator for discovery operations (inventory, scan)."""
    return dry_run_operation(OperationType.DISCOVERY)(func)


def analysis_operation(func: Callable) -> Callable:
    """Decorator for analysis operations (finops, security assess, vpc analyze)."""
    return dry_run_operation(OperationType.ANALYSIS)(func)


def assessment_operation(func: Callable) -> Callable:
    """Decorator for assessment operations (cfat assess)."""
    return dry_run_operation(OperationType.ASSESSMENT)(func)


def resource_creation_operation(estimated_impact: str = None):
    """Decorator for resource creation operations."""
    return dry_run_operation(OperationType.RESOURCE_CREATE, estimated_impact=estimated_impact)


def resource_deletion_operation(estimated_impact: str = None):
    """Decorator for resource deletion operations."""
    return dry_run_operation(OperationType.RESOURCE_DELETE, estimated_impact=estimated_impact)


def remediation_operation(estimated_impact: str = None):
    """Decorator for security remediation operations."""
    return dry_run_operation(OperationType.REMEDIATION, estimated_impact=estimated_impact)


# Global framework instance for direct use
framework = DryRunSafetyFramework()
