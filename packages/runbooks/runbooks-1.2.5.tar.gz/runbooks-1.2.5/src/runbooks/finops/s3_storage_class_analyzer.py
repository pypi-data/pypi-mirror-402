#!/usr/bin/env python3
"""
S3 Storage Class Analyzer - Storage Distribution & Optimization Analysis
========================================================================

Business Value: Identifies storage class optimization opportunities with cost impact quantification
Strategic Impact: Cross-validates lifecycle rules with actual storage distribution

Architecture Pattern: CloudWatch metrics-based storage class analysis
- Query CloudWatch for storage class distribution metrics
- Calculate percentage in each storage class
- Cross-validate with lifecycle rules
- Identify cost optimization opportunities
- Recommend storage class transitions with cost impact

Storage Classes (ap-southeast-2 pricing):
- Standard: $0.025/GB-month (baseline)
- Standard-IA: $0.0125/GB-month (50% savings)
- Intelligent-Tiering: $0.0235/GB-month + $0.0025/object monitoring
- Glacier Instant Retrieval: $0.005/GB-month (80% savings)
- Glacier Flexible Retrieval: $0.0045/GB-month (82% savings)
- Glacier Deep Archive: $0.002/GB-month (92% savings)

Usage:
    from runbooks.finops.s3_storage_class_analyzer import StorageClassAnalyzer

    analyzer = StorageClassAnalyzer(boto_session, region='ap-southeast-2')
    distribution = analyzer.get_storage_class_distribution('vamsnz-prod-atlassian-backups')
    optimization = analyzer.analyze_storage_optimization('vamsnz-prod-atlassian-backups', lifecycle_rules)

    print(f"Current distribution: {distribution.storage_classes}")
    print(f"Optimization opportunity: {format_cost(optimization.annual_savings)}/year")

Integration:
    Used by finops dashboard for storage class validation and optimization recommendations

Author: Runbooks Team
Version: 1.1.27
Track: Phase 4.2 - Storage Class Analyzer
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    create_table,
    format_cost,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class StorageClassDistribution:
    """Storage class distribution for S3 bucket."""

    bucket_name: str
    region: str
    total_storage_gb: float

    # Storage by class (GB)
    standard_gb: float = 0.0
    standard_ia_gb: float = 0.0
    onezone_ia_gb: float = 0.0
    intelligent_tiering_gb: float = 0.0
    glacier_instant_retrieval_gb: float = 0.0
    glacier_flexible_retrieval_gb: float = 0.0
    glacier_deep_archive_gb: float = 0.0
    reduced_redundancy_gb: float = 0.0

    # Percentages
    standard_percent: float = 0.0
    standard_ia_percent: float = 0.0
    intelligent_tiering_percent: float = 0.0
    glacier_percent: float = 0.0
    deep_archive_percent: float = 0.0

    # Metadata
    query_timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bucket_name": self.bucket_name,
            "region": self.region,
            "total_storage_gb": self.total_storage_gb,
            "storage_by_class_gb": {
                "standard": self.standard_gb,
                "standard_ia": self.standard_ia_gb,
                "onezone_ia": self.onezone_ia_gb,
                "intelligent_tiering": self.intelligent_tiering_gb,
                "glacier_instant_retrieval": self.glacier_instant_retrieval_gb,
                "glacier_flexible_retrieval": self.glacier_flexible_retrieval_gb,
                "glacier_deep_archive": self.glacier_deep_archive_gb,
                "reduced_redundancy": self.reduced_redundancy_gb,
            },
            "percentages": {
                "standard": self.standard_percent,
                "standard_ia": self.standard_ia_percent,
                "intelligent_tiering": self.intelligent_tiering_percent,
                "glacier": self.glacier_percent,
                "deep_archive": self.deep_archive_percent,
            },
            "query_timestamp": self.query_timestamp,
        }


@dataclass
class OptimizationReport:
    """Storage class optimization report with cost impact."""

    bucket_name: str
    region: str

    # Current state
    current_distribution: StorageClassDistribution
    current_monthly_cost: float
    current_annual_cost: float

    # Recommended state
    recommended_distribution: Dict[str, float]  # class -> GB
    recommended_monthly_cost: float
    recommended_annual_cost: float

    # Cost impact
    monthly_savings: float
    annual_savings: float
    savings_percent: float

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    confidence: str = "MEDIUM"  # LOW, MEDIUM, HIGH

    # Metadata
    analysis_timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bucket_name": self.bucket_name,
            "region": self.region,
            "current_distribution": self.current_distribution.to_dict(),
            "current_monthly_cost": self.current_monthly_cost,
            "current_annual_cost": self.current_annual_cost,
            "recommended_distribution": self.recommended_distribution,
            "recommended_monthly_cost": self.recommended_monthly_cost,
            "recommended_annual_cost": self.recommended_annual_cost,
            "monthly_savings": self.monthly_savings,
            "annual_savings": self.annual_savings,
            "savings_percent": self.savings_percent,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "analysis_timestamp": self.analysis_timestamp,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE ANALYZER CLASS
# ═════════════════════════════════════════════════════════════════════════════


class StorageClassAnalyzer:
    """
    S3 storage class analyzer for distribution and optimization analysis.

    Provides CloudWatch metrics-based analysis of S3 bucket storage class distribution,
    enabling cost optimization through intelligent storage class transitions.

    Capabilities:
    - Query CloudWatch for storage class distribution metrics
    - Calculate percentage in each storage class
    - Cross-validate with lifecycle rules
    - Identify cost optimization opportunities
    - Recommend storage class transitions with cost impact

    Example:
        >>> analyzer = StorageClassAnalyzer(session)
        >>> distribution = analyzer.get_storage_class_distribution('my-bucket')
        >>> optimization = analyzer.analyze_storage_optimization('my-bucket')
        >>> print(f"Savings: ${optimization.annual_savings:,.2f}/year")
    """

    # Storage class pricing (ap-southeast-2) - should use DynamicAWSPricing in production
    STORAGE_PRICES = {
        "standard": 0.025,  # $0.025/GB-month
        "standard_ia": 0.0125,  # $0.0125/GB-month
        "onezone_ia": 0.01,  # $0.01/GB-month
        "intelligent_tiering": 0.0235,  # $0.0235/GB-month + monitoring
        "glacier_instant_retrieval": 0.005,  # $0.005/GB-month
        "glacier_flexible_retrieval": 0.0045,  # $0.0045/GB-month
        "glacier_deep_archive": 0.002,  # $0.002/GB-month
        "reduced_redundancy": 0.025,  # Same as standard (deprecated)
    }

    def __init__(self, session: boto3.Session, region: str = "ap-southeast-2"):
        """
        Initialize storage class analyzer.

        Args:
            session: Boto3 session with S3 and CloudWatch permissions
            region: AWS region for operations
        """
        self.session = session
        self.region = region
        self.s3_client = session.client("s3", region_name=region)
        self.cloudwatch_client = session.client("cloudwatch", region_name=region)
        self.logger = logging.getLogger(__name__)

    def get_storage_class_distribution(self, bucket_name: str) -> StorageClassDistribution:
        """
        Get storage class distribution from CloudWatch metrics.

        Queries CloudWatch for BucketSizeBytes metric across all storage types:
        - StandardStorage
        - StandardIAStorage
        - IntelligentTieringFAStorage
        - GlacierInstantRetrievalStorage
        - GlacierStorage
        - DeepArchiveStorage

        Args:
            bucket_name: S3 bucket name

        Returns:
            Storage class distribution with GB and percentages
        """
        print_section(f"Analyzing Storage Class Distribution: {bucket_name}")

        distribution = StorageClassDistribution(bucket_name=bucket_name, region=self.region, total_storage_gb=0.0)

        # Query CloudWatch for each storage class
        storage_types = {
            "StandardStorage": "standard_gb",
            "StandardIAStorage": "standard_ia_gb",
            "OneZoneIAStorage": "onezone_ia_gb",
            "IntelligentTieringFAStorage": "intelligent_tiering_gb",
            "IntelligentTieringIAStorage": "intelligent_tiering_gb",  # Add to IT total
            "IntelligentTieringAAStorage": "intelligent_tiering_gb",  # Add to IT total
            "IntelligentTieringAIAStorage": "intelligent_tiering_gb",  # Add to IT total
            "IntelligentTieringDAAStorage": "intelligent_tiering_gb",  # Add to IT total
            "GlacierInstantRetrievalStorage": "glacier_instant_retrieval_gb",
            "GlacierStorage": "glacier_flexible_retrieval_gb",
            "GlacierS3GlacierStorage": "glacier_flexible_retrieval_gb",  # Legacy
            "DeepArchiveStorage": "glacier_deep_archive_gb",
            "ReducedRedundancyStorage": "reduced_redundancy_gb",
        }

        for storage_type, attr_name in storage_types.items():
            size_gb = self._get_storage_size_by_type(bucket_name, storage_type)
            current_value = getattr(distribution, attr_name, 0.0)
            setattr(distribution, attr_name, current_value + size_gb)
            distribution.total_storage_gb += size_gb

        # Calculate percentages
        if distribution.total_storage_gb > 0:
            distribution.standard_percent = (distribution.standard_gb / distribution.total_storage_gb) * 100
            distribution.standard_ia_percent = (distribution.standard_ia_gb / distribution.total_storage_gb) * 100
            distribution.intelligent_tiering_percent = (
                distribution.intelligent_tiering_gb / distribution.total_storage_gb
            ) * 100
            distribution.glacier_percent = (
                distribution.glacier_flexible_retrieval_gb / distribution.total_storage_gb
            ) * 100
            distribution.deep_archive_percent = (
                distribution.glacier_deep_archive_gb / distribution.total_storage_gb
            ) * 100

        # Display distribution
        self._display_distribution(distribution)

        return distribution

    def analyze_storage_optimization(
        self, bucket_name: str, lifecycle_rules: Optional[List[Dict]] = None
    ) -> OptimizationReport:
        """
        Analyze storage class optimization opportunities.

        Workflow:
        1. Get current storage class distribution
        2. Calculate current monthly cost
        3. Generate recommended distribution based on access patterns
        4. Calculate recommended monthly cost
        5. Compute savings and generate recommendations

        Args:
            bucket_name: S3 bucket name
            lifecycle_rules: Optional lifecycle rules for cross-validation

        Returns:
            Optimization report with cost impact and recommendations
        """
        print_section(f"Analyzing Storage Optimization: {bucket_name}")

        # Get current distribution
        current_dist = self.get_storage_class_distribution(bucket_name)

        # Calculate current cost
        current_monthly = self._calculate_storage_cost(current_dist)
        current_annual = current_monthly * 12

        # Generate recommended distribution
        recommended_dist, recommendations, confidence = self._generate_recommendations(current_dist, lifecycle_rules)

        # Calculate recommended cost
        recommended_monthly = self._calculate_recommended_cost(recommended_dist)
        recommended_annual = recommended_monthly * 12

        # Calculate savings
        monthly_savings = current_monthly - recommended_monthly
        annual_savings = monthly_savings * 12
        savings_percent = (monthly_savings / current_monthly * 100) if current_monthly > 0 else 0.0

        # Get bucket region
        try:
            bucket_region = self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        except Exception:
            bucket_region = self.region

        report = OptimizationReport(
            bucket_name=bucket_name,
            region=bucket_region,
            current_distribution=current_dist,
            current_monthly_cost=current_monthly,
            current_annual_cost=current_annual,
            recommended_distribution=recommended_dist,
            recommended_monthly_cost=recommended_monthly,
            recommended_annual_cost=recommended_annual,
            monthly_savings=monthly_savings,
            annual_savings=annual_savings,
            savings_percent=savings_percent,
            recommendations=recommendations,
            confidence=confidence,
        )

        # Display report
        self._display_optimization_report(report)

        return report

    def _get_storage_size_by_type(self, bucket_name: str, storage_type: str) -> float:
        """Get storage size (GB) for specific storage type from CloudWatch."""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": storage_type},
                ],
                StartTime=datetime.now(tz=timezone.utc) - timedelta(days=1),
                EndTime=datetime.now(tz=timezone.utc),
                Period=86400,
                Statistics=["Average"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                size_bytes = datapoints[0]["Average"]
                return size_bytes / (1024**3)  # Convert to GB
            return 0.0
        except ClientError as e:
            self.logger.debug(f"CloudWatch query failed for {bucket_name}/{storage_type}: {e}")
            return 0.0

    def _calculate_storage_cost(self, distribution: StorageClassDistribution) -> float:
        """Calculate monthly storage cost based on distribution."""
        cost = 0.0

        cost += distribution.standard_gb * self.STORAGE_PRICES["standard"]
        cost += distribution.standard_ia_gb * self.STORAGE_PRICES["standard_ia"]
        cost += distribution.onezone_ia_gb * self.STORAGE_PRICES["onezone_ia"]
        cost += distribution.intelligent_tiering_gb * self.STORAGE_PRICES["intelligent_tiering"]
        cost += distribution.glacier_instant_retrieval_gb * self.STORAGE_PRICES["glacier_instant_retrieval"]
        cost += distribution.glacier_flexible_retrieval_gb * self.STORAGE_PRICES["glacier_flexible_retrieval"]
        cost += distribution.glacier_deep_archive_gb * self.STORAGE_PRICES["glacier_deep_archive"]
        cost += distribution.reduced_redundancy_gb * self.STORAGE_PRICES["reduced_redundancy"]

        return cost

    def _generate_recommendations(
        self, distribution: StorageClassDistribution, lifecycle_rules: Optional[List[Dict]]
    ) -> tuple[Dict[str, float], List[str], str]:
        """
        Generate recommended storage class distribution.

        Optimization logic:
        - If >80% in Standard and no lifecycle: Recommend IA/Glacier transitions
        - If lifecycle configured but >50% still in Standard: Review lifecycle effectiveness
        - If intelligent-tiering not used: Recommend for unpredictable access patterns

        Returns:
            Tuple of (recommended_distribution_dict, recommendations_list, confidence)
        """
        recommendations = []
        confidence = "MEDIUM"

        # Start with current distribution
        recommended = {
            "standard": distribution.standard_gb,
            "standard_ia": distribution.standard_ia_gb,
            "onezone_ia": distribution.onezone_ia_gb,
            "intelligent_tiering": distribution.intelligent_tiering_gb,
            "glacier_instant_retrieval": distribution.glacier_instant_retrieval_gb,
            "glacier_flexible_retrieval": distribution.glacier_flexible_retrieval_gb,
            "glacier_deep_archive": distribution.glacier_deep_archive_gb,
            "reduced_redundancy": distribution.reduced_redundancy_gb,
        }

        # Check if lifecycle is configured
        has_lifecycle = lifecycle_rules is not None and len(lifecycle_rules) > 0

        # Scenario 1: High Standard storage without lifecycle
        if distribution.standard_percent > 80 and not has_lifecycle:
            recommendations.append(
                f"{distribution.standard_percent:.1f}% in Standard storage without lifecycle rules - "
                "configure transitions to IA/Glacier for archival data"
            )

            # Assume 40% can move to IA, 30% to Glacier, 10% to Deep Archive
            standard_reduction = distribution.standard_gb * 0.80
            recommended["standard"] = distribution.standard_gb * 0.20
            recommended["standard_ia"] += distribution.standard_gb * 0.40
            recommended["glacier_flexible_retrieval"] += distribution.standard_gb * 0.30
            recommended["glacier_deep_archive"] += distribution.standard_gb * 0.10

            confidence = "HIGH"

        # Scenario 2: High Standard storage with lifecycle
        elif distribution.standard_percent > 50 and has_lifecycle:
            recommendations.append(
                f"{distribution.standard_percent:.1f}% still in Standard storage despite lifecycle rules - "
                "review lifecycle effectiveness and transition timelines"
            )

            # Assume 30% can move with optimized lifecycle
            recommended["standard"] = distribution.standard_gb * 0.30
            recommended["standard_ia"] += distribution.standard_gb * 0.30
            recommended["glacier_flexible_retrieval"] += distribution.standard_gb * 0.25
            recommended["glacier_deep_archive"] += distribution.standard_gb * 0.15

            confidence = "MEDIUM"

        # Scenario 3: No Intelligent-Tiering usage
        if distribution.intelligent_tiering_gb == 0 and distribution.total_storage_gb > 100:
            recommendations.append(
                "Consider Intelligent-Tiering for unpredictable access patterns - "
                "automatic cost optimization based on access frequency"
            )

        # Scenario 4: Reduced Redundancy (deprecated)
        if distribution.reduced_redundancy_gb > 0:
            recommendations.append(
                f"{distribution.reduced_redundancy_gb:.2f} GB in deprecated Reduced Redundancy storage - "
                "migrate to Standard or Standard-IA"
            )

        # Default recommendation
        if not recommendations:
            recommendations.append("Storage class distribution is well-optimized - monitor access patterns")
            confidence = "LOW"

        return recommended, recommendations, confidence

    def _calculate_recommended_cost(self, recommended_dist: Dict[str, float]) -> float:
        """Calculate monthly cost for recommended distribution."""
        cost = 0.0

        for storage_class, size_gb in recommended_dist.items():
            cost += size_gb * self.STORAGE_PRICES[storage_class]

        return cost

    def _display_distribution(self, distribution: StorageClassDistribution) -> None:
        """Display storage class distribution in Rich table format."""
        table = create_table(
            title=f"Storage Class Distribution: {distribution.bucket_name}",
            columns=[
                {"name": "Storage Class", "style": "cyan"},
                {"name": "Size (GB)", "style": "white"},
                {"name": "Percentage", "style": "bright_yellow"},
                {"name": "Monthly Cost", "style": "bright_green"},
            ],
        )

        # Add rows for each storage class
        if distribution.standard_gb > 0:
            table.add_row(
                "Standard",
                f"{distribution.standard_gb:.2f}",
                f"{distribution.standard_percent:.1f}%",
                format_cost(distribution.standard_gb * self.STORAGE_PRICES["standard"]),
            )

        if distribution.standard_ia_gb > 0:
            table.add_row(
                "Standard-IA",
                f"{distribution.standard_ia_gb:.2f}",
                f"{distribution.standard_ia_percent:.1f}%",
                format_cost(distribution.standard_ia_gb * self.STORAGE_PRICES["standard_ia"]),
            )

        if distribution.intelligent_tiering_gb > 0:
            table.add_row(
                "Intelligent-Tiering",
                f"{distribution.intelligent_tiering_gb:.2f}",
                f"{distribution.intelligent_tiering_percent:.1f}%",
                format_cost(distribution.intelligent_tiering_gb * self.STORAGE_PRICES["intelligent_tiering"]),
            )

        if distribution.glacier_flexible_retrieval_gb > 0:
            table.add_row(
                "Glacier Flexible",
                f"{distribution.glacier_flexible_retrieval_gb:.2f}",
                f"{distribution.glacier_percent:.1f}%",
                format_cost(
                    distribution.glacier_flexible_retrieval_gb * self.STORAGE_PRICES["glacier_flexible_retrieval"]
                ),
            )

        if distribution.glacier_deep_archive_gb > 0:
            table.add_row(
                "Deep Archive",
                f"{distribution.glacier_deep_archive_gb:.2f}",
                f"{distribution.deep_archive_percent:.1f}%",
                format_cost(distribution.glacier_deep_archive_gb * self.STORAGE_PRICES["glacier_deep_archive"]),
            )

        # Total row
        total_cost = self._calculate_storage_cost(distribution)
        table.add_row(
            "[bold]Total[/bold]",
            f"[bold]{distribution.total_storage_gb:.2f}[/bold]",
            "[bold]100.0%[/bold]",
            f"[bold]{format_cost(total_cost)}[/bold]",
        )

        console.print()
        console.print(table)
        console.print()

    def _display_optimization_report(self, report: OptimizationReport) -> None:
        """Display optimization report in Rich table format."""
        print_section("Optimization Summary")

        print_info(f"Current Monthly Cost: {format_cost(report.current_monthly_cost)}")
        print_info(f"Recommended Monthly Cost: {format_cost(report.recommended_monthly_cost)}")

        if report.monthly_savings > 0:
            print_success(
                f"Potential Savings: {format_cost(report.monthly_savings)}/month "
                f"({format_cost(report.annual_savings)}/year) - {report.savings_percent:.1f}% reduction"
            )
        else:
            print_info("No optimization opportunities identified")

        if report.recommendations:
            print_section("Recommendations")
            for i, rec in enumerate(report.recommendations, 1):
                console.print(f"  {i}. {rec}")

        print_info(f"Confidence: {report.confidence}")
        console.print()


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    "StorageClassAnalyzer",
    "StorageClassDistribution",
    "OptimizationReport",
]
