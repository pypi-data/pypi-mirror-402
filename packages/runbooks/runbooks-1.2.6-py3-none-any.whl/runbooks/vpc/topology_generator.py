"""
Network Topology Generator - Lean wrapper leveraging existing VPC infrastructure

This module provides network topology visualization capabilities by reusing:
- HeatMapEngine for visualization and cost overlay
- NetworkingWrapper for network discovery
- RichFormatters for enterprise display formatting

Follows KISS/DRY/LEAN principles by wrapping existing functionality.
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .heatmap_engine import NetworkingCostHeatMapEngine, HeatMapConfig
from .networking_wrapper import VPCNetworkingWrapper
from .rich_formatters import (
    display_heatmap,
    display_transit_gateway_architecture,
    display_optimization_recommendations,
    display_success,
)
from ..common.rich_utils import console, print_header, print_success

logger = logging.getLogger(__name__)


@dataclass
class TopologyConfig:
    """Configuration for network topology generation"""

    profile: str
    region: str
    include_costs: bool = False
    detail_level: str = "detailed"
    output_dir: str = "./vpc_topology"
    export_formats: List[str] = None


class NetworkTopologyGenerator:
    """
    Network topology generator leveraging existing VPC infrastructure.

    This class is a lean wrapper that reuses:
    - HeatMapEngine for visualization capabilities
    - NetworkingWrapper for network discovery
    - RichFormatters for display formatting
    """

    def __init__(
        self,
        profile: str,
        region: str,
        include_costs: bool = False,
        detail_level: str = "detailed",
        output_dir: str = "./vpc_topology",
    ):
        """
        Initialize topology generator with existing VPC infrastructure.

        Args:
            profile: AWS profile for authentication
            region: AWS region for analysis
            include_costs: Whether to include cost overlay
            detail_level: Level of detail (detailed, comprehensive, summary)
            output_dir: Directory for output files
        """
        self.config = TopologyConfig(
            profile=profile,
            region=region,
            include_costs=include_costs,
            detail_level=detail_level,
            output_dir=output_dir,
        )

        # Initialize existing VPC infrastructure components
        self._init_vpc_components()

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _init_vpc_components(self):
        """Initialize existing VPC infrastructure components for reuse."""
        try:
            # Initialize networking wrapper for discovery
            self.networking_wrapper = VPCNetworkingWrapper(profile=self.config.profile, region=self.config.region)

            # Initialize heatmap engine for visualization (if costs enabled)
            if self.config.include_costs:
                heat_config = HeatMapConfig(single_account_profile=self.config.profile, regions=[self.config.region])
                self.heatmap_engine = NetworkingCostHeatMapEngine(config=heat_config)

        except Exception as e:
            logger.warning(f"VPC component initialization warning: {e}")
            # Continue without advanced features if components unavailable

    def generate_network_topology(self) -> Dict[str, Any]:
        """
        Generate comprehensive network topology using existing VPC infrastructure.

        Main method called by CLI. Leverages existing components:
        - NetworkingWrapper for network discovery
        - HeatMapEngine for cost visualization
        - RichFormatters for display

        Returns:
            Dict containing topology results and visualizations
        """
        print_header("Network Topology Generation", version="1.0.0")

        topology_results = {
            "timestamp": datetime.now().isoformat(),
            "profile": self.config.profile,
            "region": self.config.region,
            "detail_level": self.config.detail_level,
            "include_costs": self.config.include_costs,
            "topology_data": {},
            "visualizations": {},
            "recommendations": {},
            "output_files": [],
        }

        try:
            # Phase 1: Network Discovery (reuse networking_wrapper)
            topology_results["topology_data"] = self._discover_network_topology()

            # Phase 2: Cost Analysis (reuse heatmap_engine if enabled)
            if self.config.include_costs and hasattr(self, "heatmap_engine"):
                topology_results["cost_analysis"] = self._generate_cost_overlay()

            # Phase 3: Topology Visualization (reuse rich_formatters)
            topology_results["visualizations"] = self._generate_topology_visualizations(
                topology_results["topology_data"]
            )

            # Phase 4: Optimization Recommendations
            topology_results["recommendations"] = self._generate_topology_recommendations(
                topology_results["topology_data"]
            )

            # Phase 5: Export Results
            self._export_topology_results(topology_results)

            # Display success using rich formatters
            display_success(
                console,
                "Network topology generated successfully",
                {"profile": self.config.profile, "region": self.config.region, "output_dir": self.config.output_dir},
            )

            return topology_results

        except Exception as e:
            logger.error(f"Topology generation failed: {e}")
            raise

    def _discover_network_topology(self) -> Dict[str, Any]:
        """
        Discover network topology using existing networking wrapper.

        Leverages VPCNetworkingWrapper methods for network discovery.
        """
        topology_data = {
            "discovery_timestamp": datetime.now().isoformat(),
            "vpcs": [],
            "transit_gateways": [],
            "nat_gateways": [],
            "vpc_endpoints": [],
            "network_connections": [],
        }

        try:
            # Discover Transit Gateway architecture (reuse existing method)
            tgw_data = self.networking_wrapper.analyze_transit_gateway_architecture(
                include_costs=self.config.include_costs
            )
            topology_data["transit_gateways"] = tgw_data.get("transit_gateways", [])

            # Display Transit Gateway topology using existing formatter
            if topology_data["transit_gateways"]:
                display_transit_gateway_architecture(console, tgw_data)

            # Discover NAT Gateways (reuse existing method)
            nat_analysis = self.networking_wrapper.analyze_nat_gateways()
            topology_data["nat_gateways"] = nat_analysis.get("nat_gateways", [])

            # Discover VPC Endpoints (reuse existing method)
            endpoint_analysis = self.networking_wrapper.analyze_vpc_endpoints()
            topology_data["vpc_endpoints"] = endpoint_analysis.get("endpoints", [])

            console.print(f"[green]✅ Network discovery completed[/green]")
            console.print(
                f"[dim]Found: {len(topology_data['transit_gateways'])} TGWs, "
                f"{len(topology_data['nat_gateways'])} NAT GWs, "
                f"{len(topology_data['vpc_endpoints'])} Endpoints[/dim]"
            )

            return topology_data

        except Exception as e:
            logger.error(f"Network discovery failed: {e}")
            raise

    def _generate_cost_overlay(self) -> Dict[str, Any]:
        """
        Generate cost overlay using existing heatmap engine.

        Leverages NetworkingCostHeatMapEngine for cost visualization.
        """
        if not hasattr(self, "heatmap_engine"):
            return {"cost_overlay": "disabled", "reason": "heatmap_engine_unavailable"}

        try:
            # Generate comprehensive heat maps (reuse existing method)
            heat_maps = self.heatmap_engine.generate_comprehensive_heat_maps()

            # Display heat map using existing formatter
            display_heatmap(console, heat_maps)

            return {"cost_overlay": "enabled", "heat_maps": heat_maps, "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.warning(f"Cost overlay generation failed: {e}")
            return {"cost_overlay": "failed", "error": str(e)}

    def _generate_topology_visualizations(self, topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate topology visualizations using existing rich formatters.

        Creates visual representations of network topology.
        """
        visualizations = {"generated": True, "formats": ["rich_console", "text_summary"], "files": []}

        # Generate text-based topology summary
        topology_summary = self._create_topology_summary(topology_data)

        # Save topology summary
        summary_file = Path(self.config.output_dir) / "topology_summary.txt"
        with open(summary_file, "w") as f:
            f.write(topology_summary)
        visualizations["files"].append(str(summary_file))

        console.print(f"[green]✅ Topology visualizations generated[/green]")

        return visualizations

    def _create_topology_summary(self, topology_data: Dict[str, Any]) -> str:
        """Create a text-based topology summary."""
        summary_lines = [
            "=== Network Topology Summary ===",
            f"Profile: {self.config.profile}",
            f"Region: {self.config.region}",
            f"Generated: {topology_data.get('discovery_timestamp', 'Unknown')}",
            "",
            "=== Network Components ===",
            f"Transit Gateways: {len(topology_data.get('transit_gateways', []))}",
            f"NAT Gateways: {len(topology_data.get('nat_gateways', []))}",
            f"VPC Endpoints: {len(topology_data.get('vpc_endpoints', []))}",
            "",
        ]

        return "\n".join(summary_lines)

    def _generate_topology_recommendations(self, topology_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimization recommendations based on topology analysis.

        Uses topology data to suggest optimizations.
        """
        recommendations = {
            "optimization_opportunities": [],
            "cost_savings": [],
            "security_improvements": [],
            "performance_enhancements": [],
        }

        # Basic recommendations based on discovered components
        tgw_count = len(topology_data.get("transit_gateways", []))
        nat_count = len(topology_data.get("nat_gateways", []))
        endpoint_count = len(topology_data.get("vpc_endpoints", []))

        if nat_count > 2:
            recommendations["cost_savings"].append(
                {
                    "component": "NAT Gateways",
                    "suggestion": f"Consider consolidating {nat_count} NAT Gateways",
                    "potential_savings": "20-40% of NAT Gateway costs",
                }
            )

        if endpoint_count == 0:
            recommendations["cost_savings"].append(
                {
                    "component": "VPC Endpoints",
                    "suggestion": "Consider VPC Endpoints for AWS service access",
                    "potential_savings": "Reduced data transfer costs",
                }
            )

        # Display recommendations using existing formatter
        if recommendations["cost_savings"] or recommendations["optimization_opportunities"]:
            display_optimization_recommendations(console, recommendations)

        return recommendations

    def _export_topology_results(self, topology_results: Dict[str, Any]) -> None:
        """
        Export topology results to various formats.

        Saves results to output directory in multiple formats.
        """
        output_dir = Path(self.config.output_dir)

        # Export JSON results
        json_file = output_dir / "topology_results.json"
        import json

        with open(json_file, "w") as f:
            json.dump(topology_results, f, indent=2, default=str)
        topology_results["output_files"].append(str(json_file))

        console.print(f"[green]✅ Results exported to {self.config.output_dir}[/green]")
