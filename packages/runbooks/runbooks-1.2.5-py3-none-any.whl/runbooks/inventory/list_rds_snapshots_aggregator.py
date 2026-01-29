#!/usr/bin/env python3
"""
Enhanced RDS Snapshot Discovery via AWS Config Organization Aggregator

Root Cause Solution: AWS Config organization-aggregator provides cross-account access to RDS snapshots
where direct RDS API calls fail due to permissions. This module fixes the infrastructure to discover
all enterprise resources across 65 accounts using the proven Config aggregator approach.

Gap Analysis Results:
- AWS Config aggregator in ap-southeast-2 with 'organization-aggregator'
- Uses MANAGEMENT_PROFILE successfully for cross-account access
- Found 42 snapshots from target account 142964829704 (proves access works)
- Gap: Need multi-region support and remove query limits for full 303 snapshots

Business Case: Enhanced RDS snapshot lifecycle management with comprehensive cross-account visibility
Target Coverage: 65 AWS accounts with enterprise resource discovery capabilities
Strategic Value: Infrastructure governance and cost optimization through automated snapshot analysis
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import click
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_table,
    create_progress_bar,
    format_cost,
)
from ..common.profile_utils import get_profile_for_operation

logger = logging.getLogger(__name__)


class RDSSnapshotConfigAggregator:
    """
    Enhanced RDS Snapshot Discovery using AWS Config Organization Aggregator

    Solves cross-account access limitations by leveraging AWS Config's organization-aggregator
    to discover RDS snapshots across all accounts where direct RDS API access fails.
    """

    def __init__(self, management_profile: str = None, max_workers: int = 10):
        """
        Initialize RDS snapshot discovery with Config aggregator integration

        Args:
            management_profile: AWS profile with Config aggregator access
            max_workers: Maximum concurrent workers for multi-region discovery
        """
        self.management_profile = management_profile
        self.max_workers = max_workers

        # Config aggregator regions for comprehensive coverage
        self.config_regions = [
            "ap-southeast-2",
            "ap-southeast-6",
            "eu-west-1",
            "ap-southeast-2",
            "ap-northeast-1",
            "ca-central-1",
            "eu-central-1",
        ]

        # Session management
        self.session = None
        self.discovered_aggregators = {}
        self.snapshot_inventory = []

        # Performance metrics
        self.metrics = {
            "aggregators_found": 0,
            "snapshots_discovered": 0,
            "accounts_covered": 0,
            "regions_scanned": 0,
            "api_calls_made": 0,
            "errors_encountered": 0,
        }

    def initialize_session(self) -> bool:
        """Initialize AWS session with management profile"""
        try:
            profile = get_profile_for_operation("management", self.management_profile)
            self.session = boto3.Session(profile_name=profile)

            # Verify access with STS
            sts_client = self.session.client("sts")
            identity = sts_client.get_caller_identity()

            print_success(f"✅ Initialized session with profile: {profile}")
            console.print(f"[dim]Account: {identity['Account']} | ARN: {identity['Arn']}[/dim]")

            return True

        except Exception as e:
            print_error(f"Failed to initialize session: {e}")
            return False

    def discover_config_aggregators(self) -> Dict[str, List[str]]:
        """
        Discover AWS Config aggregators across all regions

        Returns:
            Dict mapping regions to list of aggregator names
        """
        print_info("🔍 Discovering AWS Config aggregators across regions...")

        aggregator_map = {}

        with create_progress_bar() as progress:
            task_id = progress.add_task("Scanning regions for Config aggregators...", total=len(self.config_regions))

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_region = {
                    executor.submit(self._find_aggregators_in_region, region): region for region in self.config_regions
                }

                for future in as_completed(future_to_region):
                    region = future_to_region[future]
                    try:
                        aggregators = future.result()
                        if aggregators:
                            aggregator_map[region] = aggregators
                            self.metrics["aggregators_found"] += len(aggregators)
                            console.print(f"[green]✓[/green] {region}: Found {len(aggregators)} aggregator(s)")
                        else:
                            console.print(f"[dim]○[/dim] {region}: No aggregators found")

                        self.metrics["regions_scanned"] += 1

                    except Exception as e:
                        print_warning(f"❌ {region}: {str(e)}")
                        self.metrics["errors_encountered"] += 1

                    progress.advance(task_id)

        self.discovered_aggregators = aggregator_map

        # Summary
        total_aggregators = sum(len(aggs) for aggs in aggregator_map.values())
        if total_aggregators > 0:
            print_success(f"✅ Found {total_aggregators} Config aggregators across {len(aggregator_map)} regions")
        else:
            print_warning("⚠️ No Config aggregators found - RDS snapshot discovery will be limited")

        return aggregator_map

    def _find_aggregators_in_region(self, region: str) -> List[str]:
        """Find Config aggregators in a specific region"""
        try:
            config_client = self.session.client("config", region_name=region)

            # List configuration aggregators
            response = config_client.describe_configuration_aggregators()
            self.metrics["api_calls_made"] += 1

            aggregators = []
            for aggregator in response.get("ConfigurationAggregators", []):
                aggregator_name = aggregator["ConfigurationAggregatorName"]
                aggregators.append(aggregator_name)

                # Log aggregator details for debugging
                logger.debug(f"Found aggregator {aggregator_name} in {region}")
                if "OrganizationAggregationSource" in aggregator:
                    org_source = aggregator["OrganizationAggregationSource"]
                    logger.debug(f"Organization aggregator: AllAwsRegions={org_source.get('AllAwsRegions', False)}")

            return aggregators

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code in ["AccessDenied", "UnauthorizedOperation"]:
                logger.debug(f"No Config access in {region}: {error_code}")
            else:
                logger.warning(f"Config API error in {region}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in {region}: {e}")
            return []

    def discover_rds_snapshots_via_aggregator(self, target_account_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Discover RDS snapshots using Config aggregators

        Args:
            target_account_ids: Specific account IDs to filter (None for all accounts)

        Returns:
            List of RDS snapshot dictionaries with comprehensive metadata
        """
        print_header("RDS Snapshot Discovery via Config Aggregator")

        all_snapshots = []

        if not self.discovered_aggregators:
            print_warning("No Config aggregators available - discovering now...")
            self.discover_config_aggregators()

        if not self.discovered_aggregators:
            print_error("No Config aggregators found - cannot proceed with discovery")
            return []

        # Process each region's aggregators
        with create_progress_bar() as progress:
            total_aggregators = sum(len(aggs) for aggs in self.discovered_aggregators.values())
            task_id = progress.add_task("Discovering RDS snapshots via Config aggregators...", total=total_aggregators)

            for region, aggregators in self.discovered_aggregators.items():
                console.print(f"\n[cyan]🔍 Processing Config aggregators in {region}[/cyan]")

                for aggregator_name in aggregators:
                    try:
                        snapshots = self._query_snapshots_from_aggregator(region, aggregator_name, target_account_ids)

                        if snapshots:
                            all_snapshots.extend(snapshots)
                            unique_accounts = set(s.get("AccountId", "unknown") for s in snapshots)
                            console.print(
                                f"[green]✓[/green] {aggregator_name}: "
                                f"Found {len(snapshots)} snapshots across {len(unique_accounts)} accounts"
                            )
                        else:
                            console.print(f"[dim]○[/dim] {aggregator_name}: No snapshots found")

                    except Exception as e:
                        print_warning(f"❌ {aggregator_name}: {str(e)}")
                        self.metrics["errors_encountered"] += 1

                    progress.advance(task_id)

        # Update metrics
        self.metrics["snapshots_discovered"] = len(all_snapshots)
        unique_accounts = set(s.get("AccountId", "unknown") for s in all_snapshots)
        self.metrics["accounts_covered"] = len(unique_accounts)

        # Summary
        if all_snapshots:
            print_success(
                f"✅ Discovery complete: {len(all_snapshots)} RDS snapshots across {len(unique_accounts)} accounts"
            )
        else:
            print_warning("⚠️ No RDS snapshots discovered via Config aggregators")

        self.snapshot_inventory = all_snapshots
        return all_snapshots

    def _query_snapshots_from_aggregator(
        self, region: str, aggregator_name: str, target_account_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Query RDS snapshots from a specific Config aggregator"""
        try:
            config_client = self.session.client("config", region_name=region)

            # Base query for RDS DB snapshots
            query_expression = """
            SELECT
                resourceId,
                resourceName,
                accountId,
                awsRegion,
                resourceType,
                configuration,
                configurationItemCaptureTime,
                resourceCreationTime
            WHERE
                resourceType = 'AWS::RDS::DBSnapshot'
            """

            # Add account filter if specified
            if target_account_ids:
                accounts_filter = "', '".join(target_account_ids)
                query_expression += f" AND accountId IN ('{accounts_filter}')"

            # Execute query with pagination support
            snapshots = []
            next_token = None

            while True:
                query_params = {
                    "ConfigurationAggregatorName": aggregator_name,
                    "Expression": query_expression,
                    "Limit": 100,  # Maximum allowed by Config API
                }

                if next_token:
                    query_params["NextToken"] = next_token

                response = config_client.select_aggregate_resource_config(**query_params)
                self.metrics["api_calls_made"] += 1

                # Process results
                for result in response.get("Results", []):
                    try:
                        snapshot_data = json.loads(result)
                        processed_snapshot = self._process_config_snapshot_result(snapshot_data)
                        if processed_snapshot:
                            snapshots.append(processed_snapshot)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse Config result: {e}")
                    except Exception as e:
                        logger.warning(f"Failed to process snapshot data: {e}")

                # Check for more results
                next_token = response.get("NextToken")
                if not next_token:
                    break

            return snapshots

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchConfigurationAggregatorException":
                logger.warning(f"Aggregator {aggregator_name} not found in {region}")
            elif error_code in ["AccessDenied", "UnauthorizedOperation"]:
                logger.warning(f"Access denied to aggregator {aggregator_name} in {region}")
            else:
                logger.error(f"Config aggregator query failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying aggregator {aggregator_name}: {e}")
            return []

    def _process_config_snapshot_result(self, config_data: Dict) -> Optional[Dict]:
        """Process Config aggregator result into standardized snapshot format"""
        try:
            # Extract base metadata
            snapshot_info = {
                "DBSnapshotIdentifier": config_data.get("resourceId", "unknown"),
                "AccountId": config_data.get("accountId", "unknown"),
                "Region": config_data.get("awsRegion", "unknown"),
                "DiscoveryMethod": "config_aggregator",
                "ConfigCaptureTime": config_data.get("configurationItemCaptureTime"),
                "ResourceCreationTime": config_data.get("resourceCreationTime"),
            }

            # Parse configuration details if available
            configuration = config_data.get("configuration", {})
            if isinstance(configuration, str):
                try:
                    configuration = json.loads(configuration)
                except json.JSONDecodeError:
                    configuration = {}

            # Extract RDS-specific details
            if configuration:
                snapshot_info.update(
                    {
                        "DBInstanceIdentifier": configuration.get("dBInstanceIdentifier", "unknown"),
                        "SnapshotType": configuration.get("snapshotType", "unknown"),
                        "Status": configuration.get("status", "unknown"),
                        "Engine": configuration.get("engine", "unknown"),
                        "EngineVersion": configuration.get("engineVersion", "unknown"),
                        "AllocatedStorage": configuration.get("allocatedStorage", 0),
                        "StorageType": configuration.get("storageType", "unknown"),
                        "Encrypted": configuration.get("encrypted", False),
                        "SnapshotCreateTime": configuration.get("snapshotCreateTime"),
                        "InstanceCreateTime": configuration.get("instanceCreateTime"),
                        "MasterUsername": configuration.get("masterUsername", "unknown"),
                        "Port": configuration.get("port", 0),
                        "VpcId": configuration.get("vpcId"),
                        "AvailabilityZone": configuration.get("availabilityZone"),
                        "LicenseModel": configuration.get("licenseModel", "unknown"),
                        "OptionGroupName": configuration.get("optionGroupName"),
                        "PercentProgress": configuration.get("percentProgress", 0),
                        "SourceRegion": configuration.get("sourceRegion"),
                        "SourceDBSnapshotIdentifier": configuration.get("sourceDBSnapshotIdentifier"),
                        "StorageEncrypted": configuration.get("storageEncrypted", False),
                        "KmsKeyId": configuration.get("kmsKeyId"),
                        "Timezone": configuration.get("timezone"),
                        "IAMDatabaseAuthenticationEnabled": configuration.get(
                            "iAMDatabaseAuthenticationEnabled", False
                        ),
                        "ProcessorFeatures": configuration.get("processorFeatures", []),
                        "DbiResourceId": configuration.get("dbiResourceId"),
                        "TagList": configuration.get("tagList", []),
                    }
                )

            # Calculate age and estimated cost
            if snapshot_info.get("SnapshotCreateTime"):
                try:
                    create_time = datetime.fromisoformat(snapshot_info["SnapshotCreateTime"].replace("Z", "+00:00"))
                    age_days = (datetime.now(timezone.utc) - create_time).days
                    snapshot_info["AgeDays"] = age_days

                    # Estimate storage cost (basic calculation)
                    allocated_storage = snapshot_info.get("AllocatedStorage", 0)
                    if allocated_storage > 0:
                        # Basic cost estimation - $0.095 per GB-month for snapshot storage
                        monthly_cost = allocated_storage * 0.095
                        snapshot_info["EstimatedMonthlyCost"] = round(monthly_cost, 2)
                        snapshot_info["EstimatedAnnualCost"] = round(monthly_cost * 12, 2)

                except Exception as e:
                    logger.debug(f"Failed to calculate snapshot age: {e}")
                    snapshot_info["AgeDays"] = 0

            return snapshot_info

        except Exception as e:
            logger.warning(f"Failed to process Config snapshot result: {e}")
            return None

    def filter_snapshots(
        self,
        snapshots: List[Dict],
        account_filter: Optional[List[str]] = None,
        age_filter_days: Optional[int] = None,
        snapshot_type_filter: Optional[str] = None,
        engine_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Apply filters to discovered snapshots

        Args:
            snapshots: List of snapshot dictionaries
            account_filter: Filter by specific account IDs
            age_filter_days: Filter snapshots older than X days
            snapshot_type_filter: Filter by snapshot type (manual, automated)
            engine_filter: Filter by database engine

        Returns:
            Filtered list of snapshots
        """
        filtered_snapshots = snapshots.copy()

        # Account filter
        if account_filter:
            filtered_snapshots = [s for s in filtered_snapshots if s.get("AccountId") in account_filter]
            console.print(f"[dim]Account filter: {len(filtered_snapshots)} snapshots[/dim]")

        # Age filter
        if age_filter_days is not None:
            filtered_snapshots = [s for s in filtered_snapshots if s.get("AgeDays", 0) >= age_filter_days]
            console.print(f"[dim]Age filter (>{age_filter_days}d): {len(filtered_snapshots)} snapshots[/dim]")

        # Snapshot type filter
        if snapshot_type_filter:
            filtered_snapshots = [
                s for s in filtered_snapshots if s.get("SnapshotType", "").lower() == snapshot_type_filter.lower()
            ]
            console.print(f"[dim]Type filter ({snapshot_type_filter}): {len(filtered_snapshots)} snapshots[/dim]")

        # Engine filter
        if engine_filter:
            filtered_snapshots = [s for s in filtered_snapshots if engine_filter.lower() in s.get("Engine", "").lower()]
            console.print(f"[dim]Engine filter ({engine_filter}): {len(filtered_snapshots)} snapshots[/dim]")

        return filtered_snapshots

    def generate_summary_report(self, snapshots: List[Dict]) -> Dict:
        """Generate comprehensive summary report of discovered snapshots"""
        if not snapshots:
            return {"total_snapshots": 0, "summary": "No snapshots discovered"}

        # Basic statistics
        total_snapshots = len(snapshots)
        unique_accounts = set(s.get("AccountId", "unknown") for s in snapshots)
        unique_regions = set(s.get("Region", "unknown") for s in snapshots)
        unique_engines = set(s.get("Engine", "unknown") for s in snapshots)

        # Snapshot type breakdown
        manual_snapshots = [s for s in snapshots if s.get("SnapshotType", "").lower() == "manual"]
        automated_snapshots = [s for s in snapshots if s.get("SnapshotType", "").lower() == "automated"]

        # Age analysis
        aged_snapshots = [s for s in snapshots if s.get("AgeDays", 0) >= 90]  # 3+ months
        very_old_snapshots = [s for s in snapshots if s.get("AgeDays", 0) >= 180]  # 6+ months

        # Storage analysis
        total_storage = sum(s.get("AllocatedStorage", 0) for s in snapshots)
        total_estimated_cost = sum(s.get("EstimatedMonthlyCost", 0) for s in snapshots)

        # Encryption analysis
        encrypted_snapshots = [s for s in snapshots if s.get("Encrypted", False)]

        return {
            "total_snapshots": total_snapshots,
            "unique_accounts": len(unique_accounts),
            "unique_regions": len(unique_regions),
            "unique_engines": len(unique_engines),
            "account_ids": sorted(list(unique_accounts)),
            "regions": sorted(list(unique_regions)),
            "engines": sorted(list(unique_engines)),
            "snapshot_types": {
                "manual": len(manual_snapshots),
                "automated": len(automated_snapshots),
                "unknown": total_snapshots - len(manual_snapshots) - len(automated_snapshots),
            },
            "age_analysis": {
                "aged_snapshots_90d": len(aged_snapshots),
                "very_old_snapshots_180d": len(very_old_snapshots),
                "cleanup_candidates": len([s for s in manual_snapshots if s.get("AgeDays", 0) >= 90]),
            },
            "storage_analysis": {
                "total_storage_gb": total_storage,
                "estimated_monthly_cost": round(total_estimated_cost, 2),
                "estimated_annual_cost": round(total_estimated_cost * 12, 2),
            },
            "security_analysis": {
                "encrypted_snapshots": len(encrypted_snapshots),
                "unencrypted_snapshots": total_snapshots - len(encrypted_snapshots),
                "encryption_percentage": round((len(encrypted_snapshots) / total_snapshots) * 100, 1)
                if total_snapshots > 0
                else 0,
            },
            "discovery_metrics": self.metrics,
        }

    def export_results(self, snapshots: List[Dict], output_file: str, format: str = "csv") -> bool:
        """Export snapshot results to file"""
        try:
            if format.lower() == "csv":
                import csv

                if not snapshots:
                    console.print("[yellow]No snapshots to export[/yellow]")
                    return False

                # Get all possible keys from snapshots
                all_keys = set()
                for snapshot in snapshots:
                    all_keys.update(snapshot.keys())

                fieldnames = sorted(list(all_keys))

                with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for snapshot in snapshots:
                        # Convert complex objects to strings for CSV
                        row = {}
                        for key in fieldnames:
                            value = snapshot.get(key, "")
                            if isinstance(value, (list, dict)):
                                row[key] = json.dumps(value)
                            else:
                                row[key] = str(value) if value is not None else ""
                        writer.writerow(row)

            elif format.lower() == "json":
                with open(output_file, "w", encoding="utf-8") as jsonfile:
                    json.dump(snapshots, jsonfile, indent=2, default=str)

            else:
                print_error(f"Unsupported export format: {format}")
                return False

            print_success(f"✅ Exported {len(snapshots)} snapshots to {output_file}")
            return True

        except Exception as e:
            print_error(f"Failed to export results: {e}")
            return False


@click.command()
@click.option("--profile", help="AWS profile with Config aggregator access (overrides environment)")
@click.option("--target-accounts", multiple=True, help="Specific account IDs to analyze")
@click.option("--regions", multiple=True, help="Specific regions to check for aggregators")
@click.option("--age-filter", type=int, help="Filter snapshots older than X days")
@click.option("--snapshot-type", type=click.Choice(["manual", "automated"]), help="Filter by snapshot type")
@click.option("--engine-filter", help="Filter by database engine (partial match)")
@click.option("--output-file", default="./rds_snapshots_config_discovery.csv", help="Output file path")
@click.option("--format", type=click.Choice(["csv", "json"]), default="csv", help="Output format")
@click.option("--max-workers", type=int, default=10, help="Maximum concurrent workers")
@click.option("--summary-only", is_flag=True, help="Show only summary report")
def discover_rds_snapshots(
    profile: str,
    target_accounts: Tuple[str],
    regions: Tuple[str],
    age_filter: int,
    snapshot_type: str,
    engine_filter: str,
    output_file: str,
    format: str,
    max_workers: int,
    summary_only: bool,
):
    """
    Enhanced RDS Snapshot Discovery via AWS Config Organization Aggregator

    Solves cross-account access limitations by leveraging AWS Config's organization-aggregator
    to discover RDS snapshots across all enterprise accounts where direct RDS API access fails.

    Examples:
        # Discover all snapshots across the organization
        runbooks inventory rds-snapshots-config --profile management-profile

        # Target specific accounts
        runbooks inventory rds-snapshots-config --target-accounts 142964829704 --target-accounts 363435891329

        # Focus on old manual snapshots for cleanup
        runbooks inventory rds-snapshots-config --snapshot-type manual --age-filter 90

        # Export to JSON format
        runbooks inventory rds-snapshots-config --format json --output-file snapshots.json
    """
    try:
        print_header("Enhanced RDS Snapshot Discovery via Config Aggregator", "v1.0")

        # Initialize discovery engine
        aggregator = RDSSnapshotConfigAggregator(management_profile=profile, max_workers=max_workers)

        # Override default regions if specified
        if regions:
            aggregator.config_regions = list(regions)
            console.print(f"[dim]Using custom regions: {', '.join(regions)}[/dim]")

        # Initialize session
        if not aggregator.initialize_session():
            return

        # Discover Config aggregators
        aggregator_map = aggregator.discover_config_aggregators()
        if not aggregator_map:
            print_error("❌ No Config aggregators found - cannot proceed with discovery")
            return

        # Discover RDS snapshots
        target_account_list = list(target_accounts) if target_accounts else None
        snapshots = aggregator.discover_rds_snapshots_via_aggregator(target_account_list)

        if not snapshots:
            print_warning("⚠️ No RDS snapshots discovered")
            return

        # Apply filters
        if age_filter or snapshot_type or engine_filter:
            console.print("\n[cyan]🔍 Applying filters...[/cyan]")
            snapshots = aggregator.filter_snapshots(
                snapshots,
                account_filter=target_account_list,
                age_filter_days=age_filter,
                snapshot_type_filter=snapshot_type,
                engine_filter=engine_filter,
            )

        # Generate summary report
        summary = aggregator.generate_summary_report(snapshots)

        # Display summary
        print_header("Discovery Summary")

        summary_table = create_table(
            title="RDS Snapshot Discovery Results",
            columns=[{"header": "Metric", "style": "cyan"}, {"header": "Value", "style": "green bold"}],
        )

        summary_table.add_row("Total Snapshots", str(summary["total_snapshots"]))
        summary_table.add_row("Unique Accounts", str(summary["unique_accounts"]))
        summary_table.add_row("Unique Regions", str(summary["unique_regions"]))
        summary_table.add_row("Database Engines", str(summary["unique_engines"]))
        summary_table.add_row("Manual Snapshots", str(summary["snapshot_types"]["manual"]))
        summary_table.add_row("Automated Snapshots", str(summary["snapshot_types"]["automated"]))
        summary_table.add_row("Old Snapshots (90d+)", str(summary["age_analysis"]["aged_snapshots_90d"]))
        summary_table.add_row("Cleanup Candidates", str(summary["age_analysis"]["cleanup_candidates"]))
        summary_table.add_row("Total Storage (GB)", str(summary["storage_analysis"]["total_storage_gb"]))
        summary_table.add_row("Est. Monthly Cost", format_cost(summary["storage_analysis"]["estimated_monthly_cost"]))
        summary_table.add_row("Est. Annual Cost", format_cost(summary["storage_analysis"]["estimated_annual_cost"]))
        summary_table.add_row(
            "Encrypted Snapshots",
            f"{summary['security_analysis']['encrypted_snapshots']} ({summary['security_analysis']['encryption_percentage']}%)",
        )

        console.print(summary_table)

        # Discovery metrics
        metrics_table = create_table(
            title="Discovery Performance Metrics",
            columns=[{"header": "Metric", "style": "blue"}, {"header": "Count", "style": "yellow"}],
        )

        metrics = summary["discovery_metrics"]
        metrics_table.add_row("Config Aggregators Found", str(metrics["aggregators_found"]))
        metrics_table.add_row("Regions Scanned", str(metrics["regions_scanned"]))
        metrics_table.add_row("API Calls Made", str(metrics["api_calls_made"]))
        metrics_table.add_row("Errors Encountered", str(metrics["errors_encountered"]))

        console.print(metrics_table)

        # Account details
        if summary["account_ids"] and len(summary["account_ids"]) <= 20:  # Don't flood output
            console.print(f"\n[cyan]📋 Accounts with RDS snapshots:[/cyan]")
            for account_id in summary["account_ids"]:
                account_snapshots = [s for s in snapshots if s.get("AccountId") == account_id]
                console.print(f"  [green]•[/green] {account_id}: {len(account_snapshots)} snapshots")

        # Export results unless summary-only
        if not summary_only:
            if aggregator.export_results(snapshots, output_file, format):
                console.print(f"\n[green]📁 Results exported to: {output_file}[/green]")

        # Configuration recommendations
        console.print(f"\n[cyan]💡 Configuration Details:[/cyan]")
        for region, aggregators in aggregator_map.items():
            console.print(f"  [blue]•[/blue] {region}: {', '.join(aggregators)}")

        if summary["age_analysis"]["cleanup_candidates"] > 0:
            print_warning(
                f"🎯 Found {summary['age_analysis']['cleanup_candidates']} manual snapshots "
                f"older than 90 days - consider cleanup for cost optimization"
            )

        if summary["security_analysis"]["unencrypted_snapshots"] > 0:
            print_warning(
                f"🔒 Found {summary['security_analysis']['unencrypted_snapshots']} unencrypted snapshots "
                f"- review for security compliance"
            )

    except Exception as e:
        print_error(f"Discovery failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    discover_rds_snapshots()
