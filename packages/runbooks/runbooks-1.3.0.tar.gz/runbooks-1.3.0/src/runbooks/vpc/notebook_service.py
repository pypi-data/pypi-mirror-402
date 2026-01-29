"""
VPC Notebook Service - Manager-friendly service layer for VPC cost optimization dashboard

This module provides a simplified interface for Jupyter notebooks, orchestrating
existing VPC modules (collectors, analyzers, formatters) into manager-friendly operations.

Strategic Context:
- Epic 2 Story 2.5 (AWS-25): Refactoring notebook from 2000+ lines to 50 lines
- Extracts business logic into reusable modules with zero code duplication
- Manager-friendly interface hiding Python complexity from business users

Architecture:
- Orchestrates: EvidenceLoader, CostCalculator, ScoringEngine, RecommendationEngine
- Uses: VPCMetadata, VPCResources, VPCAnalysis models (Pydantic)
- Outputs: Rich CLI tables, panels, and structured business data

Usage (Jupyter Notebook):
    from pathlib import Path
    from runbooks.vpc.notebook_service import VPCNotebookService

    # Initialize service
    service = VPCNotebookService(
        evidence_dir=Path("artifacts/evidence/network"),
        config_file=Path("vpc-config.yaml")
    )

    # Load inventory (one-line call)
    result = service.load_vpc_inventory()

    # Display decision matrix
    table = service.create_decision_matrix_table(result.analyses)
    console.print(table)

    # Business summary
    summary = service.get_business_summary(result.analyses)
    print(f"Total Monthly Cost: ${summary['total_monthly_cost']}")
"""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import re

import pandas as pd
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from runbooks.common.rich_utils import (
    console,
    create_table,
    format_cost,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from runbooks.vpc.collectors.evidence_loader import EvidenceLoader
from runbooks.vpc.config import VPCConfig, VPCConfigManager
from runbooks.vpc.core.cost_calculator import CostCalculator
from runbooks.vpc.core.recommendation_engine import RecommendationEngine
from runbooks.vpc.core.scoring_engine import ScoringEngine
from runbooks.vpc.models import VPCAnalysis, VPCMetadata, VPCResources
from runbooks.vpc.utils.rich_formatters import VPCTableFormatter


@dataclass
class NotebookInventoryResult:
    """
    Result from load_vpc_inventory() operation.

    Manager-friendly output combining all VPC analysis data with Rich CLI visualization.

    Attributes:
        analyses: Complete VPC analysis results (metadata + resources + costs + recommendations)
        total_vpcs: Total number of VPCs analyzed
        total_nat_gateways: Aggregate NAT Gateway count across all VPCs
        total_interface_vpce: Aggregate Interface VPCE count (costs $7.30/month each)
        total_gateway_vpce: Aggregate Gateway VPCE count (FREE)
        total_monthly_cost: Aggregate monthly infrastructure cost
        summary_table: Rich CLI table showing aggregate statistics
    """

    analyses: List[VPCAnalysis]
    total_vpcs: int
    total_nat_gateways: int
    total_interface_vpce: int
    total_gateway_vpce: int
    total_monthly_cost: Decimal
    summary_table: Table


@dataclass
class VPCCSVAnalysisResult:
    """
    Result from analyze_vpc_from_csv() operation.

    Replaces 140 lines of notebook inline code with enterprise-validated logic.

    Attributes:
        total_vpcs: Total number of VPCs analyzed from CSV
        must_delete: List of VPCs classified as MUST DELETE (ENI=0)
        could_delete: List of VPCs classified as COULD DELETE (orphaned NAT)
        retain: List of VPCs classified as RETAIN (active workloads)
        eni_gate_results: ENI safety gate validation results for each VPC
        total_monthly_cost: Aggregate monthly cost from CSV data
        summary_table: Rich table showing classification breakdown
        classification_table: Rich table showing per-VPC details
        csv_data: Original CSV DataFrame (for enrichment operations)
    """

    total_vpcs: int
    must_delete: List[Dict[str, Any]]
    could_delete: List[Dict[str, Any]]
    retain: List[Dict[str, Any]]
    eni_gate_results: List[Dict[str, Any]]
    total_monthly_cost: Decimal
    summary_table: Table
    classification_table: Table
    csv_data: pd.DataFrame = None


class VPCNotebookService:
    """
    Manager-friendly notebook interface - Zero Python complexity for business users.

    This service orchestrates all VPC modules to provide simple one-line operations
    for Jupyter notebooks, hiding technical complexity while maintaining enterprise
    quality standards.

    Architecture Pattern:
    - Evidence-based analysis: Load from JSON files (no live AWS API required)
    - Smart path resolution: Works from repo root OR notebook directory
    - Defensive parsing: Graceful fallback for edge cases
    - Rich CLI output: Manager-friendly tables, panels, progress bars
    - Structured data: Return Pydantic models for programmatic access

    Example:
        # Simple notebook workflow (3 lines)
        service = VPCNotebookService(Path("artifacts/evidence/network"))
        result = service.load_vpc_inventory()
        console.print(result.summary_table)
    """

    def __init__(
        self,
        evidence_dir: Path,
        config_file: Optional[Path] = None,
        aws_profiles: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize VPC Notebook Service.

        Args:
            evidence_dir: Path to directory containing JSON evidence files
                         (e.g., /Volumes/Working/1xOps/CloudOps-Runbooks/artifacts/evidence/network)
                         Smart resolution: Resolves both absolute and relative paths
            config_file: Optional path to VPC configuration file (YAML/JSON)
                        Format: vpc-config.yaml with VPC metadata
            aws_profiles: Optional AWS profile mapping (vpc_id -> profile_name)
                         Used for live AWS API operations (future enhancement)

        Raises:
            ValueError: If evidence_dir doesn't exist or is invalid

        Example:
            # Absolute path (papermill from repo root)
            service = VPCNotebookService(
                Path("/Volumes/Working/1xOps/CloudOps-Runbooks/artifacts/evidence/network")
            )

            # Relative path (JupyterLab from notebooks/ directory)
            service = VPCNotebookService(
                Path("../artifacts/evidence/network")
            )
        """
        # Smart evidence directory path resolution
        self.evidence_dir = self._resolve_evidence_dir(evidence_dir)

        # Validate evidence directory exists
        if not self.evidence_dir.exists():
            raise ValueError(
                f"Evidence directory not found: {self.evidence_dir}\n"
                f"Expected location: /Volumes/Working/1xOps/CloudOps-Runbooks/artifacts/evidence/network\n"
                f"Hint: Run vpc-resource-inventory.sh to generate evidence files"
            )

        # Initialize evidence loader
        self.evidence_loader = EvidenceLoader(self.evidence_dir)

        # Initialize VPC configuration manager
        self.config_manager = VPCConfigManager()

        # Load VPC configuration from file if provided
        if config_file:
            self._load_config_file(config_file)

        # Initialize cost calculator and scoring engines
        self.cost_calculator = CostCalculator()
        self.scoring_engine = ScoringEngine()
        self.recommendation_engine = RecommendationEngine()

        # Initialize Rich CLI formatter
        self.formatter = VPCTableFormatter()

        # Store AWS profile mapping
        self.aws_profiles = aws_profiles or {}

        console.print(f"✅ VPC Notebook Service initialized (evidence: {self.evidence_dir})")

    def _resolve_evidence_dir(self, evidence_dir: Path) -> Path:
        """
        Smart evidence directory path resolution with repo root detection.

        Supports both:
        - Absolute paths: /Volumes/Working/1xOps/CloudOps-Runbooks/artifacts/evidence/network
        - Relative paths: artifacts/evidence/network (resolved from repo root)

        Args:
            evidence_dir: Evidence directory path (absolute or relative)

        Returns:
            Resolved absolute path to evidence directory

        Raises:
            ValueError: If repo root cannot be detected for relative paths
        """
        # If absolute path, use as-is
        if evidence_dir.is_absolute():
            return evidence_dir

        # For relative paths, detect repo root and resolve from there
        repo_root = self._detect_repo_root()

        if repo_root is None:
            # Fallback: Try from current working directory (papermill compatibility)
            resolved = Path.cwd() / evidence_dir
            if resolved.exists():
                return resolved.resolve()

            raise ValueError(
                f"Cannot resolve relative path '{evidence_dir}' - repo root not detected.\n"
                f"Hint: Use absolute path or ensure notebook runs from repo root."
            )

        # Resolve from repo root
        resolved = repo_root / evidence_dir
        return resolved.resolve()

    def _detect_repo_root(self) -> Optional[Path]:
        """
        Detect repository root by searching for marker files.

        Searches upward from current directory for:
        - .git directory (primary indicator)
        - pyproject.toml (Python project root)
        - src/runbooks directory (package structure)

        Returns:
            Path to repo root, or None if not detected
        """
        # Start from module location (where this file is)
        current = Path(__file__).parent

        # Search upward (max 10 levels) for repo markers
        for _ in range(10):
            # Check for .git directory (most reliable)
            if (current / ".git").exists():
                return current

            # Check for pyproject.toml (Python project root)
            if (current / "pyproject.toml").exists():
                return current

            # Check for src/runbooks (package structure)
            if (current / "src" / "runbooks").exists():
                return current

            # Move up one level
            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent

        # Fallback: Try from CWD
        cwd = Path.cwd()
        if (cwd / ".git").exists() or (cwd / "pyproject.toml").exists():
            return cwd

        return None

    def _load_config_file(self, config_file: Path) -> None:
        """
        Load VPC configuration from YAML or JSON file.

        Args:
            config_file: Path to configuration file

        Raises:
            ValueError: If config file format is invalid or not found
        """
        if not config_file.exists():
            raise ValueError(f"Configuration file not found: {config_file}")

        try:
            if config_file.suffix in [".yaml", ".yml"]:
                self.config_manager.load_from_yaml(config_file)
            elif config_file.suffix == ".json":
                self.config_manager.load_from_json(config_file)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix} (expected .yaml or .json)")
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {config_file}: {e}") from e

    def load_vpc_inventory(self) -> NotebookInventoryResult:
        """
        Load ALL VPCs from evidence files using EvidenceLoader.

        Orchestration Workflow:
        1. Discover VPC IDs from evidence directory (*.json files)
        2. Load VPC configurations from config file OR discover metadata
        3. For each VPC: load resources from 8 evidence JSON files
        4. Calculate cost breakdown using CostCalculator
        5. Run scoring using ScoringEngine
        6. Generate recommendations using RecommendationEngine
        7. Create VPCAnalysis objects
        8. Calculate aggregate totals
        9. Generate Rich summary table

        Returns:
            NotebookInventoryResult: Complete analysis with summary table

        Example:
            service = VPCNotebookService(Path("artifacts/evidence/network"))
            result = service.load_vpc_inventory()

            print(f"Analyzed {result.total_vpcs} VPCs")
            print(f"Total Cost: ${result.total_monthly_cost}/month")
            console.print(result.summary_table)
        """
        console.print("[bold]Loading VPC Inventory from Evidence Files...[/bold]")

        # Discover VPC IDs from evidence directory
        vpc_ids = self._discover_vpc_ids()

        if not vpc_ids:
            print_warning("No VPC evidence files found in directory")
            return NotebookInventoryResult(
                analyses=[],
                total_vpcs=0,
                total_nat_gateways=0,
                total_interface_vpce=0,
                total_gateway_vpce=0,
                total_monthly_cost=Decimal("0.00"),
                summary_table=self._create_empty_summary_table(),
            )

        console.print(f"📊 Discovered {len(vpc_ids)} VPCs with evidence files")

        # Process each VPC with progress bar
        analyses: List[VPCAnalysis] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Analyzing {len(vpc_ids)} VPCs...", total=len(vpc_ids))

            for vpc_id in vpc_ids:
                try:
                    # Load VPC resources from evidence files
                    resources = self.evidence_loader.load_vpc_resources(vpc_id)

                    # Get VPC metadata from config OR use defaults
                    metadata = self._get_vpc_metadata(vpc_id)

                    # Calculate cost breakdown
                    cost_breakdown = self.cost_calculator.calculate_cost_breakdown(resources)

                    # Calculate technical and business scores
                    technical_score = self.scoring_engine.calculate_technical_score(resources)
                    business_score = self.scoring_engine.calculate_business_score(metadata.environment)

                    # Determine three-bucket categorization
                    three_bucket = self._categorize_vpc(resources, technical_score, business_score)

                    # Generate recommendation with rationale
                    recommendation, rationale = self.recommendation_engine.generate_recommendation(
                        resources, cost_breakdown, three_bucket
                    )

                    # Create VPCAnalysis object
                    analysis = VPCAnalysis(
                        metadata=metadata,
                        resources=resources,
                        cost_breakdown=cost_breakdown,
                        technical_score=technical_score,
                        business_score=business_score,
                        three_bucket=three_bucket,
                        recommendation=recommendation,
                        rationale=rationale,
                    )

                    analyses.append(analysis)

                except Exception as e:
                    print_error(f"Failed to analyze VPC {vpc_id}: {e}")
                    continue

                progress.advance(task)

        # Calculate aggregate statistics
        total_nat_gateways = sum(a.resources.nat_gateways for a in analyses)
        total_interface_vpce = sum(a.resources.vpce_interface for a in analyses)
        total_gateway_vpce = sum(a.resources.vpce_gateway for a in analyses)
        total_monthly_cost = sum(a.cost_breakdown.total_monthly_cost for a in analyses)

        # Generate summary table
        summary_table = self._create_summary_table(
            total_vpcs=len(analyses),
            total_nat_gateways=total_nat_gateways,
            total_interface_vpce=total_interface_vpce,
            total_gateway_vpce=total_gateway_vpce,
            total_monthly_cost=total_monthly_cost,
        )

        print_success(f"✅ Analyzed {len(analyses)} VPCs successfully")

        return NotebookInventoryResult(
            analyses=analyses,
            total_vpcs=len(analyses),
            total_nat_gateways=total_nat_gateways,
            total_interface_vpce=total_interface_vpce,
            total_gateway_vpce=total_gateway_vpce,
            total_monthly_cost=total_monthly_cost,
            summary_table=summary_table,
        )

    def _discover_vpc_ids(self) -> List[str]:
        """
        Discover VPC IDs from evidence directory.

        Evidence files follow naming pattern: {vpc_id}-{resource_type}.json
        Example: vpc-007462e1e648ef6de-enis.json

        Returns:
            List of unique VPC IDs found in evidence directory
        """
        vpc_ids = set()

        # Scan directory for *-enis.json files (every VPC should have ENI evidence)
        for file_path in self.evidence_dir.glob("vpc-*-enis.json"):
            # Extract VPC ID from filename: vpc-xxx-enis.json -> vpc-xxx
            vpc_id = file_path.stem.rsplit("-enis", 1)[0]
            vpc_ids.add(vpc_id)

        return sorted(vpc_ids)

    def _get_vpc_metadata(self, vpc_id: str) -> VPCMetadata:
        """
        Get VPC metadata from configuration OR use intelligent defaults.

        Priority:
        1. Configuration file (vpc-config.yaml)
        2. AWS profile mapping (aws_profiles dict)
        3. Intelligent defaults (environment from VPC ID pattern)

        Args:
            vpc_id: VPC identifier

        Returns:
            VPCMetadata: VPC metadata with account/environment information
        """
        # Try to get from configuration manager
        config = self.config_manager.get_config(vpc_id)

        if config:
            return VPCMetadata(
                vpc_id=vpc_id,
                account_id=config.account_id,
                account_name=config.account_name,
                environment=config.environment,
                vpc_name=config.vpc_name,
                region=config.region,
                profile=config.profile,
            )

        # Fallback: Use intelligent defaults
        # Extract environment from VPC name pattern (if available)
        environment = "unknown"

        # Get AWS profile from mapping if available
        profile = self.aws_profiles.get(vpc_id)

        return VPCMetadata(
            vpc_id=vpc_id,
            account_id="unknown",
            account_name="",
            environment=environment,
            vpc_name="",
            region="ap-southeast-2",
            profile=profile,
        )

    def _categorize_vpc(self, resources: VPCResources, technical_score: int, business_score: int) -> str:
        """
        Categorize VPC into three-bucket decommissioning classification.

        Decision Logic:
        - MUST DELETE: 0 ENIs (no network activity)
        - SHOULD NOT DELETE: High technical score OR high business score
        - COULD DELETE: Medium complexity with low business impact

        Args:
            resources: VPC resource counts
            technical_score: Technical complexity score (0-100)
            business_score: Business criticality score (0-100)

        Returns:
            Three-bucket classification: "MUST DELETE" | "COULD DELETE" | "SHOULD NOT DELETE"
        """
        # MUST DELETE: Zero network activity
        if resources.enis == 0:
            return "MUST DELETE"

        # SHOULD NOT DELETE: High complexity or high business impact
        if technical_score >= 50 or business_score >= 50:
            return "SHOULD NOT DELETE"

        # COULD DELETE: Medium complexity with low business impact
        return "COULD DELETE"

    def _create_summary_table(
        self,
        total_vpcs: int,
        total_nat_gateways: int,
        total_interface_vpce: int,
        total_gateway_vpce: int,
        total_monthly_cost: Decimal,
    ) -> Table:
        """
        Create Rich CLI summary table with aggregate statistics.

        Args:
            total_vpcs: Total number of VPCs analyzed
            total_nat_gateways: Aggregate NAT Gateway count
            total_interface_vpce: Aggregate Interface VPCE count
            total_gateway_vpce: Aggregate Gateway VPCE count
            total_monthly_cost: Aggregate monthly cost

        Returns:
            Rich Table: Summary statistics table
        """
        table = create_table(
            title="VPC Inventory Summary",
            columns=[
                {"name": "Metric", "justify": "left"},
                {"name": "Value", "justify": "right"},
                {"name": "Annual Cost", "justify": "right"},
            ],
        )

        table.add_row("Total VPCs", str(total_vpcs), "")
        table.add_row(
            "NAT Gateways", str(total_nat_gateways), format_cost(float(total_nat_gateways * Decimal("32.85") * 12))
        )
        table.add_row(
            "Interface VPCEs",
            str(total_interface_vpce),
            format_cost(float(total_interface_vpce * Decimal("7.30") * 12)),
        )
        table.add_row("Gateway VPCEs (FREE)", str(total_gateway_vpce), "$0.00")
        table.add_row(
            "[bold]Total Monthly Cost[/bold]",
            f"[bold]{format_cost(float(total_monthly_cost))}[/bold]",
            f"[bold]{format_cost(float(total_monthly_cost * 12))}[/bold]",
        )

        return table

    def _create_empty_summary_table(self) -> Table:
        """
        Create empty summary table for zero VPCs scenario.

        Returns:
            Rich Table: Empty summary table
        """
        return self._create_summary_table(
            total_vpcs=0,
            total_nat_gateways=0,
            total_interface_vpce=0,
            total_gateway_vpce=0,
            total_monthly_cost=Decimal("0.00"),
        )

    def create_decision_matrix_table(self, analyses: List[VPCAnalysis]) -> Table:
        """
        Generate 16-column manager decision table using VPCTableFormatter.

        Columns:
        1. VPC ID
        2. Account
        3. Env
        4. NAT GWs
        5. Interface VPCEs
        6. Gateway VPCEs
        7. ENI
        8. TGW
        9. EC2
        10. Lambda
        11. RDS
        12. LBs
        13. Monthly Cost
        14. Tech Score
        15. Biz Score
        16. Three-Bucket
        17. Recommendation
        18. Rationale

        Args:
            analyses: List of VPC analysis results

        Returns:
            Rich Table: Manager decision matrix with all VPCs

        Example:
            table = service.create_decision_matrix_table(result.analyses)
            console.print(table)
        """
        return self.formatter.create_decision_matrix_table(analyses)

    def display_configuration_summary(self) -> None:
        """
        Display Rich panel showing VPC configuration summary.

        Shows:
        - Total VPCs configured
        - Configuration source (YAML/JSON/discovery)
        - Grouping by landing zone or account

        Example:
            service.display_configuration_summary()
        """
        vpcs = self.config_manager.get_all_configs()

        if not vpcs:
            console.print(
                Panel(
                    "[yellow]No VPC configuration loaded[/yellow]\n"
                    "VPCs will be discovered from evidence directory with default metadata",
                    title="VPC Configuration Status",
                    border_style="yellow",
                )
            )
            return

        # Group VPCs by account
        by_account: Dict[str, List[VPCConfig]] = {}
        for vpc in vpcs:
            account = vpc.account_name or vpc.account_id or "unknown"
            if account not in by_account:
                by_account[account] = []
            by_account[account].append(vpc)

        # Build configuration summary
        summary_lines = []
        summary_lines.append(f"[bold]Total VPCs Configured:[/bold] {len(vpcs)}")
        summary_lines.append("")

        for account, account_vpcs in sorted(by_account.items()):
            summary_lines.append(f"[bold]{account}[/bold] ({len(account_vpcs)} VPCs)")
            for vpc in sorted(account_vpcs, key=lambda v: v.vpc_id):
                env_color = "green" if vpc.environment == "prod" else "yellow"
                summary_lines.append(
                    f"  • {vpc.vpc_id} [{env_color}]{vpc.environment}[/{env_color}] "
                    f"(profile: {vpc.profile or 'default'})"
                )
            summary_lines.append("")

        console.print(
            Panel(
                "\n".join(summary_lines),
                title="VPC Configuration Summary",
                border_style="green",
            )
        )

    def get_business_summary(self, analyses: List[VPCAnalysis]) -> Dict[str, Any]:
        """
        Generate executive summary with financial KPIs.

        Returns dict with:
        - total_vpcs: Number of VPCs analyzed
        - total_nat_gateways: Aggregate NAT Gateway count
        - total_interface_vpce: Aggregate Interface VPCE count
        - total_gateway_vpce: Aggregate Gateway VPCE count (FREE)
        - total_monthly_cost: Aggregate monthly infrastructure cost
        - baseline_target: Target monthly cost (25% reduction assumption)
        - variance_amount: Difference from baseline target
        - variance_percent: Percentage variance from target
        - variance_status: "ABOVE" | "ON_TARGET" | "BELOW"
        - must_delete_count: VPCs in "MUST DELETE" bucket
        - could_delete_count: VPCs in "COULD DELETE" bucket
        - retain_count: VPCs in "SHOULD NOT DELETE" bucket
        - must_delete_savings: Potential monthly savings from MUST DELETE VPCs
        - could_delete_savings: Potential monthly savings from COULD DELETE VPCs

        Args:
            analyses: List of VPC analysis results

        Returns:
            Dict with business KPIs and financial metrics

        Example:
            summary = service.get_business_summary(result.analyses)
            print(f"Total Cost: ${summary['total_monthly_cost']}/month")
            print(f"Savings Potential: ${summary['must_delete_savings']}/month")
        """
        total_vpcs = len(analyses)
        total_nat_gateways = sum(a.resources.nat_gateways for a in analyses)
        total_interface_vpce = sum(a.resources.vpce_interface for a in analyses)
        total_gateway_vpce = sum(a.resources.vpce_gateway for a in analyses)
        total_monthly_cost = sum(a.cost_breakdown.total_monthly_cost for a in analyses)

        # Categorize VPCs
        must_delete = [a for a in analyses if a.three_bucket == "MUST DELETE"]
        could_delete = [a for a in analyses if a.three_bucket == "COULD DELETE"]
        retain = [a for a in analyses if a.three_bucket == "SHOULD NOT DELETE"]

        # Calculate savings potential
        must_delete_savings = sum(a.cost_breakdown.total_monthly_cost for a in must_delete)
        could_delete_savings = sum(a.cost_breakdown.total_monthly_cost for a in could_delete)

        # Calculate variance from target (assume 25% reduction target)
        baseline_target = total_monthly_cost * Decimal("0.75")
        variance_amount = total_monthly_cost - baseline_target
        variance_percent = (variance_amount / total_monthly_cost * 100) if total_monthly_cost > 0 else Decimal("0.00")

        # Determine variance status
        if variance_amount > 0:
            variance_status = "ABOVE"
        elif variance_amount < 0:
            variance_status = "BELOW"
        else:
            variance_status = "ON_TARGET"

        return {
            "total_vpcs": total_vpcs,
            "total_nat_gateways": total_nat_gateways,
            "total_interface_vpce": total_interface_vpce,
            "total_gateway_vpce": total_gateway_vpce,
            "total_monthly_cost": float(total_monthly_cost),
            "baseline_target": float(baseline_target),
            "variance_amount": float(variance_amount),
            "variance_percent": float(variance_percent),
            "variance_status": variance_status,
            "must_delete_count": len(must_delete),
            "could_delete_count": len(could_delete),
            "retain_count": len(retain),
            "must_delete_savings": float(must_delete_savings),
            "could_delete_savings": float(could_delete_savings),
            "total_savings_potential": float(must_delete_savings + could_delete_savings),
        }

    def analyze_vpc_from_csv(self, csv_file: Path, profile: Optional[str] = None) -> VPCCSVAnalysisResult:
        """
        One-line notebook operation for VPC cleanup analysis from CSV.

        Replaces 140 lines of inline notebook code with enterprise-validated logic.

        This method consolidates:
        - CSV loading with pandas
        - ENI Gate safety validation (ENI=0 vs ENI>0 logic)
        - Three-Bucket classification (MUST/COULD/RETAIN)
        - Cost parsing and aggregation
        - Rich CLI tables for manager review

        Args:
            csv_file: Path to vpc-cleanup.csv (15 VPCs with ENI/EC2/Lambda/NAT columns)
            profile: Optional AWS profile for validation (future enhancement)

        Returns:
            VPCCSVAnalysisResult with:
                - Three-Bucket classification (MUST/COULD/RETAIN)
                - ENI Gate safety validation
                - Cost breakdown
                - Rich CLI tables for manager review

        Raises:
            ValueError: If CSV file doesn't exist or has invalid schema
            pd.errors.ParserError: If CSV parsing fails

        Example:
            service = VPCNotebookService()
            result = service.analyze_vpc_from_csv(Path("data/vpc-cleanup.csv"))
            console.print(result.summary_table)
            console.print(result.classification_table)
        """
        # Validate CSV file exists
        if not csv_file.exists():
            raise ValueError(f"CSV file not found: {csv_file}\nExpected location: data/vpc-cleanup.csv")

        console.print(f"[bold]Loading VPC cleanup data from CSV...[/bold] {csv_file}")

        try:
            # Load CSV with pandas
            df = pd.read_csv(csv_file)

            # Validate required columns
            required_cols = ["vpc_id", "ENI", "EC2", "Lambda", "NAT", "Env", "Cost/Mo"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"CSV missing required columns: {missing_cols}")

            console.print(f"✅ Loaded {len(df)} VPCs from CSV")

        except pd.errors.ParserError as e:
            raise ValueError(f"Failed to parse CSV file: {e}") from e

        # Initialize result buckets
        must_delete: List[Dict[str, Any]] = []
        could_delete: List[Dict[str, Any]] = []
        retain: List[Dict[str, Any]] = []
        eni_gate_results: List[Dict[str, Any]] = []
        total_monthly_cost = Decimal("0.00")

        # Process each VPC row
        for idx, row in df.iterrows():
            vpc_id = row["vpc_id"]
            eni_count = int(row["ENI"]) if pd.notna(row["ENI"]) else 0
            ec2_count = int(row["EC2"]) if pd.notna(row["EC2"]) else 0
            lambda_count = int(row["Lambda"]) if pd.notna(row["Lambda"]) else 0
            nat_count = int(row["NAT"]) if pd.notna(row["NAT"]) else 0
            env = row["Env"] if pd.notna(row["Env"]) else "unknown"

            # Parse cost from CSV (handle "$106 " format)
            cost_str = str(row["Cost/Mo"]) if pd.notna(row["Cost/Mo"]) else "$0"
            cost_value = self._parse_cost_from_csv(cost_str)
            total_monthly_cost += cost_value

            # ENI Gate validation logic
            if eni_count == 0:
                safety_status = "✅ SAFE - Zero ENI"
                risk_level = "LOW"
            elif ec2_count > 0 or lambda_count > 0:
                safety_status = "⚠️ WORKLOAD - Active compute"
                risk_level = "HIGH"
            elif nat_count > 0 and ec2_count == 0:
                safety_status = "🟡 ORPHANED - NAT only"
                risk_level = "MEDIUM"
            else:
                safety_status = "🔍 REVIEW - Manual check"
                risk_level = "MEDIUM"

            # Store ENI gate result
            eni_gate_results.append(
                {
                    "vpc_id": vpc_id,
                    "eni_count": eni_count,
                    "safety_status": safety_status,
                    "risk_level": risk_level,
                }
            )

            # Three-Bucket classification logic (follows decision tree priority)
            # Priority 1: EC2 instances = RETAIN
            if ec2_count > 0:
                bucket = "RETAIN"
                confidence = "HIGH"
            # Priority 2: Lambda functions = RETAIN
            elif lambda_count > 0:
                bucket = "RETAIN"
                confidence = "MEDIUM"
            # Priority 3: Zero ENIs = MUST DELETE (only if no EC2/Lambda above)
            elif eni_count == 0:
                bucket = "MUST DELETE"
                confidence = "HIGH"
            # Priority 4: Orphaned NAT (NAT > 0 but no EC2/Lambda)
            elif nat_count > 0 and ec2_count == 0 and lambda_count == 0:
                bucket = "COULD DELETE"
                confidence = "MEDIUM"
            # Priority 5: Production environment = RETAIN
            elif env == "prod":
                bucket = "RETAIN"
                confidence = "HIGH"
            # Default: RETAIN with low confidence
            else:
                bucket = "RETAIN"
                confidence = "LOW"

            # VPC record with classification
            vpc_record = {
                "vpc_id": vpc_id,
                "env": env,
                "eni": eni_count,
                "ec2": ec2_count,
                "lambda": lambda_count,
                "nat": nat_count,
                "cost_monthly": float(cost_value),
                "bucket": bucket,
                "confidence": confidence,
                "safety_status": safety_status,
                "risk_level": risk_level,
            }

            # Categorize into buckets
            if bucket == "MUST DELETE":
                must_delete.append(vpc_record)
            elif bucket == "COULD DELETE":
                could_delete.append(vpc_record)
            else:
                retain.append(vpc_record)

        # Generate Rich CLI summary table
        summary_table = self._create_csv_summary_table(
            total_vpcs=len(df),
            must_delete_count=len(must_delete),
            could_delete_count=len(could_delete),
            retain_count=len(retain),
            total_monthly_cost=total_monthly_cost,
        )

        # Generate Rich CLI classification table
        classification_table = self._create_csv_classification_table(
            must_delete=must_delete, could_delete=could_delete, retain=retain
        )

        print_success(
            f"✅ Analyzed {len(df)} VPCs: "
            f"{len(must_delete)} MUST DELETE, "
            f"{len(could_delete)} COULD DELETE, "
            f"{len(retain)} RETAIN"
        )

        return VPCCSVAnalysisResult(
            total_vpcs=len(df),
            must_delete=must_delete,
            could_delete=could_delete,
            retain=retain,
            eni_gate_results=eni_gate_results,
            total_monthly_cost=total_monthly_cost,
            summary_table=summary_table,
            classification_table=classification_table,
            csv_data=df,
        )

    def _parse_cost_from_csv(self, cost_str: str) -> Decimal:
        """
        Parse cost value from CSV format ("$106 " -> 106.00).

        Handles various cost formats from CSV:
        - "$106 " -> 106.00
        - "$0" -> 0.00
        - "99" -> 99.00
        - Empty/NaN -> 0.00

        Args:
            cost_str: Cost string from CSV

        Returns:
            Decimal: Parsed cost value
        """
        # Remove whitespace, dollar signs, commas
        cleaned = re.sub(r"[\$,\s]", "", str(cost_str))

        # Handle empty or NaN values
        if not cleaned or cleaned.lower() == "nan":
            return Decimal("0.00")

        try:
            return Decimal(cleaned)
        except Exception:
            # Fallback for unparseable values
            return Decimal("0.00")

    def _create_csv_summary_table(
        self,
        total_vpcs: int,
        must_delete_count: int,
        could_delete_count: int,
        retain_count: int,
        total_monthly_cost: Decimal,
    ) -> Table:
        """
        Create Rich CLI summary table for CSV analysis.

        Args:
            total_vpcs: Total VPCs analyzed
            must_delete_count: VPCs in MUST DELETE bucket
            could_delete_count: VPCs in COULD DELETE bucket
            retain_count: VPCs in RETAIN bucket
            total_monthly_cost: Aggregate monthly cost

        Returns:
            Rich Table: Summary table with classification breakdown
        """
        table = create_table(
            title="VPC Cleanup Analysis Summary",
            columns=[
                {"name": "Classification", "justify": "left"},
                {"name": "Count", "justify": "right"},
                {"name": "Percentage", "justify": "right"},
            ],
        )

        # Calculate percentages
        must_pct = (must_delete_count / total_vpcs * 100) if total_vpcs > 0 else 0
        could_pct = (could_delete_count / total_vpcs * 100) if total_vpcs > 0 else 0
        retain_pct = (retain_count / total_vpcs * 100) if total_vpcs > 0 else 0

        table.add_row(
            "[red]🔴 MUST DELETE[/red]",
            str(must_delete_count),
            f"{must_pct:.1f}%",
        )
        table.add_row(
            "[yellow]🟡 COULD DELETE[/yellow]",
            str(could_delete_count),
            f"{could_pct:.1f}%",
        )
        table.add_row(
            "[green]🟢 RETAIN[/green]",
            str(retain_count),
            f"{retain_pct:.1f}%",
        )
        table.add_row(
            "[bold]Total VPCs[/bold]",
            f"[bold]{total_vpcs}[/bold]",
            "[bold]100.0%[/bold]",
        )
        table.add_row(
            "[bold]Total Monthly Cost[/bold]",
            f"[bold]{format_cost(float(total_monthly_cost))}[/bold]",
            "",
        )

        return table

    def _create_csv_classification_table(
        self,
        must_delete: List[Dict[str, Any]],
        could_delete: List[Dict[str, Any]],
        retain: List[Dict[str, Any]],
    ) -> Table:
        """
        Create Rich CLI classification table showing per-VPC details.

        Args:
            must_delete: VPCs in MUST DELETE bucket
            could_delete: VPCs in COULD DELETE bucket
            retain: VPCs in RETAIN bucket

        Returns:
            Rich Table: Per-VPC classification details
        """
        table = create_table(
            title="VPC Classification Details",
            columns=[
                {"name": "VPC ID", "justify": "left"},
                {"name": "Env", "justify": "center"},
                {"name": "ENI", "justify": "right"},
                {"name": "EC2", "justify": "right"},
                {"name": "Lambda", "justify": "right"},
                {"name": "NAT", "justify": "right"},
                {"name": "Cost/Mo", "justify": "right"},
                {"name": "Classification", "justify": "center"},
                {"name": "Safety Status", "justify": "left"},
            ],
        )

        # Add MUST DELETE VPCs (red)
        for vpc in must_delete:
            table.add_row(
                f"[red]{vpc['vpc_id']}[/red]",
                vpc["env"],
                str(vpc["eni"]),
                str(vpc["ec2"]),
                str(vpc["lambda"]),
                str(vpc["nat"]),
                format_cost(vpc["cost_monthly"]),
                "[red]🔴 MUST DELETE[/red]",
                vpc["safety_status"],
            )

        # Add COULD DELETE VPCs (yellow)
        for vpc in could_delete:
            table.add_row(
                f"[yellow]{vpc['vpc_id']}[/yellow]",
                vpc["env"],
                str(vpc["eni"]),
                str(vpc["ec2"]),
                str(vpc["lambda"]),
                str(vpc["nat"]),
                format_cost(vpc["cost_monthly"]),
                "[yellow]🟡 COULD DELETE[/yellow]",
                vpc["safety_status"],
            )

        # Add RETAIN VPCs (green)
        for vpc in retain:
            table.add_row(
                f"[green]{vpc['vpc_id']}[/green]",
                vpc["env"],
                str(vpc["eni"]),
                str(vpc["ec2"]),
                str(vpc["lambda"]),
                str(vpc["nat"]),
                format_cost(vpc["cost_monthly"]),
                "[green]🟢 RETAIN[/green]",
                vpc["safety_status"],
            )

        return table

    def enrich_with_cost_explorer(
        self, csv_data: pd.DataFrame, billing_profile: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enrich VPC CSV data with actual last month costs from AWS Cost Explorer.

        Reuses VPCE pattern from vpce_cleanup_manager.py enrich_with_last_month_costs().

        Args:
            csv_data: DataFrame from analyze_vpc_from_csv() result
            billing_profile: AWS billing profile (defaults to VPCE_BILLING_PROFILE from config)

        Returns:
            Enrichment results: {
                'status': 'success'|'partial'|'failed',
                'last_month_total': float,
                'calculated_total': float,
                'enriched_count': int,
                'fallback_count': int,
                'variance': float,
                'accounts_with_data': int
            }

        Raises:
            ValueError: If billing_profile validation fails (ProfileNotFound)

        Example:
            >>> result = service.analyze_vpc_from_csv(Path("data/vpc-cleanup.csv"))
            >>> enrichment = service.enrich_with_cost_explorer(
            ...     csv_data=result.csv_data,
            ...     billing_profile="${BILLING_PROFILE}"
            ... )
            >>> console.print(f"✅ Enriched: {enrichment['status']}")
        """
        import boto3
        from runbooks.vpc.config import VPCE_BILLING_PROFILE, get_last_billing_month
        from runbooks.vpc.profile_validator import validate_profile
        from datetime import datetime, timedelta

        # Use billing profile from config if not provided
        if billing_profile is None:
            billing_profile = VPCE_BILLING_PROFILE

        # Pre-flight profile validation (fail-fast pattern)
        print_info(f"🔍 Validating AWS billing profile: {billing_profile}")
        validation = validate_profile(billing_profile)

        if not validation["valid"]:
            raise ValueError(
                f"Billing profile validation failed: {billing_profile}\n"
                f"Error: {validation['error']}\n"
                f"Fix: Ensure profile exists in ~/.aws/config with valid credentials"
            )

        print_success(f"✅ Profile validated: account {validation['account_id']}")

        # Get last month period dynamically
        last_month = get_last_billing_month()
        today = datetime.now()
        first_of_this_month = today.replace(day=1)
        last_month_date = first_of_this_month - timedelta(days=1)
        start_date = last_month_date.replace(day=1).strftime("%Y-%m-%d")
        end_date = (first_of_this_month).strftime("%Y-%m-%d")

        print_info(f"🔍 Retrieving {last_month} VPC costs from Cost Explorer (profile: {billing_profile})...")

        try:
            session = boto3.Session(profile_name=billing_profile)
            ce_client = session.client("ce")

            # Query Cost Explorer for VPC costs by account
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date,
                    "End": end_date,
                },
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                Filter={
                    "Dimensions": {
                        "Key": "SERVICE",
                        "Values": ["Amazon Virtual Private Cloud"],  # VPC service includes all VPC costs
                    }
                },
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}  # Group by account
                ],
            )

            # Extract last month actual costs by account
            last_month_costs_by_account = {}
            total_last_month = 0.0

            if response["ResultsByTime"]:
                for group in response["ResultsByTime"][0]["Groups"]:
                    account_id = group["Keys"][0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    last_month_costs_by_account[account_id] = cost
                    total_last_month += cost

            print_success(
                f"✅ Retrieved {last_month} billing: {format_cost(total_last_month)} across {len(last_month_costs_by_account)} accounts"
            )

            # Enrich CSV data with actual last month costs
            enriched_count = 0
            fallback_count = 0
            calculated_total = 0.0

            # Add actual_cost column to DataFrame
            csv_data["actual_last_month_cost"] = 0.0

            for idx, row in csv_data.iterrows():
                account_id = str(row["account_id"])
                calculated_cost = self._parse_cost_from_csv(row["Cost/Mo"])
                calculated_total += float(calculated_cost)

                if account_id in last_month_costs_by_account:
                    # Use actual last month cost for this account
                    actual_cost = last_month_costs_by_account[account_id]
                    csv_data.at[idx, "actual_last_month_cost"] = actual_cost
                    enriched_count += 1
                else:
                    # Fallback to calculated costs
                    csv_data.at[idx, "actual_last_month_cost"] = float(calculated_cost)
                    fallback_count += 1
                    print_warning(f"⚠️  No {last_month} billing data for account {account_id}, using calculated costs")

            # Determine enrichment status
            total_rows = len(csv_data)
            if enriched_count == total_rows:
                status = "success"
                status_msg = f"✅ All {enriched_count} VPCs enriched with {last_month} actual costs"
            elif enriched_count > 0:
                status = "partial"
                status_msg = f"⚠️  Partial enrichment: {enriched_count} actual, {fallback_count} calculated"
            else:
                status = "failed"
                status_msg = f"❌ No {last_month} data available, using calculated costs for all {fallback_count} VPCs"

            console.print(status_msg)

            return {
                "status": status,
                "last_month_total": total_last_month * 12,  # Annualized
                "last_month": last_month,  # Track which month was used
                "calculated_total": calculated_total * 12,  # Annualized
                "enriched_count": enriched_count,
                "fallback_count": fallback_count,
                "variance": abs(total_last_month * 12 - calculated_total * 12),
                "accounts_with_data": len(last_month_costs_by_account),
            }

        except Exception as e:
            print_error(f"❌ Failed to retrieve {last_month} billing data: {e}")
            print_warning("⚠️  Falling back to calculated costs (pricing API)")

            return {
                "status": "failed",
                "error": str(e),
                "last_month": last_month,
                "calculated_total": 0.0,
                "enriched_count": 0,
                "fallback_count": len(csv_data),
            }

    def validate_with_aws_api(self, csv_data: pd.DataFrame, management_profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate VPCs exist via AWS API (DescribeVpcs) across accounts.

        Args:
            csv_data: DataFrame from analyze_vpc_from_csv() result
            management_profile: AWS profile with cross-account access (defaults to AWS_PROFILE)

        Returns:
            Validation results: {
                'exists': List[str],  # VPC IDs confirmed to exist
                'not_found': List[str],  # VPC IDs not found
                'errors': Dict[str, str],  # VPC ID -> error message
                'accuracy': float,  # Percentage of VPCs validated successfully
                'accounts_validated': int
            }

        Example:
            >>> result = service.analyze_vpc_from_csv(Path("data/vpc-cleanup.csv"))
            >>> validation = service.validate_with_aws_api(
            ...     csv_data=result.csv_data,
            ...     management_profile="default"
            ... )
            >>> console.print(f"✅ Accuracy: {validation['accuracy']}%")
        """
        import boto3
        from botocore.exceptions import ClientError, ProfileNotFound

        # Use AWS_PROFILE if management_profile not provided
        if management_profile is None:
            management_profile = os.getenv("AWS_PROFILE", "default")

        print_info(f"🔍 Validating VPCs with AWS API (profile: {management_profile})...")

        # Extract VPC IDs and profiles from CSV
        vpc_ids = csv_data["vpc_id"].tolist()
        profiles = csv_data["AWS-Profile"].tolist()

        exists = []
        not_found = []
        errors = {}
        accounts_validated = set()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Validating {len(vpc_ids)} VPCs...", total=len(vpc_ids))

            for idx, vpc_id in enumerate(vpc_ids):
                profile = profiles[idx]
                try:
                    # Create session with per-account profile
                    session = boto3.Session(profile_name=profile)
                    ec2_client = session.client("ec2", region_name="ap-southeast-2")

                    # Call DescribeVpcs API
                    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])

                    if response["Vpcs"]:
                        exists.append(vpc_id)
                        accounts_validated.add(profile)
                    else:
                        not_found.append(vpc_id)

                except ClientError as e:
                    if e.response["Error"]["Code"] == "InvalidVpcID.NotFound":
                        not_found.append(vpc_id)
                    else:
                        errors[vpc_id] = f"{e.response['Error']['Code']}: {e.response['Error']['Message']}"

                except ProfileNotFound as e:
                    errors[vpc_id] = f"ProfileNotFound: {profile}"

                except Exception as e:
                    errors[vpc_id] = str(e)

                progress.advance(task)

        # Calculate accuracy
        total_validated = len(exists) + len(not_found)
        accuracy = (len(exists) / total_validated * 100) if total_validated > 0 else 0.0

        print_success(f"✅ Validated {len(exists)}/{len(vpc_ids)} VPCs ({accuracy:.1f}% accuracy)")

        if not_found:
            print_warning(f"⚠️  {len(not_found)} VPCs not found: {', '.join(not_found[:5])}")

        if errors:
            print_error(f"❌ {len(errors)} validation errors")

        return {
            "exists": exists,
            "not_found": not_found,
            "errors": errors,
            "accuracy": accuracy,
            "accounts_validated": len(accounts_validated),
        }

    def generate_cleanup_scripts(
        self, must_delete_vpcs: List[Dict[str, Any]], output_dir: Path, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Generate cleanup scripts (bash + boto3) for VPC deletion.

        Adapts VPCE script generation pattern for VPC deletion.

        Args:
            must_delete_vpcs: VPCs classified as MUST DELETE from analyze_vpc_from_csv()
            output_dir: Directory to write scripts (e.g., Path("data/scripts"))
            dry_run: Generate DryRun=True scripts (default: True for safety)

        Returns:
            Script generation results: {
                'file_count': int,
                'bash_scripts': List[str],
                'boto3_scripts': List[str],
                'master_script': str
            }

        Example:
            >>> result = service.analyze_vpc_from_csv(Path("data/vpc-cleanup.csv"))
            >>> scripts = service.generate_cleanup_scripts(
            ...     must_delete_vpcs=result.must_delete,
            ...     output_dir=Path("data/scripts"),
            ...     dry_run=True
            ... )
            >>> console.print(f"✅ Generated {scripts['file_count']} scripts")
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        bash_scripts = []
        boto3_scripts = []

        print_info(f"🔍 Generating cleanup scripts for {len(must_delete_vpcs)} VPCs...")

        # Group VPCs by account for per-account scripts
        vpcs_by_account = {}
        for vpc in must_delete_vpcs:
            account_id = vpc.get("vpc_id", "").split("-")[0]  # Extract from vpc_id if needed
            # Use actual account_id from CSV if available in vpc dict structure
            if "account_id" in vpc:
                account_id = vpc["account_id"]

            if account_id not in vpcs_by_account:
                vpcs_by_account[account_id] = []
            vpcs_by_account[account_id].append(vpc)

        # Generate per-account scripts
        for account_id, account_vpcs in vpcs_by_account.items():
            # Bash script
            bash_script_path = output_dir / f"vpc-cleanup-{account_id}.sh"
            bash_content = self._generate_bash_script(account_vpcs, dry_run)
            bash_script_path.write_text(bash_content)
            bash_script_path.chmod(0o755)  # Make executable
            bash_scripts.append(str(bash_script_path))

            # Boto3 Python script
            boto3_script_path = output_dir / f"vpc-cleanup-{account_id}.py"
            boto3_content = self._generate_boto3_script(account_vpcs, dry_run)
            boto3_script_path.write_text(boto3_content)
            boto3_scripts.append(str(boto3_script_path))

        # Generate master script (all accounts)
        master_script_path = output_dir / "vpc-cleanup-all-accounts.sh"
        master_content = self._generate_master_script(bash_scripts)
        master_script_path.write_text(master_content)
        master_script_path.chmod(0o755)
        master_script = str(master_script_path)

        print_success(f"✅ Generated {len(bash_scripts)} bash + {len(boto3_scripts)} boto3 + 1 master script")

        return {
            "file_count": len(bash_scripts) + len(boto3_scripts) + 1,
            "bash_scripts": bash_scripts,
            "boto3_scripts": boto3_scripts,
            "master_script": master_script,
        }

    def _generate_bash_script(self, vpcs: List[Dict[str, Any]], dry_run: bool) -> str:
        """Generate bash script for VPC deletion."""
        dry_run_flag = "--dry-run" if dry_run else ""

        script_lines = [
            "#!/bin/bash",
            "# VPC Cleanup Script - Generated by VPCNotebookService",
            f"# DryRun: {dry_run}",
            "",
            "set -e  # Exit on error",
            "",
        ]

        for vpc in vpcs:
            vpc_id = vpc["vpc_id"]
            script_lines.append(f"# Delete VPC: {vpc_id}")
            script_lines.append(f"aws ec2 delete-vpc --vpc-id {vpc_id} {dry_run_flag}")
            script_lines.append("")

        return "\n".join(script_lines)

    def _generate_boto3_script(self, vpcs: List[Dict[str, Any]], dry_run: bool) -> str:
        """Generate boto3 Python script for VPC deletion with Rich CLI progress."""
        vpc_ids = [vpc["vpc_id"] for vpc in vpcs]

        script = f'''#!/usr/bin/env python3
"""
VPC Cleanup Script - Generated by VPCNotebookService
DryRun: {dry_run}
"""

import boto3
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def delete_vpcs(dry_run={str(dry_run)}):
    """Delete VPCs with Rich CLI progress tracking."""
    vpc_ids = {vpc_ids}

    ec2_client = boto3.client('ec2', region_name='ap-southeast-2')

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{{task.description}}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Deleting {{len(vpc_ids)}} VPCs...", total=len(vpc_ids))

        for vpc_id in vpc_ids:
            try:
                console.print(f"[yellow]Deleting VPC: {{vpc_id}}[/yellow]")
                ec2_client.delete_vpc(VpcId=vpc_id, DryRun=dry_run)
                console.print(f"[green]✅ Deleted: {{vpc_id}}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed {{vpc_id}}: {{e}}[/red]")

            progress.advance(task)

    console.print(f"[bold green]✅ VPC cleanup complete[/bold green]")

if __name__ == "__main__":
    delete_vpcs()
'''
        return script

    def _generate_master_script(self, bash_scripts: List[str]) -> str:
        """Generate master script to execute all per-account scripts."""
        script_lines = [
            "#!/bin/bash",
            "# Master VPC Cleanup Script - Executes all account-specific scripts",
            "",
            "set -e  # Exit on error",
            "",
        ]

        for script_path in bash_scripts:
            script_lines.append(f"echo 'Executing: {script_path}'")
            script_lines.append(f"bash {script_path}")
            script_lines.append("")

        script_lines.append("echo '✅ All VPC cleanup scripts executed'")

        return "\n".join(script_lines)

    def export_vpc_analysis_to_markdown(
        self, vpc_df: pd.DataFrame, output_dir: Path = Path("data/outputs"), title: str = "VPC Cleanup Analysis"
    ) -> Dict:
        """
        Export VPC analysis DataFrame to markdown format.

        Args:
            vpc_df: VPC analysis DataFrame with recommendations
            output_dir: Output directory for markdown file
            title: Title for markdown document

        Returns:
            Dict with status and file_path

        Example:
            >>> result = service.export_vpc_analysis_to_markdown(
            ...     vpc_df=df,
            ...     output_dir=Path("data/outputs"),
            ...     title="VPC Cleanup Analysis"
            ... )
            >>> result['status']
            'success'
            >>> Path(result['file_path']).exists()
            True
        """
        from datetime import datetime

        try:
            # Create output directory if needed
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"vpc-cleanup-{timestamp}.md"
            file_path = output_dir / filename

            # Build markdown content
            lines = []

            # Title
            lines.append(f"# {title}\n")

            # Metadata section
            lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**VPCs:** {len(vpc_df)}\n")

            # Group by recommendation
            if "recommendation" in vpc_df.columns:
                recommendation_counts = vpc_df["recommendation"].value_counts().to_dict()

                # Add recommendation breakdown
                for rec_type in ["MUST DELETE", "COULD DELETE", "RETAIN"]:
                    count = recommendation_counts.get(rec_type, 0)
                    if count > 0:
                        lines.append(f"\n## {rec_type} ({count} VPCs)\n")

                        # Filter DataFrame for this recommendation
                        filtered_df = vpc_df[vpc_df["recommendation"] == rec_type]

                        # Generate table
                        lines.append(self._dataframe_to_markdown_table(filtered_df))
            else:
                # No recommendation column, export entire DataFrame
                lines.append("\n## VPC Analysis\n")
                lines.append(self._dataframe_to_markdown_table(vpc_df))

            # Write to file
            content = "\n".join(lines)
            file_path.write_text(content, encoding="utf-8")

            return {
                "status": "success",
                "file_path": str(file_path),
                "vpc_count": len(vpc_df),
                "file_size": file_path.stat().st_size,
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "file_path": None}

    def _dataframe_to_markdown_table(self, df: pd.DataFrame) -> str:
        """
        Convert DataFrame to GitHub-flavored markdown table.

        Args:
            df: DataFrame to convert

        Returns:
            Markdown table string
        """
        if df.empty:
            return "_No VPCs in this category_\n"

        # Get column names
        columns = df.columns.tolist()

        # Build header row
        header = "| " + " | ".join(columns) + " |"

        # Build separator row
        separator = "| " + " | ".join(["-" * len(col) for col in columns]) + " |"

        # Build data rows
        data_rows = []
        for _, row in df.iterrows():
            row_values = [str(row[col]) for col in columns]
            data_rows.append("| " + " | ".join(row_values) + " |")

        # Combine all parts
        table_lines = [header, separator] + data_rows

        return "\n".join(table_lines) + "\n"
