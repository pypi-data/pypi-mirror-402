#!/usr/bin/env python3
"""
VPC Endpoint Sharing & Consolidation Module

This module provides VPC endpoint sharing across accounts to reduce costs by
consolidating duplicate interface endpoints while maintaining service connectivity.

Part of CloudOps-Runbooks VPC optimization framework supporting:
- Centralized endpoint service creation
- Private Hosted Zone (PHZ) management
- Resource Access Manager (RAM) sharing
- Cost consolidation based on percentage targets (configurable via .env)

Author: Runbooks Team
Version: 1.1.x
"""

import json
from datetime import datetime
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


class EndpointSharingService:
    """
    Implement VPC endpoint sharing across accounts for cost optimization.

    This class provides systematic VPC endpoint consolidation including:
    - Centralized shared endpoint creation
    - Private Hosted Zone (PHZ) setup for DNS resolution
    - Resource Access Manager (RAM) sharing configuration
    - Cost optimization tracking and validation

    Attributes:
        central_vpc_id: Central VPC ID for shared endpoints
        region: AWS region for operations
        profile: AWS profile name for authentication
        console: Rich console for beautiful CLI output
    """

    # AWS services commonly accessed via VPC endpoints
    COMMON_SERVICES = [
        "s3",  # S3 (Gateway endpoint - free)
        "dynamodb",  # DynamoDB (Gateway endpoint - free)
        "ec2",  # EC2 API
        "ssm",  # Systems Manager
        "secretsmanager",  # Secrets Manager
        "kms",  # Key Management Service
        "lambda",  # Lambda
        "rds",  # RDS
        "ecs",  # Elastic Container Service
        "ecr.dkr",  # ECR Docker
        "ecr.api",  # ECR API
        "logs",  # CloudWatch Logs
        "monitoring",  # CloudWatch Monitoring
        "sns",  # Simple Notification Service
        "sqs",  # Simple Queue Service
    ]

    def __init__(
        self,
        central_vpc_id: str,
        region: str = "ap-southeast-2",
        profile: Optional[str] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize VPC endpoint sharing service.

        Args:
            central_vpc_id: Central VPC ID for hosting shared endpoints
            region: AWS region (default: ap-southeast-2)
            profile: AWS profile name for authentication
            console: Rich console for output (auto-created if not provided)
        """
        self.central_vpc_id = central_vpc_id
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
        self.route53 = session.client("route53", region_name=self.region)
        self.ram = session.client("ram", region_name=self.region)

        # Initialize pricing config for dynamic cost calculations (NO hardcoding)
        self.pricing_config = get_pricing_config(profile=self.profile, region=self.region)

    def create_shared_endpoints(
        self,
        services: Optional[List[str]] = None,
        subnet_ids: Optional[List[str]] = None,
        security_group_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create centralized shared VPC endpoints.

        Creates interface VPC endpoints in the central VPC for specified AWS services.
        These endpoints can then be shared across multiple accounts and VPCs.

        Args:
            services: List of service names (default: COMMON_SERVICES)
            subnet_ids: Subnet IDs for endpoint placement
            security_group_id: Security group ID for endpoint access control

        Returns:
            List of created endpoint dictionaries

        Example:
            >>> sharer = EndpointSharingService("vpc-central123", profile="prod")
            >>> endpoints = sharer.create_shared_endpoints(
            ...     services=["s3", "ec2", "ssm"],
            ...     subnet_ids=["subnet-xxx", "subnet-yyy"],
            ...     security_group_id="sg-endpoints"
            ... )
            >>> print(f"Created {len(endpoints)} shared endpoints")
        """
        print_header("VPC Endpoint Sharing Setup", version="1.1.x")
        print_info(f"Central VPC: {self.central_vpc_id}")
        print_info(f"Region: {self.region}")

        services = services or self.COMMON_SERVICES
        endpoints_created = []

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Creating shared endpoints...", total=len(services))

            for service_name in services:
                try:
                    # Build full service name
                    full_service_name = f"com.amazonaws.{self.region}.{service_name}"

                    # Check if endpoint already exists
                    existing = self.ec2.describe_vpc_endpoints(
                        Filters=[
                            {"Name": "vpc-id", "Values": [self.central_vpc_id]},
                            {"Name": "service-name", "Values": [full_service_name]},
                        ]
                    )["VpcEndpoints"]

                    if existing:
                        print_warning(f"Endpoint already exists for {service_name}")
                        endpoints_created.append(existing[0])
                        progress.update(task, advance=1)
                        continue

                    # Determine endpoint type (Gateway vs Interface)
                    endpoint_type = "Gateway" if service_name in ["s3", "dynamodb"] else "Interface"

                    # Create endpoint configuration
                    endpoint_config = {
                        "VpcId": self.central_vpc_id,
                        "ServiceName": full_service_name,
                        "TagSpecifications": [
                            {
                                "ResourceType": "vpc-endpoint",
                                "Tags": [
                                    {"Key": "Name", "Value": f"shared-{service_name}"},
                                    {"Key": "Shared", "Value": "true"},
                                    {"Key": "CostCenter", "Value": "network-optimization"},
                                ],
                            }
                        ],
                    }

                    # Add Interface endpoint specific configuration
                    if endpoint_type == "Interface":
                        if subnet_ids:
                            endpoint_config["SubnetIds"] = subnet_ids
                        if security_group_id:
                            endpoint_config["SecurityGroupIds"] = [security_group_id]
                        endpoint_config["PrivateDnsEnabled"] = False  # We'll use PHZ instead

                    # Create endpoint
                    response = self.ec2.create_vpc_endpoint(**endpoint_config)
                    endpoint = response["VpcEndpoint"]

                    endpoints_created.append(endpoint)
                    print_success(f"Created {endpoint_type} endpoint: {service_name}")

                except ClientError as e:
                    print_error(f"Failed to create endpoint for {service_name}", e)

                progress.update(task, advance=1)

        # Display summary
        self._display_endpoints_summary(endpoints_created)

        print_success(f"Created {len(endpoints_created)} shared endpoints")

        return endpoints_created

    def create_private_hosted_zones(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create Private Hosted Zones for endpoint DNS resolution.

        Creates PHZ records to enable DNS resolution of shared endpoints
        across multiple VPCs and accounts.

        Args:
            endpoints: List of endpoint dictionaries from create_shared_endpoints()

        Returns:
            List of created hosted zone dictionaries
        """
        print_info("Creating Private Hosted Zones for endpoint sharing")

        hosted_zones = []

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Creating PHZs...", total=len(endpoints))

            for endpoint in endpoints:
                try:
                    service_name = endpoint["ServiceName"]
                    endpoint_id = endpoint["VpcEndpointId"]

                    # Skip if no DNS entries (Gateway endpoints)
                    if not endpoint.get("DnsEntries"):
                        print_warning(f"No DNS entries for {service_name} - skipping PHZ")
                        progress.update(task, advance=1)
                        continue

                    dns_name = endpoint["DnsEntries"][0]["DnsName"]
                    hosted_zone_id = endpoint["DnsEntries"][0].get("HostedZoneId")

                    # Create Private Hosted Zone
                    phz_response = self.route53.create_hosted_zone(
                        Name=f"{service_name}.internal",
                        VPC={"VPCRegion": self.region, "VPCId": self.central_vpc_id},
                        CallerReference=f"shared-endpoint-{endpoint_id}-{datetime.now().timestamp()}",
                        HostedZoneConfig={"Comment": f"Shared endpoint PHZ for {service_name}", "PrivateZone": True},
                    )

                    phz_id = phz_response["HostedZone"]["Id"]

                    # Create alias record
                    self.route53.change_resource_record_sets(
                        HostedZoneId=phz_id,
                        ChangeBatch={
                            "Changes": [
                                {
                                    "Action": "CREATE",
                                    "ResourceRecordSet": {
                                        "Name": f"{service_name}.internal",
                                        "Type": "A",
                                        "AliasTarget": {
                                            "HostedZoneId": hosted_zone_id,
                                            "DNSName": dns_name,
                                            "EvaluateTargetHealth": False,
                                        },
                                    },
                                }
                            ]
                        },
                    )

                    hosted_zones.append({"service": service_name, "phz_id": phz_id, "dns_name": dns_name})

                    print_success(f"Created PHZ for {service_name}")

                except ClientError as e:
                    print_error(f"Failed to create PHZ for {service_name}", e)

                progress.update(task, advance=1)

        print_success(f"Created {len(hosted_zones)} Private Hosted Zones")

        return hosted_zones

    def share_with_accounts(
        self, target_account_ids: List[str], endpoint_arns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Share VPC endpoints with other accounts via Resource Access Manager.

        Args:
            target_account_ids: List of AWS account IDs to share with
            endpoint_arns: Optional list of specific endpoint ARNs to share

        Returns:
            Resource share configuration dictionary
        """
        print_info(f"Sharing endpoints with {len(target_account_ids)} accounts")

        try:
            # Get current account ID
            sts = boto3.client("sts")
            current_account = sts.get_caller_identity()["Account"]

            # Build resource ARNs if not provided
            if not endpoint_arns:
                endpoint_arns = [
                    f"arn:aws:ec2:{self.region}:{current_account}:vpc-endpoint/*"  # Share all endpoints
                ]

            # Create resource share
            response = self.ram.create_resource_share(
                name="shared-vpc-endpoints",
                resourceArns=endpoint_arns,
                principals=target_account_ids,
                tags=[
                    {"key": "Purpose", "value": "endpoint-sharing"},
                    {"key": "CostCenter", "value": "network-optimization"},
                ],
            )

            resource_share = response["resourceShare"]

            print_success(f"Resource share created: {resource_share['resourceShareArn']}")

            return resource_share

        except ClientError as e:
            print_error("Failed to create resource share", e)
            raise

    def calculate_endpoint_savings(self, current_endpoint_count: int, target_endpoint_count: int) -> Dict[str, float]:
        """
        Calculate cost savings from endpoint consolidation.

        Uses dynamic pricing from AWS Pricing API (NO hardcoded costs).

        Args:
            current_endpoint_count: Current number of interface endpoints
            target_endpoint_count: Target number after consolidation

        Returns:
            Dictionary with cost savings breakdown
        """
        # Get dynamic pricing from AWS Pricing API (NO hardcoded $7.20)
        interface_endpoint_cost = self.pricing_config.get_vpc_endpoint_interface_monthly_cost(self.region)

        current_monthly_cost = current_endpoint_count * interface_endpoint_cost
        target_monthly_cost = target_endpoint_count * interface_endpoint_cost

        monthly_savings = current_monthly_cost - target_monthly_cost
        annual_savings = monthly_savings * 12

        return {
            "current_monthly_cost": current_monthly_cost,
            "target_monthly_cost": target_monthly_cost,
            "monthly_savings": monthly_savings,
            "annual_savings": annual_savings,
            "reduction_percentage": (monthly_savings / current_monthly_cost * 100) if current_monthly_cost > 0 else 0,
            "endpoints_consolidated": current_endpoint_count - target_endpoint_count,
            "interface_endpoint_cost_monthly": interface_endpoint_cost,
        }

    def _display_endpoints_summary(self, endpoints: List[Dict[str, Any]]) -> None:
        """Display endpoints summary in Rich table format."""
        table = create_table(title="Shared VPC Endpoints", box_style="ROUNDED")
        table.add_column("Service", style="cyan")
        table.add_column("Endpoint ID", style="bright_blue")
        table.add_column("Type", style="bright_green")
        table.add_column("State", style="bright_yellow")

        for endpoint in endpoints:
            service = endpoint["ServiceName"].split(".")[-1]
            endpoint_type = endpoint.get("VpcEndpointType", "Interface")
            state = endpoint.get("State", "pending")

            table.add_row(service, endpoint["VpcEndpointId"], endpoint_type, state)

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")


# CLI Integration Example
if __name__ == "__main__":
    import sys

    # Simple CLI for standalone execution
    central_vpc = sys.argv[1] if len(sys.argv) > 1 else "vpc-central123456"
    profile = sys.argv[2] if len(sys.argv) > 2 else "default"

    sharer = EndpointSharingService(central_vpc, profile=profile)

    # Example: Create shared endpoints
    print("\n📦 Creating shared VPC endpoints...")
    endpoints = sharer.create_shared_endpoints(services=["s3", "ec2", "ssm", "secretsmanager"])

    # Example: Discover current endpoints and calculate savings
    existing_endpoints = sharer.ec2.describe_vpc_endpoints()["VpcEndpoints"]
    interface_endpoints = [e for e in existing_endpoints if e.get("VpcEndpointType") == "Interface"]

    current_count = len(interface_endpoints)
    # Target: 30% reduction via consolidation
    target_count = int(current_count * 0.70)

    savings = sharer.calculate_endpoint_savings(
        current_endpoint_count=current_count, target_endpoint_count=target_count
    )

    print(f"\n💰 Cost Optimization Results:")
    print(f"Current endpoints: {current_count}")
    print(f"Target endpoints: {target_count} (30% reduction)")
    print(f"Monthly savings: ${savings['monthly_savings']:.2f}")
    print(f"Annual savings: ${savings['annual_savings']:.2f}")
    print(f"Reduction: {savings['reduction_percentage']:.1f}%")
    print(f"\n✅ Endpoint sharing setup complete!")
