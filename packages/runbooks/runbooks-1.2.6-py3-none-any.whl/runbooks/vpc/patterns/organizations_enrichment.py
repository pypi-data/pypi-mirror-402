#!/usr/bin/env python3
"""
Organizations Enrichment Pattern - AWS Organizations Account Metadata

Base class for enriching resource analysis with AWS Organizations account metadata.

Design Pattern:
    - Abstract base class requiring _get_resources_by_account() implementation
    - Provides account metadata enrichment (names, emails, tags, OU paths)
    - Graceful fallback if Organizations API unavailable
    - Multi-account support with per-account enrichment

Reusability:
    - VPCE Cleanup Manager (current implementation)
    - VPC Cleanup (future enhancement)
    - NAT Gateway Optimizer (future enhancement)
    - Any multi-account resource analysis

Usage:
    class MyManager(OrganizationsEnricher):
        def _get_resources_by_account(self):
            return self.account_summaries  # Dict[str, AccountSummary]

    manager = MyManager()
    result = manager.enrich_with_organizations_api(
        management_profile="org-management-readonly"
    )
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from rich.tree import Tree

from runbooks.common.rich_utils import (
    console,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)


@dataclass
class OrganizationEnrichmentResult:
    """Result from Organizations API enrichment operation."""

    enriched_count: int
    accounts_with_org_data: int
    account_names: Dict[str, str] = field(default_factory=dict)  # account_id → name
    account_emails: Dict[str, str] = field(default_factory=dict)  # account_id → email
    account_tags: Dict[str, Dict[str, str]] = field(default_factory=dict)  # account_id → tags
    organizational_units: Dict[str, str] = field(default_factory=dict)  # account_id → OU path
    errors: List[str] = field(default_factory=list)  # Error messages


class OrganizationsEnricher(ABC):
    """
    Base class for AWS Organizations enrichment operations.

    Provides reusable methods for:
    - Retrieving account metadata (names, emails, tags)
    - Fetching organizational unit (OU) hierarchy paths
    - Graceful fallback when Organizations API unavailable
    - Multi-account enrichment with error isolation

    Subclass Requirements:
        - Implement _get_resources_by_account() → Dict[account_id, AccountSummary]
        - AccountSummary must have: endpoints (List) or resources (List)

    Profile Priority Cascade:
        1. Explicit management_profile parameter
        2. $MANAGEMENT_PROFILE environment variable
        3. $AWS_PROFILE environment variable
        4. Error (no default - Organizations requires explicit profile)
    """

    @abstractmethod
    def _get_resources_by_account(self) -> Dict:
        """
        Return resources grouped by account for enrichment.

        Returns:
            Dict[account_id: str, AccountSummary] where AccountSummary has:
                - endpoints: List[Endpoint] or resources: List[Resource]
                - Additional resource-specific fields
        """
        pass

    def enrich_with_organizations_api(
        self,
        management_profile: Optional[str] = None,
        include_tags: bool = True,
        include_ou_paths: bool = True,
    ) -> OrganizationEnrichmentResult:
        """
        Enrich resources with AWS Organizations metadata.

        Args:
            management_profile: AWS profile for Organizations management account
                              Priority: param > $MANAGEMENT_PROFILE > $AWS_PROFILE > error
            include_tags: Fetch account tags (default: True)
            include_ou_paths: Fetch organizational unit paths (default: True)

        Returns:
            OrganizationEnrichmentResult with enrichment statistics

        Example:
            >>> result = manager.enrich_with_organizations_api()
            >>> # ✅ Enriched 88 endpoints across 4 accounts
            >>> # Account names: Production (38), Development (23), ...
        """
        # Priority cascade: param > MANAGEMENT_PROFILE > AWS_PROFILE > error
        profile_source = "parameter"
        if management_profile is None:
            management_profile = os.getenv("MANAGEMENT_PROFILE")
            if management_profile:
                profile_source = "MANAGEMENT_PROFILE env"
            else:
                management_profile = os.getenv("AWS_PROFILE")
                if management_profile:
                    profile_source = "AWS_PROFILE env"
                else:
                    raise ValueError(
                        "Organizations enrichment requires management_profile parameter "
                        "or $MANAGEMENT_PROFILE environment variable"
                    )

        try:
            session = boto3.Session(profile_name=management_profile)
            orgs_client = session.client("organizations")

            # Get resources by account
            resources_by_account = self._get_resources_by_account()
            account_ids = list(resources_by_account.keys())

            if not account_ids:
                print_warning("⚠️  No accounts to enrich (resources_by_account is empty)")
                return OrganizationEnrichmentResult(
                    enriched_count=0,
                    accounts_with_org_data=0,
                )

            # Initialize result containers
            account_names = {}
            account_emails = {}
            account_tags = {}
            organizational_units = {}
            errors = []

            # Enrich each account
            for account_id in account_ids:
                try:
                    # Get account details
                    account_response = orgs_client.describe_account(AccountId=account_id)
                    account = account_response.get("Account", {})

                    # Extract basic metadata
                    account_name = account.get("Name", account_id)
                    account_email = account.get("Email", "")

                    account_names[account_id] = account_name
                    account_emails[account_id] = account_email

                    # Fetch account tags if requested
                    if include_tags:
                        try:
                            tags_response = orgs_client.list_tags_for_resource(ResourceId=account_id)
                            tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("Tags", [])}
                            account_tags[account_id] = tags
                        except ClientError as e:
                            errors.append(f"Failed to fetch tags for {account_id}: {e.response['Error']['Code']}")
                            account_tags[account_id] = {}

                    # Fetch OU path if requested
                    if include_ou_paths:
                        ou_path = self._get_account_ou_path(orgs_client, account_id, errors)
                        organizational_units[account_id] = ou_path

                except ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    if error_code == "AccountNotFoundException":
                        errors.append(f"Account {account_id} not found in organization")
                    else:
                        errors.append(f"Failed to describe account {account_id}: {error_code}")
                except Exception as e:
                    errors.append(f"Unexpected error for account {account_id}: {str(e)}")

            # Count successfully enriched resources
            enriched_count = 0
            for account_id, summary in resources_by_account.items():
                if account_id in account_names:
                    # Determine resource count
                    if hasattr(summary, "endpoint_count"):
                        enriched_count += summary.endpoint_count
                    elif hasattr(summary, "endpoints"):
                        enriched_count += len(summary.endpoints)
                    elif hasattr(summary, "resources"):
                        enriched_count += len(summary.resources)

            print_success(
                f"✅ Enriched {enriched_count} resources across {len(account_names)} accounts with Organizations metadata"
            )

            # Display Rich table with account metadata
            if account_names:
                self._display_organizations_table(
                    account_names,
                    account_emails,
                    organizational_units,
                    account_tags,
                    resources_by_account,
                )

                # Display Rich Tree with account hierarchy and tags (Manager feedback #1)
                print_info("\n🌳 Account Hierarchy Tree View:")
                self._display_organizations_tree(account_names, account_tags, resources_by_account)

            if errors:
                print_warning(f"⚠️  {len(errors)} enrichment errors (non-blocking)")

            return OrganizationEnrichmentResult(
                enriched_count=enriched_count,
                accounts_with_org_data=len(account_names),
                account_names=account_names,
                account_emails=account_emails,
                account_tags=account_tags,
                organizational_units=organizational_units,
                errors=errors,
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "AccessDeniedException":
                print_error(f"❌ Access denied to Organizations API (profile: {management_profile})")
                print_warning("⚠️  Ensure profile has organizations:Describe* permissions")
            else:
                print_error(f"❌ Organizations API error: {error_code}")

            return OrganizationEnrichmentResult(
                enriched_count=0,
                accounts_with_org_data=0,
                errors=[f"Organizations API failed: {error_code}"],
            )

        except Exception as e:
            print_error(f"❌ Failed to enrich with Organizations data: {e}")
            print_warning("⚠️  Falling back to account IDs only")

            return OrganizationEnrichmentResult(
                enriched_count=0,
                accounts_with_org_data=0,
                errors=[f"Unexpected error: {str(e)}"],
            )

    def _get_account_ou_path(self, orgs_client, account_id: str, errors: List[str]) -> str:
        """
        Get organizational unit path for account (e.g., 'Root/Production/Workloads').

        Args:
            orgs_client: Boto3 Organizations client
            account_id: AWS account ID
            errors: List to append errors to

        Returns:
            OU path string (e.g., 'Root/Production/Workloads') or 'Root' if at root
        """
        try:
            # Get parent chain for account
            parents_response = orgs_client.list_parents(ChildId=account_id)
            parents = parents_response.get("Parents", [])

            if not parents:
                return "Root"

            # Build OU path by traversing up the hierarchy
            ou_path_parts = []
            current_parent = parents[0]  # Accounts have exactly one parent

            while current_parent["Type"] == "ORGANIZATIONAL_UNIT":
                # Get OU details
                ou_response = orgs_client.describe_organizational_unit(OrganizationalUnitId=current_parent["Id"])
                ou = ou_response.get("OrganizationalUnit", {})
                ou_name = ou.get("Name", current_parent["Id"])

                ou_path_parts.insert(0, ou_name)

                # Get next parent
                parents_response = orgs_client.list_parents(ChildId=current_parent["Id"])
                parents = parents_response.get("Parents", [])

                if not parents:
                    break

                current_parent = parents[0]

            # Prepend 'Root'
            ou_path_parts.insert(0, "Root")

            return "/".join(ou_path_parts)

        except ClientError as e:
            errors.append(f"Failed to get OU path for {account_id}: {e.response['Error']['Code']}")
            return "Root"
        except Exception as e:
            errors.append(f"Unexpected error getting OU path for {account_id}: {str(e)}")
            return "Root"

    def _display_organizations_table(
        self,
        account_names: Dict[str, str],
        account_emails: Dict[str, str],
        organizational_units: Dict[str, str],
        account_tags: Dict[str, Dict[str, str]],
        resources_by_account: Dict,
    ) -> None:
        """
        Display Rich table with AWS Organizations enrichment results.

        Finops parity: Rich PyPI table by default (matches elastic_ip_optimizer.py pattern)
        """
        table = create_table(title="AWS Organizations Enrichment Results")
        table.add_column("Account ID", style="cyan", no_wrap=True)
        table.add_column("Account Name", style="green")
        table.add_column("Email", style="dim")
        table.add_column("OU Path", style="blue")
        table.add_column("Tags", style="yellow", justify="right")
        table.add_column("Resources", style="magenta", justify="right")

        # Sort by account name for readability
        sorted_accounts = sorted(account_names.items(), key=lambda x: x[1])

        for account_id, account_name in sorted_accounts:
            email = account_emails.get(account_id, "N/A")
            ou_path = organizational_units.get(account_id, "Root")
            tags = account_tags.get(account_id, {})
            tag_count = len(tags)

            # Count resources for this account
            resource_count = 0
            if account_id in resources_by_account:
                summary = resources_by_account[account_id]
                if hasattr(summary, "endpoint_count"):
                    resource_count = summary.endpoint_count
                elif hasattr(summary, "endpoints"):
                    resource_count = len(summary.endpoints)
                elif hasattr(summary, "resources"):
                    resource_count = len(summary.resources)

            table.add_row(
                account_id,
                account_name,
                email,
                ou_path,
                f"{tag_count} tags",
                str(resource_count),
            )

        console.print(table)

    def _display_organizations_tree(
        self,
        account_names: Dict[str, str],
        account_tags: Dict[str, Dict[str, str]],
        resources_by_account: Dict,
    ) -> None:
        """
        Display Rich Tree with AWS Organizations account hierarchy and tags.

        Manager feedback: Show (Account ID + Account Name) with tags (Key-Value pairs)
        Pattern: Root → Accounts → Tags → Resources

        Args:
            account_names: Dict[account_id, account_name]
            account_tags: Dict[account_id, Dict[tag_key, tag_value]]
            resources_by_account: Dict[account_id, AccountSummary]
        """
        tree = Tree("🌳 AWS Organization Account Hierarchy", guide_style="bold cyan")

        # Sort accounts by name for readability
        sorted_accounts = sorted(account_names.items(), key=lambda x: x[1])

        for account_id, account_name in sorted_accounts:
            # Account branch: "Account ID (Account Name)"
            account_label = f"[cyan]{account_id}[/cyan] ([green]{account_name}[/green])"
            account_branch = tree.add(account_label)

            # Add tags as Key: Value pairs
            tags = account_tags.get(account_id, {})
            if tags:
                tags_branch = account_branch.add("[yellow]Tags:[/yellow]")
                for key, value in sorted(tags.items()):
                    tags_branch.add(f"[dim]{key}:[/dim] [white]{value}[/white]")
            else:
                account_branch.add("[dim]No tags[/dim]")

            # Add resource count
            resource_count = 0
            if account_id in resources_by_account:
                summary = resources_by_account[account_id]
                if hasattr(summary, "endpoint_count"):
                    resource_count = summary.endpoint_count
                elif hasattr(summary, "endpoints"):
                    resource_count = len(summary.endpoints)
                elif hasattr(summary, "resources"):
                    resource_count = len(summary.resources)

            if resource_count > 0:
                account_branch.add(f"[magenta]Resources:[/magenta] {resource_count} endpoints")

        console.print(tree)
