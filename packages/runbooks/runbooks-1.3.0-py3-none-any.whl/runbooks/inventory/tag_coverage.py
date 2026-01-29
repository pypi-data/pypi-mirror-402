#!/usr/bin/env python3
"""
Tag coverage analysis and Rich CLI status display for AWS Organizations.

Provides visual feedback on AWS tag coverage across organization accounts
with tier-based analysis, actionable recommendations, and configurable
tag mapping validation.

Features:
    - Tier-based tag coverage analysis (TIER 1-4)
    - Rich CLI status displays with color-coded indicators
    - Configurable tag mapping validation
    - Multi-tenant portability across Landing Zone configurations
    - Actionable recommendations for tag standardization

Architecture:
    - Hierarchical config precedence: CLI > env > project > user > defaults
    - Zero-coverage detection for misconfigured tag mappings
    - Professional Rich formatting with CloudOps theme

Author: Runbooks Team
Version: 1.1.10
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from runbooks.common.rich_utils import STATUS_INDICATORS, console, print_header

logger = logging.getLogger(__name__)


class TagCoverageAnalyzer:
    """
    Analyze and display tag coverage across AWS accounts.

    Provides comprehensive tag coverage analysis with:
    - Per-field coverage statistics (populated vs total accounts)
    - Tier-level coverage analysis (all fields in tier must be populated)
    - Visual Rich CLI status with color-coded indicators
    - Actionable recommendations for tag standardization

    Coverage Thresholds:
        ≥90% = Excellent (Green ✅)
        80-89% = Good (Yellow ⚠️)
        50-79% = Medium (Orange ⚠️)
        <50% = Poor (Red ❌)

    Tag Tiers:
        TIER 1: Business Metadata (4 critical fields)
        TIER 2: Governance Metadata (4 important fields)
        TIER 3: Operational Metadata (4 standard fields)
        TIER 4: Extended Metadata (5 optional fields)

    Example:
        >>> accounts = [
        ...     {'id': '123456789012', 'wbs_code': 'WBS-001', 'cost_group': 'Engineering'},
        ...     {'id': '234567890123', 'wbs_code': 'N/A', 'cost_group': 'Finance'}
        ... ]
        >>> tag_mappings = {'wbs_code': 'WBS', 'cost_group': 'CostGroup'}
        >>> analyzer = TagCoverageAnalyzer(accounts, tag_mappings, logger)
        >>> analyzer.display_coverage_status()
    """

    # Tag tier definitions (aligned with config_schema.py)
    TIER_1_FIELDS = ["wbs_code", "cost_group", "technical_lead", "account_owner"]
    TIER_2_FIELDS = ["business_unit", "functional_area", "managed_by", "product_owner"]
    TIER_3_FIELDS = ["purpose", "environment", "compliance_scope", "data_classification"]
    TIER_4_FIELDS = ["project_name", "budget_code", "support_tier", "created_date", "expiry_date"]

    # Coverage thresholds
    COVERAGE_EXCELLENT = 90.0  # ≥90% = Green ✅
    COVERAGE_GOOD = 80.0  # 80-89% = Yellow ⚠️
    COVERAGE_MEDIUM = 50.0  # 50-79% = Orange ⚠️
    # <50% = Red ❌

    def __init__(self, accounts: List[Dict[str, Any]], tag_mappings: Dict[str, str], logger: logging.Logger):
        """
        Initialize coverage analyzer.

        Args:
            accounts: List of account dicts with tag data (must include tag-based fields)
            tag_mappings: Field name → AWS tag key mappings (from ConfigLoader)
            logger: Logger instance for diagnostic output

        Example:
            >>> accounts = [{'id': '123', 'wbs_code': 'WBS-001'}]
            >>> mappings = {'wbs_code': 'WBS'}
            >>> analyzer = TagCoverageAnalyzer(accounts, mappings, logger)
        """
        self.accounts = accounts
        self.tag_mappings = tag_mappings
        self.logger = logger
        self.coverage_stats = self._calculate_coverage()

    def _calculate_coverage(self) -> Dict[str, Any]:
        """
        Calculate tag coverage statistics per field.

        Computes:
        1. Per-field coverage: percentage of accounts with populated tags
        2. Tier-level coverage: percentage of accounts with ALL tier fields populated

        Returns:
            Dictionary containing:
            - Per-field stats: {field_name: {populated, total, percentage, tag_key}}
            - Tier stats: {tier_X_overall: {populated, total, percentage}}

        Example:
            >>> analyzer = TagCoverageAnalyzer([{'id': '123', 'wbs_code': 'WBS-001'}],
            ...                                 {'wbs_code': 'WBS'}, logger)
            >>> stats = analyzer._calculate_coverage()
            >>> 'wbs_code' in stats
            True
        """
        total_accounts = len(self.accounts)
        if total_accounts == 0:
            self.logger.warning("No accounts provided for tag coverage analysis")
            return {}

        coverage = {}

        # Calculate per-field coverage
        for field_name in self.tag_mappings.keys():
            populated_count = sum(1 for account in self.accounts if account.get(field_name) not in ["N/A", None, ""])

            coverage_pct = (populated_count / total_accounts) * 100

            coverage[field_name] = {
                "populated": populated_count,
                "total": total_accounts,
                "percentage": coverage_pct,
                "tag_key": self.tag_mappings[field_name],
            }

        # Calculate tier-level coverage (all fields in tier populated)
        coverage["tier_1_overall"] = self._calculate_tier_coverage(self.TIER_1_FIELDS)
        coverage["tier_2_overall"] = self._calculate_tier_coverage(self.TIER_2_FIELDS)

        self.logger.info(
            f"Tag coverage calculated: {total_accounts} accounts, "
            f"TIER 1: {coverage['tier_1_overall']['percentage']:.1f}%, "
            f"TIER 2: {coverage['tier_2_overall']['percentage']:.1f}%"
        )

        return coverage

    def _calculate_tier_coverage(self, tier_fields: List[str]) -> Dict[str, Any]:
        """
        Calculate overall coverage for a tier (all fields populated).

        For an account to have complete tier coverage, ALL fields in that tier
        must be populated (not 'N/A', None, or empty string).

        Args:
            tier_fields: List of field names in this tier

        Returns:
            Dictionary with populated count, total accounts, and percentage

        Example:
            >>> analyzer = TagCoverageAnalyzer(
            ...     [{'wbs_code': 'WBS-001', 'cost_group': 'Eng', 'technical_lead': 'N/A'}],
            ...     {'wbs_code': 'WBS', 'cost_group': 'CostGroup', 'technical_lead': 'TechLead'},
            ...     logger
            ... )
            >>> tier_coverage = analyzer._calculate_tier_coverage(['wbs_code', 'cost_group'])
            >>> tier_coverage['percentage']
            100.0
        """
        total_accounts = len(self.accounts)
        if total_accounts == 0:
            return {"populated": 0, "total": 0, "percentage": 0.0}

        # Count accounts with ALL tier fields populated
        fully_tagged_count = sum(
            1
            for account in self.accounts
            if all(account.get(field) not in ["N/A", None, ""] for field in tier_fields if field in self.tag_mappings)
        )

        coverage_pct = (fully_tagged_count / total_accounts) * 100

        return {"populated": fully_tagged_count, "total": total_accounts, "percentage": coverage_pct}

    def _get_coverage_indicator(self, percentage: float) -> str:
        """
        Get Rich status indicator for coverage percentage.

        Args:
            percentage: Coverage percentage (0-100)

        Returns:
            Status indicator emoji (✅ ⚠️ ❌)

        Example:
            >>> analyzer = TagCoverageAnalyzer([], {}, logger)
            >>> analyzer._get_coverage_indicator(95.0)
            '🟢'
        """
        if percentage >= self.COVERAGE_EXCELLENT:
            return STATUS_INDICATORS["success"]  # ✅
        elif percentage >= self.COVERAGE_GOOD:
            return STATUS_INDICATORS["warning"]  # ⚠️
        elif percentage >= self.COVERAGE_MEDIUM:
            return STATUS_INDICATORS["warning"]  # ⚠️
        else:
            return STATUS_INDICATORS["error"]  # ❌

    def _get_coverage_color(self, percentage: float) -> str:
        """
        Get Rich color for coverage percentage.

        Args:
            percentage: Coverage percentage (0-100)

        Returns:
            Rich color name (green, yellow, orange, red)

        Example:
            >>> analyzer = TagCoverageAnalyzer([], {}, logger)
            >>> analyzer._get_coverage_color(85.0)
            'yellow'
        """
        if percentage >= self.COVERAGE_EXCELLENT:
            return "green"
        elif percentage >= self.COVERAGE_GOOD:
            return "yellow"
        elif percentage >= self.COVERAGE_MEDIUM:
            return "orange"
        else:
            return "red"

    def display_coverage_status(self, config_source: str = "hierarchical config") -> None:
        """
        Display tag coverage status with Rich formatting.

        Creates professional Rich CLI display with:
        - Per-field coverage table (TIER 1 & 2 fields)
        - Color-coded status indicators
        - Overall TIER 1 coverage summary
        - Top 3 actionable recommendations

        Args:
            config_source: Description of configuration source for display

        Example:
            >>> accounts = [{'wbs_code': 'WBS-001', 'cost_group': 'Engineering'}]
            >>> mappings = {'wbs_code': 'WBS', 'cost_group': 'CostGroup'}
            >>> analyzer = TagCoverageAnalyzer(accounts, mappings, logger)
            >>> analyzer.display_coverage_status("user config")
        """
        # Build coverage table
        table = Table(title="Tag Coverage Analysis", box=box.ROUNDED, show_header=True, header_style="bold cyan")

        table.add_column("Field Name", style="white", width=20)
        table.add_column("AWS Tag Key", style="cyan", width=20)
        table.add_column("Coverage", justify="right", style="white", width=15)
        table.add_column("Status", justify="center", width=8)

        # TIER 1: Business Metadata
        table.add_row(Text("TIER 1: Business Metadata", style="bold yellow"), "", "", "", style="bold yellow")
        for field in self.TIER_1_FIELDS:
            if field in self.coverage_stats:
                self._add_coverage_row(table, field)

        # TIER 2: Governance Metadata
        table.add_row("", "", "", "")  # Spacer
        table.add_row(Text("TIER 2: Governance Metadata", style="bold magenta"), "", "", "", style="bold magenta")
        for field in self.TIER_2_FIELDS:
            if field in self.coverage_stats:
                self._add_coverage_row(table, field)

        # Build summary
        tier1_coverage = self.coverage_stats["tier_1_overall"]["percentage"]
        tier1_indicator = self._get_coverage_indicator(tier1_coverage)
        tier1_color = self._get_coverage_color(tier1_coverage)

        summary_text = Text()
        summary_text.append("Configuration Source: ", style="bold white")
        summary_text.append(f"{config_source}\n\n", style="cyan")

        summary_text.append("TIER 1 Overall Coverage: ", style="bold white")
        summary_text.append(f"{tier1_coverage:.1f}% {tier1_indicator}", style=tier1_color)
        summary_text.append(
            f" ({self.coverage_stats['tier_1_overall']['populated']}/"
            f"{self.coverage_stats['tier_1_overall']['total']} accounts)\n",
            style="white",
        )

        # Add recommendations
        recommendations = self._generate_recommendations()
        if recommendations:
            summary_text.append("\n💡 Recommendations:\n", style="bold yellow")
            for rec in recommendations[:3]:  # Top 3
                summary_text.append(f"   • {rec}\n", style="white")

        # Display panel
        panel = Panel(
            table,
            title="[bold cyan]Tag Mapping Status[/bold cyan]",
            subtitle=summary_text,
            border_style="cyan",
            box=box.DOUBLE,
        )

        console.print("\n")
        console.print(panel)
        console.print("\n")

    def _add_coverage_row(self, table: Table, field_name: str) -> None:
        """
        Add coverage row to table.

        Args:
            table: Rich Table instance to add row to
            field_name: Field name to add row for

        Example:
            >>> table = Table()
            >>> analyzer = TagCoverageAnalyzer(
            ...     [{'wbs_code': 'WBS-001'}], {'wbs_code': 'WBS'}, logger
            ... )
            >>> analyzer._add_coverage_row(table, 'wbs_code')
        """
        stats = self.coverage_stats[field_name]
        percentage = stats["percentage"]
        indicator = self._get_coverage_indicator(percentage)
        color = self._get_coverage_color(percentage)

        coverage_text = f"{stats['populated']}/{stats['total']} ({percentage:.1f}%)"

        table.add_row(f"  {field_name}", stats["tag_key"], Text(coverage_text, style=color), indicator)

    def _generate_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on coverage.

        Analyzes coverage gaps and provides specific recommendations for:
        1. Low-coverage critical fields (TIER 1 <80%)
        2. Overall TIER 1 coverage below target
        3. Zero-coverage fields (potential configuration errors)

        Returns:
            List of recommendation strings (ordered by priority)

        Example:
            >>> accounts = [{'wbs_code': 'N/A', 'cost_group': 'N/A'}]
            >>> mappings = {'wbs_code': 'WBS', 'cost_group': 'CostGroup'}
            >>> analyzer = TagCoverageAnalyzer(accounts, mappings, logger)
            >>> recommendations = analyzer._generate_recommendations()
            >>> len(recommendations) > 0
            True
        """
        recommendations = []

        # Check TIER 1 critical fields
        for field in self.TIER_1_FIELDS:
            if field in self.coverage_stats:
                stats = self.coverage_stats[field]
                if stats["percentage"] < self.COVERAGE_GOOD:
                    missing_count = stats["total"] - stats["populated"]
                    recommendations.append(
                        f"Review '{field}' tag configuration - "
                        f"{missing_count} accounts missing '{stats['tag_key']}' tag"
                    )

        # Check overall TIER 1 coverage
        tier1_coverage = self.coverage_stats["tier_1_overall"]["percentage"]
        if tier1_coverage < self.COVERAGE_GOOD:
            recommendations.append(
                f"Overall TIER 1 coverage is {tier1_coverage:.1f}% (target: ≥80%). "
                "Consider standardizing tag naming across AWS accounts."
            )

        # Check for zero coverage (wrong tag mapping?)
        zero_coverage_fields = [
            field
            for field, stats in self.coverage_stats.items()
            if isinstance(stats, dict) and stats.get("percentage", 100) == 0 and field in self.TIER_1_FIELDS
        ]
        if zero_coverage_fields:
            recommendations.append(
                f"Zero coverage for: {', '.join(zero_coverage_fields)}. "
                "Verify tag mapping configuration matches AWS tag keys."
            )

        return recommendations

    def get_coverage_summary(self) -> Dict[str, Any]:
        """
        Get coverage summary for programmatic access.

        Returns:
            Dictionary containing:
            - total_accounts: Number of accounts analyzed
            - tier_1_coverage: TIER 1 overall coverage percentage
            - tier_2_coverage: TIER 2 overall coverage percentage
            - field_coverage: Per-field coverage percentages
            - recommendations: List of actionable recommendations

        Example:
            >>> accounts = [{'wbs_code': 'WBS-001'}]
            >>> mappings = {'wbs_code': 'WBS'}
            >>> analyzer = TagCoverageAnalyzer(accounts, mappings, logger)
            >>> summary = analyzer.get_coverage_summary()
            >>> 'total_accounts' in summary
            True
        """
        return {
            "total_accounts": len(self.accounts),
            "tier_1_coverage": self.coverage_stats["tier_1_overall"]["percentage"],
            "tier_2_coverage": self.coverage_stats["tier_2_overall"]["percentage"],
            "field_coverage": {
                field: stats["percentage"]
                for field, stats in self.coverage_stats.items()
                if isinstance(stats, dict) and "percentage" in stats
            },
            "recommendations": self._generate_recommendations(),
        }


def display_tag_coverage_status(
    accounts: List[Dict[str, Any]],
    tag_mappings: Dict[str, str],
    config_source: str,
    logger: logging.Logger,
) -> None:
    """
    Display tag coverage statistics with Rich formatting (convenience function).

    Creates TagCoverageAnalyzer and displays professional Rich CLI status.
    This is the primary public API for tag coverage display.

    Args:
        accounts: List of account dicts with tag data
        tag_mappings: Field name → AWS tag key mappings
        config_source: Description of config source (e.g., "user config", "CLI overrides")
        logger: Logger instance

    Example:
        >>> accounts = [
        ...     {'id': '123456789012', 'wbs_code': 'WBS-001', 'cost_group': 'Engineering'},
        ...     {'id': '234567890123', 'wbs_code': 'WBS-002', 'cost_group': 'Finance'}
        ... ]
        >>> mappings = {'wbs_code': 'WBS', 'cost_group': 'CostGroup'}
        >>> display_tag_coverage_status(accounts, mappings, "defaults", logger)
    """
    analyzer = TagCoverageAnalyzer(accounts, tag_mappings, logger)
    analyzer.display_coverage_status(config_source)

    # Log coverage summary
    summary = analyzer.get_coverage_summary()
    logger.info(
        f"Tag coverage analysis complete: "
        f"TIER 1: {summary['tier_1_coverage']:.1f}%, "
        f"Total accounts: {summary['total_accounts']}"
    )


# Module exports
__all__ = [
    "TagCoverageAnalyzer",
    "display_tag_coverage_status",
]
