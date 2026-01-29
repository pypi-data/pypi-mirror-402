#!/usr/bin/env python3
"""
EC2 Cost Analyzer - Comprehensive EC2 Cost Optimization Analysis

This module provides enterprise EC2 cost analysis with:
- Organizations metadata enrichment (6 columns)
- Cost Explorer 12-month historical costs
- CloudTrail activity tracking
- 28-column EC2 context enrichment
- Rich CLI cost visualization
- Multi-sheet Excel export

Design Philosophy (KISS/DRY/LEAN):
- Mirror workspaces_analyzer.py proven patterns
- Reuse base_enrichers.py (Organizations, Cost, CloudTrail)
- Follow Rich CLI standards from rich_utils.py
- Production-grade error handling

Usage:
    # Python API
    from runbooks.finops.ec2_analyzer import analyze_ec2_costs

    result_df = analyze_ec2_costs(
        input_file='ec2-inventory.xlsx',
        output_file='ec2-enriched.xlsx',
        management_profile='mgmt-profile',
        billing_profile='billing-profile'
    )

    # CLI
    runbooks finops analyze-ec2 \\
        --input ec2-inventory.xlsx \\
        --output ec2-enriched.xlsx \\
        --management-profile mgmt \\
        --billing-profile billing

Strategic Alignment:
- Objective 1: EC2 cost optimization for runbooks package
- Enterprise SDLC: Proven patterns from FinOps module
- KISS/DRY/LEAN: Enhance existing, reuse patterns
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from .base_enrichers import (
    CloudTrailEnricher,
    CostExplorerEnricher,
    CostOptimizerEnricher,
    OrganizationsEnricher,
    StoppedStateEnricher,
    StorageIOEnricher,
)
from .service_attachment_enricher import get_service_attachments
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
class EC2AnalysisConfig:
    """
    Configuration for EC2 cost analysis with unified profile routing (v1.1.11+).

    Profile Resolution (5-tier priority):
    1. Explicit profile parameters (highest priority - backward compatible)
    2. Service-specific environment variables (AWS_MANAGEMENT_PROFILE, AWS_BILLING_PROFILE, AWS_CENTRALISED_OPS_PROFILE)
    3. Generic AWS_PROFILE environment variable
    4. Service-specific defaults
    5. None (AWS default credentials)

    Args:
        management_profile: AWS profile for Organizations (defaults to service routing)
        billing_profile: AWS profile for Cost Explorer (defaults to service routing)
        operational_profile: AWS profile for EC2 operations (defaults to management_profile)
    """

    management_profile: Optional[str] = None
    billing_profile: Optional[str] = None
    operational_profile: Optional[str] = None
    enable_organizations: bool = True
    enable_cost: bool = True
    enable_activity: bool = False
    enable_volume_encryption: bool = False  # Optional - PCI-DSS/HIPAA compliance check
    include_12month_cost: bool = True

    def __post_init__(self):
        """Resolve profiles using unified service routing if not explicitly provided."""
        from runbooks.common.aws_profile_manager import get_profile_for_service

        # Resolve management_profile (for Organizations)
        if not self.management_profile:
            self.management_profile = get_profile_for_service("organizations")

        # Resolve billing_profile (for Cost Explorer)
        if not self.billing_profile:
            self.billing_profile = get_profile_for_service("cost-explorer")

        # Resolve operational_profile (defaults to management_profile)
        if not self.operational_profile:
            self.operational_profile = self.management_profile


class EC2CostAnalyzer:
    """
    EC2 cost analyzer with Organizations/Cost Explorer/CloudTrail enrichment.

    Pattern: Mirror workspaces_analyzer.py structure for consistency
    """

    def __init__(self, config: EC2AnalysisConfig):
        """Initialize EC2 analyzer with enterprise configuration."""
        from runbooks.common.profile_utils import create_operational_session

        self.config = config

        # Initialize enrichers
        self.orgs_enricher = OrganizationsEnricher()
        self.cost_enricher = CostExplorerEnricher()
        self.ct_enricher = CloudTrailEnricher()

        # Initialize AWS session using standardized profile helper
        profile = config.operational_profile or config.management_profile
        self.session = create_operational_session(profile)

        logger.debug(
            f"EC2 analyzer initialized with profiles: "
            f"mgmt={config.management_profile}, billing={config.billing_profile}"
        )

    @classmethod
    def from_excel(
        cls,
        excel_file: str,
        sheet_name: str = "ec2",
        management_profile: Optional[str] = None,
        billing_profile: Optional[str] = None,
        operational_profile: Optional[str] = None,
        aws_config_path: Optional[str] = None,
    ) -> "EC2CostAnalyzer":
        """
        Load EC2 data from Excel file with unified profile routing (v1.1.11+).

        Pattern: Adapted from VPC vpce_cleanup_manager.py from_csv() (lines 271-354)

        Args:
            excel_file: Path to Excel file with EC2 inventory
            sheet_name: Sheet name to read (default: 'ec2')
            management_profile: AWS profile for Organizations (defaults to service routing)
            billing_profile: AWS profile for Cost Explorer (defaults to service routing)
            operational_profile: AWS profile for EC2 operations (defaults to management_profile)
            aws_config_path: Optional path to ~/.aws/config for profile enrichment

        Returns:
            Initialized EC2CostAnalyzer with loaded and enriched data

        Raises:
            FileNotFoundError: If excel_file doesn't exist
            ValueError: If required columns missing

        Example (v1.1.11+ with automatic profile routing):
            >>> # Profiles resolved automatically from environment or defaults
            >>> analyzer = EC2CostAnalyzer.from_excel("ec2-inventory.xlsx")

        Example (backward compatible with explicit profiles):
            >>> analyzer = EC2CostAnalyzer.from_excel(
            ...     "ec2-inventory.xlsx",
            ...     management_profile="mgmt",
            ...     billing_profile="billing"
            ... )
        """
        from pathlib import Path

        excel_path = Path(excel_file)

        # Validate file exists (fail-fast)
        if not excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_file}")

        # Load Excel and normalize column names
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # Normalize column names: Handle Title Case, lowercase, mixed formats
        # "Identifier" → "identifier", "AWS Account" → "aws_account", etc.
        df.columns = (
            df.columns.str.strip()  # Remove leading/trailing spaces
            .str.lower()  # Convert to lowercase
            .str.replace(" ", "_")  # Spaces to underscores
            .str.replace("-", "_")  # Hyphens to underscores
        )

        # Field mapping: Excel column names → Internal DataFrame column names
        column_mapping = {
            "identifier": "instance_id",
            "aws_account": "account_id",
            "region": "region",
            "resource_type": "resource_type",
            "tags": "tags",
        }

        # Apply mapping for columns that exist
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # Validate required columns exist (after normalization and mapping)
        required_columns = ["instance_id", "account_id", "region"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(
                f"Excel missing required columns: {', '.join(missing_columns)}\n"
                f"Found columns: {', '.join(df.columns)}\n"
                f"Required: {', '.join(required_columns)}"
            )

        # Optional profile enrichment from ~/.aws/config
        if aws_config_path and ("aws_profile" not in df.columns or df["aws_profile"].isna().any()):
            try:
                from runbooks.vpc.aws_config_parser import parse_aws_config

                # Parse AWS config and create account_id → profile mapping
                profile_map = parse_aws_config(aws_config_path)

                # Enrich DataFrame with profiles
                df["aws_profile"] = df["account_id"].astype(str).map(profile_map)

                enriched_count = df["aws_profile"].notna().sum()
                print_info(f"Auto-enriched {enriched_count} instances with AWS profiles from {aws_config_path}")

            except ImportError:
                print_warning("aws_config_parser unavailable - skipping profile enrichment")
            except Exception as e:
                print_warning(f"Profile enrichment failed: {e}")

        # Create configuration
        config = EC2AnalysisConfig(
            management_profile=management_profile,
            billing_profile=billing_profile,
            operational_profile=operational_profile,
            enable_organizations=True,
            enable_cost=True,
            enable_activity=False,
            enable_volume_encryption=False,
            include_12month_cost=True,
        )

        # Initialize analyzer with loaded data
        instance = cls(config)

        # Store DataFrame for immediate use (pattern: VPC analyzer stores data)
        instance._loaded_df = df

        return instance

    def analyze(
        self, input_file: str, input_sheet: str = "ec2", enable_decommission_scoring: bool = True
    ) -> pd.DataFrame:
        """
        Analyze EC2 costs with comprehensive enrichment.

        Args:
            input_file: Excel file with EC2 inventory
            input_sheet: Sheet name (default: 'ec2')
            enable_decommission_scoring: Enable Phase 1 decommission scoring (default: True)

        Returns:
            DataFrame with enriched EC2 data (28+ columns + Phase 1 signals)
        """
        start_time = time.time()

        print_header("EC2 Cost Analysis", f"Input: {input_file}")

        # Step 1: Load data
        df = self._load_data(input_file, input_sheet)

        # Step 2: Organizations enrichment
        if self.config.enable_organizations:
            df = self._enrich_organizations(df)

        # Step 3: EC2 context enrichment (28 columns)
        df = self._enrich_ec2_context(df)

        # Step 3.5: Volume encryption (optional - PCI-DSS/HIPAA)
        if self.config.enable_volume_encryption:
            df = self._enrich_volume_encryption(df)

        # Step 4: Cost enrichment
        if self.config.enable_cost:
            df = self._enrich_costs(df)

        # Step 5: CloudTrail activity (optional)
        if self.config.enable_activity:
            df = self._enrich_activity(df)

        # Step 5.5: E5 Service attachments enrichment (Track C - optional, expensive)
        df = self._enrich_service_attachments(df)

        # Step 6: E4 Stopped duration enrichment (Track B - Phase 2)
        df = self._enrich_stopped_duration(df)

        # Step 7: E6 Storage I/O enrichment (Track B - Phase 2)
        df = self._enrich_storage_io(df)

        # Step 8: E7 Cost rightsizing enrichment (Track B - Phase 2)
        df = self._enrich_cost_rightsizing(df)

        # Step 9: Phase 1 Decommission Scoring (Compute Optimizer + SSM + Scoring)
        if enable_decommission_scoring:
            df = self._enrich_decommission_signals(df)

        elapsed_time = time.time() - start_time
        print_success(f"\n✅ EC2 analysis complete in {elapsed_time:.1f}s")

        return df

    def _load_data(self, input_file: str, sheet_name: str) -> pd.DataFrame:
        """Load and validate EC2 inventory data."""
        print_section(f"EC2 Cost Analysis: {input_file}")

        try:
            # Auto-detect file format (CSV vs Excel) for pandas 3.13 compatibility
            from pathlib import Path

            file_ext = Path(input_file).suffix.lower()

            if file_ext == ".csv":
                df = pd.read_csv(input_file)
            elif file_ext in [".xlsx", ".xls"]:
                df = pd.read_excel(input_file, sheet_name=sheet_name)
            else:
                # Fallback: try Excel first, then CSV
                try:
                    df = pd.read_excel(input_file, sheet_name=sheet_name)
                except Exception:
                    df = pd.read_csv(input_file)

            # Column mapping (handle generic column names)
            column_mapping = {"Identifier": "instance_id", "AWS Account": "account_id", "Region": "region"}

            df = df.rename(columns=column_mapping)

            # Validate required columns
            required_columns = ["instance_id", "account_id", "region"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Required columns missing: {missing_columns}")

            # Display load summary in Rich Table
            load_table = create_table(
                title="Data Load Summary",
                columns=[{"header": "Metric", "style": "cyan"}, {"header": "Value", "style": "green"}],
            )
            load_table.add_row("EC2 Instances Loaded", str(len(df)))
            load_table.add_row("Sheet Name", sheet_name)
            load_table.add_row("Source File", input_file)
            console.print(load_table)

            return df

        except Exception as e:
            print_error(f"❌ Failed to load data: {e}")
            raise

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

    def discover_instances_via_resource_explorer(
        self, aggregator_profile: str = "${CENTRALISED_OPS_PROFILE}", aggregator_region: str = "ap-southeast-2"
    ) -> pd.DataFrame:
        """
        Discover ALL EC2 instances via Resource Explorer AGGREGATOR.

        Args:
            aggregator_profile: AWS profile for centralised-ops account with Resource Explorer
            aggregator_region: Region where Resource Explorer aggregator index exists

        Returns:
            DataFrame with discovered instances (instance_id, account_id, region, instance_name)
        """
        from runbooks.common.profile_utils import create_operational_session, create_timeout_protected_client

        print_section("Resource Explorer Discovery (100% Visibility)", emoji="🔍")

        try:
            # Create session for aggregator account using standardized helper
            aggregator_session = create_operational_session(aggregator_profile)
            re_client = create_timeout_protected_client(aggregator_session, "resource-explorer-2", aggregator_region)

            print_info(f"Querying Resource Explorer in {aggregator_region} (profile: {aggregator_profile})...")

            # Query Resource Explorer for ALL EC2 instances
            instances = []
            paginator = re_client.get_paginator("search")

            for page in paginator.paginate(QueryString="resourcetype:ec2:instance", MaxResults=1000):
                for resource in page.get("Resources", []):
                    # Parse ARN: arn:aws:ec2:region:account-id:instance/instance-id
                    instance_id = resource["Arn"].split("/")[-1]
                    account_id = resource.get("OwningAccountId", "N/A")
                    region = resource.get("Region", "N/A")

                    # Extract Name tag from properties
                    instance_name = "N/A"
                    for prop in resource.get("Properties", []):
                        if isinstance(prop.get("Data"), list):
                            for tag in prop["Data"]:
                                if isinstance(tag, dict) and tag.get("Key") == "Name":
                                    instance_name = tag.get("Value", "N/A")
                                    break

                    instances.append(
                        {
                            "instance_id": instance_id,
                            "account_id": account_id,
                            "region": region,
                            "instance_name": instance_name,
                            "enrichment_source": "resource_explorer",
                        }
                    )

            # Create DataFrame
            df = pd.DataFrame(instances)

            # Convert account_id to string immediately to prevent type issues
            if "account_id" in df.columns:
                df["account_id"] = df["account_id"].astype(str)

            # Display discovery summary
            discovery_table = create_table(
                title="Resource Explorer Discovery Complete",
                columns=[{"header": "Metric", "style": "cyan"}, {"header": "Value", "style": "green"}],
            )
            discovery_table.add_row("Total Instances Discovered", str(len(df)))
            discovery_table.add_row("Unique Accounts", str(df["account_id"].nunique()))
            discovery_table.add_row("Unique Regions", str(df["region"].nunique()))
            console.print(discovery_table)

            return df

        except Exception as e:
            print_error(f"❌ Resource Explorer discovery failed: {e}")
            logger.error(f"Resource Explorer error: {e}", exc_info=True)
            # Return empty DataFrame on failure
            return pd.DataFrame(columns=["instance_id", "account_id", "region", "instance_name", "enrichment_source"])

    def _enrich_ec2_context(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with EC2 context metadata (28 columns) using HYBRID approach:
        1. Resource Explorer discovery for 100% visibility
        2. SSO profile enrichment for detailed metadata where available

        Pattern: Combines Resource Explorer + SSO profile access patterns
        """
        print_section("EC2 Context Enrichment (28 columns - HYBRID)", emoji="🖥️")

        # Initialize 28 EC2 context columns
        ec2_columns = {
            # Identity
            "instance_name": "N/A",
            "instance_state": "N/A",
            "instance_type": "N/A",
            # Hardware
            "architecture": "N/A",
            "virtualization_type": "N/A",
            "hypervisor": "N/A",
            "cpu_cores": "N/A",
            "cpu_threads": "N/A",
            "ebs_optimized": "N/A",
            # Network
            "vpc_id": "N/A",
            "subnet_id": "N/A",
            "security_groups": "N/A",
            "public_ip": "N/A",
            "private_ip": "N/A",
            "network_interfaces_count": 0,
            # Storage
            "root_device_type": "N/A",
            "root_device_name": "N/A",
            "block_device_mappings_count": 0,
            "block_device_mappings": "N/A",
            # Placement & Monitoring
            "availability_zone": "N/A",
            "placement_group": "N/A",
            "platform": "Linux",
            "key_name": "N/A",
            "iam_instance_profile": "N/A",
            "monitoring_state": "N/A",
            # Lifecycle
            "launch_time": None,
            "status_check": "N/A",
        }

        for col, default in ec2_columns.items():
            if col not in df.columns:
                df[col] = default

        # Add enrichment_source column if not present
        if "enrichment_source" not in df.columns:
            df["enrichment_source"] = "N/A"

        # Step 1: Try SSO profile enrichment first (for accounts with SSO access)
        # Parse AWS config to get account-to-profile mapping
        try:
            from runbooks.vpc.aws_config_parser import parse_aws_config

            account_profiles = parse_aws_config()
            print_info(f"Loaded {len(account_profiles)} SSO profiles from ~/.aws/config")

            # Add aws_profile column
            df["aws_profile"] = df["account_id"].astype(str).map(account_profiles)
            sso_accessible_count = df["aws_profile"].notna().sum()
            print_info(
                f"SSO accessible instances: {sso_accessible_count}/{len(df)} ({sso_accessible_count / len(df) * 100:.1f}%)"
            )

        except Exception as e:
            print_warning(f"⚠️  AWS config parsing failed: {e}")
            account_profiles = {}
            df["aws_profile"] = None

        # Group instances by account and region for efficient API calls
        instances_by_account_region = df.groupby(["account_id", "region"])["instance_id"].apply(list).to_dict()

        total_instances = len(df)
        enriched_count = 0
        terminated_count = 0
        access_denied_count = 0

        with create_progress_bar() as progress:
            task = progress.add_task(
                "[cyan]Enriching with 28-column EC2 metadata (HYBRID: SSO + AssumeRole)...", total=total_instances
            )

            for (account_id, region), instance_ids in instances_by_account_region.items():
                try:
                    # Try SSO profile first, then fall back to AssumeRole
                    account_session = None

                    # Method 1: SSO profile (preferred)
                    if str(account_id) in account_profiles:
                        profile_name = account_profiles[str(account_id)]
                        try:
                            from runbooks.common.profile_utils import (
                                create_operational_session,
                                create_timeout_protected_client,
                            )

                            account_session = create_operational_session(profile_name)
                            # Validate session works
                            sts = create_timeout_protected_client(account_session, "sts")
                            sts.get_caller_identity()
                            logger.debug(f"Using SSO profile {profile_name} for account {account_id}")
                        except Exception as e:
                            logger.warning(f"SSO profile {profile_name} failed: {e}")
                            account_session = None

                    # Method 2: AssumeRole (fallback)
                    if not account_session:
                        account_session = self._get_cross_account_session(account_id)

                    if not account_session:
                        # Permission failure - mark instances as access_denied
                        logger.warning(f"No session available for account {account_id}")
                        for instance_id in instance_ids:
                            mask = (
                                (df["instance_id"] == instance_id)
                                & ((df["account_id"] == account_id) | (df["account_id"] == str(account_id)))
                                & (df["region"] == region)
                            )
                            if mask.any():
                                idx = df[mask].index[0]
                                df.at[idx, "instance_state"] = "access_denied"
                                access_denied_count += 1

                        progress.update(task, advance=len(instance_ids))
                        continue

                    ec2_client = account_session.client("ec2", region_name=region)

                    # Process in batches of 50
                    for batch_start in range(0, len(instance_ids), 50):
                        batch = instance_ids[batch_start : batch_start + 50]

                        try:
                            # Describe instances
                            response = ec2_client.describe_instances(InstanceIds=batch)

                            # Extract instance metadata
                            for reservation in response.get("Reservations", []):
                                for instance in reservation.get("Instances", []):
                                    instance_id = instance["InstanceId"]
                                    logger.debug(f"Processing instance {instance_id}")

                                    # Find matching row (account_id may be int or str)
                                    mask = (
                                        (df["instance_id"] == instance_id)
                                        & ((df["account_id"] == account_id) | (df["account_id"] == str(account_id)))
                                        & (df["region"] == region)
                                    )

                                    if mask.any():
                                        idx = df[mask].index[0]
                                        logger.debug(f"Matched instance {instance_id} to DataFrame row {idx}")

                                        # Extract all 28 fields
                                        self._extract_instance_metadata(df, idx, instance)

                                        # Mark enrichment source (SSO or AssumeRole)
                                        if str(account_id) in account_profiles:
                                            df.at[idx, "enrichment_source"] = "ec2_api_sso"
                                        else:
                                            df.at[idx, "enrichment_source"] = "ec2_api_assumerole"

                                        enriched_count += 1
                                        logger.debug(
                                            f"Successfully enriched instance {instance_id} (count: {enriched_count})"
                                        )
                                    else:
                                        logger.warning(f"Instance {instance_id} not matched in DataFrame")

                            progress.update(task, advance=len(batch))

                        except ClientError as e:
                            if "InvalidInstanceID.NotFound" in str(e):
                                # Instance truly not found - check if it has cost data
                                for instance_id in batch:
                                    mask = (
                                        (df["instance_id"] == instance_id)
                                        & ((df["account_id"] == account_id) | (df["account_id"] == str(account_id)))
                                        & (df["region"] == region)
                                    )
                                    if mask.any():
                                        idx = df[mask].index[0]

                                        # Check if instance has cost data
                                        has_cost = False
                                        if "monthly_cost" in df.columns and "annual_cost_12mo" in df.columns:
                                            monthly = (
                                                df.at[idx, "monthly_cost"]
                                                if pd.notna(df.at[idx, "monthly_cost"])
                                                else 0
                                            )
                                            annual = (
                                                df.at[idx, "annual_cost_12mo"]
                                                if pd.notna(df.at[idx, "annual_cost_12mo"])
                                                else 0
                                            )
                                            has_cost = monthly > 0 or annual > 0

                                        if has_cost:
                                            # Has cost but not found = permission failure
                                            df.at[idx, "instance_state"] = "access_denied"
                                            access_denied_count += 1
                                        else:
                                            # No cost and not found = truly terminated
                                            df.at[idx, "instance_state"] = "terminated"
                                            terminated_count += 1

                                progress.update(task, advance=len(batch))
                            else:
                                print_warning(f"⚠️  API error in {region} for account {account_id}: {e}")
                                progress.update(task, advance=len(batch))

                except Exception as e:
                    print_warning(f"⚠️  Failed to enrich instances in {region} for account {account_id}: {e}")
                    logger.error(f"Enrichment error for account {account_id}, region {region}: {e}", exc_info=True)
                    progress.update(task, advance=len(instance_ids))

        success_rate = (enriched_count / total_instances * 100) if total_instances > 0 else 0

        # Display enrichment metrics in Rich Table
        metrics_table = create_table(
            title="EC2 Context Enrichment Complete",
            columns=[
                {"header": "Status", "style": "cyan"},
                {"header": "Count", "style": "green"},
                {"header": "Percentage", "style": "yellow"},
            ],
        )
        metrics_table.add_row("Successfully Enriched", f"{enriched_count}/{total_instances}", f"{success_rate:.1f}%")
        metrics_table.add_row(
            "Access Denied (Cross-Account)",
            f"{access_denied_count}/{total_instances}",
            f"{(access_denied_count / total_instances * 100):.1f}%" if total_instances > 0 else "0.0%",
        )
        metrics_table.add_row(
            "Terminated/Missing",
            f"{terminated_count}/{total_instances}",
            f"{(terminated_count / total_instances * 100):.1f}%" if total_instances > 0 else "0.0%",
        )
        console.print(metrics_table)

        return df

    def _get_cross_account_session(self, account_id) -> Optional[boto3.Session]:
        """
        Create cross-account session using STS AssumeRole pattern.

        Pattern: Adapted from vpc/cross_account_session.py

        Args:
            account_id: AWS account ID (str or int)
        """
        from runbooks.common.profile_utils import create_timeout_protected_client

        # Ensure account_id is string
        account_id_str = str(account_id)

        # Cache sessions to avoid repeated STS calls
        if not hasattr(self, "_session_cache"):
            self._session_cache = {}

        if account_id_str in self._session_cache:
            return self._session_cache[account_id_str]

        # Try multiple role patterns for universal compatibility
        role_patterns = [
            "OrganizationAccountAccessRole",
            "AWSControlTowerExecution",
            "OrganizationAccountAccess",
            "ReadOnlyAccess",
            "PowerUserAccess",
            "AdminRole",
            "CrossAccountRole",
        ]

        for role_name in role_patterns:
            try:
                # Assume role in target account
                sts_client = create_timeout_protected_client(self.session, "sts")
                assumed_role = sts_client.assume_role(
                    RoleArn=f"arn:aws:iam::{account_id_str}:role/{role_name}",
                    RoleSessionName=f"EC2Enrichment-{account_id_str[:12]}",
                )

                # Create session with assumed role credentials
                assumed_session = boto3.Session(
                    aws_access_key_id=assumed_role["Credentials"]["AccessKeyId"],
                    aws_secret_access_key=assumed_role["Credentials"]["SecretAccessKey"],
                    aws_session_token=assumed_role["Credentials"]["SessionToken"],
                )

                # Validate session
                assumed_sts = create_timeout_protected_client(assumed_session, "sts")
                assumed_sts.get_caller_identity()

                # Cache successful session
                self._session_cache[account_id_str] = assumed_session
                logger.debug(f"Successfully assumed role {role_name} in account {account_id_str}")

                return assumed_session

            except ClientError:
                continue

        # No role pattern worked
        logger.warning(f"Unable to assume any role in account {account_id_str} - tried: {', '.join(role_patterns)}")
        self._session_cache[account_id_str] = None
        return None

    def _extract_instance_metadata(self, df: pd.DataFrame, idx: int, instance: Dict) -> None:
        """Extract all 28 EC2 metadata fields."""
        # Basic identity
        instance_name = "N/A"
        for tag in instance.get("Tags", []):
            if tag["Key"] == "Name":
                instance_name = tag["Value"]
                break

        df.at[idx, "instance_name"] = instance_name
        df.at[idx, "instance_state"] = instance["State"]["Name"]
        df.at[idx, "instance_type"] = instance["InstanceType"]

        # Hardware
        df.at[idx, "architecture"] = instance.get("Architecture", "N/A")
        df.at[idx, "virtualization_type"] = instance.get("VirtualizationType", "N/A")
        df.at[idx, "hypervisor"] = instance.get("Hypervisor", "N/A")

        cpu_options = instance.get("CpuOptions", {})
        df.at[idx, "cpu_cores"] = cpu_options.get("CoreCount", "N/A")
        df.at[idx, "cpu_threads"] = cpu_options.get("ThreadsPerCore", "N/A")
        df.at[idx, "ebs_optimized"] = "Yes" if instance.get("EbsOptimized", False) else "No"

        # Network
        df.at[idx, "vpc_id"] = instance.get("VpcId", "N/A")
        df.at[idx, "subnet_id"] = instance.get("SubnetId", "N/A")

        security_groups = [sg.get("GroupName", sg.get("GroupId", "N/A")) for sg in instance.get("SecurityGroups", [])]
        df.at[idx, "security_groups"] = ", ".join(security_groups) if security_groups else "N/A"

        df.at[idx, "public_ip"] = instance.get("PublicIpAddress", "N/A")
        df.at[idx, "private_ip"] = instance.get("PrivateIpAddress", "N/A")
        df.at[idx, "network_interfaces_count"] = len(instance.get("NetworkInterfaces", []))

        # Storage
        df.at[idx, "root_device_type"] = instance.get("RootDeviceType", "N/A")
        df.at[idx, "root_device_name"] = instance.get("RootDeviceName", "N/A")

        block_devices = instance.get("BlockDeviceMappings", [])
        df.at[idx, "block_device_mappings_count"] = len(block_devices)

        block_device_list = [
            f"{bd.get('DeviceName', 'N/A')}:{bd.get('Ebs', {}).get('VolumeId', 'N/A')}" for bd in block_devices
        ]
        df.at[idx, "block_device_mappings"] = " | ".join(block_device_list) if block_device_list else "N/A"

        # Placement & Monitoring
        df.at[idx, "availability_zone"] = instance["Placement"]["AvailabilityZone"]
        df.at[idx, "placement_group"] = instance["Placement"].get("GroupName", "N/A")
        df.at[idx, "platform"] = instance.get("Platform", "Linux")
        df.at[idx, "key_name"] = instance.get("KeyName", "N/A")

        # IAM Instance Profile
        iam_profile = "N/A"
        if "IamInstanceProfile" in instance and instance["IamInstanceProfile"]:
            iam_arn = instance["IamInstanceProfile"].get("Arn", "N/A")
            if "instance-profile/" in iam_arn:
                iam_profile = iam_arn.split("instance-profile/")[-1]
        df.at[idx, "iam_instance_profile"] = iam_profile

        df.at[idx, "monitoring_state"] = instance.get("Monitoring", {}).get("State", "N/A")

        # Lifecycle
        if "LaunchTime" in instance:
            df.at[idx, "launch_time"] = instance["LaunchTime"].strftime("%Y-%m-%d %H:%M:%S")

        df.at[idx, "status_check"] = "OK"  # Will be updated by status check API

    def _enrich_volume_encryption(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with EBS volume encryption status (PCI-DSS/HIPAA compliance).

        Adds columns:
        - root_volume_encrypted (bool): Root EBS volume encryption
        - ebs_volumes_encrypted_count (int): Number of encrypted volumes
        - ebs_volumes_total_count (int): Total EBS volumes attached
        - encryption_status (str): 'Fully Encrypted' | 'Partially Encrypted' | 'Not Encrypted'

        Pattern: Adapted from workspaces_analyzer.py check_volume_encryption()
        """
        from runbooks.common.profile_utils import create_timeout_protected_client

        print_section("EBS Volume Encryption Analysis", emoji="🔒")

        # Initialize columns
        df["root_volume_encrypted"] = False
        df["ebs_volumes_encrypted_count"] = 0
        df["ebs_volumes_total_count"] = 0
        df["encryption_status"] = "Unknown"

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Checking EBS encryption...", total=len(df))

            for idx, row in df.iterrows():
                instance_id = row.get("instance_id", "")
                region = row.get("region", "ap-southeast-2")

                if not instance_id or instance_id.startswith("N/A"):
                    df.at[idx, "encryption_status"] = "N/A"
                    progress.update(task, advance=1)
                    continue

                try:
                    # Get EC2 client for region
                    ec2_regional = create_timeout_protected_client(self.session, "ec2", region)

                    # Get instance details
                    response = ec2_regional.describe_instances(InstanceIds=[instance_id])
                    reservations = response.get("Reservations", [])

                    if not reservations:
                        progress.update(task, advance=1)
                        continue

                    instances = reservations[0].get("Instances", [])
                    if not instances:
                        progress.update(task, advance=1)
                        continue

                    instance = instances[0]
                    block_devices = instance.get("BlockDeviceMappings", [])

                    # Extract volume IDs
                    volume_ids = [bd.get("Ebs", {}).get("VolumeId") for bd in block_devices if bd.get("Ebs")]
                    volume_ids = [vid for vid in volume_ids if vid]

                    if not volume_ids:
                        df.at[idx, "encryption_status"] = "No Volumes"
                        progress.update(task, advance=1)
                        continue

                    # Describe volumes
                    volumes_response = ec2_regional.describe_volumes(VolumeIds=volume_ids)
                    volumes = volumes_response.get("Volumes", [])

                    encrypted_count = sum(1 for vol in volumes if vol.get("Encrypted", False))
                    total_count = len(volumes)

                    # Root volume check
                    root_device_name = instance.get("RootDeviceName", "")
                    root_encrypted = False

                    for vol in volumes:
                        for attachment in vol.get("Attachments", []):
                            if attachment.get("Device") == root_device_name:
                                root_encrypted = vol.get("Encrypted", False)
                                break

                    # Update DataFrame
                    df.at[idx, "root_volume_encrypted"] = root_encrypted
                    df.at[idx, "ebs_volumes_encrypted_count"] = encrypted_count
                    df.at[idx, "ebs_volumes_total_count"] = total_count

                    # Encryption status
                    if encrypted_count == total_count:
                        df.at[idx, "encryption_status"] = "Fully Encrypted"
                    elif encrypted_count > 0:
                        df.at[idx, "encryption_status"] = "Partially Encrypted"
                    else:
                        df.at[idx, "encryption_status"] = "Not Encrypted"

                except ClientError as e:
                    logger.warning(f"Failed to check encryption for {instance_id}: {e}")
                    df.at[idx, "encryption_status"] = "Error"

                progress.update(task, advance=1)

        # Summary
        compliant_count = (df["encryption_status"] == "Fully Encrypted").sum()
        total_with_volumes = (df["encryption_status"] != "N/A").sum()
        compliance_rate = (compliant_count / total_with_volumes * 100) if total_with_volumes > 0 else 0

        print_success(f"✅ Volume encryption check complete")
        print_info(f"   Fully encrypted: {compliant_count}/{total_with_volumes} ({compliance_rate:.1f}%)")

        if compliance_rate < 100:
            print_warning(
                f"⚠️  PCI-DSS/HIPAA compliance risk: {total_with_volumes - compliant_count} instances not fully encrypted"
            )

        return df

    def _enrich_costs(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich with Cost Explorer data (12-month historical)."""
        print_section("Cost Analysis (12-month trailing)", emoji="💰")

        try:
            # Get unique account IDs
            account_ids = df["account_id"].unique().tolist()
            account_ids = [str(acc_id) for acc_id in account_ids if acc_id and acc_id != "N/A"]

            # Get 12-month cost breakdown
            cost_df = self.cost_enricher.get_12_month_cost_breakdown(
                billing_profile=self.config.billing_profile,
                account_ids=account_ids,
                service_filter="Amazon Elastic Compute Cloud - Compute",
            )

            if not cost_df.empty:
                # Calculate cost metrics per account
                df = self._calculate_cost_metrics(df, cost_df)

                total_monthly = df["monthly_cost"].sum() if "monthly_cost" in df.columns else 0
                total_annual = df["annual_cost_12mo"].sum() if "annual_cost_12mo" in df.columns else 0

                # Display cost metrics in Rich Table
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

                # Update DataFrame
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

    def _enrich_activity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enrich with CloudTrail activity (4 columns)."""
        print_section("CloudTrail Activity Enrichment", emoji="📋")
        print_warning("⚠️  This operation takes 60-90 seconds due to CloudTrail API pagination")

        try:
            df = self.ct_enricher.enrich_with_activity(
                df=df,
                resource_id_column="instance_id",
                management_profile=self.config.management_profile,
                lookback_days=90,
            )

            idle_count = df["is_idle"].sum() if "is_idle" in df.columns else 0
            print_info(f"   Idle instances (>30 days): {idle_count}")

            return df

        except Exception as e:
            print_error(f"❌ CloudTrail enrichment failed: {e}")
            logger.error(f"CloudTrail error: {e}", exc_info=True)
            return df

    def _enrich_stopped_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich DataFrame with E4: Stopped state duration analysis.

        Signal: stopped_days ≥ 30 → +8 points
        Reuses existing instance_state + state_transition_time columns from EC2 context.
        No additional API calls required.
        """
        try:
            enricher = StoppedStateEnricher()
            df = enricher.enrich_with_stopped_duration(df)

            # Summary statistics
            stopped_instances = (df["instance_state"] == "stopped").sum()
            long_stopped = (df["stopped_days"] >= 30).sum()

            if stopped_instances > 0:
                print_info(f"   Stopped instances: {stopped_instances} total, {long_stopped} stopped ≥30 days")

            return df

        except Exception as e:
            print_error(f"❌ E4 stopped duration enrichment failed: {e}")
            logger.error(f"E4 enrichment error: {e}", exc_info=True)
            # Add default column on error
            if "stopped_days" not in df.columns:
                df["stopped_days"] = 0
            return df

    def _enrich_storage_io(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich DataFrame with E6: CloudWatch storage I/O metrics.

        Signal: disk_total_ops_p95 ≤ 10 → +5 points
        Queries CloudWatch for 14-day DiskReadOps + DiskWriteOps metrics (p95).
        """
        try:
            operational_profile = self.config.operational_profile or self.config.management_profile

            enricher = StorageIOEnricher()
            df = enricher.enrich_with_storage_io(
                df=df,
                instance_id_column="instance_id",
                operational_profile=operational_profile,
                region="ap-southeast-2",  # TODO: Make region-aware for production
                lookback_days=14,
            )

            # Summary statistics
            low_io_count = (df["disk_total_ops_p95"] <= 10).sum()
            instances_with_metrics = (df["disk_total_ops_p95"] > 0).sum()

            if instances_with_metrics > 0:
                print_info(f"   Low I/O instances (≤10 ops): {low_io_count}/{instances_with_metrics} with metrics")

            return df

        except Exception as e:
            print_error(f"❌ E6 storage I/O enrichment failed: {e}")
            logger.error(f"E6 enrichment error: {e}", exc_info=True)
            # Add default columns on error
            if "disk_read_ops_p95" not in df.columns:
                df["disk_read_ops_p95"] = 0.0
            if "disk_write_ops_p95" not in df.columns:
                df["disk_write_ops_p95"] = 0.0
            if "disk_total_ops_p95" not in df.columns:
                df["disk_total_ops_p95"] = 0.0
            return df

    def _enrich_cost_rightsizing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich DataFrame with E7: Cost Explorer rightsizing recommendations.

        Signal: rightsizing_recommendation == 'Terminate' AND savings > $0 → +3 points
        Queries Cost Explorer GetRightsizingRecommendation API.
        """
        try:
            enricher = CostOptimizerEnricher()
            df = enricher.enrich_with_cost_optimizer(
                df=df,
                instance_id_column="instance_id",
                billing_profile=self.config.billing_profile,
                region="ap-southeast-2",  # Cost Explorer always uses ap-southeast-2
            )

            # Summary statistics
            terminate_count = (df["rightsizing_recommendation"] == "Terminate").sum()
            total_savings = df["rightsizing_savings_estimate"].sum()

            if terminate_count > 0:
                print_info(
                    f"   Terminate recommendations: {terminate_count} instances, ${total_savings:.2f}/month savings"
                )

            return df

        except Exception as e:
            print_error(f"❌ E7 cost rightsizing enrichment failed: {e}")
            logger.error(f"E7 enrichment error: {e}", exc_info=True)
            # Add default columns on error
            if "rightsizing_savings_estimate" not in df.columns:
                df["rightsizing_savings_estimate"] = 0.0
            if "rightsizing_recommendation" not in df.columns:
                df["rightsizing_recommendation"] = "None"
            return df

    def _enrich_service_attachments(self, df: pd.DataFrame, enable_expensive_signals: bool = False) -> pd.DataFrame:
        """
        Enrich DataFrame with E5: Service attachment detection (ALB/ASG/ECS/EKS).

        Signal: No service attachments → +6 points
        Queries 4 AWS service APIs (ELBv2, AutoScaling, ECS, EKS) to detect service dependencies.

        Performance: EXPENSIVE (4 cross-service APIs), disabled by default
        """
        try:
            print_info(f"🔍 E5: Service attachment enrichment (enable_expensive_signals={enable_expensive_signals})...")

            # Get unique instance IDs
            instance_ids = df["instance_id"].unique().tolist()

            # Get operational profile for service API calls
            operational_profile = self.config.operational_profile or self.config.management_profile

            # Query service attachments
            attachments = get_service_attachments(
                instance_ids=instance_ids,
                profile=operational_profile,
                region="ap-southeast-2",  # TODO: Make region-aware for production
                enable_expensive_signals=enable_expensive_signals,
            )

            # Add service attachment columns to DataFrame
            df["service_attachment_score"] = 0
            df["is_in_target_group"] = "N/A"
            df["is_in_asg"] = "N/A"
            df["is_ecs_instance"] = "N/A"
            df["service_attachments_summary"] = "Not evaluated"
            df["attachment_count"] = 0

            for idx, row in df.iterrows():
                instance_id = row.get("instance_id", "")

                if instance_id in attachments:
                    attachment_data = attachments[instance_id]
                    df.at[idx, "service_attachment_score"] = attachment_data["score"]
                    df.at[idx, "is_in_target_group"] = attachment_data["is_in_target_group"]
                    df.at[idx, "is_in_asg"] = attachment_data["is_in_asg"]
                    df.at[idx, "is_ecs_instance"] = attachment_data["is_ecs_instance"]
                    df.at[idx, "service_attachments_summary"] = attachment_data["service_attachments_summary"]
                    df.at[idx, "attachment_count"] = attachment_data["attachment_count"]

            # Summary statistics
            if enable_expensive_signals:
                detached_count = (df["service_attachment_score"] == 6).sum()
                attached_count = (df["attachment_count"] > 0).sum()
                print_info(f"   Detached instances (E5 signal): {detached_count}/{len(df)}")
                print_info(f"   Attached instances (ALB/ASG/ECS): {attached_count}/{len(df)}")
            else:
                print_info(f"   E5 enrichment skipped (set enable_expensive_signals=True for full analysis)")

            return df

        except Exception as e:
            print_error(f"❌ E5 service attachment enrichment failed: {e}")
            logger.error(f"E5 enrichment error: {e}", exc_info=True)
            # Add default columns on error
            if "service_attachment_score" not in df.columns:
                df["service_attachment_score"] = 0
            if "is_in_target_group" not in df.columns:
                df["is_in_target_group"] = "ERROR"
            if "is_in_asg" not in df.columns:
                df["is_in_asg"] = "ERROR"
            if "is_ecs_instance" not in df.columns:
                df["is_ecs_instance"] = "ERROR"
            if "service_attachments_summary" not in df.columns:
                df["service_attachments_summary"] = f"Error: {str(e)}"
            if "attachment_count" not in df.columns:
                df["attachment_count"] = 0
            return df

    def _enrich_decommission_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich with Phase 1 decommission scoring signals.

        Integrates:
        - Signal E1: Compute Optimizer Idle (60 points)
        - Signal E2: SSM Agent Offline/Stale (8 points)
        - Decommission Score: Weighted composite (0-100 scale)
        - Decommission Tier: MUST/SHOULD/COULD/KEEP classification

        Pattern: Reuse Phase 1 modules (compute_optimizer.py, ssm_integration.py, decommission_scorer.py)
        """
        print_section("Decommission Scoring (Phase 1 Signals)", emoji="🎯")

        try:
            from .compute_optimizer import enrich_dataframe_with_compute_optimizer
            from .ssm_integration import enrich_dataframe_with_ssm_status
            from .decommission_scorer import calculate_ec2_score

            # Step 6.1: Compute Optimizer idle recommendations (Signal E1)
            print_info("🔍 Querying AWS Compute Optimizer for idle instances...")
            df = enrich_dataframe_with_compute_optimizer(
                df=df,
                instance_id_column="instance_id",
                profile=self.config.management_profile,
                region="ap-southeast-2",  # Compute Optimizer is region-agnostic for EC2
            )

            # Step 6.2: SSM agent heartbeat status (Signal E2)
            operational_profile = self.config.operational_profile or self.config.management_profile
            print_info(f"🔍 Checking SSM agent heartbeat status (profile: {operational_profile})...")

            # Get unique instance IDs for SSM check
            instance_ids = df["instance_id"].unique().tolist()

            from .ssm_integration import get_ssm_heartbeat_status

            ssm_status = get_ssm_heartbeat_status(
                instance_ids=instance_ids,
                profile=operational_profile,
                region="ap-southeast-2",  # Will need region-aware logic for production
                stale_threshold_days=7,
            )

            # Add SSM columns
            df["ssm_score"] = 0
            df["ssm_ping_status"] = "N/A"
            df["ssm_last_ping_days"] = 0

            for idx, row in df.iterrows():
                instance_id = row.get("instance_id", "")
                if instance_id in ssm_status:
                    status = ssm_status[instance_id]
                    df.at[idx, "ssm_score"] = status["score"]
                    df.at[idx, "ssm_ping_status"] = status["ping_status"]
                    df.at[idx, "ssm_last_ping_days"] = status["last_ping_days"]

            # Step 6.3: Calculate composite decommission scores
            print_info("🎯 Calculating decommission scores (7-signal framework)...")

            scores = []
            for _, row in df.iterrows():
                # Build signal dictionary (E1-E7)
                signals = {
                    "E1": row.get("co_idle_score", 0),  # Compute Optimizer Idle
                    "E2": row.get("ssm_score", 0),  # SSM Agent Offline/Stale
                    "E3": 0,  # Network Activity (future)
                    "E4": 0,  # Stopped State (future)
                    "E5": 0,  # Old Snapshot (future)
                    "E6": 0,  # No Tags (future)
                    "E7": 0,  # Dev/Test Environment (future)
                }

                score_result = calculate_ec2_score(signals)
                scores.append(score_result)

            df["decommission_score"] = [s["total_score"] for s in scores]
            df["decommission_tier"] = [s["tier"] for s in scores]
            df["decommission_recommendation"] = [s["recommendation"] for s in scores]
            df["signal_count"] = [s["signal_count"] for s in scores]

            # Add signal_breakdown for E1-E7 expansion (enables lines 1420-1430 expansion logic)
            import json

            df["signal_breakdown"] = [json.dumps(s["signals"]) for s in scores]

            # Display tier breakdown
            tier_counts = df["decommission_tier"].value_counts()

            tier_table = create_table(
                title="Decommission Tier Breakdown",
                columns=[
                    {"header": "Tier", "style": "cyan bold"},
                    {"header": "Count", "style": "green"},
                    {"header": "Percentage", "style": "yellow"},
                ],
            )

            total_instances = len(df)
            for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
                count = tier_counts.get(tier, 0)
                percentage = (count / total_instances * 100) if total_instances > 0 else 0
                tier_table.add_row(tier, str(count), f"{percentage:.1f}%")

            console.print(tier_table)

            # Priority summary
            priority_count = tier_counts.get("MUST", 0) + tier_counts.get("SHOULD", 0)
            priority_pct = (priority_count / total_instances * 100) if total_instances > 0 else 0

            if priority_count > 0:
                print_success(f"✅ Identified {priority_count} priority decommission candidates ({priority_pct:.1f}%)")
            else:
                print_info("ℹ️  No high-priority decommission candidates identified")

            return df

        except ImportError as e:
            print_error(f"❌ Phase 1 module unavailable: {e}")
            print_warning("   Ensure compute_optimizer, ssm_integration, and decommission_scorer are installed")
            return df
        except Exception as e:
            print_error(f"❌ Decommission scoring failed: {e}")
            logger.error(f"Decommission scoring error: {e}", exc_info=True)
            return df

    def display_summary(self, df: pd.DataFrame) -> None:
        """Display analysis summary with Rich CLI."""
        print_header("EC2 Cost Analysis Summary")

        # Cost tree visualization
        if "account_name" in df.columns and "monthly_cost" in df.columns:
            cost_tree = create_cost_tree(
                df=df, group_by="account_name", cost_column="monthly_cost", title="EC2 Cost Analysis"
            )
            console.print(cost_tree)

        # Summary table with Account ID
        summary_table = create_table(
            title="Cost Summary by Account",
            columns=[
                {"header": "Account", "style": "cyan"},
                {"header": "Instances", "style": "green", "justify": "right"},
                {"header": "Monthly Cost", "style": "yellow", "justify": "right"},
                {"header": "Annual Est.", "style": "magenta", "justify": "right"},
            ],
        )

        if "account_name" in df.columns and "account_id" in df.columns:
            # Group by both account_name and account_id
            account_summary = (
                df.groupby(["account_name", "account_id"])
                .agg({"instance_id": "count", "monthly_cost": "sum"})
                .reset_index()
            )

            for _, row in account_summary.iterrows():
                from ..common.rich_utils import format_account_name

                account_display = format_account_name(str(row["account_name"]), str(row["account_id"]))
                summary_table.add_row(
                    account_display,
                    str(int(row["instance_id"])),
                    str(format_cost(row["monthly_cost"])),
                    str(format_cost(row["monthly_cost"] * 12)),
                )

        console.print(summary_table)

    def export_excel(self, df: pd.DataFrame, output_file: str) -> None:
        """Export analysis to multi-sheet Excel."""
        # Phase 1 Enhancement: Expand signal_breakdown JSON into e1-e7_signal columns
        # Fix for Excel export missing 21 columns (including E1-E7 decommission signals)
        # Root cause: signal_breakdown stored as JSON blob, not expanded before export
        if "signal_breakdown" in df.columns:
            import json

            # Pre-create columns with float64 dtype to avoid LossySetitemError in pandas 3.13
            for i in range(1, 8):
                if f"e{i}_signal" not in df.columns:
                    df[f"e{i}_signal"] = 0.0  # Use float to match signal score types

            for idx, row in df.iterrows():
                try:
                    # Use df.at[idx, 'column'] for pandas 2.3.1+ compatibility
                    signal_data = df.at[idx, "signal_breakdown"]
                    signals = json.loads(signal_data) if signal_data else {}
                    for signal_id in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
                        df.at[idx, f"e{signal_id[1:]}_signal"] = float(signals.get(signal_id, 0))
                except (json.JSONDecodeError, TypeError):
                    # Handle malformed JSON gracefully (use float to match column dtype)
                    for i in range(1, 8):
                        df.at[idx, f"e{i}_signal"] = 0.0

        export_compute_excel(
            df=df,
            output_file=output_file,
            resource_type="ec2",
            include_cost_analysis=True,
            include_recommendations=False,
        )

    def export_markdown(self, df: pd.DataFrame, output_file: str) -> None:
        """
        Export EC2 analysis to GitHub-flavored Markdown.

        Args:
            df: EC2 analysis DataFrame with cost and decommission data
            output_file: Path to .md output file
        """
        from .markdown_exporter import export_dataframe_to_markdown

        # Calculate summary metrics
        summary_metrics = {
            "Total Instances": len(df),
            "MUST Tier (E1-E7: 80-100)": len(df[df["decommission_score"] >= 80])
            if "decommission_score" in df.columns
            else 0,
            "SHOULD Tier (E1-E7: 60-79)": len(df[(df["decommission_score"] >= 60) & (df["decommission_score"] < 80)])
            if "decommission_score" in df.columns
            else 0,
            "Estimated Monthly Savings": f"${df['monthly_cost'].sum():.2f}"
            if "monthly_cost" in df.columns
            else "$0.00",
        }

        # Generate recommendations
        recommendations = []
        if "decommission_score" in df.columns:
            must_count = len(df[df["decommission_score"] >= 80])
            if must_count > 0:
                recommendations.append(f"Review {must_count} MUST tier instances for immediate decommission")
        recommendations.extend(
            [
                "Validate CloudTrail data for idle instances (E1 signal)",
                "Check Cost Explorer for usage patterns (E3 signal)",
            ]
        )

        # Export to markdown
        export_dataframe_to_markdown(
            df=df,
            output_file=output_file,
            title="EC2 Decommission Analysis Report",
            summary_metrics=summary_metrics,
            recommendations=recommendations,
        )
        logger.info(f"Markdown export completed: {output_file}")


def analyze_ec2_costs(
    input_file: str,
    output_file: str,
    management_profile: Optional[str] = None,
    billing_profile: Optional[str] = None,
    operational_profile: Optional[str] = None,
    enable_organizations: bool = True,
    enable_cost: bool = True,
    enable_activity: bool = False,
    enable_volume_encryption: bool = False,
    include_12month_cost: bool = True,
    decommission_mode: bool = False,
) -> pd.DataFrame:
    """
    CLI and notebook entry point for EC2 cost analysis with unified profile routing (v1.1.11+).

    Usage (v1.1.11+ with automatic profile routing):
        # Python API - profiles auto-resolved
        from runbooks.finops.ec2_analyzer import analyze_ec2_costs

        df = analyze_ec2_costs(
            input_file='ec2.xlsx',
            output_file='ec2-enriched.xlsx'
        )

    Usage (backward compatible with explicit profiles):
        # Python API - explicit profiles
        df = analyze_ec2_costs(
            input_file='ec2.xlsx',
            output_file='ec2-enriched.xlsx',
            management_profile='mgmt',
            billing_profile='billing'
        )

        # CLI - profiles from environment or defaults
        runbooks finops analyze-ec2 --input ec2.xlsx --output enriched.xlsx

    Args:
        input_file: Excel file with EC2 inventory
        output_file: Output Excel file path
        management_profile: AWS profile for Organizations (defaults to service routing)
        billing_profile: AWS profile for Cost Explorer (defaults to service routing)
        operational_profile: AWS profile for EC2 operations (defaults to management_profile)
        enable_organizations: Enable Organizations enrichment
        enable_cost: Enable Cost Explorer enrichment
        enable_activity: Enable CloudTrail activity enrichment
        enable_volume_encryption: Enable EBS volume encryption check (PCI-DSS/HIPAA)
        include_12month_cost: Include 12-month cost breakdown

    Returns:
        DataFrame with enriched EC2 data
    """
    try:
        # Create configuration
        config = EC2AnalysisConfig(
            management_profile=management_profile,
            billing_profile=billing_profile,
            operational_profile=operational_profile,
            enable_organizations=enable_organizations,
            enable_cost=enable_cost,
            enable_activity=enable_activity,
            enable_volume_encryption=enable_volume_encryption,
            include_12month_cost=include_12month_cost,
        )

        # Initialize analyzer
        analyzer = EC2CostAnalyzer(config)

        # Execute analysis
        df = analyzer.analyze(input_file=input_file)

        # Display summary
        analyzer.display_summary(df)

        # Phase 2 Enhancement: Decommission mode filtering
        # Filter to decommission-focused columns (45 columns vs 87 full inventory)
        if decommission_mode:
            decommission_cols = [
                # Core identification (4)
                "instance_id",
                "account_name",
                "account_id",
                "region",
                # Instance context (3)
                "instance_type",
                "instance_state",
                "launch_date",
                # Cost metrics (3)
                "monthly_cost",
                "annual_cost_12mo",
                "cost_trend",
                # Decommission scoring (4)
                "decommission_score",
                "decommission_tier",
                "decommission_reason",
                "decommission_confidence",
                # E1-E7 signals (7)
                "e1_signal",
                "e2_signal",
                "e3_signal",
                "e4_signal",
                "e5_signal",
                "e6_signal",
                "e7_signal",
                # Signal evidence - Compute Optimizer (3)
                "compute_optimizer_finding",
                "co_recommendation",
                "co_lookback_days",
                # Signal evidence - CloudWatch (3)
                "p95_cpu",
                "p95_network",
                "p95_disk_io",
                # Signal evidence - CloudTrail (4)
                "days_since_activity",
                "activity_count",
                "last_activity_date",
                "is_idle",
                # Signal evidence - SSM (2)
                "ssm_ping_status",
                "ssm_last_ping_days",
                # Signal evidence - Attachments (1)
                "attached_to_service",
                # Organizations metadata (3)
                "wbs_code",
                "cost_group",
                "technical_owner",
                # Operational metadata (3)
                "vpc_id",
                "subnet_id",
                "availability_zone",
                # Tags (3)
                "Tags",
                "Tag:costgroup",
                "Tag:owner",
            ]
            # Filter to only columns that exist in DataFrame
            df_export = df[[col for col in decommission_cols if col in df.columns]]
            print_info(
                f"🎯 Decommission mode: Filtered to {len(df_export.columns)} focused columns (from {len(df.columns)} total)"
            )
        else:
            df_export = df

        # Export results
        analyzer.export_excel(df_export, output_file)

        return df

    except Exception as e:
        print_error(f"❌ EC2 analysis failed: {e}")
        logger.error(f"EC2 analysis error: {e}", exc_info=True)
        raise
