"""
Multi-Account Dashboard Module - Organizations API Integration

Phase 3 Implementation: Code separation for --all-profile mode
Extracted from dashboard_runner.py (762 lines → ~480 lines multi-account logic)

Architecture:
- Organizations API discovery (67 accounts)
- LINKED_ACCOUNT cost aggregation
- Management + Billing + Operational profile support
- Enterprise performance (<15s discovery target)

Usage:
    from runbooks.finops.dashboard_multi import run_multi_account_dashboard

    result = run_multi_account_dashboard(
        management_profile="management-profile",
        billing_profile="billing-profile",
        centralised_ops_profile="ops-profile",
        timeframe="monthly"
    )
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional
import argparse

from rich.console import Console

from runbooks.common.date_utils import DateRangeCalculator  # ADLC v3.0.0: DRY date logic
from runbooks.common.profile_utils import create_cost_session, create_operational_session
from runbooks.common import parallel, export as export_engine
from runbooks.common.rich_utils import (
    export_console_html,
    create_recording_console,
    calculate_trend_arrow,  # v1.1.32: DRY - centralized trend arrow
    create_progress_bar_sparkline,  # v1.1.32: DRY - centralized sparkline
)
from runbooks.finops import audit, trends, business_case
from runbooks.finops.aws_client import get_organization_accounts
from runbooks.finops.cost_processor import get_cost_data
from runbooks.finops.service_categories import (
    categorize_aws_service,
    categorize_services_dict,
    get_category_totals,
)
from runbooks.finops.persona_formatter import PersonaFormatter

console = Console()


def run_multi_account_dashboard(
    management_profile: str,
    billing_profile: str,
    centralised_ops_profile: str,
    timeframe: str = "monthly",
    time_range: Optional[int] = None,
    month: Optional[str] = None,  # v1.2.0: Specific month support (YYYY-MM format)
    top_n: int = 10,
    cost_threshold: float = 1.0,
    activity_analysis: bool = False,
    dry_run: bool = False,
    export_formats: Optional[List[str]] = None,
    output_file: Optional[str] = None,
    mode: str = "architect",
    **kwargs,
) -> Dict[str, Any]:
    """
    Multi-account dashboard using Organizations API.

    Requires:
    - MANAGEMENT_PROFILE: Organizations:ListAccounts permission
    - BILLING_PROFILE: Cost Explorer LINKED_ACCOUNT access
    - CENTRALISED_OPS_PROFILE: CloudWatch/operational data access

    Args:
        management_profile: AWS profile with Organizations permissions
        billing_profile: AWS profile with Cost Explorer permissions
        centralised_ops_profile: AWS profile for operational data
        timeframe: Cost aggregation timeframe (daily, weekly, monthly, quarterly)
        time_range: Optional time range in days
        month: Specific month to analyze (YYYY-MM format, e.g., 2025-12). Overrides time_range.
        top_n: Number of top accounts to display
        cost_threshold: Minimum cost threshold for display
        activity_analysis: Enable resource activity analysis
        dry_run: Dry run mode (no AWS API calls)
        export_formats: Optional list of export formats ['json', 'csv', 'pdf', 'html']
        output_file: Optional output file path for HTML export
        mode: Dashboard mode (executive/architect/sre, default: architect)

    Returns:
        Dictionary with multi-account dashboard data:
        {
            'mode': 'multi-account',
            'organization_total': float,
            'accounts': List[Dict],
            'per_account_costs': Dict[str, float],
            'service_costs': Dict[str, float],
            'account_count': int,
            'active_accounts': int
        }
    """

    # v1.1.30: Create recording console for HTML export support
    needs_html_export = export_formats and "html" in export_formats
    if needs_html_export:
        render_console = create_recording_console()
    else:
        render_console = console

    # v1.1.30: Persona-specific rendering (Sprint 3)
    persona_formatter = None
    valid_personas = ["executive", "architect", "sre", "cfo", "cto", "ceo", "technical"]
    if mode and mode.lower() in valid_personas:
        persona_formatter = PersonaFormatter(persona=mode.lower())

    if dry_run:
        render_console.print("[yellow]🔍 DRY RUN: Multi-account discovery simulation[/]")
        return {
            "mode": "multi-account",
            "dry_run": True,
            "organization_total": 0.0,
            "accounts": [],
            "per_account_costs": {},
            "service_costs": {},
            "account_count": 0,
            "active_accounts": 0,
        }

    render_console.print("\n[bold cyan]📊 Multi-Account Dashboard[/]")
    render_console.print(f"[dim]Management: {management_profile}[/]")
    render_console.print(f"[dim]Billing: {billing_profile}[/]")
    render_console.print(f"[dim]Operations: {centralised_ops_profile}[/]")
    render_console.print(f"[dim]Timeframe: {timeframe}[/]")

    # Step 1: Organizations API discovery
    try:
        management_session = create_operational_session(management_profile)
        accounts = get_organization_accounts(management_session, management_profile)

        render_console.print(f"[green]✅ Discovered {len(accounts)} accounts[/]")

        if not accounts:
            render_console.print("[yellow]⚠️ No accounts found in organization[/]")
            return {
                "mode": "multi-account",
                "organization_total": 0.0,
                "accounts": [],
                "per_account_costs": {},
                "service_costs": {},
                "account_count": 0,
                "active_accounts": 0,
                "error": "No accounts discovered",
            }

    except Exception as e:
        render_console.print(f"[red]❌ Organization discovery failed: {str(e)}[/]")
        return {
            "mode": "multi-account",
            "organization_total": 0.0,
            "accounts": [],
            "per_account_costs": {},
            "service_costs": {},
            "account_count": 0,
            "active_accounts": 0,
            "error": str(e),
        }

    # Step 2: LINKED_ACCOUNT cost aggregation
    try:
        account_ids = [acc["id"] for acc in accounts]
        org_costs = get_organization_wide_costs(
            billing_profile=billing_profile, organization_accounts=account_ids, time_range=time_range, month=month
        )

        render_console.print(f"[green]✅ Organization total: ${org_costs['organization_total']:,.2f}[/]")
        render_console.print(f"[dim]Active accounts: {org_costs['active_accounts']}/{org_costs['account_count']}[/]")

    except Exception as e:
        render_console.print(f"[red]❌ Cost aggregation failed: {str(e)}[/]")
        org_costs = {
            "organization_total": 0.0,
            "per_account_costs": {},
            "service_costs": {},
            "account_count": len(accounts),
            "active_accounts": 0,
            "error": str(e),
        }

    # Step 3: Enrich accounts with cost data
    enriched_accounts = []
    for account in accounts:
        account_id = account["id"]
        account_cost = org_costs["per_account_costs"].get(account_id, 0.0)

        # Apply cost threshold filter
        if account_cost >= cost_threshold:
            enriched_accounts.append(
                {
                    "id": account_id,
                    "name": account.get("name", "Unknown"),
                    "status": account.get("status", "ACTIVE"),
                    "email": account.get("email", ""),
                    "cost": account_cost,
                }
            )

    # Sort by cost descending
    enriched_accounts.sort(key=lambda x: x["cost"], reverse=True)

    # v1.1.30: Persona-specific data filtering (Sprint 3.2)
    # Apply persona-specific top_n if not explicitly overridden
    effective_top_n = top_n
    if persona_formatter and hasattr(persona_formatter, "config"):
        # Use persona default if user didn't specify explicit top_n
        persona_top_n = persona_formatter.config.top_services
        if persona_top_n != "all" and isinstance(persona_top_n, int):
            # Persona config provides guidance, CLI --top-n takes precedence
            if top_n == 10:  # Default value indicates user didn't specify
                effective_top_n = persona_top_n

    # Apply top_n limit
    display_accounts = enriched_accounts
    if effective_top_n and effective_top_n > 0:
        display_accounts = enriched_accounts[:effective_top_n]

    # Step 4: Build result dictionary
    # v1.1.29: Add categorized service costs using AWS Official Taxonomy
    service_costs_raw = org_costs.get("service_costs", {})
    categorized_services = categorize_services_dict(service_costs_raw)
    category_totals = get_category_totals(categorized_services)

    result = {
        "mode": "multi-account",
        "organization_total": org_costs["organization_total"],
        "accounts": display_accounts,  # v1.1.30: Use persona-filtered accounts
        "per_account_costs": org_costs["per_account_costs"],
        "service_costs": service_costs_raw,
        "service_costs_by_category": categorized_services,  # v1.1.29: AWS Official Taxonomy
        "category_totals": category_totals,  # v1.1.29: Category-level aggregation
        "account_count": org_costs["account_count"],
        "active_accounts": org_costs["active_accounts"],
        "timeframe": timeframe,
        "management_profile": management_profile,
        "billing_profile": billing_profile,
        "centralised_ops_profile": centralised_ops_profile,
    }

    # v1.1.30/v1.1.30: Persona-specific rendering with $/day normalization
    if persona_formatter:
        persona_mode = mode.lower() if mode else "architect"
        # v1.1.30: Pass period data for $/day normalization
        # v1.1.30 FIX: Include previous_service_costs for per-service % Change
        period_data = {
            "current_days": org_costs.get("current_days", 1),
            "previous_days": org_costs.get("previous_days", 1),
            "previous_account_costs": org_costs.get("previous_account_costs", {}),
            "previous_service_costs": org_costs.get("previous_service_costs", {}),  # v1.1.30 FIX
            "previous_total": org_costs.get("previous_total", 0.0),
        }
        if persona_mode in ["executive", "ceo", "cfo"]:
            _render_executive_summary(
                render_console,
                org_costs["organization_total"],
                display_accounts,
                category_totals,
                persona_mode,
                period_data,  # v1.1.30
            )
        elif persona_mode == "architect":
            _render_architect_view(
                render_console,
                display_accounts,
                categorized_services,
                category_totals,
                period_data,  # v1.1.30
            )
        elif persona_mode == "sre":
            _render_sre_alerts(
                render_console,
                display_accounts,
                org_costs["per_account_costs"],
                org_costs["organization_total"],
                period_data,  # v1.1.30
            )
        # technical mode uses default output (no additional rendering)

    # Step 5: Optional activity analysis (future enhancement)
    if activity_analysis:
        render_console.print("[dim]ℹ️ Activity analysis not yet implemented for multi-account mode[/]")

    # Step 6: Export to requested formats (if specified)
    if export_formats:
        try:
            # v1.1.30: Handle HTML export separately using recording console
            non_html_formats = [f for f in export_formats if f != "html"]

            # Export non-HTML formats using existing engine
            if non_html_formats:
                export_paths = export_engine.export_to_formats(
                    data=result, base_filename=f"multi-account-dashboard", formats=non_html_formats
                )
                result["export_paths"] = export_paths
                render_console.print(f"[green]✅ Exported to {len(export_paths)} formats[/]")

            # Handle HTML export using recording console
            if "html" in export_formats:
                if output_file:
                    html_path = export_console_html(
                        console=render_console,
                        output_path=output_file,
                        mode=mode,
                        metadata={
                            "management_profile": management_profile,
                            "billing_profile": billing_profile,
                            "organization_total": org_costs["organization_total"],
                            "account_count": org_costs["account_count"],
                        },
                    )
                    if html_path:
                        if "export_paths" not in result:
                            result["export_paths"] = {}
                        result["export_paths"]["html"] = html_path
                        render_console.print(f"[green]✅ HTML exported to {html_path}[/]")
                else:
                    render_console.print("[yellow]⚠️ HTML export requested but no --output-file specified[/]")

        except Exception as export_error:
            render_console.print(f"[yellow]⚠️ Export failed: {str(export_error)}[/]")
            result["export_error"] = str(export_error)

    return result


def get_organization_wide_costs(
    billing_profile: str,
    organization_accounts: List[str],
    time_range: Optional[int] = None,
    month: Optional[str] = None,  # v1.2.0: Specific month support (YYYY-MM format)
) -> Dict[str, Any]:
    """
    Aggregate costs across all organization accounts using LINKED_ACCOUNT dimension.

    v1.1.30: Enhanced with $/day normalization for accurate % Change calculation.
    Fetches both current and previous period costs for same-unit comparison.

    Args:
        billing_profile: AWS profile with Cost Explorer permissions
        organization_accounts: List of account IDs from Organizations API
        time_range: Optional time range in days
        month: Specific month to analyze (YYYY-MM format, e.g., 2025-12). Overrides time_range.

    Returns:
        Dictionary with organization-wide cost data:
        {
            'organization_total': float,
            'per_account_costs': Dict[str, float],
            'service_costs': Dict[str, float],
            'previous_account_costs': Dict[str, float],  # v1.1.30
            'previous_service_costs': Dict[str, float],  # v1.1.30
            'current_days': int,  # v1.1.30: For $/day normalization
            'previous_days': int,  # v1.1.30: For $/day normalization
            'account_count': int,
            'active_accounts': int
        }
    """
    try:
        # Create billing session
        session = create_cost_session(profile_name=billing_profile)
        ce_client = session.client("ce", region_name="ap-southeast-2")

        # Calculate date ranges for CURRENT and PREVIOUS periods
        # ADLC v3.0.0: Refactored to use DateRangeCalculator (DRY compliance)
        # All end dates are now EXCLUSIVE (AWS Cost Explorer convention)
        today = date.today()

        # v1.2.0: Specific month takes highest priority (overrides time_range)
        if month:
            try:
                # Use centralized DateRangeCalculator for consistent date logic
                current_range = DateRangeCalculator.month_range(month)
                start_date = current_range.start
                end_date = current_range.end  # Already exclusive
                current_days = current_range.days

                # Previous period for MoM comparison
                prev_range = DateRangeCalculator.previous_month(current_range)
                prev_start_date = prev_range.start
                prev_end_date = prev_range.end  # Already exclusive
                previous_days = prev_range.days

                console.print(f"[cyan]📅 Analyzing specific month: {month} ({current_days} days)[/]")
                console.print(f"[dim]   Period: {start_date.isoformat()} to {end_date.isoformat()} (exclusive)[/]")

            except ValueError as e:
                console.print(f"[red]❌ {e}[/]")
                raise

        elif time_range:
            # ADLC v3.0.0: Use DateRangeCalculator for consistent UTC-first logic
            current_range = DateRangeCalculator.days_range(time_range, reference_date=today)
            start_date = current_range.start
            end_date = current_range.end  # Already exclusive
            current_days = current_range.days

            prev_range = DateRangeCalculator.previous_period(current_range)
            prev_start_date = prev_range.start
            prev_end_date = prev_range.end  # Already exclusive
            previous_days = prev_range.days

        else:
            # Current month to date
            current_range = DateRangeCalculator.days_range(today.day - 1, reference_date=today)
            start_date = today.replace(day=1)
            end_date = today + timedelta(days=1)  # Exclusive (include today)
            current_days = today.day

            # Previous period: full previous month
            prev_range = DateRangeCalculator.previous_calendar_month()
            prev_start_date = prev_range.start
            prev_end_date = prev_range.end  # Already exclusive
            previous_days = prev_range.days

        # Format dates for Cost Explorer API
        # NOTE: end dates are already exclusive, no +1 needed
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        prev_start_str = prev_start_date.isoformat()
        prev_end_str = prev_end_date.isoformat()

        console.print(f"\n[dim]📊 Querying organization costs: {start_str} to {end_str} ({current_days} days)[/]")
        console.print(f"[dim]📊 Previous period: {prev_start_str} to {prev_end_str} ({previous_days} days)[/]")

        # Query 1: Per-account costs using LINKED_ACCOUNT dimension
        # Note: AWS Cost Explorer has a limit of 100 values in filter
        # Split accounts into chunks if necessary
        all_per_account_costs = {}

        # Process accounts in chunks of 100 (AWS limit)
        chunk_size = 100
        for i in range(0, len(organization_accounts), chunk_size):
            account_chunk = organization_accounts[i : i + chunk_size]

            response = ce_client.get_cost_and_usage(
                TimePeriod={"Start": start_str, "End": end_str},
                Granularity="MONTHLY",
                GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
                Metrics=["BlendedCost"],
                Filter={"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": account_chunk}},
            )

            # Aggregate costs from this chunk
            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    account_id = group["Keys"][0]
                    cost = float(group["Metrics"]["BlendedCost"]["Amount"])
                    all_per_account_costs[account_id] = all_per_account_costs.get(account_id, 0) + cost

        # Use aggregated costs
        per_account_costs = all_per_account_costs

        # Calculate organization total
        organization_total = sum(per_account_costs.values())

        # Query 2: Service breakdown across all accounts
        # Process accounts in chunks of 100 (AWS limit)
        all_service_costs = {}

        for i in range(0, len(organization_accounts), chunk_size):
            account_chunk = organization_accounts[i : i + chunk_size]

            service_response = ce_client.get_cost_and_usage(
                TimePeriod={"Start": start_str, "End": end_str},
                Granularity="MONTHLY",
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                Metrics=["BlendedCost"],
                Filter={"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": account_chunk}},
            )

            # Aggregate service costs from this chunk
            for result in service_response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    service = group["Keys"][0]
                    cost = float(group["Metrics"]["BlendedCost"]["Amount"])
                    all_service_costs[service] = all_service_costs.get(service, 0) + cost

        # Use aggregated service costs
        service_costs = all_service_costs

        console.print(f"[green]✅ Organization total: ${organization_total:,.2f}[/]")
        console.print(f"[dim]Active accounts with costs: {len(per_account_costs)}/{len(organization_accounts)}[/]")

        # v1.1.30: Query previous period for $/day normalization
        # Query 3: Previous period per-account costs
        prev_per_account_costs = {}
        for i in range(0, len(organization_accounts), chunk_size):
            account_chunk = organization_accounts[i : i + chunk_size]
            try:
                prev_response = ce_client.get_cost_and_usage(
                    TimePeriod={"Start": prev_start_str, "End": prev_end_str},
                    Granularity="MONTHLY",
                    GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
                    Metrics=["BlendedCost"],
                    Filter={"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": account_chunk}},
                )
                for result in prev_response.get("ResultsByTime", []):
                    for group in result.get("Groups", []):
                        account_id = group["Keys"][0]
                        cost = float(group["Metrics"]["BlendedCost"]["Amount"])
                        prev_per_account_costs[account_id] = prev_per_account_costs.get(account_id, 0) + cost
            except Exception as prev_err:
                console.print(f"[dim]⚠️ Previous period query failed for chunk: {prev_err}[/]")

        # Query 4: Previous period service costs
        prev_service_costs = {}
        for i in range(0, len(organization_accounts), chunk_size):
            account_chunk = organization_accounts[i : i + chunk_size]
            try:
                prev_svc_response = ce_client.get_cost_and_usage(
                    TimePeriod={"Start": prev_start_str, "End": prev_end_str},
                    Granularity="MONTHLY",
                    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                    Metrics=["BlendedCost"],
                    Filter={"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": account_chunk}},
                )
                for result in prev_svc_response.get("ResultsByTime", []):
                    for group in result.get("Groups", []):
                        service = group["Keys"][0]
                        cost = float(group["Metrics"]["BlendedCost"]["Amount"])
                        prev_service_costs[service] = prev_service_costs.get(service, 0) + cost
            except Exception as prev_svc_err:
                console.print(f"[dim]⚠️ Previous service query failed for chunk: {prev_svc_err}[/]")

        previous_total = sum(prev_per_account_costs.values())
        console.print(f"[dim]Previous period total: ${previous_total:,.2f}[/]")

        # Show top 5 accounts by cost
        if per_account_costs:
            sorted_accounts = sorted(per_account_costs.items(), key=lambda x: x[1], reverse=True)[:5]
            console.print(f"[dim]Top 5 accounts by cost:[/]")
            for account_id, cost in sorted_accounts:
                console.print(f"[dim]  • {account_id}: ${cost:,.2f}[/]")

        return {
            "organization_total": organization_total,
            "per_account_costs": per_account_costs,
            "service_costs": service_costs,
            "previous_account_costs": prev_per_account_costs,  # v1.1.30
            "previous_service_costs": prev_service_costs,  # v1.1.30
            "previous_total": previous_total,  # v1.1.30
            "current_days": current_days,  # v1.1.30
            "previous_days": previous_days,  # v1.1.30
            "account_count": len(organization_accounts),
            "active_accounts": len(per_account_costs),
        }

    except Exception as e:
        console.print(f"[yellow]⚠️ Organization cost aggregation failed: {str(e)}[/]")
        return {
            "organization_total": 0.0,
            "per_account_costs": {},
            "service_costs": {},
            "previous_account_costs": {},  # v1.1.30
            "previous_service_costs": {},  # v1.1.30
            "previous_total": 0.0,  # v1.1.30
            "current_days": 1,  # v1.1.30
            "previous_days": 1,  # v1.1.30
            "account_count": len(organization_accounts),
            "active_accounts": 0,
            "error": str(e),
        }


def run_multi_account_audit(
    management_profile: str, billing_profile: str, ops_profile: str, dry_run: bool = False, **kwargs
) -> Dict[str, Any]:
    """
    Run audit report across multiple accounts.

    Wrapper for audit.run_audit_report() with multi-account context.
    Uses parallel processing for <30s circuit breaker performance target.
    Discovers optimization opportunities across all organization accounts.

    Args:
        management_profile: AWS profile with Organizations permissions
        billing_profile: AWS profile with Cost Explorer permissions
        ops_profile: AWS profile for operational data access
        dry_run: Dry run mode (no AWS API calls)
        **kwargs: Additional arguments passed to audit module

    Returns:
        Dictionary with consolidated multi-account audit data including:
        - optimization_opportunities: Aggregated findings across accounts
        - total_potential_savings: Organization-wide potential savings
        - profiles: List of per-account audit results
    """
    console.print(f"\n[bold cyan]📋 Multi-Account Audit Report[/]")
    console.print(f"[dim]Management: {management_profile}[/]")
    console.print(f"[dim]Billing: {billing_profile}[/]")
    console.print(f"[dim]Operations: {ops_profile}[/]")

    # Build profiles list (management, billing, ops)
    profiles_list = [management_profile, billing_profile, ops_profile]

    # Create argument namespace for audit module
    args = argparse.Namespace(dry_run=dry_run, **{k: v for k, v in kwargs.items() if k in ["top_n", "output_format"]})

    # Call audit module with parallel processing
    result = audit.run_audit_report(profiles_list, args)

    return result


def run_multi_account_trends(
    management_profile: str, billing_profile: str, ops_profile: str, months: int = 6, dry_run: bool = False, **kwargs
) -> Dict[str, Any]:
    """
    Run 6-month trend analysis across multiple accounts.

    Wrapper for trends.run_trend_analysis() with multi-account context.
    Analyzes historical cost patterns across all organization accounts.

    Args:
        management_profile: AWS profile with Organizations permissions
        billing_profile: AWS profile with Cost Explorer permissions
        ops_profile: AWS profile for operational data access
        months: Number of months to analyze (default: 6)
        dry_run: Dry run mode (no AWS API calls)
        **kwargs: Additional arguments passed to trends module

    Returns:
        Dictionary with consolidated trend analysis including:
        - monthly_costs: Aggregated monthly cost data across accounts
        - trend_direction: Organization-wide trend direction
        - percentage_changes: Organization-level month-over-month changes
    """
    console.print(f"\n[bold cyan]📈 Multi-Account Trend Analysis[/]")
    console.print(f"[dim]Management: {management_profile}[/]")
    console.print(f"[dim]Billing: {billing_profile}[/]")
    console.print(f"[dim]Operations: {ops_profile}[/]")

    # Build profiles list
    profiles_list = [management_profile, billing_profile, ops_profile]

    # Create argument namespace for trends module
    args = argparse.Namespace(
        dry_run=dry_run, months=months, **{k: v for k, v in kwargs.items() if k in ["output_format", "export_json"]}
    )

    # Call trends module
    result = trends.run_trend_analysis(profiles_list, args)

    return result


def calculate_business_case(annual_savings: float, implementation_hours: float = 8, **kwargs) -> Dict[str, Any]:
    """
    Calculate ROI metrics for cost optimization business case.

    Wrapper for business_case.calculate_roi_metrics().
    Provides comprehensive ROI analysis including payback period,
    break-even point, and confidence scoring.

    Args:
        annual_savings: Projected annual cost savings in USD
        implementation_hours: Estimated implementation hours (default: 8)
        **kwargs: Additional arguments (reserved for future use)

    Returns:
        Dictionary with ROI metrics including:
        - annual_savings: Input annual savings amount
        - implementation_cost: Calculated implementation cost
        - roi_percentage: Return on investment percentage
        - payback_months: Months to recoup implementation cost
        - confidence_score: Conservative confidence rating
    """
    console.print(f"\n[bold cyan]💼 Calculating Business Case (Multi-Account)[/]")
    console.print(f"[dim]Annual Savings: ${annual_savings:,.2f}[/]")
    console.print(f"[dim]Implementation Hours: {implementation_hours}[/]")

    # Call business case module
    result = business_case.calculate_roi_metrics(annual_savings, implementation_hours)

    return result


# =============================================================================
# v1.1.30/v1.1.30: Persona-Specific Rendering Helper Functions
# =============================================================================

# v1.1.32: _calculate_trend_arrow moved to runbooks.common.rich_utils.calculate_trend_arrow
# for DRY compliance across all finops modules


def _calculate_daily_rate_change(
    current_cost: float, previous_cost: float, current_days: int, previous_days: int
) -> float:
    """
    v1.1.30: Calculate % change using $/day normalization.

    Same unit of measure comparison:
    - Current daily rate = current_cost / current_days
    - Previous daily rate = previous_cost / previous_days
    - % Change = ((current_daily - previous_daily) / previous_daily) × 100

    Args:
        current_cost: Cost for current period
        previous_cost: Cost for previous period
        current_days: Number of days in current period
        previous_days: Number of days in previous period

    Returns:
        Percentage change between daily rates
    """
    if previous_cost <= 0 or previous_days <= 0:
        return 100.0 if current_cost > 0 else 0.0

    current_daily = current_cost / max(current_days, 1)
    previous_daily = previous_cost / max(previous_days, 1)

    if previous_daily <= 0:
        return 100.0 if current_daily > 0 else 0.0

    return ((current_daily - previous_daily) / previous_daily) * 100


def _render_executive_summary(
    render_console: Console,
    organization_total: float,
    accounts: List[Dict[str, Any]],
    category_totals: Dict[str, float],
    mode: str,
    period_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render executive summary view - board-ready, high-level focus.

    v1.1.30: Enhanced with trend arrows, sparklines, and recommendations.

    Executive personas (CEO/CFO/Executive) need:
    - Total spend headline with trend
    - Top 5 accounts by cost with % Change
    - Category-level breakdown with sparklines
    - Trend indicators
    - Recommended actions
    """
    render_console.print("\n[bold magenta]━━━ Executive Summary ━━━[/]")

    # v1.1.30: Extract period data for $/day normalization
    current_days = period_data.get("current_days", 1) if period_data else 1
    previous_days = period_data.get("previous_days", 1) if period_data else 1
    previous_account_costs = period_data.get("previous_account_costs", {}) if period_data else {}
    previous_total = period_data.get("previous_total", 0.0) if period_data else 0.0

    # v1.1.30: Calculate organization-level % Change with $/day normalization
    org_change_pct = _calculate_daily_rate_change(organization_total, previous_total, current_days, previous_days)
    org_trend = calculate_trend_arrow(org_change_pct)

    # Headline: Organization total with trend
    change_color = "[red]" if org_change_pct > 0 else "[green]"
    change_sign = "+" if org_change_pct >= 0 else ""
    render_console.print(
        f"\n[bold white]💰 Total Organization Spend: ${organization_total:,.2f}[/] "
        f"{org_trend} {change_color}{change_sign}{org_change_pct:.1f}%[/]"
    )

    # Top accounts summary (max 5 for executive view) with trend
    top_accounts = accounts[:5] if len(accounts) > 5 else accounts
    if top_accounts:
        render_console.print(f"\n[bold cyan]📊 Top {len(top_accounts)} Cost Drivers:[/]")
        for i, acc in enumerate(top_accounts, 1):
            pct = (acc["cost"] / organization_total * 100) if organization_total > 0 else 0
            sparkline = create_progress_bar_sparkline(pct, bar_width=10)
            # v1.1.30: Calculate per-account % Change
            prev_cost = previous_account_costs.get(acc["id"], 0)
            acc_change = _calculate_daily_rate_change(acc["cost"], prev_cost, current_days, previous_days)
            trend = calculate_trend_arrow(acc_change)
            acc_change_color = "[red]" if acc_change > 0 else "[green]"
            acc_sign = "+" if acc_change >= 0 else ""
            render_console.print(
                f"  {i}. {acc['name'][:25]:<25} ${acc['cost']:>10,.2f} "
                f"{sparkline} {pct:>4.1f}% {trend} {acc_change_color}{acc_sign}{acc_change:>5.1f}%[/]"
            )

    # Category breakdown (if available) with sparklines
    if category_totals:
        render_console.print(f"\n[bold cyan]📁 Spend by Category:[/]")
        sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        for cat, cost in sorted_cats:
            pct = (cost / organization_total * 100) if organization_total > 0 else 0
            sparkline = create_progress_bar_sparkline(pct, bar_width=10)
            render_console.print(f"  • {cat:<20} ${cost:>10,.2f} {sparkline} {pct:>4.1f}%")

    # v1.1.30: Add executive recommendations panel
    _render_executive_recommendations(render_console, accounts, previous_account_costs, current_days, previous_days)

    render_console.print(f"\n[dim italic]Mode: {mode.upper()} | Focus: Strategic Overview[/]")


def _render_architect_view(
    render_console: Console,
    accounts: List[Dict[str, Any]],
    categorized_services: Dict[str, Dict[str, float]],
    category_totals: Dict[str, float],
    period_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render architect view - full technical detail with service breakdown.

    v1.1.30: Enhanced with $/day % Change for accounts.

    Architect persona needs:
    - All accounts with details and % Change
    - Service-level breakdown by category
    - Technical identifiers (account IDs)
    - Complete data for analysis
    """
    render_console.print("\n[bold blue]━━━ Architect View ━━━[/]")

    # v1.1.30: Extract period data
    current_days = period_data.get("current_days", 1) if period_data else 1
    previous_days = period_data.get("previous_days", 1) if period_data else 1
    previous_account_costs = period_data.get("previous_account_costs", {}) if period_data else {}
    # v1.1.30 FIX: Get previous service costs for per-service % Change calculation
    previous_service_costs = period_data.get("previous_service_costs", {}) if period_data else {}

    # Full account listing with IDs and % Change
    if accounts:
        render_console.print(f"\n[bold cyan]🏗️ Account Details ({len(accounts)} accounts):[/]")
        org_total = sum(acc["cost"] for acc in accounts)
        for acc in accounts:
            # v1.1.30: Calculate % Change with $/day normalization
            prev_cost = previous_account_costs.get(acc["id"], 0)
            change_pct = _calculate_daily_rate_change(acc["cost"], prev_cost, current_days, previous_days)
            trend = calculate_trend_arrow(change_pct)
            pct_total = (acc["cost"] / org_total * 100) if org_total > 0 else 0
            sparkline = create_progress_bar_sparkline(pct_total, bar_width=8)
            change_color = "[red]" if change_pct > 0 else "[green]"
            sign = "+" if change_pct >= 0 else ""
            render_console.print(
                f"  [{acc['status'][:3]}] {acc['id']} | {acc['name'][:30]:<30} | "
                f"${acc['cost']:>10,.2f} {sparkline} {trend} {change_color}{sign}{change_pct:>5.1f}%[/]"
            )

    # Service breakdown by category with % Change (v1.1.30 FIX)
    if categorized_services:
        render_console.print(f"\n[bold cyan]📊 Services by Category:[/]")
        for category, services in sorted(categorized_services.items()):
            cat_total = category_totals.get(category, 0)
            if cat_total > 0:
                render_console.print(f"\n  [bold]{category}[/] (${cat_total:,.2f})")
                # Top 5 services per category with $/day normalized % Change
                sorted_svc = sorted(services.items(), key=lambda x: x[1], reverse=True)[:5]
                for svc, cost in sorted_svc:
                    if cost > 0:
                        # v1.1.30 FIX: Calculate per-service % Change with $/day normalization
                        prev_cost = previous_service_costs.get(svc, 0)
                        change_pct = _calculate_daily_rate_change(cost, prev_cost, current_days, previous_days)
                        trend = calculate_trend_arrow(change_pct)
                        change_color = "[red]" if change_pct > 0 else "[green]" if change_pct < 0 else "[dim]"
                        sign = "+" if change_pct >= 0 else ""
                        render_console.print(
                            f"    • {svc[:35]:<35} ${cost:>10,.2f}  {trend} {change_color}{sign}{change_pct:>5.1f}%[/]"
                        )

    render_console.print(f"\n[dim italic]Mode: ARCHITECT | Focus: Technical Detail[/]")


def _render_sre_alerts(
    render_console: Console,
    accounts: List[Dict[str, Any]],
    per_account_costs: Dict[str, float],
    organization_total: float,
    period_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Render SRE alerts view - anomaly detection and change focus.

    v1.1.30: Enhanced with $/day % Change for anomaly detection.

    SRE persona needs:
    - Anomaly indicators with % Change
    - Cost change detection ($/day normalized)
    - Alert-style formatting
    - Operational health signals
    """
    render_console.print("\n[bold yellow]━━━ SRE Alerts View ━━━[/]")

    # v1.1.30: Extract period data
    current_days = period_data.get("current_days", 1) if period_data else 1
    previous_days = period_data.get("previous_days", 1) if period_data else 1
    previous_account_costs = period_data.get("previous_account_costs", {}) if period_data else {}

    # Calculate average for anomaly detection
    costs = list(per_account_costs.values())
    avg_cost = sum(costs) / len(costs) if costs else 0
    std_threshold = avg_cost * 2  # 2x average as anomaly threshold

    # Identify anomalies based on cost AND % change
    anomalies = []
    for acc in accounts:
        prev_cost = previous_account_costs.get(acc["id"], 0)
        change_pct = _calculate_daily_rate_change(acc["cost"], prev_cost, current_days, previous_days)
        if acc["cost"] > std_threshold:
            anomalies.append({**acc, "change_pct": change_pct})

    # Alert section with % Change
    if anomalies:
        render_console.print(f"\n[bold red]🚨 ANOMALY ALERTS ({len(anomalies)} detected):[/]")
        for acc in anomalies:
            deviation = ((acc["cost"] - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0
            trend = calculate_trend_arrow(acc["change_pct"])
            render_console.print(f"  ⚠️  {acc['name'][:30]:<30} ${acc['cost']:>12,.2f} (+{deviation:>6.1f}% above avg)")
    else:
        render_console.print(f"\n[green]✅ No anomalies detected (threshold: 2x average)[/]")

    # Top 10 accounts by cost (SRE monitoring view) with % Change
    render_console.print(f"\n[bold cyan]📈 Top Cost Accounts (Monitoring):[/]")
    for acc in accounts[:10]:
        pct = (acc["cost"] / organization_total * 100) if organization_total > 0 else 0
        status_icon = "🔴" if acc["cost"] > std_threshold else "🟢"
        # v1.1.30: Calculate % Change
        prev_cost = previous_account_costs.get(acc["id"], 0)
        change_pct = _calculate_daily_rate_change(acc["cost"], prev_cost, current_days, previous_days)
        trend = calculate_trend_arrow(change_pct)
        render_console.print(f"  {status_icon} {acc['name'][:30]:<30} ${acc['cost']:>12,.2f} ({pct:>5.1f}%)")

    render_console.print(f"\n[dim]Avg account cost: ${avg_cost:,.2f} | Anomaly threshold: ${std_threshold:,.2f}[/]")
    render_console.print(f"[dim italic]Mode: SRE | Focus: Anomaly Detection & Monitoring[/]")


def _render_executive_recommendations(
    render_console: Console,
    accounts: List[Dict[str, Any]],
    previous_account_costs: Dict[str, float],
    current_days: int,
    previous_days: int,
) -> None:
    """
    v1.1.30: Render executive recommendations panel.

    Auto-generate actionable recommendations from cost data:
    1. Top cost driver recommendation
    2. Anomaly investigation recommendation
    3. Category optimization recommendation
    """
    from rich.panel import Panel

    recommendations = []

    # 1. Top cost driver recommendation
    if accounts:
        top_account = accounts[0]
        org_total = sum(acc["cost"] for acc in accounts)
        pct = (top_account["cost"] / org_total * 100) if org_total > 0 else 0
        recommendations.append(f"1. Review [bold]{top_account['name'][:25]}[/] for optimization ({pct:.1f}% of spend)")

    # 2. Anomaly detection recommendation - find accounts with >10% increase
    high_change_accounts = []
    for acc in accounts:
        prev_cost = previous_account_costs.get(acc["id"], 0)
        change_pct = _calculate_daily_rate_change(acc["cost"], prev_cost, current_days, previous_days)
        if change_pct > 10:
            high_change_accounts.append((acc, change_pct))

    if high_change_accounts:
        recommendations.append(f"2. Investigate [bold]{len(high_change_accounts)}[/] accounts with >10% cost increase")
    else:
        recommendations.append("2. [green]No unusual cost increases detected[/]")

    # 3. General optimization recommendation
    recommendations.append("3. Consider Reserved Instances for consistent Compute workloads")

    recs_text = "\n".join(recommendations)
    render_console.print("\n")
    render_console.print(Panel(recs_text, title="[bold]📋 Recommended Actions[/bold]", border_style="yellow"))
