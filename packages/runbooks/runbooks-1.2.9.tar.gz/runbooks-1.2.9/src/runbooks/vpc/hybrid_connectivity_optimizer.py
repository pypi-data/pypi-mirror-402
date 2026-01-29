#!/usr/bin/env python3
"""
Hybrid Connectivity Optimization Module

This module optimizes VPN and Direct Connect configurations for cost efficiency
while maintaining hybrid cloud connectivity performance and reliability.

Part of CloudOps-Runbooks VPC optimization framework supporting:
- VPN connection consolidation based on usage analysis
- Direct Connect bandwidth rightsizing
- Utilization analysis via CloudWatch metrics
- Cost reduction tracking based on percentage targets (configurable via .env)

Author: Runbooks Team
Version: 1.1.x
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    Console,
    create_panel,
    create_progress_bar,
    create_table,
    format_cost,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from runbooks.vpc.config import get_pricing_config


class HybridConnectivityOptimizer:
    """
    Optimize VPN and Direct Connect configurations for cost efficiency.

    This class provides systematic hybrid connectivity optimization including:
    - VPN connection usage analysis
    - Direct Connect bandwidth utilization monitoring
    - Consolidation candidate identification
    - Cost savings calculation and validation

    Attributes:
        region: AWS region for operations
        profile: AWS profile name for authentication
        console: Rich console for beautiful CLI output
    """

    def __init__(
        self, region: str = "ap-southeast-2", profile: Optional[str] = None, console: Optional[Console] = None
    ):
        """
        Initialize hybrid connectivity optimizer.

        Args:
            region: AWS region (default: ap-southeast-2)
            profile: AWS profile name for authentication
            console: Rich console for output (auto-created if not provided)
        """
        self.region = region
        self.profile = profile
        self.console = console or Console()

        # Initialize boto3 session (with profile only if explicitly provided)
        # This allows tests to work with @mock_aws without AWS profile configuration
        if self.profile and self.profile != "default":
            session = boto3.Session(profile_name=self.profile)
        else:
            session = boto3.Session()  # Use default credentials chain

        self.ec2 = session.client("ec2", region_name=self.region)
        self.cloudwatch = session.client("cloudwatch", region_name=self.region)
        self.directconnect = session.client("directconnect", region_name=self.region)

        # Initialize pricing config for dynamic cost calculations (NO hardcoding)
        self.pricing_config = get_pricing_config(profile=self.profile, region=self.region)

    def analyze_vpn_usage(self, days: int = 30, low_usage_threshold_gb: float = 100.0) -> List[Dict[str, Any]]:
        """
        Analyze VPN connection usage for consolidation opportunities.

        Analyzes VPN connections to identify:
        - Low-usage connections (< threshold GB/month)
        - Redundant backup connections
        - Inactive or down connections
        - Data transfer patterns

        Args:
            days: Number of days to analyze (default: 30)
            low_usage_threshold_gb: GB threshold for low usage classification

        Returns:
            List of VPN analysis dictionaries with consolidation recommendations

        Example:
            >>> optimizer = HybridConnectivityOptimizer(profile="prod")
            >>> vpn_analysis = optimizer.analyze_vpn_usage(days=30)
            >>> candidates = [v for v in vpn_analysis if v['consolidation_candidate']]
            >>> print(f"Found {len(candidates)} consolidation candidates")
        """
        print_header("VPN Connection Usage Analysis", version="1.1.x")
        print_info(f"Analyzing {days} days of VPN usage data")
        print_info(f"Low usage threshold: {low_usage_threshold_gb} GB/month")

        try:
            vpn_connections = self.ec2.describe_vpn_connections()["VpnConnections"]
            usage_analysis = []

            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Analyzing VPN connections...", total=len(vpn_connections))

                for vpn in vpn_connections:
                    vpn_id = vpn["VpnConnectionId"]

                    # Get VPN name from tags
                    vpn_name = "Unnamed"
                    for tag in vpn.get("Tags", []):
                        if tag["Key"] == "Name":
                            vpn_name = tag["Value"]
                            break

                    # Get tunnel status
                    tunnel_states = [t.get("Status", "UNKNOWN") for t in vpn.get("VgwTelemetry", [])]
                    tunnels_up = tunnel_states.count("UP")

                    # Get data transfer metrics from CloudWatch
                    try:
                        bytes_out = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/VPN",
                            MetricName="TunnelDataOut",
                            Dimensions=[{"Name": "VpnId", "Value": vpn_id}],
                            StartTime=datetime.now() - timedelta(days=days),
                            EndTime=datetime.now(),
                            Period=86400 * days,  # Full period
                            Statistics=["Sum"],
                        )

                        # Calculate monthly GB
                        total_bytes = sum(d["Sum"] for d in bytes_out["Datapoints"]) if bytes_out["Datapoints"] else 0
                        monthly_gb = total_bytes / (1024**3)

                    except ClientError as e:
                        print_warning(f"Failed to get metrics for {vpn_id}: {e}")
                        monthly_gb = 0

                    # Determine if consolidation candidate
                    is_candidate = monthly_gb < low_usage_threshold_gb or tunnels_up == 0

                    # Get dynamic VPN cost from pricing config (NO hardcoded $36)
                    vpn_monthly_cost = self.pricing_config.get_vpn_connection_monthly_cost(self.region)

                    usage_analysis.append(
                        {
                            "vpn_id": vpn_id,
                            "name": vpn_name,
                            "state": vpn["State"],
                            "type": vpn.get("Type", "ipsec.1"),
                            "tunnel_up_count": tunnels_up,
                            "total_tunnels": len(tunnel_states),
                            "monthly_gb": monthly_gb,
                            "monthly_cost": vpn_monthly_cost,
                            "consolidation_candidate": is_candidate,
                            "reason": self._get_consolidation_reason(monthly_gb, tunnels_up, low_usage_threshold_gb),
                        }
                    )

                    progress.update(task, advance=1)

            # Display analysis results
            self._display_vpn_analysis_table(usage_analysis)

            # Calculate summary (use dynamic pricing)
            total_vpns = len(usage_analysis)
            candidates = sum(1 for v in usage_analysis if v["consolidation_candidate"])
            vpn_monthly_cost = self.pricing_config.get_vpn_connection_monthly_cost(self.region)
            potential_savings = candidates * vpn_monthly_cost

            print_success(f"Analysis complete: {candidates}/{total_vpns} VPNs identified for consolidation")
            print_info(f"Potential monthly savings: ${potential_savings:.2f}")

            return usage_analysis

        except ClientError as e:
            print_error("Failed to analyze VPN connections", e)
            raise

    def plan_dx_optimization(self, utilization_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Plan Direct Connect bandwidth optimization based on utilization.

        Analyzes Direct Connect virtual interfaces to identify:
        - Over-provisioned bandwidth (utilization < threshold)
        - Rightsizing opportunities
        - Cost reduction potential

        Args:
            utilization_threshold: Peak utilization threshold (default: 0.5 = 50%)

        Returns:
            List of Direct Connect optimization recommendations

        Example:
            >>> optimizer = HybridConnectivityOptimizer()
            >>> dx_plan = optimizer.plan_dx_optimization(utilization_threshold=0.5)
            >>> print(f"Rightsizing recommendations: {len(dx_plan)}")
        """
        print_header("Direct Connect Optimization Analysis", version="1.1.x")
        print_info(f"Utilization threshold: {utilization_threshold * 100:.0f}%")

        try:
            vifs = self.directconnect.describe_virtual_interfaces()["virtualInterfaces"]
            optimization_plan = []

            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Analyzing Direct Connect VIFs...", total=len(vifs))

                for vif in vifs:
                    vif_id = vif["virtualInterfaceId"]
                    connection_id = vif.get("connectionId")

                    if not connection_id:
                        progress.update(task, advance=1)
                        continue

                    # Get bandwidth utilization from CloudWatch
                    try:
                        utilization = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/DX",
                            MetricName="ConnectionBpsEgress",
                            Dimensions=[{"Name": "ConnectionId", "Value": connection_id}],
                            StartTime=datetime.now() - timedelta(days=30),
                            EndTime=datetime.now(),
                            Period=3600,  # Hourly
                            Statistics=["Maximum"],
                        )

                        # Calculate peak utilization
                        max_bps = max((d["Maximum"] for d in utilization["Datapoints"]), default=0)
                        max_mbps = max_bps / (1024 * 1024)

                    except ClientError as e:
                        print_warning(f"Failed to get metrics for {vif_id}: {e}")
                        max_mbps = 0

                    # Parse current bandwidth
                    bandwidth_str = vif.get("bandwidth", "1Gbps")
                    current_mbps = self._parse_bandwidth(bandwidth_str)

                    # Calculate utilization percentage
                    peak_utilization = (max_mbps / current_mbps) if current_mbps > 0 else 0

                    # Determine optimization opportunity
                    if peak_utilization < utilization_threshold and current_mbps >= 1000:
                        recommended_mbps = 500 if max_mbps < 500 else 1000
                        monthly_savings = 400.0 if current_mbps == 1000 and recommended_mbps == 500 else 0

                        optimization_plan.append(
                            {
                                "vif_id": vif_id,
                                "location": vif.get("location", "Unknown"),
                                "current_bandwidth_mbps": current_mbps,
                                "peak_utilization_mbps": max_mbps,
                                "peak_utilization_pct": peak_utilization * 100,
                                "recommended_bandwidth_mbps": recommended_mbps,
                                "monthly_savings": monthly_savings,
                                "annual_savings": monthly_savings * 12,
                            }
                        )

                    progress.update(task, advance=1)

            # Display optimization plan
            self._display_dx_optimization_table(optimization_plan)

            total_savings = sum(opt["monthly_savings"] for opt in optimization_plan)
            print_success(f"Optimization analysis complete: {len(optimization_plan)} recommendations")
            print_info(f"Potential monthly savings: ${total_savings:.2f}")

            return optimization_plan

        except ClientError as e:
            print_error("Failed to analyze Direct Connect", e)
            raise

    def analyze_nat_gateway_consolidation(
        self,
        target_reduction_percentage: float = 0.67,
    ) -> Dict[str, Any]:
        """
        Analyze NAT Gateway consolidation opportunities via centralized egress VPCs.

        Identifies NAT Gateways that can be consolidated into centralized
        egress VPCs using Transit Gateway routing.

        Args:
            target_reduction_percentage: Target reduction (default: 0.67 = 67%)

        Returns:
            NAT Gateway consolidation analysis with recommendations
        """
        print_header("NAT Gateway Consolidation Analysis", version="1.1.x")
        print_info(f"Target reduction: {target_reduction_percentage * 100:.0f}%")

        try:
            nat_gateways = self.ec2.describe_nat_gateways()["NatGateways"]
            current_count = len(nat_gateways)

            # Calculate target count based on reduction percentage
            target_count = int(current_count * (1 - target_reduction_percentage))

            # Get dynamic NAT Gateway cost from pricing config
            nat_monthly_cost = self.pricing_config.get_nat_gateway_monthly_cost(self.region)

            consolidation_analysis = {
                "region": self.region,
                "current_nat_count": current_count,
                "target_nat_count": target_count,
                "reduction_count": current_count - target_count,
                "reduction_percentage": target_reduction_percentage * 100,
                "nat_gateways": [],
                "consolidation_strategy": "centralized_egress_vpc",
            }

            # Analyze each NAT Gateway
            for nat in nat_gateways:
                nat_id = nat["NatGatewayId"]
                vpc_id = nat["VpcId"]
                state = nat["State"]

                consolidation_analysis["nat_gateways"].append(
                    {
                        "nat_gateway_id": nat_id,
                        "vpc_id": vpc_id,
                        "subnet_id": nat["SubnetId"],
                        "state": state,
                        "monthly_cost": nat_monthly_cost,
                    }
                )

            # Calculate savings
            monthly_savings = (current_count - target_count) * nat_monthly_cost
            annual_savings = monthly_savings * 12

            consolidation_analysis["cost_savings"] = {
                "current_monthly_cost": current_count * nat_monthly_cost,
                "target_monthly_cost": target_count * nat_monthly_cost,
                "monthly_savings": monthly_savings,
                "annual_savings": annual_savings,
            }

            print_success(f"Analysis complete: {current_count} → {target_count} NAT Gateways")
            print_info(f"Potential monthly savings: ${monthly_savings:.2f}")

            return consolidation_analysis

        except ClientError as e:
            print_error("Failed to analyze NAT Gateway consolidation", e)
            raise

    def plan_centralized_nat_migration(
        self,
        egress_vpc_id: str,
        primary_nat_id: str,
        secondary_nat_id: str,
    ) -> Dict[str, Any]:
        """
        Plan migration to centralized NAT Gateway architecture.

        Creates migration plan for consolidating NAT Gateways into
        a centralized egress VPC with Transit Gateway routing.

        Args:
            egress_vpc_id: Centralized egress VPC ID
            primary_nat_id: Primary centralized NAT Gateway ID
            secondary_nat_id: Secondary (HA) NAT Gateway ID

        Returns:
            Migration plan dictionary
        """
        print_header("Centralized NAT Migration Planning", version="1.1.x")
        print_info(f"Egress VPC: {egress_vpc_id}")
        print_info(f"Primary NAT: {primary_nat_id}")
        print_info(f"Secondary NAT: {secondary_nat_id}")

        # Get all VPCs that need migration
        vpcs = self.ec2.describe_vpcs()["Vpcs"]

        migration_plan = {
            "egress_vpc_id": egress_vpc_id,
            "primary_nat_id": primary_nat_id,
            "secondary_nat_id": secondary_nat_id,
            "region": self.region,
            "timestamp": datetime.now().isoformat(),
            "vpc_migrations": [],
        }

        for vpc in vpcs:
            vpc_id = vpc["VpcId"]

            # Skip egress VPC itself
            if vpc_id == egress_vpc_id:
                continue

            migration_plan["vpc_migrations"].append(
                {
                    "vpc_id": vpc_id,
                    "action": "update_route_tables",
                    "target": "egress_vpc_via_tgw",
                    "route": "0.0.0.0/0 → Transit Gateway",
                }
            )

        print_success(f"Migration plan created for {len(migration_plan['vpc_migrations'])} VPCs")

        return migration_plan

    def calculate_vpn_savings(self, current_vpn_count: int, target_vpn_count: int) -> Dict[str, float]:
        """
        Calculate cost savings from VPN consolidation.

        Uses dynamic pricing from AWS Pricing API (NO hardcoded costs).

        Args:
            current_vpn_count: Current number of VPN connections
            target_vpn_count: Target number after consolidation

        Returns:
            Dictionary with cost savings breakdown
        """
        # Get dynamic VPN cost from pricing config (NO hardcoded $36)
        vpn_monthly_cost = self.pricing_config.get_vpn_connection_monthly_cost(self.region)

        current_monthly = current_vpn_count * vpn_monthly_cost
        target_monthly = target_vpn_count * vpn_monthly_cost

        monthly_savings = current_monthly - target_monthly
        annual_savings = monthly_savings * 12

        return {
            "current_vpn_count": current_vpn_count,
            "target_vpn_count": target_vpn_count,
            "vpns_consolidated": current_vpn_count - target_vpn_count,
            "current_monthly_cost": current_monthly,
            "target_monthly_cost": target_monthly,
            "monthly_savings": monthly_savings,
            "annual_savings": annual_savings,
            "reduction_percentage": (monthly_savings / current_monthly * 100) if current_monthly > 0 else 0,
            "vpn_monthly_cost": vpn_monthly_cost,
        }

    def _parse_bandwidth(self, bandwidth_str: str) -> int:
        """Parse bandwidth string to Mbps integer."""
        if "Gbps" in bandwidth_str:
            return int(bandwidth_str.replace("Gbps", "").strip()) * 1000
        elif "Mbps" in bandwidth_str:
            return int(bandwidth_str.replace("Mbps", "").strip())
        return 0

    def _get_consolidation_reason(self, monthly_gb: float, tunnels_up: int, threshold: float) -> str:
        """Determine consolidation reason."""
        if tunnels_up == 0:
            return "No tunnels UP - inactive connection"
        elif monthly_gb < threshold:
            return f"Low usage: {monthly_gb:.1f} GB/month (< {threshold} GB threshold)"
        else:
            return "Active - no consolidation recommended"

    def _display_vpn_analysis_table(self, analysis: List[Dict[str, Any]]) -> None:
        """Display VPN analysis in Rich table format."""
        table = create_table(title="VPN Connection Analysis", box_style="ROUNDED")
        table.add_column("VPN Name", style="cyan")
        table.add_column("VPN ID", style="bright_blue")
        table.add_column("State", style="bright_green")
        table.add_column("Tunnels UP", style="bright_yellow", justify="right")
        table.add_column("Monthly GB", style="bright_cyan", justify="right")
        table.add_column("Candidate", style="bright_red")

        for vpn in analysis:
            candidate_mark = "✅" if vpn["consolidation_candidate"] else "❌"

            table.add_row(
                vpn["name"],
                vpn["vpn_id"],
                vpn["state"],
                f"{vpn['tunnel_up_count']}/{vpn['total_tunnels']}",
                f"{vpn['monthly_gb']:.1f}",
                candidate_mark,
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def _display_dx_optimization_table(self, plan: List[Dict[str, Any]]) -> None:
        """Display Direct Connect optimization in Rich table format."""
        table = create_table(title="Direct Connect Optimization Plan", box_style="ROUNDED")
        table.add_column("VIF ID", style="cyan")
        table.add_column("Location", style="bright_blue")
        table.add_column("Current (Mbps)", style="bright_yellow", justify="right")
        table.add_column("Peak Util %", style="bright_cyan", justify="right")
        table.add_column("Recommended (Mbps)", style="bright_green", justify="right")
        table.add_column("Monthly Savings", style="bright_red", justify="right")

        for opt in plan:
            table.add_row(
                opt["vif_id"],
                opt["location"],
                f"{opt['current_bandwidth_mbps']:.0f}",
                f"{opt['peak_utilization_pct']:.1f}%",
                f"{opt['recommended_bandwidth_mbps']:.0f}",
                f"${opt['monthly_savings']:.2f}",
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")


# CLI Integration Example
if __name__ == "__main__":
    import sys

    # Simple CLI for standalone execution
    region = sys.argv[1] if len(sys.argv) > 1 else "ap-southeast-2"
    profile = sys.argv[2] if len(sys.argv) > 2 else "default"

    optimizer = HybridConnectivityOptimizer(region=region, profile=profile)

    # Analyze VPN connections
    print("\n🔍 Analyzing VPN connections...")
    vpn_analysis = optimizer.analyze_vpn_usage()

    consolidation_candidates = [v for v in vpn_analysis if v["consolidation_candidate"]]
    vpn_savings = optimizer.calculate_vpn_savings(
        current_vpn_count=len(vpn_analysis), target_vpn_count=len(vpn_analysis) - len(consolidation_candidates)
    )

    # Analyze Direct Connect
    print("\n🔍 Analyzing Direct Connect...")
    dx_optimization = optimizer.plan_dx_optimization()

    dx_savings = sum(opt["monthly_savings"] for opt in dx_optimization)

    # Summary
    print(f"\n💰 Hybrid Connectivity Optimization Summary:")
    print(f"VPN Consolidation Potential: ${vpn_savings['monthly_savings']:.2f}/month")
    print(f"Direct Connect Optimization: ${dx_savings:.2f}/month")
    print(f"Total Monthly Savings: ${vpn_savings['monthly_savings'] + dx_savings:.2f}")
    print(f"\n✅ Hybrid connectivity analysis complete!")
