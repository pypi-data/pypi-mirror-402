"""
NAT Gateway Optimizer - Cost optimization for NAT Gateway infrastructure

Reuses existing VPC infrastructure (cost_engine.py, networking_wrapper.py)
following KISS/DRY/LEAN principles for efficient NAT Gateway optimization.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    create_table,
    format_cost,
    STATUS_INDICATORS,
)

from .cost_engine import NetworkingCostEngine
from .networking_wrapper import VPCNetworkingWrapper

logger = logging.getLogger(__name__)


@dataclass
class NATOptimizationResult:
    """NAT Gateway optimization analysis result"""

    nat_gateway_id: str
    current_monthly_cost: float
    projected_savings: float
    optimization_type: str
    confidence_score: float
    recommendations: List[str]


class NATGatewayOptimizer:
    """
    NAT Gateway cost optimization module

    Leverages existing VPC infrastructure for efficient cost analysis
    and optimization recommendations targeting 30% cost reduction.
    """

    def __init__(
        self,
        profile: str,
        region: str = "ap-southeast-2",
        analyze: bool = False,
        optimize: bool = False,
        savings_target: float = 0.3,
        include_alternatives: bool = False,
        export_format: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize NAT Gateway Optimizer

        Args:
            profile: AWS profile for operations
            region: AWS region to analyze
            analyze: Run analysis mode
            optimize: Run optimization mode
            savings_target: Target savings percentage (default 30%)
            include_alternatives: Include alternative solutions
            export_format: Export format for results
        """
        self.profile = profile
        self.region = region
        self.analyze = analyze
        self.optimize = optimize
        self.savings_target = savings_target
        self.include_alternatives = include_alternatives
        self.export_format = export_format

        # Initialize existing VPC infrastructure (DRY principle)
        self.networking_wrapper = VPCNetworkingWrapper(profile=profile, region=region, output_format="rich")

        # Initialize cost engine if session available
        self.cost_engine = None
        if self.networking_wrapper.session:
            self.cost_engine = NetworkingCostEngine(
                session=self.networking_wrapper.session, enable_parallel=True, enable_caching=True
            )

        # Results storage
        self.optimization_results = []
        self.total_potential_savings = 0.0

    def run_nat_gateway_optimization(self) -> Dict[str, Any]:
        """
        Main optimization method called by CLI

        Returns:
            Dictionary containing optimization results and recommendations
        """
        print_header("NAT Gateway Cost Optimizer", "1.0.0")

        results = {
            "timestamp": datetime.now().isoformat(),
            "profile": self.profile,
            "region": self.region,
            "savings_target": self.savings_target,
            "total_analyzed": 0,
            "total_potential_savings": 0.0,
            "optimization_opportunities": [],
            "recommendations": [],
            "alternatives": [] if self.include_alternatives else None,
        }

        if not self.networking_wrapper.session:
            print_error("❌ No AWS session available")
            return results

        if not self.cost_engine:
            print_error("❌ Cost engine initialization failed")
            return results

        try:
            # Leverage existing NAT Gateway analysis from networking_wrapper
            nat_analysis = self.networking_wrapper.analyze_nat_gateways(days=30)

            if not nat_analysis.get("nat_gateways"):
                print_warning("⚠️  No NAT Gateways found in region")
                return results

            results["total_analyzed"] = len(nat_analysis["nat_gateways"])

            # Analyze each NAT Gateway for optimization opportunities
            for ng_data in nat_analysis["nat_gateways"]:
                optimization = self._analyze_nat_gateway_optimization(ng_data)
                if optimization:
                    self.optimization_results.append(optimization)
                    results["optimization_opportunities"].append(
                        {
                            "nat_gateway_id": optimization.nat_gateway_id,
                            "current_cost": optimization.current_monthly_cost,
                            "potential_savings": optimization.projected_savings,
                            "optimization_type": optimization.optimization_type,
                            "confidence": optimization.confidence_score,
                        }
                    )

            # Calculate total potential savings
            results["total_potential_savings"] = sum(opt.projected_savings for opt in self.optimization_results)

            # Generate comprehensive recommendations
            results["recommendations"] = self._generate_optimization_recommendations()

            # Add alternative solutions if requested
            if self.include_alternatives:
                results["alternatives"] = self._generate_alternative_solutions()

            # Display results using Rich formatting
            self._display_optimization_results(results)

            return results

        except Exception as e:
            print_error(f"❌ NAT Gateway optimization failed: {str(e)}")
            logger.error(f"NAT Gateway optimization error: {e}")
            return results

    def _analyze_nat_gateway_optimization(self, nat_data: Dict[str, Any]) -> Optional[NATOptimizationResult]:
        """
        Analyze individual NAT Gateway for optimization opportunities

        Args:
            nat_data: NAT Gateway data from networking analysis

        Returns:
            Optimization result if opportunities found
        """
        nat_id = nat_data.get("nat_gateway_id", "unknown")
        monthly_cost = nat_data.get("monthly_cost", 0.0)

        # Skip if cost is negligible
        if monthly_cost < 10.0:
            return None

        # Calculate optimization based on usage patterns
        bytes_processed = nat_data.get("bytes_processed_gb", 0.0)
        confidence_score = 0.8  # Base confidence

        # Determine optimization type and potential savings
        if bytes_processed < 1.0:  # Low usage
            optimization_type = "low_usage_replacement"
            projected_savings = monthly_cost * 0.8  # 80% savings via VPC Endpoints
            confidence_score = 0.9
            recommendations = [
                "Replace with VPC Endpoints for AWS services",
                "Consider NAT Instance for minimal traffic",
                "Evaluate subnet routing optimization",
            ]

        elif bytes_processed < 10.0:  # Medium usage
            optimization_type = "nat_instance_replacement"
            projected_savings = monthly_cost * 0.4  # 40% savings via NAT Instance
            confidence_score = 0.7
            recommendations = [
                "Replace with cost-optimized NAT Instance",
                "Implement VPC Endpoints for AWS services",
                "Optimize routing for efficiency",
            ]

        elif monthly_cost > 100.0:  # High cost
            optimization_type = "architecture_optimization"
            projected_savings = monthly_cost * self.savings_target
            confidence_score = 0.6
            recommendations = [
                "Implement multi-AZ NAT Instance cluster",
                "Add VPC Endpoints for high-traffic AWS services",
                "Consider Transit Gateway for complex routing",
            ]

        else:
            # No significant optimization opportunity
            return None

        return NATOptimizationResult(
            nat_gateway_id=nat_id,
            current_monthly_cost=monthly_cost,
            projected_savings=projected_savings,
            optimization_type=optimization_type,
            confidence_score=confidence_score,
            recommendations=recommendations,
        )

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate comprehensive optimization recommendations"""
        recommendations = []

        if not self.optimization_results:
            return ["No optimization opportunities identified"]

        total_savings = sum(opt.projected_savings for opt in self.optimization_results)

        recommendations.extend(
            [
                f"💰 Potential annual savings: {format_cost(total_savings * 12)}",
                f"🎯 Target savings rate: {self.savings_target * 100:.0f}%",
                "🔧 Recommended actions:",
            ]
        )

        # Group recommendations by optimization type
        optimization_types = set(opt.optimization_type for opt in self.optimization_results)

        for opt_type in optimization_types:
            count = sum(1 for opt in self.optimization_results if opt.optimization_type == opt_type)
            if opt_type == "low_usage_replacement":
                recommendations.append(f"   • Replace {count} low-usage NAT Gateway(s) with VPC Endpoints")
            elif opt_type == "nat_instance_replacement":
                recommendations.append(f"   • Replace {count} medium-usage NAT Gateway(s) with NAT Instances")
            elif opt_type == "architecture_optimization":
                recommendations.append(f"   • Optimize {count} high-cost NAT Gateway(s) architecture")

        return recommendations

    def _generate_alternative_solutions(self) -> List[Dict[str, Any]]:
        """Generate alternative networking solutions"""
        alternatives = []

        alternatives.extend(
            [
                {
                    "solution": "VPC Endpoints",
                    "use_case": "AWS service traffic",
                    "cost_impact": "80-90% reduction for AWS service calls",
                    "complexity": "Low",
                    "implementation_time": "1-2 days",
                },
                {
                    "solution": "NAT Instance",
                    "use_case": "Medium traffic volumes",
                    "cost_impact": "40-60% cost reduction",
                    "complexity": "Medium",
                    "implementation_time": "3-5 days",
                },
                {
                    "solution": "Transit Gateway",
                    "use_case": "Complex multi-VPC scenarios",
                    "cost_impact": "20-40% cost optimization",
                    "complexity": "High",
                    "implementation_time": "1-2 weeks",
                },
            ]
        )

        return alternatives

    def _display_optimization_results(self, results: Dict[str, Any]) -> None:
        """Display optimization results using Rich formatting"""

        # Summary panel
        console.print()
        console.print("🚀 [bold green]NAT Gateway Optimization Summary[/bold green]")
        console.print(f"   • Analyzed: {results['total_analyzed']} NAT Gateway(s)")
        console.print(f"   • Opportunities: {len(results['optimization_opportunities'])}")
        console.print(
            f"   • Potential Savings: [green]{format_cost(results['total_potential_savings'] * 12)} annually[/green]"
        )

        # Optimization opportunities table
        if results["optimization_opportunities"]:
            console.print()
            table = create_table("NAT Gateway Optimization Opportunities")
            table.add_column("NAT Gateway ID", style="cyan")
            table.add_column("Current Cost", style="yellow")
            table.add_column("Potential Savings", style="green")
            table.add_column("Optimization Type", style="blue")
            table.add_column("Confidence", style="magenta")

            for opp in results["optimization_opportunities"]:
                table.add_row(
                    opp["nat_gateway_id"],
                    format_cost(opp["current_cost"]),
                    format_cost(opp["potential_savings"]),
                    opp["optimization_type"].replace("_", " ").title(),
                    f"{opp['confidence'] * 100:.0f}%",
                )

            console.print(table)

        # Recommendations
        if results["recommendations"]:
            console.print()
            console.print("📋 [bold blue]Optimization Recommendations[/bold blue]")
            for rec in results["recommendations"]:
                console.print(f"   {rec}")

        # Alternative solutions (if requested)
        if results.get("alternatives"):
            console.print()
            console.print("🔄 [bold purple]Alternative Solutions[/bold purple]")
            alt_table = create_table("Alternative Networking Solutions")
            alt_table.add_column("Solution", style="cyan")
            alt_table.add_column("Use Case", style="yellow")
            alt_table.add_column("Cost Impact", style="green")
            alt_table.add_column("Complexity", style="blue")

            for alt in results["alternatives"]:
                alt_table.add_row(alt["solution"], alt["use_case"], alt["cost_impact"], alt["complexity"])

            console.print(alt_table)

        # Success message
        if results["total_potential_savings"] > 0:
            print_success(
                f"✅ NAT Gateway optimization complete - {format_cost(results['total_potential_savings'] * 12)} annual savings identified"
            )
        else:
            print_warning("⚠️  No significant optimization opportunities found")
