#!/usr/bin/env python3
"""
Organizations Metadata Enrichment - MANAGEMENT Profile Single Responsibility

Adds 10 Organizations columns to any resource discovery data:
- account_name, account_email (from Organizations DescribeAccount)
- account_status, account_join_method, account_join_date (Phase 0 Manager Correction)
- wbs_code, cost_group (TIER 1 business metadata)
- technical_lead, account_owner (TIER 2 governance metadata)
- organizational_unit (from Organizations ListParents)

Unix Philosophy: Does ONE thing (Organizations enrichment) with ONE profile (MANAGEMENT).

Usage:
    enricher = OrganizationsEnricher(management_profile='${MANAGEMENT_PROFILE}')
    enriched_df = enricher.enrich_dataframe(discovery_df)
"""

import pandas as pd
import logging
from typing import Dict, List, Optional

from runbooks.base import CloudFoundationsBase
from runbooks.common.profile_utils import get_profile_for_operation
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
from runbooks.inventory.organizations_utils import discover_organization_accounts


class OrganizationsEnricher(CloudFoundationsBase):
    """
    Organizations metadata enrichment (MANAGEMENT_PROFILE only).

    Enriches resource discovery data with 10 Organizations columns by mapping
    account_id to Organizations metadata via discover_organization_accounts().

    Profile Isolation: Enforced via get_profile_for_operation("management", ...)

    Attributes:
        accounts (List[Dict]): Organization accounts with TIER 1-4 metadata
        account_lookup (Dict[str, Dict]): Fast account_id → metadata mapping
        error (Optional[str]): Organizations API error if unavailable
    """

    def __init__(
        self,
        management_profile: str,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize Organizations enricher with MANAGEMENT profile.

        Args:
            management_profile: AWS profile with Organizations API access
            region: AWS region for global services (default: ap-southeast-2)
            output_controller: OutputController instance for UX consistency (optional)
        """
        # Profile isolation enforced
        resolved_profile = get_profile_for_operation("management", management_profile)
        super().__init__(profile=resolved_profile, region=region)

        self.management_profile = resolved_profile
        self.region = region
        self.output_controller = output_controller or OutputController()

        # Discover organization accounts (reuse existing pattern from enrich_ec2.py)
        self.accounts, self.error = discover_organization_accounts(resolved_profile, region)

        if self.error:
            if self.output_controller.verbose:
                print_warning(f"Organizations unavailable: {self.error}")
                print_info("Enrichment will use account IDs only (no Organizations metadata)")
            else:
                logger = logging.getLogger(__name__)
                logger.debug(f"Organizations unavailable: {self.error}")

        # Create account lookup dict for fast access
        self.account_lookup = {acc["id"]: acc for acc in self.accounts}

        if self.output_controller.verbose:
            print_success(f"Initialized with {len(self.accounts)} accounts")
        else:
            logger = logging.getLogger(__name__)
            logger.debug(f"Organizations enricher initialized with {len(self.accounts)} accounts")

    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add 10 Organizations columns to resource discovery data.

        Args:
            df: DataFrame with 'account_id' column (from discovery layer)

        Returns:
            DataFrame with added Organizations columns:
            - account_name, account_email
            - account_status, account_join_method, account_join_date (Phase 0 Manager Correction)
            - wbs_code, cost_group
            - technical_lead, account_owner
            - organizational_unit

        Raises:
            ValueError: If input DataFrame missing 'account_id' column

        Example:
            >>> discovery_df = pd.read_csv('/tmp/discovered-resources.csv')
            >>> enricher = OrganizationsEnricher('${MANAGEMENT_PROFILE}')
            >>> enriched_df = enricher.enrich_dataframe(discovery_df)
            >>> enriched_df.to_csv('/tmp/resources-with-orgs.csv', index=False)
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
                f"account_id column required for Organizations enrichment.\n"
                f"Available columns: {available_columns[:10]}\n"
                f"Total columns in DataFrame: {len(available_columns)}"
            )

        # Initialize 10 Organizations columns (Phase 0 Manager Correction: +3 fields)
        orgs_columns = {
            "account_name": "N/A",
            "account_email": "N/A",
            "account_status": "N/A",  # Phase 0: ACTIVE/SUSPENDED/PENDING_CLOSURE
            "account_join_method": "N/A",  # Phase 0: INVITED/CREATED/UNKNOWN
            "account_join_date": "N/A",  # Phase 0: Account creation/join timestamp
            "wbs_code": "N/A",
            "cost_group": "N/A",
            "technical_lead": "N/A",
            "account_owner": "N/A",
            "organizational_unit": "N/A",
        }

        for col, default in orgs_columns.items():
            df[col] = default

        # Enrich with actual data (reuse pattern from enrich_ec2.py lines 176-196)
        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Enriching with Organizations...", total=len(df))

            for idx, row in df.iterrows():
                account_id = str(row.get("account_id", "")).strip()

                if account_id in self.account_lookup:
                    acc = self.account_lookup[account_id]
                    df.at[idx, "account_name"] = acc.get("name", "N/A")
                    df.at[idx, "account_email"] = acc.get("email", "N/A")
                    # Phase 0 Manager Correction: Add 3 new fields
                    df.at[idx, "account_status"] = acc.get("status", "N/A")
                    df.at[idx, "account_join_method"] = acc.get("joined_method", "N/A")
                    # Format timestamp for readability (ISO format or N/A)
                    join_ts = acc.get("joined_timestamp", "N/A")
                    df.at[idx, "account_join_date"] = str(join_ts) if join_ts != "N/A" else "N/A"
                    # Existing TIER 1-2 metadata
                    df.at[idx, "wbs_code"] = acc.get("wbs_code", "N/A")
                    df.at[idx, "cost_group"] = acc.get("cost_group", "N/A")
                    df.at[idx, "technical_lead"] = acc.get("technical_lead", "N/A")
                    df.at[idx, "account_owner"] = acc.get("account_owner", "N/A")
                    df.at[idx, "organizational_unit"] = acc.get("organizational_unit", "N/A")

                progress.update(task, advance=1)

        # Calculate enrichment statistics
        enriched_count = (df["account_name"] != "N/A").sum()
        unique_accounts = df["account_id"].nunique()

        # Display enrichment results table
        if self.output_controller.verbose:
            enrichment_summary = create_table(
                "Organizations Enrichment Results",
                ["Metric", "Value"],
                [
                    ["Total Resources", str(len(df))],
                    ["Resources Enriched", str(enriched_count)],
                    ["Enrichment Rate", f"{(enriched_count / len(df) * 100):.1f}%"],
                    ["New Columns Added", "10"],
                    ["Unique Accounts", str(unique_accounts)],
                ],
            )
            console.print(enrichment_summary)
        else:
            logger = logging.getLogger(__name__)
            logger.info(
                f"Organizations enrichment: {enriched_count}/{len(df)} resources "
                f"({(enriched_count / len(df) * 100):.1f}%) across {unique_accounts} accounts"
            )

        return df

    def run(self):
        """
        Run method required by CloudFoundationsBase.

        For OrganizationsEnricher, this returns initialization status.
        Primary usage is via enrich_dataframe() method.

        Returns:
            CloudFoundationsResult with initialization status
        """
        from runbooks.base import CloudFoundationsResult
        from datetime import datetime

        return CloudFoundationsResult(
            timestamp=datetime.now(),
            success=True,
            message=f"OrganizationsEnricher initialized with {len(self.accounts)} accounts",
            data={
                "account_count": len(self.accounts),
                "management_profile": self.management_profile,
                "region": self.region,
                "organizations_available": self.error is None,
            },
        )
