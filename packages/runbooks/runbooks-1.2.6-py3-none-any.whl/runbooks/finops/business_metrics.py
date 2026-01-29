#!/usr/bin/env python3
"""
Business Metrics Calculator for Executive Notebooks

Provides C-level financial metrics and KPIs for board presentations.
Calculates executive dashboard metrics (annual savings, ROI, quarterly projections)
with board-ready Rich CLI visualizations.

Strategic Alignment:
- Objective 1 (runbooks package): Executive decision support
- Enterprise SDLC: Business value quantification
- KISS/DRY/LEAN: Proven financial models with standard reporting

Architecture:
- Calculates CTO/CEO/CFO metrics from scored data
- Generates quarterly financial projections (Q1-Q4)
- Provides Rich CLI board-ready displays

Usage:
    from runbooks.finops.business_metrics import (
        calculate_executive_metrics,
        calculate_quarterly_projections,
        display_board_metrics,
        display_quarterly_table
    )

    # Calculate executive metrics
    metrics = calculate_executive_metrics(scored_data)

    # Display board dashboard
    display_board_metrics(metrics)

    # Generate quarterly projections
    quarterly = calculate_quarterly_projections(metrics['annual_savings'])
    display_quarterly_table(quarterly)

Author: Runbooks Team
Version: 1.1.20
Epic: v1.1.20 FinOps Dashboard Enhancements - Executive Analytics
"""

from typing import Dict

import pandas as pd
from rich.console import Console
from rich.table import Table

from runbooks.common.rich_utils import format_cost

console = Console()


def calculate_executive_metrics(scored_data: Dict[str, pd.DataFrame]) -> Dict:
    """
    Calculate CTO/CEO/CFO metrics - annual savings, ROI, quarterly projections.

    Aggregates financial metrics across all scored services:
    - Total resources analyzed
    - Decommission candidates (MUST + SHOULD tiers)
    - Current monthly/annual costs
    - Monthly/annual savings opportunity
    - Savings percentage
    - Implementation cost estimate
    - ROI percentage
    - Payback months
    - 3-year value projection

    Args:
        scored_data: Dictionary of scored DataFrames with decommission_tier column

    Returns:
        Dict with executive financial KPIs

    Example:
        {
            'total_resources': 500,
            'decommission_candidates': 125,
            'current_monthly_cost': 50000.00,
            'current_annual_cost': 600000.00,
            'monthly_savings': 12500.00,
            'annual_savings': 150000.00,
            'savings_percentage': 25.0,
            'implementation_cost': 50000.00,
            'roi_percentage': 200.0,
            'payback_months': 4.0,
            'three_year_value': 400000.00
        }
    """
    # Initialize aggregation variables
    total_current_cost = 0.0
    total_savings_opportunity = 0.0
    total_resources = 0
    decommission_candidates = 0

    # Aggregate across all services
    for service, df in scored_data.items():
        # Count total resources
        total_resources += len(df)

        # Sum current costs (if cost column exists)
        if "monthly_cost" in df.columns:
            total_current_cost += df["monthly_cost"].sum()

        # Sum savings opportunity (MUST + SHOULD tiers)
        if "decommission_tier" in df.columns and "monthly_cost" in df.columns:
            must_should = df[df["decommission_tier"].isin(["MUST", "SHOULD"])]
            if not must_should.empty:
                total_savings_opportunity += must_should["monthly_cost"].sum()
                decommission_candidates += len(must_should)

    # Calculate annual metrics
    annual_current = total_current_cost * 12
    annual_savings = total_savings_opportunity * 12

    # Calculate savings percentage
    savings_percentage = (annual_savings / annual_current * 100) if annual_current > 0 else 0.0

    # Estimate implementation cost
    # Rule of thumb: $50K for projects >$200K annual savings, 25% of savings otherwise
    implementation_cost = 50000.0 if annual_savings > 200000 else annual_savings * 0.25

    # Calculate ROI percentage
    roi_percentage = (
        ((annual_savings - implementation_cost) / implementation_cost * 100) if implementation_cost > 0 else 0.0
    )

    # Calculate payback months
    payback_months = implementation_cost / total_savings_opportunity if total_savings_opportunity > 0 else float("inf")

    # Calculate 3-year value
    three_year_value = (annual_savings * 3) - implementation_cost

    return {
        "total_resources": total_resources,
        "decommission_candidates": decommission_candidates,
        "current_monthly_cost": total_current_cost,
        "current_annual_cost": annual_current,
        "monthly_savings": total_savings_opportunity,
        "annual_savings": annual_savings,
        "savings_percentage": savings_percentage,
        "implementation_cost": implementation_cost,
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
        "three_year_value": three_year_value,
    }


def calculate_quarterly_projections(annual_savings: float) -> Dict:
    """
    Q1-Q4 phased implementation financial forecast.

    Models realistic savings realization over 4 quarters:
    - Q1: 15% realization (planning & assessment)
    - Q2: 35% realization (early implementation)
    - Q3: 75% realization (full deployment)
    - Q4: 100% realization (optimization)

    Args:
        annual_savings: Annual savings opportunity from calculate_executive_metrics()

    Returns:
        Dict with quarterly projections

    Example:
        {
            'Q1': {
                'savings': 5625.00,
                'cumulative': 5625.00,
                'realization': '15%',
                'phase': 'Planning & Assessment'
            },
            ...
        }
    """
    # Phased implementation model (industry-standard ramp-up)
    q1_realization = 0.15  # 15% in Q1 (planning phase)
    q2_realization = 0.35  # 35% in Q2 (early implementation)
    q3_realization = 0.75  # 75% in Q3 (full deployment)
    q4_realization = 1.00  # 100% in Q4 (steady state)

    # Calculate quarterly run-rate (full annual savings / 4)
    quarterly_savings = annual_savings / 4

    return {
        "Q1": {
            "savings": quarterly_savings * q1_realization,
            "cumulative": quarterly_savings * q1_realization,
            "realization": f"{int(q1_realization * 100)}%",
            "phase": "Planning & Assessment",
            "activities": "Resource validation, stakeholder alignment, runbook development",
        },
        "Q2": {
            "savings": quarterly_savings * q2_realization,
            "cumulative": quarterly_savings * (q1_realization + q2_realization),
            "realization": f"{int(q2_realization * 100)}%",
            "phase": "Early Implementation",
            "activities": "Low-risk decommissions (MUST tier), monitoring setup",
        },
        "Q3": {
            "savings": quarterly_savings * q3_realization,
            "cumulative": quarterly_savings * (q1_realization + q2_realization + q3_realization),
            "realization": f"{int(q3_realization * 100)}%",
            "phase": "Full Deployment",
            "activities": "SHOULD tier decommissions, process automation",
        },
        "Q4": {
            "savings": quarterly_savings * q4_realization,
            "cumulative": annual_savings,
            "realization": f"{int(q4_realization * 100)}%",
            "phase": "Optimization & Steady State",
            "activities": "COULD tier evaluation, continuous improvement",
        },
    }


def display_board_metrics(metrics: Dict) -> None:
    """
    Board-ready Rich table with financial KPIs.

    Args:
        metrics: Executive metrics from calculate_executive_metrics()

    Returns:
        None (prints Rich table to console)

    Note:
        Designed for C-level presentations with clear financial metrics
    """
    # Financial Summary Table
    table = Table(title="Executive Financial Dashboard", show_header=True, header_style="bold cyan")

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="green bold")

    # Resource metrics
    table.add_row("Total Resources Analyzed", f"{metrics['total_resources']:,}")
    table.add_row("Optimization Candidates", f"{metrics['decommission_candidates']:,}")

    # Cost metrics
    table.add_section()
    table.add_row("Current Annual Cost", format_cost(metrics["current_annual_cost"]))
    table.add_row("Annual Savings Opportunity", format_cost(metrics["annual_savings"]))
    table.add_row("Savings Percentage", f"{metrics['savings_percentage']:.1f}%")

    # Investment metrics
    table.add_section()
    table.add_row("Implementation Investment", format_cost(metrics["implementation_cost"]))
    table.add_row("Return on Investment (ROI)", f"{metrics['roi_percentage']:.0f}%")
    table.add_row("Payback Period", f"{metrics['payback_months']:.1f} months")
    table.add_row("3-Year Net Value", format_cost(metrics["three_year_value"]))

    console.print(table)


def display_quarterly_table(quarterly: Dict) -> None:
    """
    Display quarterly projections table.

    Args:
        quarterly: Quarterly projections from calculate_quarterly_projections()

    Returns:
        None (prints Rich table to console)

    Note:
        Shows phased savings realization for CFO planning
    """
    table = Table(title="Quarterly Financial Projections (Year 1)", show_header=True, header_style="bold cyan")

    table.add_column("Quarter", style="cyan", no_wrap=True)
    table.add_column("Phase", style="yellow")
    table.add_column("Quarterly Savings", justify="right", style="green")
    table.add_column("Cumulative Savings", justify="right", style="green bold")
    table.add_column("Realization %", justify="center", style="white")

    # Add rows for each quarter
    for quarter, data in quarterly.items():
        table.add_row(
            quarter, data["phase"], format_cost(data["savings"]), format_cost(data["cumulative"]), data["realization"]
        )

    console.print(table)


def display_detailed_quarterly_table(quarterly: Dict) -> None:
    """
    Display detailed quarterly projections with implementation activities.

    Args:
        quarterly: Quarterly projections from calculate_quarterly_projections()

    Returns:
        None (prints Rich table to console)

    Note:
        Includes implementation activities for operational planning
    """
    table = Table(title="Detailed Quarterly Implementation Plan", show_header=True, header_style="bold cyan")

    table.add_column("Quarter", style="cyan", no_wrap=True)
    table.add_column("Phase", style="yellow")
    table.add_column("Activities", style="white")
    table.add_column("Savings", justify="right", style="green bold")
    table.add_column("Realization", justify="center", style="white")

    # Add rows for each quarter
    for quarter, data in quarterly.items():
        table.add_row(quarter, data["phase"], data["activities"], format_cost(data["savings"]), data["realization"])

    console.print(table)


def generate_executive_summary(metrics: Dict, quarterly: Dict) -> str:
    """
    Generate text-based executive summary for reports.

    Args:
        metrics: Executive metrics from calculate_executive_metrics()
        quarterly: Quarterly projections from calculate_quarterly_projections()

    Returns:
        str: Formatted executive summary text

    Note:
        Suitable for email updates or slide deck content
    """
    summary = f"""
EXECUTIVE SUMMARY - Cloud Cost Optimization Analysis

Resource Landscape:
- Total AWS resources analyzed: {metrics["total_resources"]:,}
- Decommission candidates identified: {metrics["decommission_candidates"]:,}

Financial Impact:
- Current annual cloud spend: {format_cost(metrics["current_annual_cost"])}
- Annual savings opportunity: {format_cost(metrics["annual_savings"])}
- Savings percentage: {metrics["savings_percentage"]:.1f}% of current spend

Investment Analysis:
- Implementation cost: {format_cost(metrics["implementation_cost"])}
- Return on Investment: {metrics["roi_percentage"]:.0f}%
- Payback period: {metrics["payback_months"]:.1f} months
- 3-year net value: {format_cost(metrics["three_year_value"])}

Quarterly Projections (Year 1):
- Q1 (Planning): {format_cost(quarterly["Q1"]["savings"])} ({quarterly["Q1"]["realization"]} realization)
- Q2 (Implementation): {format_cost(quarterly["Q2"]["savings"])} ({quarterly["Q2"]["realization"]} realization)
- Q3 (Deployment): {format_cost(quarterly["Q3"]["savings"])} ({quarterly["Q3"]["realization"]} realization)
- Q4 (Steady State): {format_cost(quarterly["Q4"]["savings"])} ({quarterly["Q4"]["realization"]} realization)

Recommendation:
Proceed with phased implementation starting Q1 to achieve {format_cost(metrics["annual_savings"])}
in annual savings with {metrics["roi_percentage"]:.0f}% ROI and {metrics["payback_months"]:.1f}-month payback.
"""
    return summary.strip()
