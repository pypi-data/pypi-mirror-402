#!/usr/bin/env python3
"""
Activity Health Tree - S3 Storage Decommissioning Visualization
================================================================

Business Value: Visual decommission decision tree for idle S3 storage resources
Strategic Impact: Enable CFOs and technical leadership to prioritize cost optimization
Integration: Consumes S3 activity enricher signals and displays actionable recommendations

Architecture Pattern: Rich CLI Tree Visualization
- Layer 1: S3ActivityEnricher signal consumption
- Layer 2: Decommission tier classification (MUST/SHOULD/KEEP)
- Layer 3: Rich Tree visualization with savings calculations
- Layer 4: Export capabilities (JSON/CSV/HTML)

Decommission Tiers:
- MUST Decommission: High-confidence idle resources (S1 signal, confidence ≥0.90)
- SHOULD Optimize: Medium-confidence candidates (S2-S7 signals, confidence ≥0.70)
- KEEP: Active resources (confidence <0.50)

Usage:
    from runbooks.finops.activity_health_tree import ActivityHealthTree

    tree = ActivityHealthTree(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Generate tree visualization
    tree.display_activity_tree(
        account_id='363435891329',
        bucket_names=['bucket1', 'bucket2']
    )

    # Export recommendations
    tree.export_recommendations(format='json', output_file='/tmp/s3-decommission.json')

AWS Documentation References:
- S3 Cost Optimization: https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-storage.html
- Storage Classes: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
- Lifecycle Management: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 2 - S3 Activity Health Tree
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.tree import Tree
from rich.text import Text

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
from runbooks.finops.s3_activity_enricher import (
    S3ActivityEnricher,
    S3ActivityAnalysis,
    DecommissionRecommendation,
    S3IdleSignal,
    ActivityPattern,
)

# v1.1.29: Import VPC enrichers for VPC resource tree nodes
try:
    from runbooks.inventory.enrichers.vpce_activity_enricher import VPCEActivityEnricher

    VPCE_ENRICHER_AVAILABLE = True
except ImportError:
    VPCE_ENRICHER_AVAILABLE = False

try:
    from runbooks.inventory.enrichers.nat_gateway_activity_enricher import NATGatewayActivityEnricher

    NAT_ENRICHER_AVAILABLE = True
except ImportError:
    NAT_ENRICHER_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# ENUMERATION TYPES
# ═════════════════════════════════════════════════════════════════════════════


class DecommissionTier(str, Enum):
    """
    Decommission tier classification for activity health tree.

    Tier definitions aligned with enterprise risk tolerance:
    - MUST: High-confidence idle (≥90% confidence, S1 signal present)
    - SHOULD: Medium-confidence optimization (≥70% confidence, S2-S7 signals)
    - KEEP: Active resources (<50% confidence, production workloads)
    """

    MUST_DECOMMISSION = "MUST"  # High confidence - immediate action required
    SHOULD_OPTIMIZE = "SHOULD"  # Medium confidence - review and optimize
    KEEP = "KEEP"  # Active resource - retain as-is


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class TierSummary:
    """
    Summary statistics for decommission tier.

    Aggregates resource counts and savings potential for tier-level reporting.
    """

    tier: DecommissionTier
    bucket_count: int
    total_monthly_cost: float
    total_annual_cost: float
    potential_monthly_savings: float
    potential_annual_savings: float
    buckets: List[S3ActivityAnalysis] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tier": self.tier.value,
            "bucket_count": self.bucket_count,
            "total_monthly_cost": self.total_monthly_cost,
            "total_annual_cost": self.total_annual_cost,
            "potential_monthly_savings": self.potential_monthly_savings,
            "potential_annual_savings": self.potential_annual_savings,
            "buckets": [bucket.to_dict() for bucket in self.buckets],
        }


# ═════════════════════════════════════════════════════════════════════════════
# v1.1.29: VPC RESOURCE DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class VPCEndpointSummary:
    """
    Summary of VPC Endpoint analysis with V1-V10 signals.

    v1.1.29: Tracks VPC Endpoint decommission candidates with signal breakdown.
    """

    vpc_endpoint_id: str
    service_name: str
    endpoint_type: str
    vpc_id: str
    account_id: str
    account_name: str
    age_days: int
    decommission_score: int
    decommission_tier: str
    vpc_cost_90d: float
    signals_active: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "vpc_endpoint_id": self.vpc_endpoint_id,
            "service_name": self.service_name,
            "endpoint_type": self.endpoint_type,
            "vpc_id": self.vpc_id,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "age_days": self.age_days,
            "decommission_score": self.decommission_score,
            "decommission_tier": self.decommission_tier,
            "vpc_cost_90d": self.vpc_cost_90d,
            "signals_active": self.signals_active,
        }


@dataclass
class NATGatewaySummary:
    """
    Summary of NAT Gateway analysis with N1-N10 signals.

    v1.1.29: Tracks NAT Gateway decommission candidates with signal breakdown.
    """

    nat_gateway_id: str
    vpc_id: str
    availability_zone: str
    account_id: str
    account_name: str
    age_days: int
    decommission_score: int
    decommission_tier: str
    bytes_out_90d: int
    signals_active: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "nat_gateway_id": self.nat_gateway_id,
            "vpc_id": self.vpc_id,
            "availability_zone": self.availability_zone,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "age_days": self.age_days,
            "decommission_score": self.decommission_score,
            "decommission_tier": self.decommission_tier,
            "bytes_out_90d": self.bytes_out_90d,
            "signals_active": self.signals_active,
        }


@dataclass
class VPCResourceTierSummary:
    """
    Summary statistics for VPC resource decommission tier.

    v1.1.29: Aggregates VPC Endpoint and NAT Gateway counts by tier.
    """

    tier: str
    vpce_count: int
    nat_count: int
    total_cost: float
    potential_savings: float
    vpc_endpoints: List[VPCEndpointSummary] = field(default_factory=list)
    nat_gateways: List[NATGatewaySummary] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "tier": self.tier,
            "vpce_count": self.vpce_count,
            "nat_count": self.nat_count,
            "total_cost": self.total_cost,
            "potential_savings": self.potential_savings,
            "vpc_endpoints": [e.to_dict() for e in self.vpc_endpoints],
            "nat_gateways": [n.to_dict() for n in self.nat_gateways],
        }


@dataclass
class ActivityHealthReport:
    """
    Complete activity health tree report.

    Enterprise-grade decommission analysis report with tier breakdowns,
    savings projections, and actionable recommendations.
    """

    account_id: str
    region: str
    total_buckets: int
    total_annual_cost: float
    total_potential_savings: float
    must_decommission: TierSummary
    should_optimize: TierSummary
    keep: TierSummary
    analysis_timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "account_id": self.account_id,
            "region": self.region,
            "total_buckets": self.total_buckets,
            "total_annual_cost": self.total_annual_cost,
            "total_potential_savings": self.total_potential_savings,
            "savings_percentage": (
                (self.total_potential_savings / self.total_annual_cost * 100) if self.total_annual_cost > 0 else 0.0
            ),
            "must_decommission": self.must_decommission.to_dict(),
            "should_optimize": self.should_optimize.to_dict(),
            "keep": self.keep.to_dict(),
            "analysis_timestamp": self.analysis_timestamp,
            "metadata": self.metadata,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE ACTIVITY HEALTH TREE CLASS
# ═════════════════════════════════════════════════════════════════════════════


class ActivityHealthTree:
    """
    Activity Health Tree for S3 storage decommission visualization.

    Generates Rich CLI tree visualization of S3 bucket decommission recommendations
    with tier-based organization (MUST/SHOULD/KEEP) and savings calculations.

    Capabilities:
    - Consume S3ActivityEnricher signals
    - Classify buckets into decommission tiers
    - Generate Rich Tree visualization
    - Calculate tier-level savings aggregates
    - Export recommendations (JSON/CSV/HTML)

    Tier Classification:
    - MUST Decommission: confidence ≥0.90 OR S1 signal (zero requests)
    - SHOULD Optimize: confidence ≥0.70 OR S2-S7 signals present
    - KEEP: confidence <0.50 (active production workloads)

    Example:
        >>> tree = ActivityHealthTree(
        ...     operational_profile='ops-profile',
        ...     region='ap-southeast-2'
        ... )
        >>> tree.display_activity_tree(
        ...     account_id='123456789012',
        ...     bucket_names=['my-bucket']
        ... )
        🌳 Activity Health Tree (Total Savings: $12,345/year)
        ├── 📦 S3 Storage (Account: 123456789012)
        │   ├── MUST Decommission (5 buckets, $8,000 savings)
        │   ├── SHOULD Optimize (3 buckets, $3,000 savings)
        │   └── KEEP (2 buckets, Active)
    """

    def __init__(
        self, operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 90
    ):
        """
        Initialize Activity Health Tree.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region (default: ap-southeast-2)
            lookback_days: CloudWatch lookback period (default: 90)
        """
        self.operational_profile = operational_profile
        self.region = region or "ap-southeast-2"
        self.lookback_days = lookback_days

        # Initialize S3 activity enricher
        self.enricher = S3ActivityEnricher(
            operational_profile=operational_profile, region=region, lookback_days=lookback_days
        )

        # Cache for activity health report
        self._report: Optional[ActivityHealthReport] = None

        # Cache for lifecycle recommendations (for HTML export parity)
        self._lifecycle_recommendations: List[Dict[str, Any]] = []

        # Logger
        self.logger = logging.getLogger(__name__)

    def set_lifecycle_recommendations(self, recommendations: List[Any]) -> None:
        """
        Set lifecycle recommendations for HTML export parity.

        This enables the HTML export to include S3 Lifecycle Recommendations
        that are generated by the S3LifecycleOptimizer.

        Args:
            recommendations: List of LifecycleRecommendation objects
        """
        self._lifecycle_recommendations = []
        for rec in recommendations:
            self._lifecycle_recommendations.append(
                {
                    "bucket_name": getattr(rec, "bucket_name", "Unknown"),
                    "region": getattr(rec, "region", "Unknown"),
                    "recommendation_type": getattr(rec, "recommendation_type", "Unknown"),
                    "transition_days": getattr(rec, "transition_days", 0),
                    "target_storage_class": getattr(rec, "target_storage_class", "Unknown"),
                    "estimated_annual_savings": getattr(rec, "estimated_annual_savings", 0.0),
                    "confidence": getattr(rec, "confidence", "MEDIUM"),
                }
            )

    def display_activity_tree(
        self, account_id: Optional[str] = None, bucket_names: Optional[List[str]] = None, show_details: bool = True
    ) -> ActivityHealthReport:
        """
        Display Activity Health Tree with decommission recommendations.

        Creates Rich Tree visualization showing:
        1. Total savings potential
        2. Account-level S3 storage analysis
        3. Tier-based bucket classification (MUST/SHOULD/KEEP)
        4. Per-tier savings aggregates
        5. Bucket-level details with signals

        Args:
            account_id: AWS account ID (auto-detected if None)
            bucket_names: List of bucket names to analyze (all if None)
            show_details: Show bucket-level details in tree (default: True)

        Returns:
            ActivityHealthReport with complete analysis results

        Example:
            >>> tree.display_activity_tree(
            ...     account_id='363435891329',
            ...     bucket_names=['bucket1', 'bucket2']
            ... )
        """
        print_section("Activity Health Tree - S3 Storage Decommissioning")

        # Analyze S3 buckets
        analyses = self.enricher.analyze_bucket_activity(
            bucket_names=bucket_names, region=self.region, lookback_days=self.lookback_days
        )

        if not analyses:
            print_warning("No S3 buckets found for analysis")
            return self._create_empty_report(account_id or "unknown")

        # Classify buckets into tiers
        must_decommission, should_optimize, keep = self._classify_tiers(analyses)

        # Generate report
        report = self._generate_report(
            account_id=account_id or analyses[0].account_id,
            analyses=analyses,
            must_decommission=must_decommission,
            should_optimize=should_optimize,
            keep=keep,
        )

        # Cache report
        self._report = report

        # Create Rich Tree visualization
        tree = self._create_tree_visualization(report, show_details)

        # Display tree
        console.print()
        console.print(tree)
        console.print()

        # Display summary table
        self._display_summary_table(report)

        return report

    def _classify_tiers(
        self, analyses: List[S3ActivityAnalysis]
    ) -> tuple[List[S3ActivityAnalysis], List[S3ActivityAnalysis], List[S3ActivityAnalysis]]:
        """
        Classify S3 buckets into decommission tiers - S1-S10 Framework Aligned.

        Classification rules (based on 125 point scoring, normalized to 0-100):
        - MUST: score >=80 (S1+S2+S3 present) OR confidence >=0.90 OR S1 signal
        - SHOULD: score 50-79 OR confidence >=0.70 OR S2-S6 signals present
        - COULD: score 25-49 (potential candidates)
        - KEEP: score <25 OR confidence <0.50 (active resources)

        Signal Framework v2.0:
        - Tier 1 (High-Confidence): S1 (40pts), S2 (20pts) = 60 max
        - Tier 2 (Medium-Confidence): S3-S6 (45pts max)
        - Tier 3 (Lower-Confidence): S7-S10 (20pts max)

        Args:
            analyses: List of S3 activity analyses

        Returns:
            Tuple of (must_decommission, should_optimize, keep) lists
        """
        must_decommission = []
        should_optimize = []
        keep = []

        for analysis in analyses:
            # MUST Decommission: High confidence or S1 (Storage Lens Inactive) signal
            # S1 is the strongest indicator (40 pts, 0.95 confidence)
            if analysis.confidence >= 0.90 or S3IdleSignal.S1_STORAGE_LENS_INACTIVE in analysis.idle_signals:
                must_decommission.append(analysis)
            # SHOULD Optimize: Medium confidence or Tier 1-2 optimization signals
            elif analysis.confidence >= 0.70 or any(
                signal in analysis.idle_signals
                for signal in [
                    # Tier 1 signals (besides S1)
                    S3IdleSignal.S2_STORAGE_CLASS_INEFFICIENCY,
                    # Tier 2 signals
                    S3IdleSignal.S3_LIFECYCLE_MISSING,
                    S3IdleSignal.S4_INTELLIGENT_TIERING_OFF,
                    S3IdleSignal.S5_VERSIONING_NO_EXPIRATION,
                    S3IdleSignal.S6_ZERO_REQUESTS_90D,
                    # Tier 3 signals (supporting evidence)
                    S3IdleSignal.S7_REPLICATION_WASTE,
                    S3IdleSignal.S8_PUBLIC_NO_ENCRYPTION,
                    S3IdleSignal.S9_INVENTORY_OVERHEAD,
                    S3IdleSignal.S10_HIGH_REQUEST_COST,
                ]
            ):
                should_optimize.append(analysis)
            # KEEP: Active resources (no signals or confidence <0.50)
            else:
                keep.append(analysis)

        return must_decommission, should_optimize, keep

    def _generate_report(
        self,
        account_id: str,
        analyses: List[S3ActivityAnalysis],
        must_decommission: List[S3ActivityAnalysis],
        should_optimize: List[S3ActivityAnalysis],
        keep: List[S3ActivityAnalysis],
    ) -> ActivityHealthReport:
        """
        Generate Activity Health Report.

        Args:
            account_id: AWS account ID
            analyses: All bucket analyses
            must_decommission: MUST tier buckets
            should_optimize: SHOULD tier buckets
            keep: KEEP tier buckets

        Returns:
            Complete activity health report
        """
        # Calculate tier summaries
        must_summary = self._calculate_tier_summary(DecommissionTier.MUST_DECOMMISSION, must_decommission)
        should_summary = self._calculate_tier_summary(DecommissionTier.SHOULD_OPTIMIZE, should_optimize)
        keep_summary = self._calculate_tier_summary(DecommissionTier.KEEP, keep)

        # Calculate totals
        total_annual_cost = sum(a.annual_cost for a in analyses)
        total_potential_savings = sum(a.potential_savings for a in analyses)

        return ActivityHealthReport(
            account_id=account_id,
            region=self.region,
            total_buckets=len(analyses),
            total_annual_cost=total_annual_cost,
            total_potential_savings=total_potential_savings,
            must_decommission=must_summary,
            should_optimize=should_summary,
            keep=keep_summary,
            analysis_timestamp=datetime.now(tz=timezone.utc).isoformat(),
            metadata={
                "lookback_days": self.lookback_days,
                "operational_profile": self.operational_profile,
            },
        )

    def _calculate_tier_summary(self, tier: DecommissionTier, buckets: List[S3ActivityAnalysis]) -> TierSummary:
        """
        Calculate summary statistics for decommission tier.

        Args:
            tier: Decommission tier enum
            buckets: List of bucket analyses in tier

        Returns:
            TierSummary with aggregated metrics
        """
        total_monthly_cost = sum(b.monthly_cost for b in buckets)
        total_annual_cost = sum(b.annual_cost for b in buckets)
        potential_annual_savings = sum(b.potential_savings for b in buckets)
        potential_monthly_savings = potential_annual_savings / 12

        return TierSummary(
            tier=tier,
            bucket_count=len(buckets),
            total_monthly_cost=total_monthly_cost,
            total_annual_cost=total_annual_cost,
            potential_monthly_savings=potential_monthly_savings,
            potential_annual_savings=potential_annual_savings,
            buckets=buckets,
        )

    def _create_tree_visualization(self, report: ActivityHealthReport, show_details: bool) -> Tree:
        """
        Create Rich Tree visualization.

        Args:
            report: Activity health report
            show_details: Show bucket-level details

        Returns:
            Rich Tree object ready for display
        """
        # Root node with total savings
        root_label = Text()
        root_label.append("🌳 Activity Health Tree ", style="bold cyan")
        root_label.append(f"(Total Savings: ", style="white")
        root_label.append(f"{format_cost(report.total_potential_savings)}/year", style="bold bright_green")
        root_label.append(")", style="white")

        tree = Tree(root_label)

        # Account-level S3 Storage node
        account_label = Text()
        account_label.append("📦 S3 Storage ", style="bold yellow")
        account_label.append(f"(Account: {report.account_id})", style="white")

        account_node = tree.add(account_label)

        # MUST Decommission tier
        if report.must_decommission.bucket_count > 0:
            must_label = Text()
            must_label.append("❌ MUST Decommission ", style="bold bright_red")
            must_label.append(f"({report.must_decommission.bucket_count} buckets, ", style="white")
            must_label.append(
                f"{format_cost(report.must_decommission.potential_annual_savings)}/year", style="bright_green"
            )
            must_label.append(")", style="white")

            must_node = account_node.add(must_label)

            if show_details:
                for bucket in report.must_decommission.buckets:
                    self._add_bucket_node(must_node, bucket)

        # SHOULD Optimize tier
        if report.should_optimize.bucket_count > 0:
            should_label = Text()
            should_label.append("⚠️  SHOULD Optimize ", style="bold bright_yellow")
            should_label.append(f"({report.should_optimize.bucket_count} buckets, ", style="white")
            should_label.append(
                f"{format_cost(report.should_optimize.potential_annual_savings)}/year", style="bright_green"
            )
            should_label.append(")", style="white")

            should_node = account_node.add(should_label)

            if show_details:
                for bucket in report.should_optimize.buckets:
                    self._add_bucket_node(should_node, bucket)

        # KEEP tier
        if report.keep.bucket_count > 0:
            keep_label = Text()
            keep_label.append("✅ KEEP ", style="bold bright_green")
            keep_label.append(f"({report.keep.bucket_count} buckets, Active)", style="white")

            keep_node = account_node.add(keep_label)

            if show_details:
                for bucket in report.keep.buckets:
                    self._add_bucket_node(keep_node, bucket)

        return tree

    def _add_bucket_node(self, parent_node: Tree, bucket: S3ActivityAnalysis) -> None:
        """
        Add bucket detail node to tree with S1-S10 signal display.

        Signal Abbreviation Map (for compact display):
        - S1: StorLens (Storage Lens Inactive - 40pts)
        - S2: ClassIneff (Storage Class Inefficiency - 20pts)
        - S3: NoLife (Lifecycle Missing - 15pts)
        - S4: NoIT (Intelligent-Tiering Off - 10pts)
        - S5: VerNoExp (Versioning No Expiration - 10pts)
        - S6: ZeroReq (Zero Requests 90D - 10pts)
        - S7: ReplWaste (Replication Waste - 5pts)
        - S8: PubNoEnc (Public No Encryption - 5pts)
        - S9: InvOver (Inventory Overhead - 5pts)
        - S10: HighReqCost (High Request Cost - 5pts)

        Args:
            parent_node: Parent tree node
            bucket: S3 activity analysis
        """
        # Signal abbreviation mapping for compact display (v1.1.29: signal IDs only per user request)
        SIGNAL_ABBREV = {
            S3IdleSignal.S1_STORAGE_LENS_INACTIVE: "S1",
            S3IdleSignal.S2_STORAGE_CLASS_INEFFICIENCY: "S2",
            S3IdleSignal.S3_LIFECYCLE_MISSING: "S3",
            S3IdleSignal.S4_INTELLIGENT_TIERING_OFF: "S4",
            S3IdleSignal.S5_VERSIONING_NO_EXPIRATION: "S5",
            S3IdleSignal.S6_ZERO_REQUESTS_90D: "S6",
            S3IdleSignal.S7_REPLICATION_WASTE: "S7",
            S3IdleSignal.S8_PUBLIC_NO_ENCRYPTION: "S8",
            S3IdleSignal.S9_INVENTORY_OVERHEAD: "S9",
            S3IdleSignal.S10_HIGH_REQUEST_COST: "S10",
        }

        bucket_label = Text()
        bucket_label.append(f"{bucket.bucket_name} ", style="cyan")
        bucket_label.append(f"[{bucket.metrics.total_size_gb:.1f} GB, ", style="white")
        bucket_label.append(f"{bucket.metrics.avg_requests_per_day:.0f} req/day] ", style="white")

        # Add signals with abbreviations and score
        if bucket.idle_signals:
            # Calculate decommission score (S1-S10 framework: 125 pts max -> 0-100 normalized)
            signal_points = {
                S3IdleSignal.S1_STORAGE_LENS_INACTIVE: 40,
                S3IdleSignal.S2_STORAGE_CLASS_INEFFICIENCY: 20,
                S3IdleSignal.S3_LIFECYCLE_MISSING: 15,
                S3IdleSignal.S4_INTELLIGENT_TIERING_OFF: 10,
                S3IdleSignal.S5_VERSIONING_NO_EXPIRATION: 10,
                S3IdleSignal.S6_ZERO_REQUESTS_90D: 10,
                S3IdleSignal.S7_REPLICATION_WASTE: 5,
                S3IdleSignal.S8_PUBLIC_NO_ENCRYPTION: 5,
                S3IdleSignal.S9_INVENTORY_OVERHEAD: 5,
                S3IdleSignal.S10_HIGH_REQUEST_COST: 5,
            }
            raw_score = sum(signal_points.get(s, 0) for s in bucket.idle_signals)
            normalized_score = min(100, int((raw_score / 125) * 100))

            # Format signals with abbreviations
            signals_abbrev = [SIGNAL_ABBREV.get(s, s.value) for s in bucket.idle_signals]
            signals_str = ", ".join(signals_abbrev)

            # Color-code score display
            if normalized_score >= 80:
                score_style = "bold bright_red"
            elif normalized_score >= 50:
                score_style = "bold bright_yellow"
            else:
                score_style = "bold bright_blue"

            bucket_label.append(f"Score: ", style="white")
            bucket_label.append(f"{normalized_score}/100 ", style=score_style)
            bucket_label.append(f"[{signals_str}] ", style="bright_magenta")

        # Add savings
        monthly_savings = bucket.potential_savings / 12
        if monthly_savings > 0:
            bucket_label.append(f"| {format_cost(monthly_savings)}/mo", style="bright_green")

        parent_node.add(bucket_label)

    # ═════════════════════════════════════════════════════════════════════════════
    # v1.1.29: VPC RESOURCE TREE METHODS
    # ═════════════════════════════════════════════════════════════════════════════

    def add_vpc_resource_nodes(
        self,
        tree: Tree,
        vpce_df: Optional["pd.DataFrame"] = None,
        nat_df: Optional["pd.DataFrame"] = None,
        show_details: bool = True,
    ) -> None:
        """
        Add VPC resource nodes with V1-V10/N1-N10 signals to the Activity Health Tree.

        v1.1.29: Extends the Activity Health Tree to include VPC Endpoints and NAT Gateways
        with their decommission signals and cost optimization opportunities.

        Args:
            tree: Rich Tree object to add VPC nodes to
            vpce_df: DataFrame with VPC Endpoint analysis (with V1-V10 signals)
            nat_df: DataFrame with NAT Gateway analysis (with N1-N10 signals)
            show_details: Show resource-level details in tree (default: True)

        Business Value:
            - Unified decommission view across S3 + VPC resources
            - Organization-wide network cost optimization visibility
            - Combined savings potential across all resource types

        Example:
            >>> from rich.tree import Tree
            >>> tree = Tree("Activity Health Tree")
            >>> health_tree.add_vpc_resource_nodes(
            ...     tree=tree,
            ...     vpce_df=enriched_vpce_df,
            ...     nat_df=enriched_nat_df
            ... )
        """
        import pandas as pd

        # Calculate VPC resource counts
        vpce_count = len(vpce_df) if vpce_df is not None and not vpce_df.empty else 0
        nat_count = len(nat_df) if nat_df is not None and not nat_df.empty else 0

        if vpce_count == 0 and nat_count == 0:
            # No VPC resources - add informational node
            vpc_label = Text()
            vpc_label.append("🔗 VPC Resources ", style="bold blue")
            vpc_label.append("(No resources discovered)", style="dim white")
            tree.add(vpc_label)
            return

        # VPC Resources branch
        vpc_label = Text()
        vpc_label.append("🔗 VPC Resources ", style="bold blue")
        vpc_label.append(f"({vpce_count} VPC Endpoints, {nat_count} NAT Gateways)", style="white")

        vpc_branch = tree.add(vpc_label)

        # Add VPCE nodes
        if vpce_df is not None and not vpce_df.empty:
            self._add_vpce_tier_nodes(vpc_branch, vpce_df, show_details)

        # Add NAT Gateway nodes
        if nat_df is not None and not nat_df.empty:
            self._add_nat_tier_nodes(vpc_branch, nat_df, show_details)

    def _add_vpce_tier_nodes(self, parent_node: Tree, vpce_df: "pd.DataFrame", show_details: bool) -> None:
        """
        Add VPC Endpoint nodes organized by decommission tier.

        Args:
            parent_node: Parent tree node
            vpce_df: DataFrame with VPC Endpoint analysis
            show_details: Show resource-level details
        """
        # VPCE branch
        vpce_label = Text()
        vpce_label.append("🔌 VPC Endpoints ", style="bold cyan")
        vpce_label.append(f"({len(vpce_df)} discovered)", style="white")

        vpce_branch = parent_node.add(vpce_label)

        # Group by decommission tier
        tier_groups = {}
        for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
            tier_df = (
                vpce_df[vpce_df["decommission_tier"] == tier]
                if "decommission_tier" in vpce_df.columns
                else vpce_df.head(0)
            )
            if len(tier_df) > 0:
                tier_groups[tier] = tier_df

        # MUST tier
        if "MUST" in tier_groups:
            must_df = tier_groups["MUST"]
            must_label = Text()
            must_label.append("❌ MUST Decommission ", style="bold bright_red")
            must_label.append(f"({len(must_df)} endpoints)", style="white")

            must_node = vpce_branch.add(must_label)
            if show_details:
                for _, row in must_df.head(10).iterrows():  # Limit to top 10
                    self._add_vpce_detail_node(must_node, row)

        # SHOULD tier
        if "SHOULD" in tier_groups:
            should_df = tier_groups["SHOULD"]
            should_label = Text()
            should_label.append("⚠️  SHOULD Optimize ", style="bold bright_yellow")
            should_label.append(f"({len(should_df)} endpoints)", style="white")

            should_node = vpce_branch.add(should_label)
            if show_details:
                for _, row in should_df.head(10).iterrows():
                    self._add_vpce_detail_node(should_node, row)

        # COULD tier
        if "COULD" in tier_groups:
            could_df = tier_groups["COULD"]
            could_label = Text()
            could_label.append("💡 COULD Consider ", style="bold bright_blue")
            could_label.append(f"({len(could_df)} endpoints)", style="white")

            could_node = vpce_branch.add(could_label)
            if show_details:
                for _, row in could_df.head(5).iterrows():  # Limit to top 5
                    self._add_vpce_detail_node(could_node, row)

        # KEEP tier
        if "KEEP" in tier_groups:
            keep_df = tier_groups["KEEP"]
            keep_label = Text()
            keep_label.append("✅ KEEP ", style="bold bright_green")
            keep_label.append(f"({len(keep_df)} endpoints, Active)", style="white")

            vpce_branch.add(keep_label)  # No details for KEEP

    def _add_vpce_detail_node(self, parent_node: Tree, row: "pd.Series") -> None:
        """
        Add VPC Endpoint detail node with V1-V10 signals.

        Args:
            parent_node: Parent tree node
            row: DataFrame row with VPC Endpoint data
        """
        endpoint_id = row.get("vpc_endpoint_id", "Unknown")
        service_name = row.get("service_name", "Unknown")
        score = row.get("decommission_score", 0)
        vpc_cost = row.get("vpc_cost_90d", 0.0)

        # Collect active signals
        signals = []
        for i in range(1, 11):
            signal_col = f"v{i}_signal"
            if row.get(signal_col, False):
                signals.append(f"V{i}")

        signals_str = ", ".join(signals) if signals else "None"

        # Format node label
        node_label = Text()
        node_label.append(f"{endpoint_id[:20]} ", style="cyan")

        # Extract service type from service name
        service_type = service_name.split(".")[-1] if "." in service_name else service_name
        node_label.append(f"[{service_type}] ", style="dim white")

        # Color-code score
        if score >= 80:
            score_style = "bold bright_red"
        elif score >= 50:
            score_style = "bold bright_yellow"
        else:
            score_style = "bold bright_blue"

        node_label.append(f"Score: ", style="white")
        node_label.append(f"{score}/100 ", style=score_style)
        node_label.append(f"[{signals_str}] ", style="bright_magenta")

        # Add cost
        if vpc_cost > 0:
            node_label.append(f"| ${vpc_cost:.2f}/90d", style="bright_green")

        parent_node.add(node_label)

    def _add_nat_tier_nodes(self, parent_node: Tree, nat_df: "pd.DataFrame", show_details: bool) -> None:
        """
        Add NAT Gateway nodes organized by decommission tier.

        Args:
            parent_node: Parent tree node
            nat_df: DataFrame with NAT Gateway analysis
            show_details: Show resource-level details
        """
        # NAT Gateway branch
        nat_label = Text()
        nat_label.append("🌐 NAT Gateways ", style="bold yellow")
        nat_label.append(f"({len(nat_df)} discovered)", style="white")

        nat_branch = parent_node.add(nat_label)

        # Group by decommission tier
        tier_groups = {}
        for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
            tier_df = (
                nat_df[nat_df["decommission_tier"] == tier] if "decommission_tier" in nat_df.columns else nat_df.head(0)
            )
            if len(tier_df) > 0:
                tier_groups[tier] = tier_df

        # MUST tier
        if "MUST" in tier_groups:
            must_df = tier_groups["MUST"]
            must_label = Text()
            must_label.append("❌ MUST Decommission ", style="bold bright_red")
            must_label.append(f"({len(must_df)} gateways)", style="white")

            must_node = nat_branch.add(must_label)
            if show_details:
                for _, row in must_df.head(10).iterrows():
                    self._add_nat_detail_node(must_node, row)

        # SHOULD tier
        if "SHOULD" in tier_groups:
            should_df = tier_groups["SHOULD"]
            should_label = Text()
            should_label.append("⚠️  SHOULD Optimize ", style="bold bright_yellow")
            should_label.append(f"({len(should_df)} gateways)", style="white")

            should_node = nat_branch.add(should_label)
            if show_details:
                for _, row in should_df.head(10).iterrows():
                    self._add_nat_detail_node(should_node, row)

        # COULD tier
        if "COULD" in tier_groups:
            could_df = tier_groups["COULD"]
            could_label = Text()
            could_label.append("💡 COULD Consider ", style="bold bright_blue")
            could_label.append(f"({len(could_df)} gateways)", style="white")

            could_node = nat_branch.add(could_label)
            if show_details:
                for _, row in could_df.head(5).iterrows():
                    self._add_nat_detail_node(could_node, row)

        # KEEP tier
        if "KEEP" in tier_groups:
            keep_df = tier_groups["KEEP"]
            keep_label = Text()
            keep_label.append("✅ KEEP ", style="bold bright_green")
            keep_label.append(f"({len(keep_df)} gateways, Active)", style="white")

            nat_branch.add(keep_label)  # No details for KEEP

    def _add_nat_detail_node(self, parent_node: Tree, row: "pd.Series") -> None:
        """
        Add NAT Gateway detail node with N1-N10 signals.

        Args:
            parent_node: Parent tree node
            row: DataFrame row with NAT Gateway data
        """
        nat_id = row.get("nat_gateway_id", "Unknown")
        vpc_id = row.get("vpc_id", "Unknown")
        az = row.get("availability_zone", "Unknown")
        score = row.get("decommission_score", 0)
        bytes_out = row.get("bytes_out_90d", 0)

        # Collect active signals
        signals = []
        for i in range(1, 11):
            signal_col = f"n{i}_signal"
            if row.get(signal_col, False):
                signals.append(f"N{i}")

        signals_str = ", ".join(signals) if signals else "None"

        # Format node label
        node_label = Text()
        node_label.append(f"{nat_id[:20]} ", style="cyan")
        node_label.append(f"[{az}] ", style="dim white")

        # Color-code score
        if score >= 80:
            score_style = "bold bright_red"
        elif score >= 50:
            score_style = "bold bright_yellow"
        else:
            score_style = "bold bright_blue"

        node_label.append(f"Score: ", style="white")
        node_label.append(f"{score}/100 ", style=score_style)
        node_label.append(f"[{signals_str}] ", style="bright_magenta")

        # Add bytes transferred
        gb_out = bytes_out / (1024**3) if bytes_out else 0
        if gb_out > 0:
            node_label.append(f"| {gb_out:.2f} GB/90d", style="bright_green")
        else:
            node_label.append(f"| 0 GB/90d", style="dim white")

        parent_node.add(node_label)

    def add_flow_logs_legend(self, tree: Tree) -> None:
        """
        Add Flow Logs status legend explaining adaptive scoring.

        v1.1.29: Explains Flow Logs availability impact on scoring and confidence.

        Args:
            tree: Rich Tree object to add legend to

        Business Value:
            - Transparency on scoring methodology (WITH vs WITHOUT Flow Logs)
            - User education on Flow Logs infrastructure investment ROI
            - Clear confidence level interpretation

        Example:
            >>> from rich.tree import Tree
            >>> tree = Tree("Activity Health Tree")
            >>> health_tree.add_flow_logs_legend(tree)
            # Adds:
            # 📊 Flow Logs Status Legend
            #   ✅ Flow Logs Enabled: V1-V10/N1-N10 (125pt max, HIGH confidence ≥0.90)
            #   ⚠️ Flow Logs Disabled: V1-V5+V7-V10/N1-N5+N7-N10 (110pt max, MEDIUM confidence ~0.75)
            #   🎯 Tier Thresholds: MUST ≥80, SHOULD 50-79, COULD 25-49, KEEP <25
            #   💡 Flow Logs Investment: +15pt V6/N6 signals + 0.15 confidence boost
        """
        legend_label = Text()
        legend_label.append("📊 Flow Logs Status Legend", style="bold bright_blue")

        legend_branch = tree.add(legend_label)

        # Flow Logs enabled explanation
        enabled_label = Text()
        enabled_label.append("✅ Flow Logs Enabled: ", style="bright_green")
        enabled_label.append("V1-V10/N1-N10 (125pt max, HIGH confidence ≥0.90)", style="white")
        legend_branch.add(enabled_label)

        # Flow Logs disabled explanation
        disabled_label = Text()
        disabled_label.append("⚠️  Flow Logs Disabled: ", style="bright_yellow")
        disabled_label.append("V1-V5+V7-V10/N1-N5+N7-N10 (110pt max, MEDIUM confidence ~0.75)", style="white")
        legend_branch.add(disabled_label)

        # Tier thresholds
        tier_label = Text()
        tier_label.append("🎯 Tier Thresholds: ", style="bright_cyan")
        tier_label.append("MUST ≥80, SHOULD 50-79, COULD 25-49, KEEP <25", style="white")
        legend_branch.add(tier_label)

        # Flow Logs investment ROI
        roi_label = Text()
        roi_label.append("💡 Flow Logs Investment: ", style="bright_magenta")
        roi_label.append("+15pt V6/N6 signals + 0.15 confidence boost", style="white")
        legend_branch.add(roi_label)

    def add_vpc_resources_with_flow_logs_status(
        self,
        tree: Tree,
        vpce_df: Optional["pd.DataFrame"] = None,
        nat_df: Optional["pd.DataFrame"] = None,
        show_details: bool = True,
        include_legend: bool = True,
    ) -> None:
        """
        Add VPC resources with Flow Logs status visibility to Activity Health Tree.

        v1.1.29: Enhanced version of add_vpc_resource_nodes() with Flow Logs status display
        and adaptive scoring transparency.

        Args:
            tree: Rich Tree object to add VPC nodes to
            vpce_df: DataFrame with VPC Endpoint analysis (must include 'flow_logs_enabled' column)
            nat_df: DataFrame with NAT Gateway analysis (must include 'flow_logs_enabled' column)
            show_details: Show resource-level details in tree (default: True)
            include_legend: Include Flow Logs status legend (default: True)

        Business Value:
            - Unified decommission view across S3 + VPC resources
            - Transparent Flow Logs availability status per account
            - User education on scoring methodology differences
            - Combined savings potential across all resource types

        Required DataFrame Columns:
            - vpc_endpoint_id / nat_gateway_id: Resource identifier
            - decommission_score: 0-100 score
            - decommission_tier: MUST/SHOULD/COULD/KEEP
            - flow_logs_enabled: Boolean Flow Logs availability
            - confidence: Adjusted confidence (0.0-1.0)
            - v1_signal - v10_signal / n1_signal - n10_signal: Boolean signal flags
            - vpc_cost_90d / bytes_out_90d: Usage metrics

        Example:
            >>> from rich.tree import Tree
            >>> tree = Tree("Activity Health Tree")
            >>> health_tree.add_vpc_resources_with_flow_logs_status(
            ...     tree=tree,
            ...     vpce_df=enriched_vpce_df,
            ...     nat_df=enriched_nat_df,
            ...     include_legend=True
            ... )
            # Output:
            # 🔗 VPC Resources (5 VPC Endpoints, 3 NAT Gateways)
            #   🔌 VPC Endpoints (5 discovered)
            #     ❌ MUST Decommission (2 endpoints)
            #       vpce-0a1b2c3d4e5f [s3] Score: 85/100 (HIGH, ✅ Flow Logs) [V1, V2, V5, V6]
            #     ⚠️  SHOULD Optimize (2 endpoints)
            #       vpce-0a1b2c3d4e5f [dynamodb] Score: 60/100 (MEDIUM, ⚠️ No Flow Logs) [V1, V2, V5]
            #   🌐 NAT Gateways (3 discovered)
            #     ❌ MUST Decommission (1 gateway)
            #       nat-0a1b2c3d4e5f [ap-southeast-2a] Score: 90/100 (HIGH, ✅ Flow Logs) [N1, N2, N6]
            #   📊 Flow Logs Status Legend
            #     ✅ Flow Logs Enabled: V1-V10/N1-N10 (125pt max, HIGH confidence ≥0.90)
            #     ⚠️  Flow Logs Disabled: V1-V5+V7-V10/N1-N5+N7-N10 (110pt max, MEDIUM confidence ~0.75)
        """
        import pandas as pd

        # Calculate VPC resource counts
        vpce_count = len(vpce_df) if vpce_df is not None and not vpce_df.empty else 0
        nat_count = len(nat_df) if nat_df is not None and not nat_df.empty else 0

        if vpce_count == 0 and nat_count == 0:
            # No VPC resources - add informational node
            vpc_label = Text()
            vpc_label.append("🔗 VPC Resources ", style="bold blue")
            vpc_label.append("(No resources discovered)", style="dim white")
            tree.add(vpc_label)
            return

        # VPC Resources branch
        vpc_label = Text()
        vpc_label.append("🔗 VPC Resources ", style="bold blue")
        vpc_label.append(f"({vpce_count} VPC Endpoints, {nat_count} NAT Gateways)", style="white")

        vpc_branch = tree.add(vpc_label)

        # Add VPCE nodes with Flow Logs status
        if vpce_df is not None and not vpce_df.empty:
            self._add_vpce_tier_nodes_with_flow_logs(vpc_branch, vpce_df, show_details)

        # Add NAT Gateway nodes with Flow Logs status
        if nat_df is not None and not nat_df.empty:
            self._add_nat_tier_nodes_with_flow_logs(vpc_branch, nat_df, show_details)

        # Add Flow Logs legend
        if include_legend:
            self.add_flow_logs_legend(vpc_branch)

    def _add_vpce_tier_nodes_with_flow_logs(
        self, parent_node: Tree, vpce_df: "pd.DataFrame", show_details: bool
    ) -> None:
        """
        Add VPC Endpoint nodes with Flow Logs status display.

        Args:
            parent_node: Parent tree node
            vpce_df: DataFrame with VPC Endpoint analysis
            show_details: Show resource-level details
        """
        # VPCE branch
        vpce_label = Text()
        vpce_label.append("🔌 VPC Endpoints ", style="bold cyan")
        vpce_label.append(f"({len(vpce_df)} discovered)", style="white")

        vpce_branch = parent_node.add(vpce_label)

        # Group by decommission tier
        tier_groups = {}
        for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
            tier_df = (
                vpce_df[vpce_df["decommission_tier"] == tier]
                if "decommission_tier" in vpce_df.columns
                else vpce_df.head(0)
            )
            if len(tier_df) > 0:
                tier_groups[tier] = tier_df

        # MUST tier
        if "MUST" in tier_groups:
            must_df = tier_groups["MUST"]
            must_label = Text()
            must_label.append("❌ MUST Decommission ", style="bold bright_red")
            must_label.append(f"({len(must_df)} endpoints)", style="white")

            must_node = vpce_branch.add(must_label)
            if show_details:
                for _, row in must_df.head(10).iterrows():  # Limit to top 10
                    self._add_vpce_detail_node_with_flow_logs(must_node, row)

        # SHOULD tier
        if "SHOULD" in tier_groups:
            should_df = tier_groups["SHOULD"]
            should_label = Text()
            should_label.append("⚠️  SHOULD Optimize ", style="bold bright_yellow")
            should_label.append(f"({len(should_df)} endpoints)", style="white")

            should_node = vpce_branch.add(should_label)
            if show_details:
                for _, row in should_df.head(10).iterrows():
                    self._add_vpce_detail_node_with_flow_logs(should_node, row)

        # COULD tier
        if "COULD" in tier_groups:
            could_df = tier_groups["COULD"]
            could_label = Text()
            could_label.append("💡 COULD Consider ", style="bold bright_blue")
            could_label.append(f"({len(could_df)} endpoints)", style="white")

            could_node = vpce_branch.add(could_label)
            if show_details:
                for _, row in could_df.head(5).iterrows():  # Limit to top 5
                    self._add_vpce_detail_node_with_flow_logs(could_node, row)

        # KEEP tier
        if "KEEP" in tier_groups:
            keep_df = tier_groups["KEEP"]
            keep_label = Text()
            keep_label.append("✅ KEEP ", style="bold bright_green")
            keep_label.append(f"({len(keep_df)} endpoints, Active)", style="white")

            vpce_branch.add(keep_label)  # No details for KEEP

    def _add_vpce_detail_node_with_flow_logs(self, parent_node: Tree, row: "pd.Series") -> None:
        """
        Add VPC Endpoint detail node with Flow Logs status.

        Args:
            parent_node: Parent tree node
            row: DataFrame row with VPC Endpoint data
        """
        endpoint_id = row.get("vpc_endpoint_id", "Unknown")
        service_name = row.get("service_name", "Unknown")
        score = row.get("decommission_score", 0)
        confidence = row.get("confidence", 0.75)
        flow_logs_enabled = row.get("flow_logs_enabled", False)
        vpc_cost = row.get("vpc_cost_90d", 0.0)

        # Collect active signals
        signals = []
        for i in range(1, 11):
            signal_col = f"v{i}_signal"
            if row.get(signal_col, False):
                signals.append(f"V{i}")

        signals_str = ", ".join(signals) if signals else "None"

        # Format node label
        node_label = Text()
        node_label.append(f"{endpoint_id[:20]} ", style="cyan")

        # Extract service type from service name
        service_type = service_name.split(".")[-1] if "." in service_name else service_name
        node_label.append(f"[{service_type}] ", style="dim white")

        # Color-code score
        if score >= 80:
            score_style = "bold bright_red"
        elif score >= 50:
            score_style = "bold bright_yellow"
        else:
            score_style = "bold bright_blue"

        node_label.append(f"Score: ", style="white")
        node_label.append(f"{score}/100 ", style=score_style)

        # Confidence indicator
        confidence_indicator = "HIGH" if confidence >= 0.90 else "MEDIUM"
        confidence_style = "bright_green" if confidence >= 0.90 else "bright_yellow"
        node_label.append(f"({confidence_indicator}, ", style=confidence_style)

        # Flow Logs status
        if flow_logs_enabled:
            node_label.append("✅ Flow Logs", style="bright_green")
        else:
            node_label.append("⚠️ No Flow Logs", style="bright_yellow")

        node_label.append(") ", style="white")
        node_label.append(f"[{signals_str}] ", style="bright_magenta")

        # Add cost
        if vpc_cost > 0:
            node_label.append(f"| ${vpc_cost:.2f}/90d", style="bright_green")

        parent_node.add(node_label)

    def _add_nat_tier_nodes_with_flow_logs(self, parent_node: Tree, nat_df: "pd.DataFrame", show_details: bool) -> None:
        """
        Add NAT Gateway nodes with Flow Logs status display.

        Args:
            parent_node: Parent tree node
            nat_df: DataFrame with NAT Gateway analysis
            show_details: Show resource-level details
        """
        # NAT Gateway branch
        nat_label = Text()
        nat_label.append("🌐 NAT Gateways ", style="bold yellow")
        nat_label.append(f"({len(nat_df)} discovered)", style="white")

        nat_branch = parent_node.add(nat_label)

        # Group by decommission tier
        tier_groups = {}
        for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
            tier_df = (
                nat_df[nat_df["decommission_tier"] == tier] if "decommission_tier" in nat_df.columns else nat_df.head(0)
            )
            if len(tier_df) > 0:
                tier_groups[tier] = tier_df

        # MUST tier
        if "MUST" in tier_groups:
            must_df = tier_groups["MUST"]
            must_label = Text()
            must_label.append("❌ MUST Decommission ", style="bold bright_red")
            must_label.append(f"({len(must_df)} gateways)", style="white")

            must_node = nat_branch.add(must_label)
            if show_details:
                for _, row in must_df.head(10).iterrows():
                    self._add_nat_detail_node_with_flow_logs(must_node, row)

        # SHOULD tier
        if "SHOULD" in tier_groups:
            should_df = tier_groups["SHOULD"]
            should_label = Text()
            should_label.append("⚠️  SHOULD Optimize ", style="bold bright_yellow")
            should_label.append(f"({len(should_df)} gateways)", style="white")

            should_node = nat_branch.add(should_label)
            if show_details:
                for _, row in should_df.head(10).iterrows():
                    self._add_nat_detail_node_with_flow_logs(should_node, row)

        # COULD tier
        if "COULD" in tier_groups:
            could_df = tier_groups["COULD"]
            could_label = Text()
            could_label.append("💡 COULD Consider ", style="bold bright_blue")
            could_label.append(f"({len(could_df)} gateways)", style="white")

            could_node = nat_branch.add(could_label)
            if show_details:
                for _, row in could_df.head(5).iterrows():
                    self._add_nat_detail_node_with_flow_logs(could_node, row)

        # KEEP tier
        if "KEEP" in tier_groups:
            keep_df = tier_groups["KEEP"]
            keep_label = Text()
            keep_label.append("✅ KEEP ", style="bold bright_green")
            keep_label.append(f"({len(keep_df)} gateways, Active)", style="white")

            nat_branch.add(keep_label)  # No details for KEEP

    def _add_nat_detail_node_with_flow_logs(self, parent_node: Tree, row: "pd.Series") -> None:
        """
        Add NAT Gateway detail node with Flow Logs status.

        Args:
            parent_node: Parent tree node
            row: DataFrame row with NAT Gateway data
        """
        nat_id = row.get("nat_gateway_id", "Unknown")
        vpc_id = row.get("vpc_id", "Unknown")
        az = row.get("availability_zone", "Unknown")
        score = row.get("decommission_score", 0)
        confidence = row.get("confidence", 0.75)
        flow_logs_enabled = row.get("flow_logs_enabled", False)
        bytes_out = row.get("bytes_out_90d", 0)

        # Collect active signals
        signals = []
        for i in range(1, 11):
            signal_col = f"n{i}_signal"
            if row.get(signal_col, False):
                signals.append(f"N{i}")

        signals_str = ", ".join(signals) if signals else "None"

        # Format node label
        node_label = Text()
        node_label.append(f"{nat_id[:20]} ", style="cyan")
        node_label.append(f"[{az}] ", style="dim white")

        # Color-code score
        if score >= 80:
            score_style = "bold bright_red"
        elif score >= 50:
            score_style = "bold bright_yellow"
        else:
            score_style = "bold bright_blue"

        node_label.append(f"Score: ", style="white")
        node_label.append(f"{score}/100 ", style=score_style)

        # Confidence indicator
        confidence_indicator = "HIGH" if confidence >= 0.90 else "MEDIUM"
        confidence_style = "bright_green" if confidence >= 0.90 else "bright_yellow"
        node_label.append(f"({confidence_indicator}, ", style=confidence_style)

        # Flow Logs status
        if flow_logs_enabled:
            node_label.append("✅ Flow Logs", style="bright_green")
        else:
            node_label.append("⚠️ No Flow Logs", style="bright_yellow")

        node_label.append(") ", style="white")
        node_label.append(f"[{signals_str}] ", style="bright_magenta")

        # Add bytes transferred
        gb_out = bytes_out / (1024**3) if bytes_out else 0
        if gb_out > 0:
            node_label.append(f"| {gb_out:.2f} GB/90d", style="bright_green")
        else:
            node_label.append(f"| 0 GB/90d", style="dim white")

        parent_node.add(node_label)

    def _display_summary_table(self, report: ActivityHealthReport) -> None:
        """
        Display summary statistics table.

        Args:
            report: Activity health report
        """
        table = create_table(
            title="Decommission Tier Summary",
            columns=[
                {"name": "Tier", "style": "bold"},
                {"name": "Buckets", "style": "white"},
                {"name": "Annual Cost", "style": "white"},
                {"name": "Potential Savings", "style": "bright_green"},
                {"name": "Savings %", "style": "bright_green"},
            ],
        )

        # MUST Decommission row
        must_savings_pct = (
            (report.must_decommission.potential_annual_savings / report.must_decommission.total_annual_cost * 100)
            if report.must_decommission.total_annual_cost > 0
            else 0.0
        )
        table.add_row(
            "[bright_red]MUST Decommission[/bright_red]",
            str(report.must_decommission.bucket_count),
            format_cost(report.must_decommission.total_annual_cost),
            format_cost(report.must_decommission.potential_annual_savings),
            f"{must_savings_pct:.1f}%",
        )

        # SHOULD Optimize row
        should_savings_pct = (
            (report.should_optimize.potential_annual_savings / report.should_optimize.total_annual_cost * 100)
            if report.should_optimize.total_annual_cost > 0
            else 0.0
        )
        table.add_row(
            "[bright_yellow]SHOULD Optimize[/bright_yellow]",
            str(report.should_optimize.bucket_count),
            format_cost(report.should_optimize.total_annual_cost),
            format_cost(report.should_optimize.potential_annual_savings),
            f"{should_savings_pct:.1f}%",
        )

        # KEEP row
        table.add_row(
            "[bright_green]KEEP[/bright_green]",
            str(report.keep.bucket_count),
            format_cost(report.keep.total_annual_cost),
            format_cost(0.0),
            "0.0%",
        )

        # Total row
        total_savings_pct = (
            (report.total_potential_savings / report.total_annual_cost * 100) if report.total_annual_cost > 0 else 0.0
        )
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{report.total_buckets}[/bold]",
            f"[bold]{format_cost(report.total_annual_cost)}[/bold]",
            f"[bold bright_green]{format_cost(report.total_potential_savings)}[/bold bright_green]",
            f"[bold bright_green]{total_savings_pct:.1f}%[/bold bright_green]",
        )

        console.print(table)
        console.print()

    def export_recommendations(self, format: str = "json", output_file: Optional[str] = None) -> str:
        """
        Export decommission recommendations.

        Supports multiple export formats:
        - json: Complete JSON report with all details
        - csv: Bucket-level CSV for spreadsheet analysis
        - html: Executive summary HTML report

        Args:
            format: Export format ('json', 'csv', 'html')
            output_file: Output file path (auto-generated if None)

        Returns:
            Path to exported file

        Example:
            >>> tree.export_recommendations(
            ...     format='json',
            ...     output_file='/tmp/s3-decommission.json'
            ... )
            '/tmp/s3-decommission.json'
        """
        if not self._report:
            raise ValueError("No report available. Run display_activity_tree() first.")

        # Auto-generate filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"/tmp/s3-decommission-{self._report.account_id}-{timestamp}.{format}"

        output_path = Path(output_file)

        if format == "json":
            self._export_json(output_path)
        elif format == "csv":
            self._export_csv(output_path)
        elif format == "html":
            self._export_html(output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        print_success(f"Exported recommendations to: {output_path}")
        return str(output_path)

    def _export_json(self, output_path: Path) -> None:
        """Export report as JSON."""
        with open(output_path, "w") as f:
            json.dump(self._report.to_dict(), f, indent=2)

    def _export_csv(self, output_path: Path) -> None:
        """Export bucket-level recommendations as CSV."""
        import csv

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "Bucket Name",
                    "Region",
                    "Tier",
                    "Activity Pattern",
                    "Requests/Day",
                    "Size (GB)",
                    "Signals",
                    "Annual Cost",
                    "Potential Savings",
                    "Confidence",
                ]
            )

            # MUST Decommission
            for bucket in self._report.must_decommission.buckets:
                self._write_bucket_row(writer, bucket, "MUST")

            # SHOULD Optimize
            for bucket in self._report.should_optimize.buckets:
                self._write_bucket_row(writer, bucket, "SHOULD")

            # KEEP
            for bucket in self._report.keep.buckets:
                self._write_bucket_row(writer, bucket, "KEEP")

    def _write_bucket_row(self, writer, bucket: S3ActivityAnalysis, tier: str) -> None:
        """Write bucket row to CSV."""
        signals = ", ".join(signal.value for signal in bucket.idle_signals)

        writer.writerow(
            [
                bucket.bucket_name,
                bucket.region,
                tier,
                bucket.activity_pattern.value,
                f"{bucket.metrics.avg_requests_per_day:.1f}",
                f"{bucket.metrics.total_size_gb:.2f}",
                signals or "None",
                f"{bucket.annual_cost:.2f}",
                f"{bucket.potential_savings:.2f}",
                f"{bucket.confidence:.2f}",
            ]
        )

    def _export_html(self, output_path: Path) -> None:
        """Export executive summary as HTML with S3 Lifecycle Recommendations."""
        # Generate lifecycle recommendations HTML section
        lifecycle_html = ""
        if self._lifecycle_recommendations:
            # Sort by savings (descending)
            sorted_recs = sorted(
                self._lifecycle_recommendations, key=lambda x: x.get("estimated_annual_savings", 0), reverse=True
            )[:20]  # Top 20 recommendations

            lifecycle_rows = ""
            for rec in sorted_recs:
                strategy_display = {
                    "INTELLIGENT_TIERING": "IT",
                    "GLACIER": "Glacier",
                    "GLACIER_DA": "Deep Archive",
                    "EXPIRATION": "Expire",
                }.get(rec.get("recommendation_type", ""), rec.get("recommendation_type", "Unknown"))

                confidence = rec.get("confidence", "MEDIUM")
                confidence_color = {"HIGH": "#4CAF50", "MEDIUM": "#FFC107", "LOW": "#F44336"}.get(confidence, "#9E9E9E")

                lifecycle_rows += f"""
        <tr>
            <td>{rec.get("bucket_name", "Unknown")[:40]}</td>
            <td>{rec.get("region", "Unknown")}</td>
            <td>{strategy_display}</td>
            <td>{rec.get("transition_days", 0)}</td>
            <td>{rec.get("target_storage_class", "Unknown")}</td>
            <td style="color: green; font-weight: bold;">${rec.get("estimated_annual_savings", 0):,.2f}</td>
            <td style="color: {confidence_color};">{confidence}</td>
        </tr>"""

            lifecycle_html = f"""
    <h2>S3 Lifecycle Recommendations</h2>
    <table>
        <tr>
            <th>Bucket Name</th>
            <th>Region</th>
            <th>Strategy</th>
            <th>Transition Days</th>
            <th>Target Class</th>
            <th>Annual Savings</th>
            <th>Confidence</th>
        </tr>
        {lifecycle_rows}
    </table>
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>S3 Decommission Recommendations - {self._report.account_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .must {{ background-color: #ffebee; }}
        .should {{ background-color: #fff9c4; }}
        .keep {{ background-color: #e8f5e9; }}
    </style>
</head>
<body>
    <h1>S3 Storage Decommission Recommendations</h1>

    <div class="summary">
        <p><strong>Account:</strong> {self._report.account_id}</p>
        <p><strong>Region:</strong> {self._report.region}</p>
        <p><strong>Total Buckets:</strong> {self._report.total_buckets}</p>
        <p><strong>Total Annual Cost:</strong> ${self._report.total_annual_cost:,.2f}</p>
        <p><strong>Potential Annual Savings:</strong> <span style="color: green; font-weight: bold;">${self._report.total_potential_savings:,.2f}</span></p>
        <p><strong>Analysis Date:</strong> {self._report.analysis_timestamp}</p>
    </div>

    <h2>Tier Summary</h2>
    <table>
        <tr>
            <th>Tier</th>
            <th>Buckets</th>
            <th>Annual Cost</th>
            <th>Potential Savings</th>
        </tr>
        <tr class="must">
            <td><strong>MUST Decommission</strong></td>
            <td>{self._report.must_decommission.bucket_count}</td>
            <td>${self._report.must_decommission.total_annual_cost:,.2f}</td>
            <td>${self._report.must_decommission.potential_annual_savings:,.2f}</td>
        </tr>
        <tr class="should">
            <td><strong>SHOULD Optimize</strong></td>
            <td>{self._report.should_optimize.bucket_count}</td>
            <td>${self._report.should_optimize.total_annual_cost:,.2f}</td>
            <td>${self._report.should_optimize.potential_annual_savings:,.2f}</td>
        </tr>
        <tr class="keep">
            <td><strong>KEEP</strong></td>
            <td>{self._report.keep.bucket_count}</td>
            <td>${self._report.keep.total_annual_cost:,.2f}</td>
            <td>$0.00</td>
        </tr>
    </table>
{lifecycle_html}
</body>
</html>
"""

        with open(output_path, "w") as f:
            f.write(html_content)

    def _create_empty_report(self, account_id: str) -> ActivityHealthReport:
        """Create empty report when no buckets found."""
        empty_tier = TierSummary(
            tier=DecommissionTier.KEEP,
            bucket_count=0,
            total_monthly_cost=0.0,
            total_annual_cost=0.0,
            potential_monthly_savings=0.0,
            potential_annual_savings=0.0,
            buckets=[],
        )

        return ActivityHealthReport(
            account_id=account_id,
            region=self.region,
            total_buckets=0,
            total_annual_cost=0.0,
            total_potential_savings=0.0,
            must_decommission=empty_tier,
            should_optimize=empty_tier,
            keep=empty_tier,
            analysis_timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_activity_health_tree(
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 90
) -> ActivityHealthTree:
    """
    Factory function to create ActivityHealthTree.

    Provides clean initialization pattern following enterprise architecture
    with automatic profile resolution and sensible defaults.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudWatch lookback period (default: 90)

    Returns:
        Initialized ActivityHealthTree instance

    Example:
        >>> tree = create_activity_health_tree()
        >>> # Tree ready for visualization
        >>> tree.display_activity_tree(account_id='123456789012')
    """
    return ActivityHealthTree(operational_profile=operational_profile, region=region, lookback_days=lookback_days)


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core tree class
    "ActivityHealthTree",
    # Data models - S3
    "ActivityHealthReport",
    "TierSummary",
    "DecommissionTier",
    # Data models - VPC (v1.1.29)
    "VPCEndpointSummary",
    "NATGatewaySummary",
    "VPCResourceTierSummary",
    # Factory function
    "create_activity_health_tree",
]
