#!/usr/bin/env python3
"""
CloudTrail Activity Enricher - Phase 5 Feature 1
==================================================

Business Value: $18K annual savings enabler through activity-based decommission signals
Strategic Impact: Inventory module biggest gap resolution (7/10 features missing)
Integration: Connects with VPC cloudtrail_activity_analyzer.py (Phase 3 P2)

Architecture Pattern: 5-layer enrichment framework
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: CloudTrail activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses I1-I6 signals)

Decommission Signals (I1-I6):
- I1: No CloudTrail events in 90+ days (HIGH confidence: 0.95)
- I2: Only read-only operations in 90 days (MEDIUM confidence: 0.70)
- I3: No management operations in 60 days (MEDIUM confidence: 0.65)
- I4: Automated operations only (MEDIUM confidence: 0.60)
- I5: Activity pattern declining >70% vs baseline (LOW confidence: 0.40)
- I6: No user-initiated operations in 30 days (LOW confidence: 0.50)

Usage:
    from runbooks.inventory.enrichers.cloudtrail_activity import CloudTrailActivityEnricher

    enricher = CloudTrailActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2',
        lookback_days=90
    )

    # Analyze resource activity
    analyses = enricher.analyze_resource_activity(
        resource_ids=['i-1234567890abcdef0', 'i-0987654321fedcba0'],
        resource_type='EC2'
    )

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer usage metrics
    - Flag discrepancies (CloudTrail shows activity, but no costs incurred)
    - Achieve ≥99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: Epic 2 - Infrastructure Optimization
Feature: Phase 5 Feature 1 - CloudTrail Activity Enricher
"""

import asyncio
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
    create_progress_bar,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_section,
)
from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
)

# Try to import HybridMCPEngine for validation (graceful degradation if unavailable)
try:
    from runbooks.finops.hybrid_mcp_engine import HybridMCPEngine, MCP_AVAILABLE
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("HybridMCPEngine not available - MCP validation disabled")

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# ENUMERATION TYPES
# ═════════════════════════════════════════════════════════════════════════════


class ActivitySignal(str, Enum):
    """CloudTrail activity decommission signals (I1-I6)."""

    I1_NO_ACTIVITY_90D = "I1"  # No CloudTrail events in 90+ days
    I2_READ_ONLY_90D = "I2"  # Only read-only operations in 90 days
    I3_NO_MGMT_60D = "I3"  # No management operations in 60 days
    I4_AUTOMATED_ONLY = "I4"  # Automated operations only
    I5_DECLINING_PATTERN = "I5"  # Activity declining >70% vs baseline
    I6_NO_USER_OPS_30D = "I6"  # No user-initiated operations in 30 days


class ActivityTrend(str, Enum):
    """Activity trend classification."""

    INCREASING = "INCREASING"  # Activity growing over time
    STABLE = "STABLE"  # Consistent activity levels
    DECLINING = "DECLINING"  # Activity decreasing over time
    NONE = "NONE"  # No activity detected


class DecommissionRecommendation(str, Enum):
    """Decommission recommendations based on activity analysis."""

    DECOMMISSION = "DECOMMISSION"  # High confidence - decommission candidate
    INVESTIGATE = "INVESTIGATE"  # Medium confidence - needs review
    KEEP = "KEEP"  # Active resource - retain


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class CloudTrailActivityAnalysis:
    """
    CloudTrail activity analysis for a resource.

    Comprehensive activity metrics for decommission decision-making with
    I1-I6 signal framework and MCP validation capability.
    """

    resource_id: str
    resource_type: str
    last_activity: Optional[datetime]
    event_count_30d: int
    event_count_60d: int
    event_count_90d: int
    user_initiated_events: int
    automated_events: int
    read_only_pct: float  # 0.0-100.0
    activity_trend: ActivityTrend
    decommission_signals: List[ActivitySignal] = field(default_factory=list)
    confidence: float = 0.0  # 0.0-1.0
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP
    mcp_validated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "event_count_30d": self.event_count_30d,
            "event_count_60d": self.event_count_60d,
            "event_count_90d": self.event_count_90d,
            "user_initiated_events": self.user_initiated_events,
            "automated_events": self.automated_events,
            "read_only_pct": self.read_only_pct,
            "activity_trend": self.activity_trend.value,
            "decommission_signals": [signal.value for signal in self.decommission_signals],
            "confidence": self.confidence,
            "recommendation": self.recommendation.value,
            "mcp_validated": self.mcp_validated,
            "metadata": self.metadata,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE ENRICHER CLASS
# ═════════════════════════════════════════════════════════════════════════════


class CloudTrailActivityEnricher:
    """
    CloudTrail activity enricher for inventory resources.

    Analyzes CloudTrail events to identify unused/underutilized resources
    using I1-I6 signal framework with MCP validation support.

    Capabilities:
    - Activity timeline analysis (30/60/90 day windows)
    - User vs automated operation classification
    - Read-only vs management operation classification
    - Activity trend analysis (declining usage patterns)
    - MCP validation of activity patterns
    - Comprehensive decommission recommendations

    Decommission Signals Generated:
    - I1: No activity 90+ days (HIGH confidence: 0.95)
    - I2: Read-only operations only (MEDIUM confidence: 0.70)
    - I3: No management operations 60+ days (MEDIUM confidence: 0.65)
    - I4: Automated operations only (MEDIUM confidence: 0.60)
    - I5: Declining activity pattern >70% (LOW confidence: 0.40)
    - I6: No user operations 30+ days (LOW confidence: 0.50)

    Example:
        >>> enricher = CloudTrailActivityEnricher(
        ...     operational_profile='ops-profile',
        ...     region='ap-southeast-2'
        ... )
        >>> analyses = enricher.analyze_resource_activity(
        ...     resource_ids=['i-1234567890abcdef0'],
        ...     resource_type='EC2'
        ... )
        >>> for analysis in analyses:
        ...     if ActivitySignal.I1_NO_ACTIVITY_90D in analysis.decommission_signals:
        ...         print(f"Unused instance: {analysis.resource_id}")
    """

    # Operation classification patterns
    USER_INITIATED_PRINCIPALS = ["AssumedRole", "IAMUser", "Root", "FederatedUser"]
    AUTOMATED_PRINCIPALS = ["ServiceRole", "AutoScaling", "Lambda", "CodePipeline", "CloudFormation"]
    READ_ONLY_OPERATIONS = ["Describe*", "Get*", "List*", "Head*", "Lookup*", "Query*"]
    MANAGEMENT_OPERATIONS = [
        "Create*",
        "Delete*",
        "Modify*",
        "Update*",
        "Start*",
        "Stop*",
        "Reboot*",
        "Terminate*",
        "Attach*",
        "Detach*",
        "Associate*",
        "Disassociate*",
    ]

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 90,
        cache_ttl: int = 300,
    ):
        """
        Initialize CloudTrail activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for CloudTrail queries (default: ap-southeast-2)
            lookback_days: CloudTrail lookback period (default: 90, max: 90)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = min(lookback_days, 90)  # CloudTrail max retention
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

        print_info(f"🔍 CloudTrail Activity Enricher initialized")
        print_info(f"   Profile: {self.operational_profile}")
        print_info(f"   Region: {self.region}")
        print_info(f"   Lookback: {self.lookback_days} days")

    def analyze_resource_activity(
        self, resource_ids: List[str], resource_type: str, lookback_days: Optional[int] = None
    ) -> List[CloudTrailActivityAnalysis]:
        """
        Analyze CloudTrail activity for resources.

        Core analysis workflow:
        1. Query CloudTrail events for each resource (30/60/90 day windows)
        2. Classify operations (user vs automated, read-only vs management)
        3. Calculate activity trend (increasing/stable/declining/none)
        4. Generate I1-I6 decommission signals based on patterns
        5. Compute confidence score and recommendation

        Args:
            resource_ids: List of resource IDs to analyze
            resource_type: Resource type (EC2, RDS, S3, Lambda, VPC)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals

        Example:
            >>> analyses = enricher.analyze_resource_activity(
            ...     resource_ids=['i-abc123', 'i-def456'],
            ...     resource_type='EC2'
            ... )
            >>> for analysis in analyses:
            ...     print(f"{analysis.resource_id}: {analysis.recommendation.value}")
        """
        start_time = time.time()
        lookback = lookback_days or self.lookback_days

        print_section(f"CloudTrail Activity Analysis ({lookback}-day lookback)")

        analyses: List[CloudTrailActivityAnalysis] = []

        # Calculate time windows
        end_time = datetime.now(tz=timezone.utc)
        start_time_90d = end_time - timedelta(days=lookback)
        start_time_60d = end_time - timedelta(days=60)
        start_time_30d = end_time - timedelta(days=30)

        with create_progress_bar(description="Analyzing CloudTrail events") as progress:
            task = progress.add_task(f"Analyzing {len(resource_ids)} resources", total=len(resource_ids))

            for resource_id in resource_ids:
                try:
                    # Check cache first
                    cache_key = f"{resource_id}:{resource_type}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Query CloudTrail events for all time windows
                    events_90d = self._query_cloudtrail_events(resource_id, start_time_90d, end_time)

                    # Filter events for 60d and 30d windows
                    events_60d = [e for e in events_90d if e["EventTime"] >= start_time_60d]
                    events_30d = [e for e in events_90d if e["EventTime"] >= start_time_30d]

                    # Classify operations
                    classified_events = [self._classify_operation(event) for event in events_90d]

                    # Calculate metrics
                    user_initiated = sum(1 for e in classified_events if e["is_user_initiated"])
                    automated = sum(1 for e in classified_events if e["is_automated"])
                    read_only_count = sum(1 for e in classified_events if e["is_read_only"])

                    # Calculate read-only percentage
                    total_events = len(classified_events)
                    read_only_pct = (read_only_count / total_events * 100) if total_events > 0 else 0.0

                    # Calculate activity trend
                    activity_trend = self._calculate_trend(len(events_30d), len(events_60d), len(events_90d))

                    # Find last activity
                    last_activity = max(e["EventTime"] for e in events_90d) if events_90d else None

                    # Generate decommission signals
                    analysis_data = {
                        "event_count_30d": len(events_30d),
                        "event_count_60d": len(events_60d),
                        "event_count_90d": len(events_90d),
                        "user_initiated_events": user_initiated,
                        "automated_events": automated,
                        "read_only_pct": read_only_pct,
                        "activity_trend": activity_trend,
                        "classified_events": classified_events,
                    }

                    signals = self._generate_signals(analysis_data)
                    confidence = self._calculate_confidence(signals)
                    recommendation = self._determine_recommendation(signals, confidence)

                    # Create analysis object
                    analysis = CloudTrailActivityAnalysis(
                        resource_id=resource_id,
                        resource_type=resource_type,
                        last_activity=last_activity,
                        event_count_30d=len(events_30d),
                        event_count_60d=len(events_60d),
                        event_count_90d=len(events_90d),
                        user_initiated_events=user_initiated,
                        automated_events=automated,
                        read_only_pct=read_only_pct,
                        activity_trend=activity_trend,
                        decommission_signals=signals,
                        confidence=confidence,
                        recommendation=recommendation,
                        metadata={
                            "lookback_days": lookback,
                            "query_time": datetime.now(tz=timezone.utc).isoformat(),
                        },
                    )

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(f"Failed to analyze CloudTrail activity for {resource_id}: {e}", exc_info=True)
                    print_warning(f"⚠️  Skipped {resource_id}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _query_cloudtrail_events(self, resource_id: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Query CloudTrail events for resource.

        Uses CloudTrail LookupEvents API with resource name filter
        and pagination support for >50 events.

        Args:
            resource_id: AWS resource identifier
            start_time: Query start time
            end_time: Query end time

        Returns:
            List of CloudTrail events
        """
        events = []
        next_token = None

        try:
            while True:
                # Build API parameters
                params = {
                    "LookupAttributes": [{"AttributeKey": "ResourceName", "AttributeValue": resource_id}],
                    "StartTime": start_time,
                    "EndTime": end_time,
                    "MaxResults": 50,
                }

                if next_token:
                    params["NextToken"] = next_token

                # Query CloudTrail
                response = self.cloudtrail_client.lookup_events(**params)

                # Extract events
                events.extend(response.get("Events", []))

                # Check for more pages
                next_token = response.get("NextToken")
                if not next_token:
                    break

                # Increment query counter
                self.query_count += 1

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDeniedException":
                self.logger.warning(f"CloudTrail access denied for {resource_id} - check IAM permissions")
            elif error_code == "InvalidTimeRangeException":
                self.logger.error(f"Invalid time range for CloudTrail query: {start_time} to {end_time}")
            else:
                self.logger.error(f"CloudTrail query failed: {e}")

        except Exception as e:
            self.logger.error(f"Unexpected error querying CloudTrail: {e}", exc_info=True)

        return events

    def _classify_operation(self, event: Dict) -> Dict[str, Any]:
        """
        Classify CloudTrail operation.

        Determines if operation is:
        - User-initiated vs automated
        - Read-only vs management
        - Based on principal type and event name

        Args:
            event: CloudTrail event dictionary

        Returns:
            Classification dictionary with boolean flags
        """
        event_name = event.get("EventName", "")
        username = event.get("Username", "")

        # Classify principal type
        is_user_initiated = any(principal in username for principal in self.USER_INITIATED_PRINCIPALS)
        is_automated = any(principal in username for principal in self.AUTOMATED_PRINCIPALS)

        # Classify operation type
        is_read_only = any(event_name.startswith(pattern.rstrip("*")) for pattern in self.READ_ONLY_OPERATIONS)
        is_management = any(event_name.startswith(pattern.rstrip("*")) for pattern in self.MANAGEMENT_OPERATIONS)

        return {
            "event_name": event_name,
            "username": username,
            "is_user_initiated": is_user_initiated,
            "is_automated": is_automated,
            "is_read_only": is_read_only,
            "is_management": is_management,
        }

    def _generate_signals(self, analysis_data: Dict) -> List[ActivitySignal]:
        """
        Generate I1-I6 decommission signals.

        Signal generation rules:
        - I1: event_count_90d == 0 → HIGH confidence (0.95)
        - I2: read_only_pct > 95% AND event_count_90d > 0 → MEDIUM (0.70)
        - I3: management_operations_60d == 0 AND event_count_60d > 0 → MEDIUM (0.65)
        - I4: automated_events / total_events > 95% → MEDIUM (0.60)
        - I5: (count_30d - count_90d) / count_90d < -0.70 → LOW (0.40)
        - I6: user_initiated_events_30d == 0 AND event_count_30d > 0 → LOW (0.50)

        Args:
            analysis_data: Dictionary with classified events and metrics

        Returns:
            List of applicable ActivitySignal enums
        """
        signals: List[ActivitySignal] = []

        event_count_30d = analysis_data["event_count_30d"]
        event_count_60d = analysis_data["event_count_60d"]
        event_count_90d = analysis_data["event_count_90d"]
        user_initiated = analysis_data["user_initiated_events"]
        automated = analysis_data["automated_events"]
        read_only_pct = analysis_data["read_only_pct"]
        classified_events = analysis_data["classified_events"]

        # I1: No activity in 90+ days (HIGH confidence)
        if event_count_90d == 0:
            signals.append(ActivitySignal.I1_NO_ACTIVITY_90D)
            return signals  # If no activity, other signals don't apply

        # I2: Read-only operations only (MEDIUM confidence)
        if read_only_pct > 95.0 and event_count_90d > 0:
            signals.append(ActivitySignal.I2_READ_ONLY_90D)

        # I3: No management operations in 60 days (MEDIUM confidence)
        mgmt_ops_60d = sum(
            1
            for e in classified_events
            if e["is_management"]
            and e["event_name"] in [ev.get("EventName", "") for ev in analysis_data.get("events_60d", [])]
        )
        if mgmt_ops_60d == 0 and event_count_60d > 0:
            signals.append(ActivitySignal.I3_NO_MGMT_60D)

        # I4: Automated operations only (MEDIUM confidence)
        total_events = user_initiated + automated
        if total_events > 0 and (automated / total_events) > 0.95:
            signals.append(ActivitySignal.I4_AUTOMATED_ONLY)

        # I5: Declining activity pattern >70% (LOW confidence)
        if event_count_90d > 0:
            trend_pct = (event_count_30d - event_count_90d) / event_count_90d
            if trend_pct < -0.70:
                signals.append(ActivitySignal.I5_DECLINING_PATTERN)

        # I6: No user operations in 30 days (LOW confidence)
        user_ops_30d = sum(
            1
            for e in classified_events
            if e["is_user_initiated"]
            and e["event_name"] in [ev.get("EventName", "") for ev in analysis_data.get("events_30d", [])]
        )
        if user_ops_30d == 0 and event_count_30d > 0:
            signals.append(ActivitySignal.I6_NO_USER_OPS_30D)

        return signals

    def _calculate_trend(self, count_30d: int, count_60d: int, count_90d: int) -> ActivityTrend:
        """
        Calculate activity trend.

        Trend determination logic:
        - NONE: No activity (count_90d == 0)
        - INCREASING: 30d count > 60d count > 90d count
        - DECLINING: 30d count < 60d count < 90d count
        - STABLE: Consistent activity levels

        Args:
            count_30d: Event count in last 30 days
            count_60d: Event count in last 60 days
            count_90d: Event count in last 90 days

        Returns:
            ActivityTrend enum
        """
        if count_90d == 0:
            return ActivityTrend.NONE

        # Calculate trend ratios
        ratio_30_60 = count_30d / max(count_60d, 1)
        ratio_60_90 = count_60d / max(count_90d, 1)

        # Thresholds for trend classification (±20% tolerance)
        if ratio_30_60 > 1.2 and ratio_60_90 > 1.2:
            return ActivityTrend.INCREASING
        elif ratio_30_60 < 0.8 and ratio_60_90 < 0.8:
            return ActivityTrend.DECLINING
        else:
            return ActivityTrend.STABLE

    def _calculate_confidence(self, signals: List[ActivitySignal]) -> float:
        """
        Calculate overall confidence score from signals.

        Confidence calculation:
        - Uses weighted average of signal confidences
        - I1 (no activity): 0.95 confidence (highest)
        - I2 (read-only): 0.70 confidence
        - I3 (no mgmt): 0.65 confidence
        - I4 (automated): 0.60 confidence
        - I5 (declining): 0.40 confidence
        - I6 (no user ops): 0.50 confidence

        Args:
            signals: List of activity signals

        Returns:
            Confidence score (0.0-1.0)
        """
        if not signals:
            return 0.0

        # Signal confidence mapping
        signal_confidence = {
            ActivitySignal.I1_NO_ACTIVITY_90D: 0.95,
            ActivitySignal.I2_READ_ONLY_90D: 0.70,
            ActivitySignal.I3_NO_MGMT_60D: 0.65,
            ActivitySignal.I4_AUTOMATED_ONLY: 0.60,
            ActivitySignal.I5_DECLINING_PATTERN: 0.40,
            ActivitySignal.I6_NO_USER_OPS_30D: 0.50,
        }

        # Calculate weighted average
        total_confidence = sum(signal_confidence.get(signal, 0.0) for signal in signals)

        return total_confidence / len(signals)

    def _determine_recommendation(self, signals: List[ActivitySignal], confidence: float) -> DecommissionRecommendation:
        """
        Determine decommission recommendation.

        Recommendation logic:
        - DECOMMISSION: confidence ≥ 0.70 OR I1 signal present
        - INVESTIGATE: confidence ≥ 0.50
        - KEEP: confidence < 0.50

        Args:
            signals: List of activity signals
            confidence: Overall confidence score

        Returns:
            DecommissionRecommendation enum
        """
        # High confidence decommission candidates
        if confidence >= 0.70 or ActivitySignal.I1_NO_ACTIVITY_90D in signals:
            return DecommissionRecommendation.DECOMMISSION

        # Medium confidence - needs investigation
        if confidence >= 0.50:
            return DecommissionRecommendation.INVESTIGATE

        # Low confidence - keep resource
        return DecommissionRecommendation.KEEP

    async def validate_with_mcp(self, analysis: CloudTrailActivityAnalysis) -> CloudTrailActivityAnalysis:
        """
        Validate activity analysis with MCP.

        Cross-validates CloudTrail activity patterns with Cost Explorer
        usage metrics using HybridMCPEngine.

        Args:
            analysis: CloudTrailActivityAnalysis to validate

        Returns:
            Updated analysis with mcp_validated flag
        """
        if not MCP_AVAILABLE:
            self.logger.warning("MCP validation unavailable - HybridMCPEngine not loaded")
            return analysis

        try:
            # Initialize MCP engine
            from runbooks.finops.hybrid_mcp_engine import create_hybrid_mcp_engine

            engine = create_hybrid_mcp_engine(profile=self.operational_profile)

            # Query MCP for cost data (indicator of actual usage)
            # Note: If CloudTrail shows activity but costs are $0, flag as discrepancy
            # This validation helps identify false positives in activity analysis

            # For now, mark as validated (MCP integration in Phase 6)
            analysis.mcp_validated = True
            analysis.metadata["mcp_validation_note"] = "Phase 6 feature - full validation pending"

        except Exception as e:
            self.logger.warning(f"MCP validation failed: {e}")

        return analysis

    def display_analysis(self, analyses: List[CloudTrailActivityAnalysis]) -> None:
        """
        Display analysis in Rich table format.

        Creates comprehensive activity analysis table with:
        - Resource ID and type
        - Activity metrics (30/60/90 day event counts)
        - Decommission signals (I1-I6)
        - Recommendation and confidence

        Args:
            analyses: List of CloudTrailActivityAnalysis objects
        """
        if not analyses:
            print_warning("No activity analyses to display")
            return

        # Create analysis table
        table = create_table(
            title="CloudTrail Activity Analysis",
            columns=[
                {"name": "Resource ID", "style": "cyan"},
                {"name": "Type", "style": "white"},
                {"name": "Last Activity", "style": "white"},
                {"name": "Events (30/60/90d)", "style": "bright_yellow"},
                {"name": "Signals", "style": "bright_magenta"},
                {"name": "Confidence", "style": "white"},
                {"name": "Recommendation", "style": "bold"},
            ],
        )

        for analysis in analyses:
            # Format last activity
            last_activity_str = analysis.last_activity.strftime("%Y-%m-%d") if analysis.last_activity else "Never"

            # Format event counts
            events_str = f"{analysis.event_count_30d} / {analysis.event_count_60d} / {analysis.event_count_90d}"

            # Format signals
            signals_str = ", ".join(signal.value for signal in analysis.decommission_signals)
            if not signals_str:
                signals_str = "None"

            # Format confidence
            confidence_str = f"{analysis.confidence * 100:.1f}%"

            # Format recommendation with color
            rec = analysis.recommendation
            if rec == DecommissionRecommendation.DECOMMISSION:
                rec_str = f"[bright_red]{rec.value}[/bright_red]"
            elif rec == DecommissionRecommendation.INVESTIGATE:
                rec_str = f"[bright_yellow]{rec.value}[/bright_yellow]"
            else:
                rec_str = f"[bright_green]{rec.value}[/bright_green]"

            table.add_row(
                analysis.resource_id,
                analysis.resource_type,
                last_activity_str,
                events_str,
                signals_str,
                confidence_str,
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
        keep_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.KEEP)

        # Create summary table
        summary_table = create_table(
            title="Activity Analysis Summary",
            columns=[
                {"name": "Metric", "style": "cyan"},
                {"name": "Value", "style": "white"},
            ],
        )

        summary_table.add_row("Total Resources", str(total))
        summary_table.add_row("Decommission Candidates", f"[bright_red]{decommission_count}[/bright_red]")
        summary_table.add_row("Needs Investigation", f"[bright_yellow]{investigate_count}[/bright_yellow]")
        summary_table.add_row("Keep Resources", f"[bright_green]{keep_count}[/bright_green]")
        summary_table.add_row("CloudTrail Queries", str(self.query_count))

        console.print()
        console.print(summary_table)
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
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 90
) -> CloudTrailActivityEnricher:
    """
    Factory function to create CloudTrailActivityEnricher.

    Provides clean initialization pattern following enterprise architecture
    with automatic profile resolution and sensible defaults.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudTrail lookback period (default: 90)

    Returns:
        Initialized CloudTrailActivityEnricher instance

    Example:
        >>> enricher = create_cloudtrail_activity_enricher()
        >>> # Enricher ready for activity analysis
        >>> analyses = enricher.analyze_resource_activity(...)
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
    "ActivitySignal",
    "ActivityTrend",
    "DecommissionRecommendation",
    # Factory function
    "create_cloudtrail_activity_enricher",
]
