"""
Audit and Provenance Utilities for Compliance Tracking.

This module provides lightweight provenance utilities for adding cryptographic
hashes and audit metadata to data outputs. Designed for SOC2/SOX compliance.

Features:
- SHA256 content hashing for data integrity verification
- Provenance metadata injection (timestamp, version, generator)
- Response hashing for audit trail

Design Principles (KISS/DRY):
- ~50 LOC for focused functionality
- No external dependencies beyond stdlib + runbooks
- Composable with enterprise_audit_integration.py

Session 5 Lessons Learned (2026-01-16):
- Migrated from rb_fo_001.py (lines 263-278) to eliminate 600+ LOC workaround
- KISS principle: Simple provenance function vs complex parallel implementation

Author: Runbooks Team
Version: 1.2.3
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def get_version() -> str:
    """Get runbooks version safely."""
    try:
        import runbooks

        return runbooks.__version__
    except (ImportError, AttributeError):
        return "unknown"


def add_provenance_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """
    Add provenance metadata for audit trail (SOC2/SOX compliance).

    This function generates a cryptographic hash of the data content and
    adds metadata about when and how the data was generated.

    Args:
        data: Dictionary to add provenance metadata to

    Returns:
        Original data with provenance metadata added

    Example:
        >>> data = {"total_cost": 145784.56, "services": 66}
        >>> result = add_provenance_metadata(data)
        >>> result["provenance"]["content_hash"]
        '33073ea8feaa365e'  # First 16 chars of SHA256
    """
    # Serialize data deterministically for consistent hashing
    raw_json = json.dumps(data, sort_keys=True, default=str)
    content_hash = hashlib.sha256(raw_json.encode()).hexdigest()[:16]

    return {
        **data,
        "provenance": {
            "content_hash": content_hash,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "runbooks",
            "version": get_version(),
        },
    }


def compute_response_hash(data: Any, truncate: int = 16) -> str:
    """
    Compute SHA256 hash of data for audit trail.

    Args:
        data: Any JSON-serializable data
        truncate: Number of hex chars to return (default 16)

    Returns:
        Truncated SHA256 hash string

    Example:
        >>> compute_response_hash({"cost": 150616.76})
        'a1b2c3d4e5f67890'
    """
    raw_json = json.dumps(data, sort_keys=True, default=str)
    full_hash = hashlib.sha256(raw_json.encode()).hexdigest()
    return full_hash[:truncate]


def create_audit_envelope(
    data: dict[str, Any],
    control_id: str,
    agent: str = "observability-engineer",
    mcp_accuracy: float | None = None,
) -> dict[str, Any]:
    """
    Create a full audit envelope for compliance evidence.

    Args:
        data: The core data to wrap
        control_id: Control identifier (e.g., "C1", "C2")
        agent: Agent that generated the data
        mcp_accuracy: Optional MCP validation accuracy score

    Returns:
        Audit envelope with provenance and compliance metadata

    Example:
        >>> envelope = create_audit_envelope(
        ...     data={"total": 145784.56},
        ...     control_id="C1",
        ...     mcp_accuracy=99.73
        ... )
    """
    envelope = add_provenance_metadata(data)
    envelope["audit"] = {
        "control_id": control_id,
        "agent": agent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mcp_accuracy": mcp_accuracy,
        "adlc_version": "3.1.0",
    }
    return envelope
