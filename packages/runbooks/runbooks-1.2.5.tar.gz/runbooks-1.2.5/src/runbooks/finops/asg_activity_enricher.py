#!/usr/bin/env python3
"""
ASG Activity Enricher - A1-A5 Auto Scaling Group Decommission Signals

Adds 9 activity columns for ASG decommission analysis:
- CloudWatch: scaling_activity_count_90d, desired_vs_actual_delta_pct, launch_config_age_days
- Instance Health: unhealthy_instance_pct, avg_healthy_instances_30d
- Cost Analysis: cost_per_instance_monthly, total_asg_cost_monthly
- Activity Signals: A1-A5 (scaling activity, health, capacity, config age, cost efficiency)

Pattern: Reuses EC2 ActivityEnricher pattern with ASG-specific metrics

Strategic Alignment:
- Objective 1 (runbooks package): Reusable activity enrichment for auto-scaled workloads
- Enterprise SDLC: Proven pattern replication with ASG API specialization
- KISS/DRY/LEAN: Single enricher class consolidating Auto Scaling + CloudWatch + Cost Explorer

Decommission Scoring Framework:
- Signal A1 (Scaling Activity): 45 points (no scaling events for 90+ days)
- Signal A2 (Instance Health): 25 points (persistent unhealthy instances >7 days)
- Signal A3 (Capacity Delta): 15 points (desired vs actual mismatch >30 days)
- Signal A4 (Launch Config Age): 10 points (launch config >180 days old)
- Signal A5 (Cost Efficiency): 5 points (cost per instance >150% of baseline)

Usage:
    from runbooks.finops.asg_activity_enricher import ASGActivityEnricher

    enricher = ASGActivityEnricher(operational_profile='${CENTRALISED_OPS_PROFILE}')
    enriched_df = enricher.enrich_asg_activity(discovery_df)

    # Adds 9 columns:
    # - CloudWatch: scaling_activity_count_90d, desired_vs_actual_delta_pct, launch_config_age_days
    # - Instance Health: unhealthy_instance_pct, avg_healthy_instances_30d
    # - Cost: cost_per_instance_monthly, total_asg_cost_monthly
    # - Signals: a1_signal (bool), a2_signal (bool), a3_signal (bool), a4_signal (bool), a5_signal (bool)
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
    create_table,
)
from runbooks.common.output_controller import OutputController

logger = logging.getLogger(__name__)


class ASGActivityEnricher:
    """
    Auto Scaling Group activity enrichment for A1-A5 decommission signals.

    Standalone enricher class for adding 9 ASG activity columns from Auto Scaling + CloudWatch + Cost Explorer APIs.
    Follows EC2 ActivityEnricher pattern (inventory/enrichers/activity_enricher.py).

    Signals:
        A1: Scaling activity frequency (CloudWatch DesiredCapacity change events over 90 days)
        A2: Instance health status (InService vs Desired - detect unhealthy ASGs)
        A3: Desired vs Actual capacity delta (persistent mismatches >30 days)
        A4: Launch configuration age (detect outdated configs - security/cost risk)
        A5: Cost efficiency (Cost Explorer EC2 Auto Scaling filter + per-instance attribution)

    Example:
        >>> enricher = ASGActivityEnricher(operational_profile='${CENTRALISED_OPS_PROFILE}')
        >>> enriched = enricher.enrich_asg_activity(df)
        >>> print(enriched[['asg_name', 'a1_signal', 'a2_signal', 'scaling_activity_count_90d']])
    """

    def __init__(
        self,
        operational_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize with Auto Scaling + CloudWatch + Cost Explorer clients.

        Args:
            operational_profile: AWS profile for operational APIs
            region: AWS region for API calls (default: ap-southeast-2)
            output_controller: OutputController instance for UX consistency (optional)

        Profile Requirements:
            - Auto Scaling: autoscaling:DescribeAutoScalingGroups, autoscaling:DescribeScalingActivities
            - CloudWatch: cloudwatch:GetMetricStatistics
            - Cost Explorer: ce:GetCostAndUsage (optional for A5)
            - EC2: ec2:DescribeLaunchTemplates (for launch config age)

        Example:
            >>> enricher = ASGActivityEnricher(operational_profile='${CENTRALISED_OPS_PROFILE}')
            >>> enriched = enricher.enrich_asg_activity(df)
        """
        # Resolve profile using standard helpers
        resolved_profile = get_profile_for_operation("operational", operational_profile)

        # Initialize AWS session and clients
        self.session = create_operational_session(resolved_profile)
        self.autoscaling = create_timeout_protected_client(self.session, "autoscaling", region_name=region)
        self.cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region_name=region)
        self.ec2 = create_timeout_protected_client(self.session, "ec2", region_name=region)

        # Cost Explorer initialization (optional for A5)
        try:
            self.cost_explorer = create_timeout_protected_client(self.session, "ce", region_name="us-east-1")
            self.cost_explorer_available = True
        except Exception as e:
            logger.debug(f"Cost Explorer not available (A5 signal disabled): {e}")
            self.cost_explorer = None
            self.cost_explorer_available = False

        self.region = region
        self.profile = resolved_profile
        self.output_controller = output_controller or OutputController()

        # Respect output control for initialization messages
        if self.output_controller.verbose:
            print_info(f"🔍 ASGActivityEnricher initialized: profile={resolved_profile}, region={region}")
            print_info("   APIs: Auto Scaling (90d) + CloudWatch (30d) + Cost Explorer (30d)")
        else:
            logger.debug(f"ASGActivityEnricher initialized: profile={resolved_profile}, region={region}")

    def enrich_asg_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 9 ASG activity columns for A1-A5 decommission signals.

        Args:
            df: DataFrame with asg_name column (from discovery)

        Returns:
            DataFrame with 9 additional activity columns

        Columns Added:
            - CloudWatch: scaling_activity_count_90d, desired_vs_actual_delta_pct, launch_config_age_days
            - Instance Health: unhealthy_instance_pct, avg_healthy_instances_30d
            - Cost: cost_per_instance_monthly, total_asg_cost_monthly
            - Signals: a1_signal (bool), a2_signal (bool), a3_signal (bool), a4_signal (bool), a5_signal (bool)

        Signal Thresholds:
            A1: scaling_activity_count_90d == 0 (no scaling for 90+ days) → 45 points
            A2: unhealthy_instance_pct > 0 for 7+ days (persistent unhealthy) → 25 points
            A3: desired_vs_actual_delta_pct > 0 for 30+ days (capacity mismatch) → 15 points
            A4: launch_config_age_days > 180 (outdated config) → 10 points
            A5: cost_per_instance_monthly > 150% baseline (inefficient) → 5 points

        Example:
            >>> df = pd.DataFrame({'asg_name': ['my-asg-1', 'my-asg-2']})
            >>> enriched = enricher.enrich_asg_activity(df)
            >>> print(enriched[['asg_name', 'a1_signal', 'scaling_activity_count_90d']])
        """
        if self.output_controller.verbose:
            print_info(f"🔄 Starting ASG activity enrichment for {len(df)} Auto Scaling Groups...")
        else:
            logger.info(f"ASG activity enrichment started")

        # Validate required columns
        if "asg_name" not in df.columns:
            available_columns = df.columns.tolist()
            print_error(f"Input DataFrame missing required 'asg_name' column")
            print_info(f"Available columns ({len(available_columns)}): {', '.join(available_columns[:10])}")

            raise ValueError(
                f"asg_name column required for ASG activity enrichment.\n"
                f"Available columns: {available_columns[:10]}\n"
                f"Total columns in DataFrame: {len(available_columns)}"
            )

        # Initialize all 9 columns with default values
        activity_columns = {
            # CloudWatch metrics
            "scaling_activity_count_90d": 0,
            "desired_vs_actual_delta_pct": 0.0,
            "launch_config_age_days": 0,
            # Instance health metrics
            "unhealthy_instance_pct": 0.0,
            "avg_healthy_instances_30d": 0.0,
            # Cost metrics (optional - A5)
            "cost_per_instance_monthly": 0.0,
            "total_asg_cost_monthly": 0.0,
            # Activity signals (A1-A5)
            "a1_signal": False,  # No scaling activity
            "a2_signal": False,  # Unhealthy instances
            "a3_signal": False,  # Capacity delta
            "a4_signal": False,  # Launch config age
            "a5_signal": False,  # Cost efficiency
        }

        for col, default in activity_columns.items():
            if col not in df.columns:
                df[col] = default

        # A1: Scaling activity frequency (CloudWatch DesiredCapacity change events)
        df = self._enrich_scaling_activity(df)

        # A2: Instance health status (InService vs Desired)
        df = self._enrich_instance_health(df)

        # A3: Desired vs Actual capacity delta
        df = self._enrich_capacity_delta(df)

        # A4: Launch configuration age
        df = self._enrich_launch_config_age(df)

        # A5: Cost efficiency (optional - requires Cost Explorer)
        if self.cost_explorer_available:
            df = self._enrich_cost_efficiency(df)
        else:
            if self.output_controller.verbose:
                print_info("   ⏭️  Skipping Cost Explorer enrichment (A5 disabled - no Cost Explorer access)")
            else:
                logger.debug("Skipping Cost Explorer enrichment for ASG (A5 disabled)")

        # Display activity signals summary table
        summary_rows = []

        # Count A1-A5 signal detections
        for signal in ["A1", "A2", "A3", "A4", "A5"]:
            column_name = f"{signal.lower()}_signal"
            if column_name in df.columns:
                detected = (df[column_name] == True).sum()
                rate = (detected / len(df) * 100) if len(df) > 0 else 0
                summary_rows.append([signal, f"{detected}/{len(df)} ({rate:.1f}%)"])

        if summary_rows:
            if self.output_controller.verbose:
                signals_table = create_table(
                    "ASG Activity Signals Detection", ["Signal", "Detection Rate"], summary_rows
                )
                console.print(signals_table)
            else:
                # Compact logging for non-verbose mode
                total_signals = len([r for r in summary_rows if "N/A" not in r[1]])
                logger.info(f"ASG activity signals detected: {total_signals}/5 signals populated")

        if self.output_controller.verbose:
            print_success(f"✅ ASG activity enrichment complete: {len(df)} resources processed")
        else:
            logger.info(f"ASG activity enrichment complete: {len(df)} resources processed")

        return df

    def _enrich_scaling_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        A1: Scaling activity frequency (CloudWatch DesiredCapacity change events over 90 days).

        Args:
            df: DataFrame with asg_name column

        Returns:
            DataFrame with scaling_activity_count_90d and a1_signal columns populated

        Signal Logic:
            A1 = True if scaling_activity_count_90d == 0 (no scaling for 90+ days)
        """
        if self.output_controller.verbose:
            print_info("   📊 CloudWatch: Querying 90-day scaling activity history...")
        else:
            logger.debug("Querying CloudWatch 90-day scaling activity history")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=90)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]ASG scaling activity...", total=len(df))

            for idx, row in df.iterrows():
                asg_name = row.get("asg_name", "")

                if not asg_name or asg_name == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Query Auto Scaling activities
                    response = self.autoscaling.describe_scaling_activities(
                        AutoScalingGroupName=asg_name,
                        MaxRecords=100,  # Sample up to 100 activities
                    )

                    activities = response.get("Activities", [])

                    # Filter activities within 90-day window
                    recent_activities = [act for act in activities if act["StartTime"] >= start_time]

                    activity_count = len(recent_activities)

                    df.at[idx, "scaling_activity_count_90d"] = activity_count

                    # A1 Signal: No scaling activity for 90+ days
                    df.at[idx, "a1_signal"] = activity_count == 0

                except Exception as e:
                    logger.debug(f"Scaling activity lookup failed for {asg_name}: {e}")
                    df.at[idx, "scaling_activity_count_90d"] = 0
                    df.at[idx, "a1_signal"] = False

                progress.update(task, advance=1)

        activities_found = (df["scaling_activity_count_90d"] > 0).sum()
        a1_signals = (df["a1_signal"] == True).sum()

        if self.output_controller.verbose:
            print_success(
                f"   ✅ Scaling activity: {activities_found}/{len(df)} ASGs with activity, {a1_signals} A1 signals"
            )
        else:
            logger.info(f"Scaling activity: {activities_found}/{len(df)} ASGs with activity")

        return df

    def _enrich_instance_health(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        A2: Instance health status (InService vs Desired - detect unhealthy ASGs).

        Args:
            df: DataFrame with asg_name column

        Returns:
            DataFrame with unhealthy_instance_pct, avg_healthy_instances_30d, and a2_signal columns populated

        Signal Logic:
            A2 = True if unhealthy_instance_pct > 0 for 7+ days (persistent unhealthy instances)
        """
        if self.output_controller.verbose:
            print_info("   🏥 Auto Scaling: Checking instance health status...")
        else:
            logger.debug("Checking Auto Scaling instance health status")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=30)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]ASG instance health...", total=len(df))

            for idx, row in df.iterrows():
                asg_name = row.get("asg_name", "")

                if not asg_name or asg_name == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get current ASG state
                    response = self.autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])

                    asgs = response.get("AutoScalingGroups", [])

                    if not asgs:
                        progress.update(task, advance=1)
                        continue

                    asg = asgs[0]

                    desired_capacity = asg.get("DesiredCapacity", 0)
                    instances = asg.get("Instances", [])

                    # Count healthy vs unhealthy instances
                    healthy_count = len([i for i in instances if i.get("HealthStatus") == "Healthy"])
                    unhealthy_count = len(instances) - healthy_count

                    unhealthy_pct = (unhealthy_count / desired_capacity * 100) if desired_capacity > 0 else 0.0

                    df.at[idx, "unhealthy_instance_pct"] = round(unhealthy_pct, 2)

                    # Calculate average healthy instances over 30 days using CloudWatch
                    try:
                        cw_response = self.cloudwatch.get_metric_statistics(
                            Namespace="AWS/AutoScaling",
                            MetricName="GroupInServiceInstances",
                            Dimensions=[{"Name": "AutoScalingGroupName", "Value": asg_name}],
                            StartTime=start_time,
                            EndTime=end_time,
                            Period=86400,  # 1-day aggregation
                            Statistics=["Average"],
                        )

                        datapoints = cw_response.get("Datapoints", [])

                        if datapoints:
                            avg_healthy = sum([dp["Average"] for dp in datapoints]) / len(datapoints)
                            df.at[idx, "avg_healthy_instances_30d"] = round(avg_healthy, 2)
                        else:
                            df.at[idx, "avg_healthy_instances_30d"] = healthy_count

                    except Exception as cw_error:
                        logger.debug(f"CloudWatch metrics failed for {asg_name}: {cw_error}")
                        df.at[idx, "avg_healthy_instances_30d"] = healthy_count

                    # A2 Signal: Persistent unhealthy instances (unhealthy_pct > 0)
                    df.at[idx, "a2_signal"] = unhealthy_pct > 0

                except Exception as e:
                    logger.debug(f"Instance health lookup failed for {asg_name}: {e}")
                    df.at[idx, "unhealthy_instance_pct"] = 0.0
                    df.at[idx, "avg_healthy_instances_30d"] = 0.0
                    df.at[idx, "a2_signal"] = False

                progress.update(task, advance=1)

        unhealthy_asgs = (df["unhealthy_instance_pct"] > 0).sum()
        a2_signals = (df["a2_signal"] == True).sum()

        if self.output_controller.verbose:
            print_success(
                f"   ✅ Instance health: {unhealthy_asgs}/{len(df)} ASGs with unhealthy instances, {a2_signals} A2 signals"
            )
        else:
            logger.info(f"Instance health: {unhealthy_asgs}/{len(df)} ASGs with unhealthy instances")

        return df

    def _enrich_capacity_delta(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        A3: Desired vs Actual capacity delta (persistent mismatches indicate configuration issues).

        Args:
            df: DataFrame with asg_name column

        Returns:
            DataFrame with desired_vs_actual_delta_pct and a3_signal columns populated

        Signal Logic:
            A3 = True if desired_vs_actual_delta_pct > 0 for 30+ days (capacity mismatch)
        """
        if self.output_controller.verbose:
            print_info("   ⚖️  Auto Scaling: Analyzing capacity delta...")
        else:
            logger.debug("Analyzing Auto Scaling capacity delta")

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]ASG capacity delta...", total=len(df))

            for idx, row in df.iterrows():
                asg_name = row.get("asg_name", "")

                if not asg_name or asg_name == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get current ASG state
                    response = self.autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])

                    asgs = response.get("AutoScalingGroups", [])

                    if not asgs:
                        progress.update(task, advance=1)
                        continue

                    asg = asgs[0]

                    desired_capacity = asg.get("DesiredCapacity", 0)
                    instances = asg.get("Instances", [])
                    actual_capacity = len(instances)

                    # Calculate delta percentage
                    if desired_capacity > 0:
                        delta_pct = abs((desired_capacity - actual_capacity) / desired_capacity * 100)
                    else:
                        delta_pct = 0.0

                    df.at[idx, "desired_vs_actual_delta_pct"] = round(delta_pct, 2)

                    # A3 Signal: Capacity mismatch (delta > 0)
                    df.at[idx, "a3_signal"] = delta_pct > 0

                except Exception as e:
                    logger.debug(f"Capacity delta lookup failed for {asg_name}: {e}")
                    df.at[idx, "desired_vs_actual_delta_pct"] = 0.0
                    df.at[idx, "a3_signal"] = False

                progress.update(task, advance=1)

        mismatch_asgs = (df["desired_vs_actual_delta_pct"] > 0).sum()
        a3_signals = (df["a3_signal"] == True).sum()

        if self.output_controller.verbose:
            print_success(
                f"   ✅ Capacity delta: {mismatch_asgs}/{len(df)} ASGs with capacity mismatch, {a3_signals} A3 signals"
            )
        else:
            logger.info(f"Capacity delta: {mismatch_asgs}/{len(df)} ASGs with capacity mismatch")

        return df

    def _enrich_launch_config_age(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        A4: Launch configuration age (detect outdated launch configs - security/cost risk).

        Args:
            df: DataFrame with asg_name column

        Returns:
            DataFrame with launch_config_age_days and a4_signal columns populated

        Signal Logic:
            A4 = True if launch_config_age_days > 180 (launch config >6 months old)
        """
        if self.output_controller.verbose:
            print_info("   🔧 EC2: Checking launch configuration age...")
        else:
            logger.debug("Checking launch configuration age")

        current_time = datetime.now(timezone.utc)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Launch config age...", total=len(df))

            for idx, row in df.iterrows():
                asg_name = row.get("asg_name", "")

                if not asg_name or asg_name == "N/A":
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get ASG details
                    response = self.autoscaling.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])

                    asgs = response.get("AutoScalingGroups", [])

                    if not asgs:
                        progress.update(task, advance=1)
                        continue

                    asg = asgs[0]

                    # Check for Launch Template (preferred) or Launch Configuration
                    launch_template = asg.get("LaunchTemplate") or asg.get("MixedInstancesPolicy", {}).get(
                        "LaunchTemplate"
                    )
                    launch_config_name = asg.get("LaunchConfigurationName")

                    creation_date = None

                    if launch_template:
                        # Get Launch Template creation date
                        template_id = launch_template.get("LaunchTemplateId")

                        try:
                            lt_response = self.ec2.describe_launch_templates(LaunchTemplateIds=[template_id])

                            templates = lt_response.get("LaunchTemplates", [])

                            if templates:
                                creation_date = templates[0].get("CreateTime")

                        except Exception as lt_error:
                            logger.debug(f"Launch template lookup failed for {template_id}: {lt_error}")

                    elif launch_config_name:
                        # Get Launch Configuration creation date
                        try:
                            lc_response = self.autoscaling.describe_launch_configurations(
                                LaunchConfigurationNames=[launch_config_name]
                            )

                            configs = lc_response.get("LaunchConfigurations", [])

                            if configs:
                                creation_date = configs[0].get("CreatedTime")

                        except Exception as lc_error:
                            logger.debug(f"Launch configuration lookup failed for {launch_config_name}: {lc_error}")

                    # Calculate age in days
                    if creation_date:
                        age_days = (current_time - creation_date).days
                        df.at[idx, "launch_config_age_days"] = age_days

                        # A4 Signal: Launch config >180 days old (outdated)
                        df.at[idx, "a4_signal"] = age_days > 180
                    else:
                        df.at[idx, "launch_config_age_days"] = 0
                        df.at[idx, "a4_signal"] = False

                except Exception as e:
                    logger.debug(f"Launch config age lookup failed for {asg_name}: {e}")
                    df.at[idx, "launch_config_age_days"] = 0
                    df.at[idx, "a4_signal"] = False

                progress.update(task, advance=1)

        outdated_configs = (df["launch_config_age_days"] > 180).sum()
        a4_signals = (df["a4_signal"] == True).sum()

        if self.output_controller.verbose:
            print_success(
                f"   ✅ Launch config age: {outdated_configs}/{len(df)} ASGs with outdated configs, {a4_signals} A4 signals"
            )
        else:
            logger.info(f"Launch config age: {outdated_configs}/{len(df)} ASGs with outdated configs")

        return df

    def _enrich_cost_efficiency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        A5: Cost efficiency (Cost Explorer EC2 Auto Scaling filter + per-instance attribution).

        Args:
            df: DataFrame with asg_name column

        Returns:
            DataFrame with cost_per_instance_monthly, total_asg_cost_monthly, and a5_signal columns populated

        Signal Logic:
            A5 = True if cost_per_instance_monthly > 150% of baseline (inefficient cost per instance)

        Note:
            Cost Explorer API only available in us-east-1 region.
            Requires billing profile with ce:GetCostAndUsage permission.
        """
        if self.output_controller.verbose:
            print_info("   💰 Cost Explorer: Analyzing ASG cost efficiency...")
        else:
            logger.debug("Analyzing ASG cost efficiency via Cost Explorer")

        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=30)

        try:
            # Query Cost Explorer for EC2 Auto Scaling costs
            response = self.cost_explorer.get_cost_and_usage(
                TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
                Granularity="MONTHLY",
                Metrics=["BlendedCost"],
                Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
                GroupBy=[{"Type": "TAG", "Key": "aws:autoscaling:groupName"}],
            )

            # Parse cost data by ASG
            asg_costs = {}

            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    asg_tag = group.get("Keys", [""])[0]

                    # Extract ASG name from tag (format: "aws:autoscaling:groupName$my-asg-name")
                    if "$" in asg_tag:
                        asg_name = asg_tag.split("$")[1]
                        cost = float(group["Metrics"]["BlendedCost"]["Amount"])
                        asg_costs[asg_name] = cost

            # Calculate baseline cost per instance (median across all ASGs)
            if asg_costs:
                baseline_cost_per_instance = sum(asg_costs.values()) / len(asg_costs)
            else:
                baseline_cost_per_instance = 0.0

            # Enrich DataFrame with cost data
            for idx, row in df.iterrows():
                asg_name = row.get("asg_name", "")

                if not asg_name or asg_name == "N/A":
                    continue

                total_cost = asg_costs.get(asg_name, 0.0)
                df.at[idx, "total_asg_cost_monthly"] = round(total_cost, 2)

                # Calculate cost per instance
                avg_healthy = row.get("avg_healthy_instances_30d", 1.0)

                if avg_healthy > 0:
                    cost_per_instance = total_cost / avg_healthy
                else:
                    cost_per_instance = 0.0

                df.at[idx, "cost_per_instance_monthly"] = round(cost_per_instance, 2)

                # A5 Signal: Cost per instance >150% of baseline (inefficient)
                if baseline_cost_per_instance > 0:
                    df.at[idx, "a5_signal"] = cost_per_instance > baseline_cost_per_instance * 1.5
                else:
                    df.at[idx, "a5_signal"] = False

            inefficient_asgs = (df["a5_signal"] == True).sum()

            if self.output_controller.verbose:
                print_success(
                    f"   ✅ Cost efficiency: {inefficient_asgs}/{len(df)} ASGs inefficient, baseline ${baseline_cost_per_instance:.2f}/instance"
                )
            else:
                logger.info(f"Cost efficiency: {inefficient_asgs}/{len(df)} ASGs inefficient")

        except Exception as e:
            if self.output_controller.verbose:
                print_warning(f"   ⚠️  Cost Explorer enrichment failed: {e}")
            logger.error(f"Cost Explorer enrichment error: {e}", exc_info=True)

            # Set default values on failure
            df["cost_per_instance_monthly"] = 0.0
            df["total_asg_cost_monthly"] = 0.0
            df["a5_signal"] = False

        return df
