# =============================================================================
# MCP Cross-Validation Framework
# =============================================================================
# ADLC v3.0.0 - Constitutional Checkpoint CHK027 (Evidence Requirements)
#
# Cross-validates MCP server outputs against native AWS/Azure CLI APIs
# with >= 99.5% accuracy target.
#
# Usage (via runbooks package):
#   runbooks-mcp validate aws
#   runbooks-mcp validate --all
#   runbooks-mcp pdca aws --max-cycles 7
#
# Migration Note:
#   This module was migrated from cloud-infrastructure to runbooks
#   for cross-project reusability (ADLC Producer/Consumer pattern).
# =============================================================================

"""MCP Cross-Validation Framework for ADLC compliance.

This module provides cross-validation capabilities for MCP servers against
native AWS/Azure CLI APIs, ensuring >= 99.5% data accuracy.

Key Components:
    - core: Constants, exceptions, and Pydantic types
    - validators: AWS, Azure, and FinOps validators
    - comparators: Field and financial comparison utilities
    - evidence: Constitutional evidence file generation
    - cli: Typer-based CLI interface
"""

__version__ = "0.1.0"
__adlc_version__ = "3.0.0"
__migrated_from__ = "cloud-infrastructure"

from .comparators import (
    FieldComparator,
    FinancialComparator,
)
from .core import (
    ACCURACY_TARGET,
    FINANCIAL_TOLERANCE,
    MAX_PDCA_CYCLES,
    MCPAccuracyError,
    MCPConfigError,
    MCPTimeoutError,
    MCPValidationError,
    MCPValidationReport,
    ProfileMapping,
    ServerValidationResult,
    ValidationResult,
    ValidationStatus,
)
from .evidence import EvidenceGenerator
from .validators import (
    AWSConfigValidator,
    AWSControlTowerValidator,
    AWSCostExplorerValidator,
    AWSIdentityCenterValidator,
    # AWS Validators (P0-P1)
    AWSOrganizationsValidator,
    AWSSecurityHubValidator,
    # Azure Validators (P2)
    AzureBaseValidator,
    AzureCostManagementValidator,
    AzureEntraValidator,
    AzurePolicyValidator,
    AzureResourceManagerValidator,
    AzureSecurityCenterValidator,
    BaseValidator,
    # FinOps Validators (P3)
    FOCUSAggregatorValidator,
    InfracostValidator,
    KubecostValidator,
)

__all__ = [
    # Version info
    "__version__",
    "__adlc_version__",
    # Constants
    "ACCURACY_TARGET",
    "FINANCIAL_TOLERANCE",
    "MAX_PDCA_CYCLES",
    # Exceptions
    "MCPValidationError",
    "MCPAccuracyError",
    "MCPTimeoutError",
    "MCPConfigError",
    # Types
    "ValidationResult",
    "ServerValidationResult",
    "MCPValidationReport",
    "ValidationStatus",
    "ProfileMapping",
    # Validators (AWS P0-P1)
    "BaseValidator",
    "AWSOrganizationsValidator",
    "AWSCostExplorerValidator",
    "AWSSecurityHubValidator",
    "AWSIdentityCenterValidator",
    "AWSControlTowerValidator",
    "AWSConfigValidator",
    # Validators (Azure P2)
    "AzureBaseValidator",
    "AzureResourceManagerValidator",
    "AzureCostManagementValidator",
    "AzurePolicyValidator",
    "AzureSecurityCenterValidator",
    "AzureEntraValidator",
    # Validators (FinOps P3)
    "FOCUSAggregatorValidator",
    "InfracostValidator",
    "KubecostValidator",
    # Comparators
    "FieldComparator",
    "FinancialComparator",
    # Evidence
    "EvidenceGenerator",
]
