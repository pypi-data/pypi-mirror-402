"""
Configuration schema validation for Runbooks.

Provides JSON Schema validation and business rules for hierarchical
tag mapping configuration (user config > project config > env vars > defaults).

This module defines the validation schema for runbooks configuration files,
supporting hierarchical configuration loading with comprehensive validation
rules for AWS tag mappings, coverage requirements, and caching behavior.

Author: CloudOps-Runbooks Enterprise Team
Version: 1.1.10
"""

from typing import Any, Dict, List

# =============================================================================
# JSON SCHEMA VALIDATION
# =============================================================================

TAG_MAPPING_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "runbooks": {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "pattern": r"^\d+\.\d+\.\d+$",  # Semantic versioning (e.g., '1.1.10')
                    "description": "Config schema version following semantic versioning",
                },
                "inventory": {
                    "type": "object",
                    "properties": {
                        "tag_mappings": {
                            "type": "object",
                            "description": "Maps internal field names to AWS tag keys",
                            "patternProperties": {
                                "^[a-z_]+$": {  # Field names: lowercase + underscores only
                                    "type": "string",
                                    "minLength": 1,
                                    "maxLength": 128,  # AWS tag key maximum length
                                    "description": "AWS tag key name (1-128 characters)",
                                }
                            },
                            "additionalProperties": False,  # Strict validation - no unexpected fields
                        },
                        "tag_coverage": {
                            "type": "object",
                            "description": "Tag coverage analysis and reporting configuration",
                            "properties": {
                                "enabled": {
                                    "type": "boolean",
                                    "description": "Enable tag coverage analysis",
                                },
                                "minimum_tier1_coverage": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 100.0,
                                    "description": "Minimum required coverage for Tier 1 tags (percentage)",
                                },
                                "minimum_tier2_coverage": {
                                    "type": "number",
                                    "minimum": 0.0,
                                    "maximum": 100.0,
                                    "description": "Minimum required coverage for Tier 2 tags (percentage)",
                                },
                                "display_recommendations": {
                                    "type": "boolean",
                                    "description": "Display tag coverage improvement recommendations",
                                },
                            },
                        },
                        "cache": {
                            "type": "object",
                            "description": "Inventory data caching configuration",
                            "properties": {
                                "enabled": {
                                    "type": "boolean",
                                    "description": "Enable inventory data caching",
                                },
                                "ttl_seconds": {
                                    "type": "integer",
                                    "minimum": 60,  # Minimum 1 minute
                                    "maximum": 86400,  # Maximum 24 hours
                                    "description": "Cache time-to-live in seconds (60-86400)",
                                },
                            },
                        },
                    },
                },
            },
        }
    },
}


# =============================================================================
# BUSINESS RULES AND VALIDATION CONSTANTS
# =============================================================================

VALIDATION_RULES: Dict[str, Any] = {
    # Allowed field names for tag_mappings configuration
    # These field names follow the lowercase_with_underscores convention
    "allowed_field_names": [
        # TIER 1: Business Metadata (Critical for cost allocation and accountability)
        "wbs_code",  # Work Breakdown Structure code for project tracking
        "cost_group",  # Cost allocation group for financial reporting
        "technical_lead",  # Technical point of contact
        "account_owner",  # AWS account ownership
        # TIER 2: Governance Metadata (Important for organizational structure)
        "business_unit",  # Business unit or division
        "functional_area",  # Functional area within organization
        "managed_by",  # Management responsibility
        "product_owner",  # Product ownership
        # TIER 3: Operational Metadata (Standard operational requirements)
        "purpose",  # Resource purpose or description
        "environment",  # Environment classification (dev, staging, prod)
        "compliance_scope",  # Compliance framework requirements
        "data_classification",  # Data sensitivity classification
        # TIER 4: Extended Metadata (Optional supplementary information)
        "project_name",  # Project name or identifier
        "budget_code",  # Budget allocation code
        "support_tier",  # Support tier classification
        "created_date",  # Resource creation date
        "expiry_date",  # Resource expiration or review date
    ],
    # AWS reserved tag keys that cannot be used for custom mappings
    "reserved_tag_keys": [
        "Name",  # AWS reserved tag key
        "aws:",  # AWS reserved prefix (check using startswith)
    ],
    # Tier definitions for coverage analysis and reporting
    # Maps tier names to their constituent field names
    "tier_definitions": {
        "tier_1": [
            "wbs_code",
            "cost_group",
            "technical_lead",
            "account_owner",
        ],
        "tier_2": [
            "business_unit",
            "functional_area",
            "managed_by",
            "product_owner",
        ],
        "tier_3": [
            "purpose",
            "environment",
            "compliance_scope",
            "data_classification",
        ],
        "tier_4": [
            "project_name",
            "budget_code",
            "support_tier",
            "created_date",
            "expiry_date",
        ],
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_tier_for_field(field_name: str) -> str:
    """
    Determine the tier classification for a given field name.

    Args:
        field_name: The field name to classify (e.g., 'wbs_code', 'environment')

    Returns:
        Tier classification string ('tier_1', 'tier_2', 'tier_3', 'tier_4', or 'unknown')

    Example:
        >>> get_tier_for_field('wbs_code')
        'tier_1'
        >>> get_tier_for_field('environment')
        'tier_3'
    """
    for tier_name, tier_fields in VALIDATION_RULES["tier_definitions"].items():
        if field_name in tier_fields:
            return tier_name
    return "unknown"


def is_reserved_tag_key(tag_key: str) -> bool:
    """
    Check if a tag key is reserved by AWS and cannot be used for custom mappings.

    Reserved tag keys include:
    - 'Name' (AWS standard tag)
    - Any key starting with 'aws:' (AWS system tags)

    Args:
        tag_key: The AWS tag key to validate

    Returns:
        True if the tag key is reserved, False otherwise

    Example:
        >>> is_reserved_tag_key('Name')
        True
        >>> is_reserved_tag_key('aws:cloudformation:stack-name')
        True
        >>> is_reserved_tag_key('CostCenter')
        False
    """
    reserved_keys = VALIDATION_RULES["reserved_tag_keys"]
    if tag_key in reserved_keys:
        return True
    # Check for aws: prefix
    if tag_key.startswith("aws:"):
        return True
    return False


def get_allowed_field_names() -> List[str]:
    """
    Get the complete list of allowed field names for tag mappings.

    Returns:
        List of allowed field names across all tiers

    Example:
        >>> fields = get_allowed_field_names()
        >>> 'wbs_code' in fields
        True
        >>> len(fields) > 0
        True
    """
    return VALIDATION_RULES["allowed_field_names"]


def validate_field_name_format(field_name: str) -> bool:
    """
    Validate that a field name follows the required format.

    Field names must:
    - Use lowercase letters only
    - Use underscores for word separation
    - Match pattern: ^[a-z_]+$

    Args:
        field_name: The field name to validate

    Returns:
        True if field name format is valid, False otherwise

    Example:
        >>> validate_field_name_format('wbs_code')
        True
        >>> validate_field_name_format('WBS_Code')
        False
        >>> validate_field_name_format('wbs-code')
        False
    """
    import re

    pattern = r"^[a-z_]+$"
    return bool(re.match(pattern, field_name))


# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    "TAG_MAPPING_SCHEMA",
    "VALIDATION_RULES",
    "get_tier_for_field",
    "is_reserved_tag_key",
    "get_allowed_field_names",
    "validate_field_name_format",
]
