# =============================================================================
# Evidence Generator
# =============================================================================
# ADLC v3.0.0 - Constitutional evidence JSON generation (CHK027)
# =============================================================================

"""Evidence generator for ADLC constitutional compliance."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.constants import ACCURACY_TARGET, get_coordination_dir, get_evidence_dir
from ..core.types import MCPValidationReport, ServerValidationResult, ValidationStatus


class EvidenceGenerator:
    """Generator for ADLC constitutional evidence files.

    Creates JSON evidence files in the tmp/<project> directory
    structure as required by ADLC v3.0.0 CHK027.

    This generator is project-agnostic and will auto-detect the project
    from the current working directory or accept an explicit project name.
    """

    def __init__(
        self,
        project_root: Path | str | None = None,
        project_name: str | None = None,
    ) -> None:
        """Initialize the evidence generator.

        Args:
            project_root: Root directory of the project (defaults to cwd)
            project_name: Project name (auto-detected from cwd if None)
        """
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root)
        self.project_name = project_name
        self.evidence_dir = self.project_root / get_evidence_dir(project_name)
        self.coordination_dir = self.project_root / get_coordination_dir(project_name)

    def ensure_directories(self) -> None:
        """Create evidence directories if they don't exist."""
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.coordination_dir.mkdir(parents=True, exist_ok=True)

    def generate_validation_evidence(
        self,
        report: MCPValidationReport,
        filename_prefix: str = "mcp-validation",
    ) -> Path:
        """Generate MCP validation evidence file.

        Args:
            report: MCPValidationReport with validation results
            filename_prefix: Prefix for the evidence filename

        Returns:
            Path to the generated evidence file
        """
        self.ensure_directories()

        date_str = report.timestamp.strftime("%Y-%m-%d")
        filename = f"{filename_prefix}-{date_str}.json"
        filepath = self.evidence_dir / filename

        evidence_data = report.to_evidence_dict()
        evidence_data["evidence_path"] = str(filepath)

        with open(filepath, "w") as f:
            json.dump(evidence_data, f, indent=2)

        return filepath

    def generate_server_evidence(
        self,
        result: ServerValidationResult,
        filename_prefix: str | None = None,
    ) -> Path:
        """Generate evidence file for a single server validation.

        Args:
            result: ServerValidationResult with validation details
            filename_prefix: Prefix for filename (defaults to server name)

        Returns:
            Path to the generated evidence file
        """
        self.ensure_directories()

        prefix = filename_prefix or result.server_name.replace("-", "_")
        date_str = result.started_at.strftime("%Y-%m-%d")
        filename = f"{prefix}-validation-{date_str}.json"
        filepath = self.evidence_dir / filename

        evidence_data = {
            "timestamp": result.started_at.isoformat(),
            "server_name": result.server_name,
            "profile": result.profile,
            "native_command": result.native_command,
            "validation": {
                "status": result.status.value,
                "accuracy": round(result.accuracy, 2),
                "target_accuracy": result.target_accuracy,
                "target_met": result.target_met,
                "checks_passed": result.checks_passed,
                "checks_failed": result.checks_failed,
                "checks_total": result.checks_total,
                "duration_seconds": result.duration_seconds,
            },
            "adlc_version": "3.0.0",
            "checkpoint": "CHK027",
            "evidence_path": str(filepath),
        }

        with open(filepath, "w") as f:
            json.dump(evidence_data, f, indent=2)

        return filepath

    def generate_coordination_log(
        self,
        agent: str,
        action: str,
        project: str | None = None,
        details: dict[str, Any] | None = None,
        coordinated_with: list[str] | None = None,
    ) -> Path:
        """Generate coordination log for agent activities.

        Args:
            agent: Agent name (e.g., "product-owner", "cloud-architect")
            action: Action performed
            project: Project name (auto-detected if None)
            details: Additional details
            coordinated_with: List of agents coordinated with

        Returns:
            Path to the generated coordination log
        """
        self.ensure_directories()

        timestamp = datetime.utcnow()
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = f"{agent}-{date_str}.json"
        filepath = self.coordination_dir / filename

        effective_project = project or self.project_name or Path.cwd().name.lower()

        log_data = {
            "timestamp": timestamp.isoformat(),
            "agent": agent,
            "action": action,
            "project": effective_project,
            "adlc_version": "3.0.0",
            "coordinated_with": coordinated_with or [],
            "details": details or {},
            "evidence_path": str(filepath),
        }

        with open(filepath, "w") as f:
            json.dump(log_data, f, indent=2)

        return filepath

    def generate_pdca_cycle_evidence(
        self,
        cycle_number: int,
        report: MCPValidationReport,
        improvements: list[str] | None = None,
    ) -> Path:
        """Generate PDCA cycle evidence for iterative improvement.

        Args:
            cycle_number: Current PDCA cycle (1-7)
            report: MCPValidationReport from this cycle
            improvements: List of improvements made in this cycle

        Returns:
            Path to the generated PDCA evidence file
        """
        self.ensure_directories()

        date_str = report.timestamp.strftime("%Y-%m-%d")
        filename = f"pdca-cycle-{cycle_number}-{date_str}.json"
        filepath = self.evidence_dir / filename

        pdca_data = {
            "timestamp": report.timestamp.isoformat(),
            "pdca_cycle": cycle_number,
            "max_cycles": report.max_pdca_cycles,
            "phase": "CHECK" if report.target_met else "ACT",
            "validation_summary": {
                "overall_accuracy": round(report.overall_accuracy, 2),
                "target_accuracy": ACCURACY_TARGET,
                "target_met": report.target_met,
                "servers_passed": report.servers_passed,
                "servers_total": report.servers_total,
            },
            "improvements_applied": improvements or [],
            "next_action": "COMPLETE" if report.target_met else "ITERATE",
            "adlc_version": "3.0.0",
            "checkpoint": "CHK041",
            "evidence_path": str(filepath),
        }

        with open(filepath, "w") as f:
            json.dump(pdca_data, f, indent=2)

        return filepath

    def generate_summary_evidence(
        self,
        phase: str,
        status: str,
        details: dict[str, Any],
    ) -> Path:
        """Generate phase completion summary evidence.

        Args:
            phase: Phase name (e.g., "phase1-aws-profiles", "phase2-mcp-validation")
            status: Completion status ("VERIFIED", "FAILED", "PARTIAL")
            details: Phase-specific details

        Returns:
            Path to the generated summary evidence file
        """
        self.ensure_directories()

        timestamp = datetime.utcnow()
        date_str = timestamp.strftime("%Y-%m-%d")
        filename = f"{phase}-completion-{date_str}.json"
        filepath = self.evidence_dir / filename

        effective_project = self.project_name or Path.cwd().name.lower()

        summary_data = {
            "timestamp": timestamp.isoformat(),
            "phase": phase,
            "status": status,
            "project": effective_project,
            "framework_version": "ADLC v3.0.0",
            "details": details,
            "evidence_path": str(filepath),
        }

        with open(filepath, "w") as f:
            json.dump(summary_data, f, indent=2)

        return filepath
