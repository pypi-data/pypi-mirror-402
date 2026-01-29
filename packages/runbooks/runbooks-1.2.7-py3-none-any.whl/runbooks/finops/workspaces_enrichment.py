#!/usr/bin/env python3
"""
WorkSpaces Enrichment Module - Production AWS API Integration

Provides reusable WorkSpaces enrichment functions for notebook consumption:
- WorkSpaces context enrichment (13 columns from DescribeWorkspaces API)
- CloudTrail activity analysis (90-day lookback, idle detection)
- Cost Explorer 12-month trailing cost data

Design Pattern:
    - Reuses workspaces_analyzer.py patterns
    - Rich CLI output throughout (no print())
    - Profile cascade: param > $AWS_PROFILE
    - Enterprise error handling with graceful fallback

Usage:
    from runbooks.finops.workspaces_enrichment import (
        enrich_with_workspaces_context,
        analyze_workspaces_cloudtrail,
        get_workspaces_cost_data
    )

    # Enrich WorkSpaces inventory with AWS API data
    enriched_df = enrich_with_workspaces_context(df, profile='operational')
    enriched_df = analyze_workspaces_cloudtrail(enriched_df, profile='management')
    enriched_df = get_workspaces_cost_data(enriched_df, profile='billing')
"""

import logging
import os
from typing import Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from ..common.rich_utils import (
    console,
    create_progress_bar,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


def _calculate_connection_age(last_connection_timestamp) -> int:
    """
    Calculate days since last WorkSpace connection (W1 signal).

    Args:
        last_connection_timestamp: AWS timestamp (ISO format string or datetime object)

    Returns:
        Days since last connection (9999 if never connected)

    Example:
        >>> _calculate_connection_age('2025-10-01T12:00:00Z')
        29  # If today is 2025-10-30
        >>> _calculate_connection_age(None)
        9999  # Never connected
    """
    from datetime import datetime, timezone

    if last_connection_timestamp is None or pd.isna(last_connection_timestamp):
        return 9999  # Never connected

    now = datetime.now(timezone.utc)

    # Handle ISO format strings
    if isinstance(last_connection_timestamp, str):
        if last_connection_timestamp in ["Never", "N/A", ""]:
            return 9999
        try:
            last_connection = datetime.fromisoformat(last_connection_timestamp.replace("Z", "+00:00"))
        except ValueError:
            return 9999  # Invalid timestamp format
    else:
        last_connection = last_connection_timestamp

    # Ensure timezone-aware datetime
    if last_connection.tzinfo is None:
        last_connection = last_connection.replace(tzinfo=timezone.utc)

    delta = now - last_connection
    return max(0, delta.days)  # Prevent negative days


def enrich_with_workspaces_context(df: pd.DataFrame, profile: Optional[str] = None) -> pd.DataFrame:
    """
    Enrich DataFrame with WorkSpaces context from DescribeWorkspaces API.

    Adds 15 columns including:
    - WorkSpace metadata: WorkSpace ID, Username, State, Bundle ID, Running Mode
    - Network: VPC ID, Subnet ID, IP Address, Directory ID
    - Configuration: Protocol, User Volume, Root Volume
    - Timing: Last Known User Connection Timestamp
    - W1 Signal: Days Since Last Connection, W1 Connection Recency Score (45 points)

    Pattern: Reuses workspaces_analyzer.py enrichment pattern

    Args:
        df: pandas DataFrame with 'AWS Account' and 'Region' columns
        profile: AWS profile (priority: param > $AWS_PROFILE > 'default')

    Returns:
        DataFrame with WorkSpaces enrichment columns added

    Example:
        >>> df = pd.read_excel('inventory.xlsx', sheet_name='workspaces')
        >>> enriched_df = enrich_with_workspaces_context(df, profile='operational')
        >>> # DataFrame now has 15 additional WorkSpaces columns (including W1 signal)
    """
    try:
        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="operational", user_specified_profile=profile, silent=True)

        print_info(f"🔍 Enriching with WorkSpaces context (profile: {profile})...")

        # Initialize WorkSpaces enrichment columns (15 columns including W1 signal)
        workspaces_columns = [
            "workspace_id",
            "username",
            "state",
            "bundle_id",
            "running_mode",
            "vpc_id",
            "subnet_id",
            "ip_address",
            "directory_id",
            "protocol",
            "user_volume_gb",
            "root_volume_gb",
            "last_known_user_connection",
            "days_since_last_connection",
            "w1_connection_recency_score",
        ]

        for col in workspaces_columns:
            if col in ["days_since_last_connection", "w1_connection_recency_score"]:
                df[col] = 0  # Numeric columns default to 0
            else:
                df[col] = "N/A"

        enriched_count = 0
        from runbooks.common.profile_utils import create_operational_session, create_timeout_protected_client

        session = create_operational_session(profile)

        # Group by account and region for batch processing
        account_region_groups = df.groupby(["AWS Account", "Region"])

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Enriching WorkSpaces...", total=len(account_region_groups))

            for (account_id, region), group_df in account_region_groups:
                try:
                    ws_client = session.client("workspaces", region_name=region)

                    # Query all WorkSpaces in this account/region
                    paginator = ws_client.get_paginator("describe_workspaces")
                    all_workspaces = []

                    for page in paginator.paginate():
                        all_workspaces.extend(page.get("Workspaces", []))

                    # Build WorkSpace lookup by workspace ID
                    workspace_lookup = {ws.get("WorkspaceId"): ws for ws in all_workspaces}

                    # Enrich rows
                    for idx, row in group_df.iterrows():
                        # Try to find workspace by matching criteria
                        workspace_id = row.get("WorkSpace ID") or row.get("WorkspaceId") or row.get("Identifier")

                        if workspace_id and workspace_id in workspace_lookup:
                            workspace = workspace_lookup[workspace_id]

                            # Extract workspace metadata
                            df.at[idx, "workspace_id"] = workspace.get("WorkspaceId", "N/A")
                            df.at[idx, "username"] = workspace.get("UserName", "N/A")

                            # State and configuration
                            df.at[idx, "state"] = workspace.get("State", "N/A")
                            df.at[idx, "bundle_id"] = workspace.get("BundleId", "N/A")

                            # Running mode
                            properties = workspace.get("WorkspaceProperties", {})
                            df.at[idx, "running_mode"] = properties.get("RunningMode", "N/A")
                            df.at[idx, "protocol"] = (
                                properties.get("Protocols", ["N/A"])[0] if properties.get("Protocols") else "N/A"
                            )

                            # Volume sizes
                            df.at[idx, "user_volume_gb"] = str(properties.get("UserVolumeSizeGib", "N/A"))
                            df.at[idx, "root_volume_gb"] = str(properties.get("RootVolumeSizeGib", "N/A"))

                            # Network
                            df.at[idx, "vpc_id"] = (
                                workspace.get("VpcId", "N/A") or workspace.get("SubnetId", "N/A").split("-")[0]
                                if workspace.get("SubnetId")
                                else "N/A"
                            )
                            df.at[idx, "subnet_id"] = workspace.get("SubnetId", "N/A")
                            df.at[idx, "ip_address"] = workspace.get("IpAddress", "N/A")
                            df.at[idx, "directory_id"] = workspace.get("DirectoryId", "N/A")

                            # Connection status (requires separate API call)
                            try:
                                conn_response = ws_client.describe_workspaces_connection_status(
                                    WorkspaceIds=[workspace_id]
                                )

                                conn_status = conn_response.get("WorkspacesConnectionStatus", [])
                                if conn_status:
                                    last_conn = conn_status[0].get("LastKnownUserConnectionTimestamp")
                                    if last_conn:
                                        df.at[idx, "last_known_user_connection"] = last_conn.isoformat()

                                        # W1 Signal: Calculate connection age and score
                                        days_since = _calculate_connection_age(last_conn)
                                        df.at[idx, "days_since_last_connection"] = days_since

                                        # W1 scoring: 45 points if ≥60 days idle
                                        df.at[idx, "w1_connection_recency_score"] = 45 if days_since >= 60 else 0
                                    else:
                                        df.at[idx, "last_known_user_connection"] = "Never"
                                        df.at[idx, "days_since_last_connection"] = 9999
                                        df.at[idx, "w1_connection_recency_score"] = (
                                            45  # Never connected = decommission signal
                                        )
                            except ClientError:
                                # Connection status API may fail, keep default
                                pass

                            enriched_count += 1

                except ClientError as e:
                    logger.warning(f"WorkSpaces API error for {account_id}/{region}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error enriching {account_id}/{region}: {e}")

                progress.update(task, advance=1)

        enrichment_rate = (enriched_count / len(df) * 100) if len(df) > 0 else 0
        print_success(
            f"✅ WorkSpaces context enrichment complete: {enriched_count}/{len(df)} WorkSpaces ({enrichment_rate:.1f}%)"
        )

        return df

    except Exception as e:
        print_error(f"❌ WorkSpaces context enrichment failed: {e}")
        logger.error(f"WorkSpaces enrichment error: {e}", exc_info=True)
        return df


def analyze_workspaces_cloudtrail(
    df: pd.DataFrame, profile: Optional[str] = None, lookback_days: int = 90
) -> pd.DataFrame:
    """
    Analyze WorkSpaces activity via CloudTrail (90-day lookback).

    Adds 4 columns:
    - last_activity_date: Date of last CloudTrail event (YYYY-MM-DD)
    - days_since_activity: Days since last activity
    - event_count: Total CloudTrail events in lookback window
    - is_idle: True if no activity >30 days

    Pattern: Reuses EC2 CloudTrail pattern (same API calls)

    Args:
        df: pandas DataFrame with 'workspace_id' column (from enrich_with_workspaces_context)
        profile: AWS profile for CloudTrail access (typically management account)
        lookback_days: Days to look back (default: 90, max: 90)

    Returns:
        DataFrame with CloudTrail activity columns added

    Example:
        >>> df = enrich_with_workspaces_context(df, profile='operational')
        >>> df = analyze_workspaces_cloudtrail(df, profile='management', lookback_days=90)
        >>> idle_workspaces = df[df['is_idle'] == True]
    """
    try:
        from datetime import datetime, timedelta, timezone

        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="management", user_specified_profile=profile, silent=True)

        print_info(f"🔍 Analyzing CloudTrail activity ({lookback_days}-day lookback, profile: {profile})...")

        # Validate lookback window
        if lookback_days > 90:
            print_warning(f"⚠️  Lookback {lookback_days} days exceeds CloudTrail retention (90 days), capping at 90")
            lookback_days = 90

        # Initialize columns
        df["last_activity_date"] = "Never"
        df["days_since_activity"] = lookback_days
        df["event_count"] = 0
        df["is_idle"] = True

        # Calculate time window
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(days=lookback_days)

        from runbooks.common.profile_utils import create_management_session, create_timeout_protected_client

        session = create_management_session(profile)
        analyzed_count = 0
        idle_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Analyzing CloudTrail events...", total=len(df))

            for idx, row in df.iterrows():
                workspace_id = row.get("workspace_id")

                if workspace_id and workspace_id != "N/A" and workspace_id.startswith("ws-"):
                    try:
                        # Get region for CloudTrail client
                        region = row.get("Region", "ap-southeast-2")
                        cloudtrail_client = session.client("cloudtrail", region_name=region)

                        # Query CloudTrail for workspace-specific events
                        events = []
                        response = cloudtrail_client.lookup_events(
                            LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": workspace_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            MaxResults=50,
                        )

                        events.extend(response.get("Events", []))

                        # Handle pagination
                        while "NextToken" in response:
                            response = cloudtrail_client.lookup_events(
                                LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": workspace_id}],
                                StartTime=start_time,
                                EndTime=end_time,
                                NextToken=response["NextToken"],
                                MaxResults=50,
                            )
                            events.extend(response.get("Events", []))

                        if events:
                            # Extract last access timestamp
                            last_access = max(event["EventTime"] for event in events)
                            df.at[idx, "last_activity_date"] = last_access.strftime("%Y-%m-%d")
                            df.at[idx, "event_count"] = len(events)

                            # Calculate idle classification (>30 days = idle)
                            days_since_access = (datetime.now(last_access.tzinfo) - last_access).days
                            df.at[idx, "days_since_activity"] = days_since_access
                            df.at[idx, "is_idle"] = days_since_access > 30

                            if days_since_access <= 30:
                                analyzed_count += 1
                            else:
                                idle_count += 1
                        else:
                            # No activity in lookback window
                            idle_count += 1

                    except ClientError as e:
                        logger.warning(f"CloudTrail query failed for {workspace_id}: {e}")
                        # Keep defaults (Never, lookback_days, 0, True)

                progress.update(task, advance=1)

        print_success(f"✅ CloudTrail analysis complete")
        print_info(f"   Active (≤30 days): {analyzed_count} | Idle (>30 days): {idle_count}")

        return df

    except Exception as e:
        print_error(f"❌ CloudTrail activity analysis failed: {e}")
        logger.error(f"CloudTrail analysis error: {e}", exc_info=True)
        return df


def get_workspaces_cost_data(df: pd.DataFrame, profile: Optional[str] = None, period_months: int = 12) -> pd.DataFrame:
    """
    Enrich with Cost Explorer 12-month trailing actuals for WorkSpaces.

    Adds 3 columns:
    - monthly_cost: Average monthly cost (12-month average)
    - annual_cost_12mo: Total 12-month cost
    - cost_trend: Cost trend (↑ Increasing / → Stable / ↓ Decreasing)

    Pattern: Reuses Cost Explorer pattern with WorkSpaces service filter

    Args:
        df: pandas DataFrame with 'AWS Account' column
        profile: AWS profile for Cost Explorer access (billing account)
        period_months: Number of months to query (default: 12)

    Returns:
        DataFrame with Cost Explorer columns added

    Example:
        >>> df = enrich_with_workspaces_context(df, profile='operational')
        >>> df = get_workspaces_cost_data(df, profile='billing', period_months=12)
        >>> high_cost_workspaces = df[df['annual_cost_12mo'] > 500]
    """
    try:
        from datetime import datetime, timedelta

        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="billing", user_specified_profile=profile, silent=True)

        print_info(f"🔍 Fetching {period_months}-month Cost Explorer data (profile: {profile})...")

        # Initialize cost columns
        df["monthly_cost"] = 0.0
        df["annual_cost_12mo"] = 0.0
        df["cost_trend"] = "→ Stable"

        # Calculate period
        today = datetime.now()
        first_of_current_month = today.replace(day=1)
        end_date = first_of_current_month - timedelta(days=1)
        start_date = end_date - timedelta(days=30 * period_months) + timedelta(days=1)

        from runbooks.common.profile_utils import create_cost_session, create_timeout_protected_client

        session = create_cost_session(profile)
        ce_client = create_timeout_protected_client(session, "ce", "ap-southeast-2")

        # Get unique account IDs
        account_ids = df["AWS Account"].unique().tolist()

        print_info(f"   Querying {len(account_ids)} accounts for WorkSpaces costs...")

        # Query Cost Explorer (filter for Amazon WorkSpaces service)
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            Filter={
                "And": [
                    {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon WorkSpaces"]}},
                    {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [str(acc) for acc in account_ids]}},
                ]
            },
            GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
        )

        # Aggregate costs by account
        account_costs = {}
        monthly_breakdown = {}

        for month_data in response["ResultsByTime"]:
            month_start = month_data["TimePeriod"]["Start"]

            for group in month_data["Groups"]:
                account_id = group["Keys"][0]
                cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

                if account_id not in account_costs:
                    account_costs[account_id] = 0.0
                    monthly_breakdown[account_id] = []

                account_costs[account_id] += cost
                monthly_breakdown[account_id].append({"month": month_start, "cost": cost})

        # Enrich DataFrame with cost data
        enriched_count = 0
        for account_id in account_ids:
            if str(account_id) in account_costs:
                total_cost = account_costs[str(account_id)]
                avg_monthly = total_cost / period_months

                # Update all WorkSpaces in this account
                mask = df["AWS Account"] == account_id
                workspace_count = mask.sum()

                if workspace_count > 0:
                    # Distribute cost equally across WorkSpaces (simple allocation)
                    df.loc[mask, "monthly_cost"] = avg_monthly / workspace_count
                    df.loc[mask, "annual_cost_12mo"] = total_cost / workspace_count

                    # Calculate trend (first half vs second half)
                    breakdown = monthly_breakdown[str(account_id)]
                    if len(breakdown) >= 6:
                        first_half = sum(m["cost"] for m in breakdown[:6])
                        second_half = sum(m["cost"] for m in breakdown[6:])

                        if second_half > first_half * 1.1:
                            trend = "↑ Increasing"
                        elif second_half < first_half * 0.9:
                            trend = "↓ Decreasing"
                        else:
                            trend = "→ Stable"

                        df.loc[mask, "cost_trend"] = trend

                    enriched_count += workspace_count

        enrichment_rate = (enriched_count / len(df) * 100) if len(df) > 0 else 0
        print_success(
            f"✅ Cost Explorer enrichment complete: {enriched_count}/{len(df)} WorkSpaces ({enrichment_rate:.1f}%)"
        )

        return df

    except Exception as e:
        print_error(f"❌ Cost Explorer enrichment failed: {e}")
        logger.error(f"Cost Explorer error: {e}", exc_info=True)
        return df
