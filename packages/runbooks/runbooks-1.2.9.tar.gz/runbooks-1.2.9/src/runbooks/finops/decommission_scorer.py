#!/usr/bin/env python3
"""
Decommission Scorer Framework - Risk-Based Prioritization for EC2 & WorkSpaces

This module provides scoring algorithms for prioritizing EC2 and WorkSpaces
decommissioning candidates based on multiple risk signals.

Scoring Framework:
- EC2 Signals (7 signals, 0-100 scale):
  E1: Compute Optimizer Idle (60 points) - Max CPU ≤1% over 14 days
  E2: SSM Agent Offline/Stale (8 points) - >7 days since heartbeat
  E3: No Network Activity (8 points) - NetworkIn <threshold MB/day
  E4: Stopped State (8 points) - Instance stopped >30 days
  E5: Old Snapshot (6 points) - AMI/snapshot >180 days old
  E6: No Tags/Owner (5 points) - Missing critical tags
  E7: Dev/Test Environment (3 points) - Non-production classification

- WorkSpaces Signals (6 signals, 0-100 scale):
  W1: No Connection (45 points) - >90 days since last connection
  W2: Connection History (25 points) - <10% connection days over 90 days
  W3: ALWAYS_ON Non-Compliant (10 points) - <40 hrs/mo usage
  W4: Stopped State (10 points) - WorkSpace stopped >30 days
  W5: No User Tags (5 points) - Missing cost allocation tags
  W6: Test/Dev Environment (5 points) - Non-production classification

Decommission Tiers (0-100 scale):
- MUST (80-100): Immediate candidates (high confidence)
- SHOULD (50-79): Strong candidates (review recommended)
- COULD (25-49): Potential candidates (manual review required)
- KEEP (<25): Active resources (no action)

Pattern: Follows base_enrichers.py pattern (Rich CLI, configurable thresholds)

Usage:
    from runbooks.finops.decommission_scorer import calculate_ec2_score

    # Calculate EC2 decommission score
    signals = {
        'E1': 60,  # Compute Optimizer Idle
        'E2': 8,   # SSM Agent Offline
        'E3': 8,   # No Network Activity
        'E4': 0,   # Running (not stopped)
        'E5': 6,   # Old Snapshot
        'E6': 5,   # No Tags
        'E7': 3    # Dev Environment
    }

    result = calculate_ec2_score(signals)
    # Returns: {
    #     'total_score': 90,
    #     'tier': 'MUST',
    #     'recommendation': 'Immediate decommission candidate',
    #     'signals': signals,
    #     'confidence': 'High'
    # }

Strategic Alignment:
- Objective 1 (runbooks package): Reusable scoring for notebooks
- Enterprise SDLC: Evidence-based prioritization with audit trails
- KISS/DRY/LEAN: Configurable thresholds, transparent calculations
"""

import logging
from typing import Dict, List, Optional

from ..common.rich_utils import (
    console,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)

# Default EC2 signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
# Reference: .claude/prompts/aws-compute/ec2-workspaces.scoring.md lines 56-64
DEFAULT_EC2_WEIGHTS = {
    # E1: Compute Optimizer Idle recommendation (AWS native ML-based signal)
    # AWS Ref: https://docs.aws.amazon.com/compute-optimizer/latest/ug/view-ec2-recommendations.html
    # Confidence: 0.95 | Tier 1 (AWS ML-based recommendation)
    "E1": 40,
    # E2: CloudWatch CPU+Network utilization <5% avg 30d
    # AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-cloudwatch.html
    # Confidence: 0.90 | Tier 1 (direct usage metrics)
    "E2": 20,
    # E3: CloudTrail activity (API call pattern analysis)
    # AWS Ref: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html
    # Confidence: 0.85 | Tier 2 (activity pattern)
    "E3": 10,
    # E4: SSM heartbeat (Systems Manager managed instance connectivity)
    # AWS Ref: https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-instances-and-nodes.html
    # Confidence: 0.75 | Tier 3 (staleness check)
    "E4": 5,
    # E5: Service attachment (load balancer, auto-scaling group membership)
    # AWS Ref: https://docs.aws.amazon.com/autoscaling/ec2/userguide/attach-load-balancer-asg.html
    # Confidence: 0.80 | Tier 2 (production safety)
    "E5": 10,
    # E6: Storage I/O activity (EBS volume read/write operations)
    # AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-io-characteristics.html
    # Confidence: 0.85 | Tier 2 (I/O pattern)
    "E6": 10,
    # E7: Cost Explorer rightsizing recommendation
    # AWS Ref: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-rightsizing.html
    # Confidence: 0.90 | Tier 3 (AWS cost optimization)
    "E7": 5,
}

# Default WorkSpaces signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
DEFAULT_WORKSPACES_WEIGHTS = {
    # W1: No Connection (>90 days) - strongest decommission signal
    # AWS Ref: https://docs.aws.amazon.com/workspaces/latest/adminguide/cloudwatch-metrics.html
    # Confidence: 0.95 | Tier 1 (direct usage indicator)
    "W1": 45,
    # W2: Connection History (<10% days) - sporadic usage pattern
    # AWS Ref: https://docs.aws.amazon.com/workspaces/latest/adminguide/cloudwatch-metrics.html
    # Confidence: 0.90 | Tier 1 (connection frequency)
    "W2": 25,
    # W3: ALWAYS_ON Non-Compliant (<40 hrs/mo) - billing mode mismatch
    # AWS Ref: https://docs.aws.amazon.com/workspaces/latest/adminguide/running-mode.html
    # Confidence: 0.85 | Tier 2 (cost optimization)
    "W3": 10,
    # W4: Stopped State (>30 days) - extended inactivity
    # AWS Ref: https://docs.aws.amazon.com/workspaces/latest/adminguide/running-mode.html
    # Confidence: 0.80 | Tier 2 (state-based)
    "W4": 10,
    # W5: No User Tags - missing user assignment metadata
    # AWS Ref: https://docs.aws.amazon.com/workspaces/latest/adminguide/tag-workspaces.html
    # Confidence: 0.70 | Tier 3 (tagging-based)
    "W5": 5,
    # W6: Test/Dev Environment - tagged as non-production
    # AWS Ref: https://docs.aws.amazon.com/workspaces/latest/adminguide/tag-workspaces.html
    # Confidence: 0.65 | Tier 3 (environment classification)
    "W6": 5,
}

# Default RDS signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
# Weight Adjustment: R4-R7 rounded to 5pt minimum (eliminate 1-4pt noise for clearer tier classification)
DEFAULT_RDS_WEIGHTS = {
    # R1: Zero connections 90+ days (strongest decommission signal)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.html
    # Confidence: 0.95 | Tier 1 (direct usage indicator)
    "R1": 60,
    # R2: Low connections <5/day avg 90d (sustained underutilization)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Monitoring.html
    # Confidence: 0.90 | Tier 1 (usage pattern)
    "R2": 15,
    # R3: CPU <5% avg 60d (capacity waste)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PerfInsights.html
    # Confidence: 0.75 | Tier 2 (performance metric)
    "R3": 10,
    # R4: IOPS <100/day avg 60d (low I/O activity)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Storage.html
    # Confidence: 0.70 | Tier 3 (I/O pattern)
    "R4": 10,
    # R5: Backup-only connections (no application traffic)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html
    # Confidence: 0.65 | Tier 3 (connection pattern)
    "R5": 5,
    # R6: Non-business hours only (test/dev environment indicator)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_Tagging.html
    # Confidence: 0.50 | Tier 3 (schedule pattern)
    "R6": 5,
    # R7: Storage <20% utilized (over-provisioned storage)
    # AWS Ref: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Storage.html
    # Confidence: 0.45 | Tier 3 (capacity signal)
    "R7": 5,
}

# Default S3 signal weights (0-100 scale) - v1.1.30: AWS WAR Aligned (S1-S10 Framework)
# AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
# Total Maximum Points: 125 (normalized to 0-100 scale)
DEFAULT_S3_WEIGHTS = {
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 1: HIGH-CONFIDENCE SIGNALS (60 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # S1: Storage Lens Inactive - 0 requests 90d (strongest decommission signal)
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
    # Confidence: 0.95 | Tier 1 (AWS native activity detection)
    "S1": 40,
    # S2: Storage Class Inefficiency - STANDARD with <1 access/month
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
    # Confidence: 0.85 | Tier 1 (direct cost impact: 50-80% savings potential)
    "S2": 20,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 2: MEDIUM-CONFIDENCE SIGNALS (45 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # S3: Lifecycle Missing - No lifecycle + objects >365d
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
    # Confidence: 0.80 | Tier 2 (automation foundation)
    "S3": 15,
    # S4: Intelligent-Tiering Off - Bucket >10GB without IT
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
    # Confidence: 0.80 | Tier 2 (cost optimization opportunity)
    "S4": 10,
    # S5: Versioning No Expiration - Versioning + no lifecycle expiration
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
    # Confidence: 0.80 | Tier 2 (cost growth risk)
    "S5": 10,
    # S6: Zero Requests 90D - CloudWatch AllRequests=0
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html
    # Confidence: 0.80 | Tier 2 (idle detection fallback when S1 not available)
    "S6": 10,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 3: LOWER-CONFIDENCE SIGNALS (20 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # S7: Replication Waste - Replication to 0-access bucket
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
    # Confidence: 0.70 | Tier 3 (cross-region cost waste)
    "S7": 5,
    # S8: Public No Encryption - Public + no encryption + 0 GET
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
    # Confidence: 0.70 | Tier 3 (security + decommission indicator)
    "S8": 5,
    # S9: Inventory Overhead - Inventory on <1GB/0-access bucket
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
    # Confidence: 0.70 | Tier 3 (over-engineering indicator)
    "S9": 5,
    # S10: High Request Cost - Request cost >$10/month declining
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html
    # Confidence: 0.70 | Tier 3 (cost anomaly on declining bucket)
    "S10": 5,
}

# ═════════════════════════════════════════════════════════════════════════════
# v1.1.29: TO-BE S3 Signal Weights (Manager's Directive - 100pt System)
# ═════════════════════════════════════════════════════════════════════════════
# AS-IS vs TO-BE Changes:
# - S1: 40→20 (-50%) - Storage Lens cost-benefit gate (~$0.025/GB/month)
# - S2: 20→15 (-25%) - Alignment with cost optimization priority
# - S3: 15→10 (-33%) - Standardization to 10pt Tier 2 baseline
# - S4-S9: Maintained (0% change)
# - S10: 5→10 (+100%) - Increased priority for declining-use buckets
# Total: 125→100 points (no normalization step required)
#
# Manager's Rationale:
# 1. Storage Lens enablement cost (~$1,080/month for 43.2 TB) must justify ROI
# 2. Decommissioning signals (S5, S6, S10) prioritized for idle detection
# 3. Simplified scoring: 100pt direct sum (vs 125pt normalized)
#
# AWS Documentation References (Manager-Provided):
# - https://aws.amazon.com/blogs/storage/optimizing-your-s3-storage-costs-with-s3-storage-lens/
# - https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
# - https://aws.amazon.com/s3/storage-lens/pricing/
# ═════════════════════════════════════════════════════════════════════════════

DEFAULT_S3_WEIGHTS_TO_BE = {
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 1: HIGH-CONFIDENCE SIGNALS (35 points max) 🔄 UPDATED
    # ═══════════════════════════════════════════════════════════════════════
    # S1: Storage Lens Inactive - 0 requests 90d with cost-benefit gate
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
    # Confidence: 0.95 | Tier 1 (with ROI validation)
    # 🔻 REDUCED from 40pt: Only recommend if potential_savings > $0.025/GB/month
    "S1": 20,
    # S2: Storage Class Inefficiency - STANDARD with <1 access/month
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
    # Confidence: 0.85 | Tier 1 (direct cost impact: 50-80% savings potential)
    # 🔻 REDUCED from 20pt: Alignment with overall cost optimization priority
    "S2": 15,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 2: MEDIUM-CONFIDENCE SIGNALS (50 points max) 🔄 UPDATED
    # ═══════════════════════════════════════════════════════════════════════
    # S3: Lifecycle Missing - No lifecycle + objects >365d
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
    # Confidence: 0.80 | Tier 2 (automation foundation)
    # 🔻 REDUCED from 15pt: Standardized to 10pt Tier 2 baseline
    "S3": 10,
    # S4: Intelligent-Tiering Off - Bucket >10GB without IT
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
    # Confidence: 0.80 | Tier 2 (cost optimization opportunity)
    # ✅ MAINTAINED at 10pt
    "S4": 10,
    # S5: Versioning No Expiration - Versioning + no lifecycle expiration
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
    # Confidence: 0.80 | Tier 2 (cost growth risk)
    # ✅ MAINTAINED at 10pt (important for decommissioning)
    "S5": 10,
    # S6: Zero Requests 90D - CloudWatch AllRequests=0
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html
    # Confidence: 0.80 | Tier 2 (idle detection fallback)
    # ✅ MAINTAINED at 10pt (important for decommissioning)
    "S6": 10,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 3: LOWER-CONFIDENCE SIGNALS (15 points max) 🔄 S10 UPDATED
    # ═══════════════════════════════════════════════════════════════════════
    # S7: Replication Waste - Replication to 0-access bucket
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
    # Confidence: 0.70 | Tier 3 (cross-region cost waste)
    # ✅ MAINTAINED at 5pt
    "S7": 5,
    # S8: Public No Encryption - Public + no encryption + 0 GET
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
    # Confidence: 0.70 | Tier 3 (security + decommission indicator)
    # ✅ MAINTAINED at 5pt
    "S8": 5,
    # S9: Inventory Overhead - Inventory on <1GB/0-access bucket
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
    # Confidence: 0.70 | Tier 3 (over-engineering indicator)
    # ✅ MAINTAINED at 5pt
    "S9": 5,
    # S10: High Request Cost - Request cost >$10/month declining
    # AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html
    # Confidence: 0.70 | Tier 3 (cost anomaly on declining bucket)
    # 🔺 INCREASED from 5pt: Better identifies declining-use buckets
    "S10": 10,
}


def calculate_s3_agreement_percentage(bucket_name: str, detected_signals: list) -> dict:
    """
    Calculate % agreement between AS-IS (125pt) and TO-BE (100pt) S3 signal frameworks.

    This function compares the two scoring systems to quantify the impact of
    manager's directive changes (S1 cost-benefit gate, S10 decommissioning priority).

    Args:
        bucket_name: S3 bucket name
        detected_signals: List of S3IdleSignal enum values detected for this bucket

    Returns:
        dict with keys:
            - bucket: Bucket name
            - as_is_raw_score: Raw score using AS-IS weights (0-125)
            - as_is_normalized_score: Normalized AS-IS score (0-100)
            - to_be_score: Score using TO-BE weights (0-100)
            - score_difference: Absolute difference between normalized AS-IS and TO-BE
            - agreement_pct: Agreement percentage (100% - 2*diff, capped at 0)
            - tier_as_is: Decommission tier using AS-IS score
            - tier_to_be: Decommission tier using TO-BE score
            - tier_match: Boolean indicating if tiers are the same
            - signal_changes: Dict showing which signals changed weight

    Example:
        >>> signals = [S3IdleSignal.S1_STORAGE_LENS_INACTIVE,
        ...            S3IdleSignal.S2_STORAGE_CLASS_INEFFICIENCY,
        ...            S3IdleSignal.S3_LIFECYCLE_MISSING]
        >>> result = calculate_s3_agreement_percentage('test-bucket', signals)
        >>> print(result['agreement_pct'])
        70.0  # AS-IS: 60/100, TO-BE: 45/100, diff=15, agreement=100-2*15=70%
    """
    # Calculate AS-IS score (125pt system, normalized to 0-100)
    as_is_raw = sum(DEFAULT_S3_WEIGHTS.get(s.value, 0) for s in detected_signals)
    as_is_normalized = min(100, int((as_is_raw / 125) * 100))

    # Calculate TO-BE score (100pt system, direct)
    to_be_score = sum(DEFAULT_S3_WEIGHTS_TO_BE.get(s.value, 0) for s in detected_signals)

    # Calculate agreement
    score_diff = abs(as_is_normalized - to_be_score)
    # Agreement formula: 10pt diff = 80% agreement (linear decay)
    agreement_pct = max(0.0, 100.0 - (score_diff * 2.0))

    # Tier classification
    def classify_tier(score: int) -> str:
        if score >= 80:
            return "MUST"
        elif score >= 50:
            return "SHOULD"
        elif score >= 25:
            return "COULD"
        else:
            return "KEEP"

    tier_as_is = classify_tier(as_is_normalized)
    tier_to_be = classify_tier(to_be_score)

    # Identify signal weight changes
    signal_changes = {}
    for signal in detected_signals:
        as_is_weight = DEFAULT_S3_WEIGHTS.get(signal.value, 0)
        to_be_weight = DEFAULT_S3_WEIGHTS_TO_BE.get(signal.value, 0)
        if as_is_weight != to_be_weight:
            change_pct = ((to_be_weight - as_is_weight) / as_is_weight * 100) if as_is_weight > 0 else 0
            signal_changes[signal.value] = {
                "as_is": as_is_weight,
                "to_be": to_be_weight,
                "change_pct": round(change_pct, 1),
            }

    return {
        "bucket": bucket_name,
        "as_is_raw_score": as_is_raw,
        "as_is_normalized_score": as_is_normalized,
        "to_be_score": to_be_score,
        "score_difference": score_diff,
        "agreement_pct": round(agreement_pct, 1),
        "tier_as_is": tier_as_is,
        "tier_to_be": tier_to_be,
        "tier_match": (tier_as_is == tier_to_be),
        "signal_changes": signal_changes,
        "signals_detected": [s.value for s in detected_signals],
        "total_signals_count": len(detected_signals),
    }


# Default ALB signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Ref: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html
DEFAULT_ALB_WEIGHTS = {
    # L1: No active targets - load balancer with zero healthy targets
    # AWS Ref: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html
    # Confidence: 0.95 | Tier 1
    "L1": 60,
    # L2: Low request count (<100/day) - minimal traffic
    # AWS Ref: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html
    # Confidence: 0.85 | Tier 2
    "L2": 15,
    # L3: Zero active connections - no client connectivity
    # Confidence: 0.80 | Tier 2
    "L3": 10,
    # L4: No target registration 90+ days - stale configuration
    # Confidence: 0.70 | Tier 3
    "L4": 8,
    # L5: Idle scheme (internet-facing with 0 ingress) - unused public endpoint
    # Confidence: 0.75 | Tier 3
    "L5": 7,
}

# Default NLB signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Ref: https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html
DEFAULT_NLB_WEIGHTS = {
    # L1: No active targets - load balancer with zero healthy targets
    # AWS Ref: https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-cloudwatch-metrics.html
    # Confidence: 0.95 | Tier 1
    "L1": 60,
    # L2: Low connection count (<100/day) - minimal traffic
    # Confidence: 0.85 | Tier 2
    "L2": 15,
    # L3: Zero active flows - no network flows
    # Confidence: 0.80 | Tier 2
    "L3": 10,
    # L4: No target registration 90+ days - stale configuration
    # Confidence: 0.70 | Tier 3
    "L4": 8,
    # L5: Low data transfer (<100 MB/day) - minimal usage
    # Confidence: 0.75 | Tier 3
    "L5": 7,
}

# Default Direct Connect signal weights - v1.1.20: AWS WAR Aligned
# AWS Ref: https://docs.aws.amazon.com/directconnect/latest/UserGuide/Welcome.html
DEFAULT_DX_WEIGHTS = {
    # DX1: Connection down state - circuit not operational
    # AWS Ref: https://docs.aws.amazon.com/directconnect/latest/UserGuide/monitoring-cloudwatch.html
    # Confidence: 0.95 | Tier 1
    "DX1": 60,
    # DX2: Low bandwidth utilization (<10%) - capacity waste
    # Confidence: 0.85 | Tier 1
    "DX2": 20,
    # DX3: No BGP routes - routing not configured
    # Confidence: 0.80 | Tier 2
    "DX3": 10,
    # DX4: No data transfer 90+ days - unused connection
    # Confidence: 0.75 | Tier 2
    "DX4": 10,
}

# Default Route53 signal weights - v1.1.20: AWS WAR Aligned
# AWS Ref: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html
DEFAULT_ROUTE53_WEIGHTS = {
    # R53-1: Zero DNS queries 30+ days - unused hosted zone
    # AWS Ref: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-cloudwatch.html
    # Confidence: 0.90 | Tier 1
    "R53-1": 40,
    # R53-2: Health check failures - endpoint unavailability
    # AWS Ref: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover.html
    # Confidence: 0.85 | Tier 1
    "R53-2": 30,
    # R53-3: No record updates 365+ days - stale DNS configuration
    # Confidence: 0.70 | Tier 2
    "R53-3": 20,
    # R53-4: Orphaned hosted zone (0 records) - empty zone
    # Confidence: 0.95 | Tier 2
    "R53-4": 10,
}

# Default DynamoDB signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
# Weight Adjustment: D1 reduced 60→45 (ON-DEMAND tables don't have capacity utilization metric)
DEFAULT_DYNAMODB_WEIGHTS = {
    # D1: Low capacity utilization <5% (PROVISIONED tables only)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ProvisionedThroughput.html
    # Confidence: 0.90 | Tier 1 (direct cost impact for PROVISIONED mode)
    # Note: N/A for ON-DEMAND billing mode (no capacity concept)
    "D1": 45,
    # D2: Idle Global Secondary Indexes (GSI) consuming RCU/WCU
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
    # Confidence: 0.75 | Tier 1 (direct cost - GSIs double storage + consume capacity)
    "D2": 20,
    # D3: Point-in-Time Recovery (PITR) not enabled (production tables)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery.html
    # Confidence: 0.60 | Tier 2 (compliance + operational risk)
    "D3": 15,
    # D4: DynamoDB Streams not active (integration opportunity)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
    # Confidence: 0.50 | Tier 2 (integration signal, not cost)
    "D4": 10,
    # D5: Low cost efficiency (high provisioned capacity + low actual usage)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/CostOptimization.html
    # Confidence: 0.70 | Tier 2 (cost optimization opportunity)
    "D5": 10,
}

# Default ECS signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html
DEFAULT_ECS_WEIGHTS = {
    # C1: CPU/Memory utilization <5% (sustained underutilization)
    # AWS Ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cloudwatch-metrics.html
    # Confidence: 0.90 | Tier 1 (direct usage metric)
    "C1": 45,
    # C2: Task count trends (low or zero tasks running)
    # AWS Ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html
    # Confidence: 0.85 | Tier 1 (task activity)
    "C2": 30,
    # C3: Service health (unhealthy or stopped services)
    # AWS Ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-event-messages.html
    # Confidence: 0.80 | Tier 2 (health status)
    "C3": 15,
    # C4: Compute type split (EC2 vs Fargate efficiency analysis)
    # AWS Ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_types.html
    # Confidence: 0.70 | Tier 3 (cost optimization)
    "C4": 5,
    # C5: Cost efficiency (high cost per task ratio)
    # AWS Ref: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-quotas.html
    # Confidence: 0.75 | Tier 3 (cost metric)
    "C5": 5,
}

# Default ASG signal weights (0-100 scale)
DEFAULT_ASG_WEIGHTS = {
    "A1": 40,  # Scaling activity (no scaling events 90+ days)
    "A2": 25,  # Instance health (unhealthy instances)
    "A3": 20,  # Capacity delta (min = max = desired = 0)
    "A4": 10,  # Launch config age (outdated or unused)
    "A5": 5,  # Cost efficiency (high cost for low activity)
}

# Decommission tier thresholds (internal 0-100 scale)
TIER_THRESHOLDS = {
    "MUST": 80,  # 80-100: Immediate candidates
    "SHOULD": 50,  # 50-79: Strong candidates
    "COULD": 25,  # 25-49: Potential candidates
    "KEEP": 0,  # 0-24: Active resources
}

# v1.1.31: Display tier thresholds (0-10 scale for UI)
TIER_DISPLAY_THRESHOLDS = {
    "MUST": 8,  # 8-10: Immediate candidates
    "SHOULD": 5,  # 5-7: Strong candidates
    "COULD": 3,  # 3-4: Potential candidates (was 2.5, rounded to 3)
    "KEEP": 0,  # 0-2: Active resources
}


def convert_score_to_display(internal_score: int) -> float:
    """
    Convert internal 0-100 score to 0-10 display scale.

    v1.1.31: User requested 0-10 display scale for better UX.
    Internal scoring remains 0-100 for precision.

    Args:
        internal_score: Score in 0-100 range

    Returns:
        Display score in 0.0-10.0 range (one decimal precision)

    Example:
        >>> convert_score_to_display(82)
        8.2
        >>> convert_score_to_display(45)
        4.5
    """
    return round(internal_score / 10, 1)


def get_display_tier(internal_score: int) -> str:
    """
    Get tier label based on internal 0-100 score.

    Uses TIER_THRESHOLDS (0-100 scale) for classification.
    Returns display-friendly tier name.

    Args:
        internal_score: Score in 0-100 range

    Returns:
        Tier label: 'MUST', 'SHOULD', 'COULD', or 'KEEP'

    Example:
        >>> get_display_tier(82)
        'MUST'
        >>> get_display_tier(45)
        'COULD'
    """
    if internal_score >= TIER_THRESHOLDS["MUST"]:
        return "MUST"
    elif internal_score >= TIER_THRESHOLDS["SHOULD"]:
        return "SHOULD"
    elif internal_score >= TIER_THRESHOLDS["COULD"]:
        return "COULD"
    else:
        return "KEEP"


def format_score_with_tier(internal_score: int) -> str:
    """
    Format score for display with tier label.

    v1.1.31: Combined display showing 0-10 score and tier.

    Args:
        internal_score: Score in 0-100 range

    Returns:
        Formatted string like "8.2 MUST" or "4.5 COULD"

    Example:
        >>> format_score_with_tier(82)
        '8.2 MUST'
        >>> format_score_with_tier(25)
        '2.5 COULD'
    """
    display_score = convert_score_to_display(internal_score)
    tier = get_display_tier(internal_score)
    return f"{display_score} {tier}"


def calculate_ec2_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate EC2 decommission score from multiple signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (E1-E7)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'E1': 60, 'E2': 0, 'E3': 8, 'E4': 0, 'E5': 6, 'E6': 5, 'E7': 3}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 82,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'E1': {'score': 60, 'weight': 60, 'description': 'Compute Optimizer Idle'},
                'E2': {'score': 0, 'weight': 8, 'description': 'SSM Agent Offline/Stale'},
                ...
            },
            'confidence': 'High',  # Based on signal coverage
            'breakdown': 'E1(60) + E3(8) + E5(6) + E6(5) + E7(3) = 82'
        }

    Example:
        >>> signals = {'E1': 60, 'E2': 0, 'E3': 8, 'E4': 0, 'E5': 6, 'E6': 5, 'E7': 3}
        >>> result = calculate_ec2_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 82, Tier: MUST

    Signal Descriptions (per ec2-workspaces.scoring.md):
        E1: Compute Optimizer identifies instance as idle (max CPU ≤1% over 14 days)
        E2: CloudWatch metrics show low activity (p95 CPU ≤3%, Network ≤10MB/day)
        E3: CloudTrail shows no write events for instance over 90 days
        E4: SSM agent heartbeat offline or stale (PingStatus != Online OR >14d)
        E5: No service attachment (not in ASG/LB/ECS/EKS cluster)
        E6: Storage I/O minimal (p95 DiskReadOps + DiskWriteOps ≈ 0)
        E7: Cost Explorer recommends termination with savings > $0
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_EC2_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency (matches specification)
        signal_descriptions = {
            "E1": "Compute Optimizer Idle (max CPU ≤1% for 14d)",
            "E2": "CloudWatch CPU+Network (p95 ≤3%, ≤10MB/day)",
            "E3": "CloudTrail no write events (90d)",
            "E4": "SSM heartbeat (offline or >14d stale)",
            "E5": "No service attachment (ASG/LB/ECS/EKS)",
            "E6": "Storage I/O idle (p95 DiskOps ≈ 0)",
            "E7": "Cost Explorer terminate savings",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown EC2 signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active resource (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 4:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"EC2 score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_workspaces_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate WorkSpaces decommission score from multiple signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (W1-W6)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'W1': 45, 'W2': 25, 'W3': 0, 'W4': 0, 'W5': 5, 'W6': 5}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 80,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'W1': {'score': 45, 'weight': 45, 'description': 'No Connection (>90 days)'},
                'W2': {'score': 25, 'weight': 25, 'description': 'Connection History (<10%)'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'W1(45) + W2(25) + W5(5) + W6(5) = 80'
        }

    Example:
        >>> signals = {'W1': 45, 'W2': 25, 'W3': 0, 'W4': 0, 'W5': 5, 'W6': 5}
        >>> result = calculate_workspaces_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 80, Tier: MUST

    Signal Descriptions:
        W1: No connection detected (>90 days since last user connection)
        W2: Low connection history (<10% connection days over 90 days)
        W3: ALWAYS_ON mode with low usage (<40 hours/month breakeven threshold)
        W4: WorkSpace in stopped state (>30 days)
        W5: Missing user/cost allocation tags
        W6: Classified as test/dev environment (non-production)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_WORKSPACES_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "W1": "No Connection (>90 days)",
            "W2": "Connection History (<10% days)",
            "W3": "ALWAYS_ON Non-Compliant (<40 hrs/mo)",
            "W4": "Stopped State (>30 days)",
            "W5": "No User Tags",
            "W6": "Test/Dev Environment",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown WorkSpaces signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active resource (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"WorkSpaces score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_rds_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate RDS decommission score from R1-R7 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (R1-R7)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'R1': 60, 'R2': 0, 'R3': 10, 'R4': 0, 'R5': 4, 'R6': 2, 'R7': 1}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 87,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'R1': {'score': 60, 'weight': 60, 'description': 'Zero connections 90+ days'},
                'R2': {'score': 0, 'weight': 15, 'description': 'Low connections <5/day'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'R1(60) + R3(10) + R5(4) + R6(2) + R7(1) = 87'
        }

    Example:
        >>> signals = {'R1': 60, 'R2': 0, 'R3': 10, 'R4': 0, 'R5': 4, 'R6': 2, 'R7': 1}
        >>> result = calculate_rds_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 87, Tier: MUST

    Signal Descriptions:
        R1: Zero connections 90+ days (HIGH confidence: 0.95)
        R2: Low connections <5/day avg 90d (HIGH confidence: 0.90)
        R3: CPU <5% avg 60d (MEDIUM confidence: 0.75)
        R4: IOPS <100/day avg 60d (MEDIUM confidence: 0.70)
        R5: Backup-only connections (MEDIUM confidence: 0.65)
        R6: Non-business hours only (LOW confidence: 0.50)
        R7: Storage <20% utilized (LOW confidence: 0.45)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_RDS_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "R1": "Zero connections 90+ days (HIGH: 0.95)",
            "R2": "Low connections <5/day avg 90d (HIGH: 0.90)",
            "R3": "CPU <5% avg 60d (MEDIUM: 0.75)",
            "R4": "IOPS <100/day avg 60d (MEDIUM: 0.70)",
            "R5": "Backup-only connections (MEDIUM: 0.65)",
            "R6": "Non-business hours only (LOW: 0.50)",
            "R7": "Storage <20% utilized (LOW: 0.45)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown RDS signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active resource (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 4:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"RDS score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_cost_weighted_score(base_score: int, monthly_cost: float) -> int:
    """
    Apply cost multiplier to boost high-cost S3 buckets in prioritization.

    Business Problem: Ensures expensive buckets get attention regardless of signal count.
    A $1,105/mo bucket should be prioritized over a $0.10/mo bucket even if they
    have identical signals.

    Formula:
    - Cost bonus: +10 points per $100/mo (capped at +50 max)
    - Final score: base_score + cost_bonus (capped at 100)

    Args:
        base_score: Signal-based score (0-100 from S1-S7)
        monthly_cost: Monthly cost in USD

    Returns:
        Cost-weighted score (0-100, capped)

    Example:
        >>> # vamsnz-prod-atlassian-backups: 31 base, $1,105/mo
        >>> calculate_cost_weighted_score(31, 1105.81)
        81  # 31 + 50 (capped) = 81 → MUST tier

        >>> # Small bucket: 31 base, $10/mo
        >>> calculate_cost_weighted_score(31, 10.0)
        32  # 31 + 1 = 32 → COULD tier

        >>> # High-signal bucket: 75 base, $5/mo
        >>> calculate_cost_weighted_score(75, 5.0)
        75  # 75 + 0 = 75 → MUST tier (already high)
    """
    # Cost bonus: +10 points per $100/mo (capped at +50 max to prevent over-boosting)
    cost_bonus = min(int(monthly_cost / 100) * 10, 50)

    # Return cost-weighted score (capped at 100)
    return min(base_score + cost_bonus, 100)


def calculate_s3_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
    monthly_cost: Optional[float] = None,
) -> Dict:
    """
    Calculate S3 optimization score from S1-S7 signals with cost-weighted prioritization.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale) = base score
    - Cost-weighted score = base score + cost bonus (if monthly_cost provided)
    - Cost bonus: +10 points per $100/mo (capped at +50 max)
    - Tier classification based on cost-weighted score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (S1-S7)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'S1': 20, 'S2': 15, 'S3': 12, 'S4': 0, 'S5': 8, 'S6': 7, 'S7': 3}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)
        monthly_cost: Optional monthly cost for cost-weighted prioritization

    Returns:
        Dictionary with scoring results:
        {
            'base_score': 31,          # Signal-only score
            'cost_bonus': 50,          # Cost multiplier bonus
            'total_score': 81,         # Cost-weighted score (base + bonus)
            'tier': 'MUST',
            'recommendation': 'Immediate optimization candidate (high cost impact)',
            'signals': {
                'S1': {'score': 20, 'weight': 20, 'description': 'No lifecycle policy'},
                'S2': {'score': 15, 'weight': 15, 'description': 'STANDARD storage unoptimized'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'S1(20) + S2(15) + S3(12) + S5(8) + S6(7) + S7(3) = 31 base + 50 cost = 81'
        }

    Example:
        >>> signals = {'S1': 20, 'S2': 0, 'S3': 0, 'S4': 0, 'S5': 8, 'S6': 0, 'S7': 3}
        >>> result = calculate_s3_score(signals, monthly_cost=1105.81)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 81, Tier: MUST

    Signal Descriptions:
        S1: No lifecycle policy
        S2: STANDARD storage unoptimized
        S3: Glacier candidate (>90d unaccessed)
        S4: Deep Archive candidate (>365d)
        S5: Versioning without expiration
        S6: Temp/log data without expiration
        S7: Encryption missing
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_S3_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "S1": "Storage Lens optimization score low (<70/100)",
            "S2": "Storage class vs access pattern mismatch",
            "S3": "Security gap (encryption/access/logging)",
            "S4": "No lifecycle policy (bucket age >90d)",
            "S5": "High request cost (GET/PUT/LIST inefficiency)",
            "S6": "Versioning without lifecycle expiration",
            "S7": "No cross-region replication (production bucket)",
        }

        # Calculate base score (signal-only)
        base_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown S3 signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                base_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Apply cost weighting if monthly_cost provided
        cost_bonus = 0
        if monthly_cost is not None and monthly_cost > 0:
            # Calculate cost bonus: +10 points per $100/mo (capped at +50)
            cost_bonus = min(int(monthly_cost / 100) * 10, 50)

        # Calculate final cost-weighted score
        total_score = min(base_score + cost_bonus, 100)

        # Determine tier using cost-weighted score
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation (include cost impact if applicable)
        if cost_bonus > 0:
            recommendations = {
                "MUST": "Immediate optimization candidate (high cost impact)",
                "SHOULD": "Strong optimization candidate (significant cost impact)",
                "COULD": "Potential optimization candidate (moderate cost impact)",
                "KEEP": "Well-optimized bucket (no action)",
            }
        else:
            recommendations = {
                "MUST": "Immediate optimization candidate (high confidence)",
                "SHOULD": "Strong optimization candidate (review recommended)",
                "COULD": "Potential optimization candidate (manual review required)",
                "KEEP": "Well-optimized bucket (no action)",
            }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 4:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {base_score}"
            if cost_bonus > 0:
                breakdown += f" base + {cost_bonus} cost = {total_score}"
        else:
            breakdown = "No signals detected = 0"
            if cost_bonus > 0:
                breakdown += f" + {cost_bonus} cost = {total_score}"

        return {
            "base_score": base_score,
            "cost_bonus": cost_bonus,
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"S3 score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_alb_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate ALB decommission score from L1-L5 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (L1-L5)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'L1': 60, 'L2': 15, 'L3': 10, 'L4': 0, 'L5': 7}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 92,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'L1': {'score': 60, 'weight': 60, 'description': 'No active targets'},
                'L2': {'score': 15, 'weight': 15, 'description': 'Low request count'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'L1(60) + L2(15) + L3(10) + L5(7) = 92'
        }

    Example:
        >>> signals = {'L1': 60, 'L2': 15, 'L3': 10, 'L4': 0, 'L5': 7}
        >>> result = calculate_alb_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 92, Tier: MUST

    Signal Descriptions:
        L1: No active targets
        L2: Low request count (<100/day)
        L3: Zero active connections
        L4: No target registration 90+ days
        L5: Idle scheme (internet-facing with 0 ingress)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_ALB_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "L1": "No active targets",
            "L2": "Low request count (<100/day)",
            "L3": "Zero active connections",
            "L4": "No target registration 90+ days",
            "L5": "Idle scheme (internet-facing with 0 ingress)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown ALB signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active load balancer (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"ALB score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_nlb_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate NLB (Network Load Balancer) decommission score from L1-L5 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (L1-L5)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'L1': 60, 'L2': 15, 'L3': 10, 'L4': 0, 'L5': 7}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 92,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'L1': {'score': 60, 'weight': 60, 'description': 'No active targets'},
                'L2': {'score': 15, 'weight': 15, 'description': 'Low connection count'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'L1(60) + L2(15) + L3(10) + L5(7) = 92'
        }

    Example:
        >>> signals = {'L1': 60, 'L2': 15, 'L3': 10, 'L4': 0, 'L5': 7}
        >>> result = calculate_nlb_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 92, Tier: MUST

    Signal Descriptions:
        L1: No active targets
        L2: Low connection count (<100/day)
        L3: Zero active flows
        L4: No target registration 90+ days
        L5: Low data transfer (<100 MB/day)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_NLB_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "L1": "No active targets",
            "L2": "Low connection count (<100/day)",
            "L3": "Zero active flows",
            "L4": "No target registration 90+ days",
            "L5": "Low data transfer (<100 MB/day)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown NLB signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active load balancer (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"NLB score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_dx_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate Direct Connect decommission score from DX1-DX4 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (DX1-DX4)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'DX1': 60, 'DX2': 20, 'DX3': 10, 'DX4': 10}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 100,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'DX1': {'score': 60, 'weight': 60, 'description': 'Connection down state'},
                'DX2': {'score': 20, 'weight': 20, 'description': 'Low bandwidth utilization'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'DX1(60) + DX2(20) + DX3(10) + DX4(10) = 100'
        }

    Example:
        >>> signals = {'DX1': 60, 'DX2': 20, 'DX3': 10, 'DX4': 10}
        >>> result = calculate_dx_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 100, Tier: MUST

    Signal Descriptions:
        DX1: Connection down state
        DX2: Low bandwidth utilization (<10%)
        DX3: No BGP routes
        DX4: No data transfer 90+ days
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_DX_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "DX1": "Connection down state",
            "DX2": "Low bandwidth utilization (<10%)",
            "DX3": "No BGP routes",
            "DX4": "No data transfer 90+ days",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown Direct Connect signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active connection (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"Direct Connect score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_route53_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate Route53 decommission score from R53-1 to R53-4 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (R53-1 to R53-4)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'R53-1': 40, 'R53-2': 30, 'R53-3': 20, 'R53-4': 10}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 100,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'R53-1': {'score': 40, 'weight': 40, 'description': 'Zero DNS queries 30+ days'},
                'R53-2': {'score': 30, 'weight': 30, 'description': 'Health check failures'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'R53-1(40) + R53-2(30) + R53-3(20) + R53-4(10) = 100'
        }

    Example:
        >>> signals = {'R53-1': 40, 'R53-2': 30, 'R53-3': 20, 'R53-4': 10}
        >>> result = calculate_route53_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 100, Tier: MUST

    Signal Descriptions:
        R53-1: Zero DNS queries 30+ days
        R53-2: Health check failures
        R53-3: No record updates 365+ days
        R53-4: Orphaned hosted zone (0 records)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_ROUTE53_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "R53-1": "Zero DNS queries 30+ days",
            "R53-2": "Health check failures",
            "R53-3": "No record updates 365+ days",
            "R53-4": "Orphaned hosted zone (0 records)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown Route53 signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active hosted zone (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"Route53 score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_dynamodb_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate DynamoDB decommission score from D1-D5 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (D1-D5)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'D1': 60, 'D2': 15, 'D3': 0, 'D4': 8, 'D5': 7}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 90,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'D1': {'score': 60, 'weight': 60, 'description': 'Low capacity utilization'},
                'D2': {'score': 15, 'weight': 15, 'description': 'Idle GSIs'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'D1(60) + D2(15) + D4(8) + D5(7) = 90'
        }

    Example:
        >>> signals = {'D1': 60, 'D2': 15, 'D3': 0, 'D4': 8, 'D5': 7}
        >>> result = calculate_dynamodb_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 90, Tier: MUST

    Signal Descriptions:
        D1: Low capacity utilization <5% (HIGH confidence: 0.90)
        D2: Idle GSIs (MEDIUM confidence: 0.75)
        D3: No PITR enabled (MEDIUM confidence: 0.60)
        D4: No Streams activity (LOW confidence: 0.50)
        D5: Low cost efficiency (MEDIUM confidence: 0.70)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_DYNAMODB_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "D1": "Low capacity utilization <5% (HIGH: 0.90)",
            "D2": "Idle GSIs (MEDIUM: 0.75)",
            "D3": "No PITR enabled (MEDIUM: 0.60)",
            "D4": "No Streams activity (LOW: 0.50)",
            "D5": "Low cost efficiency (MEDIUM: 0.70)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown DynamoDB signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential optimization candidate (manual review required)",
            "KEEP": "Active table (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"DynamoDB score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_asg_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate Auto Scaling Group decommission score from A1-A5 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (A1-A5)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'A1': 45, 'A2': 0, 'A3': 15, 'A4': 10, 'A5': 5}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 75,
            'tier': 'SHOULD',
            'recommendation': 'Strong decommission candidate',
            'signals': {
                'A1': {'score': 45, 'weight': 45, 'description': 'No scaling activity 90+ days'},
                'A2': {'score': 0, 'weight': 25, 'description': 'Persistent unhealthy instances'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'A1(45) + A3(15) + A4(10) + A5(5) = 75'
        }

    Example:
        >>> signals = {'A1': 45, 'A2': 0, 'A3': 15, 'A4': 10, 'A5': 5}
        >>> result = calculate_asg_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 75, Tier: SHOULD

    Signal Descriptions:
        A1: No scaling activity 90+ days (HIGH confidence: no DesiredCapacity changes)
        A2: Persistent unhealthy instances (MEDIUM confidence: >0% unhealthy for 7+ days)
        A3: Capacity delta (MEDIUM confidence: desired vs actual mismatch >30 days)
        A4: Launch config age >180 days (LOW confidence: outdated configuration)
        A5: Cost efficiency >150% baseline (LOW confidence: cost per instance inefficiency)
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_ASG_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "A1": "No scaling activity 90+ days",
            "A2": "Persistent unhealthy instances",
            "A3": "Capacity delta (desired vs actual)",
            "A4": "Launch config age >180 days",
            "A5": "Cost efficiency >150% baseline",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown ASG signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential decommission candidate (manual review required)",
            "KEEP": "Active Auto Scaling Group (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"ASG score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_ecs_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate ECS cluster/service decommission score from C1-C5 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (C1-C5)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'C1': 45, 'C2': 30, 'C3': 0, 'C4': 5, 'C5': 5}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 85,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'C1': {'score': 45, 'weight': 45, 'description': 'CPU/Memory utilization'},
                'C2': {'score': 30, 'weight': 30, 'description': 'Task count trends'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'C1(45) + C2(30) + C4(5) + C5(5) = 85'
        }

    Example:
        >>> signals = {'C1': 45, 'C2': 30, 'C3': 0, 'C4': 5, 'C5': 5}
        >>> result = calculate_ecs_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 85, Tier: MUST

    Signal Descriptions:
        C1: CPU/Memory utilization <5% (HIGH confidence) - Zero workload
        C2: Task count trends - Low or zero running tasks (<10% desired)
        C3: Service health - Unhealthy or stopped services
        C4: Compute type split - EC2 vs Fargate efficiency issues
        C5: Cost efficiency - High cost per task ratio
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_ECS_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "C1": "CPU/Memory utilization <5% (HIGH: 0.90)",
            "C2": "Task count trends (low/zero tasks)",
            "C3": "Service health (unhealthy/stopped)",
            "C4": "Compute type split (efficiency)",
            "C5": "Cost efficiency (high cost per task)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown ECS signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential optimization candidate (manual review required)",
            "KEEP": "Active cluster/service (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"ECS score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def calculate_asg_score(
    signals: Dict[str, int],
    custom_weights: Optional[Dict[str, int]] = None,
    tier_thresholds: Optional[Dict[str, int]] = None,
) -> Dict:
    """
    Calculate Auto Scaling Group decommission score from A1-A5 signals.

    Scoring Logic:
    - Sum of weighted signals (0-100 scale)
    - Each signal contributes its weight if criteria met
    - Tier classification based on total score
    - High transparency: breakdown included in result

    Args:
        signals: Dictionary of signal scores (A1-A5)
                 Signal key → score (0 for absent, weight for present)
                 Example: {'A1': 40, 'A2': 25, 'A3': 20, 'A4': 0, 'A5': 5}
        custom_weights: Optional custom signal weights (override defaults)
        tier_thresholds: Optional custom tier thresholds (override defaults)

    Returns:
        Dictionary with scoring results:
        {
            'total_score': 90,
            'tier': 'MUST',
            'recommendation': 'Immediate decommission candidate',
            'signals': {
                'A1': {'score': 40, 'weight': 40, 'description': 'Scaling activity'},
                'A2': {'score': 25, 'weight': 25, 'description': 'Instance health'},
                ...
            },
            'confidence': 'High',
            'breakdown': 'A1(40) + A2(25) + A3(20) + A5(5) = 90'
        }

    Example:
        >>> signals = {'A1': 40, 'A2': 25, 'A3': 20, 'A4': 0, 'A5': 5}
        >>> result = calculate_asg_score(signals)
        >>> print(f"Score: {result['total_score']}, Tier: {result['tier']}")
        Score: 90, Tier: MUST

    Signal Descriptions:
        A1: Scaling activity - No scaling events for 90+ days (HIGH confidence)
        A2: Instance health - Unhealthy instances or all terminated
        A3: Capacity delta - min = max = desired = 0 (completely scaled down)
        A4: Launch config age - Outdated or unused launch configuration
        A5: Cost efficiency - High cost for low activity ratio
    """
    try:
        # Use custom weights if provided, otherwise defaults
        weights = custom_weights or DEFAULT_ASG_WEIGHTS
        thresholds = tier_thresholds or TIER_THRESHOLDS

        # Signal descriptions for transparency
        signal_descriptions = {
            "A1": "Scaling activity (no events 90+ days)",
            "A2": "Instance health (unhealthy/terminated)",
            "A3": "Capacity delta (min=max=desired=0)",
            "A4": "Launch config age (outdated/unused)",
            "A5": "Cost efficiency (high cost per activity)",
        }

        # Calculate total score
        total_score = 0
        signal_breakdown = {}
        contributing_signals = []

        for signal_id, signal_score in signals.items():
            if signal_id not in weights:
                logger.warning(f"Unknown ASG signal: {signal_id} (skipped)")
                continue

            weight = weights[signal_id]
            description = signal_descriptions.get(signal_id, f"Signal {signal_id}")

            # Add to total if signal is present (score > 0)
            if signal_score > 0:
                total_score += signal_score
                contributing_signals.append(f"{signal_id}({signal_score})")

            signal_breakdown[signal_id] = {
                "score": signal_score,
                "weight": weight,
                "description": description,
                "contributing": signal_score > 0,
            }

        # Determine tier
        tier = "KEEP"
        for tier_name, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                tier = tier_name
                break

        # Determine recommendation
        recommendations = {
            "MUST": "Immediate decommission candidate (high confidence)",
            "SHOULD": "Strong decommission candidate (review recommended)",
            "COULD": "Potential optimization candidate (manual review required)",
            "KEEP": "Active auto scaling group (no decommission action)",
        }
        recommendation = recommendations.get(tier, "Unknown")

        # Determine confidence based on signal coverage
        signal_count = len([s for s in signals.values() if s > 0])
        if signal_count >= 3:
            confidence = "High"
        elif signal_count >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"

        # Build breakdown string
        if contributing_signals:
            breakdown = " + ".join(contributing_signals) + f" = {total_score}"
        else:
            breakdown = "No signals detected = 0"

        return {
            "total_score": total_score,
            "tier": tier,
            "recommendation": recommendation,
            "signals": signal_breakdown,
            "confidence": confidence,
            "breakdown": breakdown,
            "signal_count": signal_count,
            "max_possible_score": sum(weights.values()),
        }

    except Exception as e:
        logger.error(f"ASG score calculation error: {e}", exc_info=True)
        return {
            "total_score": 0,
            "tier": "ERROR",
            "recommendation": f"Scoring error: {str(e)}",
            "signals": {},
            "confidence": "N/A",
            "breakdown": "Error",
            "error": str(e),
        }


def display_scoring_summary(scores: List[Dict], resource_type: str = "EC2") -> None:
    """
    Display scoring summary with Rich CLI formatting.

    Args:
        scores: List of scoring results from calculate_ec2_score() or calculate_workspaces_score()
        resource_type: 'EC2' or 'WorkSpaces' for display customization

    Example:
        >>> ec2_scores = [calculate_ec2_score(s) for s in signal_list]
        >>> display_scoring_summary(ec2_scores, resource_type='EC2')
    """
    try:
        # Count by tier
        tier_counts = {"MUST": 0, "SHOULD": 0, "COULD": 0, "KEEP": 0}

        for score in scores:
            tier = score.get("tier", "KEEP")
            if tier in tier_counts:
                tier_counts[tier] += 1

        # Create summary table
        table = create_table(
            title=f"{resource_type} Decommission Scoring Summary",
            columns=[
                {"header": "Tier", "style": "cyan bold"},
                {"header": "Count", "style": "yellow"},
                {"header": "Percentage", "style": "green"},
                {"header": "Recommendation", "style": "blue"},
            ],
        )

        total = len(scores)
        if total == 0:
            print_warning("⚠️  No scores to display")
            return

        recommendations = {
            "MUST": "Immediate decommission (80-100)",
            "SHOULD": "Review for decommission (50-79)",
            "COULD": "Manual review required (25-49)",
            "KEEP": "Active resource (<25)",
        }

        for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
            count = tier_counts[tier]
            percentage = (count / total * 100) if total > 0 else 0
            recommendation = recommendations[tier]

            table.add_row(tier, str(count), f"{percentage:.1f}%", recommendation)

        console.print(table)

        # Priority statistics
        priority_count = tier_counts["MUST"] + tier_counts["SHOULD"]
        priority_pct = (priority_count / total * 100) if total > 0 else 0

        if priority_count > 0:
            print_success(f"✅ Identified {priority_count} priority decommission candidates ({priority_pct:.1f}%)")
        else:
            print_info(f"ℹ️  No high-priority decommission candidates identified")

    except Exception as e:
        print_error(f"❌ Scoring summary display failed: {e}")
        logger.error(f"Display error: {e}", exc_info=True)


def export_scores_to_dataframe(scores: List[Dict], resource_ids: List[str]):
    """
    Export scoring results to pandas DataFrame.

    Args:
        scores: List of scoring results
        resource_ids: List of resource IDs (instance IDs or WorkSpace IDs)

    Returns:
        pandas DataFrame with scoring columns

    Example:
        >>> scores = [calculate_ec2_score(s) for s in signals_list]
        >>> df = export_scores_to_dataframe(scores, instance_ids)
        >>> df.to_excel('ec2-decommission-scores.xlsx', index=False)
    """
    import pandas as pd

    try:
        # Build DataFrame records
        records = []

        for i, score in enumerate(scores):
            resource_id = resource_ids[i] if i < len(resource_ids) else f"resource-{i}"

            record = {
                "resource_id": resource_id,
                "total_score": score.get("total_score", 0),
                "tier": score.get("tier", "KEEP"),
                "recommendation": score.get("recommendation", "N/A"),
                "confidence": score.get("confidence", "N/A"),
                "signal_count": score.get("signal_count", 0),
                "breakdown": score.get("breakdown", "N/A"),
            }

            records.append(record)

        df = pd.DataFrame(records)

        print_success(f"✅ Exported {len(df)} scores to DataFrame")

        return df

    except Exception as e:
        print_error(f"❌ DataFrame export failed: {e}")
        logger.error(f"Export error: {e}", exc_info=True)
        return pd.DataFrame()


# DataFrame-based Scoring Methods (Track 5: E1-E7/W1-W6 Implementation)


def score_ec2_dataframe(df):
    """
    Apply E1-E7 signals to EC2 DataFrame (100-point scale).

    Signal Breakdown (from ec2-workspaces.scoring.md):
    - E1: Compute Optimizer idle (60 points) - BACKBONE
    - E2: CloudWatch CPU/Network (10 points)
    - E3: CloudTrail activity (8 points)
    - E4: SSM heartbeat (8 points)
    - E5: Service attachment (6 points)
    - E6: Storage I/O (5 points)
    - E7: Cost savings (3 points)

    Classification:
    - MUST (80-100): Create Change Request → Stop → 7-day hold → Terminate
    - SHOULD (50-79): Off-hours stop schedule
    - COULD (25-49): Rightsizing or spot conversion
    - KEEP (<25): Production workload

    Args:
        df: DataFrame with enriched EC2 data (all 4 layers complete)

    Returns:
        DataFrame with 3 new columns: decommission_score, decommission_tier, signal_breakdown
    """
    import pandas as pd
    import json

    df["decommission_score"] = 0
    df["signal_breakdown"] = "{}"
    df["decommission_tier"] = "KEEP"

    for idx, row in df.iterrows():
        score = 0
        signals = {}

        # E1: Compute Optimizer idle (60 points - BACKBONE SIGNAL)
        if row.get("compute_optimizer_finding") == "Idle":
            score += 60
            signals["E1"] = 60

        # E2: CloudWatch CPU/Network (10 points)
        p95_cpu = row.get("p95_cpu_utilization", 100)
        p95_network = row.get("p95_network_bytes", float("inf"))
        E2_NETWORK_THRESHOLD_MB = 10  # Configurable parameter

        if p95_cpu <= 3.0 and p95_network <= (E2_NETWORK_THRESHOLD_MB * 1024 * 1024):
            score += 10
            signals["E2"] = 10

        # E3: CloudTrail activity (8 points)
        if row.get("days_since_activity", 0) >= 90:
            score += 8
            signals["E3"] = 8

        # E4: SSM heartbeat (8 points)
        if row.get("ssm_ping_status") != "Online" or row.get("ssm_days_since_ping", 0) > 14:
            score += 8
            signals["E4"] = 8

        # E5: Service attachment (6 points)
        if not row.get("attached_to_service", False):
            score += 6
            signals["E5"] = 6

        # E6: Storage I/O (5 points)
        if row.get("p95_disk_io", float("inf")) == 0:
            score += 5
            signals["E6"] = 5

        # E7: Cost savings (3 points)
        if row.get("cost_explorer_savings_terminate", 0) > 0:
            score += 3
            signals["E7"] = 3

        # Classification
        if score >= 80:
            tier = "MUST"
        elif score >= 50:
            tier = "SHOULD"
        elif score >= 25:
            tier = "COULD"
        else:
            tier = "KEEP"

        df.at[idx, "decommission_score"] = score
        df.at[idx, "decommission_tier"] = tier
        df.at[idx, "signal_breakdown"] = json.dumps(signals)

    return df


def score_workspaces_dataframe(df):
    """
    Apply W1-W6 signals to WorkSpaces DataFrame (100-point scale).

    Signal Breakdown:
    - W1: Connection recency (45 points) - ≥60 days since last connection
    - W2: CloudWatch usage (25 points) - UserConnected sum = 0
    - W3: Billing vs usage (10/5 points) - Dynamic break-even via Pricing API
    - W4: Cost Optimizer policy (10 points) - Flagged for termination
    - W5: Admin activity (5 points) - No admin changes for 90 days
    - W6: User status (5 points) - User NOT in Identity Center

    Args:
        df: DataFrame with enriched WorkSpaces data (all 4 layers complete)

    Returns:
        DataFrame with 3 new columns: decommission_score, decommission_tier, signal_breakdown
    """
    import pandas as pd
    import json

    df["decommission_score"] = 0
    df["signal_breakdown"] = "{}"
    df["decommission_tier"] = "KEEP"

    for idx, row in df.iterrows():
        score = 0
        signals = {}

        # W1: Connection recency (45 points)
        days_since_connection = row.get("days_since_connection", 0)
        if days_since_connection >= 60:
            score += 45
            signals["W1"] = 45

        # W2: CloudWatch usage (25 points)
        if row.get("user_connected_sum", 1) == 0:
            score += 25
            signals["W2"] = 25

        # W3: Billing vs usage (10/5 points)
        hourly_usage = row.get("hourly_usage_hours_mtd", 0)
        dynamic_breakeven = row.get("dynamic_breakeven_hours", 85)  # From Pricing API

        if hourly_usage < dynamic_breakeven:
            score += 10
            signals["W3"] = 10
        elif hourly_usage >= dynamic_breakeven:
            score += 5
            signals["W3"] = 5

        # W4: Cost Optimizer policy (10 points)
        if row.get("cost_optimizer_flags_termination", False):
            score += 10
            signals["W4"] = 10

        # W5: Admin activity (5 points)
        if row.get("no_admin_activity_90d", False):
            score += 5
            signals["W5"] = 5

        # W6: User status (5 points - Identity Center)
        if row.get("user_not_in_identity_center", False):
            score += 5
            signals["W6"] = 5

        # Classification (same thresholds)
        if score >= 80:
            tier = "MUST"
        elif score >= 50:
            tier = "SHOULD"
        elif score >= 25:
            tier = "COULD"
        else:
            tier = "KEEP"

        df.at[idx, "decommission_score"] = score
        df.at[idx, "decommission_tier"] = tier
        df.at[idx, "signal_breakdown"] = json.dumps(signals)

    return df


def display_tier_distribution(df) -> None:
    """
    Display decommission tier distribution with Rich table.

    Args:
        df: DataFrame with decommission_tier and decommission_score columns

    Example:
        >>> df = score_ec2_dataframe(enriched_df)
        >>> display_tier_distribution(df)
    """
    import pandas as pd

    if "decommission_tier" not in df.columns:
        print_warning("⚠️  No decommission_tier column found in DataFrame")
        return

    # Tier distribution
    tier_counts = df["decommission_tier"].value_counts()
    total = len(df)

    summary_rows = []
    for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
        count = tier_counts.get(tier, 0)
        pct = (count / total * 100) if total > 0 else 0
        summary_rows.append([tier, f"{count} resources ({pct:.1f}%)"])

    # Add separator and top 5 decommission candidates (MUST tier)
    if "decommission_score" in df.columns:
        must_candidates = df[df["decommission_tier"] == "MUST"].nlargest(5, "decommission_score")
        if len(must_candidates) > 0:
            summary_rows.append(["", ""])  # Separator
            summary_rows.append(["Top Candidates", "Score"])
            for idx, row in must_candidates.iterrows():
                # Try multiple possible identifier columns
                identifier = row.get(
                    "identifier", row.get("resource_id", row.get("instance_id", row.get("workspace_id", "Unknown")))
                )
                score = row.get("decommission_score", 0)
                summary_rows.append([f"  {str(identifier)[:30]}", f"{score:.0f}"])

    tier_table = create_table("Decommission Tier Distribution", ["Tier", "Count"], summary_rows)
    console.print(tier_table)

    # Print additional insights
    priority_count = tier_counts.get("MUST", 0) + tier_counts.get("SHOULD", 0)
    priority_pct = (priority_count / total * 100) if total > 0 else 0

    if priority_count > 0:
        print_success(f"✅ Identified {priority_count} priority decommission candidates ({priority_pct:.1f}%)")
    else:
        print_info(f"ℹ️  No high-priority decommission candidates identified")


def calculate_production_ready_score(validation_results: Dict) -> Dict:
    """
    Calculate production-ready score (Section 1A framework).

    Scoring Categories:
    - Data Availability: /40 points (Excel validated, MCP ≥99.5%, signals present, provenance)
    - Workflow Execution: /30 points (MCP queries, CLI tested, notebook operational)
    - Technical Credibility: /30 points (src/runbooks/ changes, execution evidence, manager summary)

    Threshold: ≥70/100 for production-ready status

    Args:
        validation_results: Dictionary with validation test results

    Returns:
        Dictionary with score breakdown and status
    """
    score = {
        "data_availability": 0,  # /40
        "workflow_execution": 0,  # /30
        "technical_credibility": 0,  # /30
        "total": 0,
        "threshold": 70,
        "status": "BLOCKED",
    }

    # Data Availability (40 points)
    if validation_results.get("excel_validated"):
        score["data_availability"] += 10
    if validation_results.get("mcp_accuracy", 0) >= 0.995:
        score["data_availability"] += 15
    if validation_results.get("decommission_signals_present"):
        score["data_availability"] += 10
    if validation_results.get("data_provenance_documented"):
        score["data_availability"] += 5

    # Workflow Execution (30 points)
    if validation_results.get("mcp_queries_executed"):
        score["workflow_execution"] += 15
    if validation_results.get("cli_tested"):
        score["workflow_execution"] += 10
    if validation_results.get("notebook_operational"):
        score["workflow_execution"] += 5

    # Technical Credibility (30 points)
    if validation_results.get("src_runbooks_changes"):
        score["technical_credibility"] += 10
    if validation_results.get("execution_evidence"):
        score["technical_credibility"] += 10
    if validation_results.get("manager_summary_concise"):
        score["technical_credibility"] += 10

    # Calculate total
    score["total"] = score["data_availability"] + score["workflow_execution"] + score["technical_credibility"]

    # Determine status
    if score["total"] >= 90:
        score["status"] = "PRODUCTION-READY"
    elif score["total"] >= 70:
        score["status"] = "ACCEPTABLE"
    else:
        score["status"] = "BLOCKED"

    return score


# ═════════════════════════════════════════════════════════════════════════════
# v1.1.29: VPC ADAPTIVE SCORING ENGINE
# ═════════════════════════════════════════════════════════════════════════════

# VPC Endpoint Signal Weights (V1-V10) - v1.1.29: Adaptive Scoring Framework
# AWS Ref: https://docs.aws.amazon.com/vpc/latest/privatelink/endpoint-services-overview.html
DEFAULT_VPCE_WEIGHTS = {
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 1: HIGH-CONFIDENCE SIGNALS (85 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # V1: Zero VPC Cost 90D - No associated billable usage
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-pricing.html
    # Confidence: 0.95 | Tier 1 (AWS Cost Explorer validation)
    "V1": 40,
    # V2: No Service Dependencies - Not attached to active services
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html
    # Confidence: 0.90 | Tier 1 (EC2 API validation)
    "V2": 20,
    # V3: Minimal Interface Configuration - Basic ENI setup only
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/privatelink/vpce-interface.html
    # Confidence: 0.85 | Tier 1 (configuration analysis)
    "V3": 10,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 2: MEDIUM-CONFIDENCE SIGNALS (40 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # V4: Non-Production VPC - VPC tagged as dev/test/sandbox
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-tagging.html
    # Confidence: 0.80 | Tier 2 (tag-based classification)
    "V4": 5,
    # V5: Age >180 Days Unused - Created >180d ago with minimal activity
    # Confidence: 0.75 | Tier 2 (temporal analysis)
    "V5": 25,
    # V6: Flow Logs Zero Traffic - VPC Flow Logs show 0 bytes transferred
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
    # Confidence: 0.95 | Tier 2 (CONDITIONAL - requires Flow Logs enabled)
    # NOTE: This signal is ONLY included when Flow Logs available
    "V6": 15,
    # V7: Security Group Permissive - SG allows 0.0.0.0/0 without usage
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html
    # Confidence: 0.70 | Tier 2 (security configuration)
    "V7": 10,
    # V8: Endpoint Policy Broad - Policy allows * actions without usage
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html
    # Confidence: 0.70 | Tier 2 (policy analysis)
    "V8": 5,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 3: LOWER-CONFIDENCE SIGNALS (15 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # V9: Network Insights Unreachable - Reachability Analyzer shows no paths
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html
    # Confidence: 0.75 | Tier 3 (reachability validation)
    "V9": 10,
    # V10: Multi-Region Redundancy Missing - No equivalent endpoint in other regions
    # Confidence: 0.65 | Tier 3 (architectural analysis)
    "V10": 5,
}

# NAT Gateway Signal Weights (N1-N10) - v1.1.29: Adaptive Scoring Framework
# AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
DEFAULT_NAT_WEIGHTS = {
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 1: HIGH-CONFIDENCE SIGNALS (85 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # N1: Zero Data Transfer 90D - BytesOutToDestination + BytesOutToSource = 0
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway-cloudwatch.html
    # Confidence: 0.95 | Tier 1 (CloudWatch metrics validation)
    "N1": 40,
    # N2: No Route Table Associations - NAT not referenced in route tables
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html
    # Confidence: 0.90 | Tier 1 (route table analysis)
    "N2": 20,
    # N3: Idle Connections - ActiveConnectionCount = 0 over 90 days
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway-cloudwatch.html
    # Confidence: 0.85 | Tier 1 (connection metrics)
    "N3": 10,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 2: MEDIUM-CONFIDENCE SIGNALS (40 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # N4: Non-Production VPC - VPC tagged as dev/test/sandbox
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-tagging.html
    # Confidence: 0.80 | Tier 2 (tag-based classification)
    "N4": 5,
    # N5: Age >180 Days Idle - Created >180d ago with minimal usage
    # Confidence: 0.75 | Tier 2 (temporal analysis)
    "N5": 25,
    # N6: Flow Logs Zero Traffic - VPC Flow Logs show 0 NAT gateway traffic
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
    # Confidence: 0.95 | Tier 2 (CONDITIONAL - requires Flow Logs enabled)
    # NOTE: This signal is ONLY included when Flow Logs available
    "N6": 15,
    # N7: High Cost Low Usage - Monthly cost >$50 with <100MB transferred
    # AWS Ref: https://aws.amazon.com/vpc/pricing/
    # Confidence: 0.80 | Tier 2 (cost efficiency)
    "N7": 10,
    # N8: No Elastic IP Usage - EIP allocated but no egress traffic
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-eips.html
    # Confidence: 0.75 | Tier 2 (IP allocation waste)
    "N8": 5,
    # ═══════════════════════════════════════════════════════════════════════
    # TIER 3: LOWER-CONFIDENCE SIGNALS (15 points max)
    # ═══════════════════════════════════════════════════════════════════════
    # N9: Packet Drop Rate High - PacketsDropCount >10% of total packets
    # AWS Ref: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway-cloudwatch.html
    # Confidence: 0.70 | Tier 3 (network health)
    "N9": 10,
    # N10: Multi-AZ Redundancy Missing - No equivalent NAT in other AZs
    # Confidence: 0.65 | Tier 3 (architectural analysis)
    "N10": 5,
}


def calculate_vpc_score_adaptive(signals: List[Dict[str, any]], flow_logs_enabled: bool, resource_type: str) -> dict:
    """
    Calculate adaptive VPC decommission score with Flow Logs availability awareness.

    v1.1.29 Enhancement: Supports both WITH and WITHOUT Flow Logs scenarios
    with graceful degradation and confidence adjustment.

    Adaptive Scoring Strategy:
    - WITH Flow Logs: V1-V10/N1-N10 (125pt max) → normalized to 0-100, confidence boost +0.15
    - WITHOUT Flow Logs: V1-V5+V7-V10/N1-N5+N7-N10 (110pt max) → normalized to 0-100, no boost

    Args:
        signals: List of signal dictionaries with keys:
            - name: Signal name (e.g., 'V1', 'V2', 'N1', 'N2')
            - confidence: Signal confidence (0.0-1.0)
            - description: Human-readable signal description
        flow_logs_enabled: Boolean indicating if VPC Flow Logs are ACTIVE for this VPC
        resource_type: 'VPCE' (VPC Endpoint) or 'NAT' (NAT Gateway)

    Returns:
        Dictionary with keys:
            - score: Normalized score (0-100 scale)
            - raw_score: Actual points earned (0-125 or 0-110)
            - max_possible: Maximum possible score (125 or 110)
            - flow_logs_enabled: Boolean Flow Logs availability
            - confidence: Adjusted confidence (0.0-1.0) with Flow Logs boost
            - tier: Decommission tier ('MUST', 'SHOULD', 'COULD', 'KEEP')
            - signal_count: Number of signals detected
            - resource_type: 'VPCE' or 'NAT'

    Business Value:
        - Enables immediate VPC resource scoring without Flow Logs infrastructure
        - Transparent confidence adjustment (+0.15 boost when Flow Logs available)
        - Graceful degradation maintains scoring accuracy without V6/N6 signals

    Example:
        >>> # Scenario 1: WITH Flow Logs
        >>> signals = [
        ...     {'name': 'V1', 'confidence': 0.95, 'description': 'Zero VPC cost'},
        ...     {'name': 'V2', 'confidence': 0.90, 'description': 'No dependencies'},
        ...     {'name': 'V6', 'confidence': 0.95, 'description': 'Flow Logs zero traffic'}
        ... ]
        >>> result = calculate_vpc_score_adaptive(signals, flow_logs_enabled=True, resource_type='VPCE')
        >>> print(result)
        {
            'score': 60,  # (40+20+15)/125 * 100 = 60
            'raw_score': 75,
            'max_possible': 125,
            'flow_logs_enabled': True,
            'confidence': 0.95,  # (0.95+0.90+0.95)/3 + 0.15 = 0.95 (capped)
            'tier': 'SHOULD',
            'signal_count': 3,
            'resource_type': 'VPCE'
        }

        >>> # Scenario 2: WITHOUT Flow Logs
        >>> signals = [
        ...     {'name': 'V1', 'confidence': 0.95, 'description': 'Zero VPC cost'},
        ...     {'name': 'V2', 'confidence': 0.90, 'description': 'No dependencies'}
        ... ]
        >>> result = calculate_vpc_score_adaptive(signals, flow_logs_enabled=False, resource_type='VPCE')
        >>> print(result)
        {
            'score': 55,  # (40+20)/110 * 100 = 55
            'raw_score': 60,
            'max_possible': 110,
            'flow_logs_enabled': False,
            'confidence': 0.93,  # (0.95+0.90)/2 = 0.925 (no boost)
            'tier': 'SHOULD',
            'signal_count': 2,
            'resource_type': 'VPCE'
        }
    """
    # Select signal weight mapping
    if resource_type == "VPCE":
        signal_weights = DEFAULT_VPCE_WEIGHTS
    elif resource_type == "NAT":
        signal_weights = DEFAULT_NAT_WEIGHTS
    else:
        raise ValueError(f"Unsupported resource_type: {resource_type}. Must be 'VPCE' or 'NAT'")

    # Calculate dynamic max_possible score
    if flow_logs_enabled:
        # Full signal framework (includes V6/N6 worth 15 points)
        max_possible = 125
    else:
        # Graceful degradation (excludes V6/N6)
        max_possible = 110

    # Calculate raw score (sum of signal weights)
    raw_score = 0
    for signal in signals:
        signal_name = signal.get("name", "")

        # Skip V6/N6 if Flow Logs not enabled (graceful degradation)
        if not flow_logs_enabled and signal_name in ["V6", "N6"]:
            logger.debug(f"Skipping signal {signal_name} (Flow Logs not enabled)")
            continue

        signal_weight = signal_weights.get(signal_name, 0)
        raw_score += signal_weight

    # Normalize score to 0-100 scale
    normalized_score = int((raw_score / max_possible) * 100) if max_possible > 0 else 0

    # Calculate base confidence (average of signal confidences)
    if signals:
        base_confidence = sum(s.get("confidence", 0.75) for s in signals) / len(signals)
    else:
        base_confidence = 0.0

    # Apply Flow Logs confidence boost (+0.15 when ground truth available)
    confidence_boost = 0.15 if flow_logs_enabled else 0.0
    adjusted_confidence = min(0.95, base_confidence + confidence_boost)

    # Classify tier
    def classify_tier(score: int) -> str:
        if score >= 80:
            return "MUST"
        elif score >= 50:
            return "SHOULD"
        elif score >= 25:
            return "COULD"
        else:
            return "KEEP"

    tier = classify_tier(normalized_score)

    return {
        "score": normalized_score,
        "raw_score": raw_score,
        "max_possible": max_possible,
        "flow_logs_enabled": flow_logs_enabled,
        "confidence": round(adjusted_confidence, 2),
        "tier": tier,
        "signal_count": len(signals),
        "resource_type": resource_type,
    }
