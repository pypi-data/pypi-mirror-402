# =============================================================================
# MCP Validation Constants
# =============================================================================
# ADLC v3.0.0 - Constitutional Thresholds and Tolerances
# =============================================================================

"""Constants for MCP validation framework."""

import os
from pathlib import Path
from typing import Final

# =============================================================
# ADLC Constitutional Thresholds
# =============================================================

# Minimum accuracy required for validation pass (99.5%)
ACCURACY_TARGET: Final[float] = 99.5

# Maximum PDCA cycles before human escalation (CHK041)
MAX_PDCA_CYCLES: Final[int] = 7

# =============================================================
# Comparison Tolerances
# =============================================================

# Financial field tolerance (0.01% for cost comparisons)
FINANCIAL_TOLERANCE: Final[float] = 0.0001  # 0.01%

# Response time tolerance (+/- 50% from baseline)
RESPONSE_TIME_TOLERANCE: Final[float] = 0.5  # 50%

# =============================================================
# Evidence Paths (Project-Agnostic)
# =============================================================

# Default evidence directory pattern
EVIDENCE_DIR: Final[str] = "tmp/{project}/test-results"
COORDINATION_DIR: Final[str] = "tmp/{project}/coordination-logs"


def get_evidence_dir(project: str | None = None) -> str:
    """Get evidence directory for a project.

    Args:
        project: Project name (auto-detected from cwd if None)

    Returns:
        Evidence directory path string
    """
    if project is None:
        # Auto-detect project from current working directory
        cwd = Path.cwd()
        project = cwd.name.lower().replace("_", "-")
    return EVIDENCE_DIR.format(project=project)


def get_coordination_dir(project: str | None = None) -> str:
    """Get coordination logs directory for a project.

    Args:
        project: Project name (auto-detected from cwd if None)

    Returns:
        Coordination logs directory path string
    """
    if project is None:
        cwd = Path.cwd()
        project = cwd.name.lower().replace("_", "-")
    return COORDINATION_DIR.format(project=project)


# =============================================================
# MCP Server Categories
# =============================================================

# Priority 0 - Critical AWS MCPs (must validate first)
P0_AWS_SERVERS: Final[list[str]] = [
    "awslabs-organizations",
    "awslabs-cost-explorer",
]

# Priority 1 - Important AWS MCPs
P1_AWS_SERVERS: Final[list[str]] = [
    "awslabs-identity-center",
    "awslabs-control-tower",
    "awslabs-security-hub",
    "awslabs-config",
]

# Priority 2 - Azure MCPs
P2_AZURE_SERVERS: Final[list[str]] = [
    "azure-resource-manager",
    "azure-cost-management",
    "azure-policy",
    "azure-security-center",
    "azure-entra",
]

# Priority 3 - FinOps MCPs
P3_FINOPS_SERVERS: Final[list[str]] = [
    "finops-focus-aggregator",
    "infracost",
    "kubecost",
]

# All servers by category
ALL_AWS_SERVERS: Final[list[str]] = P0_AWS_SERVERS + P1_AWS_SERVERS
ALL_AZURE_SERVERS: Final[list[str]] = P2_AZURE_SERVERS
ALL_FINOPS_SERVERS: Final[list[str]] = P3_FINOPS_SERVERS

# =============================================================
# Profile Mapping (MCP Server -> AWS Profile)
# =============================================================

MCP_PROFILE_MAPPING: Final[dict[str, str]] = {
    # Management profile servers
    "awslabs-organizations": "AWS_MANAGEMENT_PROFILE",
    "awslabs-identity-center": "AWS_MANAGEMENT_PROFILE",
    "awslabs-control-tower": "AWS_MANAGEMENT_PROFILE",
    # Billing profile servers
    "awslabs-cost-explorer": "AWS_BILLING_PROFILE",
    # Operations profile servers
    "awslabs-security-hub": "AWS_OPERATIONS_PROFILE",
    "awslabs-config": "AWS_OPERATIONS_PROFILE",
}

# =============================================================
# Native CLI Commands (for cross-validation)
# =============================================================

NATIVE_CLI_COMMANDS: Final[dict[str, str]] = {
    "awslabs-organizations": "aws organizations list-accounts",
    "awslabs-cost-explorer": "aws ce get-cost-and-usage",
    "awslabs-identity-center": "aws sso-admin list-instances",
    "awslabs-control-tower": "aws controltower list-enabled-controls",
    "awslabs-security-hub": "aws securityhub describe-hub",
    "awslabs-config": "aws configservice describe-configuration-recorders",
    "azure-resource-manager": "az resource list",
    "azure-cost-management": "az costmanagement query",
}

# =============================================================
# Timeouts
# =============================================================

# Default timeout for API calls (seconds)
DEFAULT_TIMEOUT: Final[int] = 30

# Extended timeout for cost queries (seconds)
COST_QUERY_TIMEOUT: Final[int] = 60

# =============================================================
# Rate Limiting
# =============================================================

# Minimum delay between API calls (seconds)
MIN_API_DELAY: Final[float] = 0.5

# Maximum retry attempts
MAX_RETRIES: Final[int] = 3

# Exponential backoff base (seconds)
BACKOFF_BASE: Final[float] = 1.0

# Maximum backoff (seconds)
MAX_BACKOFF: Final[float] = 60.0
