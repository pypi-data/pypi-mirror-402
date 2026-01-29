#!/usr/bin/env python3
"""
VPCE Cleanup Service - High-level notebook interface

Simplifies notebook operations from multi-step workflows to single-method calls.

Architecture:
- Facade pattern over VPCECleanupManager
- High-level orchestration methods
- Parallel execution support
- Comprehensive validation
- Multi-format export

Usage (Jupyter Notebook):
    # Simple workflow (one method call)
    service = VPCECleanupService()
    results = service.run_full_workflow(
        csv_file=Path("data/vpce-cleanup.csv"),
        billing_profile="billing"
    )

    # Or step-by-step
    service = VPCECleanupService()
    service.load_from_csv(Path("data/vpce-cleanup.csv"))
    service.enrich_all(parallel=True)
    service.validate_all()
    exports = service.export_all()
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from runbooks.common.rich_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from runbooks.vpc.vpce_cleanup_manager import VPCECleanupManager


class VPCECleanupService:
    """
    Service layer for VPCE cleanup notebook operations.

    Simplifies notebook from ~100 lines to ~20 lines by providing:
    - One-call workflow orchestration
    - Parallel enrichment execution
    - Comprehensive validation
    - Multi-format export
    """

    def __init__(self):
        """Initialize VPCE cleanup service."""
        self.manager: Optional[VPCECleanupManager] = None
        self._workflow_results: Dict = {}

    def load_from_csv(self, csv_file: Path, aws_config_path: Optional[str] = None) -> None:
        """
        Load VPCE data from CSV file.

        Args:
            csv_file: Path to VPCE inventory CSV
            aws_config_path: Optional AWS config for profile enrichment

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If required columns are missing
        """
        print_info(f"Loading VPCE data from {csv_file}")
        self.manager = VPCECleanupManager.from_csv(csv_file, aws_config_path)
        print_success(f"Loaded {len(self.manager.endpoints)} VPC endpoints")

    def run_full_workflow(
        self,
        csv_file: Path,
        billing_profile: Optional[str] = None,
        enable_mcp: bool = True,
        parallel_enrichment: bool = True,
        export_formats: List[str] = ["csv", "md", "json"],
    ) -> Dict:
        """
        Execute complete VPCE cleanup workflow in one call.

        Orchestrates: Load → Enrich → Validate → Analyze → Export

        Args:
            csv_file: Path to VPCE inventory CSV
            billing_profile: AWS profile for Cost Explorer
            enable_mcp: Enable MCP validation layers
            parallel_enrichment: Execute enrichments in parallel
            export_formats: Export formats to generate

        Returns:
            Dict with workflow results and validation status

        Example:
            >>> service = VPCECleanupService()
            >>> results = service.run_full_workflow(
            ...     csv_file=Path("data/vpce-cleanup.csv"),
            ...     billing_profile="billing"
            ... )
            >>> print(results['summary'])
        """
        workflow_start = datetime.now()

        try:
            # Step 1: Load data
            print_info("Step 1/5: Loading VPCE data from CSV")
            self.load_from_csv(csv_file)

            # Step 2: Enrich with all data sources
            print_info("Step 2/5: Enriching with AWS data sources")
            enrichment_results = self.enrich_all(billing_profile=billing_profile, parallel=parallel_enrichment)

            # Step 3: Validate with MCP (if enabled)
            validation_results = {}
            if enable_mcp:
                print_info("Step 3/5: Validating with MCP and AWS APIs")
                validation_results = self.validate_all(billing_profile=billing_profile)
            else:
                print_warning("Step 3/5: MCP validation skipped")

            # Step 4: Generate analysis and recommendations
            print_info("Step 4/5: Generating analysis and recommendations")
            analysis_results = self._generate_analysis()

            # Step 5: Export to all formats
            print_info("Step 5/5: Exporting results")
            export_results = self.export_all(formats=export_formats)

            # Calculate workflow duration
            workflow_duration = (datetime.now() - workflow_start).total_seconds()

            # Compile results
            self._workflow_results = {
                "workflow_duration_seconds": workflow_duration,
                "endpoints_processed": len(self.manager.endpoints),
                "enrichment": enrichment_results,
                "validation": validation_results,
                "analysis": analysis_results,
                "exports": export_results,
                "summary": self.get_executive_summary(),
            }

            print_success(f"✅ Workflow complete in {workflow_duration:.1f}s")
            return self._workflow_results

        except Exception as e:
            print_error(f"Workflow failed: {str(e)}")
            raise

    def enrich_all(self, billing_profile: Optional[str] = None, parallel: bool = True) -> Dict:
        """
        Execute all enrichment methods.

        Enriches with:
        - Organizations API (account metadata)
        - VPC API (VPC context)
        - CloudTrail (activity analysis)
        - Cost Explorer (last month actual costs)

        Args:
            billing_profile: AWS profile for Cost Explorer
            parallel: Execute enrichments in parallel (recommended)

        Returns:
            Dict with enrichment results and timing

        Example:
            >>> service.enrich_all(billing_profile="billing", parallel=True)
            {'organizations': {...}, 'vpc': {...}, 'cloudtrail': {...}, 'costs': {...}}
        """
        if not self.manager:
            raise RuntimeError("Must call load_from_csv() first")

        enrichment_start = datetime.now()
        results = {}

        if parallel:
            # Execute enrichments in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(self._enrich_organizations): "organizations",
                    executor.submit(self._enrich_vpc): "vpc",
                    executor.submit(self._enrich_cloudtrail): "cloudtrail",
                    executor.submit(self._enrich_costs, billing_profile): "costs",
                }

                for future in as_completed(futures):
                    enrichment_type = futures[future]
                    try:
                        result = future.result()
                        results[enrichment_type] = result
                        print_success(f"✓ {enrichment_type.capitalize()} enrichment complete")
                    except Exception as e:
                        results[enrichment_type] = {"error": str(e)}
                        print_warning(f"⚠ {enrichment_type.capitalize()} enrichment failed: {str(e)}")
        else:
            # Execute enrichments sequentially
            try:
                results["organizations"] = self._enrich_organizations()
                print_success("✓ Organizations enrichment complete")
            except Exception as e:
                results["organizations"] = {"error": str(e)}
                print_warning(f"⚠ Organizations enrichment failed: {str(e)}")

            try:
                results["vpc"] = self._enrich_vpc()
                print_success("✓ VPC enrichment complete")
            except Exception as e:
                results["vpc"] = {"error": str(e)}
                print_warning(f"⚠ VPC enrichment failed: {str(e)}")

            try:
                results["cloudtrail"] = self._enrich_cloudtrail()
                print_success("✓ Cloudtrail enrichment complete")
            except Exception as e:
                results["cloudtrail"] = {"error": str(e)}
                print_warning(f"⚠ Cloudtrail enrichment failed: {str(e)}")

            try:
                results["costs"] = self._enrich_costs(billing_profile)
                print_success("✓ Costs enrichment complete")
            except Exception as e:
                results["costs"] = {"error": str(e)}
                print_warning(f"⚠ Costs enrichment failed: {str(e)}")

        enrichment_duration = (datetime.now() - enrichment_start).total_seconds()
        results["duration_seconds"] = enrichment_duration

        print_info(f"All enrichments complete in {enrichment_duration:.1f}s")
        return results

    def _enrich_organizations(self) -> Dict:
        """Enrich with Organizations API metadata."""
        return self.manager.enrich_with_account_metadata()

    def _enrich_vpc(self) -> Dict:
        """Enrich with VPC API context."""
        return self.manager.enrich_with_vpc_context()

    def _enrich_cloudtrail(self) -> Dict:
        """Enrich with CloudTrail activity data."""
        return self.manager.enrich_with_activity_data()

    def _enrich_costs(self, billing_profile: Optional[str] = None) -> Dict:
        """Enrich with Cost Explorer data."""
        return self.manager.enrich_with_last_month_costs(billing_profile=billing_profile)

    def validate_all(self, billing_profile: Optional[str] = None) -> Dict:
        """
        Execute all validation methods.

        Validates with:
        - AWS API (VPCE existence checks)
        - MCP Cost Explorer (cost variance analysis)
        - Decision framework (scoring validation)

        Args:
            billing_profile: AWS profile for Cost Explorer validation

        Returns:
            Validation results with variance metrics

        Example:
            >>> results = service.validate_all(billing_profile="billing")
            >>> print(results['cost_variance_percent'])
        """
        if not self.manager:
            raise RuntimeError("Must call load_from_csv() first")

        validation_start = datetime.now()
        results = {}

        # AWS API validation
        try:
            print_info("Validating VPCE existence with AWS API")
            aws_validation = self.manager.validate_with_aws(profile="management")
            results["aws_api"] = aws_validation
            print_success("✓ AWS API validation complete")
        except Exception as e:
            results["aws_api"] = {"error": str(e)}
            print_warning(f"⚠ AWS API validation failed: {str(e)}")

        # MCP Cost Explorer validation
        if billing_profile:
            try:
                print_info("Validating costs with MCP Cost Explorer")
                cost_validation = self.manager.compare_with_cost_explorer(profile=billing_profile)
                results["mcp_cost_explorer"] = cost_validation
                print_success("✓ MCP cost validation complete")
            except Exception as e:
                results["mcp_cost_explorer"] = {"error": str(e)}
                print_warning(f"⚠ MCP cost validation failed: {str(e)}")

        # Decision framework validation
        try:
            print_info("Calculating decision scores")
            recommendations = self.manager.get_decommission_recommendations()
            results["decision_framework"] = {
                "total_endpoints": len(recommendations),
                "high_priority": len(recommendations[recommendations["two_gate_score"] >= 7]),
                "medium_priority": len(
                    recommendations[(recommendations["two_gate_score"] >= 4) & (recommendations["two_gate_score"] < 7)]
                ),
                "low_priority": len(recommendations[recommendations["two_gate_score"] < 4]),
            }
            print_success("✓ Decision framework validation complete")
        except Exception as e:
            results["decision_framework"] = {"error": str(e)}
            print_warning(f"⚠ Decision framework validation failed: {str(e)}")

        validation_duration = (datetime.now() - validation_start).total_seconds()
        results["duration_seconds"] = validation_duration

        print_info(f"All validations complete in {validation_duration:.1f}s")
        return results

    def _generate_analysis(self) -> Dict:
        """Generate comprehensive analysis and recommendations."""
        if not self.manager:
            raise RuntimeError("Must call load_from_csv() first")

        analysis = {}

        # Get decommission recommendations with scoring
        try:
            recommendations_df = self.manager.get_decommission_recommendations()
            analysis["recommendations"] = {
                "total_endpoints": len(recommendations_df),
                "total_annual_cost": recommendations_df["annual_cost"].sum(),
                "high_priority_count": len(recommendations_df[recommendations_df["two_gate_score"] >= 7]),
                "high_priority_savings": recommendations_df[recommendations_df["two_gate_score"] >= 7][
                    "annual_cost"
                ].sum(),
            }
        except Exception as e:
            analysis["recommendations"] = {"error": str(e)}

        # Get account summary
        try:
            account_summary = self.manager.get_account_summary()
            analysis["account_summary"] = str(account_summary)
        except Exception as e:
            analysis["account_summary"] = {"error": str(e)}

        return analysis

    def export_all(
        self, formats: List[str] = ["csv", "md", "json"], output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Export to all formats.

        Args:
            formats: Export formats to generate ('csv', 'md', 'json')
            output_dir: Optional output directory (default: data/exports/)

        Returns:
            Dict mapping format to export file path

        Example:
            >>> exports = service.export_all(formats=['csv', 'md'])
            >>> print(exports['csv'])
            PosixPath('data/exports/vpce-cleanup-20251021-123456.csv')
        """
        if not self.manager:
            raise RuntimeError("Must call load_from_csv() first")

        if output_dir is None:
            output_dir = Path("notebooks/vpc/data/exports")

        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        exports = {}

        # Export to each format
        for fmt in formats:
            try:
                export_path = self.manager.export_results(format=fmt, output_dir=output_dir)
                exports[fmt] = export_path
                print_success(f"✓ Exported {fmt.upper()}: {export_path}")
            except Exception as e:
                print_warning(f"⚠ {fmt.upper()} export failed: {str(e)}")
                exports[fmt] = None

        return exports

    def generate_cleanup_scripts(self, output_dir: Optional[Path] = None) -> List[Path]:
        """
        Generate cleanup scripts for all accounts.

        Args:
            output_dir: Optional output directory (default: data/scripts/)

        Returns:
            List of generated script file paths

        Example:
            >>> scripts = service.generate_cleanup_scripts()
            >>> print(f"Generated {len(scripts)} cleanup scripts")
        """
        if not self.manager:
            raise RuntimeError("Must call load_from_csv() first")

        if output_dir is None:
            output_dir = Path("notebooks/vpc/data/scripts")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate scripts using manager method
        script_results = self.manager.generate_cleanup_scripts(output_dir=output_dir)

        script_paths = []
        # Handle both dict and other return types
        if isinstance(script_results, dict):
            for account_id, script_path in script_results.items():
                if script_path:
                    script_path_obj = Path(script_path) if isinstance(script_path, str) else script_path
                    if script_path_obj.exists():
                        script_paths.append(script_path_obj)
                        print_success(f"✓ Generated cleanup script for account {account_id}")
        elif script_results:
            # Handle single path return
            script_path_obj = Path(script_results) if isinstance(script_results, str) else script_results
            if script_path_obj.exists():
                script_paths.append(script_path_obj)

        print_info(f"Generated {len(script_paths)} cleanup scripts in {output_dir}")
        return script_paths

    def get_executive_summary(self) -> Dict:
        """
        Generate executive summary for managers.

        Returns:
            Dict with high-level metrics and recommendations

        Example:
            >>> summary = service.get_executive_summary()
            >>> print(summary['total_annual_savings'])
        """
        if not self.manager:
            return {"error": "No data loaded", "status": "not_initialized"}

        try:
            # Get recommendations DataFrame
            recommendations_df = self.manager.get_decommission_recommendations()

            # Calculate key metrics
            total_endpoints = len(recommendations_df)
            total_annual_cost = recommendations_df["annual_cost"].sum()

            # High priority recommendations (score >= 7)
            high_priority = recommendations_df[recommendations_df["two_gate_score"] >= 7]
            high_priority_count = len(high_priority)
            high_priority_savings = high_priority["annual_cost"].sum()

            # Account breakdown
            account_breakdown = (
                recommendations_df.groupby("account_id").agg({"vpce_id": "count", "annual_cost": "sum"}).to_dict()
            )

            return {
                "status": "complete",
                "endpoints": {
                    "total": total_endpoints,
                    "high_priority": high_priority_count,
                    "percentage_high_priority": (
                        high_priority_count / total_endpoints * 100 if total_endpoints > 0 else 0
                    ),
                },
                "costs": {
                    "total_annual": total_annual_cost,
                    "high_priority_savings": high_priority_savings,
                    "percentage_high_priority": (
                        high_priority_savings / total_annual_cost * 100 if total_annual_cost > 0 else 0
                    ),
                },
                "accounts": account_breakdown,
                "recommendations": {
                    "immediate_action": high_priority_count,
                    "estimated_annual_savings": high_priority_savings,
                },
            }

        except Exception as e:
            return {"error": str(e), "status": "error"}

    def get_validation_status(self) -> Dict:
        """
        Get comprehensive validation status.

        Returns:
            Dict with validation status and variance metrics

        Example:
            >>> status = service.get_validation_status()
            >>> print(status['aws_api']['validated_count'])
        """
        if not self.manager:
            return {"error": "No data loaded", "status": "not_initialized"}

        validation_status = {"aws_api": {}, "mcp_cost_explorer": {}, "decision_framework": {}}

        # Check if validation results are available
        if hasattr(self.manager, "validation_results"):
            validation_status["aws_api"] = self.manager.validation_results

        if hasattr(self.manager, "mcp_cost_data"):
            validation_status["mcp_cost_explorer"] = self.manager.mcp_cost_data

        return validation_status

    @property
    def workflow_results(self) -> Dict:
        """Get last workflow execution results."""
        return self._workflow_results
