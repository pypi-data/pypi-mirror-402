"""
Azure FinOps Configuration - Aligned with runbooks.finops.config

Configuration management for Azure cost reporting, following the same
patterns as runbooks.finops.config (DisplayConfiguration).

Migration: Copy to runbooks/finops/azure_config.py

Framework: ADLC v3.0.0 | Version: 1.0.0
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _get_workspace_root() -> Path:
    """
    Detect workspace root for path resolution.

    Priority:
    1. WORKSPACE env var (explicit)
    2. DevContainer path (/workspace)
    3. Marker file detection (.git, CLAUDE.md, Taskfile.yml)
    """
    if os.environ.get("WORKSPACE"):
        return Path(os.environ["WORKSPACE"])

    cwd = Path().resolve()

    # DevContainer detection
    if cwd == Path("/workspace") or str(cwd).startswith("/workspace"):
        return Path("/workspace")

    # Marker file detection
    for marker in [".git", "CLAUDE.md", "Taskfile.yml"]:
        if (cwd / marker).exists():
            return cwd
        for parent in cwd.parents:
            if (parent / marker).exists():
                return parent

    return cwd


@dataclass
class AzureReportConfig:
    """
    Configuration for Azure Cost Management reports.

    Aligned with runbooks.finops.config.DisplayConfiguration pattern:
    - Dataclass with smart defaults
    - Environment variable support
    - Business cost thresholds

    Environment Variables:
    - AZURE_FINOPS_HIGH_COST_THRESHOLD: High cost tier threshold
    - AZURE_FINOPS_MEDIUM_COST_THRESHOLD: Medium cost tier threshold
    - AZURE_FINOPS_CURRENCY: Default currency (NZD)
    - AZURE_FINOPS_DATA_DIR: Data directory override
    """

    # Customer identification
    customer_name: str
    customer_id: str = ""
    billing_period: str = ""
    date_range: str = ""

    # Input files (auto-discovered if not provided)
    services_csv: Optional[Path] = None
    subscriptions_csv: Optional[Path] = None

    # Output configuration
    output_dir: Optional[Path] = None
    output_filename: str = ""

    # Currency (FOCUS 1.2: BillingCurrency)
    currency: str = field(default_factory=lambda: os.getenv("AZURE_FINOPS_CURRENCY", "NZD"))
    currency_symbol: str = "NZ$"

    # Cost thresholds (aligned with runbooks.finops.config)
    high_cost_threshold: float = field(
        default_factory=lambda: float(os.getenv("AZURE_FINOPS_HIGH_COST_THRESHOLD", "5000"))
    )
    medium_cost_threshold: float = field(
        default_factory=lambda: float(os.getenv("AZURE_FINOPS_MEDIUM_COST_THRESHOLD", "1000"))
    )

    # Workspace root (auto-detected)
    workspace: Path = field(default_factory=_get_workspace_root)

    def __post_init__(self):
        """Apply smart defaults after initialization."""
        if not isinstance(self.workspace, Path):
            self.workspace = Path(self.workspace)

        # Auto-generate output filename
        if not self.output_filename and self.customer_name and self.billing_period:
            parts = self.billing_period.split()
            if len(parts) == 2:
                month_abbr = parts[0][:3].upper()
                year = parts[1]
                safe_name = self.customer_name.replace(" ", "-")
                self.output_filename = f"{safe_name}-Azure-Monthly-Report-{year}-{month_abbr}.xlsx"

        # Set default output directory
        if self.output_dir is None:
            self.output_dir = self.workspace / "output/finops"
        elif not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)

    @classmethod
    def from_environment(cls, customer_name: str) -> "AzureReportConfig":
        """
        Create configuration from environment variables.

        Args:
            customer_name: Required customer name

        Returns:
            AzureReportConfig with environment-based settings
        """
        return cls(
            customer_name=customer_name,
            customer_id=os.getenv("AZURE_FINOPS_CUSTOMER_ID", ""),
            billing_period=os.getenv("AZURE_FINOPS_BILLING_PERIOD", ""),
            date_range=os.getenv("AZURE_FINOPS_DATE_RANGE", ""),
        )

    @property
    def data_dir(self) -> Path:
        """Default data directory for Azure exports."""
        env_dir = os.getenv("AZURE_FINOPS_DATA_DIR")
        if env_dir:
            return Path(env_dir)
        return self.workspace / "data/finops/azure"

    @property
    def evidence_dir(self) -> Path:
        """Directory for evidence JSON (ADLC compliance)."""
        return self.workspace / "tmp/cloud-infrastructure/cost-reports"

    @property
    def screenshots_dir(self) -> Path:
        """Directory for chart exports."""
        return self.output_dir / "screenshots"

    @property
    def output_path(self) -> Path:
        """Full path to output Excel file."""
        return self.output_dir / self.output_filename

    def to_dict(self) -> dict:
        """Serialize configuration to dictionary."""
        return {
            "customer_name": self.customer_name,
            "customer_id": self.customer_id,
            "billing_period": self.billing_period,
            "date_range": self.date_range,
            "services_csv": str(self.services_csv) if self.services_csv else None,
            "subscriptions_csv": str(self.subscriptions_csv) if self.subscriptions_csv else None,
            "output_dir": str(self.output_dir),
            "output_filename": self.output_filename,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "high_cost_threshold": self.high_cost_threshold,
            "medium_cost_threshold": self.medium_cost_threshold,
            "data_dir": str(self.data_dir),
        }
