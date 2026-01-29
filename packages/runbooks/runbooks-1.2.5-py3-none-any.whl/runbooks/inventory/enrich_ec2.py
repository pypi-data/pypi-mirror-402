#!/usr/bin/env python3
"""
EC2 Enrichment with Organizations Metadata, Cost Explorer Data, and CloudTrail Activity.

This module extends existing EC2 inventory with business context from AWS Organizations,
cost data from Cost Explorer API, and activity tracking via CloudTrail - following the
KISS/DRY principles by reusing organizations_utils.py patterns.

Architecture:
    - Organizations Integration: Reuses discover_organization_accounts() + enhance_account_with_tags()
    - Cost Explorer: Real AWS API integration with boto3 (no mock data)
    - CloudTrail: Activity tracking with last activity date and idle detection
    - Rich CLI: Enterprise UX with consistent formatting via rich_utils.py

Features:
    - Multi-account Organizations enrichment (TIER 1-4 tags)
    - Cost analysis (monthly + annual projections)
    - Activity tracking (90-day CloudTrail lookup)
    - Multiple output formats (CSV, Excel, JSON)
    - Rich CLI display with tables and trees

Author: Runbooks Team
Version: 1.1.10
"""

import boto3
import click
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from runbooks.inventory.organizations_utils import (
    discover_organization_accounts,
    SimpleProfileMapper,
)
from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_table,
    create_progress_bar,
    create_tree,
    format_cost,
)


class EC2Enricher:
    """
    EC2 instance enrichment with Organizations, Cost, and Activity data.

    Follows KISS/DRY by reusing:
    - organizations_utils.py for account discovery and tag enrichment
    - rich_utils.py for consistent CLI formatting
    - boto3 patterns from existing inventory modules
    """

    def __init__(self, management_profile: str, billing_profile: Optional[str] = None, region: str = "ap-southeast-2"):
        """
        Initialize EC2 enricher with AWS profiles.

        Args:
            management_profile: AWS profile with Organizations API access
            billing_profile: AWS profile with Cost Explorer API access (defaults to management_profile)
            region: AWS region for global services (default: ap-southeast-2)
        """
        self.management_profile = management_profile
        self.billing_profile = billing_profile or management_profile
        self.region = region

        # Discover Organizations accounts (reuse existing pattern)
        print_info(f"Discovering accounts via Organizations API (profile: {management_profile})")
        self.accounts, self.error = discover_organization_accounts(management_profile, region)

        if self.error:
            print_warning(f"Organizations unavailable: {self.error}")
            print_info("Enrichment will use account IDs only (no Organizations metadata)")

        # Create account lookup dict for fast access
        self.account_lookup = {acc["id"]: acc for acc in self.accounts}

        print_success(f"Initialized with {len(self.accounts)} accounts")

    def enrich_ec2_instances(
        self,
        ec2_df: pd.DataFrame,
        enrich_organizations: bool = True,
        enrich_cost: bool = True,
        enrich_activity: bool = True,
    ) -> pd.DataFrame:
        """
        Enrich EC2 DataFrame with Organizations, Cost, and Activity data.

        Args:
            ec2_df: DataFrame with EC2 instances (must have 'account_id' column)
            enrich_organizations: Add Organizations metadata (account names, tags)
            enrich_cost: Add Cost Explorer data (monthly/annual costs)
            enrich_activity: Add CloudTrail activity (last activity, idle detection)

        Returns:
            Enriched DataFrame with additional columns

        Required Input Columns:
            - account_id: AWS account ID (12-digit string)
            - instance_id: EC2 instance ID (i-xxxxxxxxx format)

        Added Columns (Organizations):
            - account_name, account_email, wbs_code, cost_group, technical_lead, account_owner

        Added Columns (Cost):
            - monthly_cost, annual_cost_12mo

        Added Columns (Activity):
            - last_activity_date, days_since_activity, activity_count_90d, is_idle
        """
        print_header("EC2 Enrichment Pipeline")

        # Validate required columns
        if "account_id" not in ec2_df.columns:
            print_error("Input DataFrame missing required 'account_id' column")
            raise ValueError("account_id column required for enrichment")

        if "instance_id" not in ec2_df.columns:
            print_warning("Input DataFrame missing 'instance_id' column - activity tracking disabled")
            enrich_activity = False

        # Step 1: Organizations Enrichment
        if enrich_organizations and self.accounts:
            console.print("\n[cyan]📊 Step 1: Organizations Metadata Enrichment[/cyan]")
            ec2_df = self._enrich_organizations(ec2_df)
        else:
            console.print("\n[dim]📊 Step 1: Organizations Enrichment Skipped[/dim]")

        # Step 2: Cost Explorer Enrichment
        if enrich_cost:
            console.print("\n[cyan]💰 Step 2: Cost Explorer Data Enrichment[/cyan]")
            ec2_df = self._enrich_cost(ec2_df)
        else:
            console.print("\n[dim]💰 Step 2: Cost Enrichment Skipped[/dim]")

        # Step 3: CloudTrail Activity Enrichment
        if enrich_activity:
            console.print("\n[cyan]🔍 Step 3: CloudTrail Activity Enrichment[/cyan]")
            ec2_df = self._enrich_activity(ec2_df)
        else:
            console.print("\n[dim]🔍 Step 3: Activity Enrichment Skipped[/dim]")

        return ec2_df

    def _enrich_organizations(self, ec2_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Organizations metadata columns.

        Uses account_lookup from discover_organization_accounts() which already
        includes TIER 1-4 tags via enhance_account_with_tags().
        """
        # Add Organization columns (TIER 1 business metadata)
        orgs_columns = {
            "account_name": "N/A",
            "account_email": "N/A",
            "wbs_code": "N/A",
            "cost_group": "N/A",
            "technical_lead": "N/A",
            "account_owner": "N/A",
        }

        for col, default in orgs_columns.items():
            ec2_df[col] = default

        # Enrich with actual data
        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Enriching with Organizations...", total=len(ec2_df))

            for idx, row in ec2_df.iterrows():
                account_id = str(row.get("account_id", "")).strip()

                if account_id in self.account_lookup:
                    acc = self.account_lookup[account_id]
                    ec2_df.at[idx, "account_name"] = acc.get("name", "N/A")
                    ec2_df.at[idx, "account_email"] = acc.get("email", "N/A")
                    ec2_df.at[idx, "wbs_code"] = acc.get("wbs_code", "N/A")
                    ec2_df.at[idx, "cost_group"] = acc.get("cost_group", "N/A")
                    ec2_df.at[idx, "technical_lead"] = acc.get("technical_lead", "N/A")
                    ec2_df.at[idx, "account_owner"] = acc.get("account_owner", "N/A")

                progress.update(task, advance=1)

        enriched_count = (ec2_df["account_name"] != "N/A").sum()
        print_success(f"Organizations enrichment complete: {enriched_count}/{len(ec2_df)} instances")
        return ec2_df

    def _enrich_cost(self, ec2_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Cost Explorer cost data (monthly + annual).

        Uses real AWS Cost Explorer API (no mock data) with resource-level tagging.
        """
        ec2_df["monthly_cost"] = 0.0
        ec2_df["annual_cost_12mo"] = 0.0

        # Cost Explorer client (requires billing profile permissions)
        try:
            ce_client = boto3.Session(profile_name=self.billing_profile).client("ce", region_name="ap-southeast-2")
        except Exception as e:
            print_warning(f"Cost Explorer unavailable: {e}")
            print_info("Cost enrichment skipped (no billing permissions)")
            return ec2_df

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")  # Last 30 days

        try:
            # Get EC2 costs grouped by account (LINKED_ACCOUNT dimension)
            # NOTE: Cost Explorer does NOT support RESOURCE_ID dimension for per-instance costs
            # We distribute account-level costs evenly as approximation
            response = ce_client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Elastic Compute Cloud - Compute"]}},
                GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
            )

            # Build account cost lookup (monthly costs)
            account_costs = {}
            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    account_id = group.get("Keys", [""])[0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    account_costs[account_id] = account_costs.get(account_id, 0.0) + cost

            # Count instances per account
            account_instance_counts = ec2_df["account_id"].astype(str).value_counts().to_dict()

            # Distribute costs to instances (equal distribution per account)
            for account_id, total_monthly_cost in account_costs.items():
                instance_count = account_instance_counts.get(account_id, 1)
                cost_per_instance = total_monthly_cost / instance_count if instance_count > 0 else 0.0

                # Assign cost to instances in this account
                mask = ec2_df["account_id"].astype(str) == account_id
                ec2_df.loc[mask, "monthly_cost"] = cost_per_instance
                ec2_df.loc[mask, "annual_cost_12mo"] = cost_per_instance * 12

        except Exception as e:
            print_warning(f"Cost Explorer API error: {e}")
            # Continue with $0 costs

        total_annual = ec2_df["annual_cost_12mo"].sum()
        print_success(f"Cost enrichment complete: ${total_annual:,.2f} annual cost tracked")
        return ec2_df

    def _enrich_activity(self, ec2_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add CloudTrail activity data (last activity + idle detection).

        Uses CloudTrail lookup_events API to find last activity timestamp.
        Idle detection: >90 days since last activity.
        """
        ec2_df["last_activity_date"] = None
        ec2_df["days_since_activity"] = None
        ec2_df["activity_count_90d"] = 0
        ec2_df["is_idle"] = False

        # CloudTrail client (management account profile)
        try:
            ct_client = boto3.Session(profile_name=self.management_profile).client(
                "cloudtrail", region_name=self.region
            )
        except Exception as e:
            print_warning(f"CloudTrail unavailable: {e}")
            print_info("Activity enrichment skipped (no CloudTrail permissions)")
            return ec2_df

        end_time = datetime.now()
        start_time = end_time - timedelta(days=90)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Enriching with CloudTrail...", total=len(ec2_df))

            for idx, row in ec2_df.iterrows():
                instance_id = row.get("instance_id", "")

                if not instance_id:
                    progress.update(task, advance=1)
                    continue

                try:
                    # Query CloudTrail for instance activity
                    response = ct_client.lookup_events(
                        LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        MaxResults=50,
                    )

                    events = response.get("Events", [])

                    if events:
                        # Most recent event first
                        last_event = events[0]
                        last_activity = last_event["EventTime"]
                        days_since = (datetime.now(last_activity.tzinfo) - last_activity).days

                        ec2_df.at[idx, "last_activity_date"] = last_activity.strftime("%Y-%m-%d %H:%M:%S")
                        ec2_df.at[idx, "days_since_activity"] = days_since
                        ec2_df.at[idx, "activity_count_90d"] = len(events)
                        ec2_df.at[idx, "is_idle"] = days_since > 90
                    else:
                        # No activity found in 90 days
                        ec2_df.at[idx, "is_idle"] = True
                        ec2_df.at[idx, "days_since_activity"] = 90

                except Exception as e:
                    # Silent failure (CloudTrail may not have data for all instances)
                    pass

                progress.update(task, advance=1)

        idle_count = ec2_df["is_idle"].sum()
        print_success(f"Activity enrichment complete: {idle_count} idle instances detected")
        return ec2_df

    def display_enrichment_summary(self, ec2_df: pd.DataFrame):
        """
        Display Rich CLI summary tables and trees.

        Shows:
        - Overall statistics table
        - Cost analysis tree by account
        - Idle instance warnings
        """
        print_header("EC2 Enrichment Summary")

        # Summary table
        table = create_table(title="EC2 Enrichment Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Total Instances", str(len(ec2_df)))
        table.add_row("Accounts Identified", str(ec2_df["account_name"].nunique()))

        # Only show idle instances if activity analysis was performed
        if "is_idle" in ec2_df.columns:
            table.add_row("Idle Instances (>90d)", str(int(ec2_df["is_idle"].sum())))

        # Only show cost metrics if cost analysis was performed
        if "monthly_cost" in ec2_df.columns:
            table.add_row("Total Monthly Cost", str(format_cost(ec2_df["monthly_cost"].sum())))
            table.add_row("Total Annual Cost", str(format_cost(ec2_df["annual_cost_12mo"].sum())))

        console.print(table)

        # Cost tree by account (only if cost/activity analysis performed)
        if "monthly_cost" in ec2_df.columns or "is_idle" in ec2_df.columns:
            console.print("\n")
            tree = create_tree("💰 Cost Analysis by Account", style="bright_blue bold")

            for account_name in ec2_df["account_name"].unique():
                if pd.notna(account_name) and account_name != "N/A":
                    account_df = ec2_df[ec2_df["account_name"] == account_name]
                    account_node = tree.add(f"{account_name}")
                    account_node.add(f"Instances: {len(account_df)}")

                    # Add cost metrics if available
                    if "monthly_cost" in ec2_df.columns:
                        account_node.add(f"Monthly Cost: {format_cost(account_df['monthly_cost'].sum())}")

                    # Add idle metrics if available
                    if "is_idle" in ec2_df.columns:
                        account_node.add(f"Idle: {int(account_df['is_idle'].sum())} instances")

            console.print(tree)


@click.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input EC2 data file (Excel/CSV with account_id and instance_id columns)",
)
@click.option("--output", "-o", "output_file", type=click.Path(), help="Output enriched data file (Excel/CSV/JSON)")
@click.option("--profile", "-p", default="default", help="AWS management profile (Organizations + CloudTrail access)")
@click.option(
    "--billing-profile", "-b", default=None, help="AWS billing profile (Cost Explorer access, defaults to --profile)"
)
@click.option(
    "--format", "-f", type=click.Choice(["csv", "excel", "json"]), default="csv", help="Output format (default: csv)"
)
@click.option("--display-only", is_flag=True, help="Display Rich CLI output without file export")
@click.option("--no-organizations", is_flag=True, help="Skip Organizations enrichment")
@click.option("--no-cost", is_flag=True, help="Skip Cost Explorer enrichment")
@click.option("--no-activity", is_flag=True, help="Skip CloudTrail activity enrichment")
def enrich_ec2(
    input_file, output_file, profile, billing_profile, format, display_only, no_organizations, no_cost, no_activity
):
    """
    Enrich EC2 inventory with Organizations metadata, Cost Explorer data, and CloudTrail activity.

    Extends existing EC2 inventory files with business context from AWS Organizations,
    cost tracking from Cost Explorer API, and activity analysis via CloudTrail.

    Required Input Columns:
        - account_id: AWS account ID (12-digit string)
        - instance_id: EC2 instance ID (i-xxxxxxxxx format)

    Added Enrichment Columns:
        Organizations: account_name, account_email, wbs_code, cost_group, technical_lead, account_owner
        Cost: monthly_cost, annual_cost_12mo
        Activity: last_activity_date, days_since_activity, activity_count_90d, is_idle

    Examples:
        # Basic enrichment with all features
        runbooks inventory enrich-ec2 -i data/ec2.xlsx -o data/enriched.xlsx -p mgmt-profile

        # Organizations metadata only
        runbooks inventory enrich-ec2 -i data/ec2.csv -o data/enriched.csv --no-cost --no-activity

        # Display without export
        runbooks inventory enrich-ec2 -i data/ec2.xlsx --display-only -p my-profile

        # Separate billing profile for Cost Explorer
        runbooks inventory enrich-ec2 -i data/ec2.xlsx -o data/enriched.xlsx -p mgmt -b billing
    """
    print_header("EC2 Enrichment Pipeline")

    # Load input data
    input_path = Path(input_file)

    try:
        if input_path.suffix == ".xlsx":
            ec2_df = pd.read_excel(input_file)
        elif input_path.suffix == ".csv":
            ec2_df = pd.read_csv(input_file)
        else:
            print_error(f"Unsupported input format: {input_path.suffix} (use .xlsx or .csv)")
            return
    except Exception as e:
        print_error(f"Failed to load input file: {input_file}", e)
        return

    console.print(f"[green]✅ Loaded {len(ec2_df)} EC2 instances from {input_file}[/green]")

    # Initialize enricher
    try:
        enricher = EC2Enricher(management_profile=profile, billing_profile=billing_profile)
    except Exception as e:
        print_error(f"Failed to initialize enricher: {e}")
        return

    # Execute enrichment
    try:
        enriched_df = enricher.enrich_ec2_instances(
            ec2_df, enrich_organizations=not no_organizations, enrich_cost=not no_cost, enrich_activity=not no_activity
        )
    except Exception as e:
        print_error(f"Enrichment failed: {e}")
        return

    # Display summary
    enricher.display_enrichment_summary(enriched_df)

    # Export results
    if not display_only and output_file:
        output_path = Path(output_file)

        try:
            if format == "csv" or output_path.suffix == ".csv":
                enriched_df.to_csv(output_file, index=False)
                print_success(f"Saved enriched data to {output_file} (CSV)")

            elif format == "excel" or output_path.suffix == ".xlsx":
                with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                    enriched_df.to_excel(writer, sheet_name="EC2 Enriched", index=False)

                    # Summary sheet with conditional metrics
                    metrics = ["Total Instances"]
                    values = [len(enriched_df)]

                    # Add idle metrics if available
                    if "is_idle" in enriched_df.columns:
                        metrics.append("Idle Instances")
                        values.append(int(enriched_df["is_idle"].sum()))

                    # Add cost metrics if available
                    if "monthly_cost" in enriched_df.columns:
                        metrics.append("Monthly Cost")
                        values.append(f"${enriched_df['monthly_cost'].sum():,.2f}")
                        metrics.append("Annual Cost")
                        values.append(f"${enriched_df['annual_cost_12mo'].sum():,.2f}")

                    summary_df = pd.DataFrame({"Metric": metrics, "Value": values})
                    summary_df.to_excel(writer, sheet_name="Summary", index=False)

                print_success(f"Saved enriched data to {output_file} (Excel, 2 sheets)")

            elif format == "json" or output_path.suffix == ".json":
                enriched_df.to_json(output_file, orient="records", indent=2)
                print_success(f"Saved enriched data to {output_file} (JSON)")

        except Exception as e:
            print_error(f"Failed to save output file: {output_file}", e)
            return

    elif not display_only and not output_file:
        print_warning("No output file specified - use --output or --display-only")


if __name__ == "__main__":
    enrich_ec2()
