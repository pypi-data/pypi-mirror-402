"""
Dashboard Routing Logic - Profile Mode Detection

Phase 2.3 Implementation: CLI routing extraction
Reduces CLI layer from 69 lines to single function call (96% reduction)

Architecture:
- Detects --profile vs --all-profile mode
- Routes to dashboard_single or dashboard_multi
- Handles profile environment variable fallback
- Clean separation of concerns (routing vs implementation)

Usage:
    from runbooks.finops.dashboard_router import route_dashboard_command

    result = route_dashboard_command(
        profile="aws-profile",
        all_profile=None,
        billing_profile="billing-profile",
        ops_profile="ops-profile",
        **dashboard_kwargs
    )
"""

import os
from typing import Any, Dict, Optional


def route_dashboard_command(
    profile: Optional[str] = None,
    all_profile: Optional[str] = None,
    billing_profile: Optional[str] = None,
    ops_profile: Optional[str] = None,
    **dashboard_kwargs,
) -> Dict[str, Any]:
    """
    Route dashboard command to appropriate implementation based on mode.

    Args:
        profile: Single AWS profile (--profile mode)
        all_profile: Management account profile (--all-profile mode)
        billing_profile: Billing account profile (multi-account mode)
        ops_profile: Operational account profile (multi-account mode)
        **dashboard_kwargs: Additional dashboard parameters (timeframe, top_n, etc.)

    Returns:
        Dashboard result dictionary with success status and metrics

    Mode Detection:
        - If all_profile provided → Multi-account mode (Organizations API)
        - If profile provided → Single-account mode
        - If neither → Single-account mode with AWS_PROFILE environment variable

    Environment Variable Fallback:
        Multi-account mode uses environment variables for specialized profiles:
        - MANAGEMENT_PROFILE → Management account (Organizations API)
        - BILLING_PROFILE → Billing account (Cost Explorer)
        - CENTRALISED_OPS_PROFILE → Operational account (Resource APIs)
    """

    if all_profile:
        # Multi-account mode: Organizations API discovery
        from runbooks.finops.dashboard_multi import run_multi_account_dashboard

        # Environment variable fallback for specialized profiles
        management_profile = os.getenv("MANAGEMENT_PROFILE", all_profile)
        effective_billing_profile = billing_profile or os.getenv("BILLING_PROFILE", all_profile)
        effective_ops_profile = ops_profile or os.getenv("CENTRALISED_OPS_PROFILE", all_profile)

        return run_multi_account_dashboard(
            management_profile=management_profile,
            billing_profile=effective_billing_profile,
            centralised_ops_profile=effective_ops_profile,
            **dashboard_kwargs,
        )

    else:
        # Single-account mode: Account-level resource discovery
        from runbooks.finops.dashboard_single import run_single_account_dashboard

        # Default to AWS_PROFILE environment variable if --profile not specified
        effective_profile = profile or os.getenv("AWS_PROFILE", "default")

        return run_single_account_dashboard(profile=effective_profile, **dashboard_kwargs)
