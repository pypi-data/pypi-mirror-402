#!/usr/bin/env python3
"""
Transit Gateway Activity Enricher - Transit Gateway Health Signals (V1-V5)

Analyzes Transit Gateway activity patterns using CloudWatch metrics and attachment
analysis to identify underutilized or idle transit gateways for cost optimization.

Decommission Signals (V1-V5):
- V1: Zero data transfer (40 points) - No BytesIn/BytesOut for 90+ days
- V2: No VPC attachments OR all attachments non-production (20 points)
- V3: No route table propagation enabled (10 points)
- V4: Non-production VPC (5 points) - Environment tags indicate dev/test/staging
- V5: Age >180 days (25 points)

Pattern: Reuses VPCE/Peering enricher structure (KISS/DRY/LEAN)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable Transit Gateway enrichment
- Enterprise SDLC: Cost optimization with evidence-based signals
- KISS/DRY/LEAN: Single enricher, CloudWatch consolidation, attachment delegation

Usage:
    from runbooks.inventory.enrichers.transit_gateway_activity_enricher import TransitGatewayActivityEnricher

    enricher = TransitGatewayActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='ap-southeast-2'
    )

    enriched_df = enricher.enrich_transit_gateway_activity(discovery_df)

    # Adds columns:
    # - bytes_in_90d: Sum of BytesIn over 90 days
    # - bytes_out_90d: Sum of BytesOut over 90 days
    # - packets_dropped_90d: Sum of PacketsDropped over 90 days
    # - vpc_attachment_count: Number of VPC attachments
    # - nonprod_vpc_percentage: Percentage of VPC attachments in non-production
    # - route_table_propagation_enabled: Boolean (propagation enabled)
    # - peering_connection_count: Number of Transit Gateway peering connections
    # - age_days: Days since transit gateway creation
    # - v1_signal: Zero data transfer (Boolean)
    # - v2_signal: No VPC attachments OR all non-production (Boolean)
    # - v3_signal: No route table propagation (Boolean)
    # - v4_signal: No peering connections (Boolean)
    # - v5_signal: Age >365 days (Boolean)
    # - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
    # - enrichment_status: String (SUCCESS/FAILED/PENDING)
    # - enrichment_error: String (error message if failed)
    # - decommission_score: Total score (0-100)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 16 Phase 3 - Transit Gateway Activity Enrichment
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

# Transit Gateway signal weights (0-100 scale)
DEFAULT_TRANSIT_GATEWAY_WEIGHTS = {
    "V1": 40,  # Zero data transfer 90+ days (aligns with EC2 E1/S3 S1)
    "V2": 20,  # No VPC attachments OR all attachments non-production
    "V3": 10,  # No route table propagation enabled
    "V4": 5,  # Non-production VPC
    "V5": 25,  # Age >180 days (Manager's age emphasis for VPC)
}


class TransitGatewayActivityEnricher:
    """
    Transit Gateway activity enrichment using CloudWatch metrics for V1-V5 decommission signals.

    Consolidates CloudWatch Transit Gateway metrics into actionable decommission signals:
    - BytesIn/BytesOut (V1: zero data transfer)
    - VPC attachment analysis (V2: no attachments OR all non-production)
    - Route table propagation (V3: no propagation enabled)
    - Peering connections (V4: no peering)
    - Creation timestamp (V5: age >365 days)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
    ):
        """
        Initialize Transit Gateway activity enricher.

        Args:
            operational_profile: AWS profile for CloudWatch API access
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)

        Profile Requirements:
            - cloudwatch:GetMetricStatistics (TransitGateway namespace metrics)
            - ec2:DescribeTransitGateways (transit gateway metadata)
            - ec2:DescribeTransitGatewayAttachments (VPC attachments)
            - ec2:DescribeTransitGatewayRouteTables (route table analysis)
            - ec2:DescribeTransitGatewayPeeringAttachments (peering connections)
            - ec2:DescribeVpcs (VPC environment tags)
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
            print_info(f"🔍 TransitGatewayActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: BytesIn, BytesOut, PacketsDropped, VPC Attachments, Route Tables, Peering")
        else:
            logger.debug(f"TransitGatewayActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_transit_gateway_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich Transit Gateway DataFrame with V1-V5 activity signals.

        Args:
            df: DataFrame with transit_gateway_id column

        Returns:
            DataFrame with Transit Gateway activity columns and decommission signals

        Columns Added:
            - bytes_in_90d: Sum of BytesIn over 90 days
            - bytes_out_90d: Sum of BytesOut over 90 days
            - packets_dropped_90d: Sum of PacketsDropped over 90 days
            - vpc_attachment_count: Number of VPC attachments
            - nonprod_vpc_percentage: Percentage of VPC attachments in non-production
            - route_table_propagation_enabled: Boolean (propagation enabled)
            - peering_connection_count: Number of Transit Gateway peering connections
            - age_days: Days since transit gateway creation
            - v1_signal: Zero data transfer (Boolean)
            - v2_signal: No VPC attachments OR all non-production (Boolean)
            - v3_signal: No route table propagation (Boolean)
            - v4_signal: No peering connections (Boolean)
            - v5_signal: Age >365 days (Boolean)
            - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
            - enrichment_status: String (SUCCESS/FAILED/PENDING)
            - enrichment_error: String (error message if failed)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN
        """
        # Graceful degradation: skip enrichment if no transit gateways discovered
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  Transit Gateway enrichment skipped - no transit gateways discovered")
            logger.info("Transit Gateway enrichment skipped - empty DataFrame")
            return df

        # Prerequisite validation: check for required column
        if "transit_gateway_id" not in df.columns:
            # v1.1.20: Changed to DEBUG - graceful degradation, not an error condition
            logger.debug(
                "Transit Gateway enrichment skipped - transit_gateway_id column not found",
                extra={
                    "reason": "Missing required column",
                    "signal_impact": "V1-V5 signals unavailable",
                    "alternative": "Ensure Transit Gateway discovery completed before enrichment",
                },
            )
            return df

        if self.output_controller.verbose:
            print_info(f"🔄 Starting Transit Gateway activity enrichment for {len(df)} transit gateways...")
        else:
            logger.info(f"Transit Gateway activity enrichment started for {len(df)} transit gateways")

        # Initialize activity columns with defaults
        activity_columns = {
            "bytes_in_90d": 0,
            "bytes_out_90d": 0,
            "packets_dropped_90d": 0,
            "vpc_attachment_count": 0,
            "nonprod_vpc_percentage": 0.0,
            "route_table_propagation_enabled": False,
            "peering_connection_count": 0,
            "age_days": 0,
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

        # Enrich each Transit Gateway with CloudWatch metrics and attachment analysis
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudWatch Transit Gateway metrics...", total=len(df))

            for idx, row in df.iterrows():
                tgw_id = row.get("transit_gateway_id", "")

                if not tgw_id or tgw_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get Transit Gateway metadata
                    tgw_response = self.ec2.describe_transit_gateways(TransitGatewayIds=[tgw_id])

                    transit_gateways = tgw_response.get("TransitGateways", [])
                    if not transit_gateways:
                        logger.debug(f"Transit Gateway not found: {tgw_id}")
                        df.at[idx, "enrichment_status"] = "FAILED"
                        df.at[idx, "enrichment_error"] = "Transit Gateway not found"
                        progress.update(task, advance=1)
                        continue

                    tgw_metadata = transit_gateways[0]
                    creation_time = tgw_metadata.get("CreationTime")
                    default_route_table_id = tgw_metadata.get("Options", {}).get("DefaultRouteTableId", "")

                    # V5: Age calculation
                    if creation_time:
                        age_days = (datetime.now(timezone.utc) - creation_time).days
                        df.at[idx, "age_days"] = age_days

                    # V1: CloudWatch metrics (BytesIn/BytesOut/PacketsDropped)
                    metrics_available = False
                    try:
                        # BytesIn metric
                        bytes_in_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/TransitGateway",
                            MetricName="BytesIn",
                            Dimensions=[{"Name": "TransitGateway", "Value": tgw_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,  # 1-day aggregation
                            Statistics=["Sum"],
                            Unit="Bytes",
                        )

                        bytes_in_datapoints = bytes_in_response.get("Datapoints", [])
                        if bytes_in_datapoints:
                            total_bytes_in = sum([dp["Sum"] for dp in bytes_in_datapoints])
                            df.at[idx, "bytes_in_90d"] = int(total_bytes_in)
                            metrics_available = True

                        # BytesOut metric
                        bytes_out_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/TransitGateway",
                            MetricName="BytesOut",
                            Dimensions=[{"Name": "TransitGateway", "Value": tgw_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,
                            Statistics=["Sum"],
                            Unit="Bytes",
                        )

                        bytes_out_datapoints = bytes_out_response.get("Datapoints", [])
                        if bytes_out_datapoints:
                            total_bytes_out = sum([dp["Sum"] for dp in bytes_out_datapoints])
                            df.at[idx, "bytes_out_90d"] = int(total_bytes_out)
                            metrics_available = True

                        # PacketsDropped metric (optional - may not exist)
                        try:
                            packets_dropped_response = self.cloudwatch.get_metric_statistics(
                                Namespace="AWS/TransitGateway",
                                MetricName="PacketsDropped",
                                Dimensions=[{"Name": "TransitGateway", "Value": tgw_id}],
                                StartTime=start_time,
                                EndTime=end_time,
                                Period=86400,
                                Statistics=["Sum"],
                                Unit="Count",
                            )

                            packets_dropped_datapoints = packets_dropped_response.get("Datapoints", [])
                            if packets_dropped_datapoints:
                                total_packets_dropped = sum([dp["Sum"] for dp in packets_dropped_datapoints])
                                df.at[idx, "packets_dropped_90d"] = int(total_packets_dropped)
                        except Exception:
                            # PacketsDropped metric may not exist - graceful degradation
                            pass

                        if metrics_available:
                            df.at[idx, "cloudwatch_enrichment_success"] = True
                            df.at[idx, "enrichment_status"] = "SUCCESS"

                    except Exception as metrics_error:
                        # Graceful degradation: CloudWatch metrics may not exist
                        logger.debug(
                            f"CloudWatch metrics unavailable for transit gateway {tgw_id}: {metrics_error}",
                            extra={
                                "tgw_id": tgw_id,
                                "error_type": type(metrics_error).__name__,
                                "note": "Transit Gateway metrics availability varies by region",
                            },
                        )
                        # Continue with attachment and route table analysis

                    # V2: VPC attachment analysis
                    try:
                        attachments_response = self.ec2.describe_transit_gateway_attachments(
                            Filters=[
                                {"Name": "transit-gateway-id", "Values": [tgw_id]},
                                {"Name": "resource-type", "Values": ["vpc"]},
                                {"Name": "state", "Values": ["available"]},
                            ]
                        )

                        attachments = attachments_response.get("TransitGatewayAttachments", [])
                        df.at[idx, "vpc_attachment_count"] = len(attachments)

                        # Analyze VPC environment tags
                        if attachments:
                            nonprod_count = 0
                            for attachment in attachments:
                                vpc_id = attachment.get("ResourceId", "")
                                if not vpc_id:
                                    continue

                                try:
                                    vpc_response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
                                    vpcs = vpc_response.get("Vpcs", [])

                                    if vpcs:
                                        vpc_tags = vpcs[0].get("Tags", [])
                                        for tag in vpc_tags:
                                            key = tag.get("Key", "").lower()
                                            value = tag.get("Value", "").lower()

                                            if key in ["environment", "env"]:
                                                if value in ["nonprod", "dev", "test", "staging"]:
                                                    nonprod_count += 1
                                                break
                                except Exception as vpc_error:
                                    logger.debug(
                                        f"VPC tag retrieval failed for {vpc_id}: {vpc_error}",
                                        extra={"vpc_id": vpc_id, "error_type": type(vpc_error).__name__},
                                    )

                            # Calculate non-production percentage
                            if len(attachments) > 0:
                                df.at[idx, "nonprod_vpc_percentage"] = (nonprod_count / len(attachments)) * 100

                    except Exception as attachment_error:
                        logger.debug(
                            f"VPC attachment analysis failed for transit gateway {tgw_id}: {attachment_error}",
                            extra={"tgw_id": tgw_id, "error_type": type(attachment_error).__name__},
                        )

                    # V3: Route table propagation analysis
                    if default_route_table_id:
                        try:
                            route_tables_response = self.ec2.describe_transit_gateway_route_tables(
                                TransitGatewayRouteTableIds=[default_route_table_id]
                            )

                            route_tables = route_tables_response.get("TransitGatewayRouteTables", [])
                            if route_tables:
                                # Check if propagations exist
                                # Note: Propagations are retrieved via separate API call
                                try:
                                    propagations_response = self.ec2.get_transit_gateway_route_table_propagations(
                                        TransitGatewayRouteTableId=default_route_table_id
                                    )

                                    propagations = propagations_response.get("TransitGatewayRouteTablePropagations", [])
                                    if propagations:
                                        df.at[idx, "route_table_propagation_enabled"] = True
                                except Exception:
                                    # API may not be available in all regions - graceful degradation
                                    pass

                        except Exception as route_error:
                            logger.debug(
                                f"Route table analysis failed for transit gateway {tgw_id}: {route_error}",
                                extra={"tgw_id": tgw_id, "error_type": type(route_error).__name__},
                            )

                    # V4: Peering connection analysis
                    try:
                        peering_response = self.ec2.describe_transit_gateway_peering_attachments(
                            Filters=[
                                {"Name": "transit-gateway-id", "Values": [tgw_id]},
                                {"Name": "state", "Values": ["available"]},
                            ]
                        )

                        peering_attachments = peering_response.get("TransitGatewayPeeringAttachments", [])
                        df.at[idx, "peering_connection_count"] = len(peering_attachments)

                    except Exception as peering_error:
                        logger.debug(
                            f"Peering connection analysis failed for transit gateway {tgw_id}: {peering_error}",
                            extra={"tgw_id": tgw_id, "error_type": type(peering_error).__name__},
                        )

                except Exception as e:
                    logger.warning(
                        f"Transit Gateway enrichment failed for {tgw_id}: {e}",
                        extra={
                            "tgw_id": tgw_id,
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

        metrics_found = (df["bytes_in_90d"] > 0).sum() + (df["bytes_out_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ Transit Gateway enrichment complete: {metrics_found} data points collected")
        else:
            logger.info(f"Transit Gateway enrichment complete: {metrics_found} data points collected")

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate V1-V5 decommission signals and scores.

        Args:
            df: DataFrame with Transit Gateway activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            # Calculate total possible score based on signal availability
            cloudwatch_success = row.get("cloudwatch_enrichment_success", False)
            total_possible = self._calculate_total_possible_score(cloudwatch_success)
            df.at[idx, "total_possible_score"] = total_possible

            signals = {}

            # V1: Zero data transfer (40 points) - No BytesIn/BytesOut for 90+ days
            bytes_in = row.get("bytes_in_90d", 0)
            bytes_out = row.get("bytes_out_90d", 0)
            total_bytes = bytes_in + bytes_out

            # Note: If CloudWatch metrics unavailable, V1 cannot be determined
            # Only trigger V1 if metrics available and show zero transfer
            cloudwatch_success = row.get("cloudwatch_enrichment_success", False)
            if cloudwatch_success and total_bytes == 0:
                df.at[idx, "v1_signal"] = True
                signals["V1"] = DEFAULT_TRANSIT_GATEWAY_WEIGHTS["V1"]
            else:
                signals["V1"] = 0

            # V2: No VPC attachments OR all attachments non-production (30 points)
            vpc_attachment_count = row.get("vpc_attachment_count", 0)
            nonprod_percentage = row.get("nonprod_vpc_percentage", 0.0)

            if vpc_attachment_count == 0 or nonprod_percentage == 100.0:
                df.at[idx, "v2_signal"] = True
                signals["V2"] = DEFAULT_TRANSIT_GATEWAY_WEIGHTS["V2"]
            else:
                signals["V2"] = 0

            # V3: No route table propagation enabled (10 points)
            if not row.get("route_table_propagation_enabled", False):
                df.at[idx, "v3_signal"] = True
                signals["V3"] = DEFAULT_TRANSIT_GATEWAY_WEIGHTS["V3"]
            else:
                signals["V3"] = 0

            # V4: Non-production VPC (5 points) - triggered if any attached VPC is non-production
            nonprod_percentage = row.get("nonprod_vpc_percentage", 0.0)
            if nonprod_percentage > 0:
                df.at[idx, "v4_signal"] = True
                signals["V4"] = DEFAULT_TRANSIT_GATEWAY_WEIGHTS["V4"]
            else:
                signals["V4"] = 0

            # V5: Age >180 days (25 points - Manager's adjustment)
            age_days = row.get("age_days", 0)
            if age_days > 180:
                df.at[idx, "v5_signal"] = True
                signals["V5"] = DEFAULT_TRANSIT_GATEWAY_WEIGHTS["V5"]
            else:
                signals["V5"] = 0

            # Calculate total decommission score
            total_score = sum(signals.values())
            df.at[idx, "decommission_score"] = total_score

            # Determine decommission tier (consistent with VPCE/Peering/ALB/DynamoDB/Route53)
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

        # V1 signal depends on CloudWatch metrics (BytesIn/Out for activity)
        if not cloudwatch_enrichment_success:
            base_score -= DEFAULT_TRANSIT_GATEWAY_WEIGHTS["V1"]  # Remove V1 (40pts)

        return base_score


# Export interface
__all__ = ["TransitGatewayActivityEnricher"]
