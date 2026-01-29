"""
VPC Recommendation Engine - Generate decommissioning recommendations

Extracted from vpc-inventory-analyzer.py lines 272-323
Generates evidence-based recommendations with business rationale
"""

from typing import Tuple
from decimal import Decimal
from runbooks.vpc.models import VPCResources, VPCCostBreakdown


class RecommendationEngine:
    """Generate VPC decommissioning recommendations with business rationale."""

    def generate_recommendation(
        self, resources: VPCResources, cost_breakdown: VPCCostBreakdown, three_bucket: str
    ) -> Tuple[str, str]:
        """
        Generate recommendation with WHY rationale.

        Decision Logic:
        1. MUST DELETE: 0 ENIs = No resources, immediate deletion
        2. SHOULD NOT DELETE: TGW attachments OR EC2 instances
        3. COULD DELETE: Orphaned NAT Gateways OR inactive Lambda

        Args:
            resources: VPC resource counts
            cost_breakdown: Monthly cost breakdown
            three_bucket: Decommissioning bucket

        Returns:
            Tuple of (recommendation, rationale)
        """
        # MUST DELETE logic
        if resources.enis == 0:
            return (
                "DECOMMISSION_NOW",
                f"0 ENIs = No resources. Immediate deletion (${cost_breakdown.total_monthly_cost}/month savings).",
            )

        # SHOULD NOT DELETE logic
        if resources.tgw_attachments > 0:
            return (
                "RETAIN_TGW",
                f"{resources.tgw_attachments} Transit Gateway attachment(s). Cross-account network dependency.",
            )

        if resources.ec2_instances > 0:
            return (
                "RETAIN_EC2",
                f"{resources.ec2_instances} EC2 instance(s). Active compute workloads require stakeholder approval.",
            )

        # COULD DELETE logic
        if resources.nat_gateways > 0 and resources.ec2_instances == 0 and resources.lambda_functions == 0:
            return (
                "INVESTIGATE_ORPHANED",
                f"{resources.nat_gateways} NAT Gateway(s) but no EC2/Lambda. Orphaned infrastructure (${cost_breakdown.total_monthly_cost}/month).",
            )

        if resources.lambda_functions > 0:
            return (
                "ANALYZE_LAMBDA",
                f"{resources.lambda_functions} Lambda function(s). Validate inactivity before decommissioning.",
            )

        # Default
        return ("RETAIN_MONITOR", f"Active resources: ${cost_breakdown.total_monthly_cost}/month ongoing cost.")
