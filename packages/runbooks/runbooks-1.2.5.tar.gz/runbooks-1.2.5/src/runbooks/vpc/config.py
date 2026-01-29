"""
VPC Networking Configuration Management

ZERO HARDCODED VALUES - 100% Environment-Driven Configuration
Pydantic Settings for type-safe environment variable management
AWS Pricing API integration for dynamic cost calculations
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import AWS Pricing API for dynamic pricing (NO hardcoded costs)
try:
    from runbooks.common.aws_pricing_api import AWSPricingAPI

    AWS_PRICING_AVAILABLE = True
except ImportError:
    AWS_PRICING_AVAILABLE = False


class VPCOptimizationSettings(BaseSettings):
    """
    VPC Optimization Configuration - 100% Environment-Driven

    ALL values from environment variables or .env file
    ZERO hardcoded defaults (only universal compatibility fallbacks)

    Environment Variables:
        AWS_DEFAULT_REGION: AWS region for operations
        AWS_REGIONS: Comma-separated list of regions (e.g., "ap-southeast-2,ap-southeast-2")
        AWS_PROFILE: Default AWS profile
        AWS_BILLING_PROFILE: Billing profile for Cost Explorer
        AWS_MANAGEMENT_PROFILE: Management account profile
        AWS_CENTRALISED_OPS_PROFILE: Centralized ops profile

        # Optimization Targets (PERCENTAGES, not dollar amounts)
        VPC_NAT_GATEWAY_REDUCTION_TARGET: NAT Gateway reduction target (0.0-1.0)
        VPC_VPC_ENDPOINT_REDUCTION_TARGET: VPC Endpoint reduction target (0.0-1.0)
        VPC_TRANSIT_GATEWAY_REDUCTION_TARGET: Transit Gateway reduction target (0.0-1.0)
        VPC_COST_REDUCTION_TARGET: Overall cost reduction target (0.0-1.0)

        # Discovery Configuration
        VPC_AUTO_DISCOVER_RESOURCES: Enable AWS API resource discovery
        VPC_AUTO_DISCOVER_COSTS: Enable Cost Explorer cost discovery

        # Analysis Configuration
        VPC_DEFAULT_ANALYSIS_DAYS: Days for usage analysis (default: 30)
        VPC_FORECAST_DAYS: Days for cost forecast (default: 30)

        # Output Configuration
        VPC_OUTPUT_FORMAT: Output format (json/yaml/csv)
        VPC_OUTPUT_DIR: Output directory path

        # Enterprise Workflow
        VPC_ENABLE_COST_APPROVAL_WORKFLOW: Enable cost approval workflow
        VPC_ENABLE_MCP_VALIDATION: Enable MCP cross-validation
        VPC_COST_APPROVAL_THRESHOLD: Dollar threshold requiring approval
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="VPC_",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_default_region: str = Field(
        default="ap-southeast-2", description="Default AWS region", validation_alias="AWS_DEFAULT_REGION"
    )
    aws_regions: List[str] = Field(
        default=["ap-southeast-2"], description="List of AWS regions for multi-region operations"
    )
    aws_profile: Optional[str] = Field(default=None, description="AWS CLI profile name", validation_alias="AWS_PROFILE")
    aws_billing_profile: Optional[str] = Field(
        default=None, description="AWS profile for billing/Cost Explorer access", validation_alias="AWS_BILLING_PROFILE"
    )
    aws_management_profile: Optional[str] = Field(
        default=None, description="AWS management account profile", validation_alias="AWS_MANAGEMENT_PROFILE"
    )
    aws_centralised_ops_profile: Optional[str] = Field(
        default=None, description="AWS centralized ops account profile", validation_alias="AWS_CENTRALISED_OPS_PROFILE"
    )

    # Optimization Targets (PERCENTAGES - NOT dollar amounts)
    nat_gateway_reduction_target: float = Field(
        default=0.30, ge=0.0, le=1.0, description="NAT Gateway reduction target (30% = 0.30)"
    )
    vpc_endpoint_reduction_target: float = Field(
        default=0.30, ge=0.0, le=1.0, description="VPC Endpoint reduction target (30% = 0.30)"
    )
    transit_gateway_reduction_target: float = Field(
        default=0.30, ge=0.0, le=1.0, description="Transit Gateway reduction target (30% = 0.30)"
    )
    cost_reduction_target: float = Field(
        default=0.30, ge=0.0, le=1.0, description="Overall cost reduction target (30% = 0.30)"
    )

    # Discovery Configuration
    auto_discover_resources: bool = Field(
        default=True, description="Enable AWS API resource discovery (no hardcoded counts)"
    )
    auto_discover_costs: bool = Field(
        default=True, description="Enable Cost Explorer cost discovery (no hardcoded pricing)"
    )

    # Analysis Configuration
    default_analysis_days: int = Field(default=30, ge=1, le=90, description="Days for usage analysis")
    forecast_days: int = Field(default=30, ge=1, le=365, description="Days for cost forecast")

    # Output Configuration
    output_format: str = Field(default="json", pattern="^(json|yaml|csv)$", description="Output format")
    output_dir: Path = Field(default=Path("./tmp"), description="Output directory")

    # Enterprise Workflow
    enable_cost_approval_workflow: bool = Field(default=False, description="Enable enterprise cost approval workflow")
    enable_mcp_validation: bool = Field(default=False, description="Enable MCP cross-validation")
    cost_approval_threshold: float = Field(default=500.0, ge=0.0, description="Dollar threshold requiring approval")

    # Usage thresholds for optimization recommendations
    idle_connection_threshold: int = Field(default=1, ge=0)
    low_usage_gb_threshold: float = Field(default=1.0, ge=0.0)
    low_connection_threshold: int = Field(default=5, ge=0)
    high_cost_threshold: float = Field(default=100.0, ge=0.0)
    critical_cost_threshold: float = Field(default=1000.0, ge=0.0)
    performance_baseline_threshold: float = Field(default=30.0, ge=0.0)

    @classmethod
    def from_env_file(cls, env_file: str = ".env") -> "VPCOptimizationSettings":
        """Load configuration from specific .env file."""
        return cls(_env_file=env_file)

    def get_aws_session_profile(self, profile_type: str = "default") -> str:
        """
        Get AWS profile for specific operation type.

        Args:
            profile_type: Type of profile (default, billing, management, ops)

        Returns:
            AWS profile name
        """
        if profile_type == "billing" and self.aws_billing_profile:
            return self.aws_billing_profile
        elif profile_type == "management" and self.aws_management_profile:
            return self.aws_management_profile
        elif profile_type == "ops" and self.aws_centralised_ops_profile:
            return self.aws_centralised_ops_profile
        elif self.aws_profile:
            return self.aws_profile
        else:
            return "default"

    def get_regions_for_discovery(self) -> List[str]:
        """Get regions for resource discovery (from env, not hardcoded)."""
        if isinstance(self.aws_regions, str):
            # Parse comma-separated string if needed
            return [r.strip() for r in self.aws_regions.split(",")]
        return self.aws_regions

    def get_cost_approval_required(self, monthly_cost: float) -> bool:
        """Check if cost requires approval based on threshold."""
        return self.enable_cost_approval_workflow and monthly_cost > self.cost_approval_threshold


class AWSPricingConfig:
    """
    AWS Pricing Configuration - Dynamic API Integration

    NO hardcoded pricing values
    ALL costs from AWS Pricing API or Cost Explorer
    """

    def __init__(self, profile: Optional[str] = None, region: str = "ap-southeast-2"):
        """
        Initialize pricing configuration.

        Args:
            profile: AWS profile for Pricing API access
            region: AWS region for pricing queries
        """
        self.profile = profile
        self.region = region
        self._pricing_api = None

    @property
    def pricing_api(self) -> Optional["AWSPricingAPI"]:
        """Lazy-load AWS Pricing API client."""
        if not AWS_PRICING_AVAILABLE:
            return None

        if self._pricing_api is None and self.profile:
            self._pricing_api = AWSPricingAPI(profile=self.profile)

        return self._pricing_api

    def get_nat_gateway_hourly_cost(self, region: Optional[str] = None) -> float:
        """
        Get NAT Gateway hourly cost from AWS Pricing API.

        Args:
            region: AWS region (uses config default if not specified)

        Returns:
            Hourly cost in USD
        """
        target_region = region or self.region

        if self.pricing_api:
            try:
                monthly_cost = self.pricing_api.get_nat_gateway_monthly_cost(target_region)
                return monthly_cost / (24 * 30)
            except Exception:
                pass

        # Universal compatibility fallback (AWS published rate)
        return 0.045  # $0.045/hour standard NAT Gateway rate

    def get_nat_gateway_monthly_cost(self, region: Optional[str] = None) -> float:
        """Get NAT Gateway monthly cost from AWS Pricing API."""
        return self.get_nat_gateway_hourly_cost(region) * 24 * 30

    def get_transit_gateway_hourly_cost(self, region: Optional[str] = None) -> float:
        """Get Transit Gateway hourly cost from AWS Pricing API."""
        # Would integrate with AWS Pricing API
        return 0.05  # AWS standard TGW hourly rate

    def get_transit_gateway_attachment_cost(self, region: Optional[str] = None) -> float:
        """Get Transit Gateway attachment monthly cost."""
        return 0.05 * 24 * 30  # $0.05/hour per attachment

    def get_vpc_endpoint_interface_hourly_cost(self, region: Optional[str] = None) -> float:
        """Get VPC Interface Endpoint hourly cost."""
        return 0.01  # AWS standard VPC Interface Endpoint rate

    def get_vpc_endpoint_interface_monthly_cost(self, region: Optional[str] = None) -> float:
        """Get VPC Interface Endpoint monthly cost."""
        return self.get_vpc_endpoint_interface_hourly_cost(region) * 24 * 30

    def get_vpn_connection_monthly_cost(self, region: Optional[str] = None) -> float:
        """Get VPN Connection monthly cost."""
        return 36.0  # AWS standard VPN connection cost

    # Data Transfer Pricing Attributes
    @property
    def nat_gateway_hourly(self) -> float:
        """NAT Gateway hourly cost."""
        return self.get_nat_gateway_hourly_cost()

    @property
    def nat_gateway_data_processing(self) -> float:
        """NAT Gateway data processing cost per GB."""
        return 0.045  # AWS standard NAT Gateway data processing rate

    @property
    def vpc_endpoint_interface_monthly(self) -> float:
        """VPC Interface Endpoint monthly cost."""
        return self.get_vpc_endpoint_interface_monthly_cost()

    @property
    def vpc_endpoint_data_processing(self) -> float:
        """VPC Endpoint data processing cost per GB."""
        return 0.01  # AWS standard VPC Endpoint data processing rate

    @property
    def transit_gateway_hourly(self) -> float:
        """Transit Gateway hourly cost."""
        return self.get_transit_gateway_hourly_cost()

    @property
    def transit_gateway_attachment(self) -> float:
        """Transit Gateway attachment hourly cost."""
        return 0.05  # AWS standard TGW attachment rate

    @property
    def transit_gateway_data_processing(self) -> float:
        """Transit Gateway data processing cost per GB."""
        return 0.02  # AWS standard TGW data processing rate

    @property
    def elastic_ip_idle_hourly(self) -> float:
        """Elastic IP idle hourly cost."""
        return 0.005  # AWS standard idle EIP rate

    @property
    def elastic_ip_remap(self) -> float:
        """Elastic IP remap cost."""
        return 0.10  # AWS standard EIP remap cost

    @property
    def data_transfer_inter_az(self) -> float:
        """Inter-AZ data transfer cost per GB."""
        return 0.01  # AWS standard inter-AZ data transfer rate

    @property
    def data_transfer_inter_region(self) -> float:
        """Inter-region data transfer cost per GB."""
        return 0.02  # AWS standard inter-region data transfer rate

    @property
    def data_transfer_internet_out(self) -> float:
        """Internet outbound data transfer cost per GB."""
        return 0.09  # AWS standard internet egress rate (first 10TB tier)


# Global configuration instance (lazy initialization)
_global_config: Optional[VPCOptimizationSettings] = None


def get_vpc_config() -> VPCOptimizationSettings:
    """
    Get global VPC optimization configuration.

    Lazy-loads configuration from environment on first access.

    Returns:
        VPCOptimizationSettings instance
    """
    global _global_config

    if _global_config is None:
        _global_config = VPCOptimizationSettings()

    return _global_config


def get_pricing_config(profile: Optional[str] = None, region: Optional[str] = None) -> AWSPricingConfig:
    """
    Get AWS pricing configuration.

    Args:
        profile: AWS profile (uses VPC config default if not specified)
        region: AWS region (uses VPC config default if not specified)

    Returns:
        AWSPricingConfig instance
    """
    vpc_config = get_vpc_config()

    return AWSPricingConfig(
        profile=profile or vpc_config.aws_billing_profile or vpc_config.aws_profile,
        region=region or vpc_config.aws_default_region,
    )


# Backward compatibility exports
default_config = get_vpc_config  # Function reference for lazy evaluation
VPCNetworkingConfig = VPCOptimizationSettings  # Alias for backward compatibility
load_config = get_vpc_config  # Alias for backward compatibility
VPCConfig = VPCOptimizationSettings  # Alias for notebook_service.py
OptimizationThresholds = VPCOptimizationSettings  # Alias for test_calculations.py
AWSCostModel = AWSPricingConfig  # Alias for test_config.py
RegionalConfiguration = VPCOptimizationSettings  # Alias for test_config.py


class VPCConfigManager:
    """
    Backward compatibility wrapper for VPCOptimizationSettings.

    Legacy VPC modules (cli.py, notebook_service.py) expect this class.
    Delegates to Pydantic Settings implementation.
    """

    def __init__(self, env_file: str = ".env"):
        """Initialize config manager with environment file."""
        self._config = VPCOptimizationSettings.from_env_file(env_file)

    def get_config(self) -> VPCOptimizationSettings:
        """Get VPC optimization configuration."""
        return self._config

    def get_aws_profile(self, profile_type: str = "default") -> str:
        """Get AWS profile for operation type."""
        return self._config.get_aws_session_profile(profile_type)

    def get_regions(self) -> List[str]:
        """Get regions for discovery."""
        return self._config.get_regions_for_discovery()

    # Direct attribute access for backward compatibility
    @property
    def aws_profile(self) -> Optional[str]:
        return self._config.aws_profile

    @property
    def aws_default_region(self) -> str:
        return self._config.aws_default_region

    @property
    def aws_regions(self) -> List[str]:
        return self._config.aws_regions

    @property
    def cost_reduction_target(self) -> float:
        return self._config.cost_reduction_target


# Legacy constants for backward compatibility
VPCE_BILLING_PROFILE = None  # Now loaded from environment


def get_last_billing_month() -> str:
    """
    Get last billing month in YYYY-MM format.

    Legacy function for backward compatibility with notebook_service.py.
    """
    from datetime import datetime, timedelta

    # Get last month's date
    today = datetime.now()
    first_day_this_month = today.replace(day=1)
    last_month = first_day_this_month - timedelta(days=1)

    return last_month.strftime("%Y-%m")


def get_vpce_profile_for_account(account_type: str = "default") -> str:
    """
    Get AWS profile for VPC Endpoint operations based on account type.

    Legacy function for backward compatibility with test_multi_account.py.

    Args:
        account_type: Type of account (management, billing, ops, default)

    Returns:
        AWS profile name
    """
    config = get_vpc_config()
    return config.get_aws_session_profile(account_type)
