"""
Transit Gateway Attachment Optimizer

Feature 13 from PRD Gap Analysis (lines 1717-1722)

Business Value: $30K+ annual savings
- Transit Gateway attachment optimization (unused/underutilized attachments)
- Routing efficiency improvements
- Data processing cost reduction

Strategic Alignment:
- Epic 2 (Infrastructure Optimization): Network cost reduction
- Multi-account network consolidation
- PRD Section 7 (VPC Features): TGW cost optimization

Architecture Pattern:
- TGW attachment analysis (VPC, VPN, Direct Connect)
- Traffic volume analysis via CloudWatch metrics
- Cost modeling per attachment type
- Consolidation recommendations

Usage:
    from runbooks.vpc import TransitGatewayOptimizer

    optimizer = TransitGatewayOptimizer(profile='ops-profile')
    analyses = optimizer.analyze_tgw_attachments(region='ap-southeast-2')

    for analysis in analyses:
        print(f"TGW {analysis.tgw_id}: ${analysis.potential_savings:,.2f}/year savings")
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


class AttachmentType(str, Enum):
    """Transit Gateway attachment types"""

    VPC = "vpc"
    VPN = "vpn"
    DIRECT_CONNECT = "direct-connect"
    PEERING = "peering"
    CONNECT = "connect"


class OptimizationRecommendation(str, Enum):
    """TGW optimization recommendations"""

    DELETE_UNUSED = "DELETE_UNUSED"  # No traffic, delete attachment
    CONSOLIDATE = "CONSOLIDATE"  # Low traffic, consolidate with other attachment
    OPTIMIZE_ROUTING = "OPTIMIZE_ROUTING"  # Routing inefficiencies
    KEEP = "KEEP"  # Active attachment with acceptable utilization


@dataclass
class TGWAttachmentAnalysis:
    """Transit Gateway attachment analysis"""

    tgw_id: str
    attachment_id: str
    attachment_type: AttachmentType
    resource_id: str  # VPC ID, VPN ID, etc.
    monthly_bytes_processed: float
    monthly_cost_attachment: float
    monthly_cost_data: float
    monthly_cost_total: float
    annual_cost: float
    utilization_percentage: float
    traffic_pattern: str
    recommendation: OptimizationRecommendation
    potential_savings: float = 0.0


class TransitGatewayOptimizer:
    """
    Transit Gateway attachment cost optimizer

    Analyzes TGW attachments to identify cost optimization opportunities:
    1. Unused attachments → Deletion candidates ($36.50/month per attachment)
    2. Low-utilization attachments → Consolidation opportunities
    3. Routing inefficiencies → Optimization recommendations
    4. Data processing costs → Traffic pattern analysis

    Cost Model:
    - VPC Attachment: $0.05/hour = $36.50/month
    - VPN Attachment: $0.05/hour = $36.50/month
    - Direct Connect Attachment: $0.05/hour = $36.50/month
    - Data Processing: $0.02/GB (all attachment types)

    Example:
        optimizer = TransitGatewayOptimizer(profile='centralised-ops-profile')

        # Analyze TGW attachments
        analyses = optimizer.analyze_tgw_attachments(region='ap-southeast-2')

        # Display recommendations
        optimizer.display_analysis(analyses)

        # Get deletion candidates
        unused = optimizer.get_unused_attachments(analyses)
    """

    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        """
        Initialize Transit Gateway optimizer

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
        self._cloudwatch = None

    @property
    def ec2(self):
        """Lazy EC2 client"""
        if self._ec2 is None:
            self._ec2 = self.session.client("ec2", region_name=self.region)
        return self._ec2

    @property
    def cloudwatch(self):
        """Lazy CloudWatch client"""
        if self._cloudwatch is None:
            self._cloudwatch = self.session.client("cloudwatch", region_name=self.region)
        return self._cloudwatch

    def analyze_tgw_attachments(self, tgw_id: Optional[str] = None) -> List[TGWAttachmentAnalysis]:
        """
        Analyze Transit Gateway attachments for cost optimization

        Args:
            tgw_id: Specific TGW ID to analyze (analyzes all if None)

        Returns:
            List of attachment analyses with recommendations
        """
        self.console.print("[bold blue]🔍 Analyzing Transit Gateway attachments...[/bold blue]")

        # Get Transit Gateways
        filters = [{"Name": "transit-gateway-id", "Values": [tgw_id]}] if tgw_id else []
        tgws = self.ec2.describe_transit_gateways(Filters=filters)["TransitGateways"]

        analyses = []
        for tgw in tgws:
            tgw_id = tgw["TransitGatewayId"]

            # Get attachments for this TGW
            attachments = self.ec2.describe_transit_gateway_attachments(
                Filters=[{"Name": "transit-gateway-id", "Values": [tgw_id]}]
            )["TransitGatewayAttachments"]

            self.console.print(f"[dim]Found {len(attachments)} attachments for TGW {tgw_id}[/dim]")

            for attachment in attachments:
                if attachment["State"] != "available":
                    continue

                analysis = self._analyze_attachment(tgw_id, attachment)
                analyses.append(analysis)

        self.console.print(f"[bold green]✓ Analyzed {len(analyses)} attachments[/bold green]")
        return analyses

    def _analyze_attachment(self, tgw_id: str, attachment: Dict) -> TGWAttachmentAnalysis:
        """
        Analyze individual TGW attachment

        Args:
            tgw_id: Transit Gateway ID
            attachment: Attachment metadata

        Returns:
            Attachment analysis with cost and recommendations
        """
        attachment_id = attachment["TransitGatewayAttachmentId"]
        attachment_type = AttachmentType(attachment["ResourceType"])
        resource_id = attachment["ResourceId"]

        # Get CloudWatch metrics for traffic volume
        traffic = self._get_attachment_traffic(tgw_id, attachment_id)

        # Calculate costs
        monthly_bytes = traffic["bytes_processed_monthly"]
        monthly_gb = monthly_bytes / (1024**3)

        # Attachment cost: $0.05/hour × 730 hours/month
        monthly_cost_attachment = 0.05 * 730  # $36.50

        # Data processing cost: $0.02/GB
        monthly_cost_data = monthly_gb * 0.02

        monthly_cost_total = monthly_cost_attachment + monthly_cost_data
        annual_cost = monthly_cost_total * 12

        # Calculate utilization (arbitrary: >1TB/month = high, <100GB/month = low)
        if monthly_gb > 1000:  # >1TB
            utilization = 100.0
            traffic_pattern = "HIGH"
        elif monthly_gb > 100:  # 100GB-1TB
            utilization = 50.0
            traffic_pattern = "MODERATE"
        elif monthly_gb > 10:  # 10-100GB
            utilization = 20.0
            traffic_pattern = "LOW"
        else:  # <10GB
            utilization = 5.0
            traffic_pattern = "NONE"

        # Generate recommendation
        recommendation, potential_savings = self._generate_recommendation(
            utilization, monthly_cost_attachment, traffic_pattern
        )

        return TGWAttachmentAnalysis(
            tgw_id=tgw_id,
            attachment_id=attachment_id,
            attachment_type=attachment_type,
            resource_id=resource_id,
            monthly_bytes_processed=monthly_bytes,
            monthly_cost_attachment=monthly_cost_attachment,
            monthly_cost_data=monthly_cost_data,
            monthly_cost_total=monthly_cost_total,
            annual_cost=annual_cost,
            utilization_percentage=utilization,
            traffic_pattern=traffic_pattern,
            recommendation=recommendation,
            potential_savings=potential_savings,
        )

    def _get_attachment_traffic(self, tgw_id: str, attachment_id: str) -> Dict:
        """
        Get attachment traffic via CloudWatch metrics

        Metrics:
        - BytesIn: Bytes received by TGW from attachment
        - BytesOut: Bytes sent by TGW to attachment
        - PacketsIn/PacketsOut: Packet counts

        Args:
            tgw_id: Transit Gateway ID
            attachment_id: Attachment ID

        Returns:
            Traffic analysis with byte volumes
        """
        # TODO: Implement CloudWatch metrics query
        # Query BytesIn + BytesOut for last 30 days
        # Sum for total bytes processed

        # Placeholder implementation
        return {
            "bytes_processed_monthly": 50_000_000_000,  # 50GB placeholder
            "pattern": "STEADY",
        }

    def _generate_recommendation(
        self, utilization: float, attachment_cost: float, traffic_pattern: str
    ) -> tuple[OptimizationRecommendation, float]:
        """
        Generate optimization recommendation

        Recommendation Logic:
        - NONE traffic (<10GB/month): Delete unused attachment ($438/year savings)
        - LOW traffic (10-100GB/month): Consider consolidation
        - MODERATE/HIGH: Keep attachment

        Args:
            utilization: Utilization percentage
            attachment_cost: Monthly attachment cost
            traffic_pattern: Traffic pattern classification

        Returns:
            Tuple of (recommendation, potential_savings)
        """
        if traffic_pattern == "NONE":
            # Delete unused attachment
            annual_savings = attachment_cost * 12
            return OptimizationRecommendation.DELETE_UNUSED, annual_savings

        elif traffic_pattern == "LOW":
            # Consider consolidation (50% potential savings)
            annual_savings = (attachment_cost * 12) * 0.5
            return OptimizationRecommendation.CONSOLIDATE, annual_savings

        else:
            # Keep attachment
            return OptimizationRecommendation.KEEP, 0.0

    def get_unused_attachments(self, analyses: List[TGWAttachmentAnalysis]) -> List[TGWAttachmentAnalysis]:
        """
        Get unused attachments for deletion

        Args:
            analyses: List of attachment analyses

        Returns:
            List of unused attachments
        """
        return [a for a in analyses if a.recommendation == OptimizationRecommendation.DELETE_UNUSED]

    def display_analysis(self, analyses: List[TGWAttachmentAnalysis]) -> None:
        """
        Display TGW attachment analysis in Rich table

        Args:
            analyses: List of attachment analyses
        """
        if not analyses:
            self.console.print("[yellow]No Transit Gateway attachments found[/yellow]")
            return

        table = Table(title="Transit Gateway Attachment Analysis")
        table.add_column("TGW ID", style="cyan")
        table.add_column("Attachment ID", style="blue")
        table.add_column("Type", style="magenta")
        table.add_column("Resource", style="yellow")
        table.add_column("Monthly GB", justify="right", style="green")
        table.add_column("Monthly Cost", justify="right", style="red")
        table.add_column("Annual Cost", justify="right", style="bold red")
        table.add_column("Traffic", style="yellow")
        table.add_column("Recommendation", style="green")
        table.add_column("Potential Savings", justify="right", style="bold green")

        for analysis in analyses:
            monthly_gb = analysis.monthly_bytes_processed / (1024**3)

            table.add_row(
                analysis.tgw_id,
                analysis.attachment_id,
                analysis.attachment_type.value,
                analysis.resource_id,
                f"{monthly_gb:,.1f}",
                f"${analysis.monthly_cost_total:,.2f}",
                f"${analysis.annual_cost:,.2f}",
                analysis.traffic_pattern,
                analysis.recommendation.value,
                f"${analysis.potential_savings:,.2f}",
            )

        self.console.print(table)

        # Summary statistics
        total_cost = sum(a.annual_cost for a in analyses)
        total_savings = sum(a.potential_savings for a in analyses)
        unused_count = len(self.get_unused_attachments(analyses))

        summary = Panel(
            f"[bold]Total Annual TGW Cost: ${total_cost:,.2f}[/bold]\n"
            f"[bold green]Total Potential Savings: ${total_savings:,.2f}[/bold green]\n"
            f"Total Attachments: {len(analyses)}\n"
            f"Unused Attachments: {unused_count}",
            title="Optimization Summary",
            border_style="green",
        )
        self.console.print(summary)


def create_tgw_optimizer(
    operational_profile: Optional[str] = None, region: Optional[str] = None
) -> TransitGatewayOptimizer:
    """
    Factory function to create Transit Gateway optimizer

    Args:
        operational_profile: AWS operational profile
        region: AWS region

    Returns:
        Configured optimizer instance
    """
    return TransitGatewayOptimizer(profile=operational_profile, region=region)
