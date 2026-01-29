#!/usr/bin/env python3
"""
EC2 Operational Metadata Enrichment - CENTRALISED_OPS Profile Single Responsibility

Adds 15 EC2 operational columns to any EC2 instance discovery data:

CRITICAL (5):
- instance_state (running/stopped/terminated from State.Name)
- instance_type (m5.large, t3.medium from InstanceType)
- vpc_id (from VpcId)
- subnet_id (from SubnetId)
- availability_zone (from Placement.AvailabilityZone)

NETWORKING (4):
- security_groups (comma-separated list from SecurityGroups)
- public_ip (from PublicIpAddress)
- private_ip (from PrivateIpAddress)
- network_interfaces_count (len(NetworkInterfaces))

OPERATIONAL (6):
- launch_time (ISO timestamp from LaunchTime)
- monitoring_state (from Monitoring.State)
- iam_instance_profile (from IamInstanceProfile.Arn)
- architecture (x86_64, arm64 from Architecture)
- virtualization_type (hvm, paravirtual from VirtualizationType)
- platform (Windows, Linux from Platform)

Unix Philosophy: Does ONE thing (EC2 enrichment) with ONE profile (CENTRALISED_OPS).

Usage:
    enricher = EC2Enricher(operational_profile='centralised-ops-profile')
    enriched_df = enricher.enrich_dataframe(discovery_df)
"""

import pandas as pd
from typing import Dict, List, Optional
from botocore.exceptions import ClientError

from runbooks.base import CloudFoundationsBase
from runbooks.common.profile_utils import get_profile_for_operation
from runbooks.common.rich_utils import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar,
)


class EC2Enricher(CloudFoundationsBase):
    """
    EC2 operational metadata enrichment (CENTRALISED_OPS_PROFILE).

    Enriches EC2 instance discovery data with 15 operational columns by calling
    EC2 describe-instances API per region.

    Profile Isolation: Enforced via get_profile_for_operation("operational", ...)

    Attributes:
        operational_profile (str): AWS profile with EC2 read access
        region (str): Default region for initialization
        ec2_clients (Dict[str, boto3.client]): Region-specific EC2 clients (lazy initialization)
    """

    def __init__(self, operational_profile: str, region: str = "ap-southeast-2"):
        """
        Initialize EC2 enricher with CENTRALISED_OPS profile.

        Args:
            operational_profile: AWS profile with EC2 API access
            region: AWS region for initialization (default: ap-southeast-2)
        """
        # Profile isolation enforced
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        super().__init__(profile=resolved_profile, region=region)

        self.operational_profile = resolved_profile
        self.region = region

        # Lazy initialization for EC2 clients (per-region)
        self.ec2_clients: Dict[str, any] = {}

        print_success(f"EC2Enricher initialized with profile: {resolved_profile}")

    def _get_ec2_client(self, region: str):
        """
        Get or create EC2 client for specific region (lazy initialization).

        Args:
            region: AWS region name

        Returns:
            boto3 EC2 client for the specified region
        """
        if region not in self.ec2_clients:
            self.ec2_clients[region] = self.session.client("ec2", region_name=region)
            print_info(f"Initialized EC2 client for region: {region}")

        return self.ec2_clients[region]

    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 15 EC2 operational columns to resource discovery data.

        Args:
            df: DataFrame with 'resource_id' (instance ID) and 'region' columns

        Returns:
            DataFrame with added EC2 columns:
            CRITICAL: instance_state, instance_type, vpc_id, subnet_id, availability_zone
            NETWORKING: security_groups, public_ip, private_ip, network_interfaces_count
            OPERATIONAL: launch_time, monitoring_state, iam_instance_profile, architecture,
                        virtualization_type, platform

        Raises:
            ValueError: If input DataFrame missing required columns

        Example:
            >>> discovery_df = pd.read_csv('/tmp/organizations-enhanced.csv')
            >>> enricher = EC2Enricher('centralised-ops-profile')
            >>> enriched_df = enricher.enrich_dataframe(discovery_df)
            >>> enriched_df.to_csv('/tmp/ec2-enriched.csv', index=False)
        """
        # Validate required columns
        required_columns = ["resource_id", "region"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print_error(f"Input DataFrame missing required columns: {missing_columns}")
            raise ValueError(f"Required columns missing: {missing_columns}")

        print_info(f"Enriching {len(df)} EC2 instances with operational metadata")

        # Initialize 15 EC2 columns with 'N/A' defaults
        ec2_columns = {
            # CRITICAL (5)
            "instance_state": "N/A",
            "instance_type": "N/A",
            "vpc_id": "N/A",
            "subnet_id": "N/A",
            "availability_zone": "N/A",
            # NETWORKING (4)
            "security_groups": "N/A",
            "public_ip": "N/A",
            "private_ip": "N/A",
            "network_interfaces_count": "N/A",
            # OPERATIONAL (6)
            "launch_time": "N/A",
            "monitoring_state": "N/A",
            "iam_instance_profile": "N/A",
            "architecture": "N/A",
            "virtualization_type": "N/A",
            "platform": "N/A",
        }

        for col, default in ec2_columns.items():
            df[col] = default

        # Batch enrichment by region for API efficiency
        regions = df["region"].unique()
        print_info(f"Processing {len(regions)} region(s): {', '.join(regions)}")

        enriched_count = 0
        terminated_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Enriching with EC2 metadata...", total=len(df))

            for region in regions:
                region_df = df[df["region"] == region]
                instance_ids = region_df["resource_id"].tolist()

                print_info(f"Region {region}: Enriching {len(instance_ids)} instances")

                try:
                    # EC2 describe-instances API call
                    ec2_client = self._get_ec2_client(region)
                    response = ec2_client.describe_instances(InstanceIds=instance_ids)

                    # Create instance lookup dict for fast access
                    instance_lookup = {}
                    for reservation in response["Reservations"]:
                        for instance in reservation["Instances"]:
                            instance_lookup[instance["InstanceId"]] = instance

                    # Enrich each row in this region
                    for idx, row in region_df.iterrows():
                        instance_id = row["resource_id"]

                        if instance_id in instance_lookup:
                            instance = instance_lookup[instance_id]

                            # CRITICAL (5)
                            df.at[idx, "instance_state"] = instance.get("State", {}).get("Name", "N/A")
                            df.at[idx, "instance_type"] = instance.get("InstanceType", "N/A")
                            df.at[idx, "vpc_id"] = instance.get("VpcId", "N/A")
                            df.at[idx, "subnet_id"] = instance.get("SubnetId", "N/A")
                            df.at[idx, "availability_zone"] = instance.get("Placement", {}).get(
                                "AvailabilityZone", "N/A"
                            )

                            # NETWORKING (4)
                            # Security groups: comma-separated list of group IDs
                            security_groups = instance.get("SecurityGroups", [])
                            sg_list = [sg.get("GroupId", "") for sg in security_groups if sg.get("GroupId")]
                            df.at[idx, "security_groups"] = ",".join(sg_list) if sg_list else "N/A"

                            df.at[idx, "public_ip"] = instance.get("PublicIpAddress", "N/A")
                            df.at[idx, "private_ip"] = instance.get("PrivateIpAddress", "N/A")

                            network_interfaces = instance.get("NetworkInterfaces", [])
                            df.at[idx, "network_interfaces_count"] = str(len(network_interfaces))

                            # OPERATIONAL (6)
                            launch_time = instance.get("LaunchTime", "N/A")
                            df.at[idx, "launch_time"] = str(launch_time) if launch_time != "N/A" else "N/A"

                            df.at[idx, "monitoring_state"] = instance.get("Monitoring", {}).get("State", "N/A")

                            iam_profile = instance.get("IamInstanceProfile", {}).get("Arn", "N/A")
                            df.at[idx, "iam_instance_profile"] = iam_profile

                            df.at[idx, "architecture"] = instance.get("Architecture", "N/A")
                            df.at[idx, "virtualization_type"] = instance.get("VirtualizationType", "N/A")
                            df.at[idx, "platform"] = instance.get(
                                "Platform", "Linux"
                            )  # Default to Linux if not Windows

                            enriched_count += 1
                        else:
                            # Instance not found in API response (likely terminated)
                            print_warning(f"Instance {instance_id} not found in region {region} (likely terminated)")
                            df.at[idx, "instance_state"] = "TERMINATED"
                            terminated_count += 1

                        progress.update(task, advance=1)

                except ClientError as e:
                    error_code = e.response["Error"]["Code"]

                    if error_code == "InvalidInstanceID.NotFound":
                        # Handle batch error - mark all instances as potentially terminated
                        print_warning(f"Region {region}: Some instances not found (batch error)")

                        for idx, row in region_df.iterrows():
                            instance_id = row["resource_id"]
                            # Try individual instance lookup
                            try:
                                individual_response = ec2_client.describe_instances(InstanceIds=[instance_id])

                                if individual_response["Reservations"]:
                                    instance = individual_response["Reservations"][0]["Instances"][0]

                                    # Same enrichment logic as batch processing
                                    # CRITICAL (5)
                                    df.at[idx, "instance_state"] = instance.get("State", {}).get("Name", "N/A")
                                    df.at[idx, "instance_type"] = instance.get("InstanceType", "N/A")
                                    df.at[idx, "vpc_id"] = instance.get("VpcId", "N/A")
                                    df.at[idx, "subnet_id"] = instance.get("SubnetId", "N/A")
                                    df.at[idx, "availability_zone"] = instance.get("Placement", {}).get(
                                        "AvailabilityZone", "N/A"
                                    )

                                    # NETWORKING (4)
                                    security_groups = instance.get("SecurityGroups", [])
                                    sg_list = [sg.get("GroupId", "") for sg in security_groups if sg.get("GroupId")]
                                    df.at[idx, "security_groups"] = ",".join(sg_list) if sg_list else "N/A"

                                    df.at[idx, "public_ip"] = instance.get("PublicIpAddress", "N/A")
                                    df.at[idx, "private_ip"] = instance.get("PrivateIpAddress", "N/A")

                                    network_interfaces = instance.get("NetworkInterfaces", [])
                                    df.at[idx, "network_interfaces_count"] = str(len(network_interfaces))

                                    # OPERATIONAL (6)
                                    launch_time = instance.get("LaunchTime", "N/A")
                                    df.at[idx, "launch_time"] = str(launch_time) if launch_time != "N/A" else "N/A"

                                    df.at[idx, "monitoring_state"] = instance.get("Monitoring", {}).get("State", "N/A")

                                    iam_profile = instance.get("IamInstanceProfile", {}).get("Arn", "N/A")
                                    df.at[idx, "iam_instance_profile"] = iam_profile

                                    df.at[idx, "architecture"] = instance.get("Architecture", "N/A")
                                    df.at[idx, "virtualization_type"] = instance.get("VirtualizationType", "N/A")
                                    df.at[idx, "platform"] = instance.get("Platform", "Linux")

                                    enriched_count += 1

                            except ClientError as individual_error:
                                if individual_error.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
                                    print_warning(f"Instance {instance_id} not found (terminated)")
                                    df.at[idx, "instance_state"] = "TERMINATED"
                                    terminated_count += 1
                                else:
                                    print_error(f"Error enriching instance {instance_id}: {individual_error}")

                            progress.update(task, advance=1)

                    else:
                        print_error(f"Region {region} EC2 API error: {error_code} - {e}")
                        # Continue with next region
                        for idx, row in region_df.iterrows():
                            progress.update(task, advance=1)

        print_success(f"EC2 enrichment complete: {enriched_count}/{len(df)} instances enriched")
        if terminated_count > 0:
            print_warning(f"Terminated instances detected: {terminated_count} (graceful degradation applied)")

        return df

    def run(self):
        """
        Run method required by CloudFoundationsBase.

        For EC2Enricher, this returns initialization status.
        Primary usage is via enrich_dataframe() method.

        Returns:
            CloudFoundationsResult with initialization status
        """
        from runbooks.base import CloudFoundationsResult
        from datetime import datetime

        return CloudFoundationsResult(
            timestamp=datetime.now(),
            success=True,
            message=f"EC2Enricher initialized with profile: {self.operational_profile}",
            data={
                "operational_profile": self.operational_profile,
                "region": self.region,
                "ec2_clients_initialized": len(self.ec2_clients),
            },
        )
