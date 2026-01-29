"""
Cross-Account Session Manager for VPC Module
Enterprise STS AssumeRole Implementation

This module provides the correct enterprise pattern for multi-account VPC discovery
using STS AssumeRole instead of the broken profile@accountId format.

Based on proven FinOps patterns from vpc_cleanup_optimizer.py.
"""

import boto3
import logging
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from botocore.exceptions import ClientError
from dataclasses import dataclass

from runbooks.common.rich_utils import console, print_success, print_error, print_warning, print_info
from runbooks.common.profile_utils import create_operational_session, create_management_session

logger = logging.getLogger(__name__)


@dataclass
class AccountSession:
    """Represents a cross-account session with metadata"""

    account_id: str
    account_name: Optional[str]
    session: boto3.Session
    status: str
    error_message: Optional[str] = None


def create_multi_profile_sessions(profiles: List[str]) -> List[AccountSession]:
    """
    Create sessions using direct profile access for organizations without cross-account roles.

    This is an alternative approach when OrganizationAccountAccessRole is not available.
    Uses environment variables like CENTRALISED_OPS_PROFILE, BILLING_PROFILE, etc.

    Args:
        profiles: List of AWS profile names to use

    Returns:
        List of AccountSession objects with successful and failed sessions
    """
    import os

    print_info(f"🌐 Creating sessions for {len(profiles)} profiles")
    account_sessions = []

    for profile_name in profiles:
        try:
            # Validate profile exists and is accessible
            session = boto3.Session(profile_name=profile_name)
            sts_client = session.client("sts")
            identity = sts_client.get_caller_identity()

            account_id = identity["Account"]

            # Try to get account name from Organizations if possible
            account_name = profile_name  # Default to profile name
            try:
                orgs_client = session.client("organizations")
                account_info = orgs_client.describe_account(AccountId=account_id)
                account_name = account_info["Account"]["Name"]
            except:
                pass  # Use profile name as fallback

            account_sessions.append(
                AccountSession(account_id=account_id, account_name=account_name, session=session, status="success")
            )

            print_success(f"✅ Session created for {account_id} using profile {profile_name}")

        except Exception as e:
            print_warning(f"⚠️ Failed to create session for profile {profile_name}: {e}")
            account_sessions.append(
                AccountSession(
                    account_id=profile_name,  # Use profile name as ID when we can't get real ID
                    account_name=profile_name,
                    session=None,
                    status="failed",
                    error_message=str(e),
                )
            )

    return account_sessions


class CrossAccountSessionManager:
    """
    Enterprise cross-account session manager using STS AssumeRole pattern.

    This replaces the broken profile@accountId format with proper STS AssumeRole
    for multi-account VPC discovery across Landing Zone accounts.

    Key Features:
    - Uses CENTRALISED_OPS_PROFILE as base session for assuming roles
    - Standard OrganizationAccountAccessRole assumption
    - Parallel session creation for performance
    - Comprehensive error handling and graceful degradation
    - Compatible with existing VPC module architecture
    """

    def __init__(self, base_profile: str, role_name: str = "OrganizationAccountAccessRole"):
        """
        Initialize cross-account session manager.

        Args:
            base_profile: Base profile (e.g., CENTRALISED_OPS_PROFILE) for assuming roles
            role_name: IAM role name to assume in target accounts
        """
        self.base_profile = base_profile
        self.role_name = role_name

        # Use management session for cross-account role assumptions
        # Management account has the trust relationships for OrganizationAccountAccessRole
        self.session = create_management_session(profile_name=base_profile)

        print_info(f"🔐 Cross-account session manager initialized with {base_profile}")

    def create_cross_account_sessions(
        self, accounts: List[Dict[str, str]], max_workers: int = 10
    ) -> List[AccountSession]:
        """
        Create cross-account sessions using STS AssumeRole pattern.

        Args:
            accounts: List of account dictionaries from Organizations API
            max_workers: Maximum parallel workers for session creation

        Returns:
            List of AccountSession objects with successful and failed sessions
        """
        print_info(f"🌐 Creating cross-account sessions for {len(accounts)} accounts")

        account_sessions = []

        # Filter active accounts only
        active_accounts = [acc for acc in accounts if acc.get("status") == "ACTIVE"]
        print_info(f"📋 Processing {len(active_accounts)} active accounts")

        # Create sessions in parallel for performance
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_account = {
                executor.submit(self._create_account_session, account): account for account in active_accounts
            }

            for future in as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    account_session = future.result()
                    account_sessions.append(account_session)

                    if account_session.status == "success":
                        print_success(f"✅ Session created for {account_session.account_id}")
                    else:
                        print_warning(
                            f"⚠️  Session failed for {account_session.account_id}: {account_session.error_message}"
                        )

                except Exception as e:
                    print_error(f"❌ Unexpected error creating session for {account['id']}: {e}")
                    account_sessions.append(
                        AccountSession(
                            account_id=account["id"],
                            account_name=account.get("name"),
                            session=None,
                            status="error",
                            error_message=str(e),
                        )
                    )

        successful_sessions = [s for s in account_sessions if s.status == "success"]
        failed_sessions = [s for s in account_sessions if s.status != "success"]

        print_info(
            f"🎯 Session creation complete: {len(successful_sessions)} successful, {len(failed_sessions)} failed"
        )

        return account_sessions

    def _create_account_session(self, account: Dict[str, str]) -> AccountSession:
        """
        Create a session for a single account using STS AssumeRole.

        This is the core implementation of the enterprise pattern.
        """
        account_id = account["id"]
        account_name = account.get("name", f"Account-{account_id}")

        # Try multiple role patterns for different organization setups - universal compatibility
        role_patterns = [
            self.role_name,  # Default: OrganizationAccountAccessRole
            "AWSControlTowerExecution",  # Control Tower pattern
            "OrganizationAccountAccess",  # Alternative naming
            "ReadOnlyAccess",  # Fallback for read-only operations
            "PowerUserAccess",  # Common enterprise role
            "AdminRole",  # Common enterprise role
            "CrossAccountRole",  # Generic cross-account role
            "AssumeRole",  # Generic assume role
        ]

        for role_name in role_patterns:
            try:
                # Step 1: Assume role in target account using STS
                sts_client = self.session.client("sts")
                assumed_role = sts_client.assume_role(
                    RoleArn=f"arn:aws:iam::{account_id}:role/{role_name}",
                    RoleSessionName=f"VPCDiscovery-{account_id[:12]}",
                )

                # If successful, continue with this role

                # Step 2: Create session with assumed role credentials
                assumed_session = boto3.Session(
                    aws_access_key_id=assumed_role["Credentials"]["AccessKeyId"],
                    aws_secret_access_key=assumed_role["Credentials"]["SecretAccessKey"],
                    aws_session_token=assumed_role["Credentials"]["SessionToken"],
                )

                # Step 3: Validate session with basic STS call
                assumed_sts = assumed_session.client("sts")
                identity = assumed_sts.get_caller_identity()

                logger.debug(
                    f"Successfully assumed role {role_name} in account {account_id}, identity: {identity['Arn']}"
                )

                return AccountSession(
                    account_id=account_id, account_name=account_name, session=assumed_session, status="success"
                )

            except ClientError as e:
                # Continue to next role pattern
                continue

        # If no role patterns worked, return failure
        error_msg = f"Unable to assume any role pattern in {account_id} - tried: {', '.join(role_patterns)}"
        logger.warning(f"Failed to create session for {account_id}: {error_msg}")

        return AccountSession(
            account_id=account_id, account_name=account_name, session=None, status="failed", error_message=error_msg
        )

    def get_successful_sessions(self, account_sessions: List[AccountSession]) -> List[AccountSession]:
        """Get only successful account sessions for VPC discovery."""
        successful = [s for s in account_sessions if s.status == "success"]
        print_info(f"🎯 {len(successful)} accounts ready for VPC discovery")
        return successful

    def get_session_summary(self, account_sessions: List[AccountSession]) -> Dict[str, int]:
        """Get summary statistics for session creation."""
        summary = {
            "total": len(account_sessions),
            "successful": len([s for s in account_sessions if s.status == "success"]),
            "failed": len([s for s in account_sessions if s.status == "failed"]),
            "errors": len([s for s in account_sessions if s.status == "error"]),
        }
        return summary


def create_cross_account_vpc_sessions(
    accounts: List[Dict[str, str]], base_profile: str, role_name: str = "OrganizationAccountAccessRole"
) -> List[AccountSession]:
    """
    Convenience function to create cross-account VPC sessions.

    This is the main entry point for VPC modules to replace the broken
    profile@accountId pattern with proper STS AssumeRole.

    Args:
        accounts: List of organization accounts from get_organization_accounts
        base_profile: Base profile for assuming roles (CENTRALISED_OPS_PROFILE)
        role_name: IAM role name to assume

    Returns:
        List of AccountSession objects ready for VPC discovery
    """
    session_manager = CrossAccountSessionManager(base_profile, role_name)
    return session_manager.create_cross_account_sessions(accounts)


# Compatibility functions for existing VPC module integration
def convert_accounts_to_sessions(
    accounts: List[Dict[str, str]], base_profile: str
) -> Tuple[List[AccountSession], Dict[str, Dict[str, str]]]:
    """
    Convert organization accounts to cross-account sessions.

    This replaces the broken convert_accounts_to_profiles function
    with proper STS AssumeRole session creation.

    Returns:
        Tuple of (successful_sessions, account_metadata)
    """
    account_sessions = create_cross_account_vpc_sessions(accounts, base_profile)
    successful_sessions = [s for s in account_sessions if s.status == "success"]

    # Create account metadata dict for compatibility
    account_metadata = {}
    for account in accounts:
        account_metadata[account["id"]] = account

    return successful_sessions, account_metadata
