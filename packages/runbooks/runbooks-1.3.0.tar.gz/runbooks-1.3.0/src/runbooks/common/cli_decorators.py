"""
CLI Decorators for runbooks package - Enterprise CLI Standardization

Provides standard decorators for common CLI options, eliminating code duplication
and ensuring consistent user experience across all runbooks modules.

Following KISS & DRY principles - enhance existing structure without creating complexity.
"""

import click
from functools import wraps
from typing import Callable, Any


def common_aws_options(f: Callable) -> Callable:
    """
    Standard AWS options for all runbooks commands.

    Provides consistent AWS configuration options across all modules:
    - --profile: AWS profile override (highest priority in 3-tier system)
    - --region: AWS region override
    - --dry-run: Safe analysis mode (enterprise default)

    Usage:
        @common_aws_options
        @click.command()
        def my_command(profile, region, dry_run, **kwargs):
            # Your command logic here
    """

    @click.option(
        "--profile",
        help="""AWS profile for single-account operations.

📋 Profile Selection Guide:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Single Account → Use --profile YOUR_PROFILE
  Example: --profile dev-account
  When: Developer/operator working in one AWS account

Multi-Account LZ → Use --all-profiles (see inventory commands)
  Example: --all-profiles
  When: Platform team discovering across organization

🔐 Enrichment Profiles (Automatic):
  • Organizations: MANAGEMENT_PROFILE
  • Costs: BILLING_PROFILE
  Note: Separate from discovery profile

Decision: Single account = --profile | Multi-account = --all-profiles""",
        type=str,
    )
    @click.option("--region", help="AWS region override (default: ap-southeast-2)", type=str, default="ap-southeast-2")
    @click.option(
        "--dry-run",
        is_flag=True,
        default=True,
        help="Safe analysis mode - no resource modifications (enterprise default)",
    )
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def common_output_options(f: Callable) -> Callable:
    """
    Standard output options for all runbooks commands.

    Provides consistent output formatting and export options:
    - -f, --format, --output-format: JSON, CSV, table, PDF output formats (triple alias)
    - --output-dir: Output directory for generated files
    - --all-outputs: Generate all output formats (JSON, CSV, PDF, Markdown)
    - --csv, --json, --markdown: Convenience flags for single format export (Track 5: Rich UX)
    - --export: [DEPRECATED] Use --all-outputs instead (backward compatibility)

    Usage:
        @common_output_options
        @click.command()
        def my_command(format, output_dir, all_outputs, csv, json, markdown, export, **kwargs):
            # Convenience flags automatically activate all_outputs
            # Your command logic here (parameter name is 'format')
    """

    @click.option(
        "-f",
        "--format",
        "--output-format",
        type=click.Choice(["json", "csv", "table", "pdf", "markdown"], case_sensitive=False),
        default="table",
        help="Output format for results display (-f/--format preferred, --output-format legacy)",
    )
    @click.option(
        "--output-dir",
        default="./awso_evidence",
        help="Directory for generated files and evidence packages",
        type=click.Path(),
    )
    @click.option(
        "--all-outputs",
        is_flag=True,
        help="Generate all output formats (JSON, CSV, PDF, Markdown) - use with --output-dir",
    )
    # Track 5: Rich UX Adoption - Convenience export flags (finops pattern)
    @click.option(
        "--csv", "export_csv", is_flag=True, help="Export to CSV format (convenience flag, activates --all-outputs)"
    )
    @click.option(
        "--json", "export_json", is_flag=True, help="Export to JSON format (convenience flag, activates --all-outputs)"
    )
    @click.option(
        "--markdown",
        "export_markdown",
        is_flag=True,
        help="Export to Markdown format (convenience flag, activates --all-outputs)",
    )
    # Backward compatibility (deprecated)
    @click.option(
        "--export",
        is_flag=True,
        hidden=True,  # Hide from --help
        help="[DEPRECATED] Use --all-outputs instead",
    )
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Track 5: Auto-activate all_outputs if any convenience flag is set
        if kwargs.get("export_csv") or kwargs.get("export_json") or kwargs.get("export_markdown"):
            kwargs["all_outputs"] = True
        return f(*args, **kwargs)

    return wrapper


def mcp_validation_option(f: Callable) -> Callable:
    """
    MCP validation option for cost optimization and inventory modules.

    Provides MCP (Model Context Protocol) validation capability for enhanced accuracy:
    - --validate: Enable MCP validation with ≥99.5% accuracy target
    - --confidence-threshold: Minimum confidence threshold (default: 99.5%)

    Usage:
        @mcp_validation_option
        @click.command()
        def my_command(validate, confidence_threshold, **kwargs):
            # Your command logic with MCP validation
    """

    @click.option("--validate", is_flag=True, help="Enable MCP validation for enhanced accuracy (≥99.5% target)")
    @click.option(
        "--confidence-threshold",
        type=float,
        default=99.5,
        help="Minimum confidence threshold for validation (default: 99.5%%)",
    )
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def enterprise_options(f: Callable) -> Callable:
    """
    Enterprise-specific options for multi-account operations.

    Provides enterprise deployment options:
    - --all: Use all available AWS profiles
    - --combine: Combine profiles from same AWS account
    - --approval-required: Require human approval for operations

    Usage:
        @enterprise_options
        @click.command()
        def my_command(all_profiles, combine, approval_required, **kwargs):
            # Your enterprise command logic
    """

    @click.option(
        "--all", "all_profiles", is_flag=True, help="Use all available AWS profiles for multi-account operations"
    )
    @click.option("--combine", is_flag=True, help="Combine profiles from the same AWS account for unified reporting")
    @click.option(
        "--approval-required",
        is_flag=True,
        default=True,
        help="Require human approval for state-changing operations (enterprise default)",
    )
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def performance_options(f: Callable) -> Callable:
    """
    Performance monitoring options for enterprise operations.

    Provides performance monitoring and optimization options:
    - --performance-target: Target execution time in seconds
    - --timeout: Maximum execution timeout
    - --parallel: Enable parallel processing where supported

    Usage:
        @performance_options
        @click.command()
        def my_command(performance_target, timeout, parallel, **kwargs):
            # Your performance-monitored command
    """

    @click.option(
        "--performance-target", type=int, default=30, help="Target execution time in seconds (enterprise default: 30s)"
    )
    @click.option("--timeout", type=int, default=300, help="Maximum execution timeout in seconds (default: 5 minutes)")
    @click.option("--parallel", is_flag=True, help="Enable parallel processing for multi-resource operations")
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def all_standard_options(f: Callable) -> Callable:
    """
    Convenience decorator applying all standard options.

    Combines common_aws_options, common_output_options, mcp_validation_option,
    enterprise_options, and performance_options for comprehensive CLI commands.

    Usage:
        @all_standard_options
        @click.command()
        def comprehensive_command(**kwargs):
            # Command with all standard options available
    """

    @performance_options
    @enterprise_options
    @mcp_validation_option
    @common_output_options
    @common_aws_options
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def common_multi_account_options(f: Callable) -> Callable:
    """
    Multi-account and multi-region AWS options for enterprise operations.

    Provides:
    - --all-profiles: Process all configured AWS profiles (multi-account)
    - --profiles: [LEGACY] Specific profiles (use --all-profiles for all)
    - --regions: Specific AWS regions (space-separated)
    - --all-regions: Process all enabled AWS regions

    Note: --profile is provided by common_aws_options decorator

    Usage:
        @common_multi_account_options
        @common_aws_options
        @click.command()
        def my_command(profile, all_profiles, profiles, regions, all_regions, **kwargs):
            # Multi-account command logic
    """

    @click.option(
        "--all-profiles",
        is_flag=True,
        default=False,
        help="""Multi-account discovery (CENTRALISED_OPS_PROFILE as aggregator).

📋 Behavior:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Queries AWS Resource Explorer aggregator index
• Discovers resources across ALL accounts in Landing Zone
• Requires CENTRALISED_OPS_PROFILE with cross-account permissions

🔐 Enrichment Layers (Automatic):
  • Organizations metadata: MANAGEMENT_PROFILE
  • Cost data: BILLING_PROFILE
  Note: Enrichment uses separate profiles regardless of discovery mode

Use Case: Enterprise platform teams managing 67+ account Landing Zones""",
    )
    @click.option(
        "--profiles",
        type=str,
        multiple=True,
        help='Specific AWS profiles (comma-separated, e.g., "billing,security,audit")',
    )
    @click.option("--regions", type=str, multiple=True, help="Specific AWS regions (space-separated)")
    @click.option("--all-regions", is_flag=True, default=False, help="Process all enabled AWS regions")
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper


def common_filter_options(f: Callable) -> Callable:
    """
    Common filtering options for resource discovery.

    Provides:
    - --tags: Filter by tags (key=value format)
    - --accounts: Filter by specific account IDs

    Usage:
        @common_filter_options
        @click.command()
        def my_command(tags, accounts, **kwargs):
            # Filtering logic
    """

    @click.option("--tags", type=str, multiple=True, help="Filter by tags (key=value format)")
    @click.option("--accounts", type=str, multiple=True, help="Filter by specific account IDs")
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    return wrapper
