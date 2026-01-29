# =============================================================================
# MCP Validation Types
# =============================================================================
# ADLC v3.0.0 - Pydantic models for MCP validation framework
# =============================================================================

"""Pydantic models for MCP validation framework."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class ValidationStatus(str, Enum):
    """Status of a validation check."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    PENDING = "PENDING"


class ProfileMapping(BaseModel):
    """AWS profile to MCP server mapping."""

    profile_name: str = Field(..., description="AWS profile name")
    profile_env_var: str = Field(..., description="Environment variable name")
    account_id: str | None = Field(None, description="AWS account ID")
    mcp_servers: list[str] = Field(default_factory=list, description="MCP servers using this profile")


class FieldComparison(BaseModel):
    """Result of comparing a single field between MCP and native API."""

    field_path: str = Field(..., description="JSONPath or field name")
    mcp_value: Any = Field(..., description="Value from MCP server")
    native_value: Any = Field(..., description="Value from native API")
    match: bool = Field(..., description="Whether values match")
    tolerance_applied: float | None = Field(None, description="Tolerance applied for comparison (if any)")
    notes: str | None = Field(None, description="Additional notes about comparison")


class ValidationResult(BaseModel):
    """Result of a single validation check."""

    check_name: str = Field(..., description="Name of the validation check")
    status: ValidationStatus = Field(..., description="Status of the check")
    message: str = Field(..., description="Human-readable result message")
    field_comparisons: list[FieldComparison] = Field(default_factory=list, description="Individual field comparisons")
    duration_ms: float | None = Field(None, description="Duration in milliseconds")
    error: str | None = Field(None, description="Error message if status is ERROR")

    @computed_field
    @property
    def fields_matched(self) -> int:
        """Count of fields that matched."""
        return sum(1 for f in self.field_comparisons if f.match)

    @computed_field
    @property
    def fields_total(self) -> int:
        """Total count of fields compared."""
        return len(self.field_comparisons)

    @computed_field
    @property
    def field_accuracy(self) -> float:
        """Accuracy percentage for field comparisons."""
        if self.fields_total == 0:
            return 100.0
        return (self.fields_matched / self.fields_total) * 100


class ServerValidationResult(BaseModel):
    """Result of validating a single MCP server."""

    server_name: str = Field(..., description="MCP server name")
    profile: str | None = Field(None, description="AWS/Azure profile used")
    native_command: str | None = Field(None, description="Native CLI command used")
    status: ValidationStatus = Field(..., description="Overall status")
    accuracy: float = Field(..., ge=0, le=100, description="Accuracy percentage")
    target_accuracy: float = Field(default=99.5, ge=0, le=100, description="Target accuracy")
    validation_results: list[ValidationResult] = Field(
        default_factory=list, description="Individual validation results"
    )
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Validation start time")
    completed_at: datetime | None = Field(None, description="Validation completion time")
    error: str | None = Field(None, description="Error message if validation failed")

    @computed_field
    @property
    def target_met(self) -> bool:
        """Whether accuracy target was met."""
        return self.accuracy >= self.target_accuracy

    @computed_field
    @property
    def duration_seconds(self) -> float | None:
        """Total validation duration in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @computed_field
    @property
    def checks_passed(self) -> int:
        """Count of checks that passed."""
        return sum(1 for r in self.validation_results if r.status == ValidationStatus.PASSED)

    @computed_field
    @property
    def checks_failed(self) -> int:
        """Count of checks that failed."""
        return sum(1 for r in self.validation_results if r.status == ValidationStatus.FAILED)

    @computed_field
    @property
    def checks_total(self) -> int:
        """Total count of checks."""
        return len(self.validation_results)


class MCPValidationReport(BaseModel):
    """Complete MCP validation report for evidence generation."""

    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")
    adlc_version: str = Field(default="3.0.0", description="ADLC framework version")
    project: str = Field(default="cloud-infrastructure", description="Project name")
    checkpoint: str = Field(default="CHK027", description="Constitutional checkpoint")
    validation_mode: str = Field(default="cross-validation", description="Validation mode")
    server_results: list[ServerValidationResult] = Field(default_factory=list, description="Results per MCP server")
    pdca_cycle: int = Field(default=1, ge=1, le=7, description="Current PDCA cycle")
    max_pdca_cycles: int = Field(default=7, description="Maximum PDCA cycles")

    @computed_field
    @property
    def overall_accuracy(self) -> float:
        """Overall accuracy across all validated servers (excludes skipped)."""
        if not self.server_results:
            return 0.0
        # Exclude skipped servers from accuracy calculation
        validated = [r for r in self.server_results if r.status != ValidationStatus.SKIPPED]
        if not validated:
            return 0.0
        return sum(r.accuracy for r in validated) / len(validated)

    @computed_field
    @property
    def overall_status(self) -> ValidationStatus:
        """Overall validation status (excludes skipped servers)."""
        if not self.server_results:
            return ValidationStatus.PENDING
        # Only consider non-skipped servers
        validated = [r for r in self.server_results if r.status != ValidationStatus.SKIPPED]
        if not validated:
            return ValidationStatus.PENDING
        if all(r.target_met for r in validated):
            return ValidationStatus.PASSED
        return ValidationStatus.FAILED

    @computed_field
    @property
    def target_met(self) -> bool:
        """Whether overall target was met."""
        return self.overall_status == ValidationStatus.PASSED

    @computed_field
    @property
    def servers_passed(self) -> int:
        """Count of servers that passed validation (excludes skipped)."""
        return sum(1 for r in self.server_results if r.target_met and r.status != ValidationStatus.SKIPPED)

    @computed_field
    @property
    def servers_total(self) -> int:
        """Total count of servers validated (excludes skipped)."""
        return sum(1 for r in self.server_results if r.status != ValidationStatus.SKIPPED)

    @computed_field
    @property
    def servers_skipped(self) -> int:
        """Count of servers that were skipped."""
        return sum(1 for r in self.server_results if r.status == ValidationStatus.SKIPPED)

    def to_evidence_dict(self) -> dict[str, Any]:
        """Convert to evidence dictionary for JSON output."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "adlc_version": self.adlc_version,
            "project": self.project,
            "checkpoint": self.checkpoint,
            "validation_mode": self.validation_mode,
            "summary": {
                "overall_accuracy": round(self.overall_accuracy, 2),
                "overall_status": self.overall_status.value,
                "target_met": self.target_met,
                "servers_passed": self.servers_passed,
                "servers_total": self.servers_total,
                "servers_skipped": self.servers_skipped,
                "pdca_cycle": self.pdca_cycle,
            },
            "server_results": [
                {
                    "server": r.server_name,
                    "profile": r.profile,
                    "accuracy": round(r.accuracy, 2),
                    "target_met": r.target_met,
                    "status": r.status.value,
                    "checks_passed": r.checks_passed,
                    "checks_total": r.checks_total,
                    "duration_seconds": r.duration_seconds,
                }
                for r in self.server_results
            ],
            "evidence_path": f"tmp/{self.project}/test-results/mcp-validation-{self.timestamp.strftime('%Y-%m-%d')}.json",
        }
