"""
String/file-based exporters (Markdown, JSON, CSV).

Track B v1.1.26: Added persona parameter support for role-specific formatting.
"""

import json
from datetime import datetime
from typing import Any, Dict, Literal, Optional

import pandas as pd

from .base_exporter import BaseExporter

# Persona type (Track B v1.1.26)
PersonaType = Literal["cfo", "cto", "ceo", "sre", "architect", "technical", "executive"]


class MarkdownExporter(BaseExporter):
    """
    Export as markdown format.

    Track B v1.1.26: Added persona parameter for role-specific markdown rendering.
    """

    def __init__(self, persona: Optional[PersonaType] = None, **kwargs):
        super().__init__(title="Activity Health Analysis")
        self.persona = persona  # Track B v1.1.26

    def get_format_name(self) -> str:
        """Return format identifier."""
        return "markdown"

    def export(self, enriched_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Render markdown export.

        Args:
            enriched_data: Dictionary with service names as keys, DataFrames as values
            output_path: Optional file path to save markdown

        Returns:
            Markdown string or file path if saved
        """
        md = []

        # Title
        md_title = self.metadata.title or "Activity Health Analysis"
        md.append(f"# {md_title}\n")
        md.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

        # Executive Summary
        md.append("## Executive Summary\n\n")
        total_must = sum(
            len(df[df["decommission_tier"] == "MUST"]) if "decommission_tier" in df.columns else 0
            for df in enriched_data.values()
            if isinstance(df, pd.DataFrame)
        )
        total_should = sum(
            len(df[df["decommission_tier"] == "SHOULD"]) if "decommission_tier" in df.columns else 0
            for df in enriched_data.values()
            if isinstance(df, pd.DataFrame)
        )
        total_resources = sum(len(df) for df in enriched_data.values() if isinstance(df, pd.DataFrame))
        md.append(f"- **Total Resources Analyzed**: {total_resources}\n")
        md.append(f"- **Immediate Action Required (MUST)**: {total_must} resources\n")
        md.append(f"- **Review Recommended (SHOULD)**: {total_should} resources\n\n")

        # Service-by-service breakdown
        md.append("## Service Analysis\n\n")

        for service, df in enriched_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            # Service header
            service_display = self._get_service_display_name(service)
            md.append(f"### {service_display} ({len(df)} resources)\n\n")

            # Tier distribution table
            if "decommission_tier" in df.columns:
                tier_counts = df["decommission_tier"].value_counts().to_dict()

                md.append("| Tier | Count | Action | Priority |\n")
                md.append("|------|-------|--------|----------|\n")

                for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
                    if tier in tier_counts:
                        action = self._get_tier_action_text(tier)
                        priority = self._get_tier_priority(tier)
                        md.append(f"| {tier} | {tier_counts[tier]} | {action} | {priority} |\n")

                md.append("\n")

            # Signal legend
            signal_legend = self._get_signal_legend(service)
            if signal_legend:
                md.append(f"**Signals**: {signal_legend}\n\n")

            # Top candidates for decommissioning
            if "decommission_tier" in df.columns and "decommission_score" in df.columns:
                must_df = df[df["decommission_tier"] == "MUST"].nlargest(5, "decommission_score")
                if not must_df.empty:
                    md.append("**Top Decommission Candidates**:\n")
                    for _, row in must_df.iterrows():
                        resource_id = row.get(
                            "resource_id",
                            row.get("instance_id", row.get("bucket_name", "Unknown")),
                        )
                        score = row.get("decommission_score", 0)
                        md.append(f"- `{resource_id}` (Score: {score})\n")
                    md.append("\n")

        # Recommendations
        md.append("## Recommendations\n\n")
        md.append("1. **Immediate Actions** (MUST tier):\n")
        md.append("   - Review and terminate/delete resources marked as MUST\n")
        md.append("   - Estimated savings potential: High\n")
        md.append("   - Risk level: Low (inactive resources)\n\n")
        md.append("2. **Scheduled Review** (SHOULD tier):\n")
        md.append("   - Schedule review of SHOULD resources within 30 days\n")
        md.append("   - Validate usage patterns before decommissioning\n")
        md.append("   - Consider rightsizing as alternative\n\n")
        md.append("3. **Optimization Opportunities** (COULD tier):\n")
        md.append("   - Consider for next optimization cycle\n")
        md.append("   - May benefit from reserved instances or savings plans\n\n")

        markdown_str = "".join(md)

        if output_path:
            with open(output_path, "w") as f:
                f.write(markdown_str)
            return output_path
        return markdown_str

    def _get_service_display_name(self, service: str) -> str:
        """Get human-readable service name."""
        display_names = {
            "ec2": "EC2 Instances",
            "ecs": "ECS Clusters/Tasks",
            "s3": "S3 Buckets",
            "dynamodb": "DynamoDB Tables",
            "rds": "RDS Databases",
            "workspaces": "WorkSpaces",
            "snapshots": "EBS Snapshots",
            "alb": "Application Load Balancers",
            "nlb": "Network Load Balancers",
            "route53": "Route53 Hosted Zones",
            "vpc": "VPC Resources",
            "appstream": "AppStream 2.0 Fleets",
        }
        return display_names.get(service, service.upper())

    def _get_tier_action_text(self, tier: str) -> str:
        """Get text action description for tier."""
        actions = {
            "MUST": "Decommission immediately",
            "SHOULD": "Review and decommission",
            "COULD": "Consider optimization",
            "KEEP": "Maintain active",
        }
        return actions.get(tier, "Unknown")

    def _get_tier_priority(self, tier: str) -> str:
        """Get priority level for tier."""
        priorities = {"MUST": "Critical", "SHOULD": "High", "COULD": "Medium", "KEEP": "N/A"}
        return priorities.get(tier, "Unknown")

    def _get_signal_legend(self, service: str) -> Optional[str]:
        """Get signal legend for service."""
        signal_maps = {
            "ec2": "E1-E7: Compute Optimizer, CPU, CloudTrail, SSM, ASG/LB, I/O, Cost",
            "ecs": "C6-C7: Task Scheduling Mismatch, Container Right-Sizing",
            "s3": "S1-S7: Storage Lens, Class, Security, Lifecycle, Request, Version, Replication",
            "dynamodb": "D1-D7: Capacity, GSI, PITR, Streams, Cost Efficiency, Stream Orphans, On-Demand Opportunity",
            "workspaces": "W1-W6: Usage, State, Connection, Bundle, Directory, Tags",
            "rds": "R1-R7: CPU, Storage, Connections, Backup, Multi-AZ, Read Replicas, Age",
            "appstream": "A1-A7: Usage, Sessions, Capacity, State, Age, Cost, Users",
            "lambda": "L1-L7: Invocations, Duration, Errors, Cost, Memory, Concurrency, Timeout",
            "cloudwatch": "M1-M7: Metrics, Alarms, Dashboards, Logs, Insights, Events, Usage",
            "config": "CFG1-CFG5: Recorder, Rules, Conformance, Remediation, Aggregator",
            "cloudtrail": "CT1-CT5: Trail, Events, Insights, Organization, Multi-Region",
        }
        return signal_maps.get(service)


class JsonExporter(BaseExporter):
    """
    Export as JSON structured data.

    Track B v1.1.26: Added persona parameter for role-specific JSON rendering.
    """

    def __init__(self, persona: Optional[PersonaType] = None, **kwargs):
        super().__init__(title="Activity Health JSON")
        self.persona = persona  # Track B v1.1.26

    def get_format_name(self) -> str:
        """Return format identifier."""
        return "json"

    def export(self, enriched_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Render JSON export.

        Args:
            enriched_data: Dictionary with service names as keys, DataFrames as values
            output_path: Optional file path to save JSON

        Returns:
            JSON string or file path if saved
        """
        json_data = {}
        for service, df in enriched_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Convert DataFrame to dict, handling NaN values
                json_data[service] = df.fillna("").to_dict(orient="records")

        json_str = json.dumps(json_data, indent=2, default=str)

        if output_path:
            with open(output_path, "w") as f:
                f.write(json_str)
            return output_path
        return json_str


class CsvExporter(BaseExporter):
    """
    Export as CSV multi-service format.

    Track B v1.1.26: Added persona parameter for role-specific CSV rendering.
    """

    def __init__(self, persona: Optional[PersonaType] = None, **kwargs):
        super().__init__(title="Activity Health CSV")
        self.persona = persona  # Track B v1.1.26

    def get_format_name(self) -> str:
        """Return format identifier."""
        return "csv"

    def export(self, enriched_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Render CSV export.

        Args:
            enriched_data: Dictionary with service names as keys, DataFrames as values
            output_path: Optional file path to save CSV

        Returns:
            CSV string or file path if saved
        """
        csv_parts = []

        for service, df in enriched_data.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Add service column
                df_copy = df.copy()
                df_copy["service"] = service

                # Convert to CSV
                csv_parts.append(df_copy.to_csv(index=False))

        csv_str = "\n".join(csv_parts)

        if output_path:
            with open(output_path, "w") as f:
                f.write(csv_str)
            return output_path
        return csv_str
