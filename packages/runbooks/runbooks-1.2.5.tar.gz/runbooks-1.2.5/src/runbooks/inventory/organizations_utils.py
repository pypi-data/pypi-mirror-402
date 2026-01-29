#!/usr/bin/env python3
"""
Organizations Utility Functions for Phase 2 Multi-Profile Pattern.

This module provides simplified utility functions for the 5 Organizations scripts
implementing the Group-Level with --all-profiles pattern (Option B).

Features:
    - Simple profile discovery via Organizations API
    - Account-to-profile mapping with fallback
    - Graceful error handling and single-profile fallback
    - Configuration-driven mappings

Architecture Decision: Phase 2 Multi-Profile Pattern (Option B)
    Reference: artifacts/decisions/phase-2-multi-profile-pattern.md

Scripts using this module:
    1. list_org_accounts.py
    2. list_org_accounts_users.py
    3. check_controltower_readiness.py
    4. check_landingzone_readiness.py
    5. find_landingzone_versions.py

Author: Runbooks Team
Version: 1.1.10
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from runbooks.common.config_loader import get_config_loader

logger = logging.getLogger(__name__)


class SimpleProfileMapper:
    """
    Simple account ID to profile name mapper with 3-tier fallback.

    Priority:
    1. User configuration (~/.aws/runbooks/account_mappings.json)
    2. AWS SSO configuration (~/.aws/config)
    3. Fallback: Use account ID as profile name
    """

    def __init__(self):
        """Initialize profile mapper with configuration loading."""
        self.config_path = Path.home() / ".aws" / "runbooks" / "account_mappings.json"
        self.mappings = self._load_mappings()

    def resolve_profile(self, account_id: str, account_name: Optional[str] = None) -> str:
        """
        Resolve account ID to profile name using multiple strategies.

        Args:
            account_id: AWS account ID (12-digit)
            account_name: Optional account name for logging

        Returns:
            Profile name string
        """
        # Strategy 1: User configuration
        if account_id in self.mappings:
            profile = self.mappings[account_id]
            logger.debug(f"Resolved {account_id} → {profile} (user config)")
            return profile

        # Strategy 2: AWS SSO configuration
        sso_profile = self._parse_sso_config(account_id)
        if sso_profile:
            logger.debug(f"Resolved {account_id} → {sso_profile} (SSO config)")
            return sso_profile

        # Strategy 3: Fallback to account ID
        logger.debug(f"Resolved {account_id} → {account_id} (fallback)")
        return account_id

    def _load_mappings(self) -> dict:
        """Load user-defined account mappings from JSON config."""
        if not self.config_path.exists():
            logger.debug(f"No user config found at {self.config_path}")
            return {}

        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)

            # Filter out comment keys (starting with _)
            mappings = {k: v for k, v in data.items() if not k.startswith("_")}

            logger.debug(f"Loaded {len(mappings)} account mappings from {self.config_path}")
            return mappings

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load account mappings: {e}")
            return {}

    def _parse_sso_config(self, account_id: str) -> Optional[str]:
        """Parse AWS SSO configuration for account mapping."""
        config_path = Path.home() / ".aws" / "config"

        if not config_path.exists():
            return None

        try:
            with open(config_path, "r") as f:
                current_profile = None

                for line in f:
                    line = line.strip()

                    # Parse profile headers: [profile profile-name]
                    if line.startswith("[profile "):
                        current_profile = line[9:-1].strip()
                    elif line.startswith("["):
                        current_profile = None

                    # Check for sso_account_id match
                    if current_profile and line.startswith("sso_account_id"):
                        config_account_id = line.split("=")[1].strip()
                        if config_account_id == account_id:
                            return current_profile

        except Exception as e:
            logger.debug(f"Failed to parse SSO config: {e}")

        return None


def discover_organization_accounts(
    management_profile: str, region: str = "ap-southeast-2"
) -> Tuple[List[Dict], Optional[str]]:
    """
    Discover ACTIVE accounts via Organizations API with graceful fallback.

    This function implements the Group-Level with --all-profiles pattern,
    discovering accounts via the Organizations API when available, or
    falling back to single-profile mode when Organizations permissions
    are unavailable.

    Args:
        management_profile: AWS profile with Organizations API permissions
        region: AWS region (Organizations is global, defaults to ap-southeast-2)

    Returns:
        Tuple of (accounts_list, error_message):
            - accounts_list: List of account dictionaries with keys:
                - id: Account ID (12-digit)
                - name: Account name
                - email: Account email
                - profile: Mapped profile name
                - status: Account status (ACTIVE, SUSPENDED, PENDING_CLOSURE)
                - joined_method: Provisioning method (INVITED, CREATED, UNKNOWN)
                - joined_timestamp: Account creation/join date
            - error_message: Error message if discovery failed, None if successful

    Example:
        accounts, error = discover_organization_accounts("my-mgmt-profile")
        if error:
            print(f"Fallback mode: {error}")
        for account in accounts:
            print(f"{account['id']}: {account['name']} → {account['profile']}")
    """
    profile_mapper = SimpleProfileMapper()

    try:
        # Initialize Organizations client
        session = boto3.Session(profile_name=management_profile, region_name=region)
        org_client = session.client("organizations")

        print_info(f"Discovering accounts via Organizations API (profile: {management_profile})")

        # Use paginator for large organizations
        paginator = org_client.get_paginator("list_accounts")
        page_iterator = paginator.paginate()

        accounts = []
        account_count = 0

        # Get organization details to identify management account
        try:
            org_details = org_client.describe_organization()
            mgmt_account_id = org_details["Organization"]["MasterAccountId"]
        except Exception as e:
            logger.warning(f"Could not retrieve organization details: {e}")
            mgmt_account_id = None

        for page in page_iterator:
            for account in page["Accounts"]:
                # Filter ACTIVE accounts only
                if account["Status"] != "ACTIVE":
                    logger.debug(f"Skipping account {account['Id']} with status {account['Status']}")
                    continue

                # Map account ID to profile name
                profile_name = profile_mapper.resolve_profile(account["Id"], account.get("Name"))

                # Determine if this is the management account
                is_mgmt = mgmt_account_id and account["Id"] == mgmt_account_id

                account_data = {
                    "id": account["Id"],
                    "name": account.get("Name", ""),
                    "email": account.get("Email", ""),
                    "profile": profile_name,
                    "status": account["Status"],
                    "is_management_account": is_mgmt,
                    "parent_org": mgmt_account_id if mgmt_account_id else account["Id"],
                    # Phase 0 Manager Correction: Add JoinedMethod and JoinedTimestamp
                    "joined_method": account.get("JoinedMethod", "UNKNOWN"),
                    "joined_timestamp": account.get("JoinedTimestamp", "N/A"),
                }

                # ENHANCEMENT: Add tag enrichment (v1.1.10 Tags-First)
                account_data = enhance_account_with_tags(account_data, org_client, logger)

                accounts.append(account_data)
                account_count += 1

        print_success(f"Discovered {account_count} ACTIVE accounts via Organizations API")
        return accounts, None

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "AccessDeniedException":
            return _handle_access_denied_fallback(management_profile, region, profile_mapper)
        else:
            error_msg = f"Organizations API error: {error_code}"
            print_error(error_msg)
            return _handle_generic_fallback(management_profile, region, profile_mapper, error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during Organizations discovery: {str(e)}"
        logger.error(error_msg)
        return _handle_generic_fallback(management_profile, region, profile_mapper, error_msg)


def _handle_access_denied_fallback(
    management_profile: str, region: str, profile_mapper: SimpleProfileMapper
) -> Tuple[List[Dict], str]:
    """Handle AccessDeniedException with fallback to single profile."""
    print_warning("Organizations API Access Denied - fallback to single profile mode")

    console.print("\n[yellow]Required IAM Permissions:[/yellow]")
    console.print(
        """
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "organizations:ListAccounts",
      "organizations:DescribeOrganization"
    ],
    "Resource": "*"
  }]
}
    """
    )

    console.print("\n[dim]Fallback: Using single profile mode[/dim]\n")

    return _create_single_account_fallback(management_profile, region, profile_mapper)


def _handle_generic_fallback(
    management_profile: str, region: str, profile_mapper: SimpleProfileMapper, error_msg: str
) -> Tuple[List[Dict], str]:
    """Handle generic errors with fallback to single profile."""
    print_warning(f"Organizations discovery failed: {error_msg}")
    print_info("Falling back to single profile mode")

    return _create_single_account_fallback(management_profile, region, profile_mapper)


def enhance_account_with_tags(
    account_data: Dict[str, Any],
    org_client: boto3.client,
    logger: logging.Logger,
    tag_mappings: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Enhance account metadata with AWS Tags (TIER 1-4).

    Implements Tags-First strategy: All enhanced metadata sourced from
    AWS account tags via organizations:ListTagsForResource API.

    Args:
        account_data: Existing account dictionary with baseline 9 columns
        org_client: boto3 Organizations client with ListTagsForResource permission
        logger: Logger for error tracking and debugging
        tag_mappings: Optional dict mapping field names to AWS tag keys.
                     If None, uses ConfigLoader with hierarchical precedence:
                     1. User config (~/.runbooks/config.yaml)
                     2. Project config (./.runbooks.yaml)
                     3. Environment variables (RUNBOOKS_TAG_*)
                     4. Defaults (WBS, CostGroup, TechnicalLead, etc.)

    Returns:
        Enhanced account dictionary with 14+ columns (baseline + TIER 1-4 tags)

    Tag Schema (TIER 1-4 Classification):
        TIER 1 - Critical Business Metadata (4 tags):
            - WBS (Work Breakdown Structure code for cost allocation)
            - CostGroup (Cost center assignment)
            - TechnicalLead (Primary technical owner email)
            - AccountOwner (Business owner email)

        TIER 2 - Governance Metadata (4 tags):
            - BusinessUnit (Organizational business unit)
            - FunctionalArea (Functional domain: DevOps, Security, etc.)
            - ManagedBy (Management service: Control Tower, manual, etc.)
            - ProductOwner (Product ownership email)

        TIER 3 - Operational Metadata (4 tags):
            - Purpose (Account purpose description)
            - Environment (Environment classification: prod, dev, test, etc.)
            - ComplianceScope (Regulatory compliance requirements)
            - DataClassification (Data sensitivity classification)

        TIER 4 - Extended Metadata (5 tags, optional):
            - ProjectName (Project or application name)
            - BudgetCode (Budget allocation code)
            - SupportTier (Support level: 24x7, business hours, etc.)
            - CreatedDate (Account creation date)
            - ExpiryDate (Account expiration date for temporary accounts)

        Computed Fields:
            - all_tags (Complete tag dictionary - raw AWS tags)
            - wbs_comparison (WBS vs cht-wbs consistency validation)

    Error Handling:
        - AccessDeniedException: Graceful fallback with 'N/A' values
        - API throttling: Exponential backoff retry (boto3 default)
        - Missing tags: Default to 'N/A' for missing keys
        - Any exception: Log error, return account with 'N/A' values

    Example:
        >>> # Use default hierarchical config loading
        >>> account = {"id": "123456789012", "name": "Production"}
        >>> enhanced = enhance_account_with_tags(account, org_client, logger)
        >>> enhanced["wbs_code"]
        'WBS-12345'

        >>> # Explicit tag mapping override (testing/advanced use)
        >>> custom_mappings = {'wbs_code': 'ProjectCode', 'cost_group': 'BillingGroup'}
        >>> enhanced = enhance_account_with_tags(account, org_client, logger, custom_mappings)
        >>> enhanced["wbs_code"]
        'PROJECT-789'
    """
    account_id = account_data.get("id", "unknown")

    # Load tag mappings with hierarchical precedence (if not provided)
    if tag_mappings is None:
        config_loader = get_config_loader()
        tag_mappings = config_loader.load_tag_mappings()
        logger.debug(f"Loaded tag mappings from: {', '.join(config_loader.get_config_sources())}")

    try:
        # Fetch tags from AWS Organizations API
        tags_response = org_client.list_tags_for_resource(ResourceId=account_id)
        tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("Tags", [])}

        logger.debug(f"Retrieved {len(tags)} tags for account {account_id}")

        # Map AWS tags to account fields using configured mappings
        # TIER 1: Business Metadata
        account_data["wbs_code"] = tags.get(tag_mappings.get("wbs_code"), "N/A")
        account_data["cost_group"] = tags.get(tag_mappings.get("cost_group"), "N/A")
        account_data["technical_lead"] = tags.get(tag_mappings.get("technical_lead"), "N/A")
        account_data["account_owner"] = tags.get(tag_mappings.get("account_owner"), "N/A")

        # TIER 2: Governance Metadata
        account_data["business_unit"] = tags.get(tag_mappings.get("business_unit"), "N/A")
        account_data["functional_area"] = tags.get(tag_mappings.get("functional_area"), "N/A")
        account_data["managed_by"] = tags.get(tag_mappings.get("managed_by"), "N/A")
        account_data["product_owner"] = tags.get(tag_mappings.get("product_owner"), "N/A")

        # TIER 3: Operational Metadata
        account_data["purpose"] = tags.get(tag_mappings.get("purpose"), "N/A")
        account_data["environment"] = tags.get(tag_mappings.get("environment"), "N/A")
        account_data["compliance_scope"] = tags.get(tag_mappings.get("compliance_scope"), "N/A")
        account_data["data_classification"] = tags.get(tag_mappings.get("data_classification"), "N/A")

        # TIER 4: Extended Metadata (if configured)
        if "project_name" in tag_mappings:
            account_data["project_name"] = tags.get(tag_mappings.get("project_name"), "N/A")
        if "budget_code" in tag_mappings:
            account_data["budget_code"] = tags.get(tag_mappings.get("budget_code"), "N/A")
        if "support_tier" in tag_mappings:
            account_data["support_tier"] = tags.get(tag_mappings.get("support_tier"), "N/A")
        if "created_date" in tag_mappings:
            account_data["created_date"] = tags.get(tag_mappings.get("created_date"), "N/A")
        if "expiry_date" in tag_mappings:
            account_data["expiry_date"] = tags.get(tag_mappings.get("expiry_date"), "N/A")

        # === NEW: Generate tags_combined field for business analysis ===
        # Format: "Key1=Value1 | Key2=Value2 | ..." (human-readable)
        # Include TIER 1-4 tags, skip empty/N/A values for clean display
        tags_list = []

        # Define tag order (TIER 1 → TIER 2 → TIER 3 → TIER 4 for consistency)
        tier_order = [
            # TIER 1 - Critical Business Metadata (always first)
            "WBS",
            "CostGroup",
            "TechnicalLead",
            "AccountOwner",
            # TIER 2 - Governance Metadata
            "BusinessUnit",
            "FunctionalArea",
            "ManagedBy",
            "ProductOwner",
            # TIER 3 - Operational Metadata
            "Purpose",
            "Environment",
            "ComplianceScope",
            "DataClassification",
            # TIER 4 - Extended Metadata (optional)
            "ProjectName",
            "BudgetCode",
            "SupportTier",
            "CreatedDate",
            "ExpiryDate",
        ]

        # Build tags list in priority order
        for key in tier_order:
            if key in tags:
                value = tags[key]
                # Skip empty, N/A, or None values (clean display)
                if value and value != "N/A" and value.strip():
                    tags_list.append(f"{key}={value}")

        # Add any additional tags not in tier_order (preserve all AWS tags)
        for key, value in tags.items():
            if key not in tier_order:
                if value and value != "N/A" and value.strip():
                    tags_list.append(f"{key}={value}")

        # Join with " | " delimiter (space-pipe-space for readability)
        account_data["tags_combined"] = " | ".join(tags_list) if tags_list else ""

        # Keep existing all_tags and wbs_comparison logic
        account_data["all_tags"] = tags

        # WBS comparison (if both tags exist)
        wbs_value = tags.get(tag_mappings.get("wbs_code"), "N/A")
        cht_wbs_value = tags.get("cht-wbs", "N/A")
        account_data["wbs_comparison"] = {
            "wbs": wbs_value,
            "cht_wbs": cht_wbs_value,
            "match": wbs_value == cht_wbs_value if wbs_value != "N/A" and cht_wbs_value != "N/A" else False,
        }

        return account_data

    except org_client.exceptions.AccessDeniedException:
        logger.warning(f"AccessDenied for ListTagsForResource on account {account_id}")
        # Graceful fallback: Return account with N/A values for all tag fields
        return _add_na_tag_fields(account_data)

    except Exception as e:
        logger.error(f"Failed to fetch tags for account {account_id}: {e}", exc_info=True)
        # Same graceful fallback for any unexpected error
        return _add_na_tag_fields(account_data)


def _add_na_tag_fields(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """Helper: Add N/A values for all tag-based fields."""
    account_data.update(
        {
            # TIER 1: Business Metadata
            "wbs_code": "N/A",
            "cost_group": "N/A",
            "technical_lead": "N/A",
            "account_owner": "N/A",
            # TIER 2: Governance Metadata
            "business_unit": "N/A",
            "functional_area": "N/A",
            "managed_by": "N/A",
            "product_owner": "N/A",
            # TIER 3: Operational Metadata
            "purpose": "N/A",
            "environment": "N/A",
            "compliance_scope": "N/A",
            "data_classification": "N/A",
            # TIER 4: Extended Metadata
            "project_name": "N/A",
            "budget_code": "N/A",
            "support_tier": "N/A",
            "created_date": "N/A",
            "expiry_date": "N/A",
            # Computed fields
            "all_tags": {},
            "tags_combined": "",  # Empty string for no tags (not "N/A")
            "wbs_comparison": {"wbs": "N/A", "cht_wbs": "N/A", "match": False},
        }
    )
    return account_data


def _create_single_account_fallback(
    management_profile: str, region: str, profile_mapper: SimpleProfileMapper
) -> Tuple[List[Dict], str]:
    """Create single account fallback entry."""
    try:
        # Get account ID from STS for the current profile
        session = boto3.Session(profile_name=management_profile, region_name=region)
        sts_client = session.client("sts")
        account_id = sts_client.get_caller_identity()["Account"]

        # Resolve profile name (may be different from management_profile)
        profile_name = profile_mapper.resolve_profile(account_id)

        fallback_account = {
            "id": account_id,
            "name": "Single Account (Fallback)",
            "email": "N/A",
            "profile": profile_name,
            "status": "ACTIVE",
            "is_management_account": False,
            "parent_org": account_id,
            "is_standalone": True,
            # Phase 0 Manager Correction: Consistent field structure
            "joined_method": "UNKNOWN",
            "joined_timestamp": "N/A",
        }

        print_info(f"Single profile mode: {management_profile} → Account {account_id}")

        error_msg = "Organizations API unavailable - using single profile mode"
        return [fallback_account], error_msg

    except Exception as e:
        logger.error(f"Fallback failed: {e}")
        print_error("Failed to retrieve account information for fallback mode")
        error_msg = f"Complete failure: {str(e)}"
        return [], error_msg


def create_account_mappings_template() -> None:
    """
    Create template account_mappings.json if it doesn't exist.

    Creates ~/.aws/runbooks/ directory and account_mappings.json template
    with documentation for user configuration.
    """
    config_dir = Path.home() / ".aws" / "runbooks"
    config_file = config_dir / "account_mappings.json"

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Don't overwrite existing config
    if config_file.exists():
        logger.debug(f"Account mappings config already exists: {config_file}")
        return

    # Create template
    template = {
        "_comment": "AWS Account ID to Profile Name Mappings",
        "_instructions": "Add your account mappings below. Format: 'account-id': 'profile-name'",
        "_example_1": "Replace these examples with your actual account mappings",
        "_example_2": "Remove lines starting with _ before using",
        "123456789012": "production",
        "234567890123": "staging",
        "345678901234": "development",
        "456789012345": "sandbox",
    }

    try:
        with open(config_file, "w") as f:
            json.dump(template, f, indent=2)

        print_success(f"Created account mappings template: {config_file}")
        console.print("\n[dim]Edit this file to configure account-to-profile mappings[/dim]\n")

    except Exception as e:
        logger.error(f"Failed to create account mappings template: {e}")


# Initialize configuration template on module import
def _initialize_config():
    """Initialize configuration template on module load."""
    try:
        create_account_mappings_template()
    except Exception as e:
        logger.debug(f"Config template initialization skipped: {e}")


# Run initialization
_initialize_config()
