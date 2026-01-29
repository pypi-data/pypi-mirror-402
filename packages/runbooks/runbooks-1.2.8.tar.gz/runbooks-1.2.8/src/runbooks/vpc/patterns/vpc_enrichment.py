#!/usr/bin/env python3
"""
VPC Enrichment Pattern - AWS VPC Metadata Integration

Base class for enriching VPCE/network resource analysis with VPC metadata.

Design Pattern:
    - Abstract base class requiring _get_vpce_resources() implementation
    - Provides VPC name, CIDR, and associated resource metadata
    - Per-account profile support for multi-account environments
    - Graceful fallback if VPC API unavailable

Reusability:
    - VPCE Cleanup Manager (current implementation)
    - NAT Gateway Optimizer (future enhancement)
    - ENI Cleanup (future enhancement)
    - VPC Cost Analysis (future enhancement)

Usage:
    class MyManager(VPCEnricher):
        def _get_vpce_resources(self):
            return self.vpce_endpoints  # List[VPCEndpoint]

    manager = MyManager()
    result = manager.enrich_with_vpc_api()
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from runbooks.common.rich_utils import (
    console,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)


@dataclass
class VPCEnrichmentResult:
    """Result from VPC API enrichment operation."""

    enriched_count: int
    vpcs_discovered: int
    vpc_names: Dict[str, str] = field(default_factory=dict)  # vpc_id → name
    vpc_cidrs: Dict[str, str] = field(default_factory=dict)  # vpc_id → CIDR
    vpc_resources: Dict[str, Dict] = field(default_factory=dict)  # vpc_id → resource counts
    errors: List[str] = field(default_factory=list)  # Error messages


class VPCEnricher(ABC):
    """
    Base class for AWS VPC metadata enrichment operations.

    Provides reusable methods for:
    - Retrieving VPC names from tags
    - Fetching VPC CIDR blocks
    - Discovering associated resources (subnets, route tables, IGWs, NAT Gateways)
    - Per-account profile support for multi-account environments

    Subclass Requirements:
        - Implement _get_vpce_resources() → List[VPCEndpoint]
        - VPCEndpoint must have: vpc_id, profile (AWS profile name), region

    Profile Pattern:
        - Uses per-resource profile attribute for multi-account support
        - Gracefully handles profile errors with fallback to resource IDs
    """

    @abstractmethod
    def _get_vpce_resources(self) -> List:
        """
        Return VPCE/network resources for VPC enrichment.

        Returns:
            List[VPCEndpoint] where VPCEndpoint has:
                - vpc_id: str (VPC identifier)
                - profile: str (AWS profile name)
                - region: str (AWS region)
                - Additional resource-specific fields
        """
        pass

    def enrich_with_vpc_api(
        self,
        include_resource_counts: bool = True,
    ) -> VPCEnrichmentResult:
        """
        Enrich resources with AWS VPC metadata.

        Args:
            include_resource_counts: Include associated resource counts
                                    (subnets, route tables, IGWs, NAT Gateways)

        Returns:
            VPCEnrichmentResult with enrichment statistics

        Example:
            >>> result = manager.enrich_with_vpc_api()
            >>> # ✅ Enriched 88 endpoints with VPC metadata (12 VPCs discovered)
            >>> # VPC names: prod-vpc, dev-vpc, staging-vpc, ...
        """
        resources = self._get_vpce_resources()

        if not resources:
            print_warning("⚠️  No resources to enrich (no VPCEs provided)")
            return VPCEnrichmentResult(
                enriched_count=0,
                vpcs_discovered=0,
            )

        # Initialize error tracking
        errors = []

        # PHASE 1: Fetch VPC IDs from VPCEs if vpc_id is missing (Bug fix for vpce-cleanup CSV)
        # Group VPCEs by profile/region to minimize API calls
        vpces_needing_vpc_id: Dict[str, Dict[str, List]] = {}  # profile → region → [vpce_objects]

        for resource in resources:
            profile = getattr(resource, "profile", None)
            vpc_id = getattr(resource, "vpc_id", None)
            # Try multiple attribute names for VPCE ID
            vpce_id = (
                getattr(resource, "vpce_id", None)
                or getattr(resource, "id", None)
                or getattr(resource, "vpc_endpoint_id", None)
            )
            region = getattr(resource, "region", "ap-southeast-2")

            if not profile:
                errors.append(f"Resource {vpce_id or 'unknown'} missing profile attribute")
                continue

            # If vpc_id missing but we have vpce_id, we need to fetch it
            if not vpc_id and vpce_id:
                if profile not in vpces_needing_vpc_id:
                    vpces_needing_vpc_id[profile] = {}
                if region not in vpces_needing_vpc_id[profile]:
                    vpces_needing_vpc_id[profile][region] = []
                vpces_needing_vpc_id[profile][region].append(resource)

        # Fetch VPC IDs from AWS for VPCEs missing vpc_id
        if vpces_needing_vpc_id:
            total_vpces = sum(len(r) for regions in vpces_needing_vpc_id.values() for r in regions.values())

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                transient=False,
            ) as progress:
                task = progress.add_task(f"Querying {total_vpces} VPCEs...", total=total_vpces)

                for profile, regions in vpces_needing_vpc_id.items():
                    try:
                        session = boto3.Session(profile_name=profile)

                        for region, vpce_resources in regions.items():
                            try:
                                ec2_client = session.client("ec2", region_name=region)
                                vpce_ids = [
                                    getattr(r, "vpce_id", None) or getattr(r, "id", None) for r in vpce_resources
                                ]
                                vpce_ids = [vid for vid in vpce_ids if vid]  # Filter None

                                if not vpce_ids:
                                    continue

                                # Batch describe VPC endpoints to get VPC IDs
                                vpce_to_vpc = {}
                                try:
                                    response = ec2_client.describe_vpc_endpoints(VpcEndpointIds=vpce_ids)

                                    # Map vpce_id → vpc_id
                                    vpce_to_vpc = {
                                        ep["VpcEndpointId"]: ep["VpcId"] for ep in response.get("VpcEndpoints", [])
                                    }

                                except ClientError as batch_error:
                                    # If batch fails due to missing VPCE, retry individually
                                    if batch_error.response["Error"]["Code"] == "InvalidVpcEndpointId.NotFound":
                                        print_warning(
                                            f"⚠️  Batch query failed (1+ deleted VPCEs), retrying {len(vpce_ids)} individually..."
                                        )

                                        for vpce_id in vpce_ids:
                                            try:
                                                individual_response = ec2_client.describe_vpc_endpoints(
                                                    VpcEndpointIds=[vpce_id]
                                                )
                                                endpoints = individual_response.get("VpcEndpoints", [])
                                                if endpoints:
                                                    vpce_to_vpc[vpce_id] = endpoints[0]["VpcId"]
                                            except ClientError as individual_error:
                                                if (
                                                    individual_error.response["Error"]["Code"]
                                                    == "InvalidVpcEndpointId.NotFound"
                                                ):
                                                    errors.append(
                                                        f"VPCE {vpce_id} not found in AWS (deleted but still in CSV)"
                                                    )
                                                else:
                                                    errors.append(
                                                        f"Error fetching {vpce_id}: {individual_error.response['Error']['Code']}"
                                                    )
                                            finally:
                                                # Progress advance for each individual query
                                                progress.advance(task)
                                    else:
                                        # Re-raise other errors
                                        raise

                                # Update resource objects with vpc_id
                                for resource in vpce_resources:
                                    vpce_id = getattr(resource, "vpce_id", None) or getattr(resource, "id", None)
                                    if vpce_id in vpce_to_vpc:
                                        resource.vpc_id = vpce_to_vpc[vpce_id]

                                # Progress advance for batch query
                                if vpce_to_vpc:  # If batch succeeded, advance by batch size
                                    progress.advance(task, advance=len(vpce_ids))

                            except ClientError as e:
                                errors.append(
                                    f"Failed to fetch VPC IDs in {region} (profile: {profile}): {e.response['Error']['Code']}"
                                )
                                # Advance progress even on error to prevent hanging
                                progress.advance(task, advance=len(vpce_resources))
                            except Exception as e:
                                errors.append(f"Unexpected error fetching VPC IDs in {region}: {str(e)}")
                                # Advance progress even on error to prevent hanging
                                progress.advance(task, advance=len(vpce_resources))

                    except Exception as e:
                        errors.append(f"Failed to create session (profile: {profile}): {str(e)}")

        # PHASE 2: Group resources by VPC and profile for batch queries
        vpcs_by_profile: Dict[str, Dict[str, List]] = {}
        skipped_no_profile = 0
        skipped_no_vpc_id = 0
        skipped_resources: List[Dict] = []  # Track skipped resources with full details

        # Track CSV vpc_name count and duplicate VPCEs for data integrity analysis
        csv_vpc_names = set()
        vpce_to_csv_names: Dict[str, List[str]] = {}  # Track duplicate VPCEs with different vpc_names

        for resource in resources:
            profile = getattr(resource, "profile", None)
            vpc_id = getattr(resource, "vpc_id", None)
            region = getattr(resource, "region", "ap-southeast-2")
            vpce_id = getattr(resource, "vpce_id", None) or getattr(resource, "id", None) or "unknown"

            # Track CSV vpc_name for data integrity analysis
            csv_vpc_name = getattr(resource, "vpc_name", None)
            if csv_vpc_name:
                csv_vpc_names.add(csv_vpc_name)

                # Detect duplicate VPCEs with different vpc_names
                if vpce_id not in vpce_to_csv_names:
                    vpce_to_csv_names[vpce_id] = []
                if csv_vpc_name not in vpce_to_csv_names[vpce_id]:
                    vpce_to_csv_names[vpce_id].append(csv_vpc_name)

            if not profile:
                skipped_no_profile += 1
                continue

            if not vpc_id:
                skipped_no_vpc_id += 1
                # Capture full resource details for debugging
                skipped_resources.append(
                    {
                        "account_id": getattr(resource, "account_id", "unknown"),
                        "profile": profile or "unknown",
                        "vpce_id": vpce_id,
                        "vpc_name": getattr(resource, "vpc_name", "unknown"),
                        "enis": getattr(resource, "enis", "unknown"),
                        "notes": getattr(resource, "notes", "unknown"),
                        "region": region,
                    }
                )
                continue

            if profile not in vpcs_by_profile:
                vpcs_by_profile[profile] = {}

            if region not in vpcs_by_profile[profile]:
                vpcs_by_profile[profile][region] = set()

            vpcs_by_profile[profile][region].add(vpc_id)

        # Initialize result containers
        vpc_names = {}
        vpc_cidrs = {}
        vpc_resources = {}

        # Enrich VPCs by profile and region
        total_vpcs = sum(len(vpc_ids) for regions in vpcs_by_profile.values() for vpc_ids in regions.values())

        if total_vpcs > 0:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                transient=False,
            ) as progress:
                task = progress.add_task(f"Enriching {total_vpcs} VPCs...", total=total_vpcs)

                for profile, regions in vpcs_by_profile.items():
                    try:
                        session = boto3.Session(profile_name=profile)

                        for region, vpc_ids in regions.items():
                            try:
                                ec2_client = session.client("ec2", region_name=region)

                                # Batch describe VPCs
                                response = ec2_client.describe_vpcs(VpcIds=list(vpc_ids))

                                for vpc in response.get("Vpcs", []):
                                    vpc_id = vpc["VpcId"]

                                    # Extract VPC name from tags
                                    vpc_name = vpc_id  # Default to VPC ID
                                    for tag in vpc.get("Tags", []):
                                        if tag["Key"] == "Name":
                                            vpc_name = tag["Value"]
                                            break

                                    vpc_names[vpc_id] = vpc_name
                                    vpc_cidrs[vpc_id] = vpc["CidrBlock"]

                                    # Get associated resource counts if requested
                                    if include_resource_counts:
                                        vpc_resources[vpc_id] = self._get_vpc_resource_counts(
                                            ec2_client, vpc_id, errors
                                        )

                                    # Advance progress for each VPC processed
                                    progress.advance(task)

                            except ClientError as e:
                                error_code = e.response["Error"]["Code"]
                                errors.append(f"Failed to describe VPCs in {region} (profile: {profile}): {error_code}")
                                # Advance progress even on error
                                progress.advance(task, advance=len(vpc_ids))
                            except Exception as e:
                                errors.append(f"Unexpected error in {region} (profile: {profile}): {str(e)}")
                                # Advance progress even on error
                                progress.advance(task, advance=len(vpc_ids))

                    except ClientError as e:
                        error_code = e.response["Error"]["Code"]
                        errors.append(f"Failed to create session (profile: {profile}): {error_code}")
                    except Exception as e:
                        errors.append(f"Unexpected error (profile: {profile}): {str(e)}")

        # Add diagnostic errors for skipped resources
        if skipped_no_profile > 0:
            errors.append(f"Skipped {skipped_no_profile} resources with missing profile attribute")
        # Display detailed skipped resource information for debugging
        if skipped_no_vpc_id > 0 and skipped_resources:
            error_msg = (
                f"Skipped {skipped_no_vpc_id} resource{'s' if skipped_no_vpc_id > 1 else ''} "
                f"with missing vpc_id (Phase 1 VPC ID fetch may have failed)"
            )
            errors.append(error_msg)

            # Create detailed table with full resource information
            print_warning(f"\n⚠️  {error_msg}")
            print_warning("   Resource details for debugging:\n")

            skipped_table = create_table(title="Skipped Resources (Missing VPC ID)")
            skipped_table.add_column("Account ID", style="cyan")
            skipped_table.add_column("AWS-Profile", style="blue")
            skipped_table.add_column("VPCE ID", style="yellow")
            skipped_table.add_column("VPC Name (CSV)", style="magenta")
            skipped_table.add_column("ENIs", style="dim", justify="right")
            skipped_table.add_column("Notes", style="dim")
            skipped_table.add_column("Region", style="green")

            for res in skipped_resources:
                # Truncate long values for table display
                profile_display = res["profile"][:33] + ".." if len(res["profile"]) > 35 else res["profile"]
                vpc_name_display = res["vpc_name"][:28] + ".." if len(res["vpc_name"]) > 30 else res["vpc_name"]
                notes_display = res["notes"][:23] + ".." if len(res["notes"]) > 25 else res["notes"]

                skipped_table.add_row(
                    res["account_id"],
                    profile_display,
                    res["vpce_id"],
                    vpc_name_display,
                    str(res["enis"]),
                    notes_display,
                    res["region"],
                )

            console.print(skipped_table)
            print_info(
                "\n💡 Troubleshooting: Check AWS profile permissions, VPCE existence, "
                "or update CSV with correct vpc_id values\n"
            )

        # Count enriched resources
        enriched_count = sum(1 for resource in resources if getattr(resource, "vpc_id", None) in vpc_names)

        # Consolidate VPC enrichment message with optional discrepancy note
        discrepancy_count = abs(len(csv_vpc_names) - len(vpc_names))
        if discrepancy_count > 0:
            print_success(
                f"✅ Enriched {enriched_count} resources from {len(vpc_names)} VPCs ({discrepancy_count} CSV vpc_name discrepancy noted)"
            )
        else:
            print_success(f"✅ Enriched {enriched_count} resources from {len(vpc_names)} VPCs")

        # Detect and report duplicate VPCEs with conflicting vpc_names
        duplicate_vpces = {vpce: names for vpce, names in vpce_to_csv_names.items() if len(names) > 1}
        if duplicate_vpces:
            print_info(
                f"📋 CSV Metadata Reconciliation: {len(duplicate_vpces)} VPCEs with multiple vpc_name entries detected\n"
            )

            duplicate_table = create_table(title="VPCEs Requiring Metadata Reconciliation")
            duplicate_table.add_column("VPCE ID", style="yellow")
            duplicate_table.add_column("CSV vpc_name #1", style="magenta")
            duplicate_table.add_column("CSV vpc_name #2", style="magenta")
            duplicate_table.add_column("Additional Names", style="dim")

            for vpce_id, vpc_names_list in list(duplicate_vpces.items())[:10]:  # Show first 10
                name1 = vpc_names_list[0][:38] + ".." if len(vpc_names_list[0]) > 40 else vpc_names_list[0]
                name2 = vpc_names_list[1][:38] + ".." if len(vpc_names_list[1]) > 40 else vpc_names_list[1]
                additional = f"+{len(vpc_names_list) - 2} more" if len(vpc_names_list) > 2 else ""

                duplicate_table.add_row(vpce_id, name1, name2, additional)

            console.print(duplicate_table)

            if len(duplicate_vpces) > 10:
                print_info(f"   ... and {len(duplicate_vpces) - 10} more VPCEs requiring reconciliation\n")

            print_info(
                "💡 Context: This is EXPECTED behavior for VPCEs spanning multiple VPCs or duplicate CSV entries.\n"
                "   AWS API returns single vpc_id per VPCE (ground truth), reconciling CSV metadata automatically.\n"
                "   Review if same VPCE intentionally spans multiple VPCs or if CSV has duplicate entries.\n"
            )

        # Display Rich table with VPC metadata
        if vpc_names:
            self._display_vpc_table(vpc_names, vpc_cidrs, vpc_resources, resources, enriched_count)

        if errors:
            print_warning(f"⚠️  {len(errors)} enrichment errors (non-blocking):")
            for i, error in enumerate(errors, 1):
                print_warning(f"  ├─ Error {i}: {error}")

        return VPCEnrichmentResult(
            enriched_count=enriched_count,
            vpcs_discovered=len(vpc_names),
            vpc_names=vpc_names,
            vpc_cidrs=vpc_cidrs,
            vpc_resources=vpc_resources,
            errors=errors,
        )

    def _get_vpc_resource_counts(self, ec2_client, vpc_id: str, errors: List[str]) -> Dict:
        """
        Get associated resource counts for VPC.

        Args:
            ec2_client: Boto3 EC2 client
            vpc_id: VPC identifier
            errors: List to append errors to

        Returns:
            Dict with resource counts: {
                'subnets': int,
                'route_tables': int,
                'internet_gateways': int,
                'nat_gateways': int,
            }
        """
        resource_counts = {
            "subnets": 0,
            "route_tables": 0,
            "internet_gateways": 0,
            "nat_gateways": 0,
        }

        try:
            # Count subnets
            subnets_response = ec2_client.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
            resource_counts["subnets"] = len(subnets_response.get("Subnets", []))

            # Count route tables
            route_tables_response = ec2_client.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])
            resource_counts["route_tables"] = len(route_tables_response.get("RouteTables", []))

            # Count internet gateways
            igws_response = ec2_client.describe_internet_gateways(
                Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
            )
            resource_counts["internet_gateways"] = len(igws_response.get("InternetGateways", []))

            # Count NAT gateways
            nat_gws_response = ec2_client.describe_nat_gateways(
                Filters=[
                    {"Name": "vpc-id", "Values": [vpc_id]},
                    {"Name": "state", "Values": ["available"]},
                ]
            )
            resource_counts["nat_gateways"] = len(nat_gws_response.get("NatGateways", []))

        except ClientError as e:
            errors.append(f"Failed to get resource counts for {vpc_id}: {e.response['Error']['Code']}")
        except Exception as e:
            errors.append(f"Unexpected error getting resource counts for {vpc_id}: {str(e)}")

        return resource_counts

    def _display_vpc_table(
        self,
        vpc_names: Dict[str, str],
        vpc_cidrs: Dict[str, str],
        vpc_resources: Dict[str, Dict],
        resources: List,
        enriched_count: int,
    ) -> None:
        """
        Display Rich table with VPC enrichment results.

        Finops parity: Rich PyPI table by default (matches elastic_ip_optimizer.py pattern)
        """
        table = create_table(title="VPC Context Enrichment Results")
        table.add_column("VPC ID", style="cyan", no_wrap=True)
        table.add_column("VPC Name", style="green")
        table.add_column("CIDR Block", style="blue")
        table.add_column("Endpoints", style="magenta", justify="right")
        table.add_column("Subnets", style="dim", justify="right")
        table.add_column("Route Tables", style="dim", justify="right")
        table.add_column("IGWs", style="dim", justify="right")
        table.add_column("NAT GWs", style="dim", justify="right")

        # Count endpoints per VPC
        vpc_endpoint_counts = {}
        for resource in resources:
            vpc_id = getattr(resource, "vpc_id", None)
            if vpc_id in vpc_names:
                vpc_endpoint_counts[vpc_id] = vpc_endpoint_counts.get(vpc_id, 0) + 1

        # Sort by VPC name for readability
        sorted_vpcs = sorted(vpc_names.items(), key=lambda x: x[1])

        for vpc_id, vpc_name in sorted_vpcs:
            cidr = vpc_cidrs.get(vpc_id, "N/A")
            endpoint_count = vpc_endpoint_counts.get(vpc_id, 0)
            vpc_resource_counts = vpc_resources.get(vpc_id, {})

            table.add_row(
                vpc_id,
                vpc_name,
                cidr,
                str(endpoint_count),
                str(vpc_resource_counts.get("subnets", 0)),
                str(vpc_resource_counts.get("route_tables", 0)),
                str(vpc_resource_counts.get("internet_gateways", 0)),
                str(vpc_resource_counts.get("nat_gateways", 0)),
            )

        # Add TOTAL summary row (Manager requirement)
        table.add_section()  # Visual separator

        total_endpoints = sum(vpc_endpoint_counts.values())
        total_subnets = sum(vpc_resources.get(vpc_id, {}).get("subnets", 0) for vpc_id in vpc_names.keys())
        total_route_tables = sum(vpc_resources.get(vpc_id, {}).get("route_tables", 0) for vpc_id in vpc_names.keys())
        total_igws = sum(vpc_resources.get(vpc_id, {}).get("internet_gateways", 0) for vpc_id in vpc_names.keys())
        total_nat_gws = sum(vpc_resources.get(vpc_id, {}).get("nat_gateways", 0) for vpc_id in vpc_names.keys())

        table.add_row(
            "[bold cyan]TOTAL[/bold cyan]",
            f"[bold]{len(sorted_vpcs)} VPCs[/bold]",
            "",  # No CIDR for TOTAL
            f"[bold magenta]{total_endpoints}[/bold magenta]",
            f"[bold]{total_subnets}[/bold]",
            f"[bold]{total_route_tables}[/bold]",
            f"[bold]{total_igws}[/bold]",
            f"[bold]{total_nat_gws}[/bold]",
            style="bold cyan",
        )

        console.print(table)
