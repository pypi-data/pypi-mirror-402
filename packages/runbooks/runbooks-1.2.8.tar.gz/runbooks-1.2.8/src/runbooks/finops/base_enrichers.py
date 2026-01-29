#!/usr/bin/env python3
"""
Base Enrichment Utilities - Reusable Patterns for EC2/WorkSpaces Notebooks

This module extracts proven enrichment patterns from existing runbooks code:
- Organizations enrichment: Account metadata (6 columns)
- Cost Explorer enrichment: 12-month historical costs
- CloudTrail enrichment: Activity tracking (4 columns)
- Tag formatting: Combined tag display utilities

Design Philosophy (KISS/DRY/LEAN):
- Reuse existing patterns from inventory/organizations_utils.py
- Reuse VPC patterns from vpc/patterns/cost_explorer_integration.py
- Extract shared logic, don't recreate
- Enterprise framework compliance

Usage:
    # Organizations enrichment
    enricher = OrganizationsEnricher()
    df = enricher.enrich_with_organizations(
        df,
        account_id_column='AWS Account',
        management_profile='management-profile'
    )

    # Cost Explorer 12-month breakdown
    cost_enricher = CostExplorerEnricher()
    cost_df = cost_enricher.get_12_month_cost_breakdown(
        billing_profile='billing-profile',
        account_ids=['123456789012'],
        service_filter='AmazonEC2'
    )

    # CloudTrail activity
    ct_enricher = CloudTrailEnricher()
    df = ct_enricher.enrich_with_activity(
        df,
        resource_id_column='Instance ID',
        management_profile='management-profile',
        lookback_days=90
    )

Strategic Alignment:
- Objective 1 (runbooks package): Reusable enrichment for notebooks
- Enterprise SDLC: Evidence-based patterns from proven implementations
- KISS/DRY/LEAN: Extract shared logic, enhance existing code
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from ..common.rich_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


class OrganizationsEnricher:
    """
    Reusable Organizations enrichment pattern.

    Extracted from: inventory/organizations_utils.py
    Pattern: Add 6 columns (account_name, account_email, wbs_code, cost_group,
             technical_lead, account_owner) to DataFrame
    """

    def enrich_with_organizations(
        self, df: pd.DataFrame, account_id_column: str, management_profile: str, region: str = "ap-southeast-2"
    ) -> pd.DataFrame:
        """
        Enrich DataFrame with Organizations metadata.

        Args:
            df: pandas DataFrame with account ID column
            account_id_column: Name of column containing account IDs
            management_profile: AWS profile with Organizations access
            region: AWS region (default: ap-southeast-2)

        Returns:
            Enhanced DataFrame with 6 new columns:
                - account_name: Account name from Organizations
                - account_email: Account email
                - wbs_code: WBS cost allocation code
                - cost_group: Cost center assignment
                - technical_lead: Technical owner email
                - account_owner: Business owner email
        """
        try:
            from ..inventory.organizations_utils import discover_organization_accounts

            print_info(f"🔍 Enriching with Organizations metadata (profile: {management_profile})")

            # Discover accounts using existing utility
            accounts, error = discover_organization_accounts(management_profile, region)

            if error:
                print_warning(f"⚠️  Organizations unavailable: {error}")
                print_info("Continuing without Organizations enrichment")
                # Add N/A columns
                for col in [
                    "account_name",
                    "account_email",
                    "wbs_code",
                    "cost_group",
                    "technical_lead",
                    "account_owner",
                ]:
                    df[col] = "N/A"
                # Empty string for tags_combined
                df["tags_combined"] = ""
                return df

            # Create account lookup dictionary
            account_lookup = {acc["id"]: acc for acc in accounts}

            print_success(f"✅ Organizations discovery: {len(accounts)} accounts available for enrichment")

            # Initialize new columns
            orgs_columns = [
                "account_name",
                "account_email",
                "wbs_code",
                "cost_group",
                "technical_lead",
                "account_owner",
                "tags_combined",
            ]
            for col in orgs_columns:
                df[col] = "N/A"

            # Enrich rows with Organizations metadata
            enriched_count = 0

            for idx, row in df.iterrows():
                # Get account ID (handle both int and string formats)
                account_id = str(row.get(account_id_column, "")).strip()

                if account_id and account_id in account_lookup:
                    acc = account_lookup[account_id]

                    df.at[idx, "account_name"] = acc.get("name", "N/A")
                    df.at[idx, "account_email"] = acc.get("email", "N/A")
                    df.at[idx, "wbs_code"] = acc.get("wbs_code", "N/A")
                    df.at[idx, "cost_group"] = acc.get("cost_group", "N/A")
                    df.at[idx, "technical_lead"] = acc.get("technical_lead", "N/A")
                    df.at[idx, "account_owner"] = acc.get("account_owner", "N/A")
                    df.at[idx, "tags_combined"] = acc.get("tags_combined", "")  # NEW: Combined tags

                    enriched_count += 1

            print_success(f"✅ Organizations enrichment complete: {enriched_count}/{len(df)} rows enriched")
            return df

        except ImportError as e:
            print_error(f"❌ Organizations integration unavailable: {e}")
            print_warning("Ensure runbooks.inventory module is installed")
            # Add N/A columns on error
            for col in ["account_name", "account_email", "wbs_code", "cost_group", "technical_lead", "account_owner"]:
                if col not in df.columns:
                    df[col] = "N/A"
            # Empty string fallback for tags_combined (not "N/A")
            if "tags_combined" not in df.columns:
                df["tags_combined"] = ""
            return df
        except Exception as e:
            print_error(f"❌ Organizations enrichment failed: {e}")
            logger.error(f"Organizations enrichment error: {e}", exc_info=True)
            # Add N/A columns on error
            for col in ["account_name", "account_email", "wbs_code", "cost_group", "technical_lead", "account_owner"]:
                if col not in df.columns:
                    df[col] = "N/A"
            # Empty string fallback for tags_combined (not "N/A")
            if "tags_combined" not in df.columns:
                df["tags_combined"] = ""
            return df


class CostExplorerEnricher:
    """
    Reusable Cost Explorer enrichment with 12-month breakdown.

    Extracted from: vpc/patterns/cost_explorer_integration.py
    Pattern: Retrieve monthly costs for trailing 12 months
    Enhancement: Return DataFrame suitable for notebook integration
    """

    def get_cost_by_period(
        self,
        billing_profile: str,
        period_months: int,
        usage_type_filter: str,
        account_ids: Optional[List[str]] = None,
        region_filter: Optional[str] = None,
    ) -> Dict:
        """
        Retrieve monthly costs for specified period.

        Args:
            billing_profile: AWS billing profile
            period_months: Number of months to query (1-12)
            usage_type_filter: AWS usage type filter (e.g., 'EC2', 'WorkSpaces')
            account_ids: Optional list of account IDs to filter
            region_filter: Optional region filter

        Returns:
            {
                'period_total': float,
                'account_costs': Dict[str, float],
                'monthly_breakdown': List[Dict],
                'accounts_with_data': int,
                'period_start': str,
                'period_end': str,
                'calculation_method': str
            }
        """
        try:
            from runbooks.common.profile_utils import create_cost_session, create_timeout_protected_client

            session = create_cost_session(billing_profile)
            ce_client = create_timeout_protected_client(session, "ce", "ap-southeast-2")

            # Calculate period
            today = datetime.now()
            first_of_current_month = today.replace(day=1)
            end_of_last_month = first_of_current_month - timedelta(days=1)
            end_date = end_of_last_month
            start_date = end_date - timedelta(days=30 * period_months) + timedelta(days=1)

            print_info(
                f"📊 Querying Cost Explorer: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            )

            # Build filter
            filter_expr = {"Dimensions": {"Key": "SERVICE", "Values": [usage_type_filter]}}

            if account_ids:
                filter_expr = {
                    "And": [
                        filter_expr,
                        {
                            "Dimensions": {
                                "Key": "LINKED_ACCOUNT",
                                "Values": [str(acc_id) for acc_id in account_ids],  # Convert to strings for AWS API
                            }
                        },
                    ]
                }

            if region_filter:
                current_filters = filter_expr.get("And", [filter_expr])
                filter_expr = {"And": current_filters + [{"Dimensions": {"Key": "REGION", "Values": [region_filter]}}]}

            # Query Cost Explorer
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.strftime("%Y-%m-%d"),
                    "End": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),  # CE requires +1 day
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                Filter=filter_expr,
                GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
            )

            # Process results
            account_costs = {}
            monthly_breakdown = []

            for month_data in response["ResultsByTime"]:
                month_start = month_data["TimePeriod"]["Start"]
                for group in month_data["Groups"]:
                    account_id = group["Keys"][0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])

                    if account_id not in account_costs:
                        account_costs[account_id] = 0.0
                    account_costs[account_id] += cost

                    monthly_breakdown.append({"month": month_start, "account_id": account_id, "cost": cost})

            total_cost = sum(account_costs.values())

            print_success(f"✅ Cost Explorer query complete: ${total_cost:,.2f} total for {period_months} months")

            return {
                "period_total": total_cost,
                "account_costs": account_costs,
                "monthly_breakdown": monthly_breakdown,
                "accounts_with_data": len(account_costs),
                "period_start": start_date.strftime("%Y-%m-%d"),
                "period_end": end_date.strftime("%Y-%m-%d"),
                "calculation_method": f"ACTUAL_{period_months}_MONTH_SUM",
            }

        except Exception as e:
            print_error(f"❌ Cost Explorer query failed: {e}")
            logger.error(f"Cost Explorer error: {e}", exc_info=True)
            return {
                "period_total": 0.0,
                "account_costs": {},
                "monthly_breakdown": [],
                "accounts_with_data": 0,
                "period_start": "",
                "period_end": "",
                "calculation_method": "FAILED",
                "error": str(e),
            }

    def get_12_month_cost_breakdown(
        self,
        billing_profile: str,
        account_ids: Optional[List[str]] = None,
        service_filter: str = "Amazon Elastic Compute Cloud - Compute",
    ) -> pd.DataFrame:
        """
        Return DataFrame with 12-month cost breakdown.

        Args:
            billing_profile: AWS billing profile
            account_ids: Optional list of account IDs to filter
            service_filter: AWS service name (default: EC2 compute)

        Returns:
            DataFrame with columns: month, account_id, service, cost
        """
        result = self.get_cost_by_period(
            billing_profile=billing_profile, period_months=12, usage_type_filter=service_filter, account_ids=account_ids
        )

        if result["monthly_breakdown"]:
            df = pd.DataFrame(result["monthly_breakdown"])
            df["service"] = service_filter
            return df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=["month", "account_id", "service", "cost"])


class CloudTrailEnricher:
    """
    Reusable CloudTrail activity enrichment.

    Extracted from: vpc/patterns/cloudtrail_activity_analysis.py
    Pattern: Add 4 columns (last_activity_date, days_since_activity, activity_count, is_idle)
    """

    def enrich_with_activity(
        self, df: pd.DataFrame, resource_id_column: str, management_profile: str, lookback_days: int = 90
    ) -> pd.DataFrame:
        """
        Enrich DataFrame with CloudTrail activity data.

        Args:
            df: pandas DataFrame with resource ID column
            resource_id_column: Name of column containing resource IDs
            management_profile: AWS profile with CloudTrail access
            lookback_days: Days to look back (max: 90)

        Returns:
            Enhanced DataFrame with 4 new columns:
                - last_activity_date: Last CloudTrail event timestamp
                - days_since_activity: Days since last activity
                - activity_count: Number of CloudTrail events (90 days)
                - is_idle: Boolean (>30 days = idle)
        """
        try:
            from runbooks.common.profile_utils import create_management_session, create_timeout_protected_client

            print_info(
                f"🔍 Enriching with CloudTrail activity (profile: {management_profile}, {lookback_days}-day lookback)"
            )

            session = create_management_session(management_profile)
            # Note: CloudTrail requires region-specific client
            # Using ap-southeast-2 as default (can be enhanced to detect resource region)
            ct_client = create_timeout_protected_client(session, "cloudtrail", "ap-southeast-2")

            # Initialize new columns
            df["last_activity_date"] = None
            df["days_since_activity"] = lookback_days
            df["activity_count"] = 0
            df["is_idle"] = True

            # Calculate time window
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)

            enriched_count = 0

            for idx, row in df.iterrows():
                resource_id = str(row.get(resource_id_column, "")).strip()

                if not resource_id:
                    continue

                try:
                    # Query CloudTrail for resource events
                    response = ct_client.lookup_events(
                        LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": resource_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        MaxResults=50,
                    )

                    events = response.get("Events", [])

                    if events:
                        # Extract last access timestamp
                        last_access = max(event["EventTime"] for event in events)
                        days_since = (datetime.now(last_access.tzinfo) - last_access).days

                        df.at[idx, "last_activity_date"] = last_access.strftime("%Y-%m-%d")
                        df.at[idx, "days_since_activity"] = days_since
                        df.at[idx, "activity_count"] = len(events)
                        df.at[idx, "is_idle"] = days_since > 30  # 30-day idle threshold

                        enriched_count += 1

                except ClientError as e:
                    logger.debug(f"CloudTrail query failed for {resource_id}: {e}")
                    # Keep default values (idle)
                except Exception as e:
                    logger.debug(f"Unexpected error for {resource_id}: {e}")

            print_success(f"✅ CloudTrail enrichment complete: {enriched_count}/{len(df)} rows enriched")
            return df

        except Exception as e:
            print_error(f"❌ CloudTrail enrichment failed: {e}")
            logger.error(f"CloudTrail enrichment error: {e}", exc_info=True)
            # Add N/A columns on error
            if "last_activity_date" not in df.columns:
                df["last_activity_date"] = None
            if "days_since_activity" not in df.columns:
                df["days_since_activity"] = 90
            if "activity_count" not in df.columns:
                df["activity_count"] = 0
            if "is_idle" not in df.columns:
                df["is_idle"] = True
            return df


class StoppedStateEnricher:
    """
    EC2 Stopped State Duration Enrichment.

    Extracted pattern: CloudTrailEnricher date calculation logic
    Enhancement: Calculate stopped duration from existing instance_state + launch_time columns
    No new API calls: Reuses data already in DataFrame

    Usage:
        enricher = StoppedStateEnricher()
        df = enricher.enrich_with_stopped_duration(df)

    Adds columns:
        - stopped_days: Integer, days since instance stopped (0 if running)
    """

    def enrich_with_stopped_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate stopped duration for EC2 instances.

        Args:
            df: pandas DataFrame with instance_state column

        Returns:
            Enhanced DataFrame with 1 new column:
                - stopped_days: Days since instance stopped (0 if running)

        Logic:
            - If instance_state == 'stopped' → calculate days from state_transition_time
            - If instance_state == 'running' → stopped_days = 0
            - If state_transition_time unavailable → stopped_days = 0 (conservative)
        """
        try:
            print_info("🔍 Enriching with stopped state duration...")

            # Initialize new column
            df["stopped_days"] = 0

            enriched_count = 0

            for idx, row in df.iterrows():
                instance_state = str(row.get("instance_state", "unknown")).lower()

                if instance_state == "stopped":
                    # Check if we have state transition time
                    state_transition_time = row.get("state_transition_time", None)

                    if state_transition_time:
                        try:
                            # Parse state transition time
                            if isinstance(state_transition_time, str):
                                transition_date = datetime.fromisoformat(state_transition_time.replace("Z", "+00:00"))
                            else:
                                transition_date = state_transition_time

                            # Calculate days since stopped
                            days_stopped = (datetime.now(transition_date.tzinfo) - transition_date).days

                            df.at[idx, "stopped_days"] = max(0, days_stopped)  # Ensure non-negative
                            enriched_count += 1

                        except (ValueError, AttributeError, TypeError) as e:
                            logger.debug(f"State transition time parse error: {e}")
                            # Keep default 0 (conservative - don't flag without proof)
                else:
                    # Running instances have 0 stopped days
                    df.at[idx, "stopped_days"] = 0

            print_success(f"✅ Stopped state enrichment complete: {enriched_count}/{len(df)} stopped instances")
            return df

        except Exception as e:
            print_error(f"❌ Stopped state enrichment failed: {e}")
            logger.error(f"Stopped state enrichment error: {e}", exc_info=True)
            # Add default column on error
            if "stopped_days" not in df.columns:
                df["stopped_days"] = 0
            return df


class StorageIOEnricher:
    """
    E6 Signal: Storage I/O enrichment for EC2 decommission scoring.

    v1.1.31 FIX: Use AWS/EBS VolumeReadOps/VolumeWriteOps metrics (not AWS/EC2 DiskOps)
    AWS Doc: https://docs.aws.amazon.com/ebs/latest/userguide/using_cloudwatch_ebs.html

    Pattern: Query CloudWatch for EBS VolumeReadOps + VolumeWriteOps metrics (14-day lookback)
    Signal: ebs_total_ops ≤ 100 ops/day → +10 points (E6 signal) - indicates low I/O activity
    """

    def enrich_with_storage_io(
        self,
        df: pd.DataFrame,
        instance_id_column: str,
        operational_profile: str,
        region: str = "ap-southeast-2",
        lookback_days: int = 14,
    ) -> pd.DataFrame:
        """
        Enrich DataFrame with EBS storage I/O metrics from CloudWatch.

        v1.1.31 FIX: Now uses AWS/EBS namespace (works for ALL EBS volumes)
        instead of AWS/EC2 DiskOps (only worked for instance store volumes).

        Args:
            df: pandas DataFrame with EC2 instance IDs
            instance_id_column: Name of column containing instance IDs
            operational_profile: AWS profile with CloudWatch access
            region: AWS region (default: ap-southeast-2)
            lookback_days: Days to look back for metrics (default: 14)

        Returns:
            Enhanced DataFrame with 3 new columns:
                - ebs_read_ops: Total EBS read operations (all attached volumes)
                - ebs_write_ops: Total EBS write operations (all attached volumes)
                - ebs_total_ops: Sum of read + write ops (daily average)
        """
        try:
            from runbooks.common.profile_utils import create_operational_session, create_timeout_protected_client

            print_info(
                f"🔍 E6: Enriching with EBS I/O metrics (profile: {operational_profile}, {lookback_days}d lookback)"
            )

            session = create_operational_session(operational_profile)
            cw_client = create_timeout_protected_client(session, "cloudwatch", region)
            ec2_client = create_timeout_protected_client(session, "ec2", region)

            # Initialize new columns (v1.1.31: renamed from disk_* to ebs_*)
            df["ebs_read_ops"] = 0.0
            df["ebs_write_ops"] = 0.0
            df["ebs_total_ops"] = 0.0
            # Keep legacy columns for backward compatibility
            df["disk_read_ops_p95"] = 0.0
            df["disk_write_ops_p95"] = 0.0
            df["disk_total_ops_p95"] = 0.0

            # Calculate time window
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)

            enriched_count = 0
            instance_ids = df[instance_id_column].dropna().unique().tolist()

            # Batch processing (10 instances per batch for rate limit management)
            batch_size = 10

            for batch_start in range(0, len(instance_ids), batch_size):
                batch_end = min(batch_start + batch_size, len(instance_ids))
                batch_ids = instance_ids[batch_start:batch_end]

                for instance_id in batch_ids:
                    try:
                        # Step 1: Get attached EBS volumes for this instance
                        # AWS Doc: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVolumes.html
                        volumes_response = ec2_client.describe_volumes(
                            Filters=[{"Name": "attachment.instance-id", "Values": [str(instance_id)]}]
                        )

                        volumes = volumes_response.get("Volumes", [])
                        if not volumes:
                            # No EBS volumes attached - instance may use instance store only
                            continue

                        # Step 2: Query CloudWatch for each volume's I/O metrics
                        total_read_ops = 0.0
                        total_write_ops = 0.0

                        for volume in volumes:
                            volume_id = volume["VolumeId"]

                            # Query VolumeReadOps (AWS/EBS namespace)
                            read_response = cw_client.get_metric_statistics(
                                Namespace="AWS/EBS",
                                MetricName="VolumeReadOps",
                                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                                StartTime=start_time,
                                EndTime=end_time,
                                Period=86400,  # Daily data points
                                Statistics=["Sum"],
                            )

                            # Query VolumeWriteOps (AWS/EBS namespace)
                            write_response = cw_client.get_metric_statistics(
                                Namespace="AWS/EBS",
                                MetricName="VolumeWriteOps",
                                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                                StartTime=start_time,
                                EndTime=end_time,
                                Period=86400,  # Daily data points
                                Statistics=["Sum"],
                            )

                            # Sum up operations from all datapoints
                            read_datapoints = read_response.get("Datapoints", [])
                            write_datapoints = write_response.get("Datapoints", [])

                            for dp in read_datapoints:
                                total_read_ops += dp.get("Sum", 0.0)

                            for dp in write_datapoints:
                                total_write_ops += dp.get("Sum", 0.0)

                        # Calculate daily average (total ops / lookback days)
                        daily_read_avg = total_read_ops / lookback_days if lookback_days > 0 else 0.0
                        daily_write_avg = total_write_ops / lookback_days if lookback_days > 0 else 0.0
                        daily_total_avg = daily_read_avg + daily_write_avg

                        # Update DataFrame rows matching this instance
                        mask = df[instance_id_column] == instance_id
                        df.loc[mask, "ebs_read_ops"] = daily_read_avg
                        df.loc[mask, "ebs_write_ops"] = daily_write_avg
                        df.loc[mask, "ebs_total_ops"] = daily_total_avg
                        # Update legacy columns for backward compatibility
                        df.loc[mask, "disk_read_ops_p95"] = daily_read_avg
                        df.loc[mask, "disk_write_ops_p95"] = daily_write_avg
                        df.loc[mask, "disk_total_ops_p95"] = daily_total_avg

                        if daily_total_avg > 0:
                            enriched_count += 1

                    except ClientError as e:
                        if e.response["Error"]["Code"] == "Throttling":
                            print_warning(f"⚠️  CloudWatch/EC2 throttling, applying exponential backoff...")
                            import time

                            time.sleep(2 ** (batch_start // batch_size + 1))  # Exponential backoff
                        else:
                            logger.debug(f"E6 query failed for {instance_id}: {e}")
                    except Exception as e:
                        logger.debug(f"E6 unexpected error for {instance_id}: {e}")

            print_success(
                f"✅ E6 Storage I/O: {len(instance_ids)} instances analyzed ({enriched_count} with EBS metrics) - {lookback_days}d lookback"
            )
            return df

        except Exception as e:
            print_error(f"❌ E6 Storage I/O enrichment failed: {e}")
            logger.error(f"Storage I/O enrichment error: {e}", exc_info=True)
            # Add zero columns on error
            if "disk_read_ops_p95" not in df.columns:
                df["disk_read_ops_p95"] = 0.0
            if "disk_write_ops_p95" not in df.columns:
                df["disk_write_ops_p95"] = 0.0
            if "disk_total_ops_p95" not in df.columns:
                df["disk_total_ops_p95"] = 0.0
            return df


class CostOptimizerEnricher:
    """
    E7 Signal: AWS Cost Explorer rightsizing recommendation enrichment.

    Pattern: Query Cost Explorer GetRightsizingRecommendation API for EC2 terminate recommendations
    Signal: rightsizing_recommendation == 'Terminate' AND savings > $0 → +3 points (E7 signal)
    """

    def enrich_with_cost_optimizer(
        self, df: pd.DataFrame, instance_id_column: str, billing_profile: str, region: str = "ap-southeast-2"
    ) -> pd.DataFrame:
        """
        Enrich DataFrame with Cost Explorer rightsizing recommendations.

        Args:
            df: pandas DataFrame with EC2 instance IDs
            instance_id_column: Name of column containing instance IDs
            billing_profile: AWS profile with Cost Explorer access
            region: AWS region (default: ap-southeast-2)

        Returns:
            Enhanced DataFrame with 2 new columns:
                - rightsizing_savings_estimate: Monthly savings estimate ($)
                - rightsizing_recommendation: Recommendation action (Terminate/Modify/None)
        """
        try:
            from runbooks.common.profile_utils import create_cost_session, create_timeout_protected_client

            print_info(f"🔍 E7: Enriching with Cost Explorer rightsizing recommendations (profile: {billing_profile})")

            session = create_cost_session(billing_profile)
            ce_client = create_timeout_protected_client(
                session, "ce", "ap-southeast-2"
            )  # Cost Explorer always ap-southeast-2

            # Initialize new columns
            df["rightsizing_savings_estimate"] = 0.0
            df["rightsizing_recommendation"] = "None"

            try:
                # Query Cost Explorer for rightsizing recommendations
                print_info("📊 Querying Cost Explorer GetRightsizingRecommendation API...")

                response = ce_client.get_rightsizing_recommendation(
                    Service="AmazonEC2",
                    Configuration={"RecommendationTarget": "SAME_INSTANCE_FAMILY", "BenefitsConsidered": True},
                )

                recommendations = response.get("RightsizingRecommendations", [])

                if not recommendations:
                    print_warning("⚠️  No rightsizing recommendations available from Cost Explorer")
                    return df

                print_info(f"   Found {len(recommendations)} rightsizing recommendations")

                # Build lookup dictionary: instance_id -> recommendation
                recommendation_lookup = {}

                for rec in recommendations:
                    # Extract instance ID from recommendation
                    current_instance = rec.get("CurrentInstance", {})
                    resource_id = current_instance.get("ResourceId", "")

                    # Extract recommendation action
                    rec_detail = rec.get("RightsizingRecommendationDetail", {})
                    action = rec_detail.get("Action", "None")

                    # Extract savings estimate
                    savings = rec.get("EstimatedMonthlySavings", {}).get("Value", "0")
                    try:
                        savings_amount = float(savings)
                    except (ValueError, TypeError):
                        savings_amount = 0.0

                    if resource_id:
                        recommendation_lookup[resource_id] = {"action": action, "savings": savings_amount}

                # Enrich DataFrame with recommendations
                enriched_count = 0

                for idx, row in df.iterrows():
                    instance_id = str(row.get(instance_id_column, "")).strip()

                    if instance_id in recommendation_lookup:
                        rec_data = recommendation_lookup[instance_id]
                        df.at[idx, "rightsizing_savings_estimate"] = rec_data["savings"]
                        df.at[idx, "rightsizing_recommendation"] = rec_data["action"]
                        enriched_count += 1

                print_success(
                    f"✅ E7 Cost Optimizer enrichment complete: {enriched_count}/{len(df)} instances with recommendations"
                )
                return df

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "AccessDeniedException":
                    print_warning(
                        "⚠️  Cost Explorer access denied - ensure billing profile has ce:GetRightsizingRecommendation permission"
                    )
                elif error_code == "DataUnavailableException":
                    print_warning("⚠️  Cost Explorer rightsizing data not available yet (requires 24h of data)")
                else:
                    print_warning(f"⚠️  Cost Explorer API error: {e}")
                return df

        except Exception as e:
            print_error(f"❌ E7 Cost Optimizer enrichment failed: {e}")
            logger.error(f"Cost Optimizer enrichment error: {e}", exc_info=True)
            # Add zero columns on error
            if "rightsizing_savings_estimate" not in df.columns:
                df["rightsizing_savings_estimate"] = 0.0
            if "rightsizing_recommendation" not in df.columns:
                df["rightsizing_recommendation"] = "None"
            return df


def format_tags_combined(tags_dict: Dict[str, str], separator: str = "+") -> str:
    """
    Format AWS tags as combined string.

    Args:
        tags_dict: Dictionary of tag key-value pairs
        separator: Separator character (default: '+')

    Returns:
        Combined tag string (e.g., "Environment:prod+Application:web")

    Example:
        >>> tags = {"Environment": "prod", "Application": "web"}
        >>> format_tags_combined(tags)
        'Environment:prod+Application:web'

        >>> format_tags_combined(tags, separator='|')
        'Environment:prod|Application:web'
    """
    if not tags_dict:
        return "N/A"

    tag_pairs = [f"{key}:{value}" for key, value in sorted(tags_dict.items())]
    return separator.join(tag_pairs)


class BaseAnalyzer:
    """Base class for service-specific cost analyzers.

    Provides common patterns: DataFrame ops, cost calculations, Organizations enrichment.
    Eliminates duplication across 10 analyzer files.

    Design Philosophy (KISS/DRY/LEAN):
    - Reuse existing enrichers (OrganizationsEnricher, CostExplorerEnricher)
    - Common calculation methods (annual cost, savings percentage)
    - Standardized aggregation patterns

    Usage:
        >>> class EC2Analyzer(BaseAnalyzer):
        ...     def analyze(self, df):
        ...         # Use self.calculate_annual_cost()
        ...         # Use self.enrich_with_organizations()
        ...         return enriched_df

    Version: v1.1.28+ (Phase 6 consolidation)
    """

    def __init__(self, profile: str, region: str = "ap-southeast-2"):
        """Initialize base analyzer.

        Args:
            profile: AWS profile name
            region: AWS region (default: ap-southeast-2)
        """
        self.profile = profile
        self.region = region
        self.orgs_enricher = OrganizationsEnricher(region=region)

    def calculate_annual_cost(self, monthly_cost: float) -> float:
        """Convert monthly to annual cost.

        Args:
            monthly_cost: Monthly cost value

        Returns:
            Annual cost (monthly * 12)
        """
        return monthly_cost * 12

    def calculate_savings_percentage(self, current: float, optimized: float) -> float:
        """Calculate % savings.

        Args:
            current: Current cost
            optimized: Optimized cost

        Returns:
            Savings percentage (0-100)
        """
        if current <= 0:
            return 0.0
        return ((current - optimized) / current) * 100

    def enrich_with_organizations(self, df: "pd.DataFrame", account_col: str = "AccountId") -> "pd.DataFrame":
        """Add account names from Organizations API.

        Args:
            df: DataFrame with account IDs
            account_col: Column name containing account IDs

        Returns:
            DataFrame with Organizations columns added
        """
        return self.orgs_enricher.enrich_dataframe(df, account_col)

    def aggregate_by_service(self, df: "pd.DataFrame", cost_col: str = "Cost") -> "pd.DataFrame":
        """Common aggregation pattern.

        Args:
            df: DataFrame with service and cost data
            cost_col: Column name containing cost values

        Returns:
            DataFrame aggregated by service
        """
        if "Service" not in df.columns:
            raise ValueError("DataFrame must have 'Service' column for aggregation")

        return df.groupby("Service").agg({cost_col: "sum"}).reset_index()

    def format_cost_summary(self, total: float, breakdown: Dict[str, float]) -> str:
        """Format cost summary for display.

        Args:
            total: Total cost
            breakdown: Cost breakdown by category

        Returns:
            Formatted summary string
        """
        lines = [f"Total: ${total:,.2f}"]
        for category, amount in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total * 100) if total > 0 else 0
            lines.append(f"  {category}: ${amount:,.2f} ({percentage:.1f}%)")
        return "\n".join(lines)
