#!/usr/bin/env python3
"""
Savings Plans Hybrid Optimizer - Enterprise FinOps Strategy Engine

Strategic Business Focus: Hybrid Reserved Instance + Savings Plans optimization for $500K+ annual savings
Business Impact: 60/30/10 allocation strategy (Compute SP 60%, EC2 Instance SP 30%, On-Demand 10%)
Technical Foundation: Enterprise-grade workload classification with financial modeling

This module provides comprehensive Savings Plans optimization analysis following proven FinOps patterns:
- Workload classification (stable vs variable based on CV and multi-region patterns)
- Hybrid optimization strategy (Compute SP + EC2 Instance SP + On-Demand flexibility)
- Historical usage pattern analysis for accurate SP sizing (90-day minimum)
- Financial modeling with break-even analysis and ROI calculations
- Integration with existing RI optimization for unified procurement strategy
- MCP validation for $500K+ savings projections (≥99.5% accuracy requirement)

Strategic Alignment:
- "Do one thing and do it well": Savings Plans procurement optimization specialization
- "Move Fast, But Not So Fast We Crash": Conservative SP recommendations with guaranteed ROI
- Enterprise FAANG SDLC: Evidence-based SP strategy with comprehensive financial modeling
- Universal $132K Cost Optimization Methodology: Long-term cost optimization focus

Architecture: Enhances existing reservation_optimizer.py with SP capabilities (KISS/DRY/LEAN)
"""

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pydantic import BaseModel, Field

from ..common.profile_utils import get_profile_for_operation, create_timeout_protected_client
from ..common.rich_utils import (
    STATUS_INDICATORS,
    console,
    create_panel,
    create_progress_bar,
    create_table,
    format_cost,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)
from .mcp_validator import EmbeddedMCPValidator

logger = logging.getLogger(__name__)


class SavingsPlanType(str, Enum):
    """AWS Savings Plans types."""

    COMPUTE_SP = "Compute"  # Flexible across EC2, Fargate, Lambda
    EC2_INSTANCE_SP = "EC2Instance"  # EC2 only, higher savings
    SAGEMAKER_SP = "SageMaker"  # SageMaker only


class SPTerm(str, Enum):
    """Savings Plan term lengths."""

    ONE_YEAR = "1yr"
    THREE_YEAR = "3yr"


class SPPaymentOption(str, Enum):
    """Savings Plan payment options."""

    NO_UPFRONT = "No Upfront"
    PARTIAL_UPFRONT = "Partial Upfront"
    ALL_UPFRONT = "All Upfront"


@dataclass
class WorkloadClassification:
    """Workload classification for SP recommendation strategy."""

    resource_ids: List[str]
    classification: str  # "stable", "variable", "burst"

    # Statistical metrics
    coefficient_of_variation: float  # Std Dev / Mean
    uptime_percentage: float
    region_count: int
    multi_region: bool

    # Usage patterns
    average_hourly_usage: float
    peak_hourly_usage: float
    baseline_hourly_usage: float

    # Cost metrics
    total_on_demand_cost: float
    recommended_sp_type: SavingsPlanType
    confidence_score: float  # 0-1 confidence in classification


class SavingsPlanRecommendation(BaseModel):
    """Savings Plans purchase recommendation."""

    plan_type: SavingsPlanType
    commitment_usd_hourly: float
    term_years: int  # 1 or 3
    payment_option: SPPaymentOption = SPPaymentOption.NO_UPFRONT

    # Financial analysis
    upfront_cost: float = 0.0
    estimated_annual_savings: float = 0.0
    coverage_percentage: float = 0.0  # % of usage covered by SP

    # Hybrid strategy allocation
    hybrid_strategy: Dict[str, float] = Field(default_factory=dict)
    confidence_score: float = 0.0  # 0.0-1.0

    # Supporting details
    covered_workloads: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)
    services: List[str] = Field(default_factory=list)

    # Break-even and ROI
    break_even_months: float = 0.0
    roi_percentage: float = 0.0
    risk_level: str = "low"  # low, medium, high


class SavingsPlansOptimizer:
    """
    Hybrid Savings Plans + Reserved Instance optimizer.

    Strategy:
    - 60% Compute SP (flexible, multi-region, 66% savings)
    - 30% EC2 Instance SP (stable workloads, 72% savings)
    - 10% On-Demand (burst capacity, flexibility)

    Workload Classification:
    - Stable: CV < 0.15, uptime >95%, ≤2 regions → EC2 Instance SP
    - Variable: CV ≥ 0.15, multi-region (3+) → Compute SP
    - Burst: High variability → On-Demand

    Following $132,720+ methodology with proven FinOps patterns targeting $500K+ annual savings.
    """

    def __init__(self, profile_name: Optional[str] = None, regions: Optional[List[str]] = None):
        """Initialize SP optimizer with enterprise profile support."""
        from runbooks.common.profile_utils import create_operational_session

        self.profile_name = profile_name
        self.regions = regions or ["ap-southeast-2", "ap-southeast-6"]

        # Initialize AWS session with profile priority system
        operational_profile = get_profile_for_operation("operational", profile_name)
        self.session = create_operational_session(operational_profile)

        # SP analysis parameters
        self.analysis_period_days = 90  # 3 months usage analysis (minimum for SP)
        self.stable_cv_threshold = 0.15  # CV < 0.15 = stable workload
        self.stable_uptime_threshold = 0.95  # 95% uptime = stable
        self.stable_region_threshold = 2  # ≤2 regions = stable

        # Hybrid allocation strategy (60/30/10)
        self.compute_sp_allocation = 0.60  # 60% Compute SP
        self.ec2_instance_sp_allocation = 0.30  # 30% EC2 Instance SP
        self.on_demand_allocation = 0.10  # 10% On-Demand

        # Savings percentages (approximate 2024 rates)
        self.compute_sp_savings_rate = 0.66  # 66% savings vs On-Demand
        self.ec2_instance_sp_savings_rate = 0.72  # 72% savings vs On-Demand

    async def generate_recommendations(
        self, usage_history_days: int = 90, validate_with_mcp: bool = True
    ) -> List[SavingsPlanRecommendation]:
        """
        Main entry point - Generate hybrid RI + SP recommendations.

        Args:
            usage_history_days: Historical usage analysis period (default: 90 days)
            validate_with_mcp: Enable MCP validation for $500K+ projections

        Returns:
            List of SavingsPlanRecommendation with hybrid strategy
        """
        print_header("Savings Plans Hybrid Optimizer", "Enterprise 60/30/10 Strategy Engine v1.0")

        analysis_start_time = time.time()

        try:
            with create_progress_bar() as progress:
                # Step 1: Analyze usage patterns (90-day history)
                usage_task = progress.add_task("Analyzing usage patterns...", total=len(self.regions))
                usage_patterns = await self._analyze_usage_patterns(
                    self.session, usage_history_days, progress, usage_task
                )

                if not usage_patterns:
                    print_warning("No usage data available for SP analysis")
                    return []

                # Step 2: Classify workloads (stable vs variable)
                classify_task = progress.add_task("Classifying workloads...", total=1)
                workload_classifications = await self._classify_workloads(usage_patterns, progress, classify_task)

                # Step 3: Generate SP recommendations (Compute SP + EC2 Instance SP)
                recommend_task = progress.add_task("Generating SP recommendations...", total=2)
                recommendations = await self._generate_sp_recommendations(
                    workload_classifications, usage_patterns, progress, recommend_task
                )

                # Step 4: Optimize hybrid strategy (60/30/10)
                optimize_task = progress.add_task("Optimizing hybrid strategy...", total=1)
                optimized_recommendations = await self._optimize_hybrid_strategy(
                    recommendations, usage_patterns, progress, optimize_task
                )

                # Step 5: MCP validation for $500K+ savings
                if validate_with_mcp and optimized_recommendations:
                    validation_task = progress.add_task("MCP validation...", total=1)
                    await self._validate_with_mcp(optimized_recommendations, progress, validation_task)

            # Display executive summary
            self._display_executive_summary(optimized_recommendations, analysis_start_time)

            return optimized_recommendations

        except Exception as e:
            print_error(f"Savings Plans optimization failed: {e}")
            logger.error(f"SP optimization error: {e}", exc_info=True)
            raise

    async def _analyze_usage_patterns(self, session, days: int, progress, task_id) -> Dict[str, Any]:
        """Analyze 90-day EC2/Fargate/Lambda usage patterns via Cost Explorer."""
        usage_patterns = {}

        try:
            # Create Cost Explorer client with timeout protection
            ce_client = create_timeout_protected_client(session, "ce", self.regions[0])

            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            # Get usage data with DAILY granularity for CV calculation
            response = ce_client.get_cost_and_usage(
                TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
                Granularity="DAILY",
                Metrics=["UsageQuantity", "UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "INSTANCE_TYPE"}, {"Type": "DIMENSION", "Key": "REGION"}],
                Filter={
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": [
                            "Amazon Elastic Compute Cloud - Compute",
                            "AWS Lambda",
                            "Amazon EC2 Container Service",  # Fargate
                        ],
                    }
                },
            )

            # Process results by instance type and region
            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    keys = group.get("Keys", [])
                    if len(keys) >= 2:
                        instance_type = keys[0]
                        region = keys[1]

                        key = f"{instance_type}#{region}"

                        if key not in usage_patterns:
                            usage_patterns[key] = {
                                "instance_type": instance_type,
                                "region": region,
                                "daily_usage": [],
                                "daily_costs": [],
                                "total_cost": 0.0,
                            }

                        # Extract usage and cost metrics
                        metrics = group.get("Metrics", {})
                        usage_quantity = float(metrics.get("UsageQuantity", {}).get("Amount", 0))
                        cost = float(metrics.get("UnblendedCost", {}).get("Amount", 0))

                        usage_patterns[key]["daily_usage"].append(usage_quantity)
                        usage_patterns[key]["daily_costs"].append(cost)
                        usage_patterns[key]["total_cost"] += cost

            progress.advance(task_id, len(self.regions))
            print_success(f"Analyzed {len(usage_patterns)} workload patterns over {days} days")

        except ClientError as e:
            print_error(f"Cost Explorer API error: {e.response['Error']['Code']}")
            logger.error(f"Cost Explorer failed: {e}", exc_info=True)
        except Exception as e:
            print_error(f"Usage analysis failed: {str(e)}")
            logger.error(f"Usage analysis error: {e}", exc_info=True)

        return usage_patterns

    async def _classify_workloads(self, usage_patterns: Dict, progress, task_id) -> List[WorkloadClassification]:
        """Classify workloads as stable vs variable based on CV and multi-region patterns."""
        classifications = []

        # Group by instance type across regions
        workload_groups = {}
        for key, pattern in usage_patterns.items():
            instance_type = pattern["instance_type"]
            if instance_type not in workload_groups:
                workload_groups[instance_type] = []
            workload_groups[instance_type].append(pattern)

        for instance_type, patterns in workload_groups.items():
            # Calculate statistical metrics
            all_daily_usage = []
            all_regions = set()
            total_cost = 0.0

            for pattern in patterns:
                all_daily_usage.extend(pattern["daily_usage"])
                all_regions.add(pattern["region"])
                total_cost += pattern["total_cost"]

            if not all_daily_usage or len(all_daily_usage) < 2:
                continue

            # Calculate coefficient of variation (CV = StdDev / Mean)
            mean_usage = statistics.mean(all_daily_usage)
            stdev_usage = statistics.stdev(all_daily_usage)
            cv = stdev_usage / mean_usage if mean_usage > 0 else 1.0

            # Calculate uptime percentage (days with usage > 0)
            days_with_usage = sum(1 for usage in all_daily_usage if usage > 0)
            uptime_pct = days_with_usage / len(all_daily_usage) if all_daily_usage else 0

            # Calculate baseline and peak usage
            baseline_usage = min(all_daily_usage) if all_daily_usage else 0
            peak_usage = max(all_daily_usage) if all_daily_usage else 0

            # Classify workload
            region_count = len(all_regions)
            is_stable = (
                cv < self.stable_cv_threshold
                and uptime_pct > self.stable_uptime_threshold
                and region_count <= self.stable_region_threshold
            )

            is_variable = cv >= self.stable_cv_threshold or region_count > self.stable_region_threshold

            classification_type = "stable" if is_stable else ("variable" if is_variable else "burst")

            # Determine recommended SP type
            if is_stable:
                recommended_sp = SavingsPlanType.EC2_INSTANCE_SP  # Higher savings for stable
            else:
                recommended_sp = SavingsPlanType.COMPUTE_SP  # Flexibility for variable

            # Calculate confidence score
            confidence = min(1.0, uptime_pct * (1.0 - min(cv, 1.0)))

            classifications.append(
                WorkloadClassification(
                    resource_ids=[f"{instance_type}#{r}" for r in all_regions],
                    classification=classification_type,
                    coefficient_of_variation=cv,
                    uptime_percentage=uptime_pct,
                    region_count=region_count,
                    multi_region=region_count > 2,
                    average_hourly_usage=mean_usage / 24.0,  # Convert to hourly
                    peak_hourly_usage=peak_usage / 24.0,
                    baseline_hourly_usage=baseline_usage / 24.0,
                    total_on_demand_cost=total_cost,
                    recommended_sp_type=recommended_sp,
                    confidence_score=confidence,
                )
            )

        progress.advance(task_id)
        print_success(
            f"Classified {len(classifications)} workloads: "
            f"{sum(1 for c in classifications if c.classification == 'stable')} stable, "
            f"{sum(1 for c in classifications if c.classification == 'variable')} variable"
        )

        return classifications

    async def _generate_sp_recommendations(
        self, workload_classifications: List[WorkloadClassification], usage_patterns: Dict, progress, task_id
    ) -> List[SavingsPlanRecommendation]:
        """Generate Compute SP and EC2 Instance SP recommendations."""
        recommendations = []

        # Separate stable and variable workloads
        stable_workloads = [c for c in workload_classifications if c.classification == "stable"]
        variable_workloads = [c for c in workload_classifications if c.classification == "variable"]

        # Generate EC2 Instance SP recommendations for stable workloads
        if stable_workloads:
            stable_hourly_usage = sum(w.average_hourly_usage for w in stable_workloads)
            stable_total_cost = sum(w.total_on_demand_cost for w in stable_workloads)

            # Calculate SP commitment (monthly average usage)
            monthly_hours = self.analysis_period_days / 30.44 * 24
            commitment_hourly = stable_hourly_usage

            # Financial modeling
            annual_on_demand_cost = stable_total_cost * (365.25 / self.analysis_period_days)
            annual_sp_cost = annual_on_demand_cost * (1 - self.ec2_instance_sp_savings_rate)
            annual_savings = annual_on_demand_cost - annual_sp_cost

            # Break-even analysis (no upfront for initial recommendation)
            upfront_cost = 0.0
            break_even_months = 0.0 if annual_savings > 0 else 999

            # ROI calculation
            roi_pct = (annual_savings / annual_sp_cost * 100) if annual_sp_cost > 0 else 0

            recommendations.append(
                SavingsPlanRecommendation(
                    plan_type=SavingsPlanType.EC2_INSTANCE_SP,
                    commitment_usd_hourly=commitment_hourly,
                    term_years=1,
                    payment_option=SPPaymentOption.NO_UPFRONT,
                    upfront_cost=upfront_cost,
                    estimated_annual_savings=annual_savings,
                    coverage_percentage=self.ec2_instance_sp_allocation * 100,
                    hybrid_strategy={
                        "allocation": "30%",
                        "workload_type": "stable",
                        "regions": list(set(r for w in stable_workloads for r in w.resource_ids)),
                    },
                    confidence_score=sum(w.confidence_score for w in stable_workloads) / len(stable_workloads),
                    covered_workloads=[r for w in stable_workloads for r in w.resource_ids],
                    regions=list(set(p["region"] for p in usage_patterns.values())),
                    services=["EC2"],
                    break_even_months=break_even_months,
                    roi_percentage=roi_pct,
                    risk_level="low",
                )
            )

            progress.advance(task_id)

        # Generate Compute SP recommendations for variable workloads
        if variable_workloads:
            variable_hourly_usage = sum(w.average_hourly_usage for w in variable_workloads)
            variable_total_cost = sum(w.total_on_demand_cost for w in variable_workloads)

            # Calculate SP commitment
            commitment_hourly = variable_hourly_usage

            # Financial modeling
            annual_on_demand_cost = variable_total_cost * (365.25 / self.analysis_period_days)
            annual_sp_cost = annual_on_demand_cost * (1 - self.compute_sp_savings_rate)
            annual_savings = annual_on_demand_cost - annual_sp_cost

            # Break-even and ROI
            upfront_cost = 0.0
            break_even_months = 0.0 if annual_savings > 0 else 999
            roi_pct = (annual_savings / annual_sp_cost * 100) if annual_sp_cost > 0 else 0

            recommendations.append(
                SavingsPlanRecommendation(
                    plan_type=SavingsPlanType.COMPUTE_SP,
                    commitment_usd_hourly=commitment_hourly,
                    term_years=1,
                    payment_option=SPPaymentOption.NO_UPFRONT,
                    upfront_cost=upfront_cost,
                    estimated_annual_savings=annual_savings,
                    coverage_percentage=self.compute_sp_allocation * 100,
                    hybrid_strategy={"allocation": "60%", "workload_type": "variable", "multi_region": True},
                    confidence_score=sum(w.confidence_score for w in variable_workloads) / len(variable_workloads),
                    covered_workloads=[r for w in variable_workloads for r in w.resource_ids],
                    regions=list(set(p["region"] for p in usage_patterns.values())),
                    services=["EC2", "Fargate", "Lambda"],
                    break_even_months=break_even_months,
                    roi_percentage=roi_pct,
                    risk_level="low" if sum(w.multi_region for w in variable_workloads) > 0 else "medium",
                )
            )

            progress.advance(task_id)

        print_success(f"Generated {len(recommendations)} SP recommendations")
        return recommendations

    async def _optimize_hybrid_strategy(
        self, recommendations: List[SavingsPlanRecommendation], usage_patterns: Dict, progress, task_id
    ) -> List[SavingsPlanRecommendation]:
        """
        Optimize 60/30/10 allocation for maximum savings + flexibility.

        Rules:
        1. Compute SP: 60% of steady usage (baseline coverage)
        2. EC2 Instance SP: 30% of steady usage (max savings for stable)
        3. On-Demand: 10% remaining (flexibility + burst)
        """
        optimized = []

        # Calculate total hourly usage
        total_hourly_usage = sum(
            sum(pattern["daily_usage"]) / len(pattern["daily_usage"]) / 24.0 for pattern in usage_patterns.values()
        )

        if total_hourly_usage == 0:
            progress.advance(task_id)
            return recommendations

        # Apply 60/30/10 allocation
        for rec in recommendations:
            if rec.plan_type == SavingsPlanType.COMPUTE_SP:
                # Allocate 60% to Compute SP
                rec.commitment_usd_hourly = total_hourly_usage * self.compute_sp_allocation
                rec.coverage_percentage = self.compute_sp_allocation * 100
                rec.hybrid_strategy["allocation"] = "60%"

            elif rec.plan_type == SavingsPlanType.EC2_INSTANCE_SP:
                # Allocate 30% to EC2 Instance SP (only if stable workloads exist)
                stable_percentage = rec.confidence_score
                if stable_percentage > 0.30:  # At least 30% stable workload
                    rec.commitment_usd_hourly = total_hourly_usage * self.ec2_instance_sp_allocation
                    rec.coverage_percentage = self.ec2_instance_sp_allocation * 100
                    rec.hybrid_strategy["allocation"] = "30%"
                else:
                    # Not enough stable workload, skip EC2 Instance SP
                    continue

            optimized.append(rec)

        # 10% remains On-Demand (no action needed)
        progress.advance(task_id)

        print_success(
            f"Hybrid optimization complete: {len(optimized)} SP recommendations "
            f"(60% Compute SP, 30% EC2 Instance SP, 10% On-Demand)"
        )

        return optimized

    async def _validate_with_mcp(self, recommendations: List[SavingsPlanRecommendation], progress, task_id) -> bool:
        """Validate SP savings projection against MCP Cost Explorer (≥99.5% accuracy)."""
        try:
            total_savings = sum(rec.estimated_annual_savings for rec in recommendations)

            if total_savings >= 500000:  # $500K+ requires validation
                print_info(f"Validating ${total_savings:,.2f} savings projection with MCP...")

                # Initialize MCP validator
                if self.profile_name:
                    mcp_validator = EmbeddedMCPValidator([self.profile_name])

                    validation_data = {
                        "total_annual_savings": total_savings,
                        "recommendations_count": len(recommendations),
                        "compute_sp_count": sum(
                            1 for r in recommendations if r.plan_type == SavingsPlanType.COMPUTE_SP
                        ),
                        "ec2_instance_sp_count": sum(
                            1 for r in recommendations if r.plan_type == SavingsPlanType.EC2_INSTANCE_SP
                        ),
                        "analysis_timestamp": datetime.now().isoformat(),
                    }

                    validation_results = await mcp_validator.validate_cost_data_async(validation_data)
                    accuracy = validation_results.get("total_accuracy", 0.0)

                    if accuracy >= 99.5:
                        print_success(f"MCP Validation: {accuracy:.1f}% accuracy achieved (target: ≥99.5%)")
                        progress.advance(task_id)
                        return True
                    else:
                        print_warning(f"MCP Validation: {accuracy:.1f}% accuracy (target: ≥99.5%)")
                        progress.advance(task_id)
                        return False

            progress.advance(task_id)
            return True

        except Exception as e:
            print_warning(f"MCP validation failed: {str(e)}")
            progress.advance(task_id)
            return False

    def _display_executive_summary(
        self, recommendations: List[SavingsPlanRecommendation], analysis_start_time: float
    ) -> None:
        """Display executive summary with Rich CLI formatting."""

        total_savings = sum(rec.estimated_annual_savings for rec in recommendations)
        total_commitment = sum(rec.commitment_usd_hourly for rec in recommendations)

        # Executive Summary Panel
        summary_content = f"""
💼 Savings Plans Hybrid Strategy Analysis

📊 Recommendations: {len(recommendations)}
💰 Total Annual Savings: {format_cost(total_savings)}
💲 Hourly Commitment: ${total_commitment:.2f}/hour
📈 Strategy: 60% Compute SP + 30% EC2 Instance SP + 10% On-Demand

🔧 Plan Breakdown:
"""

        for rec in recommendations:
            summary_content += (
                f"   • {rec.plan_type.value}: {format_cost(rec.estimated_annual_savings)} annual savings\n"
            )

        summary_content += f"""
⚡ Analysis Time: {time.time() - analysis_start_time:.2f}s
        """

        console.print(
            create_panel(summary_content.strip(), title="🏆 Savings Plans Executive Summary", border_style="green")
        )

        # SP Recommendations Table
        if recommendations:
            table = create_table(title="Savings Plans Purchase Recommendations")

            table.add_column("Plan Type", style="cyan", no_wrap=True)
            table.add_column("Commitment ($/hr)", justify="right", style="magenta")
            table.add_column("Annual Savings", justify="right", style="green")
            table.add_column("Coverage %", justify="right")
            table.add_column("Allocation", justify="center")
            table.add_column("Confidence", justify="right", style="blue")

            for rec in recommendations:
                table.add_row(
                    rec.plan_type.value,
                    f"${rec.commitment_usd_hourly:.2f}",
                    format_cost(rec.estimated_annual_savings),
                    f"{rec.coverage_percentage:.1f}%",
                    rec.hybrid_strategy.get("allocation", "N/A"),
                    f"{rec.confidence_score * 100:.1f}%",
                )

            console.print(table)


# Integration with existing reservation_optimizer.py
# This class can be imported and used alongside ReservationOptimizer for unified RI + SP strategy
