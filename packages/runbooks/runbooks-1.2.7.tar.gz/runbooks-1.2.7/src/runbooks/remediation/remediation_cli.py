#!/usr/bin/env python3
"""
Remediation CLI Commands - Dynamic Multi-Account Support

Enhanced remediation CLI with enterprise configuration patterns:
- Dynamic account discovery (environment variables, config files, Organizations API)
- Profile override support (--profile parameter)
- Multi-account operations with safety controls
- Configuration-driven approach eliminating hardcoded values

Author: DevOps Security Engineer (Claude Code Enterprise Team)
Version: 1.0 - Enterprise Dynamic Configuration Ready
"""

import os
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

from .multi_account import (
    MultiAccountRemediator,
    discover_organization_accounts,
    get_accounts_from_environment,
)
from .universal_account_discovery import UniversalAccountDiscovery


@click.group()
@click.option("--profile", default=None, help="AWS profile to use (overrides environment variables)")
@click.option("--output-dir", default="./artifacts/remediation", help="Output directory for remediation reports")
@click.pass_context
def remediation(ctx, profile: Optional[str], output_dir: str):
    """
    Enterprise Security Remediation with Dynamic Account Discovery.

    Supports configuration via:
    - Environment variables (REMEDIATION_TARGET_ACCOUNTS)
    - Configuration files (REMEDIATION_ACCOUNT_CONFIG)
    - AWS Organizations API discovery
    - Profile override patterns
    """
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    ctx.obj["output_dir"] = output_dir

    # Validate profile if specified
    if profile:
        resolved_profile = get_profile_for_operation("management", profile)
        if not validate_profile_access(resolved_profile, "remediation operations"):
            print_error(f"Profile validation failed: {resolved_profile}")
            raise click.Abort()


@remediation.command("s3-security")
@click.option(
    "--operations",
    multiple=True,
    type=click.Choice(["block_public_access", "enforce_ssl", "enable_encryption"]),
    default=["block_public_access"],
    help="S3 security operations to execute",
)
@click.option("--accounts", help="Comma-separated account IDs (overrides discovery)")
@click.option("--all", "all_accounts", is_flag=True, help="Execute on all discovered accounts via Organizations API")
@click.option("--dry-run", is_flag=True, default=True, help="Perform dry run without making changes (default: true)")
@click.option("--parallel", is_flag=True, default=True, help="Execute operations in parallel (default: true)")
@click.option("--max-workers", type=int, default=5, help="Maximum parallel workers")
@click.pass_context
def s3_security(
    ctx,
    operations: List[str],
    accounts: Optional[str],
    all_accounts: bool,
    dry_run: bool,
    parallel: bool,
    max_workers: int,
):
    """
    Execute S3 security remediation across multiple accounts.

    Environment Variables Supported:
    - REMEDIATION_TARGET_ACCOUNTS: Comma-separated account IDs
    - REMEDIATION_ACCOUNT_CONFIG: Path to accounts configuration file
    - ACCESS_PORTAL_URL: AWS SSO start URL for multi-account access
    """
    profile = ctx.obj["profile"]
    output_dir = ctx.obj["output_dir"]

    try:
        # Display operation header
        operation_status = "DRY RUN" if dry_run else "LIVE EXECUTION"
        console.print(
            create_panel(
                f"[bold cyan]S3 Security Remediation - {operation_status}[/bold cyan]\n\n"
                f"[dim]Operations: {', '.join(operations)}[/dim]\n"
                f"[dim]Profile: {profile or 'default'}[/dim]\n"
                f"[dim]Parallel: {parallel} (workers: {max_workers})[/dim]",
                title="🛡️ Starting S3 Remediation",
                border_style="cyan" if dry_run else "red",
            )
        )

        # Safety warning for live operations
        if not dry_run:
            console.print(
                Panel(
                    "[bold red]⚠️  LIVE EXECUTION MODE ⚠️[/bold red]\n\n"
                    "This will make actual changes to AWS resources.\n"
                    "Ensure you have proper permissions and backups.",
                    border_style="red",
                    title="Security Warning",
                )
            )

            if not click.confirm("Continue with live execution?"):
                print_warning("Operation cancelled by user")
                return

        # Determine target accounts
        target_accounts = []

        if accounts:
            # Use specified accounts
            account_ids = [acc.strip() for acc in accounts.split(",")]
            target_accounts = [
                type("AWSAccount", (), {"account_id": acc_id, "environment": f"specified-{i}"})()
                for i, acc_id in enumerate(account_ids)
            ]
            print_info(f"Using specified accounts: {len(target_accounts)} accounts")

        elif all_accounts:
            # Discover all accounts via Organizations API
            print_info("Discovering accounts via Organizations API...")
            target_accounts = discover_organization_accounts(profile=profile)
            print_info(f"Discovered {len(target_accounts)} accounts")

        else:
            # Use environment configuration
            env_accounts = get_accounts_from_environment()
            if env_accounts:
                target_accounts = env_accounts
                print_info(f"Using accounts from environment: {len(target_accounts)} accounts")
            else:
                # Fallback to Organizations discovery
                print_info("No environment configuration found, discovering via Organizations API...")
                target_accounts = discover_organization_accounts(profile=profile)
                print_info(f"Discovered {len(target_accounts)} accounts")

        if not target_accounts:
            print_error("No target accounts found for remediation")
            raise click.Abort()

        # Initialize multi-account remediator
        sso_start_url = os.getenv("ACCESS_PORTAL_URL")
        if not sso_start_url:
            print_warning("ACCESS_PORTAL_URL not set - SSO functionality may be limited")

        remediator = MultiAccountRemediator(
            sso_start_url=sso_start_url, parallel_execution=parallel, max_workers=max_workers
        )

        # Execute bulk S3 security operations
        print_info(f"Executing S3 security operations on {len(target_accounts)} accounts...")

        results = remediator.bulk_s3_security(accounts=target_accounts, operations=list(operations), dry_run=dry_run)

        # Display results summary
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if r.failed]

        print_success(
            f"S3 security remediation completed: {len(successful_results)} successful, {len(failed_results)} failed"
        )

        if failed_results:
            print_warning(f"Failed operations: {len(failed_results)}")
            for result in failed_results[:5]:  # Show first 5 failures
                print_error(f"  Account {result.context.account.account_id}: {result.error_message}")

        # Generate compliance report
        compliance_report = remediator.generate_compliance_report(results)
        print_info(
            f"Compliance report generated: {compliance_report['total_operations']} operations across {compliance_report['total_accounts']} accounts"
        )

        # Display configuration sources used
        _display_configuration_sources()

    except Exception as e:
        print_error(f"S3 security remediation failed: {str(e)}")
        raise click.Abort()


@remediation.command("list-accounts")
@click.option("--show-environment", is_flag=True, help="Show environment classification for each account")
@click.pass_context
def list_accounts(ctx, show_environment: bool):
    """
    List available accounts for remediation operations.
    """
    profile = ctx.obj["profile"]

    try:
        console.print(
            create_panel(
                "[bold cyan]Account Discovery[/bold cyan]\n\n[dim]Discovering accounts from all sources...[/dim]",
                title="📋 Account Listing",
                border_style="blue",
            )
        )

        # Try environment configuration first
        env_accounts = get_accounts_from_environment()
        if env_accounts:
            console.print("\n[bold]Accounts from Environment Configuration:[/bold]")
            for account in env_accounts:
                env_indicator = f" ({account.environment})" if show_environment else ""
                console.print(f"  ✅ {account.account_id}{env_indicator}")

        # Discover from Organizations API
        try:
            org_accounts = discover_organization_accounts(profile=profile)
            console.print(f"\n[bold]Accounts from Organizations API Discovery:[/bold]")
            for account in org_accounts:
                env_indicator = f" ({account.environment})" if show_environment else ""
                name_part = f" - {account.name}" if hasattr(account, "name") and account.name else ""
                console.print(f"  🌐 {account.account_id}{env_indicator}{name_part}")
        except Exception as e:
            print_warning(f"Organizations API discovery failed: {str(e)}")

        # Display configuration information
        console.print("\n[bold]Configuration Sources:[/bold]")

        if os.getenv("REMEDIATION_TARGET_ACCOUNTS"):
            console.print("  ✅ REMEDIATION_TARGET_ACCOUNTS environment variable")

        if os.getenv("REMEDIATION_ACCOUNT_CONFIG"):
            config_path = os.getenv("REMEDIATION_ACCOUNT_CONFIG")
            status = "✅" if os.path.exists(config_path) else "⚠️ "
            console.print(f"  {status} REMEDIATION_ACCOUNT_CONFIG: {config_path}")

        if not env_accounts:
            console.print("  ℹ️  No environment configuration - using Organizations API discovery")

    except Exception as e:
        print_error(f"Account listing failed: {str(e)}")
        raise click.Abort()


@remediation.command("config-info")
@click.pass_context
def config_info(ctx):
    """
    Display current remediation configuration and environment setup.
    """
    console.print(Panel.fit("[bold cyan]Remediation Configuration Information[/bold cyan]", border_style="cyan"))

    # Display environment variables
    print_info("Environment Configuration:")

    env_vars = {
        "Account Configuration": {
            "REMEDIATION_TARGET_ACCOUNTS": os.getenv("REMEDIATION_TARGET_ACCOUNTS", "Not set"),
            "REMEDIATION_ACCOUNT_CONFIG": os.getenv("REMEDIATION_ACCOUNT_CONFIG", "Not set"),
        },
        "SSO Configuration": {
            "ACCESS_PORTAL_URL": os.getenv("ACCESS_PORTAL_URL", "Not set"),
        },
        "Profile Configuration": {
            "MANAGEMENT_PROFILE": os.getenv("MANAGEMENT_PROFILE", "Not set"),
            "CENTRALISED_OPS_PROFILE": os.getenv("CENTRALISED_OPS_PROFILE", "Not set"),
        },
    }

    for category, variables in env_vars.items():
        console.print(f"\n[bold]{category}:[/bold]")
        for var_name, var_value in variables.items():
            status = "✅" if var_value != "Not set" else "❌"
            console.print(f"  {status} {var_name}: {var_value}")

    # Display example configuration files
    console.print("\n[bold]Example Configuration Files:[/bold]")
    config_examples = ["src/runbooks/remediation/config/accounts_example.json"]

    for config_file in config_examples:
        if os.path.exists(config_file):
            console.print(f"  ✅ {config_file}")
        else:
            console.print(f"  📝 {config_file} (example)")

    # Usage examples
    console.print("\n[bold]Usage Examples:[/bold]")
    examples = [
        "# Set target accounts via environment variable",
        'export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666"',
        "",
        "# Use configuration file",
        'export REMEDIATION_ACCOUNT_CONFIG="/path/to/accounts.json"',
        "",
        "# Execute S3 security remediation",
        "runbooks remediation s3-security --operations block_public_access --dry-run",
        "",
        "# Execute on all discovered accounts",
        "runbooks remediation s3-security --all --operations block_public_access,enforce_ssl",
    ]

    for example in examples:
        if example.startswith("#") or example == "":
            console.print(f"[dim]{example}[/dim]")
        else:
            console.print(f"[cyan]{example}[/cyan]")


def _display_configuration_sources():
    """Display information about configuration sources used."""
    console.print("\n[bold]Configuration Sources:[/bold]")

    # Check environment variables
    if os.getenv("REMEDIATION_TARGET_ACCOUNTS"):
        console.print("  ✅ Using REMEDIATION_TARGET_ACCOUNTS environment variable")

    if os.getenv("REMEDIATION_ACCOUNT_CONFIG"):
        config_path = os.getenv("REMEDIATION_ACCOUNT_CONFIG")
        if os.path.exists(config_path):
            console.print(f"  ✅ Using accounts config file: {config_path}")
        else:
            console.print(f"  ⚠️  Accounts config file not found: {config_path}")

    if os.getenv("ACCESS_PORTAL_URL"):
        console.print("  ✅ AWS SSO configured via ACCESS_PORTAL_URL")
    else:
        console.print("  ⚠️  ACCESS_PORTAL_URL not set - SSO functionality limited")

    if not any([os.getenv("REMEDIATION_TARGET_ACCOUNTS"), os.getenv("REMEDIATION_ACCOUNT_CONFIG")]):
        console.print("  ℹ️  Using default configuration (Organizations API discovery)")


@remediation.command("generate-config")
@click.option(
    "--output-dir", default="./artifacts/remediation/config", help="Output directory for configuration templates"
)
@click.pass_context
def generate_config_templates(ctx, output_dir: str):
    """
    Generate universal configuration templates for remediation operations.

    Creates templates for:
    - Account discovery configuration
    - Environment variable examples
    - Complete setup documentation

    All templates support universal AWS compatibility with no hardcoded values.
    """
    print_info(f"Generating universal remediation configuration templates in {output_dir}...")

    try:
        # Create output directory
        from pathlib import Path

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Use the security config generator (it covers remediation too)
        from runbooks.security.config_template_generator import SecurityConfigTemplateGenerator

        generator = SecurityConfigTemplateGenerator(output_dir)

        # Generate account discovery template
        account_config = generator.generate_account_config_template()
        account_path = output_path / "account_config.json"
        import json

        with open(account_path, "w") as f:
            json.dump(account_config, f, indent=2)
        print_success(f"Generated account configuration: {account_path}")

        # Generate environment variables for remediation
        env_template = """# Universal Remediation Configuration
# ===================================

# Profile Configuration (Universal Profile Management)
export AWS_PROFILE="your-aws-profile-name"

# Account Discovery Configuration
export REMEDIATION_ACCOUNT_CONFIG="/path/to/account_config.json"

# Alternative: Simple comma-separated account list
export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666,777788889999"

# Remediation Configuration
export REMEDIATION_OUTPUT_DIR="./artifacts/remediation"
export REMEDIATION_MAX_CONCURRENT="10"
export REMEDIATION_DRY_RUN="true"
export REMEDIATION_TIMEOUT_SECONDS="300"

# Multi-Account Configuration
export ORGANIZATIONS_MANAGEMENT_ROLE="OrganizationAccountAccessRole"
export CROSS_ACCOUNT_ROLE="SecurityRemediationRole"

# Example Usage Commands
# ======================

# S3 security remediation (dry run)
runbooks remediation s3-security --operations block_public_access --dry-run

# Multi-account remediation with all discovered accounts
runbooks remediation s3-security --all --operations block_public_access,enforce_ssl

# Specific account remediation
runbooks remediation s3-security --accounts 111122223333,444455556666 --operations enable_encryption

# EC2 security remediation
runbooks remediation ec2-security --operations terminate_unused_instances --dry-run

# Generate account discovery template
runbooks remediation generate-config --output-dir ./config
"""

        env_path = output_path / "environment_variables.sh"
        with open(env_path, "w") as f:
            f.write(env_template)
        print_success(f"Generated environment variables template: {env_path}")

        # Generate setup documentation specific to remediation
        setup_docs = """# Universal Remediation Module Setup Guide
========================================

This guide helps you configure the remediation module for ANY AWS environment without hardcoded values.

## Quick Start

1. **Basic Setup (Single Account)**
   ```bash
   export AWS_PROFILE="your-aws-profile"
   runbooks remediation s3-security --operations block_public_access --dry-run
   ```

2. **Multi-Account Setup (Organizations)**
   ```bash
   export AWS_PROFILE="your-management-account-profile"
   runbooks remediation s3-security --all --operations block_public_access
   ```

3. **Custom Account Configuration**
   ```bash
   export REMEDIATION_ACCOUNT_CONFIG="./account_config.json"
   runbooks remediation s3-security --operations enforce_ssl,enable_encryption
   ```

## Account Discovery

The remediation module automatically discovers target accounts using:

1. **Environment Variables** (highest priority)
   ```bash
   export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666"
   ```

2. **Configuration File**
   ```bash
   export REMEDIATION_ACCOUNT_CONFIG="./account_config.json"
   ```

3. **AWS Organizations API** (automatic discovery)
   ```bash
   # No configuration needed - uses Organizations API
   runbooks remediation s3-security --all
   ```

4. **Current Account** (single account fallback)
   ```bash
   # Falls back to current account if no other configuration
   runbooks remediation s3-security --operations block_public_access
   ```

## Available Remediation Operations

### S3 Security Operations
```bash
# Block public access (recommended)
runbooks remediation s3-security --operations block_public_access

# Enforce SSL/TLS
runbooks remediation s3-security --operations enforce_ssl

# Enable encryption at rest
runbooks remediation s3-security --operations enable_encryption

# Enable access logging
runbooks remediation s3-security --operations enable_logging

# All S3 security operations
runbooks remediation s3-security --operations block_public_access,enforce_ssl,enable_encryption
```

### EC2 Security Operations
```bash
# Security group optimization
runbooks remediation ec2-security --operations optimize_security_groups

# Unused instance cleanup
runbooks remediation ec2-security --operations terminate_unused_instances

# Enable detailed monitoring
runbooks remediation ec2-security --operations enable_monitoring
```

## Safety Features

### Dry Run Mode (Recommended)
```bash
# Always test first with dry run
runbooks remediation s3-security --operations block_public_access --dry-run

# Execute after reviewing dry run results
runbooks remediation s3-security --operations block_public_access
```

### Account Filtering
```bash
# Specific accounts only
runbooks remediation s3-security --accounts 111122223333,444455556666

# Exclude specific accounts
export REMEDIATION_EXCLUDE_ACCOUNTS="999888777666"
runbooks remediation s3-security --all
```

### Operation Scope Control
```bash
# Single operation
runbooks remediation s3-security --operations block_public_access

# Multiple operations
runbooks remediation s3-security --operations block_public_access,enforce_ssl

# All available operations for service
runbooks remediation s3-security --operations all
```

## Configuration Examples

### Account Configuration File
```json
{
  "target_accounts": [
    {
      "account_id": "111122223333",
      "account_name": "Production Environment",
      "profile_name": "prod-profile",
      "criticality": "high"
    },
    {
      "account_id": "444455556666",
      "account_name": "Staging Environment",
      "profile_name": "staging-profile",
      "criticality": "medium"
    }
  ],
  "discovery_settings": {
    "max_concurrent_accounts": 10,
    "validation_timeout_seconds": 30
  }
}
```

### Environment Variables
```bash
# Simple account list
export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666,777788889999"

# Performance tuning
export REMEDIATION_MAX_CONCURRENT="10"
export REMEDIATION_TIMEOUT_SECONDS="300"

# Output configuration
export REMEDIATION_OUTPUT_DIR="./artifacts/remediation"
export REMEDIATION_DRY_RUN="true"
```

## Troubleshooting

### Common Issues

1. **No Accounts Discovered**
   ```bash
   # Check available accounts
   runbooks remediation discover-accounts
   
   # Set specific accounts
   export REMEDIATION_TARGET_ACCOUNTS="111122223333"
   ```

2. **Access Denied**
   ```bash
   # Verify profile access
   aws sts get-caller-identity --profile your-profile
   
   # Check Organizations permissions
   aws organizations list-accounts --profile your-management-profile
   ```

3. **Operation Timeout**
   ```bash
   # Increase timeout
   export REMEDIATION_TIMEOUT_SECONDS="600"
   
   # Reduce concurrent operations
   export REMEDIATION_MAX_CONCURRENT="5"
   ```

### Validation Commands
```bash
# Test account discovery
runbooks remediation discover-accounts --profile your-profile

# Validate configuration
runbooks remediation config --profile your-profile

# Test specific operation (dry run)
runbooks remediation s3-security --operations block_public_access --dry-run --accounts 111122223333
```

This configuration system provides universal compatibility with any AWS environment while maintaining safety and control.
"""

        docs_path = output_path / "REMEDIATION_SETUP_GUIDE.md"
        with open(docs_path, "w") as f:
            f.write(setup_docs)
        print_success(f"Generated setup documentation: {docs_path}")

        print_success("Remediation configuration templates generated successfully!")
        console.print("\n[bold yellow]Next steps:[/bold yellow]")
        console.print("1. Review and customize the generated configuration files")
        console.print("2. Set REMEDIATION_ACCOUNT_CONFIG or REMEDIATION_TARGET_ACCOUNTS")
        console.print("3. Test with: runbooks remediation s3-security --operations block_public_access --dry-run")
        console.print("4. Execute: runbooks remediation s3-security --operations block_public_access")

    except Exception as e:
        print_error(f"Failed to generate configuration templates: {e}")
        raise click.Abort()


if __name__ == "__main__":
    remediation()
