"""Base optimizer class eliminating duplication across 17 optimizer files.

Consolidation Pattern (Phases 4-7):
- Provides common patterns: AWS client management, cost calculations, result formatting
- Eliminates 45% duplication across EC2, RDS, S3, Network, CloudWatch, Reservations optimizers
- Integrates with runbooks.common infrastructure (AWSClientFactory, CostExplorerClient)

Author: Runbooks Team
Version: v1.1.28+
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from runbooks.common.aws_client_factory import AWSClientFactory
from runbooks.common.cost_explorer_client import CostExplorerClient


@dataclass
class OptimizerConfig:
    """Optimizer configuration."""

    billing_profile: str
    operational_profile: str
    region: str = "ap-southeast-2"
    dry_run: bool = False
    output_format: str = "table"  # table, csv, json, markdown


@dataclass
class OptimizerResult:
    """Standardized optimizer output."""

    service: str
    annual_savings: float
    monthly_savings: float
    recommendations: List[Dict[str, Any]]
    confidence: str  # HIGH, MEDIUM, LOW
    metadata: Dict[str, Any] = field(default_factory=dict)
    recommendation_count: int = 0

    def __post_init__(self):
        """Calculate recommendation count if not provided."""
        if not self.recommendation_count:
            self.recommendation_count = len(self.recommendations)


class BaseOptimizer(ABC):
    """Abstract base for AWS cost optimizers.

    Design Principles:
    - Service-specific subclasses implement analyze() method
    - Common AWS client management and cost calculation utilities
    - Standardized result format for consistent reporting
    - Integrated with runbooks.common infrastructure

    Example:
        >>> config = OptimizerConfig(
        ...     billing_profile='default',
        ...     operational_profile='default'
        ... )
        >>> optimizer = EC2Optimizer(config)
        >>> result = optimizer.analyze()
        >>> print(f"Annual Savings: ${result.annual_savings:,.2f}")
    """

    def __init__(self, config: OptimizerConfig):
        """Initialize base optimizer with AWS clients.

        Args:
            config: Optimizer configuration with AWS profiles and settings
        """
        self.config = config
        self.ce_client = CostExplorerClient(config.billing_profile, config.region)

    @abstractmethod
    def analyze(self) -> OptimizerResult:
        """Analyze and generate recommendations.

        Returns:
            OptimizerResult with savings projections and recommendations

        Note:
            Implemented by service-specific subclasses (EC2Optimizer, RDSOptimizer, etc.)
        """
        pass

    def export_recommendations(self, result: OptimizerResult, output_dir: str = "/tmp") -> Dict[str, str]:
        """Export recommendations to multiple formats.

        Args:
            result: OptimizerResult to export
            output_dir: Directory for output files

        Returns:
            Dict mapping format to output file path
        """
        if not result.recommendations:
            return {}

        df = pd.DataFrame(result.recommendations)
        base_filename = f"{result.service.lower()}-optimization-{self.config.billing_profile}"

        exported_files = {}

        # CSV export
        if self.config.output_format in ["csv", "all"]:
            csv_path = f"{output_dir}/{base_filename}.csv"
            df.to_csv(csv_path, index=False)
            exported_files["csv"] = csv_path

        # JSON export
        if self.config.output_format in ["json", "all"]:
            json_path = f"{output_dir}/{base_filename}.json"
            df.to_json(json_path, orient="records", indent=2)
            exported_files["json"] = json_path

        # Markdown export
        if self.config.output_format in ["markdown", "all"]:
            md_path = f"{output_dir}/{base_filename}.md"
            with open(md_path, "w") as f:
                f.write(f"# {result.service} Cost Optimization Recommendations\n\n")
                f.write(f"**Annual Savings**: ${result.annual_savings:,.2f}\n")
                f.write(f"**Monthly Savings**: ${result.monthly_savings:,.2f}\n")
                f.write(f"**Confidence**: {result.confidence}\n\n")
                f.write(df.to_markdown(index=False))
            exported_files["markdown"] = md_path

        return exported_files

    def calculate_annual_savings(self, monthly_savings: float) -> float:
        """Convert monthly to annual savings.

        Args:
            monthly_savings: Monthly cost savings

        Returns:
            Annual savings (monthly * 12)
        """
        return monthly_savings * 12

    def calculate_monthly_savings(self, annual_savings: float) -> float:
        """Convert annual to monthly savings.

        Args:
            annual_savings: Annual cost savings

        Returns:
            Monthly savings (annual / 12)
        """
        return annual_savings / 12

    def create_aws_client(self, service_name: str) -> Any:
        """Create AWS service client using factory pattern.

        Args:
            service_name: AWS service name (ec2, rds, s3, etc.)

        Returns:
            Boto3 client for specified service
        """
        return AWSClientFactory.create_client(service_name, self.config.operational_profile, self.config.region)

    def format_savings_summary(self, monthly_savings: float, annual_savings: float, confidence: str) -> str:
        """Format savings summary for display.

        Args:
            monthly_savings: Monthly savings amount
            annual_savings: Annual savings amount
            confidence: Confidence level (HIGH, MEDIUM, LOW)

        Returns:
            Formatted summary string
        """
        return (
            f"Monthly Savings: ${monthly_savings:,.2f} | "
            f"Annual Savings: ${annual_savings:,.2f} | "
            f"Confidence: {confidence}"
        )

    def validate_config(self) -> bool:
        """Validate optimizer configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.billing_profile:
            raise ValueError("billing_profile is required")
        if not self.config.operational_profile:
            raise ValueError("operational_profile is required")
        return True
