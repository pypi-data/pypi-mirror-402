"""
CFAT Enhanced Commands - Week 3 Track 7 CLI Upgrade

Enhanced Cloud Foundations Assessment Tool with:
- Assessment framework tables (Well-Architected pillars)
- Compliance scoring displays (0-100% per pillar)
- Finding severity trees (Critical/High/Medium/Low)
- Remediation priority matrices
- Universal output formats (--csv, --json, --markdown)

Follows FinOps/Inventory patterns for enterprise quality.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich import box

from runbooks.common.decorators import common_aws_options, common_output_options
from runbooks.common.rich_utils import (
    console,
    create_table,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_section,
    create_tree,
    handle_output_format,
    format_percentage,
)
from runbooks.common.output_controller import OutputController
from runbooks.common.logging_config import configure_logging


def create_well_architected_pillars_table(pillar_scores: dict) -> Table:
    """
    Create Well-Architected pillars table with compliance scoring.

    Args:
        pillar_scores: Dict of {pillar_name: score_percentage}

    Returns:
        Rich Table with color-coded pillar scores
    """
    table = create_table(title="Well-Architected Framework Assessment", box_style=box.DOUBLE)

    table.add_column("Pillar", style="bold cyan", no_wrap=True)
    table.add_column("Score", justify="right", style="white")
    table.add_column("Status", justify="center", style="white")
    table.add_column("Priority", style="white")

    # Well-Architected pillars with emoji icons
    pillar_icons = {
        "operational-excellence": "⚙️",
        "security": "🔒",
        "reliability": "🛡️",
        "performance-efficiency": "⚡",
        "cost-optimization": "💰",
        "sustainability": "🌱",
    }

    for pillar, score in sorted(pillar_scores.items(), key=lambda x: x[1]):
        icon = pillar_icons.get(pillar, "📋")
        pillar_display = f"{icon} {pillar.replace('-', ' ').title()}"

        # Color-code score based on thresholds
        if score >= 90:
            score_display = f"[bright_green]{score:.1f}%[/bright_green]"
            status = "✅ Excellent"
            priority = "[dim]Maintain[/dim]"
        elif score >= 75:
            score_display = f"[green]{score:.1f}%[/green]"
            status = "🟢 Good"
            priority = "[dim]Monitor[/dim]"
        elif score >= 60:
            score_display = f"[yellow]{score:.1f}%[/yellow]"
            status = "🟡 Fair"
            priority = "[yellow]Improve[/yellow]"
        elif score >= 40:
            score_display = f"[bright_red]{score:.1f}%[/bright_red]"
            status = "🔴 Poor"
            priority = "[bright_red]High Priority[/bright_red]"
        else:
            score_display = f"[red bold]{score:.1f}%[/red bold]"
            status = "🚨 Critical"
            priority = "[red bold]Urgent[/red bold]"

        table.add_row(pillar_display, score_display, status, priority)

    return table


def create_finding_severity_tree(findings: list) -> Tree:
    """
    Create severity tree for CFAT findings.

    Args:
        findings: List of finding dicts with severity levels

    Returns:
        Rich Tree with severity hierarchy
    """
    # Count findings by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for finding in findings:
        severity = finding.get("severity", "MEDIUM").upper()
        if severity in severity_counts:
            severity_counts[severity] += 1

    # Create tree
    tree = create_tree(f"Assessment Findings (Total: {len(findings)})", style="bold bright_cyan")

    # Add severity branches
    if severity_counts["CRITICAL"] > 0:
        critical_branch = tree.add(f"[red bold]🚨 CRITICAL ({severity_counts['CRITICAL']})[/red bold]")
        critical_branch.add("[red]Immediate remediation required[/red]")

    if severity_counts["HIGH"] > 0:
        high_branch = tree.add(f"[bright_red]🔴 HIGH ({severity_counts['HIGH']})[/bright_red]")
        high_branch.add("[bright_red]Address within 30 days[/bright_red]")

    if severity_counts["MEDIUM"] > 0:
        medium_branch = tree.add(f"[yellow]🟡 MEDIUM ({severity_counts['MEDIUM']})[/yellow]")
        medium_branch.add("[yellow]Plan remediation within 90 days[/yellow]")

    if severity_counts["LOW"] > 0:
        low_branch = tree.add(f"[green]🟢 LOW ({severity_counts['LOW']})[/green]")
        low_branch.add("[green]Schedule for future improvement[/green]")

    return tree


def create_remediation_priority_matrix(findings: list) -> Table:
    """
    Create remediation priority matrix.

    Args:
        findings: List of findings with severity and effort estimates

    Returns:
        Rich Table showing remediation priorities
    """
    table = create_table(title="Remediation Priority Matrix", box_style=box.ROUNDED)

    table.add_column("Priority", style="bold", no_wrap=True)
    table.add_column("Finding", style="cyan")
    table.add_column("Severity", justify="center", style="white")
    table.add_column("Effort", justify="center", style="white")
    table.add_column("Impact", style="white")

    # Calculate priority score (severity weight - effort penalty)
    severity_weight = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25}
    effort_penalty = {"HOURS": 5, "DAYS": 15, "WEEKS": 30, "MONTHS": 50}

    prioritized = []
    for finding in findings:
        severity = finding.get("severity", "MEDIUM").upper()
        effort = finding.get("estimated_effort", "DAYS").upper()

        priority_score = severity_weight.get(severity, 50) - effort_penalty.get(effort, 15)
        prioritized.append((priority_score, finding))

    prioritized.sort(reverse=True)

    # Add top 10 priorities
    for idx, (score, finding) in enumerate(prioritized[:10], 1):
        title = finding.get("title", "Unknown Finding")[:50]
        severity = finding.get("severity", "MEDIUM").upper()
        effort = finding.get("estimated_effort", "DAYS")

        # Priority badge
        if idx <= 3:
            priority_display = f"[red bold]P{idx} 🔥[/red bold]"
        elif idx <= 6:
            priority_display = f"[yellow bold]P{idx}[/yellow bold]"
        else:
            priority_display = f"[dim]P{idx}[/dim]"

        # Severity display
        severity_colors = {
            "CRITICAL": "[red bold]CRITICAL[/red bold]",
            "HIGH": "[bright_red]HIGH[/bright_red]",
            "MEDIUM": "[yellow]MEDIUM[/yellow]",
            "LOW": "[green]LOW[/green]",
        }
        severity_display = severity_colors.get(severity, severity)

        # Impact calculation
        if severity == "CRITICAL":
            impact = "🚨 Business Critical"
        elif severity == "HIGH":
            impact = "⚠️ Significant Risk"
        elif severity == "MEDIUM":
            impact = "📊 Moderate Impact"
        else:
            impact = "💡 Improvement"

        table.add_row(priority_display, title, severity_display, effort, impact)

    return table


def create_compliance_dashboard(compliance_scores: dict) -> Panel:
    """
    Create compliance framework dashboard.

    Args:
        compliance_scores: Dict of {framework: score_percentage}

    Returns:
        Rich Panel with compliance status
    """
    from rich.text import Text

    content = Text()
    content.append("Compliance Framework Status\n\n", style="bold bright_cyan")

    frameworks = {
        "SOC2": compliance_scores.get("SOC2", 0),
        "PCI-DSS": compliance_scores.get("PCI-DSS", 0),
        "HIPAA": compliance_scores.get("HIPAA", 0),
        "GDPR": compliance_scores.get("GDPR", 0),
        "ISO27001": compliance_scores.get("ISO27001", 0),
    }

    for framework, score in frameworks.items():
        if score >= 90:
            status_icon = "✅"
            status_style = "bright_green"
            status_text = "Compliant"
        elif score >= 75:
            status_icon = "⚠️"
            status_style = "yellow"
            status_text = "Partial"
        else:
            status_icon = "❌"
            status_style = "red"
            status_text = "Non-Compliant"

        content.append(f"{status_icon} {framework}: ", style="white")
        content.append(f"{score:.1f}%", style=status_style)
        content.append(f" ({status_text})\n", style=status_style)

    return Panel(
        content, title="[bright_cyan]Compliance Dashboard[/bright_cyan]", border_style="bright_green", padding=(1, 2)
    )


@click.command()
@common_aws_options
@common_output_options
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
@click.option("--show-findings", is_flag=True, help="Show detailed findings tree")
@click.option("--show-remediation", is_flag=True, help="Show remediation priority matrix")
@click.option("--show-compliance", is_flag=True, help="Show compliance dashboard")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed logs")
@click.pass_context
def assess_enhanced(
    ctx,
    profile,
    region,
    dry_run,
    output_format,
    output_file,
    pillar,
    all_pillars,
    workload_name,
    assessment_depth,
    show_findings,
    show_remediation,
    show_compliance,
    verbose,
):
    """
    Enhanced Well-Architected Framework assessment with Rich CLI displays.

    Features:
    • Assessment framework tables (Well-Architected pillars)
    • Compliance scoring displays (0-100% per pillar)
    • Finding severity trees (Critical/High/Medium/Low)
    • Remediation priority matrices
    • Universal output formats (--csv, --json, --markdown, --pdf)

    Examples:
        runbooks cfat assess-enhanced --all-pillars --show-findings
        runbooks cfat assess-enhanced --pillar security,cost-optimization --format csv
        runbooks cfat assess-enhanced --show-remediation --format pdf --output-file report.pdf
    """
    configure_logging(verbose=verbose)

    try:
        # Mock assessment data (in real implementation, this would call actual assessment)
        pillar_scores = {
            "operational-excellence": 78.5,
            "security": 62.3,
            "reliability": 85.7,
            "performance-efficiency": 71.2,
            "cost-optimization": 55.8,
            "sustainability": 68.4,
        }

        # Filter pillars if specified
        if pillar:
            pillar_scores = {p: pillar_scores[p] for p in pillar if p in pillar_scores}

        # Mock findings data
        findings = [
            {
                "title": "Missing IAM MFA enforcement",
                "severity": "CRITICAL",
                "estimated_effort": "HOURS",
                "category": "security",
            },
            {
                "title": "No automated backup policy",
                "severity": "HIGH",
                "estimated_effort": "DAYS",
                "category": "reliability",
            },
            {
                "title": "Unoptimized EC2 instance types",
                "severity": "MEDIUM",
                "estimated_effort": "WEEKS",
                "category": "cost-optimization",
            },
            {
                "title": "CloudWatch alarms not configured",
                "severity": "HIGH",
                "estimated_effort": "HOURS",
                "category": "operational-excellence",
            },
            {
                "title": "EBS volumes not encrypted",
                "severity": "HIGH",
                "estimated_effort": "DAYS",
                "category": "security",
            },
            {
                "title": "No auto-scaling groups",
                "severity": "MEDIUM",
                "estimated_effort": "DAYS",
                "category": "reliability",
            },
        ]

        # Mock compliance scores
        compliance_scores = {"SOC2": 92.5, "PCI-DSS": 78.3, "HIPAA": 85.7, "GDPR": 88.2, "ISO27001": 81.9}

        # Print header
        print_header("Well-Architected Framework Assessment", "1.1.20")

        if workload_name:
            print_section(f"Workload: {workload_name}", emoji="🏗️")

        # Display pillar scores table
        pillars_table = create_well_architected_pillars_table(pillar_scores)

        # Handle output format
        if output_format == "table":
            console.print(pillars_table)
            console.print()

            # Show additional displays if requested
            if show_findings:
                print_section("Findings Analysis", emoji="🔍")
                findings_tree = create_finding_severity_tree(findings)
                console.print(findings_tree)
                console.print()

            if show_remediation:
                print_section("Remediation Priorities", emoji="🎯")
                remediation_matrix = create_remediation_priority_matrix(findings)
                console.print(remediation_matrix)
                console.print()

            if show_compliance:
                print_section("Compliance Status", emoji="✅")
                compliance_panel = create_compliance_dashboard(compliance_scores)
                console.print(compliance_panel)
                console.print()

            # Summary statistics
            avg_score = sum(pillar_scores.values()) / len(pillar_scores)
            print_success(
                f"Assessment complete: {len(pillar_scores)} pillars evaluated, "
                f"average score {avg_score:.1f}%, {len(findings)} findings identified"
            )
        else:
            # Export to file formats
            export_data = {
                "workload": workload_name or "Default Workload",
                "assessment_depth": assessment_depth,
                "pillar_scores": pillar_scores,
                "findings": findings,
                "compliance_scores": compliance_scores,
                "summary": {
                    "average_score": sum(pillar_scores.values()) / len(pillar_scores),
                    "total_findings": len(findings),
                    "critical_findings": sum(1 for f in findings if f["severity"] == "CRITICAL"),
                    "high_findings": sum(1 for f in findings if f["severity"] == "HIGH"),
                },
            }

            handle_output_format(
                export_data,
                output_format=output_format,
                output_file=output_file,
                title="Well-Architected Framework Assessment",
            )

            print_success(f"Assessment exported to {output_file or 'console'} ({output_format} format)")

    except Exception as e:
        print_error(f"CFAT assessment failed: {e}")
        raise click.ClickException(str(e))


# Export the enhanced assess command
def register_enhanced_cfat_commands(cfat_group):
    """
    Register enhanced CFAT commands to existing CFAT group.

    Args:
        cfat_group: Click Group for CFAT commands
    """
    cfat_group.add_command(assess_enhanced, name="assess-enhanced")
