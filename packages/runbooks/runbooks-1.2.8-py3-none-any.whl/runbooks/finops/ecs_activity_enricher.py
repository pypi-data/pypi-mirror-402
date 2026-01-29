#!/usr/bin/env python3
"""
ECS Activity Enricher - Container Service Activity Signals
===========================================================

Business Value: Idle ECS cluster detection enabling cost optimization
Strategic Impact: Complement DynamoDB pattern (D1-D5) for container workloads
Integration: Feeds data to FinOps decommission scoring framework

Architecture Pattern: 5-layer enrichment framework (matches DynamoDB pattern)
- Layer 1: Resource discovery (consumed from external modules)
- Layer 2: Organizations enrichment (account names)
- Layer 3: Cost enrichment (pricing data)
- Layer 4: ECS activity enrichment (THIS MODULE)
- Layer 5: Decommission scoring (uses C1-C5 signals)

Decommission Signals (C1-C7):
- C1: Cluster CPU/Memory utilization (HIGH confidence: 0.90)
- C2: Task count trends (MEDIUM confidence: 0.75)
- C3: Service health (MEDIUM confidence: 0.70)
- C4: Fargate vs EC2 split (MEDIUM confidence: 0.65)
- C5: Container cost efficiency (MEDIUM confidence: 0.70)
- C6: Network mode waste (MEDIUM confidence: 0.65)
- C7: Logging cost drivers (MEDIUM confidence: 0.70)

Usage:
    from runbooks.finops.ecs_activity_enricher import ECSActivityEnricher

    enricher = ECSActivityEnricher(
        operational_profile='CENTRALISED_OPS_PROFILE',
        region='ap-southeast-2'
    )

    # Analyze ECS cluster activity
    analyses = enricher.analyze_cluster_activity(
        cluster_arns=['arn:aws:ecs:...']
    )

    # Display analysis
    enricher.display_analysis(analyses)

MCP Validation:
    - Cross-validate activity patterns with Cost Explorer ECS service costs
    - Flag discrepancies (low activity but high costs = potential issue)
    - Achieve ≥99.5% validation accuracy target

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 7 - ECS Activity Enricher
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


class ECSIdleSignal(str, Enum):
    """ECS idle/underutilization decommission signals (C1-C7)."""

    C1_LOW_UTILIZATION = "C1"  # Low CPU/Memory utilization
    C2_IDLE_TASKS = "C2"  # Zero running tasks for 90+ days
    C3_UNHEALTHY_SERVICES = "C3"  # Stuck/unhealthy service deployments
    C4_INEFFICIENT_COMPUTE = "C4"  # Inefficient Fargate vs EC2 split
    C5_LOW_COST_EFFICIENCY = "C5"  # High cost, low utilization
    C6_NETWORK_MODE_WASTE = "C6"  # awsvpc mode with low network traffic
    C7_LOGGING_COST_DRIVERS = "C7"  # High CloudWatch Logs ingestion costs


class ActivityPattern(str, Enum):
    """ECS cluster access pattern classification."""

    ACTIVE = "active"  # Production workload (>10 tasks avg)
    MODERATE = "moderate"  # Development/staging (1-10 tasks avg)
    LIGHT = "light"  # Test environment (<1 task avg)
    IDLE = "idle"  # No running tasks


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
class ECSActivityMetrics:
    """
    CloudWatch metrics for ECS cluster.

    Comprehensive activity metrics for decommission decision-making with
    C1-C7 signal framework.
    """

    avg_cpu_utilization_90d: float
    avg_memory_utilization_90d: float
    avg_running_tasks_90d: float
    max_running_tasks_90d: int
    min_running_tasks_90d: int
    service_count: int
    unhealthy_service_count: int
    fargate_task_count: int
    ec2_task_count: int
    total_vcpu: float
    total_memory_gb: float
    awsvpc_services_count: int = 0
    avg_network_bytes_per_day: float = 0.0
    cloudwatch_logs_bytes_per_month: float = 0.0
    cloudwatch_logs_cost_monthly: float = 0.0


@dataclass
class ECSActivityAnalysis:
    """
    ECS cluster activity analysis result.

    Comprehensive activity metrics for decommission decision-making with
    C1-C5 signal framework and cost impact analysis.
    """

    cluster_name: str
    cluster_arn: str
    region: str
    account_id: str
    metrics: ECSActivityMetrics
    activity_pattern: ActivityPattern
    idle_signals: List[ECSIdleSignal] = field(default_factory=list)
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    potential_savings: float = 0.0
    confidence: float = 0.0  # 0.0-1.0
    recommendation: DecommissionRecommendation = DecommissionRecommendation.KEEP
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cluster_name": self.cluster_name,
            "cluster_arn": self.cluster_arn,
            "region": self.region,
            "account_id": self.account_id,
            "metrics": {
                "avg_cpu_utilization_90d": self.metrics.avg_cpu_utilization_90d,
                "avg_memory_utilization_90d": self.metrics.avg_memory_utilization_90d,
                "avg_running_tasks_90d": self.metrics.avg_running_tasks_90d,
                "max_running_tasks_90d": self.metrics.max_running_tasks_90d,
                "min_running_tasks_90d": self.metrics.min_running_tasks_90d,
                "service_count": self.metrics.service_count,
                "unhealthy_service_count": self.metrics.unhealthy_service_count,
                "fargate_task_count": self.metrics.fargate_task_count,
                "ec2_task_count": self.metrics.ec2_task_count,
                "total_vcpu": self.metrics.total_vcpu,
                "total_memory_gb": self.metrics.total_memory_gb,
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


class ECSActivityEnricher:
    """
    ECS activity enricher for inventory resources.

    Analyzes ECS clusters for idle/underutilization patterns using CloudWatch
    metrics with C1-C5 signal framework.

    Capabilities:
    - Activity metrics analysis (90 day windows)
    - CPU/Memory utilization tracking
    - Task count trend analysis
    - Service health monitoring
    - Fargate vs EC2 cost efficiency
    - Comprehensive decommission recommendations

    Decommission Signals Generated:
    - C1: Low CPU/Memory utilization <5% (HIGH confidence: 0.90)
    - C2: Zero running tasks 90+ days (MEDIUM confidence: 0.75)
    - C3: Unhealthy services (MEDIUM confidence: 0.70)
    - C4: Inefficient Fargate vs EC2 split (MEDIUM confidence: 0.65)
    - C5: Low cost efficiency (MEDIUM confidence: 0.70)
    - C6: awsvpc mode with low network traffic (MEDIUM confidence: 0.65)
    - C7: High CloudWatch Logs cost >$50/month (MEDIUM confidence: 0.70)

    Example:
        >>> enricher = ECSActivityEnricher(
        ...     operational_profile='ops-profile',
        ...     region='ap-southeast-2'
        ... )
        >>> analyses = enricher.analyze_cluster_activity(
        ...     cluster_arns=['arn:aws:ecs:...']
        ... )
        >>> for analysis in analyses:
        ...     if ECSIdleSignal.C1_LOW_UTILIZATION in analysis.idle_signals:
        ...         print(f"Idle cluster: {analysis.cluster_name}")
    """

    # Activity thresholds for classification
    IDLE_UTILIZATION_THRESHOLD = 5.0  # percent CPU/Memory
    ACTIVE_TASKS_THRESHOLD = 10  # average running tasks
    MODERATE_TASKS_THRESHOLD = 1  # average running tasks

    # ECS pricing (ap-southeast-2) - placeholder, should use AWS Pricing API
    # Example: Fargate vCPU $0.04656/hour, Memory $0.00511/GB-hour
    DEFAULT_FARGATE_VCPU_HOURLY_RATE = 0.04656
    DEFAULT_FARGATE_MEMORY_GB_HOURLY_RATE = 0.00511
    DEFAULT_EC2_HOURLY_RATE = 0.12  # Average t3.medium cost

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: Optional[str] = None,
        lookback_days: int = 90,
        cache_ttl: int = 300,
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize ECS activity enricher.

        Args:
            operational_profile: AWS profile for operational account
            region: AWS region for ECS queries (default: ap-southeast-2)
            lookback_days: CloudWatch lookback period (default: 90)
            cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        """
        self.operational_profile = operational_profile or get_profile_for_operation("operational")
        self.region = region or "ap-southeast-2"
        self.lookback_days = min(lookback_days, 455)  # CloudWatch metrics retention
        self.cache_ttl = cache_ttl

        # Initialize AWS session
        self.session = create_operational_session(self.operational_profile)
        self.ecs_client = self.session.client("ecs", region_name=self.region)
        self.cloudwatch_client = self.session.client("cloudwatch", region_name=self.region)

        # Validation cache (5-minute TTL for performance)
        self._cache: Dict[str, Tuple[ECSActivityAnalysis, float]] = {}

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
                f"🔍 ECS Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )
        else:
            self.logger.debug(
                f"ECS Activity Enricher initialized: profile={self.operational_profile}, region={self.region}, lookback={self.lookback_days}d"
            )

    def analyze_cluster_activity(
        self,
        cluster_arns: Optional[List[str]] = None,
        region: Optional[str] = None,
        lookback_days: Optional[int] = None,
    ) -> List[ECSActivityAnalysis]:
        """
        Analyze ECS cluster activity for idle detection.

        Core analysis workflow:
        1. Query ECS clusters (all or specific ARNs)
        2. Get CloudWatch metrics for each cluster (90 day window)
        3. Classify activity pattern (active/moderate/light/idle)
        4. Generate C1-C5 decommission signals based on patterns
        5. Compute confidence score and recommendation
        6. Calculate cost impact and potential savings

        Args:
            cluster_arns: List of cluster ARNs to analyze (analyzes all if None)
            region: AWS region filter (default: use instance region)
            lookback_days: Lookback period (default: use instance default)

        Returns:
            List of activity analyses with decommission signals

        Example:
            >>> analyses = enricher.analyze_cluster_activity(
            ...     cluster_arns=['arn:aws:ecs:...']
            ... )
            >>> for analysis in analyses:
            ...     print(f"{analysis.cluster_name}: {analysis.recommendation.value}")
        """
        start_time = time.time()
        analysis_region = region or self.region
        lookback = lookback_days or self.lookback_days

        # v1.1.29: Removed verbose intro (Issue #6 - consolidate to single line)
        # Get ECS clusters
        clusters = self._get_ecs_clusters(cluster_arns, analysis_region)

        if not clusters:
            # v1.1.29: Silent return, summary will show "0 clusters" if needed
            return []

        # v1.1.29: Cluster count now included in summary line only

        analyses: List[ECSActivityAnalysis] = []

        with create_progress_bar(description="Analyzing ECS clusters") as progress:
            task = progress.add_task(f"Analyzing {len(clusters)} clusters", total=len(clusters))

            for cluster in clusters:
                try:
                    # Check cache first
                    cluster_arn = cluster["clusterArn"]
                    cache_key = f"{cluster_arn}:{lookback}"
                    cached_result = self._get_from_cache(cache_key)
                    if cached_result:
                        analyses.append(cached_result)
                        progress.update(task, advance=1)
                        continue

                    # Analyze cluster
                    analysis = self._analyze_cluster(cluster, lookback)

                    # Cache result
                    self._add_to_cache(cache_key, analysis)

                    analyses.append(analysis)

                except Exception as e:
                    self.logger.error(f"Failed to analyze ECS cluster {cluster.get('clusterName')}: {e}", exc_info=True)
                    print_warning(f"⚠️  Skipped {cluster.get('clusterName')}: {str(e)[:100]}")

                progress.update(task, advance=1)

        # Update performance metrics
        self.total_execution_time += time.time() - start_time

        # Display summary
        self._display_summary(analyses)

        return analyses

    def _get_ecs_clusters(self, cluster_arns: Optional[List[str]], region: str) -> List[Dict]:
        """
        Get ECS clusters from AWS API.

        Args:
            cluster_arns: Specific clusters to retrieve (retrieves all if None)
            region: AWS region filter

        Returns:
            List of ECS cluster metadata dictionaries
        """
        clusters = []

        try:
            if cluster_arns:
                # Get specific clusters
                if cluster_arns:
                    response = self.ecs_client.describe_clusters(
                        clusters=cluster_arns, include=["STATISTICS", "SETTINGS", "CONFIGURATIONS"]
                    )
                    clusters.extend(response.get("clusters", []))
            else:
                # Get all clusters
                paginator = self.ecs_client.get_paginator("list_clusters")
                for page in paginator.paginate():
                    if page["clusterArns"]:
                        response = self.ecs_client.describe_clusters(
                            clusters=page["clusterArns"], include=["STATISTICS", "SETTINGS", "CONFIGURATIONS"]
                        )
                        clusters.extend(response.get("clusters", []))

        except ClientError as e:
            self.logger.error(f"Failed to get ECS clusters: {e}")

        return clusters

    def _analyze_cluster(self, cluster: Dict, lookback_days: int) -> ECSActivityAnalysis:
        """
        Analyze individual ECS cluster.

        Args:
            cluster: ECS cluster metadata from describe_clusters
            lookback_days: CloudWatch metrics lookback period

        Returns:
            Comprehensive activity analysis with idle signals
        """
        cluster_name = cluster["clusterName"]

        # Get CloudWatch metrics
        metrics = self._get_cloudwatch_metrics(cluster, lookback_days)

        # Classify activity pattern
        activity_pattern = self._classify_activity_pattern(metrics)

        # Generate idle signals
        idle_signals = self._generate_idle_signals(metrics, activity_pattern)

        # Calculate costs
        monthly_cost = self._calculate_monthly_cost(cluster, metrics)
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

        return ECSActivityAnalysis(
            cluster_name=cluster_name,
            cluster_arn=cluster["clusterArn"],
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

    def _get_cloudwatch_metrics(self, cluster: Dict, lookback_days: int) -> ECSActivityMetrics:
        """
        Get CloudWatch metrics for ECS cluster.

        Metrics queried:
        - CPUUtilization (90-day average)
        - MemoryUtilization (90-day average)
        - RunningTasksCount (90-day average/min/max)

        Args:
            cluster: ECS cluster metadata
            lookback_days: Lookback period for metrics

        Returns:
            Comprehensive activity metrics
        """
        cluster_name = cluster["clusterName"]
        now = datetime.utcnow()

        # Query CPUUtilization
        cpu_util = self._get_metric_average(cluster_name, "CPUUtilization", now - timedelta(days=lookback_days), now)

        # Query MemoryUtilization
        memory_util = self._get_metric_average(
            cluster_name, "MemoryUtilization", now - timedelta(days=lookback_days), now
        )

        # Query RunningTasksCount
        tasks_stats = self._get_metric_statistics(
            cluster_name, "RunningTasksCount", now - timedelta(days=lookback_days), now
        )

        # Get service information
        service_count, unhealthy_service_count = self._get_service_health(cluster_name)

        # Get task launch type split
        fargate_count, ec2_count = self._get_task_launch_types(cluster_name)

        # Calculate total capacity
        total_vcpu, total_memory_gb = self._calculate_cluster_capacity(cluster)

        # C6: Network mode analysis
        awsvpc_count, avg_network_bytes = self._get_network_mode_metrics(cluster_name)

        # C7: CloudWatch Logs cost analysis
        logs_bytes, logs_cost = self._get_cloudwatch_logs_metrics(cluster_name)

        return ECSActivityMetrics(
            avg_cpu_utilization_90d=cpu_util,
            avg_memory_utilization_90d=memory_util,
            avg_running_tasks_90d=tasks_stats.get("average", 0.0),
            max_running_tasks_90d=int(tasks_stats.get("maximum", 0)),
            min_running_tasks_90d=int(tasks_stats.get("minimum", 0)),
            service_count=service_count,
            unhealthy_service_count=unhealthy_service_count,
            fargate_task_count=fargate_count,
            ec2_task_count=ec2_count,
            total_vcpu=total_vcpu,
            total_memory_gb=total_memory_gb,
            awsvpc_services_count=awsvpc_count,
            avg_network_bytes_per_day=avg_network_bytes,
            cloudwatch_logs_bytes_per_month=logs_bytes,
            cloudwatch_logs_cost_monthly=logs_cost,
        )

    def _get_metric_average(
        self, cluster_name: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> float:
        """
        Get CloudWatch metric average.

        Args:
            cluster_name: ECS cluster name
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Metric average value, or 0.0 if no data
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/ECS",
                MetricName=metric_name,
                Dimensions=[{"Name": "ClusterName", "Value": cluster_name}],
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
            self.logger.debug(f"CloudWatch query failed for {cluster_name}/{metric_name}: {e}")
            return 0.0

    def _get_metric_statistics(
        self, cluster_name: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> Dict[str, float]:
        """
        Get CloudWatch metric statistics (average, min, max).

        Args:
            cluster_name: ECS cluster name
            metric_name: CloudWatch metric name
            start_time: Query start time
            end_time: Query end time

        Returns:
            Dictionary with average, minimum, maximum values
        """
        try:
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace="AWS/ECS",
                MetricName=metric_name,
                Dimensions=[{"Name": "ClusterName", "Value": cluster_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Average", "Minimum", "Maximum"],
            )

            datapoints = response["Datapoints"]
            if not datapoints:
                return {"average": 0.0, "minimum": 0.0, "maximum": 0.0}

            # Increment query counter
            self.query_count += 1

            return {
                "average": sum(d["Average"] for d in datapoints) / len(datapoints),
                "minimum": min(d["Minimum"] for d in datapoints),
                "maximum": max(d["Maximum"] for d in datapoints),
            }

        except ClientError as e:
            self.logger.debug(f"CloudWatch query failed for {cluster_name}/{metric_name}: {e}")
            return {"average": 0.0, "minimum": 0.0, "maximum": 0.0}

    def _get_service_health(self, cluster_name: str) -> Tuple[int, int]:
        """
        Get service count and unhealthy service count.

        Args:
            cluster_name: ECS cluster name

        Returns:
            Tuple of (total_services, unhealthy_services)
        """
        try:
            # List services
            service_arns = []
            paginator = self.ecs_client.get_paginator("list_services")
            for page in paginator.paginate(cluster=cluster_name):
                service_arns.extend(page["serviceArns"])

            if not service_arns:
                return 0, 0

            # Describe services (batch up to 10 at a time)
            unhealthy_count = 0
            for i in range(0, len(service_arns), 10):
                batch = service_arns[i : i + 10]
                response = self.ecs_client.describe_services(cluster=cluster_name, services=batch)

                for service in response["services"]:
                    desired = service.get("desiredCount", 0)
                    running = service.get("runningCount", 0)
                    if desired > 0 and running < desired:
                        unhealthy_count += 1

            return len(service_arns), unhealthy_count

        except ClientError as e:
            self.logger.debug(f"Failed to get service health for {cluster_name}: {e}")
            return 0, 0

    def _get_task_launch_types(self, cluster_name: str) -> Tuple[int, int]:
        """
        Get count of Fargate vs EC2 tasks.

        Args:
            cluster_name: ECS cluster name

        Returns:
            Tuple of (fargate_count, ec2_count)
        """
        try:
            # List tasks
            task_arns = []
            paginator = self.ecs_client.get_paginator("list_tasks")
            for page in paginator.paginate(cluster=cluster_name):
                task_arns.extend(page["taskArns"])

            if not task_arns:
                return 0, 0

            # Describe tasks (batch up to 100 at a time)
            fargate_count = 0
            ec2_count = 0

            for i in range(0, len(task_arns), 100):
                batch = task_arns[i : i + 100]
                response = self.ecs_client.describe_tasks(cluster=cluster_name, tasks=batch)

                for task in response["tasks"]:
                    launch_type = task.get("launchType", "EC2")
                    if launch_type == "FARGATE":
                        fargate_count += 1
                    else:
                        ec2_count += 1

            return fargate_count, ec2_count

        except ClientError as e:
            self.logger.debug(f"Failed to get task launch types for {cluster_name}: {e}")
            return 0, 0

    def _calculate_cluster_capacity(self, cluster: Dict) -> Tuple[float, float]:
        """
        Calculate total cluster vCPU and memory capacity.

        Args:
            cluster: ECS cluster metadata

        Returns:
            Tuple of (total_vcpu, total_memory_gb)
        """
        # Use registered container instances count as proxy
        registered_instances = cluster.get("registeredContainerInstancesCount", 0)

        # Estimate based on average instance size (t3.medium = 2 vCPU, 4 GB)
        estimated_vcpu = registered_instances * 2
        estimated_memory_gb = registered_instances * 4

        return float(estimated_vcpu), float(estimated_memory_gb)

    def _get_network_mode_metrics(self, cluster_name: str) -> Tuple[int, float]:
        """
        Get network mode metrics for C6 signal (awsvpc mode waste).

        Args:
            cluster_name: ECS cluster name

        Returns:
            Tuple of (awsvpc_services_count, avg_network_bytes_per_day)
        """
        try:
            # List services with awsvpc network mode
            awsvpc_services = []
            paginator = self.ecs_client.get_paginator("list_services")
            for page in paginator.paginate(cluster=cluster_name):
                service_arns = page["serviceArns"]
                if not service_arns:
                    continue

                # Describe services to check network configuration
                response = self.ecs_client.describe_services(cluster=cluster_name, services=service_arns)

                for service in response["services"]:
                    # Check network configuration for awsvpc mode
                    network_config = service.get("networkConfiguration", {})
                    awsvpc_config = network_config.get("awsvpcConfiguration", {})
                    if awsvpc_config:
                        awsvpc_services.append(service["serviceName"])

            if not awsvpc_services:
                return 0, 0.0

            # Query network bytes transferred (approximation using CloudWatch)
            # Note: VPC Flow Logs would be more accurate, but requires additional setup
            # Using NetworkRxBytes + NetworkTxBytes as proxy
            now = datetime.utcnow()
            start_time = now - timedelta(days=self.lookback_days)

            try:
                # Query average network bytes for cluster
                rx_bytes = self._get_metric_average(cluster_name, "NetworkRxBytes", start_time, now)
                tx_bytes = self._get_metric_average(cluster_name, "NetworkTxBytes", start_time, now)

                avg_network_bytes_per_day = (rx_bytes + tx_bytes) / max(1, self.lookback_days)

            except Exception as e:
                self.logger.debug(f"Network metrics unavailable for {cluster_name}: {e}")
                avg_network_bytes_per_day = 0.0

            return len(awsvpc_services), avg_network_bytes_per_day

        except ClientError as e:
            self.logger.debug(f"Failed to get network mode metrics for {cluster_name}: {e}")
            return 0, 0.0

    def _get_cloudwatch_logs_metrics(self, cluster_name: str) -> Tuple[float, float]:
        """
        Get CloudWatch Logs metrics for C7 signal (high logging costs).

        Args:
            cluster_name: ECS cluster name

        Returns:
            Tuple of (bytes_per_month, monthly_cost)
        """
        try:
            # Query CloudWatch Logs for ECS cluster log groups
            # Pattern: /ecs/{cluster_name}/* or /aws/ecs/{cluster_name}/*
            logs_client = self.session.client("logs", region_name=self.region)

            log_groups = []
            try:
                # Common ECS log group patterns
                patterns = [f"/ecs/{cluster_name}", f"/aws/ecs/{cluster_name}", f"ecs-{cluster_name}"]

                for pattern in patterns:
                    try:
                        response = logs_client.describe_log_groups(logGroupNamePrefix=pattern)
                        log_groups.extend(response.get("logGroups", []))
                    except Exception:
                        continue

            except ClientError:
                # Log groups might not exist
                return 0.0, 0.0

            if not log_groups:
                return 0.0, 0.0

            # Calculate total stored bytes
            total_bytes = sum(lg.get("storedBytes", 0) for lg in log_groups)

            # Estimate monthly ingestion cost
            # CloudWatch Logs pricing (ap-southeast-2): ~$0.50/GB ingestion
            # Estimate monthly ingestion as current stored bytes
            bytes_per_month = total_bytes
            gb_per_month = bytes_per_month / (1024**3)
            monthly_cost = gb_per_month * 0.50  # $0.50/GB

            return float(bytes_per_month), float(monthly_cost)

        except ClientError as e:
            self.logger.debug(f"Failed to get CloudWatch Logs metrics for {cluster_name}: {e}")
            return 0.0, 0.0

    def _classify_activity_pattern(self, metrics: ECSActivityMetrics) -> ActivityPattern:
        """
        Classify ECS activity pattern.

        Classification:
        - ACTIVE: >10 tasks avg (production)
        - MODERATE: 1-10 tasks avg (dev/staging)
        - LIGHT: <1 task avg (test)
        - IDLE: 0 tasks

        Args:
            metrics: ECS activity metrics

        Returns:
            ActivityPattern enum
        """
        avg_tasks = metrics.avg_running_tasks_90d

        if avg_tasks >= self.ACTIVE_TASKS_THRESHOLD:
            return ActivityPattern.ACTIVE
        elif avg_tasks >= self.MODERATE_TASKS_THRESHOLD:
            return ActivityPattern.MODERATE
        elif avg_tasks > 0:
            return ActivityPattern.LIGHT
        else:
            return ActivityPattern.IDLE

    def _generate_idle_signals(self, metrics: ECSActivityMetrics, pattern: ActivityPattern) -> List[ECSIdleSignal]:
        """
        Generate C1-C7 idle signals.

        Signal generation rules:
        - C1: CPU/Memory utilization < 5% → HIGH confidence (0.90)
        - C2: Zero running tasks 90+ days → MEDIUM confidence (0.75)
        - C3: Unhealthy services > 0 → MEDIUM confidence (0.70)
        - C4: Inefficient compute split → MEDIUM confidence (0.65)
        - C5: Low cost efficiency → MEDIUM confidence (0.70)
        - C6: awsvpc mode with low network traffic → MEDIUM confidence (0.65)
        - C7: High CloudWatch Logs cost → MEDIUM confidence (0.70)

        Args:
            metrics: ECS activity metrics
            pattern: Activity pattern classification

        Returns:
            List of applicable ECSIdleSignal enums
        """
        signals: List[ECSIdleSignal] = []

        # C1: Low CPU/Memory utilization (<5%)
        if (
            metrics.avg_cpu_utilization_90d < self.IDLE_UTILIZATION_THRESHOLD
            and metrics.avg_memory_utilization_90d < self.IDLE_UTILIZATION_THRESHOLD
        ):
            signals.append(ECSIdleSignal.C1_LOW_UTILIZATION)

        # C2: Zero running tasks
        if metrics.avg_running_tasks_90d == 0:
            signals.append(ECSIdleSignal.C2_IDLE_TASKS)

        # C3: Unhealthy services
        if metrics.unhealthy_service_count > 0:
            signals.append(ECSIdleSignal.C3_UNHEALTHY_SERVICES)

        # C4: Inefficient Fargate vs EC2 split
        # Flag if using expensive Fargate for idle workloads
        if pattern in [ActivityPattern.IDLE, ActivityPattern.LIGHT]:
            if metrics.fargate_task_count > metrics.ec2_task_count:
                signals.append(ECSIdleSignal.C4_INEFFICIENT_COMPUTE)

        # C5: Low cost efficiency (low utilization with tasks)
        if pattern in [ActivityPattern.IDLE, ActivityPattern.LIGHT]:
            if metrics.avg_running_tasks_90d > 0:
                signals.append(ECSIdleSignal.C5_LOW_COST_EFFICIENCY)

        # C6: awsvpc mode with low network traffic (<100MB/day)
        if metrics.awsvpc_services_count > 0:
            mb_per_day = metrics.avg_network_bytes_per_day / (1024**2)
            if mb_per_day < 100:  # Less than 100MB/day
                signals.append(ECSIdleSignal.C6_NETWORK_MODE_WASTE)

        # C7: High CloudWatch Logs costs (>$50/month)
        if metrics.cloudwatch_logs_cost_monthly > 50:
            signals.append(ECSIdleSignal.C7_LOGGING_COST_DRIVERS)

        return signals

    def _calculate_confidence(self, signals: List[ECSIdleSignal]) -> float:
        """
        Calculate idle confidence score.

        Signal weights:
        - C1: 0.90 (low CPU/Memory utilization)
        - C2: 0.75 (zero running tasks)
        - C3: 0.70 (unhealthy services)
        - C4: 0.65 (inefficient compute)
        - C5: 0.70 (low cost efficiency)
        - C6: 0.65 (network mode waste)
        - C7: 0.70 (logging cost drivers)

        Args:
            signals: List of idle signals

        Returns:
            Confidence score (0.0-1.0)
        """
        if not signals:
            return 0.0

        # Signal confidence mapping
        signal_confidence = {
            ECSIdleSignal.C1_LOW_UTILIZATION: 0.90,
            ECSIdleSignal.C2_IDLE_TASKS: 0.75,
            ECSIdleSignal.C3_UNHEALTHY_SERVICES: 0.70,
            ECSIdleSignal.C4_INEFFICIENT_COMPUTE: 0.65,
            ECSIdleSignal.C5_LOW_COST_EFFICIENCY: 0.70,
            ECSIdleSignal.C6_NETWORK_MODE_WASTE: 0.65,
            ECSIdleSignal.C7_LOGGING_COST_DRIVERS: 0.70,
        }

        # Use maximum confidence from all signals
        return max(signal_confidence.get(signal, 0.0) for signal in signals)

    def _calculate_monthly_cost(self, cluster: Dict, metrics: ECSActivityMetrics) -> float:
        """
        Calculate monthly ECS cluster cost.

        Uses AWS Pricing API to get hourly rate.
        Fallback to placeholder pricing if API unavailable.

        Args:
            cluster: ECS cluster metadata
            metrics: Activity metrics

        Returns:
            Monthly cost estimate
        """
        # TODO: Implement AWS Pricing API query
        # For now, use placeholder pricing
        monthly_hours = 730  # Average hours per month

        fargate_cost = (
            metrics.fargate_task_count
            * (
                metrics.total_vcpu * self.DEFAULT_FARGATE_VCPU_HOURLY_RATE
                + metrics.total_memory_gb * self.DEFAULT_FARGATE_MEMORY_GB_HOURLY_RATE
            )
            * monthly_hours
        )

        ec2_cost = metrics.ec2_task_count * self.DEFAULT_EC2_HOURLY_RATE * monthly_hours

        return fargate_cost + ec2_cost

    def _calculate_potential_savings(self, annual_cost: float, confidence: float, pattern: ActivityPattern) -> float:
        """
        Calculate potential annual savings.

        Savings scenarios:
        - IDLE: 100% savings (decommission)
        - LIGHT: 80% savings (optimize)
        - MODERATE: 40% savings (rightsize)
        - ACTIVE: 0% savings (keep as-is)

        Args:
            annual_cost: Annual ECS cluster cost
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
        self, pattern: ActivityPattern, signals: List[ECSIdleSignal], confidence: float
    ) -> DecommissionRecommendation:
        """
        Generate optimization recommendation.

        Recommendation logic:
        - DECOMMISSION: confidence ≥ 0.90 OR C2 signal present
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
        if confidence >= 0.90 or ECSIdleSignal.C2_IDLE_TASKS in signals:
            return DecommissionRecommendation.DECOMMISSION

        # Medium confidence - needs investigation
        if confidence >= 0.70:
            return DecommissionRecommendation.INVESTIGATE

        # Moderate underutilization - optimize
        if confidence >= 0.50:
            return DecommissionRecommendation.OPTIMIZE

        # Low confidence - keep resource
        return DecommissionRecommendation.KEEP

    def display_analysis(self, analyses: List[ECSActivityAnalysis]) -> Optional["Table"]:
        """
        Display ECS activity analysis in Rich table format.

        Creates comprehensive activity analysis table with:
        - Cluster name and region
        - Activity metrics (CPU/Memory utilization, task count)
        - Decommission signals (C1-C5)
        - Recommendation and confidence

        Args:
            analyses: List of ECSActivityAnalysis objects

        Returns:
            Table object for tree renderer integration (v1.1.27 Track 1 fix)
        """
        if not analyses:
            print_warning("No ECS clusters to display")
            return None

        # Create analysis table
        # v1.1.27: Fixed column width constraints (Track 3 - user reported truncation)
        table = create_table(
            title="ECS Cluster Activity Analysis",
            columns=[
                {"name": "Cluster Name", "style": "cyan", "no_wrap": False},
                {"name": "CPU %", "style": "bright_yellow", "justify": "right", "width": 8},
                {"name": "Mem %", "style": "bright_yellow", "justify": "right", "width": 8},
                {"name": "Tasks", "style": "white", "justify": "right", "width": 6},
                {"name": "Signals", "style": "bright_magenta", "width": 15},
                {"name": "Cost/mo", "style": "white", "justify": "right", "width": 10},
                {"name": "Savings", "style": "bright_green", "justify": "right", "width": 10},
                {"name": "Action", "style": "bold", "width": 12},
            ],
        )

        for analysis in analyses:
            # Skip rows with zero activity (blank rows)
            if analysis.metrics.avg_running_tasks_90d == 0 and analysis.metrics.avg_cpu_utilization_90d == 0:
                continue

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
                analysis.cluster_name,
                f"{analysis.metrics.avg_cpu_utilization_90d:.1f}%",
                f"{analysis.metrics.avg_memory_utilization_90d:.1f}%",
                f"{analysis.metrics.avg_running_tasks_90d:.1f}",
                signals_str,
                format_cost(analysis.monthly_cost),
                format_cost(analysis.potential_savings / 12),  # Monthly savings
                rec_str,
            )

        # Return table for tree renderer integration (v1.1.27 Track 1 fix)
        return table

    def _display_summary(self, analyses: List[ECSActivityAnalysis]) -> None:
        """Display analysis summary statistics."""
        if not analyses:
            return

        total = len(analyses)
        must_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.DECOMMISSION)
        should_count = sum(1 for a in analyses if a.recommendation == DecommissionRecommendation.INVESTIGATE)

        # Calculate total savings
        total_savings = sum(a.potential_savings for a in analyses)

        # v1.1.29: Compact 1-line summary (Issue #6 - consolidated from 4 lines to 1)
        summary = (
            f"🐳 ECS: {total} clusters | {must_count} MUST + {should_count} SHOULD | Savings: ${total_savings:,.0f}/yr"
        )
        console.print(summary)

    def enrich_ecs_activity(self, ecs_resources: "pd.DataFrame") -> "pd.DataFrame":
        """
        Enrich ECS resources DataFrame with C1-C7 activity signals.

        Dashboard integration method that wraps analyze_cluster_activity() for
        DataFrame input/output pattern (follows S3/AppStream enricher convention).

        Args:
            ecs_resources: DataFrame with 'name' or 'cluster_name' or 'arn' columns from discovery

        Returns:
            Enhanced DataFrame with activity signal columns (c1-c7, confidence, recommendation)

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'cluster_name': ['prod-cluster', 'dev-cluster']})
            >>> enriched = enricher.enrich_ecs_activity(df)
            >>> print(enriched[['cluster_name', 'confidence', 'recommendation']])
        """
        import pandas as pd

        # Graceful degradation on empty input
        if ecs_resources.empty:
            return ecs_resources

        # Extract cluster identifiers from DataFrame
        # Support multiple column naming conventions from discovery layer
        cluster_identifiers = []
        if "arn" in ecs_resources.columns:
            cluster_identifiers = ecs_resources["arn"].tolist()
        elif "cluster_arn" in ecs_resources.columns:
            cluster_identifiers = ecs_resources["cluster_arn"].tolist()
        elif "cluster_name" in ecs_resources.columns:
            cluster_identifiers = ecs_resources["cluster_name"].tolist()
        elif "name" in ecs_resources.columns:
            cluster_identifiers = ecs_resources["name"].tolist()

        if not cluster_identifiers:
            # No recognizable cluster identifiers - return input unchanged
            if self.output_controller.verbose:
                print_warning("⚠️  ECS DataFrame missing cluster identifiers (arn/cluster_name/name columns)")
            return ecs_resources

        # Call core analysis method
        try:
            analyses = self.analyze_cluster_activity(cluster_arns=cluster_identifiers)
        except Exception as e:
            self.logger.error(f"ECS activity analysis failed: {str(e)}")
            if self.output_controller.verbose:
                print_error(f"❌ ECS analysis error: {str(e)}")
            # Return input unchanged on error (graceful degradation)
            return ecs_resources

        # Convert analysis results to DataFrame columns
        enriched = ecs_resources.copy()

        # Build lookup dict from analyses (cluster_name -> analysis)
        analysis_lookup = {a.cluster_name: a for a in analyses}

        # Enrich with activity metrics and signals
        for idx, row in enriched.iterrows():
            # Find matching analysis
            cluster_key = row.get("cluster_name") or row.get("name") or row.get("arn", "")
            analysis = analysis_lookup.get(cluster_key)

            if analysis:
                # Add signal columns (using correct ECSIdleSignal enum names)
                enriched.at[idx, "c1_low_utilization"] = ECSIdleSignal.C1_LOW_UTILIZATION in analysis.idle_signals
                enriched.at[idx, "c2_idle_tasks"] = ECSIdleSignal.C2_IDLE_TASKS in analysis.idle_signals
                enriched.at[idx, "c3_unhealthy_services"] = ECSIdleSignal.C3_UNHEALTHY_SERVICES in analysis.idle_signals
                enriched.at[idx, "c4_inefficient_compute"] = (
                    ECSIdleSignal.C4_INEFFICIENT_COMPUTE in analysis.idle_signals
                )
                enriched.at[idx, "c5_low_cost_efficiency"] = (
                    ECSIdleSignal.C5_LOW_COST_EFFICIENCY in analysis.idle_signals
                )
                enriched.at[idx, "c6_network_mode_waste"] = ECSIdleSignal.C6_NETWORK_MODE_WASTE in analysis.idle_signals
                enriched.at[idx, "c7_logging_cost_drivers"] = (
                    ECSIdleSignal.C7_LOGGING_COST_DRIVERS in analysis.idle_signals
                )

                # Add metrics (using correct ECSActivityMetrics field names with _90d suffix)
                enriched.at[idx, "cpu_utilization_90d"] = analysis.metrics.avg_cpu_utilization_90d
                enriched.at[idx, "memory_utilization_90d"] = analysis.metrics.avg_memory_utilization_90d
                enriched.at[idx, "avg_running_tasks"] = analysis.metrics.avg_running_tasks_90d
                enriched.at[idx, "activity_pattern"] = analysis.activity_pattern.value
                enriched.at[idx, "confidence"] = analysis.confidence
                enriched.at[idx, "recommendation"] = analysis.recommendation.value
                enriched.at[idx, "monthly_cost"] = analysis.monthly_cost
                enriched.at[idx, "potential_savings"] = analysis.potential_savings
            else:
                # No analysis available - mark as unknown
                enriched.at[idx, "activity_pattern"] = "UNKNOWN"
                enriched.at[idx, "confidence"] = 0.0
                enriched.at[idx, "recommendation"] = "KEEP"

        return enriched

    def _get_from_cache(self, cache_key: str) -> Optional[ECSActivityAnalysis]:
        """Get analysis from cache if still valid."""
        if cache_key in self._cache:
            result, cache_time = self._cache[cache_key]
            if time.time() - cache_time < self.cache_ttl:
                return result
        return None

    def _add_to_cache(self, cache_key: str, analysis: ECSActivityAnalysis) -> None:
        """Add analysis to cache with current timestamp."""
        self._cache[cache_key] = (analysis, time.time())


# ═════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═════════════════════════════════════════════════════════════════════════════


def create_ecs_activity_enricher(
    operational_profile: Optional[str] = None, region: Optional[str] = None, lookback_days: int = 90
) -> ECSActivityEnricher:
    """
    Factory function to create ECSActivityEnricher.

    Provides clean initialization pattern following enterprise architecture
    with automatic profile resolution and sensible defaults.

    Args:
        operational_profile: AWS profile for operational account
        region: AWS region (default: ap-southeast-2)
        lookback_days: CloudWatch lookback period (default: 90)

    Returns:
        Initialized ECSActivityEnricher instance

    Example:
        >>> enricher = create_ecs_activity_enricher()
        >>> # Enricher ready for activity analysis
        >>> analyses = enricher.analyze_cluster_activity(...)
    """
    return ECSActivityEnricher(operational_profile=operational_profile, region=region, lookback_days=lookback_days)


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    # Core enricher class
    "ECSActivityEnricher",
    # Data models
    "ECSActivityAnalysis",
    "ECSActivityMetrics",
    "ECSIdleSignal",
    "ActivityPattern",
    "DecommissionRecommendation",
    # Factory function
    "create_ecs_activity_enricher",
]
