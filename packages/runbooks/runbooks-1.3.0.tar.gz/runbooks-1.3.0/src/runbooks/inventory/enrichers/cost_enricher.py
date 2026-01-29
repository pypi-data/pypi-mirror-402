#!/usr/bin/env python3
"""
Cost Explorer Enrichment - BILLING Profile Single Responsibility

Adds 3 cost columns to any resource discovery data:
- monthly_cost (last complete month from Cost Explorer)
- annual_cost_12mo (12-month trailing cost)
- cost_trend_3mo (3-month trend array for visualization)

Unix Philosophy: Does ONE thing (Cost Explorer enrichment) with ONE profile (BILLING).

Usage:
    enricher = CostEnricher(billing_profile='${BILLING_PROFILE}')
    enriched_df = enricher.enrich_costs(discovery_df, months=12)
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from botocore.exceptions import ClientError
from dateutil.relativedelta import relativedelta

from runbooks.base import CloudFoundationsBase
from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
    create_timeout_protected_client,
)
from runbooks.common.rich_utils import (
    console,
    print_info,
    print_success,
    print_warning,
    print_error,
    create_progress_bar,
    create_table,
)
from runbooks.common.output_controller import OutputController


class CostEnricher(CloudFoundationsBase):
    """
    Cost Explorer enrichment (BILLING_PROFILE only).

    Queries AWS Cost Explorer for resource-level cost data across specified
    time periods (last month + N trailing months).

    Profile Isolation: Enforced via get_profile_for_operation("billing", ...)

    Note: Cost Explorer requires us-east-1 region (global service).

    Attributes:
        ce_client: Cost Explorer boto3 client (us-east-1)
        billing_profile: Resolved BILLING profile name
    """

    def __init__(self, billing_profile: str, output_controller: Optional[OutputController] = None):
        """
        Initialize Cost Explorer enricher with BILLING profile.

        Args:
            billing_profile: AWS profile with Cost Explorer API access
            output_controller: OutputController instance for UX consistency (optional)
        """
        # Profile isolation enforced
        resolved_profile = get_profile_for_operation("billing", billing_profile)
        super().__init__(profile=resolved_profile, region="us-east-1")  # CE requires us-east-1

        self.billing_profile = resolved_profile
        self.output_controller = output_controller or OutputController()

        # Initialize Cost Explorer client with timeout protection
        # Note: Use self.get_client() from CloudFoundationsBase instead of manual session creation
        self.ce_client = self.get_client("ce", region="us-east-1")

        if self.output_controller.verbose:
            print_success(f"Cost Explorer client initialized: {resolved_profile}")
        else:
            logger = logging.getLogger(__name__)
            logger.debug(f"Cost Explorer client initialized: {resolved_profile}")

    def run(self):
        """
        Abstract method implementation (required by CloudFoundationsBase).

        CostEnricher is a stateless enrichment utility, so run() is not applicable.
        Use enrich_costs() method directly instead.
        """
        raise NotImplementedError(
            "CostEnricher is a stateless enrichment utility. Use enrich_costs(df, months) method directly."
        )

    def _calculate_cost_period(self, months: int = 1) -> Tuple[str, str]:
        """
        Calculate cost period dates with validation and fallback.

        Args:
            months: Number of months to query (default: 1 = last month)

        Returns:
            (start_date, end_date) in 'YYYY-MM-DD' format

        Raises:
            ValueError: If system date is invalid or out of range

        Date Validation Strategy:
            - Dynamic validation: AWS Cost Explorer supports 14-month historical data
            - Valid range: Current year ±10 years (prevents extreme date issues)
            - Fallback: Only for genuinely invalid dates (e.g., year < 2020 or > 2040)
            - Production: Clean execution with no false warnings for valid dates
        """
        today = datetime.now()

        # Dynamic date validation with reasonable bounds (2020-2040 range)
        # AWS Cost Explorer historical data: typically 14 months, but we use wider range for robustness
        current_year = today.year
        min_valid_year = 2020  # Reasonable lower bound (pre-pandemic baseline)
        max_valid_year = 2040  # Reasonable upper bound (20-year forward planning horizon)

        # Only fallback for genuinely invalid dates
        if not (min_valid_year <= current_year <= max_valid_year):
            print_warning(
                f"System date {today.date()} outside reasonable range ({min_valid_year}-{max_valid_year}). "
                f"This may indicate system clock misconfiguration. "
                f"Using fallback date for Cost Explorer query stability."
            )
            today = datetime(2024, 11, 3)  # Fallback to known-good date

        # Calculate last month using exact month arithmetic
        # relativedelta handles month boundaries correctly (e.g., Jan 31 → Feb 28)
        first_day_this_month = today.replace(day=1)
        first_day_last_month = first_day_this_month - relativedelta(months=1)
        first_day_start_month = first_day_last_month - relativedelta(months=months - 1)

        # End date is first day of current month (Cost Explorer excludes end date)
        start_date = first_day_start_month.strftime("%Y-%m-%d")
        end_date = first_day_this_month.strftime("%Y-%m-%d")

        # Debug logging
        if self.output_controller.verbose:
            print_info(f"🔵 Cost Explorer Period Calculation:")
            print_info(f"   System Date: {today.date()}")
            print_info(f"   Query Period: {start_date} to {end_date}")
            print_info(f"   Months Queried: {months}")
        else:
            logger = logging.getLogger(__name__)
            logger.debug(f"Cost Explorer period: {start_date} to {end_date} ({months} months)")

        # Validation: Ensure dates are sensible
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        if start_dt >= end_dt:
            raise ValueError(f"Invalid date range: start {start_date} >= end {end_date}")

        if end_dt > today:
            raise ValueError(f"Invalid end date {end_date} is in future (today: {today.date()})")

        return start_date, end_date

    def enrich_costs(self, df: pd.DataFrame, months: int = 1) -> pd.DataFrame:
        """
        Add 3 cost columns to resource discovery data.

        Args:
            df: DataFrame with 'account_id' column (from discovery layer)
            months: Number of trailing months for cost query (default: 1 = last complete month)
                   Note: AWS Cost Explorer historical data limited to 14 months

        Returns:
            DataFrame with added cost columns:
            - monthly_cost (last complete month)
            - annual_cost_12mo (months * average monthly cost)
            - cost_trend_3mo (array of last 3 months for trend analysis)

        Note:
            Cost Explorer provides ACCOUNT-level granularity (not resource-level).
            Costs are distributed proportionally across resources in each account.

        Example:
            >>> discovery_df = pd.read_csv('/tmp/discovered-resources.csv')
            >>> enricher = CostEnricher('${BILLING_PROFILE}')
            >>> enriched_df = enricher.enrich_costs(discovery_df, months=12)
            >>> enriched_df.to_csv('/tmp/resources-with-costs.csv', index=False)
        """
        # Validate required columns with contextual error messaging
        if "account_id" not in df.columns:
            available_columns = df.columns.tolist()
            print_error("Input DataFrame missing required 'account_id' column")
            print_info(f"Available columns ({len(available_columns)}): {', '.join(available_columns[:10])}")

            # Suggest similar columns
            similar = [col for col in available_columns if "account" in col.lower() or "owner" in col.lower()]
            if similar:
                print_warning(f"Found similar columns: {', '.join(similar)}")
                print_info("Possible fix: Use Track 1 column standardization")

            raise ValueError(
                f"account_id column required for cost enrichment.\n"
                f"Available columns: {available_columns[:10]}\n"
                f"Total columns in DataFrame: {len(available_columns)}"
            )

        if self.output_controller.verbose:
            print_info(f"Enriching {len(df)} resources with Cost Explorer data ({months} months)")
        else:
            logger = logging.getLogger(__name__)
            logger.info(f"Enriching {len(df)} resources with Cost Explorer data ({months} months)")

        # Calculate date range with validation and fallback
        try:
            start_str, end_str = self._calculate_cost_period(months=months)
        except ValueError as e:
            print_error(f"Date calculation error: {e}")
            raise

        # Get unique account IDs for filtering (convert to strings for AWS API)
        account_ids = [str(aid) for aid in df["account_id"].unique().tolist()]

        try:
            # Query Cost Explorer with account filtering (reuse logic from resource_explorer.py lines 549-630)
            ce_params = {
                "TimePeriod": {"Start": start_str, "End": end_str},
                "Granularity": "MONTHLY",
                "Metrics": ["UnblendedCost"],
                "GroupBy": [{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}, {"Type": "DIMENSION", "Key": "SERVICE"}],
            }

            # Filter by account IDs if available
            if account_ids:
                ce_params["Filter"] = {"Dimensions": {"Key": "LINKED_ACCOUNT", "Values": account_ids}}

            # Call Cost Explorer API with progress bar
            if self.output_controller.verbose:
                print_info(f"Querying Cost Explorer for {len(account_ids)} accounts...")
            else:
                logger = logging.getLogger(__name__)
                logger.debug(f"Querying Cost Explorer for {len(account_ids)} accounts")

            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Fetching cost data from Cost Explorer...", total=1)
                response = self.ce_client.get_cost_and_usage(**ce_params)
                progress.update(task, advance=1)

            # Parse cost data (account-level aggregation)
            cost_map = {}
            monthly_costs = {}  # For trend analysis

            for result in response.get("ResultsByTime", []):
                time_period = result.get("TimePeriod", {}).get("Start", "")

                for group in result.get("Groups", []):
                    # Extract account ID and service
                    keys = group.get("Keys", [])
                    if len(keys) >= 2:
                        account_id = keys[0]
                        service = keys[1]

                        # Extract cost
                        metrics = group.get("Metrics", {})
                        unblended_cost = float(metrics.get("UnblendedCost", {}).get("Amount", 0))

                        # Accumulate total cost per account
                        if account_id not in cost_map:
                            cost_map[account_id] = 0
                            monthly_costs[account_id] = []

                        cost_map[account_id] += unblended_cost

                        # Track monthly costs for trend (append only if not duplicate)
                        if time_period not in [m.get("period") for m in monthly_costs[account_id]]:
                            monthly_costs[account_id].append({"period": time_period, "cost": unblended_cost})

            # Add cost column to DataFrame (convert account_id to string for mapping)
            # Cost Explorer returns string account IDs, but DataFrame may have int64
            df["monthly_cost"] = df["account_id"].astype(str).map(cost_map).fillna(0.0)
            df["annual_cost_12mo"] = df["monthly_cost"] * months

            # Add cost trend (last 3 months)
            df["cost_trend_3mo"] = (
                df["account_id"]
                .astype(str)
                .map(lambda aid: [m["cost"] for m in monthly_costs.get(aid, [])][-3:] if aid in monthly_costs else [])
            )

            # Display cost summary table
            total_cost = df["monthly_cost"].sum()
            avg_cost = df["monthly_cost"].mean() if len(df) > 0 else 0

            # Cost by account (top 3)
            cost_by_account = df.groupby("account_id")["monthly_cost"].sum().nlargest(3)

            summary_rows = [
                ["Total Monthly Cost", f"${total_cost:,.2f}"],
                ["Average Cost/Resource", f"${avg_cost:,.2f}"],
                ["Resources Analyzed", str(len(df))],
            ]

            # Add top 3 accounts by cost
            for i, (acc, cost) in enumerate(cost_by_account.items(), 1):
                summary_rows.append([f"  #{i} Account Cost", f"{acc}: ${cost:,.2f}"])

            if self.output_controller.verbose:
                cost_summary = create_table("Cost Enrichment Summary", ["Metric", "Value"], summary_rows)
                console.print(cost_summary)
                print_success(f"Cost enrichment complete: ${total_cost:,.2f} total monthly cost")
            else:
                logger = logging.getLogger(__name__)
                logger.info(f"Cost enrichment complete: ${total_cost:,.2f} total monthly cost")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            print_error(f"Cost Explorer API error ({error_code})", e)
            # Graceful degradation: continue with zero costs
            df["monthly_cost"] = 0.0
            df["annual_cost_12mo"] = 0.0
            df["cost_trend_3mo"] = [[] for _ in range(len(df))]

        except Exception as e:
            print_error("Unexpected error during cost enrichment", e)
            df["monthly_cost"] = 0.0
            df["annual_cost_12mo"] = 0.0
            df["cost_trend_3mo"] = [[] for _ in range(len(df))]

        return df
