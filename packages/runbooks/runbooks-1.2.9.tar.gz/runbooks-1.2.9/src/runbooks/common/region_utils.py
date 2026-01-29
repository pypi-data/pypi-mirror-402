"""
AWS Region utilities for multi-region operations.

Provides enterprise-grade region discovery and management for runbooks package.
Supports multi-region inventory discovery and operational automation.

Following KISS & DRY principles - enhance existing infrastructure patterns.
"""

import boto3
from typing import List, Optional
from botocore.exceptions import ClientError


def get_enabled_regions(profile: Optional[str] = None) -> List[str]:
    """
    Get all enabled AWS regions for the account.

    Queries EC2 DescribeRegions API to find all regions that are either:
    - opt-in-not-required (standard regions, always enabled)
    - opted-in (opt-in regions that have been explicitly enabled)

    Args:
        profile: AWS profile name (optional). If None, uses default credentials.

    Returns:
        List of enabled region names (e.g., ['ap-southeast-2', 'us-east-1', ...])

    Example:
        >>> # Get all enabled regions for default profile
        >>> regions = get_enabled_regions()
        >>> print(f"Found {len(regions)} enabled regions")

        >>> # Get enabled regions for specific profile
        >>> regions = get_enabled_regions(profile='my-sso-profile')
        >>> # Returns: ['ap-southeast-2', 'ap-southeast-6', 'us-east-1', ...]

    Note:
        - Uses ap-southeast-2 as the base region for the API call
        - Filters out disabled regions (opt-in-status='not-opted-in')
        - Typical AWS account has 17-33 enabled regions
    """
    try:
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        ec2 = session.client("ec2", region_name="ap-southeast-2")

        response = ec2.describe_regions(
            Filters=[{"Name": "opt-in-status", "Values": ["opt-in-not-required", "opted-in"]}]
        )

        regions = [region["RegionName"] for region in response["Regions"]]
        return sorted(regions)  # Sort for consistent ordering

    except ClientError as e:
        # Handle permission errors gracefully
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code in ["AccessDenied", "UnauthorizedOperation"]:
            # Fallback to common regions if DescribeRegions fails
            return [
                "ap-southeast-2",  # Sydney (default)
                "ap-southeast-6",  # Melbourne
                "us-east-1",  # N. Virginia
                "us-west-2",  # Oregon
                "eu-west-1",  # Ireland
            ]
        raise


def get_default_region(profile: Optional[str] = None) -> str:
    """
    Get the default region for the specified profile.

    Args:
        profile: AWS profile name (optional)

    Returns:
        Default region name (e.g., 'ap-southeast-2')

    Example:
        >>> region = get_default_region(profile='my-profile')
        >>> # Returns: 'ap-southeast-2'
    """
    try:
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        return session.region_name or "ap-southeast-2"
    except Exception:
        return "ap-southeast-2"  # Fallback to Sydney


def validate_region(region: str, profile: Optional[str] = None) -> bool:
    """
    Validate if a region is enabled for the account.

    Args:
        region: AWS region name to validate
        profile: AWS profile name (optional)

    Returns:
        True if region is enabled, False otherwise

    Example:
        >>> if validate_region('ap-southeast-2'):
        ...     print("Region is enabled")
    """
    try:
        enabled_regions = get_enabled_regions(profile)
        return region in enabled_regions
    except Exception:
        return False


def parse_region_list(regions_str: str) -> List[str]:
    """
    Parse comma or space-separated region string into list.

    Args:
        regions_str: Region string (e.g., "ap-southeast-2,us-east-1" or "ap-southeast-2 us-east-1")

    Returns:
        List of region names

    Example:
        >>> regions = parse_region_list("ap-southeast-2,us-east-1,eu-west-1")
        >>> # Returns: ['ap-southeast-2', 'us-east-1', 'eu-west-1']

        >>> regions = parse_region_list("ap-southeast-2 us-east-1")
        >>> # Returns: ['ap-southeast-2', 'us-east-1']
    """
    if not regions_str:
        return []

    # Support both comma and space separation
    if "," in regions_str:
        regions = [r.strip() for r in regions_str.split(",")]
    else:
        regions = regions_str.split()

    # Remove empty strings and duplicates
    return list(filter(None, set(regions)))
