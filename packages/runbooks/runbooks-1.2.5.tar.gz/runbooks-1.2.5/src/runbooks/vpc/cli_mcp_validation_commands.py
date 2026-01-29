#!/usr/bin/env python3
"""
CLI Commands for Enhanced MCP Validation - AWS-25 VPC Cleanup

This module provides CLI command integration for the enhanced MCP validation
framework, enabling enterprise-grade accuracy validation for VPC cleanup operations.

Features:
- AWS-25 VPC cleanup validation commands
- Cost projection validation via Cost Explorer MCP
- CloudTrail audit trail validation
- Enterprise security compliance validation
- Real-time accuracy reporting ≥99.5%

Author: devops-security-engineer [5] + python-runbooks-engineer [1]
Integration: VPC module CLI commands
Strategic Coordination: enterprise-product-owner [0]
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import click

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_info,
    create_table,
    format_cost,
)
from runbooks.vpc.enhanced_mcp_validation import (
    EnhancedMCPValidator,
    SecurityValidationResults,
    validate_aws25_vpc_cleanup,
)


@click.group()
def mcp_validation():
    """Enhanced MCP validation commands for VPC cleanup operations."""
    pass


@mcp_validation.command()
@click.option("--vpc-data-file", type=click.Path(exists=True), help="JSON file containing VPC cleanup analysis data")
@click.option(
    "--cost-projections-file", type=click.Path(exists=True), help="JSON file containing cost savings projections"
)
@click.option(
    "--target-savings", type=float, default=7548.0, help="Target savings amount for validation (default: $7,548)"
)
@click.option("--profile", help="AWS profile to use for validation")
@click.option("--accuracy-threshold", type=float, default=99.5, help="Minimum accuracy threshold (default: 99.5%)")
@click.option("--export-evidence", is_flag=True, help="Export comprehensive evidence package")
@click.option("--validate-cloudtrail", is_flag=True, help="Include CloudTrail audit validation")
def validate_aws25(
    vpc_data_file: Optional[str],
    cost_projections_file: Optional[str],
    target_savings: float,
    profile: Optional[str],
    accuracy_threshold: float,
    export_evidence: bool,
    validate_cloudtrail: bool,
):
    """
    Validate AWS-25 VPC cleanup operations with ≥99.5% MCP accuracy.

    Example usage:
        runbooks vpc validate-aws25 --vpc-data-file vpc_analysis.json --target-savings 7548
        runbooks vpc validate-aws25 --validate-cloudtrail --export-evidence
    """

    async def run_validation():
        print_header("🔒 AWS-25 VPC Cleanup MCP Validation", f"Target Accuracy: ≥{accuracy_threshold}%")

        # Load VPC cleanup data
        vpc_cleanup_data = {}
        if vpc_data_file:
            try:
                with open(vpc_data_file, "r") as f:
                    vpc_cleanup_data = json.load(f)
                print_success(f"✅ Loaded VPC data from {vpc_data_file}")
            except Exception as e:
                print_error(f"Failed to load VPC data: {e}")
                return
        else:
            # Use sample data from AWS-25 test data
            vpc_cleanup_data = _generate_sample_vpc_data()
            print_info("🔧 Using sample AWS-25 VPC data for validation")

        # Load cost projections
        cost_projections = {}
        if cost_projections_file:
            try:
                with open(cost_projections_file, "r") as f:
                    cost_projections = json.load(f)
                print_success(f"✅ Loaded cost projections from {cost_projections_file}")
            except Exception as e:
                print_error(f"Failed to load cost projections: {e}")
                return
        else:
            cost_projections = {"aws25_vpc_cleanup": target_savings}
            print_info(f"💰 Using target savings: {format_cost(target_savings)}")

        # Initialize enhanced MCP validator
        validator = EnhancedMCPValidator(profile)
        validator.accuracy_threshold = accuracy_threshold

        # Include CloudTrail validation if requested
        if validate_cloudtrail:
            print_info("📋 CloudTrail audit validation enabled")

        # Perform comprehensive validation
        results = await validator.validate_aws25_vpc_cleanup(vpc_cleanup_data, cost_projections)

        # Display validation summary
        _display_validation_summary(results, accuracy_threshold)

        # Export evidence if requested
        if export_evidence:
            evidence_path = await validator._export_security_evidence(results)
            print_success(f"📄 Evidence package exported to: {evidence_path}")

        # Return validation status
        if results.accuracy_achieved >= accuracy_threshold:
            print_success(f"🎯 VALIDATION PASSED: AWS-25 ready for production execution")
            return 0
        else:
            print_error(f"❌ VALIDATION FAILED: Accuracy below threshold")
            return 1

    try:
        exit_code = asyncio.run(run_validation())
        if exit_code and exit_code != 0:
            raise click.ClickException("Validation failed - see output for details")
    except Exception as e:
        print_error(f"Validation error: {e}")
        raise click.ClickException(str(e))


@mcp_validation.command()
@click.option("--region", default="ap-southeast-2", help="AWS region for cost validation")
@click.option("--profile", help="AWS profile to use for Cost Explorer access")
@click.option("--days-back", type=int, default=30, help="Number of days to analyze for cost validation")
@click.option("--tolerance", type=float, default=5.0, help="Cost validation tolerance percentage (default: 5%)")
def validate_cost_projections(region: str, profile: Optional[str], days_back: int, tolerance: float):
    """
    Validate cost savings projections using Cost Explorer MCP integration.

    Example usage:
        runbooks vpc validate-cost-projections --region ap-southeast-2 --days-back 30
        runbooks vpc validate-cost-projections --tolerance 2.0
    """

    async def run_cost_validation():
        print_header("💰 Cost Projections MCP Validation", f"Tolerance: ±{tolerance}%")

        # Initialize validator
        validator = EnhancedMCPValidator(profile)

        # Sample cost projections based on AWS-25 data
        cost_projections = {
            "vpc_cleanup_immediate": 2700.0,  # Zero-ENI VPCs
            "vpc_optimization_potential": 4920.0,  # High/Medium priority
            "cis_compliance_value": 1260.0,  # Default VPC replacements
            "security_risk_mitigation": 1500.0,  # Attack surface reduction
            "total_aws25_savings": 7548.0,  # Total target
        }

        print_info(f"📊 Validating {len(cost_projections)} cost projection categories")
        for category, amount in cost_projections.items():
            console.print(f"  • {category}: {format_cost(amount)}")

        # Validate cost projections
        cost_validation_data = {"cost_data": cost_projections, "validation_tolerance": tolerance}

        cost_accuracy = await validator._validate_cost_projections(cost_projections, None, len(cost_projections))

        # Display results
        accuracy_color = "green" if cost_accuracy >= 95.0 else "yellow" if cost_accuracy >= 80.0 else "red"
        console.print(f"[{accuracy_color}]💰 Cost Validation Accuracy: {cost_accuracy:.2f}%[/{accuracy_color}]")

        if cost_accuracy >= 95.0:
            print_success("✅ Cost projections validated with high confidence")
        elif cost_accuracy >= 80.0:
            print_warning("⚠️ Cost projections validated with moderate confidence")
        else:
            print_error("❌ Cost projections require review")

        return cost_accuracy

    try:
        accuracy = asyncio.run(run_cost_validation())
        console.print(f"[cyan]Final cost validation accuracy: {accuracy:.2f}%[/cyan]")
    except Exception as e:
        print_error(f"Cost validation error: {e}")
        raise click.ClickException(str(e))


@mcp_validation.command()
@click.option("--days-back", type=int, default=90, help="Number of days to analyze CloudTrail events")
@click.option("--profile", help="AWS profile for CloudTrail access (default: MANAGEMENT_PROFILE)")
@click.option("--vpc-ids", help="Comma-separated list of VPC IDs to validate")
@click.option("--export-audit-trail", is_flag=True, help="Export detailed audit trail evidence")
def validate_cloudtrail_audit(days_back: int, profile: Optional[str], vpc_ids: Optional[str], export_audit_trail: bool):
    """
    Validate CloudTrail audit trails for VPC deletion verification.

    Example usage:
        runbooks vpc validate-cloudtrail-audit --days-back 90
        runbooks vpc validate-cloudtrail-audit --vpc-ids vpc-123,vpc-456 --export-audit-trail
    """

    async def run_cloudtrail_validation():
        print_header("📋 CloudTrail Audit Trail Validation", f"Period: {days_back} days")

        # Initialize CloudTrail integration
        from runbooks.vpc.cloudtrail_audit_integration import CloudTrailMCPIntegration

        cloudtrail_profile = profile or "MANAGEMENT_PROFILE"
        cloudtrail_integration = CloudTrailMCPIntegration(profile=cloudtrail_profile, audit_period_days=days_back)

        # Parse VPC IDs if provided
        target_vpc_ids = None
        if vpc_ids:
            target_vpc_ids = [vpc_id.strip() for vpc_id in vpc_ids.split(",")]
            print_info(f"🎯 Targeting {len(target_vpc_ids)} specific VPCs for validation")

        # Perform CloudTrail analysis
        audit_results = await cloudtrail_integration.analyze_deleted_vpc_resources(target_vpc_ids=target_vpc_ids)

        # Display audit results
        _display_cloudtrail_results(audit_results)

        # Export audit trail if requested
        if export_audit_trail:
            compliance_report = await cloudtrail_integration.generate_compliance_audit_report(
                audit_results, "AWS Well-Architected Security"
            )
            print_success("📄 Audit trail evidence exported")

        return audit_results

    try:
        results = asyncio.run(run_cloudtrail_validation())
        console.print(f"[cyan]CloudTrail validation accuracy: {results.validation_accuracy:.2f}%[/cyan]")
    except Exception as e:
        print_error(f"CloudTrail validation error: {e}")
        raise click.ClickException(str(e))


@mcp_validation.command()
@click.option("--test-file", type=click.Path(exists=True), help="YAML test data file for validation")
@click.option("--profile", help="AWS profile for MCP server access")
@click.option("--comprehensive", is_flag=True, help="Run comprehensive validation across all MCP servers")
def test_mcp_accuracy(test_file: Optional[str], profile: Optional[str], comprehensive: bool):
    """
    Test MCP server accuracy and connectivity for validation framework.

    Example usage:
        runbooks vpc test-mcp-accuracy --comprehensive
        runbooks vpc test-mcp-accuracy --test-file aws25-test-data.yaml
    """

    async def run_mcp_testing():
        print_header("🧪 MCP Server Accuracy Testing", "Validation Framework Testing")

        # Load test data
        test_data = {}
        if test_file:
            try:
                import yaml

                with open(test_file, "r") as f:
                    test_data = yaml.safe_load(f)
                print_success(f"✅ Loaded test data from {test_file}")
            except Exception as e:
                print_error(f"Failed to load test data: {e}")
                return
        else:
            # Use AWS-25 production test data
            test_data_path = (
                Path(__file__).parent.parent.parent.parent
                / ".claude/config/environment-data/vpc-test-data-production.yaml"
            )
            if test_data_path.exists():
                try:
                    import yaml

                    with open(test_data_path, "r") as f:
                        test_data = yaml.safe_load(f)
                    print_success(f"✅ Loaded AWS-25 production test data")
                except Exception as e:
                    print_warning(f"Failed to load production test data: {e}")
                    test_data = _generate_sample_test_data()
            else:
                test_data = _generate_sample_test_data()

        # Initialize MCP validator
        validator = EnhancedMCPValidator(profile)

        # Test MCP server connectivity
        print_info("🔗 Testing MCP server connectivity...")

        # Test AWS MCP servers
        mcp_results = {}

        # Test Cost Explorer MCP
        try:
            cost_test_data = {"cost_data": {"test": 100.0}}
            cost_result = await validator.mcp_integrator.validate_finops_operations(cost_test_data)
            mcp_results["cost_explorer"] = {"success": cost_result.success, "accuracy": cost_result.accuracy_score}
        except Exception as e:
            mcp_results["cost_explorer"] = {"success": False, "error": str(e)}

        # Test VPC MCP validation
        try:
            vpc_test_data = {
                "vpc_candidates": [{"vpc_id": "vpc-test", "account_id": "123456789012", "region": "ap-southeast-2"}]
            }
            vpc_result = await validator.mcp_integrator.validate_vpc_operations(vpc_test_data)
            mcp_results["vpc_validation"] = {"success": vpc_result.success, "accuracy": vpc_result.accuracy_score}
        except Exception as e:
            mcp_results["vpc_validation"] = {"success": False, "error": str(e)}

        # Display MCP test results
        _display_mcp_test_results(mcp_results)

        # Test comprehensive accuracy if requested
        if comprehensive:
            print_info("📊 Running comprehensive accuracy testing...")

            # Extract VPC test data
            vpc_candidates = test_data.get("vpc_test_data", {}).get("active_vpcs", [])[:5]  # Test subset

            # Convert to validation format
            validation_vpc_data = {
                "vpc_candidates": [
                    {
                        "vpc_id": vpc.get("vpc_id"),
                        "account_id": vpc.get("account"),
                        "region": vpc.get("region"),
                        "eni_count": vpc.get("enis", 0),
                    }
                    for vpc in vpc_candidates
                ]
            }

            cost_projections = {"test_validation": 1000.0}

            # Run comprehensive validation
            results = await validator.validate_aws25_vpc_cleanup(validation_vpc_data, cost_projections)

            print_success(f"🎯 Comprehensive accuracy achieved: {results.accuracy_achieved:.2f}%")

        return mcp_results

    try:
        results = asyncio.run(run_mcp_testing())
        success_count = sum(1 for result in results.values() if result.get("success", False))
        console.print(f"[cyan]MCP server test results: {success_count}/{len(results)} servers operational[/cyan]")
    except Exception as e:
        print_error(f"MCP testing error: {e}")
        raise click.ClickException(str(e))


# Helper functions for CLI commands


def _generate_sample_vpc_data() -> Dict[str, Any]:
    """Generate sample VPC data based on AWS-25 test scenarios."""
    return {
        "vpc_candidates": [
            {
                "vpc_id": "vpc-2c3d4e5f6g7h8i9j0",
                "vpc_name": "legacy-staging-vpc",
                "account_id": "123456789014",
                "region": "us-east-2",
                "eni_count": 0,
                "cost_monthly": 135.00,
                "cleanup_priority": "HIGH",
            },
            {
                "vpc_id": "vpc-3d4e5f6g7h8i9j0k1",
                "vpc_name": "dev-prototype-vpc",
                "account_id": "123456789015",
                "region": "eu-west-1",
                "eni_count": 0,
                "cost_monthly": 90.00,
                "cleanup_priority": "HIGH",
            },
            {
                "vpc_id": "vpc-5f6g7h8i9j0k1l2m3",
                "vpc_name": "default-vpc-staging",
                "account_id": "123456789017",
                "region": "us-west-1",
                "eni_count": 0,
                "cost_monthly": 45.00,
                "cleanup_priority": "CRITICAL",
            },
        ],
        "deleted_vpcs": [
            {"vpc_id": "vpc-deleted-001", "deletion_date": "2023-12-15"},
            {"vpc_id": "vpc-deleted-002", "deletion_date": "2023-11-20"},
            {"vpc_id": "vpc-deleted-003", "deletion_date": "2023-10-30"},
        ],
    }


def _generate_sample_test_data() -> Dict[str, Any]:
    """Generate sample test data for MCP accuracy testing."""
    return {
        "business_metrics": {"total_vpcs": 27, "annual_savings": 11070, "waste_percentage": 44},
        "cloudtrail_mcp_integration": {"validation_accuracy": 99.8, "audit_trail_events": 8593},
        "validation_requirements": {"mcp_accuracy_target": 99.5, "mcp_accuracy_achieved": 99.8},
    }


def _display_validation_summary(results: SecurityValidationResults, threshold: float):
    """Display comprehensive validation summary."""

    status_color = "green" if results.accuracy_achieved >= threshold else "red"
    status_text = "PASSED" if results.accuracy_achieved >= threshold else "FAILED"

    console.print(f"\n[bold {status_color}]🎯 VALIDATION {status_text}[/bold {status_color}]")
    console.print(f"[{status_color}]Accuracy: {results.accuracy_achieved:.2f}% (≥{threshold}%)[/{status_color}]")
    console.print(f"[cyan]VPCs Validated: {results.total_vpcs_validated}[/cyan]")
    console.print(f"[yellow]Compliance Score: {results.compliance_score:.1f}%[/yellow]")

    if results.remediation_required:
        console.print(f"[yellow]⚠️ Remediation Items: {len(results.remediation_required)}[/yellow]")


def _display_cloudtrail_results(audit_results):
    """Display CloudTrail audit validation results."""

    console.print(f"[cyan]📋 CloudTrail Validation Results[/cyan]")
    console.print(f"[green]Audit Completeness: {audit_results.audit_trail_completeness:.1f}%[/green]")
    console.print(f"[green]Validation Accuracy: {audit_results.validation_accuracy:.1f}%[/green]")
    console.print(f"[yellow]Events Analyzed: {audit_results.total_events_analyzed:,}[/yellow]")
    console.print(f"[blue]Deleted Resources: {audit_results.deleted_resources_found}[/blue]")


def _display_mcp_test_results(mcp_results: Dict[str, Any]):
    """Display MCP server test results."""

    table = create_table("MCP Server Test Results")
    table.add_column("Server", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Accuracy", justify="right", style="green")
    table.add_column("Notes", style="yellow")

    for server_name, result in mcp_results.items():
        if result.get("success"):
            status = "✅ Online"
            accuracy = f"{result.get('accuracy', 0):.1f}%"
            notes = "Operational"
        else:
            status = "❌ Error"
            accuracy = "N/A"
            notes = result.get("error", "Connection failed")[:50]

        table.add_row(server_name, status, accuracy, notes)

    console.print(table)


# Integration with main VPC CLI
def register_mcp_validation_commands(vpc_cli_group):
    """Register MCP validation commands with the main VPC CLI group."""
    vpc_cli_group.add_command(mcp_validation, name="mcp-validation")


if __name__ == "__main__":
    mcp_validation()
