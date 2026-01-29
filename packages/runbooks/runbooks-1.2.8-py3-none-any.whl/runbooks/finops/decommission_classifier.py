#!/usr/bin/env python3
"""
Decommission Classifier Module - Multi-Signal Scoring Framework

Implements enterprise decommission scoring for EC2 and WorkSpaces resources:
- EC2: E1-E7 signals (Compute Optimizer, CloudWatch, CloudTrail, SSM, attachments, storage, cost)
- WorkSpaces: W1-W6 signals (connection recency, CloudWatch usage, break-even, policy, admin activity, user status)

Scoring Framework (0-100 scale):
- MUST (80-100): Immediate decommission candidates
- SHOULD (50-79): Strong candidates (review recommended)
- COULD (25-49): Potential candidates (manual review)
- KEEP (<25): Active resources (no action)

Design Pattern:
    - Reuses decommission_scorer.py scoring logic
    - Returns MUST/SHOULD/COULD/KEEP tiers with breakdown
    - Adds 4 columns: decommission_score, decommission_tier, decommission_reason, decommission_confidence

Usage:
    from runbooks.finops.decommission_classifier import (
        classify_ec2,
        classify_workspaces
    )

    # Classify EC2 instances after enrichment
    df = enrich_with_ec2_context(df, profile='operational')
    df = analyze_ec2_cloudtrail(df, profile='management')
    df = classify_ec2(df)  # Adds decommission_score, tier, reason columns

    # Classify WorkSpaces after enrichment
    df = enrich_with_workspaces_context(df, profile='operational')
    df = get_volume_encryption(df)  # From workspaces_analyzer.py
    df = classify_workspaces(df)  # Adds decommission_score, tier, reason columns
"""

import logging
from typing import Dict, List

import pandas as pd

from ..common.rich_utils import (
    console,
    create_progress_bar,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


def classify_ec2(df: pd.DataFrame, enable_expensive_signals: bool = False) -> pd.DataFrame:
    """
    Classify EC2 instances for decommission using E1-E7 scoring framework.

    Scoring Framework (reference: ec2-workspaces.scoring.md):
    - E1: Compute Optimizer Idle (max CPU ≤1% for 14d) → +60 points
    - E2: CloudWatch CPU (p95 ≤3%) + Network (≤10MB/day) → +10 points
    - E3: CloudTrail no activity (90d) → +8 points (EXPENSIVE: requires 90-day CloudTrail query)
    - E4: SSM heartbeat (not online or >14d) → +8 points
    - E5: No service attachment (not in ASG/LB/ECS/EKS) → +6 points (EXPENSIVE: requires 4 cross-service APIs)
    - E6: Storage I/O idle (p95 DiskOps ≈0) → +5 points
    - E7: Cost Explorer rightsizing (terminate savings) → +3 points

    Tiers:
    - 80-100 = MUST decommission (create change request → stop → terminate)
    - 50-79 = SHOULD decommission (off-hours stop schedule, re-score after 14d)
    - 25-49 = COULD decommission (rightsizing or spot conversion)
    - <25 = KEEP (production or spiky workload)

    Performance Modes:
    - enable_expensive_signals=False (default): E1+E2+E4+E6+E7 = 86 points max, <20s execution
    - enable_expensive_signals=True: E1-E7 = 100 points max, 30-50s execution (adds E3+E5)

    Args:
        df: pandas DataFrame with enrichment columns from:
            - enrich_with_ec2_context() (instance metadata)
            - analyze_ec2_cloudtrail() (activity data) - optional if enable_expensive_signals=False
            - get_ec2_cost_data() (cost data)
        enable_expensive_signals: If True, enables E3 (CloudTrail) and E5 (service attachments).
                                 If False (default), skips expensive APIs for faster execution.

    Returns:
        DataFrame with 4 added columns:
            - decommission_score (0-100)
            - decommission_tier (MUST/SHOULD/COULD/KEEP)
            - decommission_reason (breakdown of signals)
            - decommission_confidence (High/Medium/Low)

    Example:
        >>> # Fast mode (E1+E2+E4+E6+E7, <20s)
        >>> df = enrich_with_ec2_context(df, profile='operational')
        >>> df = classify_ec2(df, enable_expensive_signals=False)
        >>> must_decom = df[df['decommission_tier'] == 'MUST']

        >>> # Comprehensive mode (E1-E7, 30-50s)
        >>> df = analyze_ec2_cloudtrail(df, profile='management')  # E3 enrichment
        >>> df = classify_ec2(df, enable_expensive_signals=True)  # Enables E3+E5
    """
    try:
        from .decommission_scorer import calculate_ec2_score

        print_info(f"🔍 Classifying EC2 instances for decommission (expensive_signals={enable_expensive_signals})...")

        # Initialize columns
        df["decommission_score"] = 0
        df["decommission_tier"] = "KEEP"
        df["decommission_reason"] = ""
        df["decommission_confidence"] = "Low"

        scored_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Scoring EC2 instances...", total=len(df))

            for idx, row in df.iterrows():
                # Build signal dictionary from enrichment columns
                signals = {}

                # E1: Compute Optimizer Idle (60 points)
                # Enriched by: compute_optimizer.py → adds 'co_idle_score' column (numeric)
                co_idle_score = row.get("co_idle_score", 0)
                if co_idle_score >= 60:
                    signals["E1"] = 60
                else:
                    signals["E1"] = 0

                # E2: CloudWatch CPU+Network (10 points)
                # Enriched by: cloudwatch_enricher.py → adds 'cloudwatch_score' column
                # Criteria: p95 CPU ≤3% AND p95 Network ≤10MB/day
                cloudwatch_score = row.get("cloudwatch_score", 0)
                signals["E2"] = cloudwatch_score  # Already calculated by cloudwatch_enricher

                # E3: CloudTrail no activity (8 points)
                # Enriched by: analyze_ec2_cloudtrail() → adds 'days_since_activity' column
                # EXPENSIVE: Only evaluate if enable_expensive_signals=True
                if enable_expensive_signals:
                    days_since_activity = row.get("days_since_activity", 0)
                    if days_since_activity >= 90:
                        signals["E3"] = 8
                    else:
                        signals["E3"] = 0
                else:
                    signals["E3"] = 0  # Skip expensive CloudTrail API

                # E4: SSM heartbeat (8 points)
                # Enriched by: ssm_integration.py → adds 'ssm_score' column
                # Criteria: PingStatus != Online OR LastPingDateTime > 14 days
                ssm_score = row.get("ssm_score", 0)
                signals["E4"] = ssm_score  # Already calculated by ssm_integration

                # E5: No service attachment (6 points)
                # Enriched by: service_attachment_enricher.py → adds 'service_attachment_score' column
                # EXPENSIVE: Only evaluate if enable_expensive_signals=True
                if enable_expensive_signals:
                    # Use service_attachment_score from enricher (if available)
                    service_attachment_score = row.get("service_attachment_score", None)

                    if service_attachment_score is not None:
                        # Enricher already calculated score (0 if attached, 6 if not)
                        signals["E5"] = service_attachment_score
                    else:
                        signals["E5"] = 0  # No data available
                else:
                    signals["E5"] = 0  # Skip expensive cross-service APIs

                # E6: Storage I/O (5 points)
                # Enriched by: storage_io_enricher.py → adds 'storage_io_score' column
                # Criteria: p95 DiskReadOps+DiskWriteOps ≈ 0
                storage_io_score = row.get("storage_io_score", 0)
                signals["E6"] = storage_io_score  # Already calculated by storage_io_enricher

                # E7: Cost Explorer rightsizing (3 points)
                # Enriched by: cost_explorer_enricher.py → adds 'cost_explorer_score' column
                # Criteria: Rightsizing recommendation = Terminate AND savings > $0
                cost_explorer_score = row.get("cost_explorer_score", 0)
                signals["E7"] = cost_explorer_score  # Already calculated by cost_explorer_enricher

                # Calculate score
                result = calculate_ec2_score(signals)

                # Update DataFrame
                df.at[idx, "decommission_score"] = result["total_score"]
                df.at[idx, "decommission_tier"] = result["tier"]
                df.at[idx, "decommission_reason"] = result["breakdown"]
                df.at[idx, "decommission_confidence"] = result["confidence"]

                scored_count += 1
                progress.update(task, advance=1)

        # Display tier distribution
        tier_counts = df["decommission_tier"].value_counts()
        mode_info = "FAST (E1+E2+E4+E6+E7)" if not enable_expensive_signals else "COMPREHENSIVE (E1-E7)"
        print_success(f"✅ EC2 classification complete [{mode_info}]: {scored_count}/{len(df)} instances")
        print_info(
            f"   MUST: {tier_counts.get('MUST', 0)} | SHOULD: {tier_counts.get('SHOULD', 0)} | COULD: {tier_counts.get('COULD', 0)} | KEEP: {tier_counts.get('KEEP', 0)}"
        )

        return df

    except Exception as e:
        print_error(f"❌ EC2 classification failed: {e}")
        logger.error(f"EC2 classification error: {e}", exc_info=True)
        return df


def classify_workspaces(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify WorkSpaces for decommission using W1-W6 scoring framework.

    Scoring Framework (reference: ec2-workspaces.scoring.md):
    - W1: User connection recency (≥60 days) → +45 points
    - W2: CloudWatch UserConnected sum=0 (no sessions) → +25 points
    - W3: Billing vs usage (hourly usage < break-even) → +10 points
    - W4: Cost Optimizer policy (N months unused) → +10 points
    - W5: No admin API activity (90d) → +5 points
    - W6: User status (not in Identity Center) → +5 points

    Tiers:
    - 80-100 = MUST decommission (export user data → terminate)
    - 50-79 = SHOULD decommission (end-of-month cleanup)
    - 25-49 = COULD decommission (force hourly/AutoStop, re-evaluate)
    - <25 = KEEP (active users or compliance-bound)

    Args:
        df: pandas DataFrame with enrichment columns from:
            - enrich_with_workspaces_context() (workspace metadata)
            - get_volume_encryption() (encryption status)
            - get_cloudwatch_user_connected() (usage metrics)
            - calculate_dynamic_breakeven() (break-even analysis)

    Returns:
        DataFrame with 4 added columns:
            - decommission_score (0-100)
            - decommission_tier (MUST/SHOULD/COULD/KEEP)
            - decommission_reason (breakdown of signals)
            - decommission_confidence (High/Medium/Low)

    Example:
        >>> df = enrich_with_workspaces_context(df, profile='operational')
        >>> df = analyzer.get_volume_encryption(df)
        >>> df = analyzer.get_cloudwatch_user_connected(df)
        >>> df = classify_workspaces(df)
        >>> must_decom = df[df['decommission_tier'] == 'MUST']
    """
    try:
        from .decommission_scorer import calculate_workspaces_score

        print_info("🔍 Classifying WorkSpaces for decommission...")

        # Initialize columns
        df["decommission_score"] = 0
        df["decommission_tier"] = "KEEP"
        df["decommission_reason"] = ""
        df["decommission_confidence"] = "Low"

        scored_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Scoring WorkSpaces...", total=len(df))

            for idx, row in df.iterrows():
                # Build signal dictionary from enrichment columns
                signals = {}

                # W1: User connection recency (from enrich_with_workspaces_context)
                # Parse last_known_user_connection timestamp
                last_connection = row.get("last_known_user_connection", "Never")
                if last_connection == "Never" or last_connection == "N/A":
                    signals["W1"] = 45  # Never connected
                else:
                    # Calculate days since last connection
                    from datetime import datetime

                    try:
                        last_conn_date = datetime.fromisoformat(last_connection.replace("Z", "+00:00"))
                        days_since = (datetime.now(last_conn_date.tzinfo) - last_conn_date).days
                        if days_since >= 60:
                            signals["W1"] = 45
                        else:
                            signals["W1"] = 0
                    except (ValueError, AttributeError):
                        signals["W1"] = 0

                # W2: CloudWatch UserConnected (from get_cloudwatch_user_connected)
                user_connected_sum = row.get("user_connected_sum", 0)
                if user_connected_sum == 0:
                    signals["W2"] = 25
                else:
                    signals["W2"] = 0

                # W3: Billing vs usage (from calculate_dynamic_breakeven)
                breakeven_hours = row.get("breakeven_hours", 85.0)
                usage_hours = row.get("user_connected_sum", 0)  # Using CloudWatch sum as proxy
                if usage_hours < breakeven_hours:
                    signals["W3"] = 10
                else:
                    signals["W3"] = 5  # Over break-even, candidate for monthly flip

                # W4: Cost Optimizer policy (N months unused)
                # Using days_since_activity as proxy for "months unused"
                days_since_activity = row.get("days_since_activity", 0)
                if days_since_activity >= 60:  # 2 months
                    signals["W4"] = 10
                else:
                    signals["W4"] = 0

                # W5: No admin API activity (would require CloudTrail admin events)
                # Using CloudTrail event_count as proxy
                event_count = row.get("event_count", 0)
                if event_count == 0:
                    signals["W5"] = 5
                else:
                    signals["W5"] = 0

                # W6: User status (would require Identity Center integration)
                # TODO: Integrate with AWS Identity Store API (identitystore:list-users)
                # For now, use basic heuristic
                signals["W6"] = 0  # Requires Identity Center integration

                # Calculate score
                result = calculate_workspaces_score(signals)

                # Update DataFrame
                df.at[idx, "decommission_score"] = result["total_score"]
                df.at[idx, "decommission_tier"] = result["tier"]
                df.at[idx, "decommission_reason"] = result["breakdown"]
                df.at[idx, "decommission_confidence"] = result["confidence"]

                scored_count += 1
                progress.update(task, advance=1)

        # Display tier distribution
        tier_counts = df["decommission_tier"].value_counts()
        print_success(f"✅ WorkSpaces classification complete: {scored_count}/{len(df)} WorkSpaces")
        print_info(
            f"   MUST: {tier_counts.get('MUST', 0)} | SHOULD: {tier_counts.get('SHOULD', 0)} | COULD: {tier_counts.get('COULD', 0)} | KEEP: {tier_counts.get('KEEP', 0)}"
        )

        return df

    except Exception as e:
        print_error(f"❌ WorkSpaces classification failed: {e}")
        logger.error(f"WorkSpaces classification error: {e}", exc_info=True)
        return df
