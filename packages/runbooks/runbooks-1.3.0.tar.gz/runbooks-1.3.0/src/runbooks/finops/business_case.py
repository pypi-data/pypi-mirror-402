#!/usr/bin/env python3
"""
FinOps Business Case ROI Module

Comprehensive ROI calculation and executive summary generation for cost optimization.
Extracted from dashboard_runner.py for KISS/DRY/LEAN architecture.

Key Features:
- Enterprise-standard ROI percentage calculation
- Payback period analysis
- Break-even point determination
- Conservative confidence scoring
- Executive summary generation

Author: Runbooks Team
Version: 1.0.0
"""

from typing import Any, Dict, Optional

from rich.console import Console

from runbooks.common.rich_utils import console as default_console


# Enterprise CloudOps hourly rate constant
ENTERPRISE_HOURLY_RATE = 150  # USD per hour (enterprise contractor rate)


def calculate_roi_metrics(
    annual_savings: float,
    implementation_hours: float = 8,
) -> Dict[str, Any]:
    """
    Calculate comprehensive ROI metrics for business case analysis.

    Uses enterprise-standard hourly rate ($150/hr) for CloudOps engineering
    to determine implementation costs and ROI calculations.

    Args:
        annual_savings: Projected annual cost savings in USD
        implementation_hours: Estimated hours for implementation (default: 8)

    Returns:
        Dict containing comprehensive ROI metrics:
            - annual_savings: Input annual savings amount
            - implementation_cost: Calculated implementation cost
            - roi_percentage: Return on investment percentage
            - payback_months: Months to recoup implementation cost
            - implementation_hours: Input implementation hours
            - net_annual_benefit: Annual savings minus implementation cost
            - break_even_point: Same as payback_months
            - confidence_score: Conservative estimate (0.85)

    Formulas:
        - Implementation Cost = implementation_hours × $150/hr
        - ROI % = ((annual_savings - implementation_cost) / implementation_cost) × 100
        - Payback Months = (implementation_cost / annual_savings) × 12

    Example:
        >>> metrics = calculate_roi_metrics(annual_savings=12000, implementation_hours=10)
        >>> print(f"ROI: {metrics['roi_percentage']:.1f}%")
        ROI: 700.0%
        >>> print(f"Payback: {metrics['payback_months']:.1f} months")
        Payback: 1.5 months
    """
    # Standard enterprise hourly rate for CloudOps engineering
    hourly_rate = ENTERPRISE_HOURLY_RATE
    implementation_cost = implementation_hours * hourly_rate

    if implementation_cost == 0:
        roi_percentage = float("inf")
        payback_months = 0
    else:
        roi_percentage = ((annual_savings - implementation_cost) / implementation_cost) * 100
        payback_months = (implementation_cost / annual_savings) * 12 if annual_savings > 0 else float("inf")

    return {
        "annual_savings": annual_savings,
        "implementation_cost": implementation_cost,
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
        "implementation_hours": implementation_hours,
        "net_annual_benefit": annual_savings - implementation_cost,
        "break_even_point": payback_months,
        "confidence_score": 0.85,  # Conservative enterprise estimate
    }


def generate_executive_summary(
    analysis_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate executive summary for stakeholder reporting.

    Aggregates multiple analysis results into a high-level executive summary
    suitable for board presentations and stakeholder communications.

    Args:
        analysis_results: Dictionary of analysis results by scenario/category
            Each value should be a dict containing 'projected_annual_savings'

    Returns:
        Dict containing executive summary:
            - total_annual_savings: Sum of all projected savings
            - analysis_scope: Number of scenarios analyzed
            - executive_summary: Human-readable summary text
            - recommendation: Next steps recommendation
            - risk_assessment: Risk level and description

    Example:
        >>> results = {
        ...     'ec2_rightsizing': {'projected_annual_savings': 5000},
        ...     's3_lifecycle': {'projected_annual_savings': 3000},
        ... }
        >>> summary = generate_executive_summary(results)
        >>> print(summary['executive_summary'])
        Cost optimization analysis identified $8,000 in potential annual savings
    """
    total_savings = sum(
        [result.get("projected_annual_savings", 0) for result in analysis_results.values() if isinstance(result, dict)]
    )

    return {
        "total_annual_savings": total_savings,
        "analysis_scope": len(analysis_results),
        "executive_summary": f"Cost optimization analysis identified ${total_savings:,.0f} in potential annual savings",
        "recommendation": "Proceed with implementation planning for highest-ROI scenarios",
        "risk_assessment": "Low risk - read-only analysis with proven optimization patterns",
    }


class BusinessCaseAnalyzer:
    """
    Business case analyzer for cost optimization scenarios.

    Provides enterprise-grade ROI analysis and executive summary generation
    with Rich CLI output for terminal display.

    Attributes:
        console: Rich console for formatted output

    Example:
        >>> analyzer = BusinessCaseAnalyzer()
        >>> metrics = analyzer.calculate_roi_metrics(annual_savings=10000)
        >>> print(f"Payback: {metrics['payback_months']:.1f} months")
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize business case analyzer.

        Args:
            console: Optional Rich console instance (uses default if not provided)
        """
        self.console = console or default_console

    def calculate_roi_metrics(self, annual_savings: float, implementation_hours: float = 8) -> Dict[str, Any]:
        """
        Calculate comprehensive ROI metrics for business case analysis.

        Wrapper method for module-level calculate_roi_metrics function.

        Args:
            annual_savings: Projected annual cost savings in USD
            implementation_hours: Estimated hours for implementation (default: 8)

        Returns:
            Dict containing comprehensive ROI metrics

        See Also:
            calculate_roi_metrics: Module-level function with detailed documentation
        """
        return calculate_roi_metrics(annual_savings, implementation_hours)

    def generate_executive_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary for stakeholder reporting.

        Wrapper method for module-level generate_executive_summary function.

        Args:
            analysis_results: Dictionary of analysis results by scenario

        Returns:
            Dict containing executive summary

        See Also:
            generate_executive_summary: Module-level function with detailed documentation
        """
        return generate_executive_summary(analysis_results)
