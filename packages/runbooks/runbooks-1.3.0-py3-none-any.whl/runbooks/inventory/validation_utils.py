"""
Shared Validation Utilities for Organizations Readiness Checks

This module provides reusable validation functions for Landing Zone and Control Tower
readiness assessments, implementing DRY principles across multiple validation scripts.

Architecture:
    - Shared validation patterns for check_landingzone_readiness.py
    - Common functions for check_controltower_readiness.py
    - Centralized readiness scoring algorithm
    - Consistent error handling and logging

Version: 1.1.10 (Modern CLI integration patterns)
"""

import logging
from typing import Tuple, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def validate_organizations_enabled(profile: str, region: str = "ap-southeast-2") -> Tuple[bool, str, str, Dict]:
    """
    Validate Organizations is enabled with all features.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        Tuple of (success: bool, check_name: str, message: str, details: dict)
            success: True if Organizations enabled with all features
            check_name: Name of the validation check
            message: Human-readable validation message
            details: Additional metadata (organization_id, master_account, feature_set)
    """
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        org_client = session.client("organizations")

        org_info = org_client.describe_organization()
        organization = org_info["Organization"]

        feature_set = organization.get("FeatureSet", "CONSOLIDATED_BILLING")
        org_id = organization.get("Id", "N/A")
        master_account = organization.get("MasterAccountId", "N/A")

        details = {
            "organization_id": org_id,
            "master_account": master_account,
            "feature_set": feature_set,
            "available_policy_types": organization.get("AvailablePolicyTypes", []),
        }

        if feature_set == "ALL":
            message = f"Organizations enabled with ALL features (Org: {org_id})"
            return True, "organizations_enabled", message, details
        else:
            message = f"Organizations enabled but using {feature_set} mode (ALL features required)"
            return False, "organizations_enabled", message, details

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "AWSOrganizationsNotInUseException":
            message = "AWS Organizations not enabled for this account"
        elif error_code == "AccessDeniedException":
            message = "Access denied - requires organizations:DescribeOrganization permission"
        else:
            message = f"Organizations validation failed: {error_code}"

        details = {"error": str(e), "error_code": error_code}
        return False, "organizations_enabled", message, details

    except Exception as e:
        message = f"Unexpected error validating Organizations: {str(e)}"
        details = {"error": str(e)}
        return False, "organizations_enabled", message, details


def validate_iam_role_exists(
    profile: str, role_name: str, region: str = "ap-southeast-2"
) -> Tuple[bool, str, str, Dict]:
    """
    Validate specific IAM role exists in account.

    Args:
        profile: AWS profile name
        role_name: IAM role name to check
        region: AWS region (default: ap-southeast-2)

    Returns:
        Tuple of (exists: bool, check_name: str, message: str, details: dict)
            exists: True if role found
            check_name: Name of the validation check
            message: Human-readable validation message
            details: Role metadata (arn, creation_date, trust_policy)
    """
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        iam_client = session.client("iam")

        role = iam_client.get_role(RoleName=role_name)
        role_info = role["Role"]

        details = {
            "role_name": role_name,
            "role_arn": role_info.get("Arn", "N/A"),
            "creation_date": str(role_info.get("CreateDate", "N/A")),
            "trust_policy": role_info.get("AssumeRolePolicyDocument", {}),
        }

        message = f"IAM role '{role_name}' exists (ARN: {details['role_arn']})"
        return True, "iam_role_exists", message, details

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "NoSuchEntity":
            message = f"IAM role '{role_name}' not found"
        elif error_code == "AccessDenied":
            message = f"Access denied checking IAM role '{role_name}'"
        else:
            message = f"IAM role validation failed: {error_code}"

        details = {"error": str(e), "error_code": error_code, "role_name": role_name}
        return False, "iam_role_exists", message, details

    except Exception as e:
        message = f"Unexpected error checking IAM role '{role_name}': {str(e)}"
        details = {"error": str(e), "role_name": role_name}
        return False, "iam_role_exists", message, details


def validate_cloudtrail_enabled(profile: str, region: str = "ap-southeast-2") -> Tuple[bool, str, str, Dict]:
    """
    Validate CloudTrail is configured in account.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        Tuple of (enabled: bool, check_name: str, message: str, details: dict)
            enabled: True if CloudTrail configured
            check_name: Name of the validation check
            message: Human-readable validation message
            details: Trail metadata (trail_names, count, multi_region_trails)
    """
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        cloudtrail_client = session.client("cloudtrail")

        trails_response = cloudtrail_client.describe_trails()
        trails = trails_response.get("trailList", [])

        if not trails:
            message = "No CloudTrail trails configured"
            details = {"trail_count": 0, "trails": []}
            return False, "cloudtrail_enabled", message, details

        # Check for multi-region trails
        multi_region_trails = [t for t in trails if t.get("IsMultiRegionTrail", False)]

        trail_names = [t.get("Name", "Unknown") for t in trails]
        details = {
            "trail_count": len(trails),
            "trail_names": trail_names,
            "multi_region_trails": len(multi_region_trails),
            "trails": trails,
        }

        if multi_region_trails:
            message = f"CloudTrail configured with {len(multi_region_trails)} multi-region trail(s)"
            return True, "cloudtrail_enabled", message, details
        else:
            message = f"CloudTrail configured but no multi-region trails ({len(trails)} single-region trail(s))"
            return False, "cloudtrail_enabled", message, details

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        message = f"CloudTrail validation failed: {error_code}"
        details = {"error": str(e), "error_code": error_code}
        return False, "cloudtrail_enabled", message, details

    except Exception as e:
        message = f"Unexpected error validating CloudTrail: {str(e)}"
        details = {"error": str(e)}
        return False, "cloudtrail_enabled", message, details


def validate_config_enabled(profile: str, region: str = "ap-southeast-2") -> Tuple[bool, str, str, Dict]:
    """
    Validate AWS Config is enabled and recording.

    Args:
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)

    Returns:
        Tuple of (enabled: bool, check_name: str, message: str, details: dict)
            enabled: True if Config enabled and recording
            check_name: Name of the validation check
            message: Human-readable validation message
            details: Config metadata (recorders, channels, recording_status)
    """
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        config_client = session.client("config")

        # Check configuration recorders
        recorders_response = config_client.describe_configuration_recorders()
        recorders = recorders_response.get("ConfigurationRecorders", [])

        # Check delivery channels
        channels_response = config_client.describe_delivery_channels()
        channels = channels_response.get("DeliveryChannels", [])

        # Check recording status
        recorder_status = []
        for recorder in recorders:
            try:
                status_response = config_client.describe_configuration_recorder_status(
                    ConfigurationRecorderNames=[recorder["name"]]
                )
                status = status_response.get("ConfigurationRecordersStatus", [])
                recorder_status.extend(status)
            except Exception as e:
                logger.warning(f"Failed to get recorder status: {e}")

        details = {
            "recorders_count": len(recorders),
            "channels_count": len(channels),
            "recorder_names": [r.get("name", "Unknown") for r in recorders],
            "channel_names": [c.get("name", "Unknown") for c in channels],
            "recording_status": recorder_status,
        }

        # Validate complete setup
        if not recorders:
            message = "AWS Config not configured - no configuration recorders found"
            return False, "config_enabled", message, details

        if not channels:
            message = "AWS Config incomplete - no delivery channels configured"
            return False, "config_enabled", message, details

        # Check if recording
        recording = any(status.get("recording", False) for status in recorder_status)

        if recording:
            message = f"AWS Config enabled and recording ({len(recorders)} recorder(s))"
            return True, "config_enabled", message, details
        else:
            message = "AWS Config configured but not recording"
            return False, "config_enabled", message, details

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        message = f"Config validation failed: {error_code}"
        details = {"error": str(e), "error_code": error_code}
        return False, "config_enabled", message, details

    except Exception as e:
        message = f"Unexpected error validating Config: {str(e)}"
        details = {"error": str(e)}
        return False, "config_enabled", message, details


def calculate_readiness_score(checks: List[Tuple[bool, str, str, Dict]]) -> int:
    """
    Calculate 0-100% readiness score from validation checks.

    Args:
        checks: List of validation check results (success, check_name, message, details)

    Returns:
        int: Readiness percentage (0-100)
    """
    if not checks:
        return 0

    passed = sum(1 for check_passed, _, _, _ in checks if check_passed)
    total = len(checks)

    return int((passed / total) * 100) if total > 0 else 0


def generate_remediation_recommendations(checks: List[Tuple[bool, str, str, Dict]]) -> List[Dict[str, str]]:
    """
    Generate remediation recommendations for failed checks.

    Args:
        checks: List of validation check results (success, check_name, message, details)

    Returns:
        List of remediation dictionaries with 'check', 'status', 'remediation' keys
    """
    recommendations = []

    for check_passed, check_name, message, details in checks:
        if not check_passed:
            # Generate remediation based on check type
            remediation = _get_remediation_for_check(check_name, details)

            recommendations.append(
                {
                    "check": check_name,
                    "status": "FAILED",
                    "message": message,
                    "remediation": remediation,
                    "details": details,
                }
            )

    return recommendations


def _get_remediation_for_check(check_name: str, details: Dict) -> str:
    """
    Get specific remediation steps for failed check.

    Args:
        check_name: Name of the validation check
        details: Check details dictionary

    Returns:
        str: Remediation recommendation
    """
    remediations = {
        "organizations_enabled": (
            "Enable AWS Organizations with ALL features: "
            "1. Go to AWS Organizations console\n"
            "2. Create organization if not exists\n"
            "3. Enable ALL features (upgrade from Consolidated Billing if needed)\n"
            "4. Verify feature_set shows 'ALL'"
        ),
        "iam_role_exists": (
            f"Create required IAM role '{details.get('role_name', 'N/A')}': "
            "1. Go to IAM console → Roles\n"
            "2. Create new role with required trust policy\n"
            "3. Attach necessary permissions policies\n"
            "4. Verify role ARN and trust relationships"
        ),
        "cloudtrail_enabled": (
            "Configure CloudTrail with multi-region trail: "
            "1. Go to CloudTrail console\n"
            "2. Create new trail with multi-region option enabled\n"
            "3. Configure S3 bucket for log storage\n"
            "4. Enable log file validation\n"
            "5. Start logging"
        ),
        "config_enabled": (
            "Enable AWS Config with configuration recorder: "
            "1. Go to AWS Config console\n"
            "2. Set up configuration recorder\n"
            "3. Configure delivery channel with S3 bucket\n"
            "4. Start recording\n"
            "5. Verify recording status"
        ),
    }

    return remediations.get(check_name, "Manual remediation required - consult AWS documentation")
