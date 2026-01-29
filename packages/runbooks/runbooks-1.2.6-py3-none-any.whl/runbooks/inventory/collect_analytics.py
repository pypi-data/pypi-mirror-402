#!/usr/bin/env python3
"""
AWS Analytics Resource Discovery CLI.

Discovers and inventories analytics resources including:
- Athena workgroups with configuration and state
- AWS Glue databases, tables, and crawlers
- Cost optimization opportunities for analytics services

Business Value:
- Analytics cost optimization (15-25% savings potential)
- Data governance compliance
- Unused workgroup/database cleanup
- Cross-account analytics resource discovery

Usage:
    # Collect analytics resources with default profile
    python collect_analytics.py

    # Collect with specific AWS profile
    python collect_analytics.py --profile ops-profile

    # Collect with cost information
    python collect_analytics.py --profile ops-profile --include-costs

    # Export to CSV
    python collect_analytics.py --profile ops-profile --output analytics-inventory.csv --format csv
"""

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import click
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from runbooks.common.rich_utils import console, print_error, print_info, print_success, print_warning
from runbooks.inventory.collectors.aws_analytics import AnalyticsCollector
from runbooks.inventory.collectors.base import CollectionContext
from runbooks.inventory.models.account import AWSAccount


@click.command()
@click.option(
    "--profile",
    envvar="CENTRALISED_OPS_PROFILE",
    default=None,
    help="AWS profile to use for authentication",
)
@click.option(
    "--region",
    default="ap-southeast-2",
    help="AWS region to scan",
)
@click.option(
    "--all-regions",
    is_flag=True,
    help="Scan all enabled AWS regions",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path",
)
@click.option(
    "--format",
    type=click.Choice(["csv", "json", "table"]),
    default="table",
    help="Output format",
)
@click.option(
    "--include-costs",
    is_flag=True,
    help="Include cost estimation for resources",
)
@click.option(
    "--resource-type",
    type=click.Choice(["athena:workgroup", "glue:database", "glue:table", "glue:crawler", "all"]),
    default=["all"],
    multiple=True,
    help="Specific resource types to collect",
)
def collect_analytics(
    profile: Optional[str],
    region: str,
    all_regions: bool,
    output: Optional[str],
    format: str,
    include_costs: bool,
    resource_type: tuple,
):
    """
    Discover AWS Analytics resources (Athena, Glue).

    This command performs comprehensive discovery of analytics infrastructure
    across your AWS environment, enabling cost optimization and governance.

    Examples:
        \b
        # Basic discovery with default profile
        runbooks inventory collect-analytics

        \b
        # Discover with specific profile and export to CSV
        runbooks inventory collect-analytics --profile ops-profile --output analytics.csv --format csv

        \b
        # Discover only Athena workgroups with cost information
        runbooks inventory collect-analytics --resource-type athena:workgroup --include-costs
    """
    try:
        print_info("Starting AWS Analytics resource discovery...")

        # Create boto3 session
        if profile:
            session = boto3.Session(profile_name=profile)
            print_info(f"Using AWS profile: {profile}")
        else:
            session = boto3.Session()
            print_info("Using default AWS credentials")

        # Get account ID
        sts_client = session.client("sts")
        account_id = sts_client.get_caller_identity()["Account"]
        account = AWSAccount(account_id=account_id, account_name=f"Account-{account_id}")

        # Determine regions to scan
        regions_to_scan = []
        if all_regions:
            ec2_client = session.client("ec2", region_name="ap-southeast-2")
            regions_response = ec2_client.describe_regions(
                Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}]
            )
            regions_to_scan = [r["RegionName"] for r in regions_response["Regions"]]
            print_info(f"Scanning all {len(regions_to_scan)} enabled regions")
        else:
            regions_to_scan = [region]
            print_info(f"Scanning region: {region}")

        # Determine resource types to collect
        if "all" in resource_type:
            resource_types_set = {
                "athena:workgroup",
                "glue:database",
                "glue:table",
                "glue:crawler",
            }
        else:
            resource_types_set = set(resource_type)

        print_info(f"Collecting resource types: {', '.join(resource_types_set)}")

        # Collect resources from all regions
        all_resources = []
        collector = AnalyticsCollector(session=session)

        for scan_region in regions_to_scan:
            print_info(f"Discovering analytics resources in {scan_region}...")

            context = CollectionContext(
                account=account,
                region=scan_region,
                resource_types=resource_types_set,
                include_costs=include_costs,
            )

            try:
                resources = collector.collect_resources(context)
                all_resources.extend(resources)
                print_success(f"Found {len(resources)} analytics resources in {scan_region}")
            except Exception as e:
                print_warning(f"Failed to collect from {scan_region}: {e}")
                continue

        # Generate summary statistics
        summary = {}
        for resource in all_resources:
            resource_type = resource.resource_type
            summary[resource_type] = summary.get(resource_type, 0) + 1

        print_success(f"\nDiscovery complete! Found {len(all_resources)} total resources")
        print_info("Resource breakdown:")
        for res_type, count in summary.items():
            print_info(f"  {res_type}: {count}")

        # Handle output
        if output or format != "table":
            output_path = (
                output or f"data/outputs/analytics-discovered-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{format}"
            )

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

            if format == "csv":
                _export_csv(all_resources, output_path)
            elif format == "json":
                _export_json(all_resources, output_path)
            else:
                _display_table(all_resources)

            if output:
                print_success(f"Results exported to: {output_path}")

        else:
            _display_table(all_resources)

    except Exception as e:
        print_error(f"Analytics discovery failed: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


def _export_csv(resources: List, output_path: str):
    """Export resources to CSV format."""
    if not resources:
        print_warning("No resources to export")
        return

    # Extract flat dictionary representation
    rows = []
    for resource in resources:
        row = {
            "resource_id": resource.resource_id,
            "resource_type": resource.resource_type,
            "resource_name": resource.resource_name,
            "account_id": resource.account_id,
            "region": resource.region,
            "state": resource.state.value if hasattr(resource.state, "value") else str(resource.state),
            "creation_date": resource.creation_date.isoformat() if resource.creation_date else "",
            "monthly_cost": resource.cost_info.monthly_cost if resource.cost_info else 0.0,
        }

        # Add flattened configuration
        if resource.configuration:
            for key, value in resource.configuration.items():
                # Flatten nested structures
                if isinstance(value, (dict, list)):
                    row[f"config_{key}"] = json.dumps(value)
                else:
                    row[f"config_{key}"] = value

        rows.append(row)

    # Write CSV
    with open(output_path, "w", newline="") as csvfile:
        if rows:
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print_info(f"Exported {len(rows)} resources to CSV")


def _export_json(resources: List, output_path: str):
    """Export resources to JSON format."""
    # Convert resources to dictionaries
    resources_dict = []
    for resource in resources:
        resource_dict = {
            "resource_id": resource.resource_id,
            "resource_type": resource.resource_type,
            "resource_name": resource.resource_name,
            "resource_arn": resource.resource_arn,
            "account_id": resource.account_id,
            "region": resource.region,
            "state": resource.state.value if hasattr(resource.state, "value") else str(resource.state),
            "creation_date": resource.creation_date.isoformat() if resource.creation_date else None,
            "configuration": resource.configuration,
            "tags": resource.tags,
        }

        if resource.cost_info:
            resource_dict["cost_info"] = {
                "monthly_cost": resource.cost_info.monthly_cost,
                "currency": resource.cost_info.currency,
            }

        resources_dict.append(resource_dict)

    with open(output_path, "w") as jsonfile:
        json.dump(
            {
                "discovery_timestamp": datetime.now().isoformat(),
                "total_resources": len(resources_dict),
                "resources": resources_dict,
            },
            jsonfile,
            indent=2,
        )

    print_info(f"Exported {len(resources_dict)} resources to JSON")


def _display_table(resources: List):
    """Display resources in a Rich table format."""
    from rich.table import Table

    table = Table(title="AWS Analytics Resources", show_lines=True)

    table.add_column("Resource Type", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Region", style="blue")
    table.add_column("State", style="yellow")
    table.add_column("Created", style="magenta")

    for resource in resources:
        table.add_row(
            resource.resource_type,
            resource.resource_name,
            resource.region,
            resource.state.value if hasattr(resource.state, "value") else str(resource.state),
            resource.creation_date.strftime("%Y-%m-%d") if resource.creation_date else "N/A",
        )

    console.print(table)


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    collect_analytics()
