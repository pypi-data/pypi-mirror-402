#!/usr/bin/env python3
"""
AWS Glue Activity Enricher - Glue Job Health Signals (U1-U7)

Analyzes AWS Glue job activity patterns using CloudWatch metrics and Glue API
to identify unused or underutilized ETL jobs for cost optimization.

Decommission Signals (U1-U7):
- U1: Job not run in 90 days (40 points) - No job runs detected
- U2: Job failures >50% (25 points) - High failure rate over 30 runs
- U3: No data processed in 30 days (15 points) - Zero processed bytes
- U4: Job disabled/suspended (10 points) - Job not in RUNNING state
- U5: Crawler not scheduled (5 points) - Associated crawler inactive
- U6: No catalog updates in 60 days (3 points) - Stale metadata
- U7: Orphaned job (2 points) - No trigger/workflow association

Pattern: Reuses ActivityEnricher structure (KISS/DRY/LEAN)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable Glue enrichment
- Enterprise SDLC: ETL cost optimization with evidence
- KISS/DRY/LEAN: Single enricher, CloudWatch + Glue API consolidation

Usage:
    from runbooks.inventory.enrichers.glue_activity_enricher import GlueActivityEnricher

    enricher = GlueActivityEnricher(
        operational_profile='${CENTRALISED_OPS_PROFILE}',
        region='ap-southeast-2'
    )

    enriched_df = enricher.enrich_glue_activity(discovery_df)

    # Adds columns:
    # - job_runs_90d: Count of job runs over 90 days
    # - job_runs_failed: Count of failed runs over 90 days
    # - data_processed_bytes_30d: Bytes processed in last 30 days
    # - job_state: Current job state (RUNNING/SUSPENDED/DISABLED)
    # - crawler_scheduled: Boolean (associated crawler scheduled)
    # - catalog_last_updated: Days since last catalog update
    # - has_trigger: Boolean (job has active trigger/workflow)
    # - u1_signal: Boolean (job not run in 90 days)
    # - u2_signal: Boolean (failures >50%)
    # - u3_signal: Boolean (no data processed)
    # - u4_signal: Boolean (job disabled/suspended)
    # - u5_signal: Boolean (crawler not scheduled)
    # - u6_signal: Boolean (no catalog updates)
    # - u7_signal: Boolean (orphaned job)
    # - decommission_score: Total score (0-100 scale)
    # - decommission_tier: MUST/SHOULD/COULD/KEEP

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.27 FinOps Dashboard Enhancements
Track: Track 4 - Glue Activity Enrichment
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

# Glue signal weights (0-100 scale)
DEFAULT_GLUE_WEIGHTS = {
    "U1": 40,  # Job not run in 90 days
    "U2": 25,  # Job failures >50%
    "U3": 15,  # No data processed in 30 days
    "U4": 10,  # Job disabled/suspended
    "U5": 5,  # Crawler not scheduled
    "U6": 3,  # No catalog updates in 60 days
    "U7": 2,  # Orphaned job (no trigger)
}


class GlueActivityEnricher:
    """
    AWS Glue activity enrichment using CloudWatch metrics and Glue API for U1-U7 decommission signals.

    Consolidates Glue job metrics and API data into actionable signals:
    - Job runs (U1: not run in 90 days)
    - Job failures (U2: high failure rate)
    - Data processing (U3: no data processed)
    - Job state (U4: disabled/suspended)
    - Crawler scheduling (U5: inactive crawlers)
    - Catalog updates (U6: stale metadata)
    - Trigger association (U7: orphaned jobs)
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
        lookback_days: int = 90,
    ):
        """
        Initialize Glue activity enricher.

        Args:
            operational_profile: AWS profile for Glue and CloudWatch API access
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController for verbose output (optional)
            lookback_days: CloudWatch metrics lookback period (default: 90 days)

        Profile Requirements:
            - glue:GetJobRuns (job execution history)
            - glue:GetJob (job metadata and state)
            - glue:GetCrawlers (crawler scheduling info)
            - glue:GetTables (catalog update timestamps)
            - glue:GetTriggers (trigger associations)
            - cloudwatch:GetMetricStatistics (Glue namespace metrics)
        """
        resolved_profile = get_profile_for_operation("operational", operational_profile)
        self.session = create_operational_session(resolved_profile)
        self.glue = create_timeout_protected_client(self.session, "glue", region_name=region)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()
        self.lookback_days = lookback_days

        if self.output_controller.verbose:
            print_info(f"🔍 GlueActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info(f"   Metrics: JobRuns, Failures, DataProcessed, JobState, Crawlers, Catalog, Triggers")
        else:
            logger.debug(f"GlueActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_glue_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich Glue DataFrame with U1-U7 activity signals.

        Args:
            df: DataFrame with job_name column

        Returns:
            DataFrame with Glue activity columns and decommission signals

        Columns Added:
            - job_runs_90d: Count of job runs over 90 days
            - job_runs_failed: Count of failed runs
            - data_processed_bytes_30d: Bytes processed in 30 days
            - job_state: RUNNING/SUSPENDED/DISABLED
            - crawler_scheduled: Boolean
            - catalog_last_updated: Days since last update
            - has_trigger: Boolean
            - u1_signal to u7_signal: Boolean signals
            - decommission_score: Total score (0-100)
            - decommission_tier: MUST/SHOULD/COULD/KEEP
        """
        if df.empty:
            if self.output_controller.verbose:
                print_warning("⚠️  No Glue jobs to enrich")
            return df

        if "job_name" not in df.columns:
            raise ValueError("DataFrame must contain 'job_name' column for Glue enrichment")

        if self.output_controller.verbose:
            print_info(f"🔄 Starting Glue activity enrichment for {len(df)} jobs...")
        else:
            logger.info(f"Glue activity enrichment started for {len(df)} jobs")

        # Initialize activity columns with defaults
        activity_columns = {
            "job_runs_90d": 0,
            "job_runs_failed": 0,
            "data_processed_bytes_30d": 0,
            "job_state": "UNKNOWN",
            "crawler_scheduled": False,
            "catalog_last_updated": 9999,  # Days since update (large default)
            "has_trigger": False,
            "u1_signal": False,
            "u2_signal": False,
            "u3_signal": False,
            "u4_signal": False,
            "u5_signal": False,
            "u6_signal": False,
            "u7_signal": False,
            "decommission_score": 0,
            "decommission_tier": "KEEP",
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # Enrich each Glue job with API data
        end_time = datetime.now(timezone.utc)
        start_time_90d = end_time - timedelta(days=self.lookback_days)
        start_time_30d = end_time - timedelta(days=30)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Glue job metrics...", total=len(df))

            for idx, row in df.iterrows():
                job_name = row.get("job_name", "")

                if not job_name or job_name == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # U1/U2: Job runs and failures (90 days)
                    try:
                        runs_response = self.glue.get_job_runs(
                            JobName=job_name,
                            MaxResults=1000,  # Get up to 1000 recent runs
                        )

                        job_runs = runs_response.get("JobRuns", [])

                        # Filter runs within 90-day window
                        runs_90d = [run for run in job_runs if run.get("StartedOn", start_time_90d) >= start_time_90d]

                        df.at[idx, "job_runs_90d"] = len(runs_90d)

                        # Count failed runs
                        failed_runs = [
                            run for run in runs_90d if run.get("JobRunState", "") in ["FAILED", "ERROR", "TIMEOUT"]
                        ]
                        df.at[idx, "job_runs_failed"] = len(failed_runs)

                    except Exception as runs_error:
                        logger.debug(f"Job runs query failed for {job_name}: {runs_error}")

                    # U3: Data processed (30 days) - from CloudWatch or job metrics
                    try:
                        # Try CloudWatch metrics first
                        metrics_response = self.cloudwatch.get_metric_statistics(
                            Namespace="Glue",
                            MetricName="glue.driver.aggregate.bytesRead",
                            Dimensions=[{"Name": "JobName", "Value": job_name}],
                            StartTime=start_time_30d,
                            EndTime=end_time,
                            Period=86400,  # 1-day aggregation
                            Statistics=["Sum"],
                            Unit="Bytes",
                        )

                        datapoints = metrics_response.get("Datapoints", [])
                        if datapoints:
                            total_bytes = sum([dp["Sum"] for dp in datapoints])
                            df.at[idx, "data_processed_bytes_30d"] = int(total_bytes)

                    except Exception as metrics_error:
                        logger.debug(f"CloudWatch metrics failed for {job_name}: {metrics_error}")

                    # U4: Job state (RUNNING/SUSPENDED/DISABLED)
                    try:
                        job_response = self.glue.get_job(JobName=job_name)
                        job_info = job_response.get("Job", {})

                        # Check if job is enabled (no explicit state, use presence of MaxRetries)
                        max_retries = job_info.get("MaxRetries", None)
                        if max_retries is not None and max_retries >= 0:
                            df.at[idx, "job_state"] = "RUNNING"
                        else:
                            df.at[idx, "job_state"] = "DISABLED"

                    except Exception as job_error:
                        logger.debug(f"Job state query failed for {job_name}: {job_error}")

                    # U5: Crawler scheduling (check associated crawler)
                    try:
                        # Extract potential crawler name from job name or database
                        # Common pattern: glue-crawler-{database} or {job_name}-crawler
                        potential_crawler_names = [
                            f"{job_name}-crawler",
                            f"crawler-{job_name}",
                            job_name.replace("job", "crawler"),
                        ]

                        crawler_scheduled = False
                        for crawler_name in potential_crawler_names:
                            try:
                                crawler_response = self.glue.get_crawler(Name=crawler_name)
                                crawler = crawler_response.get("Crawler", {})

                                # Check if crawler has schedule
                                schedule = crawler.get("Schedule", {})
                                if schedule and schedule.get("ScheduleExpression"):
                                    crawler_scheduled = True
                                    break

                            except self.glue.exceptions.EntityNotFoundException:
                                continue
                            except Exception:
                                continue

                        df.at[idx, "crawler_scheduled"] = crawler_scheduled

                    except Exception as crawler_error:
                        logger.debug(f"Crawler query failed for {job_name}: {crawler_error}")

                    # U6: Catalog updates (60 days) - check table last modified
                    try:
                        # Get database name from job (if available)
                        job_response = self.glue.get_job(JobName=job_name)
                        job_info = job_response.get("Job", {})

                        # Check for DatabaseName in job command arguments
                        command = job_info.get("Command", {})
                        database_name = None

                        # Try to extract database from job properties
                        default_args = job_info.get("DefaultArguments", {})
                        if "--database_name" in default_args:
                            database_name = default_args["--database_name"]

                        if database_name:
                            # Get tables in database
                            tables_response = self.glue.get_tables(DatabaseName=database_name)
                            tables = tables_response.get("TableList", [])

                            if tables:
                                # Find most recent table update
                                latest_update = None
                                for table in tables:
                                    update_time = table.get("UpdateTime")
                                    if update_time:
                                        if latest_update is None or update_time > latest_update:
                                            latest_update = update_time

                                if latest_update:
                                    days_since_update = (end_time - latest_update).days
                                    df.at[idx, "catalog_last_updated"] = days_since_update

                    except Exception as catalog_error:
                        logger.debug(f"Catalog query failed for {job_name}: {catalog_error}")

                    # U7: Trigger association (orphaned job detection)
                    try:
                        triggers_response = self.glue.get_triggers()
                        triggers = triggers_response.get("Triggers", [])

                        has_trigger = False
                        for trigger in triggers:
                            actions = trigger.get("Actions", [])
                            for action in actions:
                                if action.get("JobName") == job_name:
                                    has_trigger = True
                                    break
                            if has_trigger:
                                break

                        df.at[idx, "has_trigger"] = has_trigger

                    except Exception as trigger_error:
                        logger.debug(f"Trigger query failed for {job_name}: {trigger_error}")

                except Exception as e:
                    logger.debug(f"Glue enrichment failed for job {job_name}: {e}")
                    pass

                progress.update(task, advance=1)

        # Calculate decommission signals and scores
        df = self._calculate_decommission_signals(df)

        jobs_enriched = (df["job_runs_90d"] > 0).sum()
        if self.output_controller.verbose:
            print_success(f"✅ Glue enrichment complete: {jobs_enriched}/{len(df)} jobs with recent runs")
        else:
            logger.info(f"Glue enrichment complete: {jobs_enriched}/{len(df)} jobs with recent runs")

        return df

    def _calculate_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate U1-U7 decommission signals and scores.

        Args:
            df: DataFrame with Glue activity columns

        Returns:
            DataFrame with signal columns and decommission scores populated
        """
        for idx, row in df.iterrows():
            signals = {}

            # U1: Job not run in 90 days (40 points)
            if row.get("job_runs_90d", 0) == 0:
                df.at[idx, "u1_signal"] = True
                signals["U1"] = DEFAULT_GLUE_WEIGHTS["U1"]
            else:
                signals["U1"] = 0

            # U2: Job failures >50% (25 points)
            job_runs = row.get("job_runs_90d", 0)
            job_failures = row.get("job_runs_failed", 0)

            if job_runs > 0:
                failure_rate = (job_failures / job_runs) * 100
                if failure_rate > 50:
                    df.at[idx, "u2_signal"] = True
                    signals["U2"] = DEFAULT_GLUE_WEIGHTS["U2"]
                else:
                    signals["U2"] = 0
            else:
                signals["U2"] = 0

            # U3: No data processed in 30 days (15 points)
            if row.get("data_processed_bytes_30d", 0) == 0:
                df.at[idx, "u3_signal"] = True
                signals["U3"] = DEFAULT_GLUE_WEIGHTS["U3"]
            else:
                signals["U3"] = 0

            # U4: Job disabled/suspended (10 points)
            job_state = row.get("job_state", "UNKNOWN")
            if job_state in ["DISABLED", "SUSPENDED", "UNKNOWN"]:
                df.at[idx, "u4_signal"] = True
                signals["U4"] = DEFAULT_GLUE_WEIGHTS["U4"]
            else:
                signals["U4"] = 0

            # U5: Crawler not scheduled (5 points)
            if not row.get("crawler_scheduled", False):
                df.at[idx, "u5_signal"] = True
                signals["U5"] = DEFAULT_GLUE_WEIGHTS["U5"]
            else:
                signals["U5"] = 0

            # U6: No catalog updates in 60 days (3 points)
            days_since_update = row.get("catalog_last_updated", 9999)
            if days_since_update > 60:
                df.at[idx, "u6_signal"] = True
                signals["U6"] = DEFAULT_GLUE_WEIGHTS["U6"]
            else:
                signals["U6"] = 0

            # U7: Orphaned job (no trigger) (2 points)
            if not row.get("has_trigger", False):
                df.at[idx, "u7_signal"] = True
                signals["U7"] = DEFAULT_GLUE_WEIGHTS["U7"]
            else:
                signals["U7"] = 0

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
__all__ = ["GlueActivityEnricher"]
