#!/usr/bin/env python3
"""
VPC Endpoint Cleanup Cost Analyzer
==================================

Analyzes VPC endpoint cleanup candidates and calculates cost savings.

Pricing (ap-southeast-2):
- Interface VPCE: $0.01/hour per ENI
- Gateway VPCE: FREE (no charges)

This module provides:
- CSV parsing for VPCE cleanup data
- Cost calculation based on ENI counts
- Account-level aggregation
- Cleanup command generation
"""

import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List

from rich.table import Table

from runbooks.common.rich_utils import console, create_table, format_cost, print_error, print_info, print_success


# AWS Pricing (ap-southeast-2)
VPCE_INTERFACE_HOURLY_RATE = Decimal("0.01")  # $0.01/hour per ENI/AZ
HOURS_PER_MONTH = 720
HOURS_PER_YEAR = 8760


@dataclass
class VPCEndpoint:
    """VPC Endpoint data model."""

    account_id: str
    vpc_name: str
    vpce_id: str
    az_count: int  # Number of availability zones (renamed from enis for consistency)
    notes: str
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    profile: str = ""  # AWS profile for resource access
    region: str = ""  # AWS region
    id: str = ""  # Alias for vpce_id (composition pattern compatibility)
    vpc_id: str = ""  # VPC ID

    def __post_init__(self):
        """Initialize computed fields after dataclass initialization."""
        # Alias id to vpce_id for backward compatibility
        if not self.id:
            self.id = self.vpce_id

    @property
    def enis(self) -> int:
        """Backward compatibility property for enis → az_count."""
        return self.az_count


@dataclass
class AccountSummary:
    """Account-level VPCE summary."""

    account_id: str
    endpoint_count: int
    monthly_cost: float
    annual_cost: float
    endpoints: List[VPCEndpoint]


class VPCEndpointAnalyzer:
    """
    VPC Endpoint cleanup cost analyzer.

    Calculates savings for interface VPC endpoints based on ENI counts.
    Gateway endpoints are FREE and excluded from cost calculations.
    """

    def __init__(self):
        """Initialize VPCE analyzer."""
        self.endpoints: List[VPCEndpoint] = []
        self.account_summaries: Dict[str, AccountSummary] = {}

    def load_from_csv(self, csv_file: Path) -> int:
        """
        Load VPC endpoints from CSV file with automatic deduplication.

        CSV Format (flexible):
        - VPCE cleanup: account_id,profile_name,vpce_id,vpc_name,enis,notes
        - VPC cleanup: account_id,profile_name,vpc_id,vpc_name,Env,...

        **Deduplication Logic** (Track A Data Quality Fix):
        VPCEs can appear in multiple VPCs (shared via peering/PrivateLink).
        Keep FIRST occurrence only to avoid cost inflation.

        Args:
            csv_file: Path to CSV file

        Returns:
            Number of unique endpoints loaded (after deduplication)
        """
        if not csv_file.exists():
            print_error(f"CSV file not found: {csv_file}")
            return 0

        try:
            seen_vpce_ids = set()  # Track processed VPCE IDs
            duplicate_count = 0
            total_rows = 0

            with open(csv_file, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    total_rows += 1

                    # Skip empty rows - check both vpce_id and vpc_id columns
                    vpce_id = row.get("vpce_id") or row.get("vpc_id")
                    if not vpce_id:
                        continue

                    # Deduplication: Skip if VPCE already processed
                    if vpce_id in seen_vpce_ids:
                        duplicate_count += 1
                        continue

                    # Flexible vpc_name column (required)
                    vpc_name = row.get("vpc_name")
                    if not vpc_name:
                        print_error(f"Missing vpc_name column in {csv_file.name}")
                        return 0

                    # Flexible az_count/enis column (required for cost calculation)
                    az_count = row.get("az_count") or row.get("enis") or row.get("ENI", "0")

                    # Flexible notes column (optional)
                    notes = row.get("notes", "")

                    # Optional fields for composition pattern
                    # Support both normalized (aws_profile) and original (AWS-Profile) column names
                    profile = row.get("aws_profile") or row.get("AWS-Profile") or row.get("profile", "")
                    region = row.get("region", "ap-southeast-2")  # Default to ap-southeast-2 if not in CSV
                    vpc_id = row.get("vpc_id", "")

                    endpoint = VPCEndpoint(
                        account_id=row["account_id"],
                        vpc_name=vpc_name,
                        vpce_id=vpce_id,
                        az_count=int(az_count),
                        notes=notes,
                        profile=profile,
                        region=region,
                        vpc_id=vpc_id,
                    )
                    self.endpoints.append(endpoint)
                    seen_vpce_ids.add(vpce_id)  # Mark as processed

            # Report deduplication results
            if duplicate_count > 0:
                from runbooks.common.rich_utils import print_warning, print_info

                print_warning(f"⚠️  CSV contained {duplicate_count} duplicate VPCEs (shared across multiple VPCs)")
                print_info(f"   Deduplicated: {total_rows} rows → {len(self.endpoints)} unique VPCEs")

            print_success(f"Loaded {len(self.endpoints)} unique VPC endpoints from {csv_file.name}")
            return len(self.endpoints)

        except Exception as e:
            print_error(f"Failed to load CSV: {e}")
            return 0

    def calculate_costs(self) -> None:
        """
        Calculate monthly and annual costs for all endpoints.

        Formula:
        - Monthly cost = $0.01/hour × AZ count × 720 hours
        - Annual cost = $0.01/hour × AZ count × 8760 hours
        """
        for endpoint in self.endpoints:
            # Interface VPCE cost = $0.01/hour per AZ
            monthly_cost = float(VPCE_INTERFACE_HOURLY_RATE * endpoint.az_count * HOURS_PER_MONTH)
            annual_cost = float(VPCE_INTERFACE_HOURLY_RATE * endpoint.az_count * HOURS_PER_YEAR)

            endpoint.monthly_cost = monthly_cost
            endpoint.annual_cost = annual_cost

    def aggregate_by_account(self) -> None:
        """Aggregate endpoints by AWS account."""
        by_account = defaultdict(lambda: {"endpoints": [], "monthly": 0.0, "annual": 0.0})

        for endpoint in self.endpoints:
            by_account[endpoint.account_id]["endpoints"].append(endpoint)
            by_account[endpoint.account_id]["monthly"] += endpoint.monthly_cost
            by_account[endpoint.account_id]["annual"] += endpoint.annual_cost

        # Create AccountSummary objects
        for account_id, data in by_account.items():
            self.account_summaries[account_id] = AccountSummary(
                account_id=account_id,
                endpoint_count=len(data["endpoints"]),
                monthly_cost=data["monthly"],
                annual_cost=data["annual"],
                endpoints=data["endpoints"],
            )

    def get_total_savings(self) -> Dict[str, float]:
        """
        Calculate total savings across all accounts.

        Returns:
            Dict with monthly and annual totals
        """
        total_monthly = sum(summary.monthly_cost for summary in self.account_summaries.values())
        total_annual = sum(summary.annual_cost for summary in self.account_summaries.values())

        return {"monthly": total_monthly, "annual": total_annual, "endpoint_count": len(self.endpoints)}

    def display_summary(self, claimed_annual: float = None) -> None:
        """
        Display cost analysis summary with Rich tables.

        Args:
            claimed_annual: Claimed annual savings for comparison (optional)
        """
        totals = self.get_total_savings()

        # Summary table
        print_info("\n" + "=" * 70)
        console.print("[bold cyan]VPC ENDPOINT CLEANUP ANALYSIS[/bold cyan]")
        print_info("=" * 70)

        summary_table = create_table(
            title="Cost Savings Summary",
            columns=[
                {"name": "Metric", "justify": "left"},
                {"name": "Value", "justify": "right"},
            ],
        )

        summary_table.add_row("Total Endpoints", str(totals["endpoint_count"]))
        summary_table.add_row("Monthly Savings", format_cost(totals["monthly"]))
        summary_table.add_row("Annual Savings", format_cost(totals["annual"]))

        # Add comparison if claimed amount provided
        if claimed_annual:
            summary_table.add_row("", "")  # Separator
            summary_table.add_row("Projected Savings", format_cost(claimed_annual))
            summary_table.add_row("Calculated Annual", format_cost(totals["annual"]))

            difference = abs(totals["annual"] - claimed_annual)
            diff_percent = (difference / claimed_annual) * 100 if claimed_annual > 0 else 0

            if diff_percent < 5:
                status = "✅ VALIDATED (within 5%)"
            else:
                status = "⚠️  DISCREPANCY"

            summary_table.add_row("Difference", f"{format_cost(difference)} ({diff_percent:.1f}%)")
            summary_table.add_row("Status", status)

        console.print(summary_table)

        # Account breakdown
        account_table = create_table(
            title="Breakdown by Account",
            columns=[
                {"name": "Account ID", "justify": "left"},
                {"name": "Endpoints", "justify": "right"},
                {"name": "Monthly Cost", "justify": "right"},
                {"name": "Annual Cost", "justify": "right"},
            ],
        )

        for account_id in sorted(self.account_summaries.keys()):
            summary = self.account_summaries[account_id]
            account_table.add_row(
                account_id,
                str(summary.endpoint_count),
                format_cost(summary.monthly_cost),
                format_cost(summary.annual_cost),
            )

        console.print(account_table)

    def generate_cleanup_commands(self, output_file: Path, dry_run: bool = True) -> int:
        """
        Generate AWS CLI cleanup commands organized by account.

        Args:
            output_file: Path to output bash script
            dry_run: Include --dry-run flag (default: True)

        Returns:
            Number of commands generated
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("#!/bin/bash\n")
            f.write("# VPC Endpoint Cleanup Commands\n")
            f.write("# Generated from VPCE cleanup analysis\n\n")
            f.write("# IMPORTANT: Review all commands before execution\n")
            f.write("# Run with --dry-run first to validate\n\n")

            command_count = 0

            for account_id in sorted(self.account_summaries.keys()):
                summary = self.account_summaries[account_id]

                f.write(f"\n# Account: {account_id} ({summary.endpoint_count} endpoints)\n")
                f.write(f"# Annual savings: {format_cost(summary.annual_cost)}\n\n")

                for endpoint in summary.endpoints:
                    f.write(f"# {endpoint.vpc_name} - {format_cost(endpoint.annual_cost)}/year\n")

                    cmd = f"aws ec2 delete-vpc-endpoints --vpc-endpoint-ids {endpoint.vpce_id} --region ap-southeast-2"

                    if dry_run:
                        f.write(f"{cmd} --dry-run\n")
                    else:
                        f.write(f"{cmd}\n")

                    f.write("\n")
                    command_count += 1

        # Make script executable
        output_file.chmod(0o755)

        print_success(f"✅ Cleanup commands written to: {output_file}")
        print_info(f"   Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
        print_info(f"   Commands: {command_count}")

        return command_count

    def export_summary_csv(self, output_file: Path) -> None:
        """
        Export endpoint summary to CSV.

        Args:
            output_file: Path to output CSV file
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="") as f:
            fieldnames = ["account_id", "vpc_name", "vpce_id", "enis", "monthly_cost", "annual_cost", "notes"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for endpoint in self.endpoints:
                writer.writerow(
                    {
                        "account_id": endpoint.account_id,
                        "vpc_name": endpoint.vpc_name,
                        "vpce_id": endpoint.vpce_id,
                        "enis": endpoint.enis,
                        "monthly_cost": endpoint.monthly_cost,
                        "annual_cost": endpoint.annual_cost,
                        "notes": endpoint.notes,
                    }
                )

        print_success(f"✅ Summary CSV written to: {output_file}")


# Convenience function for quick analysis
def analyze_vpce_cleanup(csv_file: Path, claimed_annual: float = None, output_dir: Path = None) -> Dict[str, any]:
    """
    Quick VPCE cleanup analysis.

    Args:
        csv_file: Path to CSV file with VPCE data
        claimed_annual: Claimed annual savings for validation (optional)
        output_dir: Output directory for generated files (optional)

    Returns:
        Analysis results dictionary
    """
    analyzer = VPCEndpointAnalyzer()

    # Load and analyze
    endpoint_count = analyzer.load_from_csv(csv_file)
    if endpoint_count == 0:
        return {"success": False, "error": "no_endpoints_loaded"}

    analyzer.calculate_costs()
    analyzer.aggregate_by_account()

    # Display summary
    analyzer.display_summary(claimed_annual=claimed_annual)

    # Generate outputs if directory provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Cleanup commands
        commands_file = output_dir / "vpce-cleanup-commands.sh"
        analyzer.generate_cleanup_commands(commands_file, dry_run=True)

        # Summary CSV
        summary_file = output_dir / "vpce-cleanup-summary.csv"
        analyzer.export_summary_csv(summary_file)

    # Return results
    totals = analyzer.get_total_savings()
    return {
        "success": True,
        "endpoint_count": totals["endpoint_count"],
        "monthly_savings": totals["monthly"],
        "annual_savings": totals["annual"],
        "account_count": len(analyzer.account_summaries),
    }


if __name__ == "__main__":
    # Demo usage
    from runbooks.common.rich_utils import print_header

    print_header("VPC Endpoint Analyzer", "Demo")

    # Example data
    demo_csv = Path("tmp/vpce-cleanup-data.csv")

    if demo_csv.exists():
        result = analyze_vpce_cleanup(csv_file=demo_csv, claimed_annual=None, output_dir=Path("tmp"))

        if result["success"]:
            print_success(f"\n✅ Analysis complete: {result['endpoint_count']} endpoints analyzed")
    else:
        print_info("Demo CSV not found. Usage:")
        print_info("  python -m runbooks.vpc.vpce_analyzer")
