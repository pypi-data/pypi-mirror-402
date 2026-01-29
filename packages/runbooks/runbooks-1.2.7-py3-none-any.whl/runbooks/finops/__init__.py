"""
CloudOps & FinOps Runbooks Module - Enterprise Cost and Resource Monitoring

This module provides terminal-based AWS cost monitoring with features including:
- Multi-account cost summaries
- Service-level cost breakdown
- Budget monitoring
- EC2 resource status
- Cost trend analysis
- Audit reporting for optimization opportunities

Integrated as a submodule of Runbooks for enterprise FinOps automation.
"""

from pathlib import Path

# Import centralized version from main runbooks package
from runbooks import __version__

# ═══════════════════════════════════════════════════════════════════════════════
# v1.1.31: CENTRALIZED CONSTANTS - Enterprise validation standards
# ═══════════════════════════════════════════════════════════════════════════════

# MCP Validation Accuracy Threshold (≥99.5% = ≤0.5% variance)
# Reference: enterprise-quality-gates.md Section 1A Production-Ready Scoring
MCP_ACCURACY_THRESHOLD: float = 99.5  # Percentage (not decimal)
MCP_VARIANCE_THRESHOLD: float = 0.5  # Maximum allowable variance percentage

# Evidence Directory Path (relative to project root)
# v1.1.31: All validation evidence must be stored here for audit compliance
EVIDENCE_BASE_DIR: Path = Path("artifacts/evidence")

# Temporary output directory (for non-audit outputs)
TEMP_OUTPUT_DIR: Path = Path("/tmp/runbooks")


def get_evidence_dir(module: str = "finops") -> Path:
    """
    Get evidence directory path for a specific module.

    v1.1.31: Centralized evidence path resolution for audit compliance.
    Creates directory if it doesn't exist.

    Args:
        module: Module name (e.g., 'finops', 'security', 'inventory')

    Returns:
        Path to evidence directory

    Example:
        >>> evidence_path = get_evidence_dir("finops")
        >>> evidence_path.mkdir(parents=True, exist_ok=True)
    """
    evidence_dir = EVIDENCE_BASE_DIR / module
    evidence_dir.mkdir(parents=True, exist_ok=True)
    return evidence_dir


# Core components
# AWS client utilities
from runbooks.finops.aws_client import (
    ec2_summary,
    get_accessible_regions,
    get_account_id,
    get_aws_profiles,
    get_budgets,
    get_stopped_instances,
    get_untagged_resources,
    get_unused_eips,
    get_unused_volumes,
)

# Data processors
from runbooks.finops.cost_processor import export_to_csv, export_to_json, get_cost_data, get_trend

# Enterprise FinOps Dashboard Components (v1.1.28+)
# Mode separation: dashboard_single.py (--profile) vs dashboard_multi.py (--all-profile)
from runbooks.finops.dashboard_single import (
    run_single_account_dashboard,
    run_audit_report,
    run_trend_analysis,
    calculate_business_case,
)
from runbooks.finops.dashboard_multi import (
    run_multi_account_dashboard,
    get_organization_wide_costs,
    run_multi_account_audit,
    run_multi_account_trends,
)

# Enhanced helpers with notebook integration functions
from runbooks.finops.helpers import (
    create_business_summary_table,
    create_roi_analysis_table,
    export_audit_report_to_csv,
    export_audit_report_to_json,
    export_audit_report_to_pdf,
    export_cost_dashboard_to_pdf,
    export_scenarios_to_notebook_html,
    export_trend_data_to_json,
    # NOTEBOOK INTEGRATION FUNCTIONS - Added for clean notebook consumption
    format_currency,
    load_config_file,
)
from runbooks.finops.profile_processor import process_combined_profiles, process_single_profile

# Business scenarios with notebook integration
# NEW latest version: Clean API wrapper for notebook consumption
from runbooks.finops.scenarios import (
    UnifiedScenarioManager,  # Replaces FinOpsBusinessScenarios
    create_business_scenarios_validated,
    display_unlimited_scenarios_help,  # CLI help function
    finops_23_rds_snapshots_optimization,
    # Legacy aliases for backward compatibility
    finops_24_workspaces_cleanup,
    finops_25_commvault_investigation,
    finops_commvault,
    finops_snapshots,
    finops_workspaces,
    format_for_audience,  # Consolidated function replaces format_for_business_audience and format_for_technical_audience
    get_business_scenarios_summary,
    validate_finops_mcp_accuracy,
)

# Type definitions
from runbooks.finops.types import BudgetInfo, CostData, EC2Summary, ProfileData, RegionName

# Visualization and export
from runbooks.finops.visualisations import create_trend_bars

# NEW: Reusable Enrichment APIs for notebooks (Track 1-3 implementation)
from runbooks.finops.ec2_enrichment import (
    analyze_ec2_cloudtrail,
    enrich_with_ec2_context,
    get_ec2_cost_data,
)
from runbooks.finops.workspaces_enrichment import (
    analyze_workspaces_cloudtrail,
    enrich_with_workspaces_context,
    get_workspaces_cost_data,
)

# NEW: Decommission Classification Framework (Track 4-5 implementation)
from runbooks.finops.decommission_classifier import classify_ec2, classify_workspaces

# NEW: Cost Visualization APIs - Rich Tree hierarchies (Track 2 implementation)
from runbooks.finops.cost_visualization import (
    display_cost_comparison_table,
    display_ec2_cost_tree,
    display_workspaces_cost_tree,
)

# NEW: WorkSpaces Signals - W2-W6 Explicit Validation Functions
from runbooks.finops.workspaces_signals import (
    get_w2_cloudwatch_sessions,
    calculate_w3_breakeven_dynamic,
    check_w4_autostop_policy,
    analyze_w5_admin_activity,
    validate_w6_user_status,
)

# NEW: Base Enrichers - Reusable patterns for EC2/WorkSpaces enrichment
from runbooks.finops.base_enrichers import (
    OrganizationsEnricher,
    CostExplorerEnricher,
    CloudTrailEnricher,
    StoppedStateEnricher,
    format_tags_combined,
)

# NEW: Lambda Cost Analyzer - Serverless optimization (Track B implementation)
from runbooks.finops.lambda_analyzer import (
    analyze_lambda_costs,
    LambdaCostAnalyzer,
    LambdaAnalysisConfig,
)

# NEW: Graviton Migration Analyzer - ARM64 eligibility assessment (Epic 4 Feature 2)
from runbooks.finops.graviton_migration_analyzer import (
    analyze_graviton_eligibility,
    GravitonMigrationAnalyzer,
    GravitonAnalysisConfig,
    GravitonEligibility,
    GRAVITON_MAPPINGS,
)

# NEW: RI Utilization Tracker - Reserved Instance waste detection (Epic 4 Feature 6)
from runbooks.finops.ri_utilization_tracker import (
    track_ri_utilization,
    RIUtilizationTracker,
    RIUtilizationReport,
    Alert as RIAlert,
)

# NEW: Cost Anomaly Detector - Cost spike detection with root cause analysis (Epic 4 Feature 7)
from runbooks.finops.cost_anomaly_detector import (
    detect_cost_anomalies,
    CostAnomalyDetector,
    Anomaly,
    RootCauseAnalysis,
)

# NEW: RDS RI Optimizer - Database Reserved Instance procurement (Feature 14, $75K savings)
from runbooks.finops.rds_ri_optimizer import (
    RDSRIOptimizer,
    RDSRIOptimizerResults,
    RDSRIRecommendation,
)

# NEW: Lambda Cost Attribution - Serverless cost allocation (Feature 15, $40K savings)
from runbooks.finops.lambda_cost_attribution import (
    LambdaCostAttributionEngine,
    LambdaCostAttributionResults,
    LambdaOptimizationRecommendation,
)

# NEW: EBS Rightsizing Analyzer - IOPS optimization (Feature 16, $30K savings)
from runbooks.finops.ebs_rightsizing import (
    EBSRightsizingAnalyzer,
    EBSRightsizingResults,
    EBSRightsizingRecommendation,
)

# NEW: MCP Hybrid Intelligence Engine - Phase 4 P0 Critical Feature ($2M value)
from runbooks.finops.hybrid_mcp_engine import (
    HybridMCPEngine,
    MCPValidationResult,
    BatchValidationReport,
    ValidationSource,
    ValidationStatus,
    create_hybrid_mcp_engine,
    MCP_AVAILABLE,
)

# v1.1.31: Validation Orchestrator - Central MCP validation coordination
from runbooks.finops.validation_orchestrator import (
    ValidationOrchestrator,
    ServiceValidationResult,
    OrchestratorResults,
    create_validation_orchestrator,
)

# v1.1.31: S3 4-Way Validation Chain
from runbooks.finops.s3_mcp_validator import (
    S3MCPValidator,
    ValidationResults as S3ValidationResults,
)

# v1.2.1: Cross-Validation (AWS Console CSV vs Cost Explorer API)
from runbooks.finops.cross_validation import (
    CrossValidator,
    CrossValidationReport,
    ServiceComparison,
    save_report as save_cross_validation_report,
)

# v1.2.0: FOCUS 1.3 Multi-Cloud Cost Normalization (migrated from Cloud-Infrastructure)
from runbooks.finops.focus import (
    FocusNormalizer,
    CostAggregator,
    ExcelFormatter,
    create_finops_excel_report,
    FOCUS_1_3_SCHEMA,
    FOCUS_REQUIRED_COLUMNS,
)

# v1.2.0: Azure FinOps Extension (migrated from Cloud-Infrastructure)
from runbooks.finops.azure import (
    AzureCostReport,
    AzureReportConfig,
    AzureCostData,
    AzureServiceCost,
    AzureSubscriptionCost,
    process_azure_cost_data,
)

# NEW: Enrichers and Scorers - Direct exports (consolidating enrichers/ and scorers/ subdirectories)
# EC2 enrichers
from runbooks.finops.ec2_enrichment import (
    enrich_with_ec2_context,
    analyze_ec2_cloudtrail,
    get_ec2_cost_data,
)

# WorkSpaces enrichers
from runbooks.finops.workspaces_enrichment import (
    enrich_with_workspaces_context,
    analyze_workspaces_cloudtrail,
    get_workspaces_cost_data,
)

# Decommission scorers
from runbooks.finops.decommission_scorer import (
    calculate_ec2_score,
    calculate_workspaces_score,
    score_ec2_dataframe,
    score_workspaces_dataframe,
    display_scoring_summary,
    export_scores_to_dataframe,
    display_tier_distribution,
    calculate_production_ready_score,
)

__all__ = [
    # Core functionality
    # NOTE: run_dashboard, run_complete_finops_workflow removed in v1.1.28+
    # Use dashboard_multi.py, dashboard_single.py directly
    # Enterprise FinOps Dashboard Functions
    # NOTE: _run_* functions removed with dashboard_runner.py archival (v1.1.28+)
    # Enterprise Dashboard Classes - backward compatibility
    # NOTE: FinOpsConfig moved to dashboard_multi.py (v1.1.28+)
    # Business scenarios with notebook integration (consolidated version)
    "create_business_scenarios_validated",
    "format_for_audience",  # Consolidated function
    "UnifiedScenarioManager",  # Consolidated class
    # NEW latest version: Clean API wrapper functions (cleaned naming)
    "finops_workspaces",
    "finops_snapshots",
    "finops_commvault",
    # Legacy aliases (deprecated)
    "finops_24_workspaces_cleanup",
    "finops_23_rds_snapshots_optimization",
    "finops_25_commvault_investigation",
    "get_business_scenarios_summary",
    "format_for_audience",
    "validate_finops_mcp_accuracy",  # Updated function name in consolidated version
    "display_unlimited_scenarios_help",  # CLI help function
    # Processors
    "get_cost_data",
    "get_trend",
    "process_single_profile",
    "process_combined_profiles",
    # AWS utilities
    "get_aws_profiles",
    "get_account_id",
    "get_accessible_regions",
    "ec2_summary",
    "get_stopped_instances",
    "get_unused_volumes",
    "get_unused_eips",
    "get_untagged_resources",
    "get_budgets",
    # Visualization and export
    "create_trend_bars",
    "export_to_csv",
    "export_to_json",
    "export_audit_report_to_pdf",
    "export_cost_dashboard_to_pdf",
    "export_audit_report_to_csv",
    "export_audit_report_to_json",
    "export_trend_data_to_json",
    "load_config_file",
    # NOTEBOOK INTEGRATION FUNCTIONS (latest version)
    "format_currency",
    "create_business_summary_table",
    "export_scenarios_to_notebook_html",
    "create_roi_analysis_table",
    # Types
    "ProfileData",
    "CostData",
    "BudgetInfo",
    "EC2Summary",
    "RegionName",
    # NEW: Reusable Enrichment APIs (Track 1-3)
    "enrich_with_ec2_context",
    "analyze_ec2_cloudtrail",
    "get_ec2_cost_data",
    "enrich_with_workspaces_context",
    "analyze_workspaces_cloudtrail",
    "get_workspaces_cost_data",
    # NEW: Decommission Classification Framework (Track 4-5)
    "classify_ec2",
    "classify_workspaces",
    # NEW: Cost Visualization APIs - Rich Tree hierarchies (Track 2)
    "display_ec2_cost_tree",
    "display_workspaces_cost_tree",
    "display_cost_comparison_table",
    # NEW: WorkSpaces Signals - W2-W6 Explicit Validation Functions
    "get_w2_cloudwatch_sessions",
    "calculate_w3_breakeven_dynamic",
    "check_w4_autostop_policy",
    "analyze_w5_admin_activity",
    "validate_w6_user_status",
    # NEW: Base Enrichers - Reusable patterns
    "OrganizationsEnricher",
    "CostExplorerEnricher",
    "CloudTrailEnricher",
    "StoppedStateEnricher",
    "format_tags_combined",
    # NEW: Lambda Cost Analyzer - Serverless optimization
    "analyze_lambda_costs",
    "LambdaCostAnalyzer",
    "LambdaAnalysisConfig",
    # NEW: Graviton Migration Analyzer - ARM64 eligibility
    "analyze_graviton_eligibility",
    "GravitonMigrationAnalyzer",
    "GravitonAnalysisConfig",
    "GravitonEligibility",
    "GRAVITON_MAPPINGS",
    # NEW: RI Utilization Tracker - Reserved Instance waste detection (Feature 6)
    "track_ri_utilization",
    "RIUtilizationTracker",
    "RIUtilizationReport",
    "RIAlert",
    # NEW: Cost Anomaly Detector - Cost spike detection (Feature 7)
    "detect_cost_anomalies",
    "CostAnomalyDetector",
    "Anomaly",
    "RootCauseAnalysis",
    # NEW: RDS RI Optimizer - Database RI procurement (Feature 14)
    "RDSRIOptimizer",
    "RDSRIOptimizerResults",
    "RDSRIRecommendation",
    # NEW: Lambda Cost Attribution - Serverless cost allocation (Feature 15)
    "LambdaCostAttributionEngine",
    "LambdaCostAttributionResults",
    "LambdaOptimizationRecommendation",
    # NEW: EBS Rightsizing Analyzer - IOPS optimization (Feature 16)
    "EBSRightsizingAnalyzer",
    "EBSRightsizingResults",
    "EBSRightsizingRecommendation",
    # NEW: MCP Hybrid Intelligence Engine - Phase 4 P0 Critical Feature
    "HybridMCPEngine",
    "MCPValidationResult",
    "BatchValidationReport",
    "ValidationSource",
    "ValidationStatus",
    "create_hybrid_mcp_engine",
    "MCP_AVAILABLE",
    # v1.1.31: Validation Orchestrator - Central MCP validation
    "ValidationOrchestrator",
    "ServiceValidationResult",
    "OrchestratorResults",
    "create_validation_orchestrator",
    # v1.1.31: S3 4-Way Validation Chain
    "S3MCPValidator",
    "S3ValidationResults",
    # v1.2.1: Cross-Validation (AWS Console CSV vs Cost Explorer API)
    "CrossValidator",
    "CrossValidationReport",
    "ServiceComparison",
    "save_cross_validation_report",
    # NEW: Decommission Scorers (consolidated from scorers/ subdirectory)
    "calculate_ec2_score",
    "calculate_workspaces_score",
    "score_ec2_dataframe",
    "score_workspaces_dataframe",
    "display_scoring_summary",
    "export_scores_to_dataframe",
    "display_tier_distribution",
    "calculate_production_ready_score",
    # Metadata
    "__version__",
    # v1.1.31: Centralized constants for enterprise validation
    "MCP_ACCURACY_THRESHOLD",
    "MCP_VARIANCE_THRESHOLD",
    "EVIDENCE_BASE_DIR",
    "TEMP_OUTPUT_DIR",
    "get_evidence_dir",
    # v1.2.0: FOCUS 1.3 Multi-Cloud Cost Normalization
    "FocusNormalizer",
    "CostAggregator",
    "ExcelFormatter",
    "create_finops_excel_report",
    "FOCUS_1_3_SCHEMA",
    "FOCUS_REQUIRED_COLUMNS",
    # v1.2.0: Azure FinOps Extension
    "AzureCostReport",
    "AzureReportConfig",
    "AzureCostData",
    "AzureServiceCost",
    "AzureSubscriptionCost",
    "process_azure_cost_data",
]
