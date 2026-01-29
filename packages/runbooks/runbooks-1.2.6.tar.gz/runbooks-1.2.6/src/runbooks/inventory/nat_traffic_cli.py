#!/usr/bin/env python3
"""
NAT Gateway Traffic Analysis CLI - $100K Savings Enabler

Standalone CLI for analyzing NAT Gateway traffic patterns to identify
VPC Endpoint migration opportunities worth $100K+ annual savings.

Business Value:
- Identify idle NAT Gateways for elimination
- Detect VPCE migration candidates (80%+ AWS service traffic)
- Calculate savings potential per NAT Gateway
- Generate migration recommendations

Strategic Alignment:
- JIRA Epic: AWSO-75 (NAT→VPCE migration)
- PRD Section 5: VPC Network Optimization (Rank 9, P1 HIGH)
- ROI: $50,000 per implementation day

Features:
- Profile override priority system integration
- Rich CLI output with savings visualization
- Multi-region support
- Export results to CSV/JSON

Usage:
    runbooks inventory analyze-nat-traffic --profile my-profile
    runbooks inventory analyze-nat-traffic --region ap-southeast-2 --lookback-days 30
    runbooks inventory analyze-nat-traffic --output nat_analysis.csv --format csv
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import pandas as pd

from ..common.profile_utils import get_profile_for_operation
from ..common.rich_utils import console, print_error, print_info, print_success, print_warning, create_table
from .enrichers.nat_traffic_enricher import create_nat_traffic_enricher


@click.command()
@click.option("--profile", help="AWS profile name (takes precedence over environment variables)")
@click.option("--region", default="ap-southeast-2", help="AWS region to analyze (default: ap-southeast-2)")
@click.option("--lookback-days", type=int, default=30, help="Number of days to analyze traffic (default: 30)")
@click.option("--output", type=click.Path(), help="Output file path (CSV or JSON based on --format)")
@click.option(
    "--format",
    type=click.Choice(["table", "csv", "json"], case_sensitive=False),
    default="table",
    help="Output format (default: table)",
)
@click.option("--vpc-id", help="Analyze NAT Gateways in specific VPC only")
@click.option("--min-savings", type=float, default=0.0, help="Filter results by minimum annual savings (default: 0)")
@click.option(
    "--recommendation",
    type=click.Choice(["ELIMINATE", "REDUCE", "KEEP"], case_sensitive=False),
    help="Filter by recommendation type",
)
def analyze_nat_traffic(
    profile: Optional[str],
    region: str,
    lookback_days: int,
    output: Optional[str],
    format: str,
    vpc_id: Optional[str],
    min_savings: float,
    recommendation: Optional[str],
):
    """
    Analyze NAT Gateway traffic for VPC Endpoint migration opportunities.

    This command identifies NAT Gateways that can be eliminated or optimized
    through VPC Endpoint migration, potentially saving $100K+ annually.

    Examples:

        # Analyze all NAT Gateways in default region
        runbooks inventory analyze-nat-traffic --profile my-profile

        # Analyze specific VPC with 60-day lookback
        runbooks inventory analyze-nat-traffic --vpc-id vpc-12345 --lookback-days 60

        # Export results to CSV with minimum savings filter
        runbooks inventory analyze-nat-traffic --output nat_analysis.csv --format csv --min-savings 1000

        # Show only ELIMINATE recommendations
        runbooks inventory analyze-nat-traffic --recommendation ELIMINATE
    """
    try:
        console.print("[blue]🔍 NAT Gateway Traffic Analysis - $100K Savings Enabler[/blue]")
        console.print(
            f"[dim]Profile: {profile or 'environment fallback'} | "
            f"Region: {region} | Lookback: {lookback_days} days[/dim]"
        )

        # Apply profile priority system
        operational_profile = get_profile_for_operation("operational", profile)
        print_info(f"Using operational profile: {operational_profile}")

        # Initialize NAT traffic enricher
        enricher = create_nat_traffic_enricher(operational_profile, region)

        # Discover NAT Gateways
        print_info(f"Discovering NAT Gateways in region {region}...")
        ec2 = enricher.session.client("ec2", region_name=region)

        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})
            print_info(f"Filtering by VPC: {vpc_id}")

        nat_gateways_response = ec2.describe_nat_gateways(Filters=filters)
        nat_gateways = nat_gateways_response["NatGateways"]

        if not nat_gateways:
            print_warning(f"No NAT Gateways found in region {region}" + (f" for VPC {vpc_id}" if vpc_id else ""))
            sys.exit(0)

        print_success(f"Found {len(nat_gateways)} NAT Gateway(s)")

        # Enrich with traffic analysis
        enriched_data = enricher.enrich_nat_gateways(nat_gateways, lookback_days, region)

        # Apply filters
        filtered_data = enriched_data

        if min_savings > 0:
            filtered_data = [d for d in filtered_data if d.potential_savings >= min_savings]
            print_info(f"Filtered to {len(filtered_data)} NAT Gateway(s) with savings ≥ ${min_savings:,.2f}")

        if recommendation:
            filtered_data = [d for d in filtered_data if d.recommendation == recommendation.upper()]
            print_info(f"Filtered to {len(filtered_data)} NAT Gateway(s) with recommendation: {recommendation}")

        if not filtered_data:
            print_warning("No NAT Gateways match the specified filters")
            sys.exit(0)

        # Output results
        if format == "table":
            _display_table(filtered_data)
        elif format == "csv":
            _export_csv(filtered_data, output, enricher)
        elif format == "json":
            _export_json(filtered_data, output)

        # Summary statistics
        _display_summary(filtered_data)

    except Exception as e:
        print_error(f"NAT Gateway traffic analysis failed: {str(e)}")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        sys.exit(1)


def _display_table(enriched_data):
    """Display results in Rich table format."""
    table = create_table(
        title="NAT Gateway Traffic Analysis Results",
        columns=[
            ("NAT Gateway ID", "cyan"),
            ("VPC ID", "blue"),
            ("Idle Score", "yellow"),
            ("Recommendation", "green"),
            ("Monthly Cost", "magenta"),
            ("Annual Savings", "green"),
            ("AWS Service %", "cyan"),
            ("VPCE Candidates", "blue"),
        ],
    )

    for nat in enriched_data:
        # Color code recommendations
        rec_color = {
            "ELIMINATE": "[red]ELIMINATE[/red]",
            "REDUCE": "[yellow]REDUCE[/yellow]",
            "KEEP": "[green]KEEP[/green]",
        }.get(nat.recommendation, nat.recommendation)

        table.add_row(
            nat.nat_gateway_id,
            nat.vpc_id,
            str(nat.idle_score),
            rec_color,
            f"${nat.monthly_cost:.2f}",
            f"${nat.potential_savings:,.2f}",
            f"{nat.aws_service_percentage:.1f}%",
            ",".join(nat.migration_candidates) or "None",
        )

    console.print(table)


def _export_csv(enriched_data, output_path, enricher):
    """Export results to CSV format."""
    df = enricher.to_dataframe(enriched_data)

    if output_path:
        df.to_csv(output_path, index=False)
        print_success(f"Results exported to: {output_path}")
    else:
        print(df.to_csv(index=False))


def _export_json(enriched_data, output_path):
    """Export results to JSON format."""
    json_data = [nat.to_dict() for nat in enriched_data]

    if output_path:
        with open(output_path, "w") as f:
            json.dump(json_data, f, indent=2, default=str)
        print_success(f"Results exported to: {output_path}")
    else:
        print(json.dumps(json_data, indent=2, default=str))


def _display_summary(enriched_data):
    """Display summary statistics."""
    total_nat_gateways = len(enriched_data)
    eliminates = sum(1 for d in enriched_data if d.recommendation == "ELIMINATE")
    reduces = sum(1 for d in enriched_data if d.recommendation == "REDUCE")
    keeps = sum(1 for d in enriched_data if d.recommendation == "KEEP")

    total_monthly_cost = sum(d.monthly_cost for d in enriched_data)
    total_annual_savings = sum(d.potential_savings for d in enriched_data)

    console.print("\n[blue]═══ Summary Statistics ═══[/blue]")
    console.print(f"Total NAT Gateways: {total_nat_gateways}")
    console.print(
        f"[red]ELIMINATE: {eliminates}[/red] | [yellow]REDUCE: {reduces}[/yellow] | [green]KEEP: {keeps}[/green]"
    )
    console.print(f"Current Monthly Cost: ${total_monthly_cost:,.2f}")
    console.print(f"[green]💰 Total Annual Savings Potential: ${total_annual_savings:,.2f}[/green]")

    # VPC Endpoint migration summary
    all_candidates = set()
    for d in enriched_data:
        all_candidates.update(d.migration_candidates)

    if all_candidates:
        console.print(f"\n[cyan]VPC Endpoint Migration Candidates: {', '.join(sorted(all_candidates))}[/cyan]")


if __name__ == "__main__":
    analyze_nat_traffic()
