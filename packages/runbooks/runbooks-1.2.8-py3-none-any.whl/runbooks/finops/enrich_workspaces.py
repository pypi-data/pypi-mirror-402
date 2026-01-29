"""WorkSpaces enrichment with Organizations metadata and cost analysis."""

import click
import pandas as pd
from pathlib import Path

from runbooks.finops.workspaces_analyzer import WorkSpacesCostAnalyzer
from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
)


@click.command()
@click.option(
    "--input",
    "-i",
    "input_file",
    required=True,
    type=click.Path(exists=True),
    help="Input WorkSpaces data file (Excel/CSV with 'AWS Account' column)",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output enriched data file (Excel/CSV/JSON)",
)
@click.option(
    "--profile",
    "-p",
    default="default",
    help="AWS operational profile (WorkSpaces access)",
)
@click.option(
    "--management-profile",
    "-m",
    default=None,
    help="AWS management profile (Organizations access)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "excel", "json"]),
    default="csv",
    help="Output format (default: csv)",
)
@click.option(
    "--display-only",
    is_flag=True,
    help="Display Rich CLI output without file export",
)
def enrich_workspaces(input_file, output_file, profile, management_profile, format, display_only):
    """
    Enrich WorkSpaces inventory with Organizations metadata and cost analysis.

    Reads WorkSpaces data from Excel/CSV with 'AWS Account' column and enriches it with:
    - Account name (from AWS Organizations)
    - Account email
    - WBS code (cost allocation)
    - Cost group
    - Technical lead
    - Account owner

    Example:
        runbooks finops enrich-workspaces -i data/workspaces.xlsx -o data/enriched.xlsx -p ops-profile -m mgmt-profile
    """
    print_header("WorkSpaces Enrichment Pipeline")

    # Load input data
    input_path = Path(input_file)

    if input_path.suffix == ".xlsx":
        ws_df = pd.read_excel(input_file)
        print_success(f"Loaded {len(ws_df)} WorkSpaces from Excel: {input_file}")
    elif input_path.suffix == ".csv":
        ws_df = pd.read_csv(input_file)
        print_success(f"Loaded {len(ws_df)} WorkSpaces from CSV: {input_file}")
    else:
        print_error(f"Unsupported input format: {input_path.suffix}")
        print_info("Supported formats: .xlsx, .csv")
        return

    # Validate required columns
    if "AWS Account" not in ws_df.columns:
        print_error("Input file missing required 'AWS Account' column")
        print_info(f"Available columns: {', '.join(ws_df.columns)}")
        return

    # Initialize analyzer
    analyzer = WorkSpacesCostAnalyzer(profile=profile)

    # Enrich with Organizations metadata
    if management_profile:
        ws_df = analyzer.enrich_dataframe_with_organizations(ws_df, management_profile)
    else:
        print_info("No --management-profile specified, skipping Organizations enrichment")

    # Display preview
    print_header("Enrichment Preview")
    console.print(ws_df.head(10).to_string(index=False))

    if len(ws_df) > 10:
        console.print(f"\n[dim]... and {len(ws_df) - 10} more rows[/dim]")

    # Export results
    if not display_only and output_file:
        output_path = Path(output_file)

        if format == "csv" or output_path.suffix == ".csv":
            ws_df.to_csv(output_file, index=False)
            print_success(f"Saved enriched data to {output_file} (CSV)")

        elif format == "excel" or output_path.suffix == ".xlsx":
            with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
                ws_df.to_excel(writer, sheet_name="WorkSpaces Enriched", index=False)

            print_success(f"Saved enriched data to {output_file} (Excel)")

        elif format == "json" or output_path.suffix == ".json":
            ws_df.to_json(output_file, orient="records", indent=2)
            print_success(f"Saved enriched data to {output_file} (JSON)")

    elif not display_only and not output_file:
        print_info("No --output specified, use --display-only to preview without saving")


if __name__ == "__main__":
    enrich_workspaces()
