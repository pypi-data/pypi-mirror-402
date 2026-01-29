#!/usr/bin/env python3
"""
Service Attachment Enricher - Cross-Service Dependency Detection for EC2

This module detects EC2 instances attached to critical AWS services:
- ELBv2 Target Groups (ALB/NLB)
- Auto Scaling Groups
- ECS Container Instances
- EKS Worker Nodes (Phase 2 deferral)

Decommission Scoring Framework:
- Signal E5 (No Service Attachments): 6 points (instance not attached to any service)
- API calls: DescribeTargetHealth, DescribeAutoScalingInstances, DescribeContainerInstances
- Graceful IAM fallback: If permission denied → score=0 (conservative)

Pattern: Follows proven enricher pattern (ssm_integration.py, compute_optimizer.py)

Usage:
    from runbooks.finops.service_attachment_enricher import get_service_attachments

    # Check service attachments for instances
    attachments = get_service_attachments(
        instance_ids=['i-abc123', 'i-def456'],
        profile='operational-profile',
        region='ap-southeast-2'
    )

    # Returns: {
    #     'i-abc123': {
    #         'score': 6,
    #         'is_in_target_group': False,
    #         'target_group_arns': [],
    #         'is_in_asg': False,
    #         'asg_name': None,
    #         'is_ecs_instance': False,
    #         'ecs_cluster': None,
    #         'is_eks_node': 'PHASE_2',  # Deferred to Phase 2
    #         'service_attachments_summary': 'No attachments detected',
    #         'attachment_count': 0
    #     },
    #     'i-def456': {
    #         'score': 0,
    #         'is_in_target_group': True,
    #         'target_group_arns': ['arn:aws:elasticloadbalancing:...'],
    #         'is_in_asg': True,
    #         'asg_name': 'prod-web-asg',
    #         'is_ecs_instance': False,
    #         'ecs_cluster': None,
    #         'is_eks_node': 'PHASE_2',
    #         'service_attachments_summary': 'ALB + ASG',
    #         'attachment_count': 2
    #     }
    # }

Strategic Alignment:
- Objective 1 (runbooks package): Critical service dependency detection
- Enterprise SDLC: Evidence-based decommission safety with audit trails
- KISS/DRY/LEAN: Reuse boto3 patterns, graceful IAM fallback, modular design
"""

import logging
import os
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..common.rich_utils import (
    console,
    create_progress_bar,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


def get_service_attachments(
    instance_ids: List[str],
    profile: Optional[str] = None,
    region: str = "ap-southeast-2",
    enable_expensive_signals: bool = False,
) -> Dict[str, Dict]:
    """
    Detect EC2 instances attached to critical AWS services.

    Queries 4 AWS service APIs to identify service dependencies:
    1. ELBv2: DescribeTargetHealth → Check target group registrations
    2. Auto Scaling: DescribeAutoScalingInstances → Check ASG membership
    3. ECS: DescribeContainerInstances → Check ECS container instances
    4. EKS: Phase 2 deferral (complex node group detection)

    Signal E5: No Service Attachments (6 points)
    - Indicates instance not attached to load balancer, ASG, or container orchestration
    - Safe decommission candidate if no attachments detected
    - Complements Compute Optimizer idle signal (E1)

    IAM Permissions Required:
    - elasticloadbalancing:DescribeTargetHealth
    - autoscaling:DescribeAutoScalingInstances
    - ecs:DescribeContainerInstances
    - ecs:ListClusters

    Graceful Fallback:
    - If IAM permission denied → log warning, set column='UNKNOWN', score=0
    - If API unavailable → same conservative fallback
    - Prevents scoring failure due to permission issues

    Args:
        instance_ids: List of EC2 instance IDs to check
        profile: AWS profile name (default: $OPERATIONAL_PROFILE or $AWS_PROFILE)
        region: AWS region (default: ap-southeast-2)
        enable_expensive_signals: If False, skip E5 enrichment (returns score=0)

    Returns:
        Dictionary mapping instance IDs to service attachment data:
        {
            'i-abc123': {
                'score': 6,  # 6 if no attachments, 0 if any attachment exists
                'is_in_target_group': False,
                'target_group_arns': [],
                'is_in_asg': False,
                'asg_name': None,
                'is_ecs_instance': False,
                'ecs_cluster': None,
                'is_eks_node': 'PHASE_2',
                'service_attachments_summary': 'No attachments detected',
                'attachment_count': 0
            }
        }

    Example:
        >>> attachments = get_service_attachments(
        ...     instance_ids=['i-abc123'],
        ...     profile='operational',
        ...     region='ap-southeast-2',
        ...     enable_expensive_signals=True
        ... )
        >>> if attachments['i-abc123']['score'] == 6:
        ...     print("Safe to decommission (no service attachments)")
    """
    if not enable_expensive_signals:
        print_info("⏭️  E5 service attachment enrichment SKIPPED (enable_expensive_signals=False)")
        # Return default scores without API calls
        return {
            instance_id: {
                "score": 0,
                "is_in_target_group": "SKIPPED",
                "target_group_arns": [],
                "is_in_asg": "SKIPPED",
                "asg_name": None,
                "is_ecs_instance": "SKIPPED",
                "ecs_cluster": None,
                "is_eks_node": "PHASE_2",
                "service_attachments_summary": "Skipped (expensive signal disabled)",
                "attachment_count": 0,
            }
            for instance_id in instance_ids
        }

    try:
        # Profile cascade: param > $OPERATIONAL_PROFILE > $AWS_PROFILE
        if not profile:
            profile = os.environ.get("OPERATIONAL_PROFILE") or os.environ.get("AWS_PROFILE")
            if profile:
                print_info(f"Using profile from environment: {profile}")

        print_info(f"🔍 Detecting service attachments for {len(instance_ids)} instances...")

        from runbooks.common.profile_utils import create_operational_session, create_timeout_protected_client

        session = create_operational_session(profile)
        elbv2_client = create_timeout_protected_client(session, "elbv2", region)
        asg_client = create_timeout_protected_client(session, "autoscaling", region)
        ecs_client = create_timeout_protected_client(session, "ecs", region)

        # Initialize results
        results = {}
        for instance_id in instance_ids:
            results[instance_id] = {
                "score": 6,  # Default: assume no attachments (will be updated if found)
                "is_in_target_group": False,
                "target_group_arns": [],
                "is_in_asg": False,
                "asg_name": None,
                "is_ecs_instance": False,
                "ecs_cluster": None,
                "is_eks_node": "PHASE_2",  # Deferred to Phase 2
                "service_attachments_summary": "No attachments detected",
                "attachment_count": 0,
            }

        # Step 1: Check ELBv2 Target Group registrations
        print_info("   API 1/4: Checking ELBv2 target groups...")
        try:
            _check_elbv2_attachments(elbv2_client, instance_ids, results, region)
        except ClientError as e:
            if e.response["Error"]["Code"] in ["AccessDenied", "UnauthorizedOperation"]:
                print_warning(f"⚠️  ELBv2 API permission denied: {e.response['Error']['Message']}")
                print_info("   Setting is_in_target_group='UNKNOWN' (conservative fallback)")
                for instance_id in instance_ids:
                    results[instance_id]["is_in_target_group"] = "UNKNOWN"
            else:
                raise

        # Step 2: Check Auto Scaling Group membership
        print_info("   API 2/4: Checking Auto Scaling Groups...")
        try:
            _check_asg_attachments(asg_client, instance_ids, results)
        except ClientError as e:
            if e.response["Error"]["Code"] in ["AccessDenied", "UnauthorizedOperation"]:
                print_warning(f"⚠️  Auto Scaling API permission denied: {e.response['Error']['Message']}")
                print_info("   Setting is_in_asg='UNKNOWN' (conservative fallback)")
                for instance_id in instance_ids:
                    results[instance_id]["is_in_asg"] = "UNKNOWN"
            else:
                raise

        # Step 3: Check ECS container instances
        print_info("   API 3/4: Checking ECS container instances...")
        try:
            _check_ecs_attachments(ecs_client, instance_ids, results, region)
        except ClientError as e:
            if e.response["Error"]["Code"] in ["AccessDenied", "UnauthorizedOperation"]:
                print_warning(f"⚠️  ECS API permission denied: {e.response['Error']['Message']}")
                print_info("   Setting is_ecs_instance='UNKNOWN' (conservative fallback)")
                for instance_id in instance_ids:
                    results[instance_id]["is_ecs_instance"] = "UNKNOWN"
            else:
                raise

        # Step 4: EKS node detection (Phase 2 deferral)
        print_info("   API 4/4: EKS node detection DEFERRED (Phase 2)")

        # Finalize scores and summaries
        for instance_id, data in results.items():
            # Build summary
            attachments = []
            if data["is_in_target_group"] is True:
                attachments.append("ALB/NLB")
            if data["is_in_asg"] is True:
                attachments.append("ASG")
            if data["is_ecs_instance"] is True:
                attachments.append("ECS")

            data["attachment_count"] = len(attachments)

            if attachments:
                data["service_attachments_summary"] = " + ".join(attachments)
                data["score"] = 0  # Has attachments → no decommission points
            elif "UNKNOWN" in [data["is_in_target_group"], data["is_in_asg"], data["is_ecs_instance"]]:
                data["service_attachments_summary"] = "Unknown (IAM permission required)"
                data["score"] = 0  # Conservative: assume attached if unknown
            else:
                data["service_attachments_summary"] = "No attachments detected"
                data["score"] = 6  # No attachments → +6 decommission points

        # Summary statistics
        attached_count = sum(1 for d in results.values() if d["attachment_count"] > 0)
        detached_count = sum(1 for d in results.values() if d["score"] == 6)
        unknown_count = len(results) - attached_count - detached_count

        print_success(f"✅ Service attachment detection complete:")
        print_info(f"   Attached: {attached_count} | Detached: {detached_count} | Unknown: {unknown_count}")

        return results

    except Exception as e:
        print_error(f"❌ Service attachment detection failed: {e}")
        logger.error(f"Service attachment error: {e}", exc_info=True)
        # Return default scores (conservative fallback)
        return {
            instance_id: {
                "score": 0,  # Conservative: assume attached if error
                "is_in_target_group": "ERROR",
                "target_group_arns": [],
                "is_in_asg": "ERROR",
                "asg_name": None,
                "is_ecs_instance": "ERROR",
                "ecs_cluster": None,
                "is_eks_node": "PHASE_2",
                "service_attachments_summary": f"Error: {str(e)}",
                "attachment_count": 0,
            }
            for instance_id in instance_ids
        }


def _check_elbv2_attachments(elbv2_client, instance_ids: List[str], results: Dict[str, Dict], region: str) -> None:
    """
    Check if instances are registered in ELBv2 target groups.

    Strategy: Query all target groups, then check target health for each.
    Note: This is expensive (N+1 queries), but required for accurate detection.
    """
    try:
        # Get all target groups in region
        paginator = elbv2_client.get_paginator("describe_target_groups")
        target_groups = []

        for page in paginator.paginate():
            target_groups.extend(page["TargetGroups"])

        if not target_groups:
            print_info(f"   No ELBv2 target groups found in {region}")
            return

        print_info(f"   Checking {len(target_groups)} target groups for instance registrations...")

        # Check each target group for instance registrations
        for tg in target_groups:
            tg_arn = tg["TargetGroupArn"]

            try:
                response = elbv2_client.describe_target_health(TargetGroupArn=tg_arn)

                for target in response["TargetHealthDescriptions"]:
                    target_id = target["Target"]["Id"]

                    if target_id in results:
                        results[target_id]["is_in_target_group"] = True
                        results[target_id]["target_group_arns"].append(tg_arn)

            except ClientError as e:
                logger.debug(f"Failed to check target group {tg_arn}: {e}")
                continue

    except Exception as e:
        logger.error(f"ELBv2 attachment check failed: {e}", exc_info=True)
        raise


def _check_asg_attachments(asg_client, instance_ids: List[str], results: Dict[str, Dict]) -> None:
    """
    Check if instances are members of Auto Scaling Groups.

    API: DescribeAutoScalingInstances with InstanceIds filter.
    Note: This API supports batch filtering, more efficient than ELBv2.
    """
    try:
        # Batch query ASG instances (supports up to 50 instance IDs)
        batch_size = 50

        for i in range(0, len(instance_ids), batch_size):
            batch = instance_ids[i : i + batch_size]

            response = asg_client.describe_auto_scaling_instances(InstanceIds=batch)

            for asg_instance in response["AutoScalingInstances"]:
                instance_id = asg_instance["InstanceId"]

                if instance_id in results:
                    results[instance_id]["is_in_asg"] = True
                    results[instance_id]["asg_name"] = asg_instance["AutoScalingGroupName"]

    except Exception as e:
        logger.error(f"ASG attachment check failed: {e}", exc_info=True)
        raise


def _check_ecs_attachments(ecs_client, instance_ids: List[str], results: Dict[str, Dict], region: str) -> None:
    """
    Check if instances are ECS container instances.

    Strategy:
    1. List all ECS clusters
    2. For each cluster, list container instances
    3. Describe container instances to get EC2 instance IDs
    4. Match against input instance_ids

    Note: This is expensive (O(clusters × container_instances)), but required.
    """
    try:
        # Step 1: List all ECS clusters
        cluster_paginator = ecs_client.get_paginator("list_clusters")
        cluster_arns = []

        for page in cluster_paginator.paginate():
            cluster_arns.extend(page["clusterArns"])

        if not cluster_arns:
            print_info(f"   No ECS clusters found in {region}")
            return

        print_info(f"   Checking {len(cluster_arns)} ECS clusters for container instances...")

        # Step 2: For each cluster, check container instances
        for cluster_arn in cluster_arns:
            try:
                # List container instances in cluster
                container_paginator = ecs_client.get_paginator("list_container_instances")
                container_instance_arns = []

                for page in container_paginator.paginate(cluster=cluster_arn):
                    container_instance_arns.extend(page["containerInstanceArns"])

                if not container_instance_arns:
                    continue

                # Describe container instances to get EC2 instance IDs
                # Note: DescribeContainerInstances supports up to 100 ARNs per call
                batch_size = 100

                for i in range(0, len(container_instance_arns), batch_size):
                    batch = container_instance_arns[i : i + batch_size]

                    response = ecs_client.describe_container_instances(cluster=cluster_arn, containerInstances=batch)

                    for container_instance in response["containerInstances"]:
                        ec2_instance_id = container_instance["ec2InstanceId"]

                        if ec2_instance_id in results:
                            results[ec2_instance_id]["is_ecs_instance"] = True
                            # Extract cluster name from ARN (arn:aws:ecs:region:account:cluster/name)
                            cluster_name = cluster_arn.split("/")[-1]
                            results[ec2_instance_id]["ecs_cluster"] = cluster_name

            except ClientError as e:
                logger.debug(f"Failed to check ECS cluster {cluster_arn}: {e}")
                continue

    except Exception as e:
        logger.error(f"ECS attachment check failed: {e}", exc_info=True)
        raise
