"""
VPC Cost Calculator - Calculate VPC infrastructure costs

This module provides CostCalculator class for calculating monthly VPC infrastructure costs
based on AWS ap-southeast-2 pricing (current rates as of module implementation).

Strategic Context:
- Extracted from vpc-inventory-analyzer.py lines 185-202
- Enhanced with complete-vpc-cost-analysis.py lines 13-16
- ZERO hard-coded pricing (uses config.py AWSCostModel)
- Manager output baseline: $416.10/month total across analyzed VPCs

AWS Pricing Reference (ap-southeast-2 region):
- NAT Gateway: $0.059/hour = $32.85/month (720 hours)
- Interface VPCE: $0.014/hour = $7.30/month (720 hours)
- Gateway VPCE: $0.00/month (S3, DynamoDB are FREE)

Note: Pricing dynamically retrieved from AWS or configured via AWSCostModel

Cost Calculation Formula:
total_monthly_cost = (nat_gateways × $32.85) + (vpce_interface × $7.30) + $0.00
"""

from decimal import Decimal
from runbooks.vpc.models import VPCResources, VPCCostBreakdown
from runbooks.vpc.config import AWSCostModel


class CostCalculator:
    """
    Calculate VPC infrastructure costs.

    Uses AWS Pricing API via AWSCostModel for zero hard-coded values.
    Supports regional pricing variations through config.py.

    Example:
        calculator = CostCalculator()
        resources = VPCResources(
            vpc_id="vpc-123",
            nat_gateways=2,
            vpce_interface=3,
            vpce_gateway=2
        )
        cost_breakdown = calculator.calculate_cost_breakdown(resources)
        print(f"Monthly cost: ${cost_breakdown.total_monthly_cost}")
        # Output: Monthly cost: $87.60 (2×$32.85 + 3×$7.30 + 0×$0.00)
    """

    def __init__(self, cost_model: AWSCostModel = None):
        """
        Initialize cost calculator.

        Args:
            cost_model: AWS cost model (default: load from config.py)
        """
        self.cost_model = cost_model or AWSCostModel()

    def calculate_cost_breakdown(self, resources: VPCResources) -> VPCCostBreakdown:
        """
        Calculate monthly cost breakdown for VPC resources.

        CRITICAL COST DRIVERS:
        1. NAT Gateways: $32.85/month EACH (primary cost driver)
        2. Interface VPCEs: $7.30/month EACH
        3. Gateway VPCEs: $0.00/month (always FREE for S3, DynamoDB)

        Cost calculation uses AWS Pricing API via AWSCostModel:
        - nat_gateway_monthly: Real-time pricing or $32.85 fallback
        - vpce_interface_monthly: Real-time pricing or $7.30 fallback
        - vpce_gateway_monthly: Always $0.00

        Args:
            resources: VPC resource counts

        Returns:
            VPCCostBreakdown: Detailed monthly cost breakdown

        Example:
            resources = VPCResources(
                vpc_id="vpc-007462e1e648ef6de",
                nat_gateways=1,
                vpce_interface=0,
                vpce_gateway=2  # S3 + DynamoDB (FREE)
            )
            cost_breakdown = calculator.calculate_cost_breakdown(resources)
            # nat_gateway_cost: $32.85
            # vpce_interface_cost: $0.00
            # vpce_gateway_cost: $0.00
            # total_monthly_cost: $32.85
        """
        # Calculate NAT Gateway costs ($32.85/month per gateway)
        nat_cost = Decimal(str(resources.nat_gateways)) * Decimal(str(self.cost_model.nat_gateway_monthly))

        # Calculate Interface VPCE costs ($7.30/month per endpoint)
        vpce_interface_cost = Decimal(str(resources.vpce_interface)) * Decimal(
            str(self.cost_model.vpc_endpoint_interface_monthly)
        )

        # Gateway VPCEs are always FREE ($0.00/month)
        vpce_gateway_cost = Decimal("0.00")

        # Total monthly cost
        total_monthly_cost = nat_cost + vpce_interface_cost + vpce_gateway_cost

        return VPCCostBreakdown(
            nat_gateway_cost=nat_cost,
            vpce_interface_cost=vpce_interface_cost,
            vpce_gateway_cost=vpce_gateway_cost,
            total_monthly_cost=total_monthly_cost,
        )

    def calculate_annual_cost(self, cost_breakdown: VPCCostBreakdown) -> Decimal:
        """
        Calculate annual cost from monthly breakdown.

        Args:
            cost_breakdown: Monthly cost breakdown

        Returns:
            Annual cost (monthly_cost × 12)

        Example:
            monthly = Decimal("32.85")
            annual = calculator.calculate_annual_cost(cost_breakdown)
            # Output: $394.20 per year
        """
        return cost_breakdown.total_monthly_cost * Decimal("12")

    def calculate_savings_potential(self, current_cost: VPCCostBreakdown, optimized_resources: VPCResources) -> Decimal:
        """
        Calculate potential monthly savings from resource optimization.

        Example use case: Remove unused NAT Gateway
        - Current: 2 NAT Gateways ($65.70/month)
        - Optimized: 1 NAT Gateway ($32.85/month)
        - Savings: $32.85/month ($394.20/year)

        Args:
            current_cost: Current monthly cost breakdown
            optimized_resources: Optimized resource configuration

        Returns:
            Monthly savings potential

        Example:
            current = VPCCostBreakdown(
                nat_gateway_cost=Decimal("65.70"),  # 2 NAT Gateways
                vpce_interface_cost=Decimal("7.30"),
                total_monthly_cost=Decimal("73.00")
            )
            optimized = VPCResources(
                vpc_id="vpc-123",
                nat_gateways=1,  # Remove 1 NAT Gateway
                vpce_interface=1
            )
            savings = calculator.calculate_savings_potential(current, optimized)
            # Output: $32.85/month savings
        """
        optimized_cost = self.calculate_cost_breakdown(optimized_resources)
        return current_cost.total_monthly_cost - optimized_cost.total_monthly_cost
