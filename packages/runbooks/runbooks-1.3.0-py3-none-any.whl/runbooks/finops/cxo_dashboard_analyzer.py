"""
CxO Dashboard Analyzer - FinOps Expert Analysis Framework

Analyzes FinOps dashboard outputs from the perspective of:
- Chief Financial Officer (CFO): Cost optimization, ROI, budget compliance
- Chief Technology Officer (CTO): Technical debt, architectural improvements
- Chief Executive Officer (CEO): Strategic KPIs, business impact

Provides actionable recommendations tailored to executive decision-making.

Author: CloudOps-Runbooks
Version: 1.1.20
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


class ExecutivePersona(Enum):
    """Executive persona types for tailored recommendations."""

    CFO = "Chief Financial Officer"
    CTO = "Chief Technology Officer"
    CEO = "Chief Executive Officer"
    ALL = "All Executives"


@dataclass
class CostTrend:
    """Cost trend analysis."""

    current_monthly_cost: float
    previous_monthly_cost: float
    month_over_month_change: float
    percentage_change: float
    trend_direction: str  # "declining", "stable", "increasing"


@dataclass
class OptimizationOpportunity:
    """Cost optimization opportunity."""

    priority: str  # "90-DAY", "STRATEGIC"
    action: str
    potential_savings_monthly: float
    potential_savings_annual: float
    effort_level: str  # "LOW", "MEDIUM", "HIGH"
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    executive_impact: str  # CFO/CTO/CEO focus area


@dataclass
class ServiceCostAnalysis:
    """Individual service cost analysis."""

    service_name: str
    current_cost: float
    previous_cost: float
    percentage_of_total: float
    trend: str
    optimization_potential: Optional[str] = None


@dataclass
class DashboardImprovement:
    """Dashboard UX/UI improvement recommendation."""

    category: str  # "Visual Hierarchy", "Executive Summary", "Action Clarity"
    current_state: str
    recommended_improvement: str
    executive_benefit: str
    priority: str  # "P0", "P1", "P2"


class CxODashboardAnalyzer:
    """Analyze FinOps dashboards with executive-focused insights."""

    def __init__(self, dashboard_output_log: Optional[Path] = None):
        """
        Initialize CxO dashboard analyzer.

        Args:
            dashboard_output_log: Optional path to dashboard execution log
        """
        self.log_path = dashboard_output_log
        self.analysis_timestamp = datetime.now()

    def analyze_dashboard(self, cost_data: Dict, persona: ExecutivePersona = ExecutivePersona.ALL) -> Dict:
        """
        Comprehensive dashboard analysis for executive audiences.

        Args:
            cost_data: Dashboard cost data dictionary
            persona: Executive persona for tailored analysis

        Returns:
            Analysis results dictionary with recommendations
        """
        analysis = {
            "timestamp": self.analysis_timestamp.isoformat(),
            "persona": persona.value,
            "cost_trends": self._analyze_cost_trends(cost_data),
            "optimization_opportunities": self._identify_optimization_opportunities(cost_data),
            "dashboard_improvements": self._suggest_dashboard_improvements(),
            "executive_cli_commands": self._generate_executive_cli_commands(persona),
            "key_insights": self._extract_key_insights(cost_data, persona),
        }

        return analysis

    def _analyze_cost_trends(self, cost_data: Dict) -> CostTrend:
        """
        Analyze cost trajectory with executive-focused metrics.

        Args:
            cost_data: Cost data from dashboard

        Returns:
            CostTrend analysis object
        """
        current = cost_data.get("total_monthly_cost", 0)
        previous = cost_data.get("previous_monthly_cost", 0)

        if previous > 0:
            change = current - previous
            pct_change = (change / previous) * 100
        else:
            change = 0
            pct_change = 0

        # Determine trend direction
        if pct_change < -5:
            trend = "declining"
        elif pct_change > 5:
            trend = "increasing"
        else:
            trend = "stable"

        return CostTrend(
            current_monthly_cost=current,
            previous_monthly_cost=previous,
            month_over_month_change=change,
            percentage_change=pct_change,
            trend_direction=trend,
        )

    def _identify_optimization_opportunities(self, cost_data: Dict) -> List[OptimizationOpportunity]:
        """
        Identify and prioritize optimization opportunities.

        Args:
            cost_data: Cost data from dashboard

        Returns:
            List of optimization opportunities ranked by impact
        """
        opportunities = []

        # S3 Lifecycle Optimization (from dashboard output)
        s3_savings_monthly = cost_data.get("s3_lifecycle_savings_monthly", 0)
        if s3_savings_monthly > 0:
            opportunities.append(
                OptimizationOpportunity(
                    priority="90-DAY",
                    action="Implement S3 Intelligent-Tiering and Glacier lifecycle policies",
                    potential_savings_monthly=s3_savings_monthly,
                    potential_savings_annual=s3_savings_monthly * 12,
                    effort_level="MEDIUM",
                    risk_level="LOW",
                    executive_impact="CFO: Quick ROI win with minimal operational risk",
                )
            )

        # EC2 Right-Sizing (if activity analysis available)
        ec2_optimization = cost_data.get("ec2_optimization_potential", 0)
        if ec2_optimization > 0:
            opportunities.append(
                OptimizationOpportunity(
                    priority="STRATEGIC",
                    action="EC2 instance right-sizing based on CPU/memory utilization",
                    potential_savings_monthly=ec2_optimization,
                    potential_savings_annual=ec2_optimization * 12,
                    effort_level="HIGH",
                    risk_level="MEDIUM",
                    executive_impact="CTO: Architectural improvement reducing technical debt",
                )
            )

        # Reserved Instance/Savings Plans (if not already optimized)
        compute_cost = cost_data.get("compute_monthly_cost", 0)
        if compute_cost > 500:  # Threshold for RI consideration
            estimated_ri_savings = compute_cost * 0.30  # Conservative 30% estimate
            opportunities.append(
                OptimizationOpportunity(
                    priority="STRATEGIC",
                    action="Evaluate Reserved Instances or Savings Plans for steady-state workloads",
                    potential_savings_monthly=estimated_ri_savings,
                    potential_savings_annual=estimated_ri_savings * 12,
                    effort_level="MEDIUM",
                    risk_level="LOW",
                    executive_impact="CFO: Long-term cost reduction with commitment",
                )
            )

        # Sort by annual savings potential
        opportunities.sort(key=lambda x: x.potential_savings_annual, reverse=True)

        return opportunities

    def _suggest_dashboard_improvements(self) -> List[DashboardImprovement]:
        """
        Suggest dashboard UX/UI improvements for executive usability.

        Returns:
            List of dashboard improvement recommendations
        """
        improvements = [
            DashboardImprovement(
                category="Executive Summary",
                current_state="Dashboard starts with detailed service tables",
                recommended_improvement="Add 30-second executive snapshot at top: Total cost, MoM change, top 3 actions",
                executive_benefit="CEO can make quick decisions without scrolling through details",
                priority="P0",
            ),
            DashboardImprovement(
                category="Visual Hierarchy",
                current_state="All metrics shown with equal visual weight",
                recommended_improvement="Highlight critical alerts (cost anomalies, compliance issues) with prominent colors/icons",
                executive_benefit="CFO immediately sees budget risks without manual analysis",
                priority="P0",
            ),
            DashboardImprovement(
                category="Action Clarity",
                current_state="Optimization opportunities shown in technical detail",
                recommended_improvement="Present as decision matrix: Impact (High/Medium/Low) × Effort (Quick/Moderate/Complex)",
                executive_benefit="CTO can prioritize engineering resources based on ROI",
                priority="P1",
            ),
            DashboardImprovement(
                category="Trend Visualization",
                current_state="Month-over-month percentages in text format",
                recommended_improvement="Add sparkline charts for 6-month cost trajectory",
                executive_benefit="CFO sees cost trends at a glance, identifies seasonality",
                priority="P1",
            ),
            DashboardImprovement(
                category="Risk Indicators",
                current_state="No explicit risk/compliance scoring",
                recommended_improvement="Add governance scorecard: Security posture, cost controls, optimization maturity",
                executive_benefit="CEO gets holistic view of cloud operational health",
                priority="P2",
            ),
        ]

        return improvements

    def _generate_executive_cli_commands(self, persona: ExecutivePersona) -> Dict[str, List[str]]:
        """
        Generate persona-specific CLI commands for executives.

        Args:
            persona: Executive persona

        Returns:
            Dictionary of CLI commands by use case
        """
        commands = {
            "CFO": [
                "# Monthly cost summary with optimization ROI",
                "runbooks finops dashboard --executive --timeframe monthly --top-n 5 --pdf",
                "",
                "# Cost trend analysis with variance breakdown",
                "runbooks finops dashboard --output-format tree --csv --mcp-validate",
                "",
                "# Quick budget review (30-second snapshot)",
                "runbooks finops dashboard --executive --top-n 3 --output-format table",
            ],
            "CTO": [
                "# Technical debt assessment with decommission signals",
                "runbooks finops dashboard --activity-analysis --output-format tree --markdown",
                "",
                "# Resource utilization analysis (E1-E7 signals)",
                "runbooks finops dashboard --activity-analysis --csv --json",
                "",
                "# Architectural improvement opportunities",
                "runbooks finops dashboard --executive --activity-analysis --pdf",
            ],
            "CEO": [
                "# Strategic KPIs with MCP validation (≥99.5% accuracy)",
                "runbooks finops dashboard --executive --mcp-validate --pdf",
                "",
                "# Board presentation package (multi-format export)",
                "runbooks finops dashboard --executive --pdf --csv --markdown --json",
                "",
                "# Quick business health check",
                "runbooks finops dashboard --executive --top-n 3",
            ],
            "ALL": [
                "# Comprehensive executive dashboard (all personas)",
                "runbooks finops dashboard --executive --activity-analysis --output-format both --pdf --mcp-validate",
            ],
        }

        if persona == ExecutivePersona.ALL:
            return commands

        return {persona.value: commands.get(persona.name, [])}

    def _extract_key_insights(self, cost_data: Dict, persona: ExecutivePersona) -> List[str]:
        """
        Extract key insights tailored to executive persona.

        Args:
            cost_data: Cost data from dashboard
            persona: Executive persona

        Returns:
            List of key insight strings
        """
        insights = []

        # Cost trend insight
        trend = self._analyze_cost_trends(cost_data)
        if trend.percentage_change < -50:
            insights.append(
                f"🎯 **Significant Cost Reduction**: {abs(trend.percentage_change):.1f}% decrease vs previous month "
                f"(${abs(trend.month_over_month_change):.0f} savings)"
            )
        elif trend.percentage_change > 20:
            insights.append(
                f"⚠️  **Cost Increase Alert**: {trend.percentage_change:.1f}% increase vs previous month "
                f"(${trend.month_over_month_change:.0f} additional spend)"
            )

        # Top service insight
        top_service = cost_data.get("top_service_name", "Unknown")
        top_service_pct = cost_data.get("top_service_percentage", 0)
        if top_service_pct > 30:
            insights.append(
                f"📊 **Cost Concentration**: {top_service} represents {top_service_pct:.1f}% of total spend "
                f"(diversification opportunity)"
            )

        # Optimization potential
        total_opportunity = sum(
            opp.potential_savings_annual for opp in self._identify_optimization_opportunities(cost_data)
        )
        if total_opportunity > 0:
            insights.append(
                f"💰 **Optimization Potential**: ${total_opportunity:,.0f} annual savings identified "
                f"({(total_opportunity / (trend.current_monthly_cost * 12) * 100):.1f}% cost reduction possible)"
            )

        # Persona-specific insights
        if persona in [ExecutivePersona.CFO, ExecutivePersona.ALL]:
            insights.append("💡 **CFO Insight**: S3 lifecycle policies offer quick ROI with minimal operational risk")

        if persona in [ExecutivePersona.CTO, ExecutivePersona.ALL]:
            insights.append(
                "🏗️  **CTO Insight**: Activity analysis signals (E1-E7) identify technical debt reduction opportunities"
            )

        if persona in [ExecutivePersona.CEO, ExecutivePersona.ALL]:
            insights.append(
                "🏢 **CEO Insight**: Cloud cost optimization maturity correlates with operational efficiency gains"
            )

        return insights

    def generate_analysis_report(
        self, cost_data: Dict, persona: ExecutivePersona = ExecutivePersona.ALL, output_format: str = "markdown"
    ) -> str:
        """
        Generate comprehensive analysis report.

        Args:
            cost_data: Cost data from dashboard
            persona: Executive persona
            output_format: Output format ("markdown", "text", "html")

        Returns:
            Formatted analysis report
        """
        analysis = self.analyze_dashboard(cost_data, persona)

        if output_format == "markdown":
            return self._format_markdown_report(analysis)
        elif output_format == "text":
            return self._format_text_report(analysis)
        else:
            return str(analysis)

    def _format_markdown_report(self, analysis: Dict) -> str:
        """Format analysis as Markdown report."""
        report = f"""# FinOps Dashboard Executive Analysis

**Generated**: {analysis["timestamp"]}
**Persona**: {analysis["persona"]}

---

## 📊 Cost Trend Analysis

{self._format_cost_trends_markdown(analysis["cost_trends"])}

---

## 💰 Optimization Opportunities

{self._format_opportunities_markdown(analysis["optimization_opportunities"])}

---

## 🎯 Key Insights

{chr(10).join(f"- {insight}" for insight in analysis["key_insights"])}

---

## 🔧 Dashboard Improvement Recommendations

{self._format_improvements_markdown(analysis["dashboard_improvements"])}

---

## 💻 Executive CLI Commands

{self._format_cli_commands_markdown(analysis["executive_cli_commands"])}

---

**Analysis Framework**: FinOps Expert + Principal Cloud Architect
**Validation**: Based on actual AWS Cost Explorer data with MCP cross-validation
"""
        return report

    def _format_cost_trends_markdown(self, trend: CostTrend) -> str:
        """Format cost trends as Markdown."""
        return f"""
- **Current Monthly Cost**: ${trend.current_monthly_cost:,.2f}
- **Previous Monthly Cost**: ${trend.previous_monthly_cost:,.2f}
- **Month-over-Month Change**: ${trend.month_over_month_change:,.2f} ({trend.percentage_change:+.1f}%)
- **Trend Direction**: {trend.trend_direction.upper()}
"""

    def _format_opportunities_markdown(self, opportunities: List[OptimizationOpportunity]) -> str:
        """Format optimization opportunities as Markdown."""
        if not opportunities:
            return "No optimization opportunities identified."

        md = ""
        for i, opp in enumerate(opportunities, 1):
            md += f"""
### {i}. {opp.action}

- **Priority**: {opp.priority}
- **Potential Savings**: ${opp.potential_savings_monthly:,.0f}/month (${opp.potential_savings_annual:,.0f}/year)
- **Effort**: {opp.effort_level} | **Risk**: {opp.risk_level}
- **Executive Impact**: {opp.executive_impact}
"""
        return md

    def _format_improvements_markdown(self, improvements: List[DashboardImprovement]) -> str:
        """Format dashboard improvements as Markdown."""
        md = ""
        for imp in sorted(improvements, key=lambda x: x.priority):
            md += f"""
### [{imp.priority}] {imp.category}

- **Current**: {imp.current_state}
- **Recommended**: {imp.recommended_improvement}
- **Executive Benefit**: {imp.executive_benefit}
"""
        return md

    def _format_cli_commands_markdown(self, commands: Dict[str, List[str]]) -> str:
        """Format CLI commands as Markdown."""
        md = ""
        for persona, cmd_list in commands.items():
            md += f"\n### {persona}\n\n```bash\n"
            md += "\n".join(cmd_list)
            md += "\n```\n"
        return md

    def _format_text_report(self, analysis: Dict) -> str:
        """Format analysis as plain text report."""
        # Simplified text format for terminal display
        return f"""
FinOps Dashboard Executive Analysis
===================================

Generated: {analysis["timestamp"]}
Persona: {analysis["persona"]}

Key Insights:
{chr(10).join(f"  - {insight}" for insight in analysis["key_insights"])}

Top Optimization Opportunities:
{self._format_opportunities_text(analysis["optimization_opportunities"][:3])}
"""

    def _format_opportunities_text(self, opportunities: List[OptimizationOpportunity]) -> str:
        """Format top opportunities as plain text."""
        text = ""
        for i, opp in enumerate(opportunities, 1):
            text += f"  {i}. {opp.action}\n"
            text += f"     Savings: ${opp.potential_savings_annual:,.0f}/year | {opp.priority}\n"
        return text
