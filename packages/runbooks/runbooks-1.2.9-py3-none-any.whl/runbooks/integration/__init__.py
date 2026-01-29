"""
Integration Module for Runbooks

This module provides integration capabilities for the Runbooks platform,
including Model Context Protocol (MCP) server integration for real-time AWS API
validation and cross-verification of notebook results.

## Core Integration Components

### MCP Integration Framework
- **Real-time AWS API access** via MCP servers
- **Cross-validation engine** for notebook vs API data verification
- **24 MCP server support** across collaboration, analytics, development, and AWS categories
- **Enterprise accuracy validation** with ≥99.5% target accuracy

### Supported MCP Server Categories
- **Collaboration**: GitHub, JIRA, Slack, Teams, Playwright automation
- **Analytics**: Vizro dashboard integration
- **Development**: Terraform, AWS CDK, Knowledge Base, Serverless
- **Extended AWS**: CloudWatch, IAM, CloudTrail, ECS, Lambda, Architecture diagrams

## Usage Examples

```python
from runbooks.integration.mcp_integration import (
    create_enterprise_mcp_framework,
    create_mcp_manager_for_multi_account
)

# Create enterprise MCP framework
framework = create_enterprise_mcp_framework()

# Validate notebook results against MCP servers
validation_report = framework.validate_notebook_results(notebook_data)

# Comprehensive 24-server validation
comprehensive_report = framework.validate_comprehensive_mcp_framework(server_data)
```

## Enterprise Features
- **FAANG SDLC compliance** with enterprise coordination patterns
- **Real-time AWS data validation** for cost optimization and resource discovery
- **Cross-account operations** with multi-profile support
- **Enhanced accuracy validation** for business-critical operations
"""

from runbooks.integration.mcp_integration import (
    # Core integration classes
    MCPIntegrationManager,
    CrossValidationEngine,
    MCPAWSClient,
    MCPValidationError,
    MCPServerEndpoints,
    # Validator classes for different MCP categories
    CollaborationMCPValidator,
    AnalyticsMCPValidator,
    DevelopmentMCPValidator,
    ExtendedAWSMCPValidator,
    # Factory functions for common use cases
    create_mcp_manager_for_single_account,
    create_mcp_manager_for_multi_account,
    create_comprehensive_mcp_validator,
    create_enterprise_mcp_framework,
    create_mcp_server_for_claude_code,
    # Validation and testing functions
    validate_sample_mcp_data,
)

__all__ = [
    # Core integration classes
    "MCPIntegrationManager",
    "CrossValidationEngine",
    "MCPAWSClient",
    "MCPValidationError",
    "MCPServerEndpoints",
    # Validator classes
    "CollaborationMCPValidator",
    "AnalyticsMCPValidator",
    "DevelopmentMCPValidator",
    "ExtendedAWSMCPValidator",
    # Factory functions
    "create_mcp_manager_for_single_account",
    "create_mcp_manager_for_multi_account",
    "create_comprehensive_mcp_validator",
    "create_enterprise_mcp_framework",
    "create_mcp_server_for_claude_code",
    # Validation functions
    "validate_sample_mcp_data",
]
