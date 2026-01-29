#!/usr/bin/env python3
"""
Activity Enrichment - CloudTrail + CloudWatch + SSM + Compute Optimizer

Adds 11 activity columns for E1-E7 decommissioning signals:
- CloudTrail: last_activity_date, days_since_activity, activity_count_90d
- CloudWatch: p95_cpu_utilization, p95_network_bytes, user_connected_sum
- SSM: ssm_ping_status, ssm_last_ping_date, ssm_days_since_ping
- Compute Optimizer: compute_optimizer_finding, compute_optimizer_cpu_max, compute_optimizer_recommendation

Unix Philosophy: Multi-API consolidation with CENTRALISED_OPS_PROFILE.

Strategic Alignment:
- Objective 1 (runbooks package): Reusable activity enrichment across modules
- Enterprise SDLC: Consolidated API pattern with graceful degradation
- KISS/DRY/LEAN: Single enricher class consolidating 4 AWS services

Decommission Scoring Framework:
- Signal E1 (Compute Optimizer Idle): 60 points (max CPU ≤1% over 14 days)
- Signal E2 (CloudWatch Low CPU): 10 points (P95 CPU <5% over 14 days)
- Signal E3 (CloudTrail No Activity): 8 points (no events in 90 days)
- Signal E4 (SSM Agent Offline): 8 points (no heartbeat in 14 days)

Usage:
    from runbooks.inventory.enrichers.activity_enricher import ActivityEnricher

    enricher = ActivityEnricher(operational_profile='${CENTRALISED_OPS_PROFILE}')
    enriched_df = enricher.enrich_activity(discovery_df, resource_type='ec2')

    # Adds 11 columns:
    # - CloudTrail: last_activity_date, days_since_activity, activity_count_90d
    # - CloudWatch: p95_cpu_utilization, p95_network_bytes, user_connected_sum
    # - SSM: ssm_ping_status, ssm_last_ping_date, ssm_days_since_ping
    # - Compute Optimizer: compute_optimizer_finding, compute_optimizer_cpu_max, compute_optimizer_recommendation
"""

import pandas as pd
import logging
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
    create_timeout_protected_client,
)
from runbooks.common.rich_utils import (
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar,
    console,
    create_table,
)
from runbooks.common.output_controller import OutputController

logger = logging.getLogger(__name__)

# Resource-specific display names for contextual messaging
RESOURCE_DISPLAY_NAMES = {
    "ec2": "EC2 Instances",
    "workspaces": "WorkSpaces",
    "rds": "RDS Databases",
    "lambda": "Lambda Functions",
    "s3": "S3 Buckets",
}


class ActivityEnricher:
    """
    Multi-source activity enrichment consolidating CloudTrail + CloudWatch + SSM + Compute Optimizer.

    Standalone enricher class for adding 11 activity columns from 4 AWS services.
    Does not inherit from CloudFoundationsBase to avoid abstract method requirements.
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize with 4 AWS service clients for consolidated activity enrichment.

        Args:
            operational_profile: AWS profile for operational APIs (CloudTrail, CloudWatch, SSM, Compute Optimizer)
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController instance for UX consistency (optional)

        Profile Requirements:
            - CloudTrail: cloudtrail:LookupEvents
            - CloudWatch: cloudwatch:GetMetricStatistics
            - SSM: ssm:DescribeInstanceInformation
            - Compute Optimizer: compute-optimizer:GetEC2InstanceRecommendations

        Example:
            >>> enricher = ActivityEnricher(operational_profile='${CENTRALISED_OPS_PROFILE}')
            >>> enriched = enricher.enrich_activity(df, resource_type='ec2')
        """
        # Resolve profile using standard helpers
        resolved_profile = get_profile_for_operation("operational", operational_profile)

        # Initialize AWS session and clients
        self.session = create_operational_session(resolved_profile)
        self.cloudtrail = create_timeout_protected_client(self.session, "cloudtrail", region_name=region)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.ssm = create_timeout_protected_client(self.session, "ssm", region_name=region)
        self.compute_optimizer = create_timeout_protected_client(self.session, "compute-optimizer", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()

        # Respect output control for initialization messages
        if self.output_controller.verbose:
            print_info(f"🔍 ActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info("   APIs: CloudTrail (90d) + CloudWatch (14d) + SSM (30d) + Compute Optimizer (14d)")
        else:
            logger.debug(f"ActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_activity(self, df: pd.DataFrame, resource_type: str) -> pd.DataFrame:
        """
        Add 11 activity columns from 4 AWS services.

        Args:
            df: DataFrame with resource_id column (EC2: instance_id, WorkSpaces: workspace_id)
            resource_type: Resource type ('ec2' or 'workspaces')

        Returns:
            DataFrame with 11 additional activity columns

        Columns Added:
            - CloudTrail: last_activity_date, days_since_activity, activity_count_90d
            - CloudWatch: p95_cpu_utilization, p95_network_bytes, user_connected_sum
            - SSM: ssm_ping_status, ssm_last_ping_date, ssm_days_since_ping
            - Compute Optimizer: compute_optimizer_finding, compute_optimizer_cpu_max, compute_optimizer_recommendation

        Example:
            >>> df = pd.DataFrame({'resource_id': ['i-abc123', 'i-def456']})
            >>> enriched = enricher.enrich_activity(df, resource_type='ec2')
            >>> print(enriched[['resource_id', 'compute_optimizer_finding', 'p95_cpu_utilization']])
        """
        display_name = RESOURCE_DISPLAY_NAMES.get(resource_type, resource_type.upper())

        if self.output_controller.verbose:
            print_info(f"🔄 Starting multi-API activity enrichment for {len(df)} {display_name}...")
        else:
            logger.info(f"{display_name} activity enrichment started")

        # Validate required columns based on resource type with contextual error messaging
        required_col = "instance_id" if resource_type == "ec2" else "workspace_id"

        if required_col not in df.columns:
            available_columns = df.columns.tolist()
            print_error(f"Input DataFrame missing required '{required_col}' column for {resource_type} resources")
            print_info(f"Available columns ({len(available_columns)}): {', '.join(available_columns[:10])}")

            # Suggest similar columns
            similar = [col for col in available_columns if "id" in col.lower() or resource_type in col.lower()]
            if similar:
                print_warning(f"Found similar columns: {', '.join(similar)}")
                print_info("Possible fix: Rename column using Track 1 column standardization")

            raise ValueError(
                f"{required_col} column required for {resource_type} activity enrichment.\n"
                f"Available columns: {available_columns[:10]}\n"
                f"Total columns in DataFrame: {len(available_columns)}"
            )

        # Initialize all 11 columns with default values
        activity_columns = {
            # CloudTrail (E3: 8 points)
            "last_activity_date": None,
            "days_since_activity": 999,
            "activity_count_90d": 0,
            # CloudWatch (E2: 10 points)
            "p95_cpu_utilization": 0.0,
            "p95_network_bytes": 0.0,
            "user_connected_sum": 0.0,
            # SSM (E4: 8 points - EC2 only)
            "ssm_ping_status": "N/A",
            "ssm_last_ping_date": None,
            "ssm_days_since_ping": 0,
            # Compute Optimizer (E1: 60 points - EC2 only)
            "compute_optimizer_finding": "N/A",
            "compute_optimizer_cpu_max": 0.0,
            "compute_optimizer_recommendation": "N/A",
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # E3: CloudTrail (8 points - all resource types)
        # Enhanced with tag-based activity detection fallback
        df = self._enrich_cloudtrail(df, resource_type)

        # E3 Fallback: Tag-based activity signals (InstanceScheduler, state changes)
        df = self._enrich_from_tags(df, resource_type)

        # E2: CloudWatch (10 points - all resource types)
        df = self._enrich_cloudwatch(df, resource_type)

        # E4: SSM (8 points - EC2 only)
        if resource_type == "ec2":
            df = self._enrich_ssm(df)
        else:
            if self.output_controller.verbose:
                print_info("   ⏭️  Skipping SSM enrichment (not applicable to WorkSpaces)")
            else:
                logger.debug("Skipping SSM enrichment for WorkSpaces")

        # E1: Compute Optimizer (60 points - EC2 only)
        if resource_type == "ec2":
            df = self._enrich_compute_optimizer(df)
        else:
            if self.output_controller.verbose:
                print_info("   ⏭️  Skipping Compute Optimizer (not applicable to WorkSpaces)")
            else:
                logger.debug("Skipping Compute Optimizer for WorkSpaces")

        # Display activity signals summary table
        signal_columns = (
            ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
            if resource_type == "ec2"
            else ["W1", "W2", "W3", "W4", "W5", "W6"]
        )
        summary_rows = []

        # Map columns to activity enrichment columns
        signal_mapping = {
            "E1": "compute_optimizer_finding",
            "E2": "p95_cpu_utilization",
            "E3": "days_since_activity",
            "E4": "ssm_ping_status",
            "E5": None,  # Not enriched by activity enricher
            "E6": None,  # Not enriched by activity enricher
            "E7": None,  # Not enriched by activity enricher
            "W1": "days_since_connection",
            "W2": "user_connected_sum",
            "W3": "hourly_usage_hours_mtd",
            "W4": "state",
            "W5": None,  # Not enriched by activity enricher
            "W6": None,  # Not enriched by activity enricher
        }

        for signal in signal_columns:
            column_name = signal_mapping.get(signal)
            if column_name and column_name in df.columns:
                # Count how many resources have this signal populated
                if signal == "E1":
                    detected = (df[column_name] == "Idle").sum()
                elif signal == "E2":
                    detected = (df[column_name] > 0).sum()
                elif signal == "E3":
                    detected = (df[column_name] >= 90).sum()
                elif signal == "E4":
                    detected = (df[column_name] != "Online").sum()
                elif signal == "W2":
                    detected = (df[column_name] == 0).sum()
                else:
                    detected = df[column_name].notna().sum()

                rate = (detected / len(df) * 100) if len(df) > 0 else 0
                summary_rows.append([signal, f"{detected}/{len(df)} ({rate:.1f}%)"])
            elif column_name:
                # Column exists but not populated by activity enricher
                summary_rows.append([signal, "N/A (not enriched)"])

        if summary_rows:
            if self.output_controller.verbose:
                signals_table = create_table("Activity Signals Detection", ["Signal", "Detection Rate"], summary_rows)
                console.print(signals_table)
            else:
                # Compact logging for non-verbose mode
                total_signals = len([r for r in summary_rows if "N/A" not in r[1]])
                logger.info(f"Activity signals detected: {total_signals}/{len(summary_rows)} signals populated")

        if self.output_controller.verbose:
            print_success(f"✅ Multi-API activity enrichment complete: {len(df)} resources processed")
        else:
            logger.info(f"Multi-API activity enrichment complete: {len(df)} resources processed")

        return df

    def _enrich_from_tags(self, df: pd.DataFrame, resource_type: str) -> pd.DataFrame:
        """
        Tag-based activity detection (E3 fallback when CloudTrail unavailable).

        Parses activity signals from AWS resource tags:
        - InstanceScheduler-LastAction: Automated start/stop timestamps
        - State change tags: Resource lifecycle indicators
        - Custom activity tags: Organization-specific patterns

        This method provides fallback activity detection when CloudTrail is:
        - Not enabled in target accounts
        - Inaccessible due to permissions
        - Missing events due to retention policies

        Args:
            df: DataFrame with 'tags' column (JSON string from discovery)
            resource_type: Resource type ('ec2' or 'workspaces')

        Returns:
            DataFrame with activity columns populated from tags (only updates if CloudTrail found no events)

        Performance:
            - Zero API calls (uses existing discovery data)
            - Instant enrichment (tag parsing only)
            - 100% reliable for scheduler-managed resources
        """
        if self.output_controller.verbose:
            print_info("   🏷️  Tags: Parsing activity signals from resource tags...")
        else:
            logger.debug("Parsing activity signals from resource tags")

        resource_id_col = "instance_id" if resource_type == "ec2" else "workspace_id"

        tags_updated = 0

        for idx, row in df.iterrows():
            # Only apply tag-based detection if CloudTrail found no activity
            if row.get("activity_count_90d", 0) > 0:
                continue

            tags_str = row.get("tags", "{}")

            try:
                tags_dict = json.loads(tags_str) if isinstance(tags_str, str) else tags_str

                # Pattern 1: InstanceScheduler-LastAction tag
                # Format: "Stopped By instance-scheduler-parent 2025-11-05 07:00 UTC"
                scheduler_tag = tags_dict.get("InstanceScheduler-LastAction", "")

                if scheduler_tag:
                    # Extract timestamp from scheduler tag
                    # Pattern: "...YYYY-MM-DD HH:MM UTC"
                    date_match = re.search(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})", scheduler_tag)

                    if date_match:
                        timestamp_str = date_match.group(1)

                        try:
                            activity_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")
                            activity_time = activity_time.replace(tzinfo=timezone.utc)

                            current_time = datetime.now(timezone.utc)
                            days_since = (current_time - activity_time).days

                            # Update activity columns
                            df.at[idx, "last_activity_date"] = activity_time.strftime("%Y-%m-%d %H:%M:%S")
                            df.at[idx, "days_since_activity"] = days_since
                            df.at[idx, "activity_count_90d"] = 1  # Tag indicates at least 1 activity

                            tags_updated += 1

                        except ValueError:
                            pass  # Skip malformed timestamps

                # Pattern 2: CustodianOffHours tag (policy enforcement activity)
                custodian_tag = tags_dict.get("CustodianOffHours", "")
                if custodian_tag and df.at[idx, "activity_count_90d"] == 0:
                    # Presence of Custodian tag indicates recent policy evaluation
                    # Assume within last 7 days (conservative estimate)
                    df.at[idx, "days_since_activity"] = 7
                    df.at[idx, "activity_count_90d"] = 1
                    tags_updated += 1

                # Pattern 3: aws:cloudformation:stack-name (managed by CloudFormation)
                cfn_stack = tags_dict.get("aws:cloudformation:stack-name", "")
                if cfn_stack and df.at[idx, "activity_count_90d"] == 0:
                    # CloudFormation-managed resources typically have active lifecycle
                    # Conservative estimate: within last 30 days
                    df.at[idx, "days_since_activity"] = 30
                    df.at[idx, "activity_count_90d"] = 1
                    tags_updated += 1

            except (json.JSONDecodeError, KeyError, AttributeError):
                # Skip resources with malformed tags
                continue

        if self.output_controller.verbose:
            print_success(f"   ✅ Tags: {tags_updated} resources enriched from tag-based activity signals")
        else:
            logger.info(f"Tags: {tags_updated} resources enriched from tag-based activity signals")

        return df

    def _enrich_cloudtrail(self, df: pd.DataFrame, resource_type: str) -> pd.DataFrame:
        """
        CloudTrail 90-day activity tracking (E3: 8 points).

        Enhanced Strategy (Optimized for Performance):
        1. Primary: ResourceName lookup (captures direct API calls)
        2. Fallback: ResourceType EC2 Instance filter (captures lifecycle events efficiently)

        Performance Optimization:
        - Avoids N×M API calls (instances × event names)
        - Uses ResourceType filter for batch EC2 instance event discovery
        - Parses Resources field to match specific instances

        Args:
            df: DataFrame with resource_id column
            resource_type: Resource type ('ec2' or 'workspaces')

        Returns:
            DataFrame with CloudTrail columns populated

        Columns:
            - last_activity_date: Timestamp of most recent CloudTrail event
            - days_since_activity: Days since last event (999 if no events)
            - activity_count_90d: Total events in 90-day window
        """
        if self.output_controller.verbose:
            print_info("   📋 CloudTrail: Querying 90-day activity history (enhanced detection)...")
        else:
            logger.debug("Querying CloudTrail 90-day activity history")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=90)

        resource_id_col = "instance_id" if resource_type == "ec2" else "workspace_id"

        # Step 1: Per-resource ResourceName lookup (original strategy)
        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudTrail ResourceName...", total=len(df))

            for idx, row in df.iterrows():
                resource_id = row.get(resource_id_col, "")

                if not resource_id or resource_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    response = self.cloudtrail.lookup_events(
                        LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": resource_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        MaxResults=50,  # Sample up to 50 events
                    )

                    events = response.get("Events", [])

                    if events:
                        last_event = events[0]
                        event_time = last_event["EventTime"]

                        df.at[idx, "last_activity_date"] = event_time.strftime("%Y-%m-%d %H:%M:%S")
                        df.at[idx, "days_since_activity"] = (end_time - event_time).days
                        df.at[idx, "activity_count_90d"] = len(events)
                    else:
                        # Mark for fallback strategy
                        df.at[idx, "days_since_activity"] = 999
                        df.at[idx, "activity_count_90d"] = 0

                except Exception as e:
                    logger.debug(f"CloudTrail lookup failed for {resource_id}: {e}")
                    df.at[idx, "days_since_activity"] = 999
                    df.at[idx, "activity_count_90d"] = 0

                progress.update(task, advance=1)

        # Step 2: Batch ResourceType fallback for instances with no activity
        # Only for EC2, as WorkSpaces typically appear in ResourceName
        if resource_type == "ec2":
            no_activity_mask = df["activity_count_90d"] == 0
            no_activity_instances = df[no_activity_mask][resource_id_col].tolist()

            if no_activity_instances:
                if self.output_controller.verbose:
                    print_info(
                        f"   🔍 CloudTrail: Applying ResourceType fallback for {len(no_activity_instances)} instances..."
                    )
                else:
                    logger.debug(f"CloudTrail ResourceType fallback for {len(no_activity_instances)} instances")

                try:
                    # Query EC2 Instance events in batch
                    response = self.cloudtrail.lookup_events(
                        LookupAttributes=[{"AttributeKey": "ResourceType", "AttributeValue": "AWS::EC2::Instance"}],
                        StartTime=start_time,
                        EndTime=end_time,
                        MaxResults=1000,  # Large batch for parsing
                    )

                    # Build instance → events mapping
                    instance_events = {}

                    for event in response.get("Events", []):
                        # Parse Resources field
                        resources = event.get("Resources", [])
                        for resource in resources:
                            resource_name = resource.get("ResourceName", "")

                            # Extract instance ID from resource (e.g., "arn:aws:ec2:...:instance/i-abc123" or "i-abc123")
                            if resource_name in no_activity_instances:
                                if resource_name not in instance_events:
                                    instance_events[resource_name] = []
                                instance_events[resource_name].append(event)

                    # Update DataFrame with fallback results
                    for instance_id, events in instance_events.items():
                        if events:
                            # Find this instance in DataFrame
                            instance_mask = df[resource_id_col] == instance_id
                            instance_idx = df[instance_mask].index

                            if len(instance_idx) > 0:
                                idx = instance_idx[0]

                                last_event = events[0]  # Events sorted by EventTime descending
                                event_time = last_event["EventTime"]

                                df.at[idx, "last_activity_date"] = event_time.strftime("%Y-%m-%d %H:%M:%S")
                                df.at[idx, "days_since_activity"] = (end_time - event_time).days
                                df.at[idx, "activity_count_90d"] = len(events)

                    fallback_found = len(instance_events)
                    if self.output_controller.verbose:
                        print_info(
                            f"   ✅ CloudTrail ResourceType: {fallback_found} additional instances with activity"
                        )
                    else:
                        logger.info(f"CloudTrail ResourceType: {fallback_found} additional instances with activity")

                except Exception as batch_error:
                    logger.debug(f"CloudTrail ResourceType fallback failed: {batch_error}")
                    pass

        events_found = (df["activity_count_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"   ✅ CloudTrail: {events_found}/{len(df)} resources with activity")
        else:
            logger.info(f"CloudTrail: {events_found}/{len(df)} resources with activity")

        return df

    def _enrich_cloudwatch(self, df: pd.DataFrame, resource_type: str) -> pd.DataFrame:
        """
        CloudWatch 14-day metrics (E2: 10 points).

        Args:
            df: DataFrame with resource_id column
            resource_type: Resource type ('ec2' or 'workspaces')

        Returns:
            DataFrame with CloudWatch columns populated

        Columns:
            - p95_cpu_utilization: P95 CPU utilization over 14 days
            - p95_network_bytes: P95 network bytes over 14 days
            - user_connected_sum: Total user connection minutes (WorkSpaces only)

        Metrics:
            EC2:
                - CPUUtilization (AWS/EC2)
                - NetworkIn (AWS/EC2)
            WorkSpaces:
                - CPUUtilization (AWS/WorkSpaces)
                - UserConnected (AWS/WorkSpaces)
        """
        if self.output_controller.verbose:
            print_info("   📊 CloudWatch: Querying 14-day metric statistics...")
        else:
            logger.debug("Querying CloudWatch 14-day metric statistics")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=14)

        resource_id_col = "instance_id" if resource_type == "ec2" else "workspace_id"
        namespace = "AWS/EC2" if resource_type == "ec2" else "AWS/WorkSpaces"
        dimension_name = "InstanceId" if resource_type == "ec2" else "WorkspaceId"

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudWatch metrics...", total=len(df))

            for idx, row in df.iterrows():
                resource_id = row.get(resource_id_col, "")

                if not resource_id or resource_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # CPU Utilization (P95)
                    cpu_response = self.cloudwatch.get_metric_statistics(
                        Namespace=namespace,
                        MetricName="CPUUtilization",
                        Dimensions=[{"Name": dimension_name, "Value": resource_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1-day aggregation
                        Statistics=["Average"],
                        Unit="Percent",
                    )

                    datapoints = cpu_response.get("Datapoints", [])
                    if datapoints:
                        cpu_values = sorted([dp["Average"] for dp in datapoints])
                        p95_index = int(len(cpu_values) * 0.95)
                        df.at[idx, "p95_cpu_utilization"] = round(cpu_values[p95_index], 2)

                    if resource_type == "ec2":
                        # Network metrics for EC2
                        network_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/EC2",
                            MetricName="NetworkIn",
                            Dimensions=[{"Name": "InstanceId", "Value": resource_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,
                            Statistics=["Average"],
                            Unit="Bytes",
                        )

                        network_datapoints = network_response.get("Datapoints", [])
                        if network_datapoints:
                            network_values = sorted([dp["Average"] for dp in network_datapoints])
                            p95_index = int(len(network_values) * 0.95)
                            df.at[idx, "p95_network_bytes"] = round(network_values[p95_index], 2)

                    elif resource_type == "workspaces":
                        # UserConnected metric for WorkSpaces
                        user_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/WorkSpaces",
                            MetricName="UserConnected",
                            Dimensions=[{"Name": "WorkspaceId", "Value": resource_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,
                            Statistics=["Sum"],
                            Unit="Count",
                        )

                        user_datapoints = user_response.get("Datapoints", [])
                        if user_datapoints:
                            total_connected = sum([dp["Sum"] for dp in user_datapoints])
                            df.at[idx, "user_connected_sum"] = round(total_connected, 2)

                except Exception as e:
                    # Graceful degradation on errors
                    logger.debug(f"CloudWatch metrics failed for {resource_id}: {e}")
                    pass

                progress.update(task, advance=1)

        metrics_found = (df["p95_cpu_utilization"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"   ✅ CloudWatch: {metrics_found}/{len(df)} resources with metrics")
        else:
            logger.info(f"CloudWatch: {metrics_found}/{len(df)} resources with metrics")

        return df

    def _enrich_ssm(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        SSM heartbeat status (E4: 8 points - EC2 only).

        Args:
            df: DataFrame with instance_id column

        Returns:
            DataFrame with SSM columns populated

        Columns:
            - ssm_ping_status: Online, Offline, ConnectionLost, Not SSM managed
            - ssm_last_ping_date: Timestamp of last SSM heartbeat
            - ssm_days_since_ping: Days since last heartbeat

        API:
            ssm:DescribeInstanceInformation with InstanceIds filter
        """
        if self.output_controller.verbose:
            print_info("   🔧 SSM: Checking agent heartbeat status...")
        else:
            logger.debug("Checking SSM agent heartbeat status")

        instance_ids = df["instance_id"].unique().tolist()

        # Reuse existing SSM integration pattern
        from runbooks.finops.ssm_integration import get_ssm_heartbeat_status

        try:
            ssm_status = get_ssm_heartbeat_status(
                instance_ids=instance_ids,
                profile=self.profile,
                region=self.region,
                stale_threshold_days=14,
                verbose=self.output_controller.verbose,
            )

            # Enrich DataFrame with SSM data
            for idx, row in df.iterrows():
                instance_id = row.get("instance_id", "")

                if instance_id in ssm_status:
                    status = ssm_status[instance_id]

                    df.at[idx, "ssm_ping_status"] = status["ping_status"]
                    df.at[idx, "ssm_last_ping_date"] = status["last_ping_datetime"]
                    df.at[idx, "ssm_days_since_ping"] = status["last_ping_days"]

            managed_count = len(
                [s for s in ssm_status.values() if s["ping_status"] not in ["Not SSM managed", "SSM access denied"]]
            )
            if self.output_controller.verbose:
                print_success(f"   ✅ SSM: {managed_count}/{len(df)} instances SSM-managed")
            else:
                logger.info(f"SSM: {managed_count}/{len(df)} instances SSM-managed")

        except Exception as e:
            if self.output_controller.verbose:
                print_warning(f"   ⚠️  SSM enrichment failed: {e}")
            logger.error(f"SSM enrichment error: {e}", exc_info=True)

        return df

    def _enrich_compute_optimizer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute Optimizer recommendations (E1: 60 points - EC2 only).

        Args:
            df: DataFrame with instance_id column

        Returns:
            DataFrame with Compute Optimizer columns populated

        Columns:
            - compute_optimizer_finding: Idle, Underprovisioned, Optimized, N/A
            - compute_optimizer_cpu_max: Maximum CPU utilization over 14 days
            - compute_optimizer_recommendation: Right-sizing recommendation

        API:
            compute-optimizer:GetEC2InstanceRecommendations
        """
        if self.output_controller.verbose:
            print_info("   🎯 Compute Optimizer: Analyzing idle instance recommendations...")
        else:
            logger.debug("Analyzing Compute Optimizer idle instance recommendations")

        # Reuse existing Compute Optimizer integration pattern
        from runbooks.finops.compute_optimizer import get_ec2_idle_recommendations

        try:
            idle_instances = get_ec2_idle_recommendations(
                profile=self.profile, region=self.region, verbose=self.output_controller.verbose
            )

            # Enrich DataFrame with Compute Optimizer data
            for idx, row in df.iterrows():
                instance_id = row.get("instance_id", "")

                if instance_id in idle_instances:
                    rec = idle_instances[instance_id]

                    df.at[idx, "compute_optimizer_finding"] = rec["finding"]
                    df.at[idx, "compute_optimizer_cpu_max"] = rec["utilization_metrics"]["cpu_max"]
                    df.at[idx, "compute_optimizer_recommendation"] = rec["recommended_action"]

            idle_count = len(idle_instances)
            if self.output_controller.verbose:
                print_success(f"   ✅ Compute Optimizer: {idle_count} idle instances identified")
            else:
                logger.info(f"Compute Optimizer: {idle_count} idle instances identified")

        except Exception as e:
            if self.output_controller.verbose:
                print_warning(f"   ⚠️  Compute Optimizer enrichment failed: {e}")
            logger.error(f"Compute Optimizer enrichment error: {e}", exc_info=True)

        return df
