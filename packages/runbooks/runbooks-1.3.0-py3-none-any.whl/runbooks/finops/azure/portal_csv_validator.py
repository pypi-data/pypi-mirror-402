"""
Azure Portal CSV Validator - 4-Way Validation Cross-Check

Validates Azure Cost Management API results against Portal CSV exports.
Per ADLC v2.3.0, API is ALWAYS authoritative - CSV is for validation only.

Usage:
    from runbooks.finops.azure import validate_portal_csv, parse_portal_csv

    # Parse Portal CSV
    csv_data = parse_portal_csv(Path("portal-csv/cost-report.csv"))

    # Validate against API result
    result = validate_portal_csv(api_total=1234.56, csv_total=csv_data.total)

Architecture (v2.3.0):
    ┌──────────────┐    ┌──────────────┐
    │  REST API    │ -> │ Portal CSV   │
    │ AUTHORITATIVE│    │ VALIDATION   │
    └──────────────┘    └──────────────┘
           │                   │
           v                   v
      [FINAL VALUE]       [Alert Only]
       Always API          NO OVERRIDE

Framework: ADLC v3.0.0 | Version: 1.0.0
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class PortalCSVData:
    """Parsed Portal CSV data."""

    total_cost: float
    currency: str
    subscriptions: List[Dict[str, Any]]
    services: List[Dict[str, Any]]
    source_file: str
    parsed_at: str
    format_detected: str


@dataclass
class ValidationResult:
    """Cross-validation result."""

    api_total: float
    csv_total: float
    variance_amount: float
    variance_pct: float
    status: str  # PASS, WARN, FAIL
    ground_truth_override: bool  # ALWAYS False per v2.3.0
    authority: str
    recommendation: str


def detect_csv_format(file_path: Path) -> str:
    """
    Detect Portal CSV format (multiple Azure export formats supported).

    Returns:
        Format identifier: "cost_analysis", "cost_management", "focus_export", "unknown"
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return "empty"

    header_lower = [h.lower().strip() for h in header]

    # FOCUS 1.3 export format
    if "billedcost" in header_lower and "effectivecost" in header_lower:
        return "focus_export"

    # Azure Cost Analysis export
    if "servicename" in header_lower and "cost" in header_lower:
        return "cost_analysis"

    # Azure Cost Management export
    if "costinbillingcurrency" in header_lower:
        return "cost_management"

    # Subscription-based export
    if "subscriptionname" in header_lower and "cost" in header_lower:
        return "subscription_export"

    return "unknown"


def parse_portal_csv(
    file_path: Path,
    currency: str = "NZD",
) -> PortalCSVData:
    """
    Parse Azure Portal CSV export (multiple formats supported).

    Args:
        file_path: Path to Portal CSV file
        currency: Expected currency (default: NZD)

    Returns:
        PortalCSVData with parsed cost data
    """
    format_type = detect_csv_format(file_path)
    total_cost = 0.0
    subscriptions: List[Dict[str, Any]] = []
    services: List[Dict[str, Any]] = []
    sub_totals: Dict[str, float] = {}
    svc_totals: Dict[str, float] = {}

    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            cost = 0.0

            # Extract cost based on format
            if format_type == "focus_export":
                cost = float(row.get("BilledCost", 0) or 0)
            elif format_type == "cost_analysis":
                cost = float(row.get("Cost", 0) or 0)
            elif format_type == "cost_management":
                cost = float(row.get("CostInBillingCurrency", 0) or 0)
            elif format_type == "subscription_export":
                cost = float(row.get("Cost", 0) or 0)
            else:
                # Try common column names
                for col in ["Cost", "Amount", "BilledCost", "TotalCost"]:
                    if col in row and row[col]:
                        try:
                            cost = float(row[col].replace(",", "").replace("$", ""))
                            break
                        except ValueError:
                            continue

            total_cost += cost

            # Aggregate by subscription if available
            sub_name = row.get("SubscriptionName", row.get("subscriptionName", ""))
            if sub_name:
                sub_totals[sub_name] = sub_totals.get(sub_name, 0) + cost

            # Aggregate by service if available
            svc_name = row.get("ServiceName", row.get("serviceName", row.get("MeterCategory", "")))
            if svc_name:
                svc_totals[svc_name] = svc_totals.get(svc_name, 0) + cost

    # Convert aggregates to lists
    subscriptions = [
        {"name": name, "cost": cost, "percentage": (cost / total_cost * 100) if total_cost > 0 else 0}
        for name, cost in sorted(sub_totals.items(), key=lambda x: x[1], reverse=True)
    ]
    services = [
        {"name": name, "cost": cost, "percentage": (cost / total_cost * 100) if total_cost > 0 else 0}
        for name, cost in sorted(svc_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return PortalCSVData(
        total_cost=round(total_cost, 2),
        currency=currency,
        subscriptions=subscriptions,
        services=services,
        source_file=str(file_path),
        parsed_at=datetime.now().isoformat(),
        format_detected=format_type,
    )


def validate_portal_csv(
    api_total: float,
    csv_total: float,
    tolerance_warn: float = 1.0,
    tolerance_fail: float = 5.0,
) -> ValidationResult:
    """
    Validate API result against Portal CSV (v2.3.0 - NO OVERRIDE).

    Args:
        api_total: Total from Cost Management API (authoritative)
        csv_total: Total from Portal CSV export
        tolerance_warn: Variance % threshold for warning (default: 1%)
        tolerance_fail: Variance % threshold for failure (default: 5%)

    Returns:
        ValidationResult with variance analysis

    Note:
        Per ADLC v2.3.0, API is ALWAYS authoritative.
        ground_truth_override is ALWAYS False.
    """
    variance_amount = abs(api_total - csv_total)
    variance_pct = (variance_amount / api_total * 100) if api_total > 0 else 0

    if variance_pct <= tolerance_warn:
        status = "PASS"
        recommendation = "API validated against Portal CSV within tolerance"
    elif variance_pct <= tolerance_fail:
        status = "WARN"
        recommendation = "Investigate variance root cause (Timing? RBAC gaps? Pending charges?)"
    else:
        status = "FAIL"
        recommendation = "HITL escalation required - significant variance detected"

    return ValidationResult(
        api_total=round(api_total, 2),
        csv_total=round(csv_total, 2),
        variance_amount=round(variance_amount, 2),
        variance_pct=round(variance_pct, 4),
        status=status,
        ground_truth_override=False,  # v2.3.0: ALWAYS False
        authority="API (v2.3.0 - ALWAYS authoritative)",
        recommendation=recommendation,
    )


def find_portal_csv(
    csv_dir: Path,
    patterns: Optional[List[str]] = None,
) -> Optional[Path]:
    """
    Find Portal CSV file in directory.

    Args:
        csv_dir: Directory containing Portal CSV files
        patterns: List of filename patterns to search (default: common Azure patterns)

    Returns:
        Path to CSV file if found, None otherwise
    """
    if patterns is None:
        patterns = [
            "*.csv",
            "CostManagement*.csv",
            "AzureCostManagement*.csv",
            "cost-report*.csv",
            "costs*.csv",
            "billing*.csv",
        ]

    if not csv_dir.exists():
        return None

    for pattern in patterns:
        matches = list(csv_dir.glob(pattern))
        if matches:
            # Return most recently modified file
            return max(matches, key=lambda p: p.stat().st_mtime)

    return None
