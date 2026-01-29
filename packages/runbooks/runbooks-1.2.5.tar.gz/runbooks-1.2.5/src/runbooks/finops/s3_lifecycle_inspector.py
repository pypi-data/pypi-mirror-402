#!/usr/bin/env python3
"""
S3 Lifecycle Inspector - Deep Inspection Beyond Binary Checks
==============================================================

Business Value: Identifies lifecycle optimization opportunities with granular analysis
Strategic Impact: Resolves "bucket cost > service cost" discrepancy root cause

Architecture Pattern: Enterprise S3 lifecycle analysis with effectiveness scoring
- Parse lifecycle rules (transitions, expirations, filters, prefixes)
- Calculate effectiveness score (0-100) based on AWS best practices
- Identify missing critical transitions
- Calculate potential savings from lifecycle optimization
- Generate actionable recommendations

Lifecycle Effectiveness Scoring (0-100):
- Standard→IA transition: +25 pts
- IA→Glacier transition: +25 pts
- Glacier→Deep Archive transition: +25 pts
- Expiration rules: +20 pts
- NoncurrentVersionExpiration: +20 pts
- AbortIncompleteMultipartUpload: +10 pts
- Prefix/tag filters: +10 pts (bonus for targeted rules)

Usage:
    from runbooks.finops.s3_lifecycle_inspector import S3LifecycleInspector

    inspector = S3LifecycleInspector(boto_session, region='ap-southeast-2')
    analysis = inspector.analyze_lifecycle_rules('vamsnz-prod-atlassian-backups')

    print(f"Effectiveness: {analysis.effectiveness_score}/100")
    print(f"Missing transitions: {analysis.missing_transitions}")
    print(f"Potential savings: ${analysis.potential_annual_savings:,.2f}/year")

Integration:
    Enhanced by S3ActivityEnricher._check_lifecycle() for deep inspection vs binary exists check

Author: Runbooks Team
Version: 1.1.27
Track: Phase 4.1 - S3 Lifecycle Inspector
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
class LifecycleRule:
    """Parsed lifecycle rule with all transition details."""

    rule_id: str
    status: str  # Enabled/Disabled
    prefix: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    # Transitions
    standard_to_ia_days: Optional[int] = None
    ia_to_glacier_days: Optional[int] = None
    glacier_to_deep_archive_days: Optional[int] = None

    # Expirations
    expiration_days: Optional[int] = None
    noncurrent_version_expiration_days: Optional[int] = None
    abort_incomplete_multipart_days: Optional[int] = None

    # Metadata
    filter_type: str = "prefix"  # prefix, tag, or both


@dataclass
class LifecycleAnalysis:
    """
    Comprehensive lifecycle analysis result.

    Provides effectiveness scoring and actionable recommendations for
    S3 bucket lifecycle optimization.
    """

    bucket_name: str
    region: str
    has_lifecycle: bool

    # Parsed rules
    rules: List[LifecycleRule] = field(default_factory=list)
    enabled_rules_count: int = 0
    disabled_rules_count: int = 0

    # Effectiveness scoring (0-100)
    effectiveness_score: int = 0
    score_breakdown: Dict[str, int] = field(default_factory=dict)

    # Missing critical transitions
    missing_transitions: List[str] = field(default_factory=list)

    # Cost impact
    current_storage_gb: float = 0.0
    potential_monthly_savings: float = 0.0
    potential_annual_savings: float = 0.0

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    priority: str = "LOW"  # LOW, MEDIUM, HIGH

    # Metadata
    analysis_timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bucket_name": self.bucket_name,
            "region": self.region,
            "has_lifecycle": self.has_lifecycle,
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "status": r.status,
                    "prefix": r.prefix,
                    "tags": r.tags,
                    "transitions": {
                        "standard_to_ia_days": r.standard_to_ia_days,
                        "ia_to_glacier_days": r.ia_to_glacier_days,
                        "glacier_to_deep_archive_days": r.glacier_to_deep_archive_days,
                    },
                    "expirations": {
                        "expiration_days": r.expiration_days,
                        "noncurrent_version_expiration_days": r.noncurrent_version_expiration_days,
                        "abort_incomplete_multipart_days": r.abort_incomplete_multipart_days,
                    },
                    "filter_type": r.filter_type,
                }
                for r in self.rules
            ],
            "enabled_rules_count": self.enabled_rules_count,
            "disabled_rules_count": self.disabled_rules_count,
            "effectiveness_score": self.effectiveness_score,
            "score_breakdown": self.score_breakdown,
            "missing_transitions": self.missing_transitions,
            "current_storage_gb": self.current_storage_gb,
            "potential_monthly_savings": self.potential_monthly_savings,
            "potential_annual_savings": self.potential_annual_savings,
            "recommendations": self.recommendations,
            "priority": self.priority,
            "analysis_timestamp": self.analysis_timestamp,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE INSPECTOR CLASS
# ═════════════════════════════════════════════════════════════════════════════


class S3LifecycleInspector:
    """
    S3 lifecycle inspector for deep rule analysis.

    Provides granular lifecycle policy inspection beyond simple exists/not-exists checks,
    enabling actionable cost optimization recommendations.

    Capabilities:
    - Parse lifecycle rules (transitions, expirations, filters)
    - Calculate effectiveness score (0-100) based on AWS best practices
    - Identify missing critical transitions
    - Calculate potential savings from lifecycle optimization
    - Generate prioritized recommendations

    Effectiveness Scoring Framework (0-100):
    - Standard→IA transition: +25 pts
    - IA→Glacier transition: +25 pts
    - Glacier→Deep Archive transition: +25 pts
    - Expiration rules: +20 pts
    - NoncurrentVersionExpiration: +20 pts
    - AbortIncompleteMultipartUpload: +10 pts
    - Targeted filters (prefix/tags): +10 pts bonus

    Example:
        >>> inspector = S3LifecycleInspector(session)
        >>> analysis = inspector.analyze_lifecycle_rules('my-bucket')
        >>> if analysis.effectiveness_score < 50:
        ...     print(f"Low effectiveness: {analysis.missing_transitions}")
    """

    # AWS best practice thresholds
    RECOMMENDED_IA_DAYS = 30  # Standard → IA transition
    RECOMMENDED_GLACIER_DAYS = 90  # IA → Glacier transition
    RECOMMENDED_DEEP_ARCHIVE_DAYS = 180  # Glacier → Deep Archive transition

    # Pricing estimates (ap-southeast-2) - should use DynamicAWSPricing in production
    STORAGE_COST_STANDARD_GB = 0.025  # $0.025/GB-month
    STORAGE_COST_IA_GB = 0.0125  # $0.0125/GB-month (50% savings)
    STORAGE_COST_GLACIER_GB = 0.005  # $0.005/GB-month (80% savings)
    STORAGE_COST_DEEP_ARCHIVE_GB = 0.002  # $0.002/GB-month (92% savings)

    def __init__(self, session: boto3.Session, region: str = "ap-southeast-2"):
        """
        Initialize S3 lifecycle inspector.

        Args:
            session: Boto3 session with S3 permissions
            region: AWS region for S3 operations
        """
        self.session = session
        self.region = region
        self.s3_client = session.client("s3", region_name=region)
        self.cloudwatch_client = session.client("cloudwatch", region_name=region)
        self.logger = logging.getLogger(__name__)

    def analyze_lifecycle_rules(self, bucket_name: str, storage_size_gb: Optional[float] = None) -> LifecycleAnalysis:
        """
        Analyze S3 bucket lifecycle rules with deep inspection.

        Workflow:
        1. Retrieve lifecycle configuration from AWS API
        2. Parse rules (transitions, expirations, filters, prefixes)
        3. Calculate effectiveness score (0-100)
        4. Identify missing critical transitions
        5. Calculate potential savings
        6. Generate prioritized recommendations

        Args:
            bucket_name: S3 bucket name
            storage_size_gb: Current storage size (GB) for cost calculations

        Returns:
            Comprehensive lifecycle analysis with effectiveness score and recommendations
        """
        print_section(f"Analyzing Lifecycle Rules: {bucket_name}")

        # Get lifecycle configuration
        rules = self._get_lifecycle_rules(bucket_name)
        has_lifecycle = len(rules) > 0

        if not has_lifecycle:
            print_warning(f"No lifecycle rules configured for {bucket_name}")
            return self._create_no_lifecycle_analysis(bucket_name, storage_size_gb)

        # Parse rules
        parsed_rules = [self._parse_lifecycle_rule(rule) for rule in rules]
        enabled_rules = [r for r in parsed_rules if r.status == "Enabled"]
        disabled_rules = [r for r in parsed_rules if r.status == "Disabled"]

        print_info(f"Found {len(enabled_rules)} enabled rules, {len(disabled_rules)} disabled rules")

        # Calculate effectiveness score
        score, breakdown = self._calculate_effectiveness_score(enabled_rules)

        # Identify missing transitions
        missing = self._identify_missing_transitions(enabled_rules)

        # Get storage size if not provided
        if storage_size_gb is None:
            storage_size_gb = self._get_bucket_storage_size(bucket_name)

        # Calculate potential savings
        monthly_savings, annual_savings = self._calculate_potential_savings(missing, storage_size_gb)

        # Generate recommendations
        recommendations, priority = self._generate_recommendations(enabled_rules, missing, score, storage_size_gb)

        # Get bucket region
        try:
            bucket_region = self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        except Exception:
            bucket_region = self.region

        analysis = LifecycleAnalysis(
            bucket_name=bucket_name,
            region=bucket_region,
            has_lifecycle=has_lifecycle,
            rules=parsed_rules,
            enabled_rules_count=len(enabled_rules),
            disabled_rules_count=len(disabled_rules),
            effectiveness_score=score,
            score_breakdown=breakdown,
            missing_transitions=missing,
            current_storage_gb=storage_size_gb,
            potential_monthly_savings=monthly_savings,
            potential_annual_savings=annual_savings,
            recommendations=recommendations,
            priority=priority,
        )

        # Display summary
        self._display_analysis(analysis)

        return analysis

    def _get_lifecycle_rules(self, bucket_name: str) -> List[Dict]:
        """Get lifecycle rules from AWS API."""
        try:
            response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return response.get("Rules", [])
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchLifecycleConfiguration":
                return []
            else:
                self.logger.error(f"Failed to get lifecycle rules for {bucket_name}: {e}")
                return []

    def _parse_lifecycle_rule(self, rule: Dict) -> LifecycleRule:
        """Parse lifecycle rule from AWS API response."""
        parsed = LifecycleRule(rule_id=rule.get("ID", "unknown"), status=rule.get("Status", "Unknown"))

        # Parse filter (prefix and/or tags)
        rule_filter = rule.get("Filter", {})
        if "Prefix" in rule_filter:
            parsed.prefix = rule_filter["Prefix"]
            parsed.filter_type = "prefix"
        elif "And" in rule_filter:
            and_filter = rule_filter["And"]
            parsed.prefix = and_filter.get("Prefix", "")
            if "Tags" in and_filter:
                parsed.tags = {tag["Key"]: tag["Value"] for tag in and_filter["Tags"]}
                parsed.filter_type = "prefix_and_tags"
            else:
                parsed.filter_type = "prefix"
        elif "Tag" in rule_filter:
            tag = rule_filter["Tag"]
            parsed.tags = {tag["Key"]: tag["Value"]}
            parsed.filter_type = "tag"

        # Parse transitions
        for transition in rule.get("Transitions", []):
            storage_class = transition.get("StorageClass")
            days = transition.get("Days")

            if storage_class == "STANDARD_IA" or storage_class == "ONEZONE_IA":
                parsed.standard_to_ia_days = days
            elif storage_class == "GLACIER" or storage_class == "GLACIER_IR":
                parsed.ia_to_glacier_days = days
            elif storage_class == "DEEP_ARCHIVE":
                parsed.glacier_to_deep_archive_days = days

        # Parse expirations
        if "Expiration" in rule:
            parsed.expiration_days = rule["Expiration"].get("Days")

        if "NoncurrentVersionExpiration" in rule:
            parsed.noncurrent_version_expiration_days = rule["NoncurrentVersionExpiration"].get("NoncurrentDays")

        if "AbortIncompleteMultipartUpload" in rule:
            parsed.abort_incomplete_multipart_days = rule["AbortIncompleteMultipartUpload"].get("DaysAfterInitiation")

        return parsed

    def _calculate_effectiveness_score(self, enabled_rules: List[LifecycleRule]) -> Tuple[int, Dict[str, int]]:
        """
        Calculate lifecycle effectiveness score (0-100).

        Scoring framework:
        - Standard→IA transition: +25 pts
        - IA→Glacier transition: +25 pts
        - Glacier→Deep Archive transition: +25 pts
        - Expiration rules: +20 pts
        - NoncurrentVersionExpiration: +20 pts
        - AbortIncompleteMultipartUpload: +10 pts
        - Targeted filters: +10 pts bonus

        Returns:
            Tuple of (total_score, breakdown_dict)
        """
        if not enabled_rules:
            return 0, {}

        breakdown = {}
        total_score = 0

        # Check for Standard→IA transition
        has_ia_transition = any(r.standard_to_ia_days for r in enabled_rules)
        if has_ia_transition:
            total_score += 25
            breakdown["standard_to_ia"] = 25

        # Check for IA→Glacier transition
        has_glacier_transition = any(r.ia_to_glacier_days for r in enabled_rules)
        if has_glacier_transition:
            total_score += 25
            breakdown["ia_to_glacier"] = 25

        # Check for Glacier→Deep Archive transition
        has_deep_archive_transition = any(r.glacier_to_deep_archive_days for r in enabled_rules)
        if has_deep_archive_transition:
            total_score += 25
            breakdown["glacier_to_deep_archive"] = 25

        # Check for expiration rules
        has_expiration = any(r.expiration_days for r in enabled_rules)
        if has_expiration:
            total_score += 20
            breakdown["expiration"] = 20

        # Check for noncurrent version expiration
        has_noncurrent_expiration = any(r.noncurrent_version_expiration_days for r in enabled_rules)
        if has_noncurrent_expiration:
            total_score += 20
            breakdown["noncurrent_version_expiration"] = 20

        # Check for abort incomplete multipart
        has_abort_multipart = any(r.abort_incomplete_multipart_days for r in enabled_rules)
        if has_abort_multipart:
            total_score += 10
            breakdown["abort_incomplete_multipart"] = 10

        # Bonus for targeted filters (prefix/tags)
        has_targeted_filters = any(r.filter_type in ["tag", "prefix_and_tags"] for r in enabled_rules)
        if has_targeted_filters:
            total_score += 10
            breakdown["targeted_filters"] = 10

        # Cap at 100
        total_score = min(total_score, 100)

        return total_score, breakdown

    def _identify_missing_transitions(self, enabled_rules: List[LifecycleRule]) -> List[str]:
        """Identify missing critical transitions."""
        missing = []

        has_ia = any(r.standard_to_ia_days for r in enabled_rules)
        has_glacier = any(r.ia_to_glacier_days for r in enabled_rules)
        has_deep_archive = any(r.glacier_to_deep_archive_days for r in enabled_rules)
        has_expiration = any(r.expiration_days for r in enabled_rules)
        has_noncurrent_expiration = any(r.noncurrent_version_expiration_days for r in enabled_rules)
        has_abort_multipart = any(r.abort_incomplete_multipart_days for r in enabled_rules)

        if not has_ia:
            missing.append("Standard → IA transition (30 days recommended)")
        if not has_glacier:
            missing.append("IA → Glacier transition (90 days recommended)")
        if not has_deep_archive:
            missing.append("Glacier → Deep Archive transition (180 days recommended)")
        if not has_expiration:
            missing.append("Expiration rule (lifecycle cleanup)")
        if not has_noncurrent_expiration:
            missing.append("Noncurrent version expiration (versioning cleanup)")
        if not has_abort_multipart:
            missing.append("Abort incomplete multipart upload (reduce storage waste)")

        return missing

    def _get_bucket_storage_size(self, bucket_name: str) -> float:
        """Get bucket storage size (GB) from CloudWatch."""
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "StandardStorage"},
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
        except Exception as e:
            self.logger.debug(f"Failed to get bucket size for {bucket_name}: {e}")
            return 0.0

    def _calculate_potential_savings(self, missing_transitions: List[str], storage_gb: float) -> Tuple[float, float]:
        """
        Calculate potential monthly and annual savings from missing transitions.

        Savings calculation:
        - Standard→IA: 50% savings ($0.025 → $0.0125/GB-month)
        - IA→Glacier: 80% savings ($0.025 → $0.005/GB-month)
        - Glacier→Deep Archive: 92% savings ($0.025 → $0.002/GB-month)

        Returns:
            Tuple of (monthly_savings, annual_savings)
        """
        if storage_gb == 0 or not missing_transitions:
            return 0.0, 0.0

        # Conservative estimate: Assume 30% of data can be transitioned to IA
        ia_eligible_gb = storage_gb * 0.30
        ia_savings = ia_eligible_gb * (self.STORAGE_COST_STANDARD_GB - self.STORAGE_COST_IA_GB)

        # Conservative estimate: Assume 20% of data can be transitioned to Glacier
        glacier_eligible_gb = storage_gb * 0.20
        glacier_savings = glacier_eligible_gb * (self.STORAGE_COST_STANDARD_GB - self.STORAGE_COST_GLACIER_GB)

        # Conservative estimate: Assume 10% of data can be transitioned to Deep Archive
        deep_archive_eligible_gb = storage_gb * 0.10
        deep_archive_savings = deep_archive_eligible_gb * (
            self.STORAGE_COST_STANDARD_GB - self.STORAGE_COST_DEEP_ARCHIVE_GB
        )

        # Sum potential savings
        monthly_savings = 0.0
        if "Standard → IA" in " ".join(missing_transitions):
            monthly_savings += ia_savings
        if "IA → Glacier" in " ".join(missing_transitions):
            monthly_savings += glacier_savings
        if "Glacier → Deep Archive" in " ".join(missing_transitions):
            monthly_savings += deep_archive_savings

        annual_savings = monthly_savings * 12

        return monthly_savings, annual_savings

    def _generate_recommendations(
        self,
        enabled_rules: List[LifecycleRule],
        missing_transitions: List[str],
        effectiveness_score: int,
        storage_gb: float,
    ) -> Tuple[List[str], str]:
        """
        Generate prioritized recommendations.

        Returns:
            Tuple of (recommendations_list, priority)
        """
        recommendations = []

        # Priority calculation
        if effectiveness_score < 30:
            priority = "HIGH"
        elif effectiveness_score < 60:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Generate recommendations based on missing transitions
        if "Standard → IA" in " ".join(missing_transitions):
            recommendations.append(
                f"Configure Standard→IA transition at {self.RECOMMENDED_IA_DAYS} days "
                f"(50% storage cost reduction for infrequently accessed data)"
            )

        if "IA → Glacier" in " ".join(missing_transitions):
            recommendations.append(
                f"Configure IA→Glacier transition at {self.RECOMMENDED_GLACIER_DAYS} days "
                f"(80% storage cost reduction for archive data)"
            )

        if "Glacier → Deep Archive" in " ".join(missing_transitions):
            recommendations.append(
                f"Configure Glacier→Deep Archive transition at {self.RECOMMENDED_DEEP_ARCHIVE_DAYS} days "
                f"(92% storage cost reduction for long-term retention)"
            )

        if "Expiration rule" in " ".join(missing_transitions):
            recommendations.append(
                "Configure expiration rule to automatically delete objects after retention period "
                "(eliminate storage waste)"
            )

        if "Noncurrent version expiration" in " ".join(missing_transitions):
            recommendations.append(
                "Configure noncurrent version expiration to clean up old object versions (reduce versioning overhead)"
            )

        if "Abort incomplete multipart" in " ".join(missing_transitions):
            recommendations.append("Configure abort incomplete multipart upload after 7 days (clean up failed uploads)")

        # Size-based recommendations
        if storage_gb > 1000:  # > 1TB
            recommendations.append(
                f"Large bucket ({storage_gb:.2f} GB) - prioritize lifecycle optimization for maximum cost impact"
            )

        return recommendations, priority

    def _create_no_lifecycle_analysis(self, bucket_name: str, storage_size_gb: Optional[float]) -> LifecycleAnalysis:
        """Create analysis result for buckets without lifecycle rules."""
        if storage_size_gb is None:
            storage_size_gb = self._get_bucket_storage_size(bucket_name)

        missing = [
            "Standard → IA transition (30 days recommended)",
            "IA → Glacier transition (90 days recommended)",
            "Glacier → Deep Archive transition (180 days recommended)",
            "Expiration rule (lifecycle cleanup)",
            "Noncurrent version expiration (versioning cleanup)",
            "Abort incomplete multipart upload (reduce storage waste)",
        ]

        monthly_savings, annual_savings = self._calculate_potential_savings(missing, storage_size_gb)

        recommendations = [
            "No lifecycle rules configured - immediate optimization opportunity",
            f"Implement standard lifecycle policy for {storage_size_gb:.2f} GB storage",
            f"Potential savings: ${annual_savings:,.2f}/year",
        ]

        try:
            bucket_region = self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        except Exception:
            bucket_region = self.region

        return LifecycleAnalysis(
            bucket_name=bucket_name,
            region=bucket_region,
            has_lifecycle=False,
            effectiveness_score=0,
            missing_transitions=missing,
            current_storage_gb=storage_size_gb,
            potential_monthly_savings=monthly_savings,
            potential_annual_savings=annual_savings,
            recommendations=recommendations,
            priority="HIGH" if storage_size_gb > 100 else "MEDIUM",
        )

    def _display_analysis(self, analysis: LifecycleAnalysis) -> None:
        """Display lifecycle analysis in Rich table format."""
        # Summary table
        summary_table = create_table(
            title=f"Lifecycle Analysis: {analysis.bucket_name}",
            columns=[
                {"name": "Metric", "style": "cyan"},
                {"name": "Value", "style": "white"},
            ],
        )

        summary_table.add_row("Has Lifecycle", "Yes" if analysis.has_lifecycle else "No")
        summary_table.add_row("Enabled Rules", str(analysis.enabled_rules_count))
        summary_table.add_row("Effectiveness Score", f"{analysis.effectiveness_score}/100")
        summary_table.add_row("Storage Size", f"{analysis.current_storage_gb:.2f} GB")
        summary_table.add_row("Priority", f"[bold {self._get_priority_color(analysis.priority)}]{analysis.priority}[/]")

        console.print()
        console.print(summary_table)

        # Missing transitions
        if analysis.missing_transitions:
            print_warning(f"Missing {len(analysis.missing_transitions)} critical transitions:")
            for missing in analysis.missing_transitions:
                console.print(f"  • {missing}")

        # Potential savings
        if analysis.potential_annual_savings > 0:
            print_info(
                f"Potential Savings: {format_cost(analysis.potential_monthly_savings)}/month "
                f"({format_cost(analysis.potential_annual_savings)}/year)"
            )

        # Recommendations
        if analysis.recommendations:
            print_section("Recommendations")
            for i, rec in enumerate(analysis.recommendations, 1):
                console.print(f"  {i}. {rec}")

        console.print()

    def _get_priority_color(self, priority: str) -> str:
        """Get color for priority display."""
        if priority == "HIGH":
            return "bright_red"
        elif priority == "MEDIUM":
            return "bright_yellow"
        else:
            return "bright_green"


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    "S3LifecycleInspector",
    "LifecycleAnalysis",
    "LifecycleRule",
]
