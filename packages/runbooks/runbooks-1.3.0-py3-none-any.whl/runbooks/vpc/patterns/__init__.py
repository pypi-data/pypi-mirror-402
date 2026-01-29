"""
VPC Pattern Library - Reusable Components for Network Analysis

This module provides base classes and patterns extracted from VPCE cleanup operations
for reuse across VPC, NAT Gateway, ENI, and other network resource analysis workflows.

Patterns:
    - CostExplorerEnricher: AWS Cost Explorer integration for actual cost data
    - AWSResourceValidator: AWS API validation for resource existence
    - CleanupScriptGenerator: Dual-format cleanup script generation (bash + boto3)
    - MarkdownExporter: GitHub-flavored markdown export service
    - OrganizationsEnricher: AWS Organizations account metadata enrichment
    - VPCEnricher: VPC metadata integration (names, CIDRs, resources)
    - CloudTrailActivityAnalyzer: Activity analysis via CloudTrail event history
    - DecisionFramework: Data-driven cleanup priority scoring

Design Principles:
    - KISS: Simple, focused base classes with clear responsibilities
    - DRY: Extract common patterns for reuse across 7 runbooks modules
    - LEAN: 60% code reduction via pattern extraction (3,376 → ~1,200 lines)

Usage:
    from runbooks.vpc.patterns import CostExplorerEnricher

    class MyManager(CostExplorerEnricher):
        def _get_resources_by_account(self):
            return self.resources_by_account

        manager = MyManager()
        result = manager.enrich_with_cost_explorer()
"""

from runbooks.vpc.patterns.cost_explorer_integration import (
    CostEnrichmentResult,
    CostExplorerEnricher,
)
from runbooks.vpc.patterns.aws_validation_integration import (
    ValidationResult,
    AWSResourceValidator,
)
from runbooks.vpc.patterns.cleanup_script_generator import (
    ScriptGenerationResult,
    CleanupScriptGenerator,
)
from runbooks.vpc.patterns.markdown_export_service import (
    MarkdownExportResult,
    MarkdownExporter,
)
from runbooks.vpc.patterns.organizations_enrichment import (
    OrganizationsEnricher,
    OrganizationEnrichmentResult,
)
from runbooks.vpc.patterns.vpc_enrichment import (
    VPCEnricher,
    VPCEnrichmentResult,
)
from runbooks.vpc.patterns.cloudtrail_activity_analysis import (
    CloudTrailActivityAnalyzer,
    ActivityAnalysisResult,
)
from runbooks.vpc.patterns.decision_framework import (
    DecisionFramework,
    DecisionCriteria,
    DecisionScore,
    DecisionPriority,
)

__all__ = [
    "CostEnrichmentResult",
    "CostExplorerEnricher",
    "ValidationResult",
    "AWSResourceValidator",
    "ScriptGenerationResult",
    "CleanupScriptGenerator",
    "MarkdownExportResult",
    "MarkdownExporter",
    "OrganizationsEnricher",
    "OrganizationEnrichmentResult",
    "VPCEnricher",
    "VPCEnrichmentResult",
    "CloudTrailActivityAnalyzer",
    "ActivityAnalysisResult",
    "DecisionFramework",
    "DecisionCriteria",
    "DecisionScore",
    "DecisionPriority",
]
