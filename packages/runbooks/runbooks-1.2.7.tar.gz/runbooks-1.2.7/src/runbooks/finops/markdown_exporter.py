#!/usr/bin/env python3
"""
Rich-styled Markdown Export Module for CloudOps & FinOps Runbooks

This module provides Rich table to markdown conversion functionality with
MkDocs compatibility for copy-pasteable documentation tables.

Features:
- Rich table to markdown conversion with styled borders
- 10-column format for multi-account analysis
- MkDocs compatible table syntax
- Intelligent file management and organization
- Preserves color coding through markdown syntax
- Automated timestamping and metadata

Author: Runbooks Team
Version: 0.7.8
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich import box
from rich.table import Table
from rich.text import Text

from runbooks import __version__
from runbooks.common.rich_utils import (
    STATUS_INDICATORS,
    console,
    create_table,
    format_cost,
    print_info,
    print_success,
    print_warning,
)


class MarkdownExporter:
    """Rich-styled markdown export functionality for FinOps analysis."""

    def __init__(self, output_dir: str = "./exports"):
        """
        Initialize the markdown exporter.

        Args:
            output_dir: Directory to save markdown exports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def rich_table_to_markdown(self, table: Table, preserve_styling: bool = True) -> str:
        """
        Convert Rich table to markdown format with optional styling preservation.

        Args:
            table: Rich Table object to convert
            preserve_styling: Whether to preserve Rich styling through markdown syntax

        Returns:
            Markdown formatted table string
        """
        if not table.columns:
            return ""

        # Extract column headers
        headers = []
        for column in table.columns:
            header_text = column.header or ""
            if hasattr(header_text, "plain"):
                headers.append(header_text.plain)
            else:
                headers.append(str(header_text))

        # Create markdown table header
        markdown_lines = []
        markdown_lines.append("| " + " | ".join(headers) + " |")

        # Create GitHub-compliant separator line with proper alignment syntax
        separators = []
        for column in table.columns:
            if column.justify == "right":
                separators.append("---:")  # GitHub right alignment (minimum 3 hyphens)
            elif column.justify == "center":
                separators.append(":---:")  # GitHub center alignment
            else:
                separators.append("---")  # GitHub left alignment (default, minimum 3 hyphens)
        markdown_lines.append("| " + " | ".join(separators) + " |")

        # Extract and format data rows
        for row in table.rows:
            row_cells = []
            for cell in row:
                if isinstance(cell, Text):
                    if preserve_styling:
                        # Convert Rich Text to markdown with styling
                        cell_text = self._rich_text_to_markdown(cell)
                    else:
                        cell_text = cell.plain
                else:
                    cell_text = str(cell)

                # GitHub tables don't support multi-line content - convert to single line
                cell_text = cell_text.replace("\n", " • ").strip()

                # Escape pipes in cell content for GitHub compatibility
                cell_text = cell_text.replace("|", "\\|")

                # Remove excessive Rich formatting that doesn't render well in GitHub
                cell_text = self._clean_rich_formatting_for_github(cell_text)

                row_cells.append(cell_text)

            markdown_lines.append("| " + " | ".join(row_cells) + " |")

        return "\n".join(markdown_lines)

    def _rich_text_to_markdown(self, rich_text: Text) -> str:
        """
        Convert Rich Text object to markdown with style preservation.

        Args:
            rich_text: Rich Text object with styling

        Returns:
            Markdown formatted string with preserved styling
        """
        # Start with plain text
        text = rich_text.plain

        # Extract style information and apply markdown equivalents
        if hasattr(rich_text, "_spans") and rich_text._spans:
            for span in reversed(rich_text._spans):  # Reverse to handle overlapping spans
                style = span.style
                start, end = span.start, span.end

                # Apply markdown formatting based on Rich styles
                if style and hasattr(style, "color"):
                    if "green" in str(style.color):
                        # Green text (success/positive) - use ✅ emoji
                        text = text[:start] + "✅ " + text[start:end] + text[end:]
                    elif "red" in str(style.color):
                        # Red text (error/negative) - use ❌ emoji
                        text = text[:start] + "❌ " + text[start:end] + text[end:]
                    elif "yellow" in str(style.color):
                        # Yellow text (warning) - use ⚠️ emoji
                        text = text[:start] + "⚠️ " + text[start:end] + text[end:]
                    elif "cyan" in str(style.color):
                        # Cyan text (info) - use **bold** markdown
                        text = text[:start] + "**" + text[start:end] + "**" + text[end:]

                if style and hasattr(style, "bold") and style.bold:
                    text = text[:start] + "**" + text[start:end] + "**" + text[end:]

                if style and hasattr(style, "italic") and style.italic:
                    text = text[:start] + "*" + text[start:end] + "*" + text[end:]

        return text

    def _clean_rich_formatting_for_github(self, text: str) -> str:
        """
        Clean Rich formatting for better GitHub markdown compatibility.

        Args:
            text: Text with Rich formatting tags

        Returns:
            Cleaned text suitable for GitHub markdown tables
        """
        # Remove Rich color/style tags that don't render well in GitHub
        import re

        # Remove Rich markup tags but preserve content
        text = re.sub(r"\[/?(?:red|green|yellow|cyan|blue|magenta|white|black|bright_\w+|dim|bold|italic)\]", "", text)
        text = re.sub(r"\[/?[^\]]*\]", "", text)  # Remove any remaining Rich tags

        # Clean up multiple spaces and trim
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def create_single_account_export(self, profile_data: Dict[str, Any], account_id: str, profile_name: str) -> str:
        """
        Create markdown export for single account analysis.

        Args:
            profile_data: Single profile cost data
            account_id: AWS account ID
            profile_name: AWS profile name

        Returns:
            Markdown formatted single account analysis
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Create markdown content
        markdown_content = f"""# AWS Cost Analysis - Account {account_id}

**Generated**: {timestamp}  
**Profile**: {profile_name}  
**Organization**: Single Account Analysis

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total Cost | ${profile_data.get("total_cost", 0):,.2f} | {self._get_cost_status_emoji(profile_data.get("total_cost", 0))} |
| Service Count | {len(profile_data.get("service_breakdown", []))} services | 📊 |
| Cost Trend | {profile_data.get("cost_trend", "Stable")} | {self._get_trend_emoji(profile_data.get("cost_trend", ""))} |

## Service Breakdown

| Service | Current Cost | Percentage | Trend | Optimization |
|---------|--------------|------------|-------|--------------|
"""

        # Add service breakdown rows
        services = profile_data.get("service_breakdown", [])
        for service in services[:10]:  # Top 10 services
            service_name = service.get("service", "Unknown")
            cost = service.get("cost", 0)
            percentage = service.get("percentage", 0)
            trend = service.get("trend", "Stable")
            optimization = service.get("optimization_opportunity", "Monitor")

            markdown_content += f"| {service_name} | ${cost:,.2f} | {percentage:.1f}% | {self._get_trend_emoji(trend)} {trend} | {optimization} |\n"

        # Add resource optimization section
        markdown_content += f"""

## Resource Optimization Opportunities

| Resource Type | Count | Potential Savings | Action Required |
|---------------|-------|------------------|-----------------|
| Stopped EC2 Instances | {profile_data.get("stopped_ec2", 0)} | ${profile_data.get("stopped_ec2_savings", 0):,.2f} | Review and terminate |
| Unused EBS Volumes | {profile_data.get("unused_volumes", 0)} | ${profile_data.get("unused_volume_savings", 0):,.2f} | Clean up unused storage |
| Unused Elastic IPs | {profile_data.get("unused_eips", 0)} | ${profile_data.get("unused_eip_savings", 0):,.2f} | Release unused IPs |
| Untagged Resources | {profile_data.get("untagged_resources", 0)} | N/A | Implement tagging strategy |

---
*Generated by CloudOps & FinOps Runbooks Module v{__version__}*
"""

        return markdown_content

    def create_multi_account_export(
        self, multi_profile_data: List[Dict[str, Any]], organization_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create 10-column markdown export for multi-account analysis.

        Args:
            multi_profile_data: List of profile data dictionaries
            organization_info: Optional organization metadata

        Returns:
            Markdown formatted multi-account analysis with 10 columns
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        account_count = len(multi_profile_data)

        # Calculate organization totals
        total_cost = sum(profile.get("total_cost", 0) for profile in multi_profile_data)
        total_savings = sum(profile.get("potential_savings", 0) for profile in multi_profile_data)

        # Create markdown content with 10-column format
        markdown_content = f"""# AWS Multi-Account Cost Analysis

**Generated**: {timestamp}  
**Organization**: {account_count} accounts  
**Total Cost**: ${total_cost:,.2f}  
**Potential Savings**: ${total_savings:,.2f}

## Executive Dashboard

| Metric | Value | Status |
|--------|-------|--------|
| Total Monthly Cost | ${total_cost:,.2f} | 💰 |
| Average per Account | ${total_cost / account_count:,.2f} | 📊 |
| Optimization Opportunity | ${total_savings:,.2f} ({total_savings / total_cost * 100:.1f}%) | 🎯 |

## Multi-Account Analysis (10-Column Format)

| Profile | Last Month | Current Month | Top 3 Services | Budget | Stopped EC2 | Unused Vol | Unused EIP | Savings | Untagged |
|---------|------------|---------------|-----------------|---------|-------------|------------|------------|---------|----------|
"""

        # Add data rows for each profile
        for profile_data in multi_profile_data:
            profile_name = profile_data.get("profile_name", "Unknown")[:15]  # Truncate for table width
            last_month = profile_data.get("last_month_cost", 0)
            current_month = profile_data.get("total_cost", 0)

            # Get top 3 services
            services = profile_data.get("service_breakdown", [])
            top_services = [s.get("service", "")[:6] for s in services[:3]]  # Truncate service names
            top_services_str = ",".join(top_services) if top_services else "N/A"

            # Budget status
            budget_status = self._get_budget_status_emoji(profile_data.get("budget_status", "unknown"))

            # Resource optimization data
            stopped_ec2 = profile_data.get("stopped_ec2", 0)
            unused_volumes = profile_data.get("unused_volumes", 0)
            unused_eips = profile_data.get("unused_eips", 0)
            potential_savings = profile_data.get("potential_savings", 0)
            untagged_resources = profile_data.get("untagged_resources", 0)

            # Add row to table
            markdown_content += f"| {profile_name} | ${last_month:,.0f} | ${current_month:,.0f} | {top_services_str} | {budget_status} | {stopped_ec2} | {unused_volumes} | {unused_eips} | ${potential_savings:,.0f} | {untagged_resources} |\n"

        # Add summary section
        markdown_content += f"""

## Organization Summary

### Cost Trends
- **Month-over-Month Change**: {self._calculate_mom_change(multi_profile_data):.1f}%
- **Highest Cost Account**: {self._get_highest_cost_account(multi_profile_data)}
- **Most Opportunities**: {self._get_most_optimization_account(multi_profile_data)}

### Optimization Recommendations
1. **Immediate Actions**: Review {sum(p.get("stopped_ec2", 0) for p in multi_profile_data)} stopped EC2 instances
2. **Storage Cleanup**: Clean up {sum(p.get("unused_volumes", 0) for p in multi_profile_data)} unused EBS volumes
3. **Network Optimization**: Release {sum(p.get("unused_eips", 0) for p in multi_profile_data)} unused Elastic IPs
4. **Governance**: Tag {sum(p.get("untagged_resources", 0) for p in multi_profile_data)} untagged resources

---
*Generated by CloudOps & FinOps Runbooks Module v{__version__}*
"""

        return markdown_content

    def export_to_file(self, markdown_content: str, filename: str, account_type: str = "single") -> str:
        """
        Export markdown content to file with intelligent naming.

        Args:
            markdown_content: Markdown content to export
            filename: Base filename (without extension)
            account_type: Type of analysis (single, multi, organization)

        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not filename.endswith(".md"):
            filename = f"{filename}_{account_type}_account_{timestamp}.md"

        filepath = self.output_dir / filename

        # Show progress indication
        print_info(f"📝 Generating markdown export: {filename}")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print_success(f"Rich-styled markdown export saved: {filepath}")
            print_info(f"🔗 Ready for MkDocs or GitHub documentation sharing")
            return str(filepath)

        except Exception as e:
            print_warning(f"Failed to save markdown export: {e}")
            return ""

    def _get_cost_status_emoji(self, cost: float) -> str:
        """Get emoji based on cost level."""
        if cost >= 10000:
            return "🔴 High"
        elif cost >= 1000:
            return "🟡 Medium"
        else:
            return "🟢 Low"

    def _get_trend_emoji(self, trend: str) -> str:
        """Get emoji for cost trend."""
        trend_lower = trend.lower()
        if "up" in trend_lower or "increas" in trend_lower:
            return "📈"
        elif "down" in trend_lower or "decreas" in trend_lower:
            return "📉"
        else:
            return "➡️"

    def _get_budget_status_emoji(self, status: str) -> str:
        """Get emoji for budget status."""
        status_lower = status.lower()
        if "over" in status_lower or "exceeded" in status_lower:
            return "❌ Over"
        elif "warn" in status_lower:
            return "⚠️ Warn"
        elif "ok" in status_lower or "good" in status_lower:
            return "✅ OK"
        else:
            return "❓ Unknown"

    def _calculate_mom_change(self, profiles: List[Dict[str, Any]]) -> float:
        """
        Calculate month-over-month change percentage with smart partial month normalization.

        Features:
        - Detects partial months and applies normalization
        - Handles equal-day vs full-month comparisons intelligently
        - Integrates with existing period metadata infrastructure
        - Rich CLI formatting for transparency
        """
        try:
            from datetime import date, timedelta

            from ..common.rich_utils import console

            total_current = sum(p.get("total_cost", 0) for p in profiles)
            total_last = sum(p.get("last_month_cost", 0) for p in profiles)

            if total_last == 0:
                return 0.0

            # Check for period metadata in profiles to detect partial month scenarios
            period_metadata = None
            for profile in profiles:
                if "period_metadata" in profile and profile["period_metadata"]:
                    period_metadata = profile["period_metadata"]
                    break

            # Calculate raw percentage change
            raw_change = ((total_current - total_last) / total_last) * 100

            # If no period metadata available, return raw calculation
            if not period_metadata:
                return raw_change

            # Extract period information
            current_days = period_metadata.get("current_days", 0)
            previous_days = period_metadata.get("previous_days", 0)
            alignment_strategy = period_metadata.get("period_alignment_strategy", "standard")
            is_partial_comparison = period_metadata.get("is_partial_comparison", False)
            comparison_type = period_metadata.get("comparison_type", "standard_month_comparison")

            # Apply smart normalization based on period alignment strategy
            if alignment_strategy == "equal_days" and current_days > 0 and previous_days > 0:
                # Equal-day comparison - use raw calculation (already normalized)
                normalized_change = raw_change
                console.log(
                    f"[dim cyan]📊 MoM calculation: equal-day comparison ({current_days} vs {previous_days} days) - no adjustment needed[/]"
                )

            elif is_partial_comparison and current_days > 0 and previous_days > 0:
                # Partial month vs full month - apply normalization factor
                if current_days < previous_days:
                    # Current month is partial, previous is full - normalize previous month
                    normalization_factor = current_days / previous_days
                    adjusted_last_cost = total_last * normalization_factor
                    normalized_change = (
                        ((total_current - adjusted_last_cost) / adjusted_last_cost) * 100
                        if adjusted_last_cost > 0
                        else 0.0
                    )

                    console.log(
                        f"[yellow]⚡ MoM normalization: partial current month ({current_days} days) vs full previous ({previous_days} days)[/]"
                    )
                    console.log(
                        f"[dim yellow]   Normalized factor: {normalization_factor:.2f} (adjusted previous: ${adjusted_last_cost:,.2f})[/]"
                    )

                elif current_days > previous_days:
                    # Previous month is partial, current is full - normalize current month
                    normalization_factor = previous_days / current_days
                    adjusted_current_cost = total_current * normalization_factor
                    normalized_change = (
                        ((adjusted_current_cost - total_last) / total_last) * 100 if total_last > 0 else 0.0
                    )

                    console.log(
                        f"[yellow]⚡ MoM normalization: full current month ({current_days} days) vs partial previous ({previous_days} days)[/]"
                    )
                    console.log(
                        f"[dim yellow]   Normalized factor: {normalization_factor:.2f} (adjusted current: ${adjusted_current_cost:,.2f})[/]"
                    )
                else:
                    # Equal days but marked as partial comparison - use raw calculation
                    normalized_change = raw_change
                    console.log(
                        f"[cyan]📊 MoM calculation: equal periods ({current_days} days) - using standard calculation[/]"
                    )
            else:
                # Standard monthly comparison - use raw calculation
                normalized_change = raw_change
                console.log(f"[dim cyan]📊 MoM calculation: standard monthly comparison - no normalization applied[/]")

            # Detect and warn about extreme changes that might indicate data issues
            if abs(normalized_change) > 200:  # >200% change
                today = date.today()
                days_into_month = today.day

                if days_into_month <= 5:  # Early in month
                    console.log(
                        f"[yellow]⚠️  Large MoM change ({normalized_change:.1f}%) detected in early month (day {days_into_month})[/]"
                    )
                    console.log(
                        f"[dim yellow]   This may be due to limited current month data - consider weekly analysis for accuracy[/]"
                    )
                elif comparison_type == "standard_month_comparison" and is_partial_comparison:
                    console.log(
                        f"[yellow]⚠️  Large MoM change ({normalized_change:.1f}%) with unequal periods detected[/]"
                    )
                    console.log(
                        f"[dim yellow]   Consider using equal-day comparison for more accurate trend analysis[/]"
                    )

            return normalized_change

        except Exception as e:
            # Fallback to simple calculation if enhancement fails
            console.log(f"[red]⚠️  MoM calculation enhancement failed: {str(e)}, using fallback calculation[/]")
            total_current = sum(p.get("total_cost", 0) for p in profiles)
            total_last = sum(p.get("last_month_cost", 0) for p in profiles)

            if total_last == 0:
                return 0.0

            return ((total_current - total_last) / total_last) * 100

    def _get_highest_cost_account(self, profiles: List[Dict[str, Any]]) -> str:
        """Get the account with highest cost."""
        if not profiles:
            return "N/A"

        highest = max(profiles, key=lambda p: p.get("total_cost", 0))
        return highest.get("profile_name", "Unknown")[:20]

    def _get_most_optimization_account(self, profiles: List[Dict[str, Any]]) -> str:
        """Get the account with most optimization opportunities."""
        if not profiles:
            return "N/A"

        highest = max(profiles, key=lambda p: p.get("potential_savings", 0))
        return highest.get("profile_name", "Unknown")[:20]

    def format_vpc_cleanup_table(self, vpc_candidates: List[Any]) -> str:
        """
        Format VPC cleanup candidates into 15-column markdown table.

        Args:
            vpc_candidates: List of VPCCandidate objects from vpc.unified_scenarios

        Returns:
            Markdown formatted table string with VPC cleanup analysis
        """
        if not vpc_candidates:
            return "⚠️ No VPC candidates to format"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Build table header and separator
        headers = [
            "Account_ID",
            "VPC_ID",
            "VPC_Name",
            "CIDR_Block",
            "Overlapping",
            "Is_Default",
            "ENI_Count",
            "Tags",
            "Flow_Logs",
            "TGW/Peering",
            "LBs_Present",
            "IaC",
            "Timeline",
            "Decision",
            "Owners/Approvals",
            "Notes",
        ]

        markdown_lines = [
            "# VPC Cleanup Analysis Report",
            "",
            f"**Generated**: {timestamp}",
            f"**Total VPC Candidates**: {len(vpc_candidates)}",
            f"**Analysis Source**: Runbooks VPC Module latest version",
            "",
            "## VPC Cleanup Decision Table",
            "",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---" for _ in headers]) + " |",
        ]

        # Process each VPC candidate with enhanced data extraction
        for candidate in vpc_candidates:
            # Extract data with safe attribute access and formatting
            account_id = getattr(candidate, "account_id", "Unknown")
            vpc_id = getattr(candidate, "vpc_id", "Unknown")
            vpc_name = getattr(candidate, "vpc_name", "") or "Unnamed"
            cidr_block = getattr(candidate, "cidr_block", "Unknown")

            # Handle overlapping logic - check CIDR conflicts
            overlapping = self._check_cidr_overlapping(cidr_block, vpc_candidates)

            # Enhanced is_default handling
            is_default = getattr(candidate, "is_default", False)
            is_default_display = "⚠️ Yes" if is_default else "No"

            # Enhanced ENI count
            dependency_analysis = getattr(candidate, "dependency_analysis", None)
            eni_count = dependency_analysis.eni_count if dependency_analysis else 0

            # Enhanced tags with owner focus
            tags_dict = getattr(candidate, "tags", {}) or {}
            tags_display = self._format_tags_for_owners_display(tags_dict)

            # Flow logs detection
            flow_logs = self._detect_flow_logs(candidate)

            # TGW/Peering detection
            tgw_peering = self._detect_tgw_peering(candidate)

            # Load balancers detection
            lbs_present = self._detect_load_balancers(candidate)

            # IaC detection from tags
            iac_detected = self._detect_iac_from_tags(tags_dict)

            # Timeline estimation based on VPC state
            timeline = self._estimate_cleanup_timeline(candidate)

            # Decision based on bucket classification
            decision = self._determine_cleanup_decision(candidate)

            # Enhanced owners/approvals extraction
            owners_approvals = self._extract_owners_approvals(tags_dict, is_default)

            # Notes based on VPC characteristics
            notes = self._generate_vpc_notes(candidate)
            overlapping = "Yes" if getattr(candidate, "overlapping", False) else "No"

            # Format boolean indicators with emoji
            is_default = "⚠️ Yes" if getattr(candidate, "is_default", False) else "✅ No"
            flow_logs = "✅ Yes" if getattr(candidate, "flow_logs_enabled", False) else "❌ No"
            tgw_peering = "✅ Yes" if getattr(candidate, "tgw_peering_attached", False) else "❌ No"
            load_balancers = "✅ Yes" if getattr(candidate, "load_balancers_present", False) else "❌ No"
            iac_managed = "✅ Yes" if getattr(candidate, "iac_managed", False) else "❌ No"

            # ENI Count handling
            eni_count = getattr(candidate, "eni_count", 0)

            # Tags formatting - prioritize important tags with enhanced display
            tags = getattr(candidate, "tags", {}) or {}
            relevant_tags = []
            if tags:
                # Priority order for business-relevant tags
                priority_keys = [
                    "Name",
                    "Environment",
                    "Project",
                    "Owner",
                    "BusinessOwner",
                    "Team",
                    "CostCenter",
                    "Application",
                ]
                for key in priority_keys:
                    if key in tags and tags[key] and len(relevant_tags) < 3:  # Increased limit for better visibility
                        relevant_tags.append(f"{key}:{tags[key]}")

                # Add other important tags if space available
                for key, value in tags.items():
                    if key not in priority_keys and value and len(relevant_tags) < 3:
                        relevant_tags.append(f"{key}:{value}")

            # Enhanced display logic for tags
            if relevant_tags:
                tags_display = "; ".join(relevant_tags)
                if len(tags_display) > 35:  # Slightly increased width for better readability
                    tags_display = tags_display[:32] + "..."
            elif tags:
                # If tags exist but none were priority, show count
                tags_display = f"({len(tags)} tags)"
            else:
                # No tags at all
                tags_display = "No tags"

            # Timeline and Decision
            timeline = getattr(candidate, "cleanup_timeline", "") or getattr(
                candidate, "implementation_timeline", "Unknown"
            )

            # Decision handling - check for different decision attribute names
            decision_attr = getattr(candidate, "decision", None)
            if decision_attr:
                if hasattr(decision_attr, "value"):
                    decision = decision_attr.value
                else:
                    decision = str(decision_attr)
            else:
                # Fallback decision logic based on risk/dependencies
                decision = getattr(candidate, "cleanup_bucket", "Unknown")

            # Owners/Approvals - Enhanced extraction from tags if not populated
            owners = getattr(candidate, "owners_approvals", []) or getattr(candidate, "stakeholders", [])

            # If no owners found via attributes, try to extract from tags directly
            if not owners and tags:
                owner_keys = ["Owner", "BusinessOwner", "TechnicalOwner", "Team", "Contact", "CreatedBy", "ManagedBy"]
                for key in owner_keys:
                    if key in tags and tags[key]:
                        if "business" in key.lower() or "manager" in tags[key].lower():
                            owners.append(f"{tags[key]} (Business)")
                        elif "technical" in key.lower() or any(
                            tech in tags[key].lower() for tech in ["ops", "devops", "engineering"]
                        ):
                            owners.append(f"{tags[key]} (Technical)")
                        else:
                            owners.append(tags[key])
                        break  # Take first found owner to avoid clutter

            if owners:
                owners_display = "; ".join(owners)
                if len(owners_display) > 30:  # Increased width for better display
                    owners_display = owners_display[:27] + "..."
            else:
                # Enhanced "unknown" display based on VPC characteristics
                if getattr(candidate, "is_default", False):
                    owners_display = "System Default"
                elif getattr(candidate, "iac_detected", False):
                    owners_display = "IaC Managed"
                else:
                    owners_display = "No owner tags"

            # Notes - combination of risk assessment and business impact
            notes_parts = []
            risk_level = getattr(candidate, "risk_level", None)
            if risk_level:
                risk_val = risk_level.value if hasattr(risk_level, "value") else str(risk_level)
                notes_parts.append(f"Risk:{risk_val}")

            business_impact = getattr(candidate, "business_impact", "")
            if business_impact:
                notes_parts.append(business_impact[:15])  # Truncate

            notes = "; ".join(notes_parts) if notes_parts else getattr(candidate, "notes", "No notes")
            if len(notes) > 30:  # Truncate for table formatting
                notes = notes[:27] + "..."

            # Create table row - escape pipes for markdown compatibility
            row_data = [
                account_id,
                vpc_id,
                vpc_name,
                cidr_block,
                overlapping,
                is_default,
                str(eni_count),
                tags_display,
                flow_logs,
                tgw_peering,
                load_balancers,
                iac_managed,
                timeline,
                decision,
                owners_display,
                notes,
            ]

            # Escape pipes and format row
            escaped_data = [str(cell).replace("|", "\\|") for cell in row_data]
            markdown_lines.append("| " + " | ".join(escaped_data) + " |")

        # Add summary statistics
        total_vpcs = len(vpc_candidates)
        default_vpcs = sum(1 for c in vpc_candidates if getattr(c, "is_default", False))
        flow_logs_enabled = sum(1 for c in vpc_candidates if getattr(c, "flow_logs_enabled", False))
        iac_managed_count = sum(1 for c in vpc_candidates if getattr(c, "iac_managed", False))
        zero_eni_vpcs = sum(1 for c in vpc_candidates if getattr(c, "eni_count", 1) == 0)

        markdown_lines.extend(
            [
                "",
                "## Analysis Summary",
                "",
                f"- **Total VPCs Analyzed**: {total_vpcs}",
                f"- **Default VPCs**: {default_vpcs} ({(default_vpcs / total_vpcs * 100):.1f}%)",
                f"- **Flow Logs Enabled**: {flow_logs_enabled} ({(flow_logs_enabled / total_vpcs * 100):.1f}%)",
                f"- **IaC Managed**: {iac_managed_count} ({(iac_managed_count / total_vpcs * 100):.1f}%)",
                f"- **Zero ENI Attachments**: {zero_eni_vpcs} ({(zero_eni_vpcs / total_vpcs * 100):.1f}%)",
                "",
                "## Cleanup Recommendations",
                "",
                "1. **Priority 1**: VPCs with zero ENI attachments and no dependencies",
                "2. **Priority 2**: Default VPCs with no active resources",
                "3. **Priority 3**: Non-IaC managed VPCs requiring manual cleanup",
                "4. **Review Required**: VPCs with unclear ownership or business impact",
                "",
                "---",
                f"*Generated by Runbooks VPC Module latest version at {timestamp}*",
            ]
        )

        return "\n".join(markdown_lines)

    def export_vpc_analysis_to_file(
        self, vpc_candidates: List[Any], filename: str = None, output_dir: str = "./exports"
    ) -> str:
        """
        Export VPC analysis to markdown file with intelligent naming.

        Args:
            vpc_candidates: List of VPC candidates from analysis
            filename: Base filename (optional, auto-generated if not provided)
            output_dir: Output directory path

        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"vpc-cleanup-analysis-{timestamp}.md"

        # Ensure .md extension
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate markdown content
        markdown_content = self.format_vpc_cleanup_table(vpc_candidates)

        # Write to file
        filepath = output_path / filename

        print_info(f"📝 Exporting VPC analysis to: {filename}")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            print_success(f"✅ VPC analysis exported: {filepath}")
            print_info(f"🔗 Ready for executive review or documentation systems")
            return str(filepath)

        except Exception as e:
            print_warning(f"❌ Failed to export VPC analysis: {e}")
            return ""

    def _check_cidr_overlapping(self, cidr_block: str, vpc_candidates: List[Any]) -> str:
        """Check for CIDR block overlapping across VPCs."""
        if not cidr_block or not vpc_candidates:
            return "No"

        # Simple overlapping check - in enterprise scenario, this would use more sophisticated logic
        current_cidr = cidr_block
        for candidate in vpc_candidates:
            other_cidr = getattr(candidate, "cidr_block", None)
            if (
                other_cidr
                and other_cidr != current_cidr
                and current_cidr.startswith(other_cidr.split("/")[0].rsplit(".", 1)[0])
            ):
                return "Yes"

        return "No"

    def _detect_flow_logs(self, candidate: Any) -> str:
        """Detect if VPC has flow logs enabled."""
        return "Yes" if getattr(candidate, "flow_logs_enabled", False) else "No"

    def _detect_tgw_peering(self, candidate: Any) -> str:
        """Analyze Transit Gateway and VPC peering connections."""
        # Check for TGW attachments and peering connections
        tgw_attachments = getattr(candidate, "tgw_attachments", []) or []
        peering_connections = getattr(candidate, "peering_connections", []) or []

        if tgw_attachments or peering_connections:
            connection_count = len(tgw_attachments) + len(peering_connections)
            return f"Yes ({connection_count})"
        return "No"

    def _detect_load_balancers(self, candidate: Any) -> str:
        """Detect load balancers in the VPC."""
        load_balancers = getattr(candidate, "load_balancers", []) or []
        return "Yes" if load_balancers else "No"

    def _detect_iac_from_tags(self, tags_dict: dict) -> str:
        """Detect Infrastructure as Code management from tags."""
        iac_keys = ["aws:cloudformation:stack-name", "terraform:module", "cdktf:stack", "pulumi:project"]
        for key in iac_keys:
            if key in tags_dict and tags_dict[key]:
                return "Yes"
        return "No"

    def _estimate_cleanup_timeline(self, candidate: Any) -> str:
        """Estimate cleanup timeline based on complexity."""
        # Simple heuristic based on dependencies
        if hasattr(candidate, "dependency_analysis") and candidate.dependency_analysis:
            eni_count = getattr(candidate.dependency_analysis, "eni_count", 0)
        else:
            eni_count = 0

        if eni_count == 0:
            return "1-2 days"
        elif eni_count < 5:
            return "3-5 days"
        else:
            return "1-2 weeks"

    def _format_cleanup_decision(self, candidate: Any) -> str:
        """Format cleanup decision recommendation."""
        recommendation = getattr(candidate, "cleanup_recommendation", "unknown")
        if recommendation == "delete":
            return "Delete"
        elif recommendation == "keep":
            return "Keep"
        elif recommendation == "review":
            return "Review"
        else:
            return "TBD"

    def _format_tags_for_owners_display(self, tags_dict: dict) -> str:
        """Format tags for display with priority on ownership information."""
        if not tags_dict:
            return "No tags"

        # Priority keys focusing on ownership and approvals
        priority_keys = ["Name", "Owner", "BusinessOwner", "TechnicalOwner", "Team", "Contact"]
        relevant_tags = []

        for key in priority_keys:
            if key in tags_dict and tags_dict[key]:
                relevant_tags.append(f"{key}:{tags_dict[key]}")
                if len(relevant_tags) >= 3:  # Limit for table readability
                    break

        return "; ".join(relevant_tags) if relevant_tags else f"({len(tags_dict)} tags)"

    def _determine_cleanup_decision(self, candidate: Any) -> str:
        """Determine cleanup decision based on VPC analysis."""
        # Check the cleanup bucket from three-bucket strategy
        cleanup_bucket = getattr(candidate, "cleanup_bucket", "unknown")

        if cleanup_bucket == "bucket_1":
            return "Delete"
        elif cleanup_bucket == "bucket_2":
            return "Review"
        elif cleanup_bucket == "bucket_3":
            return "Keep"
        else:
            # Fallback logic based on other attributes
            is_default = getattr(candidate, "is_default", False)
            has_eni = getattr(candidate, "eni_count", 0) > 0

            if is_default and not has_eni:
                return "Delete"
            elif has_eni:
                return "Review"
            else:
                return "TBD"

    def _extract_owners_approvals(self, tags_dict: dict, is_default: bool) -> str:
        """Extract owners and approval information from tags and VPC status."""
        # Extract from tags with enhanced owner detection
        owner_keys = ["Owner", "BusinessOwner", "TechnicalOwner", "Team", "Contact", "CreatedBy", "ManagedBy"]

        extracted_owners = []
        for key in owner_keys:
            if key in tags_dict and tags_dict[key]:
                value = tags_dict[key]
                if "business" in key.lower():
                    extracted_owners.append(f"{value} (Business)")
                elif "technical" in key.lower():
                    extracted_owners.append(f"{value} (Technical)")
                elif "team" in key.lower():
                    extracted_owners.append(f"{value} (Team)")
                else:
                    extracted_owners.append(f"{value} ({key})")

                if len(extracted_owners) >= 2:  # Limit for table readability
                    break

        if extracted_owners:
            return "; ".join(extracted_owners)

        # Fallback based on VPC type
        if is_default:
            return "System Default VPC"
        else:
            # Check for IaC tags
            iac_keys = ["aws:cloudformation:stack-name", "terraform:module", "cdktf:stack", "pulumi:project"]
            for key in iac_keys:
                if key in tags_dict and tags_dict[key]:
                    return "IaC Managed"
            return "No owner tags found"

    def _generate_vpc_notes(self, candidate: Any) -> str:
        """Generate comprehensive notes for VPC candidate."""
        notes = []

        # Add bucket classification note
        cleanup_bucket = getattr(candidate, "cleanup_bucket", "unknown")
        if cleanup_bucket == "bucket_1":
            notes.append("Internal data plane - safe for cleanup")
        elif cleanup_bucket == "bucket_2":
            notes.append("External interconnects - requires analysis")
        elif cleanup_bucket == "bucket_3":
            notes.append("Control plane - manual review required")

        # Add ENI count if significant
        if hasattr(candidate, "dependency_analysis") and candidate.dependency_analysis:
            eni_count = getattr(candidate.dependency_analysis, "eni_count", 0)
            if eni_count > 0:
                notes.append(f"{eni_count} ENI attachments")

        # Add default VPC note
        if getattr(candidate, "is_default", False):
            notes.append("Default VPC (CIS compliance issue)")

        # Add IaC detection
        if getattr(candidate, "iac_detected", False):
            notes.append("IaC managed")

        # Add security concerns
        risk_level = getattr(candidate, "risk_level", "unknown")
        if risk_level == "high":
            notes.append("High security risk")

        return "; ".join(notes) if notes else "Standard VPC cleanup candidate"


def export_finops_to_markdown(
    profile_data: Union[Dict[str, Any], List[Dict[str, Any]]],
    output_dir: str = "./exports",
    filename: str = "finops_analysis",
    account_type: str = "auto",
) -> str:
    """
    Export FinOps analysis to markdown format.

    Args:
        profile_data: Single profile dict or list of profiles
        output_dir: Output directory for exports
        filename: Base filename for export
        account_type: Type of analysis (single, multi, auto)

    Returns:
        Path to exported markdown file
    """
    exporter = MarkdownExporter(output_dir)

    # Determine account type if auto
    if account_type == "auto":
        account_type = "multi" if isinstance(profile_data, list) else "single"

    # Generate appropriate markdown content
    if account_type == "single" and isinstance(profile_data, dict):
        markdown_content = exporter.create_single_account_export(
            profile_data, profile_data.get("account_id", "Unknown"), profile_data.get("profile_name", "Unknown")
        )
    elif account_type == "multi" and isinstance(profile_data, list):
        markdown_content = exporter.create_multi_account_export(profile_data)
    else:
        raise ValueError(f"Invalid combination: account_type={account_type}, data_type={type(profile_data)}")

    # Export to file
    return exporter.export_to_file(markdown_content, filename, account_type)


def export_dataframe_to_markdown(
    df: "pd.DataFrame",
    output_file: str,
    title: str,
    summary_metrics: Optional[Dict[str, Any]] = None,
    recommendations: Optional[List[str]] = None,
    max_rows: int = 50,
) -> str:
    """
    Export DataFrame to GitHub-flavored Markdown with executive formatting.

    This is a lightweight utility for CLI analyzers (ec2, workspaces, snapshots)
    to export analysis results to markdown format.

    Args:
        df: Data to export
        output_file: Path to .md file
        title: Report title
        summary_metrics: Key metrics dict (e.g., {"Total Cost": "$1,234", "Count": 42})
        recommendations: List of action items
        max_rows: Max rows in table (prevent huge files)

    Returns:
        Path to created file

    Examples:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'instance_id': ['i-123'], 'cost': [100]})
        >>> export_dataframe_to_markdown(
        ...     df=df,
        ...     output_file='ec2-report.md',
        ...     title='EC2 Decommission Analysis Report',
        ...     summary_metrics={'Total Instances': 1, 'Total Cost': '$100'},
        ...     recommendations=['Review MUST tier instances']
        ... )
        'ec2-report.md'
    """
    import pandas as pd

    with open(output_file, "w") as f:
        # Header
        f.write(f"# {title}\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Executive Summary
        if summary_metrics:
            f.write("## Executive Summary\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            for key, value in summary_metrics.items():
                f.write(f"| {key} | {value} |\n")
            f.write("\n")

        # Recommendations
        if recommendations:
            f.write("## Recommendations\n\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
            f.write("\n")

        # Data Table
        f.write("## Detailed Analysis\n\n")
        if len(df) > max_rows:
            f.write(f"*Showing top {max_rows} of {len(df)} rows*\n\n")
            df_display = df.head(max_rows)
        else:
            df_display = df

        # Convert DataFrame to markdown table (pipe-formatted)
        f.write(df_display.to_markdown(index=False))
        f.write("\n\n---\n")
        f.write(f"*Generated by Runbooks FinOps CLI v{__version__}*\n")

    return output_file


# Export public interface
__all__ = ["MarkdownExporter", "export_finops_to_markdown", "export_dataframe_to_markdown"]
