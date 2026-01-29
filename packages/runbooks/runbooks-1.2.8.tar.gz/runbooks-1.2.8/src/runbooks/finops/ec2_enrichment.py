#!/usr/bin/env python3
"""
EC2 Enrichment Module - Production AWS API Integration

Provides reusable EC2 enrichment functions for notebook consumption:
- EC2 context enrichment (28 columns from DescribeInstances API)
- CloudTrail activity analysis (90-day lookback, idle detection)
- Cost Explorer 12-month trailing cost data

Design Pattern:
    - Reuses VPC CloudTrail and Cost Explorer patterns
    - Rich CLI output throughout (no print())
    - Profile cascade: param > $AWS_PROFILE
    - Enterprise error handling with graceful fallback

Usage:
    from runbooks.finops.ec2_enrichment import (
        enrich_with_ec2_context,
        analyze_ec2_cloudtrail,
        get_ec2_cost_data
    )

    # Enrich EC2 inventory with AWS API data
    enriched_df = enrich_with_ec2_context(df, profile='operational')
    enriched_df = analyze_ec2_cloudtrail(enriched_df, profile='management')
    enriched_df = get_ec2_cost_data(enriched_df, profile='billing')
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


def _get_instance_type_from_cost_explorer(
    instance_id: str, account_id: str, region: str, profile: str, lookback_months: int = 12
) -> str:
    """
    Get instance type for terminated instances using Cost Explorer INSTANCE_TYPE dimension.

    Cost Explorer retains 12 months of data, matching our trailing analysis period.
    This is the primary method for terminated instance metadata recovery.

    Args:
        instance_id: EC2 instance ID (e.g., 'i-0a52e8e6e0888b2b4')
        account_id: AWS account ID
        region: AWS region
        profile: AWS profile for Cost Explorer access
        lookback_months: Months to look back (default: 12)

    Returns:
        Instance type (e.g., 't3.medium') or 'UNKNOWN' if not found
    """
    try:
        from datetime import datetime, timedelta
        from runbooks.common.profile_utils import create_cost_session, create_timeout_protected_client

        session = create_cost_session(profile)
        ce_client = create_timeout_protected_client(
            session, "ce", "ap-southeast-2"
        )  # Cost Explorer always ap-southeast-2

        # Calculate time window (12 months trailing)
        end_date = datetime.now().replace(day=1)
        start_date = end_date - timedelta(days=30 * lookback_months)

        # Query Cost Explorer with instance resource ID filter
        # Note: Querying all EC2 compute in account/region, then filtering by instance ID
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            Filter={
                "And": [
                    {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
                    {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": [str(account_id)]}},
                    {"Dimensions": {"Key": "REGION", "Values": [region]}},
                ]
            },
            GroupBy=[{"Type": "DIMENSION", "Key": "INSTANCE_TYPE"}, {"Type": "DIMENSION", "Key": "RESOURCE_ID"}],
        )

        # Search for instance ID in grouped results
        for month_data in response.get("ResultsByTime", []):
            for group in month_data.get("Groups", []):
                keys = group.get("Keys", [])
                # Keys format: ['t3.medium', 'i-0a52e8e6e0888b2b4']
                if len(keys) >= 2 and instance_id in keys[1]:
                    instance_type = keys[0]
                    logger.debug(f"Found instance type from Cost Explorer: {instance_id} -> {instance_type}")
                    return instance_type

        return "UNKNOWN"

    except ClientError as e:
        logger.warning(f"Cost Explorer query failed for {instance_id}: {e}")
        return "UNKNOWN"
    except Exception as e:
        logger.error(f"Unexpected error in Cost Explorer lookup: {e}")
        return "UNKNOWN"


def _get_instance_type_from_cloudtrail(instance_id: str, region: str, profile: str, lookback_days: int = 90) -> str:
    """
    Get instance type from CloudTrail RunInstances event history.

    CloudTrail retains 90 days of event history. This is a fallback method
    when Cost Explorer data is unavailable (instance older than 12 months).

    Args:
        instance_id: EC2 instance ID
        region: AWS region
        profile: AWS profile for CloudTrail access
        lookback_days: Days to look back (default: 90, max: 90)

    Returns:
        Instance type or 'UNKNOWN' if not found
    """
    try:
        from datetime import datetime, timedelta, timezone
        from runbooks.common.profile_utils import create_management_session, create_timeout_protected_client

        session = create_management_session(profile)
        cloudtrail_client = create_timeout_protected_client(session, "cloudtrail", region)

        # Calculate time window (90-day max)
        end_time = datetime.now(tz=timezone.utc)
        start_time = end_time - timedelta(days=min(lookback_days, 90))

        # Query CloudTrail for RunInstances event
        response = cloudtrail_client.lookup_events(
            LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50,
        )

        # Search for RunInstances event
        for event in response.get("Events", []):
            if event.get("EventName") == "RunInstances":
                import json

                cloud_trail_event = json.loads(event.get("CloudTrailEvent", "{}"))

                # Parse responseElements.instancesSet
                instances_set = cloud_trail_event.get("responseElements", {}).get("instancesSet", {}).get("items", [])
                for instance in instances_set:
                    if instance.get("instanceId") == instance_id:
                        instance_type = instance.get("instanceType", "UNKNOWN")
                        logger.debug(f"Found instance type from CloudTrail: {instance_id} -> {instance_type}")
                        return instance_type

        return "UNKNOWN"

    except ClientError as e:
        logger.warning(f"CloudTrail query failed for {instance_id}: {e}")
        return "UNKNOWN"
    except Exception as e:
        logger.error(f"Unexpected error in CloudTrail lookup: {e}")
        return "UNKNOWN"


def enrich_with_ec2_context(df: pd.DataFrame, profile: Optional[str] = None) -> pd.DataFrame:
    """
    Enrich DataFrame with EC2 context from DescribeInstances API.

    Adds 28 columns including:
    - Instance metadata: Name, Instance ID, State, Type, AZ, Launch Time
    - Network: Private IP, Public IP, VPC ID, Subnet ID, Security Groups
    - Configuration: Key Pair, IAM Role, Tenancy, Monitoring
    - Tags: Combined tags string for filtering
    - Architecture: Platform, Architecture, Virtualization Type

    Pattern: Reuses VPC enrichment pattern from vpc/patterns/ modules

    ENHANCEMENT (Track 1 - Terminated Instance Handler):
    - Primary: Cost Explorer INSTANCE_TYPE dimension (12-month retention)
    - Fallback: CloudTrail RunInstances events (90-day retention)
    - Handles terminated instances with historical metadata recovery

    Args:
        df: pandas DataFrame with 'AWS Account' and 'Region' columns
        profile: AWS profile (priority: param > $AWS_PROFILE > 'default')

    Returns:
        DataFrame with EC2 enrichment columns added

    Example:
        >>> df = pd.read_excel('inventory.xlsx', sheet_name='ec2')
        >>> enriched_df = enrich_with_ec2_context(df, profile='operational')
        >>> # DataFrame now has 28 additional EC2 columns
    """
    try:
        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        from runbooks.common.profile_utils import get_profile_for_operation

        profile = get_profile_for_operation(operation_type="operational", user_specified_profile=profile, silent=True)

        print_info(f"🔍 Enriching with EC2 context (profile: {profile})...")

        # Initialize EC2 enrichment columns (28 columns)
        ec2_columns = [
            "instance_id",
            "instance_name",
            "instance_state",
            "instance_type",
            "availability_zone",
            "launch_time",
            "private_ip",
            "public_ip",
            "vpc_id",
            "subnet_id",
            "security_groups",
            "key_pair",
            "iam_role",
            "tenancy",
            "monitoring",
            "platform",
            "architecture",
            "virtualization_type",
            "root_device_type",
            "root_device_name",
            "block_devices",
            "network_interfaces",
            "tags_combined",
            "owner_tag",
            "environment_tag",
            "cost_center_tag",
            "application_tag",
            "backup_tag",
        ]

        for col in ec2_columns:
            df[col] = "N/A"

        enriched_count = 0
        from runbooks.common.profile_utils import create_operational_session

        session = create_operational_session(profile)

        # Group by account and region for batch processing
        account_region_groups = df.groupby(["AWS Account", "Region"])

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Enriching EC2 instances...", total=len(account_region_groups))

            for (account_id, region), group_df in account_region_groups:
                try:
                    ec2_client = session.client("ec2", region_name=region)

                    # Query all instances in this account/region
                    response = ec2_client.describe_instances()

                    # Build instance lookup by instance ID
                    instance_lookup = {}
                    for reservation in response.get("Reservations", []):
                        for instance in reservation.get("Instances", []):
                            instance_id = instance.get("InstanceId")
                            instance_lookup[instance_id] = instance

                    # Enrich rows
                    for idx, row in group_df.iterrows():
                        # Try to find instance by matching criteria
                        # (inventory may use different ID column names)
                        instance_id = (
                            row.get("Instance ID")
                            or row.get("InstanceId")
                            or row.get("ResourceId")
                            or row.get("Identifier")  # Track 1: Support Resource Explorer inventory format
                        )

                        if instance_id and instance_id in instance_lookup:
                            instance = instance_lookup[instance_id]

                            # Extract instance metadata
                            df.at[idx, "instance_id"] = instance.get("InstanceId", "N/A")

                            # Name from tags
                            tags = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
                            df.at[idx, "instance_name"] = tags.get("Name", "N/A")

                            # State and type
                            df.at[idx, "instance_state"] = instance.get("State", {}).get("Name", "N/A")
                            df.at[idx, "instance_type"] = instance.get("InstanceType", "N/A")

                            # Placement
                            placement = instance.get("Placement", {})
                            df.at[idx, "availability_zone"] = placement.get("AvailabilityZone", "N/A")
                            df.at[idx, "tenancy"] = placement.get("Tenancy", "N/A")

                            # Launch time
                            launch_time = instance.get("LaunchTime")
                            df.at[idx, "launch_time"] = launch_time.isoformat() if launch_time else "N/A"

                            # Network
                            df.at[idx, "private_ip"] = instance.get("PrivateIpAddress", "N/A")
                            df.at[idx, "public_ip"] = instance.get("PublicIpAddress", "N/A")
                            df.at[idx, "vpc_id"] = instance.get("VpcId", "N/A")
                            df.at[idx, "subnet_id"] = instance.get("SubnetId", "N/A")

                            # Security groups
                            sg_list = [sg["GroupId"] for sg in instance.get("SecurityGroups", [])]
                            df.at[idx, "security_groups"] = ", ".join(sg_list) if sg_list else "N/A"

                            # Configuration
                            df.at[idx, "key_pair"] = instance.get("KeyName", "N/A")
                            iam_profile = instance.get("IamInstanceProfile", {})
                            df.at[idx, "iam_role"] = (
                                iam_profile.get("Arn", "N/A").split("/")[-1] if iam_profile else "N/A"
                            )

                            # Monitoring
                            monitoring = instance.get("Monitoring", {})
                            df.at[idx, "monitoring"] = monitoring.get("State", "N/A")

                            # Platform and architecture
                            df.at[idx, "platform"] = instance.get("Platform", "Linux/UNIX")
                            df.at[idx, "architecture"] = instance.get("Architecture", "N/A")
                            df.at[idx, "virtualization_type"] = instance.get("VirtualizationType", "N/A")

                            # Storage
                            df.at[idx, "root_device_type"] = instance.get("RootDeviceType", "N/A")
                            df.at[idx, "root_device_name"] = instance.get("RootDeviceName", "N/A")

                            # Block devices
                            block_devices = instance.get("BlockDeviceMappings", [])
                            df.at[idx, "block_devices"] = str(len(block_devices))

                            # Network interfaces
                            network_interfaces = instance.get("NetworkInterfaces", [])
                            df.at[idx, "network_interfaces"] = str(len(network_interfaces))

                            # Tags
                            df.at[idx, "tags_combined"] = (
                                ", ".join([f"{k}={v}" for k, v in tags.items()]) if tags else "N/A"
                            )
                            df.at[idx, "owner_tag"] = tags.get("Owner", "N/A")
                            df.at[idx, "environment_tag"] = tags.get("Environment", "N/A")
                            df.at[idx, "cost_center_tag"] = tags.get("CostCenter", "N/A")
                            df.at[idx, "application_tag"] = tags.get("Application", "N/A")
                            df.at[idx, "backup_tag"] = tags.get("Backup", "N/A")

                            enriched_count += 1

                        elif instance_id and instance_id.startswith("i-"):
                            # TERMINATED INSTANCE HANDLER (Track 1 enhancement)
                            # Instance not in DescribeInstances response (likely terminated)
                            # Use Cost Explorer primary + CloudTrail fallback for metadata recovery

                            df.at[idx, "instance_id"] = instance_id
                            df.at[idx, "instance_state"] = "terminated"

                            # Primary: Query Cost Explorer for instance type (12-month retention)
                            instance_type = _get_instance_type_from_cost_explorer(
                                instance_id=instance_id,
                                account_id=account_id,
                                region=region,
                                profile=profile,
                                lookback_months=12,
                            )

                            # Fallback: Query CloudTrail if Cost Explorer returns UNKNOWN
                            if instance_type == "UNKNOWN":
                                instance_type = _get_instance_type_from_cloudtrail(
                                    instance_id=instance_id, region=region, profile=profile, lookback_days=90
                                )

                            df.at[idx, "instance_type"] = instance_type

                            # Minimal metadata for terminated instances (limited availability)
                            df.at[idx, "instance_name"] = "N/A"
                            df.at[idx, "availability_zone"] = "N/A"
                            df.at[idx, "launch_time"] = "N/A"
                            df.at[idx, "private_ip"] = "N/A"
                            df.at[idx, "public_ip"] = "N/A"
                            df.at[idx, "vpc_id"] = "N/A"
                            df.at[idx, "subnet_id"] = "N/A"

                            if instance_type != "UNKNOWN":
                                enriched_count += 1
                                logger.info(
                                    f"Terminated instance enriched via historical data: {instance_id} -> {instance_type}"
                                )

                except ClientError as e:
                    logger.warning(f"EC2 API error for {account_id}/{region}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error enriching {account_id}/{region}: {e}")

                progress.update(task, advance=1)

        enrichment_rate = (enriched_count / len(df) * 100) if len(df) > 0 else 0
        print_success(
            f"✅ EC2 context enrichment complete: {enriched_count}/{len(df)} instances ({enrichment_rate:.1f}%)"
        )

        return df

    except Exception as e:
        print_error(f"❌ EC2 context enrichment failed: {e}")
        logger.error(f"EC2 enrichment error: {e}", exc_info=True)
        return df


def analyze_ec2_cloudtrail(df: pd.DataFrame, profile: Optional[str] = None, lookback_days: int = 90) -> pd.DataFrame:
    """
    Analyze EC2 instance activity via CloudTrail (90-day lookback).

    Adds 4 columns:
    - last_activity_date: Date of last CloudTrail event (YYYY-MM-DD)
    - days_since_activity: Days since last activity
    - event_count: Total CloudTrail events in lookback window
    - is_idle: True if no activity >30 days

    Pattern: Reuses vpc/patterns/cloudtrail_activity_analysis.py pattern

    Args:
        df: pandas DataFrame with 'instance_id' column (from enrich_with_ec2_context)
        profile: AWS profile for CloudTrail access (typically management account)
        lookback_days: Days to look back (default: 90, max: 90)

    Returns:
        DataFrame with CloudTrail activity columns added

    Example:
        >>> df = enrich_with_ec2_context(df, profile='operational')
        >>> df = analyze_ec2_cloudtrail(df, profile='management', lookback_days=90)
        >>> idle_instances = df[df['is_idle'] == True]
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

        from runbooks.common.profile_utils import create_management_session

        session = create_management_session(profile)
        analyzed_count = 0
        idle_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Analyzing CloudTrail events...", total=len(df))

            for idx, row in df.iterrows():
                instance_id = row.get("instance_id")

                if instance_id and instance_id != "N/A" and instance_id.startswith("i-"):
                    try:
                        # Get region for CloudTrail client
                        region = row.get("Region", "ap-southeast-2")
                        cloudtrail_client = session.client("cloudtrail", region_name=region)

                        # Query CloudTrail for instance-specific events
                        events = []
                        response = cloudtrail_client.lookup_events(
                            LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": instance_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            MaxResults=50,
                        )

                        events.extend(response.get("Events", []))

                        # Handle pagination
                        while "NextToken" in response:
                            response = cloudtrail_client.lookup_events(
                                LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": instance_id}],
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
                        logger.warning(f"CloudTrail query failed for {instance_id}: {e}")
                        # Keep defaults (Never, lookback_days, 0, True)

                progress.update(task, advance=1)

        print_success(f"✅ CloudTrail analysis complete")
        print_info(f"   Active (≤30 days): {analyzed_count} | Idle (>30 days): {idle_count}")

        return df

    except Exception as e:
        print_error(f"❌ CloudTrail activity analysis failed: {e}")
        logger.error(f"CloudTrail analysis error: {e}", exc_info=True)
        return df


def get_ec2_cost_data(df: pd.DataFrame, profile: Optional[str] = None, period_months: int = 12) -> pd.DataFrame:
    """
    Enrich with Cost Explorer 12-month trailing actuals for EC2 instances.

    Adds 3 columns:
    - monthly_cost: Average monthly cost (12-month average)
    - annual_cost_12mo: Total 12-month cost
    - cost_trend: Cost trend (↑ Increasing / → Stable / ↓ Decreasing)

    Pattern: Reuses vpc/patterns/cost_explorer_integration.py pattern

    Args:
        df: pandas DataFrame with 'AWS Account' column
        profile: AWS profile for Cost Explorer access (billing account)
        period_months: Number of months to query (default: 12)

    Returns:
        DataFrame with Cost Explorer columns added

    Example:
        >>> df = enrich_with_ec2_context(df, profile='operational')
        >>> df = get_ec2_cost_data(df, profile='billing', period_months=12)
        >>> high_cost_instances = df[df['annual_cost_12mo'] > 1000]
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

        print_info(f"   Querying {len(account_ids)} accounts for EC2 costs...")

        # Query Cost Explorer
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            Filter={
                "And": [
                    {"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
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

                # Update all instances in this account
                mask = df["AWS Account"] == account_id
                instance_count = mask.sum()

                if instance_count > 0:
                    # Distribute cost equally across instances (simple allocation)
                    df.loc[mask, "monthly_cost"] = avg_monthly / instance_count
                    df.loc[mask, "annual_cost_12mo"] = total_cost / instance_count

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

                    enriched_count += instance_count

        enrichment_rate = (enriched_count / len(df) * 100) if len(df) > 0 else 0
        print_success(
            f"✅ Cost Explorer enrichment complete: {enriched_count}/{len(df)} instances ({enrichment_rate:.1f}%)"
        )

        return df

    except Exception as e:
        print_error(f"❌ Cost Explorer enrichment failed: {e}")
        logger.error(f"Cost Explorer error: {e}", exc_info=True)
        return df
