"""
Console-based exporters (Tree, Table).

Track B v1.1.26: Added persona parameter support for role-specific formatting.
"""

from typing import Any, Dict, Literal, Optional

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from .base_exporter import BaseExporter

# Persona type (Track B v1.1.26)
PersonaType = Literal["cfo", "cto", "ceo", "sre", "architect", "technical", "executive"]


def format_cost(cost: float) -> str:
    """Format cost as currency string."""
    if cost >= 1000:
        return f"${cost:,.0f}"
    elif cost >= 1:
        return f"${cost:.2f}"
    else:
        return f"${cost:.4f}"


class TreeExporter(BaseExporter):
    """
    Export as hierarchical Rich tree (console output).

    Track B v1.1.26: Added persona parameter for role-specific tree rendering.
    """

    def __init__(
        self,
        console_instance: Optional[Console] = None,
        persona: Optional[PersonaType] = None,  # Track B v1.1.26
        **kwargs,
    ):
        super().__init__(title="Activity Health Tree")
        self.console = console_instance or Console()
        self.persona = persona  # Track B v1.1.26

    def get_format_name(self) -> str:
        """Return format identifier."""
        return "tree"

    def export(self, enriched_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Render tree to console, return empty string (console output)."""
        tree_title = self.metadata.title or "🌳 [bold cyan]Activity Health Tree[/bold cyan]"
        tree = Tree(tree_title)

        total_must = 0
        total_should = 0
        total_could = 0
        total_keep = 0

        # Track if we have any data to display
        has_data = False

        for service, df in enriched_data.items():
            if not isinstance(df, pd.DataFrame):
                continue

            # Handle empty DataFrames gracefully
            if df.empty:
                service_label = self._get_service_label(service, 0)
                service_branch = tree.add(service_label)
                service_branch.add("[dim]No resources found[/dim]")
                continue

            has_data = True

            # v1.1.27 Enhancement: Sort S3 buckets by Cost/mo (descending) for FinOps prioritization
            if service == "s3" and "monthly_cost" in df.columns:
                df = df.sort_values(by="monthly_cost", ascending=False).reset_index(drop=True)
                # Update enriched_data dict in place so sorting persists to other renderers
                enriched_data[service] = df

            # Get service label
            service_label = self._get_service_label(service, len(df))

            # Add service branch
            service_branch = tree.add(service_label)

            # Calculate tier distribution
            if "decommission_tier" in df.columns:
                tier_counts = df["decommission_tier"].value_counts().to_dict()

                # Create tier summary table
                tier_table = Table(show_header=True, header_style="bold")
                tier_table.add_column("Tier", style="cyan")
                tier_table.add_column("Count", justify="right")
                tier_table.add_column("Action", style="yellow")

                for tier in ["MUST", "SHOULD", "COULD", "KEEP"]:
                    if tier in tier_counts:
                        action = self._get_tier_action(tier)
                        tier_table.add_row(tier, str(tier_counts[tier]), action)

                        # Update totals
                        if tier == "MUST":
                            total_must += tier_counts[tier]
                        elif tier == "SHOULD":
                            total_should += tier_counts[tier]
                        elif tier == "COULD":
                            total_could += tier_counts[tier]
                        elif tier == "KEEP":
                            total_keep += tier_counts[tier]

                service_branch.add(tier_table)

                # Add signal legend
                signal_legend = self._get_signal_legend(service)
                if signal_legend:
                    service_branch.add(f"[dim]{signal_legend}[/dim]")

                # Add service summary
                summary = self._get_service_summary(tier_counts, len(df))
                service_branch.add(f"[bold]{summary}[/bold]")

        # Display the tree
        self.console.print(tree)

        # Overall summary
        if has_data:
            self.console.print(
                f"\n📊 Total Decommission Candidates: {total_must} MUST + {total_should} SHOULD + {total_could} COULD + {total_keep} KEEP"
            )
        else:
            self.console.print(
                "\n[dim]ℹ️  No activity data available for analysis. Resources may be in unsupported regions or accounts.[/dim]"
            )

        # Track B v1.1.29 Feature #3: Top 3 Quick Actions for Executive Persona
        # Only render when persona is executive/ceo AND has activity data
        if self.persona in ["executive", "ceo"] and has_data:
            self._render_top_actions(enriched_data)

        # Track B v1.1.29 Feature #1: 3-Level Service Hierarchy for Architect/SRE personas
        # Only render when persona is architect/sre AND has_data
        if self.persona in ["architect", "sre"] and has_data:
            self._render_hierarchy_tree(enriched_data)

        return ""  # Console output, no string return

    def _get_service_label(self, service: str, count: int) -> str:
        """Get formatted service label for tree display."""
        icons = {
            "ec2": "💻",
            "ecs": "🐳",
            "s3": "☁️",
            "dynamodb": "⚡",
            "rds": "🗄️",
            "workspaces": "🖥️",
            "snapshots": "📸",
            "alb": "🌐",
            "nlb": "🌐",
            "route53": "🌍",
            "vpc": "🔗",
            "appstream": "🚀",
            "lambda": "⚡",
            "cloudwatch": "📊",
            "config": "⚙️",
            "cloudtrail": "🔍",
        }
        icon = icons.get(service, "📦")
        display_name = self._get_service_display_name(service)
        return f"{icon} {display_name} ({count} discovered)"

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

    def _get_tier_action(self, tier: str) -> str:
        """Get action description for tier."""
        actions = {
            "MUST": "🔴 Decommission immediately",
            "SHOULD": "🟡 Review and decommission",
            "COULD": "🟢 Consider optimization",
            "KEEP": "✅ Maintain active",
        }
        return actions.get(tier, "Unknown")

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

    def _get_service_summary(self, tier_counts: Dict[str, int], total: int) -> str:
        """Get formatted service summary."""
        must = tier_counts.get("MUST", 0)
        should = tier_counts.get("SHOULD", 0)
        could = tier_counts.get("COULD", 0)
        keep = tier_counts.get("KEEP", 0)
        return f"Summary: {must} MUST + {should} SHOULD + {could} COULD + {keep} KEEP = {total} total"

    def _render_top_actions(self, enriched_data: Dict[str, pd.DataFrame]) -> None:
        """
        Render Top 3 Quick Actions section for Executive persona.

        Business Value (Feature #3):
        - Executives need immediate visibility into top cost-saving opportunities
        - Prioritizes actions by annual savings potential
        - One-line recommendations for quick decision-making

        Args:
            enriched_data: Dictionary with service DataFrames containing activity signals

        Integration:
            Called by TreeExporter.export() when persona='executive'/'ceo' AND has_data=True
        """
        from runbooks.finops.persona_formatter import PersonaFormatter

        # Create formatter for current persona
        formatter = PersonaFormatter(persona=self.persona)

        # Generate top 3 actions from enriched data
        top_actions = formatter.generate_top_actions(enriched_data, top_n=3)

        # Render actions table (formatter handles persona check internally)
        if top_actions:
            formatter.render_top_actions_table(top_actions, console_instance=self.console)

    def _render_hierarchy_tree(self, enriched_data: Dict[str, pd.DataFrame]) -> None:
        """
        Render 3-level service hierarchy tree for Architect/SRE personas.

        Business Value (Feature #1):
        - Architect: 3-level hierarchy (Account → Service → Resource) for multi-account optimization
        - SRE: 2-level hierarchy (Service → Resource) for operational cost management
        - Provides cost distribution visibility across organizational structure

        Args:
            enriched_data: Dictionary with service DataFrames containing activity signals

        Integration:
            Called by TreeExporter.export() when persona='architect'/'sre' AND has_data=True
        """
        from runbooks.finops.persona_formatter import PersonaFormatter

        # Create formatter for current persona
        formatter = PersonaFormatter(persona=self.persona)

        # Render hierarchy tree (formatter handles hierarchy level logic)
        formatter.render_hierarchy_tree(enriched_data, console_instance=self.console)


class TableExporter(BaseExporter):
    """
    Export as flat table (console output).

    Track B v1.1.26: Added persona parameter for role-specific table rendering.
    """

    def __init__(
        self,
        console_instance: Optional[Console] = None,
        persona: Optional[PersonaType] = None,  # Track B v1.1.26
        **kwargs,
    ):
        super().__init__(title="Activity Health Summary")
        self.console = console_instance or Console()
        self.persona = persona  # Track B v1.1.26

    def get_format_name(self) -> str:
        """Return format identifier."""
        return "table"

    def export(self, enriched_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Render table to console, return empty string."""
        table_title = self.metadata.title or "Activity Health Summary"
        table = Table(title=table_title, show_header=True)

        # Add columns
        table.add_column("Service", style="cyan")
        table.add_column("Resources", justify="right")
        table.add_column("MUST", justify="right", style="red")
        table.add_column("SHOULD", justify="right", style="yellow")
        table.add_column("COULD", justify="right", style="green")
        table.add_column("KEEP", justify="right", style="blue")
        table.add_column("Cost Impact", justify="right", style="bold")

        total_resources = 0
        total_must = 0
        total_should = 0
        total_could = 0
        total_keep = 0
        total_cost = 0

        for service, df in enriched_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            total_resources += len(df)

            # Calculate tier counts
            tier_counts = {"MUST": 0, "SHOULD": 0, "COULD": 0, "KEEP": 0}
            if "decommission_tier" in df.columns:
                counts = df["decommission_tier"].value_counts().to_dict()
                tier_counts.update(counts)

            # Calculate cost impact
            cost_impact = 0
            if "monthly_cost" in df.columns:
                must_df = df[df["decommission_tier"] == "MUST"] if "decommission_tier" in df.columns else pd.DataFrame()
                should_df = (
                    df[df["decommission_tier"] == "SHOULD"] if "decommission_tier" in df.columns else pd.DataFrame()
                )
                if not must_df.empty:
                    cost_impact += must_df["monthly_cost"].sum()
                if not should_df.empty:
                    cost_impact += should_df["monthly_cost"].sum() * 0.7  # 70% likelihood for SHOULD

            total_must += tier_counts["MUST"]
            total_should += tier_counts["SHOULD"]
            total_could += tier_counts["COULD"]
            total_keep += tier_counts["KEEP"]
            total_cost += cost_impact

            # Add row
            table.add_row(
                service.upper(),
                str(len(df)),
                str(tier_counts["MUST"]),
                str(tier_counts["SHOULD"]),
                str(tier_counts["COULD"]),
                str(tier_counts["KEEP"]),
                format_cost(cost_impact) if cost_impact > 0 else "-",
            )

        # Add totals row
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total_resources}[/bold]",
            f"[bold red]{total_must}[/bold red]",
            f"[bold yellow]{total_should}[/bold yellow]",
            f"[bold green]{total_could}[/bold green]",
            f"[bold blue]{total_keep}[/bold blue]",
            f"[bold]{format_cost(total_cost)}[/bold]",
        )

        self.console.print(table)
        return ""  # Console output, no string return
