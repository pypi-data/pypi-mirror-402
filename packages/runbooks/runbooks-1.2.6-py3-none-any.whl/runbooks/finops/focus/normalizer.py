"""
FOCUS 1.3 Cost Normalizer

Transforms AWS and Azure cost data into FOCUS 1.3 compliant schema.
Implements the FinOps Open Cost and Usage Specification (Version 1.3, ratified December 5, 2025).

Key FOCUS 1.3 Updates:
- ServiceProvider/HostProvider columns (NEW) - distinguishes billing entities
- SplitCostAllocation columns (NEW) - exposes cost splitting methodology
- ContractCommitment dataset (NEW) - RI/Savings Plan tracking
- Deprecated: Provider, Publisher columns (remove in 1.4)

References:
- https://focus.finops.org/focus-specification/
- https://www.finops.org/insights/introducing-focus-1-3/
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ==============================================================================
# FOCUS 1.3 Schema Definition
# ==============================================================================

FOCUS_1_3_SCHEMA = {
    # Dimensions (Categorical)
    "BillingAccountId": str,
    "BillingAccountName": str,
    "SubAccountId": str,
    "SubAccountName": str,
    # NEW in 1.3
    "ServiceProvider": str,
    "HostProvider": str,
    # Service
    "ServiceName": str,
    "ServiceCategory": str,
    "ResourceId": str,
    "ResourceName": str,
    "ResourceType": str,
    # Location
    "Region": str,
    "AvailabilityZone": str,
    # Time
    "BillingPeriodStart": datetime,
    "BillingPeriodEnd": datetime,
    "ChargePeriodStart": datetime,
    "ChargePeriodEnd": datetime,
    # Charge
    "ChargeCategory": str,
    "ChargeClass": str,
    "ChargeFrequency": str,
    # Pricing
    "PricingCategory": str,
    "PricingUnit": str,
    # Metrics (Numeric)
    "BilledCost": Decimal,
    "EffectiveCost": Decimal,
    "ListCost": Decimal,
    "UsageQuantity": Decimal,
    "UsageUnit": str,
    "BillingCurrency": str,
    # NEW in 1.3: Split Cost Allocation
    "SplitCostAllocationMethod": str,
    "SplitCostAllocationSource": str,
    # Custom dimensions (x_ prefix)
    "x_CostCenter": str,
    "x_Project": str,
    "x_Environment": str,
    "x_Owner": str,
    "x_Application": str,
    "x_LineOfBusiness": str,
}

# Required columns for FOCUS 1.3 compliance
FOCUS_REQUIRED_COLUMNS = [
    "BilledCost",
    "BillingCurrency",
    "ServiceName",
    "SubAccountId",
    "ChargePeriodStart",
    "ServiceProvider",  # NEW in 1.3
    "HostProvider",     # NEW in 1.3
]

# Deprecated columns (to be removed in 1.4)
DEPRECATED_COLUMNS = ["Provider", "Publisher"]


# ==============================================================================
# AWS to FOCUS 1.3 Mapping
# ==============================================================================

AWS_TO_FOCUS_1_3 = {
    # Account
    "bill/BillingAccountId": "BillingAccountId",
    "bill/PayerAccountId": "BillingAccountId",
    "bill/PayerAccountName": "BillingAccountName",
    "lineItem/UsageAccountId": "SubAccountId",
    "lineItem/UsageAccountName": "SubAccountName",
    # Provider (NEW in 1.3)
    "bill/BillingEntity": "ServiceProvider",
    # Service
    "product/ProductName": "ServiceName",
    "product/servicecode": "ServiceCategory",
    "lineItem/ResourceId": "ResourceId",
    "product/instanceType": "ResourceType",
    # Location
    "product/region": "Region",
    "lineItem/AvailabilityZone": "AvailabilityZone",
    # Time
    "bill/BillingPeriodStartDate": "BillingPeriodStart",
    "bill/BillingPeriodEndDate": "BillingPeriodEnd",
    "lineItem/UsageStartDate": "ChargePeriodStart",
    "lineItem/UsageEndDate": "ChargePeriodEnd",
    # Charge
    "lineItem/LineItemType": "ChargeCategory",
    "lineItem/LineItemDescription": "ChargeClass",
    # Pricing
    "pricing/term": "PricingCategory",
    "pricing/unit": "PricingUnit",
    # Metrics
    "lineItem/BlendedCost": "BilledCost",
    "lineItem/UnblendedCost": "BilledCost",
    "reservation/EffectiveCost": "EffectiveCost",
    "savingsPlan/SavingsPlanEffectiveCost": "EffectiveCost",
    "pricing/publicOnDemandCost": "ListCost",
    "lineItem/UsageAmount": "UsageQuantity",
    "lineItem/CurrencyCode": "BillingCurrency",
    # Tags
    "resourceTags/user:CostCenter": "x_CostCenter",
    "resourceTags/user:Project": "x_Project",
    "resourceTags/user:Environment": "x_Environment",
    "resourceTags/user:Owner": "x_Owner",
    "resourceTags/user:Application": "x_Application",
}

# AWS ChargeCategory mapping
AWS_CHARGE_CATEGORY_MAP = {
    "Usage": "Usage",
    "Tax": "Tax",
    "Fee": "Purchase",
    "Credit": "Credit",
    "Refund": "Adjustment",
    "DiscountedUsage": "Usage",
    "RIFee": "Purchase",
    "SavingsPlanCoveredUsage": "Usage",
    "SavingsPlanNegation": "Adjustment",
    "SavingsPlanRecurringFee": "Purchase",
}

# AWS PricingCategory mapping
AWS_PRICING_CATEGORY_MAP = {
    "OnDemand": "On-Demand",
    "Reserved": "Commitment",
    "Spot": "Dynamic",
    "SavingsPlan": "Commitment",
}


# ==============================================================================
# Azure to FOCUS 1.3 Mapping
# ==============================================================================

AZURE_TO_FOCUS_1_3 = {
    # Account
    "BillingAccountId": "BillingAccountId",
    "BillingAccountName": "BillingAccountName",
    "SubscriptionId": "SubAccountId",
    "SubscriptionName": "SubAccountName",
    # Provider (NEW in 1.3)
    "PublisherType": "ServiceProvider",
    "PublisherName": "ServiceProvider",
    # Service
    "ServiceName": "ServiceName",
    "MeterCategory": "ServiceName",
    "ServiceFamily": "ServiceCategory",
    "ResourceId": "ResourceId",
    "ResourceName": "ResourceName",
    "MeterSubCategory": "ResourceType",
    # Location
    "ResourceLocation": "Region",
    "ResourceLocationNormalized": "Region",
    # Time
    "BillingPeriodStartDate": "BillingPeriodStart",
    "BillingPeriodEndDate": "BillingPeriodEnd",
    "Date": "ChargePeriodStart",
    "UsageDate": "ChargePeriodStart",
    # Charge
    "ChargeType": "ChargeCategory",
    "Frequency": "ChargeFrequency",
    # Pricing
    "PricingModel": "PricingCategory",
    "UnitOfMeasure": "PricingUnit",
    # Metrics
    "CostInBillingCurrency": "BilledCost",
    "Cost": "BilledCost",
    "EffectivePrice": "EffectiveCost",
    "PayGPrice": "ListCost",
    "UnitPrice": "ListCost",
    "Quantity": "UsageQuantity",
    "BillingCurrency": "BillingCurrency",
    "Currency": "BillingCurrency",
}

# Azure tag column patterns
AZURE_TAG_PATTERNS = {
    "Tags.CostCenter": "x_CostCenter",
    "Tags.Project": "x_Project",
    "Tags.Environment": "x_Environment",
    "Tags.Owner": "x_Owner",
    "tags/CostCenter": "x_CostCenter",
    "tags/Project": "x_Project",
    "tags/Environment": "x_Environment",
    "tags/Owner": "x_Owner",
}

# Azure ChargeCategory mapping
AZURE_CHARGE_CATEGORY_MAP = {
    "Usage": "Usage",
    "Purchase": "Purchase",
    "Tax": "Tax",
    "Refund": "Adjustment",
    "UnusedReservation": "Adjustment",
    "UnusedSavingsPlan": "Adjustment",
}

# Azure PricingCategory mapping
AZURE_PRICING_CATEGORY_MAP = {
    "OnDemand": "On-Demand",
    "Reservation": "Commitment",
    "SavingsPlan": "Commitment",
    "Spot": "Dynamic",
}


# ==============================================================================
# FOCUS Normalizer Class
# ==============================================================================

class FocusNormalizer:
    """
    Transforms cloud cost data into FOCUS 1.3 compliant schema.

    Example:
        >>> normalizer = FocusNormalizer(version="1.3")
        >>> aws_focus = normalizer.normalize_aws(aws_df)
        >>> azure_focus = normalizer.normalize_azure(azure_df)
        >>> combined = normalizer.merge([aws_focus, azure_focus])
    """

    def __init__(self, version: str = "1.3"):
        """
        Initialize normalizer.

        Args:
            version: FOCUS specification version (default: "1.3")
        """
        if version not in ["1.2", "1.3"]:
            raise ValueError(f"Unsupported FOCUS version: {version}. Use '1.2' or '1.3'")
        self.version = version
        self.schema = FOCUS_1_3_SCHEMA

    def normalize_aws(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize AWS Cost and Usage Report data to FOCUS 1.3.

        Args:
            df: Raw AWS CUR DataFrame

        Returns:
            FOCUS 1.3 compliant DataFrame
        """
        # Make a copy to avoid modifying original
        result = df.copy()

        # Rename columns using mapping
        rename_map = {}
        for aws_col, focus_col in AWS_TO_FOCUS_1_3.items():
            if aws_col in result.columns:
                rename_map[aws_col] = focus_col

        result = result.rename(columns=rename_map)

        # Add HostProvider (always AWS for native services)
        result["HostProvider"] = "AWS"

        # Set ServiceProvider if not mapped (default to AWS)
        if "ServiceProvider" not in result.columns or result["ServiceProvider"].isna().all():
            result["ServiceProvider"] = "AWS"

        # Map ChargeCategory values
        if "ChargeCategory" in result.columns:
            result["ChargeCategory"] = result["ChargeCategory"].map(
                AWS_CHARGE_CATEGORY_MAP
            ).fillna("Usage")

        # Map PricingCategory values
        if "PricingCategory" in result.columns:
            result["PricingCategory"] = result["PricingCategory"].map(
                AWS_PRICING_CATEGORY_MAP
            ).fillna("On-Demand")

        # Ensure required columns exist
        result = self._ensure_required_columns(result)

        # Remove deprecated columns
        result = self._remove_deprecated_columns(result)

        # Add metadata
        result["_source_cloud"] = "AWS"
        result["_focus_version"] = self.version

        return result

    def normalize_azure(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize Azure Cost Management data to FOCUS 1.3.

        Args:
            df: Raw Azure Cost Management DataFrame

        Returns:
            FOCUS 1.3 compliant DataFrame
        """
        result = df.copy()

        # Rename columns using mapping
        rename_map = {}
        for azure_col, focus_col in AZURE_TO_FOCUS_1_3.items():
            if azure_col in result.columns:
                rename_map[azure_col] = focus_col

        result = result.rename(columns=rename_map)

        # Handle tag columns (Azure uses various patterns)
        for azure_tag, focus_tag in AZURE_TAG_PATTERNS.items():
            if azure_tag in result.columns:
                result[focus_tag] = result[azure_tag]

        # Add HostProvider (always Azure for native services)
        result["HostProvider"] = "Azure"

        # Set ServiceProvider if not mapped (default to Azure)
        if "ServiceProvider" not in result.columns or result["ServiceProvider"].isna().all():
            result["ServiceProvider"] = "Azure"

        # Map ChargeCategory values
        if "ChargeCategory" in result.columns:
            result["ChargeCategory"] = result["ChargeCategory"].map(
                AZURE_CHARGE_CATEGORY_MAP
            ).fillna("Usage")

        # Map PricingCategory values
        if "PricingCategory" in result.columns:
            result["PricingCategory"] = result["PricingCategory"].map(
                AZURE_PRICING_CATEGORY_MAP
            ).fillna("On-Demand")

        # Ensure required columns exist
        result = self._ensure_required_columns(result)

        # Remove deprecated columns
        result = self._remove_deprecated_columns(result)

        # Add metadata
        result["_source_cloud"] = "Azure"
        result["_focus_version"] = self.version

        return result

    def merge(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Merge multiple FOCUS-normalized DataFrames.

        Args:
            dataframes: List of FOCUS 1.3 compliant DataFrames

        Returns:
            Combined DataFrame with consistent schema
        """
        if not dataframes:
            return pd.DataFrame()

        # Concatenate all DataFrames
        combined = pd.concat(dataframes, ignore_index=True)

        # Ensure consistent column order
        focus_columns = list(self.schema.keys())
        existing_columns = [c for c in focus_columns if c in combined.columns]
        other_columns = [c for c in combined.columns if c not in focus_columns]

        combined = combined[existing_columns + other_columns]

        return combined

    def validate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate DataFrame against FOCUS 1.3 specification.

        Args:
            df: DataFrame to validate

        Returns:
            Validation result dict with compliance status and details
        """
        issues = []
        warnings = []

        # Check required columns
        for col in FOCUS_REQUIRED_COLUMNS:
            if col not in df.columns:
                issues.append(f"Missing required column: {col}")
            elif df[col].isna().all():
                warnings.append(f"Required column '{col}' has all null values")

        # Check for deprecated columns
        for col in DEPRECATED_COLUMNS:
            if col in df.columns:
                warnings.append(f"Deprecated column found: {col} (remove in FOCUS 1.4)")

        # Check ServiceProvider/HostProvider (NEW in 1.3)
        if self.version == "1.3":
            if "ServiceProvider" not in df.columns:
                issues.append("Missing FOCUS 1.3 required column: ServiceProvider")
            if "HostProvider" not in df.columns:
                issues.append("Missing FOCUS 1.3 required column: HostProvider")

        # Check BilledCost is numeric
        if "BilledCost" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["BilledCost"]):
                issues.append("BilledCost must be numeric")

        # Calculate tag coverage
        tag_coverage = {}
        for tag_col in ["x_CostCenter", "x_Project", "x_Environment", "x_Owner"]:
            if tag_col in df.columns:
                coverage = (df[tag_col].notna().sum() / len(df)) * 100
                tag_coverage[tag_col] = round(coverage, 2)

        return {
            "compliant": len(issues) == 0,
            "version": self.version,
            "record_count": len(df),
            "issues": issues,
            "warnings": warnings,
            "tag_coverage": tag_coverage,
            "columns_present": list(df.columns),
            "required_columns_present": [c for c in FOCUS_REQUIRED_COLUMNS if c in df.columns],
        }

    def _ensure_required_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required columns exist (with None if missing)."""
        for col in FOCUS_REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df

    def _remove_deprecated_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove deprecated columns from DataFrame."""
        for col in DEPRECATED_COLUMNS:
            if col in df.columns:
                df = df.drop(columns=[col])
        return df

    def to_jsonl(self, df: pd.DataFrame, output_path: Path) -> None:
        """
        Export DataFrame to JSONL format (one JSON object per line).

        Args:
            df: FOCUS DataFrame
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_json(output_path, orient="records", lines=True, date_format="iso")

    def to_json(self, df: pd.DataFrame, output_path: Path) -> None:
        """
        Export DataFrame to JSON format.

        Args:
            df: FOCUS DataFrame
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_json(output_path, orient="records", indent=2, date_format="iso")


# ==============================================================================
# Cost Aggregator Class
# ==============================================================================

class CostAggregator:
    """
    Aggregates cost data across multiple dimensions.

    Following Microsoft FinOps Toolkit Hub patterns for multi-cloud aggregation.
    """

    def __init__(self, normalizer: Optional[FocusNormalizer] = None):
        """
        Initialize aggregator.

        Args:
            normalizer: FocusNormalizer instance (created if not provided)
        """
        self.normalizer = normalizer or FocusNormalizer(version="1.3")

    def aggregate_by_subscription(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate costs by SubAccount (AWS Account / Azure Subscription)."""
        return df.groupby(["ServiceProvider", "SubAccountId", "SubAccountName"]).agg({
            "BilledCost": "sum",
            "EffectiveCost": lambda x: x.sum() if x.notna().any() else None,
        }).reset_index().sort_values("BilledCost", ascending=False)

    def aggregate_by_service(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate costs by Service."""
        return df.groupby(["ServiceProvider", "ServiceName"]).agg({
            "BilledCost": "sum",
            "UsageQuantity": lambda x: x.sum() if x.notna().any() else None,
        }).reset_index().sort_values("BilledCost", ascending=False)

    def aggregate_by_costcenter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate costs by CostCenter (showback)."""
        return df.groupby("x_CostCenter").agg({
            "BilledCost": "sum",
            "ServiceProvider": lambda x: list(x.unique()),
        }).reset_index().sort_values("BilledCost", ascending=False)

    def aggregate_by_region(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate costs by Region."""
        return df.groupby(["ServiceProvider", "Region"]).agg({
            "BilledCost": "sum",
        }).reset_index().sort_values("BilledCost", ascending=False)

    def generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics.

        Args:
            df: FOCUS DataFrame

        Returns:
            Summary dict with KPIs
        """
        return {
            "total_cost": float(df["BilledCost"].sum()),
            "by_cloud": df.groupby("ServiceProvider")["BilledCost"].sum().to_dict(),
            "record_count": len(df),
            "unique_accounts": df["SubAccountId"].nunique(),
            "unique_services": df["ServiceName"].nunique(),
            "unique_regions": df["Region"].nunique() if "Region" in df.columns else 0,
            "tag_coverage": {
                "x_CostCenter": (df["x_CostCenter"].notna().sum() / len(df) * 100) if "x_CostCenter" in df.columns else 0,
                "x_Project": (df["x_Project"].notna().sum() / len(df) * 100) if "x_Project" in df.columns else 0,
                "x_Environment": (df["x_Environment"].notna().sum() / len(df) * 100) if "x_Environment" in df.columns else 0,
            },
            "focus_version": self.normalizer.version,
            "generated_at": datetime.now().isoformat(),
        }
