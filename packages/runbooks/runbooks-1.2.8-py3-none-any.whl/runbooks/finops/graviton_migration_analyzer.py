#!/usr/bin/env python3
"""
Graviton Migration Analyzer - ARM64 Migration Eligibility Assessment

This module analyzes EC2 instances for ARM64 Graviton migration potential
with 40% cost savings targeting $800K+ annual opportunity.

Business Value:
- $800K+ annual savings opportunity (40% Graviton price reduction)
- 137 EC2 instances baseline analysis
- Integration with E2-E7 decommission signals for confidence scoring

Features:
- Instance type compatibility mapping (x86 → ARM64)
- AMI architecture compatibility checking
- Application workload heuristics
- Cost savings projection (40% reduction model)
- Integration with Compute Optimizer recommendations
- Eligibility scoring (0-100 scale)

Design Philosophy (KISS/DRY/LEAN):
- Mirror ec2_analyzer.py proven patterns
- Reuse base_enrichers.py (Organizations, Cost)
- Follow Rich CLI standards from rich_utils.py
- Production-grade error handling

Usage:
    # Python API
    from runbooks.finops.graviton_migration_analyzer import analyze_graviton_eligibility

    result_df = analyze_graviton_eligibility(
        input_file='ec2-enriched.xlsx',
        output_file='graviton-analysis.xlsx',
        management_profile='mgmt-profile',
        billing_profile='billing-profile'
    )

    # CLI
    runbooks finops analyze-graviton-eligibility \\
        --input ec2-enriched.xlsx \\
        --output graviton-analysis.xlsx \\
        --management-profile mgmt \\
        --billing-profile billing

Strategic Alignment:
- Objective 1: Graviton cost optimization for runbooks package
- Enterprise SDLC: Evidence-based migration planning
- KISS/DRY/LEAN: Enhance existing EC2 analyzer patterns
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import boto3
import pandas as pd
from botocore.exceptions import ClientError

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

# Configure module-level logging
logging.getLogger("runbooks").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
import warnings

warnings.filterwarnings("ignore")


# Graviton instance type mappings (x86_64 → ARM64)
GRAVITON_MAPPINGS = {
    # T3 → T4g family (Burstable Performance)
    "t3.nano": "t4g.nano",
    "t3.micro": "t4g.micro",
    "t3.small": "t4g.small",
    "t3.medium": "t4g.medium",
    "t3.large": "t4g.large",
    "t3.xlarge": "t4g.xlarge",
    "t3.2xlarge": "t4g.2xlarge",
    # M5 → M6g family (General Purpose)
    "m5.large": "m6g.large",
    "m5.xlarge": "m6g.xlarge",
    "m5.2xlarge": "m6g.2xlarge",
    "m5.4xlarge": "m6g.4xlarge",
    "m5.8xlarge": "m6g.8xlarge",
    "m5.12xlarge": "m6g.12xlarge",
    "m5.16xlarge": "m6g.16xlarge",
    "m5.24xlarge": "m6g.24xlarge",
    # M5n → M6gd family (Network Optimized)
    "m5n.large": "m6gd.large",
    "m5n.xlarge": "m6gd.xlarge",
    "m5n.2xlarge": "m6gd.2xlarge",
    "m5n.4xlarge": "m6gd.4xlarge",
    # C5 → C6g family (Compute Optimized)
    "c5.large": "c6g.large",
    "c5.xlarge": "c6g.xlarge",
    "c5.2xlarge": "c6g.2xlarge",
    "c5.4xlarge": "c6g.4xlarge",
    "c5.9xlarge": "c6g.9xlarge",
    "c5.12xlarge": "c6g.12xlarge",
    "c5.18xlarge": "c6g.18xlarge",
    "c5.24xlarge": "c6g.24xlarge",
    # R5 → R6g family (Memory Optimized)
    "r5.large": "r6g.large",
    "r5.xlarge": "r6g.xlarge",
    "r5.2xlarge": "r6g.2xlarge",
    "r5.4xlarge": "r6g.4xlarge",
    "r5.8xlarge": "r6g.8xlarge",
    "r5.12xlarge": "r6g.12xlarge",
    "r5.16xlarge": "r6g.16xlarge",
    "r5.24xlarge": "r6g.24xlarge",
    # M5a → M6g family (AMD → ARM64)
    "m5a.large": "m6g.large",
    "m5a.xlarge": "m6g.xlarge",
    "m5a.2xlarge": "m6g.2xlarge",
    "m5a.4xlarge": "m6g.4xlarge",
    # C5a → C6g family (AMD → ARM64)
    "c5a.large": "c6g.large",
    "c5a.xlarge": "c6g.xlarge",
    "c5a.2xlarge": "c6g.2xlarge",
    "c5a.4xlarge": "c6g.4xlarge",
    # R5a → R6g family (AMD → ARM64)
    "r5a.large": "r6g.large",
    "r5a.xlarge": "r6g.xlarge",
    "r5a.2xlarge": "r6g.2xlarge",
    "r5a.4xlarge": "r6g.4xlarge",
}

# Graviton cost savings model (40% average reduction)
GRAVITON_COST_SAVINGS_PERCENT = 0.40


@dataclass
class GravitonEligibility:
    """
    Graviton migration eligibility assessment result.

    Attributes:
        instance_id: EC2 instance identifier
        current_type: Current x86_64 instance type
        graviton_type: Recommended Graviton (ARM64) instance type
        eligibility_score: Migration eligibility (0-100 scale)
        ami_compatible: AMI supports ARM64 architecture
        application_compatible: Application workload assessment
        monthly_savings: Projected monthly cost savings (USD)
        annual_savings: Projected annual cost savings (USD)
        migration_complexity: LOW/MEDIUM/HIGH complexity rating
        recommendation: Migration recommendation summary
        confidence_factors: Dictionary of confidence scoring factors
        blockers: List of migration blockers (if any)
    """

    instance_id: str
    current_type: str
    graviton_type: Optional[str] = None
    eligibility_score: float = 0.0
    ami_compatible: bool = False
    application_compatible: bool = True  # Default optimistic
    monthly_savings: float = 0.0
    annual_savings: float = 0.0
    migration_complexity: str = "UNKNOWN"
    recommendation: str = "Not assessed"
    confidence_factors: Dict[str, int] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame integration."""
        return {
            "instance_id": self.instance_id,
            "current_type": self.current_type,
            "graviton_type": self.graviton_type,
            "eligibility_score": self.eligibility_score,
            "ami_compatible": self.ami_compatible,
            "application_compatible": self.application_compatible,
            "monthly_savings": self.monthly_savings,
            "annual_savings": self.annual_savings,
            "migration_complexity": self.migration_complexity,
            "recommendation": self.recommendation,
            "blockers": ", ".join(self.blockers) if self.blockers else "None",
        }


@dataclass
class GravitonAnalysisConfig:
    """
    Configuration for Graviton migration analysis with unified profile routing (v1.1.11+).

    Profile Resolution (5-tier priority):
    1. Explicit profile parameters (highest priority - backward compatible)
    2. Service-specific environment variables (AWS_MANAGEMENT_PROFILE, AWS_BILLING_PROFILE)
    3. Generic AWS_PROFILE environment variable
    4. Service-specific defaults
    5. None (AWS default credentials)

    Args:
        management_profile: AWS profile for Organizations/EC2 operations
        billing_profile: AWS profile for Cost Explorer
        enable_ami_check: Enable AMI architecture verification (default: True)
        enable_compute_optimizer: Enable Compute Optimizer integration (default: True)
        savings_threshold: Minimum monthly savings for recommendation (default: $10)
    """

    management_profile: Optional[str] = None
    billing_profile: Optional[str] = None
    enable_ami_check: bool = True
    enable_compute_optimizer: bool = True
    savings_threshold: float = 10.0  # Minimum $10/month savings

    def __post_init__(self):
        """Resolve profiles using unified service routing if not explicitly provided."""
        from runbooks.common.aws_profile_manager import get_profile_for_service

        # Resolve management_profile (for EC2 operations)
        if not self.management_profile:
            self.management_profile = get_profile_for_service("ec2")

        # Resolve billing_profile (for Cost Explorer)
        if not self.billing_profile:
            self.billing_profile = get_profile_for_service("cost-explorer")


class GravitonMigrationAnalyzer:
    """
    Graviton migration eligibility analyzer with ARM64 compatibility assessment.

    Pattern: Mirror EC2CostAnalyzer structure for consistency
    """

    def __init__(self, config: GravitonAnalysisConfig):
        """Initialize Graviton analyzer with enterprise configuration."""
        from runbooks.common.profile_utils import create_operational_session

        self.config = config

        # Initialize AWS session using standardized profile helper
        self.session = create_operational_session(config.management_profile)

        logger.debug(
            f"Graviton analyzer initialized with profiles: "
            f"mgmt={config.management_profile}, billing={config.billing_profile}"
        )

    def assess_eligibility(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assess Graviton migration eligibility for EC2 instances.

        Args:
            df: DataFrame with EC2 instances (requires: instance_id, instance_type, monthly_cost)

        Returns:
            DataFrame enriched with Graviton eligibility assessment (12 new columns)
        """
        start_time = time.time()

        print_header("Graviton Migration Analysis", f"Analyzing {len(df)} EC2 instances")

        # Validate required columns
        required_columns = ["instance_id", "instance_type"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Required columns missing: {missing_columns}")

        # Step 1: Instance type compatibility mapping
        df = self._map_instance_types(df)

        # Step 2: AMI architecture compatibility check
        if self.config.enable_ami_check:
            df = self._check_ami_compatibility(df)

        # Step 3: Application compatibility assessment
        df = self._assess_application_compatibility(df)

        # Step 4: Cost savings projection
        df = self._calculate_savings(df)

        # Step 5: Compute Optimizer integration (optional)
        if self.config.enable_compute_optimizer:
            df = self._integrate_compute_optimizer(df)

        # Step 6: Calculate eligibility scores
        df = self._calculate_eligibility_scores(df)

        # Step 7: Generate recommendations
        df = self._generate_recommendations(df)

        elapsed_time = time.time() - start_time
        print_success(f"\n✅ Graviton analysis complete in {elapsed_time:.1f}s")

        return df

    def _map_instance_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map x86_64 instance types to Graviton equivalents."""
        print_section("Instance Type Mapping (x86_64 → ARM64)", emoji="🔄")

        df["graviton_type"] = df["instance_type"].map(GRAVITON_MAPPINGS)
        df["has_graviton_mapping"] = df["graviton_type"].notna()

        mapped_count = df["has_graviton_mapping"].sum()
        unmapped_count = len(df) - mapped_count

        mapping_table = create_table(
            title="Graviton Compatibility Mapping",
            columns=[
                {"header": "Status", "style": "cyan"},
                {"header": "Count", "style": "green"},
                {"header": "Percentage", "style": "yellow"},
            ],
        )
        mapping_table.add_row("Graviton Compatible", str(mapped_count), f"{(mapped_count / len(df) * 100):.1f}%")
        mapping_table.add_row("No Graviton Equivalent", str(unmapped_count), f"{(unmapped_count / len(df) * 100):.1f}%")
        console.print(mapping_table)

        return df

    def _check_ami_compatibility(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Check AMI architecture compatibility for ARM64 migration.

        Queries EC2 DescribeImages API to validate AMI supports ARM64.
        """
        print_section("AMI Architecture Compatibility Check", emoji="🔍")

        from runbooks.common.profile_utils import create_timeout_protected_client

        df["ami_id"] = "N/A"
        df["ami_architecture"] = "N/A"
        df["ami_arm64_compatible"] = False

        # Get unique instance IDs that have Graviton mappings
        eligible_instances = df[df["has_graviton_mapping"] == True]

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Checking AMI architecture compatibility...", total=len(eligible_instances))

            for idx, row in eligible_instances.iterrows():
                instance_id = row["instance_id"]
                region = row.get("region", "ap-southeast-2")

                try:
                    # Get EC2 client for region
                    ec2_client = create_timeout_protected_client(self.session, "ec2", region)

                    # Get instance details
                    response = ec2_client.describe_instances(InstanceIds=[instance_id])

                    reservations = response.get("Reservations", [])
                    if reservations and reservations[0].get("Instances"):
                        instance = reservations[0]["Instances"][0]
                        ami_id = instance.get("ImageId", "N/A")

                        # Get AMI details
                        ami_response = ec2_client.describe_images(ImageIds=[ami_id])
                        images = ami_response.get("Images", [])

                        if images:
                            ami_arch = images[0].get("Architecture", "N/A")
                            df.at[idx, "ami_id"] = ami_id
                            df.at[idx, "ami_architecture"] = ami_arch

                            # Check ARM64 compatibility
                            # Note: ARM64 AMIs use 'arm64' architecture
                            # x86_64 AMIs may have ARM64 equivalents (needs lookup)
                            if ami_arch == "arm64":
                                df.at[idx, "ami_arm64_compatible"] = True
                            elif ami_arch == "x86_64":
                                # Check if ARM64 equivalent exists (by name pattern)
                                ami_name = images[0].get("Name", "")
                                if ami_name:
                                    # Try to find ARM64 variant
                                    try:
                                        arm_search = ec2_client.describe_images(
                                            Filters=[
                                                {"Name": "name", "Values": [ami_name.replace("x86_64", "arm64")]},
                                                {"Name": "architecture", "Values": ["arm64"]},
                                            ],
                                            Owners=["self", "amazon"],
                                        )
                                        if arm_search.get("Images"):
                                            df.at[idx, "ami_arm64_compatible"] = True
                                    except ClientError:
                                        pass

                except ClientError as e:
                    logger.warning(f"Failed to check AMI for {instance_id}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error checking AMI for {instance_id}: {e}")

                progress.update(task, advance=1)

        compatible_count = df["ami_arm64_compatible"].sum()
        print_success(f"✅ AMI compatibility check complete: {compatible_count}/{len(eligible_instances)} ARM64-ready")

        return df

    def _assess_application_compatibility(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assess application workload compatibility with ARM64.

        Uses heuristics based on:
        - Instance tags (e.g., workload type, application name)
        - Instance type family (general-purpose more compatible)
        - Platform (Linux more compatible than Windows)
        """
        print_section("Application Workload Compatibility Assessment", emoji="🎯")

        df["app_workload_type"] = "Unknown"
        df["app_compatibility_score"] = 50  # Neutral default
        df["app_compatibility_notes"] = ""

        for idx, row in df.iterrows():
            instance_type = row.get("instance_type", "")
            platform = row.get("platform", "Linux")
            tags = row.get("tags", "")

            compatibility_score = 50  # Start neutral
            notes = []

            # Platform assessment
            if platform.lower() in ["linux", "ubuntu", "amazon linux", "rhel"]:
                compatibility_score += 20
                notes.append("Linux platform (ARM64-friendly)")
            elif platform.lower() in ["windows"]:
                compatibility_score -= 30
                notes.append("Windows platform (ARM64 limited support)")

            # Instance family assessment
            family = instance_type.split(".")[0] if "." in instance_type else instance_type

            if family in ["t3", "t2", "m5", "m4", "c5", "r5"]:
                compatibility_score += 15
                notes.append("General-purpose workload (high compatibility)")
            elif family in ["p3", "g4", "inf1"]:
                compatibility_score -= 40
                notes.append("GPU/ML workload (ARM64 incompatible)")

            # Tag-based heuristics (if available)
            if isinstance(tags, str) and tags:
                tags_lower = tags.lower()

                if any(x in tags_lower for x in ["web", "api", "frontend", "nginx", "apache"]):
                    compatibility_score += 10
                    notes.append("Web/API workload (ARM64-proven)")

                if any(x in tags_lower for x in ["ml", "gpu", "cuda", "training"]):
                    compatibility_score -= 30
                    notes.append("ML/GPU workload (ARM64 challenges)")

            # Cap score at 0-100
            compatibility_score = max(0, min(100, compatibility_score))

            df.at[idx, "app_compatibility_score"] = compatibility_score
            df.at[idx, "app_compatibility_notes"] = " | ".join(notes) if notes else "No assessment"

            # Workload type classification
            if compatibility_score >= 70:
                df.at[idx, "app_workload_type"] = "ARM64-Friendly"
            elif compatibility_score >= 40:
                df.at[idx, "app_workload_type"] = "Requires Testing"
            else:
                df.at[idx, "app_workload_type"] = "High Risk"

        friendly_count = (df["app_workload_type"] == "ARM64-Friendly").sum()
        print_success(f"✅ Application assessment complete: {friendly_count}/{len(df)} ARM64-friendly workloads")

        return df

    def _calculate_savings(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate cost savings from Graviton migration (40% reduction model).

        Formula: savings = current_cost × 0.40 (Graviton typically 40% cheaper)
        """
        print_section("Cost Savings Projection (40% Model)", emoji="💰")

        # Ensure cost columns exist
        if "monthly_cost" not in df.columns:
            df["monthly_cost"] = 0.0

        # Calculate savings for instances with Graviton mappings
        df["graviton_monthly_savings"] = 0.0
        df["graviton_annual_savings"] = 0.0
        df["graviton_monthly_cost"] = 0.0

        eligible_mask = df["has_graviton_mapping"] == True

        # Calculate savings
        df.loc[eligible_mask, "graviton_monthly_savings"] = (
            df.loc[eligible_mask, "monthly_cost"] * GRAVITON_COST_SAVINGS_PERCENT
        )
        df.loc[eligible_mask, "graviton_annual_savings"] = df.loc[eligible_mask, "graviton_monthly_savings"] * 12
        df.loc[eligible_mask, "graviton_monthly_cost"] = df.loc[eligible_mask, "monthly_cost"] * (
            1 - GRAVITON_COST_SAVINGS_PERCENT
        )

        # Summary
        total_monthly_savings = df["graviton_monthly_savings"].sum()
        total_annual_savings = df["graviton_annual_savings"].sum()

        savings_table = create_table(
            title="Graviton Cost Savings Projection",
            columns=[{"header": "Metric", "style": "cyan"}, {"header": "Value", "style": "green"}],
        )
        savings_table.add_row("Eligible Instances", str(eligible_mask.sum()))
        savings_table.add_row("Monthly Savings Potential", format_cost(total_monthly_savings))
        savings_table.add_row("Annual Savings Potential", format_cost(total_annual_savings))
        savings_table.add_row("Savings Model", "40% Graviton reduction")
        console.print(savings_table)

        if total_annual_savings >= 800000:
            print_success(f"✅ $800K+ annual savings target ACHIEVED: ${total_annual_savings:,.2f}")
        else:
            print_info(f"ℹ️  Current savings projection: ${total_annual_savings:,.2f} annual")

        return df

    def _integrate_compute_optimizer(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Integrate AWS Compute Optimizer recommendations for confidence scoring.

        Compute Optimizer idle instances get boosted eligibility (already decommission candidates).
        """
        print_section("Compute Optimizer Integration", emoji="🎯")

        try:
            from runbooks.finops.compute_optimizer import get_ec2_idle_recommendations

            idle_instances = get_ec2_idle_recommendations(
                profile=self.config.management_profile, region="ap-southeast-2"
            )

            df["co_idle_recommendation"] = False

            for idx, row in df.iterrows():
                instance_id = row["instance_id"]
                if instance_id in idle_instances:
                    df.at[idx, "co_idle_recommendation"] = True

            idle_count = df["co_idle_recommendation"].sum()
            print_success(f"✅ Compute Optimizer integration complete: {idle_count} idle instances identified")

        except Exception as e:
            print_warning(f"⚠️  Compute Optimizer integration failed: {e}")
            df["co_idle_recommendation"] = False

        return df

    def _calculate_eligibility_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Graviton migration eligibility scores (0-100 scale).

        Scoring Model:
        - Has Graviton mapping: 30 points (baseline eligibility)
        - AMI ARM64 compatible: 25 points
        - Application compatible (>70): 25 points
        - Savings threshold met: 10 points
        - Compute Optimizer idle: 10 points bonus

        Total: 100 points maximum
        """
        print_section("Eligibility Scoring (0-100)", emoji="📊")

        df["graviton_eligibility_score"] = 0.0

        for idx, row in df.iterrows():
            score = 0.0

            # 1. Has Graviton mapping (30 points)
            if row.get("has_graviton_mapping", False):
                score += 30

            # 2. AMI ARM64 compatible (25 points)
            if row.get("ami_arm64_compatible", False):
                score += 25

            # 3. Application compatibility (25 points max)
            app_score = row.get("app_compatibility_score", 0)
            score += (app_score / 100) * 25

            # 4. Savings threshold met (10 points)
            monthly_savings = row.get("graviton_monthly_savings", 0)
            if monthly_savings >= self.config.savings_threshold:
                score += 10

            # 5. Compute Optimizer idle bonus (10 points)
            if row.get("co_idle_recommendation", False):
                score += 10

            df.at[idx, "graviton_eligibility_score"] = round(score, 1)

        # Distribution summary
        high_score = (df["graviton_eligibility_score"] >= 70).sum()
        medium_score = ((df["graviton_eligibility_score"] >= 40) & (df["graviton_eligibility_score"] < 70)).sum()
        low_score = (df["graviton_eligibility_score"] < 40).sum()

        score_table = create_table(
            title="Eligibility Score Distribution",
            columns=[
                {"header": "Tier", "style": "cyan"},
                {"header": "Score Range", "style": "yellow"},
                {"header": "Count", "style": "green"},
            ],
        )
        score_table.add_row("High Eligibility", "70-100", str(high_score))
        score_table.add_row("Medium Eligibility", "40-69", str(medium_score))
        score_table.add_row("Low Eligibility", "0-39", str(low_score))
        console.print(score_table)

        return df

    def _generate_recommendations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate migration recommendations based on eligibility assessment.

        Recommendations:
        - RECOMMEND (score ≥70): Strong migration candidate
        - EVALUATE (score 40-69): Requires testing/validation
        - NOT_RECOMMENDED (score <40): Migration challenges
        """
        print_section("Migration Recommendations", emoji="✅")

        df["graviton_recommendation"] = "NOT_ASSESSED"
        df["migration_complexity"] = "UNKNOWN"
        df["migration_notes"] = ""

        for idx, row in df.iterrows():
            score = row.get("graviton_eligibility_score", 0)
            monthly_savings = row.get("graviton_monthly_savings", 0)

            notes = []

            if score >= 70:
                df.at[idx, "graviton_recommendation"] = "RECOMMEND"
                df.at[idx, "migration_complexity"] = "LOW"
                notes.append(f"High eligibility (score: {score:.0f})")
                notes.append(f"Projected savings: ${monthly_savings:.2f}/month")

            elif score >= 40:
                df.at[idx, "graviton_recommendation"] = "EVALUATE"
                df.at[idx, "migration_complexity"] = "MEDIUM"
                notes.append(f"Medium eligibility (score: {score:.0f})")
                notes.append("Requires testing before migration")

            else:
                df.at[idx, "graviton_recommendation"] = "NOT_RECOMMENDED"
                df.at[idx, "migration_complexity"] = "HIGH"
                notes.append(f"Low eligibility (score: {score:.0f})")

                # Add specific blockers
                if not row.get("has_graviton_mapping", False):
                    notes.append("No Graviton equivalent instance type")
                if not row.get("ami_arm64_compatible", False):
                    notes.append("AMI not ARM64 compatible")
                if row.get("app_compatibility_score", 0) < 40:
                    notes.append("Application compatibility concerns")

            df.at[idx, "migration_notes"] = " | ".join(notes)

        # Recommendation summary
        recommend_count = (df["graviton_recommendation"] == "RECOMMEND").sum()
        evaluate_count = (df["graviton_recommendation"] == "EVALUATE").sum()
        not_recommended_count = (df["graviton_recommendation"] == "NOT_RECOMMENDED").sum()

        rec_table = create_table(
            title="Migration Recommendation Summary",
            columns=[
                {"header": "Recommendation", "style": "cyan"},
                {"header": "Count", "style": "green"},
                {"header": "Annual Savings", "style": "yellow"},
            ],
        )

        recommend_savings = df[df["graviton_recommendation"] == "RECOMMEND"]["graviton_annual_savings"].sum()
        evaluate_savings = df[df["graviton_recommendation"] == "EVALUATE"]["graviton_annual_savings"].sum()

        rec_table.add_row("RECOMMEND (Migrate)", str(recommend_count), format_cost(recommend_savings))
        rec_table.add_row("EVALUATE (Test)", str(evaluate_count), format_cost(evaluate_savings))
        rec_table.add_row("NOT_RECOMMENDED", str(not_recommended_count), "$0")
        console.print(rec_table)

        if recommend_count > 0:
            print_success(
                f"✅ {recommend_count} instances ready for Graviton migration (${recommend_savings:,.2f} annual)"
            )

        return df


def analyze_graviton_eligibility(
    input_file: str,
    output_file: str,
    management_profile: Optional[str] = None,
    billing_profile: Optional[str] = None,
    enable_ami_check: bool = True,
    enable_compute_optimizer: bool = True,
) -> pd.DataFrame:
    """
    CLI and notebook entry point for Graviton migration analysis.

    Usage (v1.1.11+ with automatic profile routing):
        # Python API - profiles auto-resolved
        from runbooks.finops.graviton_migration_analyzer import analyze_graviton_eligibility

        df = analyze_graviton_eligibility(
            input_file='ec2-enriched.xlsx',
            output_file='graviton-analysis.xlsx'
        )

    Usage (backward compatible with explicit profiles):
        # Python API - explicit profiles
        df = analyze_graviton_eligibility(
            input_file='ec2-enriched.xlsx',
            output_file='graviton-analysis.xlsx',
            management_profile='mgmt',
            billing_profile='billing'
        )

        # CLI - profiles from environment or defaults
        runbooks finops analyze-graviton-eligibility \\
            --input ec2-enriched.xlsx \\
            --output graviton-analysis.xlsx

    Args:
        input_file: Excel file with EC2 enriched data
        output_file: Output Excel file path
        management_profile: AWS profile for EC2 operations (defaults to service routing)
        billing_profile: AWS profile for Cost Explorer (defaults to service routing)
        enable_ami_check: Enable AMI architecture verification
        enable_compute_optimizer: Enable Compute Optimizer integration

    Returns:
        DataFrame with Graviton eligibility assessment (12 new columns)
    """
    try:
        # Create configuration
        config = GravitonAnalysisConfig(
            management_profile=management_profile,
            billing_profile=billing_profile,
            enable_ami_check=enable_ami_check,
            enable_compute_optimizer=enable_compute_optimizer,
        )

        # Load EC2 enriched data
        print_info(f"Loading EC2 data from {input_file}...")
        df = pd.read_excel(input_file, sheet_name="ec2")

        # Initialize analyzer
        analyzer = GravitonMigrationAnalyzer(config)

        # Execute analysis
        df = analyzer.assess_eligibility(df)

        # Export results
        print_info(f"Exporting results to {output_file}...")
        df.to_excel(output_file, sheet_name="graviton_analysis", index=False)

        print_success(f"\n✅ Graviton analysis exported to {output_file}")

        return df

    except Exception as e:
        print_error(f"❌ Graviton analysis failed: {e}")
        logger.error(f"Graviton analysis error: {e}", exc_info=True)
        raise
