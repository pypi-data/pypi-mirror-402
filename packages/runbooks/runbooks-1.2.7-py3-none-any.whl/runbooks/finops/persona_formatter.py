#!/usr/bin/env python3
"""
PersonaFormatter - Executive Persona Formatting for FinOps Dashboards

Provides persona-specific data filtering and formatting for:
- CFO: Budget-focused with top 5 cost drivers
- CTO: Technical service breakdown with optimization signals
- CEO: Strategic KPIs with top 3 action items
- SRE: Anomaly detection with cost spike alerts
- Architect: Multi-account architecture patterns
- Technical: Full detailed data (default)
- Executive: Board-ready one-page summary

Manager Requirement: Persona-specific output customization for --mode parameter
Enterprise Pattern: KISS architecture (enhance existing, no new complexity)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

import pandas as pd

# Persona types matching CLI --mode options
PersonaType = Literal["cfo", "cto", "ceo", "sre", "architect", "technical", "executive"]


@dataclass
class PersonaConfig:
    """Configuration for persona-specific dashboard formatting."""

    persona: PersonaType
    primary_metric: str
    secondary_metrics: List[str]
    top_services: int | str  # int for limit, 'all' for unlimited
    summary_length: str
    focus_areas: List[str]
    exclude_zero_cost: bool = True
    include_recommendations: bool = False
    threshold_alerts: bool = False
    dependency_graph: bool = False
    action_items: Optional[int] = None

    # Gap 4: Validation transparency configuration (v1.1.29)
    validation_level: Literal["strict", "business", "operational"] = "business"
    confidence_threshold: float = 0.995  # 99.5% default for business mode
    mcp_required: bool = True
    fallback_behavior: Literal["fail", "warn", "continue"] = "warn"

    # Feature #2: Persona-specific default export formats (v1.1.30)
    default_exports: List[str] = field(default_factory=list)

    # Feature #1: Hierarchy display level for persona (v1.1.30)
    hierarchy_level: Literal["flat", "service", "account_service"] = "flat"


class PersonaFormatter:
    """
    Format dashboard data for executive personas.

    Implements persona-specific filtering, prioritization, and formatting
    to deliver role-appropriate insights from FinOps cost data.
    """

    # Class-level access to persona configurations for CLI integration
    PERSONA_CONFIGS: Dict[str, PersonaConfig] = {}  # Populated in _get_persona_config

    def __init__(self, persona: PersonaType = "technical"):
        """
        Initialize PersonaFormatter.

        Args:
            persona: Target persona type (defaults to 'technical' for backward compatibility)
        """
        self.persona = persona.lower()
        self.config = self._get_persona_config()

    def _get_persona_config(self) -> PersonaConfig:
        """
        Get configuration for current persona.

        Returns:
            PersonaConfig with persona-specific settings
        """
        configs = {
            "cfo": PersonaConfig(
                persona="cfo",
                primary_metric="monthly_budget_utilization_pct",
                secondary_metrics=["forecast_accuracy", "cost_trend_mom"],
                top_services=5,
                summary_length="executive",
                focus_areas=["budget_compliance", "cost_optimization"],
                exclude_zero_cost=True,
                include_recommendations=True,
                # Gap 4: CFO requires business-level validation (≥99.5%)
                validation_level="business",
                confidence_threshold=0.995,
                mcp_required=True,
                fallback_behavior="warn",
                # Feature #2: CFO prefers CSV+PDF for board presentations
                default_exports=["csv", "pdf"],
            ),
            "cto": PersonaConfig(
                persona="cto",
                primary_metric="service_cost_breakdown",
                secondary_metrics=["technical_debt_cost", "architecture_optimization"],
                top_services=15,
                summary_length="technical",
                focus_areas=["E1-E7_signals", "rightsizing_opportunities"],
                exclude_zero_cost=True,
                include_recommendations=True,
                # Gap 4: CTO requires business-level validation (≥99.5%)
                validation_level="business",
                confidence_threshold=0.995,
                mcp_required=True,
                fallback_behavior="warn",
                # Feature #2: CTO prefers CSV for data analysis
                default_exports=["csv"],
            ),
            "ceo": PersonaConfig(
                persona="ceo",
                primary_metric="total_cost_trend",
                secondary_metrics=["yoy_growth", "cloud_spend_as_pct_revenue"],
                top_services=3,
                summary_length="board_ready",
                focus_areas=["strategic_initiatives", "cost_trajectory"],
                exclude_zero_cost=True,
                action_items=3,
                # Gap 4: CEO requires strict validation (≥99.9%)
                validation_level="strict",
                confidence_threshold=0.999,
                mcp_required=True,
                fallback_behavior="warn",
                # Feature #2: CEO prefers PDF for board presentations
                default_exports=["pdf"],
            ),
            "sre": PersonaConfig(
                persona="sre",
                primary_metric="cost_anomaly_score",
                secondary_metrics=["spike_alerts", "resource_utilization"],
                top_services=20,
                summary_length="operational",
                focus_areas=["cost_spikes", "resource_waste"],
                exclude_zero_cost=False,
                threshold_alerts=True,
                # Gap 4: SRE accepts operational validation (≥95%)
                validation_level="operational",
                confidence_threshold=0.95,
                mcp_required=False,
                fallback_behavior="continue",
                # Feature #2: SRE prefers JSON for automation
                default_exports=["json"],
                # Feature #1: 2-level hierarchy (Service → Resource)
                hierarchy_level="service",
            ),
            "architect": PersonaConfig(
                persona="architect",
                primary_metric="multi_account_cost_distribution",
                secondary_metrics=["architecture_patterns", "cross_account_dependencies"],
                top_services="all",
                summary_length="architectural",
                focus_areas=["workload_patterns", "optimization_architecture"],
                exclude_zero_cost=True,
                dependency_graph=True,
                # Gap 4: Architect requires business-level validation (≥99.5%)
                validation_level="business",
                confidence_threshold=0.995,
                mcp_required=True,
                fallback_behavior="warn",
                # Feature #2: Architect prefers Markdown for documentation
                default_exports=["markdown"],
                # Feature #1: 3-level hierarchy (Account → Service → Resource)
                hierarchy_level="account_service",
            ),
            "technical": PersonaConfig(
                persona="technical",
                primary_metric="all_metrics",
                secondary_metrics=[],
                top_services="all",
                summary_length="detailed",
                focus_areas=["all_signals", "full_analysis"],
                exclude_zero_cost=False,
                # Gap 4: Technical mode accepts operational validation (≥95%)
                validation_level="operational",
                confidence_threshold=0.95,
                mcp_required=False,
                fallback_behavior="continue",
            ),
            "executive": PersonaConfig(
                persona="executive",
                primary_metric="total_cost_summary",
                secondary_metrics=["key_trends", "top_recommendations"],
                top_services=5,
                summary_length="board_ready",
                focus_areas=["executive_summary", "decision_points"],
                exclude_zero_cost=True,
                include_recommendations=True,
                action_items=5,
                # Gap 4: Executive requires strict validation (≥99.9%)
                validation_level="strict",
                confidence_threshold=0.999,
                mcp_required=True,
                fallback_behavior="warn",
                # Feature #2: Executive requires CSV+PDF for board presentations
                default_exports=["csv", "pdf"],
            ),
        }
        # Populate class-level PERSONA_CONFIGS for CLI access
        PersonaFormatter.PERSONA_CONFIGS = configs
        return configs.get(self.persona, configs["technical"])

    def filter_top_services(self, service_data: pd.DataFrame, cost_column: str = "current_cost") -> pd.DataFrame:
        """
        Filter services based on persona preferences.

        Args:
            service_data: DataFrame with service cost information
            cost_column: Column name containing cost values

        Returns:
            Filtered DataFrame with top N services per persona config
        """
        if self.config.top_services == "all":
            return service_data

        # Sort by cost descending
        sorted_data = service_data.sort_values(by=cost_column, ascending=False)

        # Filter top N
        top_n = int(self.config.top_services)
        return sorted_data.head(top_n)

    def format_summary(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format dashboard summary based on persona configuration.

        Args:
            dashboard_data: Raw dashboard data dictionary

        Returns:
            Persona-formatted summary dictionary
        """
        formatted = {
            "persona": self.persona,
            "summary_length": self.config.summary_length,
            "primary_metric": self.config.primary_metric,
            "focus_areas": self.config.focus_areas,
        }

        # Add persona-specific sections
        if self.config.include_recommendations:
            formatted["recommendations"] = self._generate_recommendations(dashboard_data)

        if self.config.action_items:
            formatted["action_items"] = self._extract_action_items(dashboard_data, self.config.action_items)

        if self.config.threshold_alerts:
            formatted["alerts"] = self._detect_threshold_alerts(dashboard_data)

        return formatted

    def _generate_recommendations(self, dashboard_data: Dict[str, Any]) -> List[str]:
        """
        Generate persona-specific recommendations.

        Args:
            dashboard_data: Raw dashboard data

        Returns:
            List of recommendations tailored to persona
        """
        recommendations = []

        if self.persona == "cfo":
            # Budget-focused recommendations
            recommendations.append("Review top 5 cost drivers for optimization opportunities")
            recommendations.append("Validate forecast accuracy against actual spend")

        elif self.persona == "cto":
            # Technical recommendations
            recommendations.append("Analyze E1-E7 signals for rightsizing candidates")
            recommendations.append("Review service architecture for optimization patterns")

        elif self.persona == "ceo":
            # Strategic recommendations
            recommendations.append("Monitor cost trajectory alignment with growth targets")
            recommendations.append("Review cloud spend as percentage of revenue")

        elif self.persona == "executive":
            # Executive-level recommendations
            recommendations.append("Review board-ready summary for strategic decisions")
            recommendations.append("Validate top recommendations with leadership team")

        return recommendations

    def _extract_action_items(self, dashboard_data: Dict[str, Any], max_items: int) -> List[str]:
        """
        Extract top N action items for persona.

        Args:
            dashboard_data: Raw dashboard data
            max_items: Maximum number of action items

        Returns:
            List of prioritized action items
        """
        action_items = []

        # Extract from dashboard data based on persona focus
        if "recommendations" in dashboard_data:
            action_items = dashboard_data["recommendations"][:max_items]
        else:
            # Default action items
            action_items = [
                f"Review {self.config.primary_metric} trends",
                f"Analyze top {self.config.top_services} services",
                "Validate optimization opportunities",
            ]

        return action_items[:max_items]

    def _detect_threshold_alerts(self, dashboard_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect cost threshold alerts for SRE persona.

        Args:
            dashboard_data: Raw dashboard data

        Returns:
            List of alert dictionaries with severity and details
        """
        alerts = []

        # Cost spike detection (20% threshold for SRE)
        if "cost_change_pct" in dashboard_data:
            change_pct = dashboard_data.get("cost_change_pct", 0)
            if abs(change_pct) > 20:
                alerts.append(
                    {
                        "severity": "high" if abs(change_pct) > 50 else "medium",
                        "type": "cost_spike",
                        "message": f"Cost change of {change_pct:.1f}% exceeds 20% threshold",
                    }
                )

        return alerts

    def generate_top_actions(self, dashboard_data: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Extract top N cost-saving actions from dashboard data.

        Business Value:
        - CEO/Executive personas need immediate visibility into top cost-saving opportunities
        - Prioritizes actions by annual savings potential (highest to lowest)
        - Provides confidence indicators for decision-making

        Args:
            dashboard_data: Complete dashboard data with activity analysis
            top_n: Number of top actions to return (default 3)

        Returns:
            List of dicts with: {
                'resource_type': 'EC2'|'WorkSpaces'|'S3'|'Snapshot'|'RDS',
                'resource_name': Resource identifier,
                'action': One-line action recommendation,
                'cost_impact_annual': Estimated annual savings (float),
                'signals': List of decommission signals detected,
                'confidence': 'HIGH'|'MEDIUM'|'LOW',
                'score': Decommission score (0-100)
            }

        Example:
            >>> formatter = PersonaFormatter('executive')
            >>> actions = formatter.generate_top_actions(dashboard_data, top_n=3)
            >>> print(actions[0])
            {
                'resource_type': 'S3',
                'resource_name': 'vamsnz-prod-atlassian-backups',
                'action': 'Archive to Deep Archive',
                'cost_impact_annual': 12208.10,
                'signals': ['S1:StorLens', 'S2:ClassIneff'],
                'confidence': 'HIGH',
                'score': 85
            }
        """
        actions = []

        # Extract EC2 decommission candidates (E1-E7 signals, SHOULD/MUST tiers)
        if "ec2" in dashboard_data:
            ec2_df = dashboard_data["ec2"]
            if isinstance(ec2_df, pd.DataFrame) and not ec2_df.empty:
                # Filter EC2 instances with decommission signals
                if "decommission_tier" in ec2_df.columns:
                    decom_ec2 = ec2_df[ec2_df["decommission_tier"].isin(["MUST", "SHOULD"])]
                    for _, row in decom_ec2.iterrows():
                        # Extract signals from columns (E1-E7 flags)
                        signals = [f"E{i}" for i in range(1, 8) if row.get(f"e{i}_signal", False)]

                        # Estimate annual cost from monthly_cost if available
                        monthly_cost = row.get("monthly_cost", 0)
                        annual_cost = monthly_cost * 12 if monthly_cost else 0

                        score = row.get("decommission_score", 0)
                        confidence = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"

                        actions.append(
                            {
                                "resource_type": "EC2",
                                "resource_name": row.get("instance_id", "Unknown"),
                                "action": "Terminate idle instance",
                                "cost_impact_annual": annual_cost,
                                "signals": signals,
                                "confidence": confidence,
                                "score": score,
                            }
                        )

        # Extract WorkSpaces decommission candidates (W1-W6 signals)
        if "workspaces" in dashboard_data:
            ws_df = dashboard_data["workspaces"]
            if isinstance(ws_df, pd.DataFrame) and not ws_df.empty:
                if "decommission_tier" in ws_df.columns:
                    decom_ws = ws_df[ws_df["decommission_tier"].isin(["MUST", "SHOULD"])]
                    for _, row in decom_ws.iterrows():
                        signals = [f"W{i}" for i in range(1, 7) if row.get(f"w{i}_signal", False)]

                        monthly_cost = row.get("monthly_cost", 0)
                        annual_cost = monthly_cost * 12 if monthly_cost else 0

                        score = row.get("decommission_score", 0)
                        confidence = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"

                        actions.append(
                            {
                                "resource_type": "WorkSpaces",
                                "resource_name": row.get("workspace_id", "Unknown"),
                                "action": "Terminate idle WorkSpace",
                                "cost_impact_annual": annual_cost,
                                "signals": signals,
                                "confidence": confidence,
                                "score": score,
                            }
                        )

        # Extract S3 optimization opportunities (S1-S7 signals)
        if "s3" in dashboard_data:
            s3_df = dashboard_data["s3"]
            if isinstance(s3_df, pd.DataFrame) and not s3_df.empty:
                # S3 uses optimization_strategy column
                if "optimization_strategy" in s3_df.columns:
                    opt_s3 = s3_df[s3_df["optimization_strategy"].notna()]
                    for _, row in opt_s3.iterrows():
                        signals = [f"S{i}" for i in range(1, 11) if row.get(f"s{i}_signal", False)]

                        # S3 typically has recommended_savings directly
                        annual_savings = row.get("recommended_savings", 0)

                        score = row.get("decommission_score", 0)
                        confidence = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"

                        strategy = row.get("optimization_strategy", "Unknown")
                        action_text = f"Archive to {strategy}" if strategy != "Unknown" else "Optimize storage"

                        actions.append(
                            {
                                "resource_type": "S3",
                                "resource_name": row.get("bucket_name", "Unknown"),
                                "action": action_text,
                                "cost_impact_annual": annual_savings,
                                "signals": signals,
                                "confidence": confidence,
                                "score": score,
                            }
                        )

        # Extract RDS decommission candidates (R1-R7 signals)
        if "rds" in dashboard_data:
            rds_df = dashboard_data["rds"]
            if isinstance(rds_df, pd.DataFrame) and not rds_df.empty:
                if "decommission_tier" in rds_df.columns:
                    decom_rds = rds_df[rds_df["decommission_tier"].isin(["MUST", "SHOULD"])]
                    for _, row in decom_rds.iterrows():
                        signals = [f"R{i}" for i in range(1, 8) if row.get(f"r{i}_signal", False)]

                        monthly_cost = row.get("monthly_cost", 0)
                        annual_cost = monthly_cost * 12 if monthly_cost else 0

                        score = row.get("decommission_score", 0)
                        confidence = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"

                        actions.append(
                            {
                                "resource_type": "RDS",
                                "resource_name": row.get("db_instance_id", "Unknown"),
                                "action": "Terminate idle database",
                                "cost_impact_annual": annual_cost,
                                "signals": signals,
                                "confidence": confidence,
                                "score": score,
                            }
                        )

        # Extract Snapshot cleanup opportunities (Snapshot age signals)
        if "snapshots" in dashboard_data:
            snap_df = dashboard_data["snapshots"]
            if isinstance(snap_df, pd.DataFrame) and not snap_df.empty:
                if "decommission_tier" in snap_df.columns:
                    decom_snap = snap_df[snap_df["decommission_tier"].isin(["MUST", "SHOULD"])]
                    for _, row in decom_snap.iterrows():
                        signals = [f"SN{i}" for i in range(1, 8) if row.get(f"sn{i}_signal", False)]

                        monthly_cost = row.get("monthly_cost", 0)
                        annual_cost = monthly_cost * 12 if monthly_cost else 0

                        score = row.get("decommission_score", 0)
                        confidence = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"

                        actions.append(
                            {
                                "resource_type": "Snapshot",
                                "resource_name": row.get("snapshot_id", "Unknown"),
                                "action": "Delete orphaned snapshot",
                                "cost_impact_annual": annual_cost,
                                "signals": signals,
                                "confidence": confidence,
                                "score": score,
                            }
                        )

        # Sort by cost impact (highest first) and return top N
        actions_sorted = sorted(actions, key=lambda x: x["cost_impact_annual"], reverse=True)
        return actions_sorted[:top_n]

    def get_display_config(self) -> Dict[str, Any]:
        """
        Get display configuration for Rich CLI rendering.

        Returns:
            Dictionary with display preferences for current persona
        """
        return {
            "persona": self.persona,
            "top_n": self.config.top_services,
            "show_zero_cost": not self.config.exclude_zero_cost,
            "summary_style": self.config.summary_length,
            "include_recommendations": self.config.include_recommendations,
            "threshold_alerts": self.config.threshold_alerts,
        }

    def format_title(self, base_title: str) -> str:
        """
        Format dashboard title with persona context.

        Args:
            base_title: Base dashboard title

        Returns:
            Persona-customized title
        """
        persona_labels = {
            "cfo": "CFO Financial Dashboard",
            "cto": "CTO Technical Dashboard",
            "ceo": "CEO Executive Dashboard",
            "sre": "SRE Operations Dashboard",
            "architect": "Cloud Architecture Dashboard",
            "technical": "Technical Cost Analysis",
            "executive": "Executive Summary Dashboard",
        }
        return persona_labels.get(self.persona, base_title)

    def render_top_actions_table(self, actions: List[Dict[str, Any]], console_instance: Optional[Any] = None) -> None:
        """
        Render Top 3 Quick Actions section as Rich table.

        Executive persona feature - displays top cost-saving actions
        with one-line recommendations for quick decision-making.

        Args:
            actions: List of action dictionaries from generate_top_actions()
            console_instance: Rich Console instance (optional, uses global console if None)

        Example:
            >>> from rich.console import Console
            >>> formatter = PersonaFormatter('executive')
            >>> actions = formatter.generate_top_actions(dashboard_data, top_n=3)
            >>> formatter.render_top_actions_table(actions, Console())
        """
        from rich.table import Table
        from rich.console import Console

        if not actions:
            return

        console = console_instance or Console()

        # Only render for executive/CEO personas
        if self.persona not in ["executive", "ceo"]:
            return

        console.print("\n[bold cyan]🎯 Top 3 Quick Actions[/bold cyan]\n")

        table = Table(show_header=True, header_style="bold magenta", expand=False, box=None)
        table.add_column("Action", style="cyan", width=40)
        table.add_column("Resource", style="white", width=27)
        table.add_column("Annual Savings", justify="right", style="green", width=16)
        table.add_column("Confidence", justify="center", style="yellow", width=12)

        for i, action in enumerate(actions, 1):
            # Confidence icon
            confidence = action.get("confidence", "MEDIUM")
            confidence_icon = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"

            # Format savings
            savings = action.get("cost_impact_annual", 0)
            savings_formatted = f"${savings:,.2f}/yr"

            # Truncate resource name if too long
            resource_name = action.get("resource_name", "Unknown")
            resource_display = resource_name[:25] if len(resource_name) > 25 else resource_name

            # Add row
            table.add_row(
                f"{i}. {action.get('action', 'Unknown action')}",
                resource_display,
                savings_formatted,
                f"{confidence_icon} {confidence}",
            )

        console.print(table)

        # Show total potential savings
        total_savings = sum(a.get("cost_impact_annual", 0) for a in actions)
        console.print(f"\n[bold green]💰 Total Potential Savings: ${total_savings:,.2f}/year[/bold green]\n")

    def render_hierarchy_tree(self, dashboard_data: Dict[str, Any], console_instance: Optional[Any] = None) -> None:
        """
        Render resource hierarchy tree based on persona configuration.

        Feature #1 (v1.1.30): 3-Level Service Hierarchy for Architect/SRE personas

        Business Value:
        - Architect: 3-level view (Account → Service → Resource) for multi-account optimization
        - SRE: 2-level view (Service → Resource) for operational cost management
        - Executive: Flat view with Top 3 Actions (default behavior)

        Args:
            dashboard_data: Complete dashboard data with activity analysis
            console_instance: Optional Rich Console instance

        Rendering Logic:
            - hierarchy_level="account_service": Account → Service → Resource Type → Tier
            - hierarchy_level="service": Service → Resource Type → Tier
            - hierarchy_level="flat": No tree (default flat rendering)

        Requirements:
            - Only renders if activity_analysis=True (decommission_tier required)
            - Falls back to flat rendering if no activity data
            - Uses Rich Tree widget for visual hierarchy

        Example:
            >>> formatter = PersonaFormatter('architect')
            >>> formatter.render_hierarchy_tree(dashboard_data, console)
        """
        from rich.console import Console
        from rich.tree import Tree
        from rich.table import Table as RichTable

        console = console_instance or Console()

        # Only render for architect/sre personas with hierarchy enabled
        if self.config.hierarchy_level == "flat":
            return

        # Check if we have activity data
        has_activity_data = any(
            isinstance(dashboard_data.get(svc), pd.DataFrame)
            and not dashboard_data[svc].empty
            and "decommission_tier" in dashboard_data[svc].columns
            for svc in ["ec2", "s3", "workspaces", "rds", "snapshots", "dynamodb", "vpc", "route53"]
        )

        if not has_activity_data:
            # Debug: Show what data keys we actually have
            available_keys = [
                k
                for k in dashboard_data.keys()
                if isinstance(dashboard_data.get(k), pd.DataFrame) and not dashboard_data[k].empty
            ]
            console.print(
                f"\n[dim]ℹ️  Hierarchy view requires --activity-analysis flag (available: {', '.join(available_keys)})[/dim]"
            )
            return

        # Render based on hierarchy level
        if self.config.hierarchy_level == "account_service":
            self._render_account_service_hierarchy(dashboard_data, console)
        elif self.config.hierarchy_level == "service":
            self._render_service_hierarchy(dashboard_data, console)

    def _render_account_service_hierarchy(self, dashboard_data: Dict[str, Any], console: Any) -> None:
        """
        Render 3-level hierarchy: Account → Service → Resource Type → Tier.

        Architect persona feature - shows multi-account cost organization.
        """
        from rich.tree import Tree
        from rich.table import Table as RichTable

        console.print("\n[bold cyan]📊 Multi-Account Service Hierarchy (Architect View)[/bold cyan]\n")

        # Group resources by account
        accounts = self._group_by_account(dashboard_data)

        for account_id, account_data in accounts.items():
            # Create account-level tree
            account_label = f"[bold]Account: {account_id}[/bold]"
            account_tree = Tree(account_label)

            # Group by service within account
            services = self._group_by_service(account_data)

            for service_name, service_data in services.items():
                service_cost = sum(r.get("monthly_cost", 0) for r in service_data["resources"])
                service_branch = account_tree.add(f"[cyan]{service_name}[/cyan]")

                # Group by resource type
                resource_types = self._group_by_resource_type(service_data["resources"])

                for resource_type, resources in resource_types.items():
                    type_cost = sum(r.get("monthly_cost", 0) for r in resources)
                    type_count = len(resources)
                    type_branch = service_branch.add(f"{resource_type} ({type_count}) - ${type_cost:,.2f}/mo")

                    # Group by decommission tier
                    tiers = self._group_by_tier(resources)

                    for tier, tier_resources in tiers.items():
                        tier_count = len(tier_resources)
                        tier_cost = sum(r.get("monthly_cost", 0) for r in tier_resources)
                        tier_icon = {"KEEP": "🟢", "SHOULD": "🟡", "MUST": "🔴", "COULD": "🟠"}.get(tier, "⚪")

                        # Get common signals for this tier
                        common_signals = self._get_common_signals(tier_resources)
                        signal_text = f" ({', '.join(common_signals[:3])})" if common_signals else ""

                        type_branch.add(
                            f"{tier_icon} {tier}: {tier_count} {resource_type.lower()} - "
                            f"${tier_cost:,.2f}/mo{signal_text}"
                        )

            console.print(account_tree)

        # Calculate total potential savings
        total_cost, potential_savings = self._calculate_total_savings(dashboard_data)
        console.print(
            f"\n[bold]💰 Total Across Accounts: ${total_cost:,.2f}/mo | "
            f"🎯 Potential Savings: ${potential_savings:,.2f}/yr[/bold]\n"
        )

    def _render_service_hierarchy(self, dashboard_data: Dict[str, Any], console: Any) -> None:
        """
        Render 2-level hierarchy: Service → Resource Type → Tier.

        SRE persona feature - shows operational cost breakdown.
        """
        from rich.tree import Tree

        console.print("\n[bold cyan]📊 Service Hierarchy (SRE View)[/bold cyan]\n")

        # Group all resources by service
        services = self._group_by_service(dashboard_data)

        for service_name, service_data in services.items():
            service_cost = sum(r.get("monthly_cost", 0) for r in service_data["resources"])
            service_tree = Tree(f"[bold cyan]{service_name}[/bold cyan] - ${service_cost:,.2f}/mo")

            # Group by resource type
            resource_types = self._group_by_resource_type(service_data["resources"])

            for resource_type, resources in resource_types.items():
                type_cost = sum(r.get("monthly_cost", 0) for r in resources)
                type_count = len(resources)
                type_branch = service_tree.add(f"{resource_type} ({type_count}) - ${type_cost:,.2f}/mo")

                # Group by decommission tier
                tiers = self._group_by_tier(resources)

                for tier, tier_resources in tiers.items():
                    tier_count = len(tier_resources)
                    tier_cost = sum(r.get("monthly_cost", 0) for r in tier_resources)
                    tier_icon = {"KEEP": "🟢", "SHOULD": "🟡", "MUST": "🔴", "COULD": "🟠"}.get(tier, "⚪")

                    # Get common signals
                    common_signals = self._get_common_signals(tier_resources)
                    signal_text = f" ({', '.join(common_signals[:3])})" if common_signals else ""

                    type_branch.add(f"{tier_icon} {tier}: {tier_count} resources - ${tier_cost:,.2f}/mo{signal_text}")

            console.print(service_tree)

        # Calculate total potential savings
        total_cost, potential_savings = self._calculate_total_savings(dashboard_data)
        console.print(
            f"\n[bold]💰 Total Cost: ${total_cost:,.2f}/mo | "
            f"🎯 Potential Savings: ${potential_savings:,.2f}/yr[/bold]\n"
        )

    def _group_by_account(self, data: Dict[str, Any]) -> Dict[str, Dict]:
        """Group resources by AWS account ID."""
        accounts = {}

        for service_key, df in data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            # Extract account from resource metadata
            for _, row in df.iterrows():
                # Try to get account_id from row
                account_id = row.get("account_id", "Unknown")
                if account_id == "Unknown" and "arn" in row:
                    # Extract from ARN if available
                    arn = row.get("arn", "")
                    if arn and isinstance(arn, str):
                        parts = arn.split(":")
                        if len(parts) > 4:
                            account_id = parts[4]

                if account_id not in accounts:
                    accounts[account_id] = {}

                # Convert row to dict for storage
                resource_dict = row.to_dict()
                resource_dict["service"] = service_key

                if service_key not in accounts[account_id]:
                    accounts[account_id][service_key] = []

                accounts[account_id][service_key].append(resource_dict)

        return accounts

    def _group_by_service(self, data: Dict[str, Any]) -> Dict[str, Dict]:
        """Group resources by AWS service (EC2, S3, RDS, etc)."""
        services = {}

        # Handle both full dashboard_data and account-specific data
        for service_key, content in data.items():
            if isinstance(content, pd.DataFrame) and not content.empty:
                # Full dashboard format
                service_name = self._get_service_display_name(service_key)
                if service_name not in services:
                    services[service_name] = {"resources": []}

                for _, row in content.iterrows():
                    resource_dict = row.to_dict()
                    resource_dict["service_key"] = service_key
                    services[service_name]["resources"].append(resource_dict)

            elif isinstance(content, list):
                # Account-specific format (list of resources)
                service_name = self._get_service_display_name(service_key)
                if service_name not in services:
                    services[service_name] = {"resources": []}
                services[service_name]["resources"].extend(content)

        return services

    def _group_by_resource_type(self, resources: List[Dict]) -> Dict[str, List]:
        """Group resources by type (Instances, Snapshots, Buckets)."""
        types = {}

        for resource in resources:
            # Determine resource type
            service_key = resource.get("service_key", resource.get("service", ""))

            if service_key == "ec2":
                resource_type = "Instances"
            elif service_key == "s3":
                resource_type = "Buckets"
            elif service_key == "workspaces":
                resource_type = "WorkSpaces"
            elif service_key == "rds":
                resource_type = "Databases"
            elif service_key == "snapshots":
                resource_type = "Snapshots"
            else:
                resource_type = service_key.upper()

            if resource_type not in types:
                types[resource_type] = []

            types[resource_type].append(resource)

        return types

    def _group_by_tier(self, resources: List[Dict]) -> Dict[str, List]:
        """Group resources by decommission tier (KEEP, SHOULD, MUST, COULD)."""
        tiers = {"KEEP": [], "SHOULD": [], "MUST": [], "COULD": []}

        for resource in resources:
            tier = resource.get("decommission_tier", "KEEP")
            if tier in tiers:
                tiers[tier].append(resource)
            else:
                tiers["KEEP"].append(resource)

        # Filter empty tiers
        return {k: v for k, v in tiers.items() if v}

    def _get_common_signals(self, resources: List[Dict]) -> List[str]:
        """Extract common decommission signals across resources."""
        from collections import Counter

        all_signals = []

        for resource in resources:
            # Try different signal field formats
            signals = resource.get("signals_detected", [])

            # If signals_detected is not present, try extracting from signal flags
            if not signals:
                for key, value in resource.items():
                    if key.startswith(("e", "w", "s", "r", "l")) and key.endswith("_signal") and value:
                        # Extract signal code (e.g., 'e1_signal' → 'E1')
                        signal_code = key.split("_")[0].upper()
                        all_signals.append(signal_code)
            else:
                all_signals.extend(signals)

        # Return top 3 most common signals
        if all_signals:
            return [s for s, _ in Counter(all_signals).most_common(3)]
        return []

    def _get_service_display_name(self, service_key: str) -> str:
        """Get human-readable service name."""
        display_names = {
            "ec2": "EC2",
            "s3": "S3",
            "workspaces": "WorkSpaces",
            "rds": "RDS",
            "snapshots": "Snapshots",
            "dynamodb": "DynamoDB",
            "lambda": "Lambda",
            "ecs": "ECS",
            "vpc": "VPC",
        }
        return display_names.get(service_key, service_key.upper())

    def _calculate_total_savings(self, dashboard_data: Dict[str, Any]) -> tuple[float, float]:
        """Calculate total monthly cost and annual savings potential."""
        total_cost = 0
        must_cost = 0
        should_cost = 0

        for service_key, df in dashboard_data.items():
            if not isinstance(df, pd.DataFrame) or df.empty:
                continue

            if "monthly_cost" in df.columns:
                total_cost += df["monthly_cost"].sum()

            if "decommission_tier" in df.columns:
                must_df = df[df["decommission_tier"] == "MUST"]
                should_df = df[df["decommission_tier"] == "SHOULD"]

                if "monthly_cost" in df.columns:
                    must_cost += must_df["monthly_cost"].sum() if not must_df.empty else 0
                    should_cost += should_df["monthly_cost"].sum() if not should_df.empty else 0

        # Conservative savings: 100% MUST + 50% SHOULD
        monthly_savings = must_cost + (should_cost * 0.5)
        annual_savings = monthly_savings * 12

        return total_cost, annual_savings


def create_persona_formatter(mode: str) -> PersonaFormatter:
    """
    Factory function to create PersonaFormatter from CLI mode.

    Args:
        mode: CLI mode parameter value

    Returns:
        PersonaFormatter instance configured for specified mode
    """
    # Map CLI mode values to persona types
    mode_mapping = {
        "executive": "executive",
        "architect": "architect",
        "sre": "sre",
        "cfo": "cfo",
        "cto": "cto",
        "ceo": "ceo",
        "technical": "technical",
    }

    persona = mode_mapping.get(mode.lower(), "technical")
    return PersonaFormatter(persona)


# ========== v1.1.31: Simplified 3-Persona CLI Config ==========


@dataclass
class CLIPersonaConfig:
    """
    Simplified CLI persona configuration for v1.1.31.

    Maps the 3 CLI modes (executive|architect|sre) to optimal defaults
    following KISS/DRY/LEAN principles.
    """

    name: str  # CLI mode name
    top_n: int  # Default top N services
    validation_level: str  # strict (99.9%), mcp (99.5%), operational (95%)
    signal_display: str  # collapsed, full, full+score
    default_exports: List[str]  # Default export formats


# Pre-defined CLI persona configs (v1.1.31 user decisions)
CLI_PERSONA_CONFIGS: Dict[str, CLIPersonaConfig] = {
    "executive": CLIPersonaConfig(
        name="executive",
        top_n=5,
        validation_level="strict",  # 99.9% accuracy
        signal_display="collapsed",  # E1-E7, W1-W6, S1-S7 in collapsed summary
        default_exports=["csv", "pdf", "html"],
    ),
    "architect": CLIPersonaConfig(
        name="architect",
        top_n=20,
        validation_level="mcp",  # 99.5% accuracy
        signal_display="full",  # Full E1-E7, W1-W6, S1-S7 signals
        default_exports=["html", "markdown", "json"],
    ),
    "sre": CLIPersonaConfig(
        name="sre",
        top_n=20,
        validation_level="mcp",  # 99.5% accuracy
        signal_display="full+score",  # Full signals + decommission score + tier
        default_exports=["json", "csv"],
    ),
}


def get_cli_persona_config(mode: str) -> CLIPersonaConfig:
    """
    Get CLI persona configuration for simplified 3-mode CLI.

    Args:
        mode: CLI --mode value (executive, architect, sre)

    Returns:
        CLIPersonaConfig with optimal defaults for the mode

    Example:
        >>> config = get_cli_persona_config("executive")
        >>> print(config.top_n)  # 5
        >>> print(config.validation_level)  # strict
    """
    return CLI_PERSONA_CONFIGS.get(mode.lower(), CLI_PERSONA_CONFIGS["architect"])


def map_deprecated_persona_to_mode(persona: str) -> str:
    """
    Map deprecated --persona parameter to new --mode parameter.

    Args:
        persona: Deprecated --persona value (CFO, CTO, CEO, ALL)

    Returns:
        Equivalent --mode value (executive, architect, sre)

    Warning:
        This function is for backward compatibility only.
        --persona is deprecated in v1.1.31 and will be removed in v1.2.0.
    """
    mapping = {
        "CFO": "executive",  # CFO wants board-ready summary
        "CTO": "architect",  # CTO wants technical architecture view
        "CEO": "executive",  # CEO wants strategic summary
        "ALL": "architect",  # ALL maps to full architect view
    }
    return mapping.get(persona.upper(), "architect")
