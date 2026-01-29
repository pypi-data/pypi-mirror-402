# =============================================================================
# MCP Validation Core Module
# =============================================================================

"""Core components for MCP validation framework."""

from .constants import (
    ACCURACY_TARGET,
    EVIDENCE_DIR,
    FINANCIAL_TOLERANCE,
    MAX_PDCA_CYCLES,
    get_evidence_dir,
)
from .exceptions import (
    MCPAccuracyError,
    MCPAuthenticationError,
    MCPComparisonError,
    MCPConfigError,
    MCPTimeoutError,
    MCPValidationError,
)
from .types import (
    FieldComparison,
    MCPValidationReport,
    ProfileMapping,
    ServerValidationResult,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    # Constants
    "ACCURACY_TARGET",
    "FINANCIAL_TOLERANCE",
    "MAX_PDCA_CYCLES",
    "EVIDENCE_DIR",
    "get_evidence_dir",
    # Exceptions
    "MCPValidationError",
    "MCPAccuracyError",
    "MCPTimeoutError",
    "MCPConfigError",
    "MCPAuthenticationError",
    "MCPComparisonError",
    # Types
    "ValidationResult",
    "ServerValidationResult",
    "MCPValidationReport",
    "ValidationStatus",
    "ProfileMapping",
    "FieldComparison",
]
