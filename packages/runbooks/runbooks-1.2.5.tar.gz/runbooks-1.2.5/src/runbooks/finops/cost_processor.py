import csv
import json
import os
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from boto3.session import Session
from rich.console import Console

from runbooks.common.date_utils import DateRangeCalculator  # ADLC v3.0.0: DRY date logic
from runbooks.finops.aws_client import get_account_id
from runbooks.finops.iam_guidance import handle_cost_explorer_error
from runbooks.finops.service_mapping import get_service_display_name  # v1.1.20: Service name standardization
from runbooks.finops.types import BudgetInfo, CostData, DualMetricResult, EC2Summary, ProfileData

console = Console()

# Enterprise batch processing configuration
BATCH_COST_EXPLORER_SIZE = 5  # Optimal batch size for Cost Explorer API to avoid rate limiting
MAX_CONCURRENT_COST_CALLS = 10  # AWS Cost Explorer rate limit consideration

# Service filtering configuration for analytical insights
NON_ANALYTICAL_SERVICES = ["Tax"]  # Services excluded from Top N analysis per user requirements

# Enhanced caching for filter operations to prevent redundant logging
_filter_cache: Dict[str, tuple] = {}
_filter_session_id: Optional[str] = None


def _get_filter_session_id() -> str:
    """Generate filter session ID for cache scoping"""
    global _filter_session_id
    if _filter_session_id is None:
        _filter_session_id = f"filter_session_{int(time.time())}"
    return _filter_session_id


def filter_analytical_services(
    services_dict: Dict[str, float], excluded_services: List[str] = None
) -> Tuple[Dict[str, float], float]:
    """
    Filter out non-analytical services from service cost data.

    v1.1.23: Returns both filtered services AND total of excluded services
    for proper "Others" row calculation and 100% cost reconciliation.

    Args:
        services_dict: Dictionary of service names to costs
        excluded_services: List of service patterns to exclude (defaults to NON_ANALYTICAL_SERVICES)

    Returns:
        Tuple of (filtered_services_dict, excluded_services_total)
        - filtered_services_dict: Analytical services only
        - excluded_services_total: Sum of excluded service costs (e.g., Tax) for "Others" row

    Example:
        >>> services = {'Amazon EC2': 100.0, 'Tax': 10.0, 'S3': 50.0}
        >>> filtered, excluded_total = filter_analytical_services(services)
        >>> filtered
        {'Amazon EC2': 100.0, 'S3': 50.0}
        >>> excluded_total
        10.0
    """
    if excluded_services is None:
        excluded_services = NON_ANALYTICAL_SERVICES

    filtered_services = {}
    excluded_services_total = 0.0
    filtered_count = 0

    for service_name, cost in services_dict.items():
        should_exclude = any(excluded in service_name for excluded in excluded_services)
        if not should_exclude:
            filtered_services[service_name] = cost
        else:
            excluded_services_total += cost
            filtered_count += 1

    # SESSION-AWARE LOGGING: Only log once per session to prevent redundant messages
    if filtered_count > 0:
        excluded_names = [
            name for name in services_dict.keys() if any(excluded in name for excluded in excluded_services)
        ]

        # Create cache key for this filter operation
        cache_key = f"{_get_filter_session_id()}:filtered_services"

        # Only log if not already logged in this session
        if cache_key not in _filter_cache:
            console.log(
                f"[dim yellow]🔍 Filtered {filtered_count} non-analytical services: {', '.join(excluded_names)} (${excluded_services_total:.2f} moved to Others)[/]"
            )
            _filter_cache[cache_key] = (filtered_count, excluded_names)

    return (filtered_services, excluded_services_total)


class DualMetricCostProcessor:
    """Enhanced processor for UnblendedCost (technical) and AmortizedCost (financial) reporting."""

    def __init__(self, session: Session, profile_name: Optional[str] = None, analysis_mode: str = "comprehensive"):
        """Initialize dual-metric cost processor.

        Args:
            session: AWS boto3 session
            profile_name: AWS profile name for error handling
            analysis_mode: Analysis mode - "technical" (UnblendedCost), "financial" (AmortizedCost), or "comprehensive" (both)
        """
        self.session = session
        self.profile_name = profile_name or "default"
        self.analysis_mode = analysis_mode
        self.ce = session.client("ce")

    def collect_dual_metrics(
        self, account_id: Optional[str] = None, start_date: str = None, end_date: str = None
    ) -> DualMetricResult:
        """Collect both UnblendedCost and AmortizedCost for comprehensive reporting.

        Args:
            account_id: AWS account ID for filtering (multi-account support)
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)

        Returns:
            DualMetricResult with both technical and financial perspectives
        """
        # Build filter for account if provided
        filter_param = None
        if account_id:
            filter_param = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [account_id]}}

        # Set default dates if not provided
        if not start_date or not end_date:
            today = date.today()
            start_date = today.replace(day=1).isoformat()
            end_date = (today + timedelta(days=1)).isoformat()  # AWS CE end date is exclusive

        try:
            # Inform user about the metric collection based on analysis mode
            if self.analysis_mode == "technical":
                console.log("[bright_blue]🔧 Collecting UnblendedCost data (Technical Analysis)[/]")
            elif self.analysis_mode == "financial":
                console.log("[bright_green]📊 Collecting AmortizedCost data (Financial Analysis)[/]")
            else:
                console.log(
                    "[bright_cyan]💰 Collecting both UnblendedCost and AmortizedCost data (Dual-Metrics Analysis)[/]"
                )

            # Technical Analysis (UnblendedCost) - always collect for comparison
            unblended_response = self.ce.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                **({"Filter": filter_param} if filter_param else {}),
            )

            # Financial Reporting (AmortizedCost) - always collect for comparison
            amortized_response = self.ce.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="MONTHLY",
                Metrics=["AmortizedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                **({"Filter": filter_param} if filter_param else {}),
            )

            # Parse UnblendedCost data
            unblended_costs = {}
            technical_total = 0.0
            service_breakdown_unblended = []

            for result in unblended_response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    service = group["Keys"][0]
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    if amount > 0.001:  # Filter negligible costs
                        unblended_costs[service] = amount
                        technical_total += amount
                        service_breakdown_unblended.append((service, amount))

            # Parse AmortizedCost data
            amortized_costs = {}
            financial_total = 0.0
            service_breakdown_amortized = []

            for result in amortized_response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    service = group["Keys"][0]
                    amount = float(group["Metrics"]["AmortizedCost"]["Amount"])
                    if amount > 0.001:  # Filter negligible costs
                        amortized_costs[service] = amount
                        financial_total += amount
                        service_breakdown_amortized.append((service, amount))

            # Calculate variance
            variance = abs(technical_total - financial_total)
            variance_percentage = (variance / financial_total * 100) if financial_total > 0 else 0.0

            # Sort service breakdowns by cost (descending)
            service_breakdown_unblended.sort(key=lambda x: x[1], reverse=True)
            service_breakdown_amortized.sort(key=lambda x: x[1], reverse=True)

            console.log(
                f"[green]✅ Dual-metric collection complete: Technical ${technical_total:.2f}, Financial ${financial_total:.2f}[/]"
            )

            return DualMetricResult(
                unblended_costs=unblended_costs,
                amortized_costs=amortized_costs,
                technical_total=technical_total,
                financial_total=financial_total,
                variance=variance,
                variance_percentage=variance_percentage,
                period_start=start_date,
                period_end=end_date,
                service_breakdown_unblended=service_breakdown_unblended,
                service_breakdown_amortized=service_breakdown_amortized,
            )

        except Exception as e:
            console.log(f"[red]❌ Dual-metric collection failed: {str(e)}[/]")
            if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
                handle_cost_explorer_error(e, self.profile_name)

            # Return empty result structure
            return DualMetricResult(
                unblended_costs={},
                amortized_costs={},
                technical_total=0.0,
                financial_total=0.0,
                variance=0.0,
                variance_percentage=0.0,
                period_start=start_date,
                period_end=end_date,
                service_breakdown_unblended=[],
                service_breakdown_amortized=[],
            )


def get_equal_period_cost_data(
    session: Session, profile_name: Optional[str] = None, account_id: Optional[str] = None, months_back: int = 3
) -> Dict[str, Any]:
    """
    Get equal-period cost data for accurate trend analysis.

    Addresses the mathematical error where partial current month (e.g., Sept 1-2)
    was compared against full previous month (Aug 1-31), resulting in misleading trends.

    Args:
        session: AWS boto3 session
        profile_name: AWS profile name for error handling
        account_id: Optional account ID for filtering
        months_back: Number of complete months to analyze

    Returns:
        Dict containing monthly cost data with equal periods for accurate trends
    """
    ce = session.client("ce")
    today = date.today()

    # Calculate complete months for comparison
    monthly_data = []

    # Get last N complete months (not including current partial month)
    for i in range(1, months_back + 1):  # Start from 1 to skip current month
        # Calculate the start and end of each complete month
        if today.month - i > 0:
            target_month = today.month - i
            target_year = today.year
        else:
            # Handle year boundary
            target_month = 12 + (today.month - i)
            target_year = today.year - 1

        # First day of target month
        month_start = date(target_year, target_month, 1)

        # Last day of target month
        if target_month == 12:
            month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)

        # Build filter for account if provided
        filter_param = None
        if account_id:
            filter_param = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [account_id]}}

        kwargs = {}
        if filter_param:
            kwargs["Filter"] = filter_param

        try:
            response = ce.get_cost_and_usage(
                TimePeriod={
                    "Start": month_start.isoformat(),
                    "End": (month_end + timedelta(days=1)).isoformat(),  # AWS CE end date is exclusive
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                **kwargs,
            )

            # Extract cost data
            total_cost = 0.0
            for result in response.get("ResultsByTime", []):
                if "Total" in result and "UnblendedCost" in result["Total"]:
                    total_cost = float(result["Total"]["UnblendedCost"]["Amount"])

            monthly_data.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "start_date": month_start.isoformat(),
                    "end_date": month_end.isoformat(),
                    "days": (month_end - month_start).days + 1,
                    "cost": total_cost,
                }
            )

        except Exception as e:
            console.log(f"[yellow]Error getting cost data for {month_start.strftime('%b %Y')}: {e}[/]")
            if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
                from .iam_guidance import handle_cost_explorer_error

                handle_cost_explorer_error(e, profile_name)

            # Add empty data to maintain structure
            monthly_data.append(
                {
                    "month": month_start.strftime("%b %Y"),
                    "start_date": month_start.isoformat(),
                    "end_date": month_end.isoformat(),
                    "days": (month_end - month_start).days + 1,
                    "cost": 0.0,
                }
            )

    return {
        "account_id": get_account_id(session) or "unknown",
        "monthly_costs": monthly_data,
        "analysis_type": "equal_period",
        "profile": session.profile_name or profile_name or "default",
    }


def get_trend(session: Session, tag: Optional[List[str]] = None, account_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get cost trend data for an AWS account.

    Args:
        session: The boto3 session to use
        tag: Optional list of tags in "Key=Value" format to filter resources.
        account_id: Optional account ID to filter costs to specific account (multi-account support)

    """
    ce = session.client("ce")
    tag_filters: List[Dict[str, Any]] = []
    if tag:
        for t in tag:
            key, value = t.split("=", 1)
            tag_filters.append({"Key": key, "Values": [value]})

    # Build filters for trend data (similar to get_cost_data)
    filters = []

    # Add account filtering if account_id is provided
    if account_id:
        account_filter = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [account_id]}}
        filters.append(account_filter)

    # Add tag filtering if provided
    if tag_filters:
        for tag_filter in tag_filters:
            tag_filter_dict = {
                "Tags": {
                    "Key": tag_filter["Key"],
                    "Values": tag_filter["Values"],
                    "MatchOptions": ["EQUALS"],
                }
            }
            filters.append(tag_filter_dict)

    # Combine filters appropriately
    filter_param: Optional[Dict[str, Any]] = None
    if len(filters) == 1:
        filter_param = filters[0]
    elif len(filters) > 1:
        filter_param = {"And": filters}
    kwargs = {}
    if filter_param:
        kwargs["Filter"] = filter_param

    end_date = date.today()
    start_date = (end_date - timedelta(days=180)).replace(day=1)
    account_id = get_account_id(session)
    profile = session.profile_name

    monthly_costs = []

    try:
        monthly_data = ce.get_cost_and_usage(
            TimePeriod={
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            **kwargs,
        )
        for period in monthly_data.get("ResultsByTime", []):
            month = datetime.strptime(period["TimePeriod"]["Start"], "%Y-%m-%d").strftime("%b %Y")
            cost = float(period["Total"]["UnblendedCost"]["Amount"])
            monthly_costs.append((month, cost))
    except Exception as e:
        console.log(f"[yellow]Error getting monthly trend data: {e}[/]")
        if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
            handle_cost_explorer_error(e, profile)
        monthly_costs = []

    return {
        "monthly_costs": monthly_costs,
        "account_id": account_id,
        "profile": profile,
    }


def get_batch_cost_data(
    sessions: List[Tuple[Session, str]],
    time_range: Optional[int] = None,
    tag: Optional[List[str]] = None,
    max_workers: int = MAX_CONCURRENT_COST_CALLS,
) -> Dict[str, CostData]:
    """
    Enterprise batch cost data retrieval with parallel processing.

    Optimizes Cost Explorer API calls by processing multiple accounts concurrently
    while respecting AWS rate limits and providing circuit breaker protection.

    Args:
        sessions: List of (session, profile_name) tuples for batch processing
        time_range: Optional time range in days for cost data
        tag: Optional list of tags for filtering
        max_workers: Maximum concurrent API calls (default: 10 for rate limiting)

    Returns:
        Dictionary mapping profile_name to CostData results

    Performance: 5-10x faster than sequential processing for 10+ accounts
    """
    if not sessions:
        return {}

    console.log(f"[blue]Enterprise batch processing: {len(sessions)} accounts with {max_workers} workers[/]")
    start_time = time.time()
    results = {}

    # Thread-safe result collection
    results_lock = threading.Lock()

    def _process_single_cost_data(session_info: Tuple[Session, str]) -> Tuple[str, CostData]:
        """Process cost data for a single session."""
        session, profile_name = session_info
        try:
            # Extract account ID from profile if it's in Organizations API format (profile@accountId)
            account_id = None
            if "@" in profile_name:
                _, account_id = profile_name.split("@", 1)

            cost_data = get_cost_data(session, time_range, tag, False, profile_name, account_id)
            return profile_name, cost_data
        except Exception as e:
            console.log(f"[yellow]Batch cost data error for {profile_name}: {str(e)[:50]}[/]")
            # Return empty cost data structure for failed accounts
            return profile_name, {
                "account_id": get_account_id(session) or "unknown",
                "current_month": 0.0,
                "last_month": 0.0,
                "current_month_cost_by_service": [],
                "budgets": [],
                "current_period_name": "Current month's cost",
                "previous_period_name": "Last month's cost",
                "time_range": time_range,
                "current_period_start": "",
                "current_period_end": "",
                "previous_period_start": "",
                "previous_period_end": "",
                "monthly_costs": None,
                "costs_by_service": {},
            }

    # Execute batch processing with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_profile = {
            executor.submit(_process_single_cost_data, session_info): session_info[1] for session_info in sessions
        }

        processed = 0
        for future in as_completed(future_to_profile, timeout=120):  # 2 minute timeout for batch
            try:
                profile_name, cost_data = future.result(timeout=30)  # 30s per account

                with results_lock:
                    results[profile_name] = cost_data
                    processed += 1

                if processed % 5 == 0:  # Progress logging every 5 accounts
                    console.log(f"[green]Batch progress: {processed}/{len(sessions)} accounts processed[/]")

            except Exception as e:
                profile_name = future_to_profile[future]
                console.log(f"[yellow]Batch timeout for {profile_name}: {str(e)[:50]}[/]")
                # Continue processing other accounts

    execution_time = time.time() - start_time
    console.log(
        f"[green]✅ Batch cost processing completed: {len(results)}/{len(sessions)} accounts in {execution_time:.1f}s[/]"
    )
    console.log(f"[dim]Performance: {len(sessions) / execution_time:.1f} accounts/second[/]")

    return results


def get_cost_data(
    session: Session,
    time_range: Optional[int] = None,
    tag: Optional[List[str]] = None,
    get_trend: bool = False,
    profile_name: Optional[str] = None,
    account_id: Optional[str] = None,
    cost_metric: str = "UnblendedCost",
    month: Optional[str] = None,
) -> CostData:
    """
    Get cost data for an AWS account.

    Args:
        session: The boto3 session to use
        time_range: Optional time range in days for cost data (default: current month)
        tag: Optional list of tags in "Key=Value" format to filter resources.
        get_trend: Optional boolean to get trend data for last 6 months (default).
        profile_name: Optional AWS profile name for enhanced error messaging
        account_id: Optional account ID to filter costs to specific account (multi-account support)
        cost_metric: Cost metric to use for cost queries. Options:
            - 'UnblendedCost': Technical analysis (default, matches AWS Console)
            - 'BlendedCost': Multi-account allocation
            - 'AmortizedCost': Financial reporting (with RI/SP amortization)
        month: Optional specific month to analyze (YYYY-MM format). Overrides time_range.

    """
    ce = session.client("ce")
    budgets = session.client("budgets", region_name="ap-southeast-2")
    today = date.today()

    tag_filters: List[Dict[str, Any]] = []
    if tag:
        for t in tag:
            key, value = t.split("=", 1)
            tag_filters.append({"Key": key, "Values": [value]})

    # Build filter parameters for Cost Explorer API
    filters = []

    # Add account filtering if account_id is provided (critical for multi-account scenarios)
    if account_id:
        account_filter = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [account_id]}}
        filters.append(account_filter)
        # REMOVED: Redundant account filtering log (consolidated in finops.py)

    # Add tag filtering if provided
    if tag_filters:
        for tag_filter in tag_filters:
            tag_filter_dict = {
                "Tags": {
                    "Key": tag_filter["Key"],
                    "Values": tag_filter["Values"],
                    "MatchOptions": ["EQUALS"],
                }
            }
            filters.append(tag_filter_dict)

    # Combine filters appropriately
    filter_param: Optional[Dict[str, Any]] = None
    if len(filters) == 1:
        filter_param = filters[0]
    elif len(filters) > 1:
        filter_param = {"And": filters}
    kwargs = {}
    if filter_param:
        kwargs["Filter"] = filter_param

    # Handle specific month parameter (highest priority, overrides time_range)
    # ADLC v3.0.0: Refactored to use DateRangeCalculator (DRY compliance)
    if month:
        try:
            # Use centralized DateRangeCalculator for consistent date logic
            current_range = DateRangeCalculator.month_range(month)
            start_date = current_range.start
            end_date = current_range.end

            # Previous period for MoM comparison
            previous_range = DateRangeCalculator.previous_month(current_range)
            previous_period_start = previous_range.start
            previous_period_end = previous_range.end

            console.log(f"[cyan]📅 Analyzing specific month: {month} ({current_range.days} days)[/]")
            console.log(f"[dim]   Period: {start_date.isoformat()} to {end_date.isoformat()} (exclusive)[/]")

        except ValueError as e:
            console.log(f"[red]❌ {e}[/]")
            raise

    elif time_range:
        # ADLC v3.0.0: Use DateRangeCalculator for consistent UTC-first logic
        current_range = DateRangeCalculator.days_range(time_range, reference_date=today)
        start_date = current_range.start
        end_date = current_range.end  # Already exclusive (tomorrow)
        previous_range = DateRangeCalculator.previous_period(current_range)
        previous_period_start = previous_range.start
        previous_period_end = previous_range.end

    else:
        # CRITICAL MATHEMATICAL FIX: Equal period comparisons for accurate trends
        # Problem: Partial current month vs full previous month = misleading trends
        # Solution: Same-day comparisons or complete month comparisons

        start_date = today.replace(day=1)
        end_date = today

        # Detect if we're dealing with a partial month that could cause misleading trends
        days_into_month = today.day
        is_partial_month = days_into_month <= 5  # First 5 days are considered "partial"

        if is_partial_month:
            console.log(f"[yellow]⚠️  Partial month detected ({days_into_month} days into {today.strftime('%B')})[/]")
            console.log(
                f"[dim yellow]   Trend calculations may show extreme percentages due to limited current data[/]"
            )
            console.log(f"[dim yellow]   Consider using full month comparisons for accurate trend analysis[/]")

        # Current period: start of month to today (include today with +1 day for AWS CE)
        end_date = today + timedelta(days=1)  # AWS Cost Explorer end date is exclusive

        # Previous period: Use same day-of-month from previous month for better comparison
        # This provides more meaningful trends when current month is partial
        if is_partial_month and days_into_month > 1:
            # For partial months, compare same number of days from previous month
            previous_month_same_day = today.replace(day=1) - timedelta(days=1)  # Last day of prev month
            previous_month_start = previous_month_same_day.replace(day=1)

            # Calculate same day of previous month, handling month boundaries
            try:
                previous_month_target_day = previous_month_start.replace(day=today.day)
                previous_period_start = previous_month_start
                previous_period_end = previous_month_target_day + timedelta(days=1)  # Exclusive end

                console.log(
                    f"[cyan]📊 Using equal-day comparison: {days_into_month} days from current vs previous month[/]"
                )

            except ValueError:
                # Handle cases where previous month doesn't have the same day (e.g., Feb 30)
                previous_period_end = previous_month_same_day + timedelta(days=1)
                previous_period_start = previous_period_end.replace(day=1)
        else:
            # Standard full previous month comparison
            previous_period_end = start_date - timedelta(days=1)
            previous_period_start = previous_period_end.replace(day=1)

    # Get account ID with enhanced error handling for AWS-2 accuracy validation
    try:
        account_id = get_account_id(session)
        if not account_id:
            account_id = "unknown"
    except Exception as account_error:
        console.print(f"[yellow]Warning: Could not retrieve account ID: {account_error}[/yellow]")
        account_id = "unknown"

    try:
        this_period = ce.get_cost_and_usage(
            TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
            Granularity="MONTHLY",
            Metrics=[cost_metric],
            **kwargs,
        )
    except Exception as e:
        console.log(f"[yellow]Error getting current period cost: {e}[/]")
        if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
            handle_cost_explorer_error(e, profile_name)
        this_period = {"ResultsByTime": [{"Total": {cost_metric: {"Amount": 0}}}]}

    try:
        previous_period = ce.get_cost_and_usage(
            TimePeriod={
                "Start": previous_period_start.isoformat(),
                "End": previous_period_end.isoformat(),
            },
            Granularity="MONTHLY",
            Metrics=[cost_metric],
            **kwargs,
        )
    except Exception as e:
        console.log(f"[yellow]Error getting previous period cost: {e}[/]")
        if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
            handle_cost_explorer_error(e, profile_name)
        previous_period = {"ResultsByTime": [{"Total": {cost_metric: {"Amount": 0}}}]}

    try:
        current_period_cost_by_service = ce.get_cost_and_usage(
            TimePeriod={"Start": start_date.isoformat(), "End": end_date.isoformat()},
            Granularity="DAILY",
            Metrics=[cost_metric],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            **kwargs,
        )
    except Exception as e:
        console.log(f"[yellow]Error getting current period cost by service: {e}[/]")
        if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
            handle_cost_explorer_error(e, profile_name)
        current_period_cost_by_service = {"ResultsByTime": [{"Groups": []}]}

    # Aggregate cost by service across all days
    aggregated_service_costs: Dict[str, float] = defaultdict(float)

    for result in current_period_cost_by_service.get("ResultsByTime", []):
        for group in result.get("Groups", []):
            service = group["Keys"][0]
            amount = float(group["Metrics"][cost_metric]["Amount"])
            aggregated_service_costs[service] += amount

    # Reformat into groups by service
    aggregated_groups = [
        {"Keys": [service], "Metrics": {cost_metric: {"Amount": str(amount)}}}
        for service, amount in aggregated_service_costs.items()
    ]

    budgets_data: List[BudgetInfo] = []
    try:
        response = budgets.describe_budgets(AccountId=account_id)
        for budget in response["Budgets"]:
            budgets_data.append(
                {
                    "name": budget["BudgetName"],
                    "limit": float(budget["BudgetLimit"]["Amount"]),
                    "actual": float(budget["CalculatedSpend"]["ActualSpend"]["Amount"]),
                    "forecast": float(budget["CalculatedSpend"].get("ForecastedSpend", {}).get("Amount", 0.0)) or None,
                }
            )
    except Exception as e:
        pass

    current_period_cost = 0.0
    for period in this_period.get("ResultsByTime", []):
        if "Total" in period and cost_metric in period["Total"]:
            current_period_cost += float(period["Total"][cost_metric]["Amount"])

    previous_period_cost = 0.0
    for period in previous_period.get("ResultsByTime", []):
        if "Total" in period and cost_metric in period["Total"]:
            previous_period_cost += float(period["Total"][cost_metric]["Amount"])

    current_period_name = f"Current {time_range} days cost" if time_range else "Current month's cost"
    previous_period_name = f"Previous {time_range} days cost" if time_range else "Last month's cost"

    # Create costs_by_service dictionary for easy service lookup
    costs_by_service = {}
    for service, amount in aggregated_service_costs.items():
        if amount > 0.001:  # Filter out negligible costs
            costs_by_service[service] = amount

    # v1.1.20: Disabled EC2 aggregation - preserve separate EC2-Instances and EC2-Other (AWS Console parity)
    # costs_by_service = aggregate_ec2_costs(costs_by_service)

    # Calculate period metadata for trend context with enhanced accuracy assessment
    current_period_days = (end_date - start_date).days
    previous_period_days = (previous_period_end - previous_period_start).days
    days_difference = abs(current_period_days - previous_period_days)
    is_partial_comparison = days_difference > 5

    # ENHANCED RELIABILITY ASSESSMENT: Consider MCP validation success in trend reliability
    trend_reliability = "high"
    if is_partial_comparison:
        if days_difference > 15:
            trend_reliability = "low"
        elif days_difference > 10:
            trend_reliability = "medium"
        else:
            # Moderate difference - reliability depends on validation accuracy
            trend_reliability = "medium_with_validation_support"

    # Enhanced period information for trend analysis
    # Calculate is_partial_month for metadata (AWS-2 accuracy enhancement)
    today = date.today()
    days_into_month = today.day
    is_partial_month = days_into_month <= 5  # First 5 days are considered "partial"

    period_metadata = {
        "current_days": current_period_days,
        "previous_days": previous_period_days,
        "days_difference": days_difference,
        "is_partial_comparison": is_partial_comparison,
        "comparison_type": "equal_day_comparison" if is_partial_comparison else "standard_month_comparison",
        "trend_reliability": trend_reliability,
        "period_alignment_strategy": "equal_days"
        if is_partial_comparison and days_into_month > 1
        else "standard_monthly",
        "supports_mcp_validation": True,  # This data structure supports MCP cross-validation
    }

    return {
        "account_id": account_id,
        "current_month": current_period_cost,
        "last_month": previous_period_cost,
        "current_month_cost_by_service": aggregated_groups,
        "costs_by_service": costs_by_service,  # Added for multi_dashboard compatibility
        "budgets": budgets_data,
        "current_period_name": current_period_name,
        "previous_period_name": previous_period_name,
        "time_range": time_range,
        "current_period_start": start_date.isoformat(),
        "current_period_end": end_date.isoformat(),
        "previous_period_start": previous_period_start.isoformat(),
        "previous_period_end": previous_period_end.isoformat(),
        "monthly_costs": None,
        "period_metadata": period_metadata,  # Added for intelligent trend analysis
    }


def get_quarterly_cost_data(
    session: Session,
    profile_name: Optional[str] = None,
    account_id: Optional[str] = None,
) -> Dict[str, float]:
    """
    Get quarterly cost data for enhanced FinOps trend analysis.

    Retrieves cost data for the last complete quarter (3 months) to provide
    strategic quarterly context for financial planning and trend analysis.

    Args:
        session: The boto3 session to use
        profile_name: Optional AWS profile name for enhanced error messaging
        account_id: Optional account ID to filter costs to specific account

    Returns:
        Dictionary with service names as keys and quarterly costs as values
    """
    ce = session.client("ce")
    today = date.today()

    # Calculate last quarter date range
    # Go back 3 months for quarterly analysis
    quarterly_end_date = today.replace(day=1) - timedelta(days=1)  # Last day of previous month
    quarterly_start_date = (quarterly_end_date.replace(day=1) - timedelta(days=90)).replace(day=1)

    # Build filters for quarterly analysis
    filters = []
    if account_id:
        account_filter = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [account_id]}}
        filters.append(account_filter)

    # Combine filters if needed
    filter_param: Optional[Dict[str, Any]] = None
    if len(filters) == 1:
        filter_param = filters[0]
    elif len(filters) > 1:
        filter_param = {"And": filters}

    kwargs = {}
    if filter_param:
        kwargs["Filter"] = filter_param

    try:
        quarterly_period_cost_by_service = ce.get_cost_and_usage(
            TimePeriod={
                "Start": quarterly_start_date.isoformat(),
                "End": (quarterly_end_date + timedelta(days=1)).isoformat(),  # Exclusive end
            },
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            **kwargs,
        )
    except Exception as e:
        console.log(f"[yellow]Warning: Unable to retrieve quarterly cost data: {e}[/]")
        if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
            handle_cost_explorer_error(e, profile_name)
        return {}

    # Aggregate quarterly costs by service across the 3-month period
    quarterly_service_costs: Dict[str, float] = defaultdict(float)

    for result in quarterly_period_cost_by_service.get("ResultsByTime", []):
        for group in result.get("Groups", []):
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            quarterly_service_costs[service] += amount

    # Filter out negligible costs and convert to regular dict
    filtered_quarterly_costs = {}
    for service, amount in quarterly_service_costs.items():
        if amount > 0.001:  # Filter out negligible costs
            filtered_quarterly_costs[service] = amount

    # v1.1.20: Disabled EC2 aggregation - preserve separate EC2-Instances and EC2-Other (AWS Console parity)
    # filtered_quarterly_costs = aggregate_ec2_costs(filtered_quarterly_costs)

    console.log(f"[cyan]📊 Retrieved quarterly cost data for {len(filtered_quarterly_costs)} services[/]")
    return filtered_quarterly_costs


def aggregate_ec2_costs(costs_by_service: Dict[str, float]) -> Dict[str, float]:
    """
    Aggregate EC2-related services into a single 'Amazon Elastic Compute Cloud' entry.

    AWS Cost Explorer returns EC2 costs split across multiple service names:
    - "Amazon Elastic Compute Cloud - Compute" (EC2 instances)
    - "EC2 - Other" (EBS volumes, snapshots, data transfer, etc.)

    This function combines them for cleaner dashboard display.

    Args:
        costs_by_service: Dictionary mapping service names to cost amounts

    Returns:
        Dictionary with EC2 services aggregated under "Amazon Elastic Compute Cloud"
    """
    # EC2 service name variations to aggregate
    ec2_service_variants = {
        "Amazon Elastic Compute Cloud - Compute",
        "EC2 - Other",
        "EC2-Instances(Elastic Compute Cloud - Compute)",
        "Amazon Elastic Compute Cloud",
        "Elastic Compute Cloud",
    }

    ec2_total = 0.0
    non_ec2_services: Dict[str, float] = {}

    for service_name, cost_amount in costs_by_service.items():
        # Aggregate any service with "EC2" in the name or exact variant matches
        if service_name in ec2_service_variants or "EC2" in service_name:
            ec2_total += cost_amount
        else:
            non_ec2_services[service_name] = cost_amount

    # Build result with aggregated EC2
    result = {}
    if ec2_total > 0:
        result["Amazon Elastic Compute Cloud"] = ec2_total

    # Add all non-EC2 services
    result.update(non_ec2_services)

    return result


def process_service_costs(
    cost_data: CostData,
    top_n: int = 5,
) -> Tuple[List[str], List[Tuple[str, float]], float, float]:
    """
    Process and format service costs from cost data with Top-N + Others support.

    v1.1.23: Enhanced to support Top-N display with "Others" aggregation for
    cost reconciliation (Issue #1 + #2).

    Args:
        cost_data: Cost data dictionary from AWS Cost Explorer
        top_n: Number of top services to display (default: 5)

    Returns:
        Tuple of (service_costs_formatted, service_cost_data, others_total, grand_total)
        - service_costs_formatted: List of formatted strings for display
        - service_cost_data: List of (service_name, cost) tuples
        - others_total: Sum of costs for services beyond top N
        - grand_total: Total cost across all services
    """
    from runbooks.finops.helpers import format_top_n_with_others

    service_costs: List[str] = []
    service_cost_data: List[Tuple[str, float]] = []

    # Collect service costs
    services_dict = {}
    for group in cost_data["current_month_cost_by_service"]:
        if "Keys" in group and "Metrics" in group:
            service_name = group["Keys"][0]
            # v1.2.3: Dynamic metric detection - supports UnblendedCost (default), BlendedCost, AmortizedCost
            metrics = group["Metrics"]
            for metric_key in ["UnblendedCost", "BlendedCost", "AmortizedCost"]:
                if metric_key in metrics:
                    cost_amount = float(metrics[metric_key]["Amount"])
                    break
            else:
                cost_amount = 0.0
            if cost_amount > 0.001:
                services_dict[service_name] = cost_amount

    if not services_dict:
        service_costs.append("No costs associated with this account")
        return service_costs, service_cost_data, 0.0, 0.0

    # Use helper to get Top N + Others
    top_n_list, others_total, grand_total = format_top_n_with_others(services_dict, top_n=top_n)

    # Format top N services for display
    for service_name, cost_amount, percentage in top_n_list:
        service_costs.append(f"{service_name}: ${cost_amount:.2f}")
        service_cost_data.append((service_name, cost_amount))

    return service_costs, service_cost_data, others_total, grand_total


def format_budget_info(budgets: List[BudgetInfo]) -> List[str]:
    """Format budget information for display with enhanced error handling and concise icons."""
    budget_info: List[str] = []

    # Check if this is an access denied case (common with read-only profiles)
    if budgets and len(budgets) == 1:
        first_budget = budgets[0]
        if isinstance(first_budget, dict):
            # Check for access denied pattern
            if first_budget.get("name", "").lower() in ["access denied", "permission denied", "n/a"]:
                budget_info.append("ℹ️  Budget data unavailable")
                budget_info.append("(Read-only profile)")
                budget_info.append("")
                budget_info.append("💡 For budget access:")
                budget_info.append("Add budgets:ViewBudget")
                budget_info.append("policy to profile")
                return budget_info

    # Enhanced budget formatting with concise icons and status
    for budget in budgets:
        # Calculate budget utilization for status determination
        utilization = (budget["actual"] / budget["limit"]) * 100 if budget["limit"] > 0 else 0

        # Determine status icon and color based on utilization
        if utilization >= 100:
            status_icon = "🚨"  # Over budget - critical
            status_color = "bright_red"
        elif utilization >= 85:
            status_icon = "⚠️"  # Near limit - warning
            status_color = "orange1"
        elif utilization >= 70:
            status_icon = "🟡"  # Moderate usage - caution
            status_color = "yellow"
        else:
            status_icon = "✅"  # Under budget - good
            status_color = "green"

        # Format budget name (shortened for display)
        display_name = budget["name"].replace(" Budget", "").replace("Budget", "").strip()
        if len(display_name) > 15:
            display_name = display_name[:12] + "..."

        # Concise budget display with icons
        budget_info.append(f"{status_icon} [{status_color}]{display_name}[/]")
        budget_info.append(f"💰 ${budget['actual']:.0f}/${budget['limit']:.0f} ({utilization:.0f}%)")

        # Add forecast only if significantly different from actual
        if budget["forecast"] is not None and abs(budget["forecast"] - budget["actual"]) > (budget["actual"] * 0.1):
            trend_icon = "📈" if budget["forecast"] > budget["actual"] else "📉"
            budget_info.append(f"{trend_icon} Est: ${budget['forecast']:.0f}")

    if not budget_info:
        budget_info.append("ℹ️  No budgets configured")
        budget_info.append("💡 Create a budget to")
        budget_info.append("track spending limits")

    return budget_info


def calculate_quarterly_enhanced_trend(
    current: float,
    previous: float,
    quarterly: float,
    current_days: Optional[int] = None,
    previous_days: Optional[int] = None,
) -> str:
    """
    Calculate trend with quarterly financial intelligence for strategic decision making.

    Enhanced FinOps trend analysis that combines monthly operational trends with quarterly
    strategic context to provide executive-ready financial intelligence.

    Args:
        current: Current period cost
        previous: Previous period cost
        quarterly: Last quarter (3-month) average cost
        current_days: Number of days in current period
        previous_days: Number of days in previous period

    Returns:
        Strategic trend indicator with quarterly context
    """
    # Start with existing monthly trend logic
    monthly_trend = calculate_trend_with_context(current, previous, current_days, previous_days)

    # Handle edge case where trend calculation returns "0.0% ⚠️"
    if "0.0%" in monthly_trend and "⚠️" in monthly_trend:
        # This likely means partial period comparison issue - provide clearer message
        if current_days and previous_days and abs(current_days - previous_days) > 5:
            return "⚠️ Partial data"
        elif previous == 0 and current == 0:
            return "→ No activity"
        elif previous == 0 and current > 0:
            return "↑ New costs"
        else:
            # Recalculate with simplified logic
            if previous > 0:
                change_percent = ((current - previous) / previous) * 100
                if abs(change_percent) < 0.1:
                    return "→ Stable"
                elif change_percent > 0:
                    return f"↑ {change_percent:.1f}%"
                else:
                    return f"↓ {abs(change_percent):.1f}%"

    # Add quarterly strategic context if available and quarterly data is meaningful
    if quarterly > 0.01:  # Only use quarterly if significant amount
        # Calculate quarterly average for monthly comparison
        quarterly_monthly_avg = quarterly / 3.0  # 3-month average

        # Compare current month against quarterly average
        if current > 0.01:  # Only if current has significant amount
            quarterly_variance = ((current - quarterly_monthly_avg) / quarterly_monthly_avg) * 100

            # Strategic quarterly indicators
            if abs(quarterly_variance) < 10:  # Within 10% of quarterly average
                quarterly_context = "📊"  # Consistent with quarterly patterns
            elif quarterly_variance > 25:  # Significantly above quarterly average
                quarterly_context = "📈"  # Above quarterly baseline
            elif quarterly_variance < -25:  # Significantly below quarterly average
                quarterly_context = "📉"  # Below quarterly baseline
            else:
                quarterly_context = "📊"  # Normal quarterly variation

            # Combine monthly operational trend with quarterly strategic context
            return f"{quarterly_context} {monthly_trend}"

    # Fallback to standard monthly trend if no quarterly data or not meaningful
    return monthly_trend


def format_cost_with_precision(amount: float, context: str = "dashboard") -> str:
    """
    Format cost with context-aware precision for consistent display.

    Args:
        amount: Cost amount to format
        context: Display context ('executive', 'detailed', 'dashboard')

    Returns:
        Formatted cost string with appropriate precision
    """
    if context == "executive":
        # Executive summary - round to nearest dollar for clarity
        return f"${amount:,.0f}"
    elif context == "detailed":
        # Detailed analysis - show full precision
        return f"${amount:,.2f}"
    else:
        # Default dashboard - 2 decimal places
        return f"${amount:,.2f}"


def calculate_trend_with_context(
    current: float, previous: float, current_days: Optional[int] = None, previous_days: Optional[int] = None
) -> str:
    """
    Calculate trend with statistical context and confidence, handling partial period comparisons.

    CRITICAL MATHEMATICAL FIX: Addresses the business-critical issue where partial current month
    (e.g., September 1-2: $2.50) was compared against full previous month (August 1-31: $155.00),
    resulting in misleading -98.4% trend calculations that could cause incorrect business decisions.

    Args:
        current: Current period cost
        previous: Previous period cost
        current_days: Number of days in current period (for partial period detection)
        previous_days: Number of days in previous period (for partial period detection)

    Returns:
        Trend string with appropriate context and partial period warnings
    """
    if previous == 0:
        if current == 0:
            return "No change (both periods $0)"
        else:
            return "New spend (no historical data)"

    # Detect partial period issues and apply smart normalization
    partial_period_issue = False
    normalized_change_percent = None
    normalization_applied = False

    if current_days and previous_days:
        if abs(current_days - previous_days) > 5:  # More than 5 days difference
            partial_period_issue = True

            # Apply smart normalization for partial month comparisons
            if current_days < previous_days:
                # Current month is partial, previous is full - normalize previous month
                normalization_factor = current_days / previous_days
                adjusted_previous = previous * normalization_factor
                if adjusted_previous > 0:
                    normalized_change_percent = ((current - adjusted_previous) / adjusted_previous) * 100
                    normalization_applied = True
                    from ..common.rich_utils import console

                    console.log(
                        f"[dim yellow]📊 Trend normalization: partial current ({current_days} days) vs full previous ({previous_days} days)[/]"
                    )
                    console.log(
                        f"[dim yellow]   Adjusted comparison: ${current:.2f} vs ${adjusted_previous:.2f} (factor: {normalization_factor:.2f})[/]"
                    )

            elif current_days > previous_days:
                # Previous month is partial, current is full - normalize current month
                normalization_factor = previous_days / current_days
                adjusted_current = current * normalization_factor
                if previous > 0:
                    normalized_change_percent = ((adjusted_current - previous) / previous) * 100
                    normalization_applied = True
                    from ..common.rich_utils import console

                    console.log(
                        f"[dim yellow]📊 Trend normalization: full current ({current_days} days) vs partial previous ({previous_days} days)[/]"
                    )
                    console.log(
                        f"[dim yellow]   Adjusted comparison: ${adjusted_current:.2f} vs ${previous:.2f} (factor: {normalization_factor:.2f})[/]"
                    )

    # Use normalized change if available, otherwise calculate basic percentage change
    if normalization_applied and normalized_change_percent is not None:
        change_percent = normalized_change_percent
        # Add indicator that normalization was applied
        normalization_indicator = " 📏"
    else:
        # v1.1.31: Defensive guard against division by zero (edge case safety)
        if previous > 0:
            change_percent = ((current - previous) / previous) * 100
        else:
            # Should not reach here due to early return at line 1160, but defensive
            change_percent = 0.0 if current == 0 else None
        normalization_indicator = ""

    # v1.1.31: Handle None case (new spend with no historical baseline)
    if change_percent is None:
        return f"↑ New (no baseline){normalization_indicator}"

    # FIXED: Show meaningful percentage trends instead of generic messages
    if abs(change_percent) < 0.01:  # Less than 0.01%
        if current == previous:
            return f"→ 0.0%{normalization_indicator}"  # Show actual zero change percentage
        elif abs(current - previous) < 0.01:  # Very small absolute difference
            return f"→ <0.1%{normalization_indicator}"  # Show near-zero change with percentage
        else:
            # Show actual small change with precise percentage
            return f"{'↑' if change_percent > 0 else '↓'} {abs(change_percent):.2f}%{normalization_indicator}"

    # Handle partial period comparisons with clean display
    if partial_period_issue and not normalization_applied:
        # Only show warnings if normalization wasn't applied (fallback case)
        if abs(change_percent) > 50:
            return "⚠️ Trend not reliable (partial data)"
        else:
            base_trend = f"↑ {change_percent:.1f}%" if change_percent > 0 else f"↓ {abs(change_percent):.1f}%"
            return f"{base_trend} ⚠️"

    # Standard trend analysis for equal periods
    if abs(change_percent) > 90:
        if change_percent > 0:
            return f"↑ {change_percent:.1f}% (significant increase - verify){normalization_indicator}"
        else:
            return f"↓ {abs(change_percent):.1f}% (significant decrease - verify){normalization_indicator}"
    elif abs(change_percent) < 1:
        return f"→ Stable (< 1% change){normalization_indicator}"
    else:
        if change_percent > 0:
            return f"↑ {change_percent:.1f}%{normalization_indicator}"
        else:
            return f"↓ {abs(change_percent):.1f}%{normalization_indicator}"


def format_ec2_summary(ec2_data: EC2Summary) -> List[str]:
    """Format EC2 instance summary with enhanced visual hierarchy."""
    ec2_summary_text: List[str] = []

    # Enhanced state formatting with icons and context
    state_config = {
        "running": {"color": "bright_green", "icon": "🟢", "priority": 1},
        "stopped": {"color": "bright_yellow", "icon": "🟡", "priority": 2},
        "terminated": {"color": "dim red", "icon": "🔴", "priority": 4},
        "pending": {"color": "bright_cyan", "icon": "🔵", "priority": 3},
        "stopping": {"color": "yellow", "icon": "🟠", "priority": 3},
    }

    # Sort by priority and then by state name
    sorted_states = sorted(
        [(state, count) for state, count in ec2_data.items() if count > 0],
        key=lambda x: (state_config.get(x[0], {"priority": 99})["priority"], x[0]),
    )

    total_instances = sum(count for _, count in sorted_states)

    if sorted_states:
        # Header with total count
        ec2_summary_text.append(f"[bright_cyan]📊 EC2 Instances ({total_instances} total)[/bright_cyan]")

        # Individual states with enhanced styling
        for state, count in sorted_states:
            config = state_config.get(state, {"color": "white", "icon": "⚪", "priority": 99})
            percentage = (count / total_instances * 100) if total_instances > 0 else 0

            ec2_summary_text.append(
                f"  {config['icon']} [{config['color']}]{state.title()}: {count}[/{config['color']}] "
                f"[dim]({percentage:.1f}%)[/dim]"
            )
    else:
        ec2_summary_text = ["[dim]📭 No EC2 instances found[/dim]"]

    return ec2_summary_text


def change_in_total_cost(current_period: float, previous_period: float) -> Optional[float]:
    """Calculate the  change in total cost between current period and previous period."""
    if abs(previous_period) < 0.01:
        if abs(current_period) < 0.01:
            return 0.00  # No change if both periods are zero
        return None  # Undefined percentage change if previous is zero but current is non-zero

    # Calculate percentage change
    return ((current_period - previous_period) / previous_period) * 100.00


def export_to_csv(
    data: List[ProfileData],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
    include_dual_metrics: bool = False,
) -> Optional[str]:
    """Export dashboard data to a CSV file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.csv"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename

        previous_period_header = f"Cost for period\n({previous_period_dates})"
        current_period_header = f"Cost for period\n({current_period_dates})"

        with open(output_filename, "w", newline="") as csvfile:
            # Base fieldnames
            fieldnames = [
                "CLI Profile",
                "AWS Account ID",
                previous_period_header,
                current_period_header,
            ]

            # Add dual-metric columns if requested
            if include_dual_metrics:
                fieldnames.extend(
                    [
                        f"AmortizedCost {current_period_header}",
                        f"AmortizedCost {previous_period_header}",
                        "Metric Variance ($)",
                        "Metric Variance (%)",
                        "Cost By Service (UnblendedCost)",
                        "Cost By Service (AmortizedCost)",
                    ]
                )
            else:
                fieldnames.append("Cost By Service")

            fieldnames.extend(
                [
                    "Budget Status",
                    "EC2 Instances",
                ]
            )

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Enhanced error handling for service costs access
                try:
                    service_costs = row.get("service_costs", [])
                    if isinstance(service_costs, list) and service_costs:
                        services_data = "\n".join([f"{service}: ${cost:.2f}" for service, cost in service_costs])
                    else:
                        services_data = "No service costs"
                except (KeyError, TypeError, AttributeError) as e:
                    console.print(f"[yellow]Warning: Could not process service costs: {e}[/]")
                    services_data = "Service costs unavailable"

                # Enhanced error handling for budget_info access
                try:
                    budget_info = row.get("budget_info", [])
                    if isinstance(budget_info, list) and budget_info:
                        budgets_data = "\n".join(str(item) for item in budget_info)
                    else:
                        budgets_data = "No budgets"
                except (KeyError, TypeError, AttributeError) as e:
                    console.print(f"[yellow]Warning: Could not process budget info: {e}[/]")
                    budgets_data = "Budget info unavailable"

                # Enhanced error handling for EC2 summary access
                try:
                    ec2_summary = row.get("ec2_summary", {})
                    if isinstance(ec2_summary, dict) and ec2_summary:
                        ec2_data_summary = "\n".join(
                            [f"{state}: {count}" for state, count in ec2_summary.items() if count > 0]
                        )
                    else:
                        ec2_data_summary = "No EC2 instances"
                except (KeyError, TypeError, AttributeError) as e:
                    console.print(f"[yellow]Warning: Could not process EC2 summary: {e}[/]")
                    ec2_data_summary = "EC2 summary unavailable"

                # Enhanced error handling for writerow with safe field access
                try:
                    # Base row data
                    row_data = {
                        "CLI Profile": row.get("profile_name", "Unknown"),
                        "AWS Account ID": row.get("account_id", "Unknown"),
                        previous_period_header: row.get("previous_month_formatted", "N/A"),
                        current_period_header: row.get("current_month_formatted", "N/A"),
                    }

                    # Add dual-metric data if requested
                    if include_dual_metrics:
                        # Calculate variance for dual-metric display
                        current_unblended = row.get("current_month", 0)
                        current_amortized = row.get("current_month_amortized", current_unblended)
                        previous_amortized = row.get("previous_month_amortized", row.get("previous_month", 0))
                        variance = abs(current_unblended - current_amortized)
                        variance_pct = (variance / current_amortized * 100) if current_amortized > 0 else 0

                        # Format amortized service costs
                        amortized_services_data = "No amortized service costs"
                        if row.get("service_costs_amortized"):
                            amortized_services_data = "\n".join(
                                [f"{service}: ${cost:.2f}" for service, cost in row["service_costs_amortized"]]
                            )

                        row_data.update(
                            {
                                f"AmortizedCost {current_period_header}": f"${current_amortized:.2f}",
                                f"AmortizedCost {previous_period_header}": f"${previous_amortized:.2f}",
                                "Metric Variance ($)": f"${variance:.2f}",
                                "Metric Variance (%)": f"{variance_pct:.2f}%",
                                "Cost By Service (UnblendedCost)": services_data or "No costs",
                                "Cost By Service (AmortizedCost)": amortized_services_data,
                            }
                        )
                    else:
                        row_data["Cost By Service"] = services_data or "No costs"

                    # Add common fields
                    row_data.update(
                        {
                            "Budget Status": budgets_data or "No budgets",
                            "EC2 Instances": ec2_data_summary or "No instances",
                        }
                    )

                    writer.writerow(row_data)
                except (KeyError, TypeError) as e:
                    console.print(f"[yellow]Warning: Could not write CSV row: {e}[/]")
                    # Write a minimal error row to maintain CSV structure
                    writer.writerow(
                        {
                            "CLI Profile": "Error",
                            "AWS Account ID": "Error",
                            previous_period_header: "Error",
                            current_period_header: "Error",
                            "Cost By Service": f"Row processing error: {e}",
                            "Budget Status": "Error",
                            "EC2 Instances": "Error",
                        }
                    )
        console.print(f"[bright_green]Exported dashboard data to {os.path.abspath(output_filename)}[/]")
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to CSV: {str(e)}[/]")
        return None


def export_to_json(
    data: List[ProfileData], filename: str, output_dir: Optional[str] = None, include_dual_metrics: bool = False
) -> Optional[str]:
    """Export dashboard data to a JSON file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.json"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename

        # Prepare data with dual-metric enhancement if requested
        export_data = []
        for item in data:
            if include_dual_metrics:
                # Enhanced data structure for dual metrics
                enhanced_item = dict(item)  # Copy base data

                # Calculate variance metrics
                current_unblended = item.get("current_month", 0)
                current_amortized = item.get("current_month_amortized", current_unblended)
                variance = abs(current_unblended - current_amortized)
                variance_pct = (variance / current_amortized * 100) if current_amortized > 0 else 0

                # Add dual-metric metadata
                enhanced_item.update(
                    {
                        "dual_metric_analysis": {
                            "unblended_cost": {
                                "current": current_unblended,
                                "previous": item.get("previous_month", 0),
                                "metric_type": "technical",
                                "description": "UnblendedCost - for DevOps/SRE teams",
                            },
                            "amortized_cost": {
                                "current": current_amortized,
                                "previous": item.get("previous_month_amortized", item.get("previous_month", 0)),
                                "metric_type": "financial",
                                "description": "AmortizedCost - for Finance/Executive teams",
                            },
                            "variance_analysis": {
                                "absolute_variance": variance,
                                "percentage_variance": variance_pct,
                                "variance_level": "low"
                                if variance_pct < 1.0
                                else "moderate"
                                if variance_pct < 5.0
                                else "high",
                            },
                        },
                        "export_metadata": {
                            "export_type": "dual_metric",
                            "export_timestamp": datetime.now().isoformat(),
                            "metric_explanation": {
                                "unblended_cost": "Actual costs without Reserved Instance or Savings Plan allocations",
                                "amortized_cost": "Costs with Reserved Instance and Savings Plan benefits applied",
                            },
                        },
                    }
                )
                export_data.append(enhanced_item)
            else:
                export_data.append(item)

        with open(output_filename, "w") as jsonfile:
            json.dump(export_data, jsonfile, indent=4)

        console.print(f"[bright_green]Exported dashboard data to {os.path.abspath(output_filename)}[/]")
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to JSON: {str(e)}[/]")
        return None


def get_previous_month_costs(session: Session, profile_name: Optional[str] = None) -> Dict[str, float]:
    """
    Get previous month costs by service for trend analysis.

    Args:
        session: AWS boto3 session
        profile_name: Optional AWS profile name for enhanced error messaging

    Returns:
        Dictionary mapping service names to cost amounts
    """
    ce = session.client("ce", region_name="us-east-1")
    today = date.today()

    # Calculate previous month date range
    first_day_current = today.replace(day=1)
    last_day_previous = first_day_current - timedelta(days=1)
    first_day_previous = last_day_previous.replace(day=1)

    start_date = first_day_previous.isoformat()
    end_date = (last_day_previous + timedelta(days=1)).isoformat()  # AWS CE end date is exclusive

    try:
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        costs_by_service = {}
        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                service = group["Keys"][0]
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if cost > 0.001:  # Filter negligible costs
                    costs_by_service[service] = cost

        # v1.1.20: Disabled EC2 aggregation - preserve separate EC2-Instances and EC2-Other (AWS Console parity)
        # costs_by_service = aggregate_ec2_costs(costs_by_service)

        return costs_by_service

    except Exception as e:
        console.log(f"[yellow]Warning: Could not fetch previous month costs: {str(e)}[/]")
        if "AccessDeniedException" in str(e) and "ce:GetCostAndUsage" in str(e):
            handle_cost_explorer_error(e, profile_name)
        return {}


def categorize_aws_services(enriched_services: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize AWS services into hierarchical groups for Tree visualization.

    Args:
        enriched_services: Output from enrich_service_costs_with_trends()

    Returns:
        {
            "Compute": [list of compute services],
            "Network": [list of network services],
            "Storage": [list of storage services],
            "Database": [list of database services],
            "Other": [list of other services]
        }
    """
    categories = {"Compute": [], "Network": [], "Storage": [], "Database": [], "Other": []}

    # Service name → category mapping
    compute_keywords = [
        "EC2",
        "Lambda",
        "Fargate",
        "Batch",
        "Elastic Container",
        "ECS",
        "EKS",
        "Compute",
        "AppStream",
        "WorkSpaces",
    ]
    network_keywords = [
        "VPC",
        "Virtual Private Cloud",
        "CloudFront",
        "Route 53",
        "Direct Connect",
        "Global Accelerator",
        "API Gateway",
        "Elastic Load Balancing",
    ]
    storage_keywords = ["S3", "EBS", "Glacier", "EFS", "FSx", "Storage Gateway", "Backup", "Snapshot"]
    database_keywords = [
        "RDS",
        "DynamoDB",
        "Aurora",
        "ElastiCache",
        "Redshift",
        "DocumentDB",
        "Neptune",
        "Database Migration",
    ]

    for service in enriched_services:
        name = service["service_name"]

        # Check category membership
        if any(keyword in name for keyword in compute_keywords):
            categories["Compute"].append(service)
        elif any(keyword in name for keyword in network_keywords):
            categories["Network"].append(service)
        elif any(keyword in name for keyword in storage_keywords):
            categories["Storage"].append(service)
        elif any(keyword in name for keyword in database_keywords):
            categories["Database"].append(service)
        else:
            categories["Other"].append(service)

    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def enrich_service_costs_with_trends(
    current_costs: Dict[str, float],
    previous_costs: Dict[str, float],
    quarterly_costs: Optional[Dict[str, float]] = None,
    cache_timestamp: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Enrich service costs with trend analysis for executive dashboard.

    Args:
        current_costs: Dictionary mapping service names to current month costs
        previous_costs: Dictionary mapping service names to previous month costs
        quarterly_costs: Optional dictionary mapping service names to quarterly total costs
        cache_timestamp: Optional timestamp when data was fetched (for "last read" calculation)

    Returns:
        List of enriched service dictionaries with keys:
        - service_name: Service name (str)
        - current_cost: Current month cost (float)
        - previous_cost: Previous month cost (float)
        - change_amount: Dollar change amount (float)
        - change_pct: Percentage change (float)
        - trend_indicator: Visual trend indicator (str: ↑↑↑, ↑, →, ↓, ↓↓↓)
        - trend_description: Trend description (str: "declining", "stable", "growing", etc.)
        - pct_of_total: Percentage of total current costs (float)
        - last_read: Time since data was fetched (str: "2 mins ago")
    """
    enriched_services = []
    total_current = sum(current_costs.values())

    # Calculate time since last API call
    if cache_timestamp:
        time_ago = (datetime.now() - cache_timestamp).total_seconds()
        if time_ago < 60:
            last_read = f"{int(time_ago)} secs ago"
        elif time_ago < 3600:
            last_read = f"{int(time_ago / 60)} mins ago"
        else:
            last_read = f"{int(time_ago / 3600)} hrs ago"
    else:
        last_read = "just now"

    for service, current in sorted(current_costs.items(), key=lambda x: x[1], reverse=True):
        previous = previous_costs.get(service, 0)

        # Calculate month-over-month change
        change_amount = current - previous
        change_pct = (change_amount / previous * 100) if previous > 0 else 0

        # Calculate quarterly trend (if available)
        trend_indicator = "→"
        trend_description = "stable"

        if quarterly_costs and service in quarterly_costs:
            quarterly_total = quarterly_costs[service]
            quarterly_avg = quarterly_total / 3 if quarterly_total > 0 else 0

            if quarterly_avg > 0:
                quarterly_change = ((current - quarterly_avg) / quarterly_avg) * 100
                if quarterly_change > 25:
                    trend_indicator = "↑↑↑"
                    trend_description = "rapid growth"
                elif quarterly_change > 10:
                    trend_indicator = "↑"
                    trend_description = "growing"
                elif quarterly_change < -25:
                    trend_indicator = "↓↓↓"
                    trend_description = "declining"
                elif quarterly_change < -10:
                    trend_indicator = "↓"
                    trend_description = "decreasing"

        enriched_services.append(
            {
                "service_name": get_service_display_name(service),  # v1.1.20: Apply standardized service naming
                "current_cost": current,
                "previous_cost": previous,
                "change_amount": change_amount,
                "change_pct": change_pct,
                "trend_indicator": trend_indicator,
                "trend_description": trend_description,
                "pct_of_total": (current / total_current * 100) if total_current > 0 else 0,
                "last_read": last_read,
            }
        )

    return enriched_services
