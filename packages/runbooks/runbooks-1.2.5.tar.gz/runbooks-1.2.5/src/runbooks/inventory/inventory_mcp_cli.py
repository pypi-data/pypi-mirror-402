#!/usr/bin/env python3
"""
Inventory MCP Validation CLI - Standalone validation testing interface

This module provides a CLI interface for testing inventory MCP validation
functionality following the enterprise coordination patterns.

Strategic Alignment:
- "Do one thing and do it well" - Focused validation testing with clear output
- "Move Fast, But Not So Fast We Crash" - Safe validation testing without side effects

Features:
- Profile override priority system integration
- Rich CLI output with enterprise UX standards
- Resource count validation testing
- Evidence-based validation results
"""

import click
from typing import Dict, List, Optional

from ..common.profile_utils import get_profile_for_operation
from ..common.rich_utils import console, print_error, print_info, print_success, print_warning
from .mcp_inventory_validator import create_inventory_mcp_validator


# Terminal control constants
ERASE_LINE = "\x1b[2K"


@click.command()
@click.option("--profile", help="AWS profile name (takes precedence over environment variables)")
@click.option(
    "--resource-types",
    multiple=True,
    type=click.Choice(["ec2", "s3", "rds", "lambda", "vpc", "iam", "cloudformation"]),
    default=["ec2", "s3", "vpc"],
    help="Resource types to validate",
)
@click.option("--test-mode", is_flag=True, default=True, help="Run in test mode with sample data")
@click.option(
    "--real-validation",
    is_flag=True,
    default=False,
    help="Run validation against real AWS APIs (requires valid profiles)",
)
def validate_inventory_mcp(profile: Optional[str], resource_types: List[str], test_mode: bool, real_validation: bool):
    """
    Test inventory MCP validation functionality.

    This command demonstrates inventory MCP validation integration
    following proven enterprise patterns from FinOps module success.

    Examples:
        runbooks inventory validate-mcp --profile my-profile --resource-types ec2,s3
        runbooks inventory validate-mcp --test-mode --resource-types ec2,vpc,rds
        runbooks inventory validate-mcp --real-validation --profile enterprise-profile
    """
    try:
        console.print(f"[blue]🔍 Inventory MCP Validation Test[/blue]")
        console.print(
            f"[dim]Profile: {profile or 'environment fallback'} | Resources: {', '.join(resource_types)} | Test mode: {test_mode}[/dim]"
        )

        # Apply profile priority system following proven patterns
        operational_profile = get_profile_for_operation("operational", profile)
        validator_profiles = [operational_profile]

        # Initialize inventory MCP validator
        print_info("Initializing inventory MCP validator with enterprise patterns...")
        validator = create_inventory_mcp_validator(validator_profiles)

        if test_mode and not real_validation:
            # Test mode: Use sample data to demonstrate validation
            print_info("Running test mode with sample inventory data")

            # Create sample inventory data for testing
            sample_inventory = {
                operational_profile: {
                    "resource_counts": {
                        "ec2": 15,
                        "s3": 8,
                        "rds": 3,
                        "lambda": 12,
                        "vpc": 4,
                        "iam": 25,
                        "cloudformation": 6,
                    },
                    "regions": ["ap-southeast-2", "ap-southeast-6"],
                }
            }

            # Filter to requested resource types
            filtered_inventory = {
                operational_profile: {
                    "resource_counts": {
                        rt: sample_inventory[operational_profile]["resource_counts"].get(rt, 0) for rt in resource_types
                    },
                    "regions": sample_inventory[operational_profile]["regions"],
                }
            }

            print_info(
                f"Testing validation with sample resource counts: {filtered_inventory[operational_profile]['resource_counts']}"
            )

            # Note: In test mode, this will compare sample data against real AWS APIs
            # This demonstrates the validation mechanism without requiring mock data
            validation_results = validator.validate_inventory_data(filtered_inventory)

        elif real_validation:
            # Real validation mode: Requires actual inventory collection
            print_warning("Real validation mode requires actual inventory collection")
            print_info("This would typically be called from the main inventory collector")

            # For demonstration, we'll validate empty inventory (should show 0 vs actual counts)
            empty_inventory = {
                operational_profile: {
                    "resource_counts": {rt: 0 for rt in resource_types},
                    "regions": ["ap-southeast-2"],
                }
            }

            print_info("Validating empty inventory against real AWS APIs (demonstrates detection capability)")
            validation_results = validator.validate_inventory_data(empty_inventory)

        else:
            # Resource count validation only
            print_info("Running resource count validation test")

            sample_counts = {"ec2": 10, "s3": 5, "vpc": 2}

            # Filter to requested resource types
            test_counts = {rt: sample_counts.get(rt, 0) for rt in resource_types if rt in sample_counts}

            validation_results = validator.validate_resource_counts(test_counts)

        # Display results summary
        console.print(f"\n[bright_cyan]📊 Validation Test Results Summary[/]")

        if isinstance(validation_results, dict):
            if "total_accuracy" in validation_results:
                accuracy = validation_results.get("total_accuracy", 0)
                passed = validation_results.get("passed_validation", False)

                if passed:
                    print_success(f"✅ Test validation completed: {accuracy:.1f}% accuracy")
                else:
                    print_warning(f"⚠️ Test validation: {accuracy:.1f}% accuracy (target: ≥99.5%)")

                profiles_validated = validation_results.get("profiles_validated", 0)
                console.print(f"[dim]Profiles validated: {profiles_validated}[/dim]")

                # Show resource summary if available
                resource_summary = validation_results.get("resource_validation_summary", {})
                if resource_summary:
                    console.print(f"[dim]Resource types validated: {len(resource_summary)}[/dim]")

            elif "validated_count" in validation_results:
                validated_count = validation_results.get("validated_count", 0)
                passed_count = validation_results.get("passed_count", 0)
                print_info(f"Resource count validation: {passed_count}/{validated_count} passed")

            else:
                print_info("Validation completed - see detailed output above")

        # Integration guidance
        console.print(f"\n[bright_cyan]💡 Integration Information[/]")
        console.print(f"[dim]This MCP validator is automatically integrated into:[/dim]")
        console.print(f"[dim]  • runbooks inventory collect --profile {operational_profile}[/dim]")
        console.print(f"[dim]  • Enhanced inventory collector with --validate flag[/dim]")
        console.print(f"[dim]  • Real-time validation during inventory operations[/dim]")

    except Exception as e:
        print_error(f"Inventory MCP validation test failed: {e}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    validate_inventory_mcp()
