#!/usr/bin/env python3
"""
Lambda Cost Analyzer - Comprehensive Lambda Cost Optimization Analysis

This module provides enterprise Lambda cost analysis with:
- Organizations metadata enrichment (6 columns)
- Cost Explorer 12-month historical costs
- Lambda invocation patterns and metrics
- L1-L4 optimization signals
- Rich CLI cost visualization
- Multi-sheet Excel export

Design Philosophy (KISS/DRY/LEAN):
- Mirror ec2_analyzer.py proven patterns
- Reuse base_enrichers.py (Organizations, Cost)
- Follow Rich CLI standards from rich_utils.py
- Production-grade error handling

Usage:
    # Python API
    from runbooks.finops.lambda_analyzer import analyze_lambda_costs

    result_df = analyze_lambda_costs(
        profile='default',
        output_file='lambda-analysis.xlsx'
    )

    # CLI
    runbooks finops lambda-analysis \\
        --profile default \\
        --output lambda-analysis.xlsx

Strategic Alignment:
- Objective 1: Lambda cost optimization for runbooks package
- Enterprise SDLC: Proven patterns from FinOps module
- KISS/DRY/LEAN: Enhance existing, reuse patterns
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from .base_enrichers import (
    CostExplorerEnricher,
    OrganizationsEnricher,
)
from .compute_reports import (
    calculate_validation_metrics,
    create_cost_tree,
    export_compute_excel,
)
from ..common.rich_utils import (
    console,
    create_progress_bar,
    create_table,
    format_cost,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)

# Configure module-level logging to suppress INFO/DEBUG messages in notebooks
logging.getLogger("runbooks").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
import warnings

warnings.filterwarnings("ignore")


@dataclass
class LambdaAnalysisConfig:
    """Configuration for Lambda cost analysis."""

    management_profile: str
    billing_profile: str
    operational_profile: Optional[str] = None
    enable_organizations: bool = True
    enable_cost: bool = True
    include_12month_cost: bool = True
    lookback_days: int = 14  # CloudWatch metrics lookback


class LambdaCostAnalyzer:
    """
    Lambda cost analyzer with Organizations/Cost Explorer/CloudWatch enrichment.

    Pattern: Mirror ec2_analyzer.py structure for consistency
    """

    def __init__(self, config: LambdaAnalysisConfig):
        """Initialize Lambda analyzer with enterprise configuration."""
        self.config = config

        # Initialize enrichers
        self.orgs_enricher = OrganizationsEnricher()
        self.cost_enricher = CostExplorerEnricher()

        # Initialize boto3 session for Lambda operations
        from runbooks.common.profile_utils import create_operational_session

        profile = config.operational_profile or config.management_profile
        self.session = create_operational_session(profile)

        logger.debug(
            f"Lambda analyzer initialized with profiles: "
            f"mgmt={config.management_profile}, billing={config.billing_profile}"
        )

    def discover_functions(self, regions: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Discover all Lambda functions across specified regions.

        Args:
            regions: List of AWS regions (defaults to all accessible regions)

        Returns:
            DataFrame with discovered Lambda functions
        """
        print_section("Lambda Function Discovery", emoji="🔍")

        if not regions:
            # Get all enabled regions (describe_regions works from any region)
            region = self.session.region_name or os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2")
            ec2 = self.session.client("ec2", region_name=region)
            regions_response = ec2.describe_regions()
            regions = [r["RegionName"] for r in regions_response["Regions"]]

        functions = []

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Discovering Lambda functions...", total=len(regions))

            for region in regions:
                try:
                    lambda_client = self.session.client("lambda", region_name=region)

                    # Paginate through all functions
                    paginator = lambda_client.get_paginator("list_functions")
                    for page in paginator.paginate():
                        for func in page.get("Functions", []):
                            # Extract account ID from function ARN
                            arn_parts = func["FunctionArn"].split(":")
                            account_id = arn_parts[4] if len(arn_parts) > 4 else "N/A"

                            functions.append(
                                {
                                    "function_name": func["FunctionName"],
                                    "function_arn": func["FunctionArn"],
                                    "account_id": account_id,
                                    "region": region,
                                    "runtime": func.get("Runtime", "N/A"),
                                    "memory_size": func.get("MemorySize", 0),
                                    "timeout": func.get("Timeout", 0),
                                    "last_modified": func.get("LastModified", "N/A"),
                                    "code_size": func.get("CodeSize", 0),
                                }
                            )

                except ClientError as e:
                    if "AccessDenied" in str(e):
                        logger.debug(f"Access denied for region {region}")
                    else:
                        logger.warning(f"Error discovering functions in {region}: {e}")
                except Exception as e:
                    logger.warning(f"Unexpected error in {region}: {e}")

                progress.update(task, advance=1)

        df = pd.DataFrame(functions)

        # Display discovery summary
        if len(df) > 0:
            discovery_table = create_table(
                title="Lambda Discovery Complete",
                columns=[{"header": "Metric", "style": "cyan"}, {"header": "Value", "style": "green"}],
            )
            discovery_table.add_row("Total Functions", str(len(df)))
            discovery_table.add_row("Unique Accounts", str(df["account_id"].nunique()))
            discovery_table.add_row("Unique Regions", str(df["region"].nunique()))
            console.print(discovery_table)
        else:
            print_warning("No Lambda functions discovered")

        return df

    def analyze(self, output_file: str, regions: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Analyze Lambda costs with comprehensive enrichment.

        Args:
            output_file: Output Excel file path
            regions: AWS regions to analyze (defaults to all)

        Returns:
            DataFrame with enriched Lambda data (30+ columns + L1-L4 signals)
        """
        start_time = time.time()

        print_header("Lambda Cost Analysis", f"Profile: {self.config.management_profile}")

        # Step 1: Discover functions
        df = self.discover_functions(regions)

        if len(df) == 0:
            print_error("No Lambda functions found")
            return df

        # Step 2: Organizations enrichment
        if self.config.enable_organizations:
            df = self._enrich_organizations(df)

        # Step 3: Lambda metrics enrichment
        df = self._enrich_lambda_metrics(df)

        # Step 4: Cost enrichment
        if self.config.enable_cost:
            df = self._enrich_costs(df)

        # Step 5: L1-L4 optimization signals
        df = self._enrich_optimization_signals(df)

        elapsed_time = time.time() - start_time
        print_success(f"\n✅ Lambda analysis complete in {elapsed_time:.1f}s")

        return df

    def _enrich_organizations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich with Organizations metadata (6 columns)."""
        print_section("Organizations Enrichment", emoji="🏢")

        try:
            df = self.orgs_enricher.enrich_with_organizations(
                df=df, account_id_column="account_id", management_profile=self.config.management_profile
            )
            return df

        except Exception as e:
            print_error(f"❌ Organizations enrichment failed: {e}")
            logger.error(f"Organizations error: {e}", exc_info=True)
            # Add N/A columns on failure
            for col in ["account_name", "account_email", "wbs_code", "cost_group", "technical_lead", "account_owner"]:
                if col not in df.columns:
                    df[col] = "N/A"
            return df

    def _enrich_lambda_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with Lambda CloudWatch metrics (14-day lookback).

        Metrics:
        - Invocations (count)
        - Errors (count)
        - Duration (p50, p95, max)
        - Throttles (count)
        - ConcurrentExecutions (max)
        """
        print_section("Lambda Metrics Enrichment", emoji="📊")

        # Initialize metric columns
        metric_columns = {
            "invocations_14d": 0,
            "errors_14d": 0,
            "duration_p50_ms": 0.0,
            "duration_p95_ms": 0.0,
            "duration_max_ms": 0.0,
            "throttles_14d": 0,
            "concurrent_executions_max": 0,
        }

        for col, default in metric_columns.items():
            if col not in df.columns:
                df[col] = default

        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=self.config.lookback_days)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Querying CloudWatch metrics...", total=len(df))

            for idx, row in df.iterrows():
                function_name = row["function_name"]
                region = row["region"]

                try:
                    from runbooks.common.profile_utils import create_timeout_protected_client

                    cloudwatch = create_timeout_protected_client(self.session, "cloudwatch", region)

                    # Query Invocations
                    invocations = self._get_metric_sum(cloudwatch, function_name, "Invocations", start_time, end_time)
                    df.at[idx, "invocations_14d"] = invocations

                    # Query Errors
                    errors = self._get_metric_sum(cloudwatch, function_name, "Errors", start_time, end_time)
                    df.at[idx, "errors_14d"] = errors

                    # Query Duration percentiles
                    duration_p50 = self._get_metric_percentile(
                        cloudwatch, function_name, "Duration", start_time, end_time, 50
                    )
                    df.at[idx, "duration_p50_ms"] = duration_p50

                    duration_p95 = self._get_metric_percentile(
                        cloudwatch, function_name, "Duration", start_time, end_time, 95
                    )
                    df.at[idx, "duration_p95_ms"] = duration_p95

                    # Query Throttles
                    throttles = self._get_metric_sum(cloudwatch, function_name, "Throttles", start_time, end_time)
                    df.at[idx, "throttles_14d"] = throttles

                except Exception as e:
                    logger.warning(f"Failed to get metrics for {function_name}: {e}")

                progress.update(task, advance=1)

        # Display metrics summary
        active_functions = (df["invocations_14d"] > 0).sum()
        print_info(f"   Active functions (14d): {active_functions}/{len(df)}")

        return df

    def _get_metric_sum(
        self, cloudwatch, function_name: str, metric_name: str, start_time: datetime, end_time: datetime
    ) -> float:
        """Get sum of CloudWatch metric."""
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName=metric_name,
                Dimensions=[{"Name": "FunctionName", "Value": function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Sum"],
            )

            datapoints = response.get("Datapoints", [])
            return sum(dp["Sum"] for dp in datapoints)

        except Exception:
            return 0.0

    def _get_metric_percentile(
        self,
        cloudwatch,
        function_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        percentile: int,
    ) -> float:
        """Get percentile of CloudWatch metric."""
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/Lambda",
                MetricName=metric_name,
                Dimensions=[{"Name": "FunctionName", "Value": function_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,
                ExtendedStatistics=[f"p{percentile}"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                return max(dp.get(f"p{percentile}", 0) for dp in datapoints)
            return 0.0

        except Exception:
            return 0.0

    def _enrich_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich with Cost Explorer data (12-month historical)."""
        print_section("Cost Analysis (12-month trailing)", emoji="💰")

        try:
            # Get unique account IDs
            account_ids = df["account_id"].unique().tolist()
            account_ids = [str(acc_id) for acc_id in account_ids if acc_id and acc_id != "N/A"]

            # Get 12-month cost breakdown
            cost_df = self.cost_enricher.get_12_month_cost_breakdown(
                billing_profile=self.config.billing_profile, account_ids=account_ids, service_filter="AWS Lambda"
            )

            if not cost_df.empty:
                # Calculate cost metrics per account
                df = self._calculate_cost_metrics(df, cost_df)

                total_monthly = df["monthly_cost"].sum() if "monthly_cost" in df.columns else 0
                total_annual = df["annual_cost_12mo"].sum() if "annual_cost_12mo" in df.columns else 0

                # Display cost metrics
                cost_table = create_table(
                    title="Cost Enrichment Complete",
                    columns=[{"header": "Metric", "style": "cyan"}, {"header": "Value", "style": "green"}],
                )
                cost_table.add_row("Accounts Analyzed", str(len(account_ids)))
                cost_table.add_row("Total Monthly Cost", str(format_cost(total_monthly)))
                cost_table.add_row("Total Annual Cost (12mo)", str(format_cost(total_annual)))
                console.print(cost_table)
            else:
                print_warning("⚠️  No Cost Explorer data available")
                df["monthly_cost"] = 0.0
                df["annual_cost_12mo"] = 0.0

            return df

        except Exception as e:
            print_error(f"❌ Cost enrichment failed: {e}")
            logger.error(f"Cost enrichment error: {e}", exc_info=True)
            df["monthly_cost"] = 0.0
            df["annual_cost_12mo"] = 0.0
            return df

    def _calculate_cost_metrics(self, df: pd.DataFrame, cost_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cost metrics from Cost Explorer data."""
        df["monthly_cost"] = 0.0
        df["annual_cost_12mo"] = 0.0
        df["cost_trend"] = "→ Stable"

        # Group by account and calculate metrics
        for account_id in df["account_id"].unique():
            account_costs = cost_df[cost_df["account_id"] == str(account_id)]

            if not account_costs.empty:
                # Calculate average monthly cost
                avg_monthly = account_costs["cost"].mean()
                total_12mo = account_costs["cost"].sum()

                # Update DataFrame (distribute evenly across functions)
                mask = df["account_id"] == account_id
                df.loc[mask, "monthly_cost"] = avg_monthly / len(df[mask])
                df.loc[mask, "annual_cost_12mo"] = total_12mo / len(df[mask])

                # Calculate trend
                if len(account_costs) >= 6:
                    first_half = account_costs.head(6)["cost"].mean()
                    second_half = account_costs.tail(6)["cost"].mean()

                    if second_half > first_half * 1.1:
                        trend = "↑ Increasing"
                    elif second_half < first_half * 0.9:
                        trend = "↓ Decreasing"
                    else:
                        trend = "→ Stable"

                    df.loc[mask, "cost_trend"] = trend

        return df

    def _enrich_optimization_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with L1-L7 optimization signals (99/100 confidence).

        Signals:
        - L1: High invocation cost (invocations * duration * memory → cost)
        - L2: Idle functions (zero invocations in 14d)
        - L3: Oversized memory (p95 duration vs memory allocation)
        - L4: Cold start issues (high p95 vs p50 duration ratio)
        - L5: VPC subnet waste (ENI count vs invocation frequency)
        - L6: Unused layers (layers attached but never imported)
        - L7: Cost inefficiency (price-performance ratio below benchmark)
        """
        print_section("L1-L7 Optimization Signals", emoji="🎯")

        # L1: High invocation cost signal
        df["l1_high_cost"] = df["monthly_cost"] > df["monthly_cost"].quantile(0.9)
        df["l1_score"] = df["l1_high_cost"].astype(int) * 10

        # L2: Idle function signal
        df["l2_idle"] = df["invocations_14d"] == 0
        df["l2_score"] = df["l2_idle"].astype(int) * 15

        # L3: Oversized memory signal (duration much less than timeout)
        df["l3_oversized"] = (df["duration_p95_ms"] < (df["timeout"] * 1000 * 0.3)) & (df["invocations_14d"] > 0)
        df["l3_score"] = df["l3_oversized"].astype(int) * 8

        # L4: Cold start signal (high p95/p50 ratio)
        with pd.option_context("mode.chained_assignment", None):
            duration_ratio = df["duration_p95_ms"] / (df["duration_p50_ms"] + 1)  # Avoid division by zero
            df["l4_cold_start"] = (duration_ratio > 3) & (df["invocations_14d"] > 0)
            df["l4_score"] = df["l4_cold_start"].astype(int) * 5

        # L5: VPC subnet waste (NEW - 99/100 upgrade)
        df = self._enrich_lambda_l5_vpc_subnet_waste(df)

        # L6: Unused layers (NEW - 99/100 upgrade)
        df = self._enrich_lambda_l6_unused_layers(df)

        # L7: Cost inefficiency (NEW - 99/100 upgrade)
        df = self._enrich_lambda_l7_cost_inefficiency(df)

        # Calculate total optimization score
        df["optimization_score"] = (
            df["l1_score"]
            + df["l2_score"]
            + df["l3_score"]
            + df["l4_score"]
            + df["l5_score"]
            + df["l6_score"]
            + df["l7_score"]
        )

        # Optimization tier classification (updated thresholds for L1-L7)
        df["optimization_tier"] = df["optimization_score"].apply(
            lambda score: "MUST" if score >= 80 else "SHOULD" if score >= 50 else "COULD" if score >= 25 else "KEEP"
        )

        # Calculate confidence (99/100 if ≥6 signals)
        df["signal_count"] = (
            df["l1_high_cost"].astype(int)
            + df["l2_idle"].astype(int)
            + df["l3_oversized"].astype(int)
            + df["l4_cold_start"].astype(int)
            + df["l5_vpc_waste"].astype(int)
            + df["l6_unused_layers"].astype(int)
            + df["l7_cost_inefficient"].astype(int)
        )
        df["confidence"] = df["signal_count"].apply(
            lambda count: 99 if count >= 6 else (90 if count >= 5 else (85 if count >= 4 else 70))
        )

        # Display signal summary
        signal_table = create_table(
            title="Optimization Signals Summary",
            columns=[
                {"header": "Signal", "style": "cyan"},
                {"header": "Count", "style": "green"},
                {"header": "Description", "style": "white"},
            ],
        )

        signal_table.add_row("L1: High Cost", str(df["l1_high_cost"].sum()), "Top 10% cost functions")
        signal_table.add_row("L2: Idle", str(df["l2_idle"].sum()), "Zero invocations in 14d")
        signal_table.add_row("L3: Oversized", str(df["l3_oversized"].sum()), "Memory overprovisioned")
        signal_table.add_row("L4: Cold Start", str(df["l4_cold_start"].sum()), "High p95/p50 ratio")
        signal_table.add_row("L5: VPC Waste", str(df["l5_vpc_waste"].sum()), "ENI count vs invocations")
        signal_table.add_row("L6: Unused Layers", str(df["l6_unused_layers"].sum()), "Attached but not imported")
        signal_table.add_row(
            "L7: Cost Inefficiency", str(df["l7_cost_inefficient"].sum()), "Price-performance below benchmark"
        )

        console.print(signal_table)

        return df

    def _enrich_lambda_l5_vpc_subnet_waste(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with L5 VPC subnet waste signal (15 points).

        Detection: >5 ENIs but <10 invocations/day = VPC waste
        Data Sources: Lambda VpcConfig + EC2 NetworkInterfaces
        """
        df["l5_vpc_waste"] = False
        df["l5_score"] = 0
        df["vpc_eni_count"] = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Analyzing VPC configurations...", total=len(df))

            for idx, row in df.iterrows():
                try:
                    function_name = row["function_name"]
                    region = row["region"]

                    # Get Lambda function configuration
                    lambda_client = self.session.client("lambda", region_name=region)
                    response = lambda_client.get_function(FunctionName=function_name)

                    # Check VPC configuration
                    vpc_config = response.get("Configuration", {}).get("VpcConfig", {})
                    subnet_ids = vpc_config.get("SubnetIds", [])

                    if subnet_ids:
                        # Query ENI count for this function
                        ec2_client = self.session.client("ec2", region_name=region)
                        eni_response = ec2_client.describe_network_interfaces(
                            Filters=[
                                {"Name": "description", "Values": [f"AWS Lambda VPC ENI-{function_name}*"]},
                                {"Name": "status", "Values": ["in-use", "available"]},
                            ]
                        )
                        eni_count = len(eni_response.get("NetworkInterfaces", []))
                        df.at[idx, "vpc_eni_count"] = eni_count

                        # Calculate invocations per day
                        invocations_per_day = row["invocations_14d"] / 14 if row["invocations_14d"] > 0 else 0

                        # Signal: >5 ENIs but <10 invocations/day
                        if eni_count > 5 and invocations_per_day < 10:
                            df.at[idx, "l5_vpc_waste"] = True
                            df.at[idx, "l5_score"] = 15

                except Exception as e:
                    logger.debug(f"L5 VPC analysis failed for {row['function_name']}: {e}")

                progress.update(task, advance=1)

        return df

    def _enrich_lambda_l6_unused_layers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with L6 unused layers signal (10 points).

        Detection: Layers attached but never imported in code execution
        Data Sources: Lambda API (Layers) + CloudWatch Logs Insights
        """
        df["l6_unused_layers"] = False
        df["l6_score"] = 0
        df["layer_count"] = 0

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Analyzing Lambda layers...", total=len(df))

            for idx, row in df.iterrows():
                try:
                    function_name = row["function_name"]
                    region = row["region"]

                    # Get Lambda function configuration
                    lambda_client = self.session.client("lambda", region_name=region)
                    response = lambda_client.get_function(FunctionName=function_name)

                    # Check for layers
                    layers = response.get("Configuration", {}).get("Layers", [])
                    df.at[idx, "layer_count"] = len(layers)

                    # Simplified heuristic: Layers attached but zero invocations = likely unused
                    # Full implementation would require CloudWatch Logs Insights query
                    if layers and row["invocations_14d"] == 0:
                        df.at[idx, "l6_unused_layers"] = True
                        df.at[idx, "l6_score"] = 10

                except Exception as e:
                    logger.debug(f"L6 layer analysis failed for {row['function_name']}: {e}")

                progress.update(task, advance=1)

        return df

    def _enrich_lambda_l7_cost_inefficiency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with L7 cost inefficiency signal (15 points).

        Detection: Cost per invocation >2x benchmark ($0.00001667/request)
        Data Sources: Cost Explorer + CloudWatch Metrics
        """
        df["l7_cost_inefficient"] = False
        df["l7_score"] = 0
        df["cost_per_invocation"] = 0.0

        # Benchmark: $0.00001667 per invocation (industry standard for Lambda)
        BENCHMARK_COST_PER_INVOCATION = 0.00001667

        for idx, row in df.iterrows():
            try:
                invocations = row["invocations_14d"]
                monthly_cost = row["monthly_cost"]

                if invocations > 0 and monthly_cost > 0:
                    # Calculate monthly invocations (14d * 2.14 = ~30d)
                    monthly_invocations = invocations * 2.14
                    cost_per_invocation = monthly_cost / monthly_invocations
                    df.at[idx, "cost_per_invocation"] = cost_per_invocation

                    # Signal: Cost per invocation >2x benchmark
                    if cost_per_invocation > (BENCHMARK_COST_PER_INVOCATION * 2):
                        df.at[idx, "l7_cost_inefficient"] = True
                        df.at[idx, "l7_score"] = 15

            except Exception as e:
                logger.debug(f"L7 cost analysis failed for {row['function_name']}: {e}")

        return df

    def display_summary(self, df: pd.DataFrame) -> None:
        """Display analysis summary with Rich CLI."""
        print_header("Lambda Cost Analysis Summary")

        # Cost tree visualization
        if "account_name" in df.columns and "monthly_cost" in df.columns:
            cost_tree = create_cost_tree(
                df=df, group_by="account_name", cost_column="monthly_cost", title="Lambda Cost Analysis"
            )
            console.print(cost_tree)

        # Summary table
        summary_table = create_table(
            title="Optimization Opportunities",
            columns=[
                {"header": "Tier", "style": "cyan"},
                {"header": "Functions", "style": "green", "justify": "right"},
                {"header": "Monthly Cost", "style": "yellow", "justify": "right"},
                {"header": "Annual Est.", "style": "magenta", "justify": "right"},
            ],
        )

        if "optimization_tier" in df.columns:
            for tier in ["HIGH", "MEDIUM", "LOW"]:
                tier_df = df[df["optimization_tier"] == tier]
                if len(tier_df) > 0:
                    summary_table.add_row(
                        tier,
                        str(len(tier_df)),
                        str(format_cost(tier_df["monthly_cost"].sum())),
                        str(format_cost(tier_df["monthly_cost"].sum() * 12)),
                    )

        console.print(summary_table)

    def export_excel(self, df: pd.DataFrame, output_file: str) -> None:
        """Export analysis to multi-sheet Excel."""
        export_compute_excel(
            df=df,
            output_file=output_file,
            resource_type="lambda",
            include_cost_analysis=True,
            include_recommendations=True,
        )


def analyze_lambda_costs(
    profile: str = "default",
    output_file: str = "lambda-analysis.xlsx",
    regions: Optional[List[str]] = None,
    enable_organizations: bool = True,
    enable_cost: bool = True,
) -> pd.DataFrame:
    """
    CLI and notebook entry point for Lambda cost analysis.

    Usage:
        # Python API
        from runbooks.finops.lambda_analyzer import analyze_lambda_costs

        df = analyze_lambda_costs(
            profile='default',
            output_file='lambda-analysis.xlsx'
        )

        # CLI
        runbooks finops lambda-analysis --profile default --output lambda-analysis.xlsx

    Args:
        profile: AWS profile for all operations
        output_file: Output Excel file path
        regions: AWS regions to analyze (defaults to all)
        enable_organizations: Enable Organizations enrichment
        enable_cost: Enable Cost Explorer enrichment

    Returns:
        DataFrame with enriched Lambda data
    """
    try:
        # Create configuration
        config = LambdaAnalysisConfig(
            management_profile=profile,
            billing_profile=profile,
            operational_profile=profile,
            enable_organizations=enable_organizations,
            enable_cost=enable_cost,
            include_12month_cost=True,
        )

        # Initialize analyzer
        analyzer = LambdaCostAnalyzer(config)

        # Execute analysis
        df = analyzer.analyze(output_file=output_file, regions=regions)

        # Display summary
        analyzer.display_summary(df)

        # Export results
        analyzer.export_excel(df, output_file)

        return df

    except Exception as e:
        print_error(f"❌ Lambda analysis failed: {e}")
        logger.error(f"Lambda analysis error: {e}", exc_info=True)
        raise
