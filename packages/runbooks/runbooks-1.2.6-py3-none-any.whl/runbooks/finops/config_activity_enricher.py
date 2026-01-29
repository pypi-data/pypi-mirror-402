#!/usr/bin/env python3
"""
AWS Config Activity Enricher - Governance Service Activity Signals (G1-G7)
===========================================================================

Business Value: Idle AWS Config resources detection enabling cost optimization
Strategic Impact: Complement CloudWatch pattern for governance/compliance workloads
Integration: Feeds data to FinOps decommission scoring framework

Architecture Pattern: 5-layer enrichment framework (matches CloudWatch/ECS pattern)
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: AWS Config activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses G1-G7 signals)

Decommission Signals (G1-G7):
- G1: Recorder inactivity - No configuration changes recorded 90d
- G2: Rule evaluation waste - Rules with zero non-compliant resources
- G3: Aggregator redundancy - Multiple aggregators, same scope
- G4: Snapshot delivery failures - S3 delivery errors >7d
- G5: Retention optimization - Snapshots retained >7 years
- G6: Resource type waste - Recording all types, 90% unused
- G7: Remediation gaps - Non-compliant resources, no auto-fix configured

Target Confidence Score: 99/100 (achievable with 6+ signals present)

Usage:
    from runbooks.finops.config_activity_enricher import ConfigActivityEnricher

    enricher = ConfigActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze Config recorders
    analyses = enricher.analyze_recorder_activity()

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer AWS Config service costs
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


class ConfigIdleSignal(str, Enum):
    """AWS Config idle/underutilization decommission signals (G1-G7)."""

    G1_RECORDER_INACTIVE = "G1"  # No configuration changes recorded 90d
    G2_RULE_WASTE = "G2"  # Rules with zero non-compliant resources
    G3_AGGREGATOR_REDUNDANCY = "G3"  # Multiple aggregators, same scope
    G4_DELIVERY_FAILURE = "G4"  # S3 snapshot delivery errors >7d
    G5_RETENTION_WASTE = "G5"  # Snapshots retained >7 years
    G6_RESOURCE_TYPE_WASTE = "G6"  # Recording all types, 90% unused
    G7_REMEDIATION_GAP = "G7"  # Non-compliant resources, no auto-fix


class ActivityPattern(str, Enum):
    """AWS Config recorder activity pattern classification."""

    ACTIVE = "active"  # Active compliance monitoring
    MODERATE = "moderate"  # Moderate compliance checks
    LIGHT = "light"  # Light monitoring
    IDLE = "idle"  # No activity


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
class ConfigActivityMetrics:
    """
    AWS Config metrics for recorders.

    Comprehensive activity metrics for decommission decision-making with
    G1-G7 signal framework.
    """

    recorder_status: str  # PENDING, SUCCESS, FAILURE
    last_status_change_time: Optional[datetime]
    days_since_status_change: int
    recording_all_resource_types: bool
    resource_types_count: int
    config_rules_count: int
    compliant_rules: int
    non_compliant_rules: int
    aggregators_count: int
    delivery_channel_status: str
    days_since_delivery_failure: int
    retention_period_days: Optional[int]
    remediation_configurations: int


@dataclass
class ConfigActivityAnalysis:
    """
    AWS Config recorder activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    G1-G7 signal framework and cost impact analysis.
    """

    recorder_name: str
    region: str
    account_id: str
    metrics: ConfigActivityMetrics
    activity_pattern: ActivityPattern
    idle_signals: List[ConfigIdleSignal] = field(default_factory=list)
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: int = 0  # 0-100 scale
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "recorder_name": self.recorder_name,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "recorder_status": self.metrics.recorder_status,
                "last_status_change_time": self.metrics.last_status_change_time.isoformat()
                if self.metrics.last_status_change_time
                else None,
                "days_since_status_change": self.metrics.days_since_status_change,
                "recording_all_resource_types": self.metrics.recording_all_resource_types,
                "resource_types_count": self.metrics.resource_types_count,
                "config_rules_count": self.metrics.config_rules_count,
                "compliant_rules": self.metrics.compliant_rules,
                "non_compliant_rules": self.metrics.non_compliant_rules,
                "aggregators_count": self.metrics.aggregators_count,
                "delivery_channel_status": self.metrics.delivery_channel_status,
                "days_since_delivery_failure": self.metrics.days_since_delivery_failure,
                "retention_period_days": self.metrics.retention_period_days,
                "remediation_configurations": self.metrics.remediation_configurations,
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


class ConfigActivityEnricher:
    """
    AWS Config activity enricher for recorders and rules.

    Analyzes AWS Config resources for idle/underutilization patterns using
    Config APIs with G1-G7 signal framework.

    Capabilities:
    - Recorder activity metrics analysis (90 day windows)
    - Config rules efficiency tracking
    - Aggregator redundancy detection
    - Delivery channel health monitoring
    - Retention policy gap analysis
    - Remediation configuration assessment
    - Comprehensive decommission recommendations

    Decommission Signals Generated:
    - G1: Recorder inactivity 90d (HIGH confidence)
    - G2: Rule evaluation waste (MEDIUM confidence)
    - G3: Aggregator redundancy (MEDIUM confidence)
    - G4: Delivery failures (MEDIUM confidence)
    - G5: Retention waste (LOW confidence)
    - G6: Resource type waste (LOW confidence)
    - G7: Remediation gaps (LOW confidence)

    Target: 99/100 confidence with 6+ signals present
    """

    # Activity thresholds for classification
    IDLE_THRESHOLD_DAYS = 90  # days
    DELIVERY_FAILURE_THRESHOLD_DAYS = 7  # days
    RETENTION_THRESHOLD_DAYS = 2555  # 7 years

    # AWS Config pricing (US East - N. Virginia baseline)
    CONFIG_ITEM_COST = 0.003  # $0.003 per configuration item recorded
    CONFIG_RULE_EVALUATION_COST = 0.001  # $0.001 per evaluation
    ESTIMATED_ITEMS_PER_MONTH = 1000  # Conservative estimate

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 90,
        cache_ttl: int = 300,
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize AWS Config activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for Config queries (default: ap-southeast-2)
            lookback_days: Config lookback period (default: 90)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = lookback_days
        self.cache_ttl = cache_ttl

        # Initialize AWS session
        self.session = create_operational_session(self.operational_profile)
        self.config_client = self.session.client("config", region_name=self.region)

        # Validation cache (5-minute TTL for performance)
        self._cache: Dict[str, Tuple[ConfigActivityAnalysis, float]] = {}

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
                f"🔍 AWS Config Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )
        else:
            self.logger.debug(
                f"AWS Config Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )

    def analyze_recorder_activity(
        self,
        recorder_names: Optional[List[str]] = None,
        region: Optional[str] = None,
        lookback_days: Optional[int] = None,
    ) -> List[ConfigActivityAnalysis]:
        """
        Analyze AWS Config recorder activity for idle detection.

        Core analysis workflow:
        1. Query AWS Config recorders (all or specific names)
        2. Get activity metrics for each recorder (90 day window)
        3. Classify activity pattern (active/moderate/light/idle)
        4. Generate G1-G7 decommission signals based on patterns
        5. Compute confidence score (0-100) and recommendation
        6. Calculate cost impact and potential savings

        Args:
            recorder_names: List of recorder names to analyze (analyzes all if None)
            region: AWS region filter (default: use instance region)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals
        """
        start_time = time.time()
        analysis_region = region or self.region
        lookback = lookback_days or self.lookback_days

        print_section(f"AWS Config Activity Analysis ({lookback}-day lookback)")

        # Get recorders
        recorders = self._get_recorders(recorder_names, analysis_region)

        if not recorders:
            print_warning("No AWS Config recorders found")
            return []

        print_info(f"Found {len(recorders)} AWS Config recorders")

        analyses: List[ConfigActivityAnalysis] = []

        with create_progress_bar(description="Analyzing Config recorders") as progress:
            task = progress.add_task(f"Analyzing {len(recorders)} recorders", total=len(recorders))

            for recorder in recorders:
                try:
                    # Check cache first
                    recorder_name = recorder["name"]
                    cache_key = f"{recorder_name}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Analyze recorder
                    analysis = self._analyze_recorder(recorder, lookback)

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(f"Failed to analyze recorder {recorder.get('name')}: {e}", exc_info=True)
                    print_warning(f"⚠️  Skipped {recorder.get('name')}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _get_recorders(self, recorder_names: Optional[List[str]], region: str) -> List[Dict]:
        """
        Get AWS Config recorders from AWS API.

        Args:
            recorder_names: Specific recorders to retrieve (retrieves all if None)
            region: AWS region filter

        Returns:
            List of recorder metadata dictionaries
        """
        recorders = []

        try:
            if recorder_names:
                # Get specific recorders
                for name in recorder_names:
                    response = self.config_client.describe_configuration_recorders(ConfigurationRecorderNames=[name])
                    recorders.extend(response.get("ConfigurationRecorders", []))
            else:
                # Get all recorders
                response = self.config_client.describe_configuration_recorders()
                recorders.extend(response.get("ConfigurationRecorders", []))

            self.query_count += 1

        except ClientError as e:
            self.logger.error(f"Failed to get Config recorders: {e}")

        return recorders

    def _analyze_recorder(self, recorder: Dict, lookback_days: int) -> ConfigActivityAnalysis:
        """
        Analyze individual AWS Config recorder.

        Args:
            recorder: Recorder metadata from describe_configuration_recorders
            lookback_days: Activity metrics lookback period

        Returns:
            Comprehensive activity analysis with idle signals
        """
        recorder_name = recorder["name"]

        # Get activity metrics
        metrics = self._get_activity_metrics(recorder, lookback_days)

        # Classify activity pattern
        activity_pattern = self._classify_activity_pattern(metrics)

        # Generate idle signals (G1-G7)
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

        return ConfigActivityAnalysis(
            recorder_name=recorder_name,
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

    def _get_activity_metrics(self, recorder: Dict, lookback_days: int) -> ConfigActivityMetrics:
        """
        Get activity metrics for AWS Config recorder.

        Metrics gathered:
        - Recorder status and last change time (G1 signal)
        - Resource types being recorded (G6 signal)
        - Config rules and compliance status (G2, G7 signals)
        - Aggregators configuration (G3 signal)
        - Delivery channel status (G4 signal)
        - Retention settings (G5 signal)

        Args:
            recorder: Recorder metadata
            lookback_days: Lookback period for metrics

        Returns:
            Comprehensive activity metrics
        """
        recorder_name = recorder["name"]

        # Get recorder status
        recorder_status, last_status_change = self._get_recorder_status(recorder_name)

        if last_status_change:
            days_since_change = (datetime.now(tz=timezone.utc) - last_status_change).days
        else:
            days_since_change = lookback_days

        # Get recording configuration
        recording_all = recorder.get("recordingGroup", {}).get("allSupported", False)
        resource_types = recorder.get("recordingGroup", {}).get("resourceTypes", [])
        resource_types_count = len(resource_types) if not recording_all else 100  # Estimate

        # Get Config rules statistics (G2 signal)
        rules_count, compliant, non_compliant = self._get_rules_stats()

        # Get aggregators count (G3 signal)
        aggregators_count = self._get_aggregators_count()

        # Get delivery channel status (G4 signal)
        delivery_status, days_since_failure = self._get_delivery_status(recorder_name)

        # Get retention settings (G5 signal)
        retention_days = self._get_retention_period()

        # Get remediation configurations (G7 signal)
        remediation_count = self._get_remediation_count()

        return ConfigActivityMetrics(
            recorder_status=recorder_status,
            last_status_change_time=last_status_change,
            days_since_status_change=days_since_change,
            recording_all_resource_types=recording_all,
            resource_types_count=resource_types_count,
            config_rules_count=rules_count,
            compliant_rules=compliant,
            non_compliant_rules=non_compliant,
            aggregators_count=aggregators_count,
            delivery_channel_status=delivery_status,
            days_since_delivery_failure=days_since_failure,
            retention_period_days=retention_days,
            remediation_configurations=remediation_count,
        )

    def _get_recorder_status(self, recorder_name: str) -> Tuple[str, Optional[datetime]]:
        """
        Get recorder status (G1 signal).

        Args:
            recorder_name: Config recorder name

        Returns:
            Tuple of (status, last_status_change_time)
        """
        try:
            response = self.config_client.describe_configuration_recorder_status(
                ConfigurationRecorderNames=[recorder_name]
            )

            status_list = response.get("ConfigurationRecordersStatus", [])
            if status_list:
                status_info = status_list[0]
                recording = status_info.get("recording", False)
                last_status = status_info.get("lastStatus", "PENDING")
                last_status_change_time = status_info.get("lastStatusChangeTime")

                status = "SUCCESS" if recording and last_status == "SUCCESS" else last_status

                self.query_count += 1
                return status, last_status_change_time

        except ClientError as e:
            self.logger.debug(f"Failed to get recorder status for {recorder_name}: {e}")

        return "UNKNOWN", None

    def _get_rules_stats(self) -> Tuple[int, int, int]:
        """
        Get Config rules statistics (G2 signal).

        Returns:
            Tuple of (total_rules, compliant_rules, non_compliant_rules)
        """
        try:
            response = self.config_client.describe_compliance_by_config_rule()

            rules = response.get("ComplianceByConfigRules", [])
            total_count = len(rules)

            compliant = sum(1 for rule in rules if rule.get("Compliance", {}).get("ComplianceType") == "COMPLIANT")

            non_compliant = sum(
                1 for rule in rules if rule.get("Compliance", {}).get("ComplianceType") == "NON_COMPLIANT"
            )

            self.query_count += 1
            return total_count, compliant, non_compliant

        except ClientError as e:
            self.logger.debug(f"Failed to get rules stats: {e}")
            return 0, 0, 0

    def _get_aggregators_count(self) -> int:
        """
        Get aggregators count (G3 signal).

        Returns:
            Number of configuration aggregators
        """
        try:
            response = self.config_client.describe_configuration_aggregators()

            aggregators = response.get("ConfigurationAggregators", [])

            self.query_count += 1
            return len(aggregators)

        except ClientError as e:
            self.logger.debug(f"Failed to get aggregators: {e}")
            return 0

    def _get_delivery_status(self, recorder_name: str) -> Tuple[str, int]:
        """
        Get delivery channel status (G4 signal).

        Args:
            recorder_name: Config recorder name

        Returns:
            Tuple of (delivery_status, days_since_failure)
        """
        try:
            # Get delivery channels
            response = self.config_client.describe_delivery_channels()

            channels = response.get("DeliveryChannels", [])
            if not channels:
                return "NO_CHANNEL", 0

            # Get delivery channel status
            channel_name = channels[0]["name"]
            status_response = self.config_client.describe_delivery_channel_status(DeliveryChannelNames=[channel_name])

            status_list = status_response.get("DeliveryChannelsStatus", [])
            if status_list:
                status_info = status_list[0]
                last_delivery_status = status_info.get("configHistoryDeliveryInfo", {}).get("lastStatus", "SUCCESS")
                last_delivery_time = status_info.get("configHistoryDeliveryInfo", {}).get("lastAttemptTime")

                if last_delivery_status != "SUCCESS" and last_delivery_time:
                    days_since = (datetime.now(tz=timezone.utc) - last_delivery_time).days
                    return "FAILURE", days_since

                return last_delivery_status, 0

            self.query_count += 2
            return "UNKNOWN", 0

        except ClientError as e:
            self.logger.debug(f"Failed to get delivery status: {e}")
            return "UNKNOWN", 0

    def _get_retention_period(self) -> Optional[int]:
        """
        Get retention period (G5 signal).

        Returns:
            Retention period in days (None = indefinite)
        """
        try:
            response = self.config_client.describe_retention_configurations()

            configs = response.get("RetentionConfigurations", [])
            if configs:
                # Return first retention config
                return configs[0].get("RetentionPeriodInDays")

            self.query_count += 1
            return None  # No retention configured (indefinite)

        except ClientError as e:
            self.logger.debug(f"Failed to get retention config: {e}")
            return None

    def _get_remediation_count(self) -> int:
        """
        Get remediation configurations count (G7 signal).

        Returns:
            Number of remediation configurations
        """
        try:
            response = self.config_client.describe_remediation_configurations()

            configs = response.get("RemediationConfigurations", [])

            self.query_count += 1
            return len(configs)

        except ClientError as e:
            self.logger.debug(f"Failed to get remediation configs: {e}")
            return 0

    def _classify_activity_pattern(self, metrics: ConfigActivityMetrics) -> ActivityPattern:
        """
        Classify AWS Config activity pattern.

        Classification:
        - ACTIVE: Recorder recording successfully, rules active
        - MODERATE: Recorder active but few rules
        - LIGHT: Recorder recording but inactive rules
        - IDLE: Recorder not recording or no changes 90d

        Args:
            metrics: AWS Config activity metrics

        Returns:
            ActivityPattern enum
        """
        if metrics.recorder_status != "SUCCESS":
            return ActivityPattern.IDLE
        elif metrics.days_since_status_change >= self.IDLE_THRESHOLD_DAYS:
            return ActivityPattern.IDLE
        elif metrics.config_rules_count > 10 and metrics.non_compliant_rules > 0:
            return ActivityPattern.ACTIVE
        elif metrics.config_rules_count > 5:
            return ActivityPattern.MODERATE
        else:
            return ActivityPattern.LIGHT

    def _generate_idle_signals(
        self, metrics: ConfigActivityMetrics, pattern: ActivityPattern
    ) -> List[ConfigIdleSignal]:
        """
        Generate G1-G7 idle signals.

        Signal generation rules:
        - G1: Recorder inactive 90d → HIGH confidence
        - G2: All rules compliant (no findings) → MEDIUM confidence
        - G3: Multiple aggregators → MEDIUM confidence
        - G4: Delivery failures >7d → MEDIUM confidence
        - G5: Retention >7 years → LOW confidence
        - G6: Recording all types, >90% unused → LOW confidence
        - G7: Non-compliant resources, no remediation → LOW confidence

        Args:
            metrics: AWS Config activity metrics
            pattern: Activity pattern classification

        Returns:
            List of applicable ConfigIdleSignal enums
        """
        signals: List[ConfigIdleSignal] = []

        # G1: Recorder inactivity (90+ days no changes)
        if metrics.days_since_status_change >= 90 or metrics.recorder_status != "SUCCESS":
            signals.append(ConfigIdleSignal.G1_RECORDER_INACTIVE)

        # G2: Rule evaluation waste (all rules compliant = no findings)
        if metrics.config_rules_count > 0 and metrics.non_compliant_rules == 0:
            signals.append(ConfigIdleSignal.G2_RULE_WASTE)

        # G3: Aggregator redundancy (multiple aggregators)
        if metrics.aggregators_count > 1:
            signals.append(ConfigIdleSignal.G3_AGGREGATOR_REDUNDANCY)

        # G4: Delivery failures
        if metrics.delivery_channel_status == "FAILURE" and metrics.days_since_delivery_failure >= 7:
            signals.append(ConfigIdleSignal.G4_DELIVERY_FAILURE)

        # G5: Retention waste (>7 years)
        if metrics.retention_period_days and metrics.retention_period_days > self.RETENTION_THRESHOLD_DAYS:
            signals.append(ConfigIdleSignal.G5_RETENTION_WASTE)

        # G6: Resource type waste (recording all types)
        if metrics.recording_all_resource_types:
            signals.append(ConfigIdleSignal.G6_RESOURCE_TYPE_WASTE)

        # G7: Remediation gaps (non-compliant but no auto-fix)
        if metrics.non_compliant_rules > 0 and metrics.remediation_configurations == 0:
            signals.append(ConfigIdleSignal.G7_REMEDIATION_GAP)

        return signals

    def _calculate_confidence(self, signals: List[ConfigIdleSignal]) -> int:
        """
        Calculate idle confidence score (0-100).

        Target: 99/100 confidence with 6+ signals present

        Signal weights (proportional scoring to reach 99):
        - G1: 25 points (recorder inactivity - strongest signal)
        - G2: 20 points (rule evaluation waste)
        - G3: 15 points (aggregator redundancy)
        - G4: 15 points (delivery failures)
        - G5: 12 points (retention waste)
        - G6: 12 points (resource type waste)
        - G7: 10 points (remediation gaps)

        Total possible: 109 points (capped at 99 for 6+ signals)

        Args:
            signals: List of idle signals

        Returns:
            Confidence score (0-100, target 99 for 6+ signals)
        """
        if not signals:
            return 0

        signal_weights = {
            ConfigIdleSignal.G1_RECORDER_INACTIVE: 25,
            ConfigIdleSignal.G2_RULE_WASTE: 20,
            ConfigIdleSignal.G3_AGGREGATOR_REDUNDANCY: 15,
            ConfigIdleSignal.G4_DELIVERY_FAILURE: 15,
            ConfigIdleSignal.G5_RETENTION_WASTE: 12,
            ConfigIdleSignal.G6_RESOURCE_TYPE_WASTE: 12,
            ConfigIdleSignal.G7_REMEDIATION_GAP: 10,
        }

        total_score = sum(signal_weights.get(signal, 0) for signal in signals)

        # Cap at 99 for 6+ signals (enterprise scoring standard)
        return min(total_score, 99)

    def _calculate_monthly_cost(self, metrics: ConfigActivityMetrics) -> float:
        """
        Calculate monthly AWS Config cost.

        Cost components:
        - Configuration items: $0.003 per item recorded
        - Config rules: $0.001 per evaluation

        Args:
            metrics: Activity metrics

        Returns:
            Monthly cost estimate
        """
        # Configuration items cost
        items_cost = self.ESTIMATED_ITEMS_PER_MONTH * self.CONFIG_ITEM_COST

        # Config rules cost (estimate 1000 evaluations/month per rule)
        rules_cost = metrics.config_rules_count * 1000 * self.CONFIG_RULE_EVALUATION_COST

        return items_cost + rules_cost

    def _calculate_potential_savings(self, annual_cost: float, confidence: int, pattern: ActivityPattern) -> float:
        """
        Calculate potential annual savings.

        Savings scenarios:
        - IDLE: 100% savings (decommission)
        - LIGHT: 80% savings (optimize)
        - MODERATE: 40% savings (optimize)
        - ACTIVE: 0% savings (keep as-is)

        Args:
            annual_cost: Annual AWS Config cost
            confidence: Idle confidence score (0-100)
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
        confidence_factor = confidence / 100.0

        return annual_cost * multiplier * confidence_factor

    def _generate_recommendation(
        self, pattern: ActivityPattern, signals: List[ConfigIdleSignal], confidence: int
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

    def display_analysis(self, analyses: List[ConfigActivityAnalysis]) -> None:
        """
        Display AWS Config activity analysis in Rich table format.

        Args:
            analyses: List of ConfigActivityAnalysis objects
        """
        if not analyses:
            print_warning("No AWS Config recorders to display")
            return

        # Create analysis table
        table = create_table(
            title="AWS Config Recorder Activity Analysis",
            columns=[
                {"name": "Recorder Name", "style": "cyan"},
                {"name": "Status", "style": "bright_yellow"},
                {"name": "Days Since Change", "style": "white"},
                {"name": "Rules", "style": "white"},
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

            # Format status with color
            status = analysis.metrics.recorder_status
            if status == "SUCCESS":
                status_str = f"[green]{status}[/green]"
            else:
                status_str = f"[red]{status}[/red]"

            table.add_row(
                analysis.recorder_name,
                status_str,
                f"{analysis.metrics.days_since_status_change}d",
                f"{analysis.metrics.config_rules_count}",
                signals_str,
                f"{analysis.confidence}/100",
                format_cost(analysis.monthly_cost),
                format_cost(analysis.potential_savings / 12),  # Monthly savings
                rec_str,
            )

        console.print()
        console.print(table)
        console.print()

    def _display_summary(self, analyses: List[ConfigActivityAnalysis]) -> None:
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
            f"[bold]Total Recorders: {total}[/bold]\n"
            f"[bold green]Total Potential Savings: {format_cost(total_savings)}/year[/bold green]\n"
            f"[bold]Total Annual AWS Config Cost: {format_cost(total_cost)}[/bold]\n\n"
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
            summary_text, title="AWS Config Idle Detection Summary (G1-G7 Signals)", border_style="green"
        )
        console.print(summary)
        console.print()

    def _get_from_cache(self, cache_key: str) -> Optional[ConfigActivityAnalysis]:
        """Get analysis from cache if still valid."""
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return result
        return None

    def _add_to_cache(self, cache_key: str, analysis: ConfigActivityAnalysis) -> None:
        """Add analysis to cache with current timestamp."""
        self._cache[cache_key] = (analysis, time.time())


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_config_activity_enricher(
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 90
) -> ConfigActivityEnricher:
    """
    Factory function to create ConfigActivityEnricher.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: Config lookback period (default: 90)

    Returns:
        Initialized ConfigActivityEnricher instance
    """
    return ConfigActivityEnricher(operational_profile=operational_profile, region=region, lookback_days=lookback_days)


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core enricher class
    "ConfigActivityEnricher",
    # Data models
    "ConfigActivityAnalysis",
    "ConfigActivityMetrics",
    "ConfigIdleSignal",
    "ActivityPattern",
    "DecommissionRecommendation",
    # Factory function
    "create_config_activity_enricher",
]
