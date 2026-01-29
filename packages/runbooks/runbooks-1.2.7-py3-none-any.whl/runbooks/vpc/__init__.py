"""
VPC Networking Operations Module

This module provides comprehensive VPC networking analysis and optimization capabilities
with support for both CLI and Jupyter notebook interfaces using Rich for beautiful outputs.

Key Components:
- VPCNetworkingWrapper: Main interface for all VPC operations
- VPCManagerInterface: Business-friendly interface for non-technical users
- NetworkingCostEngine: Cost analysis and optimization engine
- NetworkingCostHeatMapEngine: Heat map generation for cost visualization
- Rich formatters: Consistent, beautiful output formatting

Usage:
    CLI: runbooks vpc analyze --profile aws-profile
    Jupyter: from runbooks.vpc import VPCNetworkingWrapper
    Manager Dashboard: from runbooks.vpc import VPCManagerInterface
"""

from .cost_engine import NetworkingCostEngine
from .heatmap_engine import NetworkingCostHeatMapEngine
from .manager_interface import BusinessRecommendation, ManagerDashboardConfig, VPCManagerInterface
from .networking_wrapper import VPCNetworkingWrapper
from .rich_formatters import display_cost_table, display_heatmap, display_optimization_recommendations
from .vpc_cleanup_integration import VPCCleanupFramework, VPCCleanupCandidate, VPCCleanupRisk, VPCCleanupPhase
from .cleanup_wrapper import (
    VPCCleanupCLI,
    analyze_cleanup_candidates,
    validate_cleanup_safety,
    generate_business_report,
)
from .runbooks_adapter import RunbooksAdapter
from .nat_gateway_optimizer import NATGatewayOptimizer

# Phase 3 P2: VPC Network Optimization Features (Features 11-13, $180K value)
from .nat_to_vpce_migration import (
    NATtoVPCEMigrationWorkflow,
    MigrationCandidate,
    MigrationPlan,
    MigrationComplexity,
    MigrationStatus,
    create_nat_to_vpce_migration_workflow,
)
from .peering_cost_analyzer import (
    VPCPeeringCostAnalyzer,
    PeeringAnalysis,
    PeeringRecommendation,
    create_peering_cost_analyzer,
)
from .tgw_optimizer import (
    TransitGatewayOptimizer,
    TGWAttachmentAnalysis,
    AttachmentType,
    OptimizationRecommendation,
    create_tgw_optimizer,
)

# Phase 6 Feature 1: VPC Endpoint Dependency Mapper (Critical Workload Protection)
from .endpoint_dependency_mapper import (
    VPCEndpointDependencyMapper,
    EndpointDependencyAnalysis,
    ResourceDependency,
    DependencyRisk,
    DependencySignal,
    create_endpoint_dependency_mapper,
)

# v1.1.29: VPC Flow Logs Analyzer (V6/N6 signals)
from .flow_logs_analyzer import (
    VPCFlowLogsAnalyzer,
    FlowLogTrafficResult,
    SecurityGroupTrafficResult,
    create_flow_logs_analyzer,
)

# v1.1.29: Network Insights Client (V9/V10 signals)
from .network_insights_client import (
    NetworkInsightsClient,
    NetworkPathAnalysisResult,
    MultiRegionEndpointAnalysis,
    NetworkPathStatus,
    create_network_insights_client,
)

__all__ = [
    "VPCNetworkingWrapper",
    "VPCManagerInterface",
    "BusinessRecommendation",
    "ManagerDashboardConfig",
    "NetworkingCostEngine",
    "NetworkingCostHeatMapEngine",
    "display_cost_table",
    "display_heatmap",
    "display_optimization_recommendations",
    "VPCCleanupFramework",
    "VPCCleanupCandidate",
    "VPCCleanupRisk",
    "VPCCleanupPhase",
    "VPCCleanupCLI",
    "analyze_cleanup_candidates",
    "validate_cleanup_safety",
    "generate_business_report",
    "RunbooksAdapter",
    "NATGatewayOptimizer",
    # Phase 3 P2 Features
    "NATtoVPCEMigrationWorkflow",
    "MigrationCandidate",
    "MigrationPlan",
    "MigrationComplexity",
    "MigrationStatus",
    "create_nat_to_vpce_migration_workflow",
    "VPCPeeringCostAnalyzer",
    "PeeringAnalysis",
    "PeeringRecommendation",
    "create_peering_cost_analyzer",
    "TransitGatewayOptimizer",
    "TGWAttachmentAnalysis",
    "AttachmentType",
    "OptimizationRecommendation",
    "create_tgw_optimizer",
    # Phase 6 Feature 1
    "VPCEndpointDependencyMapper",
    "EndpointDependencyAnalysis",
    "ResourceDependency",
    "DependencyRisk",
    "DependencySignal",
    "create_endpoint_dependency_mapper",
    # v1.1.29: VPC Flow Logs Analyzer
    "VPCFlowLogsAnalyzer",
    "FlowLogTrafficResult",
    "SecurityGroupTrafficResult",
    "create_flow_logs_analyzer",
    # v1.1.29: Network Insights Client
    "NetworkInsightsClient",
    "NetworkPathAnalysisResult",
    "MultiRegionEndpointAnalysis",
    "NetworkPathStatus",
    "create_network_insights_client",
]

# Import centralized version from main runbooks package
from runbooks import __version__
