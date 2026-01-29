#!/usr/bin/env python3
"""
Multi-Account Network Diagram Generator - Diagrams-as-Code

Generates network architecture diagrams from multi-account AWS discovery data
using the `diagrams` library. Supports combined multi-account views and
per-account detailed diagrams.

Diagram Types:
1. Multi-Account Overview - Combined view with Transit Gateway hub
2. Per-Account Detail - Individual account architecture
3. Transit Gateway Topology - TGW attachments and routing
4. VPC Connectivity Map - VPC peerings and endpoints

Author: Runbooks Team
Version: 1.1.x
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from diagrams import Cluster, Diagram, Edge
    from diagrams.aws.compute import EC2
    from diagrams.aws.general import Client
    from diagrams.aws.management import Organizations
    from diagrams.aws.network import (
        ELB,
        Endpoint,
        InternetGateway,
        NATGateway,
        PrivateSubnet,
        PublicSubnet,
        RouteTable,
        TransitGateway,
        VPC,
        VPCRouter,
    )
    from diagrams.aws.security import WAF
    from diagrams.generic.network import Firewall, Router, Switch
    from diagrams.onprem.network import Internet

    DIAGRAMS_AVAILABLE = True
except ImportError:
    DIAGRAMS_AVAILABLE = False

from runbooks.common.rich_utils import (
    Console,
    print_error,
    print_info,
    print_success,
    print_warning,
)


class MultiAccountDiagramGenerator:
    """
    Generate multi-account network architecture diagrams.

    Creates combined and per-account views from AWS discovery data,
    supporting PNG and SVG output formats.
    """

    def __init__(
        self,
        discovery_data: Optional[Dict[str, Any]] = None,
        discovery_file: Optional[str] = None,
        output_dir: Optional[str] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize multi-account diagram generator.

        Args:
            discovery_data: Pre-loaded discovery data dictionary
            discovery_file: Path to discovery JSON file
            output_dir: Output directory for diagrams
            console: Rich console for output
        """
        if not DIAGRAMS_AVAILABLE:
            raise ImportError("diagrams library not available. Install with: uv pip install diagrams")

        self.console = console or Console()
        self.output_dir = Path(output_dir or "artifacts/network-discovery/diagrams")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load discovery data
        if discovery_data:
            self.discovery_data = discovery_data
        elif discovery_file:
            self.discovery_data = self._load_discovery_file(discovery_file)
        else:
            self.discovery_data = {}

        # Common diagram attributes
        self.graph_attr = {
            "fontsize": "12",
            "bgcolor": "white",
            "pad": "0.5",
            "ranksep": "1.2",
            "nodesep": "0.8",
            "splines": "ortho",
        }

    def _load_discovery_file(self, filepath: str) -> Dict[str, Any]:
        """Load discovery data from JSON file."""
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            print_error(f"Failed to load discovery file: {e}")
            return {}

    def generate_multi_account_overview(
        self,
        output_formats: List[str] = ["png", "svg"],
        filename: Optional[str] = None,
    ) -> List[str]:
        """
        Generate multi-account overview diagram.

        Shows all discovered accounts with Transit Gateway hub and
        VPC attachments in a combined architectural view.

        Args:
            output_formats: List of output formats (png, svg)
            filename: Base filename without extension

        Returns:
            List of generated file paths
        """
        base_name = filename or "multi-account-overview"
        generated = []

        print_info("Generating multi-account overview diagram...")

        accounts = list(self.discovery_data.keys())
        if not accounts:
            print_warning("No accounts in discovery data")
            return []

        for fmt in output_formats:
            output_path = str(self.output_dir / base_name)

            with Diagram(
                "NZ Network Architecture - Multi-Account Overview",
                filename=output_path,
                outformat=fmt,
                show=False,
                direction="TB",
                graph_attr=self.graph_attr,
            ):
                # Internet/External connectivity
                internet = Internet("Internet")

                # Find Transit Gateway (shared across accounts)
                tgw_data = None
                tgw_attachments = []
                for account_id, data in self.discovery_data.items():
                    if data.get("transit_gateways"):
                        tgw_data = data["transit_gateways"][0]
                        tgw_attachments = data.get("tgw_attachments", [])
                        break

                # Transit Gateway Hub Cluster
                with Cluster("Transit Gateway Hub\nap-southeast-2"):
                    if tgw_data:
                        tgw = TransitGateway(
                            f"TGW\n{tgw_data['transit_gateway_id'][:16]}...\n{len(tgw_attachments)} attachments"
                        )
                    else:
                        tgw = TransitGateway("Transit Gateway\n(Not Discovered)")

                    # Route tables from TGW
                    tgw_rt = RouteTable("TGW Route Tables")

                # Create account clusters
                account_nodes = {}
                for account_id, data in self.discovery_data.items():
                    account_name = data.get("account_name", account_id)
                    vpcs = data.get("vpcs", [])
                    subnets = data.get("subnets", [])
                    nat_gateways = data.get("nat_gateways", [])
                    endpoints = data.get("vpc_endpoints", [])
                    igws = data.get("internet_gateways", [])

                    with Cluster(f"{account_name}\n({account_id})"):
                        if vpcs:
                            vpc = vpcs[0]
                            vpc_node = VPC(f"{vpc.get('name', 'VPC')}\n{vpc['cidr_block']}")

                            # Subnet representation
                            with Cluster(f"{len(subnets)} Subnets"):
                                pub_subnets = [s for s in subnets if s.get("map_public_ip")]
                                prv_subnets = [s for s in subnets if not s.get("map_public_ip")]

                                if pub_subnets:
                                    pub = PublicSubnet(f"Public\n{len(pub_subnets)} subnets")
                                else:
                                    pub = PublicSubnet("Public\n0 subnets")

                                prv = PrivateSubnet(f"Private\n{len(prv_subnets)} subnets")

                            # NAT Gateways
                            if nat_gateways:
                                nat = NATGateway(f"NAT GW\n{len(nat_gateways)} gateways")
                            else:
                                nat = None

                            # VPC Endpoints
                            if endpoints:
                                ep = Endpoint(f"Endpoints\n{len(endpoints)} VPCEs")
                            else:
                                ep = None

                            # Internet Gateway
                            if igws:
                                igw = InternetGateway("IGW")
                            else:
                                igw = None

                            account_nodes[account_id] = {
                                "vpc": vpc_node,
                                "pub": pub,
                                "prv": prv,
                                "nat": nat,
                                "ep": ep,
                                "igw": igw,
                            }
                        else:
                            vpc_node = VPC("No VPCs")
                            account_nodes[account_id] = {"vpc": vpc_node}

                # Connect components
                internet >> Edge(label="Public Traffic") >> tgw
                tgw >> tgw_rt

                for account_id, nodes in account_nodes.items():
                    if "vpc" in nodes:
                        (
                            tgw
                            >> Edge(
                                label="TGW Attachment",
                                color="blue",
                            )
                            >> nodes["vpc"]
                        )

                        if nodes.get("igw"):
                            (
                                internet
                                >> Edge(
                                    label="IGW",
                                    color="green",
                                    style="dashed",
                                )
                                >> nodes["igw"]
                            )
                            nodes["igw"] >> nodes.get("pub", nodes["vpc"])

                        if nodes.get("nat"):
                            nodes["prv"] >> nodes["nat"]

                        if nodes.get("ep"):
                            nodes["prv"] >> Edge(style="dotted") >> nodes["ep"]

            generated.append(f"{output_path}.{fmt}")

        print_success(f"Generated multi-account overview: {len(generated)} files")
        return generated

    def generate_account_detail_diagram(
        self,
        account_id: str,
        output_formats: List[str] = ["png", "svg"],
        filename: Optional[str] = None,
    ) -> List[str]:
        """
        Generate detailed diagram for a single account.

        Shows VPC structure, subnets by AZ, NAT gateways, endpoints,
        and network interfaces.

        Args:
            account_id: AWS account ID to diagram
            output_formats: List of output formats
            filename: Base filename without extension

        Returns:
            List of generated file paths
        """
        if account_id not in self.discovery_data:
            print_warning(f"Account {account_id} not in discovery data")
            return []

        data = self.discovery_data[account_id]
        account_name = data.get("account_name", account_id)
        base_name = filename or f"{account_id}-detail"
        generated = []

        print_info(f"Generating detail diagram for {account_name}...")

        for fmt in output_formats:
            output_path = str(self.output_dir / base_name)

            with Diagram(
                f"{account_name} ({account_id})\nNetwork Architecture Detail",
                filename=output_path,
                outformat=fmt,
                show=False,
                direction="TB",
                graph_attr=self.graph_attr,
            ):
                # VPC
                vpcs = data.get("vpcs", [])
                subnets = data.get("subnets", [])
                nat_gateways = data.get("nat_gateways", [])
                endpoints = data.get("vpc_endpoints", [])
                igws = data.get("internet_gateways", [])
                route_tables = data.get("route_tables", [])
                security_groups = data.get("security_groups", [])
                enis = data.get("network_interfaces", [])

                if not vpcs:
                    with Cluster("No VPCs Discovered"):
                        VPC("No VPCs")
                    continue

                vpc = vpcs[0]
                internet = Internet("Internet")

                with Cluster(f"VPC: {vpc.get('name', vpc['vpc_id'])}\n{vpc['cidr_block']}"):
                    # Group subnets by AZ
                    az_subnets = {}
                    for subnet in subnets:
                        az = subnet.get("availability_zone", "unknown")
                        if az not in az_subnets:
                            az_subnets[az] = []
                        az_subnets[az].append(subnet)

                    az_nodes = {}
                    for az, az_subnet_list in sorted(az_subnets.items()):
                        with Cluster(f"AZ: {az}\n{len(az_subnet_list)} subnets"):
                            # Categorize subnets
                            public = [s for s in az_subnet_list if "pub" in s.get("name", "").lower()]
                            private = [
                                s
                                for s in az_subnet_list
                                if "prv" in s.get("name", "").lower() or "private" in s.get("name", "").lower()
                            ]
                            nat_subnets = [s for s in az_subnet_list if "nat" in s.get("name", "").lower()]
                            transit = [s for s in az_subnet_list if "transit" in s.get("name", "").lower()]
                            gwlb = [s for s in az_subnet_list if "gwlb" in s.get("name", "").lower()]

                            nodes = []
                            if public:
                                pub_node = PublicSubnet(f"Public\n{len(public)} subnets")
                                nodes.append(pub_node)
                            if private:
                                prv_node = PrivateSubnet(f"Private\n{len(private)} subnets")
                                nodes.append(prv_node)
                            if nat_subnets:
                                nat_node = PrivateSubnet(f"NAT\n{len(nat_subnets)} subnets")
                                nodes.append(nat_node)
                            if transit:
                                transit_node = PrivateSubnet(f"Transit\n{len(transit)} subnets")
                                nodes.append(transit_node)
                            if gwlb:
                                gwlb_node = PrivateSubnet(f"GWLB\n{len(gwlb)} subnets")
                                nodes.append(gwlb_node)

                            if not nodes:
                                other_node = PrivateSubnet(f"Other\n{len(az_subnet_list)} subnets")
                                nodes.append(other_node)

                            az_nodes[az] = nodes

                    # NAT Gateways
                    nat_nodes = []
                    if nat_gateways:
                        with Cluster(f"NAT Gateways ({len(nat_gateways)})"):
                            for nat in nat_gateways[:3]:
                                nat_az = nat.get("subnet_az", "unknown")
                                nat_node = NATGateway(f"NAT\n{nat['nat_gateway_id'][:12]}...\n{nat_az}")
                                nat_nodes.append(nat_node)

                    # VPC Endpoints
                    ep_nodes = []
                    if endpoints:
                        with Cluster(f"VPC Endpoints ({len(endpoints)})"):
                            # Group by service
                            services = {}
                            for ep in endpoints:
                                svc = ep.get("service_name", "unknown").split(".")[-1]
                                if svc not in services:
                                    services[svc] = 0
                                services[svc] += 1

                            for svc, count in list(services.items())[:4]:
                                ep_node = Endpoint(f"{svc}\n({count})")
                                ep_nodes.append(ep_node)

                    # Route Tables
                    rt_node = RouteTable(f"Route Tables\n{len(route_tables)} tables")

                    # Security Groups
                    sg_node = WAF(f"Security Groups\n{len(security_groups)} groups")

                # Internet Gateway
                if igws:
                    igw = InternetGateway("Internet Gateway")
                    internet >> igw
                    for az, nodes in az_nodes.items():
                        for node in nodes:
                            if "Public" in str(node):
                                igw >> Edge(color="green") >> node

                # NAT Gateway connections
                for nat_node in nat_nodes:
                    if igws:
                        igw >> Edge(label="Egress", color="orange") >> nat_node
                    for az, nodes in az_nodes.items():
                        for node in nodes:
                            if "Private" in str(node) or "Transit" in str(node):
                                node >> Edge(style="dashed") >> nat_node

                # Endpoint connections
                for ep_node in ep_nodes:
                    for az, nodes in az_nodes.items():
                        for node in nodes:
                            if "Private" in str(node):
                                node >> Edge(style="dotted", color="purple") >> ep_node

            generated.append(f"{output_path}.{fmt}")

        print_success(f"Generated account detail diagram: {len(generated)} files")
        return generated

    def generate_transit_gateway_topology(
        self,
        output_formats: List[str] = ["png", "svg"],
        filename: Optional[str] = None,
    ) -> List[str]:
        """
        Generate Transit Gateway topology diagram.

        Shows TGW with all attachments categorized by type (VPC, VPN, DX, Peering).

        Args:
            output_formats: List of output formats
            filename: Base filename without extension

        Returns:
            List of generated file paths
        """
        base_name = filename or "transit-gateway-topology"
        generated = []

        print_info("Generating Transit Gateway topology diagram...")

        # Find TGW data
        tgw_data = None
        tgw_attachments = []
        for account_id, data in self.discovery_data.items():
            if data.get("transit_gateways"):
                tgw_data = data["transit_gateways"][0]
                tgw_attachments = data.get("tgw_attachments", [])
                break

        if not tgw_data:
            print_warning("No Transit Gateway found in discovery data")
            return []

        for fmt in output_formats:
            output_path = str(self.output_dir / base_name)

            with Diagram(
                f"Transit Gateway Topology\n{tgw_data['transit_gateway_id']}",
                filename=output_path,
                outformat=fmt,
                show=False,
                direction="LR",
                graph_attr=self.graph_attr,
            ):
                # Central TGW
                with Cluster("Transit Gateway Hub"):
                    tgw = TransitGateway(
                        f"TGW\n{tgw_data['transit_gateway_id'][:16]}...\nOwner: {tgw_data.get('owner_id', 'N/A')}"
                    )

                # Group attachments by type
                vpc_attachments = [a for a in tgw_attachments if a.get("resource_type") == "vpc"]
                vpn_attachments = [a for a in tgw_attachments if a.get("resource_type") == "vpn"]
                dx_attachments = [a for a in tgw_attachments if a.get("resource_type") == "direct-connect-gateway"]
                peering_attachments = [a for a in tgw_attachments if a.get("resource_type") == "peering"]
                other_attachments = [
                    a
                    for a in tgw_attachments
                    if a.get("resource_type") not in ["vpc", "vpn", "direct-connect-gateway", "peering"]
                ]

                # VPC Attachments
                if vpc_attachments:
                    with Cluster(f"VPC Attachments ({len(vpc_attachments)})"):
                        # Show up to 5 individual, then summarize
                        for att in vpc_attachments[:5]:
                            vpc_node = VPC(
                                f"VPC\n{att.get('resource_id', 'N/A')[:12]}...\n{att.get('resource_owner_id', 'N/A')}"
                            )
                            tgw >> Edge(label="VPC", color="blue") >> vpc_node

                        if len(vpc_attachments) > 5:
                            more = VPC(f"+{len(vpc_attachments) - 5} more VPCs")
                            tgw >> Edge(style="dashed") >> more

                # VPN Attachments
                if vpn_attachments:
                    with Cluster(f"VPN Attachments ({len(vpn_attachments)})"):
                        for att in vpn_attachments[:3]:
                            vpn_node = Router(f"VPN\n{att.get('resource_id', 'N/A')[:12]}...")
                            tgw >> Edge(label="VPN", color="orange") >> vpn_node

                # Direct Connect
                if dx_attachments:
                    with Cluster(f"Direct Connect ({len(dx_attachments)})"):
                        for att in dx_attachments[:2]:
                            dx_node = Switch(f"DX-GW\n{att.get('resource_id', 'N/A')[:12]}...")
                            tgw >> Edge(label="DX", color="red", style="bold") >> dx_node

                # Peering
                if peering_attachments:
                    with Cluster(f"TGW Peering ({len(peering_attachments)})"):
                        for att in peering_attachments[:2]:
                            peer_node = TransitGateway(f"Peer TGW\n{att.get('resource_id', 'N/A')[:12]}...")
                            tgw >> Edge(label="Peering", color="purple", style="dashed") >> peer_node

                # Other attachments
                if other_attachments:
                    with Cluster(f"Other ({len(other_attachments)})"):
                        other_node = VPCRouter(f"Other\n{len(other_attachments)} attachments")
                        tgw >> Edge(style="dotted") >> other_node

            generated.append(f"{output_path}.{fmt}")

        print_success(f"Generated TGW topology: {len(generated)} files")
        return generated

    def generate_vpc_connectivity_map(
        self,
        output_formats: List[str] = ["png", "svg"],
        filename: Optional[str] = None,
    ) -> List[str]:
        """
        Generate VPC connectivity map showing peerings and endpoints.

        Args:
            output_formats: List of output formats
            filename: Base filename without extension

        Returns:
            List of generated file paths
        """
        base_name = filename or "vpc-connectivity-map"
        generated = []

        print_info("Generating VPC connectivity map...")

        for fmt in output_formats:
            output_path = str(self.output_dir / base_name)

            with Diagram(
                "VPC Connectivity Map\nEndpoints & Cross-Account Access",
                filename=output_path,
                outformat=fmt,
                show=False,
                direction="TB",
                graph_attr=self.graph_attr,
            ):
                # AWS Services
                with Cluster("AWS Services (Regional)"):
                    s3 = Endpoint("S3")
                    ec2_svc = Endpoint("EC2")
                    ssm = Endpoint("SSM")
                    logs = Endpoint("CloudWatch Logs")

                # Account VPCs with endpoints
                for account_id, data in self.discovery_data.items():
                    account_name = data.get("account_name", account_id)
                    vpcs = data.get("vpcs", [])
                    endpoints = data.get("vpc_endpoints", [])

                    if not vpcs:
                        continue

                    vpc = vpcs[0]
                    with Cluster(f"{account_name}\n{vpc['cidr_block']}"):
                        vpc_node = VPC(f"VPC\n{vpc.get('name', vpc['vpc_id'])}")

                        # Endpoint connections
                        ep_services = set()
                        for ep in endpoints:
                            svc = ep.get("service_name", "").split(".")[-1].lower()
                            ep_services.add(svc)

                        # Connect to AWS services via endpoints
                        if "s3" in ep_services:
                            vpc_node >> Edge(label="VPCE", style="dashed", color="green") >> s3
                        if "ec2" in ep_services:
                            vpc_node >> Edge(label="VPCE", style="dashed", color="green") >> ec2_svc
                        if "ssm" in ep_services or "ssmmessages" in ep_services:
                            vpc_node >> Edge(label="VPCE", style="dashed", color="green") >> ssm
                        if "logs" in ep_services:
                            vpc_node >> Edge(label="VPCE", style="dashed", color="green") >> logs

            generated.append(f"{output_path}.{fmt}")

        print_success(f"Generated connectivity map: {len(generated)} files")
        return generated

    def generate_all_diagrams(
        self,
        output_formats: List[str] = ["png", "svg"],
    ) -> Dict[str, List[str]]:
        """
        Generate all diagram types.

        Args:
            output_formats: List of output formats

        Returns:
            Dictionary mapping diagram type to list of generated files
        """
        results = {}

        print_info("Generating complete diagram suite...")

        # Multi-account overview
        results["multi_account_overview"] = self.generate_multi_account_overview(output_formats=output_formats)

        # Per-account details
        for account_id in self.discovery_data.keys():
            key = f"account_detail_{account_id}"
            results[key] = self.generate_account_detail_diagram(
                account_id=account_id,
                output_formats=output_formats,
            )

        # Transit Gateway topology
        results["transit_gateway_topology"] = self.generate_transit_gateway_topology(output_formats=output_formats)

        # VPC connectivity map
        results["vpc_connectivity_map"] = self.generate_vpc_connectivity_map(output_formats=output_formats)

        # Summary
        total_files = sum(len(files) for files in results.values())
        print_success(f"Generated {total_files} diagram files")

        return results


# CLI Entry Point
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python multi_account_diagram_generator.py <discovery_file.json>")
        sys.exit(1)

    discovery_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    generator = MultiAccountDiagramGenerator(
        discovery_file=discovery_file,
        output_dir=output_dir,
    )

    results = generator.generate_all_diagrams()

    print("\nGenerated Diagrams:")
    for diagram_type, files in results.items():
        print(f"  {diagram_type}:")
        for f in files:
            print(f"    - {f}")
