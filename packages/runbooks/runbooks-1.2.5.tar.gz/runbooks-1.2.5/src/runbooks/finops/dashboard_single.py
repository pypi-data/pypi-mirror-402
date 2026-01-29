"""
Single-Account Dashboard Module - AWS Profile Integration

Phase 4 Implementation: Code separation for --profile mode
Extracted from dashboard_runner.py (762 lines → ~250 lines single-account logic)

Architecture:
- Single AWS profile cost queries
- Account-level resource discovery
- EC2, AppStream, ECS, CloudWatch integration
- Performance optimized for single account (<10s target)

Usage:
    from runbooks.finops.dashboard_single import run_single_account_dashboard

    result = run_single_account_dashboard(
        profile="aws-profile",
        timeframe="monthly"
    )
"""

from typing import Any, Dict, List, Optional
import argparse
from collections import defaultdict
import logging

from rich.console import Console
from rich.tree import Tree
from rich.table import Table as RichTable
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from botocore.exceptions import ClientError

from runbooks.common.profile_utils import create_cost_session, create_operational_session
from runbooks.common import export as export_engine, parallel
from runbooks.finops import audit, trends, business_case
from runbooks.finops.aws_client import (
    appstream_summary,
    cloudtrail_summary,
    cloudwatch_summary,
    config_summary,
    ec2_summary,
    ecs_summary,
    get_accessible_regions,
)
from runbooks.finops.cost_processor import (
    change_in_total_cost,
    format_budget_info,
    format_ec2_summary,
    get_cost_data,
    get_previous_month_costs,  # v1.1.30 FIX: For per-service % Change
    process_service_costs,
)
from runbooks.finops.service_categories import (
    categorize_aws_service,
    get_category_order,
)
from runbooks.finops.persona_formatter import (
    get_cli_persona_config,
    CLIPersonaConfig,
)
from runbooks.common.rich_utils import (
    create_progress_bar_sparkline,
    calculate_trend_arrow,  # v1.1.32: DRY - centralized trend arrow
)

console = Console()
logger = logging.getLogger(__name__)


# v1.1.32: _calculate_trend_arrow moved to runbooks.common.rich_utils.calculate_trend_arrow
# for DRY compliance across all finops modules


def create_service_cost_tree(
    services: Dict[str, float],
    total_cost: float,
    last_month_total: float = 0,
    console: Optional[Console] = None,
    previous_service_costs: Optional[Dict[str, float]] = None,
    current_days: int = 0,
    previous_days: int = 0,
) -> Tree:
    """
    Create hierarchical service cost tree visualization with cost trending.

    Groups AWS services by AWS Official Taxonomy (23 categories from AWS Whitepaper)
    and displays costs in a Rich Tree structure with month-over-month comparison.

    v1.1.29: Updated to use AWS Official Service Categories for accurate categorization.
    Tax is now displayed in header line (Previous Month), not as service category.

    v1.1.30: Added $/day normalization for accurate % Change calculation.
    When previous_service_costs is provided, uses actual per-service data.
    When period days are provided, calculates daily rate change.

    Args:
        services: Dictionary mapping service names to costs
        total_cost: Total cost across all services
        last_month_total: Total cost from previous month (for estimation)
        console: Optional Rich console for printing
        previous_service_costs: Optional dict of actual previous month per-service costs
        current_days: Number of days in current period (for $/day normalization)
        previous_days: Number of days in previous period (for $/day normalization)

    Returns:
        Rich Tree object with categorized service costs

    Example:
        >>> services = {'Amazon EC2': 1200, 'Amazon S3': 800, 'Amazon RDS': 500}
        >>> tree = create_service_cost_tree(services, 2500, 2400)
        >>> console.print(tree)
    """
    if console is None:
        console = Console()

    # v1.1.29: Extract Tax from services - display in header, not as category
    # Make a copy to avoid modifying original dict
    services_copy = dict(services)
    tax_amount = services_copy.pop("Tax", 0)

    # Calculate analytical totals (excluding Tax)
    analytical_total = total_cost - tax_amount
    cost_ratio = (last_month_total / total_cost) if total_cost > 0 else 0.85
    tax_prev = tax_amount * cost_ratio if tax_amount > 0 else 0

    # v1.1.30: Determine if we have period data for $/day normalization
    use_daily_rate = current_days > 0 and previous_days > 0

    # v1.1.29: Group services by AWS Official Taxonomy using service_categories.py
    # Uses full service name matching for reliability (not keyword matching)
    categorized = defaultdict(lambda: {"services": [], "total": 0})

    for service_name, service_data in services_copy.items():
        # Handle both dict format and direct float format
        if isinstance(service_data, dict):
            cost = service_data.get("cost", 0)
        else:
            cost = float(service_data) if service_data else 0

        # Use AWS Official Taxonomy for categorization
        category = categorize_aws_service(service_name)

        categorized[category]["services"].append((service_name, cost))
        categorized[category]["total"] += cost

    # v1.1.29: Build cost tree header with Tax shown separately
    # Tax displayed in header for visibility but excluded from analytical breakdown
    if tax_amount > 0:
        header = (
            f"[bold]💰 Top AWS Services by Cost[/bold]  "
            f"Current: ${analytical_total:,.1f}  "
            f"Previous: ${last_month_total - tax_prev:,.1f}  "
            f"[dim][Tax: ${tax_prev:,.1f}][/dim]"
        )
    else:
        header = (
            f"[bold]💰 Top AWS Services by Cost[/bold]  "
            f"Current: ${analytical_total:,.1f}  "
            f"Previous: ${last_month_total:,.1f}"
        )
    cost_tree = Tree(header)

    # Sort categories by total cost (descending)
    sorted_categories = sorted(categorized.items(), key=lambda x: x[1]["total"], reverse=True)

    for category, data in sorted_categories:
        if data["total"] > 0:
            # Add category branch with total cost
            pct_total = (data["total"] / total_cost * 100) if total_cost > 0 else 0
            cat_branch = cost_tree.add(
                f"[cyan]{category}[/]   Current: ${data['total']:,.1f}   % Total: {pct_total:.1f}%"
            )

            # Sort services within category by cost (descending)
            sorted_services = sorted(data["services"], key=lambda x: x[1], reverse=True)[:10]  # Top 10

            # Create service table with trending columns (v1.1.28 Track 1 restoration)
            # v1.1.31: Optimized column widths + sparklines for better UX
            svc_table = RichTable(show_header=True, header_style="bold")
            svc_table.add_column("Service", style="dim", width=40, no_wrap=True)
            svc_table.add_column("Current", justify="right", width=14, no_wrap=True)
            svc_table.add_column("Previous", justify="right", width=14, no_wrap=True)
            svc_table.add_column("% Change", justify="right", width=10, no_wrap=True)
            svc_table.add_column("% Total", justify="right", width=10, no_wrap=True)
            svc_table.add_column("Trend", justify="left", width=18, no_wrap=True)

            for svc_name, svc_cost in sorted_services:
                # v1.1.30: Get previous cost - actual if available, estimated if not
                if previous_service_costs and svc_name in previous_service_costs:
                    prev_month_cost = previous_service_costs[svc_name]
                else:
                    # Estimate previous month cost proportionally (legacy fallback)
                    prev_month_cost = svc_cost * cost_ratio

                # v1.1.30: Calculate % change with $/day normalization when period data available
                if use_daily_rate and prev_month_cost > 0:
                    # $/day normalization: same unit of measure comparison
                    current_daily = svc_cost / current_days
                    previous_daily = prev_month_cost / previous_days
                    if previous_daily > 0:
                        change_pct = ((current_daily - previous_daily) / previous_daily) * 100
                    else:
                        # v1.1.31: None indicates "New" service (no baseline for comparison)
                        change_pct = None if current_daily > 0 else 0.0
                elif prev_month_cost > 0:
                    # Legacy: direct comparison (when no period data)
                    change_pct = ((svc_cost - prev_month_cost) / prev_month_cost) * 100
                else:
                    # v1.1.31: Fix BUG #1 - New services show "New" not misleading "100%"
                    # None indicates service has no previous cost baseline for % change calculation
                    change_pct = 0 if svc_cost == 0 else None

                # Calculate percentage of total
                pct = (svc_cost / total_cost * 100) if total_cost > 0 else 0

                # Format change display with color
                # v1.1.31: Handle None (new service) with distinct indicator
                if change_pct is None:
                    change_display = "[cyan]New[/]"
                elif change_pct > 0:
                    change_display = f"[red]+{change_pct:.1f}%[/]"
                elif change_pct < 0:
                    change_display = f"[green]{change_pct:.1f}%[/]"
                else:
                    change_display = "[dim]0.0%[/]"

                # v1.1.31: Trend with sparkline bar + direction arrow (BAR-FIRST for vertical alignment)
                # Manager feedback: bars must start at same column position for visual comparison
                pct_bar = create_progress_bar_sparkline(pct, bar_width=10)  # Fixed 10-char bar
                trend_arrow = calculate_trend_arrow(change_pct)
                # Bar-first format: bar (10 chars) + space + arrow = consistent left edge
                # All bars align vertically, arrows at end for easy trend scanning
                trend_display = f"{pct_bar} {trend_arrow}"

                svc_table.add_row(
                    svc_name,
                    f"${svc_cost:,.1f}",
                    f"${prev_month_cost:,.1f}",
                    change_display,
                    f"{pct:.1f}%",
                    trend_display,
                )

            cat_branch.add(svc_table)

    return cost_tree


def run_single_account_dashboard(
    profile: str,
    timeframe: str = "monthly",
    time_range: Optional[int] = None,
    month: Optional[str] = None,  # v1.2.0: Specific month support (YYYY-MM format)
    user_regions: Optional[List[str]] = None,
    tag: Optional[List[str]] = None,
    activity_analysis: bool = False,
    dry_run: bool = False,
    export_formats: Optional[List[str]] = None,
    # v1.1.31: Persona mode support (executive|architect|sre)
    mode: str = "architect",  # v1.1.31: Default to architect (was "technical")
    top_n: Optional[int] = None,  # v1.1.31: None = use persona default
    output_format: str = "both",
    output_file: Optional[str] = None,
    cost_threshold: float = 0.0,
    sort_by: str = "cost",
    show_zero_cost: bool = True,
    validation_level: Optional[str] = None,  # v1.1.31: None = use persona default
    console_obj: Optional[Console] = None,
    verbose: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Single-account dashboard using AWS_PROFILE.

    Requires:
    - profile: AWS profile with Cost Explorer access

    Args:
        profile: AWS profile name
        timeframe: Cost aggregation timeframe (daily, weekly, monthly, quarterly)
        time_range: Optional time range in days
        user_regions: Optional list of regions to query
        tag: Optional tag filters for cost data
        activity_analysis: Enable resource activity analysis
        dry_run: Dry run mode (no AWS API calls)
        export_formats: Optional list of export formats ['json', 'csv', 'pdf']
        mode: Persona mode - executive (top 5), architect (top 20), sre (top 20 + anomalies)
        top_n: Number of top services (None = use persona default)
        validation_level: Validation level (None = use persona default)
        console_obj: Optional Console object with recording enabled (passed from CLI)

    Returns:
        Dictionary with single-account dashboard data:
        {
            'mode': 'single-account',
            'profile': str,
            'account_id': str,
            'total_cost': float,
            'services': Dict[str, float],
            'ec2_summary': Dict,
            'success': bool
        }
    """

    # v1.1.31: Get persona config and apply defaults
    persona_config = get_cli_persona_config(mode)

    # Apply persona defaults if parameters not explicitly provided
    if top_n is None:
        top_n = persona_config.top_n
    if validation_level is None:
        validation_level = persona_config.validation_level

    logger.debug(
        f"v1.1.31 Persona: mode={mode}, top_n={top_n}, "
        f"validation={validation_level}, signals={persona_config.signal_display}"
    )

    # Use passed console or fall back to module-level console
    # v1.1.28 Phase 1: Console recording must be initialized BEFORE Cost Explorer queries
    console = console_obj if console_obj is not None else globals()["console"]

    if dry_run:
        console.print(f"[yellow]🔍 DRY RUN: Single-account dashboard for {profile}[/]")

        # v1.1.28 Phase 1.2: Include mock services for tree rendering tests
        mock_services = {
            "Amazon EC2": 1200.00,
            "Amazon S3": 800.00,
            "Amazon RDS": 500.00,
            "Amazon Lambda": 300.00,
            "Amazon DynamoDB": 150.00,
        }

        mock_total_cost = 2950.00

        # v1.1.28 Phase 1.2: Render cost tree in dry_run if requested
        if output_format in ["tree", "both"] and mock_services:
            console.print(f"\n[bold cyan]💰 Top AWS Services by Cost[/bold cyan]  Current: ${mock_total_cost:,.1f}")
            cost_tree = create_service_cost_tree(mock_services, mock_total_cost, 2800.00, console)
            console.print(cost_tree)

        return {
            "mode": "single-account",
            "profile": profile,
            "dry_run": True,
            "account_id": "dry-run-account",
            "total_cost": mock_total_cost,
            "services": mock_services,
            "success": True,
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "current_month": mock_total_cost,
            "last_month": 2800.00,
        }

    # v1.1.29 Phase 3: Moved verbose header to debug (CLI layer handles display)
    logger.debug(f"Single-Account Dashboard: {profile}, timeframe={timeframe}")

    logger.info(
        "Dashboard execution started",
        extra={"operation_module": "dashboard_single", "profile": profile, "mode": mode, "timeframe": timeframe},
    )

    # Phase 4.1: Enhanced error handling with progress indicators
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=True,
        ) as progress:
            # Step 1: Get cost data using billing session
            task_cost = progress.add_task("[cyan]Fetching cost data...", total=None)

            try:
                cost_session = create_cost_session(profile_name=profile)
                cost_data = get_cost_data(cost_session, time_range, tag, profile_name=profile, month=month)
                # v1.1.30 FIX: Get actual previous service costs for per-service % Change calculation
                # This replaces the uniform ratio estimation that caused all services to show same % Change
                previous_service_costs = get_previous_month_costs(cost_session, profile_name=profile)
                progress.update(task_cost, completed=True)

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "AccessDeniedException":
                    logger.warning(
                        "Cost Explorer access denied - check IAM permissions",
                        extra={"operation_module": "dashboard_single", "profile": profile, "error_code": error_code},
                    )
                    console.print("[yellow]⚠️ Cost Explorer access denied - check IAM permissions[/]")
                    return {
                        "mode": "single-account",
                        "profile": profile,
                        "error": "insufficient_permissions",
                        "success": False,
                    }
                elif error_code == "RequestTimeTooSkewed":
                    logger.error(
                        "System clock skew detected - sync system time",
                        extra={"operation_module": "dashboard_single", "profile": profile, "error_code": error_code},
                    )
                    console.print("[red]❌ System clock skew detected - sync system time[/]")
                    raise
                else:
                    logger.error(
                        f"Cost Explorer error: {e}",
                        extra={"operation_module": "dashboard_single", "profile": profile, "error_code": error_code},
                    )
                    raise

            # Step 2: Get operational data using operational session
            task_ops = progress.add_task("[cyan]Initializing operational session...", total=None)

            ops_session = create_operational_session(profile)

            if user_regions:
                profile_regions = user_regions
            else:
                profile_regions = get_accessible_regions(ops_session)

            profile_name = ops_session.profile_name if hasattr(ops_session, "profile_name") else None
            progress.update(task_ops, completed=True)

            # Step 3: Parallel resource analysis (Phase 4.1 Enhancement #3)
            task_resources = progress.add_task("[cyan]Analyzing AWS resources...", total=None)

            # Define enrichment tasks for parallel execution
            def get_ec2_summary():
                return ec2_summary(ops_session, profile_regions, profile_name)

            def get_appstream_summary():
                try:
                    return appstream_summary(ops_session, profile_regions, profile_name)
                except Exception as e:
                    if verbose:
                        console.print(f"[dim yellow]AppStream unavailable: {str(e)[:30]}[/]")
                    return {}

            def get_ecs_summary():
                try:
                    return ecs_summary(ops_session, profile_regions, profile_name)
                except Exception as e:
                    if verbose:
                        console.print(f"[dim yellow]ECS unavailable: {str(e)[:30]}[/]")
                    return {}

            def get_cloudwatch_summary():
                try:
                    return cloudwatch_summary(ops_session, profile_regions, profile_name)
                except Exception as e:
                    if verbose:
                        console.print(f"[dim yellow]CloudWatch unavailable: {str(e)[:30]}[/]")
                    return {}

            def get_config_summary():
                try:
                    return config_summary(ops_session, profile_regions, profile_name)
                except Exception as e:
                    if verbose:
                        console.print(f"[dim yellow]Config unavailable: {str(e)[:30]}[/]")
                    return {}

            def get_cloudtrail_summary():
                try:
                    return cloudtrail_summary(ops_session, profile_regions, profile_name)
                except Exception as e:
                    if verbose:
                        console.print(f"[dim yellow]CloudTrail unavailable: {str(e)[:30]}[/]")
                    return {}

            # Execute resource gathering in parallel using parallel.py
            from concurrent.futures import ThreadPoolExecutor, as_completed

            enrichment_results = {}
            with ThreadPoolExecutor(max_workers=6) as executor:
                future_to_service = {
                    executor.submit(get_ec2_summary): "ec2",
                    executor.submit(get_appstream_summary): "appstream",
                    executor.submit(get_ecs_summary): "ecs",
                    executor.submit(get_cloudwatch_summary): "cloudwatch",
                    executor.submit(get_config_summary): "config",
                    executor.submit(get_cloudtrail_summary): "cloudtrail",
                }

                for future in as_completed(future_to_service):
                    service = future_to_service[future]
                    try:
                        enrichment_results[service] = future.result(timeout=10)
                        if verbose:
                            console.print(f"[dim green]✓ {service.capitalize()} summary complete[/]")
                    except Exception as e:
                        enrichment_results[service] = {}
                        logger.warning(
                            f"{service.capitalize()} summary failed: {str(e)}",
                            extra={"operation_module": "dashboard_single", "service": service},
                        )

            ec2_data = enrichment_results.get("ec2", {})
            appstream_data = enrichment_results.get("appstream", {})
            ecs_data = enrichment_results.get("ecs", {})
            cloudwatch_data = enrichment_results.get("cloudwatch", {})
            config_data = enrichment_results.get("config", {})
            cloudtrail_data = enrichment_results.get("cloudtrail", {})

            progress.update(task_resources, completed=True)

            # Step 4: VPC Resources Discovery (Track 4 - v1.1.28 regression fix)
            task_vpc = progress.add_task("[cyan]Discovering VPC resources...", total=None)

            vpc_data = []
            try:
                import boto3

                session = boto3.Session(profile_name=profile)
                ec2_client = session.client("ec2", region_name="ap-southeast-2")

                # 1. VPC Endpoints (VPCE)
                vpce_response = ec2_client.describe_vpc_endpoints()
                for vpce in vpce_response.get("VpcEndpoints", []):
                    vpc_data.append(
                        {
                            "resource_id": vpce["VpcEndpointId"],
                            "resource_type": "vpce",
                            "vpc_id": vpce.get("VpcId"),
                            "service_name": vpce.get("ServiceName"),
                            "state": vpce.get("State"),
                        }
                    )

                # 2. VPC Peering Connections
                peering_response = ec2_client.describe_vpc_peering_connections()
                for peering in peering_response.get("VpcPeeringConnections", []):
                    vpc_data.append(
                        {
                            "resource_id": peering["VpcPeeringConnectionId"],
                            "resource_type": "vpc_peering",
                            "vpc_id": peering.get("RequesterVpcInfo", {}).get("VpcId"),
                            "peer_vpc_id": peering.get("AccepterVpcInfo", {}).get("VpcId"),
                            "state": peering.get("Status", {}).get("Code"),
                        }
                    )

                # 3. Transit Gateways
                tgw_response = ec2_client.describe_transit_gateways()
                for tgw in tgw_response.get("TransitGateways", []):
                    vpc_data.append(
                        {
                            "resource_id": tgw["TransitGatewayId"],
                            "resource_type": "transit_gateway",
                            "state": tgw.get("State"),
                            "owner_id": tgw.get("OwnerId"),
                        }
                    )

                # 4. NAT Gateways
                nat_response = ec2_client.describe_nat_gateways()
                for nat in nat_response.get("NatGateways", []):
                    vpc_data.append(
                        {
                            "resource_id": nat["NatGatewayId"],
                            "resource_type": "nat_gateway",
                            "vpc_id": nat.get("VpcId"),
                            "subnet_id": nat.get("SubnetId"),
                            "state": nat.get("State"),
                        }
                    )

                if verbose and vpc_data:
                    console.print(f"[dim green]✓ VPC resources: {len(vpc_data)} total[/]")

                progress.update(task_vpc, completed=True)

            except Exception as vpc_error:
                if verbose:
                    console.print(f"[dim yellow]VPC resources unavailable: {str(vpc_error)[:30]}[/]")
                logger.warning(
                    f"VPC resource discovery failed: {str(vpc_error)}",
                    extra={"operation_module": "dashboard_single", "profile": profile},
                )
                progress.update(task_vpc, completed=True)

            # Step 5: Process service costs and build results
            task_process = progress.add_task("[cyan]Processing cost data...", total=None)

            service_costs, service_cost_data, others_total, grand_total = process_service_costs(cost_data, top_n=top_n)
            budget_info = format_budget_info(cost_data["budgets"])
            account_id = cost_data.get("account_id", "Unknown") or "Unknown"
            ec2_summary_text = format_ec2_summary(ec2_data)
            percent_change_in_total_cost = change_in_total_cost(cost_data["current_month"], cost_data["last_month"])

            # Build services dict for MCP validation
            # v1.2.3: Dynamic metric detection - supports UnblendedCost (default), BlendedCost, AmortizedCost
            services_dict = {}
            for group in cost_data.get("current_month_cost_by_service", []):
                if "Keys" in group and "Metrics" in group:
                    service_name = group["Keys"][0]
                    metrics = group["Metrics"]
                    cost_amount = 0.0
                    for metric_key in ["UnblendedCost", "BlendedCost", "AmortizedCost"]:
                        if metric_key in metrics:
                            cost_amount = float(metrics[metric_key]["Amount"])
                            break
                    if cost_amount > 0.001:  # Filter negligible costs
                        services_dict[service_name] = cost_amount

            progress.update(task_process, completed=True)

        # v1.1.29 Phase 3: Removed verbose intermediate output (moved to CLI layer)
        # Dashboard function returns data; CLI layer handles final display

        # v1.1.29 Phase A.1: Cost tree rendering moved to CLI layer (finops.py) to prevent duplication
        # Dashboard function is now pure data operation - tree rendering happens at CLI after activity analysis
        # COMMENTED OUT to fix manager feedback Item 1: "why we have double 💰 Top AWS Services by Cost?"
        # if output_format in ["tree", "both"] and services_dict:
        #     console.print(f"\n[bold cyan]💰 Top AWS Services by Cost[/bold cyan]  Current: ${cost_data['current_month']:,.1f}")
        #     cost_tree = create_service_cost_tree(services_dict, cost_data['current_month'], cost_data['last_month'], console)
        #     console.print(cost_tree)

        # Build result dictionary
        result = {
            "mode": "single-account",
            "profile": profile,
            "account_id": account_id,
            "last_month": cost_data["last_month"],
            "current_month": cost_data["current_month"],
            "total_cost": cost_data["current_month"],
            "services": services_dict,
            "start_date": cost_data.get("current_period_start"),
            "end_date": cost_data.get("current_period_end"),
            "service_costs": service_cost_data,
            "service_costs_formatted": service_costs,
            "service_costs_others_total": others_total,
            "service_costs_grand_total": grand_total,
            "budget_info": budget_info,
            "ec2_summary": ec2_data,
            "ec2_summary_formatted": ec2_summary_text,
            "appstream_summary": appstream_data,
            "ecs_summary": ecs_data,
            "cloudwatch_summary": cloudwatch_data,
            "config_summary": config_data,
            "cloudtrail_summary": cloudtrail_data,
            "vpc_summary": vpc_data,  # Track 4: VPC resources for activity analysis
            "success": True,
            "error": None,
            "current_period_name": cost_data["current_period_name"],
            "previous_period_name": cost_data["previous_period_name"],
            "percent_change_in_total_cost": percent_change_in_total_cost,
            "timeframe": timeframe,
            "previous_service_costs": previous_service_costs,  # v1.1.30 FIX: For per-service % Change
        }

        logger.info(
            "Dashboard execution completed successfully",
            extra={
                "operation_module": "dashboard_single",
                "profile": profile,
                "account_id": account_id,
                "total_cost": cost_data["current_month"],
                "service_count": len(services_dict),
            },
        )

        # v1.1.28 Phase 1 Fix: Export moved to CLI layer (after rich display)
        # Dashboard function is now pure data operation (no file writes)
        # Export happens at finops.py:6084-6130 with full console buffer
        return result

    except Exception as e:
        logger.error(
            f"Error processing profile: {str(e)}",
            extra={"operation_module": "dashboard_single", "profile": profile},
            exc_info=True,
        )
        console.print(f"[red]❌ Error processing profile {profile}: {str(e)}[/]")
        return {
            "mode": "single-account",
            "profile": profile,
            "account_id": "Error",
            "last_month": 0,
            "current_month": 0,
            "total_cost": 0,
            "services": {},
            "service_costs": [],
            "service_costs_formatted": [f"Failed to process profile: {str(e)}"],
            "budget_info": ["N/A"],
            "ec2_summary": {"N/A": 0},
            "ec2_summary_formatted": ["Error"],
            "appstream_summary": {},
            "ecs_summary": {},
            "cloudwatch_summary": {},
            "config_summary": {},
            "cloudtrail_summary": {},
            "success": False,
            "error": str(e),
            "current_period_name": "Current month",
            "previous_period_name": "Last month",
            "percent_change_in_total_cost": None,
            "timeframe": timeframe,
        }


def run_audit_report(profile: str, dry_run: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Run audit report for single account.

    Wrapper for audit.run_audit_report() with single-account context.
    Discovers optimization opportunities including untagged resources,
    stopped instances, unused volumes, and unused EIPs.

    Args:
        profile: AWS profile name
        dry_run: Dry run mode (no AWS API calls)
        **kwargs: Additional arguments passed to audit module

    Returns:
        Dictionary with audit report data including:
        - optimization_opportunities: List of resource optimization findings
        - total_potential_savings: Estimated annual savings
        - profiles: List of profile-specific audit results
    """
    # Create argument namespace for audit module
    args = argparse.Namespace(dry_run=dry_run, **{k: v for k, v in kwargs.items() if k in ["top_n", "output_format"]})

    # Convert single profile to list for audit module
    profiles_list = [profile]

    # Call audit module
    console.print(f"\n[bold cyan]📋 Running Audit Report: {profile}[/]")
    result = audit.run_audit_report(profiles_list, args)

    return result


def run_trend_analysis(profile: str, months: int = 6, dry_run: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Run 6-month cost trend analysis for single account.

    Wrapper for trends.run_trend_analysis() with single-account context.
    Analyzes historical cost patterns and identifies trends.

    Args:
        profile: AWS profile name
        months: Number of months to analyze (default: 6)
        dry_run: Dry run mode (no AWS API calls)
        **kwargs: Additional arguments passed to trends module

    Returns:
        Dictionary with trend analysis data including:
        - monthly_costs: List of monthly cost data points
        - trend_direction: Overall trend direction (increasing/decreasing/stable)
        - percentage_changes: Month-over-month percentage changes
    """
    # Create argument namespace for trends module
    args = argparse.Namespace(
        dry_run=dry_run, months=months, **{k: v for k, v in kwargs.items() if k in ["output_format", "export_json"]}
    )

    # Convert single profile to list for trends module
    profiles_list = [profile]

    # Call trends module
    console.print(f"\n[bold cyan]📈 Running Trend Analysis: {profile}[/]")
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
    console.print(f"\n[bold cyan]💼 Calculating Business Case[/]")
    console.print(f"[dim]Annual Savings: ${annual_savings:,.2f}[/]")
    console.print(f"[dim]Implementation Hours: {implementation_hours}[/]")

    # Call business case module
    result = business_case.calculate_roi_metrics(annual_savings, implementation_hours)

    return result
