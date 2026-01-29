"""
Azure FinOps Type Definitions - FOCUS 1.3 Aligned

Type definitions for Azure Cost Management data, aligned with:
- runbooks.finops.types pattern (TypedDict)
- FOCUS 1.3 schema (ratified Dec 5, 2025)
- Microsoft FinOps Toolkit conventions

Migration: Copy to runbooks/finops/azure_types.py

References:
- FOCUS Schema: https://learn.microsoft.com/azure/cost-management-billing/dataset-schema/cost-usage-details-focus
- runbooks.finops.types: /CloudOps-Runbooks/src/runbooks/finops/types.py

Framework: ADLC v3.0.0 | Version: 1.0.0
"""

from typing import Dict, List, Optional, TypedDict


# =============================================================================
# FOCUS 1.3 Core Types (ratified Dec 5, 2025)
# =============================================================================


class FOCUSCostRecord(TypedDict, total=False):
    """
    FOCUS 1.3 cost record - key columns for Azure Cost Management.

    Full schema has 105 columns. This TypedDict includes the most commonly used
    columns for cost analysis and reporting. Additional x_ prefixed columns are
    Microsoft-specific extensions.
    """

    # Billing columns
    BilledCost: float
    BillingAccountId: str
    BillingAccountName: str
    BillingCurrency: str
    BillingPeriodStart: str  # ISO 8601
    BillingPeriodEnd: str  # ISO 8601

    # Charge classification
    ChargeCategory: str  # Usage, Purchase, Tax, Adjustment
    ChargeDescription: str
    ChargeFrequency: str  # One-Time, Recurring, Usage-Based
    ChargePeriodStart: str
    ChargePeriodEnd: str

    # Cost calculations
    ListCost: float
    ContractedCost: float
    EffectiveCost: float  # Amortized cost after discounts
    ListUnitPrice: float
    ContractedUnitPrice: float

    # USD conversions (Microsoft extension)
    x_BilledCostInUsd: float
    x_EffectiveCostInUsd: float

    # Resource identification
    ResourceId: str
    ResourceName: str
    ResourceType: str
    RegionId: str
    RegionName: str
    x_ResourceGroupName: str

    # Service classification
    ServiceCategory: str
    ServiceName: str
    ServiceSubcategory: str

    # Subscription/Account
    SubAccountId: str  # Subscription ID
    SubAccountName: str  # Subscription Name
    x_BillingProfileId: str
    x_BillingProfileName: str
    x_InvoiceSectionId: str
    x_InvoiceSectionName: str

    # SKU details
    SkuId: str
    SkuMeter: str
    PricingCategory: str  # On-Demand, Commitment, Dynamic
    PricingCurrency: str

    # Usage quantities
    ConsumedQuantity: float
    ConsumedUnit: str
    PricingQuantity: float
    PricingUnit: str

    # Commitment discounts (RI, Savings Plans)
    CommitmentDiscountCategory: str
    CommitmentDiscountId: str
    CommitmentDiscountName: str
    CommitmentDiscountStatus: str  # Used, Unused
    CommitmentDiscountType: str

    # Tags
    Tags: Dict[str, str]

    # Invoice
    InvoiceId: str
    InvoiceIssuerName: str

    # Provider
    ProviderName: str
    PublisherName: str


# =============================================================================
# Azure Cost Data Types (aligned with runbooks.finops.types)
# =============================================================================


class AzureServiceCost(TypedDict):
    """Cost breakdown by Azure service (aligned with runbooks pattern)."""

    service_name: str
    cost_nzd: float
    cost_usd: float
    percentage: float
    cost_tier: str  # HIGH, MEDIUM, LOW
    rank: int


class AzureSubscriptionCost(TypedDict):
    """Cost breakdown by Azure subscription."""

    subscription_name: str
    subscription_id: str
    enrollment_account: str
    cost_nzd: float
    cost_usd: float
    percentage: float
    cost_tier: str
    rank: int


class AzureCostData(TypedDict):
    """
    Azure cost data structure (aligned with runbooks.finops.types.CostData).

    Maintains compatibility with runbooks.finops patterns while supporting
    Azure-specific fields and FOCUS 1.2 schema.
    """

    # Customer identification
    customer_name: str
    customer_id: str
    billing_period: str
    date_range: str

    # Cost totals (dual currency - FOCUS 1.3)
    total_cost_nzd: float
    total_cost_usd: float
    billing_currency: str

    # Cost breakdowns
    services: List[AzureServiceCost]
    subscriptions: List[AzureSubscriptionCost]

    # Top items (for executive summary)
    top_services: List[AzureServiceCost]
    top_subscriptions: List[AzureSubscriptionCost]

    # Cost tier distribution
    high_cost_count: int
    medium_cost_count: int
    low_cost_count: int

    # Metadata
    total_services: int
    total_subscriptions: int

    # Executive narrative
    narrative: str

    # Data source info
    source_files: List[str]
    focus_version: str  # "1.3" (ratified Dec 5, 2025)


class AzureExportMetadata(TypedDict):
    """Metadata for Azure Cost Management export files."""

    export_name: str
    export_type: str  # ActualCost, AmortizedCost
    time_frame: str
    granularity: str  # Daily, Monthly
    focus_version: str
    file_path: str
    row_count: int


# =============================================================================
# Cost Tier Classification (consistent with runbooks.finops)
# =============================================================================


def classify_cost_tier(
    cost: float,
    high_threshold: float = 5000.0,
    medium_threshold: float = 1000.0,
) -> str:
    """
    Classify cost into tier (aligned with runbooks.finops.config thresholds).

    Args:
        cost: Cost value to classify
        high_threshold: Threshold for HIGH tier (default: 5000)
        medium_threshold: Threshold for MEDIUM tier (default: 1000)

    Returns:
        'HIGH', 'MEDIUM', or 'LOW'
    """
    if cost >= high_threshold:
        return "HIGH"
    elif cost >= medium_threshold:
        return "MEDIUM"
    return "LOW"
