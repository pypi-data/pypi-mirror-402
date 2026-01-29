#!/usr/bin/env python3
"""
ALB Activity Enricher - Application Load Balancer Health Signals (A1-A5)

Analyzes Application Load Balancer activity patterns using CloudWatch metrics
to identify underutilized or idle ALBs for cost optimization.

Decommission Signals (A1-A5):
- A1: Zero active connections (45 points) - No connections for 90+ days
- A2: Low request count (25 points) - <100 requests/day average
- A3: No healthy targets (15 points) - All targets unhealthy for 30+ days
- A4: Low data transfer (10 points) - <100 MB/day transferred
- A5: High error rate (5 points) - >50% 4XX/5XX errors

Pattern: Reuses ActivityEnricher structure (KISS/DRY/LEAN)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable ALB enrichment
- Enterprise SDLC: Cost optimization with evidence-based signals
- KISS/DRY/LEAN: Single enricher, CloudWatch consolidation

Usage:
    from runbooks.inventory.enrichers.alb_activity_enricher import ALBActivityEnricher

    enricher = ALBActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='ap-southeast-2'
    )

    enriched_df = enricher.enrich_alb_activity(discovery_df)

    # Adds columns:
    # - active_connection_count_90d: Sum of ActiveConnectionCount over 90 days
    # - request_count_90d: Sum of RequestCount over 90 days
    # - healthy_host_count_avg: Average HealthyHostCount over 30 days
    # - data_processed_bytes_90d: Sum of ProcessedBytes over 90 days
    # - http_code_4xx_count: Sum of HTTPCode_Target_4XX_Count
    # - http_code_5xx_count: Sum of HTTPCode_Target_5XX_Count
    # - a1_signal: Boolean (zero connections)
    # - a2_signal: Boolean (low requests)
    # - a3_signal: Boolean (no healthy targets)
    # - a4_signal: Boolean (low data transfer)
    # - a5_signal: Boolean (high error rate)
    # - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
    # - enrichment_status: String (SUCCESS/FAILED/PENDING)
    # - enrichment_error: String (error message if failed)
    # - decommission_score: Total score (0-100 scale)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.20 FinOps Dashboard Enhancements
Track: Track 5 - ALB Activity Enrichment
"""

import pandas as pd
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
    create_timeout_protected_client,
)
from runbooks.common.rich_utils import (
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar,
    console,
)
from runbooks.common.output_controller import OutputController

logger = logging.getLogger(__name__)

# ALB signal weights (0-100 scale)
DEFAULT_ALB_WEIGHTS = {
    "A1": 45,  # Zero active connections
    "A2": 25,  # Low request count
    "A3": 15,  # No healthy targets
    "A4": 10,  # Low data transfer
    "A5": 5,  # High error rate
}


class ALBActivityEnricher:
    """
    ALB activity enrichment using CloudWatch metrics for A1-A5 decommission signals.

    Consolidates CloudWatch ALB metrics into actionable decommission signals:
    - ActiveConnectionCount (A1: zero connections)
    - RequestCount (A2: low traffic)
    - HealthyHostCount (A3: no healthy targets)
    - ProcessedBytes (A4: low data transfer)
    - HTTPCode_Target_4XX/5XX (A5: error rate)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
    ):
        """
        Initialize ALB activity enricher.

        Args:
            operational_profile: AWS profile for CloudWatch API access
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)

        Profile Requirements:
            - cloudwatch:GetMetricStatistics (ALB namespace metrics)
            - elasticloadbalancing:DescribeLoadBalancers (ALB metadata)
        """
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        self.session = create_operational_session(resolved_profile)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.elbv2 = create_timeout_protected_client(self.session, "elbv2", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        if self.output_controller.verbose:
            print_info(f"🔍 ALBActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: ActiveConnectionCount, RequestCount, HealthyHostCount, ProcessedBytes, HTTPCode")
        else:
            logger.debug(f"ALBActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_alb_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich ALB DataFrame with A1-A5 activity signals.

        Args:
            df: DataFrame with load_balancer_arn column

        Returns:
            DataFrame with ALB activity columns and decommission signals

        Columns Added:
            - active_connection_count_90d: Sum of connections over 90 days
            - request_count_90d: Sum of requests over 90 days
            - healthy_host_count_avg: Average healthy targets over 30 days
            - data_processed_bytes_90d: Sum of bytes processed
            - http_code_4xx_count: Sum of 4XX errors
            - http_code_5xx_count: Sum of 5XX errors
            - a1_signal: Zero connections (Boolean)
            - a2_signal: Low requests (Boolean)
            - a3_signal: No healthy targets (Boolean)
            - a4_signal: Low data transfer (Boolean)
            - a5_signal: High error rate (Boolean)
            - cloudwatch_enrichment_success: Boolean (enrichment succeeded)
            - enrichment_status: String (SUCCESS/FAILED/PENDING)
            - enrichment_error: String (error message if failed)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP/UNKNOWN
        """
        # Graceful degradation: skip enrichment if no load balancers discovered
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  ALB enrichment skipped - no load balancers discovered")
            logger.info("ALB enrichment skipped - empty DataFrame")
            return df

        # Prerequisite validation: check for required column
        if "load_balancer_arn" not in df.columns:
            # v1.1.20: Changed to DEBUG - graceful degradation, not an error condition
            logger.debug(
                "ALB enrichment skipped - load_balancer_arn column not found",
                extra={
                    "reason": "Missing required column",
                    "signal_impact": "A1-A5 signals unavailable",
                    "alternative": "Ensure ALB discovery completed before enrichment",
                },
            )
            return df

        if self.output_controller.verbose:
            print_info(f"🔄 Starting ALB activity enrichment for {len(df)} load balancers...")
        else:
            logger.info(f"ALB activity enrichment started for {len(df)} load balancers")

        # Initialize activity columns with defaults
        activity_columns = {
            "active_connection_count_90d": 0,
            "request_count_90d": 0,
            "healthy_host_count_avg": 0.0,
            "data_processed_bytes_90d": 0,
            "http_code_4xx_count": 0,
            "http_code_5xx_count": 0,
            "a1_signal": False,
            "a2_signal": False,
            "a3_signal": False,
            "a4_signal": False,
            "a5_signal": False,
            "cloudwatch_enrichment_success": False,
            "enrichment_status": "PENDING",
            "enrichment_error": "",
            "decommission_score": 0,
            "decommission_tier": "KEEP",
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # Enrich each ALB with CloudWatch metrics
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]CloudWatch ALB metrics...", total=len(df))

            for idx, row in df.iterrows():
                alb_arn = row.get("load_balancer_arn", "")

                if not alb_arn or alb_arn == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Extract ALB name from ARN for CloudWatch dimensions
                    # Format: arn:aws:elasticloadbalancing:region:account-id:loadbalancer/app/name/id
                    alb_name_parts = alb_arn.split(":loadbalancer/")
                    if len(alb_name_parts) == 2:
                        alb_full_name = alb_name_parts[1]  # app/name/id
                    else:
                        logger.debug(f"Invalid ALB ARN format: {alb_arn}")
                        df.at[idx, "enrichment_status"] = "FAILED"
                        df.at[idx, "enrichment_error"] = "Invalid ALB ARN format"
                        progress.update(task, advance=1)
                        continue

                    # A1: Active Connection Count (90 days)
                    connection_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/ApplicationELB",
                        MetricName="ActiveConnectionCount",
                        Dimensions=[{"Name": "LoadBalancer", "Value": alb_full_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1-day aggregation
                        Statistics=["Sum"],
                        Unit="Count",
                    )

                    connection_datapoints = connection_response.get("Datapoints", [])
                    if connection_datapoints:
                        total_connections = sum([dp["Sum"] for dp in connection_datapoints])
                        df.at[idx, "active_connection_count_90d"] = int(total_connections)
                        df.at[idx, "cloudwatch_enrichment_success"] = True
                        df.at[idx, "enrichment_status"] = "SUCCESS"

                    # A2: Request Count (90 days)
                    request_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/ApplicationELB",
                        MetricName="RequestCount",
                        Dimensions=[{"Name": "LoadBalancer", "Value": alb_full_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                        Unit="Count",
                    )

                    request_datapoints = request_response.get("Datapoints", [])
                    if request_datapoints:
                        total_requests = sum([dp["Sum"] for dp in request_datapoints])
                        df.at[idx, "request_count_90d"] = int(total_requests)
                        df.at[idx, "cloudwatch_enrichment_success"] = True
                        df.at[idx, "enrichment_status"] = "SUCCESS"

                    # A3: Healthy Host Count (30 days average)
                    healthy_start = end_time - timedelta(days=30)
                    healthy_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/ApplicationELB",
                        MetricName="HealthyHostCount",
                        Dimensions=[{"Name": "LoadBalancer", "Value": alb_full_name}],
                        StartTime=healthy_start,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Average"],
                        Unit="Count",
                    )

                    healthy_datapoints = healthy_response.get("Datapoints", [])
                    if healthy_datapoints:
                        avg_healthy_hosts = sum([dp["Average"] for dp in healthy_datapoints]) / len(healthy_datapoints)
                        df.at[idx, "healthy_host_count_avg"] = round(avg_healthy_hosts, 2)
                        df.at[idx, "cloudwatch_enrichment_success"] = True
                        df.at[idx, "enrichment_status"] = "SUCCESS"

                    # A4: Processed Bytes (90 days)
                    bytes_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/ApplicationELB",
                        MetricName="ProcessedBytes",
                        Dimensions=[{"Name": "LoadBalancer", "Value": alb_full_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                        Unit="Bytes",
                    )

                    bytes_datapoints = bytes_response.get("Datapoints", [])
                    if bytes_datapoints:
                        total_bytes = sum([dp["Sum"] for dp in bytes_datapoints])
                        df.at[idx, "data_processed_bytes_90d"] = int(total_bytes)
                        df.at[idx, "cloudwatch_enrichment_success"] = True
                        df.at[idx, "enrichment_status"] = "SUCCESS"

                    # A5: HTTP Error Codes (90 days)
                    # 4XX errors
                    code_4xx_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/ApplicationELB",
                        MetricName="HTTPCode_Target_4XX_Count",
                        Dimensions=[{"Name": "LoadBalancer", "Value": alb_full_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                        Unit="Count",
                    )

                    code_4xx_datapoints = code_4xx_response.get("Datapoints", [])
                    if code_4xx_datapoints:
                        total_4xx = sum([dp["Sum"] for dp in code_4xx_datapoints])
                        df.at[idx, "http_code_4xx_count"] = int(total_4xx)
                        df.at[idx, "cloudwatch_enrichment_success"] = True
                        df.at[idx, "enrichment_status"] = "SUCCESS"

                    # 5XX errors
                    code_5xx_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/ApplicationELB",
                        MetricName="HTTPCode_Target_5XX_Count",
                        Dimensions=[{"Name": "LoadBalancer", "Value": alb_full_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,
                        Statistics=["Sum"],
                        Unit="Count",
                    )

                    code_5xx_datapoints = code_5xx_response.get("Datapoints", [])
                    if code_5xx_datapoints:
                        total_5xx = sum([dp["Sum"] for dp in code_5xx_datapoints])
                        df.at[idx, "http_code_5xx_count"] = int(total_5xx)
                        df.at[idx, "cloudwatch_enrichment_success"] = True
                        df.at[idx, "enrichment_status"] = "SUCCESS"

                except Exception as e:
                    logger.warning(
                        f"CloudWatch metrics failed for ALB {alb_arn}: {e}",
                        extra={
                            "alb_arn": alb_arn,
                            "error_type": type(e).__name__,
                            "lookback_days": self.lookback_days,
                            "region": self.region,
                        },
                    )
                    df.at[idx, "enrichment_status"] = "FAILED"
                    df.at[idx, "enrichment_error"] = str(e)
                    pass

                progress.update(task, advance=1)

        # Calculate decommission signals and scores
        df = self._calculate_decommission_signals(df)

        metrics_found = (df["request_count_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ ALB enrichment complete: {metrics_found}/{len(df)} ALBs with activity")
        else:
            logger.info(f"ALB enrichment complete: {metrics_found}/{len(df)} ALBs with activity")

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate A1-A5 decommission signals and scores.

        Args:
            df: DataFrame with ALB activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            # Check if CloudWatch enrichment succeeded
            if not row.get("cloudwatch_enrichment_success", False):
                df.at[idx, "decommission_score"] = 0
                df.at[idx, "decommission_tier"] = "UNKNOWN"
                continue  # Skip scoring for failed enrichments

            signals = {}

            # A1: Zero active connections (45 points)
            if row.get("active_connection_count_90d", 0) == 0:
                df.at[idx, "a1_signal"] = True
                signals["A1"] = DEFAULT_ALB_WEIGHTS["A1"]
            else:
                signals["A1"] = 0

            # A2: Low request count (25 points) - <100 requests/day average
            avg_requests_per_day = row.get("request_count_90d", 0) / 90
            if avg_requests_per_day < 100:
                df.at[idx, "a2_signal"] = True
                signals["A2"] = DEFAULT_ALB_WEIGHTS["A2"]
            else:
                signals["A2"] = 0

            # A3: No healthy targets (15 points)
            if row.get("healthy_host_count_avg", 0) == 0:
                df.at[idx, "a3_signal"] = True
                signals["A3"] = DEFAULT_ALB_WEIGHTS["A3"]
            else:
                signals["A3"] = 0

            # A4: Low data transfer (10 points) - <100 MB/day average
            bytes_per_day = row.get("data_processed_bytes_90d", 0) / 90
            mb_per_day = bytes_per_day / (1024 * 1024)
            if mb_per_day < 100:
                df.at[idx, "a4_signal"] = True
                signals["A4"] = DEFAULT_ALB_WEIGHTS["A4"]
            else:
                signals["A4"] = 0

            # A5: High error rate (5 points) - >50% errors
            total_errors = row.get("http_code_4xx_count", 0) + row.get("http_code_5xx_count", 0)
            total_requests = row.get("request_count_90d", 1)  # Avoid division by zero
            error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0

            if error_rate > 50:
                df.at[idx, "a5_signal"] = True
                signals["A5"] = DEFAULT_ALB_WEIGHTS["A5"]
            else:
                signals["A5"] = 0

            # Calculate total decommission score
            total_score = sum(signals.values())
            df.at[idx, "decommission_score"] = total_score

            # Determine decommission tier
            if total_score >= 80:
                df.at[idx, "decommission_tier"] = "MUST"
            elif total_score >= 50:
                df.at[idx, "decommission_tier"] = "SHOULD"
            elif total_score >= 25:
                df.at[idx, "decommission_tier"] = "COULD"
            else:
                df.at[idx, "decommission_tier"] = "KEEP"

        return df


# Export interface
__all__ = ["ALBActivityEnricher"]
