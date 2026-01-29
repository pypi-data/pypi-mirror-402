#!/usr/bin/env python3
"""
Universal Account Discovery for Remediation Operations
=====================================================

This module provides truly universal AWS account discovery that works with ANY AWS setup:
- Single account setups
- Multi-account Organizations setups
- Mixed environments
- Any profile naming convention

Features:
- Dynamic account discovery (no hardcoded account arrays)
- Profile-based account resolution
- Environment variable configuration
- Configuration file support
- Universal compatibility across all AWS setups

Author: DevOps Security Engineer (Claude Code Enterprise Team)
Version: 1.0.0 - Universal Account Discovery
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import boto3
from botocore.exceptions import ClientError

from runbooks.common.profile_utils import get_profile_for_operation
from runbooks.common.rich_utils import console, print_error, print_info, print_warning


@dataclass
class AWSAccount:
    """Universal AWS account representation."""

    account_id: str
    account_name: Optional[str] = None
    status: str = "ACTIVE"
    email: Optional[str] = None
    joined_method: Optional[str] = None
    profile_name: Optional[str] = None


class UniversalAccountDiscovery:
    """
    Universal AWS account discovery that works with ANY AWS setup.

    Discovery methods (in priority order):
    1. Environment variables (REMEDIATION_TARGET_ACCOUNTS)
    2. Configuration file (REMEDIATION_ACCOUNT_CONFIG)
    3. AWS Organizations API (if available)
    4. Current account (single account mode)

    No hardcoded account arrays - fully dynamic discovery.
    """

    def __init__(self, profile: Optional[str] = None):
        """Initialize universal account discovery."""
        self.profile = profile
        self.resolved_profile = get_profile_for_operation("management", profile)
        self.session = self._create_session()

    def _create_session(self) -> boto3.Session:
        """Create AWS session using universal profile management."""
        return boto3.Session(profile_name=self.resolved_profile)

    def discover_target_accounts(self, include_current: bool = True) -> List[AWSAccount]:
        """
        Discover target accounts for remediation using universal approach.

        Args:
            include_current: Include current account in results

        Returns:
            List[AWSAccount]: Discovered target accounts
        """
        console.log("[cyan]🔍 Starting universal account discovery...[/]")

        discovered_accounts = []

        # Method 1: Environment variables (highest priority)
        env_accounts = self._get_accounts_from_environment()
        if env_accounts:
            console.log(f"[green]✓ Found {len(env_accounts)} accounts from environment variables[/]")
            discovered_accounts.extend(env_accounts)
            return discovered_accounts

        # Method 2: Configuration file
        config_accounts = self._get_accounts_from_config()
        if config_accounts:
            console.log(f"[green]✓ Found {len(config_accounts)} accounts from configuration file[/]")
            discovered_accounts.extend(config_accounts)
            return discovered_accounts

        # Method 3: AWS Organizations API (if available)
        org_accounts = self._get_accounts_from_organizations()
        if org_accounts:
            console.log(f"[green]✓ Found {len(org_accounts)} accounts from AWS Organizations[/]")
            discovered_accounts.extend(org_accounts)
            return discovered_accounts

        # Method 4: Current account fallback (single account mode)
        if include_current:
            current_account = self._get_current_account()
            if current_account:
                console.log("[yellow]🔍 Single account mode: Using current account[/]")
                discovered_accounts.append(current_account)

        if not discovered_accounts:
            print_warning("No target accounts discovered. Check configuration or permissions.")

        return discovered_accounts

    def _get_accounts_from_environment(self) -> List[AWSAccount]:
        """Get accounts from environment variables."""
        env_accounts = os.getenv("REMEDIATION_TARGET_ACCOUNTS")
        if not env_accounts:
            return []

        try:
            account_ids = [acc.strip() for acc in env_accounts.split(",")]
            return [
                AWSAccount(
                    account_id=account_id, account_name=f"Env-Account-{account_id}", profile_name=self.resolved_profile
                )
                for account_id in account_ids
                if account_id
            ]
        except Exception as e:
            print_warning(f"Failed to parse REMEDIATION_TARGET_ACCOUNTS: {e}")
            return []

    def _get_accounts_from_config(self) -> List[AWSAccount]:
        """Get accounts from configuration file."""
        config_path = os.getenv("REMEDIATION_ACCOUNT_CONFIG")
        if not config_path or not os.path.exists(config_path):
            return []

        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            accounts = []
            for account_config in config.get("target_accounts", []):
                account = AWSAccount(
                    account_id=account_config["account_id"],
                    account_name=account_config.get("account_name"),
                    status=account_config.get("status", "ACTIVE"),
                    email=account_config.get("email"),
                    profile_name=account_config.get("profile_name", self.resolved_profile),
                )
                accounts.append(account)

            console.log(f"[dim cyan]Loaded account configuration from: {config_path}[/]")
            return accounts

        except Exception as e:
            print_warning(f"Failed to load account configuration from {config_path}: {e}")
            return []

    def _get_accounts_from_organizations(self) -> List[AWSAccount]:
        """Get accounts from AWS Organizations API."""
        try:
            # Check if Organizations API is available
            orgs_client = self.session.client("organizations")

            # Try to list accounts
            paginator = orgs_client.get_paginator("list_accounts")
            accounts = []

            for page in paginator.paginate():
                for account in page["Accounts"]:
                    aws_account = AWSAccount(
                        account_id=account["Id"],
                        account_name=account.get("Name"),
                        status=account.get("Status", "ACTIVE"),
                        email=account.get("Email"),
                        joined_method=account.get("JoinedMethod"),
                        profile_name=self.resolved_profile,
                    )
                    accounts.append(aws_account)

            # Filter to active accounts only
            active_accounts = [acc for acc in accounts if acc.status == "ACTIVE"]
            console.log(f"[dim cyan]Discovered {len(active_accounts)} active accounts via Organizations API[/]")

            return active_accounts

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in ["AccessDenied", "AWSOrganizationsNotInUseException"]:
                console.log("[dim yellow]Organizations API not available (not in use or no permissions)[/]")
            else:
                print_warning(f"Organizations API error: {error_code}")
            return []
        except Exception as e:
            print_warning(f"Failed to access Organizations API: {e}")
            return []

    def _get_current_account(self) -> Optional[AWSAccount]:
        """Get current account as fallback."""
        try:
            sts_client = self.session.client("sts")
            identity = sts_client.get_caller_identity()

            return AWSAccount(
                account_id=identity["Account"],
                account_name=f"Current-Account-{identity['Account']}",
                status="ACTIVE",
                profile_name=self.resolved_profile,
            )

        except Exception as e:
            print_error(f"Failed to get current account identity: {e}")
            return None

    def filter_accounts_by_criteria(
        self,
        accounts: List[AWSAccount],
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_accounts: Optional[int] = None,
    ) -> List[AWSAccount]:
        """
        Filter discovered accounts by various criteria.

        Args:
            accounts: List of discovered accounts
            include_patterns: Account ID or name patterns to include
            exclude_patterns: Account ID or name patterns to exclude
            max_accounts: Maximum number of accounts to return

        Returns:
            List[AWSAccount]: Filtered accounts
        """
        filtered_accounts = accounts.copy()

        # Apply include patterns
        if include_patterns:
            filtered_accounts = [
                acc
                for acc in filtered_accounts
                if any(
                    pattern in acc.account_id or (acc.account_name and pattern in acc.account_name)
                    for pattern in include_patterns
                )
            ]

        # Apply exclude patterns
        if exclude_patterns:
            filtered_accounts = [
                acc
                for acc in filtered_accounts
                if not any(
                    pattern in acc.account_id or (acc.account_name and pattern in acc.account_name)
                    for pattern in exclude_patterns
                )
            ]

        # Apply max accounts limit
        if max_accounts and len(filtered_accounts) > max_accounts:
            console.log(f"[yellow]Limiting to {max_accounts} accounts (found {len(filtered_accounts)})[/]")
            filtered_accounts = filtered_accounts[:max_accounts]

        return filtered_accounts

    def validate_account_access(self, accounts: List[AWSAccount]) -> List[AWSAccount]:
        """
        Validate access to discovered accounts.

        Args:
            accounts: List of accounts to validate

        Returns:
            List[AWSAccount]: Accounts with validated access
        """
        validated_accounts = []

        for account in accounts:
            try:
                # Try to get caller identity to validate access
                session = boto3.Session(profile_name=account.profile_name or self.resolved_profile)
                sts_client = session.client("sts")
                identity = sts_client.get_caller_identity()

                # Verify account ID matches
                if identity["Account"] == account.account_id:
                    validated_accounts.append(account)
                    console.log(f"[green]✓ Validated access to account: {account.account_id}[/]")
                else:
                    print_warning(f"Account ID mismatch for {account.account_id}: got {identity['Account']}")

            except Exception as e:
                print_warning(f"Failed to validate access to account {account.account_id}: {e}")

        return validated_accounts

    def export_account_config_template(self, output_path: str) -> None:
        """
        Export account configuration template for enterprise customization.

        Args:
            output_path: Path to save the configuration template
        """
        template = {
            "target_accounts": [
                {
                    "account_id": "111122223333",
                    "account_name": "Production Environment",
                    "status": "ACTIVE",
                    "email": "prod@company.com",
                    "profile_name": "prod-profile",
                },
                {
                    "account_id": "444455556666",
                    "account_name": "Staging Environment",
                    "status": "ACTIVE",
                    "email": "staging@company.com",
                    "profile_name": "staging-profile",
                },
            ],
            "discovery_settings": {
                "max_concurrent_accounts": 10,
                "validation_timeout_seconds": 30,
                "include_suspended_accounts": False,
            },
        }

        try:
            with open(output_path, "w") as f:
                json.dump(template, f, indent=2)
            console.log(f"[green]Account configuration template exported to: {output_path}[/]")
        except Exception as e:
            print_error(f"Failed to export account configuration template: {e}")


def discover_remediation_accounts(profile: Optional[str] = None) -> List[AWSAccount]:
    """
    Convenience function for universal account discovery.

    Args:
        profile: AWS profile to use for discovery

    Returns:
        List[AWSAccount]: Discovered accounts for remediation
    """
    discovery = UniversalAccountDiscovery(profile=profile)
    return discovery.discover_target_accounts()


def get_account_by_id(account_id: str, profile: Optional[str] = None) -> Optional[AWSAccount]:
    """
    Get specific account by ID using universal discovery.

    Args:
        account_id: Target account ID
        profile: AWS profile to use

    Returns:
        Optional[AWSAccount]: Account if found, None otherwise
    """
    discovery = UniversalAccountDiscovery(profile=profile)
    accounts = discovery.discover_target_accounts()

    for account in accounts:
        if account.account_id == account_id:
            return account

    return None


# Export public interface
__all__ = [
    "AWSAccount",
    "UniversalAccountDiscovery",
    "discover_remediation_accounts",
    "get_account_by_id",
]
