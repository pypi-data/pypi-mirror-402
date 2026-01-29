#!/usr/bin/env python3
"""
Cloud Foundations Integration Module
Integrates proven patterns into runbooks inventory module using enterprise finops architecture

This module extracts and integrates valuable patterns while maintaining runbooks architecture:
- Enhanced multi-account session management
- Specialized service discovery capabilities
- Enterprise-grade error handling and performance
- Rich CLI integration with runbooks standards

Strategic Alignment:
- "Do one thing and do it well" - Enhance existing inventory, don't duplicate
- "Move Fast, But Not So Fast We Crash" - Proven patterns with quality validation
- Maintain 3 strategic objectives alignment
"""

from typing import Dict, List, Optional, Any, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, ProfileNotFound

# Import runbooks enterprise standards
from runbooks.common.rich_utils import (
    # Terminal control constants
    console,
    print_header,
    print_success,
    print_warning,
    print_error,
    create_table,
    create_progress_bar,
    create_panel,
)

# Terminal control constants
ERASE_LINE = "\x1b[2K"
from runbooks.common.profile_utils import get_profile_for_operation
from runbooks import __version__


@dataclass
class EnhancedAccountInfo:
    """
    Enhanced account information based on runbooks inventory account patterns
    Supports enterprise multi-account operations with session management
    """

    account_id: str
    account_name: str
    account_status: str
    account_email: str
    joined_method: str
    organizational_unit: Optional[str] = None
    account_type: str = "member"  # management, member, suspended
    session_cache: Dict[str, Any] = field(default_factory=dict)
    last_accessed: Optional[float] = None

    def __post_init__(self):
        """Initialize session cache with TTL management"""
        self.last_accessed = time.time()

    @property
    def is_session_expired(self) -> bool:
        """Check if session cache is expired (4-hour TTL)"""
        if not self.last_accessed:
            return True
        return (time.time() - self.last_accessed) > (4 * 3600)  # 4 hours TTL


class CloudFoundationsAccountManager:
    """
    Enhanced Account Manager integrating proven runbooks inventory patterns

    Key Features:
    - Multi-account organization discovery with filtering
    - 4-hour TTL session management for 60+ account operations
    - Enhanced error handling and graceful degradation
    - Rich CLI integration with runbooks standards
    - Cross-account role assumption with caching

    Enhanced from: runbooks.inventory patterns with proven finops integration
    """

    def __init__(self, profile: Optional[str] = None):
        """Initialize account manager with profile management"""
        self.profile = get_profile_for_operation("management", profile)
        self.accounts: Dict[str, EnhancedAccountInfo] = {}
        self.session_cache: Dict[str, Dict[str, Any]] = {}

        # Initialize base session
        try:
            self.base_session = boto3.Session(profile_name=self.profile)
            print_success(f"Initialized Cloud Foundations Account Manager with profile: {self.profile}")
        except ProfileNotFound as e:
            print_error(f"Profile not found: {self.profile}")
            raise

    async def discover_organization_structure(self) -> Dict[str, List[EnhancedAccountInfo]]:
        """
        Enhanced organization discovery with structure analysis

        Returns:
            Dictionary organized by organizational units with account lists

        Enhanced from: runbooks inventory organization discovery patterns with improved filtering and structure
        """
        print_header("Organization Discovery", __version__)

        try:
            with create_progress_bar() as progress:
                discovery_task = progress.add_task("Discovering organization structure...", total=100)

                # Step 1: Discover organization accounts (40%)
                accounts = await self._discover_accounts()
                progress.update(discovery_task, advance=40)

                # Step 2: Get organizational unit structure (30%)
                ou_structure = await self._discover_organizational_units()
                progress.update(discovery_task, advance=30)

                # Step 3: Map accounts to OUs (30%)
                structured_accounts = await self._map_accounts_to_ous(accounts, ou_structure)
                progress.update(discovery_task, advance=30)

            print_success(f"Discovered {len(accounts)} accounts across {len(structured_accounts)} organizational units")
            return structured_accounts

        except ClientError as e:
            print_error(f"Organization discovery failed: {e}")
            raise

    async def _discover_accounts(self) -> List[EnhancedAccountInfo]:
        """
        Discover all organization accounts with enhanced filtering
        Based on proven runbooks inventory patterns
        """
        try:
            orgs_client = self.base_session.client("organizations")
            accounts = []

            # Use paginator for large organizations (60+ accounts)
            paginator = orgs_client.get_paginator("list_accounts")

            for page in paginator.paginate():
                for account_data in page["Accounts"]:
                    # Filter active accounts only (decommissioning filter)
                    if account_data["Status"] == "ACTIVE":
                        account_info = EnhancedAccountInfo(
                            account_id=account_data["Id"],
                            account_name=account_data["Name"],
                            account_status=account_data["Status"],
                            account_email=account_data["Email"],
                            joined_method=account_data["JoinedMethod"],
                            account_type="management"
                            if account_data["Id"] == self._get_management_account_id()
                            else "member",
                        )
                        accounts.append(account_info)
                        self.accounts[account_data["Id"]] = account_info

            return accounts

        except ClientError as e:
            if e.response["Error"]["Code"] == "AWSOrganizationsNotInUseException":
                print_warning("Account is not part of an AWS Organization")
                return []
            raise

    async def _discover_organizational_units(self) -> Dict[str, Dict[str, Any]]:
        """Discover organizational unit structure"""
        try:
            orgs_client = self.base_session.client("organizations")

            # Get root and traverse OU structure
            roots = orgs_client.list_roots()["Roots"]
            ou_structure = {}

            for root in roots:
                root_id = root["Id"]
                ou_structure[root_id] = {
                    "Name": root["Name"],
                    "Type": "ROOT",
                    "Children": await self._get_ou_children(orgs_client, root_id),
                }

            return ou_structure

        except ClientError as e:
            print_warning(f"Could not discover OU structure: {e}")
            return {}

    async def _get_ou_children(self, orgs_client, parent_id: str) -> List[Dict[str, Any]]:
        """Recursively get OU children"""
        children = []

        try:
            paginator = orgs_client.get_paginator("list_organizational_units_for_parent")
            for page in paginator.paginate(ParentId=parent_id):
                for ou in page["OrganizationalUnits"]:
                    child_info = {
                        "Id": ou["Id"],
                        "Name": ou["Name"],
                        "Type": "ORGANIZATIONAL_UNIT",
                        "Children": await self._get_ou_children(orgs_client, ou["Id"]),
                    }
                    children.append(child_info)

        except ClientError as e:
            print_warning(f"Could not get children for {parent_id}: {e}")

        return children

    async def _map_accounts_to_ous(
        self, accounts: List[EnhancedAccountInfo], ou_structure: Dict[str, Dict[str, Any]]
    ) -> Dict[str, List[EnhancedAccountInfo]]:
        """Map accounts to their organizational units"""
        mapped_accounts = {}

        try:
            orgs_client = self.base_session.client("organizations")

            for account in accounts:
                try:
                    # Find which OU this account belongs to
                    parents = orgs_client.list_parents(ChildId=account.account_id)["Parents"]

                    for parent in parents:
                        parent_id = parent["Id"]
                        parent_type = parent["Type"]

                        # Create OU key for grouping
                        ou_key = f"{parent_type}:{parent_id}"
                        if ou_key not in mapped_accounts:
                            mapped_accounts[ou_key] = []

                        account.organizational_unit = parent_id
                        mapped_accounts[ou_key].append(account)

                except ClientError as e:
                    print_warning(f"Could not map account {account.account_id} to OU: {e}")
                    # Add to ungrouped accounts
                    if "ungrouped" not in mapped_accounts:
                        mapped_accounts["ungrouped"] = []
                    mapped_accounts["ungrouped"].append(account)

        except Exception as e:
            print_warning(f"Account to OU mapping encountered issues: {e}")

        return mapped_accounts

    def get_cross_account_session(
        self, target_account_id: str, role_name: str = "OrganizationAccountAccessRole"
    ) -> Optional[boto3.Session]:
        """
        Get cross-account session with enhanced caching and TTL management

        Based on runbooks inventory patterns with 4-hour TTL optimization
        """
        session_key = f"{target_account_id}_{role_name}"

        # Check session cache with TTL validation
        if session_key in self.session_cache and not self._is_session_expired(self.session_cache[session_key]):
            return self.session_cache[session_key]["session"]

        # Create new cross-account session
        try:
            sts_client = self.base_session.client("sts")
            role_arn = f"arn:aws:iam::{target_account_id}:role/{role_name}"

            response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"CloudOpsRunbooks-CF-{target_account_id}",
                DurationSeconds=14400,  # 4 hours maximum
            )

            credentials = response["Credentials"]
            cross_account_session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )

            # Cache session with TTL
            self.session_cache[session_key] = {
                "session": cross_account_session,
                "expires_at": credentials["Expiration"],
                "created_at": time.time(),
            }

            return cross_account_session

        except ClientError as e:
            if "AccessDenied" in str(e):
                print_warning(f"Cross-account access denied for {target_account_id} (role: {role_name})")
            else:
                print_warning(f"Cross-account session creation failed for {target_account_id}: {e}")
            return None

    def _is_session_expired(self, session_info: Dict[str, Any]) -> bool:
        """Check if cached session is expired"""
        if "expires_at" in session_info:
            return time.time() >= session_info["expires_at"].timestamp()
        return True

    def _get_management_account_id(self) -> Optional[str]:
        """Get the management account ID"""
        try:
            orgs_client = self.base_session.client("organizations")
            org_info = orgs_client.describe_organization()
            return org_info["Organization"]["MasterAccountId"]
        except ClientError:
            return None

    def display_organization_summary(self, structured_accounts: Dict[str, List[EnhancedAccountInfo]]):
        """
        Display organization summary with Rich CLI formatting
        Enterprise-ready visualization of multi-account structure
        """
        print_header("Organization Structure Summary", __version__)

        # Create summary table
        table = create_table(
            title="Multi-Account Organization Structure", caption=f"Discovered via profile: {self.profile}"
        )

        table.add_column("Organizational Unit", style="cyan", no_wrap=True)
        table.add_column("Account Count", justify="right", style="green")
        table.add_column("Account Types", style="blue")
        table.add_column("Status", style="yellow")

        total_accounts = 0
        management_accounts = 0
        member_accounts = 0

        for ou_key, accounts in structured_accounts.items():
            account_types = []
            active_count = 0

            for account in accounts:
                total_accounts += 1
                if account.account_type == "management":
                    management_accounts += 1
                    account_types.append("Management")
                else:
                    member_accounts += 1
                    account_types.append("Member")

                if account.account_status == "ACTIVE":
                    active_count += 1

            ou_display = ou_key.replace("ORGANIZATIONAL_UNIT:", "OU: ").replace("ROOT:", "Root: ")
            table.add_row(
                ou_display, str(len(accounts)), ", ".join(set(account_types)), f"{active_count}/{len(accounts)} Active"
            )

        console.print(table)

        # Summary panel
        summary_text = f"""
Total Accounts: {total_accounts}
Management Accounts: {management_accounts} 
Member Accounts: {member_accounts}
Organizational Units: {len(structured_accounts)}
Session Cache: {len(self.session_cache)} active sessions
        """

        from rich.panel import Panel

        summary_panel = Panel(
            summary_text.strip(), title="[bold green]Organization Summary[/bold green]", border_style="green"
        )
        console.print(summary_panel)


async def main():
    """
    Demonstration of Cloud Foundations integration
    Shows enhanced multi-account discovery capabilities
    """
    import argparse

    parser = argparse.ArgumentParser(description="Cloud Foundations Integration - Enhanced Multi-Account Discovery")
    parser.add_argument("--profile", help="AWS profile to use (defaults to management profile detection)")
    args = parser.parse_args()

    # Initialize enhanced account manager
    try:
        account_manager = CloudFoundationsAccountManager(profile=args.profile)

        # Discover organization structure
        structured_accounts = await account_manager.discover_organization_structure()

        # Display results with Rich formatting
        account_manager.display_organization_summary(structured_accounts)

        print_success("Cloud Foundations integration demonstration completed successfully")

    except Exception as e:
        print_error(f"Integration demonstration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
