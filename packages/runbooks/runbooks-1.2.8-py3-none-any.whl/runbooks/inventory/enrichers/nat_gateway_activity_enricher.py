#!/usr/bin/env python3
"""
NAT Gateway Activity Enricher - NAT Gateway Health Signals (N1-N5)

Analyzes NAT Gateway activity patterns using CloudWatch metrics and availability zone
analysis to identify underutilized or idle NAT Gateways for cost optimization.

Decommission Signals (N1-N5):
- N1: Zero data transfer (40 points) - No BytesOutToDestination for 90+ days
- N2: Zero active connections (20 points) - No ActiveConnectionCount for 90+ days
- N3: Single AZ NAT Gateway (10 points) - No HA redundancy
- N4: Non-production VPC (5 points) - VPC tagged as dev/test/staging
- N5: Age >180 days (25 points) - Old NAT Gateway

Pattern: Reuses VPCE/Peering/Transit Gateway enricher structure (KISS/DRY/LEAN)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable NAT Gateway enrichment
- Enterprise SDLC: Cost optimization with evidence-based signals
- KISS/DRY/LEAN: Single enricher, CloudWatch consolidation, HA validation

Usage:
    from runbooks.inventory.enrichers.nat_gateway_activity_enricher import NATGatewayActivityEnricher

    enricher = NATGatewayActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='ap-southeast-2'
    )

    enriched_df = enricher.enrich_nat_gateway_activity(discovery_df)

    # Adds columns:
    # - bytes_out_90d: Sum of BytesOutToDestination over 90 days
    # - active_connections_90d: Sum of ActiveConnectionCount over 90 days
    # - packets_dropped_90d: Sum of PacketsDropCount over 90 days
    # - availability_zone: NAT Gateway availability zone
    # - vpc_environment: VPC environment tag
    # - nat_gateway_count_same_vpc: Number of NAT Gateways in same VPC
    # - unique_az_count_same_vpc: Number of unique AZs with NAT Gateways in VPC
    # - age_days: Days since NAT Gateway creation
    # - n1_signal: Zero data transfer (Boolean)
    # - n2_signal: Zero active connections (Boolean)
    # - n3_signal: Single AZ NAT Gateway (Boolean)
    # - n4_signal: Non-production VPC (Boolean)
    # - n5_signal: Age >365 days (Boolean)
    # - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
    # - enrichment_status: String (SUCCESS/FAILED/PENDING)
    # - enrichment_error: String (error message if failed)
    # - decommission_score: Total score (0-100)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 16 Phase 4 - NAT Gateway Activity Enrichment
"""

import pandas as pd
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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

# v1.1.29: Import Flow Logs for N6-N10 signals
try:
    from runbooks.vpc.flow_logs_analyzer import VPCFlowLogsAnalyzer, FlowLogTrafficResult

    FLOW_LOGS_AVAILABLE = True
except ImportError:
    FLOW_LOGS_AVAILABLE = False

# v1.1.29: Import Organizations client for multi-account support
try:
    from runbooks.common.organizations_client import UnifiedOrganizationsClient, get_unified_organizations_client

    ORGANIZATIONS_AVAILABLE = True
except ImportError:
    ORGANIZATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)

# NAT Gateway signal weights (0-100 scale for N1-N5, 125 total with N6-N10)
# v1.1.29: Extended from N1-N5 (100 points) to N1-N10 (125 points)
DEFAULT_NAT_GATEWAY_WEIGHTS = {
    "N1": 40,  # Zero data transfer 90+ days (aligns with EC2 E1/S3 S1)
    "N2": 20,  # Zero active connections 90+ days
    "N3": 10,  # Single AZ NAT Gateway (not HA)
    "N4": 5,  # Non-production VPC
    "N5": 25,  # Age >180 days (Manager's age emphasis for VPC)
    # v1.1.29: Enhanced N6-N10 signals via Flow Logs
    "N6": 15,  # VPC Flow Logs zero outbound (0.95 confidence)
    "N7": 10,  # VPCE Gateway alternative available ($0.045/GB savings)
    "N8": 5,  # EIP underutilization (cost waste indicator)
    "N9": 5,  # High packet drop rate (performance issue)
    "N10": 5,  # Cross-AZ traffic cost (architectural inefficiency)
}

# Maximum possible score (N1-N10 total)
MAX_NAT_GATEWAY_SCORE = sum(DEFAULT_NAT_GATEWAY_WEIGHTS.values())  # 140


class NATGatewayActivityEnricher:
    """
    NAT Gateway activity enrichment using CloudWatch metrics for N1-N5 decommission signals.

    Consolidates CloudWatch NAT Gateway metrics into actionable decommission signals:
    - BytesOutToDestination (N1: zero data transfer)
    - ActiveConnectionCount (N2: zero active connections)
    - Availability zone analysis (N3: single AZ, no HA)
    - VPC environment tags (N4: non-production)
    - Creation timestamp (N5: age >365 days)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
        enable_flow_logs: bool = False,
    ):
        """
        Initialize NAT Gateway activity enricher.

        v1.1.29: Added enable_flow_logs for N6-N10 signals via VPC Flow Logs.

        Args:
            operational_profile: AWS profile for CloudWatch API access
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)
            enable_flow_logs: Enable N6-N10 signals via VPC Flow Logs (default: False)

        Profile Requirements:
            - cloudwatch:GetMetricStatistics (NAT Gateway namespace metrics)
            - ec2:DescribeNatGateways (NAT Gateway metadata)
            - ec2:DescribeSubnets (availability zone analysis)
            - ec2:DescribeVpcs (VPC environment tags)
            - logs:StartQuery (CloudWatch Logs Insights - if enable_flow_logs=True)
        """
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        self.session = create_operational_session(resolved_profile)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.ec2 = create_timeout_protected_client(self.session, "ec2", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        # v1.1.29: Enhanced signal configuration
        self.enable_flow_logs = enable_flow_logs and FLOW_LOGS_AVAILABLE

        # Cache for VPC NAT Gateway counts (avoid repeated API calls)
        self._vpc_nat_gateway_cache: Dict[str, Dict] = {}

        # v1.1.29: Lazy initialization for Flow Logs analyzer
        self._flow_logs_analyzer: Optional[VPCFlowLogsAnalyzer] = None

        if self.output_controller.verbose:
            print_info(f"🔍 NATGatewayActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: BytesOutToDestination, ActiveConnectionCount, PacketsDropCount, AZ Analysis")
            if self.enable_flow_logs:
                print_info(f"   Enhanced: N6-N10 Flow Logs signals enabled")
        else:
            logger.debug(f"NATGatewayActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_nat_gateway_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich NAT Gateway DataFrame with N1-N5 activity signals.

        Args:
            df: DataFrame with nat_gateway_id column

        Returns:
            DataFrame with NAT Gateway activity columns and decommission signals

        Columns Added:
            - bytes_out_90d: Sum of BytesOutToDestination over 90 days
            - active_connections_90d: Sum of ActiveConnectionCount over 90 days
            - packets_dropped_90d: Sum of PacketsDropCount over 90 days
            - availability_zone: NAT Gateway availability zone
            - vpc_environment: VPC environment tag
            - nat_gateway_count_same_vpc: Number of NAT Gateways in same VPC
            - unique_az_count_same_vpc: Number of unique AZs with NAT Gateways in VPC
            - age_days: Days since NAT Gateway creation
            - n1_signal: Zero data transfer (Boolean)
            - n2_signal: Zero active connections (Boolean)
            - n3_signal: Single AZ NAT Gateway (Boolean)
            - n4_signal: Non-production VPC (Boolean)
            - n5_signal: Age >365 days (Boolean)
            - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
            - enrichment_status: String (SUCCESS/FAILED/PENDING)
            - enrichment_error: String (error message if failed)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN
        """
        # Graceful degradation: skip enrichment if no NAT Gateways discovered
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  NAT Gateway enrichment skipped - no NAT Gateways discovered")
            logger.info("NAT Gateway enrichment skipped - empty DataFrame")
            return df

        # Prerequisite validation: check for required column
        if "nat_gateway_id" not in df.columns:
            # v1.1.20: Changed to DEBUG - graceful degradation, not an error condition
            logger.debug(
                "NAT Gateway enrichment skipped - nat_gateway_id column not found",
                extra={
                    "reason": "Missing required column",
                    "signal_impact": "N1-N5 signals unavailable",
                    "alternative": "Ensure NAT Gateway discovery completed before enrichment",
                },
            )
            return df

        if self.output_controller.verbose:
            print_info(f"🔄 Starting NAT Gateway activity enrichment for {len(df)} NAT Gateways...")
        else:
            logger.info(f"NAT Gateway activity enrichment started for {len(df)} NAT Gateways")

        # Initialize activity columns with defaults
        # v1.1.29: Added N6-N10 signal columns for Flow Logs analysis
        activity_columns = {
            "bytes_out_90d": 0,
            "active_connections_90d": 0,
            "packets_dropped_90d": 0,
            "availability_zone": "unknown",
            "vpc_environment": "unknown",
            "nat_gateway_count_same_vpc": 0,
            "unique_az_count_same_vpc": 0,
            "age_days": 0,
            "n1_signal": False,
            "n2_signal": False,
            "n3_signal": False,
            "n4_signal": False,
            "n5_signal": False,
            # v1.1.29: Enhanced N6-N10 signals
            "n6_signal": False,  # Flow Logs zero outbound
            "n7_signal": False,  # VPCE Gateway alternative available
            "n8_signal": False,  # EIP underutilization
            "n9_signal": False,  # High packet drop rate
            "n10_signal": False,  # Cross-AZ traffic cost
            "flow_logs_enabled": False,
            "flow_logs_zero_outbound": False,
            "vpce_gateway_alternative": False,
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

        # Enrich each NAT Gateway with CloudWatch metrics and availability zone analysis
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudWatch NAT Gateway metrics...", total=len(df))

            for idx, row in df.iterrows():
                nat_gateway_id = row.get("nat_gateway_id", "")

                if not nat_gateway_id or nat_gateway_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get NAT Gateway metadata
                    nat_response = self.ec2.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])

                    nat_gateways = nat_response.get("NatGateways", [])
                    if not nat_gateways:
                        logger.debug(f"NAT Gateway not found: {nat_gateway_id}")
                        df.at[idx, "enrichment_status"] = "FAILED"
                        df.at[idx, "enrichment_error"] = "NAT Gateway not found"
                        progress.update(task, advance=1)
                        continue

                    nat_metadata = nat_gateways[0]
                    vpc_id = nat_metadata.get("VpcId", "")
                    subnet_id = nat_metadata.get("SubnetId", "")
                    creation_time = nat_metadata.get("CreateTime")
                    state = nat_metadata.get("State", "")

                    # V5: Age calculation
                    if creation_time:
                        age_days = (datetime.now(timezone.utc) - creation_time).days
                        df.at[idx, "age_days"] = age_days

                    # N3: Availability zone analysis via subnet
                    if subnet_id:
                        try:
                            subnet_response = self.ec2.describe_subnets(SubnetIds=[subnet_id])
                            subnets = subnet_response.get("Subnets", [])

                            if subnets:
                                availability_zone = subnets[0].get("AvailabilityZone", "unknown")
                                df.at[idx, "availability_zone"] = availability_zone

                        except Exception as subnet_error:
                            logger.debug(
                                f"Subnet retrieval failed for {subnet_id}: {subnet_error}",
                                extra={"subnet_id": subnet_id, "error_type": type(subnet_error).__name__},
                            )

                    # N3: Count NAT Gateways and unique AZs in same VPC
                    if vpc_id:
                        vpc_analysis = self._get_vpc_nat_gateway_analysis(vpc_id)
                        df.at[idx, "nat_gateway_count_same_vpc"] = vpc_analysis["total_count"]
                        df.at[idx, "unique_az_count_same_vpc"] = vpc_analysis["unique_az_count"]

                    # N4: VPC environment tag
                    if vpc_id and vpc_id != "N/A":
                        try:
                            vpc_response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
                            vpcs = vpc_response.get("Vpcs", [])

                            if vpcs:
                                vpc_tags = vpcs[0].get("Tags", [])
                                for tag in vpc_tags:
                                    key = tag.get("Key", "").lower()
                                    value = tag.get("Value", "").lower()

                                    if key in ["environment", "env"]:
                                        df.at[idx, "vpc_environment"] = value
                                        break

                        except Exception as vpc_error:
                            logger.debug(
                                f"VPC tag retrieval failed for {vpc_id}: {vpc_error}",
                                extra={"vpc_id": vpc_id, "error_type": type(vpc_error).__name__},
                            )

                    # N1 & N2: CloudWatch metrics (BytesOutToDestination/ActiveConnectionCount/PacketsDropCount)
                    metrics_available = False
                    try:
                        # BytesOutToDestination metric
                        bytes_out_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/NATGateway",
                            MetricName="BytesOutToDestination",
                            Dimensions=[{"Name": "NatGatewayId", "Value": nat_gateway_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,  # 1-day aggregation
                            Statistics=["Sum"],
                            Unit="Bytes",
                        )

                        bytes_out_datapoints = bytes_out_response.get("Datapoints", [])
                        if bytes_out_datapoints:
                            total_bytes_out = sum([dp["Sum"] for dp in bytes_out_datapoints])
                            df.at[idx, "bytes_out_90d"] = int(total_bytes_out)
                            metrics_available = True

                        # ActiveConnectionCount metric
                        connections_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/NATGateway",
                            MetricName="ActiveConnectionCount",
                            Dimensions=[{"Name": "NatGatewayId", "Value": nat_gateway_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,
                            Statistics=["Sum"],
                            Unit="Count",
                        )

                        connections_datapoints = connections_response.get("Datapoints", [])
                        if connections_datapoints:
                            total_connections = sum([dp["Sum"] for dp in connections_datapoints])
                            df.at[idx, "active_connections_90d"] = int(total_connections)
                            metrics_available = True

                        # PacketsDropCount metric (optional - may not exist)
                        try:
                            packets_dropped_response = self.cloudwatch.get_metric_statistics(
                                Namespace="AWS/NATGateway",
                                MetricName="PacketsDropCount",
                                Dimensions=[{"Name": "NatGatewayId", "Value": nat_gateway_id}],
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
                            # PacketsDropCount metric may not exist - graceful degradation
                            pass

                        if metrics_available:
                            df.at[idx, "cloudwatch_enrichment_success"] = True
                            df.at[idx, "enrichment_status"] = "SUCCESS"

                    except Exception as metrics_error:
                        # Graceful degradation: CloudWatch metrics may not exist
                        logger.debug(
                            f"CloudWatch metrics unavailable for NAT Gateway {nat_gateway_id}: {metrics_error}",
                            extra={
                                "nat_gateway_id": nat_gateway_id,
                                "error_type": type(metrics_error).__name__,
                                "note": "NAT Gateway metrics availability varies by region",
                            },
                        )
                        # Continue with availability zone and VPC environment analysis

                except Exception as e:
                    logger.warning(
                        f"NAT Gateway enrichment failed for {nat_gateway_id}: {e}",
                        extra={
                            "nat_gateway_id": nat_gateway_id,
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

        metrics_found = (df["bytes_out_90d"] > 0).sum() + (df["active_connections_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ NAT Gateway enrichment complete: {metrics_found} data points collected")
        else:
            logger.info(f"NAT Gateway enrichment complete: {metrics_found} data points collected")

        return df

    def _get_vpc_nat_gateway_analysis(self, vpc_id: str) -> Dict[str, int]:
        """
        Get NAT Gateway count and unique AZ count for a VPC.

        Args:
            vpc_id: VPC ID to analyze

        Returns:
            Dict with total_count and unique_az_count
        """
        # Check cache first
        if vpc_id in self._vpc_nat_gateway_cache:
            return self._vpc_nat_gateway_cache[vpc_id]

        try:
            # Query all NAT Gateways in this VPC
            nat_response = self.ec2.describe_nat_gateways(
                Filters=[{"Name": "vpc-id", "Values": [vpc_id]}, {"Name": "state", "Values": ["available"]}]
            )

            nat_gateways = nat_response.get("NatGateways", [])
            total_count = len(nat_gateways)

            # Get unique availability zones
            availability_zones = set()
            for nat_gateway in nat_gateways:
                subnet_id = nat_gateway.get("SubnetId", "")
                if subnet_id:
                    try:
                        subnet_response = self.ec2.describe_subnets(SubnetIds=[subnet_id])
                        subnets = subnet_response.get("Subnets", [])
                        if subnets:
                            az = subnets[0].get("AvailabilityZone")
                            if az:
                                availability_zones.add(az)
                    except Exception:
                        # Graceful degradation - skip subnet if unavailable
                        pass

            unique_az_count = len(availability_zones)

            result = {"total_count": total_count, "unique_az_count": unique_az_count}

            # Cache result
            self._vpc_nat_gateway_cache[vpc_id] = result

            return result

        except Exception as e:
            logger.debug(
                f"VPC NAT Gateway analysis failed for {vpc_id}: {e}",
                extra={"vpc_id": vpc_id, "error_type": type(e).__name__},
            )
            return {"total_count": 0, "unique_az_count": 0}

    def _get_nat_gateway_route_analysis(self, nat_gateway_id: str) -> Dict[str, Any]:
        """
        Check if NAT Gateway has active route table entries.

        Returns:
            {
                'has_routes': bool,
                'route_count': int,
                'route_table_available': bool
            }
        """
        # Check cache first
        if not hasattr(self, "_route_cache"):
            self._route_cache = {}

        if nat_gateway_id in self._route_cache:
            return self._route_cache[nat_gateway_id]

        try:
            route_tables = self.ec2.describe_route_tables(
                Filters=[{"Name": "route.nat-gateway-id", "Values": [nat_gateway_id]}]
            )

            result = {
                "has_routes": len(route_tables["RouteTables"]) > 0,
                "route_count": len(route_tables["RouteTables"]),
                "route_table_available": True,
            }

            # Cache result
            self._route_cache[nat_gateway_id] = result
            return result

        except Exception as e:
            logger.debug(f"Route table query failed for {nat_gateway_id}: {e}")
            return {"has_routes": False, "route_count": 0, "route_table_available": False}

    def _check_alternative_egress(self, nat_gateway_id: str, vpc_id: str) -> Dict[str, Any]:
        """
        Check if private subnets have alternative egress (IGW or other NAT).

        Simplified logic:
        1. Find route tables using this NAT Gateway
        2. Check for IGW route (0.0.0.0/0 → igw-*)
        3. Check for another NAT Gateway route

        Returns:
            {
                'has_alternative': bool,
                'alternative_type': str,  # 'igw', 'nat', 'none'
                'route_table_available': bool
            }
        """
        try:
            # Find route tables using this NAT
            route_tables = self.ec2.describe_route_tables(
                Filters=[{"Name": "route.nat-gateway-id", "Values": [nat_gateway_id]}]
            )

            if not route_tables["RouteTables"]:
                return {"has_alternative": False, "alternative_type": "none", "route_table_available": True}

            # Check for IGW or other NAT in same VPC
            for rt in route_tables["RouteTables"]:
                for route in rt.get("Routes", []):
                    destination = route.get("DestinationCidrBlock", "")
                    gateway_id = route.get("GatewayId", "")
                    nat_gw = route.get("NatGatewayId", "")

                    # IGW route = alternative egress
                    if destination == "0.0.0.0/0" and gateway_id.startswith("igw-"):
                        return {"has_alternative": True, "alternative_type": "igw", "route_table_available": True}

                    # Another NAT = alternative egress
                    if nat_gw and nat_gw != nat_gateway_id:
                        return {"has_alternative": True, "alternative_type": "nat", "route_table_available": True}

            return {"has_alternative": False, "alternative_type": "none", "route_table_available": True}

        except Exception as e:
            logger.debug(f"Alternative egress check failed: {e}")
            return {"has_alternative": False, "alternative_type": "none", "route_table_available": False}

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate N1-N5 decommission signals and scores.

        Args:
            df: DataFrame with NAT Gateway activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        # Initialize route cache for route table queries
        self._route_cache = {}

        for idx, row in df.iterrows():
            nat_gateway_id = row.get("nat_gateway_id")
            vpc_id = row.get("vpc_id")

            # Check signal availability for dynamic denominator
            cloudwatch_success = row.get("cloudwatch_enrichment_success", False)

            # Check route table availability (used by N2A and N3A)
            route_analysis = self._get_nat_gateway_route_analysis(nat_gateway_id)
            route_table_available = route_analysis["route_table_available"]

            # Calculate total possible score based on signal availability
            total_possible = self._calculate_total_possible_score(cloudwatch_success, route_table_available)
            df.at[idx, "total_possible_score"] = total_possible

            signals = {}

            # N1: Zero data transfer (40 points) - No BytesOutToDestination for 90+ days
            bytes_out = row.get("bytes_out_90d", 0)

            # Note: If CloudWatch metrics unavailable, N1 cannot be determined
            # Only trigger N1 if metrics available and show zero transfer
            if cloudwatch_success and bytes_out == 0:
                df.at[idx, "n1_signal"] = True
                signals["N1"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N1"]
            else:
                signals["N1"] = 0

            # N2: Hybrid signal (routes + connections) - 20 points total
            # N2A: No route table entries (10pts)
            if route_table_available and not route_analysis["has_routes"]:
                df.at[idx, "n2a_signal"] = True
                signals["N2A"] = 10
            else:
                df.at[idx, "n2a_signal"] = False
                signals["N2A"] = 0

            # N2B: Zero CloudWatch connections (10pts - adjusted from 5pts for 20pt total)
            active_connections = row.get("active_connections_90d", 0)
            if cloudwatch_success and active_connections == 0:
                df.at[idx, "n2b_signal"] = True
                signals["N2B"] = 10
            else:
                df.at[idx, "n2b_signal"] = False
                signals["N2B"] = 0

            # Total N2 signal
            signals["N2"] = signals["N2A"] + signals["N2B"]
            df.at[idx, "n2_signal"] = signals["N2"] > 0

            # N3: Hybrid signal (egress + HA) - 10 points total
            # N3A: Alternative egress exists (5pts - adjusted for balance)
            egress_analysis = self._check_alternative_egress(nat_gateway_id, vpc_id)
            if route_table_available and not egress_analysis["has_alternative"]:
                df.at[idx, "n3a_signal"] = True
                signals["N3A"] = 5
            else:
                df.at[idx, "n3a_signal"] = False
                signals["N3A"] = 0

            # N3B: Single AZ deployment (5pts)
            unique_az_count = row.get("unique_az_count_same_vpc", 0)
            if unique_az_count == 1:
                df.at[idx, "n3b_signal"] = True
                signals["N3B"] = 5
            else:
                df.at[idx, "n3b_signal"] = False
                signals["N3B"] = 0

            # Total N3 signal
            signals["N3"] = signals["N3A"] + signals["N3B"]
            df.at[idx, "n3_signal"] = signals["N3"] > 0

            # N4: Non-production VPC (5 points)
            vpc_environment = row.get("vpc_environment", "unknown").lower()

            nonprod_environments = ["nonprod", "dev", "test", "staging"]
            if vpc_environment in nonprod_environments:
                df.at[idx, "n4_signal"] = True
                signals["N4"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N4"]
            else:
                signals["N4"] = 0

            # N5: Age >180 days (25 points - Manager's adjustment)
            age_days = row.get("age_days", 0)
            if age_days > 180:
                df.at[idx, "n5_signal"] = True
                signals["N5"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N5"]
            else:
                signals["N5"] = 0

            # Calculate total decommission score
            total_score = sum(signals.values())
            df.at[idx, "decommission_score"] = total_score

            # Determine decommission tier with dynamic threshold adjustment
            tier = self._calculate_tier_with_dynamic_scoring(total_score, total_possible)
            df.at[idx, "decommission_tier"] = tier

        return df

    def _calculate_total_possible_score(self, cloudwatch_enrichment_success: bool, route_table_available: bool) -> int:
        """
        Calculate NAT Gateway total possible score with dynamic denominator.

        Implements manager's pattern: Adjust denominator when APIs unavailable.

        Args:
            cloudwatch_enrichment_success: Whether CloudWatch metrics succeeded
            route_table_available: Whether EC2 route table API succeeded

        Returns:
            Total possible score (30-100 range)
        """
        base_score = 100

        # N1 depends on CloudWatch (40pts)
        if not cloudwatch_enrichment_success:
            base_score -= DEFAULT_NAT_GATEWAY_WEIGHTS["N1"]  # -40

        # N2B depends on CloudWatch (10pts)
        if not cloudwatch_enrichment_success:
            base_score -= 10

        # N2A + N3A depend on route table API (10pts + 5pts = 15pts)
        if not route_table_available:
            base_score -= 15

        # Possible scores: 100 (all available), 50 (no CloudWatch),
        # 85 (no routes), 35 (neither), minimum 30 (N3B+N4+N5)
        return base_score

    def _calculate_tier_with_dynamic_scoring(self, score: int, total_possible: int) -> str:
        """
        Calculate tier with dynamic threshold adjustment.

        Implements manager's proportional tier adjustment:
        - Full signals (100): MUST=80, SHOULD=50, COULD=25
        - Reduced signals: Proportional thresholds

        Args:
            score: Actual decommission score (0-100)
            total_possible: Total possible score (30-100 depending on signal availability)

        Returns:
            Tier classification (MUST/SHOULD/COULD/KEEP)
        """
        base_thresholds = {"MUST": 80, "SHOULD": 50, "COULD": 25, "KEEP": 0}

        if total_possible < 100:
            # Proportional adjustment: threshold * (total_possible / 100)
            adjusted_thresholds = {
                tier: int(threshold * total_possible / 100) for tier, threshold in base_thresholds.items()
            }
        else:
            adjusted_thresholds = base_thresholds

        # Tier classification with adjusted thresholds
        if score >= adjusted_thresholds["MUST"]:
            return "MUST"
        elif score >= adjusted_thresholds["SHOULD"]:
            return "SHOULD"
        elif score >= adjusted_thresholds["COULD"]:
            return "COULD"
        else:
            return "KEEP"

    # ═══════════════════════════════════════════════════════════════════════════
    # v1.1.29: N6-N10 ENHANCED SIGNAL METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_flow_logs_analyzer(self) -> Optional["VPCFlowLogsAnalyzer"]:
        """
        Lazy initialization of VPC Flow Logs analyzer.

        Returns:
            VPCFlowLogsAnalyzer instance or None if unavailable
        """
        if not self.enable_flow_logs:
            return None

        if self._flow_logs_analyzer is None:
            try:
                self._flow_logs_analyzer = VPCFlowLogsAnalyzer(operational_profile=self.profile, region=self.region)
                logger.debug("VPCFlowLogsAnalyzer initialized for NAT Gateway analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize Flow Logs analyzer: {e}")
                return None

        return self._flow_logs_analyzer

    def _check_n6_flow_logs_zero_outbound(
        self, nat_gateway_id: str, nat_eni_id: str, vpc_id: str, age_days: int
    ) -> tuple:
        """
        N6: VPC Flow Logs show 0 outbound flows through NAT Gateway.

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
        Confidence: 0.95 (Flow Logs proof)
        Business Value: Ground truth NAT usage validation

        v1.1.29: Updated to use flow_logs_detector.py for availability check

        Args:
            nat_gateway_id: NAT Gateway ID
            nat_eni_id: NAT Gateway ENI ID
            vpc_id: VPC ID containing the NAT Gateway
            age_days: Age of NAT Gateway in days

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            # Import flow_logs_detector for availability check
            from runbooks.vpc.flow_logs_detector import detect_flow_logs_availability

            # Check Flow Logs availability first (cached, efficient)
            flow_logs_enabled = detect_flow_logs_availability(vpc_id, self.ec2)

            if not flow_logs_enabled:
                # Gracefully skip - Flow Logs not available
                return False, {"flow_logs_available": False, "error": "Flow Logs not enabled for VPC"}

            # Flow Logs available - query traffic analyzer
            flow_analyzer = self._get_flow_logs_analyzer()
            if not flow_analyzer:
                return False, {"error": "Flow Logs analyzer unavailable", "flow_logs_available": False}

            traffic_result = flow_analyzer.query_nat_gateway_traffic(
                nat_gateway_id=nat_gateway_id, nat_eni_id=nat_eni_id, vpc_id=vpc_id, days=90
            )

            # Signal if 0 outbound flows AND age >90 days
            signal_active = traffic_result.accepted_flows == 0 and age_days >= 90 and traffic_result.flow_logs_enabled

            metadata = {
                "outbound_flows": traffic_result.accepted_flows,
                "total_bytes_out": traffic_result.total_bytes,
                "flow_logs_available": traffic_result.flow_logs_enabled,
                "confidence": 0.95 if traffic_result.flow_logs_enabled else 0.0,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"N6 signal check failed for {nat_gateway_id}: {e}")
            return False, {"error": str(e), "flow_logs_available": False}

    def _check_n7_vpce_alternative(self, nat_gateway_id: str, vpc_id: str, nat_eni_id: str) -> tuple:
        """
        N7: NAT used for AWS services (S3/DynamoDB) but no VPCE Gateway exists.

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/vpce-gateway.html
        Confidence: 0.85 (Cost optimization opportunity)
        Business Value: $0.045/GB NAT -> $0 VPCE Gateway (100% savings)

        Args:
            nat_gateway_id: NAT Gateway ID
            vpc_id: VPC ID containing the NAT Gateway
            nat_eni_id: NAT Gateway ENI ID

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            # Query Flow Logs for AWS service destinations
            aws_service_traffic = False
            monthly_gb = 0.0

            flow_analyzer = self._get_flow_logs_analyzer()
            if flow_analyzer:
                try:
                    traffic_result = flow_analyzer.query_nat_gateway_traffic(
                        nat_gateway_id=nat_gateway_id, nat_eni_id=nat_eni_id, vpc_id=vpc_id, days=30
                    )
                    # Note: Full implementation would analyze destinations for S3/DynamoDB IPs
                    # Simplified: Check if significant traffic exists
                    monthly_gb = traffic_result.total_bytes / (1024**3) if traffic_result.total_bytes else 0
                except Exception:
                    pass

            # Check for existing VPCE Gateway endpoints
            try:
                vpce_response = self.ec2.describe_vpc_endpoints(
                    Filters=[
                        {"Name": "vpc-id", "Values": [vpc_id]},
                        {"Name": "vpc-endpoint-type", "Values": ["Gateway"]},
                    ]
                )

                gateway_endpoints = vpce_response.get("VpcEndpoints", [])
                has_s3_gateway = any(
                    "com.amazonaws" in ep.get("ServiceName", "") and "s3" in ep.get("ServiceName", "")
                    for ep in gateway_endpoints
                )
                has_dynamodb_gateway = any(
                    "com.amazonaws" in ep.get("ServiceName", "") and "dynamodb" in ep.get("ServiceName", "")
                    for ep in gateway_endpoints
                )

                # Signal if no gateway endpoint AND NAT has traffic
                # Simplified: Signal if no gateway endpoints exist at all
                signal_active = not (has_s3_gateway or has_dynamodb_gateway) and monthly_gb > 0

                # Calculate potential savings: $0.045/GB
                monthly_savings = monthly_gb * 0.045
                annual_savings = monthly_savings * 12

                metadata = {
                    "has_s3_gateway": has_s3_gateway,
                    "has_dynamodb_gateway": has_dynamodb_gateway,
                    "monthly_gb_transferred": round(monthly_gb, 2),
                    "annual_savings_potential": round(annual_savings, 2),
                    "confidence": 0.85,
                }

                return signal_active, metadata

            except Exception as e:
                logger.debug(f"VPCE Gateway check failed for {vpc_id}: {e}")
                return False, {"error": str(e)}

        except Exception as e:
            logger.debug(f"N7 signal check failed for {nat_gateway_id}: {e}")
            return False, {"error": str(e)}

    def _check_n8_eip_underutilization(self, nat_gateway_id: str, bytes_out_90d: int) -> tuple:
        """
        N8: EIP underutilization (NAT with minimal traffic).

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
        Confidence: 0.70 (Cost waste indicator)
        Business Value: $0.045/hour EIP cost with minimal usage

        Args:
            nat_gateway_id: NAT Gateway ID
            bytes_out_90d: Bytes out over 90 days

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            # Get NAT Gateway EIP allocation
            nat_response = self.ec2.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])

            nat_gateways = nat_response.get("NatGateways", [])
            if not nat_gateways:
                return False, {"error": "NAT Gateway not found"}

            nat_gateway = nat_gateways[0]
            eip_allocations = nat_gateway.get("NatGatewayAddresses", [])

            has_eip = len(eip_allocations) > 0

            # Convert bytes to GB for 90 days
            gb_out_90d = bytes_out_90d / (1024**3) if bytes_out_90d else 0

            # Underutilization threshold: <1GB over 90 days
            is_underutilized = gb_out_90d < 1.0

            # Signal if has EIP AND underutilized
            signal_active = has_eip and is_underutilized

            # EIP cost: $0.045/hour = $32.40/month = $388.80/year
            annual_eip_cost = 0.045 * 24 * 365

            metadata = {
                "has_eip": has_eip,
                "eip_count": len(eip_allocations),
                "gb_out_90d": round(gb_out_90d, 4),
                "is_underutilized": is_underutilized,
                "annual_eip_cost": round(annual_eip_cost, 2),
                "confidence": 0.70,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"N8 signal check failed for {nat_gateway_id}: {e}")
            return False, {"error": str(e)}

    def _check_n9_packet_drop_rate(self, packets_dropped_90d: int, bytes_out_90d: int) -> tuple:
        """
        N9: High packet drop rate (performance issue indicator).

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway-cloudwatch.html
        Confidence: 0.75 (Performance degradation)
        Business Value: Network quality issue identification

        Args:
            packets_dropped_90d: Packets dropped over 90 days
            bytes_out_90d: Bytes out over 90 days (for ratio calculation)

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            # Calculate drop rate (packets dropped vs total traffic)
            # Simplified: If packets dropped > 1000 with low traffic, flag as issue
            has_drops = packets_dropped_90d > 1000
            low_traffic = bytes_out_90d < (100 * 1024 * 1024)  # < 100MB

            # Signal if high drops AND low traffic (indicates unused with issues)
            signal_active = has_drops and low_traffic

            metadata = {
                "packets_dropped_90d": packets_dropped_90d,
                "bytes_out_90d": bytes_out_90d,
                "has_drops": has_drops,
                "low_traffic": low_traffic,
                "confidence": 0.75,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"N9 signal check failed: {e}")
            return False, {"error": str(e)}

    def _check_n10_cross_az_traffic(self, nat_gateway_id: str, vpc_id: str, availability_zone: str) -> tuple:
        """
        N10: Cross-AZ traffic cost (architectural inefficiency).

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html#nat-gateway-limits
        Confidence: 0.60 (Architecture assessment)
        Business Value: $0.01/GB cross-AZ data transfer cost

        Args:
            nat_gateway_id: NAT Gateway ID
            vpc_id: VPC ID
            availability_zone: NAT Gateway availability zone

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            # Check for subnets in other AZs using this NAT Gateway
            route_tables = self.ec2.describe_route_tables(
                Filters=[{"Name": "route.nat-gateway-id", "Values": [nat_gateway_id]}]
            )

            cross_az_subnets = []
            for rt in route_tables.get("RouteTables", []):
                associations = rt.get("Associations", [])
                for assoc in associations:
                    subnet_id = assoc.get("SubnetId")
                    if subnet_id:
                        try:
                            subnet_response = self.ec2.describe_subnets(SubnetIds=[subnet_id])
                            subnets = subnet_response.get("Subnets", [])
                            if subnets:
                                subnet_az = subnets[0].get("AvailabilityZone", "")
                                if subnet_az and subnet_az != availability_zone:
                                    cross_az_subnets.append(subnet_id)
                        except Exception:
                            pass

            # Signal if NAT serves subnets in different AZs
            signal_active = len(cross_az_subnets) > 0

            metadata = {
                "nat_az": availability_zone,
                "cross_az_subnet_count": len(cross_az_subnets),
                "cross_az_subnets": cross_az_subnets[:5],  # Limit for response size
                "cross_az_cost_per_gb": 0.01,
                "confidence": 0.60,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"N10 signal check failed for {nat_gateway_id}: {e}")
            return False, {"error": str(e)}

    def enrich_n6_n10_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enhanced enrichment with N6-N10 signals via Flow Logs.

        v1.1.29: This method adds N6-N10 signal columns to an existing DataFrame
        that already has N1-N5 signals from enrich_nat_gateway_activity().

        Args:
            df: DataFrame with nat_gateway_id and N1-N5 signals

        Returns:
            DataFrame with N6-N10 signal columns added

        Signal Coverage:
        - N6: Flow Logs zero outbound (15 pts, confidence 0.95)
        - N7: VPCE Gateway alternative (10 pts, confidence 0.85)
        - N8: EIP underutilization (5 pts, confidence 0.70)
        - N9: High packet drop rate (5 pts, confidence 0.75)
        - N10: Cross-AZ traffic cost (5 pts, confidence 0.60)
        """
        if df.empty:
            return df

        if "nat_gateway_id" not in df.columns:
            logger.debug("N6-N10 enrichment skipped - nat_gateway_id column not found")
            return df

        if not self.enable_flow_logs:
            logger.debug("N6-N10 enrichment skipped - Flow Logs disabled")
            return df

        if self.output_controller.verbose:
            print_info(f"🔍 Starting N6-N10 enhanced signal enrichment for {len(df)} NAT Gateways...")

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]N6-N10 Enhanced Signals...", total=len(df))

            for idx, row in df.iterrows():
                nat_gateway_id = row.get("nat_gateway_id", "")
                vpc_id = row.get("vpc_id", "")
                age_days = row.get("age_days", 0)
                bytes_out_90d = row.get("bytes_out_90d", 0)
                packets_dropped_90d = row.get("packets_dropped_90d", 0)
                availability_zone = row.get("availability_zone", "")

                if not nat_gateway_id or nat_gateway_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                # Get NAT Gateway ENI ID
                nat_eni_id = ""
                try:
                    nat_response = self.ec2.describe_nat_gateways(NatGatewayIds=[nat_gateway_id])
                    nat_gateways = nat_response.get("NatGateways", [])
                    if nat_gateways:
                        addresses = nat_gateways[0].get("NatGatewayAddresses", [])
                        if addresses:
                            nat_eni_id = addresses[0].get("NetworkInterfaceId", "")
                except Exception:
                    pass

                # N6: Flow Logs zero outbound
                if nat_eni_id:
                    n6_active, n6_metadata = self._check_n6_flow_logs_zero_outbound(
                        nat_gateway_id=nat_gateway_id, nat_eni_id=nat_eni_id, vpc_id=vpc_id, age_days=age_days
                    )
                    df.at[idx, "n6_signal"] = n6_active
                    df.at[idx, "flow_logs_enabled"] = n6_metadata.get("flow_logs_available", False)
                    df.at[idx, "flow_logs_zero_outbound"] = n6_active

                # N7: VPCE Gateway alternative
                n7_active, n7_metadata = self._check_n7_vpce_alternative(
                    nat_gateway_id=nat_gateway_id, vpc_id=vpc_id, nat_eni_id=nat_eni_id
                )
                df.at[idx, "n7_signal"] = n7_active
                df.at[idx, "vpce_gateway_alternative"] = n7_active

                # N8: EIP underutilization
                n8_active, _ = self._check_n8_eip_underutilization(
                    nat_gateway_id=nat_gateway_id, bytes_out_90d=bytes_out_90d
                )
                df.at[idx, "n8_signal"] = n8_active

                # N9: High packet drop rate
                n9_active, _ = self._check_n9_packet_drop_rate(
                    packets_dropped_90d=packets_dropped_90d, bytes_out_90d=bytes_out_90d
                )
                df.at[idx, "n9_signal"] = n9_active

                # N10: Cross-AZ traffic cost
                n10_active, _ = self._check_n10_cross_az_traffic(
                    nat_gateway_id=nat_gateway_id, vpc_id=vpc_id, availability_zone=availability_zone
                )
                df.at[idx, "n10_signal"] = n10_active

                progress.update(task, advance=1)

        # Recalculate decommission scores with N6-N10 signals
        df = self._calculate_enhanced_decommission_scores(df)

        if self.output_controller.verbose:
            n6_count = df["n6_signal"].sum()
            n7_count = df["n7_signal"].sum()
            n8_count = df["n8_signal"].sum()
            n9_count = df["n9_signal"].sum()
            n10_count = df["n10_signal"].sum()
            print_success(
                f"✅ N6-N10 enrichment complete: N6={n6_count}, N7={n7_count}, N8={n8_count}, N9={n9_count}, N10={n10_count}"
            )

        return df

    def _calculate_enhanced_decommission_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Recalculate decommission scores including N6-N10 signals.

        v1.1.29: Updates scores from 100-point scale to 140-point scale (normalized to 0-100).

        Args:
            df: DataFrame with N1-N10 signal columns

        Returns:
            DataFrame with updated decommission_score and decommission_tier
        """
        for idx, row in df.iterrows():
            signals = {}

            # N1-N5 signals (100 points base)
            if row.get("n1_signal", False):
                signals["N1"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N1"]
            if row.get("n2_signal", False):
                signals["N2"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N2"]
            if row.get("n3_signal", False):
                signals["N3"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N3"]
            if row.get("n4_signal", False):
                signals["N4"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N4"]
            if row.get("n5_signal", False):
                signals["N5"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N5"]

            # N6-N10 signals (40 additional points)
            if row.get("n6_signal", False):
                signals["N6"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N6"]
            if row.get("n7_signal", False):
                signals["N7"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N7"]
            if row.get("n8_signal", False):
                signals["N8"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N8"]
            if row.get("n9_signal", False):
                signals["N9"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N9"]
            if row.get("n10_signal", False):
                signals["N10"] = DEFAULT_NAT_GATEWAY_WEIGHTS["N10"]

            # Calculate raw score (0-140 range)
            raw_score = sum(signals.values())

            # Normalize to 0-100 scale
            normalized_score = int(raw_score * 100 / MAX_NAT_GATEWAY_SCORE)
            df.at[idx, "decommission_score"] = normalized_score
            df.at[idx, "total_possible_score"] = 100  # Normalized

            # Determine tier based on normalized score
            if normalized_score >= 80:
                df.at[idx, "decommission_tier"] = "MUST"
            elif normalized_score >= 50:
                df.at[idx, "decommission_tier"] = "SHOULD"
            elif normalized_score >= 25:
                df.at[idx, "decommission_tier"] = "COULD"
            else:
                df.at[idx, "decommission_tier"] = "KEEP"

        return df

    # ═══════════════════════════════════════════════════════════════════════════
    # v1.1.29: MULTI-ACCOUNT ORGANIZATIONS INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def enrich_multi_account(
        self, management_profile: str, ops_profile: str, cross_account_role: str = "CloudOpsReadOnly"
    ) -> pd.DataFrame:
        """
        Multi-account NAT Gateway enrichment via Organizations API.

        v1.1.29: Discovers NAT Gateways across all organization accounts and
        enriches with N1-N10 signals using cross-account AssumeRole.

        Args:
            management_profile: AWS profile with organizations:ListAccounts
            ops_profile: AWS profile with ec2:Describe* (for cross-account AssumeRole)
            cross_account_role: IAM role name for cross-account access (default: CloudOpsReadOnly)

        Returns:
            DataFrame with NAT Gateways from all organization accounts

        Profile Requirements:
            - management_profile: organizations:ListAccounts
            - ops_profile: ec2:DescribeNatGateways + sts:AssumeRole

        Business Value:
            - 67 accounts baseline (proven from organization)
            - Organization-wide NAT Gateway cost optimization visibility
            - Cross-account HA architecture validation
        """
        if not ORGANIZATIONS_AVAILABLE:
            logger.warning("Organizations client unavailable - single account enrichment only")
            return pd.DataFrame()

        if self.output_controller.verbose:
            print_info("🏢 Starting multi-account NAT Gateway discovery...")

        # Get organization accounts
        org_client = get_unified_organizations_client(management_profile)
        accounts = await org_client.get_organization_accounts()

        if not accounts:
            logger.warning("No organization accounts discovered")
            return pd.DataFrame()

        if self.output_controller.verbose:
            print_info(f"📊 Discovered {len(accounts)} organization accounts")

        # Discover NAT Gateways across accounts
        all_nat_dfs = []
        successful_accounts = 0
        failed_accounts = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Multi-Account NAT Gateway Discovery...", total=len(accounts))

            for account in accounts:
                account_id = account.account_id
                account_name = account.name

                try:
                    # Create cross-account session via AssumeRole
                    account_df = await self._discover_account_nat_gateways(
                        account_id=account_id,
                        account_name=account_name,
                        ops_profile=ops_profile,
                        cross_account_role=cross_account_role,
                    )

                    if not account_df.empty:
                        # Add account metadata
                        account_df["account_id"] = account_id
                        account_df["account_name"] = account_name
                        account_df["organizational_unit"] = account.organizational_unit or "Unknown"

                        all_nat_dfs.append(account_df)
                        successful_accounts += 1

                except Exception as e:
                    # Graceful degradation: skip inaccessible accounts
                    logger.debug(f"Account {account_id} ({account_name}) enrichment failed: {e}")
                    failed_accounts += 1

                progress.update(task, advance=1)

        if not all_nat_dfs:
            if self.output_controller.verbose:
                print_warning("⚠️  No NAT Gateways discovered across organization")
            return pd.DataFrame()

        # Combine all account DataFrames
        combined_df = pd.concat(all_nat_dfs, ignore_index=True)

        if self.output_controller.verbose:
            print_success(
                f"✅ Multi-account discovery complete: "
                f"{len(combined_df)} NAT Gateways from {successful_accounts} accounts "
                f"({failed_accounts} accounts inaccessible)"
            )

        return combined_df

    async def _discover_account_nat_gateways(
        self, account_id: str, account_name: str, ops_profile: str, cross_account_role: str
    ) -> pd.DataFrame:
        """
        Discover NAT Gateways in a single account via cross-account AssumeRole.

        Args:
            account_id: Target account ID
            account_name: Target account name (for logging)
            ops_profile: Profile for STS AssumeRole
            cross_account_role: IAM role name to assume

        Returns:
            DataFrame with NAT Gateways from the target account
        """
        import boto3

        try:
            # Create STS client from operational profile
            resolved_profile = get_profile_for_operation("operational", ops_profile)
            session = create_operational_session(resolved_profile)
            sts = session.client("sts")

            # Assume cross-account role
            role_arn = f"arn:aws:iam::{account_id}:role/{cross_account_role}"
            assumed_role = sts.assume_role(RoleArn=role_arn, RoleSessionName=f"runbooks-nat-discovery-{account_id[:8]}")

            credentials = assumed_role["Credentials"]

            # Create EC2 client with assumed credentials
            assumed_session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )

            ec2 = assumed_session.client("ec2", region_name=self.region)

            # Discover NAT Gateways
            nat_gateways = []
            paginator = ec2.get_paginator("describe_nat_gateways")

            for page in paginator.paginate():
                for nat_gw in page.get("NatGateways", []):
                    nat_gateways.append(
                        {
                            "nat_gateway_id": nat_gw.get("NatGatewayId", ""),
                            "vpc_id": nat_gw.get("VpcId", ""),
                            "subnet_id": nat_gw.get("SubnetId", ""),
                            "state": nat_gw.get("State", ""),
                            "create_time": nat_gw.get("CreateTime"),
                            "connectivity_type": nat_gw.get("ConnectivityType", "public"),
                            "nat_gateway_addresses": nat_gw.get("NatGatewayAddresses", []),
                            "tags": {t["Key"]: t["Value"] for t in nat_gw.get("Tags", [])},
                        }
                    )

            return pd.DataFrame(nat_gateways)

        except Exception as e:
            logger.debug(f"NAT Gateway discovery failed for account {account_id}: {e}")
            return pd.DataFrame()


# Export interface
__all__ = ["NATGatewayActivityEnricher"]
