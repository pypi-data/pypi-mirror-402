"""AWS Profile Validation - Pre-flight STS Checks

Prevents ProfileNotFound errors by validating profiles before API calls.
Enterprise fail-fast pattern with comprehensive validation reporting.

Manager Issue #8: validate the aws account, profiles, vpc first
"""

from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ProfileNotFound, NoCredentialsError, ClientError

from runbooks.common.rich_utils import (
    console,
    print_success,
    print_error,
    print_warning,
    print_info,
    create_table,
)


def validate_profile(profile_name: str, region: str = "ap-southeast-2") -> Dict:
    """
    Validate AWS profile with pre-flight STS check.

    Args:
        profile_name: AWS profile to validate
        region: AWS region for session (default: ap-southeast-2)

    Returns:
        Dict with validation results:
        {
            'valid': bool,
            'account_id': str | None,
            'arn': str | None,
            'user_id': str | None,
            'error': str | None
        }

    Example:
        >>> result = validate_profile("${BILLING_PROFILE}")
        >>> # ✅ Profile validated: account ID extracted from profile
    """
    try:
        # Create session with profile
        session = boto3.Session(profile_name=profile_name, region_name=region)

        # Pre-flight STS check (get caller identity)
        sts_client = session.client("sts")
        identity = sts_client.get_caller_identity()

        return {
            "valid": True,
            "profile_name": profile_name,
            "account_id": identity["Account"],
            "arn": identity["Arn"],
            "user_id": identity["UserId"],
            "error": None,
        }

    except ProfileNotFound as e:
        return {
            "valid": False,
            "profile_name": profile_name,
            "account_id": None,
            "arn": None,
            "user_id": None,
            "error": f"ProfileNotFound: {profile_name} not in ~/.aws/config",
        }

    except NoCredentialsError:
        return {
            "valid": False,
            "profile_name": profile_name,
            "account_id": None,
            "arn": None,
            "user_id": None,
            "error": "NoCredentialsError: AWS credentials not configured",
        }

    except ClientError as e:
        return {
            "valid": False,
            "profile_name": profile_name,
            "account_id": None,
            "arn": None,
            "user_id": None,
            "error": f"ClientError: {e.response['Error']['Code']} - {e.response['Error']['Message']}",
        }

    except Exception as e:
        return {
            "valid": False,
            "profile_name": profile_name,
            "account_id": None,
            "arn": None,
            "user_id": None,
            "error": f"UnexpectedError: {str(e)}",
        }


def validate_profiles_batch(profiles: List[str], region: str = "ap-southeast-2", fail_fast: bool = True) -> Dict:
    """
    Validate multiple AWS profiles with pre-flight STS checks.

    Args:
        profiles: List of AWS profile names to validate
        region: AWS region for sessions
        fail_fast: Stop on first error (default: True)

    Returns:
        Dict with batch validation results:
        {
            'total_profiles': int,
            'valid_profiles': int,
            'invalid_profiles': int,
            'results': Dict[profile_name, validation_result],
            'all_valid': bool
        }

    Raises:
        ValueError: If fail_fast=True and any profile invalid

    Example:
        >>> profiles = ["billing-profile", "management-profile"]
        >>> results = validate_profiles_batch(profiles, fail_fast=True)
        >>> # ✅ All 2 profiles validated successfully
    """
    results = {}
    valid_count = 0
    invalid_count = 0

    for profile_name in profiles:
        result = validate_profile(profile_name, region=region)
        results[profile_name] = result

        if result["valid"]:
            valid_count += 1
            print_success(f"✅ {profile_name}: account {result['account_id']}")
        else:
            invalid_count += 1
            print_error(f"❌ {profile_name}: {result['error']}")

            if fail_fast:
                raise ValueError(f"Profile validation failed: {profile_name} - {result['error']}")

    # Summary
    all_valid = invalid_count == 0

    if all_valid:
        print_success(f"✅ All {valid_count} profiles validated successfully")
    else:
        print_warning(f"⚠️  Profile validation: {valid_count} valid, {invalid_count} invalid")

    return {
        "total_profiles": len(profiles),
        "valid_profiles": valid_count,
        "invalid_profiles": invalid_count,
        "results": results,
        "all_valid": all_valid,
    }


def display_validation_table(validation_results: Dict) -> None:
    """
    Display profile validation results in Rich CLI table.

    Args:
        validation_results: Results from validate_profiles_batch()

    Example:
        >>> results = validate_profiles_batch(profiles)
        >>> display_validation_table(results)
    """
    table = create_table(
        title="AWS Profile Validation Results",
        columns=[
            {"name": "Profile Name", "justify": "left"},
            {"name": "Status", "justify": "center"},
            {"name": "Account ID", "justify": "left"},
            {"name": "Error", "justify": "left"},
        ],
    )

    for profile_name, result in validation_results["results"].items():
        status = "✅ Valid" if result["valid"] else "❌ Invalid"
        account_id = result["account_id"] or "-"
        error = result["error"] or "-"

        table.add_row(profile_name, status, account_id, error)

    console.print(table)


def validate_csv_profiles(csv_path: str, aws_config_path: Optional[str] = None) -> Dict:
    """
    Validate all profiles referenced in VPCE cleanup CSV.

    Args:
        csv_path: Path to CSV with AWS-Profile column
        aws_config_path: Optional AWS config path (uses ~/.aws/config if not provided)

    Returns:
        Dict with validation results for all profiles in CSV

    Raises:
        ValueError: If CSV missing AWS-Profile column
        ValueError: If any profile validation fails

    Example:
        >>> results = validate_csv_profiles("data/vpce-cleanup-summary.csv")
        >>> # ✅ All 4 unique profiles validated successfully
    """
    import pandas as pd
    from pathlib import Path

    # Read CSV
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_file)

    # Check for AWS-Profile column
    if "AWS-Profile" not in df.columns:
        if aws_config_path:
            # Auto-enrich CSV
            from runbooks.vpc.aws_config_parser import enrich_csv_with_profiles

            enriched_csv = csv_file.parent / f"{csv_file.stem}-enriched.csv"
            enrich_csv_with_profiles(str(csv_file), str(enriched_csv), aws_config_path)
            df = pd.read_csv(enriched_csv)
        else:
            raise ValueError(
                f"CSV missing AWS-Profile column. Provide aws_config_path to auto-enrich or add column manually."
            )

    # Extract unique profiles (exclude NaN)
    unique_profiles = df["AWS-Profile"].dropna().unique().tolist()

    print_info(f"🔍 Validating {len(unique_profiles)} unique profiles from {csv_path}")

    # Validate all profiles (fail-fast on errors)
    validation_results = validate_profiles_batch(unique_profiles, fail_fast=True)

    return validation_results


if __name__ == "__main__":
    # Demo: Profile validation
    from runbooks.common.rich_utils import print_header

    print_header("AWS Profile Validator", "Demo")

    # Example 1: Single profile validation
    print_info("\n=== Single Profile Validation ===")
    result = validate_profile("default")

    if result["valid"]:
        print_success(f"✅ Profile 'default' validated: {result['account_id']}")
    else:
        print_error(f"❌ Profile 'default' validation failed: {result['error']}")

    # Example 2: Batch validation
    print_info("\n=== Batch Profile Validation ===")
    test_profiles = [
        "default",
        "non-existent-profile",  # Should fail
    ]

    try:
        batch_results = validate_profiles_batch(test_profiles, fail_fast=False)
        display_validation_table(batch_results)
    except ValueError as e:
        print_error(f"Batch validation failed: {e}")
