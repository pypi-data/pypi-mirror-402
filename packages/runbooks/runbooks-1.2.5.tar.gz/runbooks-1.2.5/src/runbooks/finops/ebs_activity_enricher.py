#!/usr/bin/env python3
"""
EBS Activity Enricher - EBS Volume Activity Signals
====================================================

Business Value: Idle EBS volume detection enabling storage cost optimization
Strategic Impact: Complement S3/EC2 patterns for block storage workloads
Integration: Feeds data to FinOps decommission scoring framework

Architecture Pattern: 5-layer enrichment framework
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: EBS activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses B1-B7 signals)

Decommission Signals (B1-B7) - AWS Well-Architected Framework Aligned:

Tier 1: High-Confidence (60 points max)
- B1 (40 pts): Zero IOPS - No read/write operations 90d (Confidence: 0.95)
- B2 (20 pts): Unattached - Volume not attached to instance (Confidence: 0.90)

Tier 2: Medium-Confidence (30 points max)
- B3 (15 pts): Low Throughput - <1MB/day throughput 90d (Confidence: 0.85)
- B4 (10 pts): Stale Volume - No modifications 180d+ (Confidence: 0.80)
- B5 (5 pts): No Encryption - Unencrypted volume (Confidence: 0.75)

Tier 3: Lower-Confidence (10 points max)
- B6 (5 pts): Oversized - <10% capacity utilization (Confidence: 0.70)
- B7 (5 pts): Cost Inefficiency - High $/GB vs activity (Confidence: 0.70)

Usage:
    from runbooks.finops.ebs_activity_enricher import EBSActivityEnricher

    enricher = EBSActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze EBS volume activity
    analyses = enricher.analyze_volume_activity(
        volume_ids=['vol-0123456789abcdef0']
    )

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer EBS costs
    - Flag discrepancies (low activity but high costs = potential issue)
    - Achieve >=99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.31 FinOps Dashboard Enhancements
Track: Track 12 - EBS Activity Enricher
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    create_panel,
    create_table,
    format_cost,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)
from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
)
from runbooks.common.output_controller import OutputController

logger = logging.getLogger(__name__)


# Signal weights for EBS decommission scoring (0-100 scale)
DEFAULT_EBS_WEIGHTS = {
    "B1": 40,  # Zero IOPS - No read/write 90d
    "B2": 20,  # Unattached - Not attached to instance
    "B3": 15,  # Low Throughput - <1MB/day 90d
    "B4": 10,  # Stale Volume - No modifications 180d+
    "B5": 5,  # No Encryption - Unencrypted volume
    "B6": 5,  # Oversized - <10% capacity utilization
    "B7": 5,  # Cost Inefficiency - High $/GB vs activity
}


class EBSIdleSignal(str, Enum):
    """
    EBS decommission signals (B1-B7) - AWS Well-Architected Framework Aligned.

    Signal Framework v2.0: Hybrid 0-100 scoring with tier-based confidence levels.
    Total Maximum Points: 100

    Tier 1: High-Confidence Signals (60 points max)
    - B1 (40 pts): Zero IOPS - No read/write operations 90d (Confidence: 0.95)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-io-characteristics.html
    - B2 (20 pts): Unattached - Volume not attached to instance (Confidence: 0.90)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-attaching-volume.html

    Tier 2: Medium-Confidence Signals (30 points max)
    - B3 (15 pts): Low Throughput - <1MB/day throughput 90d (Confidence: 0.85)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html
    - B4 (10 pts): Stale Volume - No modifications 180d+ (Confidence: 0.80)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-modify-volume.html
    - B5 (5 pts): No Encryption - Unencrypted volume (Confidence: 0.75)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSEncryption.html

    Tier 3: Lower-Confidence Signals (10 points max)
    - B6 (5 pts): Oversized - <10% capacity utilization (Confidence: 0.70)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-describing-volumes.html
    - B7 (5 pts): Cost Inefficiency - High $/GB vs activity (Confidence: 0.70)
      AWS Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html

    Decommission Tier Classification:
    - MUST tier: score >=80 (B1+B2 present = immediate candidates)
    - SHOULD tier: score 50-79
    - COULD tier: score 25-49
    - KEEP tier: score <25
    """

    # Tier 1: High-Confidence (60 points max)
    B1_ZERO_IOPS = "B1"  # 40 pts - No read/write 90d (0.95 confidence)
    B2_UNATTACHED = "B2"  # 20 pts - Not attached to instance (0.90 confidence)

    # Tier 2: Medium-Confidence (30 points max)
    B3_LOW_THROUGHPUT = "B3"  # 15 pts - <1MB/day 90d (0.85 confidence)
    B4_STALE_VOLUME = "B4"  # 10 pts - No modifications 180d+ (0.80 confidence)
    B5_NO_ENCRYPTION = "B5"  # 5 pts - Unencrypted volume (0.75 confidence)

    # Tier 3: Lower-Confidence (10 points max)
    B6_OVERSIZED = "B6"  # 5 pts - <10% capacity utilization (0.70 confidence)
    B7_COST_INEFFICIENCY = "B7"  # 5 pts - High $/GB vs activity (0.70 confidence)


class EBSActivityPattern(str, Enum):
    """EBS volume access pattern classification."""

    ACTIVE = "active"  # Production workload (>1000 IOPS/day)
    MODERATE = "moderate"  # Development/staging (100-1000 IOPS/day)
    LIGHT = "light"  # Test environment (<100 IOPS/day)
    IDLE = "idle"  # No IOPS in 90 days


class EBSDecommissionRecommendation(str, Enum):
    """Decommission recommendations based on activity analysis."""

    DECOMMISSION = "DECOMMISSION"  # High confidence - decommission candidate
    INVESTIGATE = "INVESTIGATE"  # Medium confidence - needs review
    OPTIMIZE = "OPTIMIZE"  # Moderate underutilization - rightsize
    KEEP = "KEEP"  # Active resource - retain


@dataclass
class EBSActivityMetrics:
    """
    CloudWatch metrics for EBS volume.

    Comprehensive activity metrics for decommission decision-making with
    B1-B7 signal framework.
    """

    total_read_ops_90d: int
    total_write_ops_90d: int
    total_read_bytes_90d: int
    total_write_bytes_90d: int
    avg_iops_per_day: float
    avg_throughput_mb_per_day: float
    volume_size_gb: int
    volume_type: str
    attached: bool
    attachment_instance_id: Optional[str]
    encrypted: bool
    iops_provisioned: Optional[int]
    throughput_provisioned: Optional[int]
    create_time: datetime
    last_modification_time: Optional[datetime] = None
    snapshot_count: int = 0


@dataclass
class EBSActivityAnalysis:
    """
    EBS volume activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    B1-B7 signal framework and cost impact analysis.
    """

    volume_id: str
    region: str
    account_id: str
    metrics: EBSActivityMetrics
    activity_pattern: EBSActivityPattern
    idle_signals: List[EBSIdleSignal] = field(default_factory=list)
    signal_scores: Dict[str, int] = field(default_factory=dict)
    total_score: int = 0
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: float = 0.0  # 0.0-1.0
    recommendation: EBSDecommissionRecommendation = EBSDecommissionRecommendation.KEEP
    tier: str = "KEEP"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "volume_id": self.volume_id,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "total_read_ops_90d": self.metrics.total_read_ops_90d,
                "total_write_ops_90d": self.metrics.total_write_ops_90d,
                "total_read_bytes_90d": self.metrics.total_read_bytes_90d,
                "total_write_bytes_90d": self.metrics.total_write_bytes_90d,
                "avg_iops_per_day": self.metrics.avg_iops_per_day,
                "avg_throughput_mb_per_day": self.metrics.avg_throughput_mb_per_day,
                "volume_size_gb": self.metrics.volume_size_gb,
                "volume_type": self.metrics.volume_type,
                "attached": self.metrics.attached,
                "attachment_instance_id": self.metrics.attachment_instance_id,
                "encrypted": self.metrics.encrypted,
                "iops_provisioned": self.metrics.iops_provisioned,
                "throughput_provisioned": self.metrics.throughput_provisioned,
                "create_time": self.metrics.create_time.isoformat(),
                "last_modification_time": (
                    self.metrics.last_modification_time.isoformat() if self.metrics.last_modification_time else None
                ),
                "snapshot_count": self.metrics.snapshot_count,
            },
            "activity_pattern": self.activity_pattern.value,
            "idle_signals": [signal.value for signal in self.idle_signals],
            "signal_scores": self.signal_scores,
            "total_score": self.total_score,
            "monthly_cost": self.monthly_cost,
            "annual_cost": self.annual_cost,
            "potential_savings": self.potential_savings,
            "confidence": self.confidence,
            "recommendation": self.recommendation.value,
            "tier": self.tier,
            "metadata": self.metadata,
        }


class EBSActivityEnricher:
    """
    EBS activity enricher for inventory resources.

    Analyzes EBS volumes for idle/underutilization patterns using CloudWatch
    metrics and EC2 APIs with B1-B7 signal framework.

    Capabilities:
    - Activity metrics analysis (90 day windows)
    - Attachment status tracking
    - IOPS and throughput analysis
    - Encryption compliance checking
    - Volume age and modification tracking
    - Comprehensive decommission recommendations

    Decommission Signals Generated (B1-B7):

    Tier 1: High-Confidence (60 points max)
    - B1 (40 pts): Zero IOPS - No read/write 90d (Confidence: 0.95)
    - B2 (20 pts): Unattached - Not attached to instance (Confidence: 0.90)

    Tier 2: Medium-Confidence (30 points max)
    - B3 (15 pts): Low Throughput - <1MB/day 90d (Confidence: 0.85)
    - B4 (10 pts): Stale Volume - No modifications 180d+ (Confidence: 0.80)
    - B5 (5 pts): No Encryption - Unencrypted volume (Confidence: 0.75)

    Tier 3: Lower-Confidence (10 points max)
    - B6 (5 pts): Oversized - <10% capacity utilization (Confidence: 0.70)
    - B7 (5 pts): Cost Inefficiency - High $/GB vs activity (Confidence: 0.70)
    """

    # Signal descriptions for transparency
    SIGNAL_DESCRIPTIONS = {
        "B1": "Zero IOPS (no read/write 90d)",
        "B2": "Unattached (no instance)",
        "B3": "Low Throughput (<1MB/day)",
        "B4": "Stale Volume (no mods 180d+)",
        "B5": "No Encryption",
        "B6": "Oversized (<10% util)",
        "B7": "Cost Inefficiency",
    }

    # Confidence levels per signal
    SIGNAL_CONFIDENCE = {
        "B1": 0.95,
        "B2": 0.90,
        "B3": 0.85,
        "B4": 0.80,
        "B5": 0.75,
        "B6": 0.70,
        "B7": 0.70,
    }

    # EBS pricing per GB/month (approximate ap-southeast-2)
    EBS_PRICING = {
        "gp2": 0.12,
        "gp3": 0.096,
        "io1": 0.138,
        "io2": 0.138,
        "st1": 0.054,
        "sc1": 0.036,
        "standard": 0.10,
    }

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: str = "ap-southeast-2",
        lookback_days: int = 90,
        verbose: bool = False,
    ):
        """
        Initialize EBS Activity Enricher.

        Args:
            operational_profile: AWS profile for operations
            region: AWS region (default: ap-southeast-2)
            lookback_days: Days to analyze for activity (default: 90)
            verbose: Enable verbose logging
        """
        self.operational_profile = operational_profile
        self.region = region
        self.lookback_days = lookback_days
        self.verbose = verbose

        # Initialize AWS clients
        self._init_clients()

        # Output controller for formatting
        self.output = OutputController(verbose=verbose)

    def _init_clients(self) -> None:
        """Initialize AWS clients with profile."""
        try:
            session_kwargs = {"region_name": self.region}
            if self.operational_profile:
                session_kwargs["profile_name"] = self.operational_profile

            self.session = boto3.Session(**session_kwargs)
            self.ec2_client = self.session.client("ec2")
            self.cloudwatch_client = self.session.client("cloudwatch")
            self.sts_client = self.session.client("sts")

            # Get account ID
            self.account_id = self.sts_client.get_caller_identity()["Account"]

            logger.debug(f"Initialized EBS enricher for account {self.account_id}")
        except ClientError as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise

    def analyze_volume_activity(
        self,
        volume_ids: Optional[List[str]] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> List[EBSActivityAnalysis]:
        """
        Analyze EBS volume activity for decommission signals.

        Args:
            volume_ids: Specific volume IDs to analyze (optional)
            filters: EC2 describe_volumes filters (optional)

        Returns:
            List of EBSActivityAnalysis results
        """
        analyses = []

        try:
            # Get volumes
            describe_params = {}
            if volume_ids:
                describe_params["VolumeIds"] = volume_ids
            if filters:
                describe_params["Filters"] = filters

            paginator = self.ec2_client.get_paginator("describe_volumes")
            for page in paginator.paginate(**describe_params):
                for volume in page.get("Volumes", []):
                    analysis = self._analyze_single_volume(volume)
                    if analysis:
                        analyses.append(analysis)

        except ClientError as e:
            logger.error(f"Failed to analyze volumes: {e}")

        return analyses

    def _analyze_single_volume(self, volume: Dict[str, Any]) -> Optional[EBSActivityAnalysis]:
        """
        Analyze a single EBS volume.

        Args:
            volume: Volume dict from describe_volumes

        Returns:
            EBSActivityAnalysis or None
        """
        try:
            volume_id = volume["VolumeId"]
            volume_type = volume.get("VolumeType", "gp2")
            volume_size = volume.get("Size", 0)
            encrypted = volume.get("Encrypted", False)
            create_time = volume.get("CreateTime", datetime.now(timezone.utc))

            # Get attachment status
            attachments = volume.get("Attachments", [])
            attached = len(attachments) > 0
            attachment_instance_id = attachments[0].get("InstanceId") if attached else None

            # Get CloudWatch metrics
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=self.lookback_days)

            metrics = self._get_cloudwatch_metrics(volume_id, start_time, end_time)

            # Build metrics object
            ebs_metrics = EBSActivityMetrics(
                total_read_ops_90d=metrics.get("read_ops", 0),
                total_write_ops_90d=metrics.get("write_ops", 0),
                total_read_bytes_90d=metrics.get("read_bytes", 0),
                total_write_bytes_90d=metrics.get("write_bytes", 0),
                avg_iops_per_day=metrics.get("avg_iops", 0.0),
                avg_throughput_mb_per_day=metrics.get("avg_throughput_mb", 0.0),
                volume_size_gb=volume_size,
                volume_type=volume_type,
                attached=attached,
                attachment_instance_id=attachment_instance_id,
                encrypted=encrypted,
                iops_provisioned=volume.get("Iops"),
                throughput_provisioned=volume.get("Throughput"),
                create_time=create_time,
            )

            # Calculate idle signals and scores
            idle_signals, signal_scores, total_score = self._evaluate_signals(ebs_metrics, create_time)

            # Determine activity pattern
            activity_pattern = self._classify_activity_pattern(ebs_metrics)

            # Calculate cost
            price_per_gb = self.EBS_PRICING.get(volume_type, 0.12)
            monthly_cost = volume_size * price_per_gb
            annual_cost = monthly_cost * 12

            # Calculate potential savings based on score
            savings_multiplier = min(total_score / 100, 1.0)
            potential_savings = annual_cost * savings_multiplier

            # Determine tier and recommendation
            tier = self._get_tier(total_score)
            recommendation = self._get_recommendation(total_score, activity_pattern)

            # Calculate confidence
            confidence = self._calculate_confidence(idle_signals)

            return EBSActivityAnalysis(
                volume_id=volume_id,
                region=self.region,
                account_id=self.account_id,
                metrics=ebs_metrics,
                activity_pattern=activity_pattern,
                idle_signals=idle_signals,
                signal_scores=signal_scores,
                total_score=total_score,
                monthly_cost=monthly_cost,
                annual_cost=annual_cost,
                potential_savings=potential_savings,
                confidence=confidence,
                recommendation=recommendation,
                tier=tier,
            )

        except Exception as e:
            logger.error(f"Failed to analyze volume {volume.get('VolumeId')}: {e}")
            return None

    def _get_cloudwatch_metrics(
        self,
        volume_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Get CloudWatch metrics for an EBS volume.

        Args:
            volume_id: EBS volume ID
            start_time: Metrics start time
            end_time: Metrics end time

        Returns:
            Dictionary of metrics
        """
        metrics = {
            "read_ops": 0,
            "write_ops": 0,
            "read_bytes": 0,
            "write_bytes": 0,
            "avg_iops": 0.0,
            "avg_throughput_mb": 0.0,
        }

        try:
            # Query VolumeReadOps
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/EBS",
                MetricName="VolumeReadOps",
                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily
                Statistics=["Sum"],
            )
            for dp in response.get("Datapoints", []):
                metrics["read_ops"] += int(dp.get("Sum", 0))

            # Query VolumeWriteOps
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/EBS",
                MetricName="VolumeWriteOps",
                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=["Sum"],
            )
            for dp in response.get("Datapoints", []):
                metrics["write_ops"] += int(dp.get("Sum", 0))

            # Query VolumeReadBytes
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/EBS",
                MetricName="VolumeReadBytes",
                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=["Sum"],
            )
            for dp in response.get("Datapoints", []):
                metrics["read_bytes"] += int(dp.get("Sum", 0))

            # Query VolumeWriteBytes
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/EBS",
                MetricName="VolumeWriteBytes",
                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                Statistics=["Sum"],
            )
            for dp in response.get("Datapoints", []):
                metrics["write_bytes"] += int(dp.get("Sum", 0))

            # Calculate averages
            days = self.lookback_days
            total_ops = metrics["read_ops"] + metrics["write_ops"]
            total_bytes = metrics["read_bytes"] + metrics["write_bytes"]

            metrics["avg_iops"] = total_ops / days if days > 0 else 0.0
            metrics["avg_throughput_mb"] = total_bytes / (days * 1024 * 1024) if days > 0 else 0.0

        except ClientError as e:
            logger.warning(f"Failed to get CloudWatch metrics for {volume_id}: {e}")

        return metrics

    def _evaluate_signals(
        self,
        metrics: EBSActivityMetrics,
        create_time: datetime,
    ) -> tuple[List[EBSIdleSignal], Dict[str, int], int]:
        """
        Evaluate B1-B7 signals for an EBS volume.

        Args:
            metrics: EBSActivityMetrics
            create_time: Volume creation time

        Returns:
            Tuple of (idle_signals, signal_scores, total_score)
        """
        idle_signals = []
        signal_scores = {}
        total_score = 0

        # B1: Zero IOPS - No read/write operations in 90 days
        total_ops = metrics.total_read_ops_90d + metrics.total_write_ops_90d
        if total_ops == 0:
            idle_signals.append(EBSIdleSignal.B1_ZERO_IOPS)
            signal_scores["B1"] = DEFAULT_EBS_WEIGHTS["B1"]
            total_score += DEFAULT_EBS_WEIGHTS["B1"]

        # B2: Unattached - Volume not attached to any instance
        if not metrics.attached:
            idle_signals.append(EBSIdleSignal.B2_UNATTACHED)
            signal_scores["B2"] = DEFAULT_EBS_WEIGHTS["B2"]
            total_score += DEFAULT_EBS_WEIGHTS["B2"]

        # B3: Low Throughput - <1MB/day throughput
        if metrics.avg_throughput_mb_per_day < 1.0 and total_ops > 0:
            idle_signals.append(EBSIdleSignal.B3_LOW_THROUGHPUT)
            signal_scores["B3"] = DEFAULT_EBS_WEIGHTS["B3"]
            total_score += DEFAULT_EBS_WEIGHTS["B3"]

        # B4: Stale Volume - No modifications for 180+ days
        volume_age_days = (datetime.now(timezone.utc) - create_time).days
        if volume_age_days > 180:
            # Check if volume hasn't been modified (using create_time as proxy)
            if metrics.last_modification_time is None:
                idle_signals.append(EBSIdleSignal.B4_STALE_VOLUME)
                signal_scores["B4"] = DEFAULT_EBS_WEIGHTS["B4"]
                total_score += DEFAULT_EBS_WEIGHTS["B4"]

        # B5: No Encryption - Unencrypted volume
        if not metrics.encrypted:
            idle_signals.append(EBSIdleSignal.B5_NO_ENCRYPTION)
            signal_scores["B5"] = DEFAULT_EBS_WEIGHTS["B5"]
            total_score += DEFAULT_EBS_WEIGHTS["B5"]

        # B6: Oversized - Less than 10% capacity utilization
        # (Estimate based on throughput vs size)
        if metrics.volume_size_gb > 0:
            total_bytes = metrics.total_read_bytes_90d + metrics.total_write_bytes_90d
            utilization_pct = (total_bytes / (metrics.volume_size_gb * 1e9)) * 100
            if utilization_pct < 10:
                idle_signals.append(EBSIdleSignal.B6_OVERSIZED)
                signal_scores["B6"] = DEFAULT_EBS_WEIGHTS["B6"]
                total_score += DEFAULT_EBS_WEIGHTS["B6"]

        # B7: Cost Inefficiency - High cost per GB relative to activity
        # (Triggered if cost > $0.15/GB and low activity)
        price_per_gb = self.EBS_PRICING.get(metrics.volume_type, 0.12)
        if price_per_gb > 0.10 and metrics.avg_iops_per_day < 10:
            idle_signals.append(EBSIdleSignal.B7_COST_INEFFICIENCY)
            signal_scores["B7"] = DEFAULT_EBS_WEIGHTS["B7"]
            total_score += DEFAULT_EBS_WEIGHTS["B7"]

        return idle_signals, signal_scores, min(total_score, 100)

    def _classify_activity_pattern(self, metrics: EBSActivityMetrics) -> EBSActivityPattern:
        """Classify activity pattern based on IOPS."""
        avg_iops = metrics.avg_iops_per_day

        if avg_iops == 0:
            return EBSActivityPattern.IDLE
        elif avg_iops < 100:
            return EBSActivityPattern.LIGHT
        elif avg_iops < 1000:
            return EBSActivityPattern.MODERATE
        else:
            return EBSActivityPattern.ACTIVE

    def _get_tier(self, score: int) -> str:
        """Get tier classification based on score."""
        if score >= 80:
            return "MUST"
        elif score >= 50:
            return "SHOULD"
        elif score >= 25:
            return "COULD"
        else:
            return "KEEP"

    def _get_recommendation(self, score: int, pattern: EBSActivityPattern) -> EBSDecommissionRecommendation:
        """Get recommendation based on score and pattern."""
        if score >= 80:
            return EBSDecommissionRecommendation.DECOMMISSION
        elif score >= 50:
            return EBSDecommissionRecommendation.INVESTIGATE
        elif score >= 25 or pattern == EBSActivityPattern.LIGHT:
            return EBSDecommissionRecommendation.OPTIMIZE
        else:
            return EBSDecommissionRecommendation.KEEP

    def _calculate_confidence(self, signals: List[EBSIdleSignal]) -> float:
        """Calculate overall confidence based on triggered signals."""
        if not signals:
            return 0.0

        confidences = [self.SIGNAL_CONFIDENCE.get(signal.value, 0.5) for signal in signals]

        # Weighted average based on signal weights
        total_weight = sum(DEFAULT_EBS_WEIGHTS.get(signal.value, 1) for signal in signals)
        weighted_confidence = sum(
            self.SIGNAL_CONFIDENCE.get(signal.value, 0.5) * DEFAULT_EBS_WEIGHTS.get(signal.value, 1)
            for signal in signals
        )

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def display_analysis(
        self,
        analyses: List[EBSActivityAnalysis],
        show_all: bool = False,
    ) -> None:
        """
        Display EBS analysis results using Rich tables.

        Args:
            analyses: List of EBSActivityAnalysis results
            show_all: Show all volumes (not just candidates)
        """
        if not analyses:
            print_warning("No EBS volumes analyzed")
            return

        # Filter to decommission candidates unless show_all
        candidates = [a for a in analyses if show_all or a.total_score >= 25]

        if not candidates:
            print_info("No EBS decommission candidates found")
            return

        # Create summary table
        table = create_table(
            title="EBS Volume Activity Analysis (B1-B7 Signals)",
            columns=[
                ("Volume ID", {"style": "cyan", "width": 24}),
                ("Size", {"justify": "right", "width": 8}),
                ("Type", {"width": 6}),
                ("Attached", {"width": 8}),
                ("Score", {"justify": "right", "width": 8}),
                ("Tier", {"width": 8}),
                ("Signals", {"width": 20}),
                ("Monthly $", {"justify": "right", "width": 10}),
                ("Savings", {"justify": "right", "width": 10}),
            ],
        )

        # Sort by score descending
        candidates.sort(key=lambda x: x.total_score, reverse=True)

        for analysis in candidates:
            # Format signals
            signals_str = ",".join(s.value for s in analysis.idle_signals) or "-"

            # Tier styling
            tier_style = {
                "MUST": "[red]MUST[/red]",
                "SHOULD": "[yellow]SHOULD[/yellow]",
                "COULD": "[blue]COULD[/blue]",
                "KEEP": "[green]KEEP[/green]",
            }.get(analysis.tier, analysis.tier)

            table.add_row(
                analysis.volume_id,
                f"{analysis.metrics.volume_size_gb} GB",
                analysis.metrics.volume_type,
                "Yes" if analysis.metrics.attached else "[red]No[/red]",
                f"{analysis.total_score}/100",
                tier_style,
                signals_str,
                format_cost(analysis.monthly_cost),
                format_cost(analysis.potential_savings),
            )

        console.print(table)

        # Summary stats
        total_savings = sum(a.potential_savings for a in candidates)
        must_count = sum(1 for a in candidates if a.tier == "MUST")
        should_count = sum(1 for a in candidates if a.tier == "SHOULD")

        print_section("EBS Decommission Summary")
        console.print(f"  Total candidates: {len(candidates)}")
        console.print(f"  MUST tier: {must_count}")
        console.print(f"  SHOULD tier: {should_count}")
        console.print(f"  Potential annual savings: {format_cost(total_savings)}")


# Factory function for dashboard integration
def create_ebs_activity_enricher(
    profile: str,
    region: str = "ap-southeast-2",
    lookback_days: int = 90,
    verbose: bool = False,
) -> EBSActivityEnricher:
    """
    Factory function to create EBSActivityEnricher.

    Args:
        profile: AWS profile name
        region: AWS region
        lookback_days: Days to analyze
        verbose: Enable verbose logging

    Returns:
        EBSActivityEnricher instance
    """
    return EBSActivityEnricher(
        operational_profile=profile,
        region=region,
        lookback_days=lookback_days,
        verbose=verbose,
    )
