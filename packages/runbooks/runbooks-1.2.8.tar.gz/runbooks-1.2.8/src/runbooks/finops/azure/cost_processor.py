"""
Azure Cost Processor - FOCUS 1.3 Aligned Data Processing

Processes Azure Cost Management exports with FOCUS 1.3 schema alignment.
Follows runbooks.finops.cost_processor patterns for consistency.

Migration: Copy to runbooks/finops/azure_cost_processor.py

References:
- FOCUS 1.3 (ratified Dec 5, 2025): https://focus.finops.org/
- Azure FOCUS Schema: https://learn.microsoft.com/azure/cost-management-billing/dataset-schema/cost-usage-details-focus
- runbooks.finops.cost_processor: Processing patterns

Framework: ADLC v3.0.0 | Version: 1.0.0
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from runbooks.finops.azure.types import (
    AzureCostData,
    AzureServiceCost,
    AzureSubscriptionCost,
    classify_cost_tier,
)
from runbooks.finops.azure.config import AzureReportConfig


def load_azure_services_csv(
    file_path: Path,
    currency_column: str = "Cost",
    usd_column: str = "CostUSD",
) -> Tuple[List[Dict[str, Any]], float, float]:
    """
    Load Azure Cost Management services export CSV.

    Args:
        file_path: Path to services CSV file
        currency_column: Column name for billing currency cost (default: "Cost")
        usd_column: Column name for USD cost (default: "CostUSD")

    Returns:
        Tuple of (rows, total_nzd, total_usd)

    CSV Format (FOCUS 1.3 aligned):
        UsageDate, ServiceName, CostUSD, Cost, Currency
    """
    rows = []
    total_nzd = 0.0
    total_usd = 0.0

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            service_name = row.get("ServiceName", "").strip()
            if not service_name:
                continue  # Skip rows without service name

            cost_nzd = float(row.get(currency_column, 0) or 0)
            cost_usd = float(row.get(usd_column, 0) or 0)

            # Skip zero or negative costs (credits/adjustments handled separately)
            if cost_nzd <= 0:
                continue

            rows.append({
                "usage_date": row.get("UsageDate", ""),
                "service_name": service_name,
                "cost_nzd": cost_nzd,
                "cost_usd": cost_usd,
                "currency": row.get("Currency", "NZD"),
            })
            total_nzd += cost_nzd
            total_usd += cost_usd

    return rows, total_nzd, total_usd


def load_azure_subscriptions_csv(
    file_path: Path,
    currency_column: str = "Cost",
    usd_column: str = "CostUSD",
) -> Tuple[List[Dict[str, Any]], float, float]:
    """
    Load Azure Cost Management subscriptions export CSV.

    Args:
        file_path: Path to subscriptions CSV file
        currency_column: Column name for billing currency cost (default: "Cost")
        usd_column: Column name for USD cost (default: "CostUSD")

    Returns:
        Tuple of (rows, total_nzd, total_usd)

    CSV Format (FOCUS 1.3 aligned):
        UsageDate, SubscriptionName, SubscriptionId, EnrollmentAccountName, CostUSD, Cost, Currency
    """
    rows = []
    total_nzd = 0.0
    total_usd = 0.0

    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub_name = row.get("SubscriptionName", "").strip()
            if not sub_name:
                continue

            cost_nzd = float(row.get(currency_column, 0) or 0)
            cost_usd = float(row.get(usd_column, 0) or 0)

            if cost_nzd <= 0:
                continue

            rows.append({
                "usage_date": row.get("UsageDate", ""),
                "subscription_name": sub_name,
                "subscription_id": row.get("SubscriptionId", ""),
                "enrollment_account": row.get("EnrollmentAccountName", ""),
                "cost_nzd": cost_nzd,
                "cost_usd": cost_usd,
                "currency": row.get("Currency", "NZD"),
            })
            total_nzd += cost_nzd
            total_usd += cost_usd

    return rows, total_nzd, total_usd


def aggregate_services_by_name(
    rows: List[Dict[str, Any]],
    config: AzureReportConfig,
) -> List[AzureServiceCost]:
    """
    Aggregate service costs and apply tier classification.

    Args:
        rows: Raw service cost rows
        config: Report configuration with thresholds

    Returns:
        List of AzureServiceCost sorted by cost descending
    """
    # Aggregate by service name
    aggregated: Dict[str, Dict[str, float]] = {}
    for row in rows:
        name = row["service_name"]
        if name not in aggregated:
            aggregated[name] = {"cost_nzd": 0.0, "cost_usd": 0.0}
        aggregated[name]["cost_nzd"] += row["cost_nzd"]
        aggregated[name]["cost_usd"] += row["cost_usd"]

    # Calculate total for percentage
    total_nzd = sum(s["cost_nzd"] for s in aggregated.values())

    # Convert to typed list with tier classification
    services: List[AzureServiceCost] = []
    for name, costs in aggregated.items():
        pct = (costs["cost_nzd"] / total_nzd * 100) if total_nzd > 0 else 0.0
        tier = classify_cost_tier(
            costs["cost_nzd"],
            config.high_cost_threshold,
            config.medium_cost_threshold,
        )
        services.append(AzureServiceCost(
            service_name=name,
            cost_nzd=costs["cost_nzd"],
            cost_usd=costs["cost_usd"],
            percentage=pct,
            cost_tier=tier,
            rank=0,  # Will be set after sorting
        ))

    # Sort by cost descending and assign ranks
    services.sort(key=lambda x: x["cost_nzd"], reverse=True)
    for i, svc in enumerate(services):
        svc["rank"] = i + 1

    return services


def aggregate_subscriptions_by_name(
    rows: List[Dict[str, Any]],
    config: AzureReportConfig,
) -> List[AzureSubscriptionCost]:
    """
    Aggregate subscription costs and apply tier classification.

    Args:
        rows: Raw subscription cost rows
        config: Report configuration with thresholds

    Returns:
        List of AzureSubscriptionCost sorted by cost descending
    """
    # Aggregate by subscription name
    aggregated: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        name = row["subscription_name"]
        if name not in aggregated:
            aggregated[name] = {
                "subscription_id": row["subscription_id"],
                "enrollment_account": row["enrollment_account"],
                "cost_nzd": 0.0,
                "cost_usd": 0.0,
            }
        aggregated[name]["cost_nzd"] += row["cost_nzd"]
        aggregated[name]["cost_usd"] += row["cost_usd"]

    # Calculate total for percentage
    total_nzd = sum(s["cost_nzd"] for s in aggregated.values())

    # Convert to typed list
    subscriptions: List[AzureSubscriptionCost] = []
    for name, data in aggregated.items():
        pct = (data["cost_nzd"] / total_nzd * 100) if total_nzd > 0 else 0.0
        tier = classify_cost_tier(
            data["cost_nzd"],
            config.high_cost_threshold,
            config.medium_cost_threshold,
        )
        subscriptions.append(AzureSubscriptionCost(
            subscription_name=name,
            subscription_id=data["subscription_id"],
            enrollment_account=data["enrollment_account"],
            cost_nzd=data["cost_nzd"],
            cost_usd=data["cost_usd"],
            percentage=pct,
            cost_tier=tier,
            rank=0,
        ))

    # Sort by cost descending and assign ranks
    subscriptions.sort(key=lambda x: x["cost_nzd"], reverse=True)
    for i, sub in enumerate(subscriptions):
        sub["rank"] = i + 1

    return subscriptions


def generate_executive_narrative(
    services: List[AzureServiceCost],
    subscriptions: List[AzureSubscriptionCost],
    total_nzd: float,
    config: AzureReportConfig,
    top_n: int = 3,
) -> str:
    """
    Generate executive summary narrative for cost report.

    Args:
        services: Aggregated service costs
        subscriptions: Aggregated subscription costs
        total_nzd: Total cost in billing currency
        config: Report configuration
        top_n: Number of top items to highlight

    Returns:
        Executive narrative string
    """
    # Count tiers
    high_count = sum(1 for s in services if s["cost_tier"] == "HIGH")
    medium_count = sum(1 for s in services if s["cost_tier"] == "MEDIUM")
    low_count = sum(1 for s in services if s["cost_tier"] == "LOW")

    # Top services
    top_services = services[:top_n]
    top_services_text = ", ".join(
        f"{s['service_name']} ({config.currency_symbol}{s['cost_nzd']:,.0f})"
        for s in top_services
    )

    # Top subscriptions
    top_subs = subscriptions[:top_n]
    top_subs_text = ", ".join(
        f"{s['subscription_name']} ({config.currency_symbol}{s['cost_nzd']:,.0f})"
        for s in top_subs
    )

    narrative = f"""Azure Monthly Cost Summary for {config.customer_name}

Billing Period: {config.billing_period}
Date Range: {config.date_range}
Total Cost: {config.currency_symbol}{total_nzd:,.2f} {config.currency}

Cost Tier Distribution:
- HIGH (≥{config.currency_symbol}{config.high_cost_threshold:,.0f}): {high_count} services
- MEDIUM (≥{config.currency_symbol}{config.medium_cost_threshold:,.0f}): {medium_count} services
- LOW: {low_count} services

Top {top_n} Services by Cost:
{top_services_text}

Top {top_n} Subscriptions by Cost:
{top_subs_text}

Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
FOCUS Version: 1.3 (ratified Dec 5, 2025)
"""
    return narrative


def process_azure_cost_data(
    config: AzureReportConfig,
    services_csv: Optional[Path] = None,
    subscriptions_csv: Optional[Path] = None,
) -> AzureCostData:
    """
    Process Azure cost data from CSV exports.

    This is the main entry point for cost data processing.
    Follows runbooks.finops.cost_processor patterns.

    Args:
        config: Report configuration
        services_csv: Path to services CSV (uses config default if not provided)
        subscriptions_csv: Path to subscriptions CSV (uses config default if not provided)

    Returns:
        AzureCostData with processed cost breakdown

    Raises:
        FileNotFoundError: If required CSV files not found
        ValueError: If CSV data is invalid
    """
    # Use provided paths or config defaults
    services_path = services_csv or config.services_csv
    subscriptions_path = subscriptions_csv or config.subscriptions_csv

    if not services_path or not services_path.exists():
        raise FileNotFoundError(f"Services CSV not found: {services_path}")

    # Load and process services data
    service_rows, services_total_nzd, services_total_usd = load_azure_services_csv(
        services_path
    )
    services = aggregate_services_by_name(service_rows, config)

    # Load and process subscriptions data (optional)
    subscriptions: List[AzureSubscriptionCost] = []
    subs_total_nzd = 0.0
    subs_total_usd = 0.0

    if subscriptions_path and subscriptions_path.exists():
        sub_rows, subs_total_nzd, subs_total_usd = load_azure_subscriptions_csv(
            subscriptions_path
        )
        subscriptions = aggregate_subscriptions_by_name(sub_rows, config)

    # Use services total as primary (subscriptions may not include all costs)
    total_nzd = services_total_nzd
    total_usd = services_total_usd

    # Cost tier counts
    high_count = sum(1 for s in services if s["cost_tier"] == "HIGH")
    medium_count = sum(1 for s in services if s["cost_tier"] == "MEDIUM")
    low_count = sum(1 for s in services if s["cost_tier"] == "LOW")

    # Generate narrative
    narrative = generate_executive_narrative(
        services, subscriptions, total_nzd, config
    )

    # Build source files list
    source_files = [str(services_path)]
    if subscriptions_path and subscriptions_path.exists():
        source_files.append(str(subscriptions_path))

    return AzureCostData(
        customer_name=config.customer_name,
        customer_id=config.customer_id,
        billing_period=config.billing_period,
        date_range=config.date_range,
        total_cost_nzd=total_nzd,
        total_cost_usd=total_usd,
        billing_currency=config.currency,
        services=services,
        subscriptions=subscriptions,
        top_services=services[:5],
        top_subscriptions=subscriptions[:5],
        high_cost_count=high_count,
        medium_cost_count=medium_count,
        low_cost_count=low_count,
        total_services=len(services),
        total_subscriptions=len(subscriptions),
        narrative=narrative,
        source_files=source_files,
        focus_version="1.3",
    )


def filter_analytical_services(
    services: List[AzureServiceCost],
    excluded_names: Optional[List[str]] = None,
) -> Tuple[List[AzureServiceCost], float]:
    """
    Filter out non-analytical services (aligned with runbooks.finops pattern).

    Args:
        services: List of service costs
        excluded_names: Service names to exclude (e.g., ["Tax", "Credits"])

    Returns:
        Tuple of (filtered_services, excluded_total)
    """
    if excluded_names is None:
        excluded_names = []

    filtered = []
    excluded_total = 0.0

    for svc in services:
        if any(ex.lower() in svc["service_name"].lower() for ex in excluded_names):
            excluded_total += svc["cost_nzd"]
        else:
            filtered.append(svc)

    return filtered, excluded_total


def get_top_n_services(
    services: List[AzureServiceCost],
    n: int = 5,
    include_others: bool = True,
) -> Tuple[List[AzureServiceCost], float]:
    """
    Get top N services with optional "Others" aggregation.

    Args:
        services: Full list of services
        n: Number of top services to return
        include_others: Whether to calculate "Others" total

    Returns:
        Tuple of (top_n_services, others_total)
    """
    top_n = services[:n]
    others_total = sum(s["cost_nzd"] for s in services[n:]) if include_others else 0.0
    return top_n, others_total
