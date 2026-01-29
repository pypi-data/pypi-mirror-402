"""
OutputController - Centralized UX Control Framework

Enterprise-grade output management for Runbooks with 3-line compact defaults.

Design Pattern:
- Default: 3-line compact output (production UX)
- --verbose: Extended debug output (development)
- --format: compact/table/json
- Rich library integration
- Profile name truncation
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)


class OutputController:
    """
    Centralized output controller for consistent UX across all runbooks modules.

    Features:
    - 3-line compact output by default (production UX)
    - Extended debug output with --verbose flag
    - Multiple output formats (compact/table/json)
    - Profile name truncation for readability
    - Integration with Rich library and logging

    Usage:
        controller = OutputController(verbose=False, format="compact")
        controller.print_operation_summary(
            emoji="🔍",
            operation="EC2 Organizations Enrichment",
            input_count=146,
            enriched_count=67,
            enrichment_type="AWS accounts",
            success_percentage=100.0,
            profile="ams-admin-ReadOnly-909189038205",
            output_file="data/outputs/ec2-org.csv",
            added_columns=["AccountName", "AccountEmail", "OrgUnit", ...]
        )
    """

    def __init__(self, verbose: bool = False, format: str = "compact", console: Optional[Console] = None):
        """
        Initialize OutputController.

        Args:
            verbose: Enable verbose debug output
            format: Output format (compact/table/json)
            console: Rich Console instance (creates new if None)
        """
        self.verbose = verbose
        self.format = format
        self.console = console or Console()

        logger.debug(f"OutputController initialized: verbose={verbose}, format={format}")

    def truncate_profile(self, profile: str, max_length: int = 50) -> str:
        """
        Truncate long profile names for readability.

        Args:
            profile: AWS profile name
            max_length: Maximum length before truncation

        Returns:
            Truncated profile name with ellipsis

        Examples:
            "ams-admin-ReadOnly-909189038205" → "ams-admin-ReadOnly-9091..."
            "short-profile" → "short-profile"
            None → "default"
        """
        # Handle None profile
        if profile is None:
            return "default"

        if len(profile) <= max_length:
            return profile

        return profile[: max_length - 3] + "..."

    def format_added_columns(self, columns: Optional[List[str]]) -> str:
        """
        Format added columns list for compact display.

        Args:
            columns: List of column names added during enrichment

        Returns:
            Formatted string like "+10 columns" or "+3 columns: Col1, Col2, Col3"

        Examples:
            ["Col1", "Col2", "Col3"] → "+3 columns"
            None → ""
        """
        if not columns:
            return ""

        count = len(columns)
        if self.verbose and count <= 5:
            # Show column names in verbose mode for small lists
            return f"+{count} columns: {', '.join(columns)}"
        else:
            return f"+{count} columns"

    def print_operation_summary(
        self,
        emoji: str,
        operation: str,
        input_count: int,
        enriched_count: int,
        enrichment_type: str,
        success_percentage: float,
        profile: str,
        output_file: str,
        added_columns: Optional[List[str]] = None,
    ) -> None:
        """
        Print 3-line operation summary (compact) or extended output (verbose).

        Args:
            emoji: Operation emoji (🔍, 💰, ⚡, etc.)
            operation: Operation description
            input_count: Number of input resources
            enriched_count: Number of successfully enriched resources
            enrichment_type: Type of enrichment (e.g., "AWS accounts", "cost data")
            success_percentage: Percentage of successful enrichment
            profile: AWS profile name
            output_file: Output file path
            added_columns: List of columns added during enrichment

        Output (compact):
            🔍 Operation: 146 resources → 67 AWS accounts (100% enriched)
            ├─ Profile: ams-admin-ReadOnly-9091...
            └─ Output: data/outputs/ec2-org.csv (+10 columns)

        Output (verbose):
            [Extended table with all details]
        """
        logger.debug(
            f"Operation summary: {operation} | "
            f"{input_count} → {enriched_count} {enrichment_type} | "
            f"{success_percentage}% success | profile={profile}"
        )

        if self.format == "json":
            self._print_json_summary(
                operation=operation,
                input_count=input_count,
                enriched_count=enriched_count,
                enrichment_type=enrichment_type,
                success_percentage=success_percentage,
                profile=profile,
                output_file=output_file,
                added_columns=added_columns,
            )
        elif self.format == "table" or self.verbose:
            self._print_table_summary(
                emoji=emoji,
                operation=operation,
                input_count=input_count,
                enriched_count=enriched_count,
                enrichment_type=enrichment_type,
                success_percentage=success_percentage,
                profile=profile,
                output_file=output_file,
                added_columns=added_columns,
            )
        else:
            # Default: 3-line compact output
            self._print_compact_summary(
                emoji=emoji,
                operation=operation,
                input_count=input_count,
                enriched_count=enriched_count,
                enrichment_type=enrichment_type,
                success_percentage=success_percentage,
                profile=profile,
                output_file=output_file,
                added_columns=added_columns,
            )

    def _print_compact_summary(
        self,
        emoji: str,
        operation: str,
        input_count: int,
        enriched_count: int,
        enrichment_type: str,
        success_percentage: float,
        profile: str,
        output_file: str,
        added_columns: Optional[List[str]] = None,
    ) -> None:
        """Print 3-line compact operation summary."""
        truncated_profile = self.truncate_profile(profile)
        columns_info = self.format_added_columns(added_columns)

        # Line 1: Operation summary
        self.console.print(
            f"{emoji} {operation}: {input_count} resources → "
            f"{enriched_count} {enrichment_type} "
            f"({success_percentage:.1f}% enriched)"
        )

        # Line 2: Profile
        self.console.print(f"├─ Profile: {truncated_profile}")

        # Line 3: Output file
        output_display = f"{output_file}"
        if columns_info:
            output_display += f" ({columns_info})"
        self.console.print(f"└─ Output: {output_display}")

    def _print_table_summary(
        self,
        emoji: str,
        operation: str,
        input_count: int,
        enriched_count: int,
        enrichment_type: str,
        success_percentage: float,
        profile: str,
        output_file: str,
        added_columns: Optional[List[str]] = None,
    ) -> None:
        """Print extended table summary for verbose mode."""
        table = Table(title=f"{emoji} {operation}")

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Input Resources", str(input_count))
        table.add_row("Enriched Count", str(enriched_count))
        table.add_row("Enrichment Type", enrichment_type)
        table.add_row("Success Rate", f"{success_percentage:.1f}%")
        table.add_row("AWS Profile", profile)
        table.add_row("Output File", output_file)

        if added_columns:
            table.add_row("Added Columns", f"{len(added_columns)}: {', '.join(added_columns)}")

        self.console.print(table)

    def _print_json_summary(
        self,
        operation: str,
        input_count: int,
        enriched_count: int,
        enrichment_type: str,
        success_percentage: float,
        profile: str,
        output_file: str,
        added_columns: Optional[List[str]] = None,
    ) -> None:
        """Print JSON summary for programmatic consumption."""
        import json

        summary = {
            "operation": operation,
            "input_count": input_count,
            "enriched_count": enriched_count,
            "enrichment_type": enrichment_type,
            "success_percentage": success_percentage,
            "profile": profile,
            "output_file": output_file,
            "added_columns": added_columns or [],
        }

        self.console.print(json.dumps(summary, indent=2))
