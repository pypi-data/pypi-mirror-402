#!/usr/bin/env python3
"""
WorkSpaces Signals Module - W2-W7 Decommission Scoring Signals

Implements WorkSpaces-specific decommission signals for enterprise cost optimization:
- W2: CloudWatch UserConnected explicit validation (25 points)
- W3: Dynamic break-even analysis via AWS Pricing API (10 points)
- W4: AutoStop policy validation (10 points)
- W5: CloudTrail admin activity detection (5 points)
- W6: Identity Center user status validation (5 points)
- W7: Volume encryption compliance validation (5 points)

Combined with W1 (connection recency from workspaces_enrichment.py - 45 points), provides
complete 105-point scoring framework for WorkSpaces decommission classification.

Design Pattern:
    - Reuses boto3 patterns from ec2_enrichment.py
    - Rich CLI output throughout (no print())
    - Profile cascade: param > $AWS_PROFILE
    - Enterprise error handling with graceful fallback

Usage:
    from runbooks.finops.workspaces_signals import (
        get_w2_cloudwatch_sessions,
        calculate_w3_breakeven_dynamic,
        check_w4_autostop_policy,
        analyze_w5_admin_activity,
        validate_w6_user_status,
        validate_w7_volume_encryption
    )

    # W2: Explicit CloudWatch validation
    w2_results = get_w2_cloudwatch_sessions(workspace_ids, profile='operational')

    # W3: Dynamic break-even analysis
    w3_results = calculate_w3_breakeven_dynamic(df, profile='billing')

    # W4: AutoStop policy check
    w4_results = check_w4_autostop_policy(workspace_ids, profile='operational')

    # W5: Admin activity analysis
    w5_results = analyze_w5_admin_activity(workspace_ids, profile='management')

    # W6: User status validation
    w6_results = validate_w6_user_status(usernames, profile='management')

    # W7: Volume encryption compliance
    w7_results = validate_w7_volume_encryption(workspace_ids, profile='operational')

Strategic Alignment:
- Objective 1 (runbooks package): Reusable WorkSpaces decommission analysis
- Enterprise SDLC: Evidence-based scoring with audit trails
- KISS/DRY/LEAN: Reuse enrichment patterns, enhance existing framework
"""

import logging
import os
from datetime import datetime, timedelta, timezone
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


def get_w2_cloudwatch_sessions(
    workspace_ids: List[str], profile: Optional[str] = None, region: str = "ap-southeast-2", lookback_days: int = 30
) -> Dict[str, Dict]:
    """
    W2 Signal: CloudWatch UserConnected metric explicit validation (25 points).

    Queries CloudWatch UserConnected metric for explicit session validation.
    UserConnected = 1 when connected, 0 when disconnected.
    Sum over lookback period: 0 = no sessions = 25 points.

    Signal W2: No UserConnected events in 30+ days → +25 points

    Args:
        workspace_ids: List of WorkSpace IDs to check
        profile: AWS profile name (default: $AWS_PROFILE)
        region: AWS region (default: ap-southeast-2)
        lookback_days: Days to look back for sessions (default: 30)

    Returns:
        Dictionary mapping workspace IDs to W2 results:
        {
            'ws-abc123': {
                'w2_score': 25,  # 25 if no sessions, 0 if active
                'session_sum': 0,
                'evidence': 'No sessions in 30 days',
                'lookback_days': 30,
                'data_points': 0
            }
        }

    Example:
        >>> w2_results = get_w2_cloudwatch_sessions(
        ...     workspace_ids=['ws-abc123', 'ws-def456'],
        ...     profile='operational',
        ...     lookback_days=30
        ... )
        >>> idle_workspaces = [ws for ws, r in w2_results.items() if r['w2_score'] == 15]
    """
    try:
        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="operational", user_specified_profile=profile, silent=True)

        print_info(
            f"🔍 W2 Signal: Checking CloudWatch UserConnected metrics ({lookback_days}-day lookback, region: {region}, profile: {profile})..."
        )

        session = boto3.Session(profile_name=profile)
        cw_client = session.client("cloudwatch", region_name=region)

        w2_results = {}
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(days=lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Querying CloudWatch metrics...", total=len(workspace_ids))

            for workspace_id in workspace_ids:
                try:
                    # Query UserConnected metric
                    response = cw_client.get_metric_statistics(
                        Namespace="AWS/WorkSpaces",
                        MetricName="UserConnected",
                        Dimensions=[{"Name": "WorkspaceId", "Value": workspace_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # 1-hour periods
                        Statistics=["Sum"],
                    )

                    datapoints = response.get("Datapoints", [])

                    # Calculate total sessions (sum over all data points)
                    session_sum = sum(dp.get("Sum", 0) for dp in datapoints)

                    # Score: 25 points if no sessions
                    w2_score = 25 if session_sum == 0 else 0

                    # Build evidence
                    if session_sum == 0:
                        evidence = f"No sessions in {lookback_days} days"
                    else:
                        evidence = f"Active: {int(session_sum)} sessions detected"

                    w2_results[workspace_id] = {
                        "w2_score": w2_score,
                        "session_sum": session_sum,
                        "evidence": evidence,
                        "lookback_days": lookback_days,
                        "data_points": len(datapoints),
                    }

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    if error_code == "ResourceNotFoundException":
                        # WorkSpace not found in CloudWatch (possibly new or deleted)
                        w2_results[workspace_id] = {
                            "w2_score": 0,
                            "session_sum": 0,
                            "evidence": "No CloudWatch data available",
                            "lookback_days": lookback_days,
                            "data_points": 0,
                        }
                    else:
                        logger.warning(f"CloudWatch query failed for {workspace_id}: {e}")
                        w2_results[workspace_id] = {
                            "w2_score": 0,
                            "session_sum": 0,
                            "evidence": f"Error: {error_code}",
                            "lookback_days": lookback_days,
                            "data_points": 0,
                        }

                progress.update(task, advance=1)

        idle_count = len([r for r in w2_results.values() if r["w2_score"] == 25])
        print_success(f"✅ W2 signal analysis complete: {idle_count}/{len(workspace_ids)} idle WorkSpaces")

        return w2_results

    except Exception as e:
        print_error(f"❌ W2 signal analysis failed: {e}")
        logger.error(f"W2 signal error: {e}", exc_info=True)
        return {
            ws: {"w2_score": 0, "session_sum": 0, "evidence": "Error", "lookback_days": lookback_days, "data_points": 0}
            for ws in workspace_ids
        }


def calculate_w3_breakeven_dynamic(
    bundle_ids: Dict[str, str], region: str = "ap-southeast-2", profile: Optional[str] = None
) -> Dict[str, Dict]:
    """
    W3 Signal: Dynamic break-even analysis via AWS Pricing API (10 points).

    Queries AWS Pricing API for dynamic break-even calculation.
    Break-even = monthly_cost / hourly_rate (hours).

    Signal W3: 10 points if usage < break-even, 5 points if usage > break-even

    Args:
        bundle_ids: Dict mapping WorkSpace IDs to bundle IDs
                   {'ws-xxxxx': 'wsb-abc123', ...}
        region: AWS region for pricing (default: ap-southeast-2)
        profile: AWS profile name

    Returns:
        Dictionary mapping WorkSpace IDs to break-even analysis:
        {
            'ws-xxxxx': {
                'w3_score': 10,              # 10 if under break-even, 5 if over
                'breakeven_hours': 86.2,     # Monthly hours threshold
                'monthly_cost': 25.00,       # AlwaysOn monthly cost
                'hourly_rate': 0.29,         # AutoStop hourly rate
                'bundle_id': 'wsb-abc123',
                'bundle_type': 'VALUE'
            }
        }

    Example:
        >>> bundle_map = {'ws-abc123': 'wsb-def456'}
        >>> w3_data = calculate_w3_breakeven_dynamic(bundle_map, profile='default')
        >>> print(f"Break-even: {w3_data['ws-abc123']['breakeven_hours']:.1f} hours")

    Note:
        Break-even calculation:
        - If monthly_cost = $25 and hourly_rate = $0.29
        - Break-even = $25 / $0.29 = 86.2 hours/month
        - Usage < 86.2 hours → AutoStop cheaper (10 points)
        - Usage > 86.2 hours → AlwaysOn cheaper (5 points)
    """
    try:
        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="operational", user_specified_profile=profile, silent=True)

        print_info(
            f"🔍 W3 Signal: Querying Pricing API for dynamic break-even ({len(bundle_ids)} WorkSpaces, region: {region}, profile: {profile})..."
        )

        # Initialize Pricing client (ap-southeast-2 only)
        session = boto3.Session(profile_name=profile)
        pricing_client = session.client("pricing", region_name="ap-southeast-2")

        # Cache pricing data by bundle ID to avoid redundant calls
        bundle_pricing_cache = {}
        results = {}

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Calculating break-even thresholds...", total=len(bundle_ids))

            for ws_id, bundle_id in bundle_ids.items():
                try:
                    # Check cache first
                    if bundle_id not in bundle_pricing_cache:
                        # Query pricing for this bundle
                        response = pricing_client.get_products(
                            ServiceCode="AmazonWorkSpaces",
                            Filters=[
                                {"Type": "TERM_MATCH", "Field": "bundleId", "Value": bundle_id},
                                {"Type": "TERM_MATCH", "Field": "location", "Value": _get_pricing_location(region)},
                            ],
                            MaxResults=10,
                        )

                        # Parse pricing data
                        pricing_data = _parse_pricing_response(response)
                        bundle_pricing_cache[bundle_id] = pricing_data
                    else:
                        pricing_data = bundle_pricing_cache[bundle_id]

                    # Calculate break-even
                    monthly_cost = pricing_data.get("monthly_cost", 0.0)
                    hourly_rate = pricing_data.get("hourly_rate", 0.0)

                    if hourly_rate > 0:
                        breakeven_hours = monthly_cost / hourly_rate
                    else:
                        breakeven_hours = 0.0

                    # Scoring: 10 pts if under break-even preferred, 5 pts otherwise
                    # Note: Actual usage comparison done in notebook with usage data
                    w3_score = 10  # Default to high score (assume under break-even)

                    results[ws_id] = {
                        "w3_score": w3_score,
                        "breakeven_hours": breakeven_hours,
                        "monthly_cost": monthly_cost,
                        "hourly_rate": hourly_rate,
                        "bundle_id": bundle_id,
                        "bundle_type": pricing_data.get("bundle_type", "UNKNOWN"),
                    }

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")
                    logger.warning(f"Pricing API error for {ws_id}: {e}")

                    results[ws_id] = {
                        "w3_score": 5,  # Default to lower score on error
                        "breakeven_hours": 0.0,
                        "monthly_cost": 0.0,
                        "hourly_rate": 0.0,
                        "bundle_id": bundle_id,
                        "bundle_type": "ERROR",
                    }

                progress.update(task, advance=1)

        print_success(f"✅ W3 signal analysis complete: Break-even calculated for {len(results)} WorkSpaces")
        print_info(f"   Pricing cache: {len(bundle_pricing_cache)} unique bundles")

        return results

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print_error(f"❌ Pricing API error: {error_code}")
        logger.error(f"Pricing API error: {e}", exc_info=True)
        return {}
    except Exception as e:
        print_error(f"❌ W3 signal analysis failed: {e}")
        logger.error(f"W3 signal error: {e}", exc_info=True)
        return {}


def check_w4_autostop_policy(workspaces_df: pd.DataFrame, profile: Optional[str] = None) -> Dict[str, Dict]:
    """
    W4 Signal: AutoStop policy validation (10 points).

    Validates AutoStop policy via running_mode column in DataFrame.
    WorkSpaces running ALWAYS_ON mode get +10 points (should use AutoStop).

    Signal W4: ALWAYS_ON mode (should switch to AutoStop) → +10 points

    Args:
        workspaces_df: pandas DataFrame with columns:
                      - WorkspaceId (or workspace_id)
                      - running_mode (or RunningMode)
        profile: AWS profile name (unused, for API consistency)

    Returns:
        Dictionary mapping workspace IDs to W4 results:
        {
            'ws-abc123': {
                'w4_score': 10,  # 10 if ALWAYS_ON, 0 if AUTO_STOP
                'running_mode': 'ALWAYS_ON',
                'evidence': 'Running mode: ALWAYS_ON'
            }
        }

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'WorkspaceId': ['ws-abc123'],
        ...     'running_mode': ['ALWAYS_ON']
        ... })
        >>> w4_results = check_w4_autostop_policy(df)
        >>> print(f"W4 Score: {w4_results['ws-abc123']['w4_score']}")

    Note:
        This function reads from DataFrame (no AWS API calls).
        Running modes:
        - ALWAYS_ON: WorkSpace never stops (higher cost)
        - AUTO_STOP: WorkSpace stops when idle (cost-optimized)
    """
    try:
        print_info(f"🔍 W4 Signal: Validating AutoStop policies ({len(workspaces_df)} WorkSpaces)...")

        results = {}

        # Normalize column names (handle both formats)
        df = workspaces_df.copy()

        # Find workspace ID column
        ws_id_col = None
        for col in ["WorkspaceId", "workspace_id", "Workspace ID"]:
            if col in df.columns:
                ws_id_col = col
                break

        # Find running mode column
        mode_col = None
        for col in ["running_mode", "RunningMode", "Running Mode"]:
            if col in df.columns:
                mode_col = col
                break

        if not ws_id_col or not mode_col:
            print_error("❌ Required columns not found in DataFrame")
            print_warning("   Expected: WorkspaceId and running_mode")
            print_warning(f"   Found: {list(df.columns)}")
            return {}

        # Analyze each WorkSpace
        for idx, row in df.iterrows():
            ws_id = str(row[ws_id_col]).strip()
            running_mode = str(row[mode_col]).strip().upper()

            # Scoring: 10 points if ALWAYS_ON (should switch to AutoStop)
            w4_score = 10 if running_mode == "ALWAYS_ON" else 0

            evidence = f"Running mode: {running_mode}"

            results[ws_id] = {"w4_score": w4_score, "running_mode": running_mode, "evidence": evidence}

        # Summary
        always_on_count = sum(1 for r in results.values() if r["w4_score"] == 10)

        if always_on_count > 0:
            print_success(
                f"✅ W4 signal analysis complete: {always_on_count}/{len(results)} WorkSpaces with ALWAYS_ON mode"
            )
        else:
            print_info(f"ℹ️  W4 signal analysis complete: All {len(results)} WorkSpaces use AUTO_STOP")

        return results

    except Exception as e:
        print_error(f"❌ W4 signal analysis failed: {e}")
        logger.error(f"W4 signal error: {e}", exc_info=True)
        return {}


def analyze_w5_admin_activity(
    workspace_ids: List[str], profile: Optional[str] = None, region: str = "ap-southeast-2", lookback_days: int = 90
) -> Dict[str, Dict]:
    """
    W5 Signal: CloudTrail admin activity detection (5 points).

    Analyzes CloudTrail for admin operations (RebuildWorkspaces, MigrateWorkspace, ModifyWorkspaceProperties, etc.).
    WorkSpaces with no admin activity in 90+ days may be orphaned → +5 points.

    Signal W5: No admin CloudTrail activity in 90+ days → +5 points

    Args:
        workspace_ids: List of WorkSpace IDs to check
        profile: AWS profile for CloudTrail (default: $AWS_PROFILE)
        region: AWS region (default: ap-southeast-2)
        lookback_days: Days to look back (default: 90, max: 90)

    Returns:
        Dictionary mapping workspace IDs to W5 results:
        {
            'ws-abc123': {
                'w5_score': 5,  # 5 if no activity, 0 if active
                'event_count': 0,
                'evidence': 'No admin activity in 90 days',
                'lookback_days': 90,
                'events': []
            }
        }

    Admin Events Tracked:
        - RebuildWorkspaces
        - MigrateWorkspace
        - ModifyWorkspaceProperties
        - ModifyWorkspaceState
        - RestoreWorkspace

    Example:
        >>> w5_results = analyze_w5_admin_activity(
        ...     workspace_ids=['ws-abc123'],
        ...     profile='management'
        ... )
    """
    try:
        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="operational", user_specified_profile=profile, silent=True)

        print_info(
            f"🔍 W5 Signal: Analyzing CloudTrail admin activity ({lookback_days}-day lookback, region: {region}, profile: {profile})..."
        )

        session = boto3.Session(profile_name=profile)
        ct_client = session.client("cloudtrail", region_name=region)

        w5_results = {}
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(days=min(lookback_days, 90))

        # Admin event names to track
        admin_events = [
            "RebuildWorkspaces",
            "MigrateWorkspace",
            "ModifyWorkspaceProperties",
            "ModifyWorkspaceState",
            "RestoreWorkspace",
        ]

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Querying CloudTrail events...", total=len(workspace_ids))

            for workspace_id in workspace_ids:
                try:
                    # Query CloudTrail for this WorkSpace
                    events_found = []
                    next_token = None

                    while True:
                        params = {
                            "LookupAttributes": [{"AttributeKey": "ResourceName", "AttributeValue": workspace_id}],
                            "StartTime": start_time,
                            "EndTime": end_time,
                            "MaxResults": 50,
                        }

                        if next_token:
                            params["NextToken"] = next_token

                        response = ct_client.lookup_events(**params)

                        # Filter for admin events
                        for event in response.get("Events", []):
                            event_name = event.get("EventName", "")
                            if event_name in admin_events:
                                events_found.append(event_name)

                        next_token = response.get("NextToken")
                        if not next_token:
                            break

                    # Scoring: 5 points if no admin activity
                    event_count = len(events_found)
                    w5_score = 5 if event_count == 0 else 0

                    # Build evidence
                    if event_count == 0:
                        evidence = f"No admin activity in {lookback_days} days"
                    else:
                        unique_events = set(events_found)
                        evidence = f"Admin activity: {', '.join(unique_events)}"

                    w5_results[workspace_id] = {
                        "w5_score": w5_score,
                        "event_count": event_count,
                        "evidence": evidence,
                        "lookback_days": lookback_days,
                        "events": events_found,
                    }

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    if error_code == "AccessDeniedException":
                        print_warning("   CloudTrail access denied (skipping W5)")
                        w5_results[workspace_id] = {
                            "w5_score": 0,
                            "event_count": 0,
                            "evidence": "CloudTrail access denied",
                            "lookback_days": lookback_days,
                            "events": [],
                        }
                    else:
                        logger.warning(f"CloudTrail query failed for {workspace_id}: {e}")
                        w5_results[workspace_id] = {
                            "w5_score": 0,
                            "event_count": 0,
                            "evidence": f"Error: {error_code}",
                            "lookback_days": lookback_days,
                            "events": [],
                        }

                progress.update(task, advance=1)

        # Summary
        inactive_count = sum(1 for r in w5_results.values() if r["w5_score"] == 5)

        if inactive_count > 0:
            print_success(
                f"✅ W5 signal analysis complete: {inactive_count}/{len(workspace_ids)} WorkSpaces with no admin activity"
            )
        else:
            print_info(f"ℹ️  W5 signal analysis complete: All {len(workspace_ids)} WorkSpaces show admin activity")

        return w5_results

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print_error(f"❌ CloudTrail API error: {error_code}")
        logger.error(f"CloudTrail API error: {e}", exc_info=True)
        return {}
    except Exception as e:
        print_error(f"❌ W5 signal analysis failed: {e}")
        logger.error(f"W5 signal error: {e}", exc_info=True)
        return {}


def validate_w6_user_status(
    usernames: List[str], profile: Optional[str] = None, identity_store_id: str = "d-976752e8d5"
) -> Dict[str, Dict]:
    """
    W6 Signal: Identity Center user status validation (5 points).

    Checks if WorkSpaces users still exist and are active in Identity Center.
    WorkSpaces with disabled/deleted users get +5 points.

    Signal W6: User NOT found in Identity Center (potentially disabled) → +5 points

    Args:
        usernames: List of WorkSpace usernames (email addresses) to validate
        profile: AWS profile for Identity Center (default: $AWS_PROFILE)
        identity_store_id: Identity Store ID (default: d-976752e8d5)

    Returns:
        Dictionary mapping usernames to W6 results:
        {
            'user@example.com': {
                'w6_score': 5,  # 5 if NOT found, 0 if found
                'user_status': 'NOT_FOUND',
                'evidence': 'User not found (potentially disabled)',
                'user_id': None
            }
        }

    Example:
        >>> usernames = df['username'].unique().tolist()
        >>> w6_results = validate_w6_user_status(usernames, profile='default')
        >>> print(f"User status: {w6_results['user@example.com']['user_status']}")

    Note:
        Requires management account access for Identity Center API.
        Identity Store ID varies by organization (check AWS SSO settings).
    """
    try:
        # Profile cascade
        if profile is None:
            profile = os.getenv("AWS_PROFILE", "default")

        print_info(
            f"🔍 W6 Signal: Validating Identity Center user status ({len(usernames)} users, identity_store_id: {identity_store_id}, profile: {profile})..."
        )

        # Initialize Identity Store client (region configurable via session or environment)
        session = boto3.Session(profile_name=profile)
        region = session.region_name or os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
        ids_client = session.client("identitystore", region_name=region)

        w6_results = {}

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Querying Identity Center...", total=len(usernames))

            for username in usernames:
                try:
                    # Query user by username (email)
                    response = ids_client.list_users(
                        IdentityStoreId=identity_store_id,
                        Filters=[{"AttributePath": "UserName", "AttributeValue": username}],
                    )

                    users = response.get("Users", [])

                    if len(users) == 0:
                        # User not found = potential decommission
                        w6_score = 5
                        user_status = "NOT_FOUND"
                        evidence = "User not found (potentially disabled)"
                        user_id = None
                    else:
                        # User found = active
                        w6_score = 0
                        user_status = "ACTIVE"
                        user_id = users[0].get("UserId", "Unknown")
                        evidence = f"User active (ID: {user_id})"

                    w6_results[username] = {
                        "w6_score": w6_score,
                        "user_status": user_status,
                        "evidence": evidence,
                        "user_id": user_id,
                    }

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    if error_code == "AccessDeniedException":
                        print_warning("   Identity Center access denied (skipping W6)")
                        w6_results[username] = {
                            "w6_score": 0,
                            "user_status": "ERROR",
                            "evidence": "Identity Center access denied",
                            "user_id": None,
                        }
                    else:
                        logger.warning(f"Identity Center error for {username}: {e}")
                        w6_results[username] = {
                            "w6_score": 0,
                            "user_status": "ERROR",
                            "evidence": f"Error: {error_code}",
                            "user_id": None,
                        }

                progress.update(task, advance=1)

        # Summary
        not_found_count = sum(1 for r in w6_results.values() if r["w6_score"] == 5)

        if not_found_count > 0:
            print_success(
                f"✅ W6 signal analysis complete: {not_found_count}/{len(usernames)} users not found in Identity Center"
            )
        else:
            print_info(f"ℹ️  W6 signal analysis complete: All {len(usernames)} users found in Identity Center")

        return w6_results

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print_error(f"❌ Identity Center API error: {error_code}")
        logger.error(f"Identity Center API error: {e}", exc_info=True)
        return {}
    except Exception as e:
        print_error(f"❌ W6 signal validation failed: {e}")
        logger.error(f"W6 signal error: {e}", exc_info=True)
        return {}


# Helper functions


def _get_pricing_location(region: str) -> str:
    """
    Convert AWS region code to Pricing API location name.

    Args:
        region: AWS region code (e.g., 'ap-southeast-2')

    Returns:
        Pricing API location name (e.g., 'Asia Pacific (Sydney)')
    """
    location_map = {
        "ap-southeast-2": "US East (N. Virginia)",
        "ap-southeast-6": "US West (Oregon)",
        "ap-southeast-2": "Asia Pacific (Sydney)",
        "eu-west-1": "EU (Ireland)",
        # Add more as needed
    }

    return location_map.get(region, "US East (N. Virginia)")


def _parse_pricing_response(response: Dict) -> Dict:
    """
    Parse Pricing API response to extract costs.

    Args:
        response: Pricing API GetProducts response

    Returns:
        Dict with monthly_cost, hourly_rate, bundle_type
    """
    try:
        import json

        price_list = response.get("PriceList", [])

        if not price_list:
            return {"monthly_cost": 0.0, "hourly_rate": 0.0, "bundle_type": "UNKNOWN"}

        # Parse first product
        product = json.loads(price_list[0])

        # Extract pricing terms
        on_demand = product.get("terms", {}).get("OnDemand", {})

        monthly_cost = 0.0
        hourly_rate = 0.0
        bundle_type = "UNKNOWN"

        for term_key, term_data in on_demand.items():
            price_dimensions = term_data.get("priceDimensions", {})

            for dim_key, dim_data in price_dimensions.items():
                unit = dim_data.get("unit", "")
                price = float(dim_data.get("pricePerUnit", {}).get("USD", 0.0))

                if unit == "Hrs":
                    hourly_rate = price
                elif unit == "Monthly":
                    monthly_cost = price

        # Extract bundle type from attributes
        attributes = product.get("product", {}).get("attributes", {})
        bundle_type = attributes.get("bundleType", "UNKNOWN")

        return {"monthly_cost": monthly_cost, "hourly_rate": hourly_rate, "bundle_type": bundle_type}

    except Exception as e:
        logger.warning(f"Failed to parse pricing response: {e}")
        return {"monthly_cost": 0.0, "hourly_rate": 0.0, "bundle_type": "ERROR"}


def validate_w7_volume_encryption(
    workspace_ids: List[str], profile: Optional[str] = None, region: str = "ap-southeast-2"
) -> Dict[str, Dict]:
    """
    W7 Signal: Volume encryption compliance validation (5 points).

    Validates WorkSpaces volume encryption via DescribeWorkspaces API.
    WorkSpaces properties include UserVolumeEncryptionEnabled and RootVolumeEncryptionEnabled.

    Signal W7: Unencrypted volumes (security/compliance risk) → +5 points

    Scoring:
    - 5 points: No encryption (both volumes unencrypted)
    - 2 points: Partial encryption (only one volume encrypted)
    - 0 points: Full encryption (both volumes encrypted) ✅ Compliant

    Args:
        workspace_ids: List of WorkSpace IDs to check
        profile: AWS profile name (default: $AWS_PROFILE)
        region: AWS region (default: ap-southeast-2)

    Returns:
        Dictionary mapping workspace IDs to W7 results:
        {
            'ws-abc123': {
                'w7_score': 5,  # 5=unencrypted, 2=partial, 0=encrypted
                'root_encrypted': False,
                'user_encrypted': False,
                'encryption_status': 'UNENCRYPTED',  # ENCRYPTED/PARTIAL/UNENCRYPTED
                'evidence': 'No encryption (security risk)'
            }
        }

    Example:
        >>> w7_results = validate_w7_volume_encryption(
        ...     workspace_ids=['ws-abc123'],
        ...     profile='operational'
        ... )
        >>> unencrypted = [ws for ws, r in w7_results.items() if r['w7_score'] == 5]

    Note:
        - Encryption status from WorkspaceProperties API (no separate API call needed)
        - Root volume encryption: Operating system security
        - User volume encryption: User data security
        - Both should be encrypted for compliance
    """
    try:
        # Profile cascade
        if profile is None:
            profile = os.getenv("AWS_PROFILE", "default")

        print_info(
            f"🔍 W7 Signal: Validating volume encryption compliance ({len(workspace_ids)} WorkSpaces, region: {region}, profile: {profile})..."
        )

        session = boto3.Session(profile_name=profile)
        ws_client = session.client("workspaces", region_name=region)

        w7_results = {}

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Checking volume encryption...", total=len(workspace_ids))

            for workspace_id in workspace_ids:
                try:
                    # Query WorkSpace properties
                    response = ws_client.describe_workspaces(WorkspaceIds=[workspace_id])

                    workspaces = response.get("Workspaces", [])

                    if not workspaces:
                        # WorkSpace not found
                        w7_results[workspace_id] = {
                            "w7_score": 0,
                            "root_encrypted": None,
                            "user_encrypted": None,
                            "encryption_status": "NOT_FOUND",
                            "evidence": "WorkSpace not found",
                        }
                        progress.update(task, advance=1)
                        continue

                    workspace = workspaces[0]
                    properties = workspace.get("WorkspaceProperties", {})

                    # Extract encryption flags
                    root_encrypted = properties.get("RootVolumeEncryptionEnabled", False)
                    user_encrypted = properties.get("UserVolumeEncryptionEnabled", False)

                    # Scoring logic
                    if root_encrypted and user_encrypted:
                        # Full encryption (compliant)
                        w7_score = 0
                        encryption_status = "ENCRYPTED"
                        evidence = "Full encryption (compliant) ✅"
                    elif root_encrypted or user_encrypted:
                        # Partial encryption (security gap)
                        w7_score = 2
                        encryption_status = "PARTIAL"
                        if root_encrypted:
                            evidence = "Partial: Root encrypted, User unencrypted"
                        else:
                            evidence = "Partial: User encrypted, Root unencrypted"
                    else:
                        # No encryption (security risk)
                        w7_score = 5
                        encryption_status = "UNENCRYPTED"
                        evidence = "No encryption (security/compliance risk) ⚠️"

                    w7_results[workspace_id] = {
                        "w7_score": w7_score,
                        "root_encrypted": root_encrypted,
                        "user_encrypted": user_encrypted,
                        "encryption_status": encryption_status,
                        "evidence": evidence,
                    }

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    if error_code == "ResourceNotFoundException":
                        w7_results[workspace_id] = {
                            "w7_score": 0,
                            "root_encrypted": None,
                            "user_encrypted": None,
                            "encryption_status": "NOT_FOUND",
                            "evidence": "WorkSpace not found",
                        }
                    else:
                        logger.warning(f"WorkSpaces API error for {workspace_id}: {e}")
                        w7_results[workspace_id] = {
                            "w7_score": 0,
                            "root_encrypted": None,
                            "user_encrypted": None,
                            "encryption_status": "ERROR",
                            "evidence": f"Error: {error_code}",
                        }

                progress.update(task, advance=1)

        # Summary statistics
        unencrypted_count = sum(1 for r in w7_results.values() if r["w7_score"] == 5)
        partial_count = sum(1 for r in w7_results.values() if r["w7_score"] == 2)
        encrypted_count = sum(
            1 for r in w7_results.values() if r["w7_score"] == 0 and r["encryption_status"] == "ENCRYPTED"
        )

        total_workspaces = len(workspace_ids)
        compliance_rate = (encrypted_count / total_workspaces * 100) if total_workspaces > 0 else 0

        print_success(f"✅ W7 signal analysis complete")
        print_info(f"   Encrypted: {encrypted_count} ({compliance_rate:.1f}%)")
        print_info(f"   Partial: {partial_count}")
        print_info(f"   Unencrypted: {unencrypted_count}")

        if unencrypted_count > 0:
            print_warning(f"   ⚠️  {unencrypted_count} WorkSpaces require encryption for compliance")

        return w7_results

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print_error(f"❌ WorkSpaces API error: {error_code}")
        logger.error(f"WorkSpaces API error: {e}", exc_info=True)
        return {}
    except Exception as e:
        print_error(f"❌ W7 signal validation failed: {e}")
        logger.error(f"W7 signal error: {e}", exc_info=True)
        return {}
