#!/usr/bin/env python3
"""Centralized AWS client factory for runbooks automation.

Eliminates duplication of boto3 client creation across 30+ finops files.
Implements session caching and consistent error handling.

Strategic Achievement: DRY principle enforcement for AWS client management
Business Impact: Reduces maintenance overhead and ensures consistency
Technical Foundation: Centralized session management with LRU caching

Author: Runbooks Team
Version: 1.0.0
"""

import boto3
from functools import lru_cache
from typing import Any, Optional

from botocore.config import Config


class AWSClientFactory:
    """Factory for creating AWS service clients with session caching."""

    @staticmethod
    @lru_cache(maxsize=128)
    def create_cached_session(profile: str, region: str = "ap-southeast-2") -> boto3.Session:
        """Create and cache boto3 session for reuse.

        Args:
            profile: AWS profile name
            region: AWS region (default: ap-southeast-2)

        Returns:
            Cached boto3.Session instance

        Example:
            >>> session = AWSClientFactory.create_cached_session("my-profile")
            >>> session.region_name
            'ap-southeast-2'
        """
        return boto3.Session(profile_name=profile, region_name=region)

    @staticmethod
    def create_client(service: str, profile: str, region: str = "ap-southeast-2", **kwargs) -> Any:
        """Create AWS service client using cached session.

        Args:
            service: AWS service name ('ce', 'ec2', 'rds', etc.)
            profile: AWS profile name
            region: AWS region
            **kwargs: Additional boto3.client() parameters

        Returns:
            boto3 service client

        Example:
            >>> ce_client = AWSClientFactory.create_client('ce', 'my-profile')
            >>> ec2_client = AWSClientFactory.create_client('ec2', 'my-profile', region='us-east-1')
        """
        session = AWSClientFactory.create_cached_session(profile, region)

        # Apply default config if not provided
        if "config" not in kwargs:
            kwargs["config"] = Config(
                retries={"max_attempts": 3, "mode": "standard"},
                max_pool_connections=50,
            )

        return session.client(service, **kwargs)


# Convenience functions for common services
def create_cost_explorer_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create Cost Explorer client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        Cost Explorer boto3 client

    Example:
        >>> ce_client = create_cost_explorer_client('my-profile')
        >>> ce_client.get_cost_and_usage(...)
    """
    return AWSClientFactory.create_client("ce", profile, region)


def create_ec2_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create EC2 client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        EC2 boto3 client

    Example:
        >>> ec2_client = create_ec2_client('my-profile')
        >>> ec2_client.describe_instances(...)
    """
    return AWSClientFactory.create_client("ec2", profile, region)


def create_rds_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create RDS client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        RDS boto3 client

    Example:
        >>> rds_client = create_rds_client('my-profile')
        >>> rds_client.describe_db_instances(...)
    """
    return AWSClientFactory.create_client("rds", profile, region)


def create_s3_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create S3 client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        S3 boto3 client

    Example:
        >>> s3_client = create_s3_client('my-profile')
        >>> s3_client.list_buckets()
    """
    return AWSClientFactory.create_client("s3", profile, region)


def create_cloudwatch_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create CloudWatch client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        CloudWatch boto3 client

    Example:
        >>> cw_client = create_cloudwatch_client('my-profile')
        >>> cw_client.get_metric_statistics(...)
    """
    return AWSClientFactory.create_client("cloudwatch", profile, region)


def create_lambda_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create Lambda client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        Lambda boto3 client

    Example:
        >>> lambda_client = create_lambda_client('my-profile')
        >>> lambda_client.list_functions()
    """
    return AWSClientFactory.create_client("lambda", profile, region)


def create_workspaces_client(profile: str, region: str = "ap-southeast-2") -> Any:
    """Create WorkSpaces client.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        WorkSpaces boto3 client

    Example:
        >>> ws_client = create_workspaces_client('my-profile')
        >>> ws_client.describe_workspaces()
    """
    return AWSClientFactory.create_client("workspaces", profile, region)
