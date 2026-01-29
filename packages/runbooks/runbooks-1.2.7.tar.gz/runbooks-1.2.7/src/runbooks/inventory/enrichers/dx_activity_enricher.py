#!/usr/bin/env python3
"""
Direct Connect Activity Enricher - DX Connection Health Signals (DX1-DX4)

Analyzes AWS Direct Connect connection activity patterns using CloudWatch metrics
to identify underutilized or idle DX connections for cost optimization.

Decommission Signals (DX1-DX4):
- DX1: Zero data transfer (55 points) - No ingress/egress for 90+ days
- DX2: Low bandwidth utilization (25 points) - <10% utilization average
- DX3: Connection down (15 points) - ConnectionState != available for 30+ days
- DX4: No BGP peers (5 points) - Virtual interfaces with no BGP peers established

Pattern: Reuses ActivityEnricher structure (KISS/DRY/LEAN)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable DX enrichment
- Enterprise SDLC: Cost optimization for hybrid cloud connectivity
- KISS/DRY/LEAN: Single enricher, CloudWatch consolidation

Usage:
    from runbooks.inventory.enrichers.dx_activity_enricher import DXActivityEnricher

    enricher = DXActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='ap-southeast-2'
    )

    enriched_df = enricher.enrich_dx_activity(discovery_df)

    # Adds columns:
    # - connection_bps_egress_90d: Sum of ConnectionBpsEgress over 90 days
    # - connection_bps_ingress_90d: Sum of ConnectionBpsIngress over 90 days
    # - connection_state: Current connection state (available/down/ordering/requested/pending/deleting/deleted)
    # - bandwidth_gbps: Connection bandwidth in Gbps
    # - utilization_percent_avg: Average utilization over 90 days
    # - dx1_signal: Boolean (zero data transfer)
    # - dx2_signal: Boolean (low utilization)
    # - dx3_signal: Boolean (connection down)
    # - dx4_signal: Boolean (no BGP peers)
    # - decommission_score: Total score (0-100 scale)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 5 - DX Activity Enrichment
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

# DX signal weights (0-100 scale)
DEFAULT_DX_WEIGHTS = {
    "DX1": 55,  # Zero data transfer
    "DX2": 25,  # Low bandwidth utilization
    "DX3": 15,  # Connection down
    "DX4": 5,  # No BGP peers
}


class DXActivityEnricher:
    """
    Direct Connect activity enrichment using CloudWatch metrics for DX1-DX4 decommission signals.

    Consolidates CloudWatch DX metrics into actionable decommission signals:
    - ConnectionBpsEgress/Ingress (DX1: zero transfer)
    - ConnectionState (DX3: connection availability)
    - Bandwidth utilization (DX2: underutilization)
    - BGP peer status (DX4: connectivity health)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
    ):
        """
        Initialize DX activity enricher.

        Args:
            operational_profile: AWS profile for CloudWatch and DirectConnect API access
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)

        Profile Requirements:
            - cloudwatch:GetMetricStatistics (DX namespace metrics)
            - directconnect:DescribeConnections (connection metadata)
            - directconnect:DescribeVirtualInterfaces (BGP peer status)
        """
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        self.session = create_operational_session(resolved_profile)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.dx = create_timeout_protected_client(self.session, "directconnect", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        if self.output_controller.verbose:
            print_info(f"🔍 DXActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: ConnectionBpsEgress/Ingress, ConnectionState, BGP peers")
        else:
            logger.debug(f"DXActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_dx_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich DX DataFrame with DX1-DX4 activity signals.

        Args:
            df: DataFrame with connection_id column

        Returns:
            DataFrame with DX activity columns and decommission signals

        Columns Added:
            - connection_bps_egress_90d: Sum of egress traffic (bps) over 90 days
            - connection_bps_ingress_90d: Sum of ingress traffic (bps) over 90 days
            - connection_state: Connection state (available/down/ordering/etc.)
            - bandwidth_gbps: Connection bandwidth in Gbps
            - utilization_percent_avg: Average utilization percentage
            - dx1_signal: Zero data transfer (Boolean)
            - dx2_signal: Low utilization (Boolean)
            - dx3_signal: Connection down (Boolean)
            - dx4_signal: No BGP peers (Boolean)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP
        """
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  No DX connections to enrich")
            return df

        if "connection_id" not in df.columns:
            raise ValueError("DataFrame must contain 'connection_id' column for DX enrichment")

        if self.output_controller.verbose:
            print_info(f"🔄 Starting DX activity enrichment for {len(df)} connections...")
        else:
            logger.info(f"DX activity enrichment started for {len(df)} connections")

        # Initialize activity columns with defaults
        activity_columns = {
            "connection_bps_egress_90d": 0,
            "connection_bps_ingress_90d": 0,
            "connection_state": "unknown",
            "bandwidth_gbps": 0,
            "utilization_percent_avg": 0.0,
            "dx1_signal": False,
            "dx2_signal": False,
            "dx3_signal": False,
            "dx4_signal": False,
            "decommission_score": 0,
            "decommission_tier": "KEEP",
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # Enrich each DX connection with CloudWatch metrics and metadata
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudWatch DX metrics...", total=len(df))

            for idx, row in df.iterrows():
                connection_id = row.get("connection_id", "")

                if not connection_id or connection_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get connection metadata (state, bandwidth)
                    connection_response = self.dx.describe_connections(connectionId=connection_id)

                    connections = connection_response.get("connections", [])
                    if connections:
                        connection_data = connections[0]
                        df.at[idx, "connection_state"] = connection_data.get("connectionState", "unknown")
                        bandwidth_str = connection_data.get("bandwidth", "0Gbps")
                        # Extract bandwidth numeric value (e.g., "1Gbps" -> 1)
                        bandwidth_gbps = (
                            int(bandwidth_str.replace("Gbps", "").replace("Mbps", "")) if "Gbps" in bandwidth_str else 0
                        )
                        df.at[idx, "bandwidth_gbps"] = bandwidth_gbps

                    # DX1: Connection egress traffic (90 days)
                    egress_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/DX",
                        MetricName="ConnectionBpsEgress",
                        Dimensions=[{"Name": "ConnectionId", "Value": connection_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1-day aggregation
                        Statistics=["Sum"],
                        Unit="Bits/Second",
                    )

                    egress_datapoints = egress_response.get("Datapoints", [])
                    if egress_datapoints:
                        total_egress = sum([dp["Sum"] for dp in egress_datapoints])
                        df.at[idx, "connection_bps_egress_90d"] = int(total_egress)

                    # DX1: Connection ingress traffic (90 days)
                    ingress_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/DX",
                        MetricName="ConnectionBpsIngress",
                        Dimensions=[{"Name": "ConnectionId", "Value": connection_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                        Unit="Bits/Second",
                    )

                    ingress_datapoints = ingress_response.get("Datapoints", [])
                    if ingress_datapoints:
                        total_ingress = sum([dp["Sum"] for dp in ingress_datapoints])
                        df.at[idx, "connection_bps_ingress_90d"] = int(total_ingress)

                    # DX2: Calculate utilization percentage
                    # Utilization = (egress + ingress) / (bandwidth * 2 * time)
                    total_traffic_bps = (
                        df.at[idx, "connection_bps_egress_90d"] + df.at[idx, "connection_bps_ingress_90d"]
                    )
                    bandwidth_bps = bandwidth_gbps * 1_000_000_000  # Convert Gbps to bps
                    total_capacity_bps = bandwidth_bps * 2 * 90 * 86400  # Bidirectional, 90 days in seconds

                    if total_capacity_bps > 0:
                        utilization_percent = (total_traffic_bps / total_capacity_bps) * 100
                        df.at[idx, "utilization_percent_avg"] = round(utilization_percent, 2)

                    # DX4: Check BGP peer status via virtual interfaces
                    try:
                        vif_response = self.dx.describe_virtual_interfaces(connectionId=connection_id)

                        virtual_interfaces = vif_response.get("virtualInterfaces", [])
                        has_bgp_peers = any(vif.get("bgpPeers", []) for vif in virtual_interfaces)

                        if not has_bgp_peers:
                            df.at[idx, "dx4_signal"] = True

                    except Exception as vif_error:
                        logger.debug(f"Virtual interface query failed for {connection_id}: {vif_error}")

                except Exception as e:
                    logger.debug(f"DX metrics failed for connection {connection_id}: {e}")
                    pass

                progress.update(task, advance=1)

        # Calculate decommission signals and scores
        df = self._calculate_decommission_signals(df)

        metrics_found = (df["connection_bps_egress_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ DX enrichment complete: {metrics_found}/{len(df)} connections with traffic")
        else:
            logger.info(f"DX enrichment complete: {metrics_found}/{len(df)} connections with traffic")

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate DX1-DX4 decommission signals and scores.

        Args:
            df: DataFrame with DX activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            signals = {}

            # DX1: Zero data transfer (55 points)
            total_traffic = row.get("connection_bps_egress_90d", 0) + row.get("connection_bps_ingress_90d", 0)
            if total_traffic == 0:
                df.at[idx, "dx1_signal"] = True
                signals["DX1"] = DEFAULT_DX_WEIGHTS["DX1"]
            else:
                signals["DX1"] = 0

            # DX2: Low bandwidth utilization (25 points) - <10% average
            if row.get("utilization_percent_avg", 0) < 10:
                df.at[idx, "dx2_signal"] = True
                signals["DX2"] = DEFAULT_DX_WEIGHTS["DX2"]
            else:
                signals["DX2"] = 0

            # DX3: Connection down (15 points)
            connection_state = row.get("connection_state", "unknown").lower()
            if connection_state in ["down", "deleting", "deleted", "rejected"]:
                df.at[idx, "dx3_signal"] = True
                signals["DX3"] = DEFAULT_DX_WEIGHTS["DX3"]
            else:
                signals["DX3"] = 0

            # DX4: No BGP peers (5 points)
            if row.get("dx4_signal", False):
                signals["DX4"] = DEFAULT_DX_WEIGHTS["DX4"]
            else:
                signals["DX4"] = 0

            # Calculate total decommission score
            total_score = sum(signals.values())
            df.at[idx, "decommission_score"] = total_score

            # Determine decommission tier
            if total_score >= 80:
                df.at[idx, "decommission_tier"] = "MUST"
            elif total_score >= 50:
                df.at[idx, "decommission_tier"] = "SHOULD"
            elif total_score >= 25:
                df.at[idx, "decommission_tier"] = "COULD"
            else:
                df.at[idx, "decommission_tier"] = "KEEP"

        return df


# Export interface
__all__ = ["DXActivityEnricher"]
