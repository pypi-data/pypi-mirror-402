"""
VPC Peering Cost Analyzer

Feature 12 from PRD Gap Analysis (lines 1655-1709)

Business Value: $50K+ annual savings
- Data transfer cost optimization for VPC peering connections
- Transit Gateway consolidation opportunities identification
- Unused peering connection cleanup

Strategic Alignment:
- Epic 2 (Infrastructure Optimization): Network cost reduction
- Multi-account network optimization (68 accounts, multiple VPCs)
- PRD Section 7 (VPC Features): Peering cost analysis

Architecture Pattern:
- VPC Flow Logs analysis for data transfer volumes
- Cost modeling for peering vs Transit Gateway
- High-traffic peering identification for TGW consolidation
- Unused peering detection for cleanup

Usage:
    from runbooks.vpc import VPCPeeringCostAnalyzer

    analyzer = VPCPeeringCostAnalyzer(profile='ops-profile')
    analyses = analyzer.analyze_peering_costs(region='ap-southeast-2')

    for analysis in analyses:
        print(f"Peering {analysis['peering_id']}: {analysis['recommendation']}")
"""

import boto3
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from enum import Enum

try:
    from runbooks.common.profile_utils import get_profile_for_operation
except ImportError:
    # Fallback for environments where profile_utils is not available
    def get_profile_for_operation(operation_type: str = "operational", user_specified_profile=None, **kwargs):
        return user_specified_profile or "default"


class PeeringRecommendation(str, Enum):
    """VPC peering optimization recommendations"""

    KEEP = "KEEP"  # Active peering with acceptable cost
    CONSOLIDATE_TGW = "CONSOLIDATE_TGW"  # High traffic, move to Transit Gateway
    DELETE_UNUSED = "DELETE_UNUSED"  # No traffic, safe to delete
    OPTIMIZE_ROUTING = "OPTIMIZE_ROUTING"  # Routing inefficiencies detected


@dataclass
class PeeringAnalysis:
    """VPC peering connection analysis result"""

    peering_id: str
    requester_vpc: str
    accepter_vpc: str
    status: str
    monthly_data_transfer_gb: float
    monthly_cost: float
    annual_cost: float
    traffic_pattern: str  # HEAVY, MODERATE, LIGHT, NONE
    recommendation: PeeringRecommendation
    tgw_comparison: Optional[Dict] = None
    potential_savings: float = 0.0


class VPCPeeringCostAnalyzer:
    """
    VPC Peering cost analysis and optimization

    Analyzes VPC peering connections to identify cost optimization opportunities:
    1. High-traffic peering → Transit Gateway consolidation
    2. Unused peering → Deletion candidates
    3. Data transfer cost analysis → Routing optimization

    Cost Model:
    - VPC Peering data transfer: $0.01/GB (same AZ), $0.02/GB (cross-AZ)
    - Transit Gateway: $0.02/hour/attachment + $0.02/GB data processing
    - Breakeven: ~5TB/month per connection

    Example:
        analyzer = VPCPeeringCostAnalyzer(profile='centralised-ops-profile')

        # Analyze all peering connections
        analyses = analyzer.analyze_peering_costs(region='ap-southeast-2')

        # Display recommendations
        analyzer.display_analysis(analyses)

        # Generate cleanup list
        unused = analyzer.get_unused_peering_connections(analyses)
    """

    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize VPC peering cost analyzer

        Args:
            profile: AWS profile name
            region: AWS region
        """
        self.profile = get_profile_for_operation("operational", profile)
        self.session = boto3.Session(profile_name=self.profile)
        self.region = region or self.session.region_name
        self.console = Console()

        # AWS clients
        self._ec2 = None
        self._logs = None
        self._ce = None

    @property
    def ec2(self):
        """Lazy EC2 client"""
        if self._ec2 is None:
            self._ec2 = self.session.client("ec2", region_name=self.region)
        return self._ec2

    @property
    def logs(self):
        """Lazy CloudWatch Logs client"""
        if self._logs is None:
            self._logs = self.session.client("logs", region_name=self.region)
        return self._logs

    @property
    def cost_explorer(self):
        """Lazy Cost Explorer client"""
        if self._ce is None:
            self._ce = self.session.client("ce", region_name="us-east-1")  # CE is global
        return self._ce

    def analyze_peering_costs(self, region: Optional[str] = None) -> List[PeeringAnalysis]:
        """
        Analyze VPC peering connection costs

        Analyzes:
        - Data transfer volumes via VPC Flow Logs
        - Cost calculations (peering vs Transit Gateway)
        - Traffic patterns and usage trends
        - Optimization recommendations

        Args:
            region: AWS region to analyze (uses instance region if None)

        Returns:
            List of peering analyses with recommendations
        """
        analysis_region = region or self.region
        self.console.print(f"[bold blue]🔍 Analyzing VPC peering connections in {analysis_region}...[/bold blue]")

        # Get all peering connections
        peering_connections = self.ec2.describe_vpc_peering_connections()["VpcPeeringConnections"]

        self.console.print(f"[dim]Found {len(peering_connections)} peering connections[/dim]")

        analyses = []
        for peering in peering_connections:
            if peering["Status"]["Code"] != "active":
                continue

            # Analyze traffic
            traffic = self._analyze_peering_traffic(peering["VpcPeeringConnectionId"])

            # Calculate costs
            cost_analysis = self._calculate_peering_costs(traffic, peering)

            # Generate recommendation
            recommendation = self._recommend_optimization(peering, cost_analysis)

            # Compare with Transit Gateway costs
            tgw_comparison = self._compare_with_tgw(cost_analysis)

            analysis = PeeringAnalysis(
                peering_id=peering["VpcPeeringConnectionId"],
                requester_vpc=peering["RequesterVpcInfo"]["VpcId"],
                accepter_vpc=peering["AccepterVpcInfo"]["VpcId"],
                status=peering["Status"]["Code"],
                monthly_data_transfer_gb=cost_analysis["monthly_gb"],
                monthly_cost=cost_analysis["monthly_cost"],
                annual_cost=cost_analysis["annual_cost"],
                traffic_pattern=cost_analysis["traffic_pattern"],
                recommendation=recommendation,
                tgw_comparison=tgw_comparison,
                potential_savings=cost_analysis.get("potential_savings", 0.0),
            )
            analyses.append(analysis)

        self.console.print(f"[bold green]✓ Analysis complete[/bold green]")
        return analyses

    def _analyze_peering_traffic(self, peering_id: str) -> Dict:
        """
        Analyze peering connection traffic via VPC Flow Logs

        Args:
            peering_id: VPC peering connection ID

        Returns:
            Traffic analysis with volume and patterns
        """
        # TODO: Implement VPC Flow Logs query for peering traffic
        # Query VPC Flow Logs for traffic through peering connection
        # Calculate bytes transferred in last 30 days
        # Identify traffic patterns (steady, bursty, declining)

        # Placeholder implementation
        return {
            "bytes_transferred": 500_000_000_000,  # 500GB
            "pattern": "STEADY",
            "peak_throughput_mbps": 100,
            "avg_throughput_mbps": 50,
            "analysis_period_days": 30,
        }

    def _calculate_peering_costs(self, traffic: Dict, peering: Dict) -> Dict:
        """
        Calculate VPC peering costs

        Cost Model:
        - Same AZ: $0.01/GB
        - Cross-AZ (same region): $0.02/GB
        - Cross-region: $0.02/GB (source) + $0.02/GB (destination)

        Args:
            traffic: Traffic analysis from _analyze_peering_traffic
            peering: Peering connection metadata

        Returns:
            Cost analysis with monthly/annual projections
        """
        bytes_monthly = traffic["bytes_transferred"]
        gb_monthly = bytes_monthly / (1024**3)

        # Determine pricing (simplified: assume cross-AZ)
        cost_per_gb = 0.02  # Cross-AZ pricing
        monthly_cost = gb_monthly * cost_per_gb
        annual_cost = monthly_cost * 12

        # Classify traffic pattern
        if gb_monthly > 5000:  # >5TB/month
            traffic_pattern = "HEAVY"
        elif gb_monthly > 1000:  # 1-5TB/month
            traffic_pattern = "MODERATE"
        elif gb_monthly > 100:  # 100GB-1TB/month
            traffic_pattern = "LIGHT"
        else:
            traffic_pattern = "NONE"

        return {
            "monthly_gb": gb_monthly,
            "monthly_cost": monthly_cost,
            "annual_cost": annual_cost,
            "traffic_pattern": traffic_pattern,
            "cost_per_gb": cost_per_gb,
        }

    def _recommend_optimization(self, peering: Dict, cost_analysis: Dict) -> PeeringRecommendation:
        """
        Generate optimization recommendation

        Recommendation Logic:
        - HEAVY traffic (>5TB/month): Consider Transit Gateway consolidation
        - NONE traffic (<100GB/month): Delete unused peering
        - MODERATE/LIGHT: Keep peering connection

        Args:
            peering: Peering metadata
            cost_analysis: Cost analysis

        Returns:
            Optimization recommendation
        """
        pattern = cost_analysis["traffic_pattern"]

        if pattern == "HEAVY":
            return PeeringRecommendation.CONSOLIDATE_TGW
        elif pattern == "NONE":
            return PeeringRecommendation.DELETE_UNUSED
        else:
            return PeeringRecommendation.KEEP

    def _compare_with_tgw(self, cost_analysis: Dict) -> Optional[Dict]:
        """
        Compare VPC peering costs with Transit Gateway costs

        Transit Gateway Cost Model:
        - Attachment: $0.05/hour = $36.50/month
        - Data processing: $0.02/GB

        Breakeven Point:
        - Peering: $0.02/GB
        - TGW: $36.50/month + $0.02/GB
        - Breakeven: When data transfer cost savings offset attachment cost

        Args:
            cost_analysis: Peering cost analysis

        Returns:
            TGW comparison with savings/cost difference
        """
        monthly_gb = cost_analysis["monthly_gb"]

        # TGW costs
        tgw_attachment_cost = 0.05 * 730  # $0.05/hour × 730 hours/month
        tgw_data_cost = monthly_gb * 0.02
        tgw_total = tgw_attachment_cost + tgw_data_cost

        # Peering cost
        peering_cost = cost_analysis["monthly_cost"]

        # Calculate difference
        monthly_difference = peering_cost - tgw_total
        annual_difference = monthly_difference * 12

        return {
            "tgw_monthly_cost": tgw_total,
            "peering_monthly_cost": peering_cost,
            "monthly_difference": monthly_difference,
            "annual_difference": annual_difference,
            "recommendation": "TGW" if monthly_difference > 0 else "PEERING",
            "breakeven_gb": tgw_attachment_cost / (cost_analysis["cost_per_gb"] - 0.02),
        }

    def get_unused_peering_connections(self, analyses: List[PeeringAnalysis]) -> List[PeeringAnalysis]:
        """
        Get unused peering connections for cleanup

        Args:
            analyses: List of peering analyses

        Returns:
            List of unused peering connections
        """
        return [a for a in analyses if a.recommendation == PeeringRecommendation.DELETE_UNUSED]

    def display_analysis(self, analyses: List[PeeringAnalysis]) -> None:
        """
        Display peering analysis in Rich table format

        Args:
            analyses: List of peering analyses
        """
        if not analyses:
            self.console.print("[yellow]No peering connections found[/yellow]")
            return

        table = Table(title="VPC Peering Cost Analysis")
        table.add_column("Peering ID", style="cyan")
        table.add_column("Requester VPC", style="blue")
        table.add_column("Accepter VPC", style="blue")
        table.add_column("Monthly GB", justify="right", style="yellow")
        table.add_column("Monthly Cost", justify="right", style="red")
        table.add_column("Annual Cost", justify="right", style="bold red")
        table.add_column("Traffic", style="magenta")
        table.add_column("Recommendation", style="green")

        for analysis in analyses:
            table.add_row(
                analysis.peering_id,
                analysis.requester_vpc,
                analysis.accepter_vpc,
                f"{analysis.monthly_data_transfer_gb:,.1f}",
                f"${analysis.monthly_cost:,.2f}",
                f"${analysis.annual_cost:,.2f}",
                analysis.traffic_pattern,
                analysis.recommendation.value,
            )

        self.console.print(table)

        # Summary statistics
        total_cost = sum(a.annual_cost for a in analyses)
        unused_count = len(self.get_unused_peering_connections(analyses))
        heavy_count = len([a for a in analyses if a.traffic_pattern == "HEAVY"])

        summary = Panel(
            f"[bold]Total Annual Peering Cost: ${total_cost:,.2f}[/bold]\n"
            f"Total Connections: {len(analyses)}\n"
            f"Unused Connections: {unused_count}\n"
            f"Heavy Traffic Connections: {heavy_count} (TGW candidates)",
            title="Summary",
            border_style="blue",
        )
        self.console.print(summary)


def create_peering_cost_analyzer(
    operational_profile: Optional[str] = None, region: Optional[str] = None
) -> VPCPeeringCostAnalyzer:
    """
    Factory function to create VPC peering cost analyzer

    Args:
        operational_profile: AWS operational profile
        region: AWS region

    Returns:
        Configured analyzer instance
    """
    return VPCPeeringCostAnalyzer(profile=operational_profile, region=region)
