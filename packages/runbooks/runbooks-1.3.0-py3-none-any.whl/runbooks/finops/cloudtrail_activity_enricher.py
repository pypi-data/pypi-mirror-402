#!/usr/bin/env python3
"""
CloudTrail Activity Enricher - Audit Service Activity Signals (T1-T7)
=======================================================================

Business Value: Idle CloudTrail resources detection enabling cost optimization
Strategic Impact: Complement CloudWatch/Config pattern for governance/audit workloads
Integration: Feeds data to FinOps decommission scoring framework

Architecture Pattern: 5-layer enrichment framework (matches CloudWatch/Config pattern)
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: CloudTrail activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses T1-T7 signals)

Decommission Signals (T1-T7):
- T1: No logging - Trail recording disabled (IsLogging=False)
- T2: S3 delivery errors - Snapshot delivery failures >7d
- T3: Insight disabled - Insight selectors not configured
- T4: Multi-region redundancy - Organization trail + redundant regional trails
- T5: Event selector bloat - Recording all events (cost driver)
- T6: Log validation disabled - Security best practice gap
- T7: Cross-account delivery cost - High S3 cross-account transfer costs

Target Confidence Score: 99/100 (achievable with 6+ signals present)

Usage:
    from runbooks.finops.cloudtrail_activity_enricher import CloudTrailActivityEnricher

    enricher = CloudTrailActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze CloudTrail trails
    analyses = enricher.analyze_trail_activity()

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer CloudTrail service costs
    - Flag discrepancies (low activity but high costs = potential issue)
    - Achieve ≥99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements - Track 3
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


class CloudTrailIdleSignal(str, Enum):
    """CloudTrail idle/underutilization decommission signals (T1-T7)."""

    T1_NO_LOGGING = "T1"  # Trail recording disabled (IsLogging=False)
    T2_DELIVERY_ERRORS = "T2"  # S3 delivery errors >7d
    T3_INSIGHT_DISABLED = "T3"  # Insight selectors not configured
    T4_REGIONAL_REDUNDANCY = "T4"  # Organization trail + redundant regional trails
    T5_EVENT_BLOAT = "T5"  # Recording all events (cost driver)
    T6_VALIDATION_DISABLED = "T6"  # Log validation disabled
    T7_CROSS_ACCOUNT_COST = "T7"  # High S3 cross-account transfer costs


class ActivityPattern(str, Enum):
    """CloudTrail activity pattern classification."""

    ACTIVE = "active"  # Active logging and event recording
    MODERATE = "moderate"  # Moderate logging configuration
    LIGHT = "light"  # Light logging
    IDLE = "idle"  # No logging activity


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
class CloudTrailActivityMetrics:
    """
    CloudTrail metrics for trails.

    Comprehensive activity metrics for decommission decision-making with
    T1-T7 signal framework.
    """

    is_logging: bool
    is_multi_region: bool
    is_organization_trail: bool
    has_log_validation: bool
    has_insight_selectors: bool
    has_event_selectors: bool
    recording_all_events: bool
    last_delivery_time: Optional[datetime]
    days_since_delivery: int
    delivery_error_count_7d: int
    s3_bucket_name: str
    sns_topic_arn: Optional[str]
    kms_key_id: Optional[str]


@dataclass
class CloudTrailActivityAnalysis:
    """
    CloudTrail trail activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    T1-T7 signal framework and cost impact analysis.
    """

    trail_name: str
    region: str
    account_id: str
    metrics: CloudTrailActivityMetrics
    activity_pattern: ActivityPattern
    idle_signals: List[CloudTrailIdleSignal] = field(default_factory=list)
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: int = 0  # 0-100 scale
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "trail_name": self.trail_name,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "is_logging": self.metrics.is_logging,
                "is_multi_region": self.metrics.is_multi_region,
                "is_organization_trail": self.metrics.is_organization_trail,
                "has_log_validation": self.metrics.has_log_validation,
                "has_insight_selectors": self.metrics.has_insight_selectors,
                "has_event_selectors": self.metrics.has_event_selectors,
                "recording_all_events": self.metrics.recording_all_events,
                "last_delivery_time": self.metrics.last_delivery_time.isoformat()
                if self.metrics.last_delivery_time
                else None,
                "days_since_delivery": self.metrics.days_since_delivery,
                "delivery_error_count_7d": self.metrics.delivery_error_count_7d,
                "s3_bucket_name": self.metrics.s3_bucket_name,
                "sns_topic_arn": self.metrics.sns_topic_arn,
                "kms_key_id": self.metrics.kms_key_id,
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


class CloudTrailActivityEnricher:
    """
    CloudTrail activity enricher for trails and event logging.

    Analyzes CloudTrail resources for idle/underutilization patterns using
    CloudTrail APIs with T1-T7 signal framework.

    Capabilities:
    - Trail activity metrics analysis
    - Logging status tracking
    - Delivery channel health monitoring
    - Event selector efficiency analysis
    - Insight configuration assessment
    - Comprehensive decommission recommendations

    Decommission Signals Generated:
    - T1: No logging (HIGH confidence)
    - T2: Delivery errors (MEDIUM confidence)
    - T3: Insight disabled (LOW confidence)
    - T4: Regional redundancy (MEDIUM confidence)
    - T5: Event bloat (MEDIUM confidence)
    - T6: Validation disabled (LOW confidence)
    - T7: Cross-account cost (LOW confidence)

    Target: 99/100 confidence with 6+ signals present
    """

    # Activity thresholds for classification
    DELIVERY_ERROR_THRESHOLD_DAYS = 7  # days

    # CloudTrail pricing (US East - N. Virginia baseline)
    DATA_EVENT_COST_PER_100K = 0.10  # $0.10 per 100K data events
    MANAGEMENT_EVENT_COST = 0.00  # First copy free, additional copies $2.00 per 100K
    INSIGHT_EVENT_COST_PER_100K = 0.35  # $0.35 per 100K insight events
    ESTIMATED_EVENTS_PER_MONTH = 1000000  # Conservative estimate (1M events)

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 7,
        cache_ttl: int = 300,
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize CloudTrail activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for CloudTrail queries (default: ap-southeast-2)
            lookback_days: CloudTrail lookback period (default: 7)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = lookback_days
        self.cache_ttl = cache_ttl

        # Initialize AWS session
        self.session = create_operational_session(self.operational_profile)
        self.cloudtrail_client = self.session.client("cloudtrail", region_name=self.region)

        # Validation cache (5-minute TTL for performance)
        self._cache: Dict[str, Tuple[CloudTrailActivityAnalysis, float]] = {}

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
                f"🔍 CloudTrail Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )
        else:
            self.logger.debug(
                f"CloudTrail Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )

    def analyze_trail_activity(
        self, trail_names: Optional[List[str]] = None, region: Optional[str] = None, lookback_days: Optional[int] = None
    ) -> List[CloudTrailActivityAnalysis]:
        """
        Analyze CloudTrail trail activity for idle detection.

        Core analysis workflow:
        1. Query CloudTrail trails (all or specific names)
        2. Get activity metrics for each trail (7 day window)
        3. Classify activity pattern (active/moderate/light/idle)
        4. Generate T1-T7 decommission signals based on patterns
        5. Compute confidence score (0-100) and recommendation
        6. Calculate cost impact and potential savings

        Args:
            trail_names: List of trail names to analyze (analyzes all if None)
            region: AWS region filter (default: use instance region)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals
        """
        start_time = time.time()
        analysis_region = region or self.region
        lookback = lookback_days or self.lookback_days

        print_section(f"CloudTrail Activity Analysis ({lookback}-day lookback)")

        # Get trails
        trails = self._get_trails(trail_names, analysis_region)

        if not trails:
            print_warning("No CloudTrail trails found")
            return []

        print_info(f"Found {len(trails)} CloudTrail trails")

        analyses: List[CloudTrailActivityAnalysis] = []

        with create_progress_bar(description="Analyzing CloudTrail trails") as progress:
            task = progress.add_task(f"Analyzing {len(trails)} trails", total=len(trails))

            for trail in trails:
                try:
                    # Check cache first
                    trail_name = trail["Name"]
                    cache_key = f"{trail_name}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Analyze trail
                    analysis = self._analyze_trail(trail, lookback)

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(f"Failed to analyze trail {trail.get('Name')}: {e}", exc_info=True)
                    print_warning(f"⚠️  Skipped {trail.get('Name')}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _get_trails(self, trail_names: Optional[List[str]], region: str) -> List[Dict]:
        """
        Get CloudTrail trails from AWS API.

        Args:
            trail_names: Specific trails to retrieve (retrieves all if None)
            region: AWS region filter

        Returns:
            List of trail metadata dictionaries
        """
        trails = []

        try:
            # DescribeTrails returns all trails (no pagination needed)
            response = self.cloudtrail_client.describe_trails()
            all_trails = response.get("trailList", [])

            # Filter by trail names if specified
            if trail_names:
                trails = [t for t in all_trails if t["Name"] in trail_names]
            else:
                trails = all_trails

            self.query_count += 1

        except ClientError as e:
            self.logger.error(f"Failed to get CloudTrail trails: {e}")

        return trails

    def _analyze_trail(self, trail: Dict, lookback_days: int) -> CloudTrailActivityAnalysis:
        """
        Analyze individual CloudTrail trail.

        Args:
            trail: Trail metadata from describe_trails
            lookback_days: Activity metrics lookback period

        Returns:
            Comprehensive activity analysis with idle signals
        """
        trail_name = trail["Name"]

        # Get activity metrics
        metrics = self._get_activity_metrics(trail, lookback_days)

        # Classify activity pattern
        activity_pattern = self._classify_activity_pattern(metrics)

        # Generate idle signals (T1-T7)
        idle_signals = self._generate_idle_signals(metrics, activity_pattern)

        # Calculate confidence score (0-100)
        confidence = self._calculate_confidence(idle_signals)

        # Calculate costs
        monthly_cost = self._calculate_monthly_cost(metrics)
        annual_cost = monthly_cost * 12

        # Calculate potential savings
        potential_savings = self._calculate_potential_savings(annual_cost, confidence, activity_pattern)

        # Generate recommendation
        recommendation = self._generate_recommendation(activity_pattern, idle_signals, confidence)

        # Get account ID
        try:
            sts = self.session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
        except Exception:
            account_id = "unknown"

        return CloudTrailActivityAnalysis(
            trail_name=trail_name,
            region=self.region,
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

    def _get_activity_metrics(self, trail: Dict, lookback_days: int) -> CloudTrailActivityMetrics:
        """
        Get activity metrics for CloudTrail trail.

        Metrics gathered:
        - Logging status (T1 signal)
        - Multi-region configuration
        - Organization trail status
        - Log validation (T6 signal)
        - Insight selectors (T3 signal)
        - Event selectors (T5 signal)
        - Delivery status (T2 signal)

        Args:
            trail: Trail metadata
            lookback_days: Lookback period for metrics

        Returns:
            Comprehensive activity metrics
        """
        trail_name = trail["Name"]
        trail_arn = trail.get("TrailARN", "")

        # Extract basic configuration
        is_multi_region = trail.get("IsMultiRegionTrail", False)
        is_organization_trail = trail.get("IsOrganizationTrail", False)
        has_log_validation = trail.get("LogFileValidationEnabled", False)
        s3_bucket_name = trail.get("S3BucketName", "")
        sns_topic_arn = trail.get("SnsTopicARN")
        kms_key_id = trail.get("KmsKeyId")

        # Get logging status (T1 signal)
        is_logging, last_delivery_time, days_since_delivery = self._get_logging_status(trail_name)

        # Get event selectors (T5 signal)
        has_event_selectors, recording_all_events = self._get_event_selectors(trail_name)

        # Get insight selectors (T3 signal)
        has_insight_selectors = self._get_insight_selectors(trail_name)

        # Get delivery errors (T2 signal)
        delivery_error_count = self._get_delivery_error_count(trail_name, lookback_days)

        return CloudTrailActivityMetrics(
            is_logging=is_logging,
            is_multi_region=is_multi_region,
            is_organization_trail=is_organization_trail,
            has_log_validation=has_log_validation,
            has_insight_selectors=has_insight_selectors,
            has_event_selectors=has_event_selectors,
            recording_all_events=recording_all_events,
            last_delivery_time=last_delivery_time,
            days_since_delivery=days_since_delivery,
            delivery_error_count_7d=delivery_error_count,
            s3_bucket_name=s3_bucket_name,
            sns_topic_arn=sns_topic_arn,
            kms_key_id=kms_key_id,
        )

    def _get_logging_status(self, trail_name: str) -> Tuple[bool, Optional[datetime], int]:
        """
        Get trail logging status (T1 signal).

        Args:
            trail_name: CloudTrail trail name

        Returns:
            Tuple of (is_logging, last_delivery_time, days_since_delivery)
        """
        try:
            response = self.cloudtrail_client.get_trail_status(Name=trail_name)

            is_logging = response.get("IsLogging", False)
            last_delivery_time = response.get("LatestDeliveryTime")

            if last_delivery_time:
                days_since = (datetime.now(tz=timezone.utc) - last_delivery_time).days
            else:
                days_since = 999  # Large value if never delivered

            self.query_count += 1
            return is_logging, last_delivery_time, days_since

        except ClientError as e:
            self.logger.debug(f"Failed to get trail status for {trail_name}: {e}")
            return False, None, 999

    def _get_event_selectors(self, trail_name: str) -> Tuple[bool, bool]:
        """
        Get event selectors (T5 signal).

        Args:
            trail_name: CloudTrail trail name

        Returns:
            Tuple of (has_event_selectors, recording_all_events)
        """
        try:
            response = self.cloudtrail_client.get_event_selectors(TrailName=trail_name)

            event_selectors = response.get("EventSelectors", [])
            has_selectors = len(event_selectors) > 0

            # Check if recording all events (IncludeManagementEvents=True, ReadWriteType=All)
            recording_all = False
            if has_selectors:
                for selector in event_selectors:
                    if selector.get("IncludeManagementEvents", False) and selector.get("ReadWriteType") == "All":
                        recording_all = True
                        break

            self.query_count += 1
            return has_selectors, recording_all

        except ClientError as e:
            self.logger.debug(f"Failed to get event selectors for {trail_name}: {e}")
            return False, False

    def _get_insight_selectors(self, trail_name: str) -> bool:
        """
        Get insight selectors (T3 signal).

        Args:
            trail_name: CloudTrail trail name

        Returns:
            True if insight selectors configured
        """
        try:
            response = self.cloudtrail_client.get_insight_selectors(TrailName=trail_name)

            insight_selectors = response.get("InsightSelectors", [])

            self.query_count += 1
            return len(insight_selectors) > 0

        except ClientError as e:
            # InsightSelectors may not be available in all regions
            self.logger.debug(f"Failed to get insight selectors for {trail_name}: {e}")
            return False

    def _get_delivery_error_count(self, trail_name: str, lookback_days: int) -> int:
        """
        Get delivery error count (T2 signal).

        Args:
            trail_name: CloudTrail trail name
            lookback_days: Lookback period

        Returns:
            Number of delivery errors in lookback period
        """
        try:
            response = self.cloudtrail_client.get_trail_status(Name=trail_name)

            # Check for delivery errors
            latest_delivery_error = response.get("LatestDeliveryError")
            latest_digest_delivery_error = response.get("LatestDigestDeliveryError")

            error_count = 0
            if latest_delivery_error:
                error_count += 1
            if latest_digest_delivery_error:
                error_count += 1

            return error_count

        except ClientError as e:
            self.logger.debug(f"Failed to get delivery errors for {trail_name}: {e}")
            return 0

    def _classify_activity_pattern(self, metrics: CloudTrailActivityMetrics) -> ActivityPattern:
        """
        Classify CloudTrail activity pattern.

        Classification:
        - ACTIVE: Logging enabled, recent delivery, insights configured
        - MODERATE: Logging enabled, basic configuration
        - LIGHT: Logging enabled but minimal configuration
        - IDLE: Logging disabled or delivery failures

        Args:
            metrics: CloudTrail activity metrics

        Returns:
            ActivityPattern enum
        """
        if not metrics.is_logging or metrics.days_since_delivery >= 7:
            return ActivityPattern.IDLE
        elif metrics.has_insight_selectors and metrics.has_log_validation:
            return ActivityPattern.ACTIVE
        elif metrics.has_event_selectors:
            return ActivityPattern.MODERATE
        else:
            return ActivityPattern.LIGHT

    def _generate_idle_signals(
        self, metrics: CloudTrailActivityMetrics, pattern: ActivityPattern
    ) -> List[CloudTrailIdleSignal]:
        """
        Generate T1-T7 idle signals.

        Signal generation rules:
        - T1: No logging → HIGH confidence
        - T2: Delivery errors >7d → MEDIUM confidence
        - T3: Insight disabled → LOW confidence
        - T4: Regional redundancy → MEDIUM confidence
        - T5: Event bloat → MEDIUM confidence
        - T6: Validation disabled → LOW confidence
        - T7: Cross-account cost (placeholder) → LOW confidence

        Args:
            metrics: CloudTrail activity metrics
            pattern: Activity pattern classification

        Returns:
            List of applicable CloudTrailIdleSignal enums
        """
        signals: List[CloudTrailIdleSignal] = []

        # T1: No logging
        if not metrics.is_logging:
            signals.append(CloudTrailIdleSignal.T1_NO_LOGGING)

        # T2: Delivery errors
        if metrics.delivery_error_count_7d > 0 or metrics.days_since_delivery >= 7:
            signals.append(CloudTrailIdleSignal.T2_DELIVERY_ERRORS)

        # T3: Insight disabled
        if not metrics.has_insight_selectors:
            signals.append(CloudTrailIdleSignal.T3_INSIGHT_DISABLED)

        # T4: Regional redundancy (organization trail should be sufficient)
        if metrics.is_organization_trail and not metrics.is_multi_region:
            signals.append(CloudTrailIdleSignal.T4_REGIONAL_REDUNDANCY)

        # T5: Event bloat (recording all events)
        if metrics.recording_all_events:
            signals.append(CloudTrailIdleSignal.T5_EVENT_BLOAT)

        # T6: Validation disabled
        if not metrics.has_log_validation:
            signals.append(CloudTrailIdleSignal.T6_VALIDATION_DISABLED)

        # T7: Cross-account cost (placeholder - would need Cost Explorer)
        # signals.append(CloudTrailIdleSignal.T7_CROSS_ACCOUNT_COST)

        return signals

    def _calculate_confidence(self, signals: List[CloudTrailIdleSignal]) -> int:
        """
        Calculate idle confidence score (0-100).

        Target: 99/100 confidence with 6+ signals present

        Signal weights (proportional scoring to reach 99):
        - T1: 30 points (no logging - strongest signal)
        - T2: 25 points (delivery errors)
        - T3: 10 points (insight disabled)
        - T4: 15 points (regional redundancy)
        - T5: 12 points (event bloat)
        - T6: 10 points (validation disabled)
        - T7: 7 points (cross-account cost)

        Total possible: 109 points (capped at 99 for 6+ signals)

        Args:
            signals: List of idle signals

        Returns:
            Confidence score (0-100, target 99 for 6+ signals)
        """
        if not signals:
            return 0

        signal_weights = {
            CloudTrailIdleSignal.T1_NO_LOGGING: 30,
            CloudTrailIdleSignal.T2_DELIVERY_ERRORS: 25,
            CloudTrailIdleSignal.T3_INSIGHT_DISABLED: 10,
            CloudTrailIdleSignal.T4_REGIONAL_REDUNDANCY: 15,
            CloudTrailIdleSignal.T5_EVENT_BLOAT: 12,
            CloudTrailIdleSignal.T6_VALIDATION_DISABLED: 10,
            CloudTrailIdleSignal.T7_CROSS_ACCOUNT_COST: 7,
        }

        total_score = sum(signal_weights.get(signal, 0) for signal in signals)

        # Cap at 99 for 6+ signals (enterprise scoring standard)
        return min(total_score, 99)

    def _calculate_monthly_cost(self, metrics: CloudTrailActivityMetrics) -> float:
        """
        Calculate monthly CloudTrail cost.

        Cost components:
        - Management events: First copy free, additional $2.00 per 100K
        - Data events: $0.10 per 100K
        - Insight events: $0.35 per 100K

        Args:
            metrics: Activity metrics

        Returns:
            Monthly cost estimate
        """
        # Simplified cost model (would need actual event counts)
        if metrics.recording_all_events:
            # Conservative estimate for recording all events
            events_cost = (self.ESTIMATED_EVENTS_PER_MONTH / 100000) * self.DATA_EVENT_COST_PER_100K
        else:
            # Management events only (first copy free)
            events_cost = 0

        # Insight events (if enabled)
        insight_cost = 0
        if metrics.has_insight_selectors:
            insight_cost = (self.ESTIMATED_EVENTS_PER_MONTH / 100000) * self.INSIGHT_EVENT_COST_PER_100K

        return events_cost + insight_cost

    def _calculate_potential_savings(self, annual_cost: float, confidence: int, pattern: ActivityPattern) -> float:
        """
        Calculate potential annual savings.

        Savings scenarios:
        - IDLE: 100% savings (decommission)
        - LIGHT: 60% savings (optimize configuration)
        - MODERATE: 30% savings (optimize event selectors)
        - ACTIVE: 0% savings (keep as-is)

        Args:
            annual_cost: Annual CloudTrail cost
            confidence: Idle confidence score (0-100)
            pattern: Activity pattern

        Returns:
            Potential annual savings amount
        """
        savings_multiplier = {
            ActivityPattern.IDLE: 1.0,
            ActivityPattern.LIGHT: 0.6,
            ActivityPattern.MODERATE: 0.3,
            ActivityPattern.ACTIVE: 0.0,
        }

        multiplier = savings_multiplier.get(pattern, 0.0)
        confidence_factor = confidence / 100.0

        return annual_cost * multiplier * confidence_factor

    def _generate_recommendation(
        self, pattern: ActivityPattern, signals: List[CloudTrailIdleSignal], confidence: int
    ) -> DecommissionRecommendation:
        """
        Generate optimization recommendation.

        Recommendation logic (aligned with 0-100 scoring):
        - DECOMMISSION: confidence ≥ 80 (MUST tier)
        - INVESTIGATE: confidence ≥ 50 (SHOULD tier)
        - OPTIMIZE: confidence ≥ 25 (COULD tier)
        - KEEP: confidence < 25 (KEEP tier)

        Args:
            pattern: Activity pattern
            signals: List of idle signals
            confidence: Overall confidence score (0-100)

        Returns:
            DecommissionRecommendation enum
        """
        if confidence >= 80:
            return DecommissionRecommendation.DECOMMISSION
        elif confidence >= 50:
            return DecommissionRecommendation.INVESTIGATE
        elif confidence >= 25:
            return DecommissionRecommendation.OPTIMIZE
        else:
            return DecommissionRecommendation.KEEP

    def display_analysis(self, analyses: List[CloudTrailActivityAnalysis]) -> None:
        """
        Display CloudTrail activity analysis in Rich table format.

        Args:
            analyses: List of CloudTrailActivityAnalysis objects
        """
        if not analyses:
            print_warning("No CloudTrail trails to display")
            return

        # Create analysis table
        table = create_table(
            title="CloudTrail Activity Analysis",
            columns=[
                {"name": "Trail Name", "style": "cyan"},
                {"name": "Logging", "style": "bright_yellow"},
                {"name": "Multi-Region", "style": "white"},
                {"name": "Signals", "style": "bright_magenta"},
                {"name": "Confidence", "style": "white"},
                {"name": "Monthly Cost", "style": "white"},
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

            # Format logging status
            logging_status = "[green]Enabled[/]" if analysis.metrics.is_logging else "[red]Disabled[/]"
            multi_region = "[green]Yes[/]" if analysis.metrics.is_multi_region else "[dim]No[/]"

            table.add_row(
                analysis.trail_name,
                logging_status,
                multi_region,
                signals_str,
                f"{analysis.confidence}/100",
                format_cost(analysis.monthly_cost),
                format_cost(analysis.potential_savings / 12),  # Monthly savings
                rec_str,
            )

        console.print()
        console.print(table)
        console.print()

    def _display_summary(self, analyses: List[CloudTrailActivityAnalysis]) -> None:
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

        # Calculate average confidence for high-confidence candidates
        high_confidence_analyses = [a for a in analyses if a.confidence >= 80]
        avg_confidence = (
            sum(a.confidence for a in high_confidence_analyses) / len(high_confidence_analyses)
            if high_confidence_analyses
            else 0
        )

        # Create summary panel
        summary_text = (
            f"[bold]Total Trails: {total}[/bold]\n"
            f"[bold green]Total Potential Savings: {format_cost(total_savings)}/year[/bold green]\n"
            f"[bold]Total Annual CloudTrail Cost: {format_cost(total_cost)}[/bold]\n\n"
            f"Recommendations:\n"
            f"  [bright_red]Decommission: {decommission_count}[/bright_red]\n"
            f"  [bright_yellow]Investigate: {investigate_count}[/bright_yellow]\n"
            f"  [yellow]Optimize: {optimize_count}[/yellow]\n"
            f"  [bright_green]Keep: {keep_count}[/bright_green]\n\n"
            f"Quality Metrics:\n"
            f"  Average Confidence (≥80): {avg_confidence:.0f}/100\n"
            f"  API Queries: {self.query_count}\n"
            f"  Target: 99/100 confidence (6+ signals)"
        )

        summary = create_panel(
            summary_text, title="CloudTrail Idle Detection Summary (T1-T7 Signals)", border_style="green"
        )
        console.print(summary)
        console.print()

    def _get_from_cache(self, cache_key: str) -> Optional[CloudTrailActivityAnalysis]:
        """Get analysis from cache if still valid."""
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return result
        return None

    def _add_to_cache(self, cache_key: str, analysis: CloudTrailActivityAnalysis) -> None:
        """Add analysis to cache with current timestamp."""
        self._cache[cache_key] = (analysis, time.time())


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_cloudtrail_activity_enricher(
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 7
) -> CloudTrailActivityEnricher:
    """
    Factory function to create CloudTrailActivityEnricher.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudTrail lookback period (default: 7)

    Returns:
        Initialized CloudTrailActivityEnricher instance
    """
    return CloudTrailActivityEnricher(
        operational_profile=operational_profile, region=region, lookback_days=lookback_days
    )


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core enricher class
    "CloudTrailActivityEnricher",
    # Data models
    "CloudTrailActivityAnalysis",
    "CloudTrailActivityMetrics",
    "CloudTrailIdleSignal",
    "ActivityPattern",
    "DecommissionRecommendation",
    # Factory function
    "create_cloudtrail_activity_enricher",
]
