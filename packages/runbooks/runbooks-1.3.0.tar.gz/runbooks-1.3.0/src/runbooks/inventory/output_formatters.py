#!/usr/bin/env python3
"""
Output formatting utilities for Organizations module.

This module provides consistent multi-format export capabilities for
Organizations inventory scripts supporting JSON, CSV, Markdown, and
Rich table formats.

Features:
    - Rich table formatting with CloudOps theme
    - Multi-format export (JSON, CSV, Markdown, Table)
    - Account metadata formatting utilities
    - Organizations hierarchy visualization helpers

Author: Runbooks Team
Version: 1.1.10
"""

import csv
import json
import logging
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.table import Table

from runbooks.common.rich_utils import console, create_table, print_error, print_success
from runbooks.common.config_loader import get_config_loader

logger = logging.getLogger(__name__)


class OrganizationsFormatter:
    """Format Organizations data for various output types."""

    @staticmethod
    def format_accounts_table(accounts: List[Dict], title: str = "AWS Organization Accounts") -> Table:
        """
        Create Rich table for accounts listing.

        Args:
            accounts: List of account dictionaries with keys:
                - id: Account ID
                - name: Account name
                - email: Email address
                - status: Account status
                - profile: Mapped profile name
            title: Table title

        Returns:
            Rich Table object with CloudOps theme
        """
        table = create_table(
            title=title,
            columns=[
                {"name": "Account ID", "style": "cyan", "justify": "left"},
                {"name": "Account Name", "style": "white", "justify": "left"},
                {"name": "Email", "style": "dim", "justify": "left"},
                {"name": "Status", "style": "green", "justify": "center"},
                {"name": "Profile", "style": "yellow", "justify": "left"},
            ],
        )

        for account in accounts:
            # Color status based on value
            status = account.get("status", "UNKNOWN")
            status_style = "green" if status == "ACTIVE" else "red"
            status_display = f"[{status_style}]{status}[/{status_style}]"

            table.add_row(
                account.get("id", ""),
                account.get("name", ""),
                account.get("email", ""),
                status_display,
                account.get("profile", ""),
            )

        return table

    @staticmethod
    def export_json(accounts: List[Dict], output_file: str, metadata: Optional[Dict] = None) -> None:
        """
        Export accounts to JSON format with config-aware 14+ columns.

        Args:
            accounts: List of account dictionaries
            output_file: Output file path
            metadata: Optional metadata to include in export

        Raises:
            IOError: If file write fails
        """
        try:
            # Load tag mappings for field names (optional metadata)
            config_loader = get_config_loader()
            tag_mappings = config_loader.load_tag_mappings()

            # Enhanced accounts with all tiers
            enhanced_accounts = []
            for account in accounts:
                enhanced_account = {
                    # Baseline fields (9 columns - unchanged for backward compatibility)
                    "id": account.get("id"),
                    "name": account.get("name"),
                    "email": account.get("email"),
                    "status": account.get("status"),
                    "joined_method": account.get("joined_method"),
                    "joined_timestamp": account.get("joined_timestamp"),
                    "organizational_unit": account.get("organizational_unit"),
                    "organizational_unit_id": account.get("organizational_unit_id"),
                    "parent_id": account.get("parent_id"),
                    # TIER 1: Business Metadata (config-aware)
                    "wbs_code": account.get("wbs_code", "N/A"),
                    "cost_group": account.get("cost_group", "N/A"),
                    "technical_lead": account.get("technical_lead", "N/A"),
                    "account_owner": account.get("account_owner", "N/A"),
                    # TIER 2: Governance Metadata (config-aware)
                    "business_unit": account.get("business_unit", "N/A"),
                    "functional_area": account.get("functional_area", "N/A"),
                    "managed_by": account.get("managed_by", "N/A"),
                    "product_owner": account.get("product_owner", "N/A"),
                    # TIER 3: Operational Metadata (config-aware)
                    "purpose": account.get("purpose", "N/A"),
                    "environment": account.get("environment", "N/A"),
                    "compliance_scope": account.get("compliance_scope", "N/A"),
                    "data_classification": account.get("data_classification", "N/A"),
                    # TIER 4: Extended Metadata (optional, config-aware)
                    "project_name": account.get("project_name", "N/A"),
                    "budget_code": account.get("budget_code", "N/A"),
                    "support_tier": account.get("support_tier", "N/A"),
                    "created_date": account.get("created_date", "N/A"),
                    "expiry_date": account.get("expiry_date", "N/A"),
                    # Computed fields (if present)
                    "all_tags": account.get("all_tags", {}),
                    "wbs_comparison": account.get("wbs_comparison", {}),
                }

                # Preserve any additional fields from source (forward compatibility)
                for key in account:
                    if key not in enhanced_account:
                        enhanced_account[key] = account[key]

                enhanced_accounts.append(enhanced_account)

            output_data = {"accounts": enhanced_accounts}

            if metadata:
                output_data["metadata"] = metadata

            # Add tag mapping metadata for reference
            output_data["tag_mappings_used"] = tag_mappings
            output_data["config_sources"] = config_loader.get_config_sources()

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print_success(
                f"Exported {len(accounts)} accounts to {output_file} (JSON, {len(enhanced_accounts[0])} fields)"
            )

        except Exception as e:
            error_msg = f"Failed to export JSON: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def export_csv(accounts: List[Dict], output_file: str, include_header: bool = True) -> None:
        """
        Export accounts to CSV format with config-aware 14+ columns.

        Args:
            accounts: List of account dictionaries
            output_file: Output file path
            include_header: Include CSV header row

        Raises:
            IOError: If file write fails
        """
        if not accounts:
            logger.warning("No accounts to export to CSV")
            return

        try:
            # Define CSV headers (all tiers in priority order)
            headers = [
                # Baseline fields (9 columns)
                "id",
                "name",
                "email",
                "status",
                "joined_method",
                "joined_timestamp",
                "organizational_unit",
                "organizational_unit_id",
                "parent_id",
                # TIER 1: Business Metadata
                "wbs_code",
                "cost_group",
                "technical_lead",
                "account_owner",
                # TIER 2: Governance Metadata
                "business_unit",
                "functional_area",
                "managed_by",
                "product_owner",
                # TIER 3: Operational Metadata
                "purpose",
                "environment",
                "compliance_scope",
                "data_classification",
                # TIER 4: Extended Metadata (optional)
                "project_name",
                "budget_code",
                "support_tier",
                "created_date",
                "expiry_date",
            ]

            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")

                if include_header:
                    writer.writeheader()

                # Write rows with N/A for missing fields
                for account in accounts:
                    row_data = {header: account.get(header, "N/A") for header in headers}
                    writer.writerow(row_data)

            print_success(f"Exported {len(accounts)} accounts to {output_file} (CSV, {len(headers)} columns)")

        except Exception as e:
            error_msg = f"Failed to export CSV: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def export_markdown(accounts: List[Dict], output_file: str, title: str = "AWS Organization Accounts") -> None:
        """
        Export accounts to Markdown table format with config-aware 14+ columns.

        Args:
            accounts: List of account dictionaries
            output_file: Output file path
            title: Markdown document title

        Raises:
            IOError: If file write fails
        """
        if not accounts:
            logger.warning("No accounts to export to Markdown")
            return

        try:
            # Load config for metadata
            config_loader = get_config_loader()
            tag_mappings = config_loader.load_tag_mappings()

            # Priority columns for markdown display (top 12 most important)
            display_columns = [
                "id",
                "name",
                "status",
                "email",
                "wbs_code",
                "cost_group",
                "technical_lead",
                "business_unit",
                "environment",
                "organizational_unit",
                "managed_by",
                "purpose",
            ]

            with open(output_file, "w", encoding="utf-8") as f:
                # Write title
                f.write(f"# {title}\n\n")

                # Write metadata
                f.write("## Configuration Details\n\n")
                f.write(f"**Config Sources**: {' → '.join(config_loader.get_config_sources())}\n\n")
                f.write(f"**Tag Mappings**: {len(tag_mappings)} fields configured\n\n")

                # Write table header (display columns only)
                header_names = [col.replace("_", " ").title() for col in display_columns]
                f.write("| " + " | ".join(header_names) + " |\n")
                f.write("| " + " | ".join(["---"] * len(display_columns)) + " |\n")

                # Write table rows
                for account in accounts:
                    values = [str(account.get(col, "N/A")) for col in display_columns]
                    # Truncate long values for readability
                    values = [v[:50] + "..." if len(v) > 50 else v for v in values]
                    f.write("| " + " | ".join(values) + " |\n")

                # Write summary
                f.write(f"\n**Total Accounts:** {len(accounts)}\n")
                f.write(f"\n**Display Columns:** {len(display_columns)} (showing most important fields)\n")
                f.write(f"\n**Full Export:** Use JSON/CSV format for complete {len(accounts[0])} field export\n")

            print_success(
                f"Exported {len(accounts)} accounts to {output_file} (Markdown, {len(display_columns)} display columns)"
            )

        except Exception as e:
            error_msg = f"Failed to export Markdown: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def to_csv_string(accounts: List[Dict]) -> str:
        """
        Convert accounts to CSV string format (in-memory).

        Args:
            accounts: List of account dictionaries

        Returns:
            CSV formatted string
        """
        if not accounts:
            return ""

        output = StringIO()
        fieldnames = list(accounts[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(accounts)

        return output.getvalue()

    @staticmethod
    def to_json_string(accounts: List[Dict], indent: int = 2) -> str:
        """
        Convert accounts to JSON string format (in-memory).

        Args:
            accounts: List of account dictionaries
            indent: JSON indentation level

        Returns:
            JSON formatted string
        """
        return json.dumps({"accounts": accounts}, indent=indent, ensure_ascii=False)


class ResourceExplorerFormatter:
    """
    Format Resource Explorer discovery data for various output types.

    Supports 4 enterprise output formats:
    - CSV (default): Human+agent readable, Excel-compatible
    - Markdown: Documentation-ready with resource summaries
    - JSON: Machine-parseable with full metadata
    - Excel: 4-sheet executive reporting (Summary, Resources, Costs, Metadata)
    """

    @staticmethod
    def format_resources_table(resources: List[Dict], title: str = "Resource Explorer Discovery") -> Table:
        """
        Create Rich table for Resource Explorer results.

        Args:
            resources: List of resource dictionaries with keys:
                - resource_arn: Full ARN of the resource
                - account_id: AWS account ID
                - region: AWS region
                - resource_type: Resource type string
                - resource_id: Extracted resource ID
                - tags: Dictionary of resource tags
            title: Table title

        Returns:
            Rich Table object with CloudOps theme
        """
        table = create_table(
            title=title,
            columns=[
                {"name": "Resource ARN", "style": "cyan", "justify": "left"},
                {"name": "Account ID", "style": "yellow", "justify": "left"},
                {"name": "Region", "style": "blue", "justify": "center"},
                {"name": "Resource Type", "style": "green", "justify": "left"},
                {"name": "Tags", "style": "dim", "justify": "left"},
            ],
        )

        for resource in resources:
            # Format tags for display (show first 2 tags)
            tags = resource.get("tags", {})
            if tags:
                tag_items = list(tags.items())[:2]
                tags_display = ", ".join([f"{k}={v}" for k, v in tag_items])
                if len(tags) > 2:
                    tags_display += f" (+{len(tags) - 2} more)"
            else:
                tags_display = "No tags"

            table.add_row(
                resource.get("resource_arn", "")[:80] + "...",  # Truncate long ARNs
                resource.get("account_id", ""),
                resource.get("region", ""),
                resource.get("resource_type", ""),
                tags_display,
            )

        return table

    @staticmethod
    def export_json(resources: List[Dict], output_file: str, metadata: Optional[Dict] = None) -> None:
        """
        Export resources to JSON format with complete metadata.

        Args:
            resources: List of resource dictionaries
            output_file: Output file path
            metadata: Optional metadata to include in export

        Raises:
            IOError: If file write fails
        """
        try:
            output_data = {"resources": resources}

            if metadata:
                output_data["metadata"] = metadata

            # Add discovery statistics
            output_data["statistics"] = {
                "total_resources": len(resources),
                "resources_by_type": {},
                "resources_by_account": {},
                "resources_by_region": {},
            }

            # Calculate statistics
            for resource in resources:
                resource_type = resource.get("resource_type", "unknown")
                account_id = resource.get("account_id", "unknown")
                region = resource.get("region", "unknown")

                # Count by type
                output_data["statistics"]["resources_by_type"][resource_type] = (
                    output_data["statistics"]["resources_by_type"].get(resource_type, 0) + 1
                )

                # Count by account
                output_data["statistics"]["resources_by_account"][account_id] = (
                    output_data["statistics"]["resources_by_account"].get(account_id, 0) + 1
                )

                # Count by region
                output_data["statistics"]["resources_by_region"][region] = (
                    output_data["statistics"]["resources_by_region"].get(region, 0) + 1
                )

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

            print_success(f"Exported {len(resources)} resources to {output_file} (JSON)")

        except Exception as e:
            error_msg = f"Failed to export JSON: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def export_csv(resources: List[Dict], output_file: str, include_header: bool = True) -> None:
        """
        Export resources to CSV format (default format for human+agent).

        Args:
            resources: List of resource dictionaries
            output_file: Output file path
            include_header: Include CSV header row

        Raises:
            IOError: If file write fails
        """
        if not resources:
            logger.warning("No resources to export to CSV")
            return

        try:
            # Define CSV headers
            headers = [
                "resource_arn",
                "account_id",
                "region",
                "resource_type",
                "resource_id",
                "tags",
                "monthly_cost",
                "annual_cost",
            ]

            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")

                if include_header:
                    writer.writeheader()

                # Write rows with N/A for missing fields
                for resource in resources:
                    row_data = {
                        "resource_arn": resource.get("resource_arn", "N/A"),
                        "account_id": resource.get("account_id", "N/A"),
                        "region": resource.get("region", "N/A"),
                        "resource_type": resource.get("resource_type", "N/A"),
                        "resource_id": resource.get("resource_id", "N/A"),
                        "tags": json.dumps(resource.get("tags", {})),
                        "monthly_cost": resource.get("monthly_cost", "N/A"),
                        "annual_cost": resource.get("annual_cost", "N/A"),
                    }
                    writer.writerow(row_data)

            print_success(f"Exported {len(resources)} resources to {output_file} (CSV, {len(headers)} columns)")

        except Exception as e:
            error_msg = f"Failed to export CSV: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def export_markdown(resources: List[Dict], output_file: str, title: str = "Resource Explorer Discovery") -> None:
        """
        Export resources to Markdown documentation format.

        Args:
            resources: List of resource dictionaries
            output_file: Output file path
            title: Markdown document title

        Raises:
            IOError: If file write fails
        """
        if not resources:
            logger.warning("No resources to export to Markdown")
            return

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                # Write title and metadata
                f.write(f"# {title}\n\n")

                # Discovery metadata
                f.write("## Discovery Metadata\n\n")
                if resources:
                    first_resource = resources[0]
                    f.write(f"**Total Resources**: {len(resources)}\n\n")
                    f.write(f"**Discovery Time**: {first_resource.get('last_reported_at', 'N/A')}\n\n")

                # Summary statistics
                f.write("## Summary Statistics\n\n")

                # Calculate statistics
                resources_by_type = {}
                resources_by_account = {}
                resources_by_region = {}

                for resource in resources:
                    resource_type = resource.get("resource_type", "unknown")
                    account_id = resource.get("account_id", "unknown")
                    region = resource.get("region", "unknown")

                    resources_by_type[resource_type] = resources_by_type.get(resource_type, 0) + 1
                    resources_by_account[account_id] = resources_by_account.get(account_id, 0) + 1
                    resources_by_region[region] = resources_by_region.get(region, 0) + 1

                # Write summary tables
                f.write("### Resources by Type\n\n")
                f.write("| Resource Type | Count |\n")
                f.write("| --- | --- |\n")
                for resource_type, count in sorted(resources_by_type.items()):
                    f.write(f"| {resource_type} | {count} |\n")
                f.write("\n")

                f.write("### Resources by Account\n\n")
                f.write("| Account ID | Count |\n")
                f.write("| --- | --- |\n")
                for account_id, count in sorted(resources_by_account.items()):
                    f.write(f"| {account_id} | {count} |\n")
                f.write("\n")

                f.write("### Resources by Region\n\n")
                f.write("| Region | Count |\n")
                f.write("| --- | --- |\n")
                for region, count in sorted(resources_by_region.items()):
                    f.write(f"| {region} | {count} |\n")
                f.write("\n")

                # Resources table (top 100)
                f.write("## Resource Details (Top 100)\n\n")
                f.write("| Resource ARN | Account ID | Region | Resource Type | Tags |\n")
                f.write("| --- | --- | --- | --- | --- |\n")

                for resource in resources[:100]:
                    arn = resource.get("resource_arn", "N/A")
                    if len(arn) > 80:
                        arn = arn[:77] + "..."

                    tags = resource.get("tags", {})
                    tags_str = ", ".join([f"{k}={v}" for k, v in list(tags.items())[:2]])
                    if len(tags) > 2:
                        tags_str += f" (+{len(tags) - 2} more)"

                    f.write(
                        f"| {arn} | {resource.get('account_id', 'N/A')} | "
                        f"{resource.get('region', 'N/A')} | {resource.get('resource_type', 'N/A')} | "
                        f"{tags_str or 'No tags'} |\n"
                    )

                # Cost analysis (if enriched)
                if resources and "monthly_cost" in resources[0]:
                    f.write("\n## Cost Analysis\n\n")
                    total_monthly_cost = sum(r.get("monthly_cost", 0) for r in resources)
                    total_annual_cost = total_monthly_cost * 12

                    f.write(f"**Total Monthly Cost**: ${total_monthly_cost:,.2f}\n\n")
                    f.write(f"**Projected Annual Cost**: ${total_annual_cost:,.2f}\n\n")

            print_success(f"Exported {len(resources)} resources to {output_file} (Markdown)")

        except Exception as e:
            error_msg = f"Failed to export Markdown: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def export_excel(resources: List[Dict], output_file: str, metadata: Optional[Dict] = None) -> None:
        """
        Export resources to Excel with 4-sheet executive reporting.

        Sheets:
        - Summary: Resource counts, cost totals, discovery stats
        - Resources: Full resource details
        - Cost Analysis: Monthly/annual costs if enriched
        - Metadata: Filters applied, execution time, profiles used

        Args:
            resources: List of resource dictionaries
            output_file: Output file path
            metadata: Optional metadata to include

        Raises:
            IOError: If file write fails
            ImportError: If pandas is not available
        """
        try:
            import pandas as pd
        except ImportError:
            error_msg = "pandas is required for Excel export. Install with: uv pip install pandas openpyxl"
            logger.error(error_msg)
            print_error(error_msg)
            raise ImportError(error_msg)

        if not resources:
            logger.warning("No resources to export to Excel")
            return

        try:
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                # Sheet 1: Summary
                summary_data = []

                # Calculate statistics
                resources_by_type = {}
                resources_by_account = {}
                resources_by_region = {}

                for resource in resources:
                    resource_type = resource.get("resource_type", "unknown")
                    account_id = resource.get("account_id", "unknown")
                    region = resource.get("region", "unknown")

                    resources_by_type[resource_type] = resources_by_type.get(resource_type, 0) + 1
                    resources_by_account[account_id] = resources_by_account.get(account_id, 0) + 1
                    resources_by_region[region] = resources_by_region.get(region, 0) + 1

                # Summary statistics
                summary_data.append({"Metric": "Total Resources", "Value": len(resources)})
                summary_data.append({"Metric": "Resource Types", "Value": len(resources_by_type)})
                summary_data.append({"Metric": "Accounts", "Value": len(resources_by_account)})
                summary_data.append({"Metric": "Regions", "Value": len(resources_by_region)})

                # Cost totals (if enriched)
                if resources and "monthly_cost" in resources[0]:
                    total_monthly_cost = sum(r.get("monthly_cost", 0) for r in resources)
                    total_annual_cost = total_monthly_cost * 12
                    summary_data.append({"Metric": "Total Monthly Cost", "Value": f"${total_monthly_cost:,.2f}"})
                    summary_data.append({"Metric": "Projected Annual Cost", "Value": f"${total_annual_cost:,.2f}"})

                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name="Summary", index=False)

                # Sheet 2: Resources
                resources_data = []
                for resource in resources:
                    resources_data.append(
                        {
                            "Resource ARN": resource.get("resource_arn", "N/A"),
                            "Account ID": resource.get("account_id", "N/A"),
                            "Region": resource.get("region", "N/A"),
                            "Resource Type": resource.get("resource_type", "N/A"),
                            "Resource ID": resource.get("resource_id", "N/A"),
                            "Tags": json.dumps(resource.get("tags", {})),
                            "Monthly Cost": resource.get("monthly_cost", "N/A"),
                            "Annual Cost": resource.get("annual_cost", "N/A"),
                        }
                    )

                df_resources = pd.DataFrame(resources_data)
                df_resources.to_excel(writer, sheet_name="Resources", index=False)

                # Sheet 3: Cost Analysis (if enriched)
                if resources and "monthly_cost" in resources[0]:
                    cost_data = []

                    # Cost by account
                    cost_by_account = {}
                    for resource in resources:
                        account_id = resource.get("account_id", "unknown")
                        monthly_cost = resource.get("monthly_cost", 0)
                        cost_by_account[account_id] = cost_by_account.get(account_id, 0) + monthly_cost

                    for account_id, monthly_cost in cost_by_account.items():
                        cost_data.append(
                            {
                                "Account ID": account_id,
                                "Monthly Cost": monthly_cost,
                                "Annual Cost": monthly_cost * 12,
                            }
                        )

                    df_cost = pd.DataFrame(cost_data)
                    df_cost.to_excel(writer, sheet_name="Cost Analysis", index=False)

                # Sheet 4: Metadata
                metadata_data = []

                if metadata:
                    for key, value in metadata.items():
                        metadata_data.append({"Key": key, "Value": str(value)})

                # Add discovery statistics
                metadata_data.append({"Key": "Total Resources", "Value": len(resources)})
                metadata_data.append({"Key": "Resource Types", "Value": ", ".join(resources_by_type.keys())})
                metadata_data.append({"Key": "Accounts", "Value": ", ".join(resources_by_account.keys())})
                metadata_data.append({"Key": "Regions", "Value": ", ".join(resources_by_region.keys())})

                df_metadata = pd.DataFrame(metadata_data)
                df_metadata.to_excel(writer, sheet_name="Metadata", index=False)

            print_success(f"Exported {len(resources)} resources to {output_file} (Excel, 4 sheets)")

        except Exception as e:
            error_msg = f"Failed to export Excel: {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def format_console_export(resources: List[Dict]) -> List[Dict]:
        """
        Format resources to match AWS Console export format (7 columns).

        Converts CLI format (12 columns) to AWS Console format matching
        data/test/resources-ec2.csv structure for direct comparison with
        AWS Console Excel exports.

        Args:
            resources: List of resource dictionaries in CLI format

        Returns:
            List of resource dictionaries in AWS Console format with columns:
            - Identifier: Resource identifier
            - Service: AWS service name (lowercase)
            - Resource type: Resource type string
            - Region: AWS region
            - AWS Account: Account ID
            - Application: Application name ("-" if empty)
            - Tags: Tag count (integer)
        """
        console_resources = []

        for resource in resources:
            # Extract tags count from JSON dict
            tags = resource.get("tags", {})
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except (json.JSONDecodeError, TypeError):
                    tags = {}
            tag_count = len(tags) if isinstance(tags, dict) else 0

            # Format to AWS Console structure (Title Case headers)
            console_resource = {
                "Identifier": resource.get("identifier", resource.get("resource_id", "N/A")),
                "Service": resource.get("service", "N/A").lower(),
                "Resource type": resource.get("resource_type", "N/A"),
                "Region": resource.get("region", "N/A"),
                "AWS Account": resource.get("owner_account_id", resource.get("account_id", "N/A")),
                "Application": resource.get("application", "-") or "-",
                "Tags": tag_count,
            }

            console_resources.append(console_resource)

        return console_resources

    @staticmethod
    def export_csv_console(resources: List[Dict], output_file: str, include_header: bool = True) -> None:
        """
        Export resources to CSV in AWS Console format (7 columns).

        Matches AWS Console Excel export structure for direct comparison.
        Use this when you need output compatible with AWS Console exports
        from Resource Explorer.

        Args:
            resources: List of resource dictionaries
            output_file: Output file path
            include_header: Include CSV header row

        Raises:
            IOError: If file write fails
        """
        if not resources:
            logger.warning("No resources to export to CSV (console format)")
            return

        try:
            # Convert to console format
            console_resources = ResourceExplorerFormatter.format_console_export(resources)

            # Define CSV headers (AWS Console format with Title Case)
            headers = ["Identifier", "Service", "Resource type", "Region", "AWS Account", "Application", "Tags"]

            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)

                if include_header:
                    writer.writeheader()

                writer.writerows(console_resources)

            print_success(
                f"Exported {len(resources)} resources to {output_file} (CSV Console format, {len(headers)} columns)"
            )

        except Exception as e:
            error_msg = f"Failed to export CSV (console format): {str(e)}"
            logger.error(error_msg)
            print_error(error_msg)
            raise IOError(error_msg) from e

    @staticmethod
    def to_csv_string(resources: List[Dict]) -> str:
        """
        Convert resources to CSV string format (in-memory).

        Args:
            resources: List of resource dictionaries

        Returns:
            CSV formatted string
        """
        if not resources:
            return ""

        output = StringIO()

        # Use all available keys from first resource
        fieldnames = [
            "resource_arn",
            "account_id",
            "region",
            "resource_type",
            "resource_id",
            "tags",
            "monthly_cost",
            "annual_cost",
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        # Write rows with tags as JSON string
        for resource in resources:
            row_data = {**resource}
            if "tags" in row_data:
                row_data["tags"] = json.dumps(row_data["tags"])
            writer.writerow(row_data)

        return output.getvalue()

    @staticmethod
    def to_json_string(resources: List[Dict], indent: int = 2) -> str:
        """
        Convert resources to JSON string format (in-memory).

        Args:
            resources: List of resource dictionaries
            indent: JSON indentation level

        Returns:
            JSON formatted string
        """
        return json.dumps({"resources": resources}, indent=indent, ensure_ascii=False, default=str)


class HierarchyFormatter:
    """Format Organizations hierarchy visualization data."""

    @staticmethod
    def format_hierarchy_tree(accounts: List[Dict], show_profiles: bool = True) -> str:
        """
        Format accounts as hierarchical tree structure.

        Args:
            accounts: List of account dictionaries
            show_profiles: Include profile mappings in output

        Returns:
            Formatted tree string
        """
        tree_lines = []
        tree_lines.append("AWS Organization Hierarchy")
        tree_lines.append("=" * 50)
        tree_lines.append("")

        for idx, account in enumerate(accounts):
            is_last = idx == len(accounts) - 1
            prefix = "└── " if is_last else "├── "

            account_line = f"{prefix}{account.get('name', 'N/A')} ({account.get('id', 'N/A')})"

            if show_profiles:
                account_line += f" → {account.get('profile', 'N/A')}"

            tree_lines.append(account_line)

            # Add status as sub-item
            status_prefix = "    " if is_last else "│   "
            tree_lines.append(f"{status_prefix}Status: {account.get('status', 'UNKNOWN')}")

            if not is_last:
                tree_lines.append("│")

        return "\n".join(tree_lines)

    @staticmethod
    def format_summary(accounts: List[Dict]) -> str:
        """
        Format summary statistics for accounts.

        Args:
            accounts: List of account dictionaries

        Returns:
            Formatted summary string
        """
        total = len(accounts)
        active = sum(1 for a in accounts if a.get("status") == "ACTIVE")
        suspended = sum(1 for a in accounts if a.get("status") == "SUSPENDED")
        closed = sum(1 for a in accounts if a.get("status") == "CLOSED")

        summary_lines = []
        summary_lines.append("Account Summary")
        summary_lines.append("=" * 40)
        summary_lines.append(f"Total Accounts:     {total}")
        summary_lines.append(f"Active Accounts:    {active}")
        summary_lines.append(f"Suspended Accounts: {suspended}")
        summary_lines.append(f"Closed Accounts:    {closed}")

        return "\n".join(summary_lines)


def export_to_file(
    data: Any, output_path: str, format_type: str = "json", data_type: str = "organizations", **kwargs
) -> None:
    """
    Universal export function supporting multiple data types and formats.

    Args:
        data: List of dictionaries or pandas DataFrame
        output_path: Output file path
        format_type: Export format ('json', 'csv', 'markdown', 'excel')
        data_type: Data type ('organizations' or 'resource_explorer')
        **kwargs: Additional format-specific arguments

    Raises:
        ValueError: If format_type or data_type is unsupported
        IOError: If file write fails
    """
    # Convert DataFrame to list of dicts if needed
    if hasattr(data, "to_dict"):  # pandas DataFrame
        data = data.to_dict("records")

    format_type = format_type.lower()
    data_type = data_type.lower()

    # Route to appropriate formatter based on data_type
    if data_type == "organizations":
        if format_type == "json":
            metadata = kwargs.get("metadata")
            OrganizationsFormatter.export_json(data, output_path, metadata=metadata)

        elif format_type == "csv":
            include_header = kwargs.get("include_header", True)
            OrganizationsFormatter.export_csv(data, output_path, include_header=include_header)

        elif format_type == "markdown":
            title = kwargs.get("title", "AWS Organization Accounts")
            OrganizationsFormatter.export_markdown(data, output_path, title=title)

        else:
            supported_formats = ["json", "csv", "markdown"]
            raise ValueError(
                f"Unsupported format for organizations: {format_type}. Supported formats: {supported_formats}"
            )

    elif data_type == "resource_explorer":
        if format_type == "json":
            metadata = kwargs.get("metadata")
            ResourceExplorerFormatter.export_json(data, output_path, metadata=metadata)

        elif format_type == "csv":
            include_header = kwargs.get("include_header", True)
            ResourceExplorerFormatter.export_csv(data, output_path, include_header=include_header)

        elif format_type == "markdown":
            title = kwargs.get("title", "Resource Explorer Discovery")
            ResourceExplorerFormatter.export_markdown(data, output_path, title=title)

        elif format_type == "excel":
            metadata = kwargs.get("metadata")
            ResourceExplorerFormatter.export_excel(data, output_path, metadata=metadata)

        else:
            supported_formats = ["json", "csv", "markdown", "excel"]
            raise ValueError(
                f"Unsupported format for resource_explorer: {format_type}. Supported formats: {supported_formats}"
            )

    else:
        supported_types = ["organizations", "resource_explorer"]
        raise ValueError(f"Unsupported data type: {data_type}. Supported types: {supported_types}")
