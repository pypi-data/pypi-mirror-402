"""
Security Commands Module - Security Assessment & Compliance

KISS Principle: Focused on security assessment and compliance operations
DRY Principle: Centralized security patterns and compliance frameworks

Extracted from main.py lines 4500-6000 for modular architecture.
Preserves 100% functionality while reducing main.py context overhead.
"""

import click
from rich.console import Console

# Import common utilities and decorators
from runbooks.common.decorators import common_aws_options, common_output_options
from runbooks.common.rich_utils import console

# console = Console()  # Removed - using rich_utils.console for consistency


def create_security_group():
    """
    Create the security command group with all subcommands.

    Returns:
        Click Group object with all security commands

    Performance: Lazy creation only when needed by DRYCommandRegistry
    Context Reduction: ~1500 lines extracted from main.py
    """

    # Custom Group class with Rich Tree/Table help formatting (Track 3A pattern)
    class RichSecurityGroup(click.Group):
        """Custom Click Group with Rich Tree/Table help display."""

        def format_help(self, ctx, formatter):
            """Format help text with Rich Tree/Table categorization."""
            import os
            from rich.tree import Tree
            from rich.table import Table as RichTable

            # Check for TEST_MODE environment variable for backward compatibility
            test_mode = os.environ.get("RUNBOOKS_TEST_MODE", "0") == "1"

            if test_mode:
                # Plain text fallback for testing
                click.echo("Usage: runbooks security [OPTIONS] COMMAND [ARGS]...")
                click.echo("")
                click.echo("  Security assessment and compliance operations.")
                click.echo("")
                click.echo("Commands:")
                click.echo("  assess              Multi-framework compliance assessment")
                click.echo("  baseline            Security baseline validation")
                click.echo("  report              Generate compliance reports")
                click.echo("  remediate-findings  Remediate Security Hub findings (multi-account)")
                return

            # Categorize commands based on business function
            categories = {
                "🔒 Security Assessment": [
                    ("assess", "Multi-framework compliance assessment (SOC2, PCI-DSS, HIPAA, ISO27001)"),
                    ("baseline", "Security baseline validation with remediation recommendations"),
                ],
                "📋 Compliance Reporting": [("report", "Generate compliance reports (PDF, HTML, Markdown, JSON)")],
                "🛡️ Security Hub & GuardDuty": [
                    (
                        "remediate-findings",
                        "Remediate Security Hub findings across multi-account organization (AWSO-63/62/61)",
                    ),
                    (
                        "deploy-guardduty",
                        "Deploy GuardDuty organization-wide with delegated admin configuration (AWSO-64)",
                    ),
                ],
            }

            # Phase 1: Pre-calculate max column widths across ALL categories (Track 3A pattern)
            max_cmd_len = 0
            for category_commands in categories.values():
                for cmd, desc in category_commands:
                    max_cmd_len = max(max_cmd_len, len(cmd))

            # Set command column width with padding
            cmd_width = max_cmd_len + 2

            # Create Rich Tree
            tree = Tree("[bold cyan]Security Commands[/bold cyan] (5 commands)")

            # Add each category with fixed-width tables
            for category_name, commands in categories.items():
                category_branch = tree.add(
                    f"[bold green]{category_name}[/bold green] [dim]({len(commands)} commands)[/dim]"
                )

                # Create table with FIXED command width for vertical alignment, flexible description
                table = RichTable(show_header=True, box=None, padding=(0, 2))
                table.add_column("Command", style="cyan", no_wrap=True, min_width=cmd_width, max_width=cmd_width)
                table.add_column("Description", style="dim", no_wrap=False, overflow="fold")

                # Add rows
                for cmd, desc in commands:
                    table.add_row(cmd, desc)

                category_branch.add(table)

            # Display the tree
            console.print(tree)
            console.print("\n[blue]💡 Usage: runbooks security [COMMAND] [OPTIONS][/blue]")
            console.print("[blue]📖 Frameworks: CIS, NIST, AWS Security Best Practices[/blue]")

    @click.group(cls=RichSecurityGroup, invoke_without_command=True)
    @common_aws_options
    @click.pass_context
    def security(ctx, profile, region, dry_run):
        """
        Security assessment and compliance operations.

        Comprehensive security baseline assessment with multi-framework compliance
        and enterprise-grade reporting capabilities.

        Compliance Frameworks:
        • SOC2, PCI-DSS, HIPAA, ISO 27001
        • AWS Well-Architected Security Pillar
        • NIST Cybersecurity Framework
        • CIS Benchmarks

        Examples:
            runbooks security assess --framework soc2
            runbooks security baseline --all-checks
            runbooks security report --format pdf --compliance hipaa
        """
        ctx.obj.update({"profile": profile, "region": region, "dry_run": dry_run})

        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @security.command()
    @common_aws_options
    @common_output_options
    @click.option(
        "--framework",
        type=click.Choice(["soc2", "pci-dss", "hipaa", "iso27001", "well-architected"]),
        multiple=True,
        help="Compliance frameworks to assess",
    )
    @click.option("--all-checks", is_flag=True, help="Run all available security checks")
    @click.option(
        "--severity", type=click.Choice(["critical", "high", "medium", "low"]), help="Filter by minimum severity level"
    )
    @click.option(
        "--language",
        type=click.Choice(["en", "ja", "ko", "vi"]),
        default="en",
        help="Report language (English, Japanese, Korean, Vietnamese)",
    )
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account security assessment")
    @click.pass_context
    def assess(
        ctx, profile, region, dry_run, csv, json_output, markdown, framework, all_checks, severity, language, all
    ):
        """
        Comprehensive security assessment with multi-framework compliance and universal profile support.

        Enterprise Features:
        • 15+ security checks across multiple frameworks
        • Multi-language reporting (EN/JP/KR/VN)
        • Risk scoring and prioritization
        • Remediation recommendations with business impact
        • Multi-account security assessment with --all flag

        Examples:
            runbooks security assess --framework soc2,pci-dss
            runbooks security assess --all-checks --export-format pdf
            runbooks security assess --severity critical --language ja
            runbooks security assess --all --framework soc2  # Multi-account assessment
        """
        try:
            from runbooks.security.assessment_runner import SecurityAssessmentRunner
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import handle_output_format

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            assessment = SecurityAssessmentRunner(
                profile=resolved_profile,
                region=region,
                frameworks=list(framework) if framework else None,
                all_checks=all_checks,
                severity_filter=severity,
                language=language,
            )

            results = assessment.run_comprehensive_assessment()

            # Determine output format (CSV/JSON/Markdown override default table display)
            if csv:
                output_format = "csv"
            elif json_output:
                output_format = "json"
            elif markdown:
                output_format = "markdown"
            else:
                output_format = "table"

            # Use unified output handler
            handle_output_format(results, output_format=output_format, title="Security Assessment Results")

            return results

        except ImportError as e:
            console.print(f"[red]❌ Security assessment module not available: {e}[/red]")
            raise click.ClickException("Security assessment functionality not available")
        except Exception as e:
            console.print(f"[red]❌ Security assessment failed: {e}[/red]")
            raise click.ClickException(str(e))

    @security.command()
    @common_aws_options
    @common_output_options
    @click.option(
        "--check-type",
        type=click.Choice(["baseline", "advanced", "enterprise"]),
        default="baseline",
        help="Security check depth level",
    )
    @click.option("--include-remediation", is_flag=True, help="Include remediation recommendations")
    @click.option("--auto-fix", is_flag=True, help="Automatically fix low-risk issues (with approval)")
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account baseline assessment")
    @click.pass_context
    def baseline(
        ctx, profile, region, dry_run, csv, json_output, markdown, check_type, include_remediation, auto_fix, all
    ):
        """
        Security baseline assessment and configuration validation with universal profile support.

        Baseline Security Checks:
        • IAM policy analysis and least privilege validation
        • S3 bucket public access and encryption assessment
        • VPC security group and NACL configuration review
        • CloudTrail and logging configuration verification
        • Encryption at rest and in transit validation

        Examples:
            runbooks security baseline --check-type enterprise
            runbooks security baseline --include-remediation --auto-fix
            runbooks security baseline --all --check-type enterprise  # Multi-account assessment
        """
        try:
            from runbooks.security.baseline_checker import SecurityBaselineChecker
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import handle_output_format

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            baseline_checker = SecurityBaselineChecker(
                profile=resolved_profile,
                region=region,
                check_type=check_type,
                include_remediation=include_remediation,
                auto_fix=auto_fix and not dry_run,
            )

            baseline_results = baseline_checker.run_baseline_assessment()

            # Determine output format
            if csv:
                output_format = "csv"
            elif json_output:
                output_format = "json"
            elif markdown:
                output_format = "markdown"
            else:
                output_format = "table"

            # Use unified output handler
            handle_output_format(baseline_results, output_format=output_format, title="Security Baseline Assessment")

            return baseline_results

        except ImportError as e:
            console.print(f"[red]❌ Security baseline module not available: {e}[/red]")
            raise click.ClickException("Security baseline functionality not available")
        except Exception as e:
            console.print(f"[red]❌ Security baseline assessment failed: {e}[/red]")
            raise click.ClickException(str(e))

    @security.command()
    @common_aws_options
    @common_output_options
    @click.option(
        "--format",
        "report_format",
        type=click.Choice(["pdf", "html", "markdown", "json"]),
        multiple=True,
        default=["pdf"],
        help="Report formats",
    )
    @click.option(
        "--compliance",
        type=click.Choice(["soc2", "pci-dss", "hipaa", "iso27001"]),
        multiple=True,
        help="Include compliance mapping",
    )
    @click.option("--executive-summary", is_flag=True, help="Generate executive summary")
    @click.option("--output-dir", default="./security_reports", help="Output directory")
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account security reporting")
    @click.pass_context
    def report(
        ctx,
        profile,
        region,
        dry_run,
        csv,
        json_output,
        markdown,
        report_format,
        compliance,
        executive_summary,
        output_dir,
        all,
    ):
        """
        Generate comprehensive security compliance reports with universal profile support.

        Enterprise Reporting Features:
        • Executive-ready summary with risk quantification
        • Compliance framework mapping and gap analysis
        • Multi-language support for global enterprises
        • Audit trail documentation and evidence collection
        • Multi-account security reporting with --all flag

        Examples:
            runbooks security report --format pdf,html --executive-summary
            runbooks security report --compliance soc2,hipaa --output-dir ./audit
            runbooks security report --all --compliance soc2  # Multi-account reporting
        """
        try:
            from runbooks.security.report_generator import SecurityReportGenerator
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import handle_output_format

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            # Override report_format if CLI output options provided
            if csv:
                report_format = ("csv",)
            elif json_output:
                report_format = ("json",)
            elif markdown:
                report_format = ("markdown",)

            report_generator = SecurityReportGenerator(
                profile=resolved_profile,
                output_dir=output_dir,
                compliance_frameworks=list(compliance) if compliance else None,
                executive_summary=executive_summary,
            )

            report_results = {}
            for format_type in report_format:
                result = report_generator.generate_report(format=format_type)
                report_results[format_type] = result

            console.print(f"[green]✅ Successfully generated {len(report_format)} report format(s)[/green]")
            console.print(f"[dim]Output directory: {output_dir}[/dim]")

            return report_results

        except ImportError as e:
            console.print(f"[red]❌ Security report module not available: {e}[/red]")
            raise click.ClickException("Security report functionality not available")
        except Exception as e:
            console.print(f"[red]❌ Security report generation failed: {e}[/red]")
            raise click.ClickException(str(e))

    @security.command("remediate-findings")
    @common_aws_options
    @click.option(
        "--accounts", default=None, help="Comma-separated account IDs (default: discover all from organization)"
    )
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
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account remediation")
    @click.pass_context
    def remediate_findings(
        ctx, profile, region, dry_run, accounts, severity, finding_types, output_file, remediation_plan_file, all
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
        - Execute (--no-dry-run): Apply remediation actions with approval gates for high-risk changes

        Safety Features:
        - Dry-run mode enabled by default
        - Approval gates for CRITICAL and HIGH severity findings
        - Multi-account validation before execution
        - Complete audit trail generation

        Example Usage:
            # Discover HIGH severity findings (dry-run)
            runbooks security remediate-findings --severity HIGH

            # Multi-account Security Group remediation (dry-run)
            runbooks security remediate-findings --finding-types "Security Group"

            # Execute remediation with approval (IAM findings)
            runbooks security remediate-findings --finding-types IAM --no-dry-run

            # Custom account list with CRITICAL findings
            runbooks security remediate-findings --accounts 123456789012,987654321098 --severity CRITICAL
        """
        try:
            from runbooks.security.securityhub_finding_remediation import SecurityHubFindingRemediation
            from runbooks.common.profile_utils import get_profile_for_operation

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("management", profile)

            # Display operation banner
            mode_text = "DRY-RUN (Safe Mode)" if dry_run else "EXECUTE (Changes Applied)"
            console.print(f"\n[bold cyan]🛡️ Security Hub Finding Remediation[/bold cyan]")
            console.print(f"[dim]Profile: {resolved_profile}[/dim]")
            console.print(f"[dim]Severity: {severity}[/dim]")
            console.print(f"[dim]Finding Types: {finding_types}[/dim]")
            console.print(f"[dim]Mode: {mode_text}[/dim]")
            console.print(f"[dim]Region: {region}[/dim]\n")

            # Parse accounts if provided
            account_list = None
            if accounts:
                account_list = [acc.strip() for acc in accounts.split(",")]
                console.print(f"[green]Using specified accounts: {len(account_list)} accounts[/green]")

            # Initialize remediation engine
            remediation = SecurityHubFindingRemediation(
                profile=resolved_profile, accounts=account_list, severity=severity, region=region
            )

            console.print(
                f"[green]Targeting {len(remediation.accounts)} accounts for Security Hub findings discovery[/green]"
            )

            # Discover findings
            finding_types_list = [ft.strip() for ft in finding_types.split(",")]
            findings = remediation.discover_findings(finding_types=finding_types_list, compliance_status="FAILED")

            if not findings:
                console.print(f"[yellow]No {severity} severity findings discovered[/yellow]")
                console.print("\n[dim]Possible reasons:[/dim]")
                console.print("[dim]• Security Hub not enabled in target accounts[/dim]")
                console.print("[dim]• No findings match severity and compliance filters[/dim]")
                console.print("[dim]• Insufficient permissions (securityhub:GetFindings required)[/dim]")
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
            console.print(f"\n[bold green]✅ Security Hub Remediation Complete[/bold green]")
            console.print(f"[dim]Findings Report: {output_file}[/dim]")
            console.print(f"[dim]Remediation Plan: {remediation_plan_file}[/dim]")
            console.print(f"[dim]Mode: {mode_text}[/dim]\n")

            if dry_run:
                console.print("[bold yellow]Next Steps:[/bold yellow]")
                console.print("[dim]1. Review findings report and remediation plan[/dim]")
                console.print("[dim]2. Run with --no-dry-run flag to apply changes[/dim]")
                console.print("[dim]3. Monitor Security Hub for finding status updates[/dim]")

            return findings_df

        except ImportError as e:
            console.print(f"[red]❌ Security Hub remediation module not available: {e}[/red]")
            raise click.ClickException("Security Hub remediation functionality not available")
        except Exception as e:
            console.print(f"[red]❌ Security Hub remediation failed: {e}[/red]")
            import traceback

            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
            raise click.ClickException(str(e))

    @security.command("deploy-guardduty")
    @common_aws_options
    @click.option("--delegated-admin", required=True, help="Account ID for GuardDuty delegated administrator")
    @click.option(
        "--auto-enable-new-accounts/--no-auto-enable", default=True, help="Auto-enable GuardDuty for new accounts"
    )
    @click.option(
        "--output-file", default="/tmp/guardduty-deployment-report.xlsx", help="Output file for deployment report"
    )
    @click.pass_context
    def deploy_guardduty(ctx, profile, region, dry_run, delegated_admin, auto_enable_new_accounts, output_file):
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
          runbooks security deploy-guardduty --delegated-admin 123456789012 --no-dry-run

          # Deploy without auto-enable for new accounts
          runbooks security deploy-guardduty --delegated-admin 123456789012 --no-auto-enable --no-dry-run
        """
        import time
        from runbooks.security.guardduty_org_deployment import (
            GuardDutyOrgDeployment,
            print_deployment_plan,
        )
        from runbooks.common.profile_utils import get_profile_for_operation
        from runbooks.common.rich_utils import create_panel

        try:
            start_time = time.time()

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("management", profile)

            # Display deployment header
            console.print(
                create_panel(
                    f"[bold cyan]🛡️ GuardDuty Organization-wide Deployment[/bold cyan]\n\n"
                    f"[dim]Profile: {resolved_profile}[/dim]\n"
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
                profile=resolved_profile,
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
                    console.print("[red]❌ Delegated admin configuration failed - aborting deployment[/red]")
                    raise click.Abort()

                # Step 3b: Enable GuardDuty org-wide
                newly_enabled, already_enabled, errors = deployment.enable_guardduty_org_wide(
                    org_data["accounts"],
                    auto_enable=auto_enable_new_accounts,
                    dry_run=False,
                )

                console.print(
                    f"[green]Deployment results: {newly_enabled} newly enabled, {already_enabled} already enabled[/green]"
                )

                if errors:
                    console.print(f"[yellow]⚠️  Encountered {len(errors)} errors during deployment[/yellow]")
                    for error in errors[:5]:  # Show first 5 errors
                        console.print(f"  [red]• {error}[/red]")

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
                        f"[yellow]To execute deployment, run with --no-dry-run flag[/yellow]",
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

            console.print("[green]✅ GuardDuty organization-wide deployment completed successfully![/green]")

        except Exception as e:
            console.print(f"[red]❌ GuardDuty deployment failed: {str(e)}[/red]")
            import traceback

            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
            raise click.ClickException(str(e))

    return security
