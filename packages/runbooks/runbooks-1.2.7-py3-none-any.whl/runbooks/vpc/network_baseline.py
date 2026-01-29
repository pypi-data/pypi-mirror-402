#!/usr/bin/env python3
"""
Network Baseline Metrics Collection Module

This module collects comprehensive baseline metrics for AWS network infrastructure
across multiple regions, including NAT Gateways, Transit Gateways, VPC Endpoints,
VPN Connections, and data transfer metrics.

Part of CloudOps-Runbooks VPC optimization framework supporting:
- Multi-region baseline collection
- CloudWatch metrics integration
- JSON export with SHA256 checksums
- Rich CLI integration for beautiful terminal output

Author: Runbooks Team
Version: 1.1.x
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    Console,
    create_progress_bar,
    create_table,
    format_cost,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from runbooks.vpc.config import get_vpc_config, get_pricing_config


class NetworkBaselineCollector:
    """
    Collect comprehensive network baseline metrics across AWS regions.

    This class provides systematic collection of network infrastructure metrics
    to establish baseline for optimization initiatives. Supports multi-region
    data collection with CloudWatch integration.

    Attributes:
        account_id: AWS account ID for baseline collection
        regions: List of AWS regions to collect metrics from
        profile: AWS profile name for session management
        console: Rich console for beautiful CLI output
        metrics: Dictionary storing collected metrics by region
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        regions: Optional[List[str]] = None,
        profile: Optional[str] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize network baseline collector.

        Args:
            account_id: AWS account ID (auto-discovered from STS if not provided)
            regions: List of regions (from config if not provided)
            profile: AWS profile name (from config if not provided)
            console: Rich console for output (auto-created if not provided)
        """
        # Load configuration (ZERO hardcoded values)
        config = get_vpc_config()

        self.profile = profile or config.get_aws_session_profile()
        self.regions = regions or config.get_regions_for_discovery()
        self.console = console or Console()
        self.metrics: Dict[str, Any] = {}

        # Initialize boto3 session (with profile only if explicitly provided)
        # This allows tests to work with @mock_aws without AWS profile configuration
        if self.profile and self.profile != "default":
            self.session = boto3.Session(profile_name=self.profile)
        else:
            self.session = boto3.Session()  # Use default credentials chain

        # Auto-discover account ID if not provided (NO hardcoding)
        if account_id is None:
            sts = self.session.client("sts")
            self.account_id = sts.get_caller_identity()["Account"]
        else:
            self.account_id = account_id

        # Initialize pricing config for dynamic cost calculations
        self.pricing_config = get_pricing_config(profile=self.profile)

    def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collect baseline metrics across all configured regions.

        Collects comprehensive network infrastructure metrics including:
        - NAT Gateway utilization and cost metrics
        - Transit Gateway attachment and routing metrics
        - VPC Endpoint configuration and usage
        - VPN Connection status and throughput
        - Data transfer volumes and patterns

        Returns:
            Dictionary containing all collected metrics organized by region

        Example:
            >>> collector = NetworkBaselineCollector(profile="prod")
            >>> baseline = collector.collect_all_metrics()
            >>> print(f"Collected metrics for {len(baseline)} regions")
        """
        print_header("Network Baseline Collection", version="1.1.x")
        self.console.print(f"\n[cyan]Account:[/cyan] {self.account_id}")
        self.console.print(f"[cyan]Regions:[/cyan] {', '.join(self.regions)}")
        self.console.print(f"[cyan]Profile:[/cyan] {self.profile}\n")

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Collecting metrics...", total=len(self.regions))

            for region in self.regions:
                print_info(f"Collecting metrics for {region}")

                try:
                    self.metrics[region] = {
                        "timestamp": datetime.now().isoformat(),
                        "nat_gateways": self.collect_nat_metrics(region),
                        "transit_gateways": self.collect_tgw_metrics(region),
                        "vpc_endpoints": self.collect_endpoint_metrics(region),
                        "vpn_connections": self.collect_vpn_metrics(region),
                        "data_transfer": self.collect_transfer_metrics(region),
                    }

                    print_success(f"Completed {region}")

                except Exception as e:
                    print_error(f"Failed to collect metrics for {region}", e)
                    self.metrics[region] = {"error": str(e), "timestamp": datetime.now().isoformat()}

                progress.update(task, advance=1)

        return self.metrics

    def collect_nat_metrics(self, region: str) -> List[Dict[str, Any]]:
        """
        Collect NAT Gateway metrics for a specific region.

        Retrieves NAT Gateway configuration and CloudWatch metrics including:
        - BytesOutToDestination (weekly sum and daily average)
        - Active connection count
        - Packet drop count
        - Current state and configuration

        Args:
            region: AWS region name

        Returns:
            List of dictionaries containing NAT Gateway metrics
        """
        try:
            ec2 = self.session.client("ec2", region_name=region)
            cw = self.session.client("cloudwatch", region_name=region)

            nat_gateways = ec2.describe_nat_gateways()["NatGateways"]
            metrics = []

            for nat in nat_gateways:
                nat_id = nat["NatGatewayId"]

                # Get CloudWatch metrics for last 7 days
                bytes_out = cw.get_metric_statistics(
                    Namespace="AWS/NATGateway",
                    MetricName="BytesOutToDestination",
                    Dimensions=[{"Name": "NatGatewayId", "Value": nat_id}],
                    StartTime=datetime.now() - timedelta(days=7),
                    EndTime=datetime.now(),
                    Period=86400,  # Daily
                    Statistics=["Sum", "Average"],
                )

                # Calculate usage metrics
                bytes_out_weekly = sum(d["Sum"] for d in bytes_out["Datapoints"]) if bytes_out["Datapoints"] else 0
                average_daily = sum(d["Average"] for d in bytes_out["Datapoints"]) / 7 if bytes_out["Datapoints"] else 0

                # Calculate monthly cost from pricing config (NO hardcoding)
                monthly_cost = self.pricing_config.get_nat_gateway_monthly_cost(region)

                metrics.append(
                    {
                        "nat_gateway_id": nat_id,
                        "state": nat["State"],
                        "vpc_id": nat["VpcId"],
                        "subnet_id": nat["SubnetId"],
                        "bytes_out_weekly": bytes_out_weekly,
                        "average_daily_bytes": average_daily,
                        "monthly_cost_estimate": monthly_cost,
                    }
                )

            return metrics

        except ClientError as e:
            print_warning(f"NAT Gateway collection failed for {region}: {e}")
            return []

    def collect_tgw_metrics(self, region: str) -> List[Dict[str, Any]]:
        """
        Collect Transit Gateway metrics for a specific region.

        Args:
            region: AWS region name

        Returns:
            List of dictionaries containing Transit Gateway metrics
        """
        try:
            ec2 = self.session.client("ec2", region_name=region)

            tgws = ec2.describe_transit_gateways()["TransitGateways"]
            metrics = []

            for tgw in tgws:
                tgw_id = tgw["TransitGatewayId"]

                # Get attachments
                attachments = ec2.describe_transit_gateway_attachments(
                    Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]
                )["TransitGatewayAttachments"]

                # Calculate cost from pricing config (NO hardcoding)
                attachment_cost = self.pricing_config.get_transit_gateway_attachment_cost(region)
                monthly_cost = (attachment_cost / 30) * len(attachments)  # Attachment cost is monthly

                metrics.append(
                    {
                        "transit_gateway_id": tgw_id,
                        "state": tgw["State"],
                        "attachment_count": len(attachments),
                        "monthly_cost_estimate": monthly_cost,
                    }
                )

            return metrics

        except ClientError as e:
            print_warning(f"Transit Gateway collection failed for {region}: {e}")
            return []

    def collect_endpoint_metrics(self, region: str) -> List[Dict[str, Any]]:
        """
        Collect VPC Endpoint metrics for a specific region.

        Args:
            region: AWS region name

        Returns:
            List of dictionaries containing VPC Endpoint metrics
        """
        try:
            ec2 = self.session.client("ec2", region_name=region)

            endpoints = ec2.describe_vpc_endpoints()["VpcEndpoints"]
            metrics = []

            for endpoint in endpoints:
                endpoint_type = endpoint["VpcEndpointType"]

                # Calculate cost from pricing config (NO hardcoding)
                # Interface endpoints have cost, Gateway endpoints are free
                if endpoint_type == "Interface":
                    monthly_cost = self.pricing_config.get_vpc_endpoint_interface_monthly_cost(region)
                else:
                    monthly_cost = 0.0

                metrics.append(
                    {
                        "vpc_endpoint_id": endpoint["VpcEndpointId"],
                        "service_name": endpoint["ServiceName"],
                        "vpc_id": endpoint["VpcId"],
                        "state": endpoint["State"],
                        "endpoint_type": endpoint_type,
                        "monthly_cost_estimate": monthly_cost,
                    }
                )

            return metrics

        except ClientError as e:
            print_warning(f"VPC Endpoint collection failed for {region}: {e}")
            return []

    def collect_vpn_metrics(self, region: str) -> List[Dict[str, Any]]:
        """
        Collect VPN Connection metrics for a specific region.

        Args:
            region: AWS region name

        Returns:
            List of dictionaries containing VPN metrics
        """
        try:
            ec2 = self.session.client("ec2", region_name=region)

            vpn_connections = ec2.describe_vpn_connections()["VpnConnections"]
            metrics = []

            for vpn in vpn_connections:
                # Get tunnel status
                tunnel_statuses = [t.get("Status", "UNKNOWN") for t in vpn.get("VgwTelemetry", [])]

                # Calculate cost from pricing config (NO hardcoding)
                monthly_cost = self.pricing_config.get_vpn_connection_monthly_cost(region)

                metrics.append(
                    {
                        "vpn_connection_id": vpn["VpnConnectionId"],
                        "state": vpn["State"],
                        "type": vpn["Type"],
                        "tunnel_up_count": tunnel_statuses.count("UP"),
                        "monthly_cost_estimate": monthly_cost,
                    }
                )

            return metrics

        except ClientError as e:
            print_warning(f"VPN Connection collection failed for {region}: {e}")
            return []

    def collect_transfer_metrics(self, region: str) -> Dict[str, Any]:
        """
        Collect data transfer metrics for a specific region.

        Args:
            region: AWS region name

        Returns:
            Dictionary containing data transfer metrics
        """
        # Placeholder for data transfer metrics
        # Would integrate with CloudWatch for actual data transfer tracking
        return {
            "cross_az_transfer_gb": 0.0,
            "cross_region_transfer_gb": 0.0,
            "internet_transfer_gb": 0.0,
            "estimated_monthly_cost": 0.0,
        }

    def generate_baseline_report(self, output_file: str = "network-baseline-report.json") -> Dict[str, Any]:
        """
        Generate comprehensive baseline report with SHA256 checksum.

        Creates a JSON report containing all collected metrics with:
        - Complete metric data by region
        - Summary statistics
        - Cost estimates
        - SHA256 checksum for verification

        Args:
            output_file: Path to output JSON file

        Returns:
            Complete report dictionary

        Example:
            >>> collector = NetworkBaselineCollector()
            >>> collector.collect_all_metrics()
            >>> report = collector.generate_baseline_report("baseline.json")
            >>> print(f"Report checksum: {report['checksum']}")
        """
        # Calculate summary statistics
        total_nat = sum(len(m.get("nat_gateways", [])) for m in self.metrics.values() if isinstance(m, dict))
        total_tgw = sum(len(m.get("transit_gateways", [])) for m in self.metrics.values() if isinstance(m, dict))
        total_endpoints = sum(len(m.get("vpc_endpoints", [])) for m in self.metrics.values() if isinstance(m, dict))
        total_vpn = sum(len(m.get("vpn_connections", [])) for m in self.metrics.values() if isinstance(m, dict))

        report = {
            "account_id": self.account_id,
            "collection_date": datetime.now().isoformat(),
            "regions": self.regions,
            "metrics": self.metrics,
            "summary": {
                "total_nat_gateways": total_nat,
                "total_transit_gateways": total_tgw,
                "total_vpc_endpoints": total_endpoints,
                "total_vpn_connections": total_vpn,
            },
        }

        # Generate JSON and calculate SHA256
        report_json = json.dumps(report, indent=2, default=str)
        checksum = hashlib.sha256(report_json.encode()).hexdigest()

        # Add checksum to report
        report["checksum"] = checksum

        # Write to file
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print_success(f"Baseline report generated: {output_file}")
        print_info(f"SHA256 Checksum: {checksum}")

        # Display summary table
        self._display_summary_table(report["summary"])

        return report

    def _display_summary_table(self, summary: Dict[str, int]) -> None:
        """
        Display summary statistics in Rich table format.

        Args:
            summary: Summary statistics dictionary
        """
        table = create_table(title="Network Baseline Summary", box_style="ROUNDED")
        table.add_column("Component", style="cyan")
        table.add_column("Count", style="bright_green", justify="right")
        table.add_column("Est. Monthly Cost", style="bright_yellow", justify="right")

        # Calculate costs dynamically (NO hardcoded pricing)
        nat_cost = summary["total_nat_gateways"] * self.pricing_config.get_nat_gateway_monthly_cost()
        tgw_cost = summary["total_transit_gateways"] * self.pricing_config.get_transit_gateway_attachment_cost()
        endpoint_cost = summary["total_vpc_endpoints"] * self.pricing_config.get_vpc_endpoint_interface_monthly_cost()
        vpn_cost = summary["total_vpn_connections"] * self.pricing_config.get_vpn_connection_monthly_cost()

        table.add_row("NAT Gateways", str(summary["total_nat_gateways"]), f"${nat_cost:,.2f}")
        table.add_row("Transit Gateways", str(summary["total_transit_gateways"]), f"${tgw_cost:,.2f}")
        table.add_row("VPC Endpoints", str(summary["total_vpc_endpoints"]), f"${endpoint_cost:,.2f}")
        table.add_row("VPN Connections", str(summary["total_vpn_connections"]), f"${vpn_cost:,.2f}")

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")


# CLI Integration Example
if __name__ == "__main__":
    import sys

    # Simple CLI for standalone execution
    profile = sys.argv[1] if len(sys.argv) > 1 else "default"

    collector = NetworkBaselineCollector(profile=profile)
    baseline = collector.collect_all_metrics()
    report = collector.generate_baseline_report()

    print(f"\n✅ Baseline collection complete!")
    print(f"Regions analyzed: {len(baseline)}")
    print(f"Report saved with checksum: {report['checksum'][:16]}...")
