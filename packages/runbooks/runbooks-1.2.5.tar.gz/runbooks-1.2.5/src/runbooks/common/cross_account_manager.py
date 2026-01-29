#!/usr/bin/env python3
"""
Enhanced Cross-Account Session Manager for Runbooks Platform

This module consolidates cross-account session patterns from VPC and other modules
into a unified, high-performance manager optimized for 61-account enterprise operations.

Features:
- STS AssumeRole patterns with multiple role fallbacks
- Session caching and reuse for performance optimization
- Parallel session creation using ThreadPoolExecutor
- Integration with unified Organizations client
- Rich CLI progress indicators and error reporting
- Comprehensive session validation and metadata tracking

Author: Runbooks Team
Version: latest version
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from runbooks.common.organizations_client import OrganizationAccount, get_unified_organizations_client
from runbooks.common.profile_utils import create_management_session, get_profile_for_operation
from runbooks.common.rich_utils import (
    console,
    create_progress_bar,
    print_error,
    print_info,
    print_success,
    print_warning,
)

# Global session cache for performance optimization
_SESSION_CACHE = {}
_cache_lock = threading.Lock()


@dataclass
class CrossAccountSession:
    """Enhanced cross-account session with comprehensive metadata and refresh capabilities"""

    account_id: str
    account_name: Optional[str]
    session: Optional[boto3.Session]
    status: str  # 'success', 'failed', 'error', 'cached'
    role_used: Optional[str] = None
    assumed_role_arn: Optional[str] = None
    session_expires: Optional[float] = None  # Unix timestamp
    error_message: Optional[str] = None
    creation_timestamp: Optional[float] = None
    last_refresh_timestamp: Optional[float] = None  # Enhanced: Track refresh cycles
    refresh_count: int = 0  # Enhanced: Count refresh operations
    next_refresh_time: Optional[float] = None  # Enhanced: Calculated refresh time

    def __post_init__(self):
        if self.creation_timestamp is None:
            self.creation_timestamp = time.time()

    def is_expired(self, session_ttl_minutes: int = 240) -> bool:
        """Check if session is expired based on TTL (enhanced default: 4-hour)"""
        if not self.session_expires:
            # If no explicit expiry, use creation time + TTL
            return (time.time() - self.creation_timestamp) > (session_ttl_minutes * 60)

        return time.time() > self.session_expires

    def needs_refresh(self, session_ttl_minutes: int = 240, auto_refresh_threshold: float = 0.9) -> bool:
        """Enhanced: Check if session needs preemptive refresh"""
        if not self.session_expires:
            # Use creation time + TTL for calculation
            ttl_seconds = session_ttl_minutes * 60
            refresh_time = self.creation_timestamp + (ttl_seconds * auto_refresh_threshold)
            return time.time() >= refresh_time

        # Use explicit expiry time
        refresh_time = self.session_expires - ((session_ttl_minutes * 60) * (1 - auto_refresh_threshold))
        return time.time() >= refresh_time

    def calculate_next_refresh(self, session_ttl_minutes: int = 240, auto_refresh_threshold: float = 0.9):
        """Enhanced: Calculate next refresh time"""
        if self.session_expires:
            ttl_seconds = self.session_expires - time.time()
        else:
            ttl_seconds = session_ttl_minutes * 60

        self.next_refresh_time = time.time() + (ttl_seconds * auto_refresh_threshold)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization (excluding session object)"""
        data = self.__dict__.copy()
        data.pop("session", None)  # Remove session object for serialization
        return data


class EnhancedCrossAccountManager:
    """
    Enhanced cross-account session manager for enterprise 61-account operations.

    This manager provides optimized cross-account access using:
    - STS AssumeRole with multiple role pattern fallbacks
    - Session caching and reuse for performance
    - Parallel session creation for speed
    - Integration with Organizations API for account discovery
    - Rich progress indicators and comprehensive error handling
    """

    # Standard role patterns for cross-account access
    STANDARD_ROLE_PATTERNS = [
        "OrganizationAccountAccessRole",  # AWS Organizations default
        "AWSControlTowerExecution",  # AWS Control Tower
        "OrganizationAccountAccess",  # Alternative naming
        "CrossAccountAccessRole",  # Custom pattern
        "ReadOnlyAccess",  # Fallback for read-only operations
    ]

    def __init__(
        self,
        base_profile: Optional[str] = None,
        role_patterns: Optional[List[str]] = None,
        max_workers: int = 10,
        session_ttl_minutes: int = 240,  # Enhanced: 4-hour TTL for enterprise operations
        enable_session_cache: bool = True,
        auto_refresh_threshold: float = 0.9,  # Auto-refresh at 90% of TTL (216 minutes)
        enable_preemptive_refresh: bool = True,  # Preemptive session refresh capability
    ):
        """
        Initialize enhanced cross-account session manager.

        Args:
            base_profile: Base profile for assuming roles
            role_patterns: Custom role patterns to try (defaults to STANDARD_ROLE_PATTERNS)
            max_workers: Maximum parallel workers for session creation
            session_ttl_minutes: Session TTL in minutes (enhanced default: 240 minutes / 4 hours)
            enable_session_cache: Whether to enable session caching
            auto_refresh_threshold: Fraction of TTL at which to trigger refresh (0.9 = 90%)
            enable_preemptive_refresh: Enable background session refresh before expiration
        """
        self.base_profile = base_profile
        self.role_patterns = role_patterns or self.STANDARD_ROLE_PATTERNS.copy()
        self.max_workers = max_workers
        self.session_ttl_minutes = session_ttl_minutes
        self.enable_session_cache = enable_session_cache
        self.auto_refresh_threshold = auto_refresh_threshold
        self.enable_preemptive_refresh = enable_preemptive_refresh

        # Initialize base session for role assumptions
        if base_profile:
            self.base_session = create_management_session(base_profile)
        else:
            # Use profile resolution for management operations
            management_profile = get_profile_for_operation("management", None)
            self.base_session = boto3.Session(profile_name=management_profile)

        # Performance metrics
        self.metrics = {
            "sessions_created": 0,
            "sessions_cached": 0,
            "sessions_failed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_api_calls": 0,
        }

        print_info(f"🔐 Enhanced cross-account manager initialized")
        print_info(f"   Role patterns: {len(self.role_patterns)} configured")
        print_info(f"   Session caching: {'enabled' if enable_session_cache else 'disabled'}")
        print_info(f"   Session TTL: {session_ttl_minutes} minutes (4-hour enterprise standard)")
        print_info(
            f"   Auto-refresh: {'enabled' if enable_preemptive_refresh else 'disabled'} at {auto_refresh_threshold:.0%} TTL"
        )

    def _get_cached_session(self, account_id: str) -> Optional[CrossAccountSession]:
        """Get cached session if valid and not expired"""
        if not self.enable_session_cache:
            return None

        with _cache_lock:
            cached_session = _SESSION_CACHE.get(account_id)
            if cached_session and not cached_session.is_expired(self.session_ttl_minutes):
                self.metrics["cache_hits"] += 1
                return cached_session
            elif cached_session:
                # Remove expired session from cache
                del _SESSION_CACHE[account_id]

        self.metrics["cache_misses"] += 1
        return None

    def _cache_session(self, session: CrossAccountSession):
        """Cache session for reuse"""
        if not self.enable_session_cache or session.status != "success":
            return

        with _cache_lock:
            _SESSION_CACHE[session.account_id] = session

        print_info(f"💾 Cached session for account {session.account_id}")

    async def create_cross_account_sessions_from_accounts(
        self, accounts: List[OrganizationAccount]
    ) -> List[CrossAccountSession]:
        """
        Create cross-account sessions from OrganizationAccount objects.

        Args:
            accounts: List of OrganizationAccount objects

        Returns:
            List of CrossAccountSession objects
        """
        # Filter active accounts
        active_accounts = [acc for acc in accounts if acc.status == "ACTIVE"]

        print_info(f"🌐 Creating cross-account sessions for {len(active_accounts)} active accounts")

        return await self._create_sessions_parallel(active_accounts)

    async def create_cross_account_sessions_from_organization(
        self, management_profile: Optional[str] = None
    ) -> List[CrossAccountSession]:
        """
        Create cross-account sessions by discovering accounts from Organizations API.

        Args:
            management_profile: Profile for Organizations API access

        Returns:
            List of CrossAccountSession objects
        """
        print_info("🏢 Discovering accounts from Organizations API...")

        # Use unified Organizations client to discover accounts
        orgs_client = get_unified_organizations_client(management_profile or self.base_profile)
        accounts = await orgs_client.get_organization_accounts()

        if not accounts:
            print_warning("No accounts discovered from Organizations API")
            return []

        return await self.create_cross_account_sessions_from_accounts(accounts)

    async def _create_sessions_parallel(self, accounts: List[OrganizationAccount]) -> List[CrossAccountSession]:
        """Create sessions in parallel for performance"""

        sessions = []

        with create_progress_bar() as progress:
            task = progress.add_task("Creating cross-account sessions...", total=len(accounts))

            # Use ThreadPoolExecutor for parallel session creation
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_account = {
                    executor.submit(self._create_single_session, account): account for account in accounts
                }

                for future in as_completed(future_to_account):
                    account = future_to_account[future]
                    try:
                        session = future.result()
                        sessions.append(session)

                        # Update progress with status
                        if session.status == "success":
                            self.metrics["sessions_created"] += 1
                        elif session.status == "cached":
                            self.metrics["sessions_cached"] += 1
                        else:
                            self.metrics["sessions_failed"] += 1

                        progress.advance(task)

                    except Exception as e:
                        print_error(f"❌ Unexpected error creating session for {account.account_id}: {e}")
                        sessions.append(
                            CrossAccountSession(
                                account_id=account.account_id,
                                account_name=account.name,
                                session=None,
                                status="error",
                                error_message=str(e),
                            )
                        )
                        progress.advance(task)

        # Summary
        successful = len([s for s in sessions if s.status in ["success", "cached"]])
        failed = len([s for s in sessions if s.status in ["failed", "error"]])

        print_success(f"✅ Session creation complete: {successful} successful, {failed} failed")

        return sessions

    def _create_single_session(self, account: OrganizationAccount) -> CrossAccountSession:
        """
        Create a single cross-account session with caching and role pattern fallback.

        This is the core implementation handling caching, role patterns, and error handling.
        """
        # Check cache first
        cached_session = self._get_cached_session(account.account_id)
        if cached_session:
            print_info(f"💾 Using cached session for {account.account_id}")
            cached_session.status = "cached"  # Mark as cached for metrics
            return cached_session

        # Try each role pattern
        for role_name in self.role_patterns:
            try:
                session = self._assume_role_and_create_session(account.account_id, account.name, role_name)

                if session.status == "success":
                    # Cache successful session
                    self._cache_session(session)
                    return session

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                # Continue to next role pattern for certain errors
                if error_code in ["AccessDenied", "NoSuchEntity"]:
                    continue
                else:
                    # For other errors, return failure
                    return CrossAccountSession(
                        account_id=account.account_id,
                        account_name=account.name,
                        session=None,
                        status="failed",
                        error_message=f"AWS API error: {error_code}",
                    )

            except Exception as e:
                # For unexpected errors, continue to next role pattern
                continue

        # If no role patterns worked
        return CrossAccountSession(
            account_id=account.account_id,
            account_name=account.name,
            session=None,
            status="failed",
            role_used=None,
            error_message=f"Unable to assume any role pattern: {', '.join(self.role_patterns)}",
        )

    def _assume_role_and_create_session(
        self, account_id: str, account_name: Optional[str], role_name: str
    ) -> CrossAccountSession:
        """Assume role and create session with validation"""

        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        session_name = f"CloudOpsRunbooks-{account_id[:12]}-{int(time.time())}"

        try:
            # Step 1: Assume role using base session
            sts_client = self.base_session.client("sts")
            assume_role_response = sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName=session_name,
                DurationSeconds=3600,  # 1 hour (default)
            )

            credentials = assume_role_response["Credentials"]
            expiration = credentials["Expiration"].timestamp()

            self.metrics["total_api_calls"] += 1

            # Step 2: Create session with assumed role credentials
            assumed_session = boto3.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
            )

            # Step 3: Validate session with STS call
            assumed_sts = assumed_session.client("sts")
            identity = assumed_sts.get_caller_identity()
            self.metrics["total_api_calls"] += 1

            # Verify we're in the correct account
            if identity["Account"] != account_id:
                return CrossAccountSession(
                    account_id=account_id,
                    account_name=account_name,
                    session=None,
                    status="failed",
                    error_message=f"Role assumption returned wrong account: {identity['Account']}",
                )

            return CrossAccountSession(
                account_id=account_id,
                account_name=account_name,
                session=assumed_session,
                status="success",
                role_used=role_name,
                assumed_role_arn=role_arn,
                session_expires=expiration,
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            return CrossAccountSession(
                account_id=account_id,
                account_name=account_name,
                session=None,
                status="failed",
                error_message=f"Failed to assume {role_name}: {error_code}",
            )

    def get_successful_sessions(self, sessions: List[CrossAccountSession]) -> List[CrossAccountSession]:
        """Get only successful sessions for operations"""
        successful = [s for s in sessions if s.status in ["success", "cached"]]
        print_info(f"🎯 {len(successful)}/{len(sessions)} sessions ready for cross-account operations")
        return successful

    def get_session_by_account_id(
        self, sessions: List[CrossAccountSession], account_id: str
    ) -> Optional[CrossAccountSession]:
        """Get session for specific account ID"""
        for session in sessions:
            if session.account_id == account_id and session.status in ["success", "cached"]:
                return session
        return None

    def refresh_expired_sessions(self, sessions: List[CrossAccountSession]) -> List[CrossAccountSession]:
        """Enhanced: Refresh expired sessions with preemptive refresh support"""
        refreshed_sessions = []

        for session in sessions:
            should_refresh = False
            refresh_reason = ""

            if session.status in ["success", "cached"]:
                if session.is_expired(self.session_ttl_minutes):
                    should_refresh = True
                    refresh_reason = "expired"
                elif self.enable_preemptive_refresh and session.needs_refresh(
                    self.session_ttl_minutes, self.auto_refresh_threshold
                ):
                    should_refresh = True
                    refresh_reason = "preemptive"

            if should_refresh:
                print_info(f"🔄 Refreshing {refresh_reason} session for {session.account_id}")

                # Create new session
                account = OrganizationAccount(
                    account_id=session.account_id,
                    name=session.account_name or session.account_id,
                    email="refresh@system",
                    status="ACTIVE",
                    joined_method="REFRESH",
                )

                new_session = self._create_single_session(account)

                # Enhanced: Copy refresh metadata
                if new_session.status == "success":
                    new_session.refresh_count = session.refresh_count + 1
                    new_session.last_refresh_timestamp = time.time()
                    new_session.calculate_next_refresh(self.session_ttl_minutes, self.auto_refresh_threshold)
                    print_info(f"✅ Session refreshed successfully (refresh #{new_session.refresh_count})")

                refreshed_sessions.append(new_session)
            else:
                refreshed_sessions.append(session)

        return refreshed_sessions

    def get_session_summary(self, sessions: List[CrossAccountSession]) -> Dict:
        """Enhanced: Get comprehensive session summary with refresh metrics"""
        refresh_stats = {
            "sessions_needing_refresh": len(
                [
                    s
                    for s in sessions
                    if s.status in ["success", "cached"]
                    and s.needs_refresh(self.session_ttl_minutes, self.auto_refresh_threshold)
                ]
            ),
            "refreshed_sessions": len([s for s in sessions if s.refresh_count > 0]),
            "total_refresh_operations": sum(s.refresh_count for s in sessions),
            "sessions_with_next_refresh_time": len([s for s in sessions if s.next_refresh_time is not None]),
        }

        return {
            "total_sessions": len(sessions),
            "successful_sessions": len([s for s in sessions if s.status == "success"]),
            "cached_sessions": len([s for s in sessions if s.status == "cached"]),
            "failed_sessions": len([s for s in sessions if s.status == "failed"]),
            "error_sessions": len([s for s in sessions if s.status == "error"]),
            "metrics": self.metrics.copy(),
            "refresh_metrics": refresh_stats,  # Enhanced: Refresh statistics
            "role_patterns_configured": len(self.role_patterns),
            "session_ttl_minutes": self.session_ttl_minutes,
            "cache_enabled": self.enable_session_cache,
            "preemptive_refresh_enabled": self.enable_preemptive_refresh,  # Enhanced
            "auto_refresh_threshold": self.auto_refresh_threshold,  # Enhanced
        }

    def clear_session_cache(self):
        """Clear the global session cache"""
        with _cache_lock:
            cache_size = len(_SESSION_CACHE)
            _SESSION_CACHE.clear()

        print_info(f"🗑️ Cleared {cache_size} cached sessions")

    def get_cache_statistics(self) -> Dict:
        """Get cache statistics"""
        with _cache_lock:
            cache_size = len(_SESSION_CACHE)
            expired_count = sum(1 for s in _SESSION_CACHE.values() if s.is_expired(self.session_ttl_minutes))

        return {
            "cache_size": cache_size,
            "expired_sessions": expired_count,
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "hit_rate": (
                self.metrics["cache_hits"] / (self.metrics["cache_hits"] + self.metrics["cache_misses"])
                if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
                else 0
            ),
        }


# Convenience functions for easy integration


async def create_cross_account_sessions(
    base_profile: Optional[str] = None,
    management_profile: Optional[str] = None,
    role_patterns: Optional[List[str]] = None,
    max_workers: int = 10,
) -> List[CrossAccountSession]:
    """
    Convenience function to create cross-account sessions from Organizations API.

    Args:
        base_profile: Base profile for assuming roles
        management_profile: Profile for Organizations API access
        role_patterns: Custom role patterns to try
        max_workers: Maximum parallel workers

    Returns:
        List of CrossAccountSession objects
    """
    manager = EnhancedCrossAccountManager(
        base_profile=base_profile, role_patterns=role_patterns, max_workers=max_workers
    )

    return await manager.create_cross_account_sessions_from_organization(management_profile)


def convert_sessions_to_profiles_compatibility(sessions: List[CrossAccountSession]) -> Tuple[List[str], Dict[str, str]]:
    """
    Convert sessions to profile format for compatibility with existing VPC module.

    This function provides backward compatibility for modules expecting profile names.
    Note: This is a bridge function - modules should migrate to use sessions directly.

    Returns:
        Tuple of (profile_list, account_metadata) for compatibility
    """
    successful_sessions = [s for s in sessions if s.status in ["success", "cached"]]

    # Create temporary profile identifiers (session-based)
    profile_list = [f"session:{s.account_id}" for s in successful_sessions]

    # Create account metadata
    account_metadata = {
        s.account_id: {
            "id": s.account_id,
            "name": s.account_name or s.account_id,
            "profile_identifier": f"session:{s.account_id}",
            "role_used": s.role_used,
            "session_available": True,
        }
        for s in successful_sessions
    }

    return profile_list, account_metadata


# Export public interface
__all__ = [
    "EnhancedCrossAccountManager",
    "CrossAccountSession",
    "create_cross_account_sessions",
    "convert_sessions_to_profiles_compatibility",
]
