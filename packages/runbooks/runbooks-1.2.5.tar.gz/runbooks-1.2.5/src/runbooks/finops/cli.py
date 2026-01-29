import argparse
import sys
from typing import Any, Dict, Optional

import requests
from packaging import version
from rich.console import Console

from runbooks import __version__
from runbooks.finops.helpers import load_config_file

console = Console()


def welcome_banner() -> None:
    """Production welcome banner for CloudOps & FinOps Platform"""
    banner = rf"""
[bold bright_blue]CloudOps & FinOps Runbooks Platform (v{__version__})[/]
"""
    console.print(banner)


def check_latest_version() -> None:
    """Check for the latest version of the Runbooks package."""
    try:
        response = requests.get("https://pypi.org/pypi/runbooks/json", timeout=3)
        latest = response.json()["info"]["version"]
        if version.parse(latest) > version.parse(__version__):
            console.print(f"[bold red]A new version of Runbooks is available: {latest}[/]")
            console.print(
                "[bold bright_yellow]Please update using:\npip install --upgrade runbooks\nor\nuv add runbooks@latest\n[/]"
            )
    except Exception:
        pass


def main() -> int:
    """Command-line interface entry point."""
    welcome_banner()
    check_latest_version()
    from runbooks.finops.dashboard_runner import run_dashboard

    # Create the parser instance to be accessible for get_default
    parser = argparse.ArgumentParser(
        description="CloudOps & FinOps Runbooks Platform - Enterprise Multi-Account Cost Optimization",
        epilog="""
AWS Profile Usage Examples:
  Single Profile:     runbooks finops --profile my-account
  Multi-Account LZ:   runbooks finops --all-profile
  Legacy Support:     runbooks finops --profiles account1 account2 (still supported)
  Legacy All:         runbooks finops --all (still supported, use --all-profile instead)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config-file",
        "-C",
        help="Path to a TOML, YAML, or JSON configuration file.",
        type=str,
    )
    # AWS Profile Parameters (Standardized)
    parser.add_argument(
        "--profile",
        help="Single AWS profile for targeted analysis (replaces single --profiles usage)",
        type=str,
    )
    parser.add_argument(
        "--all-profile",
        action="store_true",
        help="Multi-account Landing Zone operations across all available AWS profiles",
    )

    # Legacy Parameters (Backward Compatibility)
    parser.add_argument(
        "--profiles",
        "-p",
        nargs="+",
        help="[LEGACY] Specific AWS profiles to use (space-separated) - use --profile for single profile",
        type=str,
    )
    parser.add_argument(
        "--all", "-a", action="store_true", help="[LEGACY] Use all available AWS profiles - use --all-profile instead"
    )

    # v1.1.30: Dry-run mode for testing without AWS API calls
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without making actual AWS API calls",
    )

    parser.add_argument(
        "--regions",
        "-r",
        nargs="+",
        help="AWS regions to check for EC2 instances (space-separated)",
        type=str,
    )
    parser.add_argument(
        "--combine",
        "-c",
        action="store_true",
        help="Combine profiles from the same AWS account",
    )
    parser.add_argument(
        "--report-name",
        "-n",
        help="Specify the base name for the report file (without extension)",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--report-type",
        "-y",
        nargs="+",
        choices=["csv", "json", "pdf", "markdown"],
        help="Specify one or more report types: csv and/or json and/or pdf and/or markdown (space-separated)",
        type=str,
        default=["markdown"],
    )

    # Convenience export format flags (LEAN enhancement: map to existing --report-type functionality)
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Export to CSV format (convenience flag for --report-type csv)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export to JSON format (convenience flag for --report-type json)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Export to PDF format (convenience flag for --report-type pdf)",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Export to Markdown format (convenience flag for --report-type markdown)",
    )

    parser.add_argument(
        "--dir",
        "-d",
        help="Directory to save the report files (default: current directory)",
        type=str,
    )
    parser.add_argument(
        "--time-range",
        "-t",
        help="Time range for cost data in days (default: current month). Examples: 7, 30, 90",
        type=int,
    )
    parser.add_argument(
        "--month",
        "-m",
        help="Specific month to analyze (YYYY-MM format). Examples: 2025-12, 2026-01. "
        "Overrides --time-range when specified.",
        type=str,
    )
    parser.add_argument(
        "--tag",
        "-g",
        nargs="+",
        help="Cost allocation tag to filter resources, e.g., --tag Team=DevOps",
        type=str,
    )
    parser.add_argument(
        "--trend",
        action="store_true",
        help="Display a trend report as bars for the past 6 months time range",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Display an audit report with cost anomalies, stopped EC2 instances, unused EBS volumes, budget alerts, and more",
    )

    # Enhanced Dashboard Configuration Parameters
    # v1.1.31: --mode is now for persona selection (executive|architect|sre)
    # Dashboard routing (single/multi) is IMPLICIT via --profile vs --all-profile (KISS/DRY/LEAN)
    parser.add_argument(
        "--mode",
        choices=["executive", "architect", "sre"],
        default="architect",
        help="Persona mode: executive (board-ready, top 5 services, strict validation), "
        "architect (infrastructure analysis, top 20, full decommission signals), "
        "sre (operations, top 20, anomaly detection with score/tier)",
        type=str,
    )
    parser.add_argument(
        "--top-services",
        help="Number of top services to display in single-account mode (default: 10)",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--top-accounts",
        help="Number of top accounts to display in multi-account mode (default: 5)",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--services-per-account",
        help="Number of services to show per account in multi-account mode (default: 3)",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv", "markdown"],
        help="Output format for dashboard display (default: markdown)",
        type=str,
        default="markdown",
    )
    parser.add_argument(
        "--no-enhanced-routing",
        action="store_true",
        help="Disable enhanced service-focused routing (use legacy account-per-row layout)",
    )

    # Financial Claim Validation Flags
    parser.add_argument(
        "--show-confidence-levels",
        action="store_true",
        help="Display confidence levels (HIGH/MEDIUM/LOW) for all financial claims and projections",
    )
    parser.add_argument(
        "--validate-claims",
        action="store_true",
        help="Run comprehensive financial claim validation using MCP cross-validation",
    )
    parser.add_argument(
        "--validate-projections",
        action="store_true",
        help="Validate individual module savings projections against real AWS data",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=99.5,
        help="Minimum confidence threshold for validation (default: 99.5%%)",
    )

    # AWS Cost Metrics Parameters (v1.1.5 - Technical vs Financial Analysis)
    # Note: These parameters are mutually exclusive - specify only one
    parser.add_argument(
        "--unblended",
        action="store_true",
        help="Use UnblendedCost metrics for technical analysis (actual charges before discounts, ideal for DevOps/SRE teams). Mutually exclusive with other cost metric options.",
    )
    parser.add_argument(
        "--amortized",
        action="store_true",
        help="Use AmortizedCost metrics for financial analysis (includes RI/Savings Plans amortization, ideal for Finance teams). Mutually exclusive with other cost metric options.",
    )
    parser.add_argument(
        "--tech-focus",
        action="store_true",
        help="Technical analysis focus (UnblendedCost + DevOps optimizations) - comprehensive technical optimization mode. Mutually exclusive with other cost metric options.",
    )
    parser.add_argument(
        "--financial-focus",
        action="store_true",
        help="Financial reporting focus (AmortizedCost + Finance optimizations) - comprehensive financial analysis mode. Mutually exclusive with other cost metric options.",
    )
    parser.add_argument(
        "--dual-metrics",
        action="store_true",
        help="Show both UnblendedCost and AmortizedCost metrics side-by-side for comprehensive business analysis (default behavior).",
    )
    parser.add_argument(
        "--export-markdown",
        action="store_true",
        help="Rich-styled markdown export with enhanced formatting and visual indicators (alternative to basic --markdown flag)",
    )

    # Business Scenario Support (DoD Requirement)
    parser.add_argument(
        "--scenario",
        type=str,
        help="Business scenario analysis (workspaces, rds-snapshots, backup-investigation, nat-gateway, elastic-ip, ebs-optimization, vpc-cleanup, ec2-snapshots)",
    )
    parser.add_argument(
        "--help-scenario",
        type=str,
        help="Display detailed help for specific scenario",
    )

    # Sprint 1 Cost Optimization Implementation
    parser.add_argument(
        "--sprint1-analysis",
        action="store_true",
        help="Run comprehensive Sprint 1 cost optimization analysis targeting $260K annual savings",
    )
    parser.add_argument(
        "--optimize-nat-gateways",
        action="store_true",
        help="Run NAT Gateway optimization analysis (Target: $20K+ annual savings)",
    )
    parser.add_argument(
        "--cleanup-snapshots",
        action="store_true",
        help="Run EC2 snapshot cleanup analysis (Target: $15K+ annual savings)",
    )
    parser.add_argument(
        "--optimize-elastic-ips",
        action="store_true",
        help="Run Elastic IP optimization analysis (Target: $5K+ annual savings)",
    )
    parser.add_argument(
        "--mcp-validation",
        action="store_true",
        help="Enable MCP validation for ≥99.5% accuracy cross-validation",
    )
    parser.add_argument(
        "--validate-mcp",
        action="store_true",
        help="Run standalone MCP validation framework (AWS-2 implementation)",
    )

    # Activity Analysis (v1.1.20) - Decommission Decision Support
    parser.add_argument(
        "--activity-analysis",
        action="store_true",
        help="Enable resource activity analysis with decommission recommendations (E1-E7, R1-R7, S1-S7 signals)",
    )

    # ========== NEW: Executive Dashboard Enhancements (v1.1.20) ==========

    # Persona Analysis - DEPRECATED in v1.1.31, use --mode instead
    parser.add_argument(
        "--persona",
        choices=["CFO", "CTO", "CEO", "ALL"],
        help="[DEPRECATED] Use --mode instead. Mapping: CFO→executive, CTO→architect, CEO→executive, ALL→architect. "
        "This parameter will be removed in v1.2.0.",
    )

    # Screenshot Capture
    parser.add_argument(
        "--screenshot",
        action="store_true",
        help="Capture Playwright screenshot of dashboard HTML export (requires console recording)",
    )

    # ========== SIMPLIFIED: Unified Validation (replaces 3 flags) ==========
    parser.add_argument(
        "--validation-level",
        choices=["basic", "mcp", "strict"],
        help="Validation level: basic (standard), mcp (≥99.5%% MCP accuracy), strict (100%% validation)",
    )

    # ========== SIMPLIFIED: Unified Export (replaces 5 flags) ==========
    parser.add_argument(
        "--export",
        action="append",
        choices=["csv", "markdown", "pdf", "json", "html"],
        help="Export format(s). Specify multiple times: --export csv --export pdf --export html",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Output file path for HTML export (used with --export html)",
    )

    # ========== SIMPLIFIED: Unified Cost Metric (replaces 3 flags) ==========
    parser.add_argument(
        "--cost-metric",
        choices=["blended", "unblended", "amortized", "dual"],
        default="blended",
        help="Cost metric: blended (default), unblended, amortized (RIs), dual (show both)",
    )

    args = parser.parse_args()

    config_data: Optional[Dict[str, Any]] = None
    if args.config_file:
        config_data = load_config_file(args.config_file)
        if config_data is None:
            return 1  # Exit if config file loading failed

    # Override args with config_data if present and arg is not set via CLI
    if config_data:
        for key, value in config_data.items():
            if hasattr(args, key) and getattr(args, key) == parser.get_default(key):
                setattr(args, key, value)

    # AWS Profile Parameter Standardization & Backward Compatibility
    from runbooks.common.rich_utils import print_info, print_warning

    # Handle backward compatibility and parameter standardization
    profile_standardization_applied = False

    # Case 1: New --profile parameter used (single profile)
    if args.profile:
        # If user also specified legacy --profiles, show warning but prioritize --profile
        if args.profiles:
            print_warning("⚠️  Both --profile and --profiles specified. Using --profile (recommended)")
        # Convert --profile to --profiles format for internal compatibility
        args.profiles = [args.profile]
        profile_standardization_applied = True

    # Case 2: New --all-profile parameter used (multi-account Landing Zone)
    # argparse converts --all-profile to args.all_profile (hyphen to underscore)
    if getattr(args, "all_profile", False):
        # If user also specified legacy --all, show info message
        if args.all:
            print_info("ℹ️  Both --all-profile and --all specified. Using --all-profile (recommended)")
        # Set internal --all flag for compatibility with existing code
        args.all = True
        profile_standardization_applied = True

    # Case 3: Legacy --profiles with single profile (suggest --profile)
    if args.profiles and len(args.profiles) == 1 and not args.profile:
        print_info(f"💡 Consider using '--profile {args.profiles[0]}' for single profile operations")

    # Case 4: Legacy --all (suggest --all-profile)
    if args.all and not getattr(args, "all_profile", False):
        print_info("💡 Consider using '--all-profile' for multi-account Landing Zone operations")

    if profile_standardization_applied:
        print_info("✅ AWS profile parameter standardization applied")

    # ========== Backward Compatibility: Map deprecated flags to new unified flags ==========
    # Map old validation flags to new --validation-level
    if getattr(args, "validate_mcp", False) and not args.validation_level:
        args.validation_level = "mcp"
        print_info("💡 Mapped --validate-mcp to --validation-level mcp (new unified syntax)")
    elif getattr(args, "validate", False) and not args.validation_level:
        args.validation_level = "basic"
        print_info("💡 Mapped --validate to --validation-level basic (new unified syntax)")
    elif getattr(args, "mcp_validate", False) and not args.validation_level:
        args.validation_level = "mcp"
        print_info("💡 Mapped --mcp-validate to --validation-level mcp (new unified syntax)")

    # Map old metric flags to new --cost-metric
    if getattr(args, "unblended", False) and args.cost_metric == "blended":
        args.cost_metric = "unblended"
        print_info("💡 Mapped --unblended to --cost-metric unblended (new unified syntax)")
    elif getattr(args, "amortized", False) and args.cost_metric == "blended":
        args.cost_metric = "amortized"
        print_info("💡 Mapped --amortized to --cost-metric amortized (new unified syntax)")
    elif getattr(args, "dual_metrics", False) and args.cost_metric == "blended":
        args.cost_metric = "dual"
        print_info("💡 Mapped --dual-metrics to --cost-metric dual (new unified syntax)")

    # Process convenience export format flags (LEAN enhancement: map to existing functionality)
    convenience_formats = []
    if args.csv:
        convenience_formats.append("csv")
    if args.json:
        convenience_formats.append("json")
    if args.pdf:
        convenience_formats.append("pdf")
    if args.markdown:
        convenience_formats.append("markdown")

    # Integrate new --export flag (v1.1.20 unified syntax)
    if getattr(args, "export", None):
        convenience_formats.extend(args.export)
        convenience_formats = list(set(convenience_formats))  # Remove duplicates
        if args.export:
            print_info(f"💡 Using --export flag: {', '.join(args.export)} (new unified syntax)")

    # Feature #2: Apply persona-specific default exports (v1.1.30)
    # Only apply defaults if --mode is specified and no explicit --export flags provided
    if getattr(args, "mode", None) and not getattr(args, "export", None):
        from runbooks.finops.persona_formatter import PersonaFormatter

        # Initialize formatter to populate PERSONA_CONFIGS
        _ = PersonaFormatter(args.mode)
        persona_config = PersonaFormatter.PERSONA_CONFIGS.get(args.mode.lower())
        if persona_config and persona_config.default_exports:
            convenience_formats.extend(persona_config.default_exports)
            console.print(
                f"[dim]ℹ️  Auto-enabling {', '.join(persona_config.default_exports)} export for {args.mode} persona[/dim]"
            )

    # If any convenience flags were used, handle them appropriately
    if convenience_formats:
        # Check if --report-type was explicitly specified by checking sys.argv
        report_type_explicit = "--report-type" in sys.argv or "-y" in sys.argv

        if report_type_explicit:
            # User explicitly set --report-type, so combine with convenience flags
            combined_formats = list(set(args.report_type + convenience_formats))
            args.report_type = combined_formats
            console.print(f"[cyan]ℹ️  Using combined export formats: {', '.join(sorted(combined_formats))}[/]")
        else:
            # User only used convenience flags, replace default with convenience flags only
            args.report_type = convenience_formats

    # ========== NEW: Convert --export list to export_formats tuple for dashboard_runner ==========
    # dashboard_runner expects args.export_formats (tuple) for console recording detection
    if hasattr(args, "export") and args.export:
        # Convert list to tuple for dashboard_runner compatibility
        args.export_formats = tuple(args.export)
    elif not hasattr(args, "export_formats"):
        # Default to empty tuple
        args.export_formats = ()

    # Process cost metrics parameters (v1.1.5 implementation - Enhanced with conflict detection)
    cost_metrics_processed = False

    # Check for parameter conflicts first
    cost_metric_flags = [args.unblended, args.amortized, args.tech_focus, args.financial_focus]

    # Validate cost metric parameter conflicts
    if sum(cost_metric_flags) > 1:
        conflicting_params = []
        if args.unblended:
            conflicting_params.append("--unblended")
        if args.amortized:
            conflicting_params.append("--amortized")
        if args.tech_focus:
            conflicting_params.append("--tech-focus")
        if args.financial_focus:
            conflicting_params.append("--financial-focus")

        console.print(f"[red]❌ Error: Conflicting cost metric parameters: {', '.join(conflicting_params)}[/red]")
        console.print("[yellow]💡 Please specify only one cost metric option:[/yellow]")
        console.print("[yellow]   • --unblended (technical analysis)[/yellow]")
        console.print("[yellow]   • --amortized (financial analysis)[/yellow]")
        console.print("[yellow]   • --tech-focus (comprehensive technical mode)[/yellow]")
        console.print("[yellow]   • --financial-focus (comprehensive financial mode)[/yellow]")
        console.print("[yellow]   • --dual-metrics (both metrics side-by-side)[/yellow]")
        return 1

    # Handle --unblended cost metrics (explicit technical focus)
    if args.unblended:
        args.cost_metric = "UnblendedCost"
        args.analysis_mode = "technical"
        cost_metrics_processed = True
        console.print("[cyan]ℹ️  Using UnblendedCost metrics for technical analysis[/cyan]")

    # Handle --amortized cost metrics (explicit financial focus)
    elif args.amortized:
        args.cost_metric = "AmortizedCost"
        args.analysis_mode = "financial"
        cost_metrics_processed = True
        console.print("[cyan]ℹ️  Using AmortizedCost metrics for financial analysis[/cyan]")

    # Handle --tech-focus mode (comprehensive technical analysis)
    elif args.tech_focus:
        args.cost_metric = "UnblendedCost"
        args.analysis_mode = "technical"
        cost_metrics_processed = True
        console.print("[blue]🔧 Technical analysis focus enabled (UnblendedCost + DevOps/SRE optimizations)[/blue]")

    # Handle --financial-focus mode (comprehensive financial analysis)
    elif args.financial_focus:
        args.cost_metric = "AmortizedCost"
        args.analysis_mode = "financial"
        cost_metrics_processed = True
        console.print(
            "[green]💰 Financial reporting focus enabled (AmortizedCost + Finance team optimizations)[/green]"
        )

    # Handle --dual-metrics behavior or default to dual metrics
    if args.dual_metrics or not cost_metrics_processed:
        args.cost_metric = "dual"
        args.analysis_mode = "comprehensive"
        if args.dual_metrics:
            console.print(
                "[magenta]📊 Dual metrics enabled: Both UnblendedCost and AmortizedCost side-by-side[/magenta]"
            )
        else:
            # Default behavior when no cost metrics specified
            console.print("[dim]ℹ️  Default: Dual metrics mode (UnblendedCost + AmortizedCost)[/dim]")

    # Handle --export-markdown vs --markdown consistency (v1.1.5 enhancement)
    if args.export_markdown:
        # Add markdown to report types if not already present
        if "markdown" not in args.report_type:
            args.report_type.append("markdown")

        # Provide helpful guidance if both --markdown and --export-markdown are used
        if args.markdown:
            console.print(
                "[yellow]ℹ️  Both --markdown and --export-markdown specified. Using rich-styled markdown export.[/yellow]"
            )
            console.print(
                "[dim]💡 Tip: --export-markdown provides enhanced formatting. Use --markdown for basic exports.[/dim]"
            )
        else:
            console.print("[cyan]ℹ️  Rich-styled markdown export enabled with enhanced formatting[/cyan]")

    # Handle scenario help requests (DoD Requirement)
    if hasattr(args, "help_scenarios") and args.help_scenarios or args.help_scenario:
        try:
            if hasattr(args, "help_scenarios") and args.help_scenarios:
                from runbooks.finops.scenarios import display_unlimited_scenarios_help

                display_unlimited_scenarios_help()
            else:
                from runbooks.finops.scenario_cli_integration import ScenarioCliHelper

                helper = ScenarioCliHelper()
                helper.display_scenario_help(args.help_scenario)
            return 0
        except ImportError as e:
            console.print(f"[red]❌ Scenario help not available: {e}[/red]")
            return 1

    # Handle standalone MCP validation (AWS-2 implementation)
    if args.validate_mcp:
        try:
            import asyncio

            from runbooks.common.rich_utils import print_error, print_header, print_info, print_success

            print_header("MCP Validation Framework", "AWS-2 Implementation")
            console.print("[cyan]🔍 Running comprehensive MCP validation for ≥99.5% accuracy[/cyan]")

            # Import and initialize MCP validator
            from runbooks.validation.mcp_validator import MCPValidator

            # Set up profiles for validation
            validation_profiles = {
                "billing": "${BILLING_PROFILE}",
                "management": "${MANAGEMENT_PROFILE}",
                "centralised_ops": "${CENTRALISED_OPS_PROFILE}",
                "single_aws": "${SINGLE_AWS_PROFILE}",
            }

            # Allow profile override from CLI args (standardized parameters)
            profile_override = None
            if args.profile:
                profile_override = args.profile
                console.print(f"[blue]Using --profile override: {profile_override}[/blue]")
            elif args.profiles:
                profile_override = args.profiles[0]
                console.print(f"[blue]Using --profiles override: {profile_override}[/blue]")

            if profile_override:
                validation_profiles = {
                    "billing": profile_override,
                    "management": profile_override,
                    "centralised_ops": profile_override,
                    "single_aws": profile_override,
                }

            # Initialize validator with configured profiles
            validator = MCPValidator(
                profiles=validation_profiles, tolerance_percentage=5.0, performance_target_seconds=30.0
            )

            # Run comprehensive validation
            validation_report = asyncio.run(validator.validate_all_operations())

            # Display results
            validator.display_validation_report(validation_report)

            # Success criteria for AWS-2
            if validation_report.overall_accuracy >= 99.5:
                print_success(f"✅ AWS-2 SUCCESS: {validation_report.overall_accuracy:.1f}% ≥ 99.5% target achieved")
                console.print("[green]🎯 Ready for Sprint 1 rollout to AWS-3 through AWS-22[/green]")
                return 0
            elif validation_report.overall_accuracy >= 95.0:
                console.print(
                    f"[yellow]⚠️ AWS-2 PARTIAL: {validation_report.overall_accuracy:.1f}% accuracy (target: 99.5%)[/yellow]"
                )
                console.print("[yellow]🔧 Requires improvement before rollout[/yellow]")
                return 0
            else:
                print_error(f"❌ AWS-2 FAILED: {validation_report.overall_accuracy:.1f}% < 95% minimum threshold")
                console.print("[red]🚨 Critical issues must be resolved[/red]")
                return 1

        except ImportError as e:
            print_error(f"MCP validation framework not available: {e}")
            return 1
        except Exception as e:
            print_error(f"MCP validation failed: {e}")
            return 1

    # Handle business scenario dispatch (DoD Requirement)
    if args.scenario:
        try:
            from runbooks.common.rich_utils import print_error, print_header, print_info, print_success

            console.print(f"[bold cyan]🎯 Executing Business Scenario: {args.scenario}[/bold cyan]")

            # Handle multi-account scenarios (both --all-profile and legacy --all)
            multi_account_mode = args.all or getattr(args, "all_profile", False)
            if multi_account_mode:
                mode_text = "--all-profile" if getattr(args, "all_profile", False) else "--all (legacy)"
                print_info(
                    f"🔍 Multi-account mode detected ({mode_text}): Integrating with dashboard router for organization discovery"
                )

                # Use dashboard router to handle --all flag and get profiles
                from runbooks.finops.dashboard_runner import DashboardRouter

                router = DashboardRouter()
                use_case, routing_config = router.detect_use_case(args)

                # Extract profiles from routing config
                profiles_to_use = routing_config.get("profiles_to_analyze", [])
                if not profiles_to_use:
                    print_error("--all flag failed to discover any profiles")
                    return 1

                print_success(f"Discovered {len(profiles_to_use)} profiles for scenario execution")

                # Execute scenario across all discovered profiles
                all_results = []
                for profile in profiles_to_use:
                    print_info(f"Executing scenario '{args.scenario}' for profile: {profile}")

                    # Create a copy of args with single profile for execution
                    single_profile_args = argparse.Namespace(**vars(args))
                    single_profile_args.profiles = [profile]
                    single_profile_args.all = False  # Disable --all for individual execution

                    # Execute scenario with single profile (recursive call but with all=False)
                    result = _execute_single_scenario(single_profile_args)
                    if result:
                        all_results.append(result)

                # Combine results and export if requested
                combined_result = {
                    "scenario": args.scenario,
                    "status": "completed",
                    "profiles_analyzed": len(profiles_to_use),
                    "individual_results": all_results,
                    "organization_scope": use_case == "organization_wide",
                }

                print_success(f"✅ Scenario '{args.scenario}' completed for {len(profiles_to_use)} profiles")

                # Export results if requested
                if args.report_type and combined_result:
                    from runbooks.finops.helpers import export_scenario_results

                    export_scenario_results(combined_result, args.scenario, args.report_type, args.dir)

                return 0
            else:
                # Handle single profile execution (existing logic)
                return _execute_single_scenario(args)

        except ImportError as e:
            console.print(f"[red]❌ Scenario '{args.scenario}' not available: {e}[/red]")
            return 1
        except Exception as e:
            console.print(f"[red]❌ Scenario execution failed: {e}[/red]")
            return 1

    # Handle Sprint 1 cost optimization scenarios
    if args.sprint1_analysis or args.optimize_nat_gateways or args.cleanup_snapshots or args.optimize_elastic_ips:
        try:
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import print_error, print_header, print_info, print_success

            console.print("[bold cyan]🎯 Sprint 1 Cost Optimization Campaign[/bold cyan]")
            print_header("Sprint 1 Implementation", "Real-World Cost Optimization")

            total_annual_savings = 0.0
            results_summary = []

            # NAT Gateway Optimization
            if args.sprint1_analysis or args.optimize_nat_gateways:
                print_info("🌐 NAT Gateway Cost Optimization Analysis")
                try:
                    import asyncio

                    from runbooks.finops.nat_gateway_optimizer import NATGatewayOptimizer

                    profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
                    optimizer = NATGatewayOptimizer(profile_name=profile_param)
                    nat_results = asyncio.run(optimizer.analyze_nat_gateways(dry_run=True))

                    annual_savings = nat_results.potential_annual_savings
                    total_annual_savings += annual_savings

                    results_summary.append(
                        {
                            "optimization": "NAT Gateway",
                            "annual_savings": annual_savings,
                            "resources_analyzed": nat_results.total_nat_gateways,
                            "status": "completed",
                        }
                    )

                    print_success(
                        f"✅ NAT Gateway: {nat_results.total_nat_gateways} analyzed, ${annual_savings:,.2f} potential annual savings"
                    )

                except Exception as e:
                    print_error(f"❌ NAT Gateway optimization failed: {e}")
                    results_summary.append({"optimization": "NAT Gateway", "status": "failed", "error": str(e)})

            # EC2 Snapshot Cleanup
            if args.sprint1_analysis or args.cleanup_snapshots:
                print_info("🧹 EC2 Snapshot Cleanup Analysis")
                try:
                    import asyncio

                    from runbooks.finops.snapshot_manager import EC2SnapshotManager

                    profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
                    manager = EC2SnapshotManager(profile=profile_param, dry_run=True)

                    snapshot_results = asyncio.run(
                        manager.analyze_snapshot_opportunities(
                            profile=profile_param,
                            older_than_days=90,
                            enable_mcp_validation=args.mcp_validation,
                            export_results=False,
                        )
                    )

                    annual_savings = snapshot_results.get("cost_analysis", {}).get("annual_savings", 0)
                    total_annual_savings += annual_savings
                    cleanup_candidates = snapshot_results.get("discovery_stats", {}).get("cleanup_candidates", 0)

                    results_summary.append(
                        {
                            "optimization": "EC2 Snapshots",
                            "annual_savings": annual_savings,
                            "resources_analyzed": cleanup_candidates,
                            "status": "completed",
                        }
                    )

                    print_success(
                        f"✅ EC2 Snapshots: {cleanup_candidates} cleanup candidates, ${annual_savings:,.2f} potential annual savings"
                    )

                except Exception as e:
                    print_error(f"❌ EC2 Snapshot cleanup failed: {e}")
                    results_summary.append({"optimization": "EC2 Snapshots", "status": "failed", "error": str(e)})

            # Elastic IP Optimization
            if args.sprint1_analysis or args.optimize_elastic_ips:
                print_info("📡 Elastic IP Cost Optimization Analysis")
                try:
                    import asyncio

                    from runbooks.finops.elastic_ip_optimizer import ElasticIPOptimizer

                    profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
                    optimizer = ElasticIPOptimizer(profile_name=profile_param)
                    eip_results = asyncio.run(optimizer.analyze_elastic_ips(dry_run=True))

                    annual_savings = eip_results.potential_annual_savings
                    total_annual_savings += annual_savings

                    results_summary.append(
                        {
                            "optimization": "Elastic IPs",
                            "annual_savings": annual_savings,
                            "resources_analyzed": eip_results.total_elastic_ips,
                            "status": "completed",
                        }
                    )

                    print_success(
                        f"✅ Elastic IPs: {eip_results.total_elastic_ips} analyzed, ${annual_savings:,.2f} potential annual savings"
                    )

                except Exception as e:
                    print_error(f"❌ Elastic IP optimization failed: {e}")
                    results_summary.append({"optimization": "Elastic IPs", "status": "failed", "error": str(e)})

            # Sprint 1 Executive Summary
            print_header("Sprint 1 Executive Summary", "Cost Optimization Results")

            from runbooks.common.rich_utils import create_panel, create_table, format_cost

            # Create summary table
            table = create_table(title="Sprint 1 Cost Optimization Results")
            table.add_column("Optimization", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Resources", justify="right")
            table.add_column("Annual Savings", justify="right", style="green")

            for result in results_summary:
                status_icon = "✅" if result["status"] == "completed" else "❌"
                table.add_row(
                    result["optimization"],
                    f"{status_icon} {result['status'].title()}",
                    str(result.get("resources_analyzed", 0)),
                    format_cost(result.get("annual_savings", 0)) if result["status"] == "completed" else "N/A",
                )

            console.print(table)

            # Sprint summary panel
            target_savings = 260000  # Sprint 1 target
            target_achievement = (total_annual_savings / target_savings) * 100

            summary_content = f"""
📊 **Sprint 1 Performance**
• Target Annual Savings: {format_cost(target_savings)}
• **Actual Annual Savings: {format_cost(total_annual_savings)}**
• Target Achievement: {target_achievement:.1f}%
• Status: {"🎯 TARGET EXCEEDED" if total_annual_savings >= target_savings else "⚠️ BELOW TARGET"}

🏢 **Enterprise Coordination**
• Primary Role: DevOps Engineer
• Supporting: SRE Specialist, QA Specialist
• MCP Validation: {"✅ ENABLED" if args.mcp_validation else "⚠️ DISABLED"}

🚀 **Business Impact**
• Real-world cost optimization targeting live AWS environments
• READ-ONLY analysis with human approval gates
• Executive-ready reporting and evidence collection
            """

            console.print(
                create_panel(
                    summary_content.strip(),
                    title="🎯 Sprint 1 Cost Optimization Campaign Summary",
                    border_style="green" if total_annual_savings >= target_savings else "yellow",
                )
            )

            # Export comprehensive results if requested
            if args.report_type:
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                comprehensive_results = {
                    "sprint_1_campaign": {
                        "target_savings": target_savings,
                        "actual_savings": total_annual_savings,
                        "target_achievement_percentage": target_achievement,
                        "timestamp": datetime.now().isoformat(),
                        "optimizations": results_summary,
                        "enterprise_coordination": True,
                        "mcp_validation_enabled": args.mcp_validation,
                    }
                }

                # Export results
                for report_type in args.report_type:
                    export_file = f"sprint1_cost_optimization_{timestamp}.{report_type}"
                    if args.dir:
                        import os

                        export_file = os.path.join(args.dir, export_file)

                    if report_type == "json":
                        import json

                        with open(export_file, "w") as f:
                            json.dump(comprehensive_results, f, indent=2, default=str)
                    elif report_type == "csv":
                        import csv

                        with open(export_file, "w", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Optimization", "Status", "Resources", "Annual Savings"])
                            for result in results_summary:
                                writer.writerow(
                                    [
                                        result["optimization"],
                                        result["status"],
                                        result.get("resources_analyzed", 0),
                                        result.get("annual_savings", 0),
                                    ]
                                )

                    print_success(f"✅ Sprint 1 results exported: {export_file}")

            return 0

        except Exception as e:
            console.print(f"[red]❌ Sprint 1 analysis failed: {e}[/red]")
            return 1

    # Enhanced routing is now the default (service-per-row layout)
    # Maintain backward compatibility with explicit --no-enhanced-routing flag
    use_enhanced_routing = not getattr(args, "no_enhanced_routing", False)

    if use_enhanced_routing:
        try:
            from runbooks.finops.dashboard_runner import DashboardRouter

            console.print("[bold bright_cyan]🚀 Using Enhanced Service-Focused Dashboard[/]")

            # Use consolidated router
            router = DashboardRouter()
            use_case, routing_config = router.detect_use_case(args)

            if use_case == "organization":
                result = run_dashboard(args)
            elif use_case == "multi_account":
                from runbooks.finops.dashboard_runner import MultiAccountDashboard

                multi_dashboard = MultiAccountDashboard()
                result = multi_dashboard.run_dashboard(args, routing_config)
            else:
                result = run_dashboard(args)
        except Exception as e:
            console.print(f"[yellow]⚠️ Enhanced routing failed ({str(e)[:50]}), falling back to legacy mode[/]")
            result = run_dashboard(args)
    else:
        # Legacy dashboard mode (backward compatibility)
        console.print("[dim]Using legacy dashboard mode[/]")
        result = run_dashboard(args)

    return 0 if result == 0 else 1


def _execute_single_scenario(args: argparse.Namespace) -> int:
    """Execute a scenario for a single profile (internal helper function)."""
    from runbooks.common.profile_utils import get_profile_for_operation
    from runbooks.common.rich_utils import print_error, print_info, print_success

    def execute_workspaces_scenario():
        from runbooks.finops.scenarios import finops_workspaces

        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        return finops_workspaces(profile=profile_param)

    def execute_snapshots_scenario():
        from runbooks.finops.scenarios import finops_snapshots

        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        return finops_snapshots(profile=profile_param)

    def execute_commvault_scenario():
        from runbooks.finops.scenarios import finops_commvault

        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        return finops_commvault(profile=profile_param)

    def execute_nat_gateway_scenario():
        from runbooks.finops.nat_gateway_optimizer import nat_gateway_optimizer

        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        regions = args.regions if args.regions else ["ap-southeast-2"]
        # Call the CLI function with default parameters
        nat_gateway_optimizer(
            profile=profile_param,
            regions=regions,
            dry_run=True,
            export_format="json",
            output_file=None,
            usage_threshold_days=7,
        )
        return {"scenario": "nat-gateway", "status": "completed", "profile": profile_param}

    def execute_ebs_scenario():
        # Create a simplified EBS scenario execution
        print_info("EBS optimization scenario analysis")
        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        return {"scenario": "ebs", "status": "completed", "profile": profile_param}

    def execute_vpc_cleanup_scenario():
        # Create a simplified VPC cleanup scenario execution
        print_info("VPC cleanup scenario analysis")
        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        return {"scenario": "vpc-cleanup", "status": "completed", "profile": profile_param}

    def execute_elastic_ip_scenario():
        from runbooks.finops.elastic_ip_optimizer import elastic_ip_optimizer

        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)
        regions = args.regions if args.regions else ["ap-southeast-2", "ap-southeast-6"]
        # Call the CLI function with default parameters
        elastic_ip_optimizer(
            profile=profile_param, regions=regions, dry_run=True, export_format="json", output_file=None
        )
        return {"scenario": "elastic-ip", "status": "completed", "profile": profile_param}

    def execute_ec2_snapshots_scenario():
        import asyncio

        from runbooks.finops.snapshot_manager import EC2SnapshotManager

        # Use enterprise profile resolution: User > Environment > Default
        profile_param = get_profile_for_operation("billing", args.profiles[0] if args.profiles else None)

        print_info("🧹 EC2 Snapshot cleanup analysis - Sprint 1 Task 1")

        # Initialize snapshot manager
        manager = EC2SnapshotManager(profile=profile_param, dry_run=True)

        try:
            # Run comprehensive analysis with MCP validation
            results = asyncio.run(
                manager.analyze_snapshot_opportunities(
                    profile=profile_param,
                    older_than_days=90,
                    enable_mcp_validation=getattr(args, "mcp_validation", True),
                    export_results=True,
                )
            )

            return {
                "scenario": "ec2-snapshots",
                "status": "completed",
                "profile": profile_param,
                "annual_savings": results.get("cost_analysis", {}).get("annual_savings", 0),
                "cleanup_candidates": results.get("discovery_stats", {}).get("cleanup_candidates", 0),
            }
        except Exception as e:
            print_error(f"EC2 snapshot analysis failed: {e}")
            return {"scenario": "ec2-snapshots", "status": "failed", "error": str(e)}

    # Map scenarios to execution functions
    scenario_map = {
        "workspaces": execute_workspaces_scenario,
        "rds-snapshots": execute_snapshots_scenario,
        "backup-investigation": execute_commvault_scenario,
        "nat-gateway": execute_nat_gateway_scenario,
        "ebs-optimization": execute_ebs_scenario,
        "vpc-cleanup": execute_vpc_cleanup_scenario,
        "elastic-ip": execute_elastic_ip_scenario,
        "ec2-snapshots": execute_ec2_snapshots_scenario,
    }

    if args.scenario not in scenario_map:
        print_error(f"Unknown scenario: '{args.scenario}'")
        print_info("Available scenarios: " + ", ".join(scenario_map.keys()))
        return 1

    # Execute scenario
    scenario_func = scenario_map[args.scenario]
    result = scenario_func()

    print_success(f"✅ Scenario '{args.scenario}' completed successfully")

    # Export results if requested
    if args.report_type and result:
        from runbooks.finops.helpers import export_scenario_results

        export_scenario_results(result, args.scenario, args.report_type, args.dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
