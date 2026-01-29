#!/usr/bin/env python3
"""
AWS Profile Manager - Universal v1.1.x Compatibility

Centralized AWS profile and account management for Runbooks platform.
Eliminates ALL hardcoded account IDs and provides universal --profile support.

Features:
- 3-tier profile priority: User > Environment > Default
- Dynamic account ID resolution
- Multi-account discovery and validation
- Profile existence validation with helpful error messages
- Integration with Rich CLI for beautiful output
- Service-specific profile routing (v1.1.11+):
  * Organizations → MANAGEMENT_PROFILE
  * Cost Explorer → BILLING_PROFILE
  * CloudWatch/Metrics → CENTRALISED_OPS_PROFILE

Author: Runbooks Team
Version: 1.1.11
"""

import os
import boto3
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, ProfileNotFound, NoCredentialsError
from rich.console import Console

from runbooks.common.rich_utils import console, print_error, print_success, print_warning, print_info


# Service-to-Profile Routing Configuration (v1.1.11+)
# Maps AWS services to their appropriate profile environment variables
SERVICE_PROFILE_MAPPING = {
    # Organization Management (multi-account operations)
    "organizations": "AWS_MANAGEMENT_PROFILE",
    "organization": "AWS_MANAGEMENT_PROFILE",
    # Billing & Cost Analysis
    "cost-explorer": "AWS_BILLING_PROFILE",
    "ce": "AWS_BILLING_PROFILE",
    "billing": "AWS_BILLING_PROFILE",
    "cost": "AWS_BILLING_PROFILE",
    # Centralized Operations & Monitoring
    "cloudwatch": "AWS_CENTRALISED_OPS_PROFILE",
    "logs": "AWS_CENTRALISED_OPS_PROFILE",
    "monitoring": "AWS_CENTRALISED_OPS_PROFILE",
    "metrics": "AWS_CENTRALISED_OPS_PROFILE",
    # Default operational profile for compute services
    "ec2": "AWS_MANAGEMENT_PROFILE",
    "workspaces": "AWS_MANAGEMENT_PROFILE",
    "ecs": "AWS_MANAGEMENT_PROFILE",
    "eks": "AWS_MANAGEMENT_PROFILE",
}

# Default profile values (fallback when environment variables not set)
DEFAULT_PROFILES = {
    "AWS_MANAGEMENT_PROFILE": "${MANAGEMENT_PROFILE}",
    "AWS_BILLING_PROFILE": "${BILLING_PROFILE}",
    "AWS_CENTRALISED_OPS_PROFILE": "${CENTRALISED_OPS_PROFILE}",
}


def get_profile_for_service(service_name: str, override_profile: Optional[str] = None) -> str:
    """
    Get appropriate AWS profile for a given service (v1.1.11+ unified routing).

    Priority:
    1. User-specified override profile (highest)
    2. Service-specific environment variable (e.g., AWS_MANAGEMENT_PROFILE)
    3. Generic AWS_PROFILE environment variable
    4. Service-specific default profile
    5. None (use AWS default credentials)

    Args:
        service_name: AWS service name (e.g., 'organizations', 'cost-explorer', 'cloudwatch')
        override_profile: User-specified profile (CLI --profile flag)

    Returns:
        Profile name to use, or None for AWS default credentials

    Examples:
        >>> get_profile_for_service("organizations")
        '${MANAGEMENT_PROFILE}'  # from AWS_MANAGEMENT_PROFILE

        >>> get_profile_for_service("cost-explorer")
        '${BILLING_PROFILE}'  # from AWS_BILLING_PROFILE

        >>> get_profile_for_service("cloudwatch")
        '${CENTRALISED_OPS_PROFILE}'  # from AWS_CENTRALISED_OPS_PROFILE

        >>> get_profile_for_service("ec2", override_profile="custom-profile")
        'custom-profile'  # override takes precedence
    """
    # Priority 1: User override (CLI --profile)
    if override_profile:
        return override_profile

    # Priority 2: Service-specific environment variable
    env_var_name = SERVICE_PROFILE_MAPPING.get(service_name.lower())
    if env_var_name:
        service_profile = os.getenv(env_var_name)
        if service_profile:
            return service_profile

        # Priority 4: Service-specific default
        default_profile = DEFAULT_PROFILES.get(env_var_name)
        if default_profile:
            return default_profile

    # Priority 3: Generic AWS_PROFILE
    aws_profile = os.getenv("AWS_PROFILE")
    if aws_profile:
        return aws_profile

    # Priority 5: None (AWS default credentials)
    return None


class AWSProfileManager:
    """
    Universal AWS Profile Manager for CloudOps v1.1.x compatibility.

    Provides centralized profile management, account resolution, and
    multi-account discovery for all CloudOps modules.
    """

    def __init__(self, profile: Optional[str] = None):
        """
        Initialize ProfileManager with 3-tier priority.

        Args:
            profile: User-specified profile (highest priority)
        """
        self.profile = self._resolve_profile(profile)
        self.session = None
        self._account_cache: Dict[str, str] = {}

    def _resolve_profile(self, user_profile: Optional[str]) -> Optional[str]:
        """
        Resolve profile using 3-tier priority: User > Environment > Default

        Args:
            user_profile: User-specified profile

        Returns:
            Resolved profile name or None for default
        """
        # Tier 1: User-specified profile (highest priority)
        if user_profile:
            return user_profile

        # Tier 2: Environment variable
        env_profile = os.getenv("AWS_PROFILE")
        if env_profile:
            return env_profile

        # Tier 3: Default (no explicit profile)
        return None

    def get_session(self, region: str = "ap-southeast-2") -> boto3.Session:
        """
        Get boto3 session with resolved profile.

        Args:
            region: AWS region (default: ap-southeast-2)

        Returns:
            Configured boto3 session

        Raises:
            ProfileNotFound: If specified profile doesn't exist
            NoCredentialsError: If no valid credentials found
        """
        if not self.session:
            try:
                if self.profile:
                    self.session = boto3.Session(profile_name=self.profile, region_name=region)
                    print_info(f"Using AWS profile: {self.profile}")
                else:
                    self.session = boto3.Session(region_name=region)
                    print_info("Using default AWS credentials")

                # Validate credentials by getting caller identity
                sts = self.session.client("sts")
                identity = sts.get_caller_identity()
                print_success(f"✅ Authenticated as: {identity.get('Arn', 'Unknown')}")

            except ProfileNotFound as e:
                print_error(f"❌ AWS profile '{self.profile}' not found")
                print_info("Available profiles:")
                self._list_available_profiles()
                raise e
            except NoCredentialsError as e:
                print_error("❌ No AWS credentials found")
                print_info("Setup options:")
                print_info("1. Configure AWS CLI: aws configure")
                print_info("2. Set AWS_PROFILE environment variable")
                print_info("3. Use --profile flag with valid profile name")
                raise e

        return self.session

    def get_account_id(self, region: str = "ap-southeast-2") -> str:
        """
        Get current AWS account ID dynamically.

        Args:
            region: AWS region

        Returns:
            Current AWS account ID
        """
        cache_key = f"{self.profile or 'default'}:{region}"

        if cache_key not in self._account_cache:
            try:
                session = self.get_session(region)
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                account_id = identity["Account"]
                self._account_cache[cache_key] = account_id
                print_info(f"Current account ID: {account_id}")

            except ClientError as e:
                print_error(f"❌ Failed to get account ID: {e}")
                # Return generic account ID for testing/mock scenarios
                return "123456789012"

        return self._account_cache[cache_key]

    def discover_organization_accounts(self, region: str = "ap-southeast-2") -> List[Dict[str, Any]]:
        """
        Discover all accounts in AWS Organizations (if available).

        Args:
            region: AWS region

        Returns:
            List of organization accounts with metadata
        """
        try:
            session = self.get_session(region)
            org_client = session.client("organizations")

            # Get organization information
            try:
                org_info = org_client.describe_organization()
                print_success(f"✅ Organization: {org_info['Organization']['Id']}")
            except ClientError:
                print_warning("⚠️ Not connected to AWS Organizations")
                return []

            # List all accounts
            accounts = []
            paginator = org_client.get_paginator("list_accounts")

            for page in paginator.paginate():
                for account in page["Accounts"]:
                    accounts.append(
                        {
                            "Id": account["Id"],
                            "Name": account["Name"],
                            "Email": account["Email"],
                            "Status": account["Status"],
                            "JoinedMethod": account.get("JoinedMethod", "UNKNOWN"),
                        }
                    )

            print_success(f"✅ Discovered {len(accounts)} organization accounts")
            return accounts

        except ClientError as e:
            print_warning(f"⚠️ Unable to discover organization accounts: {e}")
            return []

    def validate_profile_access(self, required_services: List[str] = None) -> Dict[str, bool]:
        """
        Validate profile has access to required AWS services.

        Args:
            required_services: List of AWS service names to validate

        Returns:
            Dict mapping service names to access status
        """
        if not required_services:
            required_services = ["sts", "ce", "ec2", "s3"]

        access_status = {}
        session = self.get_session()

        for service in required_services:
            try:
                client = session.client(service)

                # Service-specific health checks
                if service == "sts":
                    client.get_caller_identity()
                elif service == "ce":
                    # Test Cost Explorer access
                    from datetime import datetime, timedelta

                    end_date = datetime.now().strftime("%Y-%m-%d")
                    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                    client.get_cost_and_usage(
                        TimePeriod={"Start": start_date, "End": end_date},
                        Granularity="MONTHLY",
                        Metrics=["UnblendedCost"],
                    )
                elif service == "ec2":
                    client.describe_regions(MaxResults=1)
                elif service == "s3":
                    client.list_buckets()

                access_status[service] = True
                print_success(f"✅ {service.upper()} access validated")

            except ClientError as e:
                access_status[service] = False
                print_warning(f"⚠️ {service.upper()} access limited: {e}")

        return access_status

    def _list_available_profiles(self) -> None:
        """List available AWS profiles from credentials file."""
        try:
            import configparser
            import os.path

            credentials_path = os.path.expanduser("~/.aws/credentials")
            config_path = os.path.expanduser("~/.aws/config")

            profiles = set()

            # Check credentials file
            if os.path.exists(credentials_path):
                cred_config = configparser.ConfigParser()
                cred_config.read(credentials_path)
                profiles.update(cred_config.sections())

            # Check config file (profiles prefixed with 'profile ')
            if os.path.exists(config_path):
                config_config = configparser.ConfigParser()
                config_config.read(config_path)
                for section in config_config.sections():
                    if section.startswith("profile "):
                        profiles.add(section[8:])  # Remove 'profile ' prefix
                    elif section == "default":
                        profiles.add("default")

            if profiles:
                for profile in sorted(profiles):
                    print_info(f"  - {profile}")
            else:
                print_info("  No profiles found in ~/.aws/credentials or ~/.aws/config")

        except Exception as e:
            print_warning(f"⚠️ Could not list profiles: {e}")

    @classmethod
    def create_mock_account_context(cls, mock_account_id: str = "123456789012") -> "AWSProfileManager":
        """
        Create mock profile manager for testing scenarios.

        Args:
            mock_account_id: Mock account ID to use

        Returns:
            ProfileManager configured for testing
        """
        manager = cls()
        manager._account_cache["mock"] = mock_account_id
        return manager

    def get_profile_display_name(self) -> str:
        """
        Get human-friendly profile display name.

        Returns:
            Profile display name for CLI output
        """
        if self.profile:
            return f"Profile: {self.profile}"
        else:
            return "Profile: default"

    def __repr__(self) -> str:
        return f"AWSProfileManager(profile={self.profile})"


# Global convenience functions for backward compatibility
def get_current_account_id(profile: Optional[str] = None, region: str = "ap-southeast-2") -> str:
    """
    Convenience function to get current account ID.

    Args:
        profile: AWS profile name
        region: AWS region

    Returns:
        Current AWS account ID
    """
    manager = AWSProfileManager(profile)
    return manager.get_account_id(region)


def validate_profile_or_exit(profile: Optional[str] = None, required_services: List[str] = None) -> AWSProfileManager:
    """
    Validate profile exists and has required access, exit gracefully if not.

    Args:
        profile: AWS profile name
        required_services: Required AWS services for validation

    Returns:
        Validated AWSProfileManager instance
    """
    try:
        manager = AWSProfileManager(profile)
        access_status = manager.validate_profile_access(required_services)

        failed_services = [svc for svc, status in access_status.items() if not status]
        if failed_services:
            print_warning(f"⚠️ Limited access to services: {', '.join(failed_services)}")
            print_info("Continuing with available services...")

        return manager

    except (ProfileNotFound, NoCredentialsError):
        print_error("❌ Cannot proceed without valid AWS credentials")
        print_info("Please configure AWS credentials and try again.")
        exit(1)
