"""
VPC Cleanup Wrapper - Enterprise CLI Integration

This module provides the CLI wrapper for VPC cleanup operations, integrating
with the existing runbooks framework and providing enterprise-grade safety
controls and multi-account support.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from runbooks.common.profile_utils import get_profile_for_operation
from runbooks.common.rich_utils import console, print_header, print_success, print_error, print_warning, create_table
from runbooks.common.mcp_integration import EnterpriseMCPIntegrator
from .vpc_cleanup_integration import VPCCleanupFramework, VPCCleanupPhase, VPCCleanupRisk
from .manager_interface import VPCManagerInterface

logger = logging.getLogger(__name__)


class VPCCleanupCLI:
    """
    Enterprise VPC Cleanup CLI wrapper with safety controls and approval gates

    Provides comprehensive VPC cleanup capabilities integrated with the existing
    runbooks framework architecture and enterprise multi-account patterns.
    """

    def __init__(
        self,
        profile: Optional[str] = None,
        region: str = "ap-southeast-2",
        safety_mode: bool = True,
        console: Optional[Console] = None,
    ):
        """
        Initialize VPC Cleanup CLI

        Args:
            profile: AWS profile for operations
            region: AWS region
            safety_mode: Enable safety controls and approval gates
            console: Rich console for output
        """
        self.profile = profile
        self.region = region
        self.safety_mode = safety_mode
        self.console = console or Console()

        # Initialize cleanup framework
        self.cleanup_framework = VPCCleanupFramework(
            profile=profile, region=region, console=self.console, safety_mode=safety_mode
        )

        # Initialize manager interface for business reporting
        self.manager_interface = VPCManagerInterface(console=self.console)

        # Initialize MCP integrator for cross-validation
        self.mcp_integrator = EnterpriseMCPIntegrator(user_profile=profile, console_instance=self.console)

    def generate_cleanup_plan(self, vpc_id: str, use_three_bucket: bool = False) -> Dict[str, Any]:
        """
        Generate VPC cleanup execution plan.

        Args:
            vpc_id: VPC ID to clean up
            use_three_bucket: Use three-bucket cleanup sequence

        Returns:
            Dict with cleanup plan steps
        """
        try:
            # Get VPC dependencies first
            from runbooks.vpc.networking_wrapper import VPCNetworkingWrapper

            wrapper = VPCNetworkingWrapper(profile=self.profile, region=self.region, console=self.console)
            dependencies = wrapper.get_vpc_dependencies(vpc_id)

            if "error" in dependencies:
                print_error(f"Failed to get VPC dependencies: {dependencies['error']}")
                return {"vpc_id": vpc_id, "error": dependencies["error"], "steps": []}

            # Generate cleanup steps based on dependencies
            steps = []
            step_num = 1

            # Step 1: Delete NAT Gateways (if any ENIs belong to NAT Gateways)
            # Note: ENI count includes NAT Gateway ENIs, would need detailed filtering
            if dependencies.get("eni_count", 0) > 0:
                steps.append(
                    {
                        "step": step_num,
                        "action": "Delete NAT Gateways",
                        "resource_type": "nat-gateway",
                        "count": "Check AWS Console",  # Would need NAT Gateway API call
                        "bucket": 1 if use_three_bucket else None,
                        "rationale": "NAT Gateways have ENIs that block VPC deletion",
                    }
                )
                step_num += 1

            # Step 2: Delete VPC Endpoints
            if dependencies.get("vpce_count", 0) > 0:
                steps.append(
                    {
                        "step": step_num,
                        "action": "Delete VPC Endpoints",
                        "resource_type": "vpc-endpoint",
                        "count": dependencies["vpce_count"],
                        "bucket": 1 if use_three_bucket else None,
                        "rationale": "VPC Endpoints have ENIs that must be removed",
                    }
                )
                step_num += 1

            # Step 3: Delete Route Tables (non-main)
            if dependencies.get("rt_count", 0) > 1:  # >1 because main RT can't be deleted
                steps.append(
                    {
                        "step": step_num,
                        "action": "Delete Route Tables",
                        "resource_type": "route-table",
                        "count": dependencies["rt_count"] - 1,
                        "bucket": 2 if use_three_bucket else None,
                        "rationale": "Custom route tables must be deleted before VPC",
                    }
                )
                step_num += 1

            # Step 4: Delete Security Groups (non-default)
            if dependencies.get("sg_count", 0) > 1:  # >1 because default SG can't be deleted
                steps.append(
                    {
                        "step": step_num,
                        "action": "Delete Security Groups",
                        "resource_type": "security-group",
                        "count": dependencies["sg_count"] - 1,
                        "bucket": 2 if use_three_bucket else None,
                        "rationale": "Custom security groups must be deleted before VPC",
                    }
                )
                step_num += 1

            # Step 5: Delete VPC
            steps.append(
                {
                    "step": step_num,
                    "action": "Delete VPC",
                    "resource_type": "vpc",
                    "count": 1,
                    "bucket": 3 if use_three_bucket else None,
                    "rationale": "Final VPC deletion after all dependencies removed",
                }
            )

            plan = {
                "vpc_id": vpc_id,
                "three_bucket": use_three_bucket,
                "total_steps": len(steps),
                "steps": steps,
                "dependencies": dependencies,
                "warnings": [],
            }

            # Add warnings
            if dependencies.get("eni_count", 0) > 0:
                plan["warnings"].append(
                    f"⚠️ {dependencies['eni_count']} ENIs detected - VPC cannot be deleted until ENIs removed"
                )

            # Display plan
            if self.output_format != "json":
                self._display_cleanup_plan(plan)

            return plan

        except Exception as e:
            print_error(f"Error generating cleanup plan: {e}")
            logger.error(f"Cleanup plan generation failed: {e}")
            return {"vpc_id": vpc_id, "error": str(e), "steps": []}

    def _display_cleanup_plan(self, plan: Dict[str, Any]) -> None:
        """Display VPC cleanup plan using Rich"""
        from runbooks.common.rich_utils import create_table

        vpc_id = plan["vpc_id"]
        three_bucket = plan["three_bucket"]

        # Plan header
        title = f"VPC Cleanup Plan - {vpc_id}"
        if three_bucket:
            title += " (Three-Bucket Strategy)"

        print_header(title, "Enterprise Safety Controls")

        # Warnings first
        if plan.get("warnings"):
            for warning in plan["warnings"]:
                print_warning(warning)
            console.print()

        # Steps table
        table = create_table(
            title=f"Cleanup Steps ({plan['total_steps']} steps)",
            columns=[
                {"header": "Step", "style": "cyan", "justify": "center"},
                {"header": "Action", "style": "yellow"},
                {"header": "Resource Type", "style": "magenta"},
                {"header": "Count", "style": "green", "justify": "right"},
                {"header": "Bucket", "style": "blue", "justify": "center"} if three_bucket else None,
                {"header": "Rationale", "style": "white"},
            ],
        )

        for step in plan["steps"]:
            row = [
                str(step["step"]),
                step["action"],
                step["resource_type"],
                str(step["count"]),
            ]
            if three_bucket:
                row.append(f"Bucket {step['bucket']}" if step["bucket"] else "N/A")
            row.append(step.get("rationale", ""))
            table.add_row(*row)

        console.print(table)
        console.print()

        # Summary
        deps = plan["dependencies"]
        summary = f"""
[bold]Dependency Summary[/bold]

ENIs: [red]{deps.get("eni_count", 0)}[/red] (blocking)
VPC Endpoints: [yellow]{deps.get("vpce_count", 0)}[/yellow]
Route Tables: [yellow]{deps.get("rt_count", 0)}[/yellow]
Security Groups: [yellow]{deps.get("sg_count", 0)}[/yellow]

[bold]Cleanup Status:[/bold]
{"[red]⛔ BLOCKED - Remove ENIs first[/red]" if deps.get("eni_count", 0) > 0 else "[green]✅ Ready for cleanup execution[/green]"}
        """
        console.print(Panel(summary.strip(), title="Summary", style="bold blue"))

    def analyze_vpc_cleanup_candidates(
        self,
        vpc_ids: Optional[List[str]] = None,
        account_profiles: Optional[List[str]] = None,
        export_results: bool = True,
        output_directory: str = "./exports/vpc_cleanup",
    ) -> Dict[str, Any]:
        """
        Analyze VPC cleanup candidates with comprehensive dependency analysis

        Args:
            vpc_ids: Specific VPC IDs to analyze
            account_profiles: Multiple account profiles for multi-account analysis
            export_results: Export analysis results to files
            output_directory: Directory for exported files

        Returns:
            Dictionary with analysis results and recommendations
        """
        print_header("VPC Cleanup Analysis", "Enterprise Framework")

        # Profile validation
        if account_profiles:
            validated_profiles = []
            for profile_candidate in account_profiles:
                try:
                    # Validate profile exists and is accessible
                    get_profile_for_operation("operational", profile_candidate)
                    validated_profiles.append(profile_candidate)
                    print_success(f"Profile validated: {profile_candidate}")
                except Exception as e:
                    print_error(f"Profile validation failed: {profile_candidate} - {e}")

            if not validated_profiles:
                print_error("No valid profiles available for analysis")
                return {}

            account_profiles = validated_profiles

        # Perform analysis
        try:
            candidates = self.cleanup_framework.analyze_vpc_cleanup_candidates(
                vpc_ids=vpc_ids, account_profiles=account_profiles
            )

            if not candidates:
                print_warning("No VPC cleanup candidates found")
                return {}

            # Generate cleanup plan
            cleanup_plan = self.cleanup_framework.generate_cleanup_plan(candidates)

            # MCP Cross-Validation: Verify VPC data against real AWS APIs
            vpc_validation_data = {
                "vpc_candidates": candidates,
                "total_vpcs": len(candidates),
                "regions": [self.region],
                "profile": self.profile,
            }

            print_warning("Performing MCP cross-validation against AWS APIs...")
            try:
                # Cross-validate VPC discovery and dependencies
                import asyncio

                mcp_result = asyncio.run(self.mcp_integrator.validate_vpc_operations(vpc_validation_data))

                if mcp_result.success and mcp_result.consistency_score >= 99.5:
                    actual_vpc_count = mcp_result.total_resources_validated
                    consistency_score = mcp_result.consistency_score

                    print_success(
                        f"✅ MCP Validation: {consistency_score:.1f}% accuracy - "
                        f"Found {actual_vpc_count} VPCs vs {len(candidates)} candidates"
                    )

                    # Add MCP validation results to cleanup plan
                    cleanup_plan["mcp_validation"] = {
                        "validated": True,
                        "consistency_score": consistency_score,
                        "actual_vpc_count": actual_vpc_count,
                        "validation_timestamp": mcp_result.validation_timestamp,
                    }
                else:
                    print_error(f"❌ MCP Validation failed: {mcp_result.consistency_score:.1f}% accuracy")
                    cleanup_plan["mcp_validation"] = {"validated": False, "errors": mcp_result.error_details}

            except Exception as e:
                print_error(f"MCP cross-validation error: {e}")
                cleanup_plan["mcp_validation"] = {"validated": False, "error": str(e)}

            # Display results
            self.cleanup_framework.display_cleanup_analysis(candidates)

            # Display executive summary
            self._display_executive_summary(cleanup_plan)

            # Export results if requested
            exported_files = {}
            if export_results:
                exported_files = self.cleanup_framework.export_cleanup_plan(
                    output_directory=output_directory, include_dependencies=True
                )

            return {
                "candidates": candidates,
                "cleanup_plan": cleanup_plan,
                "exported_files": exported_files,
                "analysis_summary": {
                    "total_vpcs": len(candidates),
                    "immediate_cleanup": len([c for c in candidates if c.cleanup_phase == VPCCleanupPhase.IMMEDIATE]),
                    "total_annual_savings": sum((c.annual_savings or 0.0) for c in candidates),
                    "safety_mode_enabled": self.safety_mode,
                },
            }

        except Exception as e:
            print_error(f"VPC cleanup analysis failed: {e}")
            logger.error(f"VPC cleanup analysis error: {e}")
            return {}

    def execute_cleanup_phase(
        self, phase: str, vpc_ids: Optional[List[str]] = None, dry_run: bool = True, require_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Execute VPC cleanup for a specific phase

        Args:
            phase: Cleanup phase to execute (immediate, investigation, governance, complex)
            vpc_ids: Specific VPC IDs to clean up
            dry_run: Execute in dry-run mode only
            require_approval: Require explicit user approval

        Returns:
            Dictionary with execution results
        """
        print_header(f"VPC Cleanup Execution - {phase.title()} Phase", "Enterprise Safety Controls")

        if not self.cleanup_framework.cleanup_candidates:
            print_error("No VPC candidates available. Run analysis first.")
            return {}

        # Map phase string to enum
        phase_mapping = {
            "immediate": VPCCleanupPhase.IMMEDIATE,
            "investigation": VPCCleanupPhase.INVESTIGATION,
            "governance": VPCCleanupPhase.GOVERNANCE,
            "complex": VPCCleanupPhase.COMPLEX,
        }

        cleanup_phase = phase_mapping.get(phase.lower())
        if not cleanup_phase:
            print_error(f"Invalid cleanup phase: {phase}")
            return {}

        # Filter candidates for this phase
        phase_candidates = [c for c in self.cleanup_framework.cleanup_candidates if c.cleanup_phase == cleanup_phase]

        if vpc_ids:
            phase_candidates = [c for c in phase_candidates if c.vpc_id in vpc_ids]

        if not phase_candidates:
            print_warning(f"No VPC candidates found for {phase} phase")
            return {}

        # Safety checks
        if self.safety_mode and not dry_run:
            print_warning("Safety mode is enabled. Forced dry-run execution.")
            dry_run = True

        # Display execution plan
        self._display_execution_plan(phase_candidates, dry_run)

        # Require approval for non-dry-run execution
        if not dry_run and require_approval:
            approval_message = (
                f"You are about to execute VPC cleanup for {len(phase_candidates)} VPCs.\n"
                f"This action cannot be undone. Are you sure you want to proceed?"
            )

            if not Confirm.ask(approval_message, default=False):
                print_warning("VPC cleanup execution cancelled by user")
                return {"status": "cancelled", "reason": "user_cancellation"}

        # Execute cleanup (currently dry-run only for safety)
        execution_results = {
            "phase": phase,
            "vpc_count": len(phase_candidates),
            "dry_run": True,  # Force dry-run for safety
            "execution_plan": [],
            "warnings": [],
            "recommendations": [],
        }

        for candidate in phase_candidates:
            vpc_plan = self._generate_vpc_deletion_plan(candidate)
            execution_results["execution_plan"].append(vpc_plan)

            # Safety warnings
            if (candidate.blocking_dependencies or 0) > 0:
                execution_results["warnings"].append(
                    f"VPC {candidate.vpc_id} has {candidate.blocking_dependencies or 0} blocking dependencies"
                )

            if candidate.is_default:
                execution_results["warnings"].append(
                    f"VPC {candidate.vpc_id} is a default VPC - requires platform approval"
                )

        # Generate recommendations
        execution_results["recommendations"] = self._generate_execution_recommendations(phase_candidates)

        print_success(f"VPC cleanup plan generated for {len(phase_candidates)} VPCs")

        if dry_run:
            print_warning("Dry-run mode: No actual VPC deletions performed")

        return execution_results

    def generate_business_report(
        self, include_executive_summary: bool = True, export_formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate business-focused VPC cleanup report

        Args:
            include_executive_summary: Include executive summary
            export_formats: Export formats (json, csv, html)

        Returns:
            Dictionary with business report and export information
        """
        print_header("VPC Cleanup Business Report", "Executive Dashboard")

        if not self.cleanup_framework.cleanup_candidates:
            print_error("No VPC analysis data available. Run analysis first.")
            return {}

        if not export_formats:
            export_formats = ["json", "csv"]

        try:
            # Configure manager interface for business reporting
            self.manager_interface.configure_for_business_user(
                safety_mode=self.safety_mode,
                target_savings=30.0,  # 30% cost reduction target
                approval_threshold=1000.0,  # $1K approval threshold
            )

            # Convert technical analysis to business insights
            vpc_analysis_results = {
                "vpc_candidates": self.cleanup_framework.cleanup_candidates,
                "cleanup_plan": self.cleanup_framework.analysis_results,
            }

            business_analysis = self.manager_interface.analyze_cost_optimization_opportunity(vpc_analysis_results)

            # Display business dashboard
            if include_executive_summary:
                self.manager_interface.display_business_dashboard()

            # Export business reports
            exported_files = self.manager_interface.export_manager_friendly_reports()

            return {
                "business_analysis": business_analysis,
                "recommendations": self.manager_interface.business_recommendations,
                "executive_presentation": self.manager_interface.generate_executive_presentation(),
                "exported_files": exported_files,
            }

        except Exception as e:
            print_error(f"Business report generation failed: {e}")
            logger.error(f"Business report error: {e}")
            return {}

    def validate_vpc_cleanup_safety(self, vpc_id: str, account_profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate VPC cleanup safety with comprehensive dependency checking

        Args:
            vpc_id: VPC ID to validate
            account_profile: AWS profile for the account containing the VPC

        Returns:
            Dictionary with safety validation results
        """
        print_header(f"VPC Safety Validation", vpc_id)

        # Find the VPC candidate
        vpc_candidate = None
        for candidate in self.cleanup_framework.cleanup_candidates:
            if candidate.vpc_id == vpc_id:
                vpc_candidate = candidate
                break

        if not vpc_candidate:
            # Run targeted analysis for this VPC
            profile_to_use = account_profile or self.profile

            temp_framework = VPCCleanupFramework(
                profile=profile_to_use, region=self.region, console=self.console, safety_mode=True
            )

            candidates = temp_framework.analyze_vpc_cleanup_candidates(vpc_ids=[vpc_id])

            if candidates:
                vpc_candidate = candidates[0]
            else:
                print_error(f"VPC {vpc_id} not found or inaccessible")
                return {}

        # Perform safety validation
        safety_results = {
            "vpc_id": vpc_id,
            "safety_score": "SAFE",
            "blocking_dependencies": vpc_candidate.blocking_dependencies or 0,
            "risk_level": vpc_candidate.risk_level.value,
            "safety_checks": [],
            "warnings": [],
            "approval_required": vpc_candidate.approval_required,
        }

        # ENI check (most critical)
        if vpc_candidate.eni_count > 0:
            safety_results["safety_checks"].append(
                {
                    "check": "ENI Count",
                    "status": "FAIL",
                    "details": f"{vpc_candidate.eni_count} network interfaces found",
                    "blocking": True,
                }
            )
            safety_results["safety_score"] = "UNSAFE"
        else:
            safety_results["safety_checks"].append(
                {"check": "ENI Count", "status": "PASS", "details": "No active network interfaces", "blocking": False}
            )

        # Dependency checks
        internal_deps = len([d for d in vpc_candidate.dependencies if d.dependency_level == 1])
        external_deps = len([d for d in vpc_candidate.dependencies if d.dependency_level == 2])
        control_deps = len([d for d in vpc_candidate.dependencies if d.dependency_level == 3])

        safety_results["safety_checks"].extend(
            [
                {
                    "check": "Internal Dependencies",
                    "status": "WARN" if internal_deps > 0 else "PASS",
                    "details": f"{internal_deps} internal dependencies (NAT, Endpoints, etc.)",
                    "blocking": internal_deps > 0,
                },
                {
                    "check": "External Dependencies",
                    "status": "WARN" if external_deps > 0 else "PASS",
                    "details": f"{external_deps} external dependencies (TGW, Peering, etc.)",
                    "blocking": external_deps > 0,
                },
                {
                    "check": "Control Plane Dependencies",
                    "status": "WARN" if control_deps > 0 else "PASS",
                    "details": f"{control_deps} control plane dependencies",
                    "blocking": control_deps > 0,
                },
            ]
        )

        # Update safety score based on blocking dependencies
        blocking_checks = len([c for c in safety_results["safety_checks"] if c["blocking"]])
        if blocking_checks > 0:
            safety_results["safety_score"] = "UNSAFE"

        # IaC management check
        if vpc_candidate.iac_managed:
            safety_results["warnings"].append(f"VPC is managed by Infrastructure as Code: {vpc_candidate.iac_source}")

        # Default VPC check
        if vpc_candidate.is_default:
            safety_results["warnings"].append("VPC is a default VPC - requires platform team approval")

        # Display results
        self._display_safety_validation(safety_results)

        return safety_results

    def _display_executive_summary(self, cleanup_plan: Dict[str, Any]) -> None:
        """Display executive summary of cleanup plan"""
        if not cleanup_plan:
            return

        exec_summary = cleanup_plan.get("executive_summary", {})

        summary_text = (
            f"[bold blue]📊 EXECUTIVE SUMMARY[/bold blue]\n\n"
            f"Total VPCs Analyzed: [yellow]{cleanup_plan['metadata']['total_vpcs_analyzed']}[/yellow]\n"
            f"Ready for Immediate Cleanup: [green]{exec_summary.get('immediate_candidates', 0)}[/green] "
            f"({exec_summary.get('percentage_ready', 0):.1f}%)\n"
            f"Investigation Required: [yellow]{exec_summary.get('investigation_required', 0)}[/yellow]\n"
            f"Governance Approval Needed: [blue]{exec_summary.get('governance_approval_needed', 0)}[/blue]\n"
            f"Complex Migration Required: [red]{exec_summary.get('complex_migration_required', 0)}[/red]\n\n"
            f"Total Annual Savings: [bold green]${(cleanup_plan['metadata']['total_annual_savings'] or 0.0):,.2f}[/bold green]\n"
            f"Business Case Strength: [cyan]{exec_summary.get('business_case_strength', 'Unknown')}[/cyan]"
        )

        self.console.print(Panel(summary_text, title="Executive Summary", style="white", width=80))

    def _display_execution_plan(self, candidates: List, dry_run: bool) -> None:
        """Display VPC cleanup execution plan"""
        mode_text = "[yellow]DRY RUN MODE[/yellow]" if dry_run else "[red]LIVE EXECUTION MODE[/red]"

        plan_text = (
            f"[bold blue]🚀 EXECUTION PLAN[/bold blue]\n\n"
            f"Mode: {mode_text}\n"
            f"VPCs to Process: [yellow]{len(candidates)}[/yellow]\n"
            f"Total Dependencies to Remove: [red]{sum((c.blocking_dependencies or 0) for c in candidates)}[/red]\n"
            f"High Risk VPCs: [red]{len([c for c in candidates if c.risk_level == VPCCleanupRisk.HIGH])}[/red]\n"
            f"Default VPCs: [magenta]{len([c for c in candidates if c.is_default])}[/magenta]"
        )

        self.console.print(Panel(plan_text, title="Execution Plan", style="yellow" if dry_run else "red", width=80))

    def _display_safety_validation(self, safety_results: Dict[str, Any]) -> None:
        """Display VPC safety validation results"""
        # Create safety checks table
        table = create_table(
            title=f"Safety Validation - {safety_results['vpc_id']}",
            columns=[
                {"header": "Check", "style": "cyan"},
                {"header": "Status", "style": "green"},
                {"header": "Details", "style": "white"},
                {"header": "Blocking", "style": "red"},
            ],
        )

        for check in safety_results["safety_checks"]:
            status_color = {
                "PASS": "[green]✅ PASS[/green]",
                "WARN": "[yellow]⚠️ WARN[/yellow]",
                "FAIL": "[red]❌ FAIL[/red]",
            }.get(check["status"], check["status"])

            blocking_indicator = "🔴 YES" if check["blocking"] else "✅ NO"

            table.add_row(check["check"], status_color, check["details"], blocking_indicator)

        self.console.print(table)

        # Overall safety assessment
        safety_color = "green" if safety_results["safety_score"] == "SAFE" else "red"
        assessment_text = (
            f"[bold {safety_color}]Overall Safety: {safety_results['safety_score']}[/bold {safety_color}]\n"
            f"Risk Level: [magenta]{safety_results['risk_level']}[/magenta]\n"
            f"Approval Required: [yellow]{'YES' if safety_results['approval_required'] else 'NO'}[/yellow]"
        )

        self.console.print(Panel(assessment_text, title="Safety Assessment", style=safety_color, width=60))

        # Display warnings
        if safety_results["warnings"]:
            warnings_text = "\n".join([f"⚠️ {warning}" for warning in safety_results["warnings"]])
            self.console.print(Panel(warnings_text, title="Important Warnings", style="yellow", width=80))

    def _generate_vpc_deletion_plan(self, candidate) -> Dict[str, Any]:
        """Generate detailed VPC deletion plan"""
        deletion_steps = []

        # Sort dependencies by deletion order
        sorted_deps = sorted(candidate.dependencies, key=lambda x: x.deletion_order)

        for i, dep in enumerate(sorted_deps, 1):
            deletion_steps.append(
                {
                    "step": i,
                    "action": f"Delete {dep.resource_type}",
                    "resource_id": dep.resource_id,
                    "api_method": dep.api_method,
                    "description": dep.description,
                    "dependency_level": dep.dependency_level,
                }
            )

        # Final VPC deletion step
        deletion_steps.append(
            {
                "step": len(deletion_steps) + 1,
                "action": "Delete VPC",
                "resource_id": candidate.vpc_id,
                "api_method": "delete_vpc",
                "description": "Final VPC deletion",
                "dependency_level": 0,
            }
        )

        return {
            "vpc_id": candidate.vpc_id,
            "vpc_name": candidate.vpc_name,
            "risk_level": candidate.risk_level.value,
            "total_steps": len(deletion_steps),
            "estimated_time": f"{len(deletion_steps) * 2} minutes",
            "deletion_steps": deletion_steps,
        }

    def _generate_execution_recommendations(self, candidates: List) -> List[str]:
        """Generate execution recommendations"""
        recommendations = []

        # Phase-specific recommendations
        immediate_count = len([c for c in candidates if c.cleanup_phase == VPCCleanupPhase.IMMEDIATE])
        high_risk_count = len([c for c in candidates if c.risk_level == VPCCleanupRisk.HIGH])
        default_vpc_count = len([c for c in candidates if c.is_default])
        iac_managed_count = len([c for c in candidates if c.iac_managed])

        if immediate_count > 0:
            recommendations.append(f"Execute {immediate_count} immediate cleanup candidates first for quick wins")

        if high_risk_count > 0:
            recommendations.append(f"Review {high_risk_count} high-risk VPCs with stakeholders before execution")

        if default_vpc_count > 0:
            recommendations.append(f"Obtain platform team approval for {default_vpc_count} default VPC deletions")

        if iac_managed_count > 0:
            recommendations.append(f"Update Infrastructure as Code for {iac_managed_count} IaC-managed VPCs")

        # General recommendations
        recommendations.extend(
            [
                "Execute VPC cleanup in phases to minimize blast radius",
                "Validate each deletion step before proceeding to next",
                "Maintain comprehensive audit trail of all deletion activities",
                "Schedule cleanup during maintenance windows to minimize impact",
            ]
        )

        return recommendations


def display_config_campaign_results(results: Dict[str, Any]) -> None:
    """
    Display config-driven campaign results using Rich CLI formatting (NEW FUNCTION)

    This function formats and displays the results from VPCCleanupFramework.analyze_from_config()
    with enterprise-grade Rich CLI presentation for campaign analysis visibility.

    Args:
        results: Campaign analysis results from analyze_from_config()
    """
    from runbooks.common.rich_utils import (
        console,
        create_table,
        print_header,
        print_success,
        print_warning,
        print_info,
        create_panel,
    )

    # Extract campaign metadata
    campaign_meta = results.get("campaign_metadata", {})
    campaign_id = campaign_meta.get("campaign_id", "Unknown")
    campaign_name = campaign_meta.get("campaign_name", "VPC Cleanup Campaign")
    aws_profile = campaign_meta.get("aws_billing_profile", "default")
    execution_date = campaign_meta.get("execution_date", "N/A")

    # Display campaign header
    print_header(f"Campaign {campaign_id}: {campaign_name}", "Config-Driven Analysis")

    # Campaign metadata panel
    metadata_content = (
        f"[bold cyan]Campaign Metadata[/bold cyan]\n\n"
        f"[white]Campaign ID:[/white] [bright_yellow]{campaign_id}[/bright_yellow]\n"
        f"[white]AWS Billing Profile:[/white] [bright_blue]{aws_profile}[/bright_blue]\n"
        f"[white]Execution Date:[/white] [dim]{execution_date}[/dim]\n"
        f"[white]Description:[/white] {campaign_meta.get('description', 'N/A')}"
    )

    console.print(create_panel(metadata_content, title="Campaign Information", border_style="cyan"))
    console.print()

    # VPC results table
    vpc_results = results.get("vpc_results", [])

    if vpc_results:
        table = create_table(
            title=f"VPC Campaign Results - {len(vpc_results)} VPCs Analyzed",
            columns=[
                {"name": "VPC ID", "style": "bright_cyan"},
                {"name": "Account", "style": "bright_blue"},
                {"name": "Region", "style": "yellow"},
                {"name": "Deletion Date", "style": "dim"},
                {"name": "Monthly Savings", "style": "bright_green", "justify": "right"},
                {"name": "Annual Savings", "style": "bright_green bold", "justify": "right"},
                {"name": "Confidence", "style": "cyan"},
            ],
        )

        for vpc_result in vpc_results:
            table.add_row(
                vpc_result.get("vpc_id", "N/A"),
                vpc_result.get("account_id", "N/A"),
                vpc_result.get("region", "N/A"),
                vpc_result.get("deletion_date", "N/A"),
                f"${vpc_result.get('monthly_savings', 0.0):,.2f}",
                f"${vpc_result.get('annual_savings', 0.0):,.2f}",
                vpc_result.get("confidence_level", "MEDIUM"),
            )

        console.print(table)
        console.print()
    else:
        print_warning("No VPC results found in campaign analysis")
        console.print()

    # Total savings summary panel
    total_savings = results.get("total_savings", {})
    monthly_total = total_savings.get("monthly", 0.0)
    annual_total = total_savings.get("annual", 0.0)

    savings_content = (
        f"[bold green]💰 Total Realized Savings[/bold green]\n\n"
        f"[white]Monthly Savings:[/white] [bright_green]${monthly_total:,.2f}[/bright_green]\n"
        f"[white]Annual Savings:[/white] [bright_green bold]${annual_total:,.2f}[/bright_green bold]\n"
        f"[white]VPCs Analyzed:[/white] [bright_yellow]{len(vpc_results)}[/bright_yellow]"
    )

    console.print(create_panel(savings_content, title="Financial Impact", border_style="bright_green"))
    console.print()

    # Campaign success message
    if annual_total > 0:
        print_success(
            f"Campaign {campaign_id} analysis complete: ${annual_total:,.2f}/year realized savings from {len(vpc_results)} VPCs"
        )
    else:
        print_info(f"Campaign {campaign_id} analysis complete - See results above")


# CLI Command Functions for integration with runbooks CLI


def analyze_cleanup_candidates(
    profile: Optional[str] = None,
    vpc_ids: Optional[List[str]] = None,
    all_accounts: bool = False,
    region: str = "ap-southeast-2",
    export_results: bool = True,
    account_limit: Optional[int] = None,
    region_limit: Optional[int] = None,
    config: Optional[str] = None,
) -> Dict[str, Any]:
    """
    CLI function to analyze VPC cleanup candidates

    Args:
        profile: AWS profile for analysis
        vpc_ids: Specific VPC IDs to analyze
        all_accounts: Analyze across all accessible accounts
        region: AWS region
        export_results: Export results to files
        account_limit: Limit number of accounts to process for faster testing
        region_limit: Limit number of regions to scan per account
        config: Path to YAML campaign configuration file (NEW)

    Returns:
        Dictionary with analysis results
    """
    # Determine profile to use
    operational_profile = get_profile_for_operation("operational", profile)

    # NEW: Config-driven campaign analysis
    if config:
        cleanup_framework = VPCCleanupFramework(profile=operational_profile, region=region, safety_mode=True)

        results = cleanup_framework.analyze_from_config(config)
        display_config_campaign_results(results)
        return results

    # Initialize CLI wrapper
    cleanup_cli = VPCCleanupCLI(
        profile=operational_profile,
        region=region,
        safety_mode=True,  # Always enable safety mode
    )

    # Handle multi-account analysis
    account_profiles = None
    if all_accounts:
        # Use Organizations API to discover all accounts
        console.print("[blue]🔍 Discovering organization accounts for multi-account VPC analysis...[/blue]")

        try:
            # Import Organizations discovery functionality from FinOps module
            from runbooks.finops.aws_client import get_organization_accounts
            from runbooks.common.profile_utils import create_operational_session, create_management_session
            from runbooks.vpc.cross_account_session import convert_accounts_to_sessions

            # Check for cached Organizations data first (performance optimization)

            # Use CENTRALISED_OPS_PROFILE if available for operational accounts
            import os

            centralised_ops_profile = os.getenv("CENTRALISED_OPS_PROFILE")
            if centralised_ops_profile:
                console.print(f"[green]✅ Using CENTRALISED_OPS_PROFILE: {centralised_ops_profile}[/green]")
            from .mcp_no_eni_validator import _get_cached_organizations_data, _cache_organizations_data

            org_accounts = _get_cached_organizations_data()

            if not org_accounts:
                # Create management session for Organizations discovery (needs Organizations permissions)
                session = create_management_session(profile_name=operational_profile)

                # Discover all organization accounts
                org_accounts = get_organization_accounts(session, operational_profile)

                # Cache the results for future use (prevents duplicate calls)
                if org_accounts:
                    _cache_organizations_data(org_accounts)

            if org_accounts:
                # Apply account limit for performance optimization before session creation
                if account_limit and account_limit < len(org_accounts):
                    console.print(f"[yellow]🎯 Performance mode: limiting to first {account_limit} accounts[/yellow]")
                    org_accounts = org_accounts[:account_limit]

                # Convert accounts to cross-account sessions using STS AssumeRole
                account_sessions, account_metadata = convert_accounts_to_sessions(org_accounts, operational_profile)

                console.print(f"[green]✅ Discovered {len(org_accounts)} organization accounts[/green]")
                console.print(
                    f"[cyan]📋 Created {len(account_sessions)} cross-account sessions for VPC analysis[/cyan]"
                )

                # Log account discovery for transparency
                active_count = len([acc for acc in org_accounts if acc.get("status") == "ACTIVE"])
                inactive_count = len(org_accounts) - active_count
                console.print(
                    f"[dim]Organization scope: {active_count} active, {inactive_count} inactive accounts[/dim]"
                )

                # Detect STS AssumeRole failures and switch to multi-profile discovery
                if len(account_sessions) == 0 and len(org_accounts) > 0:
                    console.print(
                        f"[red]❌ STS AssumeRole failed for all {len(org_accounts)} accounts - cross-account access denied[/red]"
                    )
                    console.print(
                        "[yellow]💡 Enhancing to multi-profile discovery for comprehensive VPC scanning[/yellow]"
                    )

                    # Enhanced multi-profile discovery pattern (KISS & DRY)
                    console.print("[blue]🔍 Discovering VPC profiles from available AWS configurations...[/blue]")
                    account_profiles = _discover_vpc_profiles_from_available_aws_profiles(operational_profile)

                    if account_profiles and len(account_profiles) > 1:
                        console.print(
                            f"[green]✅ Enhanced discovery found {len(account_profiles)} profiles with VPC access[/green]"
                        )
                    else:
                        console.print("[yellow]⚠️ Enhanced discovery fallback to single profile[/yellow]")
                else:
                    # Store sessions for VPC discovery instead of profiles
                    account_profiles = account_sessions  # Pass sessions instead of profile strings

            else:
                console.print("[yellow]⚠️ No organization accounts found, falling back to single profile[/yellow]")
                account_profiles = [operational_profile] if operational_profile else None

        except ImportError as e:
            console.print(f"[red]❌ Organizations discovery unavailable: {e}[/red]")
            console.print("[yellow]💡 Falling back to single profile analysis[/yellow]")
            account_profiles = [operational_profile] if operational_profile else None

        except Exception as e:
            console.print(f"[red]❌ Organizations discovery failed: {e}[/red]")
            console.print("[yellow]💡 Enhancing to multi-profile discovery for comprehensive VPC scanning[/yellow]")

            # Enhanced multi-profile discovery pattern (KISS & DRY)
            console.print("[blue]🔍 Discovering VPC profiles from available AWS configurations...[/blue]")
            account_profiles = _discover_vpc_profiles_from_available_aws_profiles(operational_profile)

            if account_profiles and len(account_profiles) > 1:
                console.print(
                    f"[green]✅ Enhanced discovery found {len(account_profiles)} profiles with VPC access[/green]"
                )
            else:
                console.print("[yellow]⚠️ Enhanced discovery fallback to single profile[/yellow]")

    return cleanup_cli.analyze_vpc_cleanup_candidates(
        vpc_ids=vpc_ids, account_profiles=account_profiles, export_results=export_results
    )


def validate_cleanup_safety(
    vpc_id: str, profile: Optional[str] = None, region: str = "ap-southeast-2"
) -> Dict[str, Any]:
    """
    CLI function to validate VPC cleanup safety

    Args:
        vpc_id: VPC ID to validate
        profile: AWS profile
        region: AWS region

    Returns:
        Dictionary with safety validation results
    """
    operational_profile = get_profile_for_operation("operational", profile)

    cleanup_cli = VPCCleanupCLI(profile=operational_profile, region=region, safety_mode=True)

    return cleanup_cli.validate_vpc_cleanup_safety(vpc_id=vpc_id, account_profile=operational_profile)


def _discover_vpc_profiles_from_available_aws_profiles(primary_profile: str) -> List[str]:
    """
    Enhanced multi-profile discovery for comprehensive VPC scanning across all available AWS profiles.

    KISS & DRY approach: Use boto3's available_profiles to discover VPCs across Landing Zone
    when Organizations API cross-account role assumption fails.

    Args:
        primary_profile: Primary operational profile to include

    Returns:
        List of validated AWS profile names for VPC discovery
    """
    import boto3
    from rich.progress import Progress, TaskID

    console.print("[blue]🔍 Discovering VPC profiles from available AWS configurations...[/blue]")

    # Get all available AWS profiles
    try:
        session = boto3.Session()
        available_profiles = session.available_profiles

        if not available_profiles:
            console.print("[yellow]⚠️ No AWS profiles found in configuration[/yellow]")
            return [primary_profile] if primary_profile else []

        console.print(f"[cyan]📋 Found {len(available_profiles)} AWS profiles in configuration[/cyan]")

        # Enhanced multi-region discovery for comprehensive Landing Zone coverage
        # Based on user's confirmed NO-ENI VPCs in: ap-southeast-2, ap-southeast-6, ap-southeast-2
        regions_to_check = [
            "ap-southeast-2",  # Primary US region - user confirmed VPCs here
            "ap-southeast-6",  # Secondary US region - user confirmed VPCs here
            "ap-southeast-2",  # APAC region - user confirmed VPCs here
            "eu-west-1",  # Europe primary
            "ca-central-1",  # Canada
            "ap-northeast-1",  # Tokyo (common enterprise region)
        ]

        # Validate profiles by attempting to create sessions and check VPC access
        validated_profiles = []
        profile_vpc_details = {}

        with Progress() as progress:
            profile_task = progress.add_task("🔍 Validating profiles for VPC access...", total=len(available_profiles))

            for profile_name in available_profiles:
                try:
                    # Skip obvious non-VPC profiles but be less restrictive
                    if "billing" in profile_name.lower() and "readonly" in profile_name.lower():
                        console.print(f"[dim]⏭️ Skipping {profile_name} (billing-only profile)[/dim]")
                        progress.advance(profile_task)
                        continue

                    # Create test session
                    test_session = boto3.Session(profile_name=profile_name)
                    total_vpcs = 0
                    regions_with_vpcs = []

                    # Check multiple regions for VPCs (Landing Zone accounts may have VPCs in different regions)
                    for region in regions_to_check:
                        try:
                            ec2_client = test_session.client("ec2", region_name=region)
                            vpc_response = ec2_client.describe_vpcs(MaxResults=10)  # Check more VPCs per region
                            region_vpc_count = len(vpc_response.get("Vpcs", []))

                            if region_vpc_count > 0:
                                total_vpcs += region_vpc_count
                                regions_with_vpcs.append(f"{region}:{region_vpc_count}")

                        except Exception as region_error:
                            # Log region-specific errors but don't fail the whole profile
                            if "UnauthorizedOperation" not in str(region_error):
                                console.print(f"[dim]⚠️ {profile_name} in {region}: {str(region_error)[:30]}...[/dim]")
                            continue

                    # Add profile if it has VPCs in any region OR if it's the primary profile
                    if total_vpcs > 0:
                        validated_profiles.append(profile_name)
                        profile_vpc_details[profile_name] = {"total_vpcs": total_vpcs, "regions": regions_with_vpcs}
                        console.print(
                            f"[green]✅ {profile_name}: {total_vpcs} VPCs across {len(regions_with_vpcs)} regions[/green]"
                        )
                    elif profile_name == primary_profile:
                        # Always include primary profile even if no VPCs found
                        validated_profiles.append(profile_name)
                        console.print(
                            f"[yellow]🔑 {profile_name}: Primary profile (included despite no VPCs found)[/yellow]"
                        )
                    else:
                        console.print(f"[dim]⚪ {profile_name}: No VPCs found in {len(regions_to_check)} regions[/dim]")

                except Exception as e:
                    console.print(f"[dim]❌ {profile_name}: Access failed ({str(e)[:50]}...)[/dim]")

                progress.advance(profile_task)

        # Ensure primary profile is included if it was validated
        if primary_profile and primary_profile not in validated_profiles:
            try:
                # Test primary profile separately
                test_session = boto3.Session(profile_name=primary_profile)
                ec2_client = test_session.client("ec2", region_name="ap-southeast-2")
                ec2_client.describe_vpcs(MaxResults=1)
                validated_profiles.insert(0, primary_profile)  # Add at front
                console.print(f"[green]✅ Primary profile {primary_profile} added[/green]")
            except Exception:
                console.print(f"[yellow]⚠️ Primary profile {primary_profile} validation failed[/yellow]")

        # Enhanced VPC discovery summary
        total_vpcs_found = sum(details.get("total_vpcs", 0) for details in profile_vpc_details.values())
        console.print(f"[bold green]🎯 VPC Discovery Ready: {len(validated_profiles)} validated profiles[/bold green]")

        if total_vpcs_found > 0:
            console.print(
                f"[bold cyan]📊 Total VPCs discovered: {total_vpcs_found} across {len(profile_vpc_details)} accounts[/bold cyan]"
            )

            # Show detailed breakdown for profiles with VPCs
            for profile, details in profile_vpc_details.items():
                if details["total_vpcs"] > 0:
                    regions_str = ", ".join(details["regions"])
                    console.print(f"[dim]  • {profile}: {regions_str}[/dim]")
        else:
            console.print(
                f"[yellow]⚠️ No VPCs found across {len(validated_profiles)} profiles - Landing Zone accounts may be empty[/yellow]"
            )

        console.print(
            f"[dim]Profiles: {', '.join(validated_profiles[:3])}{'...' if len(validated_profiles) > 3 else ''}[/dim]"
        )

        return validated_profiles

    except Exception as e:
        console.print(f"[red]❌ Profile discovery failed: {e}[/red]")
        console.print(f"[yellow]💡 Falling back to primary profile: {primary_profile}[/yellow]")
        return [primary_profile] if primary_profile else []


def generate_business_report(
    profile: Optional[str] = None, region: str = "ap-southeast-2", export_formats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    CLI function to generate business VPC cleanup report

    Args:
        profile: AWS profile
        region: AWS region
        export_formats: Export formats

    Returns:
        Dictionary with business report
    """
    operational_profile = get_profile_for_operation("operational", profile)

    cleanup_cli = VPCCleanupCLI(profile=operational_profile, region=region, safety_mode=True)

    # First run analysis if no candidates exist
    if not cleanup_cli.cleanup_framework.cleanup_candidates:
        cleanup_cli.analyze_vpc_cleanup_candidates()

    return cleanup_cli.generate_business_report(export_formats=export_formats or ["json", "csv"])
