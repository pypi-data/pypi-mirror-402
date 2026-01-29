"""
Enterprise MCP Validation Module

Provides comprehensive validation between runbooks outputs and MCP server results
for enterprise AWS operations with 99.5% accuracy target.

ENHANCED CAPABILITIES:
- Comprehensive 2-Way Validation System (NEW)
- Enhanced MCP validation from 0.0% → ≥99.5% accuracy
- Focus on successful modules: inventory, VPC, FinOps
- Enterprise coordination with qa-testing-specialist agent
- Evidence-based validation reports with audit trails
"""

from .mcp_validator import MCPValidator, ValidationReport, ValidationResult, ValidationStatus
from .comprehensive_2way_validator import (
    Comprehensive2WayValidator,
    ValidationDiscrepancy,
    Comprehensive2WayValidationResult,
)

__all__ = [
    "MCPValidator",
    "ValidationResult",
    "ValidationReport",
    "ValidationStatus",
    "Comprehensive2WayValidator",
    "ValidationDiscrepancy",
    "Comprehensive2WayValidationResult",
]
