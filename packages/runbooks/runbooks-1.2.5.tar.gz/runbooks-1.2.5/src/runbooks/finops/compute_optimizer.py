#!/usr/bin/env python3
"""
Compute Optimizer Integration - AWS Compute Optimizer API for EC2 Right-Sizing

This module provides integration with AWS Compute Optimizer to identify
idle EC2 instances based on utilization patterns over 14+ days.

Decommission Scoring Framework:
- Signal E1 (Compute Optimizer Idle): 60 points (max CPU ≤1% over 14 days)
- API: describe_ec2_instance_recommendations with finding="Idle"
- Profile cascade: param > $MANAGEMENT_PROFILE > $AWS_PROFILE

Pattern: Follows base_enrichers.py pattern (Rich CLI, error handling, boto3 integration)

Usage:
    from runbooks.finops.compute_optimizer import get_ec2_idle_recommendations

    # Get idle instance recommendations
    idle_instances = get_ec2_idle_recommendations(
        profile='management-profile',
        region='ap-southeast-2'
    )

    # Returns: {
    #     'i-abc123': {
    #         'score': 60,
    #         'finding': 'Idle',
    #         'reason': 'Max CPU: 0.5% over 14 days',
    #         'lookback_days': 14,
    #         'current_type': 't3.medium',
    #         'recommended_action': 'Terminate or stop'
    #     }
    # }

Strategic Alignment:
- Objective 1 (runbooks package): Reusable decommission analysis for notebooks
- Enterprise SDLC: Evidence-based right-sizing with audit trails
- KISS/DRY/LEAN: Reuse boto3 patterns, enhance existing enrichers
"""

import logging
import os
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..common.rich_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
    create_progress_bar,
)

logger = logging.getLogger(__name__)


def get_ec2_idle_recommendations(
    profile: Optional[str] = None, region: str = "ap-southeast-2", max_results: int = 1000, verbose: bool = False
) -> Dict[str, Dict]:
    """
    Get EC2 idle instance recommendations from Compute Optimizer.

    Queries AWS Compute Optimizer API for instances with finding="Idle"
    based on 14-day utilization analysis. Idle instances have max CPU ≤1%
    over the lookback period.

    Signal E1: Compute Optimizer Idle (60 points)
    - Highest priority signal for decommission scoring
    - Indicates consistently underutilized instances
    - Reliable 14-day historical analysis

    Args:
        profile: AWS profile name (default: $MANAGEMENT_PROFILE or $AWS_PROFILE)
        region: AWS region (default: ap-southeast-2)
        max_results: Maximum results per page (default: 1000)

    Returns:
        Dictionary mapping instance IDs to recommendation details:
        {
            'i-abc123': {
                'score': 60,
                'finding': 'Idle',
                'reason': 'Max CPU: 0.5% over 14 days',
                'lookback_days': 14,
                'current_type': 't3.medium',
                'recommended_action': 'Terminate or stop',
                'utilization_metrics': {
                    'cpu_max': 0.5,
                    'cpu_p99': 0.3,
                    'network_max': 10.0,
                    'memory_max': 15.0  # If available
                }
            }
        }

    Raises:
        ClientError: AWS API errors (AccessDenied, ServiceUnavailable, etc.)
        Exception: Unexpected errors with comprehensive logging

    Example:
        >>> idle = get_ec2_idle_recommendations(profile='management')
        >>> print(f"Found {len(idle)} idle instances")
        >>> for instance_id, rec in idle.items():
        ...     print(f"{instance_id}: {rec['reason']}")

    Profile Cascade:
        1. profile parameter (explicit)
        2. $MANAGEMENT_PROFILE environment variable
        3. $AWS_PROFILE environment variable
        4. 'default' AWS profile
    """
    try:
        from runbooks.common.profile_utils import (
            create_management_session,
            create_timeout_protected_client,
            get_profile_for_operation,
        )

        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        profile = get_profile_for_operation(
            operation_type="management", user_specified_profile=profile, silent=not verbose
        )

        # Debug details (show only in verbose mode)
        if verbose:
            print_info(f"🔍 Querying Compute Optimizer for idle EC2 instances (profile: {profile}, region: {region})")

        # Initialize Compute Optimizer client using standardized helper
        session = create_management_session(profile)
        co_client = create_timeout_protected_client(session, "compute-optimizer", region)

        # Query for EC2 instance recommendations
        idle_instances = {}
        next_token = None
        page_count = 0

        # Idle threshold: Max CPU ≤1% over 14+ days (AWS standard)
        IDLE_CPU_THRESHOLD = 1.0

        with create_progress_bar() as progress:
            task = progress.add_task(
                "[cyan]Fetching Compute Optimizer recommendations...",
                total=None,  # Indeterminate progress
            )

            while True:
                page_count += 1

                # API call with pagination
                # Note: Compute Optimizer doesn't have an "Idle" finding value
                # We retrieve all recommendations and filter for low utilization later
                params = {"maxResults": max_results}

                if next_token:
                    params["nextToken"] = next_token

                try:
                    response = co_client.get_ec2_instance_recommendations(**params)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    if error_code == "AccessDeniedException":
                        print_error(f"❌ Access denied to Compute Optimizer API")
                        print_warning(
                            f"   Required IAM permission: compute-optimizer:DescribeEC2InstanceRecommendations"
                        )
                        print_info(f"   Current profile: {profile}")
                        return {}
                    elif error_code == "OptInRequiredException":
                        print_error(f"❌ Compute Optimizer not enabled for this account")
                        print_warning(f"   Enable Compute Optimizer: https://console.aws.amazon.com/compute-optimizer/")
                        return {}
                    else:
                        raise

                # Process recommendations
                recommendations = response.get("instanceRecommendations", [])

                for rec in recommendations:
                    instance_arn = rec.get("instanceArn", "")
                    # Extract instance ID from ARN: arn:aws:ec2:region:account:instance/i-xxxxx
                    instance_id = instance_arn.split("/")[-1] if "/" in instance_arn else instance_arn

                    finding = rec.get("finding", "Unknown")
                    current_type = rec.get("currentInstanceType", "Unknown")

                    # Extract utilization metrics
                    utilization = rec.get("utilizationMetrics", [])
                    cpu_max = 0.0
                    cpu_p99 = 0.0
                    network_max = 0.0
                    memory_max = 0.0

                    for metric in utilization:
                        metric_name = metric.get("name", "")
                        metric_value = metric.get("statistic", "MAXIMUM")
                        value = float(metric.get("value", 0.0))

                        if metric_name == "CPU" and metric_value == "MAXIMUM":
                            cpu_max = value
                        elif metric_name == "CPU" and metric_value == "P99":
                            cpu_p99 = value
                        elif metric_name == "NETWORK_IN_BYTES_PER_SECOND" and metric_value == "MAXIMUM":
                            network_max = value / (1024 * 1024)  # Convert to MB/s
                        elif metric_name == "MEMORY" and metric_value == "MAXIMUM":
                            memory_max = value

                    # Determine lookback period (default: 14 days for Compute Optimizer)
                    lookback_days = rec.get("lookBackPeriodInDays", 14)

                    # v1.1.31 BUG FIX: Return ALL instances with original AWS Compute Optimizer findings
                    # Previously: Skipped instances with CPU > 1%, discarding "Under-provisioned" findings
                    # Now: Return all findings (Optimized, Under-provisioned, Over-provisioned, Idle)

                    # Calculate E1 score based on finding type
                    # - Idle (CPU ≤1%): 60 pts (decommission candidate)
                    # - Under-provisioned: 0 pts (needs upsize, not decommission)
                    # - Over-provisioned: 0 pts (potential rightsizing, not decommission)
                    # - Optimized: 0 pts (correctly sized)
                    is_idle = cpu_max <= IDLE_CPU_THRESHOLD
                    if is_idle:
                        finding = "Idle"  # Override to Idle for very low CPU instances
                        e1_score = 60
                        recommended_action = "Terminate or stop"
                    else:
                        # Preserve original AWS finding
                        e1_score = 0  # Not a decommission candidate
                        if finding == "UNDER_PROVISIONED":
                            finding = "Under-provisioned"
                            recommended_action = "Upsize instance"
                        elif finding == "OVER_PROVISIONED":
                            finding = "Over-provisioned"
                            recommended_action = "Downsize instance"
                        else:
                            # Optimized or Unknown
                            recommended_action = "No action needed"

                    # Build recommendation record for ALL instances
                    idle_instances[instance_id] = {
                        "score": e1_score,
                        "finding": finding,  # Original AWS finding preserved
                        "reason": f"Max CPU: {cpu_max:.1f}% over {lookback_days} days",
                        "lookback_days": lookback_days,
                        "current_type": current_type,
                        "recommended_action": recommended_action,
                        "utilization_metrics": {
                            "cpu_max": cpu_max,
                            "cpu_p99": cpu_p99,
                            "network_max": network_max,
                            "memory_max": memory_max,
                        },
                    }

                    progress.update(task, advance=0.1)  # Visual progress feedback

                # Check for more pages
                next_token = response.get("nextToken")
                if not next_token:
                    break

        idle_count = len(idle_instances)

        # Consolidated completion message (business value only)
        if not verbose:
            # Compact: 1 line with essential result
            if idle_count > 0:
                print_success(f"✅ Compute Optimizer: {idle_count} idle instances")
            else:
                print_success(f"✅ Compute Optimizer: 0 idle instances")
        else:
            # Verbose: detailed breakdown
            if idle_count > 0:
                print_success(f"✅ Compute Optimizer analysis complete: {idle_count} idle instances identified")
                print_info(f"   Idle threshold: Max CPU ≤1% over 14+ days")
            else:
                print_info(f"ℹ️  No idle instances found by Compute Optimizer")
                print_info(f"   Check: Compute Optimizer enabled + 14-day data collection complete")

        return idle_instances

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print_error(f"❌ Compute Optimizer API error: {error_code}")
        print_warning(f"   Error details: {e}")
        logger.error(f"Compute Optimizer API error: {e}", exc_info=True)
        return {}
    except Exception as e:
        print_error(f"❌ Compute Optimizer query failed: {e}")
        logger.error(f"Compute Optimizer error: {e}", exc_info=True)
        return {}


def enrich_dataframe_with_compute_optimizer(
    df, instance_id_column: str = "Instance ID", profile: Optional[str] = None, region: str = "ap-southeast-2"
):
    """
    Enrich DataFrame with Compute Optimizer idle recommendations.

    Adds 5 columns to DataFrame:
    - co_idle_score: Signal E1 score (60 if idle, 0 otherwise)
    - co_finding: Compute Optimizer finding ('Idle', 'N/A')
    - co_reason: Explanation of finding
    - co_cpu_max: Maximum CPU utilization (%)
    - co_lookback_days: Analysis period (typically 14 days)

    Args:
        df: pandas DataFrame with EC2 instance IDs
        instance_id_column: Column containing instance IDs (default: 'Instance ID')
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        Enriched DataFrame with Compute Optimizer signals

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'Instance ID': ['i-abc', 'i-def']})
        >>> enriched = enrich_dataframe_with_compute_optimizer(df, profile='management')
        >>> print(enriched[['Instance ID', 'co_idle_score', 'co_finding']])
    """
    import pandas as pd

    try:
        print_info(f"🔍 Enriching DataFrame with Compute Optimizer recommendations...")

        # Get idle recommendations
        idle_instances = get_ec2_idle_recommendations(profile=profile, region=region)

        # Initialize new columns
        df["co_idle_score"] = 0
        df["co_finding"] = "N/A"
        df["co_reason"] = "Not analyzed"
        df["co_cpu_max"] = 0.0
        df["co_lookback_days"] = 0

        enriched_count = 0

        # Enrich rows
        for idx, row in df.iterrows():
            instance_id = str(row.get(instance_id_column, "")).strip()

            if instance_id in idle_instances:
                rec = idle_instances[instance_id]

                df.at[idx, "co_idle_score"] = rec["score"]
                df.at[idx, "co_finding"] = rec["finding"]
                df.at[idx, "co_reason"] = rec["reason"]
                df.at[idx, "co_cpu_max"] = rec["utilization_metrics"]["cpu_max"]
                df.at[idx, "co_lookback_days"] = rec["lookback_days"]

                enriched_count += 1

        print_success(f"✅ Compute Optimizer enrichment complete: {enriched_count}/{len(df)} instances analyzed")

        return df

    except Exception as e:
        print_error(f"❌ Compute Optimizer enrichment failed: {e}")
        logger.error(f"Compute Optimizer enrichment error: {e}", exc_info=True)
        return df


def enrich_dataframe_with_all_signals(
    df,
    instance_id_column: str = "Instance ID",
    management_profile: Optional[str] = None,
    operational_profile: Optional[str] = None,
    region: str = "ap-southeast-2",
    include_graviton_analysis: bool = True,
):
    """
    Enrich DataFrame with complete E1-E7 decommission signals.

    This is the comprehensive enrichment function that combines:
    - E1: Compute Optimizer idle (60 points) - from this module
    - E2-E7: Activity signals (40 points) - from ec2_decommission_signals enricher

    Adds 15+ columns to DataFrame:
    - E1 columns (5): co_idle_score, co_finding, co_reason, co_cpu_max, co_lookback_days
    - E2-E7 columns (9): e2_low_network_score, e3_low_iops_score, e4_no_elb_score,
                         e5_old_instance_score, e6_no_asg_score, e7_dev_test_score,
                         e2_e7_total_score, signal_details
    - Combined columns (2): total_decommission_score (E1+E2-E7, 0-100), decommission_tier
    - Graviton columns (2): graviton_eligible, graviton_recommendation

    Args:
        df: pandas DataFrame with EC2 instance IDs
        instance_id_column: Column containing instance IDs (default: 'Instance ID')
        management_profile: AWS profile for Compute Optimizer (E1)
        operational_profile: AWS profile for CloudWatch/ELB/ASG (E2-E7)
        region: AWS region (default: ap-southeast-2)
        include_graviton_analysis: Include Graviton eligibility assessment (default: True)

    Returns:
        Enriched DataFrame with complete E1-E7 signals

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'Instance ID': ['i-abc', 'i-def'], 'region': ['ap-southeast-2', 'ap-southeast-2']})
        >>> enriched = enrich_dataframe_with_all_signals(
        ...     df,
        ...     management_profile='management',
        ...     operational_profile='centralised-ops'
        ... )
        >>> print(enriched[['Instance ID', 'total_decommission_score', 'decommission_tier']])

    Integration:
        - Feature 2 (Graviton): Uses E2-E7 score to filter decommission candidates
        - Feature 4 (Decommission): Complete E1-E7 scoring for tier classification
        - Notebooks: Single enrichment call for all signals
    """
    import pandas as pd

    try:
        print_info(f"🔍 Enriching DataFrame with complete E1-E7 decommission signals...")

        # Step 1: E1 enrichment (Compute Optimizer)
        print_info(f"   Step 1/3: E1 signal (Compute Optimizer)...")
        df = enrich_dataframe_with_compute_optimizer(
            df, instance_id_column=instance_id_column, profile=management_profile, region=region
        )

        # Step 2: E2-E7 enrichment (Activity signals)
        print_info(f"   Step 2/3: E2-E7 signals (Network, IOPS, ELB, Age, ASG, Tags)...")

        # Import EC2DecommissionSignalEnricher
        from ..inventory.enrichers.ec2_decommission_signals import EC2DecommissionSignalEnricher
        from runbooks.common.profile_utils import get_profile_for_operation

        # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
        operational_profile = get_profile_for_operation(
            operation_type="operational", user_specified_profile=operational_profile, silent=True
        )

        signal_enricher = EC2DecommissionSignalEnricher(operational_profile=operational_profile, region=region)

        # Map column name to 'resource_id' expected by enricher
        df_copy = df.copy()
        df_copy["resource_id"] = df_copy[instance_id_column]

        # Enrich with E2-E7
        df_enriched = signal_enricher.enrich_instances(df_copy, profile=operational_profile)

        # Copy E2-E7 columns back to original DataFrame
        e2_e7_columns = [
            "e2_low_network_score",
            "e3_low_iops_score",
            "e4_no_elb_score",
            "e5_old_instance_score",
            "e6_no_asg_score",
            "e7_dev_test_score",
            "e2_e7_total_score",
            "signal_details",
        ]

        if include_graviton_analysis:
            e2_e7_columns.extend(["graviton_eligible", "graviton_recommendation"])

        for col in e2_e7_columns:
            if col in df_enriched.columns:
                df[col] = df_enriched[col]

        # Step 3: Calculate combined E1-E7 total score and tier
        print_info(f"   Step 3/3: Combined E1-E7 scoring and tier classification...")

        df["total_decommission_score"] = df["co_idle_score"] + df["e2_e7_total_score"]

        # Tier classification (matches decommission_scorer.py)
        def classify_tier(score):
            if score >= 80:
                return "MUST"
            elif score >= 50:
                return "SHOULD"
            elif score >= 25:
                return "COULD"
            else:
                return "KEEP"

        df["decommission_tier"] = df["total_decommission_score"].apply(classify_tier)

        # Summary statistics
        tier_counts = df["decommission_tier"].value_counts()
        print_success(f"✅ Complete E1-E7 enrichment finished")
        print_info(
            f"   Tier distribution: MUST={tier_counts.get('MUST', 0)}, "
            f"SHOULD={tier_counts.get('SHOULD', 0)}, "
            f"COULD={tier_counts.get('COULD', 0)}, "
            f"KEEP={tier_counts.get('KEEP', 0)}"
        )

        if include_graviton_analysis:
            graviton_count = len(df[df["graviton_eligible"] == True])
            print_info(f"   Graviton eligible: {graviton_count} instances")

        return df

    except Exception as e:
        print_error(f"❌ Complete E1-E7 enrichment failed: {e}")
        logger.error(f"Complete enrichment error: {e}", exc_info=True)
        return df
