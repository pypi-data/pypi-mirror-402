# =============================================================================
# MCP Validation CLI
# =============================================================================
# ADLC v3.0.0 - Command-line interface for MCP cross-validation
# =============================================================================

"""CLI interface for MCP cross-validation framework.

Usage:
    runbooks-mcp validate aws --verbose
    runbooks-mcp validate azure
    runbooks-mcp pdca aws --max-cycles 7
    runbooks-mcp list-servers
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core.constants import (
    ACCURACY_TARGET,
    ALL_AWS_SERVERS,
    ALL_AZURE_SERVERS,
    ALL_FINOPS_SERVERS,
    MAX_PDCA_CYCLES,
)
from .core.types import (
    MCPValidationReport,
    ServerValidationResult,
    ValidationStatus,
)
from .evidence import EvidenceGenerator
from .validators import (
    AWSConfigValidator,
    AWSControlTowerValidator,
    AWSCostExplorerValidator,
    AWSIdentityCenterValidator,
    # AWS Validators (P0-P1)
    AWSOrganizationsValidator,
    AWSSecurityHubValidator,
    AzureCostManagementValidator,
    AzureEntraValidator,
    AzurePolicyValidator,
    # Azure Validators (P2)
    AzureResourceManagerValidator,
    AzureSecurityCenterValidator,
    # FinOps Validators (P3)
    FOCUSAggregatorValidator,
    InfracostValidator,
    KubecostValidator,
)

app = typer.Typer(
    name="runbooks-mcp",
    help="MCP Cross-Validation Framework for ADLC compliance (runbooks package)",
    add_completion=False,
)

console = Console()


def get_validator_for_server(server_name: str):
    """Get the appropriate validator class for a server.

    Args:
        server_name: MCP server name

    Returns:
        Validator instance or None if not implemented
    """
    validators = {
        # AWS Validators (P0-P1): 6 total
        "awslabs-organizations": AWSOrganizationsValidator,
        "awslabs-cost-explorer": AWSCostExplorerValidator,
        "awslabs-security-hub": AWSSecurityHubValidator,
        "awslabs-identity-center": AWSIdentityCenterValidator,
        "awslabs-control-tower": AWSControlTowerValidator,
        "awslabs-config": AWSConfigValidator,
        # Azure Validators (P2): 5 total
        "azure-resource-manager": AzureResourceManagerValidator,
        "azure-cost-management": AzureCostManagementValidator,
        "azure-policy": AzurePolicyValidator,
        "azure-security-center": AzureSecurityCenterValidator,
        "azure-entra": AzureEntraValidator,
        # FinOps Validators (P3): 3 total
        "finops-focus-aggregator": FOCUSAggregatorValidator,
        "infracost": InfracostValidator,
        "kubecost": KubecostValidator,
    }
    validator_class = validators.get(server_name)
    if validator_class:
        return validator_class()
    return None


def print_server_result(result: ServerValidationResult) -> None:
    """Print a single server validation result."""
    status_color = {
        ValidationStatus.PASSED: "green",
        ValidationStatus.FAILED: "red",
        ValidationStatus.ERROR: "yellow",
        ValidationStatus.SKIPPED: "dim",
        ValidationStatus.PENDING: "blue",
    }

    color = status_color.get(result.status, "white")
    status_icon = "✓" if result.target_met else "✗"

    console.print(
        f"  [{color}]{status_icon}[/{color}] {result.server_name}: "
        f"[{color}]{result.accuracy:.2f}%[/{color}] "
        f"({result.checks_passed}/{result.checks_total} checks)"
    )


def print_report_summary(report: MCPValidationReport) -> None:
    """Print validation report summary."""
    console.print()

    # Create summary table
    table = Table(title="MCP Validation Summary", show_header=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    status_color = "green" if report.target_met else "red"

    table.add_row("Overall Accuracy", f"[{status_color}]{report.overall_accuracy:.2f}%[/{status_color}]")
    table.add_row("Target Accuracy", f"{ACCURACY_TARGET}%")
    table.add_row("Target Met", f"[{status_color}]{'Yes' if report.target_met else 'No'}[/{status_color}]")
    table.add_row("Servers Passed", f"{report.servers_passed}/{report.servers_total}")
    if report.servers_skipped > 0:
        table.add_row("Servers Skipped", f"[dim]{report.servers_skipped}[/dim]")
    table.add_row("PDCA Cycle", f"{report.pdca_cycle}/{report.max_pdca_cycles}")

    console.print(table)


@app.command()
def validate(
    category: str = typer.Argument(
        "all",
        help="Category to validate: aws, azure, finops, or all",
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        "-s",
        help="Specific server to validate",
    ),
    target: float = typer.Option(
        ACCURACY_TARGET,
        "--target",
        "-t",
        help="Target accuracy percentage",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project name for evidence output (auto-detected if not specified)",
    ),
) -> None:
    """Run MCP cross-validation against native APIs."""
    console.print()
    console.print(
        Panel.fit(
            "[bold blue]MCP Cross-Validation Framework[/bold blue]\n"
            "[dim]ADLC v3.0.0 | Constitutional Checkpoint CHK027[/dim]\n"
            "[dim]via runbooks package (PyPI)[/dim]",
            border_style="blue",
        )
    )
    console.print()

    # Determine servers to validate
    if server:
        servers_to_validate = [server]
    elif category == "aws":
        servers_to_validate = ALL_AWS_SERVERS
    elif category == "azure":
        servers_to_validate = ALL_AZURE_SERVERS
    elif category == "finops":
        servers_to_validate = ALL_FINOPS_SERVERS
    else:
        servers_to_validate = ALL_AWS_SERVERS + ALL_AZURE_SERVERS + ALL_FINOPS_SERVERS

    console.print(f"[cyan]Validating {len(servers_to_validate)} server(s)...[/cyan]")
    console.print()

    # Run validations
    results: list[ServerValidationResult] = []

    for server_name in servers_to_validate:
        validator = get_validator_for_server(server_name)

        if validator is None:
            # Create a skipped result
            result = ServerValidationResult(
                server_name=server_name,
                status=ValidationStatus.SKIPPED,
                accuracy=0.0,
                target_accuracy=target,
                error="Validator not implemented",
            )
            results.append(result)
            console.print(f"  [dim]○[/dim] {server_name}: [dim]skipped (not implemented)[/dim]")
            continue

        try:
            result = validator.validate()
            results.append(result)
            print_server_result(result)

            if verbose and result.validation_results:
                for vr in result.validation_results:
                    status_char = "✓" if vr.status == ValidationStatus.PASSED else "✗"
                    console.print(f"    {status_char} {vr.check_name}: {vr.message}")

        except Exception as e:
            result = ServerValidationResult(
                server_name=server_name,
                status=ValidationStatus.ERROR,
                accuracy=0.0,
                target_accuracy=target,
                error=str(e),
            )
            results.append(result)
            console.print(f"  [red]✗[/red] {server_name}: [red]error - {e}[/red]")

    # Create report
    report = MCPValidationReport(
        server_results=results,
        pdca_cycle=1,
        project=project or Path.cwd().name.lower().replace("_", "-"),
    )

    # Print summary
    print_report_summary(report)

    # Generate evidence
    generator = EvidenceGenerator(project_name=project)
    evidence_path = generator.generate_validation_evidence(report)
    console.print()
    console.print(f"[green]Evidence:[/green] {evidence_path}")

    # Exit with appropriate code
    if report.target_met:
        console.print()
        console.print("[green bold]✓ ALL VALIDATIONS PASSED[/green bold]")
        raise typer.Exit(0)
    else:
        console.print()
        console.print("[red bold]✗ SOME VALIDATIONS FAILED[/red bold]")
        raise typer.Exit(1)


@app.command()
def pdca(
    category: str = typer.Argument(
        "aws",
        help="Category to validate: aws, azure, finops",
    ),
    max_cycles: int = typer.Option(
        MAX_PDCA_CYCLES,
        "--max-cycles",
        "-m",
        help="Maximum PDCA cycles before escalation",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project name for evidence output (auto-detected if not specified)",
    ),
) -> None:
    """Run PDCA cycles until target accuracy is achieved."""
    console.print()
    console.print(
        Panel.fit(
            "[bold blue]MCP PDCA Validation Cycle[/bold blue]\n"
            f"[dim]Max cycles: {max_cycles} | Target: {ACCURACY_TARGET}%[/dim]",
            border_style="blue",
        )
    )
    console.print()

    generator = EvidenceGenerator(project_name=project)

    for cycle in range(1, max_cycles + 1):
        console.print(f"[cyan]━━━ PDCA Cycle {cycle}/{max_cycles} ━━━[/cyan]")
        console.print()

        # Determine servers based on category
        if category == "aws":
            servers = ALL_AWS_SERVERS
        elif category == "azure":
            servers = ALL_AZURE_SERVERS
        elif category == "finops":
            servers = ALL_FINOPS_SERVERS
        else:
            servers = ALL_AWS_SERVERS

        # Run validations
        results: list[ServerValidationResult] = []
        for server_name in servers:
            validator = get_validator_for_server(server_name)
            if validator:
                try:
                    result = validator.validate()
                    results.append(result)
                    print_server_result(result)
                except Exception as e:
                    result = ServerValidationResult(
                        server_name=server_name,
                        status=ValidationStatus.ERROR,
                        accuracy=0.0,
                        error=str(e),
                    )
                    results.append(result)

        # Create report
        report = MCPValidationReport(
            server_results=results,
            pdca_cycle=cycle,
            max_pdca_cycles=max_cycles,
            project=project or Path.cwd().name.lower().replace("_", "-"),
        )

        # Generate cycle evidence
        evidence_path = generator.generate_pdca_cycle_evidence(cycle, report)
        console.print()
        console.print(f"[dim]Cycle evidence: {evidence_path}[/dim]")

        if report.target_met:
            console.print()
            console.print(f"[green bold]✓ Target achieved in cycle {cycle}![/green bold]")
            generator.generate_validation_evidence(report)
            raise typer.Exit(0)

        console.print()
        console.print(f"[yellow]Target not met ({report.overall_accuracy:.2f}% < {ACCURACY_TARGET}%)[/yellow]")

        if cycle < max_cycles:
            console.print("[dim]Starting next cycle...[/dim]")
            console.print()

    # Max cycles reached without achieving target
    console.print()
    console.print(f"[red bold]✗ Max cycles ({max_cycles}) reached without achieving target[/red bold]")
    console.print("[yellow]Human escalation required (CHK041)[/yellow]")
    raise typer.Exit(1)


@app.command()
def list_servers() -> None:
    """List all available MCP servers for validation."""
    console.print()
    console.print("[bold]Available MCP Servers[/bold]")
    console.print()

    console.print("[cyan]AWS Servers (P0-P1):[/cyan]")
    for server in ALL_AWS_SERVERS:
        validator = get_validator_for_server(server)
        status = "[green]✓[/green]" if validator else "[dim]○[/dim]"
        console.print(f"  {status} {server}")

    console.print()
    console.print("[cyan]Azure Servers (P2):[/cyan]")
    for server in ALL_AZURE_SERVERS:
        validator = get_validator_for_server(server)
        status = "[green]✓[/green]" if validator else "[dim]○[/dim]"
        console.print(f"  {status} {server}")

    console.print()
    console.print("[cyan]FinOps Servers (P3):[/cyan]")
    for server in ALL_FINOPS_SERVERS:
        validator = get_validator_for_server(server)
        status = "[green]✓[/green]" if validator else "[dim]○[/dim]"
        console.print(f"  {status} {server}")

    console.print()
    console.print("[dim]✓ = Validator implemented, ○ = Not yet implemented[/dim]")


@app.command()
def version() -> None:
    """Show version information."""
    from . import __adlc_version__, __version__

    console.print(f"MCP Validation Framework v{__version__}")
    console.print(f"ADLC Version: {__adlc_version__}")
    console.print("Package: runbooks (PyPI)")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
