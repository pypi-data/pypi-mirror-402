#!/usr/bin/env python3
"""
WHAT-IF Scenario Calculator for FinOps Notebooks

Provides business scenario analysis for cost optimization initiatives.
Generates Conservative, Moderate, and Aggressive decommission scenarios
with ROI calculations and quarterly financial projections.

Strategic Alignment:
- Objective 1 (runbooks package): Executive decision support
- Enterprise SDLC: Evidence-based financial planning
- KISS/DRY/LEAN: Standard scenario templates with configurable parameters

Architecture:
- Wraps scored data to generate 3 standard scenarios
- Calculates ROI metrics (percentage, payback months, 3-year NPV)
- Provides Rich CLI visualization for executive presentations

Usage:
    from runbooks.finops.whatif_scenarios import (
        calculate_whatif_scenarios,
        display_scenario_table,
        calculate_roi_metrics
    )

    # Generate standard scenarios
    scenarios = calculate_whatif_scenarios(scored_data)

    # Display Rich table
    display_scenario_table(scenarios)

    # Calculate ROI for specific scenario
    roi = calculate_roi_metrics(scenarios[0], implementation_cost=50000)

Author: Runbooks Team
Version: 1.1.20
Epic: v1.1.20 FinOps Dashboard Enhancements - Executive Scenario Analysis
"""

from typing import Dict, List

import pandas as pd
from rich.console import Console
from rich.table import Table

from runbooks.common.rich_utils import format_cost

console = Console()


def calculate_whatif_scenarios(scored_data: Dict[str, pd.DataFrame]) -> List[Dict]:
    """
    Generate 3 standard WHAT-IF scenarios with savings projections.

    Scenarios:
    1. Conservative: Retire MUST tier only (80-100 decommission score)
    2. Moderate: Retire MUST + 50% SHOULD (80-100 + half of 50-79 scores)
    3. Aggressive: Retire all recommendations (MUST + SHOULD + COULD tiers)

    Args:
        scored_data: Dictionary of scored DataFrames with decommission_tier column

    Returns:
        List of scenario dictionaries with financial projections

    Example:
        [
            {
                'name': 'Conservative',
                'description': 'Retire MUST tier only (high confidence)',
                'resources_affected': 25,
                'monthly_savings': 15000.00,
                'annual_savings': 180000.00,
                'confidence': 95,
                'risk': 'Low',
                'implementation_effort': '1-2 weeks'
            },
            ...
        ]
    """
    scenarios = []

    # Calculate totals across all services
    must_savings = 0.0
    should_savings = 0.0
    could_savings = 0.0
    must_count = 0
    should_count = 0
    could_count = 0

    for service, df in scored_data.items():
        # Only process DataFrames with decommission scoring
        if "decommission_tier" not in df.columns or "monthly_cost" not in df.columns:
            continue

        # Calculate tier-based savings
        must_df = df[df["decommission_tier"] == "MUST"]
        should_df = df[df["decommission_tier"] == "SHOULD"]
        could_df = df[df["decommission_tier"] == "COULD"]

        must_savings += must_df["monthly_cost"].sum() if not must_df.empty else 0.0
        should_savings += should_df["monthly_cost"].sum() if not should_df.empty else 0.0
        could_savings += could_df["monthly_cost"].sum() if not could_df.empty else 0.0

        must_count += len(must_df)
        should_count += len(should_df)
        could_count += len(could_df)

    # Scenario 1: Conservative (MUST tier only)
    scenarios.append(
        {
            "name": "Conservative",
            "description": "Retire MUST tier only (high confidence decommissions)",
            "resources_affected": must_count,
            "monthly_savings": must_savings,
            "annual_savings": must_savings * 12,
            "confidence": 95,
            "risk": "Low",
            "implementation_effort": "1-2 weeks",
            "business_impact": "Minimal disruption, clear cost reduction",
        }
    )

    # Scenario 2: Moderate (MUST + 50% SHOULD)
    moderate_savings = must_savings + (should_savings * 0.5)
    moderate_count = must_count + int(should_count * 0.5)

    scenarios.append(
        {
            "name": "Moderate",
            "description": "Retire MUST + 50% SHOULD tier (balanced approach)",
            "resources_affected": moderate_count,
            "monthly_savings": moderate_savings,
            "annual_savings": moderate_savings * 12,
            "confidence": 80,
            "risk": "Medium",
            "implementation_effort": "2-4 weeks",
            "business_impact": "Moderate savings with managed risk",
        }
    )

    # Scenario 3: Aggressive (MUST + SHOULD + COULD)
    total_savings = must_savings + should_savings + could_savings
    total_count = must_count + should_count + could_count

    scenarios.append(
        {
            "name": "Aggressive",
            "description": "Retire all recommendations (maximum cost reduction)",
            "resources_affected": total_count,
            "monthly_savings": total_savings,
            "annual_savings": total_savings * 12,
            "confidence": 60,
            "risk": "High",
            "implementation_effort": "4-8 weeks",
            "business_impact": "Maximum savings with thorough validation required",
        }
    )

    return scenarios


def display_scenario_table(scenarios: List[Dict]) -> None:
    """
    Display Rich CLI table with scenario comparison.

    Args:
        scenarios: List of scenario dictionaries from calculate_whatif_scenarios()

    Returns:
        None (prints Rich table to console)

    Note:
        Table includes: Scenario, Resources, Monthly/Annual Savings, Confidence,
        Risk, Timeline for executive decision-making
    """
    table = Table(title="WHAT-IF Scenario Analysis", show_header=True, header_style="bold cyan")

    # Define columns
    table.add_column("Scenario", style="cyan", no_wrap=True)
    table.add_column("Resources", justify="right", style="white")
    table.add_column("Monthly Savings", justify="right", style="green")
    table.add_column("Annual Savings", justify="right", style="green bold")
    table.add_column("Confidence", justify="right", style="yellow")
    table.add_column("Risk", justify="center", style="white")
    table.add_column("Timeline", justify="center", style="white")

    # Add rows for each scenario
    for s in scenarios:
        table.add_row(
            s["name"],
            f"{s['resources_affected']:,}",
            format_cost(s["monthly_savings"]),
            format_cost(s["annual_savings"]),
            f"{s['confidence']}%",
            s["risk"],
            s["implementation_effort"],
        )

    console.print(table)


def calculate_roi_metrics(scenario: Dict, implementation_cost: float = 50000.0) -> Dict:
    """
    Calculate ROI metrics for a scenario (ROI%, payback months, 3-year NPV).

    Args:
        scenario: Scenario dictionary from calculate_whatif_scenarios()
        implementation_cost: One-time implementation investment (default: $50K)

    Returns:
        Dict with ROI calculations:
            {
                'roi_percentage': 260.0,  # (annual_savings - cost) / cost * 100
                'payback_months': 3.3,    # implementation_cost / monthly_savings
                'three_year_value': 490000.0,  # (annual_savings * 3) - cost
                'break_even_month': 4  # Month when savings exceed investment
            }

    Note:
        ROI calculations assume:
        - Linear savings realization (monthly_savings consistent)
        - One-time implementation cost (no recurring expenses)
        - No discount rate applied (nominal dollars)
    """
    annual_savings = scenario["annual_savings"]
    monthly_savings = scenario["monthly_savings"]

    # ROI percentage: ((Annual Savings - Investment) / Investment) * 100
    roi_percentage = (
        ((annual_savings - implementation_cost) / implementation_cost * 100)
        if implementation_cost > 0
        else float("inf")
    )

    # Payback months: Investment / Monthly Savings
    payback_months = implementation_cost / monthly_savings if monthly_savings > 0 else float("inf")

    # 3-year net present value (simplified, no discount rate)
    three_year_value = (annual_savings * 3) - implementation_cost

    # Break-even month (ceiling of payback months)
    break_even_month = int(payback_months) + 1 if payback_months != float("inf") else None

    return {
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
        "three_year_value": three_year_value,
        "break_even_month": break_even_month,
    }


def display_roi_table(scenario: Dict, roi_metrics: Dict) -> None:
    """
    Display Rich CLI table with ROI metrics for a specific scenario.

    Args:
        scenario: Scenario dictionary from calculate_whatif_scenarios()
        roi_metrics: ROI metrics from calculate_roi_metrics()

    Returns:
        None (prints Rich table to console)

    Note:
        Executive-friendly display with key financial metrics for board presentations
    """
    table = Table(title=f"ROI Analysis - {scenario['name']} Scenario", show_header=True, header_style="bold cyan")

    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green bold")

    # Financial metrics
    table.add_row("Annual Savings", format_cost(scenario["annual_savings"]))
    table.add_row("Implementation Cost", format_cost(50000.0))  # Default assumption
    table.add_row("ROI Percentage", f"{roi_metrics['roi_percentage']:.1f}%")
    table.add_row("Payback Period", f"{roi_metrics['payback_months']:.1f} months")
    table.add_row("Break-Even Month", f"Month {roi_metrics['break_even_month']}")
    table.add_row("3-Year NPV", format_cost(roi_metrics["three_year_value"]))

    # Risk profile
    table.add_section()
    table.add_row("Confidence Level", f"{scenario['confidence']}%")
    table.add_row("Risk Assessment", scenario["risk"])
    table.add_row("Timeline", scenario["implementation_effort"])

    console.print(table)


def compare_scenarios(scenarios: List[Dict]) -> None:
    """
    Display comprehensive scenario comparison with ROI metrics.

    Args:
        scenarios: List of scenarios from calculate_whatif_scenarios()

    Returns:
        None (prints comprehensive Rich tables to console)

    Note:
        Displays:
        1. Scenario comparison table
        2. ROI metrics for each scenario
        3. Recommendation summary based on risk tolerance
    """
    # Display scenario comparison
    display_scenario_table(scenarios)

    console.print()  # Blank line for spacing

    # Display ROI analysis for each scenario
    for scenario in scenarios:
        roi = calculate_roi_metrics(scenario)
        display_roi_table(scenario, roi)
        console.print()  # Blank line between scenarios

    # Display recommendation summary
    recommendation_table = Table(
        title="Scenario Recommendations by Risk Tolerance", show_header=True, header_style="bold cyan"
    )

    recommendation_table.add_column("Risk Tolerance", style="cyan")
    recommendation_table.add_column("Recommended Scenario", style="yellow")
    recommendation_table.add_column("Rationale", style="white")

    recommendation_table.add_row("Risk-Averse", "Conservative", "High confidence (95%), minimal disruption, quick wins")

    recommendation_table.add_row("Balanced", "Moderate", "Optimal risk/reward (80% confidence), phased approach")

    recommendation_table.add_row("Growth-Focused", "Aggressive", "Maximum savings potential with thorough validation")

    console.print(recommendation_table)
