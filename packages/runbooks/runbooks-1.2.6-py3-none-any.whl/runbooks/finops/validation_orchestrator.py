#!/usr/bin/env python3
"""
Validation Orchestrator - Central MCP Validation Coordination
==============================================================

v1.1.31: Central orchestrator for coordinating 4-way MCP validation across
all resource types (S3, EC2, WorkSpaces, RDS, Lambda, etc.)

Business Value:
- Unified validation interface achieving >=99.5% MCP accuracy
- Aggregated validation reports for enterprise audit compliance
- Evidence package generation in artifacts/evidence/

Architecture:
    ValidationOrchestrator
        ├── S3MCPValidator (4-way validation)
        ├── HybridMCPEngine (service-level validation)
        └── Future validators (EC2, WorkSpaces, RDS, Lambda)

Usage:
    from runbooks.finops.validation_orchestrator import ValidationOrchestrator

    orchestrator = ValidationOrchestrator(profile='my-profile')
    results = orchestrator.validate_all()
    print(f"Overall accuracy: {results.overall_accuracy:.2f}%")

Author: Runbooks Team
Version: 1.0.0
Epic: v1.1.31 MCP Validation Improvements
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from runbooks.common.rich_utils import (
    console,
    create_table,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
)

# Centralized constants
from runbooks.finops import (
    MCP_ACCURACY_THRESHOLD,
    MCP_VARIANCE_THRESHOLD,
    get_evidence_dir,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ServiceValidationResult:
    """Result for a single service validation."""

    service_name: str
    accuracy_pct: float
    variance_pct: float
    passes_threshold: bool
    validation_method: str  # '4-way', 'service-level', 'resource-level'
    runbooks_cost: float
    reference_cost: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "service_name": self.service_name,
            "accuracy_pct": self.accuracy_pct,
            "variance_pct": self.variance_pct,
            "passes_threshold": self.passes_threshold,
            "validation_method": self.validation_method,
            "runbooks_cost": self.runbooks_cost,
            "reference_cost": self.reference_cost,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class OrchestratorResults:
    """Aggregated results from all validations."""

    total_services: int = 0
    validated_services: int = 0
    passed_services: int = 0
    failed_services: int = 0
    overall_accuracy: float = 0.0
    overall_variance: float = 0.0
    passes_threshold: bool = False
    service_results: List[ServiceValidationResult] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    evidence_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Calculate derived metrics."""
        self.passes_threshold = self.overall_accuracy >= MCP_ACCURACY_THRESHOLD

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_services": self.total_services,
            "validated_services": self.validated_services,
            "passed_services": self.passed_services,
            "failed_services": self.failed_services,
            "overall_accuracy": self.overall_accuracy,
            "overall_variance": self.overall_variance,
            "passes_threshold": self.passes_threshold,
            "accuracy_threshold": MCP_ACCURACY_THRESHOLD,
            "service_results": [r.to_dict() for r in self.service_results],
            "execution_time_seconds": self.execution_time_seconds,
            "evidence_path": self.evidence_path,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════


class ValidationOrchestrator:
    """
    Central Validation Orchestrator for MCP Cross-Validation.

    Coordinates validation across multiple resource types using:
    - S3MCPValidator: 4-way validation for S3 buckets
    - HybridMCPEngine: Service-level validation via Cost Explorer

    Example:
        >>> orchestrator = ValidationOrchestrator(profile='my-profile')
        >>> results = orchestrator.validate_services(['EC2', 'S3', 'RDS'])
        >>> if results.passes_threshold:
        ...     print("Enterprise accuracy target achieved!")
    """

    def __init__(
        self,
        profile: str,
        region: str = "ap-southeast-2",
        accuracy_threshold: float = MCP_ACCURACY_THRESHOLD,
    ):
        """
        Initialize ValidationOrchestrator.

        Args:
            profile: AWS profile for Cost Explorer API
            region: AWS region (default: ap-southeast-2)
            accuracy_threshold: Minimum accuracy for pass (default: 99.5%)
        """
        self.profile = profile
        self.region = region
        self.accuracy_threshold = accuracy_threshold
        self.evidence_dir = get_evidence_dir("finops")

        # Lazy-loaded validators
        self._hybrid_engine = None
        self._s3_validator = None

        logger.info(f"ValidationOrchestrator initialized for profile: {profile}")

    @property
    def hybrid_engine(self):
        """Lazy-load HybridMCPEngine."""
        if self._hybrid_engine is None:
            from runbooks.finops.hybrid_mcp_engine import create_hybrid_mcp_engine

            self._hybrid_engine = create_hybrid_mcp_engine(
                accuracy_threshold=self.accuracy_threshold / 100,  # Convert to decimal
                profile=self.profile,
            )
        return self._hybrid_engine

    @property
    def s3_validator(self):
        """Lazy-load S3MCPValidator."""
        if self._s3_validator is None:
            from runbooks.finops.s3_mcp_validator import S3MCPValidator

            self._s3_validator = S3MCPValidator(
                profile=self.profile,
                region=self.region,
                output_dir=str(self.evidence_dir),
            )
        return self._s3_validator

    async def validate_service(
        self,
        service_name: str,
        runbooks_cost: float,
        account_id: Optional[str] = None,
    ) -> ServiceValidationResult:
        """
        Validate a single service's cost against AWS Cost Explorer.

        Args:
            service_name: AWS service type (EC2, S3, RDS, etc.)
            runbooks_cost: Runbooks-calculated total service cost
            account_id: AWS account ID (optional)

        Returns:
            ServiceValidationResult with accuracy metrics
        """
        logger.info(f"Validating {service_name} cost: ${runbooks_cost:.2f}")

        try:
            # Use HybridMCPEngine for service-level validation
            mcp_result = await self.hybrid_engine.validate_service_total(
                service_name=service_name,
                runbooks_total=runbooks_cost,
                account_id=account_id,
            )

            accuracy = (1.0 - mcp_result.variance_pct / 100) * 100
            passes = accuracy >= self.accuracy_threshold

            return ServiceValidationResult(
                service_name=service_name,
                accuracy_pct=accuracy,
                variance_pct=mcp_result.variance_pct,
                passes_threshold=passes,
                validation_method="service-level",
                runbooks_cost=runbooks_cost,
                reference_cost=mcp_result.metadata.get("aws_cost_explorer_cost", 0),
                metadata=mcp_result.metadata,
            )

        except Exception as e:
            logger.error(f"Validation failed for {service_name}: {e}")
            return ServiceValidationResult(
                service_name=service_name,
                accuracy_pct=0.0,
                variance_pct=100.0,
                passes_threshold=False,
                validation_method="service-level",
                runbooks_cost=runbooks_cost,
                reference_cost=0.0,
                metadata={"error": str(e)},
            )

    async def validate_services(
        self,
        service_costs: Dict[str, float],
        account_id: Optional[str] = None,
    ) -> OrchestratorResults:
        """
        Validate multiple services concurrently.

        Args:
            service_costs: Dictionary of {service_name: runbooks_cost}
            account_id: AWS account ID (optional)

        Returns:
            OrchestratorResults with aggregated validation metrics
        """
        import asyncio
        import time

        start_time = time.time()
        print_header("MCP Validation Orchestrator")
        print_info(f"Profile: {self.profile}")
        print_info(f"Services: {len(service_costs)}")
        print_info(f"Accuracy Target: {self.accuracy_threshold}%")
        console.print()

        # Validate each service
        results = []
        for service_name, cost in service_costs.items():
            result = await self.validate_service(service_name, cost, account_id)
            results.append(result)

        # Calculate aggregates
        validated = [r for r in results if r.accuracy_pct > 0]
        passed = [r for r in validated if r.passes_threshold]

        overall_accuracy = sum(r.accuracy_pct for r in validated) / len(validated) if validated else 0.0
        overall_variance = sum(r.variance_pct for r in validated) / len(validated) if validated else 100.0

        # Create results object
        orchestrator_results = OrchestratorResults(
            total_services=len(service_costs),
            validated_services=len(validated),
            passed_services=len(passed),
            failed_services=len(validated) - len(passed),
            overall_accuracy=overall_accuracy,
            overall_variance=overall_variance,
            service_results=results,
            execution_time_seconds=time.time() - start_time,
            evidence_path=str(self.evidence_dir),
        )

        # Display results
        self._display_results(orchestrator_results)

        # Save evidence
        self._save_evidence(orchestrator_results)

        return orchestrator_results

    def validate_s3_4way(self):
        """
        Run complete S3 4-way validation chain.

        Returns:
            ValidationResults from S3MCPValidator
        """
        print_section("S3 4-Way Validation Chain")
        return self.s3_validator.run_complete_validation()

    def _display_results(self, results: OrchestratorResults) -> None:
        """Display validation results with Rich formatting."""
        console.print()

        # Summary table
        table = create_table(
            title="Validation Summary",
            columns=[
                {"name": "Metric", "style": "cyan bold"},
                {"name": "Value", "style": "white"},
            ],
        )

        table.add_row("Total Services", str(results.total_services))
        table.add_row("Validated", str(results.validated_services))
        table.add_row("Passed", f"[green]{results.passed_services}[/green]")
        table.add_row("Failed", f"[red]{results.failed_services}[/red]")
        table.add_row("Overall Accuracy", f"{results.overall_accuracy:.2f}%")
        table.add_row("Overall Variance", f"{results.overall_variance:.2f}%")
        table.add_row("Execution Time", f"{results.execution_time_seconds:.2f}s")

        console.print(table)
        console.print()

        # Service details table
        if results.service_results:
            detail_table = create_table(
                title="Service Validation Details",
                columns=[
                    {"name": "Service", "style": "cyan"},
                    {"name": "Runbooks", "style": "white", "justify": "right"},
                    {"name": "Reference", "style": "white", "justify": "right"},
                    {"name": "Accuracy", "style": "white", "justify": "right"},
                    {"name": "Status", "style": "white"},
                ],
            )

            for r in results.service_results:
                status = "[green]PASS[/]" if r.passes_threshold else "[red]FAIL[/]"
                accuracy_style = "green" if r.passes_threshold else "red"
                detail_table.add_row(
                    r.service_name,
                    f"${r.runbooks_cost:,.2f}",
                    f"${r.reference_cost:,.2f}",
                    f"[{accuracy_style}]{r.accuracy_pct:.2f}%[/]",
                    status,
                )

            console.print(detail_table)

        # Overall status
        console.print()
        if results.passes_threshold:
            print_success(f"VALIDATION PASSED: {results.overall_accuracy:.2f}% (threshold: {MCP_ACCURACY_THRESHOLD}%)")
        else:
            print_warning(
                f"VALIDATION BELOW THRESHOLD: {results.overall_accuracy:.2f}% (threshold: {MCP_ACCURACY_THRESHOLD}%)"
            )

    def _save_evidence(self, results: OrchestratorResults) -> None:
        """Save validation evidence for audit compliance."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_file = self.evidence_dir / f"validation-orchestrator-{timestamp}.json"

        with open(evidence_file, "w") as f:
            json.dump(results.to_dict(), f, indent=2, default=str)

        print_info(f"Evidence saved: {evidence_file}")


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════


def create_validation_orchestrator(
    profile: str,
    region: str = "ap-southeast-2",
) -> ValidationOrchestrator:
    """
    Factory function to create ValidationOrchestrator.

    Args:
        profile: AWS profile for Cost Explorer API
        region: AWS region (default: ap-southeast-2)

    Returns:
        Initialized ValidationOrchestrator instance
    """
    return ValidationOrchestrator(profile=profile, region=region)


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════


__all__ = [
    "ValidationOrchestrator",
    "ServiceValidationResult",
    "OrchestratorResults",
    "create_validation_orchestrator",
]
