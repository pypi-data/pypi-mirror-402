#!/usr/bin/env python3
"""
VPC Central Firewall Bypass Discovery Engine

Discovers VPCs NOT routing traffic through central firewall for inspection
across multi-account AWS Organizations environments.

Methodology:
1. Discover organization accounts via Organizations API
2. Enumerate all VPCs across accounts and regions
3. Analyze Transit Gateway (TGW) attachments per VPC
4. Examine route tables to detect IGW vs TGW routing patterns
5. Classify inspection status: NONE (direct IGW) | EGRESS_ONLY | INGRESS_EGRESS | UNKNOWN

Author: Runbooks Team
Version: 1.1.x
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    create_table,
    create_progress_bar,
)
from runbooks.inventory.organizations_utils import (
    discover_organization_accounts,
)
from runbooks.vpc.transit_gateway_manager import TransitGatewayManager


class InspectionStatus(Enum):
    """VPC traffic inspection status classification"""

    NONE = "none"  # No inspection (direct IGW routing)
    EGRESS_ONLY = "egress_only"  # Only egress traffic inspected
    INGRESS_EGRESS = "ingress_egress"  # Full bidirectional inspection
    UNKNOWN = "unknown"  # Cannot determine (needs investigation)


class RoutingPattern(Enum):
    """VPC routing configuration patterns"""

    DIRECT_IGW = "direct_igw"  # Direct internet gateway (no firewall)
    TGW_ROUTED = "tgw_routed"  # Transit Gateway routing (potential firewall)
    NAT_GATEWAY = "nat_gateway"  # NAT Gateway routing
    VPN_GATEWAY = "vpn_gateway"  # VPN Gateway routing
    UNKNOWN = "unknown"  # Cannot determine routing


@dataclass
class VPCInspectionRecord:
    """Complete VPC firewall inspection record"""

    # Identity
    account_id: str
    account_name: str
    region: str
    vpc_id: str
    vpc_name: str
    cidr_block: str

    # Routing Configuration
    routing_pattern: RoutingPattern
    default_route_target: Optional[str]  # IGW/TGW/NAT ID
    default_route_target_type: Optional[str]  # igw/tgw/nat-gateway/vpn-gateway

    # Transit Gateway Details
    tgw_attached: bool
    tgw_id: Optional[str]
    tgw_attachment_id: Optional[str]

    # Inspection Status
    inspection_status: InspectionStatus
    firewall_vpc_id: Optional[str]  # Central firewall VPC (if routed via TGW)

    # Metadata
    discovery_timestamp: str


class FirewallBypassDiscovery:
    """
    Multi-account VPC firewall bypass discovery engine

    Discovers:
    1. VPCs with NO traffic inspection (direct IGW routing)
    2. VPCs with PARTIAL inspection (egress only)
    3. VPCs with FULL inspection (ingress + egress)

    Methodology:
    - Organizations API for multi-account discovery
    - EC2 DescribeVpcs for VPC enumeration
    - EC2 DescribeTransitGatewayAttachments for TGW topology
    - EC2 DescribeRouteTables for routing analysis
    """

    def __init__(
        self,
        management_profile: str,
        operational_profile: str,
        billing_profile: str,
        regions: List[str] = None,
        max_workers: int = 10,
    ):
        """
        Initialize firewall bypass discovery

        Args:
            management_profile: AWS profile with Organizations API access
            operational_profile: AWS profile for VPC/TGW discovery
            billing_profile: AWS profile for cost analysis (future use)
            regions: AWS regions to scan (default: ap-southeast-2)
            max_workers: Maximum concurrent worker threads
        """
        self.management_profile = management_profile
        self.operational_profile = operational_profile
        self.billing_profile = billing_profile
        self.regions = regions or ["ap-southeast-2"]
        self.max_workers = max_workers

        # Initialize AWS sessions
        self.mgmt_session = boto3.Session(profile_name=management_profile)
        self.ops_session = boto3.Session(profile_name=operational_profile)

        # Discovery results storage
        self.inspection_records: List[VPCInspectionRecord] = []
        self.discovery_timestamp = datetime.now().isoformat()

    def discover_all(self) -> List[VPCInspectionRecord]:
        """
        Execute complete firewall bypass discovery across organization

        Returns:
            List of VPCInspectionRecord with inspection status classification
        """
        print_header("VPC Firewall Bypass Discovery", version="1.1.x")
        console.print(f"[cyan]Management Profile:[/cyan] {self.management_profile}")
        console.print(f"[cyan]Operational Profile:[/cyan] {self.operational_profile}")
        console.print(f"[cyan]Regions:[/cyan] {', '.join(self.regions)}\n")

        # Step 1: Discover organization accounts
        print_info("Step 1: Discovering organization accounts...")
        accounts, error = discover_organization_accounts(
            management_profile=self.management_profile, region=self.regions[0]
        )

        if error:
            print_warning(f"Organizations API fallback: {error}")

        print_success(f"Found {len(accounts)} accounts to scan")

        # Step 2: Discover all VPCs across accounts and regions
        print_info("\nStep 2: Discovering VPCs across accounts and regions...")
        all_vpcs = self._discover_vpcs_multi_account(accounts)
        print_success(f"Found {len(all_vpcs)} VPCs across {len(accounts)} accounts")

        # Step 3: Analyze TGW attachments for all VPCs
        print_info("\nStep 3: Analyzing Transit Gateway attachments...")
        tgw_attachments = self._analyze_tgw_attachments(all_vpcs)
        print_success(f"Analyzed TGW topology for {len(all_vpcs)} VPCs")

        # Step 4: Analyze route tables to determine routing patterns
        print_info("\nStep 4: Analyzing route tables for routing patterns...")
        self._analyze_routing_patterns(all_vpcs, tgw_attachments)
        print_success(f"Analyzed routing patterns for {len(all_vpcs)} VPCs")

        # Step 5: Classify inspection status
        print_info("\nStep 5: Classifying firewall inspection status...")
        self._classify_inspection_status()
        print_success(f"Classified {len(self.inspection_records)} VPC inspection records")

        # Display results summary
        self._display_summary()

        return self.inspection_records

    def _discover_vpcs_multi_account(self, accounts: List[Dict]) -> List[Dict]:
        """
        Discover all VPCs across multiple accounts and regions

        Args:
            accounts: List of account dictionaries from Organizations API

        Returns:
            List of VPC metadata dictionaries with account context
        """
        all_vpcs = []

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Discovering VPCs...", total=len(accounts) * len(self.regions))

            # Concurrent multi-account VPC discovery
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_account = {
                    executor.submit(self._discover_vpcs_in_account, account, region): (account, region)
                    for account in accounts
                    for region in self.regions
                }

                for future in as_completed(future_to_account):
                    account, region = future_to_account[future]
                    try:
                        vpcs = future.result()
                        all_vpcs.extend(vpcs)
                    except Exception as e:
                        console.print(f"[dim red]Failed to discover VPCs in {account['id']} ({region}): {e}[/]")

                    progress.update(task, advance=1)

        return all_vpcs

    def _discover_vpcs_in_account(self, account: Dict, region: str) -> List[Dict]:
        """
        Discover VPCs in single account/region

        Args:
            account: Account dictionary with id, name, profile
            region: AWS region

        Returns:
            List of VPC metadata dictionaries
        """
        vpcs = []

        try:
            # Create EC2 client for this account/region
            session = boto3.Session(profile_name=account.get("profile", self.operational_profile), region_name=region)
            ec2_client = session.client("ec2")

            # Describe VPCs
            response = ec2_client.describe_vpcs()

            for vpc in response.get("Vpcs", []):
                vpc_id = vpc["VpcId"]
                vpc_name = self._get_vpc_name(vpc)

                vpcs.append(
                    {
                        "account_id": account["id"],
                        "account_name": account.get("name", account["id"]),
                        "region": region,
                        "vpc_id": vpc_id,
                        "vpc_name": vpc_name,
                        "cidr_block": vpc.get("CidrBlock", ""),
                        "is_default": vpc.get("IsDefault", False),
                        "state": vpc.get("State", "unknown"),
                        "tags": vpc.get("Tags", []),
                    }
                )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "UnauthorizedOperation":
                # Expected for accounts without VPC access
                pass
            else:
                console.print(f"[dim red]EC2 API error in {account['id']} ({region}): {error_code}[/]")
        except Exception as e:
            console.print(f"[dim red]Unexpected error in {account['id']} ({region}): {e}[/]")

        return vpcs

    def _analyze_tgw_attachments(self, vpcs: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze Transit Gateway attachments for all VPCs

        Args:
            vpcs: List of VPC metadata dictionaries

        Returns:
            Dictionary mapping vpc_id to TGW attachment details
        """
        tgw_attachments = {}

        # Group VPCs by region for efficient TGW queries
        vpcs_by_region = {}
        for vpc in vpcs:
            region = vpc["region"]
            if region not in vpcs_by_region:
                vpcs_by_region[region] = []
            vpcs_by_region[region].append(vpc)

        # Query TGW attachments per region
        for region, regional_vpcs in vpcs_by_region.items():
            try:
                ec2_client = self.ops_session.client("ec2", region_name=region)

                # Get all TGW attachments in region
                response = ec2_client.describe_transit_gateway_vpc_attachments()

                for attachment in response.get("TransitGatewayVpcAttachments", []):
                    vpc_id = attachment["VpcId"]
                    tgw_id = attachment["TransitGatewayId"]
                    attachment_id = attachment["TransitGatewayAttachmentId"]
                    state = attachment["State"]

                    if state == "available":
                        tgw_attachments[vpc_id] = {
                            "tgw_id": tgw_id,
                            "attachment_id": attachment_id,
                            "state": state,
                            "region": region,
                        }

            except ClientError as e:
                console.print(f"[dim red]Failed to query TGW attachments in {region}: {e.response['Error']['Code']}[/]")

        return tgw_attachments

    def _analyze_routing_patterns(self, vpcs: List[Dict], tgw_attachments: Dict[str, Dict]) -> None:
        """
        Analyze route tables to determine routing patterns

        Args:
            vpcs: List of VPC metadata dictionaries
            tgw_attachments: Dictionary of TGW attachments by VPC ID
        """
        for vpc in vpcs:
            vpc_id = vpc["vpc_id"]
            region = vpc["region"]
            account_profile = vpc.get("profile", self.operational_profile)

            try:
                # Create EC2 client for this VPC's account/region
                session = boto3.Session(profile_name=account_profile, region_name=region)
                ec2_client = session.client("ec2")

                # Get route tables for this VPC
                response = ec2_client.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])

                route_tables = response.get("RouteTables", [])
                routing_pattern, default_target, target_type = self._classify_routing_pattern(route_tables)

                # Check TGW attachment
                tgw_attachment = tgw_attachments.get(vpc_id)
                tgw_attached = tgw_attachment is not None

                # Create inspection record
                record = VPCInspectionRecord(
                    account_id=vpc["account_id"],
                    account_name=vpc["account_name"],
                    region=region,
                    vpc_id=vpc_id,
                    vpc_name=vpc["vpc_name"],
                    cidr_block=vpc["cidr_block"],
                    routing_pattern=routing_pattern,
                    default_route_target=default_target,
                    default_route_target_type=target_type,
                    tgw_attached=tgw_attached,
                    tgw_id=tgw_attachment["tgw_id"] if tgw_attached else None,
                    tgw_attachment_id=tgw_attachment["attachment_id"] if tgw_attached else None,
                    inspection_status=InspectionStatus.UNKNOWN,  # Classified in next step
                    firewall_vpc_id=None,
                    discovery_timestamp=self.discovery_timestamp,
                )

                self.inspection_records.append(record)

            except ClientError as e:
                console.print(f"[dim red]Failed to analyze routes for {vpc_id}: {e.response['Error']['Code']}[/]")

    def _classify_routing_pattern(
        self, route_tables: List[Dict]
    ) -> Tuple[RoutingPattern, Optional[str], Optional[str]]:
        """
        Classify VPC routing pattern based on route tables

        Args:
            route_tables: List of route table dictionaries from DescribeRouteTables

        Returns:
            Tuple of (routing_pattern, default_route_target, target_type)
        """
        # Look for default route (0.0.0.0/0) across all route tables
        for rt in route_tables:
            for route in rt.get("Routes", []):
                dest = route.get("DestinationCidrBlock", "")

                if dest == "0.0.0.0/0":
                    # Found default route - determine target type
                    if "GatewayId" in route:
                        gateway_id = route["GatewayId"]
                        if gateway_id.startswith("igw-"):
                            return (RoutingPattern.DIRECT_IGW, gateway_id, "igw")
                        elif gateway_id.startswith("vgw-"):
                            return (RoutingPattern.VPN_GATEWAY, gateway_id, "vpn-gateway")
                    elif "TransitGatewayId" in route:
                        tgw_id = route["TransitGatewayId"]
                        return (RoutingPattern.TGW_ROUTED, tgw_id, "tgw")
                    elif "NatGatewayId" in route:
                        nat_id = route["NatGatewayId"]
                        return (RoutingPattern.NAT_GATEWAY, nat_id, "nat-gateway")

        # No default route found
        return (RoutingPattern.UNKNOWN, None, None)

    def _classify_inspection_status(self) -> None:
        """
        Classify firewall inspection status for all VPC records

        Classification logic:
        - DIRECT_IGW → NONE (no firewall inspection)
        - TGW_ROUTED → INGRESS_EGRESS (assumes central firewall via TGW)
        - NAT_GATEWAY → EGRESS_ONLY (NAT provides egress only)
        - VPN_GATEWAY → UNKNOWN (needs investigation)
        - UNKNOWN routing → UNKNOWN inspection
        """
        for record in self.inspection_records:
            if record.routing_pattern == RoutingPattern.DIRECT_IGW:
                record.inspection_status = InspectionStatus.NONE
            elif record.routing_pattern == RoutingPattern.TGW_ROUTED:
                record.inspection_status = InspectionStatus.INGRESS_EGRESS
            elif record.routing_pattern == RoutingPattern.NAT_GATEWAY:
                record.inspection_status = InspectionStatus.EGRESS_ONLY
            else:
                record.inspection_status = InspectionStatus.UNKNOWN

    def _display_summary(self) -> None:
        """Display discovery results summary"""
        # Count by inspection status
        none_count = sum(1 for r in self.inspection_records if r.inspection_status == InspectionStatus.NONE)
        egress_only_count = sum(
            1 for r in self.inspection_records if r.inspection_status == InspectionStatus.EGRESS_ONLY
        )
        full_count = sum(1 for r in self.inspection_records if r.inspection_status == InspectionStatus.INGRESS_EGRESS)
        unknown_count = sum(1 for r in self.inspection_records if r.inspection_status == InspectionStatus.UNKNOWN)

        console.print("\n[bold cyan]Firewall Bypass Discovery Summary[/bold cyan]")
        console.print(f"[bright_red]❌ NO Inspection (Direct IGW):[/bright_red] {none_count} VPCs")
        console.print(f"[bright_yellow]⚠️  PARTIAL Inspection (Egress Only):[/bright_yellow] {egress_only_count} VPCs")
        console.print(f"[bright_green]✅ FULL Inspection (Ingress+Egress):[/bright_green] {full_count} VPCs")
        console.print(f"[dim]❓ UNKNOWN:[/dim] {unknown_count} VPCs\n")

        # Display table with bypassing VPCs
        if none_count > 0:
            self._display_bypassing_vpcs_table()

    def _display_bypassing_vpcs_table(self) -> None:
        """Display table of VPCs bypassing central firewall"""
        table = create_table(title="VPCs Bypassing Central Firewall (Direct IGW Routing)")
        table.add_column("Account", style="cyan")
        table.add_column("Region", style="bright_blue")
        table.add_column("VPC ID", style="bright_yellow")
        table.add_column("VPC Name", style="white")
        table.add_column("CIDR", style="dim")
        table.add_column("Route Target", style="bright_red")

        for record in self.inspection_records:
            if record.inspection_status == InspectionStatus.NONE:
                table.add_row(
                    f"{record.account_name}\n{record.account_id}",
                    record.region,
                    record.vpc_id,
                    record.vpc_name,
                    record.cidr_block,
                    record.default_route_target or "N/A",
                )

        console.print(table)

    def export_to_csv(self, output_path: Path) -> None:
        """
        Export discovery results to CSV

        Args:
            output_path: Path to output CSV file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="") as csvfile:
            fieldnames = [
                "account_id",
                "account_name",
                "region",
                "vpc_id",
                "vpc_name",
                "cidr_block",
                "routing_pattern",
                "default_route_target",
                "default_route_target_type",
                "tgw_attached",
                "tgw_id",
                "inspection_status",
                "discovery_timestamp",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for record in self.inspection_records:
                writer.writerow(
                    {
                        "account_id": record.account_id,
                        "account_name": record.account_name,
                        "region": record.region,
                        "vpc_id": record.vpc_id,
                        "vpc_name": record.vpc_name,
                        "cidr_block": record.cidr_block,
                        "routing_pattern": record.routing_pattern.value,
                        "default_route_target": record.default_route_target or "",
                        "default_route_target_type": record.default_route_target_type or "",
                        "tgw_attached": record.tgw_attached,
                        "tgw_id": record.tgw_id or "",
                        "inspection_status": record.inspection_status.value,
                        "discovery_timestamp": record.discovery_timestamp,
                    }
                )

        print_success(f"CSV exported to: {output_path}")

    def export_to_json(self, output_path: Path) -> None:
        """
        Export discovery results to JSON

        Args:
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_data = {
            "metadata": {
                "discovery_timestamp": self.discovery_timestamp,
                "management_profile": self.management_profile,
                "operational_profile": self.operational_profile,
                "regions": self.regions,
                "total_vpcs": len(self.inspection_records),
            },
            "vpcs": [
                {
                    "account_id": r.account_id,
                    "account_name": r.account_name,
                    "region": r.region,
                    "vpc_id": r.vpc_id,
                    "vpc_name": r.vpc_name,
                    "cidr_block": r.cidr_block,
                    "routing_pattern": r.routing_pattern.value,
                    "default_route_target": r.default_route_target,
                    "default_route_target_type": r.default_route_target_type,
                    "tgw_attached": r.tgw_attached,
                    "tgw_id": r.tgw_id,
                    "tgw_attachment_id": r.tgw_attachment_id,
                    "inspection_status": r.inspection_status.value,
                    "firewall_vpc_id": r.firewall_vpc_id,
                }
                for r in self.inspection_records
            ],
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print_success(f"JSON exported to: {output_path}")

    def _get_vpc_name(self, vpc: Dict) -> str:
        """Extract VPC name from tags"""
        tags = vpc.get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Name":
                return tag["Value"]
        return f"vpc-{vpc['VpcId'][-8:]}"  # Fallback to truncated ID


# CLI Integration Example
if __name__ == "__main__":
    import sys

    # Simple CLI for standalone execution
    if len(sys.argv) < 3:
        print("Usage: python firewall_bypass_discovery.py <management_profile> <operational_profile> [regions...]")
        sys.exit(1)

    management_profile = sys.argv[1]
    operational_profile = sys.argv[2]
    billing_profile = operational_profile  # Use operational for billing fallback
    regions = sys.argv[3:] if len(sys.argv) > 3 else ["ap-southeast-2"]

    discovery = FirewallBypassDiscovery(
        management_profile=management_profile,
        operational_profile=operational_profile,
        billing_profile=billing_profile,
        regions=regions,
    )

    records = discovery.discover_all()

    # Export results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    discovery.export_to_csv(Path(f"/tmp/firewall-bypass-{timestamp}.csv"))
    discovery.export_to_json(Path(f"/tmp/firewall-bypass-{timestamp}.json"))

    print_success(f"\n✅ Discovery complete: {len(records)} VPCs analyzed")
