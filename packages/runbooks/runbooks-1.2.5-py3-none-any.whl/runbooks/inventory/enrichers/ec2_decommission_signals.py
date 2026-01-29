#!/usr/bin/env python3
"""
EC2 Decommission Signals E2-E7 Enrichment Module

This module provides comprehensive decommission signal enrichment for EC2 instances
to support cost optimization and resource rationalization initiatives.

Signal Definitions (E2-E7):
- E2 (Low Network): NetworkIn + NetworkOut < 1 Mbps average (30 days) - 10 points
- E3 (Low IOPS): VolumeReadOps + VolumeWriteOps < 100 IOPS average (30 days) - 8 points
- E4 (No ELB): Not attached to any ELB/ALB/NLB target group - 8 points
- E5 (Old Instance): LaunchTime > 365 days ago, no modifications - 6 points
- E6 (No ASG): Not member of any Auto Scaling Group - 5 points
- E7 (Dev/Test): Tags contain 'dev', 'test', 'sandbox', 'temporary' - 3 points

Scoring Framework:
- Total possible: 40 points (E2-E7 only, E1 from Compute Optimizer = 60 points)
- Combined with E1: 0-100 scale for decommission tier classification
- MUST (80-100): Immediate candidates
- SHOULD (50-79): Strong candidates
- COULD (25-49): Potential candidates
- KEEP (<25): Active resources

Integration:
- Complements compute_optimizer.py (E1 signal = 60 points)
- Feeds into decommission_scorer.py for tier classification
- Supports Feature 2 (Graviton eligibility analysis)

Unix Philosophy: Does ONE thing (E2-E7 enrichment) with CENTRALISED_OPS profile.

Usage:
    enricher = EC2DecommissionSignalEnricher(operational_profile='centralised-ops-profile')
    enriched_df = enricher.enrich_instances(discovery_df, profile='management-profile')

    # Result columns added:
    # - e2_low_network_score: 0 or 10
    # - e3_low_iops_score: 0 or 8
    # - e4_no_elb_score: 0 or 8
    # - e5_old_instance_score: 0 or 6
    # - e6_no_asg_score: 0 or 5
    # - e7_dev_test_score: 0 or 3
    # - e2_e7_total_score: Sum of E2-E7 (0-40 range)
    # - signal_details: JSON with threshold details

Author: Runbooks Team
Version: 1.0.0
Strategic Alignment: Epic 4 - $800K Graviton enabler
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from runbooks.base import CloudFoundationsBase
from runbooks.common.profile_utils import get_profile_for_operation, create_management_session
from runbooks.common.rich_utils import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar,
)

logger = logging.getLogger(__name__)


class EC2DecommissionSignalEnricher(CloudFoundationsBase):
    """
    EC2 decommission signal enrichment (E2-E7) for cost optimization.

    Enriches EC2 instance data with 6 decommission signals by calling:
    - CloudWatch GetMetricStatistics (network throughput, disk IOPS)
    - ELBv2 DescribeTargetHealth (load balancer attachments)
    - AutoScaling DescribeAutoScalingGroups (ASG membership)
    - EC2 Tags analysis (environment classification)

    Profile Isolation: Enforced via get_profile_for_operation("operational", ...)

    Attributes:
        operational_profile (str): AWS profile with EC2/CloudWatch/ELB/ASG read access
        region (str): Default region for initialization
        cloudwatch_clients (Dict[str, boto3.client]): Region-specific CloudWatch clients
        elbv2_clients (Dict[str, boto3.client]): Region-specific ELBv2 clients
        autoscaling_clients (Dict[str, boto3.client]): Region-specific AutoScaling clients
    """

    # Signal weight definitions (matches decommission_scorer.py)
    SIGNAL_WEIGHTS = {
        "E2": 10,  # Low Network
        "E3": 8,  # Low IOPS
        "E4": 8,  # No ELB
        "E5": 6,  # Old Instance
        "E6": 5,  # No ASG
        "E7": 3,  # Dev/Test
    }

    # Configurable thresholds
    E2_NETWORK_THRESHOLD_MBPS = 1.0  # 1 Mbps average
    E3_IOPS_THRESHOLD = 100  # 100 IOPS average
    E5_AGE_THRESHOLD_DAYS = 365  # 365 days
    E7_DEV_TEST_TAGS = {"dev", "test", "sandbox", "temporary", "development", "testing"}

    def __init__(self, operational_profile: str, region: str = "ap-southeast-2"):
        """
        Initialize EC2 decommission signal enricher with CENTRALISED_OPS profile.

        Args:
            operational_profile: AWS profile with EC2/CloudWatch/ELB/ASG API access
            region: AWS region for initialization (default: ap-southeast-2)
        """
        # Profile isolation enforced
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        super().__init__(profile=resolved_profile, region=region)

        self.operational_profile = resolved_profile
        self.region = region

        # Lazy initialization for service clients (per-region)
        self.cloudwatch_clients: Dict[str, any] = {}
        self.elbv2_clients: Dict[str, any] = {}
        self.autoscaling_clients: Dict[str, any] = {}

        print_success(f"EC2DecommissionSignalEnricher initialized with profile: {resolved_profile}")

    def _get_cloudwatch_client(self, region: str):
        """
        Get or create CloudWatch client for specific region (lazy initialization).

        Args:
            region: AWS region name

        Returns:
            boto3 CloudWatch client for the specified region
        """
        if region not in self.cloudwatch_clients:
            self.cloudwatch_clients[region] = self.session.client("cloudwatch", region_name=region)
            print_info(f"Initialized CloudWatch client for region: {region}")

        return self.cloudwatch_clients[region]

    def _get_elbv2_client(self, region: str):
        """
        Get or create ELBv2 client for specific region (lazy initialization).

        Args:
            region: AWS region name

        Returns:
            boto3 ELBv2 client for the specified region
        """
        if region not in self.elbv2_clients:
            self.elbv2_clients[region] = self.session.client("elbv2", region_name=region)
            print_info(f"Initialized ELBv2 client for region: {region}")

        return self.elbv2_clients[region]

    def _get_autoscaling_client(self, region: str):
        """
        Get or create AutoScaling client for specific region (lazy initialization).

        Args:
            region: AWS region name

        Returns:
            boto3 AutoScaling client for the specified region
        """
        if region not in self.autoscaling_clients:
            self.autoscaling_clients[region] = self.session.client("autoscaling", region_name=region)
            print_info(f"Initialized AutoScaling client for region: {region}")

        return self.autoscaling_clients[region]

    def _check_network_throughput(self, instance_id: str, region: str, lookback_days: int = 30) -> Dict:
        """
        Check E2 signal: Network throughput < 1 Mbps average (30 days).

        Uses CloudWatch GetMetricStatistics for NetworkIn + NetworkOut.

        Args:
            instance_id: EC2 instance ID
            region: AWS region
            lookback_days: Historical period to analyze (default: 30)

        Returns:
            Dict with signal result:
            {
                'score': 10 or 0,
                'network_in_avg_mbps': float,
                'network_out_avg_mbps': float,
                'total_avg_mbps': float,
                'threshold_mbps': 1.0,
                'triggered': bool
            }
        """
        try:
            cloudwatch = self._get_cloudwatch_client(region)

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)

            # Get NetworkIn metric
            network_in_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="NetworkIn",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily granularity
                Statistics=["Average"],
            )

            # Get NetworkOut metric
            network_out_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="NetworkOut",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily granularity
                Statistics=["Average"],
            )

            # Calculate averages (bytes to Mbps)
            network_in_bytes = [dp["Average"] for dp in network_in_response.get("Datapoints", [])]
            network_out_bytes = [dp["Average"] for dp in network_out_response.get("Datapoints", [])]

            network_in_avg_mbps = (
                (sum(network_in_bytes) / len(network_in_bytes) / 1024 / 1024 * 8) if network_in_bytes else 0
            )
            network_out_avg_mbps = (
                (sum(network_out_bytes) / len(network_out_bytes) / 1024 / 1024 * 8) if network_out_bytes else 0
            )

            total_avg_mbps = network_in_avg_mbps + network_out_avg_mbps

            triggered = total_avg_mbps < self.E2_NETWORK_THRESHOLD_MBPS

            return {
                "score": self.SIGNAL_WEIGHTS["E2"] if triggered else 0,
                "network_in_avg_mbps": network_in_avg_mbps,
                "network_out_avg_mbps": network_out_avg_mbps,
                "total_avg_mbps": total_avg_mbps,
                "threshold_mbps": self.E2_NETWORK_THRESHOLD_MBPS,
                "triggered": triggered,
            }

        except ClientError as e:
            logger.warning(f"CloudWatch network metrics error for {instance_id}: {e}")
            return {
                "score": 0,
                "network_in_avg_mbps": 0,
                "network_out_avg_mbps": 0,
                "total_avg_mbps": 0,
                "threshold_mbps": self.E2_NETWORK_THRESHOLD_MBPS,
                "triggered": False,
                "error": str(e),
            }

    def _check_ebs_activity(self, instance_id: str, region: str, lookback_days: int = 30) -> Dict:
        """
        Check E3 signal: EBS IOPS < 100 average (30 days).

        Uses CloudWatch GetMetricStatistics for VolumeReadOps + VolumeWriteOps.

        Args:
            instance_id: EC2 instance ID
            region: AWS region
            lookback_days: Historical period to analyze (default: 30)

        Returns:
            Dict with signal result:
            {
                'score': 8 or 0,
                'read_ops_avg': float,
                'write_ops_avg': float,
                'total_iops_avg': float,
                'threshold_iops': 100,
                'triggered': bool
            }
        """
        try:
            cloudwatch = self._get_cloudwatch_client(region)

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)

            # Get VolumeReadOps metric
            read_ops_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="DiskReadOps",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily granularity
                Statistics=["Average"],
            )

            # Get VolumeWriteOps metric
            write_ops_response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="DiskWriteOps",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily granularity
                Statistics=["Average"],
            )

            # Calculate averages
            read_ops = [dp["Average"] for dp in read_ops_response.get("Datapoints", [])]
            write_ops = [dp["Average"] for dp in write_ops_response.get("Datapoints", [])]

            read_ops_avg = (sum(read_ops) / len(read_ops)) if read_ops else 0
            write_ops_avg = (sum(write_ops) / len(write_ops)) if write_ops else 0

            total_iops_avg = read_ops_avg + write_ops_avg

            triggered = total_iops_avg < self.E3_IOPS_THRESHOLD

            return {
                "score": self.SIGNAL_WEIGHTS["E3"] if triggered else 0,
                "read_ops_avg": read_ops_avg,
                "write_ops_avg": write_ops_avg,
                "total_iops_avg": total_iops_avg,
                "threshold_iops": self.E3_IOPS_THRESHOLD,
                "triggered": triggered,
            }

        except ClientError as e:
            logger.warning(f"CloudWatch disk metrics error for {instance_id}: {e}")
            return {
                "score": 0,
                "read_ops_avg": 0,
                "write_ops_avg": 0,
                "total_iops_avg": 0,
                "threshold_iops": self.E3_IOPS_THRESHOLD,
                "triggered": False,
                "error": str(e),
            }

    def _check_load_balancer(self, instance_id: str, region: str) -> Dict:
        """
        Check E4 signal: Not attached to any ELB/ALB/NLB target group.

        Uses ELBv2 DescribeTargetHealth to check all load balancers.

        Args:
            instance_id: EC2 instance ID
            region: AWS region

        Returns:
            Dict with signal result:
            {
                'score': 8 or 0,
                'attached_to_elb': bool,
                'target_groups': List[str],
                'triggered': bool
            }
        """
        try:
            elbv2 = self._get_elbv2_client(region)

            # Get all target groups
            target_groups_response = elbv2.describe_target_groups()
            target_groups = target_groups_response.get("TargetGroups", [])

            attached_target_groups = []

            # Check each target group for this instance
            for tg in target_groups:
                tg_arn = tg["TargetGroupArn"]

                try:
                    health_response = elbv2.describe_target_health(TargetGroupArn=tg_arn)

                    targets = health_response.get("TargetHealthDescriptions", [])

                    # Check if instance is in this target group
                    for target in targets:
                        if target.get("Target", {}).get("Id") == instance_id:
                            attached_target_groups.append(tg_arn)
                            break

                except ClientError:
                    # Target group might not be accessible, skip
                    continue

            attached_to_elb = len(attached_target_groups) > 0
            triggered = not attached_to_elb

            return {
                "score": self.SIGNAL_WEIGHTS["E4"] if triggered else 0,
                "attached_to_elb": attached_to_elb,
                "target_groups": attached_target_groups,
                "triggered": triggered,
            }

        except ClientError as e:
            logger.warning(f"ELBv2 attachment check error for {instance_id}: {e}")
            return {"score": 0, "attached_to_elb": False, "target_groups": [], "triggered": False, "error": str(e)}

    def _check_instance_age(self, launch_time: str) -> Dict:
        """
        Check E5 signal: Instance age > 365 days.

        Args:
            launch_time: Instance launch time (ISO format string or datetime)

        Returns:
            Dict with signal result:
            {
                'score': 6 or 0,
                'age_days': int,
                'threshold_days': 365,
                'triggered': bool
            }
        """
        try:
            # Parse launch time
            if isinstance(launch_time, str):
                # Try multiple datetime formats
                if "T" in launch_time:
                    # ISO format with timezone
                    launch_dt = datetime.fromisoformat(launch_time.replace("Z", "+00:00"))
                else:
                    # Simple format
                    launch_dt = datetime.strptime(launch_time, "%Y-%m-%d %H:%M:%S")
            else:
                launch_dt = launch_time

            age_days = (datetime.utcnow().replace(tzinfo=launch_dt.tzinfo) - launch_dt).days
            triggered = age_days > self.E5_AGE_THRESHOLD_DAYS

            return {
                "score": self.SIGNAL_WEIGHTS["E5"] if triggered else 0,
                "age_days": age_days,
                "threshold_days": self.E5_AGE_THRESHOLD_DAYS,
                "triggered": triggered,
            }

        except Exception as e:
            logger.warning(f"Instance age calculation error: {e}")
            return {
                "score": 0,
                "age_days": 0,
                "threshold_days": self.E5_AGE_THRESHOLD_DAYS,
                "triggered": False,
                "error": str(e),
            }

    def _check_autoscaling(self, instance_id: str, region: str) -> Dict:
        """
        Check E6 signal: Not member of any Auto Scaling Group.

        Uses AutoScaling DescribeAutoScalingGroups.

        Args:
            instance_id: EC2 instance ID
            region: AWS region

        Returns:
            Dict with signal result:
            {
                'score': 5 or 0,
                'in_asg': bool,
                'asg_name': str or None,
                'triggered': bool
            }
        """
        try:
            autoscaling = self._get_autoscaling_client(region)

            # Describe all ASGs (paginated)
            paginator = autoscaling.get_paginator("describe_auto_scaling_groups")

            for page in paginator.paginate():
                asgs = page.get("AutoScalingGroups", [])

                for asg in asgs:
                    asg_name = asg.get("AutoScalingGroupName")
                    instances = asg.get("Instances", [])

                    # Check if instance is in this ASG
                    for instance in instances:
                        if instance.get("InstanceId") == instance_id:
                            return {"score": 0, "in_asg": True, "asg_name": asg_name, "triggered": False}

            # Instance not found in any ASG
            return {"score": self.SIGNAL_WEIGHTS["E6"], "in_asg": False, "asg_name": None, "triggered": True}

        except ClientError as e:
            logger.warning(f"AutoScaling membership check error for {instance_id}: {e}")
            return {"score": 0, "in_asg": False, "asg_name": None, "triggered": False, "error": str(e)}

    def _check_tags(self, tags: Dict[str, str]) -> Dict:
        """
        Check E7 signal: Tags contain dev/test environment patterns.

        Args:
            tags: Dictionary of instance tags {key: value}

        Returns:
            Dict with signal result:
            {
                'score': 3 or 0,
                'dev_test_tags_found': List[str],
                'triggered': bool
            }
        """
        try:
            dev_test_tags_found = []

            # Check all tag keys and values for dev/test patterns
            for key, value in tags.items():
                key_lower = key.lower()
                value_lower = str(value).lower()

                # Check if any dev/test keyword matches
                for keyword in self.E7_DEV_TEST_TAGS:
                    if keyword in key_lower or keyword in value_lower:
                        dev_test_tags_found.append(f"{key}={value}")
                        break

            triggered = len(dev_test_tags_found) > 0

            return {
                "score": self.SIGNAL_WEIGHTS["E7"] if triggered else 0,
                "dev_test_tags_found": dev_test_tags_found,
                "triggered": triggered,
            }

        except Exception as e:
            logger.warning(f"Tag analysis error: {e}")
            return {"score": 0, "dev_test_tags_found": [], "triggered": False, "error": str(e)}

    def _calculate_signals(self, row: pd.Series) -> Dict:
        """
        Calculate all E2-E7 signals for a single EC2 instance.

        Args:
            row: pandas Series with instance data (must include: resource_id, region, launch_time, tags)

        Returns:
            Dict with all signal results:
            {
                'E2': {...},
                'E3': {...},
                'E4': {...},
                'E5': {...},
                'E6': {...},
                'E7': {...},
                'total_score': int (0-40),
                'triggered_signals': List[str]
            }
        """
        instance_id = row.get("resource_id")
        region = row.get("region")
        launch_time = row.get("launch_time")

        # Parse tags (might be JSON string or dict)
        tags_raw = row.get("tags", {})
        if isinstance(tags_raw, str):
            try:
                tags = json.loads(tags_raw)
            except:
                tags = {}
        else:
            tags = tags_raw if isinstance(tags_raw, dict) else {}

        signals = {}
        total_score = 0
        triggered_signals = []

        # E2: Network throughput
        e2_result = self._check_network_throughput(instance_id, region)
        signals["E2"] = e2_result
        total_score += e2_result["score"]
        if e2_result["triggered"]:
            triggered_signals.append("E2")

        # E3: EBS activity
        e3_result = self._check_ebs_activity(instance_id, region)
        signals["E3"] = e3_result
        total_score += e3_result["score"]
        if e3_result["triggered"]:
            triggered_signals.append("E3")

        # E4: Load balancer
        e4_result = self._check_load_balancer(instance_id, region)
        signals["E4"] = e4_result
        total_score += e4_result["score"]
        if e4_result["triggered"]:
            triggered_signals.append("E4")

        # E5: Instance age
        e5_result = self._check_instance_age(launch_time)
        signals["E5"] = e5_result
        total_score += e5_result["score"]
        if e5_result["triggered"]:
            triggered_signals.append("E5")

        # E6: Auto Scaling
        e6_result = self._check_autoscaling(instance_id, region)
        signals["E6"] = e6_result
        total_score += e6_result["score"]
        if e6_result["triggered"]:
            triggered_signals.append("E6")

        # E7: Dev/Test tags
        e7_result = self._check_tags(tags)
        signals["E7"] = e7_result
        total_score += e7_result["score"]
        if e7_result["triggered"]:
            triggered_signals.append("E7")

        return {**signals, "total_score": total_score, "triggered_signals": triggered_signals}

    def _assess_graviton_eligibility(self, row: pd.Series, signals: Dict) -> Dict:
        """
        Assess Graviton migration eligibility based on decommission signals.

        Integration with Feature 2 (Graviton Analyzer):
        - High decommission score (E2-E7 ≥ 25) → Consider decommissioning instead
        - Low decommission score (E2-E7 < 25) → Good Graviton candidate

        Args:
            row: pandas Series with instance data
            signals: Dictionary with calculated E2-E7 signals

        Returns:
            Dict with Graviton eligibility assessment:
            {
                'graviton_eligible': bool,
                'recommendation': str,
                'reason': str
            }
        """
        total_score = signals["total_score"]
        instance_type = row.get("instance_type", "unknown")
        architecture = row.get("architecture", "unknown")

        # Already ARM-based
        if architecture == "arm64":
            return {
                "graviton_eligible": False,
                "recommendation": "Already ARM-based",
                "reason": "Instance already running on Graviton architecture",
            }

        # High decommission signals → prioritize decommissioning
        if total_score >= 25:
            return {
                "graviton_eligible": False,
                "recommendation": "Consider decommissioning",
                "reason": f"High decommission score ({total_score}/40) suggests resource underutilization",
            }

        # Low decommission signals → good Graviton candidate
        return {
            "graviton_eligible": True,
            "recommendation": "Strong Graviton candidate",
            "reason": f"Low decommission score ({total_score}/40) indicates active workload suitable for migration",
        }

    def enrich_instances(self, df: pd.DataFrame, profile: Optional[str] = None) -> pd.DataFrame:
        """
        Add E2-E7 decommission signal columns to EC2 instances DataFrame.

        Args:
            df: DataFrame with EC2 instances (must include: resource_id, region, launch_time, tags)
            profile: Optional AWS profile override (uses operational_profile if not specified)

        Returns:
            DataFrame with added columns:
            - e2_low_network_score: 0 or 10
            - e3_low_iops_score: 0 or 8
            - e4_no_elb_score: 0 or 8
            - e5_old_instance_score: 0 or 6
            - e6_no_asg_score: 0 or 5
            - e7_dev_test_score: 0 or 3
            - e2_e7_total_score: Sum of E2-E7 (0-40 range)
            - signal_details: JSON with detailed signal information
            - graviton_eligible: bool (integration with Feature 2)
            - graviton_recommendation: str

        Raises:
            ValueError: If input DataFrame missing required columns

        Example:
            >>> from runbooks.inventory.enrichers.ec2_decommission_signals import EC2DecommissionSignalEnricher
            >>> enricher = EC2DecommissionSignalEnricher('centralised-ops-profile')
            >>> enriched_df = enricher.enrich_instances(discovery_df)
            >>> enriched_df.to_excel('ec2-with-decommission-signals.xlsx', index=False)
        """
        # Validate required columns
        required_columns = ["resource_id", "region"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print_error(f"Input DataFrame missing required columns: {missing_columns}")
            raise ValueError(f"Required columns missing: {missing_columns}")

        print_info(f"Enriching {len(df)} EC2 instances with E2-E7 decommission signals")

        # Initialize signal columns
        signal_columns = {
            "e2_low_network_score": 0,
            "e3_low_iops_score": 0,
            "e4_no_elb_score": 0,
            "e5_old_instance_score": 0,
            "e6_no_asg_score": 0,
            "e7_dev_test_score": 0,
            "e2_e7_total_score": 0,
            "signal_details": "{}",
            "graviton_eligible": False,
            "graviton_recommendation": "N/A",
        }

        for col, default in signal_columns.items():
            df[col] = default

        enriched_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Calculating E2-E7 signals...", total=len(df))

            for idx, row in df.iterrows():
                try:
                    # Calculate all signals
                    signals = self._calculate_signals(row)

                    # Populate signal score columns
                    df.at[idx, "e2_low_network_score"] = signals["E2"]["score"]
                    df.at[idx, "e3_low_iops_score"] = signals["E3"]["score"]
                    df.at[idx, "e4_no_elb_score"] = signals["E4"]["score"]
                    df.at[idx, "e5_old_instance_score"] = signals["E5"]["score"]
                    df.at[idx, "e6_no_asg_score"] = signals["E6"]["score"]
                    df.at[idx, "e7_dev_test_score"] = signals["E7"]["score"]
                    df.at[idx, "e2_e7_total_score"] = signals["total_score"]

                    # Store detailed signal information as JSON
                    df.at[idx, "signal_details"] = json.dumps(
                        {
                            "E2": signals["E2"],
                            "E3": signals["E3"],
                            "E4": signals["E4"],
                            "E5": signals["E5"],
                            "E6": signals["E6"],
                            "E7": signals["E7"],
                            "triggered_signals": signals["triggered_signals"],
                        }
                    )

                    # Graviton eligibility assessment (Feature 2 integration)
                    graviton_assessment = self._assess_graviton_eligibility(row, signals)
                    df.at[idx, "graviton_eligible"] = graviton_assessment["graviton_eligible"]
                    df.at[idx, "graviton_recommendation"] = graviton_assessment["recommendation"]

                    enriched_count += 1

                except Exception as e:
                    instance_id = row.get("resource_id", "unknown")
                    print_warning(f"Signal calculation failed for {instance_id}: {e}")
                    logger.error(f"Signal enrichment error for {instance_id}: {e}", exc_info=True)

                progress.update(task, advance=1)

        print_success(f"E2-E7 signal enrichment complete: {enriched_count}/{len(df)} instances processed")

        # Display summary statistics
        self._display_signal_summary(df)

        return df

    def _display_signal_summary(self, df: pd.DataFrame) -> None:
        """
        Display summary statistics for E2-E7 signals.

        Args:
            df: DataFrame with E2-E7 signal columns
        """
        try:
            from runbooks.common.rich_utils import create_table

            # Calculate signal trigger counts
            signal_stats = []

            for signal_id in ["E2", "E3", "E4", "E5", "E6", "E7"]:
                col_name = f"e{signal_id[1]}_{'low_network' if signal_id == 'E2' else 'low_iops' if signal_id == 'E3' else 'no_elb' if signal_id == 'E4' else 'old_instance' if signal_id == 'E5' else 'no_asg' if signal_id == 'E6' else 'dev_test'}_score"

                triggered_count = len(df[df[col_name] > 0])
                triggered_pct = (triggered_count / len(df) * 100) if len(df) > 0 else 0

                signal_stats.append(
                    [signal_id, str(self.SIGNAL_WEIGHTS[signal_id]), str(triggered_count), f"{triggered_pct:.1f}%"]
                )

            table = create_table("E2-E7 Signal Summary", ["Signal", "Weight", "Triggered", "Percentage"], signal_stats)
            console.print(table)

            # Total score distribution
            avg_score = df["e2_e7_total_score"].mean()
            max_score = df["e2_e7_total_score"].max()

            print_info(f"Average E2-E7 score: {avg_score:.1f}/40")
            print_info(f"Maximum E2-E7 score: {max_score:.0f}/40")

            # Graviton eligibility count
            graviton_eligible_count = len(df[df["graviton_eligible"] == True])
            graviton_pct = (graviton_eligible_count / len(df) * 100) if len(df) > 0 else 0
            print_info(f"Graviton eligible instances: {graviton_eligible_count} ({graviton_pct:.1f}%)")

        except Exception as e:
            print_warning(f"Summary display failed: {e}")
            logger.error(f"Summary display error: {e}", exc_info=True)

    def run(self):
        """
        Run method required by CloudFoundationsBase.

        For EC2DecommissionSignalEnricher, this returns initialization status.
        Primary usage is via enrich_instances() method.

        Returns:
            CloudFoundationsResult with initialization status
        """
        from runbooks.base import CloudFoundationsResult
        from datetime import datetime

        return CloudFoundationsResult(
            timestamp=datetime.now(),
            success=True,
            message=f"EC2DecommissionSignalEnricher initialized with profile: {self.operational_profile}",
            data={
                "operational_profile": self.operational_profile,
                "region": self.region,
                "signal_weights": self.SIGNAL_WEIGHTS,
                "thresholds": {
                    "E2_network_mbps": self.E2_NETWORK_THRESHOLD_MBPS,
                    "E3_iops": self.E3_IOPS_THRESHOLD,
                    "E5_age_days": self.E5_AGE_THRESHOLD_DAYS,
                },
            },
        )
