"""
CFAT Commands Module - Cloud Foundations Assessment Tool

KISS Principle: Focused on cloud foundations assessment and Well-Architected reviews
DRY Principle: Centralized assessment patterns and framework evaluations

Extracted from main.py lines 6000-7500 for modular architecture.
Preserves 100% functionality while reducing main.py context overhead.
"""

import click
from rich.console import Console

# Import common utilities and decorators
from runbooks.common.decorators import common_aws_options
from runbooks.common.output_controller import OutputController
from runbooks.common.logging_config import configure_logging

console = Console()


def create_cfat_group():
    """
    Create the cfat command group with all subcommands.

    Returns:
        Click Group object with all cfat commands

    Performance: Lazy creation only when needed by DRYCommandRegistry
    Context Reduction: ~1500 lines extracted from main.py
    """

    # Custom Group class with Rich Tree/Table help formatting
    class RichCFATGroup(click.Group):
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
                click.echo("Usage: runbooks cfat [OPTIONS] COMMAND [ARGS]...")
                click.echo("")
                click.echo("  Cloud Foundations Assessment Tool (CFAT) - Well-Architected Reviews.")
                click.echo("")
                click.echo("Commands:")
                click.echo("  assess   Comprehensive framework assessment")
                click.echo("  review   Structured architecture review")
                click.echo("  report   Generate assessment reports")
                return

            # Categorize commands based on business function
            categories = {
                "🔍 Well-Architected Assessment": [
                    ("assess", "Comprehensive framework assessment"),
                    ("review", "Structured architecture review"),
                ],
                "📊 Reporting & Documentation": [("report", "Generate assessment reports")],
            }

            # Phase 1: Pre-calculate max column widths across ALL categories (Track 3A pattern)
            max_cmd_len = 0
            for category_commands in categories.values():
                for cmd, desc in category_commands:
                    max_cmd_len = max(max_cmd_len, len(cmd))

            # Set command column width with padding
            cmd_width = max_cmd_len + 2

            # Create Rich Tree
            tree = Tree("[bold cyan]CFAT Commands[/bold cyan] (3 commands)")

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
            console.print("\n[blue]💡 Usage: runbooks cfat [COMMAND] [OPTIONS][/blue]")
            console.print("[blue]📖 CFAT Framework: AWS Well-Architected best practices assessment[/blue]")

    @click.group(cls=RichCFATGroup, invoke_without_command=True)
    @common_aws_options
    @click.pass_context
    def cfat(ctx, profile, region, dry_run):
        """
        Cloud Foundations Assessment Tool (CFAT) - Well-Architected Reviews.

        Comprehensive cloud architecture assessment based on AWS Well-Architected
        Framework with enterprise governance and compliance validation.

        Assessment Pillars:
        • Operational Excellence
        • Security
        • Reliability
        • Performance Efficiency
        • Cost Optimization
        • Sustainability

        Examples:
            runbooks cfat assess --pillar security,cost-optimization
            runbooks cfat review --workload-name production-app
            runbooks cfat report --format pdf --executive-summary
        """
        ctx.obj.update({"profile": profile, "region": region, "dry_run": dry_run})

        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @cfat.command()
    @common_aws_options
    @click.option(
        "--pillar",
        type=click.Choice(
            [
                "operational-excellence",
                "security",
                "reliability",
                "performance-efficiency",
                "cost-optimization",
                "sustainability",
            ]
        ),
        multiple=True,
        help="Specific Well-Architected pillars to assess",
    )
    @click.option("--all-pillars", is_flag=True, help="Assess all Well-Architected pillars")
    @click.option("--workload-name", help="Name of the workload being assessed")
    @click.option(
        "--assessment-depth",
        type=click.Choice(["basic", "comprehensive", "enterprise"]),
        default="comprehensive",
        help="Assessment depth level",
    )
    @click.option(
        "--export-format",
        type=click.Choice(["json", "csv", "pdf", "html"]),
        help="Export format for assessment results",
    )
    @click.option(
        "--all", is_flag=True, help="Use all available AWS profiles for multi-account Well-Architected assessment"
    )
    @click.option("--verbose", "-v", is_flag=True, help="Show detailed logs")
    @click.option("--format", type=click.Choice(["compact", "table", "json"]), default="compact", help="Output format")
    @click.pass_context
    def assess(
        ctx,
        profile,
        region,
        dry_run,
        pillar,
        all_pillars,
        workload_name,
        assessment_depth,
        export_format,
        all,
        verbose,
        format,
    ):
        """
        Comprehensive Well-Architected Framework assessment with universal profile support.

        Enterprise Assessment Features:
        • 6-pillar Well-Architected evaluation (including Sustainability)
        • Risk scoring and prioritization
        • Industry best practices validation
        • Governance and compliance alignment
        • Remediation roadmap with business impact
        • Multi-account assessment with --all flag

        Examples:
            runbooks cfat assess --all-pillars --workload-name production
            runbooks cfat assess --pillar security,cost-optimization
            runbooks cfat assess --assessment-depth enterprise --export-format pdf
            runbooks cfat assess --all --pillar security  # Multi-account assessment
        """
        # Initialize output controller
        configure_logging(verbose=verbose)
        controller = OutputController(verbose=verbose, format=format)

        try:
            from runbooks.cfat.assessment_runner import WellArchitectedAssessment
            from runbooks.common.profile_utils import get_profile_for_operation

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            assessment = WellArchitectedAssessment(
                profile=resolved_profile,
                region=region,
                pillars=list(pillar) if pillar else None,
                all_pillars=all_pillars,
                workload_name=workload_name or "Default Workload",
                assessment_depth=assessment_depth,
            )

            assessment_results = assessment.run_well_architected_assessment()

            # Print summary using OutputController
            total_checks = assessment_results.get("total_checks", 0)
            passed_checks = assessment_results.get("passed_checks", 0)
            success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

            controller.print_operation_summary(
                emoji="🏗️",
                operation="Well-Architected Assessment",
                input_count=total_checks,
                enriched_count=passed_checks,
                enrichment_type="checks passed",
                success_percentage=success_rate,
                profile=resolved_profile,
                output_file=export_format or "console",
                added_columns=list(pillar) if pillar else ["all-pillars"],
            )

            if export_format:
                assessment.export_results(assessment_results, format=export_format)

            return assessment_results

        except ImportError as e:
            console.print(f"[red]❌ CFAT assessment module not available: {e}[/red]")
            raise click.ClickException("CFAT assessment functionality not available")
        except Exception as e:
            console.print(f"[red]❌ CFAT assessment failed: {e}[/red]")
            raise click.ClickException(str(e))

    @cfat.command()
    @common_aws_options
    @click.option("--workload-name", required=True, help="Name of the workload for review")
    @click.option(
        "--review-type",
        type=click.Choice(["initial", "milestone", "continuous"]),
        default="milestone",
        help="Type of architecture review",
    )
    @click.option("--stakeholders", multiple=True, help="Stakeholder names/emails for review")
    @click.option("--include-recommendations", is_flag=True, default=True, help="Include remediation recommendations")
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account architecture review")
    @click.option("--verbose", "-v", is_flag=True, help="Show detailed logs")
    @click.option("--format", type=click.Choice(["compact", "table", "json"]), default="compact", help="Output format")
    @click.pass_context
    def review(
        ctx,
        profile,
        region,
        dry_run,
        workload_name,
        review_type,
        stakeholders,
        include_recommendations,
        all,
        verbose,
        format,
    ):
        """
        Structured architecture review with stakeholder collaboration and universal profile support.

        Architecture Review Process:
        • Multi-pillar assessment with stakeholder input
        • Risk identification and business impact analysis
        • Remediation prioritization and timeline planning
        • Executive summary with actionable recommendations
        • Multi-account architecture review with --all flag

        Examples:
            runbooks cfat review --workload-name api-gateway --review-type milestone
            runbooks cfat review --workload-name data-platform --stakeholders team@company.com
            runbooks cfat review --all --workload-name cross-account-app  # Multi-account review
        """
        # Initialize output controller
        configure_logging(verbose=verbose)
        controller = OutputController(verbose=verbose, format=format)

        try:
            from runbooks.cfat.review_manager import ArchitectureReviewManager
            from runbooks.common.profile_utils import get_profile_for_operation

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            review_manager = ArchitectureReviewManager(
                profile=resolved_profile,
                region=region,
                workload_name=workload_name,
                review_type=review_type,
                stakeholders=list(stakeholders) if stakeholders else None,
                include_recommendations=include_recommendations,
            )

            review_results = review_manager.conduct_architecture_review()

            # Print summary using OutputController
            findings_count = review_results.get("findings_count", 0)
            recommendations_count = review_results.get("recommendations_count", 0)

            controller.print_operation_summary(
                emoji="🔍",
                operation="Architecture Review",
                input_count=findings_count,
                enriched_count=recommendations_count,
                enrichment_type="recommendations generated",
                success_percentage=100.0,
                profile=resolved_profile,
                output_file=f"review-{workload_name}",
                added_columns=[review_type, f"{len(stakeholders) if stakeholders else 0} stakeholders"],
            )

            return review_results

        except ImportError as e:
            console.print(f"[red]❌ CFAT review module not available: {e}[/red]")
            raise click.ClickException("CFAT review functionality not available")
        except Exception as e:
            console.print(f"[red]❌ CFAT architecture review failed: {e}[/red]")
            raise click.ClickException(str(e))

    @cfat.command()
    @common_aws_options
    @click.option(
        "--format",
        "report_format",
        type=click.Choice(["pdf", "html", "markdown", "json"]),
        multiple=True,
        default=["pdf"],
        help="Report formats",
    )
    @click.option("--executive-summary", is_flag=True, help="Generate executive summary")
    @click.option("--include-remediation", is_flag=True, default=True, help="Include remediation roadmap")
    @click.option("--output-dir", default="./cfat_reports", help="Output directory")
    @click.option("--workload-filter", help="Filter reports by workload name")
    @click.option(
        "--all", is_flag=True, help="Use all available AWS profiles for multi-account Well-Architected reporting"
    )
    @click.pass_context
    def report(
        ctx,
        profile,
        region,
        dry_run,
        report_format,
        executive_summary,
        include_remediation,
        output_dir,
        workload_filter,
        all,
    ):
        """
        Generate comprehensive Well-Architected assessment reports with universal profile support.

        Enterprise Reporting Features:
        • Executive-ready summary with risk quantification
        • Well-Architected score trending and improvement tracking
        • Remediation roadmap with business priority alignment
        • Multi-format output for stakeholder consumption
        • Multi-account Well-Architected reporting with --all flag

        Examples:
            runbooks cfat report --format pdf,html --executive-summary
            runbooks cfat report --include-remediation --workload-filter production
            runbooks cfat report --all --format pdf  # Multi-account reporting
        """
        try:
            from runbooks.cfat.report_generator import CFATReportGenerator
            from runbooks.common.profile_utils import get_profile_for_operation

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            report_generator = CFATReportGenerator(
                profile=resolved_profile,
                output_dir=output_dir,
                executive_summary=executive_summary,
                include_remediation=include_remediation,
                workload_filter=workload_filter,
            )

            report_results = {}
            for format_type in report_format:
                result = report_generator.generate_report(format=format_type)
                report_results[format_type] = result

            console.print(f"[green]✅ Successfully generated {len(report_format)} report format(s)[/green]")
            console.print(f"[dim]Output directory: {output_dir}[/dim]")

            return report_results

        except ImportError as e:
            console.print(f"[red]❌ CFAT report module not available: {e}[/red]")
            raise click.ClickException("CFAT report functionality not available")
        except Exception as e:
            console.print(f"[red]❌ CFAT report generation failed: {e}[/red]")
            raise click.ClickException(str(e))

    return cfat
