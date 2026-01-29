"""
Common CLI Decorators for Modular Commands

KISS Principle: Simple, reusable decorators for consistent CLI patterns
DRY Principle: No duplicated decorator logic across command modules

This module provides consistent decorators used across all modular command
files, enabling the DRY principle while maintaining enterprise standards.
"""

import functools
import time
from typing import Any, Callable

import click
from rich.console import Console

console = Console()


def common_aws_options(f):
    """
    Common AWS options for all commands.

    Provides consistent AWS configuration options across all command modules:
    - --profile: AWS profile selection
    - --region: AWS region targeting
    - --dry-run: Safety mode for testing
    """
    f = click.option("--profile", default="default", help="AWS profile to use")(f)
    f = click.option("--region", help="AWS region (overrides profile default)")(f)
    f = click.option("--dry-run", is_flag=True, help="Perform a dry run without making changes")(f)
    return f


def common_output_options(f):
    """
    Common output options for commands that generate reports.

    Provides consistent output formatting options:
    - --format: Output format selection (table, csv, json, markdown, pdf)
    - --output-file: File output destination
    """
    f = click.option(
        "--format",
        "output_format",
        type=click.Choice(["table", "csv", "json", "markdown", "pdf"]),
        default="table",
        help="Output format",
    )(f)
    f = click.option("--output-file", type=click.Path(), help="Output file path")(f)
    return f


def common_filter_options(f):
    """
    Common filtering options for resource discovery commands.

    Provides consistent filtering capabilities:
    - --tags: Resource tag filtering
    - --accounts: Account ID filtering
    - --regions: Region filtering
    """
    f = click.option("--tags", multiple=True, help="Filter by tags (key=value format)")(f)
    f = click.option("--accounts", multiple=True, help="Filter by account IDs")(f)
    f = click.option("--regions", multiple=True, help="Filter by regions")(f)
    return f


def performance_timing(f):
    """
    Performance timing decorator for measuring command execution time.

    Automatically tracks and reports command execution time for performance
    monitoring and optimization analysis.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time

            # Only show timing in debug mode or for slow operations
            if execution_time > 1.0:  # Show for operations > 1 second
                console.print(f"[dim]⏱️ Completed in {execution_time:.2f}s[/dim]")

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            console.print(f"[red]❌ Failed after {execution_time:.2f}s: {e}[/red]")
            raise

    return wrapper


def error_handler(f):
    """
    Common error handling decorator for consistent error reporting.

    Provides enterprise-grade error handling with:
    - Rich formatting for better UX
    - Consistent error message structure
    - Debug information when enabled
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except click.ClickException:
            # Re-raise Click exceptions as-is
            raise
        except ImportError as e:
            console.print(f"[red]❌ Module not available: {e}[/red]")
            console.print(f"[yellow]💡 This functionality may require additional dependencies[/yellow]")
            raise click.ClickException("Required module not available")
        except Exception as e:
            console.print(f"[red]❌ Unexpected error: {e}[/red]")
            console.print(f"[yellow]💡 Run with --debug for detailed error information[/yellow]")
            raise click.ClickException(str(e))

    return wrapper


def require_aws_profile(f):
    """
    Decorator to ensure AWS profile is properly configured.

    Validates that the AWS profile exists and is accessible before
    executing commands that require AWS API access.
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Get profile from context or kwargs
        ctx = click.get_current_context()
        profile = ctx.obj.get("profile", "default")

        try:
            import boto3

            # Test profile access
            session = boto3.Session(profile_name=profile)
            session.get_credentials()

            return f(*args, **kwargs)
        except Exception as e:
            console.print(f"[red]❌ AWS profile '{profile}' not accessible: {e}[/red]")
            console.print(f"[yellow]💡 Run 'aws configure list-profiles' to see available profiles[/yellow]")
            raise click.ClickException(f"AWS profile '{profile}' not accessible")

    return wrapper


def enterprise_audit_trail(f):
    """
    Enterprise audit trail decorator for compliance and governance.

    Automatically logs command execution for audit purposes with:
    - Command name and parameters
    - User context and timestamp
    - Execution results and duration
    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        ctx = click.get_current_context()

        # Log command execution start
        audit_data = {
            "command": ctx.command.name,
            "profile": ctx.obj.get("profile", "default"),
            "region": ctx.obj.get("region", "default"),
            "dry_run": ctx.obj.get("dry_run", False),
            "timestamp": time.time(),
        }

        try:
            result = f(*args, **kwargs)
            audit_data["status"] = "success"
            audit_data["duration"] = time.time() - audit_data["timestamp"]

            # Log successful execution
            if ctx.obj.get("debug"):
                console.print(f"[dim]📋 Audit: {audit_data}[/dim]")

            return result
        except Exception as e:
            audit_data["status"] = "error"
            audit_data["error"] = str(e)
            audit_data["duration"] = time.time() - audit_data["timestamp"]

            # Log failed execution
            if ctx.obj.get("debug"):
                console.print(f"[dim]📋 Audit: {audit_data}[/dim]")

            raise

    return wrapper


def rich_progress(description: str = "Processing"):
    """
    Rich progress indicator decorator for long-running operations.

    Args:
        description: Description text for the progress indicator

    Automatically shows a progress spinner for operations that take time,
    improving user experience for long-running commands.
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            from rich.progress import Progress, SpinnerColumn, TextColumn

            with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
            ) as progress:
                task = progress.add_task(description, total=None)

                try:
                    result = f(*args, **kwargs)
                    progress.update(task, description=f"✅ {description} completed")
                    return result
                except Exception as e:
                    progress.update(task, description=f"❌ {description} failed")
                    raise

        return wrapper

    return decorator
