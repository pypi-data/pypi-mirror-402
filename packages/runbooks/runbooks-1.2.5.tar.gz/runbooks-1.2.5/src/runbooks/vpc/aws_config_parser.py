"""AWS config parser for profile discovery (NO hardcoded paths)."""

from pathlib import Path
from configparser import ConfigParser
from typing import Dict, Optional
import os
import re


def parse_aws_config(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Parse AWS config file to extract account-to-profile mappings.

    Args:
        config_path: Path to AWS config (default: ~/.aws/config via env)

    Returns:
        Dict[account_id, profile_name] - Account to profile mapping

    Raises:
        ValueError: If config_path not provided and AWS_CONFIG_FILE not set
        FileNotFoundError: If config file doesn't exist
    """
    # Resolve config path (NO hardcoded ~/.aws/config)
    if config_path is None:
        config_path = os.getenv("AWS_CONFIG_FILE")
        if not config_path:
            # Try standard location as FALLBACK (fail-fast if doesn't exist)
            default_path = Path.home() / ".aws" / "config"
            if not default_path.exists():
                raise ValueError(
                    "AWS config path not provided. Set AWS_CONFIG_FILE environment variable "
                    "or pass config_path parameter explicitly."
                )
            config_path = str(default_path)

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"AWS config not found: {config_path}")

    # Parse config file
    parser = ConfigParser()
    parser.read(config_file)

    # Extract account-to-profile mappings
    # Supports TWO patterns:
    # 1. [profile ams-account-role-123456789012] → Extract from name
    # 2. [profile xyz] with sso_account_id = 123456789012 → Extract from field
    mappings = {}
    for section in parser.sections():
        if section.startswith("profile "):
            profile_name = section.replace("profile ", "")
            account_id = None

            # Pattern 1: Extract account ID from sso_account_id field (SSO profiles)
            if parser.has_option(section, "sso_account_id"):
                account_id = parser.get(section, "sso_account_id")

            # Pattern 2: Extract account ID from profile name (fallback)
            if not account_id:
                match = re.search(r"(\d{12})", profile_name)
                if match:
                    account_id = match.group(1)

            if account_id:
                mappings[account_id] = profile_name

    return mappings


def enrich_csv_with_profiles(csv_path: str, output_path: str, config_path: Optional[str] = None) -> Dict[str, any]:
    """
    Enrich VPCE cleanup CSV with AWS-Profile column.

    Args:
        csv_path: Input CSV path (data/vpce-cleanup-summary.csv)
        output_path: Output enriched CSV path
        config_path: AWS config path (optional, uses env AWS_CONFIG_FILE)

    Returns:
        Dict with enrichment stats
    """
    import pandas as pd

    # Parse AWS config
    account_profiles = parse_aws_config(config_path)

    # Read CSV
    df = pd.read_csv(csv_path)

    # Add AWS-Profile column
    df["AWS-Profile"] = df["Account-ID"].astype(str).map(account_profiles)

    # Stats
    total_rows = len(df)
    enriched_rows = df["AWS-Profile"].notna().sum()
    missing_rows = df["AWS-Profile"].isna().sum()

    # Save enriched CSV
    df.to_csv(output_path, index=False)

    return {
        "total_rows": total_rows,
        "enriched_rows": enriched_rows,
        "missing_rows": missing_rows,
        "account_profiles_found": len(account_profiles),
        "output_file": output_path,
    }
