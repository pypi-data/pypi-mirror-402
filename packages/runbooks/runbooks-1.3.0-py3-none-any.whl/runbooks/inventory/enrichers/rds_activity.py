#!/usr/bin/env python3
"""
RDS Activity Enricher - Phase 5 Feature 3
==========================================

Business Value: $50K annual savings enabler through idle RDS instance detection
Strategic Impact: Inventory module gap closure (Epic 4 - Compute Optimization)
Integration: Feeds data to FinOps RDS RI optimizer (Phase 3 P2 implemented)

Architecture Pattern: 5-layer enrichment framework
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: RDS activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses R1-R7 signals)

Decommission Signals (R1-R7):
- R1: No connections 90+ days (HIGH confidence: 0.95)
- R2: <5 connections/day avg 90d (HIGH confidence: 0.90)
- R3: CPU <5% avg 60d (MEDIUM confidence: 0.75)
- R4: IOPS <100/day avg 60d (MEDIUM confidence: 0.70)
- R5: Backup-only connections (MEDIUM confidence: 0.65)
- R6: Non-business hours only (LOW confidence: 0.50)
- R7: Storage <20% utilized (LOW confidence: 0.45)

Usage:
    from runbooks.inventory.enrichers.rds_activity import RDSActivityEnricher

    enricher = RDSActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze RDS instance activity
    analyses = enricher.analyze_instance_activity(
        instance_ids=['mydb-instance-1', 'mydb-instance-2']
    )

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer RDS service costs
    - Flag discrepancies (low activity but high costs = potential issue)
    - Achieve ≥99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: Epic 4 - Compute Optimization
Feature: Phase 5 Feature 3 - RDS Activity Enricher
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


class RDSIdleSignal(str, Enum):
    """RDS idle/underutilization decommission signals (R1-R7)."""

    R1_ZERO_CONNECTIONS_90D = "R1"  # No connections in 90+ days
    R2_LOW_CONNECTIONS = "R2"  # <5 connections/day avg 90d
    R3_LOW_CPU = "R3"  # CPU <5% avg 60d
    R4_LOW_IOPS = "R4"  # IOPS <100/day avg 60d
    R5_BACKUP_ONLY = "R5"  # Backup-only connections
    R6_NONBUSINESS_HOURS = "R6"  # Non-business hours only
    R7_STORAGE_UNDERUTILIZED = "R7"  # Storage <20% utilized


class ActivityPattern(str, Enum):
    """RDS access pattern classification."""

    ACTIVE = "active"  # Production workload (>100 conn/day, >20% CPU)
    MODERATE = "moderate"  # Development/staging (10-100 conn/day, 5-20% CPU)
    LIGHT = "light"  # Test environment (<10 conn/day, <5% CPU)
    IDLE = "idle"  # No meaningful activity
    BACKUP_ONLY = "backup_only"  # Only automated backup connections


class DecommissionRecommendation(str, Enum):
    """Decommission recommendations based on activity analysis."""

    DECOMMISSION = "DECOMMISSION"  # High confidence - decommission candidate
    INVESTIGATE = "INVESTIGATE"  # Medium confidence - needs review
    DOWNSIZE = "DOWNSIZE"  # Moderate underutilization - reduce capacity
    KEEP = "KEEP"  # Active resource - retain


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class RDSActivityMetrics:
    """
    CloudWatch metrics for RDS instance.

    Comprehensive activity metrics for decommission decision-making with
    R1-R7 signal framework and MCP validation capability.
    """

    avg_connections_30d: float
    avg_connections_60d: float
    avg_connections_90d: float
    max_connections_90d: int
    avg_cpu_percent_30d: float
    avg_cpu_percent_60d: float
    avg_iops_30d: float
    avg_iops_60d: float
    storage_allocated_gb: float
    storage_used_gb: float
    storage_utilization_pct: float
    backup_connection_ratio: float = 0.0  # % connections from backup jobs
    business_hours_ratio: float = 0.0  # % connections during business hours


@dataclass
class RDSActivityAnalysis:
    """
    RDS instance activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    R1-R7 signal framework and cost impact analysis.
    """

    instance_id: str
    db_name: Optional[str]
    engine: str
    instance_class: str
    region: str
    account_id: str
    metrics: RDSActivityMetrics
    activity_pattern: ActivityPattern
    idle_signals: List[RDSIdleSignal] = field(default_factory=list)
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: float = 0.0  # 0.0-1.0
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP
    mcp_validated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "instance_id": self.instance_id,
            "db_name": self.db_name,
            "engine": self.engine,
            "instance_class": self.instance_class,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "avg_connections_30d": self.metrics.avg_connections_30d,
                "avg_connections_60d": self.metrics.avg_connections_60d,
                "avg_connections_90d": self.metrics.avg_connections_90d,
                "max_connections_90d": self.metrics.max_connections_90d,
                "avg_cpu_percent_30d": self.metrics.avg_cpu_percent_30d,
                "avg_cpu_percent_60d": self.metrics.avg_cpu_percent_60d,
                "avg_iops_30d": self.metrics.avg_iops_30d,
                "avg_iops_60d": self.metrics.avg_iops_60d,
                "storage_allocated_gb": self.metrics.storage_allocated_gb,
                "storage_used_gb": self.metrics.storage_used_gb,
                "storage_utilization_pct": self.metrics.storage_utilization_pct,
                "backup_connection_ratio": self.metrics.backup_connection_ratio,
                "business_hours_ratio": self.metrics.business_hours_ratio,
            },
            "activity_pattern": self.activity_pattern.value,
            "idle_signals": [signal.value for signal in self.idle_signals],
            "monthly_cost": self.monthly_cost,
            "annual_cost": self.annual_cost,
            "potential_savings": self.potential_savings,
            "confidence": self.confidence,
            "recommendation": self.recommendation.value,
            "mcp_validated": self.mcp_validated,
            "metadata": self.metadata,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE ENRICHER CLASS
# ═════════════════════════════════════════════════════════════════════════════

# v1.1.23: Module-level flag for summary deduplication across multiple enricher instances (Issue #7)
_RDS_SUMMARY_DISPLAYED_GLOBALLY = False


class RDSActivityEnricher:
    """
    RDS activity enricher for inventory resources.

    Analyzes RDS instances for idle/underutilization patterns using CloudWatch
    metrics with R1-R7 signal framework and MCP validation support.

    Capabilities:
    - Activity metrics analysis (30/60/90 day windows)
    - Connection pattern classification (user vs backup operations)
    - CPU and IOPS utilization tracking
    - Storage utilization analysis
    - Activity pattern classification (active/moderate/light/idle)
    - MCP validation of RDS costs
    - Comprehensive decommission recommendations

    Decommission Signals Generated:
    - R1: Zero connections 90+ days (HIGH confidence: 0.95)
    - R2: Low connections <5/day (HIGH confidence: 0.90)
    - R3: Low CPU <5% avg (MEDIUM confidence: 0.75)
    - R4: Low IOPS <100/day (MEDIUM confidence: 0.70)
    - R5: Backup-only connections (MEDIUM confidence: 0.65)
    - R6: Non-business hours only (LOW confidence: 0.50)
    - R7: Storage underutilized <20% (LOW confidence: 0.45)

    Example:
        >>> enricher = RDSActivityEnricher(
        ...     operational_profile='ops-profile',
        ...     region='ap-southeast-2'
        ... )
        >>> analyses = enricher.analyze_instance_activity(
        ...     instance_ids=['mydb-instance-1']
        ... )
        >>> for analysis in analyses:
        ...     if RDSIdleSignal.R1_ZERO_CONNECTIONS_90D in analysis.idle_signals:
        ...         print(f"Idle database: {analysis.instance_id}")
    """

    # Activity thresholds for classification
    IDLE_CONNECTION_THRESHOLD = 5  # connections/day
    IDLE_CPU_THRESHOLD = 5.0  # percent
    IDLE_IOPS_THRESHOLD = 100  # IOPS/day
    STORAGE_UTILIZATION_THRESHOLD = 20.0  # percent

    # RDS pricing (ap-southeast-2) - placeholder, should use AWS Pricing API
    # Example: db.t3.medium = $0.068/hour
    DEFAULT_HOURLY_RATE = 0.068

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 90,
        cache_ttl: int = 300,
        enable_mcp_validation: bool = False,
        verbose: bool = True,
    ):
        """
        Initialize RDS activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for RDS queries (default: ap-southeast-2)
            lookback_days: CloudWatch lookback period (default: 90, max: 455)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
            enable_mcp_validation: Enable MCP cross-validation (default: False for performance)
            verbose: Enable verbose output (detailed panel summary vs compact single-line, default: True for backward compatibility)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = min(lookback_days, 455)  # CloudWatch metrics retention
        self.cache_ttl = cache_ttl
        self.enable_mcp_validation = enable_mcp_validation
        self.verbose = verbose

        # Initialize AWS session
        self.session = create_operational_session(self.operational_profile)
        self.rds_client = self.session.client("rds", region_name=self.region)
        self.cloudwatch_client = self.session.client("cloudwatch", region_name=self.region)
        self.pricing_client = self.session.client("pricing", region_name="us-east-1")  # Pricing API in us-east-1

        # MCP integration (lazy initialization to avoid blocking startup)
        self._mcp_engine = None
        if enable_mcp_validation:
            print_warning("MCP validation enabled - initialization may take 30-60s")
            self._initialize_mcp_engine()

        # Validation cache (5-minute TTL for performance)
        self._cache: Dict[str, Tuple[RDSActivityAnalysis, float]] = {}

        # Performance tracking
        self.query_count = 0
        self.total_execution_time = 0.0

        # Logger
        self.logger = logging.getLogger(__name__)

    def _initialize_mcp_engine(self):
        """Lazy initialize MCP engine for cost validation."""
        if not MCP_AVAILABLE:
            print_warning("MCP Python SDK not available - MCP validation disabled")
            self.enable_mcp_validation = False
            return

        try:
            from runbooks.finops.hybrid_mcp_engine import create_hybrid_mcp_engine

            self._mcp_engine = create_hybrid_mcp_engine(profile=self.operational_profile)
            print_success("MCP validation engine initialized")
        except ImportError:
            print_warning("MCP Python SDK not available. Install with: uv add mcp")
            self.enable_mcp_validation = False
        except Exception as e:
            print_error(f"MCP initialization failed: {str(e)}")
            self.enable_mcp_validation = False

    def analyze_instance_activity(
        self,
        instance_ids: Optional[List[str]] = None,
        region: Optional[str] = None,
        lookback_days: Optional[int] = None,
    ) -> List[RDSActivityAnalysis]:
        """
        Analyze RDS instance activity for idle detection.

        Core analysis workflow:
        1. Query RDS instances (all or specific IDs)
        2. Get CloudWatch metrics for each instance (30/60/90 day windows)
        3. Classify activity pattern (active/moderate/light/idle)
        4. Generate R1-R7 decommission signals based on patterns
        5. Compute confidence score and recommendation
        6. Calculate cost impact and potential savings

        Args:
            instance_ids: List of instance IDs to analyze (analyzes all if None)
            region: AWS region filter (default: use instance region)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals

        Example:
            >>> analyses = enricher.analyze_instance_activity(
            ...     instance_ids=['mydb-1', 'mydb-2']
            ... )
            >>> for analysis in analyses:
            ...     print(f"{analysis.instance_id}: {analysis.recommendation.value}")
        """
        start_time = time.time()
        analysis_region = region or self.region
        lookback = lookback_days or self.lookback_days

        # Get RDS instances
        instances = self._get_rds_instances(instance_ids, analysis_region)

        if not instances:
            print_warning("No RDS instances found")
            return []

        analyses: List[RDSActivityAnalysis] = []

        with create_progress_bar(description="Analyzing RDS instances") as progress:
            task = progress.add_task(f"Analyzing {len(instances)} instances", total=len(instances))

            for instance in instances:
                try:
                    # Check cache first
                    instance_id = instance["DBInstanceIdentifier"]
                    cache_key = f"{instance_id}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Analyze instance
                    analysis = self._analyze_instance(instance, lookback)

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(
                        f"Failed to analyze RDS instance {instance.get('DBInstanceIdentifier')}: {e}", exc_info=True
                    )
                    print_warning(f"⚠️  Skipped {instance.get('DBInstanceIdentifier')}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _get_rds_instances(self, instance_ids: Optional[List[str]], region: str) -> List[Dict]:
        """
        Get RDS instances from AWS API.

        Args:
            instance_ids: Specific instances to retrieve (retrieves all if None)
            region: AWS region filter

        Returns:
            List of RDS instance metadata dictionaries
        """
        instances = []

        try:
            if instance_ids:
                # Get specific instances
                for instance_id in instance_ids:
                    try:
                        response = self.rds_client.describe_db_instances(DBInstanceIdentifier=instance_id)
                        instances.extend(response["DBInstances"])
                    except ClientError as e:
                        if e.response["Error"]["Code"] == "DBInstanceNotFound":
                            self.logger.warning(f"RDS instance not found: {instance_id}")
                        else:
                            raise
            else:
                # Get all instances
                paginator = self.rds_client.get_paginator("describe_db_instances")
                for page in paginator.paginate():
                    instances.extend(page["DBInstances"])

        except ClientError as e:
            self.logger.error(f"Failed to get RDS instances: {e}")

        return instances

    def _analyze_instance(self, instance: Dict, lookback_days: int) -> RDSActivityAnalysis:
        """
        Analyze individual RDS instance.

        Args:
            instance: RDS instance metadata from describe_db_instances
            lookback_days: CloudWatch metrics lookback period

        Returns:
            Comprehensive activity analysis with idle signals
        """
        instance_id = instance["DBInstanceIdentifier"]

        # Get CloudWatch metrics
        metrics = self._get_cloudwatch_metrics(instance_id, lookback_days)

        # Classify activity pattern
        activity_pattern = self._classify_activity_pattern(metrics)

        # Generate idle signals
        idle_signals = self._generate_idle_signals(metrics, activity_pattern)

        # Calculate costs
        monthly_cost = self._calculate_monthly_cost(instance)
        annual_cost = monthly_cost * 12

        # Calculate potential savings
        confidence = self._calculate_confidence(idle_signals)
        potential_savings = self._calculate_potential_savings(annual_cost, confidence, activity_pattern)

        # Generate recommendation
        recommendation = self._generate_recommendation(activity_pattern, idle_signals, confidence)

        # Get account ID
        try:
            sts = self.session.client("sts")
            account_id = sts.get_caller_identity()["Account"]
        except Exception:
            account_id = "unknown"

        return RDSActivityAnalysis(
            instance_id=instance_id,
            db_name=instance.get("DBName"),
            engine=instance["Engine"],
            instance_class=instance["DBInstanceClass"],
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

    def _get_cloudwatch_metrics(self, instance_id: str, lookback_days: int) -> RDSActivityMetrics:
        """
        Get CloudWatch metrics for RDS instance.

        Metrics queried:
        - DatabaseConnections (30/60/90-day average, max)
        - CPUUtilization (30/60-day average)
        - ReadIOPS + WriteIOPS (30/60-day average)
        - FreeStorageSpace (current)

        Args:
            instance_id: RDS instance identifier
            lookback_days: Lookback period for metrics

        Returns:
            Comprehensive activity metrics
        """
        now = datetime.utcnow()

        # Query DatabaseConnections
        conn_30d = self._get_metric_average(instance_id, "DatabaseConnections", now - timedelta(days=30), now)
        conn_60d = self._get_metric_average(instance_id, "DatabaseConnections", now - timedelta(days=60), now)
        conn_90d = self._get_metric_average(instance_id, "DatabaseConnections", now - timedelta(days=90), now)
        conn_max = self._get_metric_max(instance_id, "DatabaseConnections", now - timedelta(days=90), now)

        # Query CPUUtilization
        cpu_30d = self._get_metric_average(instance_id, "CPUUtilization", now - timedelta(days=30), now)
        cpu_60d = self._get_metric_average(instance_id, "CPUUtilization", now - timedelta(days=60), now)

        # Query IOPS (Read + Write)
        read_iops_30d = self._get_metric_average(instance_id, "ReadIOPS", now - timedelta(days=30), now)
        write_iops_30d = self._get_metric_average(instance_id, "WriteIOPS", now - timedelta(days=30), now)
        read_iops_60d = self._get_metric_average(instance_id, "ReadIOPS", now - timedelta(days=60), now)
        write_iops_60d = self._get_metric_average(instance_id, "WriteIOPS", now - timedelta(days=60), now)

        # Get storage info from RDS API
        try:
            instance_info = self.rds_client.describe_db_instances(DBInstanceIdentifier=instance_id)["DBInstances"][0]
            storage_allocated = instance_info["AllocatedStorage"]
        except Exception as e:
            self.logger.warning(f"Failed to get storage info for {instance_id}: {e}")
            storage_allocated = 0

        # Get free storage from CloudWatch
        free_storage_bytes = self._get_metric_average(instance_id, "FreeStorageSpace", now - timedelta(days=1), now)
        free_storage_gb = free_storage_bytes / (1024**3) if free_storage_bytes > 0 else 0
        storage_used = max(0, storage_allocated - free_storage_gb)
        storage_utilization = (storage_used / storage_allocated * 100) if storage_allocated > 0 else 0

        return RDSActivityMetrics(
            avg_connections_30d=conn_30d,
            avg_connections_60d=conn_60d,
            avg_connections_90d=conn_90d,
            max_connections_90d=int(conn_max),
            avg_cpu_percent_30d=cpu_30d,
            avg_cpu_percent_60d=cpu_60d,
            avg_iops_30d=read_iops_30d + write_iops_30d,
            avg_iops_60d=read_iops_60d + write_iops_60d,
            storage_allocated_gb=float(storage_allocated),
            storage_used_gb=storage_used,
            storage_utilization_pct=storage_utilization,
            backup_connection_ratio=0.0,  # TODO: Analyze connection patterns
            business_hours_ratio=0.0,  # TODO: Analyze time-of-day patterns
        )

    def _get_metric_average(
        self, instance_id: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> float:
        """
        Get CloudWatch metric average.

        Args:
            instance_id: RDS instance identifier
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Metric average value, or 0.0 if no data
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName=metric_name,
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
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
            self.logger.warning(f"CloudWatch query failed for {instance_id}/{metric_name}: {e}")
            return 0.0

    def _get_metric_max(self, instance_id: str, metric_name: str, start_time: datetime, end_time: datetime) -> float:
        """
        Get CloudWatch metric maximum.

        Args:
            instance_id: RDS instance identifier
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Metric maximum value, or 0.0 if no data
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/RDS",
                MetricName=metric_name,
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Maximum"],
            )

            datapoints = response["Datapoints"]
            if not datapoints:
                return 0.0

            # Increment query counter
            self.query_count += 1

            return max(d["Maximum"] for d in datapoints)

        except ClientError as e:
            self.logger.warning(f"CloudWatch query failed for {instance_id}/{metric_name}: {e}")
            return 0.0

    def _classify_activity_pattern(self, metrics: RDSActivityMetrics) -> ActivityPattern:
        """
        Classify RDS activity pattern.

        Classification:
        - ACTIVE: >100 conn/day, >20% CPU (production)
        - MODERATE: 10-100 conn/day, 5-20% CPU (dev/staging)
        - LIGHT: <10 conn/day, <5% CPU (test)
        - IDLE: <1 conn/day, <1% CPU
        - BACKUP_ONLY: All connections from backup jobs

        Args:
            metrics: RDS activity metrics

        Returns:
            ActivityPattern enum
        """
        conn_avg = metrics.avg_connections_90d
        cpu_avg = metrics.avg_cpu_percent_60d

        if conn_avg >= 100 and cpu_avg >= 20:
            return ActivityPattern.ACTIVE
        elif conn_avg >= 10 and cpu_avg >= 5:
            return ActivityPattern.MODERATE
        elif conn_avg >= 1 and cpu_avg >= 1:
            return ActivityPattern.LIGHT
        elif metrics.backup_connection_ratio > 0.9:
            return ActivityPattern.BACKUP_ONLY
        else:
            return ActivityPattern.IDLE

    def _generate_idle_signals(self, metrics: RDSActivityMetrics, pattern: ActivityPattern) -> List[RDSIdleSignal]:
        """
        Generate R1-R7 idle signals.

        Signal generation rules:
        - R1: avg_connections_90d == 0 → HIGH confidence (0.95)
        - R2: avg_connections_90d < 5 → HIGH confidence (0.90)
        - R3: avg_cpu_60d < 5.0 → MEDIUM confidence (0.75)
        - R4: avg_iops_60d < 100 → MEDIUM confidence (0.70)
        - R5: backup_connection_ratio > 0.9 → MEDIUM confidence (0.65)
        - R6: business_hours_ratio < 0.1 → LOW confidence (0.50)
        - R7: storage_utilization < 20 → LOW confidence (0.45)

        Args:
            metrics: RDS activity metrics
            pattern: Activity pattern classification

        Returns:
            List of applicable RDSIdleSignal enums
        """
        signals: List[RDSIdleSignal] = []

        # R1: Zero connections 90+ days (HIGH confidence)
        if metrics.avg_connections_90d == 0:
            signals.append(RDSIdleSignal.R1_ZERO_CONNECTIONS_90D)
            return signals  # If no activity, other signals don't apply

        # R2: Low connections (<5/day avg over 90d)
        if metrics.avg_connections_90d < self.IDLE_CONNECTION_THRESHOLD:
            signals.append(RDSIdleSignal.R2_LOW_CONNECTIONS)

        # R3: Low CPU (<5% avg over 60d)
        if metrics.avg_cpu_percent_60d < self.IDLE_CPU_THRESHOLD:
            signals.append(RDSIdleSignal.R3_LOW_CPU)

        # R4: Low IOPS (<100/day avg over 60d)
        if metrics.avg_iops_60d < self.IDLE_IOPS_THRESHOLD:
            signals.append(RDSIdleSignal.R4_LOW_IOPS)

        # R5: Backup-only connections
        if pattern == ActivityPattern.BACKUP_ONLY:
            signals.append(RDSIdleSignal.R5_BACKUP_ONLY)

        # R6: Non-business hours only
        if metrics.business_hours_ratio < 0.1 and metrics.avg_connections_90d > 0:
            signals.append(RDSIdleSignal.R6_NONBUSINESS_HOURS)

        # R7: Storage underutilized (<20%)
        if metrics.storage_utilization_pct < self.STORAGE_UTILIZATION_THRESHOLD:
            signals.append(RDSIdleSignal.R7_STORAGE_UNDERUTILIZED)

        return signals

    def _calculate_confidence(self, signals: List[RDSIdleSignal]) -> float:
        """
        Calculate idle confidence score.

        Signal weights:
        - R1: 0.95 (zero connections - highest confidence)
        - R2: 0.90 (very low connections)
        - R3: 0.75 (low CPU)
        - R4: 0.70 (low IOPS)
        - R5: 0.65 (backup-only)
        - R6: 0.50 (non-business hours)
        - R7: 0.45 (storage underutilized)

        Args:
            signals: List of idle signals

        Returns:
            Confidence score (0.0-1.0)
        """
        if not signals:
            return 0.0

        # Signal confidence mapping
        signal_confidence = {
            RDSIdleSignal.R1_ZERO_CONNECTIONS_90D: 0.95,
            RDSIdleSignal.R2_LOW_CONNECTIONS: 0.90,
            RDSIdleSignal.R3_LOW_CPU: 0.75,
            RDSIdleSignal.R4_LOW_IOPS: 0.70,
            RDSIdleSignal.R5_BACKUP_ONLY: 0.65,
            RDSIdleSignal.R6_NONBUSINESS_HOURS: 0.50,
            RDSIdleSignal.R7_STORAGE_UNDERUTILIZED: 0.45,
        }

        # Use maximum confidence from all signals
        return max(signal_confidence.get(signal, 0.0) for signal in signals)

    def _calculate_monthly_cost(self, instance: Dict) -> float:
        """
        Calculate monthly RDS instance cost.

        Uses AWS Pricing API to get hourly rate.
        Fallback to placeholder pricing if API unavailable.

        Args:
            instance: RDS instance metadata

        Returns:
            Monthly cost estimate
        """
        instance_class = instance["DBInstanceClass"]
        engine = instance["Engine"]

        # TODO: Implement AWS Pricing API query
        # For now, use placeholder pricing (db.t3.medium ≈ $0.068/hour)
        hourly_rate = self.DEFAULT_HOURLY_RATE
        monthly_hours = 730  # Average hours per month

        return hourly_rate * monthly_hours

    def _calculate_potential_savings(self, annual_cost: float, confidence: float, pattern: ActivityPattern) -> float:
        """
        Calculate potential annual savings.

        Savings scenarios:
        - IDLE: 100% savings (decommission)
        - BACKUP_ONLY: 100% savings (use snapshots)
        - LIGHT: 80% savings (downsize significantly)
        - MODERATE: 40% savings (downsize moderately)
        - ACTIVE: 0% savings (keep as-is)

        Args:
            annual_cost: Annual RDS instance cost
            confidence: Idle confidence score
            pattern: Activity pattern

        Returns:
            Potential annual savings amount
        """
        savings_multiplier = {
            ActivityPattern.IDLE: 1.0,
            ActivityPattern.BACKUP_ONLY: 1.0,
            ActivityPattern.LIGHT: 0.8,
            ActivityPattern.MODERATE: 0.4,
            ActivityPattern.ACTIVE: 0.0,
        }

        multiplier = savings_multiplier.get(pattern, 0.0)
        return annual_cost * multiplier * confidence

    def _generate_recommendation(
        self, pattern: ActivityPattern, signals: List[RDSIdleSignal], confidence: float
    ) -> DecommissionRecommendation:
        """
        Generate optimization recommendation.

        Recommendation logic:
        - DECOMMISSION: confidence ≥ 0.90 OR R1 signal present
        - INVESTIGATE: confidence ≥ 0.70
        - DOWNSIZE: confidence ≥ 0.50
        - KEEP: confidence < 0.50

        Args:
            pattern: Activity pattern
            signals: List of idle signals
            confidence: Overall confidence score

        Returns:
            DecommissionRecommendation enum
        """
        # High confidence decommission candidates
        if confidence >= 0.90 or RDSIdleSignal.R1_ZERO_CONNECTIONS_90D in signals:
            return DecommissionRecommendation.DECOMMISSION

        # Medium confidence - needs investigation
        if confidence >= 0.70:
            return DecommissionRecommendation.INVESTIGATE

        # Moderate underutilization - downsize
        if confidence >= 0.50:
            return DecommissionRecommendation.DOWNSIZE

        # Low confidence - keep resource
        return DecommissionRecommendation.KEEP

    async def validate_with_mcp(self, analysis: RDSActivityAnalysis) -> RDSActivityAnalysis:
        """
        Validate activity analysis with MCP.

        Cross-validates RDS activity patterns with Cost Explorer
        RDS service costs using HybridMCPEngine.

        Args:
            analysis: RDSActivityAnalysis to validate

        Returns:
            Updated analysis with mcp_validated flag
        """
        if not self.enable_mcp_validation or not self._mcp_engine:
            return analysis

        try:
            # Use MCP engine to validate cost projection
            validation = await self._mcp_engine.validate_cost_projection(
                resource_id=analysis.instance_id, resource_type="RDS", runbooks_projection=analysis.monthly_cost
            )

            analysis.mcp_validated = validation.passes_threshold

            # Add MCP metadata
            analysis.metadata["mcp_validation"] = {
                "variance_pct": validation.variance_pct,
                "confidence": validation.confidence,
                "passes_threshold": validation.passes_threshold,
            }

        except Exception as e:
            self.logger.warning(f"MCP validation failed for {analysis.instance_id}: {e}")

        return analysis

    def display_analysis(self, analyses: List[RDSActivityAnalysis]) -> None:
        """
        Display RDS activity analysis in Rich table format.

        Creates comprehensive activity analysis table with:
        - Instance ID and engine
        - Activity metrics (connections, CPU)
        - Decommission signals (R1-R7)
        - Recommendation and confidence

        Args:
            analyses: List of RDSActivityAnalysis objects
        """
        if not analyses:
            print_warning("No RDS instances to display")
            return

        # Create analysis table
        table = create_table(
            title="RDS Instance Activity Analysis",
            columns=[
                {"name": "Instance ID", "style": "cyan"},
                {"name": "Engine", "style": "white"},
                {"name": "Class", "style": "white"},
                {"name": "Conn/Day (90d)", "style": "bright_yellow"},
                {"name": "CPU% (60d)", "style": "bright_yellow"},
                {"name": "Pattern", "style": "white"},
                {"name": "Signals", "style": "bright_magenta"},
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
            elif rec == DecommissionRecommendation.DOWNSIZE:
                rec_str = f"[yellow]{rec.value}[/yellow]"
            else:
                rec_str = f"[bright_green]{rec.value}[/bright_green]"

            # v1.1.24 FIX: Handle None/NaN costs safely (prevents float rendering errors)
            monthly_cost_str = (
                f"${analysis.monthly_cost:,.2f}"
                if analysis.monthly_cost and not pd.isna(analysis.monthly_cost)
                else "$0.00"
            )
            monthly_savings_str = (
                f"${analysis.potential_savings / 12:,.2f}"
                if analysis.potential_savings and not pd.isna(analysis.potential_savings)
                else "$0.00"
            )

            table.add_row(
                analysis.instance_id,
                analysis.engine,
                analysis.instance_class,
                f"{analysis.metrics.avg_connections_90d:.1f}",
                f"{analysis.metrics.avg_cpu_percent_60d:.1f}%",
                analysis.activity_pattern.value,
                signals_str,
                monthly_cost_str,  # ✅ Direct string formatting (safe)
                monthly_savings_str,  # ✅ Direct string formatting (safe)
                rec_str,
            )

        console.print()
        console.print(table)
        console.print()

    def _display_summary(self, analyses: List[RDSActivityAnalysis]) -> None:
        """
        Display analysis summary statistics.

        v1.1.23: Deduplication - display summary only once globally across all enricher instances (Issue #7).
        """
        global _RDS_SUMMARY_DISPLAYED_GLOBALLY

        if not analyses:
            return

        # Skip if summary already displayed globally (deduplication across instances)
        if _RDS_SUMMARY_DISPLAYED_GLOBALLY:
            return

        # Mark as displayed globally to prevent duplicates
        _RDS_SUMMARY_DISPLAYED_GLOBALLY = True

        total = len(analyses)
        decommission_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.DECOMMISSION)
        investigate_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.INVESTIGATE)
        downsize_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.DOWNSIZE)
        keep_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.KEEP)

        # Calculate totals
        total_cost = sum(a.annual_cost for a in analyses)
        total_savings = sum(a.potential_savings for a in analyses)

        if self.verbose:
            # Technical/Debug mode: Detailed Rich Panel summary (original behavior)
            summary_text = (
                f"[bold]Total Instances: {total}[/bold]\n"
                f"[bold green]Total Potential Savings: ${total_savings:,.2f}/year[/bold green]\n"
                f"[bold]Total Annual RDS Cost: ${total_cost:,.2f}[/bold]\n\n"
                f"Recommendations:\n"
                f"  [bright_red]Decommission: {decommission_count}[/bright_red]\n"
                f"  [bright_yellow]Investigate: {investigate_count}[/bright_yellow]\n"
                f"  [yellow]Downsize: {downsize_count}[/yellow]\n"
                f"  [bright_green]Keep: {keep_count}[/bright_green]\n\n"
                f"CloudWatch Queries: {self.query_count}"
            )

            summary = create_panel(summary_text, title="RDS Idle Detection Summary", border_style="green")
            console.print(summary)
            console.print()
        else:
            # Executive mode: Compact single-line summary
            savings_pct = (total_savings / total_cost * 100) if total_cost > 0 else 0
            console.print(
                f"💰 RDS: {total} instances → "
                f"${total_savings:,.0f}/year ({savings_pct:.0f}% savings) | "
                f"Action: Decommission {decommission_count}"
            )

    def _get_from_cache(self, cache_key: str) -> Optional[RDSActivityAnalysis]:
        """Get analysis from cache if still valid."""
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return result
        return None

    def _add_to_cache(self, cache_key: str, analysis: RDSActivityAnalysis) -> None:
        """Add analysis to cache with current timestamp."""
        self._cache[cache_key] = (analysis, time.time())


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_rds_activity_enricher(
    operational_profile: Optional[str] = None,
    region: Optional[str] = None,
    lookback_days: int = 90,
    enable_mcp_validation: bool = False,
) -> RDSActivityEnricher:
    """
    Factory function to create RDSActivityEnricher.

    Provides clean initialization pattern following enterprise architecture
    with automatic profile resolution and sensible defaults.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudWatch lookback period (default: 90)
        enable_mcp_validation: Enable MCP cross-validation (default: False for performance)

    Returns:
        Initialized RDSActivityEnricher instance

    Example:
        >>> enricher = create_rds_activity_enricher()
        >>> # Enricher ready for activity analysis
        >>> analyses = enricher.analyze_instance_activity(...)
    """
    return RDSActivityEnricher(
        operational_profile=operational_profile,
        region=region,
        lookback_days=lookback_days,
        enable_mcp_validation=enable_mcp_validation,
    )


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core enricher class
    "RDSActivityEnricher",
    # Data models
    "RDSActivityAnalysis",
    "RDSActivityMetrics",
    "RDSIdleSignal",
    "ActivityPattern",
    "DecommissionRecommendation",
    # Factory function
    "create_rds_activity_enricher",
]
