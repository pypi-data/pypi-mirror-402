"""
Remediation Commands Module - Security Remediation & Multi-Account Operations

KISS Principle: Focused on security remediation and compliance automation
DRY Principle: Centralized multi-account remediation patterns

Exposes enterprise remediation functionality from src/runbooks/remediation/
with 45 Python files covering Security Hub, GuardDuty, S3, IAM, EC2, and more.
"""

import click
from runbooks.common.rich_utils import console


def create_remediation_group():
    """
    Create the remediation command group with all subcommands.

    Returns:
        Click Group object with all remediation commands

    Performance: Lazy creation only when needed by DRYCommandRegistry
    Context Reduction: Exposes hidden 45-file remediation module
    """

    # Custom Group class with Rich Tree/Table help formatting
    class RichRemediationGroup(click.Group):
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
                click.echo("Usage: runbooks remediation [OPTIONS] COMMAND [ARGS]...")
                click.echo("")
                click.echo("  Enterprise Security Remediation with Dynamic Account Discovery.")
                click.echo("")
                click.echo("Commands:")
                click.echo("  s3-security      Execute S3 security remediation across multiple accounts")
                click.echo("  list-accounts    List available accounts for remediation operations")
                click.echo("  config-info      Display current remediation configuration")
                click.echo("  generate-config  Generate universal configuration templates")
                return

            # Categorize commands based on business function
            categories = {
                "🛡️ S3 Security Operations": [
                    ("s3-security", "S3 security remediation (block public access, enforce SSL, enable encryption)")
                ],
                "📋 Account Management": [("list-accounts", "List available accounts for remediation operations")],
                "⚙️ Configuration": [
                    ("config-info", "Display current remediation configuration and environment setup"),
                    ("generate-config", "Generate universal configuration templates for remediation operations"),
                ],
            }

            # Phase 1: Pre-calculate max column widths across ALL categories
            max_cmd_len = 0
            for category_commands in categories.values():
                for cmd, desc in category_commands:
                    max_cmd_len = max(max_cmd_len, len(cmd))

            # Set command column width with padding
            cmd_width = max_cmd_len + 2

            # Create Rich Tree
            tree = Tree("[bold cyan]Remediation Commands[/bold cyan] (4 commands)")

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

            # Add usage hints
            console.print("\n[bold]Usage Patterns:[/bold]")
            console.print("  [dim]# List available accounts for remediation[/dim]")
            console.print("  [cyan]runbooks remediation list-accounts[/cyan]")
            console.print("")
            console.print("  [dim]# Execute S3 security remediation (dry-run by default)[/dim]")
            console.print("  [cyan]runbooks remediation s3-security --operations block_public_access --dry-run[/cyan]")
            console.print("")
            console.print("  [dim]# Generate configuration templates[/dim]")
            console.print("  [cyan]runbooks remediation generate-config --output-dir ./config[/cyan]")

    # Import the existing remediation CLI group
    from runbooks.remediation.remediation_cli import remediation

    # Return the existing group (it already has all commands)
    # We just need to wrap it with the custom Group class for rich formatting
    return remediation


# Export for registry
__all__ = ["create_remediation_group"]
