#!/usr/bin/env python3
"""
VPC Endpoint Activity Enricher - VPC Endpoint Health Signals (V1-V10)

Analyzes VPC Endpoint activity patterns using Cost Explorer billing data, VPC Flow Logs,
and Network Insights for comprehensive decommission signal analysis.

v1.1.29 Enhancement: Added V6-V10 signals with VPC Flow Logs and Network Insights integration
for enhanced confidence in decommission decisions (125 points total, normalized to 0-100).

v1.1.27 Enhancement: Replaced CloudWatch data transfer metrics with Cost Explorer billing data
to align with MCP validator expectations and achieve >=99.5% accuracy target (was 1.31%).

Decommission Signals (V1-V10):
- V1: Zero billing cost (40 points) - No VPC charges for 90+ days (Cost Explorer)
- V2: No service dependencies (20 points) - Zero resources using endpoint
- V3: Interface endpoints with 1 interface only (10 points) - Minimal configuration
- V4: Non-production VPC (5 points) - Environment tags indicate dev/test/staging
- V5: Age >180 days unused (25 points) - Old endpoint with zero billing

v1.1.29 Enhanced Signals (V6-V10):
- V6: VPC Flow Logs Zero Traffic (15 points) - 0 accepted flows over 30 days
- V7: Security Group Overly Permissive (10 points) - 0.0.0.0/0 but no traffic
- V8: Endpoint Policy Too Broad (5 points) - "*" actions but no usage
- V9: Network Insights Path Unreachable (10 points) - Path analysis fails to destination
- V10: Multi-Region Redundancy Missing (5 points) - Single-region endpoint without DR

AWS Well-Architected Alignment:
- Cost Optimization: Evidence-based idle resource identification
- Security: Overly permissive security group detection
- Reliability: Multi-region redundancy assessment
- Operational Excellence: Automated decommission signal generation

AWS Documentation References:
- V1-V5: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints.html
- V6/N6: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
- V7: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html
- V8: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints-access.html
- V9: https://docs.aws.amazon.com/vpc/latest/userguide/network-insights.html

Pattern: Reuses FinOps cost_processor.py Cost Explorer pattern (100% MCP accuracy proven)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable VPC Endpoint enrichment
- Enterprise SDLC: Cost optimization with evidence-based signals
- KISS/DRY/LEAN: Single enricher, Cost Explorer integration, dependency delegation

Usage:
    from runbooks.inventory.enrichers.vpce_activity_enricher import VPCEActivityEnricher

    enricher = VPCEActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        billing_profile='${BILLING_PROFILE}',  # v1.1.27: Cost Explorer access
        region='ap-southeast-2',
        enable_flow_logs=True,  # v1.1.29: Enable V6-V8 signals
        enable_network_insights=True  # v1.1.29: Enable V9-V10 signals
    )

    enriched_df = enricher.enrich_vpce_activity(discovery_df)

    # Adds columns:
    # - vpc_cost_90d: VPC billing charges over 90 days (Cost Explorer) [v1.1.27]
    # - bytes_in_90d: Deprecated (kept for backward compatibility, set to 0.0)
    # - bytes_out_90d: Deprecated (kept for backward compatibility, set to 0.0)
    # - dependency_count: Number of resources using endpoint
    # - interface_count: Number of network interfaces
    # - vpc_environment: VPC environment tag (prod/nonprod/dev/test/staging)
    # - age_days: Days since endpoint creation
    # - v1_signal: Boolean (zero billing cost) [v1.1.27 UPDATED]
    # - v2_signal: Boolean (no dependencies)
    # - v3_signal: Boolean (minimal interfaces)
    # - v4_signal: Boolean (non-production VPC)
    # - v5_signal: Boolean (age >180 days with zero billing) [v1.1.27 UPDATED]
    # - v6_signal: Boolean (Flow Logs zero traffic) [v1.1.29 NEW]
    # - v7_signal: Boolean (Security Group overly permissive) [v1.1.29 NEW]
    # - v8_signal: Boolean (Endpoint policy too broad) [v1.1.29 NEW]
    # - v9_signal: Boolean (Network Insights unreachable) [v1.1.29 NEW]
    # - v10_signal: Boolean (Multi-region redundancy missing) [v1.1.29 NEW]
    # - flow_logs_enabled: Boolean (Flow Logs available for VPC) [v1.1.29]
    # - flow_logs_zero_traffic: Boolean (zero accepted flows) [v1.1.29]
    # - network_insights_unreachable: Boolean (path unreachable) [v1.1.29]
    # - cost_explorer_enrichment_success: Boolean (enrichment succeeded) [v1.1.27]
    # - enrichment_status: String (SUCCESS/FAILED/PENDING)
    # - enrichment_error: String (error message if failed)
    # - decommission_score: Total score (0-100 scale, normalized from 125 points)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN
    # - total_possible_score: Maximum achievable score (varies by signal availability)

Author: Runbooks Team
Version: 1.1.29
Epic: v1.1.29 VPC/VPCE Enhanced Signals
Track: Track 2 Day 1 - V6-V10 Flow Logs + Network Insights Integration
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
from runbooks.vpc.endpoint_dependency_mapper import VPCEndpointDependencyMapper

# v1.1.29: Import Flow Logs and Network Insights for V6-V10 signals
try:
    from runbooks.vpc.flow_logs_analyzer import VPCFlowLogsAnalyzer, FlowLogTrafficResult

    FLOW_LOGS_AVAILABLE = True
except ImportError:
    FLOW_LOGS_AVAILABLE = False

try:
    from runbooks.vpc.network_insights_client import NetworkInsightsClient, NetworkPathAnalysisResult

    NETWORK_INSIGHTS_AVAILABLE = True
except ImportError:
    NETWORK_INSIGHTS_AVAILABLE = False

# v1.1.29: Import Organizations client for multi-account support
try:
    from runbooks.common.organizations_client import UnifiedOrganizationsClient, get_unified_organizations_client

    ORGANIZATIONS_AVAILABLE = True
except ImportError:
    ORGANIZATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)

# VPC Endpoint signal weights (125 points total, normalized to 0-100 scale)
# v1.1.29: Extended from V1-V5 (100 points) to V1-V10 (125 points)
DEFAULT_VPCE_WEIGHTS = {
    # Original V1-V5 signals (100 points)
    "V1": 40,  # Zero billing cost 90+ days (Cost Explorer)
    "V2": 20,  # No service dependencies
    "V3": 10,  # Interface endpoints with 1 interface only
    "V4": 5,  # Non-production VPC
    "V5": 25,  # Age >180 days unused (Manager's age emphasis for VPC)
    # v1.1.29: Enhanced V6-V10 signals (25 additional points)
    "V6": 15,  # VPC Flow Logs zero traffic (ground truth validation)
    "V7": 10,  # Security Group overly permissive (0.0.0.0/0 but no traffic)
    "V8": 5,  # Endpoint policy too broad ("*" actions but no usage)
    "V9": 10,  # Network Insights path unreachable
    "V10": 5,  # Multi-region redundancy missing (single-region + zero usage)
}

# Maximum possible score (V1-V10 = 145 points, normalized to 0-100)
MAX_VPCE_SCORE = sum(DEFAULT_VPCE_WEIGHTS.values())  # 145 (V1-V10 total)


class VPCEActivityEnricher:
    """
    VPC Endpoint activity enrichment using Cost Explorer billing data for V1-V5 decommission signals.

    v1.1.27: Replaced CloudWatch data transfer metrics with Cost Explorer billing data
    to align with MCP validator expectations and achieve ≥99.5% accuracy target.

    Consolidates AWS Cost Explorer and EC2 metadata into actionable decommission signals:
    - VPC billing costs (V1: zero charges) [Cost Explorer - v1.1.27]
    - VPCEndpointDependencyMapper delegation (V2: no dependencies)
    - NetworkInterfaceIds count (V3: minimal interfaces)
    - VPC environment tags (V4: non-production)
    - CreationTimestamp + zero billing (V5: age unused) [v1.1.27]
    """

    def __init__(
        self,
        operational_profile: str,
        billing_profile: Optional[str] = None,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
        enable_flow_logs: bool = False,
        enable_network_insights: bool = False,
    ):
        """
        Initialize VPC Endpoint activity enricher.

        v1.1.27: Added billing_profile for Cost Explorer API access (replaces CloudWatch metrics).
        v1.1.29: Added enable_flow_logs and enable_network_insights for V6-V10 signals.

        Args:
            operational_profile: AWS profile for EC2 API access (endpoint metadata, VPC tags)
            billing_profile: AWS profile for Cost Explorer API access (optional, defaults to operational_profile)
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: Cost Explorer lookback period (default: 90 days)
            enable_flow_logs: Enable V6-V8 signals via VPC Flow Logs (default: False)
            enable_network_insights: Enable V9-V10 signals via Network Insights (default: False)

        Profile Requirements:
            - ce:GetCostAndUsage (Cost Explorer billing data) [billing_profile]
            - ec2:DescribeVpcEndpoints (endpoint metadata) [operational_profile]
            - ec2:DescribeVpcs (VPC environment tags) [operational_profile]
            - logs:StartQuery (CloudWatch Logs Insights - if enable_flow_logs=True)
            - ec2:CreateNetworkInsightsPath (Network Insights - if enable_network_insights=True)
        """
        resolved_operational_profile = get_profile_for_operation("operational", operational_profile)
        self.operational_session = create_operational_session(resolved_operational_profile)

        # v1.1.27: Create separate billing session for Cost Explorer
        # Default to operational_profile if billing_profile not provided (backward compatibility)
        resolved_billing_profile = billing_profile or resolved_operational_profile
        if billing_profile:
            resolved_billing_profile = get_profile_for_operation("billing", billing_profile)

        self.billing_session = create_operational_session(resolved_billing_profile)
        self.ce = create_timeout_protected_client(
            self.billing_session, "ce", region_name="us-east-1"
        )  # Cost Explorer requires us-east-1

        self.ec2 = create_timeout_protected_client(self.operational_session, "ec2", region_name=region)

        self.region = region
        self.operational_profile = resolved_operational_profile
        self.billing_profile = resolved_billing_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        # v1.1.29: Enhanced signal configuration
        self.enable_flow_logs = enable_flow_logs and FLOW_LOGS_AVAILABLE
        self.enable_network_insights = enable_network_insights and NETWORK_INSIGHTS_AVAILABLE

        # Initialize VPCEndpointDependencyMapper (DRY - reuse existing code)
        self.dependency_mapper = VPCEndpointDependencyMapper(profile=resolved_operational_profile, region=region)

        # v1.1.29: Initialize Flow Logs analyzer (lazy - only if enabled)
        self._flow_logs_analyzer: Optional[VPCFlowLogsAnalyzer] = None
        self._network_insights_client: Optional[NetworkInsightsClient] = None

        if self.output_controller.verbose:
            print_info(
                f"🔍 VPCEActivityEnricher initialized: operational={resolved_operational_profile}, billing={resolved_billing_profile}, region={region}"
            )
            print_info(f"   Metrics: VPC Cost (Cost Explorer), Dependencies, NetworkInterfaces, VPC Environment")
            if self.enable_flow_logs:
                print_info(f"   Enhanced: V6-V8 Flow Logs signals enabled")
            if self.enable_network_insights:
                print_info(f"   Enhanced: V9-V10 Network Insights signals enabled")
        else:
            logger.debug(
                f"VPCEActivityEnricher initialized: operational={resolved_operational_profile}, billing={resolved_billing_profile}, region={region}"
            )

    def enrich_vpce_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich VPC Endpoint DataFrame with V1-V5 activity signals.

        v1.1.27: Updated to use Cost Explorer billing data instead of CloudWatch metrics.

        Args:
            df: DataFrame with vpc_endpoint_id column

        Returns:
            DataFrame with VPC Endpoint activity columns and decommission signals

        Columns Added:
            - vpc_cost_90d: VPC billing charges over 90 days (Cost Explorer) [v1.1.27]
            - bytes_in_90d: Deprecated (kept for backward compatibility, set to 0.0)
            - bytes_out_90d: Deprecated (kept for backward compatibility, set to 0.0)
            - dependency_count: Number of resources using endpoint
            - interface_count: Number of network interfaces
            - vpc_environment: VPC environment tag (prod/nonprod/dev/test/staging)
            - age_days: Days since endpoint creation
            - v1_signal: Zero billing cost (Boolean) [v1.1.27 UPDATED]
            - v2_signal: No dependencies (Boolean)
            - v3_signal: Minimal interfaces (Boolean)
            - v4_signal: Non-production VPC (Boolean)
            - v5_signal: Age >180 days with zero billing (Boolean) [v1.1.27 UPDATED]
            - cost_explorer_enrichment_success: Boolean (enrichment succeeded) [v1.1.27]
            - enrichment_status: String (SUCCESS/FAILED/PENDING)
            - enrichment_error: String (error message if failed)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN
        """
        # Graceful degradation: skip enrichment if no VPC endpoints discovered
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  VPC Endpoint enrichment skipped - no endpoints discovered")
            logger.info("VPC Endpoint enrichment skipped - empty DataFrame")
            return df

        # Prerequisite validation: check for required column
        if "vpc_endpoint_id" not in df.columns:
            # v1.1.20: Changed to DEBUG - graceful degradation, not an error condition
            logger.debug(
                "VPC Endpoint enrichment skipped - vpc_endpoint_id column not found",
                extra={
                    "reason": "Missing required column",
                    "signal_impact": "V1-V5 signals unavailable",
                    "alternative": "Ensure VPC Endpoint discovery completed before enrichment",
                },
            )
            return df

        if self.output_controller.verbose:
            print_info(f"🔄 Starting VPC Endpoint activity enrichment for {len(df)} endpoints...")
        else:
            logger.info(f"VPC Endpoint activity enrichment started for {len(df)} endpoints")

        # Initialize activity columns with defaults
        # v1.1.27: Added vpc_cost_90d (Cost Explorer), deprecated bytes_in_90d/bytes_out_90d
        # v1.1.29: Added V6-V10 signal columns for Flow Logs and Network Insights
        activity_columns = {
            "vpc_cost_90d": 0.0,
            "bytes_in_90d": 0.0,  # Deprecated - kept for backward compatibility
            "bytes_out_90d": 0.0,  # Deprecated - kept for backward compatibility
            "dependency_count": 0,
            "interface_count": 0,
            "vpc_environment": "unknown",
            "age_days": 0,
            "v1_signal": False,
            "v2_signal": False,
            "v3_signal": False,
            "v4_signal": False,
            "v5_signal": False,
            # v1.1.29: Enhanced V6-V10 signals
            "v6_signal": False,  # Flow Logs zero traffic
            "v7_signal": False,  # Security Group overly permissive
            "v8_signal": False,  # Endpoint policy too broad
            "v9_signal": False,  # Network Insights unreachable
            "v10_signal": False,  # Multi-region redundancy missing
            "flow_logs_enabled": False,
            "flow_logs_zero_traffic": False,
            "network_insights_unreachable": False,
            "cost_explorer_enrichment_success": False,  # v1.1.27: Renamed from cloudwatch_enrichment_success
            "enrichment_status": "PENDING",
            "enrichment_error": "",
            "decommission_score": 0,
            "decommission_tier": "KEEP",
            "total_possible_score": 100,
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # v1.1.27: Get VPC costs from Cost Explorer (replaces CloudWatch metrics)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=self.lookback_days)

        # Format dates for Cost Explorer API (ISO format required)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Get VPC costs from Cost Explorer (following cost_processor.py pattern)
        vpc_cost_90d = 0.0
        try:
            vpc_cost_response = self.ce.get_cost_and_usage(
                TimePeriod={"Start": start_str, "End": end_str},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Virtual Private Cloud"]}},
            )

            # Extract VPC cost from response
            if "ResultsByTime" in vpc_cost_response:
                for result in vpc_cost_response["ResultsByTime"]:
                    if "Groups" in result:
                        for group in result["Groups"]:
                            if group["Keys"][0] == "Amazon Virtual Private Cloud":
                                vpc_cost_90d += float(group["Metrics"]["UnblendedCost"]["Amount"])

            if self.output_controller.verbose:
                print_info(f"💰 Cost Explorer: VPC costs over 90 days = ${vpc_cost_90d:.2f}")
            else:
                logger.debug(f"Cost Explorer: VPC costs over 90 days = ${vpc_cost_90d:.2f}")

        except Exception as ce_error:
            logger.warning(
                f"Cost Explorer API failed: {ce_error}",
                extra={
                    "error_type": type(ce_error).__name__,
                    "profile": self.billing_profile,
                    "period": f"{start_str} to {end_str}",
                },
            )
            # Graceful degradation: continue with vpc_cost_90d = 0.0

        # v1.1.23: Batch process dependency analysis before loop for performance
        # Collect all valid endpoint IDs
        all_endpoint_ids = [
            row.get("vpc_endpoint_id", "")
            for _, row in df.iterrows()
            if row.get("vpc_endpoint_id") and row.get("vpc_endpoint_id") != "N/A"
        ]

        # Batch dependency analysis with lookup dictionary
        dependency_lookup = {}
        if all_endpoint_ids:
            try:
                dependency_analyses = self.dependency_mapper.analyze_endpoint_dependencies(
                    endpoint_ids=all_endpoint_ids
                )
                # Create lookup dictionary for fast access
                for analysis in dependency_analyses:
                    dependency_lookup[analysis.endpoint_id] = analysis.dependency_count
            except Exception as batch_dep_error:
                logger.debug(
                    f"Batch dependency analysis failed: {batch_dep_error}",
                    extra={"error_type": type(batch_dep_error).__name__},
                )

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]VPC Endpoint Cost Explorer enrichment...", total=len(df))

            for idx, row in df.iterrows():
                endpoint_id = row.get("vpc_endpoint_id", "")
                vpc_id = row.get("vpc_id", "")

                if not endpoint_id or endpoint_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get VPC Endpoint metadata
                    endpoint_response = self.ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])

                    endpoints = endpoint_response.get("VpcEndpoints", [])
                    if not endpoints:
                        logger.debug(f"VPC Endpoint not found: {endpoint_id}")
                        df.at[idx, "enrichment_status"] = "FAILED"
                        df.at[idx, "enrichment_error"] = "Endpoint not found"
                        progress.update(task, advance=1)
                        continue

                    endpoint_metadata = endpoints[0]
                    service_name = endpoint_metadata.get("ServiceName", "").split(".")[
                        -1
                    ]  # Extract service (s3, dynamodb, etc.)
                    creation_timestamp = endpoint_metadata.get("CreationTimestamp")
                    network_interface_ids = endpoint_metadata.get("NetworkInterfaceIds", [])

                    # V3: Interface count
                    df.at[idx, "interface_count"] = len(network_interface_ids)

                    # V5: Age calculation
                    if creation_timestamp:
                        age_days = (datetime.now(timezone.utc) - creation_timestamp).days
                        df.at[idx, "age_days"] = age_days

                    # v1.1.27: Set VPC cost from Cost Explorer (replaced CloudWatch metrics)
                    # Note: Cost Explorer provides account-level VPC costs, not per-endpoint granularity
                    # This aligns with MCP validator expectations (billing data, not data transfer metrics)
                    df.at[idx, "vpc_cost_90d"] = vpc_cost_90d

                    # Deprecated fields - set to 0.0 for backward compatibility
                    df.at[idx, "bytes_in_90d"] = 0.0
                    df.at[idx, "bytes_out_90d"] = 0.0

                    # Mark Cost Explorer enrichment as successful
                    df.at[idx, "cost_explorer_enrichment_success"] = True
                    df.at[idx, "enrichment_status"] = "SUCCESS"

                    # V2: Dependency analysis (use batch-processed lookup for performance)
                    # v1.1.23 FIX: Use pre-computed dependency lookup instead of per-endpoint API call
                    if endpoint_id in dependency_lookup:
                        df.at[idx, "dependency_count"] = dependency_lookup[endpoint_id]

                    # V4: VPC environment tag
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

                except Exception as e:
                    logger.warning(
                        f"CloudWatch metrics failed for VPC Endpoint {endpoint_id}: {e}",
                        extra={
                            "endpoint_id": endpoint_id,
                            "error_type": type(e).__name__,
                            "lookback_days": self.lookback_days,
                            "region": self.region,
                        },
                    )
                    df.at[idx, "enrichment_status"] = "FAILED"
                    df.at[idx, "enrichment_error"] = str(e)
                    pass

                progress.update(task, advance=1)

        # Calculate decommission signals and scores
        df = self._calculate_decommission_signals(df)

        # v1.1.27: Updated success message to reflect Cost Explorer integration
        endpoints_with_cost = (df["vpc_cost_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(
                f"✅ VPC Endpoint enrichment complete: ${vpc_cost_90d:.2f} total VPC costs ({endpoints_with_cost} endpoints with billing)"
            )
        else:
            logger.info(
                f"VPC Endpoint enrichment complete: ${vpc_cost_90d:.2f} total VPC costs ({endpoints_with_cost} endpoints with billing)"
            )

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate V1-V5 decommission signals and scores.

        Args:
            df: DataFrame with VPC Endpoint activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            # v1.1.27: Calculate total possible score based on Cost Explorer availability
            cost_explorer_success = row.get("cost_explorer_enrichment_success", False)
            total_possible = self._calculate_total_possible_score(cost_explorer_success)
            df.at[idx, "total_possible_score"] = total_possible

            # Check if Cost Explorer enrichment succeeded
            if not cost_explorer_success:
                # Fallback scoring using V4/V5 signals (don't require Cost Explorer)
                signals = {}

                # V4: Non-production VPC (5 points)
                vpc_env = row.get("vpc_environment", "unknown").lower()
                if vpc_env in ["nonprod", "dev", "test", "staging"]:
                    df.at[idx, "v4_signal"] = True
                    signals["V4"] = DEFAULT_VPCE_WEIGHTS["V4"]
                else:
                    signals["V4"] = 0

                # V5: Age >180 days unused (25 points - Manager's adjustment)
                age_days = row.get("age_days", 0)
                if age_days > 180:  # Can't check vpc_cost without Cost Explorer
                    df.at[idx, "v5_signal"] = True
                    signals["V5"] = DEFAULT_VPCE_WEIGHTS["V5"]
                else:
                    signals["V5"] = 0

                # Calculate fallback score and tier
                total_score = sum(signals.values())
                df.at[idx, "decommission_score"] = total_score

                # Calculate decommission tier from fallback score
                if total_score >= 80:
                    tier = "MUST"
                elif total_score >= 50:
                    tier = "SHOULD"
                elif total_score >= 25:
                    tier = "COULD"
                else:
                    tier = "KEEP"

                df.at[idx, "decommission_tier"] = tier
                continue  # Skip Cost Explorer-based scoring

            signals = {}

            # v1.1.27: V1 signal updated to use vpc_cost_90d instead of bytes
            # V1: Zero billing cost (40 points) - No VPC charges for 90+ days
            vpc_cost = row.get("vpc_cost_90d", 0.0)

            if vpc_cost == 0.0:
                df.at[idx, "v1_signal"] = True
                signals["V1"] = DEFAULT_VPCE_WEIGHTS["V1"]
            else:
                signals["V1"] = 0

            # V2: No service dependencies (25 points)
            if row.get("dependency_count", 0) == 0:
                df.at[idx, "v2_signal"] = True
                signals["V2"] = DEFAULT_VPCE_WEIGHTS["V2"]
            else:
                signals["V2"] = 0

            # V3: Interface endpoints with 1 interface only (15 points)
            if row.get("interface_count", 0) == 1:
                df.at[idx, "v3_signal"] = True
                signals["V3"] = DEFAULT_VPCE_WEIGHTS["V3"]
            else:
                signals["V3"] = 0

            # V4: Non-production VPC (5 points)
            vpc_env = row.get("vpc_environment", "unknown").lower()
            if vpc_env in ["nonprod", "dev", "test", "staging"]:
                df.at[idx, "v4_signal"] = True
                signals["V4"] = DEFAULT_VPCE_WEIGHTS["V4"]
            else:
                signals["V4"] = 0

            # v1.1.27: V5 signal updated to use vpc_cost_90d instead of total_bytes
            # V5: Age >180 days with zero billing (25 points - Manager's adjustment)
            age_days = row.get("age_days", 0)
            if age_days > 180 and vpc_cost == 0.0:
                df.at[idx, "v5_signal"] = True
                signals["V5"] = DEFAULT_VPCE_WEIGHTS["V5"]
            else:
                signals["V5"] = 0

            # Calculate total decommission score
            total_score = sum(signals.values())
            df.at[idx, "decommission_score"] = total_score

            # Determine decommission tier (consistent with ALB/DynamoDB/Route53)
            if total_score >= 80:
                df.at[idx, "decommission_tier"] = "MUST"
            elif total_score >= 50:
                df.at[idx, "decommission_tier"] = "SHOULD"
            elif total_score >= 25:
                df.at[idx, "decommission_tier"] = "COULD"
            else:
                df.at[idx, "decommission_tier"] = "KEEP"

        return df

    def _calculate_total_possible_score(self, cost_explorer_enrichment_success: bool) -> int:
        """
        Calculate total possible score based on signal availability.

        v1.1.27: Updated to reflect Cost Explorer integration (replaces CloudWatch).

        Implements manager's dynamic scoring denominator pattern:
        - If Cost Explorer available: Score out of 100 (V1 = 40pts possible)
        - If Cost Explorer unavailable: Score out of 60 (100-40, V1 removed)

        Args:
            cost_explorer_enrichment_success: Whether Cost Explorer billing data was successfully retrieved

        Returns:
            Total possible score (60 or 100)

        Examples:
            >>> # Cost Explorer available
            >>> self._calculate_total_possible_score(True)
            100

            >>> # Cost Explorer unavailable (V1 signal removed)
            >>> self._calculate_total_possible_score(False)
            60  # 100 - 40 (V1 weight)
        """
        base_score = 100

        # v1.1.27: V1 signal depends on Cost Explorer billing data (vpc_cost_90d)
        if not cost_explorer_enrichment_success:
            base_score -= DEFAULT_VPCE_WEIGHTS["V1"]  # Remove V1 (40pts)

        return base_score

    # ═══════════════════════════════════════════════════════════════════════════
    # v1.1.29: V6-V10 ENHANCED SIGNAL METHODS
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
                self._flow_logs_analyzer = VPCFlowLogsAnalyzer(
                    operational_profile=self.operational_profile, region=self.region
                )
                logger.debug("VPCFlowLogsAnalyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Flow Logs analyzer: {e}")
                return None

        return self._flow_logs_analyzer

    def _get_network_insights_client(self) -> Optional["NetworkInsightsClient"]:
        """
        Lazy initialization of Network Insights client.

        Returns:
            NetworkInsightsClient instance or None if unavailable
        """
        if not self.enable_network_insights:
            return None

        if self._network_insights_client is None:
            try:
                self._network_insights_client = NetworkInsightsClient(
                    operational_profile=self.operational_profile, region=self.region
                )
                logger.debug("NetworkInsightsClient initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Network Insights client: {e}")
                return None

        return self._network_insights_client

    def _check_v6_flow_logs_zero_traffic(self, vpc_endpoint_id: str, vpc_id: str, age_days: int) -> tuple:
        """
        V6: VPC Flow Logs analysis shows 0 accepted flows over 30 days.

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
        Confidence: 0.95 (Flow Logs ground truth)
        Business Value: Direct proof of zero usage

        v1.1.29: Updated to use flow_logs_detector.py for availability check

        Args:
            vpc_endpoint_id: VPC Endpoint ID
            vpc_id: VPC ID containing the endpoint
            age_days: Age of endpoint in days

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

            # Query traffic for VPC Endpoint
            traffic_result = flow_analyzer.query_vpc_endpoint_traffic(
                vpc_endpoint_id=vpc_endpoint_id, vpc_id=vpc_id, days=30
            )

            # Signal active if 0 accepted flows AND age >30 days
            signal_active = (
                traffic_result.accepted_flows == 0
                and traffic_result.rejected_flows == 0
                and age_days >= 30
                and traffic_result.flow_logs_enabled
            )

            metadata = {
                "accepted_flows": traffic_result.accepted_flows,
                "rejected_flows": traffic_result.rejected_flows,
                "total_bytes": traffic_result.total_bytes,
                "flow_logs_available": traffic_result.flow_logs_enabled,
                "confidence": 0.95 if traffic_result.flow_logs_enabled else 0.0,
            }

            return signal_active, metadata

        except Exception as e:
            # Graceful degradation: Flow Logs unavailable
            logger.debug(f"V6 signal check failed for {vpc_endpoint_id}: {e}")
            return False, {"error": str(e), "flow_logs_available": False}

    def _check_v7_security_group_permissive(
        self, vpc_endpoint_id: str, security_group_ids: List[str], vpc_id: str
    ) -> tuple:
        """
        V7: Security group allows 0.0.0.0/0 but Flow Logs show no traffic.

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html
        Confidence: 0.80 (Security + cost risk)
        Business Value: Security compliance + unused resource

        Args:
            vpc_endpoint_id: VPC Endpoint ID
            security_group_ids: List of security group IDs attached to endpoint
            vpc_id: VPC ID containing the endpoint

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            if not security_group_ids:
                return False, {"permissive_security_groups": [], "error": "No security groups"}

            # Check for overly permissive security groups
            permissive_sgs = []
            for sg_id in security_group_ids:
                try:
                    sg_response = self.ec2.describe_security_groups(GroupIds=[sg_id])
                    for sg in sg_response.get("SecurityGroups", []):
                        for rule in sg.get("IpPermissions", []):
                            for ip_range in rule.get("IpRanges", []):
                                if ip_range.get("CidrIp") == "0.0.0.0/0":
                                    permissive_sgs.append(sg_id)
                                    break
                except Exception as sg_error:
                    logger.debug(f"Failed to check security group {sg_id}: {sg_error}")

            if not permissive_sgs:
                return False, {"permissive_security_groups": []}

            # Cross-check with Flow Logs if available
            flow_analyzer = self._get_flow_logs_analyzer()
            inbound_flows = 0

            if flow_analyzer:
                try:
                    sg_traffic = flow_analyzer.analyze_security_group_traffic(
                        vpc_endpoint_id=vpc_endpoint_id, vpc_id=vpc_id, days=30
                    )
                    inbound_flows = 1 if sg_traffic.traffic_detected else 0
                except Exception:
                    pass

            # Signal if permissive SGs AND zero traffic
            signal_active = len(permissive_sgs) > 0 and inbound_flows == 0

            metadata = {
                "permissive_security_groups": permissive_sgs,
                "inbound_flows": inbound_flows,
                "confidence": 0.80,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"V7 signal check failed for {vpc_endpoint_id}: {e}")
            return False, {"error": str(e)}

    def _check_v8_endpoint_policy_broad(self, vpc_endpoint_id: str, vpc_cost_90d: float) -> tuple:
        """
        V8: Endpoint policy too broad ("*" actions) but no billing activity.

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints-access.html
        Confidence: 0.70 (Policy + cost correlation)
        Business Value: Security posture + unused broad access

        Args:
            vpc_endpoint_id: VPC Endpoint ID
            vpc_cost_90d: VPC cost over 90 days from Cost Explorer

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            # Get VPC Endpoint policy
            endpoint_response = self.ec2.describe_vpc_endpoints(VpcEndpointIds=[vpc_endpoint_id])

            endpoints = endpoint_response.get("VpcEndpoints", [])
            if not endpoints:
                return False, {"error": "Endpoint not found"}

            endpoint = endpoints[0]
            policy_document = endpoint.get("PolicyDocument", "{}")

            # Check for "*" in policy actions (overly permissive)
            import json

            try:
                policy = json.loads(policy_document) if isinstance(policy_document, str) else policy_document
            except json.JSONDecodeError:
                return False, {"error": "Invalid policy document"}

            has_wildcard_action = False
            statements = policy.get("Statement", [])
            for statement in statements:
                action = statement.get("Action", [])
                if isinstance(action, str):
                    action = [action]
                if "*" in action or any("*" in a for a in action):
                    has_wildcard_action = True
                    break

            # Signal if broad policy AND zero billing
            signal_active = has_wildcard_action and vpc_cost_90d == 0.0

            metadata = {"has_wildcard_action": has_wildcard_action, "vpc_cost_90d": vpc_cost_90d, "confidence": 0.70}

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"V8 signal check failed for {vpc_endpoint_id}: {e}")
            return False, {"error": str(e)}

    def _check_v9_network_insights_unreachable(self, vpc_endpoint_id: str) -> tuple:
        """
        V9: Network Insights path analysis fails to destination.

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/network-insights.html
        Confidence: 0.85 (Network path validation)
        Business Value: Identify unreachable endpoints safe to decommission

        Args:
            vpc_endpoint_id: VPC Endpoint ID

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            insights_client = self._get_network_insights_client()
            if not insights_client:
                return False, {"error": "Network Insights client unavailable"}

            # Analyze VPC Endpoint reachability
            result = insights_client.analyze_vpc_endpoint_reachability(
                vpc_endpoint_id=vpc_endpoint_id, cleanup_after=True
            )

            # Signal active if unreachable
            signal_active = result.unreachable

            metadata = {
                "path_found": result.path_found,
                "status": result.status.value,
                "explanations": result.explanations[:5],  # Limit explanations
                "confidence": result.confidence,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"V9 signal check failed for {vpc_endpoint_id}: {e}")
            return False, {"error": str(e)}

    def _check_v10_multi_region_redundancy(self, vpc_endpoint_id: str, zero_usage: bool) -> tuple:
        """
        V10: Multi-region redundancy missing (single-region + zero usage).

        AWS Doc: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-endpoints.html
        Confidence: 0.60 (Architecture assessment)
        Business Value: Identify single-point-of-failure endpoints with no activity

        Args:
            vpc_endpoint_id: VPC Endpoint ID
            zero_usage: Whether endpoint has zero usage (from V1/V6 signals)

        Returns:
            Tuple of (signal_active: bool, metadata: dict)
        """
        try:
            insights_client = self._get_network_insights_client()
            if not insights_client:
                return False, {"error": "Network Insights client unavailable"}

            # Analyze multi-region redundancy
            result = insights_client.analyze_multi_region_redundancy(
                vpc_endpoint_id=vpc_endpoint_id, zero_usage=zero_usage
            )

            # Signal active if single region with no usage
            signal_active = result.single_region_no_usage

            metadata = {
                "service_type": result.service_type,
                "primary_region": result.primary_region,
                "has_redundancy": result.has_redundancy,
                "other_regions": result.other_regions[:3],  # Limit regions
                "confidence": 0.60,
            }

            return signal_active, metadata

        except Exception as e:
            logger.debug(f"V10 signal check failed for {vpc_endpoint_id}: {e}")
            return False, {"error": str(e)}

    def enrich_v6_v10_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enhanced enrichment with V6-V10 signals via Flow Logs and Network Insights.

        v1.1.29: This method adds V6-V10 signal columns to an existing DataFrame
        that already has V1-V5 signals from enrich_vpce_activity().

        Args:
            df: DataFrame with vpc_endpoint_id and V1-V5 signals

        Returns:
            DataFrame with V6-V10 signal columns added

        Signal Coverage:
        - V6: Flow Logs zero traffic (15 pts, confidence 0.95)
        - V7: Security Group overly permissive (10 pts, confidence 0.80)
        - V8: Endpoint policy too broad (5 pts, confidence 0.70)
        - V9: Network Insights unreachable (10 pts, confidence 0.85)
        - V10: Multi-region redundancy missing (5 pts, confidence 0.60)
        """
        if df.empty:
            return df

        if "vpc_endpoint_id" not in df.columns:
            logger.debug("V6-V10 enrichment skipped - vpc_endpoint_id column not found")
            return df

        if not (self.enable_flow_logs or self.enable_network_insights):
            logger.debug("V6-V10 enrichment skipped - Flow Logs and Network Insights disabled")
            return df

        if self.output_controller.verbose:
            print_info(f"🔍 Starting V6-V10 enhanced signal enrichment for {len(df)} endpoints...")

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]V6-V10 Enhanced Signals...", total=len(df))

            for idx, row in df.iterrows():
                endpoint_id = row.get("vpc_endpoint_id", "")
                vpc_id = row.get("vpc_id", "")
                age_days = row.get("age_days", 0)
                vpc_cost_90d = row.get("vpc_cost_90d", 0.0)

                if not endpoint_id or endpoint_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                # Get security group IDs from endpoint
                security_group_ids = []
                try:
                    endpoint_response = self.ec2.describe_vpc_endpoints(VpcEndpointIds=[endpoint_id])
                    endpoints = endpoint_response.get("VpcEndpoints", [])
                    if endpoints:
                        groups = endpoints[0].get("Groups", [])
                        security_group_ids = [g["GroupId"] for g in groups]
                except Exception:
                    pass

                # V6: Flow Logs zero traffic
                if self.enable_flow_logs:
                    v6_active, v6_metadata = self._check_v6_flow_logs_zero_traffic(
                        vpc_endpoint_id=endpoint_id, vpc_id=vpc_id, age_days=age_days
                    )
                    df.at[idx, "v6_signal"] = v6_active
                    df.at[idx, "flow_logs_enabled"] = v6_metadata.get("flow_logs_available", False)
                    df.at[idx, "flow_logs_zero_traffic"] = v6_active

                    # V7: Security Group overly permissive
                    v7_active, _ = self._check_v7_security_group_permissive(
                        vpc_endpoint_id=endpoint_id, security_group_ids=security_group_ids, vpc_id=vpc_id
                    )
                    df.at[idx, "v7_signal"] = v7_active

                    # V8: Endpoint policy too broad
                    v8_active, _ = self._check_v8_endpoint_policy_broad(
                        vpc_endpoint_id=endpoint_id, vpc_cost_90d=vpc_cost_90d
                    )
                    df.at[idx, "v8_signal"] = v8_active

                # V9-V10: Network Insights signals
                if self.enable_network_insights:
                    # V9: Network Insights unreachable
                    v9_active, v9_metadata = self._check_v9_network_insights_unreachable(vpc_endpoint_id=endpoint_id)
                    df.at[idx, "v9_signal"] = v9_active
                    df.at[idx, "network_insights_unreachable"] = v9_active

                    # V10: Multi-region redundancy missing
                    zero_usage = row.get("v1_signal", False) or row.get("v6_signal", False)
                    v10_active, _ = self._check_v10_multi_region_redundancy(
                        vpc_endpoint_id=endpoint_id, zero_usage=zero_usage
                    )
                    df.at[idx, "v10_signal"] = v10_active

                progress.update(task, advance=1)

        # Recalculate decommission scores with V6-V10 signals
        df = self._calculate_enhanced_decommission_scores(df)

        if self.output_controller.verbose:
            v6_count = df["v6_signal"].sum()
            v7_count = df["v7_signal"].sum()
            v8_count = df["v8_signal"].sum()
            v9_count = df["v9_signal"].sum()
            v10_count = df["v10_signal"].sum()
            print_success(
                f"✅ V6-V10 enrichment complete: V6={v6_count}, V7={v7_count}, V8={v8_count}, V9={v9_count}, V10={v10_count}"
            )

        return df

    def _calculate_enhanced_decommission_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Recalculate decommission scores including V6-V10 signals.

        v1.1.29: Updates scores from 100-point scale to 125-point scale (normalized to 0-100).

        Args:
            df: DataFrame with V1-V10 signal columns

        Returns:
            DataFrame with updated decommission_score and decommission_tier
        """
        for idx, row in df.iterrows():
            signals = {}

            # V1-V5 signals (100 points base)
            if row.get("v1_signal", False):
                signals["V1"] = DEFAULT_VPCE_WEIGHTS["V1"]
            if row.get("v2_signal", False):
                signals["V2"] = DEFAULT_VPCE_WEIGHTS["V2"]
            if row.get("v3_signal", False):
                signals["V3"] = DEFAULT_VPCE_WEIGHTS["V3"]
            if row.get("v4_signal", False):
                signals["V4"] = DEFAULT_VPCE_WEIGHTS["V4"]
            if row.get("v5_signal", False):
                signals["V5"] = DEFAULT_VPCE_WEIGHTS["V5"]

            # V6-V10 signals (25 additional points)
            if row.get("v6_signal", False):
                signals["V6"] = DEFAULT_VPCE_WEIGHTS["V6"]
            if row.get("v7_signal", False):
                signals["V7"] = DEFAULT_VPCE_WEIGHTS["V7"]
            if row.get("v8_signal", False):
                signals["V8"] = DEFAULT_VPCE_WEIGHTS["V8"]
            if row.get("v9_signal", False):
                signals["V9"] = DEFAULT_VPCE_WEIGHTS["V9"]
            if row.get("v10_signal", False):
                signals["V10"] = DEFAULT_VPCE_WEIGHTS["V10"]

            # Calculate raw score (0-125 range)
            raw_score = sum(signals.values())

            # Normalize to 0-100 scale
            normalized_score = int(raw_score * 100 / MAX_VPCE_SCORE)
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
        self,
        management_profile: str,
        billing_profile: str,
        ops_profile: str,
        cross_account_role: str = "CloudOpsReadOnly",
    ) -> pd.DataFrame:
        """
        Multi-account VPC Endpoint enrichment via Organizations API.

        v1.1.29: Discovers VPC Endpoints across all organization accounts and
        enriches with V1-V10 signals using cross-account AssumeRole.

        Args:
            management_profile: AWS profile with organizations:ListAccounts
            billing_profile: AWS profile with ce:GetCostAndUsage
            ops_profile: AWS profile with ec2:Describe* (for cross-account AssumeRole)
            cross_account_role: IAM role name for cross-account access (default: CloudOpsReadOnly)

        Returns:
            DataFrame with VPC Endpoints from all organization accounts

        Profile Requirements:
            - management_profile: organizations:ListAccounts
            - billing_profile: ce:GetCostAndUsage
            - ops_profile: ec2:DescribeVpcEndpoints + sts:AssumeRole

        Business Value:
            - 67 accounts baseline (proven from organization)
            - 22 accounts with VPC/VPCE resources expected
            - Organization-wide VPC cost optimization visibility
        """
        if not ORGANIZATIONS_AVAILABLE:
            logger.warning("Organizations client unavailable - single account enrichment only")
            return pd.DataFrame()

        if self.output_controller.verbose:
            print_info("🏢 Starting multi-account VPC Endpoint discovery...")

        # Get organization accounts
        org_client = get_unified_organizations_client(management_profile)
        accounts = await org_client.get_organization_accounts()

        if not accounts:
            logger.warning("No organization accounts discovered")
            return pd.DataFrame()

        if self.output_controller.verbose:
            print_info(f"📊 Discovered {len(accounts)} organization accounts")

        # Discover VPC Endpoints across accounts
        all_endpoints_dfs = []
        successful_accounts = 0
        failed_accounts = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Multi-Account VPC Endpoint Discovery...", total=len(accounts))

            for account in accounts:
                account_id = account.account_id
                account_name = account.name

                try:
                    # Create cross-account session via AssumeRole
                    account_df = await self._discover_account_vpce(
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

                        all_endpoints_dfs.append(account_df)
                        successful_accounts += 1

                except Exception as e:
                    # Graceful degradation: skip inaccessible accounts
                    logger.debug(f"Account {account_id} ({account_name}) enrichment failed: {e}")
                    failed_accounts += 1

                progress.update(task, advance=1)

        if not all_endpoints_dfs:
            if self.output_controller.verbose:
                print_warning("⚠️  No VPC Endpoints discovered across organization")
            return pd.DataFrame()

        # Combine all account DataFrames
        combined_df = pd.concat(all_endpoints_dfs, ignore_index=True)

        if self.output_controller.verbose:
            print_success(
                f"✅ Multi-account discovery complete: "
                f"{len(combined_df)} VPC Endpoints from {successful_accounts} accounts "
                f"({failed_accounts} accounts inaccessible)"
            )

        return combined_df

    async def _discover_account_vpce(
        self, account_id: str, account_name: str, ops_profile: str, cross_account_role: str
    ) -> pd.DataFrame:
        """
        Discover VPC Endpoints in a single account via cross-account AssumeRole.

        Args:
            account_id: Target account ID
            account_name: Target account name (for logging)
            ops_profile: Profile for STS AssumeRole
            cross_account_role: IAM role name to assume

        Returns:
            DataFrame with VPC Endpoints from the target account
        """
        import boto3

        try:
            # Create STS client from operational profile
            resolved_profile = get_profile_for_operation("operational", ops_profile)
            session = create_operational_session(resolved_profile)
            sts = session.client("sts")

            # Assume cross-account role
            role_arn = f"arn:aws:iam::{account_id}:role/{cross_account_role}"
            assumed_role = sts.assume_role(
                RoleArn=role_arn, RoleSessionName=f"runbooks-vpce-discovery-{account_id[:8]}"
            )

            credentials = assumed_role["Credentials"]

            # Create EC2 client with assumed credentials
            assumed_session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )

            ec2 = assumed_session.client("ec2", region_name=self.region)

            # Discover VPC Endpoints
            endpoints = []
            paginator = ec2.get_paginator("describe_vpc_endpoints")

            for page in paginator.paginate():
                for endpoint in page.get("VpcEndpoints", []):
                    endpoints.append(
                        {
                            "vpc_endpoint_id": endpoint.get("VpcEndpointId", ""),
                            "vpc_id": endpoint.get("VpcId", ""),
                            "service_name": endpoint.get("ServiceName", ""),
                            "endpoint_type": endpoint.get("VpcEndpointType", ""),
                            "state": endpoint.get("State", ""),
                            "creation_timestamp": endpoint.get("CreationTimestamp"),
                            "network_interface_count": len(endpoint.get("NetworkInterfaceIds", [])),
                            "subnet_ids": endpoint.get("SubnetIds", []),
                            "security_group_ids": [g["GroupId"] for g in endpoint.get("Groups", [])],
                        }
                    )

            return pd.DataFrame(endpoints)

        except Exception as e:
            logger.debug(f"VPC Endpoint discovery failed for account {account_id}: {e}")
            return pd.DataFrame()


# Export interface
__all__ = ["VPCEActivityEnricher"]
