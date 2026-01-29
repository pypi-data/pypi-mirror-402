#!/usr/bin/env python3
"""
VPC Peering Activity Enricher - VPC Peering Health Signals (V1-V5)

Analyzes VPC Peering Connection activity patterns using CloudWatch metrics and
route table analysis to identify underutilized or idle peering connections for cost optimization.

Decommission Signals (V1-V5):
- V1: Zero data transfer (40 points) - No BytesSent/BytesReceived for 90+ days
- V2: Both VPCs non-production (20 points) - Both VPCs tagged as dev/test/staging
- V3: No route table entries (10 points) - Zero route tables using peering connection
- V4: Non-production VPC (5 points) - Environment tags indicate dev/test/staging
- V5: Age >180 days (25 points) - Old peering connection

Pattern: Reuses VPCE enricher structure (KISS/DRY/LEAN) + Route table dependency analysis

Strategic Alignment:
- Objective 1 (runbooks package): Reusable VPC Peering enrichment
- Enterprise SDLC: Cost optimization with evidence-based signals
- KISS/DRY/LEAN: Single enricher, CloudWatch consolidation, route table delegation

Usage:
    from runbooks.inventory.enrichers.vpc_peering_activity_enricher import VPCPeeringActivityEnricher

    enricher = VPCPeeringActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='ap-southeast-2'
    )

    enriched_df = enricher.enrich_vpc_peering_activity(discovery_df)

    # Adds columns:
    # - bytes_sent_90d: Sum of BytesSent over 90 days
    # - bytes_received_90d: Sum of BytesReceived over 90 days
    # - accepter_vpc_environment: Accepter VPC environment tag
    # - requester_vpc_environment: Requester VPC environment tag
    # - route_table_entry_count: Number of route tables using peering
    # - age_days: Days since peering creation
    # - same_account: Boolean (accepter and requester in same account)
    # - v1_signal: Boolean (zero data transfer)
    # - v2_signal: Boolean (both VPCs non-production)
    # - v3_signal: Boolean (no route table entries)
    # - v4_signal: Boolean (age >365 days)
    # - v5_signal: Boolean (same account peering)
    # - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
    # - enrichment_status: String (SUCCESS/FAILED/PENDING)
    # - enrichment_error: String (error message if failed)
    # - decommission_score: Total score (0-100 scale)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 16 Phase 2 - VPC Peering Activity Enrichment
"""

import pandas as pd
import logging
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
)
from runbooks.common.output_controller import OutputController

logger = logging.getLogger(__name__)

# VPC Peering signal weights (0-100 scale)
DEFAULT_VPC_PEERING_WEIGHTS = {
    "V1": 40,  # Zero data transfer 90+ days (aligns with EC2 E1/S3 S1)
    "V2": 20,  # Both VPCs non-production
    "V3": 10,  # No active route table entries using peering
    "V4": 5,  # Non-production VPC
    "V5": 25,  # Age >180 days (Manager's age emphasis for VPC)
}


class VPCPeeringActivityEnricher:
    """
    VPC Peering activity enrichment using CloudWatch metrics for V1-V5 decommission signals.

    Consolidates CloudWatch VPC Peering metrics into actionable decommission signals:
    - BytesSent/BytesReceived (V1: zero data transfer)
    - VPC environment tags (V2: both VPCs non-production)
    - Route table dependencies (V3: no route entries)
    - Creation timestamp (V4: age >365 days)
    - Account ownership (V5: same account peering)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
    ):
        """
        Initialize VPC Peering activity enricher.

        Args:
            operational_profile: AWS profile for CloudWatch API access
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)

        Profile Requirements:
            - cloudwatch:GetMetricStatistics (VPC metrics)
            - ec2:DescribeVpcPeeringConnections (peering metadata)
            - ec2:DescribeVpcs (VPC environment tags)
            - ec2:DescribeRouteTables (route table analysis)
        """
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        self.session = create_operational_session(resolved_profile)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.ec2 = create_timeout_protected_client(self.session, "ec2", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        if self.output_controller.verbose:
            print_info(f"🔍 VPCPeeringActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: BytesSent, BytesReceived, VPC Environment, Route Tables")
        else:
            logger.debug(f"VPCPeeringActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_vpc_peering_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich VPC Peering DataFrame with V1-V5 activity signals.

        Args:
            df: DataFrame with vpc_peering_connection_id column

        Returns:
            DataFrame with VPC Peering activity columns and decommission signals

        Columns Added:
            - bytes_sent_90d: Sum of BytesSent over 90 days
            - bytes_received_90d: Sum of BytesReceived over 90 days
            - accepter_vpc_environment: Accepter VPC environment tag
            - requester_vpc_environment: Requester VPC environment tag
            - route_table_entry_count: Number of route tables using peering
            - age_days: Days since peering creation
            - same_account: Boolean (accepter and requester in same account)
            - v1_signal: Zero data transfer (Boolean)
            - v2_signal: Both VPCs non-production (Boolean)
            - v3_signal: No route table entries (Boolean)
            - v4_signal: Age >365 days (Boolean)
            - v5_signal: Same account peering (Boolean)
            - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
            - enrichment_status: String (SUCCESS/FAILED/PENDING)
            - enrichment_error: String (error message if failed)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN
        """
        # Graceful degradation: skip enrichment if no VPC peering connections discovered
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  VPC Peering enrichment skipped - no peering connections discovered")
            logger.info("VPC Peering enrichment skipped - empty DataFrame")
            return df

        # Prerequisite validation: check for required column
        if "vpc_peering_connection_id" not in df.columns:
            # v1.1.20: Changed to DEBUG - graceful degradation, not an error condition
            logger.debug(
                "VPC Peering enrichment skipped - vpc_peering_connection_id column not found",
                extra={
                    "reason": "Missing required column",
                    "signal_impact": "V1-V5 signals unavailable",
                    "alternative": "Ensure VPC Peering discovery completed before enrichment",
                },
            )
            return df

        if self.output_controller.verbose:
            print_info(f"🔄 Starting VPC Peering activity enrichment for {len(df)} peering connections...")
        else:
            logger.info(f"VPC Peering activity enrichment started for {len(df)} peering connections")

        # Initialize activity columns with defaults
        activity_columns = {
            "bytes_sent_90d": 0,
            "bytes_received_90d": 0,
            "accepter_vpc_environment": "unknown",
            "requester_vpc_environment": "unknown",
            "route_table_entry_count": 0,
            "age_days": 0,
            "same_account": False,
            "v1_signal": False,
            "v2_signal": False,
            "v3_signal": False,
            "v4_signal": False,
            "v5_signal": False,
            "cloudwatch_enrichment_success": False,
            "enrichment_status": "PENDING",
            "enrichment_error": "",
            "decommission_score": 0,
            "decommission_tier": "KEEP",
            "total_possible_score": 100,
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # Enrich each VPC Peering Connection with CloudWatch metrics and dependency analysis
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudWatch VPC Peering metrics...", total=len(df))

            for idx, row in df.iterrows():
                peering_id = row.get("vpc_peering_connection_id", "")

                if not peering_id or peering_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get VPC Peering metadata
                    peering_response = self.ec2.describe_vpc_peering_connections(VpcPeeringConnectionIds=[peering_id])

                    peering_connections = peering_response.get("VpcPeeringConnections", [])
                    if not peering_connections:
                        logger.debug(f"VPC Peering Connection not found: {peering_id}")
                        df.at[idx, "enrichment_status"] = "FAILED"
                        df.at[idx, "enrichment_error"] = "Peering connection not found"
                        progress.update(task, advance=1)
                        continue

                    peering_metadata = peering_connections[0]
                    accepter_vpc_info = peering_metadata.get("AccepterVpcInfo", {})
                    requester_vpc_info = peering_metadata.get("RequesterVpcInfo", {})
                    status = peering_metadata.get("Status", {})

                    accepter_vpc_id = accepter_vpc_info.get("VpcId", "")
                    requester_vpc_id = requester_vpc_info.get("VpcId", "")
                    accepter_owner_id = accepter_vpc_info.get("OwnerId", "")
                    requester_owner_id = requester_vpc_info.get("OwnerId", "")

                    # V5: Same account detection
                    if accepter_owner_id and requester_owner_id:
                        df.at[idx, "same_account"] = accepter_owner_id == requester_owner_id

                    # V4: Age calculation
                    # Note: VPC Peering doesn't have explicit creation timestamp in status
                    # Use ExpirationTime if available, otherwise estimate from status timestamp
                    expiration_time = status.get("ExpirationTime")
                    if expiration_time:
                        # Estimate creation as 7 days before expiration (typical peering timeout)
                        creation_estimate = expiration_time - timedelta(days=7)
                        age_days = (datetime.now(timezone.utc) - creation_estimate).days
                        df.at[idx, "age_days"] = age_days

                    # V1: CloudWatch metrics (BytesSent/BytesReceived)
                    # Note: VPC Peering metrics may not be available in all regions/configurations
                    # Graceful degradation if metrics unavailable
                    metrics_available = False
                    try:
                        # Try BytesSent metric
                        bytes_sent_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/VPC",
                            MetricName="BytesSent",
                            Dimensions=[{"Name": "VpcPeeringConnectionId", "Value": peering_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,  # 1-day aggregation
                            Statistics=["Sum"],
                            Unit="Bytes",
                        )

                        bytes_sent_datapoints = bytes_sent_response.get("Datapoints", [])
                        if bytes_sent_datapoints:
                            total_bytes_sent = sum([dp["Sum"] for dp in bytes_sent_datapoints])
                            df.at[idx, "bytes_sent_90d"] = int(total_bytes_sent)
                            metrics_available = True

                        # Try BytesReceived metric
                        bytes_received_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/VPC",
                            MetricName="BytesReceived",
                            Dimensions=[{"Name": "VpcPeeringConnectionId", "Value": peering_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,
                            Statistics=["Sum"],
                            Unit="Bytes",
                        )

                        bytes_received_datapoints = bytes_received_response.get("Datapoints", [])
                        if bytes_received_datapoints:
                            total_bytes_received = sum([dp["Sum"] for dp in bytes_received_datapoints])
                            df.at[idx, "bytes_received_90d"] = int(total_bytes_received)
                            metrics_available = True

                        if metrics_available:
                            df.at[idx, "cloudwatch_enrichment_success"] = True
                            df.at[idx, "enrichment_status"] = "SUCCESS"

                    except Exception as metrics_error:
                        # Graceful degradation: CloudWatch metrics may not exist
                        logger.debug(
                            f"CloudWatch metrics unavailable for peering {peering_id}: {metrics_error}",
                            extra={
                                "peering_id": peering_id,
                                "error_type": type(metrics_error).__name__,
                                "note": "VPC Peering metrics availability varies by region",
                            },
                        )
                        # Continue with route table and VPC environment analysis

                    # V2: VPC environment tags (both accepter and requester)
                    if accepter_vpc_id and accepter_vpc_id != "N/A":
                        try:
                            accepter_vpc_response = self.ec2.describe_vpcs(VpcIds=[accepter_vpc_id])
                            accepter_vpcs = accepter_vpc_response.get("Vpcs", [])

                            if accepter_vpcs:
                                accepter_tags = accepter_vpcs[0].get("Tags", [])
                                for tag in accepter_tags:
                                    key = tag.get("Key", "").lower()
                                    value = tag.get("Value", "").lower()

                                    if key in ["environment", "env"]:
                                        df.at[idx, "accepter_vpc_environment"] = value
                                        break
                        except Exception as vpc_error:
                            logger.debug(
                                f"Accepter VPC tag retrieval failed for {accepter_vpc_id}: {vpc_error}",
                                extra={"vpc_id": accepter_vpc_id, "error_type": type(vpc_error).__name__},
                            )

                    if requester_vpc_id and requester_vpc_id != "N/A":
                        try:
                            requester_vpc_response = self.ec2.describe_vpcs(VpcIds=[requester_vpc_id])
                            requester_vpcs = requester_vpc_response.get("Vpcs", [])

                            if requester_vpcs:
                                requester_tags = requester_vpcs[0].get("Tags", [])
                                for tag in requester_tags:
                                    key = tag.get("Key", "").lower()
                                    value = tag.get("Value", "").lower()

                                    if key in ["environment", "env"]:
                                        df.at[idx, "requester_vpc_environment"] = value
                                        break
                        except Exception as vpc_error:
                            logger.debug(
                                f"Requester VPC tag retrieval failed for {requester_vpc_id}: {vpc_error}",
                                extra={"vpc_id": requester_vpc_id, "error_type": type(vpc_error).__name__},
                            )

                    # V3: Route table dependencies
                    try:
                        # Query all route tables for routes using this peering connection
                        route_tables_response = self.ec2.describe_route_tables(
                            Filters=[{"Name": "route.vpc-peering-connection-id", "Values": [peering_id]}]
                        )

                        route_tables = route_tables_response.get("RouteTables", [])
                        df.at[idx, "route_table_entry_count"] = len(route_tables)

                    except Exception as route_error:
                        logger.debug(
                            f"Route table analysis failed for peering {peering_id}: {route_error}",
                            extra={"peering_id": peering_id, "error_type": type(route_error).__name__},
                        )

                except Exception as e:
                    logger.warning(
                        f"VPC Peering enrichment failed for {peering_id}: {e}",
                        extra={
                            "peering_id": peering_id,
                            "error_type": type(e).__name__,
                            "lookback_days": self.lookback_days,
                            "region": self.region,
                        },
                    )
                    df.at[idx, "enrichment_status"] = "FAILED"
                    df.at[idx, "enrichment_error"] = str(e)

                progress.update(task, advance=1)

        # Calculate decommission signals and scores
        df = self._calculate_decommission_signals(df)

        metrics_found = (df["bytes_sent_90d"] > 0).sum() + (df["bytes_received_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ VPC Peering enrichment complete: {metrics_found} data points collected")
        else:
            logger.info(f"VPC Peering enrichment complete: {metrics_found} data points collected")

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate V1-V5 decommission signals and scores.

        Args:
            df: DataFrame with VPC Peering activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            # Calculate total possible score based on signal availability
            cloudwatch_success = row.get("cloudwatch_enrichment_success", False)
            total_possible = self._calculate_total_possible_score(cloudwatch_success)
            df.at[idx, "total_possible_score"] = total_possible

            signals = {}

            # V1: Zero data transfer (40 points) - No BytesSent/BytesReceived for 90+ days
            bytes_sent = row.get("bytes_sent_90d", 0)
            bytes_received = row.get("bytes_received_90d", 0)
            total_bytes = bytes_sent + bytes_received

            # Note: If CloudWatch metrics unavailable, V1 cannot be determined
            # Only trigger V1 if metrics available and show zero transfer
            cloudwatch_success = row.get("cloudwatch_enrichment_success", False)
            if cloudwatch_success and total_bytes == 0:
                df.at[idx, "v1_signal"] = True
                signals["V1"] = DEFAULT_VPC_PEERING_WEIGHTS["V1"]
            else:
                signals["V1"] = 0

            # V2: Both VPCs non-production (30 points)
            accepter_env = row.get("accepter_vpc_environment", "unknown").lower()
            requester_env = row.get("requester_vpc_environment", "unknown").lower()

            nonprod_environments = ["nonprod", "dev", "test", "staging"]
            accepter_nonprod = accepter_env in nonprod_environments
            requester_nonprod = requester_env in nonprod_environments

            if accepter_nonprod and requester_nonprod:
                df.at[idx, "v2_signal"] = True
                signals["V2"] = DEFAULT_VPC_PEERING_WEIGHTS["V2"]
            else:
                signals["V2"] = 0

            # V3: No route table entries (10 points)
            if row.get("route_table_entry_count", 0) == 0:
                df.at[idx, "v3_signal"] = True
                signals["V3"] = DEFAULT_VPC_PEERING_WEIGHTS["V3"]
            else:
                signals["V3"] = 0

            # V4: Non-production VPC (5 points)
            # Trigger if either VPC is non-production (not both required)
            if accepter_nonprod or requester_nonprod:
                df.at[idx, "v4_signal"] = True
                signals["V4"] = DEFAULT_VPC_PEERING_WEIGHTS["V4"]
            else:
                signals["V4"] = 0

            # V5: Age >180 days (25 points - Manager's adjustment)
            age_days = row.get("age_days", 0)
            if age_days > 180:
                df.at[idx, "v5_signal"] = True
                signals["V5"] = DEFAULT_VPC_PEERING_WEIGHTS["V5"]
            else:
                signals["V5"] = 0

            # Calculate total decommission score
            total_score = sum(signals.values())
            df.at[idx, "decommission_score"] = total_score

            # Determine decommission tier (consistent with VPCE/ALB/DynamoDB/Route53)
            if total_score >= 80:
                df.at[idx, "decommission_tier"] = "MUST"
            elif total_score >= 50:
                df.at[idx, "decommission_tier"] = "SHOULD"
            elif total_score >= 25:
                df.at[idx, "decommission_tier"] = "COULD"
            else:
                df.at[idx, "decommission_tier"] = "KEEP"

        return df

    def _calculate_total_possible_score(self, cloudwatch_enrichment_success: bool) -> int:
        """
        Calculate total possible score based on signal availability.

        Implements manager's dynamic scoring denominator pattern:
        - If CloudWatch available: Score out of 100 (V1 = 40pts possible)
        - If CloudWatch unavailable: Score out of 60 (100-40, V1 removed)

        Args:
            cloudwatch_enrichment_success: Whether CloudWatch metrics were successfully retrieved

        Returns:
            Total possible score (60 or 100)

        Examples:
            >>> # CloudWatch available
            >>> self._calculate_total_possible_score(True)
            100

            >>> # CloudWatch unavailable (V1 signal removed)
            >>> self._calculate_total_possible_score(False)
            60  # 100 - 40 (V1 weight)
        """
        base_score = 100

        # V1 signal depends on CloudWatch metrics (BytesSent/Received for activity)
        if not cloudwatch_enrichment_success:
            base_score -= DEFAULT_VPC_PEERING_WEIGHTS["V1"]  # Remove V1 (40pts)

        return base_score


# Export interface
__all__ = ["VPCPeeringActivityEnricher"]
