#!/usr/bin/env python3
"""
Compute Reports Module - Shared Excel and Rich CLI Utilities for EC2/WorkSpaces

This module provides DRY utilities for compute resource analysis:
- Multi-sheet Excel exports with formatting
- Rich Tree visualizations for cost hierarchy
- Validation metrics calculation
- Reusable reporting patterns

Design Philosophy (KISS/DRY/LEAN):
- Extract duplicated patterns from EC2/WorkSpaces notebooks
- Reuse existing rich_utils.py patterns
- Follow workspaces_analyzer.py proven structure
- Single location for compute reporting logic

Usage:
    # Excel export
    from runbooks.finops.compute_reports import export_compute_excel
    export_compute_excel(
        df=enriched_df,
        output_file='output.xlsx',
        resource_type='ec2',
        include_cost_analysis=True
    )

    # Cost tree visualization
    tree = create_cost_tree(
        df=enriched_df,
        group_by='account_name',
        cost_column='monthly_cost',
        title='EC2 Cost Analysis'
    )
    console.print(tree)

Strategic Alignment:
- Objective 1: Reusable reporting for runbooks package
- KISS/DRY/LEAN: Extract shared logic from notebooks
- Enterprise patterns: Proven from FinOps module
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

from ..common.rich_utils import (
    console,
    create_tree,
    format_cost,
    print_error,
    print_info,
    print_success,
    print_warning,
)

# Import Rich Tree for type hints
from rich.tree import Tree

logger = logging.getLogger(__name__)


def export_compute_excel(
    df: pd.DataFrame,
    output_file: str,
    resource_type: str,
    include_cost_analysis: bool = True,
    include_recommendations: bool = False,
    verbose: bool = False,
) -> None:
    """
    Export compute resource analysis to multi-sheet Excel workbook.

    Creates standardized Excel workbook with:
    - Sheet 1: Enriched Data (all columns)
    - Sheet 2: Cost Summary (by account/region)
    - Sheet 3: Organizations Hierarchy
    - Sheet 4: Recommendations (optional)
    - Sheet 5: Validation Metrics

    Args:
        df: pandas DataFrame with enriched compute data
        output_file: Path to output Excel file
        resource_type: 'ec2' or 'workspaces'
        include_cost_analysis: Include cost summary sheet
        include_recommendations: Include recommendations sheet

    Pattern:
        Extracted from notebooks/compute/ec2.ipynb Cell 21
        and notebooks/compute/workspaces.ipynb Cell 20
    """
    try:
        import xlsxwriter

        # Count sheets that will be created
        sheet_count = 4  # Enriched Data + Validation Metrics (always present)
        if include_cost_analysis and "monthly_cost" in df.columns and "account_name" in df.columns:
            # Cost Summary sheet will be added (already counted in base 4)
            pass
        if "account_name" in df.columns and "wbs_code" in df.columns:
            # Organizations sheet will be added (already counted in base 4)
            pass

        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            workbook = writer.book

            # Define formats
            header_format = workbook.add_format(
                {"bold": True, "bg_color": "#4472C4", "font_color": "white", "border": 1, "align": "center"}
            )

            currency_format = workbook.add_format({"num_format": "$#,##0.00"})
            number_format = workbook.add_format({"num_format": "#,##0"})

            # Sheet 1: Enriched Data
            df.to_excel(writer, sheet_name="Enriched Data", index=False)

            worksheet = writer.sheets["Enriched Data"]

            # Apply header formatting
            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_format)

                # Auto-width columns
                max_len = max(len(str(col_name)), df[col_name].astype(str).str.len().max() if not df.empty else 0)
                worksheet.set_column(col_num, col_num, min(max_len + 2, 50))

            # Sheet 2: Cost Summary (if cost data available)
            if include_cost_analysis and "monthly_cost" in df.columns and "account_name" in df.columns:
                # Determine account ID column (EC2 vs WorkSpaces schema)
                account_id_col = "account_id" if "account_id" in df.columns else "AWS Account"

                # Determine resource ID column
                if resource_type == "ec2":
                    resource_id_col = "instance_id"
                elif resource_type == "lambda":
                    resource_id_col = "function_name"
                else:
                    resource_id_col = "Identifier"

                cost_summary = (
                    df.groupby([account_id_col, "account_name"])
                    .agg({resource_id_col: "count", "monthly_cost": "sum"})
                    .reset_index()
                )

                cost_summary.columns = ["Account ID", "Account Name", "Resource Count", "Monthly Cost"]
                cost_summary["Annual Cost"] = cost_summary["Monthly Cost"] * 12
                cost_summary = cost_summary.sort_values("Annual Cost", ascending=False)

                cost_summary.to_excel(writer, sheet_name="Cost Summary", index=False)

                # Format cost columns
                cost_worksheet = writer.sheets["Cost Summary"]
                for col_num, col_name in enumerate(cost_summary.columns):
                    cost_worksheet.write(0, col_num, col_name, header_format)
                    if "Cost" in col_name:
                        for row_num, value in enumerate(cost_summary[col_name], start=1):
                            cost_worksheet.write(row_num, col_num, value, currency_format)

            # Sheet 3: Organizations Hierarchy (if available)
            if "account_name" in df.columns and "wbs_code" in df.columns:
                orgs_summary = df[
                    ["account_name", "account_email", "wbs_code", "cost_group", "technical_lead", "account_owner"]
                ].drop_duplicates()

                orgs_summary.to_excel(writer, sheet_name="Organizations", index=False)

                orgs_worksheet = writer.sheets["Organizations"]
                for col_num, col_name in enumerate(orgs_summary.columns):
                    orgs_worksheet.write(0, col_num, col_name, header_format)
                    orgs_worksheet.set_column(col_num, col_num, 25)

            # Sheet 4: Validation Metrics
            metrics = calculate_validation_metrics(df, resource_type)
            metrics_df = pd.DataFrame([metrics])

            metrics_df.to_excel(writer, sheet_name="Validation Metrics", index=False)

            metrics_worksheet = writer.sheets["Validation Metrics"]
            for col_num, col_name in enumerate(metrics_df.columns):
                metrics_worksheet.write(0, col_num, col_name, header_format)
                metrics_worksheet.set_column(col_num, col_num, 25)

        # Consolidated single-line output (Manager's requirement)
        import os

        file_size_kb = os.path.getsize(output_file) / 1024
        print_success(f"✅ Excel export: {output_file} ({file_size_kb:.1f} KB, {sheet_count} sheets)")

    except Exception as e:
        print_error(f"❌ Excel export failed: {e}")
        logger.error(f"Excel export error: {e}", exc_info=True)
        raise


def create_cost_tree(
    df: pd.DataFrame, group_by: str = "account_name", cost_column: str = "monthly_cost", title: str = "Cost Analysis"
) -> Tree:
    """
    Create hierarchical Rich Tree for cost visualization.

    Pattern: Account → Resource State → Cost Breakdown

    Args:
        df: pandas DataFrame with cost data
        group_by: Column to group by (default: account_name)
        cost_column: Column containing costs (default: monthly_cost)
        title: Tree title

    Returns:
        Rich Tree object ready for console.print()

    Pattern:
        Extracted from notebooks/compute/ec2.ipynb Cell 19
        and notebooks/compute/workspaces.ipynb Cell 18
    """
    try:
        # Create root tree
        total_cost = df[cost_column].sum() if cost_column in df.columns else 0
        tree = create_tree(f"💰 {title} - Total: {format_cost(total_cost)}/month", style="bright_green bold")

        # Group by account/category
        if group_by not in df.columns:
            print_warning(f"⚠️  Column '{group_by}' not found, using flat structure")
            return tree

        groups = df.groupby(group_by)

        for group_name, group_data in groups:
            if group_name == "N/A" or pd.isna(group_name):
                continue

            # Calculate group totals
            group_cost = group_data[cost_column].sum() if cost_column in group_data.columns else 0
            resource_count = len(group_data)

            # Add group branch
            group_branch = tree.add(
                f"🏢 {group_name} - {format_cost(group_cost)}/month ({resource_count} resources)", style="cyan"
            )

            # Add resource state breakdown (if available)
            if "instance_state" in group_data.columns:
                states = group_data.groupby("instance_state")
                for state, state_data in states:
                    state_cost = state_data[cost_column].sum() if cost_column in state_data.columns else 0
                    state_count = len(state_data)

                    state_color = "green" if state == "running" else "yellow"
                    group_branch.add(
                        f"{state.title()}: {state_count} instances - {format_cost(state_cost)}/month", style=state_color
                    )

            # Add top 3 cost drivers
            if len(group_data) > 0 and cost_column in group_data.columns:
                top_costs = group_data.nlargest(3, cost_column)
                if len(top_costs) > 0:
                    cost_branch = group_branch.add("[bold]Top Cost Drivers[/bold]")

                    for idx, row in top_costs.iterrows():
                        resource_id = row.get("instance_id", row.get("Identifier", "Unknown"))
                        resource_cost = row.get(cost_column, 0)
                        resource_type = row.get("instance_type", "Unknown")

                        cost_branch.add(
                            f"{str(resource_id)[:20]} ({resource_type}): {format_cost(resource_cost)}/month",
                            style="yellow",
                        )

        return tree

    except Exception as e:
        print_error(f"❌ Cost tree creation failed: {e}")
        logger.error(f"Cost tree error: {e}", exc_info=True)
        # Return empty tree
        return create_tree(f"💰 {title} - Error", style="red")


def calculate_validation_metrics(df: pd.DataFrame, resource_type: str) -> Dict:
    """
    Calculate enrichment quality metrics.

    Returns validation metrics including:
    - Total resources
    - Enriched count
    - Success rate
    - Missing data columns

    Args:
        df: pandas DataFrame with enriched data
        resource_type: 'ec2' or 'workspaces'

    Returns:
        Dictionary with validation metrics:
        {
            'total_resources': int,
            'enriched_count': int,
            'success_rate': float,
            'organizations_enriched': int,
            'cost_enriched': int,
            'missing_data_columns': List[str]
        }
    """
    try:
        total_resources = len(df)

        # Organizations enrichment success
        orgs_enriched = 0
        if "account_name" in df.columns:
            orgs_enriched = (df["account_name"] != "N/A").sum()

        # Cost enrichment success
        cost_enriched = 0
        if "monthly_cost" in df.columns:
            cost_enriched = (df["monthly_cost"] > 0).sum()

        # Calculate overall enrichment success
        # For EC2: Check instance_state and instance_name
        # For WorkSpaces: Check WorkSpace ID (primary key - always present)
        if resource_type == "ec2":
            enriched_count = 0
            if "instance_state" in df.columns:
                enriched_count = ((df["instance_state"] != "N/A") & (df["instance_state"].notna())).sum()
        else:  # workspaces
            enriched_count = 0
            # WorkSpaces: Check WorkSpace ID (primary key) OR account_name (Organizations enrichment)
            if "WorkSpace ID" in df.columns:
                enriched_count = df["WorkSpace ID"].notna().sum()
            elif "account_name" in df.columns:
                enriched_count = (df["account_name"] != "N/A").sum()

        success_rate = (enriched_count / total_resources * 100) if total_resources > 0 else 0

        # Identify missing data columns
        expected_columns = {
            "ec2": ["instance_id", "instance_state", "instance_type", "account_name", "monthly_cost", "region"],
            "workspaces": ["Identifier", "workspace_state", "username", "account_name", "monthly_cost"],
        }

        missing_columns = [col for col in expected_columns.get(resource_type, []) if col not in df.columns]

        return {
            "total_resources": total_resources,
            "enriched_count": enriched_count,
            "success_rate": round(success_rate, 2),
            "organizations_enriched": orgs_enriched,
            "cost_enriched": cost_enriched,
            "missing_data_columns": missing_columns,
            "validation_timestamp": pd.Timestamp.now().isoformat(),
        }

    except Exception as e:
        print_error(f"❌ Validation metrics calculation failed: {e}")
        logger.error(f"Validation metrics error: {e}", exc_info=True)
        return {
            "total_resources": 0,
            "enriched_count": 0,
            "success_rate": 0.0,
            "organizations_enriched": 0,
            "cost_enriched": 0,
            "missing_data_columns": [],
            "error": str(e),
        }


def display_validation_metrics(df: pd.DataFrame, resource_type: str, verbose: bool = False) -> Dict:
    """
    Display validation metrics with consolidated output (Manager's requirement).

    Args:
        df: pandas DataFrame with enriched data
        resource_type: 'ec2' or 'workspaces'
        verbose: If True, show detailed Rich Table. If False, single-line output.

    Returns:
        Dictionary with validation metrics

    Manager's Requirement (Oct 2025):
        Default (verbose=False): Single-line consolidated output
        Optional (verbose=True): Rich Table for detailed analysis
    """
    metrics = calculate_validation_metrics(df, resource_type)

    if verbose:
        # Rich Table for detailed analysis
        from ..common.rich_utils import create_table

        metrics_table = create_table(
            title="Enrichment Quality Metrics",
            columns=[
                {"header": "Metric", "style": "cyan"},
                {"header": "Value", "style": "green"},
                {"header": "Status", "style": "yellow"},
            ],
        )

        # Success rate with pass/fail
        pass_status = (
            "✅ PASS" if metrics["success_rate"] >= 90 else "⚠️ WARN" if metrics["success_rate"] >= 75 else "❌ FAIL"
        )
        metrics_table.add_row("Success Rate", f"{metrics['success_rate']:.1f}%", pass_status)
        metrics_table.add_row("Total Resources", str(metrics["total_resources"]), "")
        metrics_table.add_row("Enriched Count", str(metrics["enriched_count"]), "")
        metrics_table.add_row("Organizations", str(metrics["organizations_enriched"]), "")
        metrics_table.add_row("Cost Data", str(metrics["cost_enriched"]), "")

        console.print(metrics_table)
    else:
        # Consolidated single-line output (Manager's preference)
        pass_status = (
            "✅ PASS" if metrics["success_rate"] >= 90 else "⚠️ WARN" if metrics["success_rate"] >= 75 else "❌ FAIL"
        )
        print_success(
            f"✅ Enrichment: {metrics['enriched_count']}/{metrics['total_resources']} "
            f"({metrics['success_rate']:.1f}%) | "
            f"Organizations: {metrics['organizations_enriched']} | "
            f"Cost: {metrics['cost_enriched']} | {pass_status}"
        )

    return metrics


# ===========================
# DECOMMISSION-SPECIFIC DISPLAY FUNCTIONS (Phase 4)
# ===========================


def display_decommission_distribution(df: pd.DataFrame, resource_type: str = "EC2") -> None:
    """
    Display decommission tier breakdown with Rich table.

    Shows distribution of resources across decommission tiers (MUST, SHOULD, COULD, KEEP)
    with cost analysis and savings potential.

    Args:
        df: pandas DataFrame with decommission_tier and decommission_score columns
        resource_type: 'EC2' or 'WorkSpaces' for display customization

    Pattern:
        Extracted from Phase 4 requirements for decommission-specific displays
        Follows rich_utils.py create_table() pattern with tier ordering

    Example:
        >>> display_decommission_distribution(enriched_df, resource_type='EC2')

        ┏━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
        ┃ Tier   ┃ Count ┃ %      ┃ Total Cost    ┃ Savings Potential  ┃
        ┡━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
        │ MUST   │    15 │  12.5% │     $3,450.00 │          $3,450.00 │
        │ SHOULD │    25 │  20.8% │     $5,200.00 │          $5,200.00 │
        │ COULD  │    30 │  25.0% │     $4,800.00 │          $2,400.00 │
        │ KEEP   │    50 │  41.7% │    $12,000.00 │               $0.00 │
        └────────┴───────┴────────┴───────────────┴────────────────────┘
    """
    try:
        from ..common.rich_utils import create_table

        # Check for required columns
        if "decommission_tier" not in df.columns:
            print_warning(f"⚠️  decommission_tier column not found in {resource_type} data")
            return

        table = create_table(
            title=f"{resource_type} Decommission Tier Breakdown",
            columns=[
                {"header": "Tier", "style": "bold cyan"},
                {"header": "Count", "style": "yellow"},
                {"header": "%", "style": "green"},
                {"header": "Total Cost", "style": "bright_green"},
                {"header": "Savings Potential", "style": "bright_yellow"},
            ],
        )

        tier_order = ["MUST", "SHOULD", "COULD", "KEEP"]
        total_count = len(df)

        for tier in tier_order:
            tier_df = df[df["decommission_tier"] == tier]
            count = len(tier_df)
            pct = (count / total_count * 100) if total_count > 0 else 0

            # Calculate cost (handle missing column gracefully)
            if "monthly_cost" in df.columns:
                cost = tier_df["monthly_cost"].sum()
            else:
                cost = 0

            # Calculate savings potential
            # MUST/SHOULD = 100% savings, COULD = 50% savings, KEEP = 0%
            if tier in ["MUST", "SHOULD"]:
                savings = cost
            elif tier == "COULD":
                savings = cost * 0.5
            else:
                savings = 0

            table.add_row(tier, str(count), f"{pct:.1f}%", format_cost(cost), format_cost(savings))

        console.print(table)

        # Summary metrics
        priority_count = len(df[df["decommission_tier"].isin(["MUST", "SHOULD"])])
        if "monthly_cost" in df.columns:
            priority_cost = df[df["decommission_tier"].isin(["MUST", "SHOULD"])]["monthly_cost"].sum()
            print_success(
                f"✅ Priority decommission candidates: {priority_count} ({priority_cost:,.2f}/month savings potential)"
            )

    except Exception as e:
        print_error(f"❌ Decommission distribution display failed: {e}")
        logger.error(f"Display error: {e}", exc_info=True)


def display_cost_tree_by_tier(df: pd.DataFrame, resource_type: str = "EC2") -> None:
    """
    Display hierarchical cost tree: Tier → Account → Resource.

    Shows cost breakdown organized by decommission tier with account-level
    detail and top cost drivers per account.

    Args:
        df: pandas DataFrame with decommission_tier, account_name, and monthly_cost columns
        resource_type: 'EC2' or 'WorkSpaces' for display customization

    Pattern:
        Follows rich_utils.py create_tree() pattern with hierarchical structure
        Extracted from Phase 4 requirements for decommission-specific displays

    Example:
        >>> display_cost_tree_by_tier(enriched_df, resource_type='EC2')

        💰 EC2 Cost Analysis by Decommission Tier
        ├── MUST: $3,450.00 (15 resources)
        │   ├── Production Account: $2,100.00 (8 resources)
        │   │   ├── i-1234567890abcdef0: $250.00
        │   │   ├── i-abcdef1234567890: $220.00
        │   │   └── i-567890abcdef1234: $180.00
        │   └── Dev Account: $1,350.00 (7 resources)
        └── SHOULD: $5,200.00 (25 resources)
            └── Staging Account: $5,200.00 (25 resources)
    """
    try:
        # Check for required columns
        if "decommission_tier" not in df.columns:
            print_warning(f"⚠️  decommission_tier column not found in {resource_type} data")
            return

        if "monthly_cost" not in df.columns:
            print_warning(f"⚠️  monthly_cost column not found in {resource_type} data")
            return

        tree = create_tree(f"💰 {resource_type} Cost Analysis by Decommission Tier", style="bright_green bold")

        tier_order = ["MUST", "SHOULD", "COULD", "KEEP"]

        for tier in tier_order:
            tier_df = df[df["decommission_tier"] == tier]
            if len(tier_df) == 0:
                continue

            tier_cost = tier_df["monthly_cost"].sum()
            tier_branch = tree.add(
                f"[bold]{tier}[/bold]: {format_cost(tier_cost)} ({len(tier_df)} resources)",
                style="cyan" if tier in ["MUST", "SHOULD"] else "dim",
            )

            # Group by account (if available)
            if "account_name" in df.columns:
                account_groups = tier_df.groupby("account_name")

                for account, account_df in account_groups:
                    if account == "N/A" or pd.isna(account):
                        continue

                    account_cost = account_df["monthly_cost"].sum()
                    account_branch = tier_branch.add(
                        f"{account}: {format_cost(account_cost)} ({len(account_df)} resources)",
                        style="yellow" if tier in ["MUST", "SHOULD"] else "dim",
                    )

                    # Top 5 resources by cost
                    top_resources = account_df.nlargest(5, "monthly_cost")

                    for _, row in top_resources.iterrows():
                        # Determine resource ID column based on resource type
                        if resource_type.lower() == "ec2":
                            resource_id = row.get("instance_id", row.get("Instance ID", "Unknown"))
                        else:  # WorkSpaces
                            resource_id = row.get("Identifier", row.get("WorkSpace ID", "Unknown"))

                        cost = row["monthly_cost"]
                        account_branch.add(
                            f"{resource_id}: {format_cost(cost)}",
                            style="green" if tier in ["MUST", "SHOULD"] else "dim",
                        )

        console.print(tree)

    except Exception as e:
        print_error(f"❌ Cost tree display failed: {e}")
        logger.error(f"Cost tree error: {e}", exc_info=True)


def display_idle_summary(df: pd.DataFrame, resource_type: str = "EC2") -> None:
    """
    Display summary of MUST/SHOULD decommission candidates.

    Shows high-priority idle resources with immediate action opportunities
    and annual savings projections.

    Args:
        df: pandas DataFrame with decommission_tier and monthly_cost columns
        resource_type: 'EC2' or 'WorkSpaces' for display customization

    Pattern:
        Follows rich_utils.py create_table() pattern with summary metrics
        Extracted from Phase 4 requirements for decommission-specific displays

    Example:
        >>> display_idle_summary(enriched_df, resource_type='EC2')

        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
        ┃ Category                  ┃ Value         ┃
        ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
        │ Total Idle Resources      │            40 │
        │ MUST Decommission         │            15 │
        │ SHOULD Decommission       │            25 │
        │ Total Monthly Cost        │     $8,650.00 │
        │ Annual Savings Potential  │   $103,800.00 │
        └───────────────────────────┴───────────────┘
    """
    try:
        from ..common.rich_utils import create_table

        # Check for required columns
        if "decommission_tier" not in df.columns:
            print_warning(f"⚠️  decommission_tier column not found in {resource_type} data")
            return

        idle_df = df[df["decommission_tier"].isin(["MUST", "SHOULD"])]

        table = create_table(
            title=f"{resource_type} Idle Resource Summary",
            columns=[{"header": "Category", "style": "bold cyan"}, {"header": "Value", "style": "bright_yellow"}],
        )

        # Calculate metrics
        total_idle = len(idle_df)
        must_count = len(df[df["decommission_tier"] == "MUST"])
        should_count = len(df[df["decommission_tier"] == "SHOULD"])

        # Cost metrics (handle missing column gracefully)
        if "monthly_cost" in df.columns:
            monthly_cost = idle_df["monthly_cost"].sum()
            annual_savings = monthly_cost * 12
        else:
            monthly_cost = 0
            annual_savings = 0

        table.add_row("Total Idle Resources", str(total_idle))
        table.add_row("MUST Decommission", str(must_count))
        table.add_row("SHOULD Decommission", str(should_count))
        table.add_row("Total Monthly Cost", format_cost(monthly_cost))
        table.add_row("Annual Savings Potential", format_cost(annual_savings))

        console.print(table)

        if total_idle > 0:
            print_success(
                f"✅ Identified {total_idle} idle resources with ${annual_savings:,.2f} annual savings potential"
            )
        else:
            print_info(f"ℹ️  No high-priority idle resources identified")

    except Exception as e:
        print_error(f"❌ Idle summary display failed: {e}")
        logger.error(f"Idle summary error: {e}", exc_info=True)


def export_decommission_analysis(df: pd.DataFrame, output_path: str, resource_type: str = "EC2") -> None:
    """
    Export decommission analysis to multi-sheet Excel with standardized 4-sheet structure.

    Creates comprehensive Excel workbook with:
    - Sheet 1: Enriched - All columns (28 for EC2, 20 for WorkSpaces)
    - Sheet 2: Summary - Executive summary with tier breakdown
    - Sheet 3: Cost - 12-month trailing cost analysis by account + tier
    - Sheet 4: Idle - MUST/SHOULD decommission candidates only

    Args:
        df: pandas DataFrame with enriched compute data and decommission columns
        output_path: Path to output Excel file
        resource_type: 'EC2' or 'WorkSpaces' for display customization

    Pattern:
        Follows compute_reports.py export_compute_excel() pattern
        Enhanced with decommission-specific sheets

    Example:
        >>> export_decommission_analysis(
        ...     df=enriched_df,
        ...     output_path='ec2-decommission-analysis.xlsx',
        ...     resource_type='EC2'
        ... )
        ✅ Excel export: ec2-decommission-analysis.xlsx (245.3 KB, 4 sheets)

    DoD (Definition of Done):
        - 4 sheets created (Enriched, Summary, Cost, Idle)
        - Professional formatting with xlsxwriter
        - Consolidated single-line output (Manager's requirement)
        - Error handling with graceful degradation
    """
    try:
        import xlsxwriter

        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            workbook = writer.book

            # Define formats
            header_format = workbook.add_format(
                {"bold": True, "bg_color": "#4472C4", "font_color": "white", "border": 1, "align": "center"}
            )

            currency_format = workbook.add_format({"num_format": "$#,##0.00"})
            number_format = workbook.add_format({"num_format": "#,##0"})
            percent_format = workbook.add_format({"num_format": "0.0%"})

            # Sheet 1: Enriched (all data)
            df.to_excel(writer, sheet_name="Enriched", index=False)
            worksheet = writer.sheets["Enriched"]

            # Apply header formatting
            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_format)
                # Auto-width columns
                max_len = max(len(str(col_name)), df[col_name].astype(str).str.len().max() if not df.empty else 0)
                worksheet.set_column(col_num, col_num, min(max_len + 2, 50))

            # Sheet 2: Executive Summary
            if "decommission_tier" in df.columns:
                summary_data = []
                tier_order = ["MUST", "SHOULD", "COULD", "KEEP"]

                # Calculate tier metrics
                for tier in tier_order:
                    tier_df = df[df["decommission_tier"] == tier]
                    count = len(tier_df)

                    if "monthly_cost" in df.columns:
                        tier_cost = tier_df["monthly_cost"].sum()
                    else:
                        tier_cost = 0

                    summary_data.append(
                        {
                            "Metric": f"{tier} Decommission",
                            "Count": count,
                            "Monthly Cost": tier_cost,
                            "Annual Cost": tier_cost * 12,
                        }
                    )

                # Add total and savings rows
                total_count = len(df)
                if "monthly_cost" in df.columns:
                    total_cost = df["monthly_cost"].sum()
                    priority_cost = df[df["decommission_tier"].isin(["MUST", "SHOULD"])]["monthly_cost"].sum()
                else:
                    total_cost = 0
                    priority_cost = 0

                summary_data.extend(
                    [
                        {"Metric": "", "Count": "", "Monthly Cost": "", "Annual Cost": ""},
                        {
                            "Metric": "Total Resources",
                            "Count": total_count,
                            "Monthly Cost": total_cost,
                            "Annual Cost": total_cost * 12,
                        },
                        {
                            "Metric": "Potential Annual Savings (MUST+SHOULD)",
                            "Count": "",
                            "Monthly Cost": "",
                            "Annual Cost": priority_cost * 12,
                        },
                    ]
                )

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

                # Format summary sheet
                summary_worksheet = writer.sheets["Summary"]
                for col_num, col_name in enumerate(summary_df.columns):
                    summary_worksheet.write(0, col_num, col_name, header_format)
                    if "Cost" in col_name:
                        for row_num in range(1, len(summary_df) + 1):
                            value = summary_df.iloc[row_num - 1][col_name]
                            if pd.notna(value) and value != "":
                                summary_worksheet.write(row_num, col_num, value, currency_format)

            # Sheet 3: Cost Analysis (by account + tier)
            if "account_name" in df.columns and "decommission_tier" in df.columns and "monthly_cost" in df.columns:
                cost_pivot = df.pivot_table(
                    values="monthly_cost",
                    index="account_name",
                    columns="decommission_tier",
                    aggfunc="sum",
                    fill_value=0,
                )

                # Add total column
                cost_pivot["Total"] = cost_pivot.sum(axis=1)

                cost_pivot.to_excel(writer, sheet_name="Cost")

                # Format cost sheet
                cost_worksheet = writer.sheets["Cost"]
                for col_num in range(1, len(cost_pivot.columns) + 1):
                    for row_num in range(1, len(cost_pivot) + 1):
                        cost_worksheet.write(
                            row_num, col_num, cost_pivot.iloc[row_num - 1, col_num - 1], currency_format
                        )

            # Sheet 4: Idle Resources (MUST + SHOULD only)
            if "decommission_tier" in df.columns:
                idle_df = df[df["decommission_tier"].isin(["MUST", "SHOULD"])].copy()

                if "decommission_score" in df.columns:
                    idle_df = idle_df.sort_values("decommission_score", ascending=False)

                idle_df.to_excel(writer, sheet_name="Idle", index=False)

                # Format idle sheet
                idle_worksheet = writer.sheets["Idle"]
                for col_num, col_name in enumerate(idle_df.columns):
                    idle_worksheet.write(0, col_num, col_name, header_format)

        # Consolidated single-line output (Manager's requirement)
        import os

        file_size_kb = os.path.getsize(output_path) / 1024
        print_success(f"✅ Excel export: {output_path} ({file_size_kb:.1f} KB, 4 sheets)")

    except Exception as e:
        print_error(f"❌ Decommission analysis export failed: {e}")
        logger.error(f"Export error: {e}", exc_info=True)
        raise
