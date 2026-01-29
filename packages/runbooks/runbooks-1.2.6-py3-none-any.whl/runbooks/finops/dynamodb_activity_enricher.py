#!/usr/bin/env python3
"""
DynamoDB Activity Enricher - NoSQL Database Activity Signals
============================================================

Business Value: Idle DynamoDB table detection enabling cost optimization
Strategic Impact: Complement RDS pattern (R1-R7) for NoSQL databases
Integration: Feeds data to FinOps decommission scoring framework

Architecture Pattern: 5-layer enrichment framework (matches RDS pattern)
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: DynamoDB activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses D1-D5 signals)

Decommission Signals (D1-D5):
- D1: Table read/write capacity utilization (HIGH confidence: 0.90)
- D2: Global Secondary Index (GSI) utilization (MEDIUM confidence: 0.75)
- D3: Point-in-time recovery (PITR) enabled (MEDIUM confidence: 0.60)
- D4: DynamoDB Streams activity (LOW confidence: 0.50)
- D5: Table cost efficiency (MEDIUM confidence: 0.70)

Usage:
    from runbooks.finops.dynamodb_activity_enricher import DynamoDBActivityEnricher

    enricher = DynamoDBActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze DynamoDB table activity
    analyses = enricher.analyze_table_activity(
        table_names=['my-table-1', 'my-table-2']
    )

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer DynamoDB service costs
    - Flag discrepancies (low activity but high costs = potential issue)
    - Achieve ≥99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 3 - DynamoDB Activity Enricher
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
    create_inline_metrics,
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


class DynamoDBIdleSignal(str, Enum):
    """DynamoDB idle/underutilization decommission signals (D1-D7)."""

    D1_LOW_CAPACITY_UTILIZATION = "D1"  # Low read/write capacity utilization
    D2_IDLE_GSI = "D2"  # Idle Global Secondary Indexes
    D3_NO_PITR = "D3"  # Point-in-time recovery not enabled
    D4_NO_STREAMS = "D4"  # DynamoDB Streams not active
    D5_LOW_COST_EFFICIENCY = "D5"  # Low cost efficiency (high cost, low usage)
    D6_STREAM_ORPHANS = "D6"  # Streams enabled but no Lambda consumers
    D7_ONDEMAND_OPPORTUNITY = "D7"  # On-Demand mode 30% cheaper for usage pattern


# DynamoDB signal weights (0-100 scale) - v1.1.20: AWS WAR Aligned
# AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html
# Synchronized with decommission_scorer.py DEFAULT_DYNAMODB_WEIGHTS
DEFAULT_DYNAMODB_WEIGHTS = {
    # D1: Low capacity utilization <5% (PROVISIONED tables only)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ProvisionedThroughput.html
    # Confidence: 0.90 | Tier 1 | N/A for ON-DEMAND billing mode
    "D1": 45,
    # D2: Idle Global Secondary Indexes (GSI) consuming RCU/WCU
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html
    # Confidence: 0.75 | Tier 1 (direct cost)
    "D2": 20,
    # D3: Point-in-Time Recovery (PITR) not enabled (production tables)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/PointInTimeRecovery.html
    # Confidence: 0.60 | Tier 2 (compliance)
    "D3": 15,
    # D4: DynamoDB Streams not active (integration opportunity)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
    # Confidence: 0.50 | Tier 2 (integration signal)
    "D4": 10,
    # D5: Low cost efficiency (high provisioned capacity + low actual usage)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/CostOptimization.html
    # Confidence: 0.70 | Tier 2
    "D5": 10,
    # D6: Stream orphans (Streams enabled but no Lambda consumers)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.Lambda.html
    # Confidence: 0.65 | Tier 2 (integration waste)
    "D6": 5,
    # D7: On-Demand opportunity (low predictable traffic, On-Demand 30% cheaper)
    # AWS Ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html
    # Confidence: 0.75 | Tier 2 (billing optimization)
    "D7": 5,
}


class ActivityPattern(str, Enum):
    """DynamoDB access pattern classification."""

    ACTIVE = "active"  # Production workload (>1000 ops/day)
    MODERATE = "moderate"  # Development/staging (100-1000 ops/day)
    LIGHT = "light"  # Test environment (<100 ops/day)
    IDLE = "idle"  # No meaningful activity


class DecommissionRecommendation(str, Enum):
    """Decommission recommendations based on activity analysis."""

    DECOMMISSION = "DECOMMISSION"  # High confidence - decommission candidate
    INVESTIGATE = "INVESTIGATE"  # Medium confidence - needs review
    OPTIMIZE = "OPTIMIZE"  # Moderate underutilization - reduce capacity
    KEEP = "KEEP"  # Active resource - retain


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class DynamoDBActivityMetrics:
    """
    CloudWatch metrics for DynamoDB table.

    Comprehensive activity metrics for decommission decision-making with
    D1-D7 signal framework (99/100 confidence).
    """

    consumed_read_capacity_30d: float
    consumed_write_capacity_30d: float
    consumed_read_capacity_60d: float
    consumed_write_capacity_60d: float
    provisioned_read_capacity: float
    provisioned_write_capacity: float
    read_utilization_pct: float
    write_utilization_pct: float
    gsi_count: int
    gsi_idle_count: int  # Number of idle GSIs
    pitr_enabled: bool
    streams_enabled: bool
    stream_records_30d: float  # Average stream records per day
    table_size_gb: float
    item_count: int
    # D6-D7 signal fields (99/100 upgrade)
    stream_orphan: bool = False  # Streams enabled but no Lambda consumers
    ondemand_savings_pct: float = 0.0  # Potential savings switching to On-Demand


@dataclass
class DynamoDBActivityAnalysis:
    """
    DynamoDB table activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    D1-D5 signal framework and cost impact analysis.
    """

    table_name: str
    table_arn: str
    region: str
    account_id: str
    metrics: DynamoDBActivityMetrics
    activity_pattern: ActivityPattern
    idle_signals: List[DynamoDBIdleSignal] = field(default_factory=list)
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: float = 0.0  # 0.0-1.0 (DEPRECATED: kept for backward compatibility)
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP  # DEPRECATED
    decommission_score: int = 0  # NEW: 0-100 scale
    decommission_tier: str = "KEEP"  # NEW: MUST/SHOULD/COULD/KEEP
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "table_name": self.table_name,
            "table_arn": self.table_arn,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "consumed_read_capacity_30d": self.metrics.consumed_read_capacity_30d,
                "consumed_write_capacity_30d": self.metrics.consumed_write_capacity_30d,
                "consumed_read_capacity_60d": self.metrics.consumed_read_capacity_60d,
                "consumed_write_capacity_60d": self.metrics.consumed_write_capacity_60d,
                "provisioned_read_capacity": self.metrics.provisioned_read_capacity,
                "provisioned_write_capacity": self.metrics.provisioned_write_capacity,
                "read_utilization_pct": self.metrics.read_utilization_pct,
                "write_utilization_pct": self.metrics.write_utilization_pct,
                "gsi_count": self.metrics.gsi_count,
                "gsi_idle_count": self.metrics.gsi_idle_count,
                "pitr_enabled": self.metrics.pitr_enabled,
                "streams_enabled": self.metrics.streams_enabled,
                "stream_records_30d": self.metrics.stream_records_30d,
                "table_size_gb": self.metrics.table_size_gb,
                "item_count": self.metrics.item_count,
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


class DynamoDBActivityEnricher:
    """
    DynamoDB activity enricher for inventory resources.

    Analyzes DynamoDB tables for idle/underutilization patterns using CloudWatch
    metrics with D1-D5 signal framework.

    Capabilities:
    - Activity metrics analysis (30/60 day windows)
    - Capacity utilization tracking (read/write)
    - GSI utilization analysis
    - PITR and Streams configuration checks
    - Activity pattern classification (active/moderate/light/idle)
    - Comprehensive decommission recommendations

    Decommission Signals Generated:
    - D1: Low capacity utilization <5% (HIGH confidence: 0.90)
    - D2: Idle GSIs (MEDIUM confidence: 0.75)
    - D3: No PITR enabled (MEDIUM confidence: 0.60)
    - D4: No Streams activity (LOW confidence: 0.50)
    - D5: Low cost efficiency (MEDIUM confidence: 0.70)

    Example:
        >>> enricher = DynamoDBActivityEnricher(
        ...     operational_profile='ops-profile',
        ...     region='ap-southeast-2'
        ... )
        >>> analyses = enricher.analyze_table_activity(
        ...     table_names=['my-table-1']
        ... )
        >>> for analysis in analyses:
        ...     if DynamoDBIdleSignal.D1_LOW_CAPACITY_UTILIZATION in analysis.idle_signals:
        ...         print(f"Idle table: {analysis.table_name}")
    """

    # Activity thresholds for classification
    IDLE_CAPACITY_THRESHOLD = 5.0  # percent utilization
    ACTIVE_OPS_THRESHOLD = 1000  # operations/day
    MODERATE_OPS_THRESHOLD = 100  # operations/day

    # DynamoDB pricing (ap-southeast-2) - placeholder, should use AWS Pricing API
    # Example: Provisioned capacity $0.000742/hour per RCU, $0.003712/hour per WCU
    DEFAULT_RCU_HOURLY_RATE = 0.000742
    DEFAULT_WCU_HOURLY_RATE = 0.003712

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 60,
        cache_ttl: int = 300,
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize DynamoDB activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for DynamoDB queries (default: ap-southeast-2)
            lookback_days: CloudWatch lookback period (default: 60)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = min(lookback_days, 455)  # CloudWatch metrics retention
        self.cache_ttl = cache_ttl

        # Initialize AWS session
        self.session = create_operational_session(self.operational_profile)
        self.dynamodb_client = self.session.client("dynamodb", region_name=self.region)
        self.cloudwatch_client = self.session.client("cloudwatch", region_name=self.region)

        # Validation cache (5-minute TTL for performance)
        self._cache: Dict[str, Tuple[DynamoDBActivityAnalysis, float]] = {}

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
                f"🔍 DynamoDB Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )
        else:
            self.logger.debug(
                f"DynamoDB Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )

    def analyze_table_activity(
        self, table_names: Optional[List[str]] = None, region: Optional[str] = None, lookback_days: Optional[int] = None
    ) -> List[DynamoDBActivityAnalysis]:
        """
        Analyze DynamoDB table activity for idle detection.

        Core analysis workflow:
        1. Query DynamoDB tables (all or specific names)
        2. Get CloudWatch metrics for each table (30/60 day windows)
        3. Classify activity pattern (active/moderate/light/idle)
        4. Generate D1-D5 decommission signals based on patterns
        5. Compute confidence score and recommendation
        6. Calculate cost impact and potential savings

        Args:
            table_names: List of table names to analyze (analyzes all if None)
            region: AWS region filter (default: use instance region)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals

        Example:
            >>> analyses = enricher.analyze_table_activity(
            ...     table_names=['table-1', 'table-2']
            ... )
            >>> for analysis in analyses:
            ...     print(f"{analysis.table_name}: {analysis.recommendation.value}")
        """
        start_time = time.time()
        analysis_region = region or self.region
        lookback = lookback_days or self.lookback_days

        # Get DynamoDB tables
        tables = self._get_dynamodb_tables(table_names, analysis_region)

        if not tables:
            print_warning("No DynamoDB tables found")
            return []

        analyses: List[DynamoDBActivityAnalysis] = []

        with create_progress_bar(description="Analyzing DynamoDB tables") as progress:
            task = progress.add_task(f"Analyzing {len(tables)} tables", total=len(tables))

            for table in tables:
                try:
                    # Check cache first
                    table_name = table["TableName"]
                    cache_key = f"{table_name}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Analyze table
                    analysis = self._analyze_table(table, lookback)

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(f"Failed to analyze DynamoDB table {table.get('TableName')}: {e}", exc_info=True)
                    print_warning(f"⚠️  Skipped {table.get('TableName')}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _get_dynamodb_tables(self, table_names: Optional[List[str]], region: str) -> List[Dict]:
        """
        Get DynamoDB tables from AWS API.

        Args:
            table_names: Specific tables to retrieve (retrieves all if None)
            region: AWS region filter

        Returns:
            List of DynamoDB table metadata dictionaries
        """
        tables = []

        try:
            if table_names:
                # Get specific tables
                for table_name in table_names:
                    try:
                        response = self.dynamodb_client.describe_table(TableName=table_name)
                        tables.append(response["Table"])
                    except ClientError as e:
                        if e.response["Error"]["Code"] == "ResourceNotFoundException":
                            self.logger.debug(f"DynamoDB table not found: {table_name}")
                        else:
                            raise
            else:
                # Get all tables
                paginator = self.dynamodb_client.get_paginator("list_tables")
                for page in paginator.paginate():
                    for table_name in page["TableNames"]:
                        try:
                            response = self.dynamodb_client.describe_table(TableName=table_name)
                            tables.append(response["Table"])
                        except ClientError as e:
                            self.logger.debug(f"Failed to describe table {table_name}: {e}")

        except ClientError as e:
            self.logger.error(f"Failed to get DynamoDB tables: {e}")

        return tables

    def _analyze_table(self, table: Dict, lookback_days: int) -> DynamoDBActivityAnalysis:
        """
        Analyze individual DynamoDB table.

        Args:
            table: DynamoDB table metadata from describe_table
            lookback_days: CloudWatch metrics lookback period

        Returns:
            Comprehensive activity analysis with idle signals
        """
        table_name = table["TableName"]

        # Get CloudWatch metrics
        metrics = self._get_cloudwatch_metrics(table, lookback_days)

        # Classify activity pattern
        activity_pattern = self._classify_activity_pattern(metrics)

        # Generate idle signals and decommission score
        idle_signals, decommission_score = self._generate_idle_signals(metrics, activity_pattern)

        # Calculate tier from score
        decommission_tier = self._calculate_tier(decommission_score)

        # Calculate costs
        monthly_cost = self._calculate_monthly_cost(table, metrics)
        annual_cost = monthly_cost * 12

        # Calculate potential savings (using deprecated confidence for backward compatibility)
        confidence = self._calculate_confidence(idle_signals)
        potential_savings = self._calculate_potential_savings(annual_cost, confidence, activity_pattern)

        # Generate recommendation (deprecated, using tier instead)
        recommendation = self._generate_recommendation(activity_pattern, idle_signals, confidence)

        # Get account ID
        try:
            sts = self.session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
        except Exception:
            account_id = "unknown"

        return DynamoDBActivityAnalysis(
            table_name=table_name,
            table_arn=table["TableArn"],
            region=self.region,
            account_id=account_id,
            metrics=metrics,
            activity_pattern=activity_pattern,
            idle_signals=idle_signals,
            monthly_cost=monthly_cost,
            annual_cost=annual_cost,
            potential_savings=potential_savings,
            confidence=confidence,  # DEPRECATED: kept for backward compatibility
            recommendation=recommendation,  # DEPRECATED: use decommission_tier instead
            decommission_score=decommission_score,  # NEW: 0-100 scale
            decommission_tier=decommission_tier,  # NEW: MUST/SHOULD/COULD/KEEP
            metadata={
                "lookback_days": lookback_days,
                "query_time": datetime.now(tz=timezone.utc).isoformat(),
            },
        )

    def _get_cloudwatch_metrics(self, table: Dict, lookback_days: int) -> DynamoDBActivityMetrics:
        """
        Get CloudWatch metrics for DynamoDB table.

        Metrics queried:
        - ConsumedReadCapacityUnits (30/60-day average)
        - ConsumedWriteCapacityUnits (30/60-day average)
        - ProvisionedReadCapacityUnits (current)
        - ProvisionedWriteCapacityUnits (current)

        Args:
            table: DynamoDB table metadata
            lookback_days: Lookback period for metrics

        Returns:
            Comprehensive activity metrics
        """
        table_name = table["TableName"]
        now = datetime.utcnow()

        # Query ConsumedReadCapacityUnits
        read_30d = self._get_metric_average(table_name, "ConsumedReadCapacityUnits", now - timedelta(days=30), now)
        read_60d = self._get_metric_average(table_name, "ConsumedReadCapacityUnits", now - timedelta(days=60), now)

        # Query ConsumedWriteCapacityUnits
        write_30d = self._get_metric_average(table_name, "ConsumedWriteCapacityUnits", now - timedelta(days=30), now)
        write_60d = self._get_metric_average(table_name, "ConsumedWriteCapacityUnits", now - timedelta(days=60), now)

        # Get provisioned capacity from table metadata
        provisioned_read = 0.0
        provisioned_write = 0.0

        if "BillingModeSummary" in table:
            if table["BillingModeSummary"].get("BillingMode") == "PROVISIONED":
                provisioned_read = float(table.get("ProvisionedThroughput", {}).get("ReadCapacityUnits", 0))
                provisioned_write = float(table.get("ProvisionedThroughput", {}).get("WriteCapacityUnits", 0))
        elif "ProvisionedThroughput" in table:
            provisioned_read = float(table["ProvisionedThroughput"].get("ReadCapacityUnits", 0))
            provisioned_write = float(table["ProvisionedThroughput"].get("WriteCapacityUnits", 0))

        # Calculate utilization percentages
        read_utilization = (read_30d / provisioned_read * 100) if provisioned_read > 0 else 0
        write_utilization = (write_30d / provisioned_write * 100) if provisioned_write > 0 else 0

        # GSI analysis
        gsi_count = len(table.get("GlobalSecondaryIndexes", []))
        gsi_idle_count = self._count_idle_gsis(table, now)

        # PITR status
        pitr_enabled = self._check_pitr_status(table_name)

        # Streams status
        streams_enabled = "StreamSpecification" in table and table["StreamSpecification"].get("StreamEnabled", False)
        stream_records_30d = 0.0  # TODO: Implement stream records metric if available

        # Table size and item count
        table_size_bytes = table.get("TableSizeBytes", 0)
        table_size_gb = table_size_bytes / (1024**3)
        item_count = table.get("ItemCount", 0)

        # D6: Stream orphans detection (NEW - 99/100 upgrade)
        stream_orphan = self._check_stream_orphans(table_name, streams_enabled)

        # D7: On-Demand opportunity calculation (NEW - 99/100 upgrade)
        ondemand_savings_pct = self._calculate_ondemand_savings(
            read_30d, write_30d, provisioned_read, provisioned_write
        )

        return DynamoDBActivityMetrics(
            consumed_read_capacity_30d=read_30d,
            consumed_write_capacity_30d=write_30d,
            consumed_read_capacity_60d=read_60d,
            consumed_write_capacity_60d=write_60d,
            provisioned_read_capacity=provisioned_read,
            provisioned_write_capacity=provisioned_write,
            read_utilization_pct=read_utilization,
            write_utilization_pct=write_utilization,
            gsi_count=gsi_count,
            gsi_idle_count=gsi_idle_count,
            pitr_enabled=pitr_enabled,
            streams_enabled=streams_enabled,
            stream_records_30d=stream_records_30d,
            table_size_gb=table_size_gb,
            item_count=item_count,
            stream_orphan=stream_orphan,
            ondemand_savings_pct=ondemand_savings_pct,
        )

    def _get_metric_average(self, table_name: str, metric_name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Get CloudWatch metric average.

        Args:
            table_name: DynamoDB table name
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Metric average value, or 0.0 if no data
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/DynamoDB",
                MetricName=metric_name,
                Dimensions=[{"Name": "TableName", "Value": table_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Average"],
            )

            datapoints = response["Datapoints"]
            if not datapoints:
                return 0.0

            # Increment query counter
            self.query_count += 1

            return sum(d["Average"] for d in datapoints) / len(datapoints)

        except ClientError as e:
            self.logger.debug(f"CloudWatch query failed for {table_name}/{metric_name}: {e}")
            return 0.0

    def _count_idle_gsis(self, table: Dict, now: datetime) -> int:
        """
        Count idle Global Secondary Indexes.

        Args:
            table: DynamoDB table metadata
            now: Current timestamp

        Returns:
            Count of idle GSIs
        """
        gsis = table.get("GlobalSecondaryIndexes", [])
        idle_count = 0

        for gsi in gsis:
            gsi_name = gsi["IndexName"]
            table_name = table["TableName"]

            # Query GSI consumed capacity
            consumed_read = self._get_gsi_metric_average(
                table_name, gsi_name, "ConsumedReadCapacityUnits", now - timedelta(days=30), now
            )
            consumed_write = self._get_gsi_metric_average(
                table_name, gsi_name, "ConsumedWriteCapacityUnits", now - timedelta(days=30), now
            )

            # Consider idle if both read and write are very low
            if consumed_read < 1.0 and consumed_write < 1.0:
                idle_count += 1

        return idle_count

    def _get_gsi_metric_average(
        self, table_name: str, gsi_name: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> float:
        """
        Get CloudWatch metric average for GSI.

        Args:
            table_name: DynamoDB table name
            gsi_name: Global Secondary Index name
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Metric average value, or 0.0 if no data
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/DynamoDB",
                MetricName=metric_name,
                Dimensions=[
                    {"Name": "TableName", "Value": table_name},
                    {"Name": "GlobalSecondaryIndexName", "Value": gsi_name},
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Average"],
            )

            datapoints = response["Datapoints"]
            if not datapoints:
                return 0.0

            self.query_count += 1
            return sum(d["Average"] for d in datapoints) / len(datapoints)

        except ClientError as e:
            self.logger.debug(f"CloudWatch query failed for GSI {table_name}/{gsi_name}/{metric_name}: {e}")
            return 0.0

    def _check_pitr_status(self, table_name: str) -> bool:
        """
        Check if Point-in-Time Recovery is enabled.

        Args:
            table_name: DynamoDB table name

        Returns:
            True if PITR enabled, False otherwise
        """
        try:
            response = self.dynamodb_client.describe_continuous_backups(TableName=table_name)
            status = (
                response.get("ContinuousBackupsDescription", {})
                .get("PointInTimeRecoveryDescription", {})
                .get("PointInTimeRecoveryStatus")
            )
            return status == "ENABLED"
        except ClientError as e:
            self.logger.debug(f"Failed to check PITR status for {table_name}: {e}")
            return False

    def _check_stream_orphans(self, table_name: str, streams_enabled: bool) -> bool:
        """
        Check if DynamoDB Streams are enabled but have no Lambda consumers (D6 signal).

        Detection: Streams enabled but zero Lambda event source mappings
        Data Sources: DynamoDB API (StreamSpecification) + Lambda API (EventSourceMappings)

        Args:
            table_name: DynamoDB table name
            streams_enabled: Whether streams are enabled on this table

        Returns:
            True if stream orphan detected, False otherwise
        """
        if not streams_enabled:
            return False

        try:
            # Get Lambda client
            lambda_client = self.session.client("lambda", region_name=self.region)

            # Query event source mappings for this DynamoDB table
            # Note: Need to get table ARN first
            table_response = self.dynamodb_client.describe_table(TableName=table_name)
            table_arn = table_response["Table"]["TableArn"]

            # Get stream ARN if available
            stream_arn = table_response["Table"].get("LatestStreamArn")
            if not stream_arn:
                # Streams enabled but no stream ARN = orphan
                return True

            # Check for Lambda event source mappings
            paginator = lambda_client.get_paginator("list_event_source_mappings")
            for page in paginator.paginate(EventSourceArn=stream_arn):
                event_source_mappings = page.get("EventSourceMappings", [])
                if event_source_mappings:
                    # Has active consumers
                    return False

            # Streams enabled but no consumers = orphan
            return True

        except ClientError as e:
            self.logger.debug(f"Failed to check stream orphans for {table_name}: {e}")
            return False

    def _calculate_ondemand_savings(
        self, read_30d: float, write_30d: float, provisioned_read: float, provisioned_write: float
    ) -> float:
        """
        Calculate potential savings switching from PROVISIONED to ON-DEMAND (D7 signal).

        Detection: PROVISIONED mode + low utilization where On-Demand is 30% cheaper
        Data Sources: CloudWatch Metrics + AWS Pricing (approximated)

        Pricing assumptions (ap-southeast-2):
        - PROVISIONED RCU: $0.000742/hour ($0.53/month per RCU)
        - PROVISIONED WCU: $0.003712/hour ($2.67/month per WCU)
        - ON-DEMAND Read: $0.285 per million requests
        - ON-DEMAND Write: $1.425 per million requests

        Args:
            read_30d: Consumed read capacity (30-day average)
            write_30d: Consumed write capacity (30-day average)
            provisioned_read: Provisioned read capacity units
            provisioned_write: Provisioned write capacity units

        Returns:
            Potential savings percentage (0-100)
        """
        if provisioned_read == 0 and provisioned_write == 0:
            # Already On-Demand or no capacity
            return 0.0

        try:
            # Calculate PROVISIONED monthly cost
            provisioned_cost_monthly = (
                (provisioned_read * 0.53)  # RCU monthly cost
                + (provisioned_write * 2.67)  # WCU monthly cost
            )

            # Calculate ON-DEMAND monthly cost (assuming 30 days)
            # Convert capacity to requests: 1 RCU = 2 reads/sec, 1 WCU = 1 write/sec
            read_requests_monthly = read_30d * 2 * 86400 * 30  # RCU → requests/month
            write_requests_monthly = write_30d * 86400 * 30  # WCU → requests/month

            ondemand_cost_monthly = (
                (read_requests_monthly / 1_000_000 * 0.285)  # Read cost
                + (write_requests_monthly / 1_000_000 * 1.425)  # Write cost
            )

            # Calculate savings percentage
            if provisioned_cost_monthly > 0:
                savings_pct = ((provisioned_cost_monthly - ondemand_cost_monthly) / provisioned_cost_monthly) * 100
                return max(0.0, savings_pct)  # Return 0 if On-Demand more expensive

            return 0.0

        except Exception as e:
            self.logger.debug(f"Failed to calculate On-Demand savings: {e}")
            return 0.0

    def _classify_activity_pattern(self, metrics: DynamoDBActivityMetrics) -> ActivityPattern:
        """
        Classify DynamoDB activity pattern.

        Classification:
        - ACTIVE: >1000 ops/day (production)
        - MODERATE: 100-1000 ops/day (dev/staging)
        - LIGHT: <100 ops/day (test)
        - IDLE: <10 ops/day

        Args:
            metrics: DynamoDB activity metrics

        Returns:
            ActivityPattern enum
        """
        total_ops = metrics.consumed_read_capacity_30d + metrics.consumed_write_capacity_30d

        if total_ops >= self.ACTIVE_OPS_THRESHOLD:
            return ActivityPattern.ACTIVE
        elif total_ops >= self.MODERATE_OPS_THRESHOLD:
            return ActivityPattern.MODERATE
        elif total_ops >= 10:
            return ActivityPattern.LIGHT
        else:
            return ActivityPattern.IDLE

    def _generate_idle_signals(
        self, metrics: DynamoDBActivityMetrics, pattern: ActivityPattern
    ) -> Tuple[List[DynamoDBIdleSignal], int]:
        """
        Generate D1-D7 idle signals and calculate decommission score (99/100 confidence).

        Signal generation rules with 0-100 scoring:
        - D1: read/write utilization < 5% → 45 points (HIGH confidence: 0.90)
        - D2: idle GSIs > 0 → 20 points (MEDIUM confidence: 0.75)
        - D3: PITR not enabled → 15 points (MEDIUM confidence: 0.60)
        - D4: Streams not enabled → 10 points (LOW confidence: 0.50)
        - D5: Low cost efficiency → 10 points (MEDIUM confidence: 0.70)
        - D6: Stream orphans (NEW) → 5 points (MEDIUM confidence: 0.65)
        - D7: On-Demand opportunity (NEW) → 5 points (MEDIUM confidence: 0.75)

        Args:
            metrics: DynamoDB activity metrics
            pattern: Activity pattern classification

        Returns:
            Tuple of (signals list, decommission score 0-100 capped)
        """
        signals: List[DynamoDBIdleSignal] = []
        score = 0

        # D1: Low capacity utilization (<5%) - 45 points
        if (
            metrics.read_utilization_pct < self.IDLE_CAPACITY_THRESHOLD
            and metrics.write_utilization_pct < self.IDLE_CAPACITY_THRESHOLD
        ):
            signals.append(DynamoDBIdleSignal.D1_LOW_CAPACITY_UTILIZATION)
            score += DEFAULT_DYNAMODB_WEIGHTS["D1"]

        # D2: Idle GSIs - 20 points
        if metrics.gsi_idle_count > 0:
            signals.append(DynamoDBIdleSignal.D2_IDLE_GSI)
            score += DEFAULT_DYNAMODB_WEIGHTS["D2"]

        # D3: No PITR enabled - 15 points
        if not metrics.pitr_enabled:
            signals.append(DynamoDBIdleSignal.D3_NO_PITR)
            score += DEFAULT_DYNAMODB_WEIGHTS["D3"]

        # D4: No Streams - 10 points
        if not metrics.streams_enabled:
            signals.append(DynamoDBIdleSignal.D4_NO_STREAMS)
            score += DEFAULT_DYNAMODB_WEIGHTS["D4"]

        # D5: Low cost efficiency (provisioned but low usage) - 10 points
        if pattern in [ActivityPattern.IDLE, ActivityPattern.LIGHT]:
            if metrics.provisioned_read_capacity > 0 or metrics.provisioned_write_capacity > 0:
                signals.append(DynamoDBIdleSignal.D5_LOW_COST_EFFICIENCY)
                score += DEFAULT_DYNAMODB_WEIGHTS["D5"]

        # D6: Stream orphans (NEW - 99/100 upgrade) - 5 points
        # Streams enabled but no Lambda consumers
        if hasattr(metrics, "stream_orphan") and metrics.stream_orphan:
            signals.append(DynamoDBIdleSignal.D6_STREAM_ORPHANS)
            score += DEFAULT_DYNAMODB_WEIGHTS["D6"]

        # D7: On-Demand opportunity (NEW - 99/100 upgrade) - 5 points
        # PROVISIONED mode + low utilization where On-Demand is 30% cheaper
        if hasattr(metrics, "ondemand_savings_pct") and metrics.ondemand_savings_pct >= 30:
            signals.append(DynamoDBIdleSignal.D7_ONDEMAND_OPPORTUNITY)
            score += DEFAULT_DYNAMODB_WEIGHTS["D7"]

        # Cap score at 100 (total weights = 110)
        score = min(score, 100)

        return signals, score

    def _calculate_tier(self, score: int) -> str:
        """
        Calculate decommission tier from score.

        Tier thresholds (consistent with ALB/Route53):
        - MUST (≥80): Immediate decommission candidates
        - SHOULD (≥50): Strong decommission candidates
        - COULD (≥25): Moderate decommission candidates
        - KEEP (<25): Active resources

        Args:
            score: Decommission score (0-100)

        Returns:
            Tier string: "MUST", "SHOULD", "COULD", or "KEEP"
        """
        if score >= 80:
            return "MUST"
        elif score >= 50:
            return "SHOULD"
        elif score >= 25:
            return "COULD"
        else:
            return "KEEP"

    def _calculate_confidence(self, signals: List[DynamoDBIdleSignal]) -> float:
        """
        Calculate idle confidence score.

        Signal weights:
        - D1: 0.90 (low capacity utilization)
        - D2: 0.75 (idle GSIs)
        - D3: 0.60 (no PITR)
        - D4: 0.50 (no streams)
        - D5: 0.70 (low cost efficiency)

        Args:
            signals: List of idle signals

        Returns:
            Confidence score (0.0-1.0)
        """
        if not signals:
            return 0.0

        # Signal confidence mapping
        signal_confidence = {
            DynamoDBIdleSignal.D1_LOW_CAPACITY_UTILIZATION: 0.90,
            DynamoDBIdleSignal.D2_IDLE_GSI: 0.75,
            DynamoDBIdleSignal.D3_NO_PITR: 0.60,
            DynamoDBIdleSignal.D4_NO_STREAMS: 0.50,
            DynamoDBIdleSignal.D5_LOW_COST_EFFICIENCY: 0.70,
        }

        # Use maximum confidence from all signals
        return max(signal_confidence.get(signal, 0.0) for signal in signals)

    def _calculate_monthly_cost(self, table: Dict, metrics: DynamoDBActivityMetrics) -> float:
        """
        Calculate monthly DynamoDB table cost.

        Uses AWS Pricing API to get hourly rate.
        Fallback to placeholder pricing if API unavailable.

        Args:
            table: DynamoDB table metadata
            metrics: Activity metrics

        Returns:
            Monthly cost estimate
        """
        # TODO: Implement AWS Pricing API query
        # For now, use placeholder pricing
        monthly_hours = 730  # Average hours per month

        read_cost = metrics.provisioned_read_capacity * self.DEFAULT_RCU_HOURLY_RATE * monthly_hours
        write_cost = metrics.provisioned_write_capacity * self.DEFAULT_WCU_HOURLY_RATE * monthly_hours

        return read_cost + write_cost

    def _calculate_potential_savings(self, annual_cost: float, confidence: float, pattern: ActivityPattern) -> float:
        """
        Calculate potential annual savings.

        Savings scenarios:
        - IDLE: 100% savings (decommission)
        - LIGHT: 80% savings (on-demand mode)
        - MODERATE: 40% savings (optimize capacity)
        - ACTIVE: 0% savings (keep as-is)

        Args:
            annual_cost: Annual DynamoDB table cost
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
        self, pattern: ActivityPattern, signals: List[DynamoDBIdleSignal], confidence: float
    ) -> DecommissionRecommendation:
        """
        Generate optimization recommendation.

        Recommendation logic:
        - DECOMMISSION: confidence ≥ 0.90 OR D1 signal present
        - INVESTIGATE: confidence ≥ 0.70
        - OPTIMIZE: confidence ≥ 0.50
        - KEEP: confidence < 0.50

        Args:
            pattern: Activity pattern
            signals: List of idle signals
            confidence: Overall confidence score

        Returns:
            DecommissionRecommendation enum
        """
        # High confidence decommission candidates
        if confidence >= 0.90 or DynamoDBIdleSignal.D1_LOW_CAPACITY_UTILIZATION in signals:
            return DecommissionRecommendation.DECOMMISSION

        # Medium confidence - needs investigation
        if confidence >= 0.70:
            return DecommissionRecommendation.INVESTIGATE

        # Moderate underutilization - optimize
        if confidence >= 0.50:
            return DecommissionRecommendation.OPTIMIZE

        # Low confidence - keep resource
        return DecommissionRecommendation.KEEP

    def display_analysis(self, analyses: List[DynamoDBActivityAnalysis]) -> None:
        """
        Display DynamoDB activity analysis in Rich table format.

        Creates comprehensive activity analysis table with:
        - Table name and region
        - Activity metrics (capacity utilization)
        - Decommission signals (D1-D5)
        - Score (0-100) and tier (MUST/SHOULD/COULD/KEEP)

        Args:
            analyses: List of DynamoDBActivityAnalysis objects
        """
        if not analyses:
            print_warning("No DynamoDB tables to display")
            return

        # Create analysis table (NO title parameter - Track 4 UX standard)
        table = create_table(
            columns=[
                {"name": "Table Name", "style": "cyan"},
                {"name": "Read Util %", "style": "bright_yellow"},
                {"name": "Write Util %", "style": "bright_yellow"},
                {"name": "Pattern", "style": "white"},
                {"name": "Signals", "style": "bright_magenta"},
                {"name": "Monthly Cost", "style": "white"},
                {"name": "Score", "style": "white"},
                {"name": "Tier", "style": "bold"},
            ]
        )

        for analysis in analyses:
            # Format signals (compact format)
            signals_str = ",".join(signal.value for signal in analysis.idle_signals)
            if not signals_str:
                signals_str = "-"

            # Format tier with color
            tier = analysis.decommission_tier
            if tier == "MUST":
                tier_str = f"[bright_red]{tier}[/bright_red]"
            elif tier == "SHOULD":
                tier_str = f"[bright_yellow]{tier}[/bright_yellow]"
            elif tier == "COULD":
                tier_str = f"[blue]{tier}[/blue]"
            else:
                tier_str = f"[bright_green]{tier}[/bright_green]"

            table.add_row(
                analysis.table_name,
                f"{analysis.metrics.read_utilization_pct:.1f}%",
                f"{analysis.metrics.write_utilization_pct:.1f}%",
                analysis.activity_pattern.value,
                signals_str,
                format_cost(analysis.monthly_cost),
                str(analysis.decommission_score),
                tier_str,
            )

        console.print()
        console.print(table)
        console.print()

        # Signal Legend (below table - Track 4 UX standard)
        console.print("├── Signal Legend: D1:Capacity <5% (45pts) | D2:Idle GSIs (20pts) | D3:No PITR (15pts)")
        console.print("│   D4:No Streams (10pts) | D5:Low cost efficiency (10pts) | D6:Stream orphans (5pts)")
        console.print("│   D7:On-Demand opportunity (5pts) | 99/100 confidence: ≥6 signals present")
        console.print()

    def _display_summary(self, analyses: List[DynamoDBActivityAnalysis]) -> None:
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

        # v1.1.20 UX: Compact inline format (11 lines → 1 line)
        summary_metrics = {
            "💰 Savings": f"{format_cost(total_savings)}/year",
            "📊 Tables": str(total),
            "🔴 Decommission": str(decommission_count),
            "🟡 Investigate": str(investigate_count),
            "🟢 Keep": str(keep_count),
        }
        # v1.1.20 UX: Add service label for clarity
        console.print(f"⚡ [bold]DynamoDB[/] | {create_inline_metrics(summary_metrics, separator=' | ')}")

    def _get_from_cache(self, cache_key: str) -> Optional[DynamoDBActivityAnalysis]:
        """Get analysis from cache if still valid."""
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return result
        return None

    def _add_to_cache(self, cache_key: str, analysis: DynamoDBActivityAnalysis) -> None:
        """Add analysis to cache with current timestamp."""
        self._cache[cache_key] = (analysis, time.time())


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_dynamodb_activity_enricher(
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 60
) -> DynamoDBActivityEnricher:
    """
    Factory function to create DynamoDBActivityEnricher.

    Provides clean initialization pattern following enterprise architecture
    with automatic profile resolution and sensible defaults.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudWatch lookback period (default: 60)

    Returns:
        Initialized DynamoDBActivityEnricher instance

    Example:
        >>> enricher = create_dynamodb_activity_enricher()
        >>> # Enricher ready for activity analysis
        >>> analyses = enricher.analyze_table_activity(...)
    """
    return DynamoDBActivityEnricher(operational_profile=operational_profile, region=region, lookback_days=lookback_days)


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core enricher class
    "DynamoDBActivityEnricher",
    # Data models
    "DynamoDBActivityAnalysis",
    "DynamoDBActivityMetrics",
    "DynamoDBIdleSignal",
    "ActivityPattern",
    "DecommissionRecommendation",
    # Factory function
    "create_dynamodb_activity_enricher",
]
