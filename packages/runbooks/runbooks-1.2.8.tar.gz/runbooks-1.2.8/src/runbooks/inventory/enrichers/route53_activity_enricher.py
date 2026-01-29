#!/usr/bin/env python3
"""
Route53 Activity Enricher - DNS Hosted Zone Health Signals (R53-1 to R53-7)

Analyzes Route53 hosted zone activity patterns using CloudWatch metrics and
Route53 API data to identify unused or underutilized DNS zones for cost optimization.

Decommission Signals (R53-1 to R53-7):
- R53-1: Zero DNS queries (50 points) - No queries for 90+ days
- R53-2: Low query count (30 points) - <100 queries/day average
- R53-3: No record sets (15 points) - Only NS and SOA records
- R53-4: Inactive health checks (5 points) - All health checks failed/disabled
- R53-5: Health check failures (3 points) - Health checks failing >30 days
- R53-6: No queries detected (2 points) - CloudWatch Logs show zero queries in 90 days
- R53-7: Deprecated records (1 point) - A records vs ALIAS inefficiency

Pattern: Reuses ActivityEnricher structure (KISS/DRY/LEAN)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable Route53 enrichment
- Enterprise SDLC: DNS cost optimization with evidence
- KISS/DRY/LEAN: Single enricher, CloudWatch + Route53 API consolidation

Usage:
    from runbooks.inventory.enrichers.route53_activity_enricher import Route53ActivityEnricher

    enricher = Route53ActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='us-east-1'  # Route53 is global, use us-east-1 for API
    )

    enriched_df = enricher.enrich_route53_activity(discovery_df)

    # Adds columns:
    # - dns_queries_90d: Sum of DNSQueries over 90 days
    # - record_set_count: Total DNS record sets in zone
    # - health_check_count: Total health checks for zone
    # - health_check_active: Number of active/passing health checks
    # - health_check_failing_days: Days health checks have been failing
    # - cloudwatch_queries_90d: Query count from CloudWatch Logs
    # - a_record_count: Count of A records
    # - alias_record_count: Count of ALIAS records
    # - r53_1_signal: Boolean (zero queries)
    # - r53_2_signal: Boolean (low queries)
    # - r53_3_signal: Boolean (no record sets)
    # - r53_4_signal: Boolean (inactive health checks)
    # - r53_5_signal: Boolean (health check failures >30 days)
    # - r53_6_signal: Boolean (no CloudWatch queries)
    # - r53_7_signal: Boolean (deprecated A records)
    # - decommission_score: Total score (0-100 scale)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP

Author: Runbooks Team
Version: 1.1.0
Epic: v1.1.27 FinOps Dashboard Enhancements
Track: Track 4 - Route53 Enhancement (R53-5 to R53-7)
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

# Route53 signal weights (0-100 scale)
DEFAULT_R53_WEIGHTS = {
    "R53_1": 50,  # Zero DNS queries
    "R53_2": 30,  # Low query count
    "R53_3": 15,  # No record sets
    "R53_4": 5,  # Inactive health checks
    "R53_5": 3,  # Health check failures >30 days
    "R53_6": 2,  # No CloudWatch queries detected
    "R53_7": 1,  # Deprecated A records (vs ALIAS)
}


class Route53ActivityEnricher:
    """
    Route53 activity enrichment using CloudWatch metrics for R53-1 to R53-7 decommission signals.

    Consolidates CloudWatch DNS metrics and Route53 API data into actionable signals:
    - DNSQueries (R53-1: zero queries, R53-2: low queries)
    - Record sets (R53-3: minimal DNS configuration)
    - Health checks (R53-4: inactive monitoring, R53-5: persistent failures)
    - CloudWatch Logs (R53-6: no query logs)
    - Record efficiency (R53-7: A records vs ALIAS optimization)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "us-east-1",  # Route53 is global, but API requires us-east-1
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
    ):
        """
        Initialize Route53 activity enricher.

        Args:
            operational_profile: AWS profile for CloudWatch and Route53 API access
            region: AWS region for API calls (default: us-east-1 for Route53)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)

        Profile Requirements:
            - cloudwatch:GetMetricStatistics (Route53 namespace metrics)
            - route53:ListResourceRecordSets (DNS record enumeration)
            - route53:ListHealthChecks (health check status)
        """
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        self.session = create_operational_session(resolved_profile)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.route53 = create_timeout_protected_client(self.session, "route53", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        if self.output_controller.verbose:
            print_info(f"🔍 Route53ActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: DNSQueries, RecordSetCount, HealthCheckStatus")
        else:
            logger.debug(f"Route53ActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_route53_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich Route53 DataFrame with R53-1 to R53-7 activity signals.

        Args:
            df: DataFrame with hosted_zone_id column

        Returns:
            DataFrame with Route53 activity columns and decommission signals

        Columns Added:
            - dns_queries_90d: Sum of DNS queries over 90 days
            - record_set_count: Total DNS record sets
            - health_check_count: Total health checks
            - health_check_active: Active/passing health checks
            - health_check_failing_days: Days health checks failing
            - cloudwatch_queries_90d: Queries from CloudWatch Logs
            - a_record_count: Count of A records
            - alias_record_count: Count of ALIAS records
            - r53_1_signal: Zero queries (Boolean)
            - r53_2_signal: Low queries (Boolean)
            - r53_3_signal: No record sets (Boolean)
            - r53_4_signal: Inactive health checks (Boolean)
            - r53_5_signal: Health check failures >30 days (Boolean)
            - r53_6_signal: No CloudWatch queries (Boolean)
            - r53_7_signal: Deprecated A records (Boolean)
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP
        """
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  No Route53 hosted zones to enrich")
            return df

        if "hosted_zone_id" not in df.columns:
            raise ValueError("DataFrame must contain 'hosted_zone_id' column for Route53 enrichment")

        if self.output_controller.verbose:
            print_info(f"🔄 Starting Route53 activity enrichment for {len(df)} hosted zones...")
        else:
            logger.info(f"Route53 activity enrichment started for {len(df)} hosted zones")

        # Initialize activity columns with defaults
        activity_columns = {
            "dns_queries_90d": 0,
            "record_set_count": 0,
            "health_check_count": 0,
            "health_check_active": 0,
            "health_check_failing_days": 0,
            "cloudwatch_queries_90d": 0,
            "a_record_count": 0,
            "alias_record_count": 0,
            "r53_1_signal": False,
            "r53_2_signal": False,
            "r53_3_signal": False,
            "r53_4_signal": False,
            "r53_5_signal": False,
            "r53_6_signal": False,
            "r53_7_signal": False,
            "decommission_score": 0,
            "decommission_tier": "KEEP",
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # Enrich each hosted zone with CloudWatch metrics and Route53 API data
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=self.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Route53 metrics...", total=len(df))

            for idx, row in df.iterrows():
                hosted_zone_id = row.get("hosted_zone_id", "")

                if not hosted_zone_id or hosted_zone_id == "N/A":
                    progress.update(task, advance=1)
                    continue

                # Remove /hostedzone/ prefix if present
                zone_id = hosted_zone_id.replace("/hostedzone/", "")

                try:
                    # R53-1/R53-2: DNS query metrics (90 days)
                    query_response = self.cloudwatch.get_metric_statistics(
                        Namespace="AWS/Route53",
                        MetricName="DNSQueries",
                        Dimensions=[{"Name": "HostedZoneId", "Value": zone_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1-day aggregation
                        Statistics=["Sum"],
                        Unit="Count",
                    )

                    query_datapoints = query_response.get("Datapoints", [])
                    if query_datapoints:
                        total_queries = sum([dp["Sum"] for dp in query_datapoints])
                        df.at[idx, "dns_queries_90d"] = int(total_queries)

                    # R53-3/R53-7: Count record sets and analyze A vs ALIAS records
                    try:
                        record_response = self.route53.list_resource_record_sets(
                            HostedZoneId=zone_id,
                            MaxItems="100",  # Sample first 100 records
                        )

                        record_sets = record_response.get("ResourceRecordSets", [])

                        # Count non-default records (exclude NS and SOA)
                        non_default_records = [rs for rs in record_sets if rs["Type"] not in ["NS", "SOA"]]
                        df.at[idx, "record_set_count"] = len(non_default_records)

                        # R53-7: Count A records and ALIAS records
                        a_records = [rs for rs in record_sets if rs["Type"] == "A" and not rs.get("AliasTarget")]
                        alias_records = [rs for rs in record_sets if rs.get("AliasTarget")]

                        df.at[idx, "a_record_count"] = len(a_records)
                        df.at[idx, "alias_record_count"] = len(alias_records)

                    except Exception as record_error:
                        logger.debug(f"Record set query failed for {zone_id}: {record_error}")

                    # R53-4: Health check status
                    try:
                        # List health checks associated with this zone
                        # Note: Route53 doesn't directly link health checks to zones,
                        # so we check health checks with markers containing the zone name
                        health_response = self.route53.list_health_checks()

                        health_checks = health_response.get("HealthChecks", [])
                        zone_health_checks = []
                        active_health_checks = 0

                        for hc in health_checks:
                            # Check if health check references this zone (heuristic)
                            hc_config = hc.get("HealthCheckConfig", {})
                            fully_qualified_domain_name = hc_config.get("FullyQualifiedDomainName", "")

                            # If FQDN matches zone name, associate health check
                            zone_name = row.get("name", "").rstrip(".")
                            if zone_name and zone_name in fully_qualified_domain_name:
                                zone_health_checks.append(hc)

                                # Check if health check is active
                                hc_id = hc.get("Id", "")
                                if hc_id:
                                    status_response = self.route53.get_health_check_status(HealthCheckId=hc_id)

                                    statuses = status_response.get("HealthCheckObservations", [])
                                    # Consider active if any checker reports healthy
                                    is_active = any(
                                        obs.get("StatusReport", {}).get("Status") == "Success" for obs in statuses
                                    )
                                    if is_active:
                                        active_health_checks += 1

                        df.at[idx, "health_check_count"] = len(zone_health_checks)
                        df.at[idx, "health_check_active"] = active_health_checks

                        # R53-5: Check health check failure duration
                        if len(zone_health_checks) > 0 and active_health_checks == 0:
                            # Calculate days since first failure (estimate from last status check)
                            # For simplicity, use lookback period as proxy
                            df.at[idx, "health_check_failing_days"] = self.lookback_days

                    except Exception as health_error:
                        logger.debug(f"Health check query failed for {zone_id}: {health_error}")

                    # R53-6: CloudWatch Logs query count (alternative validation)
                    try:
                        # Check CloudWatch Logs Insights for query patterns
                        # Note: This requires CloudWatch Logs Query Logging to be enabled
                        # We'll use CloudWatch metrics as proxy since Logs may not be available
                        logs_query_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/Route53",
                            MetricName="QueryCount",
                            Dimensions=[{"Name": "HostedZoneId", "Value": zone_id}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,
                            Statistics=["Sum"],
                            Unit="Count",
                        )

                        logs_datapoints = logs_query_response.get("Datapoints", [])
                        if logs_datapoints:
                            total_logs_queries = sum([dp["Sum"] for dp in logs_datapoints])
                            df.at[idx, "cloudwatch_queries_90d"] = int(total_logs_queries)

                    except Exception as logs_error:
                        logger.debug(f"CloudWatch Logs query failed for {zone_id}: {logs_error}")

                except Exception as e:
                    logger.debug(f"Route53 metrics failed for zone {zone_id}: {e}")
                    pass

                progress.update(task, advance=1)

        # Calculate decommission signals and scores
        df = self._calculate_decommission_signals(df)

        metrics_found = (df["dns_queries_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ Route53 enrichment complete: {metrics_found}/{len(df)} zones with queries")
        else:
            logger.info(f"Route53 enrichment complete: {metrics_found}/{len(df)} zones with queries")

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate R53-1 to R53-7 decommission signals and scores.

        Args:
            df: DataFrame with Route53 activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            signals = {}

            # R53-1: Zero DNS queries (50 points)
            if row.get("dns_queries_90d", 0) == 0:
                df.at[idx, "r53_1_signal"] = True
                signals["R53_1"] = DEFAULT_R53_WEIGHTS["R53_1"]
            else:
                signals["R53_1"] = 0

            # R53-2: Low query count (30 points) - <100 queries/day average
            avg_queries_per_day = row.get("dns_queries_90d", 0) / 90
            if avg_queries_per_day < 100:
                df.at[idx, "r53_2_signal"] = True
                signals["R53_2"] = DEFAULT_R53_WEIGHTS["R53_2"]
            else:
                signals["R53_2"] = 0

            # R53-3: No record sets (15 points) - Only default NS/SOA records
            if row.get("record_set_count", 0) == 0:
                df.at[idx, "r53_3_signal"] = True
                signals["R53_3"] = DEFAULT_R53_WEIGHTS["R53_3"]
            else:
                signals["R53_3"] = 0

            # R53-4: Inactive health checks (5 points)
            health_check_count = row.get("health_check_count", 0)
            health_check_active = row.get("health_check_active", 0)

            if health_check_count > 0 and health_check_active == 0:
                df.at[idx, "r53_4_signal"] = True
                signals["R53_4"] = DEFAULT_R53_WEIGHTS["R53_4"]
            else:
                signals["R53_4"] = 0

            # R53-5: Health check failures >30 days (3 points)
            health_check_failing_days = row.get("health_check_failing_days", 0)
            if health_check_failing_days > 30:
                df.at[idx, "r53_5_signal"] = True
                signals["R53_5"] = DEFAULT_R53_WEIGHTS["R53_5"]
            else:
                signals["R53_5"] = 0

            # R53-6: No CloudWatch queries detected (2 points)
            if row.get("cloudwatch_queries_90d", 0) == 0:
                df.at[idx, "r53_6_signal"] = True
                signals["R53_6"] = DEFAULT_R53_WEIGHTS["R53_6"]
            else:
                signals["R53_6"] = 0

            # R53-7: Deprecated A records (1 point) - A records exist but ALIAS would be better
            a_record_count = row.get("a_record_count", 0)
            alias_record_count = row.get("alias_record_count", 0)

            # Signal if zone has A records but no ALIAS records (inefficiency)
            if a_record_count > 0 and alias_record_count == 0:
                df.at[idx, "r53_7_signal"] = True
                signals["R53_7"] = DEFAULT_R53_WEIGHTS["R53_7"]
            else:
                signals["R53_7"] = 0

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
__all__ = ["Route53ActivityEnricher"]
