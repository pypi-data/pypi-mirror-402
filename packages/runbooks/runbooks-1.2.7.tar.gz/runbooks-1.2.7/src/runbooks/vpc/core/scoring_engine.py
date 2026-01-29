"""
VPC Scoring Engine - Calculate technical and business risk scores

This module provides ScoringEngine class for calculating technical complexity
and business criticality scores for VPC decommissioning analysis.

Strategic Context:
- Extracted from vpc-inventory-analyzer.py lines 209-246
- Technical score (0-100): Resource complexity and interconnectivity
- Business score (0-100): Environment criticality and business impact
- Scores drive three-bucket categorization (MUST/COULD/SHOULD NOT delete)
"""

from runbooks.vpc.models import VPCResources


# Business criticality mapping by environment tier
BUSINESS_SCORE_MAP = {
    "prod": 80,  # Production: High business impact
    "preprod": 50,  # Pre-production: Medium impact
    "sit": 50,  # System Integration Testing: Medium impact
    "uat": 40,  # User Acceptance Testing: Medium-low impact
    "nonprod": 30,  # Non-production: Low-medium impact
    "dev": 20,  # Development: Low impact
    "test": 20,  # Testing: Low impact
    "sandbox": 10,  # Sandbox: Very low impact
    "security": 90,  # Security infrastructure: Very high impact
    "unknown": 20,  # Unknown: Assume low impact (conservative)
}


class ScoringEngine:
    """
    Calculate technical and business risk scores for VPC decommissioning.

    Technical Score (0-100):
    - Measures resource complexity and interconnectivity
    - Higher score = more complex to decommission
    - Weighting: NAT (20), Interface VPCE (15), Lambda (25), EC2 (30), TGW (30)

    Business Score (0-100):
    - Measures business criticality by environment tier
    - Higher score = higher business impact if decommissioned
    - Mapping: prod (80), preprod (50), dev (20), sandbox (10), etc.

    Example:
        engine = ScoringEngine()
        resources = VPCResources(
            vpc_id="vpc-123",
            nat_gateways=1,
            vpce_interface=2,
            ec2_instances=3
        )
        technical_score = engine.calculate_technical_score(resources)
        business_score = engine.calculate_business_score("prod")
        # technical_score: 140 (capped at 100)
        # business_score: 80 (production environment)
    """

    def calculate_technical_score(self, resources: VPCResources) -> int:
        """
        Calculate technical complexity score (0-100).

        Resource complexity weighting:
        - NAT Gateways: 20 points each (network egress dependency)
        - Interface VPCEs: 15 points each (service connectivity)
        - Lambda Functions: 25 points each (application logic)
        - EC2 Instances: 30 points each (compute workloads)
        - TGW Attachments: 30 points each (cross-account connectivity)

        Higher scores indicate more complex decommissioning:
        - 0-20: Simple (minimal resources)
        - 21-50: Moderate (some interconnections)
        - 51-80: Complex (multiple resource types)
        - 81-100: Very complex (extensive dependencies)

        Args:
            resources: VPC resource counts

        Returns:
            Technical complexity score (0-100, capped at 100)

        Example:
            resources = VPCResources(
                vpc_id="vpc-007462e1e648ef6de",
                nat_gateways=1,        # +20 points
                vpce_interface=0,      # +0 points
                lambda_functions=0,    # +0 points
                ec2_instances=0,       # +0 points
                tgw_attachments=2      # +60 points
            )
            score = engine.calculate_technical_score(resources)
            # Result: 80 (NAT 20 + TGW 60)
        """
        score = (
            resources.nat_gateways * 20  # Network egress dependency
            + resources.vpce_interface * 15  # Service connectivity
            + resources.lambda_functions * 25  # Application logic
            + resources.ec2_instances * 30  # Compute workloads
            + resources.tgw_attachments * 30  # Cross-account connectivity
        )

        # Cap score at 100 (maximum complexity)
        return min(score, 100)

    def calculate_business_score(self, environment: str) -> int:
        """
        Calculate business criticality score (0-100).

        Environment tier mapping:
        - prod: 80 (production workloads)
        - preprod: 50 (pre-production testing)
        - sit/uat: 40-50 (integration/acceptance testing)
        - dev/test: 20 (development/testing)
        - sandbox: 10 (experimental environments)
        - security: 90 (security infrastructure)
        - unknown: 20 (conservative assumption)

        Higher scores indicate higher business impact:
        - 80-100: Critical (production/security)
        - 50-79: Important (pre-production)
        - 20-49: Moderate (development/testing)
        - 0-19: Low (sandbox/experimental)

        Args:
            environment: Environment tier (case-insensitive)

        Returns:
            Business criticality score (0-100)

        Example:
            score_prod = engine.calculate_business_score("prod")
            # Result: 80 (high business impact)

            score_sandbox = engine.calculate_business_score("sandbox")
            # Result: 10 (low business impact)
        """
        return BUSINESS_SCORE_MAP.get(environment.lower(), 20)

    def calculate_decommissioning_risk(self, technical_score: int, business_score: int) -> str:
        """
        Calculate overall decommissioning risk level.

        Risk calculation combines technical complexity and business criticality:
        - HIGH RISK: (technical >= 50 OR business >= 50)
        - MEDIUM RISK: (technical >= 30 OR business >= 30)
        - LOW RISK: (technical < 30 AND business < 30)

        Args:
            technical_score: Technical complexity score (0-100)
            business_score: Business criticality score (0-100)

        Returns:
            Risk level: "HIGH", "MEDIUM", or "LOW"

        Example:
            risk = engine.calculate_decommissioning_risk(
                technical_score=80,  # Complex VPC
                business_score=80    # Production environment
            )
            # Result: "HIGH" (high complexity + high business impact)
        """
        if technical_score >= 50 or business_score >= 50:
            return "HIGH"
        elif technical_score >= 30 or business_score >= 30:
            return "MEDIUM"
        else:
            return "LOW"
