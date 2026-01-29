#!/usr/bin/env python3
"""
S3 Activity Enricher - S3 Bucket Activity Signals
==================================================

Business Value: Idle S3 bucket detection enabling cost optimization
Strategic Impact: Complement ECS/DynamoDB patterns for storage workloads
Integration: Feeds data to FinOps decommission scoring framework

Architecture Pattern: 5-layer enrichment framework (matches DynamoDB/ECS patterns)
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: S3 activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses S1-S10 signals)

Decommission Signals (S1-S10) - AWS Well-Architected Framework Aligned:

Tier 1: High-Confidence (60 points max)
- S1 (40 pts): Storage Lens Inactive - 0 requests 90d (Confidence: 0.95)
- S2 (20 pts): Storage Class Inefficiency - STANDARD with <1 access/month (Confidence: 0.85)

Tier 2: Medium-Confidence (45 points max)
- S3 (15 pts): Lifecycle Missing - No lifecycle + objects >365d (Confidence: 0.80)
- S4 (10 pts): Intelligent-Tiering Off - Bucket >10GB without IT (Confidence: 0.80)
- S5 (10 pts): Versioning No Expiration - Versioning + no expiration (Confidence: 0.80)
- S6 (10 pts): Zero Requests 90D - CloudWatch AllRequests=0 (Confidence: 0.80)

Tier 3: Lower-Confidence (20 points max)
- S7 (5 pts): Replication Waste - Replication to 0-access bucket (Confidence: 0.70)
- S8 (5 pts): Public No Encryption - Public + no encryption + 0 GET (Confidence: 0.70)
- S9 (5 pts): Inventory Overhead - Inventory on <1GB/0-access bucket (Confidence: 0.70)
- S10 (5 pts): High Request Cost - Request cost >$10/month declining (Confidence: 0.70)

Usage:
    from runbooks.finops.s3_activity_enricher import S3ActivityEnricher

    enricher = S3ActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze S3 bucket activity
    analyses = enricher.analyze_bucket_activity(
        bucket_names=['my-bucket-name']
    )

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer S3 service costs
    - Flag discrepancies (low activity but high costs = potential issue)
    - Achieve ≥99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 2 - S3 Activity Enricher
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    create_panel,
    create_progress_bar,
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


# ═════════════════════════════════════════════════════════════════════════════
# ENUMERATION TYPES
# ═════════════════════════════════════════════════════════════════════════════


class S3IdleSignal(str, Enum):
    """
    S3 decommission signals (S1-S10) - AWS Well-Architected Framework Aligned.

    Signal Framework v2.0: Hybrid 0-100 scoring with tier-based confidence levels.
    Total Maximum Points: 125 (normalized to 0-100 scale)

    Tier 1: High-Confidence Signals (60 points max)
    - S1 (40 pts): Storage Lens Inactive - 0 requests 90d (Confidence: 0.95)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
    - S2 (20 pts): Storage Class Inefficiency - STANDARD with <1 access/month (Confidence: 0.85)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html

    Tier 2: Medium-Confidence Signals (45 points max)
    - S3 (15 pts): Lifecycle Missing - No lifecycle + objects >365d (Confidence: 0.80)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
    - S4 (10 pts): Intelligent-Tiering Off - Bucket >10GB without IT (Confidence: 0.80)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
    - S5 (10 pts): Versioning No Expiration - Versioning + no expiration (Confidence: 0.80)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
    - S6 (10 pts): Zero Requests 90D - CloudWatch AllRequests=0 (Confidence: 0.80)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

    Tier 3: Lower-Confidence Signals (20 points max)
    - S7 (5 pts): Replication Waste - Replication to 0-access bucket (Confidence: 0.70)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
    - S8 (5 pts): Public No Encryption - Public + no encryption + 0 GET (Confidence: 0.70)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
    - S9 (5 pts): Inventory Overhead - Inventory on <1GB/0-access bucket (Confidence: 0.70)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
    - S10 (5 pts): High Request Cost - Request cost >$10/month declining (Confidence: 0.70)
      AWS Ref: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

    Decommission Tier Classification:
    - MUST tier: score >=80 (S1+S2+S3 present)
    - SHOULD tier: score 50-79
    - COULD tier: score 25-49
    - KEEP tier: score <25
    """

    # Tier 1: High-Confidence (60 points max)
    S1_STORAGE_LENS_INACTIVE = "S1"  # 40 pts - Storage Lens 0 requests 90d (0.95 confidence)
    S2_STORAGE_CLASS_INEFFICIENCY = "S2"  # 20 pts - STANDARD with <1 access/month (0.85 confidence)

    # Tier 2: Medium-Confidence (45 points max)
    S3_LIFECYCLE_MISSING = "S3"  # 15 pts - No lifecycle + objects >365d (0.80 confidence)
    S4_INTELLIGENT_TIERING_OFF = "S4"  # 10 pts - Bucket >10GB without IT (0.80 confidence)
    S5_VERSIONING_NO_EXPIRATION = "S5"  # 10 pts - Versioning + no expiration (0.80 confidence)
    S6_ZERO_REQUESTS_90D = "S6"  # 10 pts - CloudWatch AllRequests=0 (0.80 confidence)

    # Tier 3: Lower-Confidence (20 points max)
    S7_REPLICATION_WASTE = "S7"  # 5 pts - Replication to 0-access bucket (0.70 confidence)
    S8_PUBLIC_NO_ENCRYPTION = "S8"  # 5 pts - Public + no encryption + 0 GET (0.70 confidence)
    S9_INVENTORY_OVERHEAD = "S9"  # 5 pts - Inventory on <1GB/0-access bucket (0.70 confidence)
    S10_HIGH_REQUEST_COST = "S10"  # 5 pts - Request cost >$10/month declining (0.70 confidence)


class ActivityPattern(str, Enum):
    """S3 bucket access pattern classification."""

    ACTIVE = "active"  # Production workload (>1000 requests/day)
    MODERATE = "moderate"  # Development/staging (100-1000 requests/day)
    LIGHT = "light"  # Test environment (<100 requests/day)
    IDLE = "idle"  # No requests in 90 days


class DecommissionRecommendation(str, Enum):
    """Decommission recommendations based on activity analysis."""

    DECOMMISSION = "DECOMMISSION"  # High confidence - decommission candidate
    INVESTIGATE = "INVESTIGATE"  # Medium confidence - needs review
    OPTIMIZE = "OPTIMIZE"  # Moderate underutilization - rightsize
    KEEP = "KEEP"  # Active resource - retain


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class S3ActivityMetrics:
    """
    CloudWatch metrics for S3 bucket.

    Comprehensive activity metrics for decommission decision-making with
    S1-S7 signal framework.
    """

    total_requests_90d: int
    avg_requests_per_day: float
    get_requests_90d: int
    put_requests_90d: int
    total_objects: int
    total_size_gb: float
    versioning_enabled: bool
    lifecycle_enabled: bool
    public_access_blocked: bool
    encryption_enabled: bool
    replication_enabled: bool
    intelligent_tiering_enabled: bool
    avg_object_age_days: float = 0.0
    request_cost_monthly: float = 0.0


@dataclass
class S3ActivityAnalysis:
    """
    S3 bucket activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    S1-S7 signal framework and cost impact analysis.
    """

    bucket_name: str
    region: str
    account_id: str
    metrics: S3ActivityMetrics
    activity_pattern: ActivityPattern
    idle_signals: List[S3IdleSignal] = field(default_factory=list)
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: float = 0.0  # 0.0-1.0
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bucket_name": self.bucket_name,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "total_requests_90d": self.metrics.total_requests_90d,
                "avg_requests_per_day": self.metrics.avg_requests_per_day,
                "get_requests_90d": self.metrics.get_requests_90d,
                "put_requests_90d": self.metrics.put_requests_90d,
                "total_objects": self.metrics.total_objects,
                "total_size_gb": self.metrics.total_size_gb,
                "versioning_enabled": self.metrics.versioning_enabled,
                "lifecycle_enabled": self.metrics.lifecycle_enabled,
                "public_access_blocked": self.metrics.public_access_blocked,
                "encryption_enabled": self.metrics.encryption_enabled,
                "replication_enabled": self.metrics.replication_enabled,
                "intelligent_tiering_enabled": self.metrics.intelligent_tiering_enabled,
                "avg_object_age_days": self.metrics.avg_object_age_days,
                "request_cost_monthly": self.metrics.request_cost_monthly,
            },
            "activity_pattern": self.activity_pattern.value,
            "idle_signals": [signal.value for signal in self.idle_signals],
            "monthly_cost": self.monthly_cost,
            "annual_cost": self.annual_cost,
            "potential_savings": self.potential_savings,
            "confidence": self.confidence,
            "recommendation": self.recommendation.value,
            "metadata": self.metadata,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE ENRICHER CLASS
# ═════════════════════════════════════════════════════════════════════════════


class S3ActivityEnricher:
    """
    S3 activity enricher for inventory resources.

    Analyzes S3 buckets for idle/underutilization patterns using CloudWatch
    metrics and S3 APIs with S1-S10 signal framework (AWS Well-Architected aligned).

    Capabilities:
    - Activity metrics analysis (90 day windows)
    - Storage Lens integration for activity detection
    - Storage class optimization analysis
    - Request pattern tracking
    - Lifecycle policy evaluation
    - Public access and encryption validation
    - Comprehensive decommission recommendations

    Decommission Signals Generated (S1-S10) - AWS Well-Architected Framework Aligned:

    Tier 1: High-Confidence (60 points max)
    - S1 (40 pts): Storage Lens Inactive - 0 requests 90d (Confidence: 0.95)
    - S2 (20 pts): Storage Class Inefficiency - STANDARD with <1 access/month (Confidence: 0.85)

    Tier 2: Medium-Confidence (45 points max)
    - S3 (15 pts): Lifecycle Missing - No lifecycle + objects >365d (Confidence: 0.80)
    - S4 (10 pts): Intelligent-Tiering Off - Bucket >10GB without IT (Confidence: 0.80)
    - S5 (10 pts): Versioning No Expiration - Versioning + no expiration (Confidence: 0.80)
    - S6 (10 pts): Zero Requests 90D - CloudWatch AllRequests=0 (Confidence: 0.80)

    Tier 3: Lower-Confidence (20 points max)
    - S7 (5 pts): Replication Waste - Replication to 0-access bucket (Confidence: 0.70)
    - S8 (5 pts): Public No Encryption - Public + no encryption + 0 GET (Confidence: 0.70)
    - S9 (5 pts): Inventory Overhead - Inventory on <1GB/0-access bucket (Confidence: 0.70)
    - S10 (5 pts): High Request Cost - Request cost >$10/month declining (Confidence: 0.70)

    AWS Documentation References:
    - S1: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
    - S2: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
    - S3: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
    - S4: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
    - S5: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
    - S6: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html
    - S7: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
    - S8: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
    - S9: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
    - S10: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

    Example:
        >>> enricher = S3ActivityEnricher(
        ...     operational_profile='ops-profile',
        ...     region='ap-southeast-2'
        ... )
        >>> analyses = enricher.analyze_bucket_activity(
        ...     bucket_names=['my-bucket']
        ... )
        >>> for analysis in analyses:
        ...     if S3IdleSignal.S1_STORAGE_LENS_INACTIVE in analysis.idle_signals:
        ...         print(f"Idle bucket: {analysis.bucket_name}")
    """

    # Activity thresholds for classification
    ACTIVE_REQUESTS_THRESHOLD = 1000  # requests per day
    MODERATE_REQUESTS_THRESHOLD = 100  # requests per day

    # S3 pricing (ap-southeast-2) - placeholder, should use AWS Pricing API
    # Example: $0.025/GB-month Standard, $0.005/1000 GET requests
    DEFAULT_STORAGE_GB_MONTHLY_RATE = 0.025
    DEFAULT_GET_REQUEST_PER_1000 = 0.0005
    DEFAULT_PUT_REQUEST_PER_1000 = 0.005

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 90,
        cache_ttl: int = 300,
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize S3 activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for S3 queries (default: ap-southeast-2)
            lookback_days: CloudWatch lookback period (default: 90)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = min(lookback_days, 455)  # CloudWatch metrics retention
        self.cache_ttl = cache_ttl

        # Initialize AWS session
        self.session = create_operational_session(self.operational_profile)
        self.s3_client = self.session.client("s3", region_name=self.region)
        self.cloudwatch_client = self.session.client("cloudwatch", region_name=self.region)

        # Validation cache (5-minute TTL for performance)
        self._cache: Dict[str, Tuple[S3ActivityAnalysis, float]] = {}

        # Performance tracking
        self.query_count = 0
        self.total_execution_time = 0.0

        # Logger
        self.logger = logging.getLogger(__name__)

        # OutputController for verbose mode support
        self.output_controller = output_controller or OutputController()

        # Verbose-aware initialization logging
        if self.output_controller.verbose:
            print_info(
                f"🔍 S3 Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )
        else:
            self.logger.debug(
                f"S3 Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )

    def analyze_bucket_activity(
        self,
        bucket_names: Optional[List[str]] = None,
        region: Optional[str] = None,
        lookback_days: Optional[int] = None,
    ) -> List[S3ActivityAnalysis]:
        """
        Analyze S3 bucket activity for idle detection.

        Core analysis workflow:
        1. Query S3 buckets (all or specific names)
        2. Get CloudWatch metrics for each bucket (90 day window)
        3. Classify activity pattern (active/moderate/light/idle)
        4. Generate S1-S7 decommission signals based on patterns
        5. Compute confidence score and recommendation
        6. Calculate cost impact and potential savings

        Args:
            bucket_names: List of bucket names to analyze (analyzes all if None)
            region: AWS region filter (default: use instance region)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals

        Example:
            >>> analyses = enricher.analyze_bucket_activity(
            ...     bucket_names=['my-bucket']
            ... )
            >>> for analysis in analyses:
            ...     print(f"{analysis.bucket_name}: {analysis.recommendation.value}")
        """
        start_time = time.time()
        analysis_region = region or self.region
        lookback = lookback_days or self.lookback_days

        print_section(f"S3 Activity Analysis ({lookback}-day lookback)")

        # Get S3 buckets
        buckets = self._get_s3_buckets(bucket_names, analysis_region)

        if not buckets:
            print_warning("No S3 buckets found")
            return []

        print_info(f"Found {len(buckets)} S3 buckets")

        analyses: List[S3ActivityAnalysis] = []

        with create_progress_bar(description="Analyzing S3 buckets") as progress:
            task = progress.add_task(f"Analyzing {len(buckets)} buckets", total=len(buckets))

            for bucket in buckets:
                try:
                    # Check cache first
                    bucket_name = bucket["Name"]
                    cache_key = f"{bucket_name}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Analyze bucket
                    analysis = self._analyze_bucket(bucket, lookback)

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(f"Failed to analyze S3 bucket {bucket.get('Name')}: {e}", exc_info=True)
                    print_warning(f"⚠️  Skipped {bucket.get('Name')}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _get_s3_buckets(self, bucket_names: Optional[List[str]], region: str) -> List[Dict]:
        """
        Get S3 buckets from AWS API.

        Args:
            bucket_names: Specific buckets to retrieve (retrieves all if None)
            region: AWS region filter

        Returns:
            List of S3 bucket metadata dictionaries
        """
        buckets = []

        try:
            response = self.s3_client.list_buckets()
            all_buckets = response.get("Buckets", [])

            for bucket in all_buckets:
                bucket_name = bucket["Name"]

                # Filter by specific bucket names if provided
                if bucket_names and bucket_name not in bucket_names:
                    continue

                # Get bucket region
                try:
                    bucket_region = (
                        self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
                    )

                    # Filter by region if specified
                    if region and bucket_region != region:
                        continue

                except ClientError:
                    # Skip buckets we can't access
                    continue

                buckets.append(bucket)

        except ClientError as e:
            self.logger.error(f"Failed to list S3 buckets: {e}")

        return buckets

    def _analyze_bucket(self, bucket: Dict, lookback_days: int) -> S3ActivityAnalysis:
        """
        Analyze individual S3 bucket.

        Args:
            bucket: S3 bucket metadata from list_buckets
            lookback_days: CloudWatch metrics lookback period

        Returns:
            Comprehensive activity analysis with idle signals
        """
        bucket_name = bucket["Name"]

        # Get CloudWatch metrics
        metrics = self._get_cloudwatch_metrics(bucket, lookback_days)

        # Classify activity pattern
        activity_pattern = self._classify_activity_pattern(metrics)

        # Generate idle signals (S1-S10 framework) with confidence
        idle_signals, signal_confidence = self._generate_idle_signals(metrics, activity_pattern, bucket_name)

        # Calculate costs
        monthly_cost = self._calculate_monthly_cost(metrics)
        annual_cost = monthly_cost * 12

        # Calculate potential savings using signal-derived confidence or calculated confidence
        confidence = signal_confidence if signal_confidence > 0 else self._calculate_confidence(idle_signals)
        potential_savings = self._calculate_potential_savings(annual_cost, confidence, activity_pattern)

        # Generate recommendation
        recommendation = self._generate_recommendation(activity_pattern, idle_signals, confidence)

        # Get account ID
        try:
            sts = self.session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
        except Exception:
            account_id = "unknown"

        # Get bucket region
        try:
            bucket_region = self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        except Exception:
            bucket_region = self.region

        return S3ActivityAnalysis(
            bucket_name=bucket_name,
            region=bucket_region,
            account_id=account_id,
            metrics=metrics,
            activity_pattern=activity_pattern,
            idle_signals=idle_signals,
            monthly_cost=monthly_cost,
            annual_cost=annual_cost,
            potential_savings=potential_savings,
            confidence=confidence,
            recommendation=recommendation,
            metadata={
                "lookback_days": lookback_days,
                "query_time": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    def _get_cloudwatch_metrics(self, bucket: Dict, lookback_days: int) -> S3ActivityMetrics:
        """
        Get CloudWatch metrics for S3 bucket.

        Metrics queried:
        - NumberOfObjects (bucket size)
        - BucketSizeBytes (storage size)
        - AllRequests (total requests)

        Args:
            bucket: S3 bucket metadata
            lookback_days: Lookback period for metrics

        Returns:
            Comprehensive activity metrics
        """
        bucket_name = bucket["Name"]
        now = datetime.utcnow()

        # Query total requests
        total_requests = self._get_s3_metric_sum(bucket_name, "AllRequests", now - timedelta(days=lookback_days), now)

        # Query GET requests
        get_requests = self._get_s3_metric_sum(bucket_name, "GetRequests", now - timedelta(days=lookback_days), now)

        # Query PUT requests
        put_requests = self._get_s3_metric_sum(bucket_name, "PutRequests", now - timedelta(days=lookback_days), now)

        # Get bucket configuration
        versioning_enabled = self._check_versioning(bucket_name)
        lifecycle_enabled = self._check_lifecycle(bucket_name)
        public_access_blocked = self._check_public_access_block(bucket_name)
        encryption_enabled = self._check_encryption(bucket_name)
        replication_enabled = self._check_replication(bucket_name)
        intelligent_tiering_enabled = self._check_intelligent_tiering(bucket_name)

        # Get bucket size and object count
        total_objects, total_size_gb = self._get_bucket_size(bucket_name)

        # Calculate average object age (approximation)
        avg_object_age_days = self._estimate_object_age(bucket_name)

        # Calculate request costs
        request_cost_monthly = self._calculate_request_cost(get_requests, put_requests, lookback_days)

        avg_requests_per_day = total_requests / max(1, lookback_days)

        return S3ActivityMetrics(
            total_requests_90d=int(total_requests),
            avg_requests_per_day=avg_requests_per_day,
            get_requests_90d=int(get_requests),
            put_requests_90d=int(put_requests),
            total_objects=total_objects,
            total_size_gb=total_size_gb,
            versioning_enabled=versioning_enabled,
            lifecycle_enabled=lifecycle_enabled,
            public_access_blocked=public_access_blocked,
            encryption_enabled=encryption_enabled,
            replication_enabled=replication_enabled,
            intelligent_tiering_enabled=intelligent_tiering_enabled,
            avg_object_age_days=avg_object_age_days,
            request_cost_monthly=request_cost_monthly,
        )

    def _get_s3_metric_sum(self, bucket_name: str, metric_name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Get S3 CloudWatch metric sum.

        Args:
            bucket_name: S3 bucket name
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Metric sum value, or 0.0 if no data
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName=metric_name,
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "AllStorageTypes"},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Sum"],
            )

            datapoints = response["Datapoints"]
            if not datapoints:
                return 0.0

            # Increment query counter
            self.query_count += 1

            return sum(d["Sum"] for d in datapoints)

        except ClientError as e:
            self.logger.debug(f"CloudWatch query failed for {bucket_name}/{metric_name}: {e}")
            return 0.0

    def _check_versioning(self, bucket_name: str) -> bool:
        """Check if bucket has versioning enabled."""
        try:
            response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            return response.get("Status") == "Enabled"
        except ClientError:
            return False

    def _check_lifecycle(self, bucket_name: str) -> bool:
        """Check if bucket has lifecycle policies."""
        try:
            self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def _check_public_access_block(self, bucket_name: str) -> bool:
        """Check if bucket has public access blocked."""
        try:
            response = self.s3_client.get_public_access_block(Bucket=bucket_name)
            config = response.get("PublicAccessBlockConfiguration", {})
            return all(
                [
                    config.get("BlockPublicAcls", False),
                    config.get("IgnorePublicAcls", False),
                    config.get("BlockPublicPolicy", False),
                    config.get("RestrictPublicBuckets", False),
                ]
            )
        except ClientError:
            return False

    def _check_encryption(self, bucket_name: str) -> bool:
        """Check if bucket has default encryption."""
        try:
            self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def _check_replication(self, bucket_name: str) -> bool:
        """
        Check if bucket has replication enabled.

        S7 Signal Enhancement (v1.1.27): 100% confidence via AWS API
        Replaces name-based heuristic (75% confidence) with direct API check.

        Returns:
            True if replication configured, False otherwise
        """
        try:
            self.s3_client.get_bucket_replication(Bucket=bucket_name)
            return True
        except ClientError as e:
            # ReplicationConfigurationNotFoundError means no replication
            if e.response["Error"]["Code"] == "ReplicationConfigurationNotFoundError":
                return False
            # Other errors (AccessDenied, etc.) treated as False
            self.logger.debug(f"S7 replication check failed for {bucket_name}: {e}")
            return False

    def _check_intelligent_tiering(self, bucket_name: str) -> bool:
        """Check if bucket has Intelligent-Tiering configuration."""
        try:
            self.s3_client.list_bucket_intelligent_tiering_configurations(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def _check_storage_lens_inactive(self, bucket_name: str, total_requests_90d: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S1: Storage Lens Inactive - 0 requests in 90 days.

        S1 Signal (40 pts, Confidence: 0.95): Uses Storage Lens data if available,
        falls back to CloudWatch AllRequests metric for 90-day activity detection.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html

        Business Value: Highest-confidence idle bucket signal - Storage Lens provides
        ML-based activity insights; CloudWatch provides direct request metrics.

        Args:
            bucket_name: S3 bucket name
            total_requests_90d: Pre-computed total requests from CloudWatch (fallback)

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S1_STORAGE_LENS_INACTIVE",
            "detection_method": "cloudwatch_fallback",  # Default to CloudWatch
            "bucket_name": bucket_name,
            "total_requests_90d": total_requests_90d,
            "confidence": 0.95,
        }

        # Primary: Check Storage Lens if available (s3control API)
        try:
            # Get account ID for Storage Lens API
            sts = self.session.client("sts")
            account_id = sts.get_caller_identity()["Account"]

            # Storage Lens requires s3control client
            s3control = self.session.client("s3control", region_name=self.region)

            # List Storage Lens configurations
            lens_response = s3control.list_storage_lens_configurations(AccountId=account_id)
            configurations = lens_response.get("StorageLensConfigurationList", [])

            if configurations:
                # Storage Lens is configured - would need to query actual metrics
                # For now, note Storage Lens availability in metadata
                metadata["storage_lens_available"] = True
                metadata["storage_lens_configs"] = len(configurations)
                self.logger.debug(f"Storage Lens available for {bucket_name} with {len(configurations)} configs")
            else:
                metadata["storage_lens_available"] = False

        except ClientError as e:
            # Storage Lens not available or access denied - use CloudWatch fallback
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            metadata["storage_lens_available"] = False
            metadata["storage_lens_error"] = error_code
            self.logger.debug(f"Storage Lens unavailable for {bucket_name}: {error_code}")

        except Exception as e:
            # General error - use CloudWatch fallback
            metadata["storage_lens_available"] = False
            metadata["storage_lens_error"] = str(e)

        # Fallback: Use pre-computed CloudWatch AllRequests metric (always available)
        signal_active = total_requests_90d == 0
        metadata["signal_active"] = signal_active

        return signal_active, metadata

    def _check_storage_lens_inactive_with_cost_benefit(
        self, bucket_name: str, total_requests_90d: int, total_size_gb: float
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S1 with Storage Lens cost-benefit gate (v1.1.29 Track 2 Day 2).

        Manager's Directive: "Only enable Storage Lens if necessary for cost
        optimization from Storage Lens itself" - requires cost-benefit analysis
        before recommending Storage Lens enablement.

        Cost-Benefit Analysis:
        - Storage Lens Cost: ~$0.025/GB/month (AWS Advanced Tier pricing)
        - Estimated Savings: Storage class optimization potential (Glacier, IT, etc.)
        - Gate: Only return S1 signal if estimated_savings > storage_lens_cost

        AWS Documentation (Manager-Provided):
        1. Storage Lens Pricing:
           https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens_basics_metrics_recommendations.html#storage_lens_basics_metrics_recommendations_pricing
        2. Storage Lens Cost Optimization:
           https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens_optimize_storage.html
        3. Storage Class Analysis:
           https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html

        Business Value: Prevents recommending Storage Lens when enablement cost
        exceeds potential savings (e.g., small buckets <10GB).

        Args:
            bucket_name: S3 bucket name
            total_requests_90d: Pre-computed total requests from CloudWatch (fallback)
            total_size_gb: Bucket size in GB for cost calculation

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S1_STORAGE_LENS_INACTIVE",
            "detection_method": "cost_benefit_gated",
            "bucket_name": bucket_name,
            "total_requests_90d": total_requests_90d,
            "total_size_gb": total_size_gb,
            "confidence": 0.95,
        }

        # Calculate Storage Lens monthly cost (AWS Advanced Tier: ~$0.025/GB/month)
        storage_lens_cost_monthly = total_size_gb * self.DEFAULT_STORAGE_GB_MONTHLY_RATE
        metadata["storage_lens_cost_monthly"] = storage_lens_cost_monthly

        # Estimate potential savings from storage class optimization
        # Assumptions:
        # - Bucket is idle (0 requests 90d) → candidate for Glacier/DeepArchive
        # - Standard storage: $0.025/GB-month
        # - Glacier Flexible: $0.0045/GB-month (82% savings)
        # - Deep Archive: $0.00099/GB-month (96% savings)
        # Conservative estimate: Use Glacier Flexible (82% savings)
        if total_requests_90d == 0:
            # Idle bucket → Glacier optimization potential
            standard_cost_monthly = total_size_gb * 0.025
            glacier_cost_monthly = total_size_gb * 0.0045
            estimated_savings_monthly = standard_cost_monthly - glacier_cost_monthly
            metadata["optimization_strategy"] = "glacier_flexible"
        else:
            # Some activity → Intelligent-Tiering optimization potential (40-90% savings)
            # Conservative estimate: 40% savings
            estimated_savings_monthly = (total_size_gb * 0.025) * 0.40
            metadata["optimization_strategy"] = "intelligent_tiering"

        metadata["estimated_savings_monthly"] = estimated_savings_monthly

        # Cost-benefit gate: Only recommend Storage Lens if savings > cost
        cost_benefit_positive = estimated_savings_monthly > storage_lens_cost_monthly
        metadata["cost_benefit_positive"] = cost_benefit_positive
        metadata["cost_benefit_ratio"] = (
            estimated_savings_monthly / storage_lens_cost_monthly if storage_lens_cost_monthly > 0 else 0.0
        )

        if not cost_benefit_positive:
            # Skip S1 signal - Storage Lens cost exceeds potential savings
            metadata["signal_active"] = False
            metadata["skip_reason"] = (
                f"storage_lens_cost (${storage_lens_cost_monthly:.2f}/month) "
                f"> estimated_savings (${estimated_savings_monthly:.2f}/month)"
            )
            return False, metadata

        # Cost-benefit positive → Proceed with Storage Lens check
        signal_active, lens_metadata = self._check_storage_lens_inactive(
            bucket_name=bucket_name, total_requests_90d=total_requests_90d
        )

        # Merge metadata
        metadata.update(lens_metadata)
        metadata["cost_benefit_gated"] = True

        return signal_active, metadata

    def _check_storage_class_inefficiency(
        self, bucket_name: str, total_size_gb: float, get_requests_90d: int, lookback_days: int = 90
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S2: Storage Class Inefficiency - STANDARD class with <1 access/month.

        S2 Signal (20 pts, Confidence: 0.85): Detects buckets using STANDARD storage
        class with very low access frequency that should be transitioned to IA or Glacier.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html

        Business Value: STANDARD ($0.025/GB) vs IA ($0.0125/GB) = 50% savings
                       STANDARD ($0.025/GB) vs Glacier ($0.005/GB) = 80% savings

        Args:
            bucket_name: S3 bucket name
            total_size_gb: Total bucket size in GB
            get_requests_90d: Total GET requests in 90 days
            lookback_days: Lookback period (default: 90 days)

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S2_STORAGE_CLASS_INEFFICIENCY",
            "bucket_name": bucket_name,
            "total_size_gb": total_size_gb,
            "get_requests_90d": get_requests_90d,
            "lookback_days": lookback_days,
            "confidence": 0.85,
        }

        # Calculate monthly access rate
        months_in_period = lookback_days / 30
        monthly_gets = get_requests_90d / months_in_period if months_in_period > 0 else 0
        metadata["monthly_get_requests"] = monthly_gets

        # Check storage class distribution (primary method)
        try:
            # Try to get analytics configuration for storage class analysis
            analytics_configs = self.s3_client.list_bucket_analytics_configurations(Bucket=bucket_name)
            metadata["has_analytics"] = "AnalyticsConfigurationList" in analytics_configs
        except ClientError:
            metadata["has_analytics"] = False

        # Signal active if: bucket uses STANDARD class (default) + <1 GET/month
        # AND bucket has meaningful size (>100MB to avoid noise)
        signal_active = (
            monthly_gets < 1.0 and total_size_gb > 0.1  # >100MB threshold
        )

        # Calculate potential savings
        if signal_active:
            # STANDARD → IA savings (50%)
            ia_savings = total_size_gb * 0.025 * 0.5 * 12  # Annual
            # STANDARD → Glacier savings (80%)
            glacier_savings = total_size_gb * 0.025 * 0.8 * 12  # Annual
            metadata["potential_ia_savings_annual"] = ia_savings
            metadata["potential_glacier_savings_annual"] = glacier_savings
            metadata["recommended_class"] = "GLACIER" if monthly_gets == 0 else "STANDARD_IA"

        metadata["signal_active"] = signal_active
        return signal_active, metadata

    def _check_storage_inventory_overhead(
        self, bucket_name: str, total_size_gb: float, total_requests_90d: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S9: Inventory Overhead - Inventory on <1GB or 0-access bucket.

        S9 Signal (5 pts, Confidence: 0.70): Detects over-engineered inventory
        configurations on small or inactive buckets where inventory cost exceeds value.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html

        Business Value: S3 Inventory costs $0.0025 per million objects listed.
        For small/inactive buckets, this overhead provides minimal value.

        Args:
            bucket_name: S3 bucket name
            total_size_gb: Total bucket size in GB
            total_requests_90d: Total requests in 90 days

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S9_INVENTORY_OVERHEAD",
            "bucket_name": bucket_name,
            "total_size_gb": total_size_gb,
            "total_requests_90d": total_requests_90d,
            "confidence": 0.70,
        }

        # Check if inventory is configured
        inventory_configured = False
        inventory_count = 0

        try:
            response = self.s3_client.list_bucket_inventory_configurations(Bucket=bucket_name)
            inventory_list = response.get("InventoryConfigurationList", [])
            inventory_configured = len(inventory_list) > 0
            inventory_count = len(inventory_list)

            metadata["inventory_configured"] = inventory_configured
            metadata["inventory_count"] = inventory_count

            if inventory_configured:
                # Extract inventory details
                metadata["inventory_destinations"] = [
                    inv.get("Destination", {}).get("S3BucketDestination", {}).get("Bucket", "unknown")
                    for inv in inventory_list
                ]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            metadata["inventory_configured"] = False
            metadata["inventory_error"] = error_code
            self.logger.debug(f"Inventory check failed for {bucket_name}: {error_code}")

        # Signal active if: inventory configured on small bucket (<1GB) OR idle bucket
        signal_active = inventory_configured and (
            total_size_gb < 1.0  # Small bucket (inventory overhead > value)
            or total_requests_90d == 0  # Idle bucket (no activity to analyze)
        )

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "inventory_on_small_bucket"
            if total_size_gb < 1.0
            else "inventory_on_idle_bucket"
            if total_requests_90d == 0
            else "inventory_appropriate"
        )

        return signal_active, metadata

    def _check_lifecycle_missing(self, bucket_name: str, avg_object_age_days: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S3: Lifecycle Missing - No lifecycle policy + objects >365 days old.

        S3 Signal (15 pts, Confidence: 0.80): Detects buckets without lifecycle
        policies that have old objects, indicating potential storage optimization.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html

        Business Value: Lifecycle policies automate storage class transitions
        and object expiration, reducing manual intervention and storage costs.

        Args:
            bucket_name: S3 bucket name
            avg_object_age_days: Average age of objects in days

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S3_LIFECYCLE_MISSING",
            "bucket_name": bucket_name,
            "avg_object_age_days": avg_object_age_days,
            "confidence": 0.80,
        }

        lifecycle_enabled = False
        lifecycle_rules_count = 0

        try:
            response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            rules = response.get("Rules", [])
            lifecycle_enabled = len(rules) > 0
            lifecycle_rules_count = len(rules)

            metadata["lifecycle_enabled"] = lifecycle_enabled
            metadata["lifecycle_rules_count"] = lifecycle_rules_count

            # Extract rule summaries
            if rules:
                metadata["lifecycle_rules"] = [
                    {
                        "id": rule.get("ID", "Unknown"),
                        "status": rule.get("Status", "Unknown"),
                        "has_transitions": "Transitions" in rule,
                        "has_expiration": "Expiration" in rule,
                    }
                    for rule in rules[:5]  # Limit to first 5 rules
                ]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "NoSuchLifecycleConfiguration":
                metadata["lifecycle_enabled"] = False
                metadata["lifecycle_rules_count"] = 0
            else:
                metadata["lifecycle_error"] = error_code
                self.logger.debug(f"Lifecycle check failed for {bucket_name}: {error_code}")

        # Signal active if: no lifecycle AND old objects (>365 days)
        signal_active = not lifecycle_enabled and avg_object_age_days > 365

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "no_lifecycle_old_objects"
            if signal_active
            else "lifecycle_configured"
            if lifecycle_enabled
            else "objects_not_old_enough"
        )

        return signal_active, metadata

    def _check_intelligent_tiering_off(self, bucket_name: str, total_size_gb: float) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S4: Intelligent-Tiering Off - Bucket >10GB without IT configuration.

        S4 Signal (10 pts, Confidence: 0.80): Detects large buckets without
        Intelligent-Tiering, which can automatically optimize storage costs
        for data with unpredictable access patterns.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html

        Business Value: S3 Intelligent-Tiering moves objects between access tiers
        based on access patterns, providing 40-90% cost savings with no retrieval fees.

        Args:
            bucket_name: S3 bucket name
            total_size_gb: Total bucket size in GB

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S4_INTELLIGENT_TIERING_OFF",
            "bucket_name": bucket_name,
            "total_size_gb": total_size_gb,
            "confidence": 0.80,
            "threshold_gb": 10.0,  # Minimum size for IT recommendation
        }

        intelligent_tiering_enabled = False
        it_config_count = 0

        try:
            response = self.s3_client.list_bucket_intelligent_tiering_configurations(Bucket=bucket_name)
            configs = response.get("IntelligentTieringConfigurationList", [])
            intelligent_tiering_enabled = len(configs) > 0
            it_config_count = len(configs)

            metadata["intelligent_tiering_enabled"] = intelligent_tiering_enabled
            metadata["it_config_count"] = it_config_count

            if configs:
                metadata["it_configurations"] = [
                    {
                        "id": config.get("Id", "Unknown"),
                        "status": config.get("Status", "Unknown"),
                        "tierings": [
                            {"days": tier.get("Days", 0), "access_tier": tier.get("AccessTier", "Unknown")}
                            for tier in config.get("Tierings", [])
                        ],
                    }
                    for config in configs[:3]  # Limit to first 3 configs
                ]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            metadata["intelligent_tiering_enabled"] = False
            metadata["it_error"] = error_code
            self.logger.debug(f"Intelligent-Tiering check failed for {bucket_name}: {error_code}")

        # Signal active if: no IT AND bucket >10GB (meaningful size for IT benefit)
        signal_active = not intelligent_tiering_enabled and total_size_gb > 10.0

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "no_intelligent_tiering_large_bucket"
            if signal_active
            else "intelligent_tiering_configured"
            if intelligent_tiering_enabled
            else "bucket_too_small_for_it"
        )

        # Calculate potential savings estimate
        if signal_active:
            # Estimate: IT can save 40-90% on infrequently accessed data
            # Conservative estimate: 30% of bucket data is infrequently accessed
            estimated_ia_data_gb = total_size_gb * 0.30
            # Standard: $0.025/GB, IT Infrequent: $0.0125/GB = 50% savings
            estimated_monthly_savings = estimated_ia_data_gb * (0.025 - 0.0125)
            metadata["estimated_monthly_savings"] = estimated_monthly_savings
            metadata["estimated_annual_savings"] = estimated_monthly_savings * 12

        return signal_active, metadata

    def _check_versioning_no_expiration(
        self, bucket_name: str, versioning_enabled: bool, lifecycle_enabled: bool
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S5: Versioning No Expiration - Versioning enabled without expiration.

        S5 Signal (10 pts, Confidence: 0.80): Detects buckets with versioning
        enabled but no lifecycle policy to expire old versions, leading to
        unbounded storage growth.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html

        Business Value: Without noncurrent version expiration, versioned buckets
        accumulate old versions indefinitely, increasing storage costs linearly.

        Args:
            bucket_name: S3 bucket name
            versioning_enabled: Whether versioning is enabled
            lifecycle_enabled: Whether lifecycle policy exists

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S5_VERSIONING_NO_EXPIRATION",
            "bucket_name": bucket_name,
            "versioning_enabled": versioning_enabled,
            "lifecycle_enabled": lifecycle_enabled,
            "confidence": 0.80,
        }

        has_noncurrent_expiration = False

        # If lifecycle is enabled, check for noncurrent version expiration
        if lifecycle_enabled:
            try:
                response = self.s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                rules = response.get("Rules", [])

                for rule in rules:
                    if rule.get("Status") == "Enabled":
                        # Check for NoncurrentVersionExpiration
                        if "NoncurrentVersionExpiration" in rule:
                            has_noncurrent_expiration = True
                            metadata["noncurrent_expiration_days"] = rule["NoncurrentVersionExpiration"].get(
                                "NoncurrentDays", 0
                            )
                            break
                        # Check for NoncurrentVersionTransitions (also acceptable)
                        if "NoncurrentVersionTransitions" in rule:
                            has_noncurrent_expiration = True
                            break

                metadata["has_noncurrent_expiration"] = has_noncurrent_expiration

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                metadata["lifecycle_error"] = error_code
                self.logger.debug(f"Lifecycle version check failed for {bucket_name}: {error_code}")

        # Signal active if: versioning enabled AND no noncurrent version management
        signal_active = versioning_enabled and not has_noncurrent_expiration

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "versioning_without_expiration"
            if signal_active
            else "versioning_disabled"
            if not versioning_enabled
            else "noncurrent_expiration_configured"
        )

        return signal_active, metadata

    def _check_zero_requests_90d(self, bucket_name: str, total_requests_90d: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S6: Zero Requests 90D - CloudWatch AllRequests metric = 0.

        S6 Signal (10 pts, Confidence: 0.80): Uses CloudWatch metrics to detect
        buckets with zero requests over 90 days, indicating no API activity.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

        Business Value: Buckets with zero requests are strong decommission
        candidates. This signal provides CloudWatch-based idle detection.

        Args:
            bucket_name: S3 bucket name
            total_requests_90d: Total AllRequests metric sum over 90 days

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S6_ZERO_REQUESTS_90D",
            "bucket_name": bucket_name,
            "total_requests_90d": total_requests_90d,
            "confidence": 0.80,
            "detection_method": "cloudwatch_all_requests",
        }

        # Signal active if: zero requests in 90 days
        signal_active = total_requests_90d == 0

        metadata["signal_active"] = signal_active
        metadata["reason"] = "zero_requests_detected" if signal_active else f"has_requests_{total_requests_90d}"

        return signal_active, metadata

    def _check_replication_waste(
        self, bucket_name: str, total_requests_90d: int, activity_pattern: "ActivityPattern"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S7: Replication Waste - Replication to 0-access bucket.

        S7 Signal (5 pts, Confidence: 0.70): Detects buckets with cross-region
        replication enabled but low/no access, indicating wasted replication costs.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html

        Business Value: S3 replication incurs costs for storage in destination
        region plus data transfer. If source bucket is idle, replication is waste.

        Args:
            bucket_name: S3 bucket name
            total_requests_90d: Total requests in 90 days
            activity_pattern: Activity pattern classification

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S7_REPLICATION_WASTE",
            "bucket_name": bucket_name,
            "total_requests_90d": total_requests_90d,
            "activity_pattern": activity_pattern.value if hasattr(activity_pattern, "value") else str(activity_pattern),
            "confidence": 0.70,
        }

        replication_enabled = False
        replication_rules_count = 0

        try:
            response = self.s3_client.get_bucket_replication(Bucket=bucket_name)
            replication_config = response.get("ReplicationConfiguration", {})
            rules = replication_config.get("Rules", [])
            replication_enabled = len(rules) > 0
            replication_rules_count = len(rules)

            metadata["replication_enabled"] = replication_enabled
            metadata["replication_rules_count"] = replication_rules_count

            if rules:
                metadata["replication_rules"] = [
                    {
                        "id": rule.get("ID", "Unknown"),
                        "status": rule.get("Status", "Unknown"),
                        "destination_bucket": rule.get("Destination", {}).get("Bucket", "Unknown"),
                    }
                    for rule in rules[:3]  # Limit to first 3 rules
                ]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "ReplicationConfigurationNotFoundError":
                metadata["replication_enabled"] = False
                metadata["replication_rules_count"] = 0
            else:
                metadata["replication_error"] = error_code
                self.logger.debug(f"Replication check failed for {bucket_name}: {error_code}")

        # Signal active if: replication enabled AND (idle OR light activity)
        signal_active = replication_enabled and activity_pattern in [ActivityPattern.IDLE, ActivityPattern.LIGHT]

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "replication_on_idle_bucket"
            if signal_active
            else "no_replication"
            if not replication_enabled
            else "replication_on_active_bucket"
        )

        return signal_active, metadata

    def _check_public_no_encryption(
        self, bucket_name: str, public_access_blocked: bool, encryption_enabled: bool, get_requests_90d: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S8: Public No Encryption - Public + no encryption + 0 GET requests.

        S8 Signal (5 pts, Confidence: 0.70): Detects publicly accessible buckets
        without encryption that have zero GET requests, indicating potential
        security risk with no usage.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html

        Business Value: Public buckets without encryption and no usage are
        security risks that should be reviewed for decommissioning.

        Args:
            bucket_name: S3 bucket name
            public_access_blocked: Whether public access is blocked
            encryption_enabled: Whether default encryption is enabled
            get_requests_90d: Total GET requests in 90 days

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S8_PUBLIC_NO_ENCRYPTION",
            "bucket_name": bucket_name,
            "public_access_blocked": public_access_blocked,
            "encryption_enabled": encryption_enabled,
            "get_requests_90d": get_requests_90d,
            "confidence": 0.70,
        }

        # Signal active if: NOT blocked public access AND NOT encrypted AND zero GET
        signal_active = not public_access_blocked and not encryption_enabled and get_requests_90d == 0

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "public_unencrypted_unused"
            if signal_active
            else "access_blocked"
            if public_access_blocked
            else "encrypted"
            if encryption_enabled
            else "has_get_requests"
        )

        return signal_active, metadata

    def _check_high_request_cost(
        self, bucket_name: str, request_cost_monthly: float, activity_pattern: "ActivityPattern"
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check S10: High Request Cost - Request cost >$10/month on declining bucket.

        S10 Signal (5 pts, Confidence: 0.70): Detects buckets with high request
        costs but declining or light activity, indicating potential waste.

        AWS Documentation:
        https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

        Business Value: High request costs on buckets with declining activity
        suggest optimization opportunities (caching, CDN, or decommissioning).

        Args:
            bucket_name: S3 bucket name
            request_cost_monthly: Estimated monthly request cost
            activity_pattern: Activity pattern classification

        Returns:
            Tuple of (signal_active: bool, metadata: dict with detection details)
        """
        metadata = {
            "signal": "S10_HIGH_REQUEST_COST",
            "bucket_name": bucket_name,
            "request_cost_monthly": request_cost_monthly,
            "activity_pattern": activity_pattern.value if hasattr(activity_pattern, "value") else str(activity_pattern),
            "confidence": 0.70,
            "threshold_monthly": 10.0,  # $10/month threshold
        }

        # Signal active if: high request cost AND (light OR moderate activity)
        # Business logic: Active buckets justify request costs, declining don't
        signal_active = request_cost_monthly > 10.0 and activity_pattern in [
            ActivityPattern.LIGHT,
            ActivityPattern.MODERATE,
        ]

        metadata["signal_active"] = signal_active
        metadata["reason"] = (
            "high_request_cost_declining_activity"
            if signal_active
            else "request_cost_acceptable"
            if request_cost_monthly <= 10.0
            else "high_request_cost_justified_by_activity"
        )

        return signal_active, metadata

    def _get_bucket_size(self, bucket_name: str) -> Tuple[int, float]:
        """
        Get bucket object count and size.

        Args:
            bucket_name: S3 bucket name

        Returns:
            Tuple of (object_count, size_gb)
        """
        try:
            # Query CloudWatch for bucket metrics
            # v1.1.29: Extended lookback to 7 days to ensure datapoints are available
            # S3 CloudWatch metrics are published once per day; 24-hour window often misses data
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)

            # Get number of objects
            objects_response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="NumberOfObjects",
                Dimensions=[
                    {"Name": "BucketName", "Value": bucket_name},
                    {"Name": "StorageType", "Value": "AllStorageTypes"},
                ],
                StartTime=seven_days_ago,
                EndTime=now,
                Period=86400,
                Statistics=["Average"],
            )

            objects_datapoints = objects_response["Datapoints"]
            # v1.1.29: Sort by timestamp descending and use most recent datapoint
            if objects_datapoints:
                objects_datapoints.sort(key=lambda x: x["Timestamp"], reverse=True)
                object_count = int(objects_datapoints[0].get("Average", 0))
            else:
                object_count = 0

            # Get bucket size - Query ALL 13 storage types (v1.1.29 bug fix)
            # Fix: Hardcoded 'StandardStorage' caused 43.2 TB of Glacier/DeepArchive data to show 0 GB
            # Pattern adopted from s3_storage_class_analyzer.py lines 258-279
            storage_types = [
                "StandardStorage",
                "StandardIAStorage",
                "OneZoneIAStorage",
                "IntelligentTieringFAStorage",
                "IntelligentTieringIAStorage",
                "IntelligentTieringAAStorage",
                "IntelligentTieringAIAStorage",
                "IntelligentTieringDAAStorage",
                "GlacierInstantRetrievalStorage",
                "GlacierStorage",
                "GlacierS3GlacierStorage",  # Legacy Glacier
                "DeepArchiveStorage",
                "ReducedRedundancyStorage",
            ]

            total_size_bytes = 0.0
            for storage_type in storage_types:
                try:
                    size_response = self.cloudwatch_client.get_metric_statistics(
                        Namespace="AWS/S3",
                        MetricName="BucketSizeBytes",
                        Dimensions=[
                            {"Name": "BucketName", "Value": bucket_name},
                            {"Name": "StorageType", "Value": storage_type},
                        ],
                        StartTime=seven_days_ago,  # v1.1.29: Use 7-day lookback
                        EndTime=now,
                        Period=86400,
                        Statistics=["Average"],
                    )

                    size_datapoints = size_response["Datapoints"]
                    # v1.1.29: Sort by timestamp and use most recent datapoint
                    if size_datapoints:
                        size_datapoints.sort(key=lambda x: x["Timestamp"], reverse=True)
                        total_size_bytes += size_datapoints[0].get("Average", 0)

                except ClientError:
                    # Graceful degradation if specific storage type unavailable
                    continue

            size_gb = total_size_bytes / (1024**3)

            # v1.1.27: Full pagination for accurate object counts (user requested - Track 2)
            # CloudWatch metrics can be stale (24-48hr lag); use direct API for accurate counts
            if object_count == 0:
                try:
                    # Full pagination: Get actual object count (handles large buckets)
                    paginator = self.s3_client.get_paginator("list_objects_v2")
                    page_iterator = paginator.paginate(
                        Bucket=bucket_name,
                        PaginationConfig={"MaxItems": 1000000},  # Reasonable limit for decommission detection
                    )

                    # Sum KeyCount across all pages (more efficient than counting Contents)
                    total_count = sum(page.get("KeyCount", 0) for page in page_iterator)
                    object_count = total_count  # Actual count from pagination

                except ClientError as e:
                    # Access denied or bucket doesn't exist - keep CloudWatch value (0)
                    # Common for encrypted buckets without KMS permissions
                    pass

            return object_count, size_gb

        except ClientError:
            return 0, 0.0

    def _estimate_object_age(self, bucket_name: str) -> float:
        """
        Estimate average object age (days since creation).

        Args:
            bucket_name: S3 bucket name

        Returns:
            Average object age in days
        """
        # Simplified estimation: use bucket creation date as proxy
        # In production, would sample objects for accurate age
        try:
            response = self.s3_client.list_buckets()
            for bucket in response["Buckets"]:
                if bucket["Name"] == bucket_name:
                    creation_date = bucket["CreationDate"]
                    age_days = (datetime.now(tz=timezone.utc) - creation_date).days
                    return float(age_days)
        except Exception:
            pass

        return 0.0

    def _calculate_request_cost(self, get_requests: float, put_requests: float, lookback_days: int) -> float:
        """
        Calculate monthly request costs.

        Args:
            get_requests: Total GET requests in period
            put_requests: Total PUT requests in period
            lookback_days: Lookback period

        Returns:
            Estimated monthly request cost
        """
        # Extrapolate to monthly
        days_per_month = 30
        monthly_gets = (get_requests / lookback_days) * days_per_month
        monthly_puts = (put_requests / lookback_days) * days_per_month

        # Calculate costs
        get_cost = (monthly_gets / 1000) * self.DEFAULT_GET_REQUEST_PER_1000
        put_cost = (monthly_puts / 1000) * self.DEFAULT_PUT_REQUEST_PER_1000

        return get_cost + put_cost

    def _classify_activity_pattern(self, metrics: S3ActivityMetrics) -> ActivityPattern:
        """
        Classify S3 activity pattern.

        Classification:
        - ACTIVE: >1000 requests/day (production)
        - MODERATE: 100-1000 requests/day (dev/staging)
        - LIGHT: <100 requests/day (test)
        - IDLE: 0 requests in 90 days

        Args:
            metrics: S3 activity metrics

        Returns:
            ActivityPattern enum
        """
        avg_requests = metrics.avg_requests_per_day

        if avg_requests >= self.ACTIVE_REQUESTS_THRESHOLD:
            return ActivityPattern.ACTIVE
        elif avg_requests >= self.MODERATE_REQUESTS_THRESHOLD:
            return ActivityPattern.MODERATE
        elif avg_requests > 0:
            return ActivityPattern.LIGHT
        else:
            return ActivityPattern.IDLE

    def _generate_idle_signals(
        self, metrics: S3ActivityMetrics, pattern: ActivityPattern, bucket_name: str = ""
    ) -> Tuple[List[S3IdleSignal], float]:
        """
        Generate S1-S10 idle signals - AWS Well-Architected Framework Aligned.

        Signal Framework v2.0: Hybrid 0-100 scoring with tier-based confidence levels.
        Total Maximum Points: 125 (normalized to 0-100 scale)

        Tier 1: High-Confidence (60 points max)
        - S1 (40 pts): Storage Lens Inactive - 0 requests 90d (Confidence: 0.95)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
        - S2 (20 pts): Storage Class Inefficiency - STANDARD with <1 access/month (Confidence: 0.85)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html

        Tier 2: Medium-Confidence (45 points max)
        - S3 (15 pts): Lifecycle Missing - No lifecycle + objects >365d (Confidence: 0.80)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
        - S4 (10 pts): Intelligent-Tiering Off - Bucket >10GB without IT (Confidence: 0.80)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
        - S5 (10 pts): Versioning No Expiration - Versioning + no expiration (Confidence: 0.80)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
        - S6 (10 pts): Zero Requests 90D - CloudWatch AllRequests=0 (Confidence: 0.80)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

        Tier 3: Lower-Confidence (20 points max)
        - S7 (5 pts): Replication Waste - Replication to 0-access bucket (Confidence: 0.70)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
        - S8 (5 pts): Public No Encryption - Public + no encryption + 0 GET (Confidence: 0.70)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
        - S9 (5 pts): Inventory Overhead - Inventory on <1GB/0-access bucket (Confidence: 0.70)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
        - S10 (5 pts): High Request Cost - Request cost >$10/month declining (Confidence: 0.70)
          AWS Docs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

        Args:
            metrics: S3 activity metrics
            pattern: Activity pattern classification
            bucket_name: S3 bucket name (for API-based signal checks)

        Returns:
            Tuple[List[S3IdleSignal], float]: (signals, overall_confidence)
        """
        signals: List[S3IdleSignal] = []
        confidence_scores: List[float] = []

        # ═══════════════════════════════════════════════════════════════════════
        # TIER 1: HIGH-CONFIDENCE SIGNALS (60 points max)
        # ═══════════════════════════════════════════════════════════════════════

        # S1: Storage Lens Inactive - 0 requests 90d (40 pts → 20 pts v1.1.29, Confidence: 0.95)
        # AWS API: s3control.list_storage_lens_configurations + CloudWatch fallback
        # v1.1.29 Track 2 Day 2: Added cost-benefit gate (Manager's directive)
        try:
            s1_active, s1_metadata = self._check_storage_lens_inactive_with_cost_benefit(
                bucket_name=bucket_name,
                total_requests_90d=metrics.total_requests_90d,
                total_size_gb=metrics.total_size_gb,
            )
            if s1_active:
                signals.append(S3IdleSignal.S1_STORAGE_LENS_INACTIVE)
                confidence_scores.append(0.95)
        except Exception as e:
            # Fallback: Use CloudWatch AllRequests metric directly
            if metrics.total_requests_90d == 0:
                signals.append(S3IdleSignal.S1_STORAGE_LENS_INACTIVE)
                confidence_scores.append(0.95)
            self.logger.debug(f"S1 Storage Lens check (cost-benefit gated) failed for {bucket_name}: {e}")

        # S2: Storage Class Inefficiency - STANDARD with <1 access/month (20 pts, Confidence: 0.85)
        # AWS API: s3.list_bucket_analytics_configurations + CloudWatch GET metrics
        try:
            s2_active, s2_metadata = self._check_storage_class_inefficiency(
                bucket_name=bucket_name, total_size_gb=metrics.total_size_gb, get_requests_90d=metrics.get_requests_90d
            )
            if s2_active:
                signals.append(S3IdleSignal.S2_STORAGE_CLASS_INEFFICIENCY)
                confidence_scores.append(0.85)
        except Exception as e:
            self.logger.debug(f"S2 Storage Class check failed for {bucket_name}: {e}")

        # ═══════════════════════════════════════════════════════════════════════
        # TIER 2: MEDIUM-CONFIDENCE SIGNALS (45 points max)
        # ═══════════════════════════════════════════════════════════════════════

        # S3: Lifecycle Missing - No lifecycle + objects >365d (15 pts, Confidence: 0.80)
        # AWS API: GetBucketLifecycleConfiguration
        try:
            s3_active, s3_metadata = self._check_lifecycle_missing(
                bucket_name=bucket_name, avg_object_age_days=metrics.avg_object_age_days
            )
            if s3_active:
                signals.append(S3IdleSignal.S3_LIFECYCLE_MISSING)
                confidence_scores.append(0.80)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if metrics.avg_object_age_days > 365 and not metrics.lifecycle_enabled:
                signals.append(S3IdleSignal.S3_LIFECYCLE_MISSING)
                confidence_scores.append(0.80)
            self.logger.debug(f"S3 Lifecycle check failed for {bucket_name}: {e}")

        # S4: Intelligent-Tiering Off - Bucket >10GB without IT (10 pts, Confidence: 0.80)
        # AWS API: ListBucketIntelligentTieringConfigurations
        try:
            s4_active, s4_metadata = self._check_intelligent_tiering_off(
                bucket_name=bucket_name, total_size_gb=metrics.total_size_gb
            )
            if s4_active:
                signals.append(S3IdleSignal.S4_INTELLIGENT_TIERING_OFF)
                confidence_scores.append(0.80)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if not metrics.intelligent_tiering_enabled and metrics.total_size_gb > 10:
                signals.append(S3IdleSignal.S4_INTELLIGENT_TIERING_OFF)
                confidence_scores.append(0.80)
            self.logger.debug(f"S4 Intelligent-Tiering check failed for {bucket_name}: {e}")

        # S5: Versioning No Expiration - Versioning + no lifecycle (10 pts, Confidence: 0.80)
        # AWS API: GetBucketVersioning + GetBucketLifecycleConfiguration
        try:
            s5_active, s5_metadata = self._check_versioning_no_expiration(
                bucket_name=bucket_name,
                versioning_enabled=metrics.versioning_enabled,
                lifecycle_enabled=metrics.lifecycle_enabled,
            )
            if s5_active:
                signals.append(S3IdleSignal.S5_VERSIONING_NO_EXPIRATION)
                confidence_scores.append(0.80)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if metrics.versioning_enabled and not metrics.lifecycle_enabled:
                signals.append(S3IdleSignal.S5_VERSIONING_NO_EXPIRATION)
                confidence_scores.append(0.80)
            self.logger.debug(f"S5 Versioning check failed for {bucket_name}: {e}")

        # S6: Zero Requests 90D - CloudWatch AllRequests=0 (10 pts, Confidence: 0.80)
        # AWS API: CloudWatch GetMetricStatistics AllRequests metric
        # Note: Only add S6 if S1 is NOT present (avoid double-counting idle)
        try:
            s6_active, s6_metadata = self._check_zero_requests_90d(
                bucket_name=bucket_name, total_requests_90d=metrics.total_requests_90d
            )
            if s6_active and S3IdleSignal.S1_STORAGE_LENS_INACTIVE not in signals:
                signals.append(S3IdleSignal.S6_ZERO_REQUESTS_90D)
                confidence_scores.append(0.80)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if metrics.total_requests_90d == 0 and S3IdleSignal.S1_STORAGE_LENS_INACTIVE not in signals:
                signals.append(S3IdleSignal.S6_ZERO_REQUESTS_90D)
                confidence_scores.append(0.80)
            self.logger.debug(f"S6 Zero Requests check failed for {bucket_name}: {e}")

        # ═══════════════════════════════════════════════════════════════════════
        # TIER 3: LOWER-CONFIDENCE SIGNALS (20 points max)
        # ═══════════════════════════════════════════════════════════════════════

        # S7: Replication Waste - Replication to 0-access bucket (5 pts, Confidence: 0.70)
        # AWS API: GetBucketReplication
        try:
            s7_active, s7_metadata = self._check_replication_waste(
                bucket_name=bucket_name, total_requests_90d=metrics.total_requests_90d, activity_pattern=pattern
            )
            if s7_active:
                signals.append(S3IdleSignal.S7_REPLICATION_WASTE)
                confidence_scores.append(0.70)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if metrics.replication_enabled and pattern in [ActivityPattern.IDLE, ActivityPattern.LIGHT]:
                signals.append(S3IdleSignal.S7_REPLICATION_WASTE)
                confidence_scores.append(0.70)
            self.logger.debug(f"S7 Replication check failed for {bucket_name}: {e}")

        # S8: Public No Encryption - Public + no encryption + 0 GET (5 pts, Confidence: 0.70)
        # AWS API: GetPublicAccessBlock + GetBucketEncryption + CloudWatch GET metrics
        try:
            s8_active, s8_metadata = self._check_public_no_encryption(
                bucket_name=bucket_name,
                public_access_blocked=metrics.public_access_blocked,
                encryption_enabled=metrics.encryption_enabled,
                get_requests_90d=metrics.get_requests_90d,
            )
            if s8_active:
                signals.append(S3IdleSignal.S8_PUBLIC_NO_ENCRYPTION)
                confidence_scores.append(0.70)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if not metrics.public_access_blocked and not metrics.encryption_enabled:
                if metrics.get_requests_90d == 0:  # Only flag if truly unused
                    signals.append(S3IdleSignal.S8_PUBLIC_NO_ENCRYPTION)
                    confidence_scores.append(0.70)
            self.logger.debug(f"S8 Public No Encryption check failed for {bucket_name}: {e}")

        # S9: Inventory Overhead - Inventory on <1GB/0-access bucket (5 pts, Confidence: 0.70)
        # AWS API: ListBucketInventoryConfigurations
        try:
            s9_active, s9_metadata = self._check_storage_inventory_overhead(
                bucket_name=bucket_name,
                total_size_gb=metrics.total_size_gb,
                total_requests_90d=metrics.total_requests_90d,
            )
            if s9_active:
                signals.append(S3IdleSignal.S9_INVENTORY_OVERHEAD)
                confidence_scores.append(0.70)
        except Exception as e:
            self.logger.debug(f"S9 Inventory check failed for {bucket_name}: {e}")

        # S10: High Request Cost - Request cost >$10/month declining (5 pts, Confidence: 0.70)
        # AWS API: CloudWatch GetRequests/PutRequests metrics
        try:
            s10_active, s10_metadata = self._check_high_request_cost(
                bucket_name=bucket_name, request_cost_monthly=metrics.request_cost_monthly, activity_pattern=pattern
            )
            if s10_active:
                signals.append(S3IdleSignal.S10_HIGH_REQUEST_COST)
                confidence_scores.append(0.70)
        except Exception as e:
            # Fallback: Use pre-computed metrics
            if metrics.request_cost_monthly > 10 and pattern in [ActivityPattern.LIGHT, ActivityPattern.MODERATE]:
                signals.append(S3IdleSignal.S10_HIGH_REQUEST_COST)
                confidence_scores.append(0.70)
            self.logger.debug(f"S10 High Request Cost check failed for {bucket_name}: {e}")

        # Calculate overall confidence: max(signal_confidences) OR 0.0 if no signals
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0

        return signals, overall_confidence

    def _calculate_confidence(self, signals: List[S3IdleSignal]) -> float:
        """
        Calculate idle confidence score - AWS Well-Architected Framework Aligned.

        Signal Framework v2.0 confidence mapping:

        Tier 1: High-Confidence (60 points max)
        - S1 (40 pts): 0.95 - Storage Lens Inactive
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html
        - S2 (20 pts): 0.85 - Storage Class Inefficiency
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html

        Tier 2: Medium-Confidence (45 points max)
        - S3 (15 pts): 0.80 - Lifecycle Missing
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
        - S4 (10 pts): 0.80 - Intelligent-Tiering Off
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/intelligent-tiering.html
        - S5 (10 pts): 0.80 - Versioning No Expiration
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
        - S6 (10 pts): 0.80 - Zero Requests 90D
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

        Tier 3: Lower-Confidence (20 points max)
        - S7 (5 pts): 0.70 - Replication Waste
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html
        - S8 (5 pts): 0.70 - Public No Encryption
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
        - S9 (5 pts): 0.70 - Inventory Overhead
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html
        - S10 (5 pts): 0.70 - High Request Cost
          https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudwatch-monitoring.html

        Args:
            signals: List of idle signals

        Returns:
            Confidence score (0.0-1.0) - maximum confidence from all signals
        """
        if not signals:
            return 0.0

        # Signal confidence mapping - S1-S10 framework (125 total points)
        signal_confidence = {
            # Tier 1: High-Confidence (60 points max)
            S3IdleSignal.S1_STORAGE_LENS_INACTIVE: 0.95,  # 40 pts
            S3IdleSignal.S2_STORAGE_CLASS_INEFFICIENCY: 0.85,  # 20 pts
            # Tier 2: Medium-Confidence (45 points max)
            S3IdleSignal.S3_LIFECYCLE_MISSING: 0.80,  # 15 pts
            S3IdleSignal.S4_INTELLIGENT_TIERING_OFF: 0.80,  # 10 pts
            S3IdleSignal.S5_VERSIONING_NO_EXPIRATION: 0.80,  # 10 pts
            S3IdleSignal.S6_ZERO_REQUESTS_90D: 0.80,  # 10 pts
            # Tier 3: Lower-Confidence (20 points max)
            S3IdleSignal.S7_REPLICATION_WASTE: 0.70,  # 5 pts
            S3IdleSignal.S8_PUBLIC_NO_ENCRYPTION: 0.70,  # 5 pts
            S3IdleSignal.S9_INVENTORY_OVERHEAD: 0.70,  # 5 pts
            S3IdleSignal.S10_HIGH_REQUEST_COST: 0.70,  # 5 pts
        }

        # Use maximum confidence from all signals
        return max(signal_confidence.get(signal, 0.0) for signal in signals)

    def _calculate_monthly_cost(self, metrics: S3ActivityMetrics) -> float:
        """
        Calculate monthly S3 bucket cost.

        Args:
            metrics: Activity metrics

        Returns:
            Monthly cost estimate
        """
        # Storage cost
        storage_cost = metrics.total_size_gb * self.DEFAULT_STORAGE_GB_MONTHLY_RATE

        # Request cost (already calculated)
        request_cost = metrics.request_cost_monthly

        return storage_cost + request_cost

    def _calculate_potential_savings(self, annual_cost: float, confidence: float, pattern: ActivityPattern) -> float:
        """
        Calculate potential annual savings.

        Savings scenarios:
        - IDLE: 100% savings (decommission)
        - LIGHT: 80% savings (optimize with lifecycle)
        - MODERATE: 40% savings (intelligent-tiering)
        - ACTIVE: 0% savings (keep as-is)

        Args:
            annual_cost: Annual S3 bucket cost
            confidence: Idle confidence score
            pattern: Activity pattern

        Returns:
            Potential annual savings amount
        """
        savings_multiplier = {
            ActivityPattern.IDLE: 1.0,
            ActivityPattern.LIGHT: 0.8,
            ActivityPattern.MODERATE: 0.4,
            ActivityPattern.ACTIVE: 0.0,
        }

        multiplier = savings_multiplier.get(pattern, 0.0)
        return annual_cost * multiplier * confidence

    def _generate_recommendation(
        self, pattern: ActivityPattern, signals: List[S3IdleSignal], confidence: float
    ) -> DecommissionRecommendation:
        """
        Generate optimization recommendation - S1-S10 framework aligned.

        Recommendation logic (normalized 125→100 scale):
        - DECOMMISSION: confidence >= 0.90 OR S1 signal present (Tier 1 high-confidence)
        - INVESTIGATE: confidence >= 0.70 (Tier 2 medium-confidence)
        - OPTIMIZE: confidence >= 0.50
        - KEEP: confidence < 0.50

        Args:
            pattern: Activity pattern
            signals: List of idle signals (S1-S10 framework)
            confidence: Overall confidence score (0.0-1.0)

        Returns:
            DecommissionRecommendation enum
        """
        # High confidence decommission candidates
        # S1 Storage Lens Inactive is the strongest decommission signal (40 pts)
        if confidence >= 0.90 or S3IdleSignal.S1_STORAGE_LENS_INACTIVE in signals:
            return DecommissionRecommendation.DECOMMISSION

        # Medium confidence - needs investigation
        if confidence >= 0.70:
            return DecommissionRecommendation.INVESTIGATE

        # Moderate underutilization - optimize
        if confidence >= 0.50:
            return DecommissionRecommendation.OPTIMIZE

        # Low confidence - keep resource
        return DecommissionRecommendation.KEEP

    def display_analysis(self, analyses: List[S3ActivityAnalysis]) -> None:
        """
        Display S3 activity analysis in Rich table format.

        Creates comprehensive activity analysis table with:
        - Bucket name and region
        - Activity metrics (requests, storage size)
        - Decommission signals (S1-S10) - AWS Well-Architected aligned
        - Recommendation and confidence

        Args:
            analyses: List of S3ActivityAnalysis objects
        """
        if not analyses:
            print_warning("No S3 buckets to display")
            return

        # Create analysis table
        table = create_table(
            title="S3 Bucket Activity Analysis",
            columns=[
                {"name": "Bucket Name", "style": "cyan"},
                {"name": "Requests/Day", "style": "bright_yellow"},
                {"name": "Size (GB)", "style": "white"},
                {"name": "Signals", "style": "bright_magenta"},
                {"name": "Annual Cost", "style": "white"},
                {"name": "Potential Savings", "style": "bright_green"},
                {"name": "Recommendation", "style": "bold"},
            ],
        )

        for analysis in analyses:
            # Format signals
            signals_str = ", ".join(signal.value for signal in analysis.idle_signals)
            if not signals_str:
                signals_str = "None"

            # Format recommendation with color
            rec = analysis.recommendation
            if rec == DecommissionRecommendation.DECOMMISSION:
                rec_str = f"[bright_red]{rec.value}[/bright_red]"
            elif rec == DecommissionRecommendation.INVESTIGATE:
                rec_str = f"[bright_yellow]{rec.value}[/bright_yellow]"
            elif rec == DecommissionRecommendation.OPTIMIZE:
                rec_str = f"[yellow]{rec.value}[/yellow]"
            else:
                rec_str = f"[bright_green]{rec.value}[/bright_green]"

            table.add_row(
                analysis.bucket_name,
                f"{analysis.metrics.avg_requests_per_day:.1f}",
                f"{analysis.metrics.total_size_gb:.2f}",
                signals_str,
                format_cost(analysis.monthly_cost * 12),  # Annual cost
                format_cost(analysis.potential_savings),  # Annual savings
                rec_str,
            )

        console.print()
        console.print(table)
        console.print()

    def _display_summary(self, analyses: List[S3ActivityAnalysis]) -> None:
        """Display analysis summary statistics."""
        if not analyses:
            return

        total = len(analyses)
        decommission_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.DECOMMISSION)
        investigate_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.INVESTIGATE)
        optimize_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.OPTIMIZE)
        keep_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.KEEP)

        # Calculate totals
        total_cost = sum(a.annual_cost for a in analyses)
        total_savings = sum(a.potential_savings for a in analyses)

        # Create summary panel
        summary_text = (
            f"[bold]Total Buckets: {total}[/bold]\n"
            f"[bold green]Total Potential Savings: {format_cost(total_savings)}/year[/bold green]\n"
            f"[bold]Total Annual S3 Cost: {format_cost(total_cost)}[/bold]\n\n"
            f"Recommendations:\n"
            f"  [bright_red]Decommission: {decommission_count}[/bright_red]\n"
            f"  [bright_yellow]Investigate: {investigate_count}[/bright_yellow]\n"
            f"  [yellow]Optimize: {optimize_count}[/yellow]\n"
            f"  [bright_green]Keep: {keep_count}[/bright_green]\n\n"
            f"CloudWatch Queries: {self.query_count}"
        )

        summary = create_panel(summary_text, title="S3 Idle Detection Summary", border_style="green")
        console.print(summary)
        console.print()

    def _get_from_cache(self, cache_key: str) -> Optional[S3ActivityAnalysis]:
        """Get analysis from cache if still valid."""
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return result
        return None

    def _add_to_cache(self, cache_key: str, analysis: S3ActivityAnalysis) -> None:
        """Add analysis to cache with current timestamp."""
        self._cache[cache_key] = (analysis, time.time())


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_s3_activity_enricher(
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 90
) -> S3ActivityEnricher:
    """
    Factory function to create S3ActivityEnricher.

    Provides clean initialization pattern following enterprise architecture
    with automatic profile resolution and sensible defaults.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudWatch lookback period (default: 90)

    Returns:
        Initialized S3ActivityEnricher instance

    Example:
        >>> enricher = create_s3_activity_enricher()
        >>> # Enricher ready for activity analysis
        >>> analyses = enricher.analyze_bucket_activity(...)
    """
    return S3ActivityEnricher(operational_profile=operational_profile, region=region, lookback_days=lookback_days)


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core enricher class
    "S3ActivityEnricher",
    # Data models
    "S3ActivityAnalysis",
    "S3ActivityMetrics",
    "S3IdleSignal",
    "ActivityPattern",
    "DecommissionRecommendation",
    # Factory function
    "create_s3_activity_enricher",
]
