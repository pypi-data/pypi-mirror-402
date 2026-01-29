"""
Dashboard Runner Facade - Backward Compatibility Layer

v1.1.29: Provides CLI import compatibility after Phase 2.3 modular extraction.
Routes to dashboard_single.py, dashboard_multi.py via dashboard_router.py.

This module provides:
- run_dashboard(args): Main entry point for CLI
- DashboardRouter: Use-case detection class
- MultiAccountDashboard: Multi-account wrapper class

Design Principles (KISS/DRY/LEAN):
- Lightweight facade (~100 lines vs 4500+ deprecated)
- Delegates to existing modular implementations
- Maintains CLI backward compatibility
- Zero code duplication
"""

import argparse
import os
from typing import Any, Dict, Optional, Tuple

from rich.console import Console

from runbooks.finops.dashboard_router import route_dashboard_command
from runbooks.finops.dashboard_single import run_single_account_dashboard
from runbooks.finops.dashboard_multi import run_multi_account_dashboard
from runbooks.finops.profile_resolver_v2 import ProfileMode, ProfileResolverV2


console = Console()


class DashboardRouter:
    """
    Backward compatibility class for dashboard routing functionality.

    Used by cli.py for intelligent use-case detection based on:
    - CLI flags (--profile vs --all-profile)
    - Environment variables (MANAGEMENT_PROFILE, BILLING_PROFILE, etc.)
    - Organizations API capability testing
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.profile_resolver = ProfileResolverV2(console=self.console)

    def detect_use_case(self, args: argparse.Namespace) -> Tuple[str, Dict[str, Any]]:
        """
        Intelligent use-case detection with ProfileResolverV2 integration.

        Args:
            args: Parsed CLI arguments namespace

        Returns:
            Tuple of (use_case: str, config: Dict) where:
            - use_case: "single_account", "multi_account", or "organization"
            - config: Routing configuration with profiles_used, routing_reason, etc.
        """
        # Build CLI flags dictionary for ProfileResolverV2
        cli_flags = {
            "profile": getattr(args, "profile", None),
            "all_profile": getattr(args, "all_profile", None),
            "all_accounts": getattr(args, "all_accounts", False) or getattr(args, "all", False),
        }

        # Build ENV vars dictionary
        env_vars = {
            "AWS_PROFILE": os.environ.get("AWS_PROFILE"),
            "MANAGEMENT_PROFILE": os.environ.get("MANAGEMENT_PROFILE"),
            "BILLING_PROFILE": os.environ.get("BILLING_PROFILE"),
            "CENTRALISED_OPS_PROFILE": os.environ.get("CENTRALISED_OPS_PROFILE"),
        }

        # Use ProfileResolverV2 for intelligent detection
        try:
            context = self.profile_resolver.resolve_mode(cli_flags, env_vars)

            # Map ProfileMode to use_case string for backward compatibility
            if context.detected_mode == ProfileMode.MULTI_ACCOUNT:
                use_case = "multi_account"
                routing_reason = "profile_resolver_v2_multi_account"
            else:
                use_case = "single_account"
                routing_reason = "profile_resolver_v2_single_account"

            # Build profiles_to_analyze list for scenario execution
            profiles_used = context.validation_result.profiles_used if context.validation_result else {}
            profiles_to_analyze = list(set(profiles_used.values())) if profiles_used else []

            config = {
                "routing_reason": routing_reason,
                "profiles_used": profiles_used,
                "profiles_to_analyze": profiles_to_analyze,
                "mode": str(context.detected_mode),
                "validation_passed": context.validation_result.passed if context.validation_result else True,
            }

            return use_case, config

        except SystemExit:
            # ProfileResolverV2 failed validation (fail-fast for explicit flags)
            raise
        except Exception as e:
            # Fallback to legacy detection if ProfileResolverV2 fails
            self.console.print(f"[yellow]⚠️ ProfileResolverV2 error: {e}[/yellow]")
            self.console.print("[dim]Falling back to legacy profile detection...[/dim]")

            # Legacy fallback logic
            if getattr(args, "all_accounts", False) or getattr(args, "all", False):
                return "organization", {"routing_reason": "explicit_all_flag", "profiles_to_analyze": []}

            if getattr(args, "all_profile", None):
                return "multi_account", {"routing_reason": "explicit_all_profile", "profiles_to_analyze": []}

            profile = getattr(args, "profile", None)
            if profile:
                return "single_account", {
                    "routing_reason": "explicit_profile",
                    "profile": profile,
                    "profiles_to_analyze": [profile],
                }

            return "single_account", {"routing_reason": "default_single", "profiles_to_analyze": []}


class MultiAccountDashboard:
    """
    Backward compatibility class for multi-account dashboard functionality.

    Used by cli.py for enterprise multi-account execution with:
    - Organizations API discovery
    - LINKED_ACCOUNT cost aggregation
    - Parallel processing across accounts
    """

    def __init__(self, console: Optional[Console] = None, max_concurrent_accounts: int = 15, context: str = "cli"):
        self.console = console or Console()
        self.max_concurrent_accounts = max_concurrent_accounts
        self.context = context

    def run_dashboard(self, args: argparse.Namespace, config: Dict[str, Any]) -> int:
        """
        Execute multi-account dashboard via run_dashboard().

        Args:
            args: Parsed CLI arguments namespace
            config: Routing configuration from DashboardRouter.detect_use_case()

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        return run_dashboard(args)


def run_dashboard(args: argparse.Namespace) -> int:
    """
    Main dashboard entry point - routes to appropriate implementation.

    This function provides CLI backward compatibility by:
    1. Detecting mode from args (--profile vs --all-profile)
    2. Extracting relevant parameters from args namespace
    3. Routing to dashboard_single or dashboard_multi

    Args:
        args: Parsed CLI arguments namespace with:
            - profile: Single AWS profile
            - all_profile: Multi-account mode flag/profile
            - timeframe: Cost aggregation period
            - top_n: Number of top items to display
            - activity_analysis: Enable resource activity signals
            - export: Export formats list
            - output_file: Export file path
            - dry_run: Dry run mode flag

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    try:
        # Extract common parameters from args
        profile = getattr(args, "profile", None)
        all_profile = getattr(args, "all_profile", None)
        timeframe = getattr(args, "timeframe", "monthly")
        month = getattr(args, "month", None)  # v1.2.2: Specific month (YYYY-MM format)
        top_n = getattr(args, "top_n", getattr(args, "top_services", 10))
        activity_analysis = getattr(args, "activity_analysis", False)
        dry_run = getattr(args, "dry_run", False)
        export_formats = getattr(args, "export", None) or getattr(args, "export_formats", None)
        cost_threshold = getattr(args, "cost_threshold", 1.0)
        output_file = getattr(args, "output_file", None)  # v1.1.30: HTML export support
        mode = getattr(args, "mode", "architect")  # v1.1.30: Dashboard mode (executive/architect/sre)

        # Build kwargs for dashboard functions
        dashboard_kwargs = {
            "timeframe": timeframe,
            "month": month,  # v1.2.2: Specific month support (YYYY-MM format)
            "top_n": top_n,
            "activity_analysis": activity_analysis,
            "dry_run": dry_run,
            "cost_threshold": cost_threshold,
        }

        if export_formats:
            dashboard_kwargs["export_formats"] = (
                list(export_formats) if not isinstance(export_formats, list) else export_formats
            )

        # v1.1.30: Pass HTML export parameters for multi-account dashboard
        if output_file:
            dashboard_kwargs["output_file"] = output_file
        if mode:
            dashboard_kwargs["mode"] = mode

        # Route to appropriate dashboard using dashboard_router
        result = route_dashboard_command(
            profile=profile,
            all_profile=all_profile
            if isinstance(all_profile, str)
            else (os.environ.get("MANAGEMENT_PROFILE") if all_profile else None),
            billing_profile=os.environ.get("BILLING_PROFILE"),
            ops_profile=os.environ.get("CENTRALISED_OPS_PROFILE"),
            **dashboard_kwargs,
        )

        # Check result for success
        if isinstance(result, dict):
            success = result.get("success", True)
            if not success:
                error = result.get("error", "Unknown error")
                console.print(f"[red]❌ Dashboard failed: {error}[/]")
                return 1
            return 0
        elif isinstance(result, int):
            return result
        else:
            return 0

    except Exception as e:
        console.print(f"[red]❌ Dashboard error: {e}[/]")
        return 1


# Export backward compatibility functions
def create_dashboard_router(console: Optional[Console] = None) -> DashboardRouter:
    """Backward compatibility function to create DashboardRouter."""
    return DashboardRouter(console)


def route_finops_request(args: argparse.Namespace) -> int:
    """Backward compatibility function that routes to run_dashboard."""
    return run_dashboard(args)
