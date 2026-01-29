#!/usr/bin/env python3
"""
Security CLI Commands - Dynamic Configuration Support

Enhanced security CLI with enterprise configuration patterns:
- Dynamic account discovery (environment variables, config files, Organizations API)
- Dynamic compliance weights and thresholds
- Profile override support (--profile parameter)
- Multi-account operations (--all flag)
- Configuration-driven approach eliminating hardcoded values

Author: DevOps Security Engineer (Claude Code Enterprise Team)
Version: 1.0 - Enterprise Dynamic Configuration Ready
"""

import asyncio
import os
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel

from runbooks.common.profile_utils import get_profile_for_operation, validate_profile_access
from runbooks.common.rich_utils import (
    console,
    create_panel,
    print_error,
    print_info,
    print_success,
    print_warning,
)

from .compliance_automation_engine import ComplianceAutomationEngine, ComplianceFramework
from .security_baseline_tester import SecurityBaselineTester
from .config_template_generator import SecurityConfigTemplateGenerator
from .two_way_validation_framework import execute_2way_validation


@click.group()
@click.option("--profile", default=None, help="AWS profile to use (overrides environment variables)")
@click.option("--output-dir", default="./artifacts/security", help="Output directory for security reports")
@click.pass_context
def security(ctx, profile: Optional[str], output_dir: str):
    """
    Enterprise Security Operations with Dynamic Configuration.

    Supports configuration via:
    - Environment variables
    - Configuration files
    - AWS Organizations API
    - Profile override patterns
    """
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["output_dir"] = output_dir

    # Validate profile if specified
    if profile:
        resolved_profile = get_profile_for_operation("management", profile)
        if not validate_profile_access(resolved_profile, "security operations"):
            print_error(f"Profile validation failed: {resolved_profile}")
            raise click.Abort()


@security.command()
@click.option(
    "--frameworks",
    multiple=True,
    type=click.Choice(
        ["aws-well-architected", "soc2-type-ii", "pci-dss", "hipaa", "iso27001", "nist-cybersecurity", "cis-benchmarks"]
    ),
    default=["aws-well-architected"],
    help="Compliance frameworks to assess",
)
@click.option("--accounts", help="Comma-separated account IDs (overrides discovery)")
@click.option("--all", "all_accounts", is_flag=True, help="Assess all discovered accounts via Organizations API")
@click.option("--scope", type=click.Choice(["full", "quick", "critical"]), default="full", help="Assessment scope")
@click.option(
    "--export-formats",
    multiple=True,
    type=click.Choice(["json", "csv", "html", "pdf"]),
    default=["json", "csv"],
    help="Export formats for compliance reports",
)
@click.pass_context
def assess(
    ctx, frameworks: List[str], accounts: Optional[str], all_accounts: bool, scope: str, export_formats: List[str]
):
    """
    Execute comprehensive compliance assessment with dynamic configuration.

    Environment Variables Supported:
    - COMPLIANCE_TARGET_ACCOUNTS: Comma-separated account IDs
    - COMPLIANCE_ACCOUNTS_CONFIG: Path to accounts configuration file
    - COMPLIANCE_WEIGHT_<CONTROL_ID>: Dynamic control weights
    - COMPLIANCE_THRESHOLD_<FRAMEWORK>: Dynamic framework thresholds
    """
    profile = ctx.obj["profile"]
    output_dir = ctx.obj["output_dir"]

    try:
        # Convert framework names to enum values
        framework_mapping = {
            "aws-well-architected": ComplianceFramework.AWS_WELL_ARCHITECTED,
            "soc2-type-ii": ComplianceFramework.SOC2_TYPE_II,
            "pci-dss": ComplianceFramework.PCI_DSS,
            "hipaa": ComplianceFramework.HIPAA,
            "iso27001": ComplianceFramework.ISO27001,
            "nist-cybersecurity": ComplianceFramework.NIST_CYBERSECURITY,
            "cis-benchmarks": ComplianceFramework.CIS_BENCHMARKS,
        }

        selected_frameworks = [framework_mapping[f] for f in frameworks]

        # Parse target accounts
        target_accounts = None
        if accounts:
            target_accounts = [acc.strip() for acc in accounts.split(",")]
            print_info(f"Using specified accounts: {len(target_accounts)} accounts")
        elif all_accounts:
            print_info("Using all discovered accounts via Organizations API")
            # target_accounts will be None, triggering discovery
        else:
            print_info("Using default account discovery")

        # Initialize compliance engine
        console.print(
            create_panel(
                f"[bold cyan]Enterprise Compliance Assessment[/bold cyan]\n\n"
                f"[dim]Frameworks: {', '.join(frameworks)}[/dim]\n"
                f"[dim]Profile: {profile or 'default'}[/dim]\n"
                f"[dim]Scope: {scope}[/dim]\n"
                f"[dim]Export Formats: {', '.join(export_formats)}[/dim]",
                title="🛡️ Starting Assessment",
                border_style="cyan",
            )
        )

        compliance_engine = ComplianceAutomationEngine(profile=profile, output_dir=output_dir)

        # Execute assessment
        reports = asyncio.run(
            compliance_engine.assess_compliance(
                frameworks=selected_frameworks, target_accounts=target_accounts, scope=scope
            )
        )

        # Display summary
        print_success(f"Assessment completed! Generated {len(reports)} compliance reports")
        print_info(f"Reports saved to: {output_dir}")

        # Display configuration sources used
        _display_configuration_sources()

    except Exception as e:
        print_error(f"Compliance assessment failed: {str(e)}")
        raise click.Abort()


@security.command()
@click.option("--language", type=click.Choice(["en", "ja", "ko", "vi"]), default="en", help="Report language")
@click.option(
    "--export-formats",
    multiple=True,
    type=click.Choice(["json", "csv", "html", "pdf"]),
    default=["json", "csv"],
    help="Export formats for security reports",
)
@click.pass_context
def baseline(ctx, language: str, export_formats: List[str]):
    """
    Execute security baseline assessment with dynamic configuration.

    Uses enterprise profile management and configuration-driven approach.
    """
    profile = ctx.obj["profile"]
    output_dir = ctx.obj["output_dir"]

    try:
        console.print(
            create_panel(
                f"[bold cyan]AWS Security Baseline Assessment[/bold cyan]\n\n"
                f"[dim]Profile: {profile or 'default'}[/dim]\n"
                f"[dim]Language: {language}[/dim]\n"
                f"[dim]Export Formats: {', '.join(export_formats)}[/dim]",
                title="🔒 Starting Baseline Assessment",
                border_style="green",
            )
        )

        # Initialize security baseline tester
        baseline_tester = SecurityBaselineTester(
            profile=profile, lang_code=language, output_dir=output_dir, export_formats=list(export_formats)
        )

        # Execute baseline assessment
        baseline_tester.run()

        print_success("Security baseline assessment completed successfully!")
        print_info(f"Results saved to: {output_dir}")

    except Exception as e:
        print_error(f"Security baseline assessment failed: {str(e)}")
        raise click.Abort()


@security.command()
@click.pass_context
def config_info(ctx):
    """
    Display current security configuration and environment setup.
    """
    console.print(Panel.fit("[bold cyan]Security Configuration Information[/bold cyan]", border_style="cyan"))

    # Display environment variables
    print_info("Environment Configuration:")

    env_vars = {
        "Profile Configuration": {
            "MANAGEMENT_PROFILE": os.getenv("MANAGEMENT_PROFILE", "Not set"),
            "BILLING_PROFILE": os.getenv("BILLING_PROFILE", "Not set"),
            "CENTRALISED_OPS_PROFILE": os.getenv("CENTRALISED_OPS_PROFILE", "Not set"),
        },
        "Compliance Configuration": {
            "COMPLIANCE_TARGET_ACCOUNTS": os.getenv("COMPLIANCE_TARGET_ACCOUNTS", "Not set"),
            "COMPLIANCE_ACCOUNTS_CONFIG": os.getenv("COMPLIANCE_ACCOUNTS_CONFIG", "Not set"),
            "COMPLIANCE_WEIGHTS_CONFIG": os.getenv("COMPLIANCE_WEIGHTS_CONFIG", "Not set"),
            "COMPLIANCE_THRESHOLDS_CONFIG": os.getenv("COMPLIANCE_THRESHOLDS_CONFIG", "Not set"),
        },
        "Remediation Configuration": {
            "REMEDIATION_TARGET_ACCOUNTS": os.getenv("REMEDIATION_TARGET_ACCOUNTS", "Not set"),
            "REMEDIATION_ACCOUNT_CONFIG": os.getenv("REMEDIATION_ACCOUNT_CONFIG", "Not set"),
        },
    }

    for category, variables in env_vars.items():
        console.print(f"\n[bold]{category}:[/bold]")
        for var_name, var_value in variables.items():
            status = "✅" if var_value != "Not set" else "❌"
            console.print(f"  {status} {var_name}: {var_value}")

    # Display example configuration files
    console.print("\n[bold]Example Configuration Files:[/bold]")
    config_examples = [
        "src/runbooks/security/config/compliance_weights_example.json",
        "src/runbooks/remediation/config/accounts_example.json",
    ]

    for config_file in config_examples:
        if os.path.exists(config_file):
            console.print(f"  ✅ {config_file}")
        else:
            console.print(f"  📝 {config_file} (example)")


def _display_configuration_sources():
    """Display information about configuration sources used."""
    console.print("\n[bold]Configuration Sources:[/bold]")

    # Check environment variables
    if os.getenv("COMPLIANCE_TARGET_ACCOUNTS"):
        console.print("  ✅ Using COMPLIANCE_TARGET_ACCOUNTS environment variable")

    if os.getenv("COMPLIANCE_ACCOUNTS_CONFIG"):
        config_path = os.getenv("COMPLIANCE_ACCOUNTS_CONFIG")
        if os.path.exists(config_path):
            console.print(f"  ✅ Using accounts config file: {config_path}")
        else:
            console.print(f"  ⚠️  Accounts config file not found: {config_path}")

    if os.getenv("COMPLIANCE_WEIGHTS_CONFIG"):
        config_path = os.getenv("COMPLIANCE_WEIGHTS_CONFIG")
        if os.path.exists(config_path):
            console.print(f"  ✅ Using compliance weights config: {config_path}")
        else:
            console.print(f"  ⚠️  Compliance weights config not found: {config_path}")

    # Check for dynamic control weights
    weight_vars = [var for var in os.environ.keys() if var.startswith("COMPLIANCE_WEIGHT_")]
    if weight_vars:
        console.print(f"  ✅ Using {len(weight_vars)} dynamic control weights")

    # Check for dynamic thresholds
    threshold_vars = [var for var in os.environ.keys() if var.startswith("COMPLIANCE_THRESHOLD_")]
    if threshold_vars:
        console.print(f"  ✅ Using {len(threshold_vars)} dynamic framework thresholds")

    if not any(
        [os.getenv("COMPLIANCE_TARGET_ACCOUNTS"), os.getenv("COMPLIANCE_ACCOUNTS_CONFIG"), weight_vars, threshold_vars]
    ):
        console.print("  ℹ️  Using default configuration (Organizations API discovery)")


@security.command("2way-validate")
@click.option("--profile", default="${MANAGEMENT_PROFILE}", help="AWS profile for validation testing")
@click.option(
    "--certification-required", is_flag=True, help="Require production certification (≥97% combined accuracy)"
)
@click.pass_context
def two_way_validate(ctx, profile: str, certification_required: bool):
    """
    Execute comprehensive 2-Way Validation Framework for production readiness.

    Combines Playwright MCP (UI/browser testing) with AWS MCP (real API validation)
    to achieve ≥97% combined accuracy for enterprise production deployment.

    **SECURITY VALIDATION SCOPE**:
    - Playwright MCP: >98% browser testing success rate
    - AWS MCP: >97.5% real AWS API validation accuracy
    - Combined Accuracy: ≥97% overall validation requirement
    - Enterprise Compliance: Audit trail and production certification
    """
    try:
        console.print(
            create_panel(
                f"[bold cyan]🚨 Enterprise 2-Way Validation Framework[/bold cyan]\n\n"
                f"[dim]Profile: {profile}[/dim]\n"
                f"[dim]Certification Required: {'Yes' if certification_required else 'No'}[/dim]\n"
                f"[dim]Target Accuracy: ≥97% Combined[/dim]",
                title="🛡️ Security Validation Execution",
                border_style="cyan",
            )
        )

        print_info("🚀 Initiating comprehensive 2-way validation framework...")

        # Execute 2-way validation
        results = asyncio.run(execute_2way_validation(profile))

        # Display results
        certification_status = results["overall_status"]
        combined_accuracy = results["combined_accuracy"]["combined_accuracy"]

        if certification_status == "CERTIFIED":
            print_success(f"🏆 2-Way Validation: PRODUCTION CERTIFIED")
            print_success(f"📊 Combined Accuracy: {combined_accuracy * 100:.1f}%")
        else:
            print_warning(f"⚠️ 2-Way Validation: REQUIRES REVIEW")
            print_warning(f"📊 Combined Accuracy: {combined_accuracy * 100:.1f}%")

        # Display detailed metrics
        playwright_success = results["playwright_validation"]["success_rate"]
        aws_mcp_accuracy = results["aws_mcp_validation"]["accuracy_rate"]
        compliance_score = results["enterprise_compliance"]["compliance_score"]

        console.print(f"\n[bold cyan]Validation Metrics:[/bold cyan]")
        console.print(f"🎭 Playwright Success Rate: {playwright_success * 100:.1f}%")
        console.print(f"☁️ AWS MCP Accuracy Rate: {aws_mcp_accuracy * 100:.1f}%")
        console.print(f"🏢 Enterprise Compliance Score: {compliance_score * 100:.1f}%")

        # Handle certification requirements
        if certification_required and certification_status != "CERTIFIED":
            print_error("❌ Production certification required but not achieved")

            if results["recommendations"]:
                console.print(f"\n[bold yellow]Recommendations:[/bold yellow]")
                for recommendation in results["recommendations"]:
                    console.print(f"• {recommendation}")

            raise click.Abort()

        print_success("✅ 2-Way Validation Framework execution completed")
        print_info(f"📁 Evidence package saved to: ./artifacts/2way_validation_evidence/")

    except Exception as e:
        print_error(f"2-Way validation failed: {str(e)}")
        raise click.Abort()


@security.command("generate-config")
@click.option(
    "--output-dir", default="./artifacts/security/config", help="Output directory for configuration templates"
)
@click.pass_context
def generate_config_templates(ctx, output_dir: str):
    """
    Generate universal configuration templates for security operations.

    Creates templates for:
    - Compliance weights and thresholds
    - Account discovery configuration
    - Environment variable examples
    - Complete setup documentation

    All templates support universal AWS compatibility with no hardcoded values.
    """
    print_info(f"Generating universal security configuration templates in {output_dir}...")

    try:
        generator = SecurityConfigTemplateGenerator(output_dir)
        generator.generate_all_templates()

        print_success("Configuration templates generated successfully!")
        console.print("\n[bold yellow]Next steps:[/bold yellow]")
        console.print("1. Review and customize the generated configuration files")
        console.print("2. Set environment variables or copy configuration files to your preferred location")
        console.print("3. Run: runbooks security assess --help")
        console.print("4. Run: runbooks security 2way-validate --help")

    except Exception as e:
        print_error(f"Failed to generate configuration templates: {e}")
        raise click.Abort()


@security.command("deploy-guardduty")
@click.option(
    "--profile",
    default="MANAGEMENT_PROFILE",
    help="AWS profile for management account (Organizations + GuardDuty admin)",
)
@click.option("--delegated-admin", required=True, help="Account ID for GuardDuty delegated administrator")
@click.option("--region", default="ap-southeast-2", help="AWS region for GuardDuty operations")
@click.option(
    "--auto-enable-new-accounts/--no-auto-enable", default=True, help="Auto-enable GuardDuty for new accounts"
)
@click.option("--dry-run/--execute", default=True, help="Dry-run mode (default) or execute deployment")
@click.option(
    "--output-file", default="/tmp/guardduty-deployment-report.xlsx", help="Output file for deployment report"
)
@click.pass_context
def deploy_guardduty(
    ctx,
    profile: str,
    delegated_admin: str,
    region: str,
    auto_enable_new_accounts: bool,
    dry_run: bool,
    output_file: str,
):
    """
    Deploy GuardDuty organization-wide with delegated admin configuration (JIRA AWSO-64).

    This command provides comprehensive GuardDuty deployment across AWS Organizations:

    \b
    Deployment Steps:
    1. Discover all accounts in organization
    2. Check current GuardDuty status across accounts
    3. Configure delegated admin account
    4. Enable GuardDuty across all active accounts
    5. Configure auto-enable for new accounts
    6. Validate 100% coverage and generate report

    \b
    Best Practices:
    - Delegated admin: Use Security/Audit account (not management account)
    - Auto-enable: Recommended (automatically enables for new accounts)
    - Finding aggregation: Central account receives all findings
    - Dry-run first: Always test deployment plan before execution

    \b
    GuardDuty Configuration:
    - Finding frequency: FIFTEEN_MINUTES (fastest detection)
    - S3 data events: ENABLED (bucket threat detection)
    - Kubernetes audit logs: ENABLED (EKS security)
    - Malware protection: ENABLED (EBS volume scanning)

    \b
    Examples:

      # Dry-run deployment plan (safe, no changes)
      runbooks security deploy-guardduty --delegated-admin 123456789012 --dry-run

      # Execute organization-wide deployment
      runbooks security deploy-guardduty --delegated-admin 123456789012 --execute

      # Deploy without auto-enable for new accounts
      runbooks security deploy-guardduty --delegated-admin 123456789012 --no-auto-enable --execute
    """
    import time
    from runbooks.security.guardduty_org_deployment import (
        GuardDutyOrgDeployment,
        print_deployment_plan,
    )

    try:
        start_time = time.time()

        # Display deployment header
        console.print(
            create_panel(
                f"[bold cyan]🛡️ GuardDuty Organization-wide Deployment[/bold cyan]\n\n"
                f"[dim]Profile: {profile}[/dim]\n"
                f"[dim]Delegated Admin: {delegated_admin}[/dim]\n"
                f"[dim]Region: {region}[/dim]\n"
                f"[dim]Auto-enable New Accounts: {'Yes' if auto_enable_new_accounts else 'No'}[/dim]\n"
                f"[dim]Mode: {'🔍 DRY-RUN (no changes)' if dry_run else '⚡ EXECUTE (deployment)'}[/dim]",
                title="🚨 Enterprise Security Deployment",
                border_style="cyan",
            )
        )

        if not dry_run:
            console.print(
                create_panel(
                    "[bold red]⚠️  EXECUTE MODE ACTIVE[/bold red]\n\n"
                    "[yellow]This will make changes to your AWS Organization:[/yellow]\n"
                    "• Configure GuardDuty delegated admin\n"
                    "• Enable GuardDuty detectors across accounts\n"
                    "• Configure data sources (S3, Kubernetes, Malware Protection)\n"
                    "• Enable auto-enable for new accounts\n\n"
                    "[bold]Proceeding in 5 seconds...[/bold]",
                    border_style="red",
                )
            )
            time.sleep(5)

        # Initialize deployment engine
        deployment = GuardDutyOrgDeployment(
            profile=profile,
            delegated_admin_account=delegated_admin,
            region=region,
        )

        # Step 1: Discover organization
        org_data = deployment.discover_organization()

        # Step 2: Check current GuardDuty status
        status_df = deployment.check_guardduty_status(org_data["accounts"])

        # Step 3: Display deployment plan (dry-run mode)
        if dry_run:
            print_deployment_plan(status_df, delegated_admin, auto_enable_new_accounts)
        else:
            # Execute deployment
            # Step 3a: Configure delegated admin
            admin_success = deployment.configure_delegated_admin(delegated_admin, dry_run=False)

            if not admin_success:
                print_error("Delegated admin configuration failed - aborting deployment")
                raise click.Abort()

            # Step 3b: Enable GuardDuty org-wide
            newly_enabled, already_enabled, errors = deployment.enable_guardduty_org_wide(
                org_data["accounts"],
                auto_enable=auto_enable_new_accounts,
                dry_run=False,
            )

            print_info(f"Deployment results: {newly_enabled} newly enabled, {already_enabled} already enabled")

            if errors:
                print_warning(f"Encountered {len(errors)} errors during deployment")
                for error in errors[:5]:  # Show first 5 errors
                    print_error(f"  - {error}")

            # Re-check status after deployment
            status_df = deployment.check_guardduty_status(org_data["accounts"])

        # Step 4: Validate deployment
        validation_results = deployment.validate_deployment(status_df)

        # Step 5: Generate and export report
        execution_time = time.time() - start_time

        deployment_metadata = {
            "newly_enabled": 0 if dry_run else newly_enabled if "newly_enabled" in locals() else 0,
            "already_enabled": 0 if dry_run else already_enabled if "already_enabled" in locals() else 0,
            "auto_enable": auto_enable_new_accounts,
            "execution_time": execution_time,
            "dry_run": dry_run,
            "errors": [] if dry_run else (errors if "errors" in locals() else []),
        }

        report = deployment.generate_deployment_report(
            org_data,
            status_df,
            validation_results,
            deployment_metadata,
        )

        deployment.export_report(report, output_file)

        # Final summary
        if dry_run:
            console.print(
                create_panel(
                    f"[bold cyan]✅ Deployment Plan Generated[/bold cyan]\n\n"
                    f"Coverage: [yellow]{report.coverage_percentage:.1f}%[/yellow]\n"
                    f"Would enable: [cyan]{len(status_df[status_df['guardduty_status'] == 'DISABLED'])} accounts[/cyan]\n"
                    f"Already enabled: [green]{report.accounts_enabled} accounts[/green]\n\n"
                    f"[bold green]📊 Report: {output_file}[/bold green]\n\n"
                    f"[yellow]To execute deployment, run with --execute flag[/yellow]",
                    title="🔍 Dry-Run Complete",
                    border_style="green",
                )
            )
        else:
            console.print(
                create_panel(
                    f"[bold green]🎉 GuardDuty Deployment Complete[/bold green]\n\n"
                    f"Coverage: [cyan]{report.coverage_percentage:.1f}%[/cyan]\n"
                    f"Newly enabled: [green]{report.accounts_newly_enabled} accounts[/green]\n"
                    f"Already enabled: [cyan]{report.accounts_already_enabled} accounts[/cyan]\n"
                    f"Failed: [red]{report.accounts_failed} accounts[/red]\n"
                    f"Execution time: [dim]{execution_time:.1f}s[/dim]\n\n"
                    f"[bold cyan]📊 Report: {output_file}[/bold cyan]",
                    title="✅ Deployment Success",
                    border_style="green",
                )
            )

        print_success("GuardDuty organization-wide deployment completed successfully!")

    except Exception as e:
        print_error(f"GuardDuty deployment failed: {str(e)}")
        raise click.Abort()


@security.command("remediate-findings")
@click.option(
    "--profile", default="${MANAGEMENT_PROFILE}", help="AWS profile with SecurityHub and Organizations permissions"
)
@click.option("--accounts", default=None, help="Comma-separated account IDs (default: discover all from organization)")
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]),
    default="HIGH",
    help="Minimum severity level for findings",
)
@click.option(
    "--finding-types",
    default="Security Group,IAM,S3",
    help="Comma-separated finding types to remediate",
)
@click.option("--dry-run/--execute", default=True, help="Dry-run mode (safe default) or execute remediation")
@click.option(
    "--output-file",
    default="/tmp/securityhub-findings.xlsx",
    help="Output file for findings report (Excel format)",
)
@click.option(
    "--remediation-plan-file",
    default="/tmp/securityhub-remediation-plan.json",
    help="Output file for remediation plan (JSON format)",
)
@click.option("--region", default="ap-southeast-2", help="AWS region for Security Hub operations")
@click.pass_context
def remediate_findings(
    ctx, profile, accounts, severity, finding_types, dry_run, output_file, remediation_plan_file, region
):
    """
    Remediate Security Hub findings across multi-account organization (JIRA AWSO-63/62/61).

    This command automates the discovery and remediation of Security Hub findings
    with support for 25+ accounts via Organizations API integration.

    Finding Types:
    - Security Group: Unrestricted ingress rules (0.0.0.0/0), unused security groups
    - IAM: Overprivileged roles, unused credentials, missing MFA
    - S3: Public buckets, missing encryption, versioning disabled
    - CloudTrail: Not encrypted, log file validation disabled
    - Config: Recorder not enabled, insufficient retention

    Remediation Modes:
    - Dry-run (default): Analyze findings and generate remediation plan without changes
    - Execute: Apply remediation actions with approval gates for high-risk changes

    Safety Features:
    - Dry-run mode enabled by default
    - Approval gates for CRITICAL and HIGH severity findings
    - Multi-account validation before execution
    - Complete audit trail generation

    Example Usage:
        # Discover HIGH severity findings (dry-run)
        runbooks security remediate-findings --severity HIGH --dry-run

        # Multi-account Security Group remediation (dry-run)
        runbooks security remediate-findings --finding-types "Security Group" --dry-run

        # Execute remediation with approval (IAM findings)
        runbooks security remediate-findings --finding-types IAM --execute

        # Custom account list with CRITICAL findings
        runbooks security remediate-findings --accounts 123456789012,987654321098 --severity CRITICAL
    """
    try:
        from runbooks.security.securityhub_finding_remediation import SecurityHubFindingRemediation

        # Display operation banner
        mode_text = "DRY-RUN (Safe Mode)" if dry_run else "EXECUTE (Changes Applied)"
        console.print(
            create_panel(
                f"[bold cyan]🛡️ Security Hub Finding Remediation[/bold cyan]\n\n"
                f"[dim]Profile: {profile}[/dim]\n"
                f"[dim]Severity: {severity}[/dim]\n"
                f"[dim]Finding Types: {finding_types}[/dim]\n"
                f"[dim]Mode: {mode_text}[/dim]\n"
                f"[dim]Region: {region}[/dim]",
                title="🔒 Track 3: Security Hub Integration",
                border_style="cyan",
            )
        )

        # Parse accounts if provided
        account_list = None
        if accounts:
            account_list = [acc.strip() for acc in accounts.split(",")]
            print_info(f"Using specified accounts: {len(account_list)} accounts")

        # Initialize remediation engine
        remediation = SecurityHubFindingRemediation(
            profile=profile, accounts=account_list, severity=severity, region=region
        )

        print_info(f"Targeting {len(remediation.accounts)} accounts for Security Hub findings discovery")

        # Discover findings
        finding_types_list = [ft.strip() for ft in finding_types.split(",")]
        findings = remediation.discover_findings(finding_types=finding_types_list, compliance_status="FAILED")

        if not findings:
            print_warning(f"No {severity} severity findings discovered")
            console.print(
                "\n[dim]Possible reasons:[/dim]\n"
                "[dim]• Security Hub not enabled in target accounts[/dim]\n"
                "[dim]• No findings match severity and compliance filters[/dim]\n"
                "[dim]• Insufficient permissions (securityhub:GetFindings required)[/dim]"
            )
            return

        # Classify findings
        findings_df = remediation.classify_findings(findings)

        # Display summary
        console.print(f"\n[bold green]✅ Finding Discovery Summary[/bold green]")
        console.print(f"Total Findings: {len(findings_df)}")
        console.print(f"Accounts Covered: {findings_df['Account ID'].nunique()}")
        console.print(f"Finding Types: {', '.join(findings_df['Finding Type'].unique())}")

        # Display findings by type
        console.print(f"\n[bold]Findings by Type:[/bold]")
        for finding_type, count in findings_df["Finding Type"].value_counts().items():
            console.print(f"  • {finding_type}: {count}")

        # Display findings by severity
        console.print(f"\n[bold]Findings by Severity:[/bold]")
        for sev, count in findings_df["Severity"].value_counts().items():
            console.print(f"  • {sev}: {count}")

        # Generate remediation plan
        remediation_plan = remediation.generate_remediation_plan(findings_df)

        # Display remediation summary
        console.print(f"\n[bold yellow]📋 Remediation Plan Summary[/bold yellow]")
        console.print(f"Total Remediations: {len(remediation_plan['remediations'])}")

        automated_count = sum(1 for r in remediation_plan["remediations"] if r["remediation_available"])
        manual_count = len(remediation_plan["remediations"]) - automated_count

        console.print(f"Automated Actions: {automated_count}")
        console.print(f"Manual Review Required: {manual_count}")

        # Execute remediation (dry-run or actual)
        results = remediation.execute_remediation(remediation_plan, dry_run=dry_run)

        # Display execution results
        console.print(f"\n[bold cyan]🔧 Remediation Execution Results[/bold cyan]")
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        for status, count in status_counts.items():
            console.print(f"  • {status}: {count}")

        # Export findings report
        remediation.export_findings_report(findings_df, output_file)

        # Export remediation plan
        remediation.export_remediation_plan(remediation_plan, remediation_plan_file)

        # Final summary
        console.print(
            create_panel(
                f"[bold green]✅ Security Hub Remediation Complete[/bold green]\n\n"
                f"[dim]Findings Report: {output_file}[/dim]\n"
                f"[dim]Remediation Plan: {remediation_plan_file}[/dim]\n"
                f"[dim]Mode: {mode_text}[/dim]",
                title="📊 Results",
                border_style="green",
            )
        )

        if dry_run:
            console.print(
                "\n[bold yellow]Next Steps:[/bold yellow]\n"
                "[dim]1. Review findings report and remediation plan[/dim]\n"
                "[dim]2. Run with --execute flag to apply changes[/dim]\n"
                "[dim]3. Monitor Security Hub for finding status updates[/dim]"
            )

    except Exception as e:
        print_error(f"Security Hub remediation failed: {str(e)}")
        import traceback

        console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise click.Abort()


if __name__ == "__main__":
    security()
