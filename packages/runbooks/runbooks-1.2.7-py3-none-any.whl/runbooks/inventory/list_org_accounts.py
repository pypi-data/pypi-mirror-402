#!/usr/bin/env python3
"""
AWS Organizations Account Inventory

A comprehensive AWS Organizations account discovery tool that provides detailed visibility
into multi-account structures across all accessible Management Accounts. Supports account
status analysis, organizational hierarchy mapping, and cross-organization account lookup.

**AWS API Mapping**: `organizations.list_accounts()`, `organizations.describe_organization()`

Features:
    - Multi-organization account discovery via --all-profiles pattern
    - Management Account identification and validation
    - Account status tracking (ACTIVE, SUSPENDED, etc.)
    - Cross-organization account lookup by ID
    - Multi-format export (JSON, CSV, Markdown, Table)
    - Short-form and detailed organizational views
    - Root profile discovery and listing
    - Account hierarchy visualization

Architecture (v1.1.10):
    - Group-level with --all-profiles pattern (Option B)
    - Shared utilities integration (organizations_utils.py + output_formatters.py)
    - Modern CLI + Legacy Python Main dual compatibility
    - Rich CLI output with enterprise UX standards

Compatibility:
    - AWS Organizations with cross-account roles
    - AWS Control Tower managed accounts
    - Multiple AWS Organizations access
    - AWS Account Factory provisioned accounts
    - Single-account fallback for non-Organizations environments

Example (Modern CLI):
    Multi-account Organizations discovery:
    ```bash
    runbooks inventory --all-profiles $MANAGEMENT_PROFILE list-org-accounts
    ```

    Brief listing with timing:
    ```bash
    runbooks inventory --profile mgmt list-org-accounts --short --timing
    ```

    Find specific accounts across organizations:
    ```bash
    runbooks inventory --all-profiles mgmt list-org-accounts --acct 123456789012 987654321098
    ```

Example (Legacy Python Main):
    ```bash
    python src/runbooks/inventory/list_org_accounts.py --profile my-org-profile
    python src/runbooks/inventory/list_org_accounts.py --profile my-profile --short
    python src/runbooks/inventory/list_org_accounts.py --acct 123456789012 987654321098
    python src/runbooks/inventory/list_org_accounts.py --rootonly
    ```

Use Cases:
    - AWS Organizations discovery and mapping
    - Account governance and compliance auditing
    - Cross-organization account tracking
    - Management Account validation
    - Account migration planning

Requirements:
    - IAM permissions: `organizations:ListAccounts`, `organizations:DescribeOrganization`
    - AWS Organizations access (Management Account or delegated admin)
    - Python 3.8+ with required dependencies

Author:
    AWS Cloud Foundations Team

Version:
    1.1.10 (v1.1.10 parameter patterns + shared utilities)
"""

import logging
import sys
import json
from os.path import split
from time import time
from typing import Dict, List, Optional

from runbooks.inventory.ArgumentsClass import CommonArguments
from runbooks.inventory.organizations_utils import discover_organization_accounts
from runbooks.inventory.output_formatters import OrganizationsFormatter, export_to_file
from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_table,
)
from runbooks.common.config_loader import get_config_loader
from runbooks import __version__

logger = logging.getLogger(__name__)

begin_time = time()


##################
# Core Functions
##################
def list_organization_accounts(
    profiles: List[str],
    short_form: bool = False,
    root_only: bool = False,
    account_lookup: Optional[List[str]] = None,
    export_format: str = "table",
    output_file: Optional[str] = None,
    skip_profiles: Optional[List[str]] = None,
    verbose: int = logging.ERROR,
) -> Dict:
    """
    List all accounts in AWS Organizations with multi-profile support.

    This function serves both Modern CLI and legacy Python Main modes,
    implementing the Group-Level with --all-profiles pattern (Option B).

    Args:
        profiles: List of AWS profiles to query (Organizations management accounts)
        short_form: Show only profile-level info, skip child accounts (performance optimization)
        root_only: Show only management accounts (governance focus)
        account_lookup: Specific account IDs to find across organizations (cross-org search)
        export_format: Output format (json, csv, markdown, table)
        output_file: Output filename (None = console only)
        skip_profiles: Profiles to exclude from discovery
        verbose: Logging level (logging.ERROR, WARNING, INFO, DEBUG)

    Returns:
        Dictionary containing:
            - OrgsFound: List of management account IDs discovered
            - AccountList: Complete account inventory with metadata
            - ClosedAccounts: Suspended/closed account IDs
            - FailedProfiles: Profiles that failed authentication/access
            - StandAloneAccounts: Non-organizational standalone accounts

    Architecture:
        - Uses organizations_utils.discover_organization_accounts() for AWS API integration
        - Uses output_formatters.OrganizationsFormatter() for multi-format export
        - Graceful fallback to single-account mode when Organizations unavailable
        - Profile-level caching to avoid redundant API calls
    """
    # Configure logging
    logger.setLevel(verbose)

    # Print header
    print_header("Organizations Account Inventory", __version__)

    # Filter profiles
    active_profiles = [p for p in profiles if not skip_profiles or p not in skip_profiles]

    if skip_profiles:
        excluded_count = len(profiles) - len(active_profiles)
        print_info(f"Excluding {excluded_count} profile(s): {', '.join(skip_profiles)}")

    print_info(f"Scanning {len(active_profiles)} profile(s) for Organizations membership")

    # Account discovery across profiles
    all_accounts = []
    orgs_found = set()
    failed_profiles = []
    profile_errors = {}

    for profile in active_profiles:
        try:
            logger.info(f"Discovering accounts for profile: {profile}")

            # Use shared utility for Organizations API discovery
            accounts, error_msg = discover_organization_accounts(profile, region="ap-southeast-2")

            if error_msg:
                # Fallback mode - single account
                logger.warning(f"Profile {profile} fallback mode: {error_msg}")
                profile_errors[profile] = error_msg

            if accounts:
                # Track management accounts
                mgmt_accounts = [acc for acc in accounts if acc.get("is_management_account", False)]
                for mgmt_acc in mgmt_accounts:
                    orgs_found.add(mgmt_acc["id"])

                # Add profile metadata to each account
                for account in accounts:
                    account["discovery_profile"] = profile

                all_accounts.extend(accounts)
                print_success(f"Profile '{profile}': {len(accounts)} accounts discovered")
            else:
                failed_profiles.append(profile)
                print_error(f"Profile '{profile}': Discovery failed")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Profile {profile} failed: {error_msg}", exc_info=True)
            failed_profiles.append(profile)
            profile_errors[profile] = error_msg
            print_error(f"Profile '{profile}': {error_msg}")

    # Summary statistics
    console.print()
    console.print("[cyan]📊 Discovery Summary:[/cyan]")
    console.print(f"Organizations found: {len(orgs_found)}")
    console.print(f"Total accounts: {len(all_accounts)}")

    # Status breakdown
    active_count = sum(1 for acc in all_accounts if acc.get("status") == "ACTIVE")
    suspended_count = sum(1 for acc in all_accounts if acc.get("status") == "SUSPENDED")
    closed_count = sum(1 for acc in all_accounts if acc.get("status") == "CLOSED")

    console.print(f"  - Active: {active_count}")
    if suspended_count > 0:
        console.print(f"  - Suspended: {suspended_count}")
    if closed_count > 0:
        console.print(f"  - Closed: {closed_count}")

    if failed_profiles:
        console.print(f"[yellow]Failed profiles: {len(failed_profiles)}[/yellow]")
    console.print()

    # Apply filters
    if root_only:
        all_accounts = [acc for acc in all_accounts if acc.get("is_management_account", False)]
        print_info(f"Root-only filter: {len(all_accounts)} management accounts")

    # Account lookup (cross-organization search)
    if account_lookup:
        found_accounts = [acc for acc in all_accounts if acc["id"] in account_lookup]

        console.print("[cyan]🔍 Account Lookup Results:[/cyan]")
        if found_accounts:
            for acc in found_accounts:
                org_id = acc.get("parent_org", "N/A")
                console.print(
                    f"  Account: [bold]{acc['id']}[/bold] | "
                    f"Name: {acc.get('name', 'N/A')} | "
                    f"Org: {org_id} | "
                    f"Status: {acc['status']} | "
                    f"Profile: {acc.get('profile', 'N/A')}"
                )
        else:
            console.print(f"[yellow]  No accounts found matching IDs: {', '.join(account_lookup)}[/yellow]")
        console.print()

    # Output formatting
    formatter = OrganizationsFormatter()

    if export_format == "table":
        # Rich table for console display
        table = formatter.format_accounts_table(all_accounts, title="AWS Organization Accounts")
        console.print(table)

    elif export_format == "json":
        # JSON export with metadata
        output_filename = output_file or "organizations_accounts.json"
        metadata = {
            "organizations_count": len(orgs_found),
            "total_accounts": len(all_accounts),
            "discovery_profiles": active_profiles,
            "failed_profiles": failed_profiles,
        }
        formatter.export_json(all_accounts, output_filename, metadata=metadata)

    elif export_format == "csv":
        # CSV export
        output_filename = output_file or "organizations_accounts.csv"
        formatter.export_csv(all_accounts, output_filename)

    elif export_format == "markdown":
        # Markdown export
        output_filename = output_file or "organizations_accounts.md"
        formatter.export_markdown(all_accounts, output_filename, title="AWS Organization Accounts")

    # Closed/suspended account tracking
    closed_accounts = [acc["id"] for acc in all_accounts if acc["status"] != "ACTIVE"]

    # Standalone account detection (accounts with no parent org)
    standalone_accounts = [
        acc["id"] for acc in all_accounts if acc.get("email") == "N/A" and acc.get("id") == acc.get("parent_org")
    ]

    return {
        "OrgsFound": list(orgs_found),
        "AccountList": all_accounts,
        "ClosedAccounts": closed_accounts,
        "FailedProfiles": failed_profiles,
        "StandAloneAccounts": standalone_accounts,
        "ProfileErrors": profile_errors,
    }


##################
# Legacy Python Main Entry Point
##################
def parse_args(f_arguments):
    """
    Parse and validate command-line arguments for AWS Organizations account discovery.

    Configures the argument parser with Organizations-specific options including
    profile management, output formatting, and account lookup capabilities.
    Uses the standardized CommonArguments framework for consistency.

    Args:
        f_arguments (list): Command-line arguments to parse (typically sys.argv[1:])

    Returns:
        argparse.Namespace: Parsed arguments containing:
            - Profiles: AWS profiles for multi-organization access
            - RootOnly: Flag to display only Management Accounts
            - pShortform: Brief output format (profiles only, not child accounts)
            - accountList: Specific account IDs to lookup across organizations
            - SkipProfiles: Profiles to exclude from discovery
            - Filename: Output file prefix for export
            - Time: Enable execution timing measurements
            - Other standard framework arguments

    Script-Specific Arguments:
        --short/-s/-q: Enables brief output showing only profile-level information
                      without detailed child account enumeration. Improves performance
                      for large organizations where only high-level view is needed.

        --acct/-A: Cross-organization account lookup feature. Accepts multiple
                  account IDs and determines which organization each belongs to.
                  Essential for account governance and migration planning.

    Use Cases:
        - Quick organization overview: --short for high-level visibility
        - Account location discovery: --acct 123456789012 to find parent org
        - Management account audit: --rootonly for governance review
        - Comprehensive inventory: default mode for complete account listing
    """
    script_path, script_name = split(sys.argv[0])
    parser = CommonArguments()

    # Enable multi-profile support for cross-organization discovery
    parser.multiprofile()

    # Add extended arguments (skip accounts, skip profiles, etc.)
    parser.extendedargs()

    # Enable root-only filtering for Management Account focus
    parser.rootOnly()

    # Add execution timing capabilities
    parser.timing()

    # Enable file export functionality
    parser.save_to_file()

    # Configure logging verbosity levels
    parser.verbosity()

    # Set script version for --version flag
    parser.version(__version__)

    # Add script-specific argument group
    local = parser.my_parser.add_argument_group(script_name, "Parameters specific to this script")

    # Short-form display option for performance and readability
    local.add_argument(
        "-s",
        "-q",
        "--short",
        help="Display only brief listing of the profile accounts, and not the Child Accounts under them",
        action="store_const",
        dest="pShortform",
        const=True,
        default=False,
    )

    # Cross-organization account lookup capability
    local.add_argument(
        "-A", "--acct", help="Find which Org this account is a part of", nargs="*", dest="accountList", default=None
    )

    # Tag mappings configuration (v1.1.10 config-aware feature)
    local.add_argument(
        "--tag-mappings",
        type=str,
        default=None,
        dest="tagMappings",
        help="JSON string mapping field names to AWS tag keys. "
        'Example: \'{"wbs_code": "ProjectCode", "cost_group": "BillingGroup"}\'. '
        "Overrides hierarchical config (user/project/env defaults).",
    )

    return parser.my_parser.parse_args(f_arguments)


##################
# Main
##################
if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    # Extract arguments
    pProfiles = args.Profiles
    pRootOnly = args.RootOnly
    pTiming = args.Time
    pSkipProfiles = args.SkipProfiles
    verbose = args.loglevel
    pSaveFilename = args.Filename
    pShortform = args.pShortform
    pAccountList = args.accountList
    pTagMappings = args.tagMappings

    # Configure logging
    logging.basicConfig(level=verbose, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

    # Suppress AWS SDK noise unless in DEBUG mode
    if verbose > logging.DEBUG:
        for logger_name in ["boto3", "botocore", "s3transfer", "urllib3"]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)

    # Parse CLI tag mappings (if provided)
    cli_tag_overrides = None
    if pTagMappings:
        try:
            cli_tag_overrides = json.loads(pTagMappings)
            logger.info(f"Using CLI tag mapping overrides: {cli_tag_overrides}")
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in --tag-mappings: {e}[/red]")
            console.print(
                '[yellow]Example: --tag-mappings \'{"wbs_code": "ProjectCode", "cost_group": "BillingGroup"}\'[/yellow]'
            )
            sys.exit(1)

    # Load tag mappings with hierarchical precedence
    config_loader = get_config_loader()
    final_tag_mappings = config_loader.load_tag_mappings(cli_overrides=cli_tag_overrides)

    # Display configuration sources
    config_sources = config_loader.get_config_sources()
    if verbose <= logging.INFO:
        print_info(f"Tag mapping sources: {' → '.join(config_sources)}")
        logger.info(f"Loaded {len(final_tag_mappings)} tag mappings from {len(config_sources)} sources")

    # Determine export format based on filename
    export_format = "table"
    if pSaveFilename:
        if pSaveFilename.endswith(".json"):
            export_format = "json"
        elif pSaveFilename.endswith(".csv"):
            export_format = "csv"
        elif pSaveFilename.endswith(".md"):
            export_format = "markdown"
        else:
            # Default to CSV if no extension provided
            export_format = "csv"
            pSaveFilename = f"{pSaveFilename}.csv"

    # Execute discovery
    results = list_organization_accounts(
        profiles=pProfiles,
        short_form=pShortform,
        root_only=pRootOnly,
        account_lookup=pAccountList,
        export_format=export_format,
        output_file=pSaveFilename,
        skip_profiles=pSkipProfiles,
        verbose=verbose,
    )

    # Timing summary
    if pTiming:
        elapsed = time() - begin_time
        console.print(f"\n[green]⏱️  Execution time: {elapsed:.2f}s[/green]")

    console.print("\n[dim]Thanks for using this script[/dim]\n")
