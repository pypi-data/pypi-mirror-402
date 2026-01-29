"""
VPC Data Models - Pydantic Schemas for VPC Analysis

This module provides Pydantic models for VPC metadata, resources, costs, and analysis results.
Migrated from vpc-inventory-analyzer.py with enhanced type safety and validation.

Strategic Context:
- Replaces dictionary-based data structures with type-safe Pydantic models
- Enables validation at data ingestion boundaries
- Supports JSON serialization for evidence artifacts
- Manager-friendly field names for business reporting
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class VPCMetadata(BaseModel):
    """
    VPC metadata including account and environment information.

    Fields align with manager reporting requirements:
    - vpc_id: AWS VPC identifier (vpc-xxxxx)
    - account_id: AWS account ID
    - account_name: Business-friendly account name
    - environment: Environment tier (prod, preprod, test, dev, sandbox)
    - vpc_name: Descriptive VPC name from tags
    - region: AWS region (default: ap-southeast-2)
    - profile: AWS CLI profile for access
    """

    vpc_id: str = Field(..., description="AWS VPC ID (e.g., vpc-xxxxx)")
    account_id: str = Field(..., description="AWS Account ID")
    account_name: str = Field(default="", description="Business-friendly account name")
    environment: str = Field(..., description="Environment tier (prod/preprod/test/dev/sandbox)")
    vpc_name: str = Field(default="", description="VPC name from tags")
    region: str = Field(default="ap-southeast-2", description="AWS region")
    profile: Optional[str] = Field(default=None, description="AWS CLI profile")

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: float}


class VPCResources(BaseModel):
    """
    Aggregated resource counts for VPC analysis.

    CRITICAL DISTINCTION:
    - vpce_interface: Interface VPCEs cost $7.30/month EACH
    - vpce_gateway: Gateway VPCEs (S3, DynamoDB) are FREE

    Resource categories:
    - Network interfaces (ENIs): Primary activity indicator (0 ENIs = unused VPC)
    - NAT Gateways: $32.85/month EACH (primary cost driver)
    - VPC Endpoints: Interface ($7.30/mo) vs Gateway ($0.00)
    - Compute: EC2 instances, Lambda functions
    - Database: RDS instances
    - Networking: Load balancers, subnets, Transit Gateway attachments
    """

    vpc_id: str = Field(..., description="VPC ID this resource count belongs to")

    # Primary activity indicator
    enis: int = Field(default=0, description="Network interfaces (0 = unused VPC)")

    # Cost drivers
    nat_gateways: int = Field(default=0, description="NAT Gateways ($32.85/month each)")
    vpce_interface: int = Field(default=0, description="Interface VPCEs ($7.30/month each)")
    vpce_gateway: int = Field(default=0, description="Gateway VPCEs (FREE)")

    # Compute resources
    ec2_instances: int = Field(default=0, description="EC2 instances")
    lambda_functions: int = Field(default=0, description="Lambda functions")

    # Database resources
    rds_instances: int = Field(default=0, description="RDS database instances")

    # Network resources
    load_balancers: int = Field(default=0, description="Load balancers (ALB/NLB)")
    subnets: int = Field(default=0, description="Subnets")
    tgw_attachments: int = Field(default=0, description="Transit Gateway attachments")

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: float}


class VPCCostBreakdown(BaseModel):
    """
    Monthly cost breakdown by resource type.

    AWS ap-southeast-2 pricing reference:
    - NAT Gateway: $0.059/hour = $32.85/month (720 hours)
    - Interface VPCE: $0.014/hour = $7.30/month (720 hours)
    - Gateway VPCE: $0.00/month (always FREE)

    Note: Actual pricing dynamically retrieved from AWS APIs or AWSCostModel configuration

    Cost calculation formula:
    total_monthly_cost = (nat_gateways × $32.85) + (vpce_interface × $7.30) + $0.00
    """

    nat_gateway_cost: Decimal = Field(
        default=Decimal("0.00"), description="NAT Gateway monthly cost ($32.85 per gateway)"
    )
    vpce_interface_cost: Decimal = Field(
        default=Decimal("0.00"), description="Interface VPCE monthly cost ($7.30 per endpoint)"
    )
    vpce_gateway_cost: Decimal = Field(default=Decimal("0.00"), description="Gateway VPCE monthly cost (always $0.00)")
    total_monthly_cost: Decimal = Field(default=Decimal("0.00"), description="Total monthly infrastructure cost")

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: float}


class VPCAnalysis(BaseModel):
    """
    Complete VPC analysis results combining metadata, resources, costs, and recommendations.

    Analysis workflow:
    1. Load metadata (account, environment, VPC name)
    2. Count resources (ENIs, NAT, VPCEs, EC2, Lambda, RDS, etc.)
    3. Calculate costs (NAT $32.85/mo, Interface VPCE $7.30/mo)
    4. Score technical complexity (0-100) and business criticality (0-100)
    5. Categorize into three buckets (MUST DELETE / COULD DELETE / SHOULD NOT DELETE)
    6. Generate recommendation with rationale

    Manager output format (15 columns):
    VPC ID | Account | Env | NAT | VPCE(I) | VPCE(G) | ENI | TGW | EC2 | Lambda | Cost/Mo | Tech | Biz | Three-Bucket | Recommendation | Rationale
    """

    metadata: VPCMetadata = Field(..., description="VPC metadata")
    resources: VPCResources = Field(..., description="Resource counts")
    cost_breakdown: VPCCostBreakdown = Field(..., description="Cost breakdown")
    technical_score: int = Field(..., ge=0, le=100, description="Technical complexity score (0-100)")
    business_score: int = Field(..., ge=0, le=100, description="Business criticality score (0-100)")
    three_bucket: str = Field(
        ..., description="Decommissioning bucket (MUST DELETE | COULD DELETE | SHOULD NOT DELETE)"
    )
    recommendation: str = Field(..., description="Decommissioning recommendation")
    rationale: str = Field(..., description="Business rationale for recommendation")

    class Config:
        """Pydantic configuration."""

        json_encoders = {Decimal: float}
