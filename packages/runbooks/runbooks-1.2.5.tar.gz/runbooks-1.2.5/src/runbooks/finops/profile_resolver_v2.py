"""
Profile Resolver V2 - Intelligent Multi-Account Detection

ENTERPRISE INTEGRATION: ProfileResolverV2 for finops dashboard intelligent profile mode detection.

Design Principles:
- Explicit flags override environment variables (user control)
- Capability-based detection (Organizations API test, not name patterns)
- Graceful degradation (multi-account → single-account fallback)
- Comprehensive error messages (setup instructions with examples)
- Professional logging (Rich progress indicators, clear mode indication)

Integration Points:
- Replaces: EnterpriseRouter.detect_use_case() (dashboard_runner.py)
- Enhances: _validate_all_profile_prerequisites() (dashboard_runner.py)
- Coordinates: get_profile_for_operation() (profile_utils.py)
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import boto3
from boto3.session import Session
from botocore.exceptions import ClientError
from rich.console import Console

from runbooks.common.rich_utils import console as default_console


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================


class ProfileMode(Enum):
    """Profile resolution mode for dashboard execution."""

    SINGLE_ACCOUNT = "single_account"  # Single AWS account analysis
    MULTI_ACCOUNT = "multi_account"  # Multiple accounts via Organizations API

    def __str__(self) -> str:
        return self.value


class ProfileCapability(Enum):
    """AWS API capabilities for profile validation."""

    ORGANIZATIONS_READ = "organizations:ListAccounts"
    COST_EXPLORER_READ = "ce:GetCostAndUsage"
    EC2_READ = "ec2:DescribeInstances"


@dataclass
class ProfileValidationResult:
    """Structured validation result with actionable feedback."""

    passed: bool
    mode: ProfileMode
    profiles_used: Dict[str, str]  # {operation_type: profile_name}
    errors: List[str]
    warnings: List[str]
    setup_instructions: Optional[str] = None
    fallback_available: bool = False
    fallback_mode: Optional[ProfileMode] = None

    def __str__(self) -> str:
        """Human-readable summary for logging."""
        if self.passed:
            return f"✅ Validation passed: {self.mode} mode with {len(self.profiles_used)} profiles"
        else:
            error_summary = f"❌ Validation failed: {len(self.errors)} errors"
            if self.fallback_available:
                error_summary += f" (fallback to {self.fallback_mode} available)"
            return error_summary


@dataclass
class ProfileResolutionContext:
    """Complete context for profile resolution decision."""

    cli_flags: Dict[str, any]  # {profile, all_profile, all_accounts}
    env_vars: Dict[str, str]  # {AWS_PROFILE, MANAGEMENT_PROFILE, BILLING_PROFILE, ...}
    available_profiles: List[str]  # From ~/.aws/config
    detected_mode: ProfileMode
    validation_result: Optional[ProfileValidationResult] = None


# ============================================================================
# PROFILE RESOLVER V2 (INTELLIGENT DETECTION)
# ============================================================================


class ProfileResolverV2:
    """
    Intelligent profile resolution with fail-fast validation.

    Design Principles:
    - Explicit flags override environment variables (user control)
    - Capability-based detection (try Organizations API, not name patterns)
    - Graceful degradation (multi-account → single-account fallback)
    - Comprehensive error messages (setup instructions with examples)
    - Professional logging (Rich progress indicators, clear mode indication)

    Integration Strategy:
    - Replaces: EnterpriseRouter.detect_use_case() (dashboard_runner.py:244)
    - Enhances: _validate_all_profile_prerequisites() (dashboard_runner.py:164)
    - Coordinates: get_profile_for_operation() (profile_utils.py:94)
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or default_console
        self._capability_cache: Dict[Tuple[str, ProfileCapability], bool] = {}

    def resolve_mode(self, cli_flags: Dict[str, any], env_vars: Dict[str, str]) -> ProfileResolutionContext:
        """
        Determine single-account vs multi-account mode with intelligent detection.

        Resolution Logic:
        1. --all-profile flag → MULTI_ACCOUNT (validate prerequisites, fail fast)
        2. --profile flag → Try capability detection (Organizations API test)
           - If Organizations succeeds (>1 account) → MULTI_ACCOUNT
           - If Organizations fails or 1 account → SINGLE_ACCOUNT
        3. BILLING_PROFILE + MANAGEMENT_PROFILE ENV set → Try MULTI_ACCOUNT
           - If validation passes → MULTI_ACCOUNT
           - If validation fails → Fallback to SINGLE_ACCOUNT with warning
        4. AWS_PROFILE ENV set → SINGLE_ACCOUNT (default behavior)
        5. Default profile → SINGLE_ACCOUNT (safest default)

        Args:
            cli_flags: {profile, all_profile, all_accounts} from Click
            env_vars: {AWS_PROFILE, MANAGEMENT_PROFILE, BILLING_PROFILE, CENTRALISED_OPS_PROFILE}

        Returns:
            ProfileResolutionContext with detected_mode and validation_result
        """
        available_profiles = boto3.Session().available_profiles

        context = ProfileResolutionContext(
            cli_flags=cli_flags,
            env_vars=env_vars,
            available_profiles=available_profiles,
            detected_mode=ProfileMode.SINGLE_ACCOUNT,  # Default
        )

        # PRIORITY 1: --all-profile flag (explicit multi-account request)
        if cli_flags.get("all_profile") or cli_flags.get("all_accounts"):
            self.console.print("[cyan]🔍 Detected --all-profile flag: Multi-account mode requested[/]")
            context.detected_mode = ProfileMode.MULTI_ACCOUNT
            context.validation_result = self.validate_prerequisites(mode=ProfileMode.MULTI_ACCOUNT, context=context)

            # FAIL FAST if prerequisites not met (no silent fallback for explicit flag)
            if not context.validation_result.passed:
                self._display_validation_errors(context.validation_result)
                raise SystemExit(1)

            return context

        # PRIORITY 2: --profile flag (capability-based detection)
        if cli_flags.get("profile"):
            profile_name = cli_flags["profile"]
            self.console.print(f"[cyan]🔍 Detected --profile '{profile_name}': Testing capabilities...[/]")

            # Test Organizations API capability
            has_organizations = self._test_profile_capability(
                profile_name=profile_name, capability=ProfileCapability.ORGANIZATIONS_READ
            )

            if has_organizations:
                # Check account count (>1 account = multi-account mode)
                account_count = self._get_organization_account_count(profile_name)
                if account_count > 1:
                    self.console.print(f"[green]✅ Organizations API: {account_count} accounts discovered[/]")
                    context.detected_mode = ProfileMode.MULTI_ACCOUNT
                else:
                    self.console.print(f"[yellow]ℹ️ Organizations API: 1 account (single-account mode)[/]")
                    context.detected_mode = ProfileMode.SINGLE_ACCOUNT
            else:
                self.console.print(f"[dim]Organizations API not available: Single-account mode[/]")
                context.detected_mode = ProfileMode.SINGLE_ACCOUNT

            context.validation_result = self.validate_prerequisites(mode=context.detected_mode, context=context)
            return context

        # PRIORITY 3: Multi-account ENV vars (MANAGEMENT_PROFILE + BILLING_PROFILE)
        if env_vars.get("MANAGEMENT_PROFILE") and env_vars.get("BILLING_PROFILE"):
            self.console.print(
                "[cyan]🔍 Detected MANAGEMENT_PROFILE + BILLING_PROFILE: Attempting multi-account mode[/]"
            )
            context.detected_mode = ProfileMode.MULTI_ACCOUNT
            context.validation_result = self.validate_prerequisites(mode=ProfileMode.MULTI_ACCOUNT, context=context)

            # GRACEFUL DEGRADATION: Fallback to single-account if validation fails
            if not context.validation_result.passed:
                self.console.print("[yellow]⚠️ Multi-account validation failed, falling back to single-account mode[/]")
                context.detected_mode = ProfileMode.SINGLE_ACCOUNT
                context.validation_result = self.validate_prerequisites(
                    mode=ProfileMode.SINGLE_ACCOUNT, context=context
                )

            return context

        # PRIORITY 4: AWS_PROFILE or default profile (single-account default)
        profile_name = env_vars.get("AWS_PROFILE", "default")
        self.console.print(f"[dim]Using single-account mode with profile: {profile_name}[/]")
        context.detected_mode = ProfileMode.SINGLE_ACCOUNT
        context.validation_result = self.validate_prerequisites(mode=ProfileMode.SINGLE_ACCOUNT, context=context)

        return context

    def validate_prerequisites(self, mode: ProfileMode, context: ProfileResolutionContext) -> ProfileValidationResult:
        """
        Validate environment variables and profile capabilities for selected mode.

        Validation Requirements:

        MULTI_ACCOUNT mode:
        - MANAGEMENT_PROFILE exists in ~/.aws/config
        - MANAGEMENT_PROFILE has Organizations:ListAccounts permission
        - BILLING_PROFILE exists in ~/.aws/config
        - BILLING_PROFILE has Cost Explorer with LINKED_ACCOUNT dimension
        - (Optional) CENTRALISED_OPS_PROFILE for EC2/VPC inventory

        SINGLE_ACCOUNT mode:
        - Profile exists in ~/.aws/config (--profile or AWS_PROFILE or default)
        - Profile has Cost Explorer access (basic GetCostAndUsage)

        Args:
            mode: ProfileMode to validate
            context: ProfileResolutionContext with CLI flags and ENV vars

        Returns:
            ProfileValidationResult with passed status, errors, warnings, setup instructions
        """
        errors = []
        warnings = []
        profiles_used = {}

        if mode == ProfileMode.MULTI_ACCOUNT:
            # REQUIRED: Management profile for Organizations API
            mgmt_profile = context.env_vars.get("MANAGEMENT_PROFILE")
            if not mgmt_profile:
                errors.append(
                    "❌ MANAGEMENT_PROFILE not set (required for Organizations API)\n"
                    "   Fix: export MANAGEMENT_PROFILE='your-admin-profile-name'"
                )
            elif mgmt_profile not in context.available_profiles:
                errors.append(
                    f"❌ MANAGEMENT_PROFILE '{mgmt_profile}' not found in ~/.aws/config\n"
                    f"   Available profiles: {', '.join(context.available_profiles[:5])}"
                )
            else:
                # Test Organizations API capability
                has_orgs = self._test_profile_capability(
                    profile_name=mgmt_profile, capability=ProfileCapability.ORGANIZATIONS_READ
                )
                if not has_orgs:
                    errors.append(
                        f"❌ MANAGEMENT_PROFILE '{mgmt_profile}' lacks Organizations:ListAccounts permission\n"
                        f"   Required IAM policy: organizations:ListAccounts, organizations:DescribeOrganization"
                    )
                else:
                    profiles_used["management"] = mgmt_profile

            # REQUIRED: Billing profile for Cost Explorer
            billing_profile = context.env_vars.get("BILLING_PROFILE")
            if not billing_profile:
                errors.append(
                    "❌ BILLING_PROFILE not set (required for Cost Explorer with LINKED_ACCOUNT)\n"
                    "   Fix: export BILLING_PROFILE='your-billing-profile-name'\n"
                    "   ⚠️ Using wrong billing account could show incorrect costs (20%+ variance possible)"
                )
            elif billing_profile not in context.available_profiles:
                errors.append(
                    f"❌ BILLING_PROFILE '{billing_profile}' not found in ~/.aws/config\n"
                    f"   Available profiles: {', '.join(context.available_profiles[:5])}"
                )
            else:
                # Test Cost Explorer capability
                has_ce = self._test_profile_capability(
                    profile_name=billing_profile, capability=ProfileCapability.COST_EXPLORER_READ
                )
                if not has_ce:
                    errors.append(
                        f"❌ BILLING_PROFILE '{billing_profile}' lacks Cost Explorer access\n"
                        f"   Required IAM policy: ce:GetCostAndUsage, ce:GetCostForecast"
                    )
                else:
                    profiles_used["billing"] = billing_profile

            # OPTIONAL: Centralised ops for inventory/VPC (graceful degradation)
            ops_profile = context.env_vars.get("CENTRALISED_OPS_PROFILE")
            if not ops_profile:
                warnings.append(
                    "⚠️ CENTRALISED_OPS_PROFILE not set (EC2/VPC validation will be skipped)\n"
                    "   Optional: export CENTRALISED_OPS_PROFILE='your-ops-profile-name'"
                )
            elif ops_profile in context.available_profiles:
                profiles_used["operational"] = ops_profile

        elif mode == ProfileMode.SINGLE_ACCOUNT:
            # Determine profile from CLI flag or ENV or default
            profile_name = context.cli_flags.get("profile") or context.env_vars.get("AWS_PROFILE") or "default"

            if profile_name not in context.available_profiles:
                errors.append(
                    f"❌ Profile '{profile_name}' not found in ~/.aws/config\n"
                    f"   Available profiles: {', '.join(context.available_profiles[:10])}\n"
                    f"   Fix: Specify valid profile with --profile flag or set AWS_PROFILE"
                )
            else:
                # Test Cost Explorer capability (minimum requirement)
                has_ce = self._test_profile_capability(
                    profile_name=profile_name, capability=ProfileCapability.COST_EXPLORER_READ
                )
                if not has_ce:
                    errors.append(
                        f"❌ Profile '{profile_name}' lacks Cost Explorer access\n"
                        f"   Required IAM policy: ce:GetCostAndUsage\n"
                        f"   Verify permissions: aws ce get-cost-and-usage --profile {profile_name}"
                    )
                else:
                    profiles_used["single"] = profile_name

        # Build validation result
        passed = len(errors) == 0

        result = ProfileValidationResult(
            passed=passed,
            mode=mode,
            profiles_used=profiles_used,
            errors=errors,
            warnings=warnings,
            setup_instructions=self._generate_setup_instructions(mode, errors) if not passed else None,
            fallback_available=(mode == ProfileMode.MULTI_ACCOUNT and len(errors) > 0),
            fallback_mode=ProfileMode.SINGLE_ACCOUNT if mode == ProfileMode.MULTI_ACCOUNT else None,
        )

        return result

    def _test_profile_capability(self, profile_name: str, capability: ProfileCapability) -> bool:
        """
        Test if profile has specific AWS API capability (actual API call, not name pattern).

        Capability Tests:
        - ORGANIZATIONS_READ: Try organizations:ListAccounts (1 page, MaxResults=1)
        - COST_EXPLORER_READ: Try ce:GetCostAndUsage (MTD, no dimensions)
        - EC2_READ: Try ec2:DescribeInstances (MaxResults=1)

        Args:
            profile_name: AWS profile to test
            capability: ProfileCapability enum to check

        Returns:
            True if capability available, False otherwise (conservative on errors)

        Caching:
            Results cached per (profile, capability) tuple for session duration
        """
        cache_key = (profile_name, capability)
        if cache_key in self._capability_cache:
            return self._capability_cache[cache_key]

        try:
            session = boto3.Session(profile_name=profile_name)

            if capability == ProfileCapability.ORGANIZATIONS_READ:
                # Test Organizations API
                org_client = session.client("organizations")
                org_client.list_accounts(MaxResults=1)
                self._capability_cache[cache_key] = True
                return True

            elif capability == ProfileCapability.COST_EXPLORER_READ:
                # Test Cost Explorer API
                from datetime import datetime, timedelta

                ce_client = session.client("ce")
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)

                ce_client.get_cost_and_usage(
                    TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
                    Granularity="MONTHLY",
                    Metrics=["BlendedCost"],
                )
                self._capability_cache[cache_key] = True
                return True

            elif capability == ProfileCapability.EC2_READ:
                # Test EC2 API
                ec2_client = session.client("ec2", region_name="ap-southeast-2")
                ec2_client.describe_instances(MaxResults=1)
                self._capability_cache[cache_key] = True
                return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            # AccessDenied = lacks permission (capability not available)
            # Other errors = conservative False (don't assume capability)
            self._capability_cache[cache_key] = False
            return False
        except Exception:
            # Conservative: Unknown errors = no capability
            self._capability_cache[cache_key] = False
            return False

    def _get_organization_account_count(self, profile_name: str) -> int:
        """
        Get organization account count (for single vs multi-account detection).

        Returns 0 if Organizations API unavailable or fails.
        """
        try:
            session = boto3.Session(profile_name=profile_name)
            org_client = session.client("organizations")

            paginator = org_client.get_paginator("list_accounts")
            account_count = 0

            for page in paginator.paginate():
                account_count += len(page.get("Accounts", []))

            return account_count

        except Exception:
            return 0

    def _generate_setup_instructions(self, mode: ProfileMode, errors: List[str]) -> str:
        """
        Generate actionable setup instructions based on validation errors.

        Returns professional setup guide with copy-paste commands.
        """
        instructions = []

        instructions.append("\n[bold red]🚨 Prerequisites Not Met[/bold red]\n")
        instructions.append("[dim]Follow these steps to configure multi-account access:[/dim]\n")

        if mode == ProfileMode.MULTI_ACCOUNT:
            instructions.append("[yellow]Step 1: Configure AWS SSO profiles[/yellow]")
            instructions.append("[dim]  aws configure sso --profile admin-profile[/dim]")
            instructions.append("[dim]  aws configure sso --profile billing-profile[/dim]\n")

            instructions.append("[yellow]Step 2: Set environment variables[/yellow]")
            instructions.append("[dim]  export MANAGEMENT_PROFILE='admin-profile'[/dim]")
            instructions.append("[dim]  export BILLING_PROFILE='billing-profile'[/dim]")
            instructions.append("[dim]  export CENTRALISED_OPS_PROFILE='ops-profile'  # optional[/dim]\n")

            instructions.append("[yellow]Step 3: Verify access[/yellow]")
            instructions.append("[dim]  aws organizations list-accounts --profile admin-profile[/dim]")
            instructions.append("[dim]  aws ce get-cost-and-usage --profile billing-profile \\[/dim]")
            instructions.append("[dim]    --time-period Start=2025-11-01,End=2025-11-21 \\[/dim]")
            instructions.append("[dim]    --granularity MONTHLY --metrics BlendedCost[/dim]\n")

        instructions.append(
            "[dim]Documentation: https://github.com/1xOps/CloudOps-Runbooks/docs/multi-account-setup[/dim]"
        )

        return "\n".join(instructions)

    def _display_validation_errors(self, result: ProfileValidationResult) -> None:
        """
        Display validation errors with professional Rich formatting.

        Uses Panel for structure, color-coded messages, and actionable instructions.
        """
        self.console.print("\n[bold red]🚨 Profile Validation Failed[/bold red]\n")

        for error in result.errors:
            self.console.print(f"[red]{error}[/]")

        if result.warnings:
            self.console.print()
            for warning in result.warnings:
                self.console.print(f"[yellow]{warning}[/]")

        if result.setup_instructions:
            self.console.print(result.setup_instructions)

        self.console.print()
