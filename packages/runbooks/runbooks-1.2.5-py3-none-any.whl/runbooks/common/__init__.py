"""
Runbooks Common Framework - Universal Foundation

This module provides the foundational universal framework components
that work with ANY AWS setup without hardcoded assumptions.

Components:
- rich_utils: Beautiful CLI formatting with CloudOps theme
- profile_utils: Universal AWS profile management (User → AWS_PROFILE → default)
- date_utils: Dynamic date generation utilities (No hardcoded dates)
- performance_monitor: Enterprise-grade performance benchmarking
- context_logger: Context-aware logging for CLI and Jupyter
- mcp_integration: Phase 4 MCP Integration Framework (NEW)
- cross_module_integration: Phase 4 Cross-Module Data Flow (NEW)
- enterprise_audit_integration: Phase 4 Enterprise Audit Framework (NEW)

Version: 1.0.0 - Universal Compatibility Update
"""

# Rich CLI utilities (CloudOps theme, console, formatting)
# AWS client factory utilities (Session caching and client creation)
from .aws_client_factory import (
    AWSClientFactory,
    create_cloudwatch_client,
    create_cost_explorer_client,
    create_ec2_client,
    create_lambda_client,
    create_rds_client,
    create_s3_client,
    create_workspaces_client,
)

# Cost Explorer client utilities (Cost API wrapper)
from .cost_explorer_client import CostExplorerClient

# Dynamic date utilities (No hardcoded dates)
# ADLC v3.0.0: Added DateRange and DateRangeCalculator for DRY compliance
from .date_utils import (
    DateRange,
    DateRangeCalculator,
    get_aws_cli_example_period,
    get_collection_timestamp,
    get_current_month_period,
    get_current_year,
    get_previous_month_period,
    get_test_date_period,
)

# Export utilities (Multi-format data export)
from .export import DataFrameExporter, ExportEngine, export_to_formats

# Phase 4: Cross-Module Integration (Data Flow Architecture)
from .cross_module_integration import (
    DataFlowContext,
    DataFlowResult,
    DataFlowType,
    EnterpriseCrossModuleIntegrator,
)

# Phase 4: Enterprise Audit Integration (Compliance Framework)
from .enterprise_audit_integration import (
    AuditEvent,
    AuditSeverity,
    ComplianceFramework,
    ComplianceReport,
    EnterpriseAuditIntegrator,
)

# Phase 4: MCP Integration Framework (Multi-Module MCP)
from .mcp_integration import (
    EnterpriseMCPIntegrator,
    MCPOperationType,
    MCPValidationResult,
)

# Performance monitoring framework (Enterprise benchmarking)
from .performance_monitor import (
    ModulePerformanceConfig,
    PerformanceBenchmark,
    PerformanceMetrics,
    create_enterprise_performance_report,
    get_performance_benchmark,
)

# Profile management utilities (Universal AWS profile system)
from .profile_utils import (
    create_cost_session,
    create_management_session,
    create_operational_session,
    get_current_profile_info,
    get_profile_for_operation,
    resolve_profile_for_operation_silent,
    validate_profile_access,
)
from .rich_utils import (
    CLOUDOPS_THEME,
    STATUS_INDICATORS,
    confirm_action,
    console,
    create_columns,
    create_display_profile_name,
    create_layout,
    create_panel,
    create_progress_bar,
    create_table,
    create_tree,
    format_account_name,
    format_cost,
    format_profile_name,
    format_resource_count,
    get_console,
    get_context_aware_console,
    print_banner,
    print_error,
    print_header,
    print_info,
    print_json,
    print_markdown,
    print_separator,
    print_status,
    print_success,
    print_warning,
)

__all__ = [
    # Rich CLI utilities
    "CLOUDOPS_THEME",
    "STATUS_INDICATORS",
    "console",
    "get_console",
    "get_context_aware_console",
    "print_header",
    "print_banner",
    "create_table",
    "create_progress_bar",
    "print_status",
    "print_error",
    "print_success",
    "print_warning",
    "print_info",
    "create_tree",
    "print_separator",
    "create_panel",
    "format_cost",
    "format_resource_count",
    "create_display_profile_name",
    "format_profile_name",
    "format_account_name",
    "create_layout",
    "print_json",
    "print_markdown",
    "confirm_action",
    "create_columns",
    # AWS client factory utilities
    "AWSClientFactory",
    "create_cost_explorer_client",
    "create_ec2_client",
    "create_rds_client",
    "create_s3_client",
    "create_cloudwatch_client",
    "create_lambda_client",
    "create_workspaces_client",
    # Cost Explorer client utilities
    "CostExplorerClient",
    # Export utilities
    "DataFrameExporter",
    "ExportEngine",
    "export_to_formats",
    # Dynamic date utilities
    "DateRange",
    "DateRangeCalculator",
    "get_current_year",
    "get_current_month_period",
    "get_previous_month_period",
    "get_test_date_period",
    "get_aws_cli_example_period",
    "get_collection_timestamp",
    # Profile management utilities
    "get_profile_for_operation",
    "resolve_profile_for_operation_silent",
    "create_cost_session",
    "create_management_session",
    "create_operational_session",
    "get_current_profile_info",
    "validate_profile_access",
    # Performance monitoring framework
    "PerformanceMetrics",
    "ModulePerformanceConfig",
    "PerformanceBenchmark",
    "get_performance_benchmark",
    "create_enterprise_performance_report",
    # Phase 4: MCP Integration Framework
    "EnterpriseMCPIntegrator",
    "MCPOperationType",
    "MCPValidationResult",
    # Phase 4: Cross-Module Integration
    "EnterpriseCrossModuleIntegrator",
    "DataFlowType",
    "DataFlowContext",
    "DataFlowResult",
    # Phase 4: Enterprise Audit Integration
    "EnterpriseAuditIntegrator",
    "ComplianceFramework",
    "AuditSeverity",
    "AuditEvent",
    "ComplianceReport",
]
