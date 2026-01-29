"""
MCP (Model Context Protocol) Integration Module

Enhanced MCP server integration for AWS API access with enterprise-grade
error handling, Rich CLI formatting, and ≥99.5% accuracy validation.

Key Components:
- MCPIntegrationManager: Main integration orchestrator
- CrossValidationEngine: Data accuracy validation
- MCPAWSClient: AWS API access via MCP
- Enhanced decimal conversion with error handling

Submodules:
- validation: MCP Cross-Validation Framework (CHK027)
  Cross-validates MCP server outputs against native AWS/Azure CLI APIs
  with >= 99.5% accuracy target for ADLC constitutional compliance.
"""

from .integration import (
    MCPIntegrationManager,
    CrossValidationEngine,
    MCPAWSClient,
    MCPValidationError,
    MCPServerEndpoints,
    create_mcp_manager_for_single_account,
    create_mcp_manager_for_multi_account,
    create_mcp_server_for_claude_code,
    _safe_decimal_conversion,
)

# Lazy import validation submodule to avoid circular imports
# Use: from runbooks.mcp.validation import ...
# Or:  from runbooks.mcp import validation

__all__ = [
    # Integration components
    "MCPIntegrationManager",
    "CrossValidationEngine",
    "MCPAWSClient",
    "MCPValidationError",
    "MCPServerEndpoints",
    "create_mcp_manager_for_single_account",
    "create_mcp_manager_for_multi_account",
    "create_mcp_server_for_claude_code",
    "_safe_decimal_conversion",
    # Validation submodule (available as runbooks.mcp.validation)
    "validation",
]
