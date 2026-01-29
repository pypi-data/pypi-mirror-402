"""
WorkSpaces Cost Optimization Analysis - Enterprise Framework:

This module provides business-focused WorkSpaces analysis with enterprise patterns:
- Real AWS API integration (no hardcoded values)
- Rich CLI formatting throughout
- Profile management following proven patterns
- MCP validation ready
- Enterprise safety controls

Strategic Alignment:
- "Do one thing and do it well": WorkSpaces cost optimization focus
- "Move Fast, But Not So Fast We Crash": Safety controls with dry-run defaults
- Enterprise FAANG SDLC: Evidence-based cost optimization with audit trails
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from ..common.aws_profile_manager import get_profile_for_service
from ..common.rich_utils import (
    console,
    create_panel,
    create_progress_bar,
    create_table,
    format_account_name,
    format_cost,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)
from ..remediation.workspaces_list import calculate_workspace_monthly_cost, get_workspaces

logger = logging.getLogger(__name__)

# Configure module-level logging to suppress INFO/DEBUG messages in notebooks
logging.getLogger("runbooks").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.ERROR)
logging.getLogger("boto3").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
import warnings

warnings.filterwarnings("ignore")


@dataclass
class WorkSpaceAnalysisResult:
    """WorkSpace analysis result with cost optimization data."""

    workspace_id: str
    username: str
    state: str
    running_mode: str
    bundle_id: str
    monthly_cost: float
    annual_cost: float
    last_connection: Optional[str]
    days_since_connection: int
    is_unused: bool
    usage_hours: float
    connection_state: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class WorkSpacesCostSummary:
    """Summary of WorkSpaces cost analysis."""

    total_workspaces: int
    unused_workspaces: int
    total_monthly_cost: float
    unused_monthly_cost: float
    potential_annual_savings: float
    target_achievement_rate: float
    analysis_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class WorkSpacesCostAnalyzer:
    """
    WorkSpaces cost optimization analyzer following enterprise patterns.

    Implements WorkSpaces optimization requirements with proven profile management and Rich CLI standards.
    """

    def __init__(self, profile: Optional[str] = None):
        """
        Initialize analyzer with unified profile routing (v1.1.11+).

        Profile Resolution:
        1. Explicit profile parameter (highest priority - backward compatible)
        2. AWS_MANAGEMENT_PROFILE environment variable
        3. Service-specific default (${MANAGEMENT_PROFILE})
        4. AWS_PROFILE environment variable
        5. None (AWS default credentials)

        Args:
            profile: AWS profile override (defaults to service routing)
        """
        from runbooks.common.profile_utils import create_operational_session

        # v1.1.11+ unified profile routing
        # Resolves WorkSpaces profile with automatic fallback chain
        self.profile = get_profile_for_service("workspaces", override_profile=profile)
        self.session = create_operational_session(self.profile)

        # WorkSpaces optimization business targets
        self.target_annual_savings = 12518.0
        self.unused_threshold_days = 90
        self.analysis_period_days = 30

        logger.debug(f"WorkSpaces analyzer initialized with profile: {self.profile}")

    def check_volume_encryption(self, workspace_id: str) -> Dict[str, bool]:
        """
        Check volume encryption status for WorkSpace.

        Args:
            workspace_id: WorkSpace ID (e.g., 'ws-xxx')

        Returns:
            {
                'root_volume_encrypted': bool,
                'user_volume_encrypted': bool
            }
        """
        try:
            ws_client = self.session.client("workspaces")

            # Get WorkSpace details
            response = ws_client.describe_workspaces(WorkspaceIds=[workspace_id])

            workspaces = response.get("Workspaces", [])
            if not workspaces:
                return {"root_volume_encrypted": False, "user_volume_encrypted": False}

            workspace = workspaces[0]

            # Extract volume encryption properties
            root_encrypted = workspace.get("RootVolumeEncryptionEnabled", False)
            user_encrypted = workspace.get("UserVolumeEncryptionEnabled", False)

            return {"root_volume_encrypted": root_encrypted, "user_volume_encrypted": user_encrypted}

        except ClientError as e:
            logger.error(f"Failed to check encryption for {workspace_id}: {e}")
            return {"root_volume_encrypted": False, "user_volume_encrypted": False}
        except Exception as e:
            logger.error(f"Unexpected error checking encryption for {workspace_id}: {e}")
            return {"root_volume_encrypted": False, "user_volume_encrypted": False}

    def get_volume_encryption(self, df) -> pd.DataFrame:
        """
        Check EBS volume encryption for WorkSpaces DataFrame and enrich with W1 connection signals.

        This method now performs dual enrichment:
        1. Volume encryption status (original functionality)
        2. W1 connection recency signals (new: days since last connection + scoring)

        Args:
            df: pandas DataFrame with WorkSpace IDs

        Returns:
            DataFrame with 'root_volume_encrypted', 'user_volume_encrypted',
            'days_since_last_connection', 'w1_connection_recency_score' columns

        Migration: notebooks/compute/workspaces.ipynb Cell 12A implementation
        Enhancement: W1 signal calculation added for decommission classification
        """
        try:
            import pandas as pd

            print_info("🔍 Checking volume encryption and connection status for WorkSpaces...")

            # Add encryption columns
            df["root_volume_encrypted"] = False
            df["user_volume_encrypted"] = False
            df["encryption_status"] = "Unknown"

            # Add W1 connection signal columns
            df["days_since_last_connection"] = 9999  # Default: never connected
            df["w1_connection_recency_score"] = 45  # Default: decommission signal

            encrypted_count = 0
            w1_idle_count = 0  # WorkSpaces with ≥60 days idle

            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Checking volume encryption and connection status...", total=len(df))

                for idx, row in df.iterrows():
                    workspace_id = row.get("Identifier", row.get("WorkspaceId", ""))

                    if workspace_id and workspace_id.startswith("ws-"):
                        # Encryption enrichment (original functionality)
                        encryption_info = self.check_volume_encryption(workspace_id)

                        root_enc = encryption_info.get("root_volume_encrypted", False)
                        user_enc = encryption_info.get("user_volume_encrypted", False)

                        df.at[idx, "root_volume_encrypted"] = root_enc
                        df.at[idx, "user_volume_encrypted"] = user_enc

                        # Determine status
                        if root_enc and user_enc:
                            status = "Fully Encrypted"
                            encrypted_count += 1
                        elif root_enc or user_enc:
                            status = "Partially Encrypted"
                        else:
                            status = "Not Encrypted"

                        df.at[idx, "encryption_status"] = status

                        # W1 Signal Enrichment: Connection recency
                        try:
                            from runbooks.common.profile_utils import create_timeout_protected_client

                            ws_client = create_timeout_protected_client(self.session, "workspaces")
                            conn_response = ws_client.describe_workspaces_connection_status(WorkspaceIds=[workspace_id])

                            conn_status = conn_response.get("WorkspacesConnectionStatus", [])
                            if conn_status:
                                last_conn = conn_status[0].get("LastKnownUserConnectionTimestamp")
                                if last_conn:
                                    # Calculate days since last connection
                                    from datetime import timezone as tz

                                    now = datetime.now(tz.utc)
                                    if last_conn.tzinfo is None:
                                        last_conn = last_conn.replace(tzinfo=tz.utc)

                                    days_since = (now - last_conn).days
                                    df.at[idx, "days_since_last_connection"] = max(0, days_since)

                                    # W1 scoring: 45 points if ≥60 days idle
                                    w1_score = 45 if days_since >= 60 else 0
                                    df.at[idx, "w1_connection_recency_score"] = w1_score

                                    if days_since >= 60:
                                        w1_idle_count += 1
                                # else: Keep default (9999 days, 45 points) for never-connected
                        except ClientError as e:
                            logger.debug(f"Connection status unavailable for {workspace_id}: {e}")
                            # Keep defaults: 9999 days, 45 points

                    progress.update(task, advance=1)

            compliance_rate = (encrypted_count / len(df) * 100) if len(df) > 0 else 0
            w1_idle_rate = (w1_idle_count / len(df) * 100) if len(df) > 0 else 0

            print_success(f"✅ Volume encryption and connection status check complete")
            print_info(f"   Fully encrypted: {encrypted_count}/{len(df)} ({compliance_rate:.1f}%)")
            print_info(f"   W1 idle (≥60 days): {w1_idle_count}/{len(df)} ({w1_idle_rate:.1f}%)")

            return df

        except Exception as e:
            print_error(f"❌ Volume encryption and connection status check failed: {e}")
            logger.error(f"Enrichment error: {e}", exc_info=True)
            return df

    def get_cloudwatch_user_connected(self, df, lookback_days: int = 30) -> pd.DataFrame:
        """
        Get CloudWatch UserConnected metric for WorkSpaces.

        Signal W2: Sum of UserConnected = 0 (no sessions) → +25 points for decommission

        Args:
            df: pandas DataFrame with WorkSpace IDs
            lookback_days: Days to look back (default: 30)

        Returns:
            DataFrame with 'user_connected_sum', 'user_connected_score' columns

        Pattern: CloudWatch metric query following AWS SDK patterns
        """
        try:
            from runbooks.common.profile_utils import create_timeout_protected_client

            print_info(f"🔍 Analyzing CloudWatch UserConnected metric ({lookback_days}-day lookback)...")

            cw_client = create_timeout_protected_client(self.session, "cloudwatch")

            # Initialize columns
            df["user_connected_sum"] = 0.0
            df["user_connected_score"] = 0

            # Calculate time window
            end_time = datetime.now(tz=timezone.utc)
            start_time = end_time - timedelta(days=lookback_days)

            no_activity_count = 0

            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Checking UserConnected metrics...", total=len(df))

                for idx, row in df.iterrows():
                    workspace_id = row.get("Identifier", row.get("WorkspaceId", ""))

                    if workspace_id and workspace_id.startswith("ws-"):
                        try:
                            response = cw_client.get_metric_statistics(
                                Namespace="AWS/WorkSpaces",
                                MetricName="UserConnected",
                                Dimensions=[{"Name": "WorkspaceId", "Value": workspace_id}],
                                StartTime=start_time,
                                EndTime=end_time,
                                Period=86400,  # 1 day
                                Statistics=["Sum"],
                            )

                            total_connected = sum(dp["Sum"] for dp in response["Datapoints"])
                            score = 25 if total_connected == 0 else 0

                            df.at[idx, "user_connected_sum"] = total_connected
                            df.at[idx, "user_connected_score"] = score

                            if total_connected == 0:
                                no_activity_count += 1

                        except ClientError as e:
                            logger.warning(f"CloudWatch query failed for {workspace_id}: {e}")
                            # Keep defaults (0 sum, 0 score)

                    progress.update(task, advance=1)

            print_success(f"✅ CloudWatch analysis complete")
            print_info(f"   No activity detected: {no_activity_count}/{len(df)} WorkSpaces")

            return df

        except Exception as e:
            print_error(f"❌ CloudWatch UserConnected analysis failed: {e}")
            logger.error(f"CloudWatch error: {e}", exc_info=True)
            return df

    def calculate_dynamic_breakeven(self, df) -> pd.DataFrame:
        """
        Calculate dynamic break-even hours using bundle pricing.

        Signal W3: Usage < break-even → +10 points (stay hourly recommendation)

        Formula: monthly_cost / hourly_rate = break_even_hours

        Args:
            df: pandas DataFrame with WorkSpace bundle information

        Returns:
            DataFrame with 'breakeven_hours', 'breakeven_score' columns

        Pattern: Pricing calculation following EC2 pattern from ec2_analyzer.py
        """
        try:
            print_info("🔍 Calculating dynamic break-even hours...")

            # Default break-even map (Conservative estimates based on AWS pricing)
            # Standard: $35/mo ÷ $0.43/hr = ~81h
            # Performance: $60/mo ÷ $0.75/hr = ~80h
            # Power: $75/mo ÷ $0.94/hr = ~80h
            # PowerPro: $90/mo ÷ $1.13/hr = ~80h
            breakeven_map = {"standard": 85.0, "performance": 80.0, "power": 80.0, "powerpro": 75.0, "value": 85.0}

            # Initialize columns
            df["breakeven_hours"] = 85.0  # Default conservative
            df["breakeven_score"] = 0

            enriched_count = 0

            for idx, row in df.iterrows():
                bundle_name = str(row.get("Compute", row.get("BundleName", ""))).lower()

                # Match bundle type
                breakeven = 85.0  # Default
                for bundle_type, hours in breakeven_map.items():
                    if bundle_type in bundle_name:
                        breakeven = hours
                        break

                df.at[idx, "breakeven_hours"] = breakeven

                # Calculate score (W3 signal)
                # If usage_hours < breakeven, +10 points (should stay hourly)
                usage_hours = row.get("user_connected_sum", 0)
                if usage_hours < breakeven:
                    df.at[idx, "breakeven_score"] = 10

                enriched_count += 1

            print_success(f"✅ Break-even calculation complete: {enriched_count}/{len(df)} WorkSpaces")

            return df

        except Exception as e:
            print_error(f"❌ Break-even calculation failed: {e}")
            logger.error(f"Break-even error: {e}", exc_info=True)
            return df

    def calculate_decommission_scores(self, df) -> pd.DataFrame:
        """
        Calculate WorkSpaces decommission scores using multi-signal framework.

        Scoring Framework (0-100 scale):
        - W1: No Connection (>90 days) → +45 points
        - W2: UserConnected = 0 (no sessions) → +25 points
        - W3: Usage < break-even → +10 points
        - W4: Stopped State (>30 days) → +10 points
        - W5: No User Tags → +5 points
        - W6: Test/Dev Environment → +5 points

        Tiers:
        - MUST (80-100): Immediate decommission candidates
        - SHOULD (50-79): Strong candidates (review recommended)
        - COULD (25-49): Potential candidates (manual review)
        - KEEP (<25): Active resources (no action)

        Args:
            df: pandas DataFrame with enrichment columns

        Returns:
            DataFrame with 'decommission_score', 'decommission_tier', 'decommission_breakdown' columns

        Pattern: Adapted from decommission_scorer.py calculate_workspaces_score()
        """
        try:
            from .decommission_scorer import calculate_workspaces_score

            print_info("🔍 Calculating decommission scores...")

            # Initialize columns
            df["decommission_score"] = 0
            df["decommission_tier"] = "KEEP"
            df["decommission_breakdown"] = ""
            df["decommission_confidence"] = "Low"

            scored_count = 0

            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Scoring WorkSpaces for decommission...", total=len(df))

                for idx, row in df.iterrows():
                    # Build signal dictionary
                    signals = {}

                    # W1: No Connection (>90 days)
                    days_since_activity = row.get("days_since_activity", 0)
                    signals["W1"] = 45 if days_since_activity > 90 else 0

                    # W2: UserConnected = 0 (from CloudWatch)
                    signals["W2"] = row.get("user_connected_score", 0)

                    # W3: Usage < break-even (from break-even calculation)
                    signals["W3"] = row.get("breakeven_score", 0)

                    # W4: Stopped State (>30 days)
                    state = str(row.get("State", row.get("Status", ""))).upper()
                    signals["W4"] = 10 if state in ["STOPPED", "SUSPENDED"] else 0

                    # W5: No User Tags
                    tags_combined = row.get("tags_combined", "")
                    signals["W5"] = 5 if not tags_combined or tags_combined == "N/A" else 0

                    # W6: Test/Dev Environment
                    account_name = str(row.get("account_name", "")).lower()
                    signals["W6"] = 5 if any(env in account_name for env in ["test", "dev", "staging"]) else 0

                    # Calculate score
                    result = calculate_workspaces_score(signals)

                    # Update DataFrame
                    df.at[idx, "decommission_score"] = result["total_score"]
                    df.at[idx, "decommission_tier"] = result["tier"]
                    df.at[idx, "decommission_breakdown"] = result["breakdown"]
                    df.at[idx, "decommission_confidence"] = result["confidence"]

                    scored_count += 1
                    progress.update(task, advance=1)

            # Display tier distribution
            tier_counts = df["decommission_tier"].value_counts()
            print_success(f"✅ Decommission scoring complete: {scored_count}/{len(df)} WorkSpaces")
            print_info(
                f"   MUST: {tier_counts.get('MUST', 0)} | SHOULD: {tier_counts.get('SHOULD', 0)} | COULD: {tier_counts.get('COULD', 0)} | KEEP: {tier_counts.get('KEEP', 0)}"
            )

            return df

        except Exception as e:
            print_error(f"❌ Decommission scoring failed: {e}")
            logger.error(f"Decommission scoring error: {e}", exc_info=True)
            return df

    def get_cloudtrail_activity(self, df, days_back: int = 90) -> pd.DataFrame:
        """
        Enrich with CloudTrail user activity.

        Args:
            df: pandas DataFrame with WorkSpace IDs
            days_back: Days to look back (default: 90)

        Returns:
            DataFrame with 'last_activity_date', 'days_since_activity', 'is_idle' columns

        Migration: Use CloudTrailEnricher from base_enrichers.py
        """
        try:
            from .base_enrichers import CloudTrailEnricher

            print_info(f"🔍 Enriching with CloudTrail activity ({days_back}-day lookback)...")

            # Initialize enricher
            ct_enricher = CloudTrailEnricher()

            # Determine resource ID column
            resource_id_column = "Identifier" if "Identifier" in df.columns else "WorkspaceId"

            # Enrich with activity
            df = ct_enricher.enrich_with_activity(
                df=df, resource_id_column=resource_id_column, management_profile=self.profile, lookback_days=days_back
            )

            idle_count = df["is_idle"].sum() if "is_idle" in df.columns else 0
            print_info(f"   Idle WorkSpaces (>30 days): {idle_count}")

            return df

        except Exception as e:
            print_error(f"❌ CloudTrail activity enrichment failed: {e}")
            logger.error(f"CloudTrail activity error: {e}", exc_info=True)
            return df

    def _calculate_cost_metrics(self, df: pd.DataFrame, cost_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate cost metrics from Cost Explorer data.

        Pattern: Adapted from EC2 analyzer (src/runbooks/finops/ec2_analyzer.py:477-511)

        Args:
            df: WorkSpaces DataFrame with 'AWS Account' column
            cost_df: Cost Explorer DataFrame with 'account_id' and 'cost' columns

        Returns:
            DataFrame with added columns: monthly_cost, annual_cost_12mo, cost_trend
        """
        # Initialize cost columns
        df["monthly_cost"] = 0.0
        df["annual_cost_12mo"] = 0.0
        df["cost_trend"] = "→ Stable"

        # Group by account and calculate metrics
        for account_id in df["AWS Account"].unique():
            account_costs = cost_df[cost_df["account_id"] == str(account_id)]

            if not account_costs.empty:
                # Calculate average monthly cost
                avg_monthly = account_costs["cost"].mean()
                total_12mo = account_costs["cost"].sum()

                # Update DataFrame
                mask = df["AWS Account"] == account_id
                df.loc[mask, "monthly_cost"] = avg_monthly / len(df[mask])
                df.loc[mask, "annual_cost_12mo"] = total_12mo / len(df[mask])

                # Calculate trend (first half vs second half comparison)
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

    def enrich_dataframe_with_organizations(self, workspaces_df, management_profile: str):
        """
        Enrich WorkSpaces DataFrame with Organizations metadata.

        Args:
            workspaces_df: pandas DataFrame with 'AWS Account' column
            management_profile: AWS profile with Organizations access

        Returns:
            Enriched DataFrame with Organizations columns:
                - account_name: Account name from Organizations
                - account_email: Account email
                - wbs_code: WBS cost allocation code
                - cost_group: Cost center assignment
                - technical_lead: Technical owner email
                - account_owner: Business owner email
        """
        try:
            import pandas as pd
            from ..inventory.organizations_utils import discover_organization_accounts

            print_info(f"Enriching WorkSpaces with Organizations metadata (profile: {management_profile})")

            # Discover accounts
            accounts, error = discover_organization_accounts(management_profile)

            if error:
                print_warning(f"⚠️  Organizations unavailable: {error}")
                print_info("Continuing without Organizations enrichment")
                # Add N/A columns
                for col in [
                    "account_name",
                    "account_email",
                    "wbs_code",
                    "cost_group",
                    "technical_lead",
                    "account_owner",
                ]:
                    workspaces_df[col] = "N/A"
                return workspaces_df

            # Create account lookup dictionary
            account_lookup = {acc["id"]: acc for acc in accounts}

            print_success(f"Organizations discovery: {len(accounts)} accounts available for enrichment")

            # Initialize new columns
            orgs_columns = [
                "account_name",
                "account_email",
                "wbs_code",
                "cost_group",
                "technical_lead",
                "account_owner",
            ]
            for col in orgs_columns:
                workspaces_df[col] = "N/A"

            # Enrich rows with Organizations metadata
            enriched_count = 0

            with create_progress_bar() as progress:
                task_id = progress.add_task(
                    "[cyan]Enriching WorkSpaces with Organizations...", total=len(workspaces_df)
                )

                for idx, row in workspaces_df.iterrows():
                    # Get account ID (handle both int and string formats)
                    account_id = str(row.get("AWS Account", "")).strip()

                    if account_id and account_id in account_lookup:
                        acc = account_lookup[account_id]

                        workspaces_df.at[idx, "account_name"] = acc.get("name", "N/A")
                        workspaces_df.at[idx, "account_email"] = acc.get("email", "N/A")
                        workspaces_df.at[idx, "wbs_code"] = acc.get("wbs_code", "N/A")
                        workspaces_df.at[idx, "cost_group"] = acc.get("cost_group", "N/A")
                        workspaces_df.at[idx, "technical_lead"] = acc.get("technical_lead", "N/A")
                        workspaces_df.at[idx, "account_owner"] = acc.get("account_owner", "N/A")

                        enriched_count += 1

                    progress.update(task_id, advance=1)

            print_success(
                f"Organizations enrichment complete: {enriched_count}/{len(workspaces_df)} WorkSpaces enriched"
            )
            return workspaces_df

        except ImportError as e:
            print_error(f"Organizations integration unavailable: {e}")
            print_warning("Ensure runbooks.inventory module is installed")
            # Add N/A columns on error
            for col in ["account_name", "account_email", "wbs_code", "cost_group", "technical_lead", "account_owner"]:
                if col not in workspaces_df.columns:
                    workspaces_df[col] = "N/A"
            return workspaces_df
        except Exception as e:
            print_error(f"Organizations enrichment failed: {e}")
            logger.error(f"Organizations enrichment error: {e}", exc_info=True)
            # Add N/A columns on error
            for col in ["account_name", "account_email", "wbs_code", "cost_group", "technical_lead", "account_owner"]:
                if col not in workspaces_df.columns:
                    workspaces_df[col] = "N/A"
            return workspaces_df

    def analyze_workspaces(
        self, unused_days: int = 90, analysis_days: int = 30, dry_run: bool = True
    ) -> Tuple[List[WorkSpaceAnalysisResult], WorkSpacesCostSummary]:
        """
        Analyze WorkSpaces for cost optimization opportunities.

        Args:
            unused_days: Days threshold for unused WorkSpaces detection
            analysis_days: Period for usage analysis
            dry_run: Safety flag for preview mode

        Returns:
            Tuple of analysis results and summary
        """
        print_header("WorkSpaces Cost Optimization Analysis", f"Profile: {self.profile}")

        if dry_run:
            print_info("🔍 Running in DRY-RUN mode (safe preview)")

        try:
            from runbooks.common.profile_utils import create_timeout_protected_client

            # Get WorkSpaces client
            ws_client = create_timeout_protected_client(self.session, "workspaces")

            # Calculate time ranges
            end_time = datetime.now(tz=timezone.utc)
            start_time = end_time - timedelta(days=analysis_days)
            unused_threshold = end_time - timedelta(days=unused_days)

            console.print(
                f"[dim]Analysis period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}[/dim]"
            )
            console.print(f"[dim]Unused threshold: {unused_days} days ({unused_threshold.strftime('%Y-%m-%d')})[/dim]")

            # Get all WorkSpaces with progress tracking
            print_info("Collecting WorkSpaces inventory...")
            paginator = ws_client.get_paginator("describe_workspaces")
            all_workspaces = []

            for page in paginator.paginate():
                workspaces = page.get("Workspaces", [])
                all_workspaces.extend(workspaces)

            console.print(f"[green]✅ Found {len(all_workspaces)} WorkSpaces[/green]")

            # Analyze each WorkSpace with progress bar
            analysis_results = []
            total_cost = 0.0
            unused_cost = 0.0

            with create_progress_bar() as progress:
                task_id = progress.add_task(f"Analyzing WorkSpaces cost optimization...", total=len(all_workspaces))

                for workspace in all_workspaces:
                    result = self._analyze_single_workspace(
                        workspace, ws_client, start_time, end_time, unused_threshold
                    )

                    analysis_results.append(result)
                    total_cost += result.monthly_cost

                    if result.is_unused:
                        unused_cost += result.monthly_cost

                    progress.advance(task_id)

            # Create summary
            unused_count = len([r for r in analysis_results if r.is_unused])
            potential_annual_savings = unused_cost * 12
            achievement_rate = (
                (potential_annual_savings / self.target_annual_savings * 100) if self.target_annual_savings > 0 else 0
            )

            summary = WorkSpacesCostSummary(
                total_workspaces=len(analysis_results),
                unused_workspaces=unused_count,
                total_monthly_cost=total_cost,
                unused_monthly_cost=unused_cost,
                potential_annual_savings=potential_annual_savings,
                target_achievement_rate=achievement_rate,
                analysis_timestamp=datetime.now().isoformat(),
            )

            return analysis_results, summary

        except ClientError as e:
            print_error(f"AWS API error: {e}")
            if "AccessDenied" in str(e):
                print_warning("💡 Try using a profile with WorkSpaces permissions")
                print_info(f"Current profile: {self.profile}")
            raise
        except Exception as e:
            print_error(f"Analysis failed: {e}")
            raise

    def _analyze_single_workspace(
        self, workspace: Dict[str, Any], ws_client, start_time: datetime, end_time: datetime, unused_threshold: datetime
    ) -> WorkSpaceAnalysisResult:
        """Analyze a single WorkSpace for cost optimization."""
        workspace_id = workspace["WorkspaceId"]
        username = workspace["UserName"]
        state = workspace["State"]
        bundle_id = workspace["BundleId"]
        running_mode = workspace["WorkspaceProperties"]["RunningMode"]

        # Get connection status
        last_connection = None
        connection_state = "UNKNOWN"

        try:
            connection_response = ws_client.describe_workspaces_connection_status(WorkspaceIds=[workspace_id])

            connection_status_list = connection_response.get("WorkspacesConnectionStatus", [])
            if connection_status_list:
                last_connection = connection_status_list[0].get("LastKnownUserConnectionTimestamp")
                connection_state = connection_status_list[0].get("ConnectionState", "UNKNOWN")
        except ClientError as e:
            logger.warning(f"Could not get connection status for {workspace_id}: {e}")

        # Format connection info
        if last_connection:
            last_connection_str = last_connection.strftime("%Y-%m-%d %H:%M:%S")
            days_since_connection = (end_time - last_connection).days
        else:
            last_connection_str = None
            days_since_connection = 999

        # Get usage metrics
        usage_hours = self._get_workspace_usage(workspace_id, start_time, end_time)

        # Calculate costs
        monthly_cost = calculate_workspace_monthly_cost(bundle_id, running_mode)
        annual_cost = monthly_cost * 12

        # Determine if unused
        is_unused = last_connection is None or last_connection < unused_threshold

        return WorkSpaceAnalysisResult(
            workspace_id=workspace_id,
            username=username,
            state=state,
            running_mode=running_mode,
            bundle_id=bundle_id,
            monthly_cost=monthly_cost,
            annual_cost=annual_cost,
            last_connection=last_connection_str,
            days_since_connection=days_since_connection,
            is_unused=is_unused,
            usage_hours=usage_hours,
            connection_state=connection_state,
        )

    def _get_workspace_usage(self, workspace_id: str, start_time: datetime, end_time: datetime) -> float:
        """Get WorkSpace usage hours from CloudWatch metrics."""
        from runbooks.common.profile_utils import create_timeout_protected_client

        try:
            cloudwatch = create_timeout_protected_client(self.session, "cloudwatch")

            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/WorkSpaces",
                MetricName="UserConnected",
                Dimensions=[{"Name": "WorkspaceId", "Value": workspace_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour intervals
                Statistics=["Sum"],
            )

            usage_hours = sum(datapoint["Sum"] for datapoint in response.get("Datapoints", []))
            return round(usage_hours, 2)

        except ClientError as e:
            logger.warning(f"Could not get usage metrics for {workspace_id}: {e}")
            return 0.0

    def display_analysis_results(self, results: List[WorkSpaceAnalysisResult], summary: WorkSpacesCostSummary) -> None:
        """Display analysis results using Rich CLI formatting."""

        # Summary table
        print_section("Cost Analysis Summary", emoji="💰")

        summary_table = create_table(
            title="WorkSpaces Optimization Summary",
            columns=[
                {"header": "Metric", "style": "cyan"},
                {"header": "Count", "style": "green bold"},
                {"header": "Monthly Cost", "style": "red"},
                {"header": "Annual Cost", "style": "red bold"},
            ],
        )

        summary_table.add_row(
            "Total WorkSpaces",
            str(summary.total_workspaces),
            format_cost(summary.total_monthly_cost),
            format_cost(summary.total_monthly_cost * 12),
        )

        summary_table.add_row(
            f"Unused WorkSpaces (>{self.unused_threshold_days} days)",
            str(summary.unused_workspaces),
            format_cost(summary.unused_monthly_cost),
            format_cost(summary.potential_annual_savings),
        )

        summary_table.add_row(
            "🎯 Potential Savings",
            f"{summary.unused_workspaces} WorkSpaces",
            format_cost(summary.unused_monthly_cost),
            format_cost(summary.potential_annual_savings),
        )

        console.print(summary_table)

        # Achievement analysis
        if summary.target_achievement_rate >= 80:
            print_success(
                f"🎯 Target Achievement: {summary.target_achievement_rate:.1f}% of ${self.target_annual_savings:,.0f} annual savings target"
            )
        else:
            print_warning(
                f"📊 Analysis: {summary.target_achievement_rate:.1f}% of ${self.target_annual_savings:,.0f} annual savings target"
            )

        # Detailed unused WorkSpaces
        unused_results = [r for r in results if r.is_unused]
        if unused_results:
            print_warning(f"⚠ Found {len(unused_results)} unused WorkSpaces:")

            unused_table = create_table(
                title="Unused WorkSpaces Details",
                columns=[
                    {"header": "WorkSpace ID", "style": "cyan", "max_width": 20},
                    {"header": "Username", "style": "blue", "max_width": 15},
                    {"header": "Days Unused", "style": "yellow"},
                    {"header": "Running Mode", "style": "green"},
                    {"header": "Monthly Cost", "style": "red"},
                    {"header": "State", "style": "magenta"},
                ],
            )

            # Show first 10 for readability
            for ws in unused_results[:10]:
                unused_table.add_row(
                    ws.workspace_id,
                    ws.username,
                    str(ws.days_since_connection),
                    ws.running_mode,
                    format_cost(ws.monthly_cost),
                    ws.state,
                )

            console.print(unused_table)

            if len(unused_results) > 10:
                console.print(f"[dim]... and {len(unused_results) - 10} more unused WorkSpaces[/dim]")

    def export_results(
        self,
        results: List[WorkSpaceAnalysisResult],
        summary: WorkSpacesCostSummary,
        output_format: str = "json",
        output_file: Optional[str] = None,
    ) -> str:
        """Export analysis results in specified format."""

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"./tmp/workspaces_analysis_{timestamp}.{output_format}"

        export_data = {
            "summary": summary.to_dict(),
            "workspaces": [result.to_dict() for result in results],
            "metadata": {
                "analysis_timestamp": summary.analysis_timestamp,
                "profile": self.profile,
                "target_savings": self.target_annual_savings,
                "version": "latest version",
            },
        }

        if output_format.lower() == "json":
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
        elif output_format.lower() == "csv":
            import csv

            with open(output_file, "w", newline="") as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
                    writer.writeheader()
                    for result in results:
                        writer.writerow(result.to_dict())

        print_success(f"Analysis results exported to: {output_file}")
        return output_file

    def export_markdown(
        self, results: List[WorkSpaceAnalysisResult], summary: WorkSpacesCostSummary, output_file: str
    ) -> str:
        """
        Export WorkSpaces analysis to GitHub-flavored Markdown.

        Args:
            results: List of WorkSpace analysis results
            summary: Cost summary object
            output_file: Path to .md output file

        Returns:
            Path to created markdown file
        """
        from .markdown_exporter import export_dataframe_to_markdown
        import pandas as pd

        # Convert results to DataFrame
        df = pd.DataFrame([result.to_dict() for result in results])

        # Calculate summary metrics
        summary_metrics = {
            "Total WorkSpaces": summary.total_workspaces,
            "CRITICAL Tier (W1-W7: 100-105)": len(df[df["total_score"] >= 100]) if "total_score" in df.columns else 0,
            "HIGH Tier (W1-W7: 95-99)": len(df[(df["total_score"] >= 95) & (df["total_score"] < 100)])
            if "total_score" in df.columns
            else 0,
            "Unencrypted WorkSpaces (W7)": len(df[df.get("w7_score", pd.Series([0] * len(df))) == 5])
            if "w7_score" in df.columns
            else 0,
            "Estimated Monthly Savings": f"${summary.unused_monthly_cost:.2f}",
            "Estimated Annual Savings": f"${summary.potential_annual_savings:.2f}",
        }

        # Generate recommendations
        recommendations = [
            f"Review {summary.unused_workspaces} unused WorkSpaces (>30 days idle)",
            f"Encrypt unencrypted WorkSpaces (W7 compliance)",
            "Implement AutoStop for ALWAYS_ON candidates (W4 signal)",
            f"Target achievement rate: {summary.target_achievement_rate:.1f}%",
        ]

        # Export to markdown
        export_dataframe_to_markdown(
            df=df,
            output_file=output_file,
            title="WorkSpaces Optimization Analysis Report",
            summary_metrics=summary_metrics,
            recommendations=recommendations,
        )
        logger.info(f"Markdown export completed: {output_file}")
        return output_file

    def cleanup_unused_workspaces(
        self, unused_results: List[WorkSpaceAnalysisResult], dry_run: bool = True, confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Cleanup unused WorkSpaces with enterprise safety controls.

        Args:
            unused_results: List of unused WorkSpaces to cleanup
            dry_run: Safety flag for preview mode
            confirm: Skip confirmation prompts

        Returns:
            Cleanup operation results
        """
        print_header("WorkSpaces Cleanup Operation", "🚨 HIGH-RISK OPERATION")

        if not unused_results:
            print_info("✅ No unused WorkSpaces found for cleanup")
            return {"status": "no_action", "deleted": 0, "message": "No unused WorkSpaces"}

        # Safety validation
        cleanup_candidates = [
            ws
            for ws in unused_results
            if ws.state in ["AVAILABLE", "STOPPED"] and ws.days_since_connection >= self.unused_threshold_days
        ]

        if not cleanup_candidates:
            print_warning("⚠ No WorkSpaces meet the safety criteria for cleanup")
            return {"status": "no_candidates", "deleted": 0, "message": "No cleanup candidates"}

        # Display cleanup preview using print_section for sub-operation
        print_section("Cleanup Operation Preview", emoji="🗑️")

        cleanup_table = create_table(
            title=f"Cleanup Candidates ({len(cleanup_candidates)} WorkSpaces)",
            columns=[
                {"header": "WorkSpace ID", "style": "cyan"},
                {"header": "Username", "style": "blue"},
                {"header": "Days Unused", "style": "yellow"},
                {"header": "Monthly Cost", "style": "red"},
                {"header": "State", "style": "magenta"},
            ],
        )

        total_cleanup_savings = 0.0
        for ws in cleanup_candidates:
            cleanup_table.add_row(
                ws.workspace_id, ws.username, str(ws.days_since_connection), format_cost(ws.monthly_cost), ws.state
            )
            total_cleanup_savings += ws.monthly_cost

        console.print(cleanup_table)

        annual_cleanup_savings = total_cleanup_savings * 12
        print_info(
            f"💰 Cleanup savings: {format_cost(total_cleanup_savings)}/month, {format_cost(annual_cleanup_savings)}/year"
        )

        if dry_run:
            print_info("🔍 DRY-RUN: Preview mode - no WorkSpaces will be deleted")
            return {
                "status": "dry_run",
                "candidates": len(cleanup_candidates),
                "monthly_savings": total_cleanup_savings,
                "annual_savings": annual_cleanup_savings,
            }

        # Confirmation required for actual cleanup
        if not confirm:
            print_warning("🚨 DANGER: This will permanently delete WorkSpaces and all user data")
            print_warning(f"About to delete {len(cleanup_candidates)} WorkSpaces")

            if not console.input("Type 'DELETE' to confirm: ") == "DELETE":
                print_error("Cleanup cancelled - confirmation failed")
                return {"status": "cancelled", "deleted": 0}

        # Perform cleanup
        print_warning("🗑 Starting WorkSpaces cleanup...")
        ws_client = self.session.client("workspaces")

        deleted_count = 0
        failed_count = 0
        cleanup_results = []

        for ws in cleanup_candidates:
            try:
                print_info(f"Deleting: {ws.workspace_id} ({ws.username})")

                ws_client.terminate_workspaces(TerminateWorkspaceRequests=[{"WorkspaceId": ws.workspace_id}])

                deleted_count += 1
                cleanup_results.append(
                    {
                        "workspace_id": ws.workspace_id,
                        "username": ws.username,
                        "status": "deleted",
                        "monthly_saving": ws.monthly_cost,
                    }
                )

                print_success(f"✅ Deleted: {ws.workspace_id}")

            except ClientError as e:
                failed_count += 1
                cleanup_results.append(
                    {"workspace_id": ws.workspace_id, "username": ws.username, "status": "failed", "error": str(e)}
                )
                print_error(f"❌ Failed: {ws.workspace_id} - {e}")

        # Summary
        actual_monthly_savings = sum(
            result.get("monthly_saving", 0) for result in cleanup_results if result["status"] == "deleted"
        )
        actual_annual_savings = actual_monthly_savings * 12

        print_success(f"🔄 Cleanup complete: {deleted_count} deleted, {failed_count} failed")
        print_success(
            f"💰 Realized savings: {format_cost(actual_monthly_savings)}/month, {format_cost(actual_annual_savings)}/year"
        )

        return {
            "status": "completed",
            "deleted": deleted_count,
            "failed": failed_count,
            "monthly_savings": actual_monthly_savings,
            "annual_savings": actual_annual_savings,
            "details": cleanup_results,
        }


def analyze_workspaces(
    profile: Optional[str] = None,
    unused_days: int = 90,
    analysis_days: int = 30,
    output_format: str = "json",
    output_file: Optional[str] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    WorkSpaces analysis wrapper for CLI and notebook integration.

    Args:
        profile: AWS profile to use
        unused_days: Days threshold for unused detection
        analysis_days: Period for usage analysis
        output_format: Export format (json, csv)
        output_file: Optional output file path
        dry_run: Safety flag for preview mode

    Returns:
        Analysis results with cost optimization recommendations
    """
    try:
        # Initialize variables to prevent scope errors
        results = []
        summary = None
        export_file = None

        analyzer = WorkSpacesCostAnalyzer(profile=profile)
        results, summary = analyzer.analyze_workspaces(
            unused_days=unused_days, analysis_days=analysis_days, dry_run=dry_run
        )

        # Display results
        analyzer.display_analysis_results(results, summary)

        # Export if requested
        export_file = None
        if output_file or output_format:
            export_file = analyzer.export_results(results, summary, output_format, output_file)

        # Return comprehensive results
        if summary is not None:
            return {
                "summary": summary.to_dict(),
                "workspaces": [result.to_dict() for result in results],
                "export_file": export_file,
                "achievement_rate": summary.target_achievement_rate,
                "status": "success",
            }
        else:
            return {
                "summary": {"error": "Analysis failed before completion"},
                "workspaces": [],
                "export_file": None,
                "achievement_rate": 0,
                "status": "partial_failure",
            }

    except Exception as e:
        print_error(f"WorkSpaces analysis failed: {e}")
        return {
            "error": str(e),
            "status": "failed",
            "summary": {"error": str(e)},
            "workspaces": [],
            "export_file": None,
            "achievement_rate": 0,
        }


def analyze_workspaces_costs(
    input_file: str,
    output_file: str,
    management_profile: str,
    billing_profile: str,
    operational_profile: Optional[str] = None,
    enable_organizations: bool = True,
    enable_cost: bool = True,
    enable_activity: bool = False,
    include_12month_cost: bool = True,
    include_volume_encryption: bool = True,
) -> pd.DataFrame:
    """
    CLI and notebook entry point for WorkSpaces cost analysis.

    Architecture: Matches EC2 analyzer pattern exactly (enterprise DRY compliance)

    This function provides a unified entry point for WorkSpaces cost analysis,
    mirroring the architecture pattern used in analyze_ec2_costs(). It orchestrates
    the complete enrichment pipeline: Organizations metadata → WorkSpaces context →
    Volume encryption → Cost Explorer → CloudTrail activity → Rich CLI display →
    Multi-sheet Excel export.

    Usage:
        from runbooks.finops.workspaces_analyzer import analyze_workspaces_costs

        # Minimal usage (default enrichment)
        df = analyze_workspaces_costs(
            input_file='data/resources-ec2-workspaces.xlsx',
            output_file='data/workspaces-enriched-analysis.xlsx',
            management_profile='management-profile',
            billing_profile='billing-profile'
        )

        # Comprehensive enrichment (with CloudTrail activity, slower)
        df = analyze_workspaces_costs(
            input_file='data/resources-ec2-workspaces.xlsx',
            output_file='data/workspaces-enriched-analysis.xlsx',
            management_profile='management-profile',
            billing_profile='billing-profile',
            operational_profile='operational-profile',
            enable_activity=True  # WARNING: Adds 60-90s execution time
        )

        # CLI integration (future)
        runbooks finops analyze-workspaces \
            --input workspaces.xlsx \
            --output analysis.xlsx \
            --management-profile mgmt \
            --billing-profile billing

    Args:
        input_file: Excel file with WorkSpaces inventory (sheet: 'workspaces')
                    Source: runbooks inventory collect-workspaces
        output_file: Output Excel file path (multi-sheet workbook)
        management_profile: AWS profile for Organizations metadata enrichment
                            Required for: Organizations API (6 columns)
        billing_profile: AWS profile for Cost Explorer 12-month cost data
                         Required for: Cost Explorer API (historical costs)
        operational_profile: AWS profile for WorkSpaces/EC2 operations
                             Required for: WorkSpaces DescribeWorkspaces, EC2 DescribeVolumes
                             Default: Uses management_profile if not specified
        enable_organizations: Enable Organizations metadata enrichment
                              Adds 6 columns: account_name, account_email, wbs_code,
                              cost_group, technical_lead, account_owner
                              Default: True (recommended for multi-account analysis)
        enable_cost: Enable Cost Explorer enrichment
                     Adds 12-month historical cost data
                     Default: True (essential for cost analysis)
        enable_activity: Enable CloudTrail activity enrichment
                         Adds 4 columns: last_activity_date, days_since_activity,
                         event_count, is_idle
                         WARNING: Slow (60-90s execution time)
                         Default: False (disabled for performance)
        include_12month_cost: Include 12-month cost breakdown in enrichment
                              Requires: enable_cost=True
                              Default: True (recommended for trend analysis)
        include_volume_encryption: Include EBS volume encryption status
                                    Adds 3 columns: root_volume_encrypted,
                                    user_volume_encrypted, encryption_status
                                    Default: True (recommended for compliance)

    Returns:
        pd.DataFrame: Enriched WorkSpaces data with all enabled enrichment stages

                      Standard columns (from inventory):
                      - WorkSpace ID, Username, Compute, Root volume, User volume,
                        Operating system, Bundle name, WorkSpace IP, Running mode,
                        Protocol, Status, Organization name

                      Enriched columns (conditional based on flags):
                      - Organizations (6 columns, if enable_organizations=True)
                      - Volume encryption (3 columns, if include_volume_encryption=True)
                      - CloudTrail activity (4 columns, if enable_activity=True)
                      - Cost data (12-month breakdown, if enable_cost=True)

    Raises:
        FileNotFoundError: If input_file does not exist
        ValueError: If input file missing required 'workspaces' sheet
        ProfileNotFound: If AWS profiles not configured in ~/.aws/config
        TokenRetrievalError: If AWS SSO tokens expired (run aws sso login)
        Exception: Generic error with comprehensive logging

    Exports:
        Multi-sheet Excel workbook via export_compute_excel():
        - Sheet 1: Enriched Data (all columns with formatting)
        - Sheet 2: Cost Summary (by account/region aggregations)
        - Sheet 3: Organizations Hierarchy (account metadata)
        - Sheet 4: Validation Metrics (enrichment success rates)

        Excel formatting:
        - Header row: Bold, colored background
        - Cost columns: Currency format ($X,XXX.XX)
        - Date columns: YYYY-MM-DD format
        - Auto-column width adjustment

    Architecture Notes:
        - DRY Compliance: Reuses export_compute_excel() from compute_reports.py
        - Pattern Consistency: Matches EC2 analyzer architecture exactly
        - Performance: Default execution ~5-10s (without CloudTrail activity)
        - Extensibility: Optional flags enable/disable enrichment stages
        - Error Handling: Comprehensive try/except with graceful fallback

    Example Output:
        Input: 50 WorkSpaces from inventory
        Enrichment: Organizations (6 cols) + Volume encryption (3 cols) + Cost (12mo)
        Output: 50 rows × ~25 columns (original + enriched)
        Excel: 4-sheet workbook with summary tables and validation metrics
        Execution time: ~5-7s (no CloudTrail), ~70s (with CloudTrail)
    """
    from pathlib import Path
    from .compute_reports import export_compute_excel
    from .base_enrichers import OrganizationsEnricher, CostExplorerEnricher, CloudTrailEnricher

    try:
        # Step 1: Initialize WorkSpaces analyzer
        print_section(f"WorkSpaces Cost Analysis: {input_file}", emoji="🖥️")
        analyzer = WorkSpacesCostAnalyzer(profile=operational_profile or management_profile)

        # Step 2: Load input file
        print_info(f"Loading WorkSpaces inventory from: {input_file}")
        if not Path(input_file).exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Read WorkSpaces data from Excel
        try:
            df = pd.read_excel(input_file, sheet_name="workspaces")
        except ValueError as e:
            raise ValueError(f"Sheet 'workspaces' not found in {input_file}") from e

        print_success(f"✅ Loaded {len(df)} WorkSpaces from inventory")
        enriched_df = df.copy()

        # Step 3: Organizations enrichment (if enabled)
        if enable_organizations:
            print_section("Organizations Enrichment", emoji="🏢")
            orgs_enricher = OrganizationsEnricher()
            enriched_df = orgs_enricher.enrich_with_organizations(
                enriched_df,
                account_id_column="AWS Account",  # WorkSpaces inventory column name
                management_profile=management_profile,
            )

        # Step 4: Volume encryption enrichment (if enabled)
        if include_volume_encryption:
            print_section("Volume Encryption Analysis", emoji="🔒")
            enriched_df = analyzer.get_volume_encryption(enriched_df)

        # Step 5: Cost Explorer enrichment (if enabled)
        if enable_cost and include_12month_cost:
            print_section("Cost Analysis (12-month trailing)", emoji="💰")
            cost_enricher = CostExplorerEnricher()

            # Get unique account IDs for Cost Explorer query
            account_ids = enriched_df["AWS Account"].unique().tolist()

            # Fetch 12-month cost breakdown (service filter: Amazon WorkSpaces)
            cost_df = cost_enricher.get_12_month_cost_breakdown(
                billing_profile=billing_profile, account_ids=account_ids, service_filter="Amazon WorkSpaces"
            )

            # Merge cost data with enriched DataFrame
            if not cost_df.empty:
                # Convert account IDs to same type for merge compatibility
                enriched_df["AWS Account"] = enriched_df["AWS Account"].astype(str)
                cost_df["account_id"] = cost_df["account_id"].astype(str)

                # Aggregate cost data by account BEFORE merging to prevent row duplication
                # Cost Explorer returns 12 months × N accounts (one row per month per account)
                # Merging directly creates duplicates (one WorkSpace row per month)
                cost_summary = (
                    cost_df.groupby("account_id")
                    .agg(
                        {
                            "cost": "sum"  # Total 12-month cost
                        }
                    )
                    .reset_index()
                )

                # Rename for clarity
                cost_summary.rename(columns={"cost": "annual_cost_12mo"}, inplace=True)

                # Calculate average monthly cost
                cost_summary["monthly_cost"] = cost_summary["annual_cost_12mo"] / 12

                # Merge aggregated cost data (one row per account - prevents duplication)
                enriched_df = enriched_df.merge(
                    cost_summary,
                    left_on="AWS Account",
                    right_on="account_id",
                    how="left",
                    suffixes=("", "_cost"),  # Avoid duplicate column conflicts
                )

                # Calculate cost trend metrics (6-month comparison)
                enriched_df = analyzer._calculate_cost_metrics(enriched_df, cost_df)

                # Keep account_id column for downstream export compatibility
                # (Don't drop it - export_compute_excel() expects it)

        # Step 6: CloudTrail activity enrichment (if enabled, WARNING: slow)
        if enable_activity:
            print_info("⚠️  CloudTrail activity analysis enabled (60-90s execution time)")
            print_section("CloudTrail Activity Analysis", emoji="📊")
            ct_enricher = CloudTrailEnricher()
            enriched_df = ct_enricher.enrich_with_activity(
                enriched_df, resource_id_column="WorkSpace ID", management_profile=management_profile, lookback_days=90
            )

        # Step 7: Display enrichment summary
        print_section("Enrichment Summary", emoji="📊")
        print_info(f"   Total WorkSpaces: {len(enriched_df)}")
        if enable_organizations:
            print_success(f"   ✅ Organizations metadata enriched")
        if include_volume_encryption:
            print_success(f"   ✅ Volume encryption status analyzed")
        if enable_cost and include_12month_cost:
            print_success(f"   ✅ 12-month cost data enriched")
        if enable_activity:
            print_success(f"   ✅ CloudTrail activity analyzed")

        # Step 8: Export to multi-sheet Excel (DRY compliance)
        print_section("Excel Export", emoji="📝")
        export_compute_excel(
            df=enriched_df,
            output_file=output_file,
            resource_type="workspaces",
            include_cost_analysis=True,
            include_recommendations=False,
            verbose=False,
        )

        print_success(f"✅ Analysis complete: {len(enriched_df)} WorkSpaces enriched")
        print_info(f"   Output: {output_file}")

        return enriched_df

    except FileNotFoundError as e:
        print_error(f"❌ Input file not found: {input_file}", exception=e)
        logger.error(f"Input file not found: {input_file}", exc_info=True)
        raise
    except Exception as e:
        print_error(f"❌ WorkSpaces analysis failed", exception=e)
        logger.error(f"WorkSpaces analysis error: {e}", exc_info=True)
        raise


# Legacy alias for backward compatibility
def analyze_workspaces_finops_24(*args, **kwargs):
    """Legacy alias for analyze_workspaces - deprecated, use analyze_workspaces instead."""
    return analyze_workspaces(*args, **kwargs)
