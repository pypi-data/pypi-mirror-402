#!/usr/bin/env python3
"""
Unified Organizations API Client for Runbooks Platform

This module consolidates Organizations API patterns from inventory, finops, and vpc modules
into a unified, cached, high-performance client following enterprise standards.

Features:
- Global caching with 30-minute TTL (extracted from inventory module)
- 4-profile enterprise architecture support
- Rich CLI integration with progress indicators
- Comprehensive error handling and graceful degradation
- Performance optimization for 61-account enterprise scale
- Thread-safe operations with concurrent access support

Author: Runbooks Team
Version: latest version
"""

import asyncio
import functools
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from runbooks.common.profile_utils import create_management_session, get_profile_for_operation
from runbooks.common.rich_utils import (
    console,
    create_progress_bar,
    print_error,
    print_info,
    print_success,
    print_warning,
)

# Global Organizations cache shared across all instances and modules
_GLOBAL_ORGS_CACHE = {
    "data": None,
    "accounts": None,
    "organizational_units": None,
    "timestamp": None,
    "ttl_minutes": 30,
}

# Thread lock for cache operations
import threading

_cache_lock = threading.Lock()


@dataclass
class OrganizationAccount:
    """Standard organization account representation across all modules"""

    account_id: str
    name: str
    email: str
    status: str
    joined_method: str
    joined_timestamp: Optional[datetime] = None
    parent_id: Optional[str] = None
    organizational_unit: Optional[str] = None
    tags: Dict[str, str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for compatibility with existing modules"""
        return asdict(self)


@dataclass
class OrganizationalUnit:
    """Standard organizational unit representation"""

    ou_id: str
    name: str
    parent_id: Optional[str] = None
    accounts: List[str] = None
    child_ous: List[str] = None

    def __post_init__(self):
        if self.accounts is None:
            self.accounts = []
        if self.child_ous is None:
            self.child_ous = []


class UnifiedOrganizationsClient:
    """
    Unified Organizations API client consolidating patterns from all modules.

    This client provides a single interface for Organizations API operations
    with global caching, error handling, and performance optimization.
    """

    def __init__(self, management_profile: Optional[str] = None, cache_ttl_minutes: int = 30, max_workers: int = 50):
        """
        Initialize unified Organizations client.

        Args:
            management_profile: AWS profile with Organizations access
            cache_ttl_minutes: Cache TTL in minutes (default: 30)
            max_workers: Maximum workers for parallel operations
        """
        self.management_profile = management_profile
        self.cache_ttl_minutes = cache_ttl_minutes
        self.max_workers = max_workers

        # Initialize session
        self.session = None
        self.client = None

        # Performance metrics
        self.metrics = {
            "api_calls_made": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors_encountered": 0,
            "last_refresh": None,
        }

    def _initialize_client(self) -> bool:
        """Initialize Organizations client with error handling"""
        try:
            if self.management_profile:
                self.session = create_management_session(self.management_profile)
            else:
                # Use profile resolution from existing patterns
                profile = get_profile_for_operation("management", None)
                self.session = boto3.Session(profile_name=profile)

            # Organizations is a global service - always use ap-southeast-2
            self.client = self.session.client("organizations", region_name="ap-southeast-2")

            # Test connectivity
            self.client.describe_organization()
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDeniedException":
                print_warning(f"Organizations access denied for profile '{self.management_profile}'")
            elif error_code == "AWSOrganizationsNotInUseException":
                print_info("AWS Organizations not enabled for this account")
            else:
                print_warning(f"Organizations API error: {error_code}")
            return False

        except NoCredentialsError:
            print_warning("AWS credentials not available for Organizations API")
            return False

        except Exception as e:
            print_error(f"Failed to initialize Organizations client: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """Check if global cache is still valid"""
        with _cache_lock:
            if not _GLOBAL_ORGS_CACHE["timestamp"]:
                return False

            cache_age_minutes = (datetime.now(timezone.utc) - _GLOBAL_ORGS_CACHE["timestamp"]).total_seconds() / 60

            return cache_age_minutes < self.cache_ttl_minutes

    def _get_cached_data(self, data_type: str) -> Optional[any]:
        """Get specific cached data type"""
        if self._is_cache_valid():
            with _cache_lock:
                self.metrics["cache_hits"] += 1
                if data_type == "accounts":
                    return _GLOBAL_ORGS_CACHE.get("accounts")
                elif data_type == "organizational_units":
                    return _GLOBAL_ORGS_CACHE.get("organizational_units")
                elif data_type == "complete":
                    return _GLOBAL_ORGS_CACHE.get("data")

        self.metrics["cache_misses"] += 1
        return None

    def _set_cached_data(self, accounts: List[OrganizationAccount], ous: List[OrganizationalUnit], complete_data: Dict):
        """Set cached data with thread safety"""
        with _cache_lock:
            _GLOBAL_ORGS_CACHE["accounts"] = accounts
            _GLOBAL_ORGS_CACHE["organizational_units"] = ous
            _GLOBAL_ORGS_CACHE["data"] = complete_data
            _GLOBAL_ORGS_CACHE["timestamp"] = datetime.now(timezone.utc)
            self.metrics["last_refresh"] = datetime.now(timezone.utc)

        accounts_count = len(accounts) if accounts else 0
        ous_count = len(ous) if ous else 0
        print_success(f"✅ Organizations cache updated: {accounts_count} accounts, {ous_count} OUs")

    async def get_organization_accounts(self, include_tags: bool = False) -> List[OrganizationAccount]:
        """
        Get all organization accounts with caching support.

        Args:
            include_tags: Whether to include account tags (slower but more comprehensive)

        Returns:
            List of OrganizationAccount objects
        """
        # Check cache first
        cached_accounts = self._get_cached_data("accounts")
        if cached_accounts:
            print_info(f"🚀 Using cached account data ({len(cached_accounts)} accounts)")
            return cached_accounts

        # Initialize client if needed
        if not self.client and not self._initialize_client():
            print_warning("Organizations client unavailable - returning empty account list")
            return []

        print_info("🔍 Discovering organization accounts...")
        accounts = []

        try:
            with create_progress_bar() as progress:
                task = progress.add_task("Discovering accounts...", total=None)

                # Get accounts using paginator for large organizations
                paginator = self.client.get_paginator("list_accounts")

                for page in paginator.paginate():
                    for account_data in page["Accounts"]:
                        account = OrganizationAccount(
                            account_id=account_data["Id"],
                            name=account_data["Name"],
                            email=account_data["Email"],
                            status=account_data["Status"],
                            joined_method=account_data["JoinedMethod"],
                            joined_timestamp=account_data["JoinedTimestamp"],
                        )

                        # Get account tags if requested
                        if include_tags:
                            try:
                                tags_response = self.client.list_tags_for_resource(ResourceId=account.account_id)
                                account.tags = {tag["Key"]: tag["Value"] for tag in tags_response["Tags"]}
                                self.metrics["api_calls_made"] += 1
                            except ClientError:
                                # Tags may not be accessible for all accounts
                                account.tags = {}

                        accounts.append(account)

                    self.metrics["api_calls_made"] += 1
                    progress.update(task, description=f"Found {len(accounts)} accounts...")

            # Map accounts to OUs
            await self._map_accounts_to_ous(accounts)

            print_success(f"✅ Discovered {len(accounts)} organization accounts")
            return accounts

        except Exception as e:
            self.metrics["errors_encountered"] += 1
            print_error(f"Failed to discover organization accounts: {e}")
            return []

    async def get_organizational_units(self) -> List[OrganizationalUnit]:
        """
        Get all organizational units with caching support.

        Returns:
            List of OrganizationalUnit objects
        """
        # Check cache first
        cached_ous = self._get_cached_data("organizational_units")
        if cached_ous:
            print_info(f"🚀 Using cached OU data ({len(cached_ous)} OUs)")
            return cached_ous

        # Initialize client if needed
        if not self.client and not self._initialize_client():
            print_warning("Organizations client unavailable - returning empty OU list")
            return []

        print_info("🏗️ Discovering organizational units...")
        all_ous = []

        try:
            # Get root OU
            roots_response = self.client.list_roots()
            if not roots_response.get("Roots"):
                print_warning("No root organizational units found")
                return []

            root_id = roots_response["Roots"][0]["Id"]
            self.metrics["api_calls_made"] += 1

            # Recursively discover all OUs
            await self._discover_ou_recursive(root_id, all_ous)

            print_success(f"✅ Discovered {len(all_ous)} organizational units")
            return all_ous

        except Exception as e:
            self.metrics["errors_encountered"] += 1
            print_error(f"Failed to discover organizational units: {e}")
            return []

    async def _discover_ou_recursive(self, parent_id: str, ou_list: List[OrganizationalUnit]):
        """Recursively discover organizational units"""
        try:
            paginator = self.client.get_paginator("list_organizational_units_for_parent")

            for page in paginator.paginate(ParentId=parent_id):
                for ou_data in page["OrganizationalUnits"]:
                    ou = OrganizationalUnit(ou_id=ou_data["Id"], name=ou_data["Name"], parent_id=parent_id)

                    ou_list.append(ou)

                    # Recursively discover child OUs
                    await self._discover_ou_recursive(ou.ou_id, ou_list)

                self.metrics["api_calls_made"] += 1

        except ClientError as e:
            print_warning(f"Failed to discover OU children for {parent_id}: {e}")
            self.metrics["errors_encountered"] += 1

    async def _map_accounts_to_ous(self, accounts: List[OrganizationAccount]):
        """Map accounts to their organizational units"""
        if not self.client:
            return

        print_info("🗺️ Mapping accounts to organizational units...")

        with create_progress_bar() as progress:
            task = progress.add_task("Mapping accounts to OUs...", total=len(accounts))

            for account in accounts:
                try:
                    parents_response = self.client.list_parents(ChildId=account.account_id)

                    if parents_response["Parents"]:
                        parent = parents_response["Parents"][0]
                        account.parent_id = parent["Id"]

                        # Get OU name if parent is an OU
                        if parent["Type"] == "ORGANIZATIONAL_UNIT":
                            try:
                                ou_response = self.client.describe_organizational_unit(
                                    OrganizationalUnitId=parent["Id"]
                                )
                                account.organizational_unit = ou_response["OrganizationalUnit"]["Name"]
                                self.metrics["api_calls_made"] += 1
                            except ClientError:
                                account.organizational_unit = f"OU-{parent['Id']}"

                    self.metrics["api_calls_made"] += 1

                except ClientError:
                    # Continue with other accounts
                    self.metrics["errors_encountered"] += 1

                progress.advance(task)

    async def get_complete_organization_structure(self, include_tags: bool = False) -> Dict:
        """
        Get complete organization structure with caching.

        This method provides compatibility with existing inventory module patterns.

        Args:
            include_tags: Whether to include account tags

        Returns:
            Complete organization structure dictionary
        """
        # Check for complete cached data
        cached_data = self._get_cached_data("complete")
        if cached_data:
            print_info("🚀 Using cached complete organization structure")
            return cached_data

        print_info("🏢 Discovering complete organization structure...")

        # Get accounts and OUs
        accounts = await self.get_organization_accounts(include_tags=include_tags)
        ous = await self.get_organizational_units()

        # Get organization info
        org_info = await self._get_organization_info()

        # Build complete structure
        complete_data = {
            "status": "completed",
            "discovery_type": "unified_organizations_api",
            "organization_info": org_info,
            "accounts": {
                "total_accounts": len(accounts),
                "active_accounts": len([a for a in accounts if a.status == "ACTIVE"]),
                "discovered_accounts": [a.to_dict() for a in accounts],
                "discovery_method": "organizations_api",
            },
            "organizational_units": {
                "total_ous": len(ous),
                "organizational_units": [asdict(ou) for ou in ous],
                "discovery_method": "organizations_api",
            },
            "metrics": self.metrics.copy(),
            "timestamp": datetime.now().isoformat(),
        }

        # Cache the complete structure
        self._set_cached_data(accounts, ous, complete_data)

        return complete_data

    async def _get_organization_info(self) -> Dict:
        """Get high-level organization information"""
        if not self.client:
            return {
                "organization_id": "unavailable",
                "master_account_id": "unavailable",
                "master_account_email": "unavailable",
                "feature_set": "unavailable",
                "available_policy_types": [],
                "discovery_method": "unavailable",
            }

        try:
            org_response = self.client.describe_organization()
            org = org_response["Organization"]
            self.metrics["api_calls_made"] += 1

            return {
                "organization_id": org["Id"],
                "master_account_id": org["MasterAccountId"],
                "master_account_email": org["MasterAccountEmail"],
                "feature_set": org["FeatureSet"],
                "available_policy_types": [pt["Type"] for pt in org.get("AvailablePolicyTypes", [])],
                "discovery_method": "organizations_api",
            }

        except ClientError as e:
            print_warning(f"Failed to get organization info: {e}")
            return {
                "organization_id": "error",
                "master_account_id": "error",
                "master_account_email": "error",
                "feature_set": "error",
                "available_policy_types": [],
                "discovery_method": "failed",
                "error": str(e),
            }

    def get_account_name_mapping(self) -> Dict[str, str]:
        """
        Get account ID to name mapping for compatibility with FinOps module.

        Returns:
            Dictionary mapping account IDs to account names
        """
        cached_accounts = self._get_cached_data("accounts")
        if not cached_accounts:
            # Try to refresh cache
            import asyncio

            try:
                cached_accounts = asyncio.get_event_loop().run_until_complete(self.get_organization_accounts())
            except:
                return {}

        return {account.account_id: account.name for account in cached_accounts}

    def invalidate_cache(self):
        """Manually invalidate the global cache"""
        with _cache_lock:
            _GLOBAL_ORGS_CACHE["data"] = None
            _GLOBAL_ORGS_CACHE["accounts"] = None
            _GLOBAL_ORGS_CACHE["organizational_units"] = None
            _GLOBAL_ORGS_CACHE["timestamp"] = None

        print_info("🗑️ Organizations cache invalidated")

    def get_cache_status(self) -> Dict:
        """Get cache status and metrics"""
        with _cache_lock:
            return {
                "cache_valid": self._is_cache_valid(),
                "cache_timestamp": _GLOBAL_ORGS_CACHE.get("timestamp"),
                "ttl_minutes": self.cache_ttl_minutes,
                "metrics": self.metrics.copy(),
                "accounts_cached": len(_GLOBAL_ORGS_CACHE.get("accounts", [])),
                "ous_cached": len(_GLOBAL_ORGS_CACHE.get("organizational_units", [])),
            }


# Factory functions for easy integration with existing modules
def get_unified_organizations_client(
    management_profile: Optional[str] = None, cache_ttl_minutes: int = 30
) -> UnifiedOrganizationsClient:
    """
    Factory function to get unified Organizations client.

    Args:
        management_profile: AWS profile with Organizations access
        cache_ttl_minutes: Cache TTL in minutes

    Returns:
        UnifiedOrganizationsClient instance
    """
    return UnifiedOrganizationsClient(management_profile, cache_ttl_minutes)


async def get_organization_accounts(
    management_profile: Optional[str] = None, include_tags: bool = False
) -> List[OrganizationAccount]:
    """
    Convenience function to get organization accounts.

    Args:
        management_profile: AWS profile with Organizations access
        include_tags: Whether to include account tags

    Returns:
        List of OrganizationAccount objects
    """
    client = get_unified_organizations_client(management_profile)
    return await client.get_organization_accounts(include_tags)


async def get_organization_structure(management_profile: Optional[str] = None, include_tags: bool = False) -> Dict:
    """
    Convenience function to get complete organization structure.

    This function provides backward compatibility with existing inventory module.

    Args:
        management_profile: AWS profile with Organizations access
        include_tags: Whether to include account tags

    Returns:
        Complete organization structure dictionary
    """
    client = get_unified_organizations_client(management_profile)
    return await client.get_complete_organization_structure(include_tags)


# Export public interface
__all__ = [
    "UnifiedOrganizationsClient",
    "OrganizationAccount",
    "OrganizationalUnit",
    "get_unified_organizations_client",
    "get_organization_accounts",
    "get_organization_structure",
]
