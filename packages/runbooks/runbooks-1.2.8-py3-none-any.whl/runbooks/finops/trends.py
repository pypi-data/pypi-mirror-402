#!/usr/bin/env python3
"""
FinOps Trend Analysis Module

Comprehensive 6-month cost trend analysis with enhanced visualization.
Extracted from dashboard_runner.py for KISS/DRY/LEAN architecture.

Key Features:
- 6-month historical cost trend analysis
- Enhanced Rich CLI visualization with color-coded indicators
- Month-over-month percentage calculations
- Trend direction arrows and insights
- Resource-based estimation when Cost Explorer blocked
- JSON export for audit trail

Author: Runbooks Team
Version: 1.0.0
"""

import argparse
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from runbooks.common.profile_utils import (
    create_cost_session,
    create_management_session,
    resolve_profile_for_operation_silent,
)
from runbooks.common.rich_utils import console
from runbooks.finops.aws_client import get_account_id
from runbooks.finops.cost_processor import get_trend
from runbooks.finops.helpers import export_trend_data_to_json


def run_trend_analysis(
    profiles_to_use: List[str],
    args: argparse.Namespace,
) -> Dict[str, Any]:
    """
    Analyze and display cost trends with enhanced visualization.

    This function provides comprehensive 6-month cost trend analysis with:
    - Enhanced Rich CLI visualization matching reference screenshot
    - Color-coded trend indicators (Green/Yellow/Red)
    - Month-over-month percentage calculations
    - Trend direction arrows and insights
    - Resource-based estimation when Cost Explorer blocked
    - JSON-only export (contract compliance)

    Args:
        profiles_to_use: List of AWS profiles to analyze
        args: Command line arguments including:
            - profile: User-specified profile for explicit override
            - all_profile: Flag for multi-account aggregation
            - tag: Optional tag filter for cost grouping
            - combine: Boolean flag to combine profiles by account
            - report_name: Base filename for JSON export
            - report_type: List of export formats (only 'json' supported)
            - dir: Output directory for exported reports

    Returns:
        Dict containing trend analysis results with monthly costs and metadata

    Performance:
        - Uses enhanced trend visualizer for rich output
        - Supports both individual and combined account views
        - Progress tracking for user feedback
        - Graceful error handling with detailed logging

    Example:
        >>> trend_data = run_trend_analysis(
        ...     profiles_to_use=['default'],
        ...     args=argparse.Namespace(
        ...         profile='default',
        ...         all_profile=False,
        ...         tag=None,
        ...         combine=False,
        ...         report_name='trends-2024',
        ...         report_type=['json'],
        ...         dir='reports/'
        ...     )
        ... )
        >>> print(f"Analyzed {trend_data['profile_count']} profiles")
    """
    console.print("[bold bright_cyan]📈 Enhanced Cost Trend Analysis[/]")
    console.print("[dim]QA Testing Specialist - Reference Image Compliant Implementation[/]")

    # Display billing profile information with universal --profile override support
    # v1.1.23: Context-aware display - suppress for single-account mode (Issue #4)
    user_profile = getattr(args, "profile", None)
    all_profile = getattr(args, "all_profile", None)
    billing_profile = resolve_profile_for_operation_silent("billing", user_profile)

    # Detect single-account context (--profile without --all-profile)
    is_single_account = user_profile and not all_profile

    if not is_single_account:
        # Multi-account or default mode: Show billing context
        if user_profile:
            console.print(f"[green]Using --profile override for cost data: {billing_profile}[/]")
        elif os.getenv("BILLING_PROFILE"):
            console.print(f"[dim cyan]Using billing profile for cost data: {billing_profile}[/]")
        else:
            console.print(f"[dim cyan]Using default profile for cost data: {billing_profile}[/]")
    # Single-account mode: Suppress billing context (user already knows the profile)

    # Use enhanced trend visualizer
    from runbooks.finops.enhanced_trend_visualization import EnhancedTrendVisualizer

    enhanced_visualizer = EnhancedTrendVisualizer(console=console)

    raw_trend_data = []

    # Enhanced progress tracking for trend analysis
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        if hasattr(args, "combine") and args.combine:
            account_profiles = defaultdict(list)
            task1 = progress.add_task("Grouping profiles by account", total=len(profiles_to_use))

            for profile in profiles_to_use:
                try:
                    # Use management session to get account ID
                    session = create_management_session(profile)
                    account_id = get_account_id(session)
                    if account_id:
                        account_profiles[account_id].append(profile)
                except Exception as e:
                    console.print(f"[red]Error checking account ID for profile {profile}: {str(e)}[/]")
                progress.advance(task1)

            task2 = progress.add_task("Fetching cost trends", total=len(account_profiles))
            for account_id, profiles in account_profiles.items():
                progress.update(task2, description=f"Fetching trends for account: {account_id}")
                try:
                    primary_profile = profiles[0]
                    # Use billing session for cost trend data
                    cost_session = create_cost_session(profile_name=primary_profile)
                    tag_filter = getattr(args, "tag", None)
                    cost_data = get_trend(cost_session, tag_filter)
                    trend_data = cost_data.get("monthly_costs")

                    if not trend_data:
                        console.print(f"[yellow]No trend data available for account {account_id}[/]")
                        continue

                    profile_list = ", ".join(profiles)
                    console.print(f"\n[bright_yellow]Account: {account_id} (Profiles: {profile_list})[/]")
                    raw_trend_data.append(cost_data)

                    # Use enhanced visualization
                    enhanced_visualizer.create_enhanced_trend_display(
                        monthly_costs=trend_data, account_id=account_id, profile=f"Combined: {profile_list}"
                    )
                except Exception as e:
                    console.print(f"[red]Error getting trend for account {account_id}: {str(e)}[/]")
                progress.advance(task2)

        else:
            task3 = progress.add_task("Fetching individual trends", total=len(profiles_to_use))
            for profile in profiles_to_use:
                progress.update(task3, description=f"Processing profile: {profile}")
                try:
                    # Use billing session for cost data
                    cost_session = create_cost_session(profile_name=profile)
                    # Use management session for account ID
                    mgmt_session = create_management_session(profile)

                    tag_filter = getattr(args, "tag", None)
                    cost_data = get_trend(cost_session, tag_filter)
                    trend_data = cost_data.get("monthly_costs")
                    account_id = get_account_id(mgmt_session) or cost_data.get("account_id", "Unknown")

                    if not trend_data:
                        console.print(f"[yellow]No trend data available for profile {profile}[/]")
                        continue

                    console.print(f"\n[bright_yellow]Account: {account_id} (Profile: {profile})[/]")
                    raw_trend_data.append(cost_data)

                    # Use enhanced visualization
                    enhanced_visualizer.create_enhanced_trend_display(
                        monthly_costs=trend_data, account_id=account_id, profile=profile
                    )
                except Exception as e:
                    console.print(f"[red]Error getting trend for profile {profile}: {str(e)}[/]")
                progress.advance(task3)

    # Export to JSON if requested
    export_path = None
    if (
        raw_trend_data
        and hasattr(args, "report_name")
        and args.report_name
        and hasattr(args, "report_type")
        and args.report_type
    ):
        if "json" in args.report_type:
            json_path = export_trend_data_to_json(raw_trend_data, args.report_name, args.dir)
            if json_path:
                # Enhanced export confirmation with file size
                file_size = os.path.getsize(json_path) if os.path.exists(json_path) else 0
                file_size_mb = file_size / (1024 * 1024)
                if file_size_mb >= 1:
                    size_str = f"{file_size_mb:.1f} MB"
                else:
                    size_str = f"{file_size / 1024:.1f} KB"
                console.print(f"[bright_green]✅ Trend data exported to JSON: {json_path} ({size_str})[/]")
                export_path = json_path

    # Return trend analysis summary
    return {
        "trend_data": raw_trend_data,
        "profile_count": len(profiles_to_use),
        "account_count": len(raw_trend_data),
        "export_path": export_path,
        "combined_mode": hasattr(args, "combine") and args.combine,
    }
