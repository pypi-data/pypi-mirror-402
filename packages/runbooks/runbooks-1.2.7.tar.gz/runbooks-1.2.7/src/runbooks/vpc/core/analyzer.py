"""
VPC Analyzer - Consolidated VPC analysis engine

Consolidates analyze_vpc() from 3 scripts into single modular implementation.
Complete analysis pipeline: resources → costs → scores → categorization → recommendations
"""

from pathlib import Path
from runbooks.vpc.models import VPCAnalysis, VPCMetadata
from runbooks.vpc.collectors.evidence_loader import EvidenceLoader
from runbooks.vpc.core.cost_calculator import CostCalculator
from runbooks.vpc.core.scoring_engine import ScoringEngine
from runbooks.vpc.core.recommendation_engine import RecommendationEngine


class VPCAnalyzer:
    """VPC analysis engine - consolidate logic from 3 scripts."""

    def __init__(self):
        self.evidence_loader = None
        self.cost_calculator = CostCalculator()
        self.scoring_engine = ScoringEngine()
        self.recommendation_engine = RecommendationEngine()

    def analyze_vpc(self, vpc_id: str, metadata: VPCMetadata, evidence_dir: Path) -> VPCAnalysis:
        """
        Complete VPC analysis pipeline.

        Workflow:
        1. Load resources from evidence files
        2. Calculate costs (NAT $32.85/mo, Interface VPCE $7.30/mo)
        3. Calculate scores (technical complexity, business criticality)
        4. Categorize (MUST/COULD/SHOULD NOT delete)
        5. Generate recommendation with rationale
        """
        # Step 1: Load resources
        if not self.evidence_loader:
            self.evidence_loader = EvidenceLoader(evidence_dir)
        resources = self.evidence_loader.load_vpc_resources(vpc_id)

        # Step 2: Calculate costs
        cost_breakdown = self.cost_calculator.calculate_cost_breakdown(resources)

        # Step 3: Calculate scores
        technical_score = self.scoring_engine.calculate_technical_score(resources)
        business_score = self.scoring_engine.calculate_business_score(metadata.environment)

        # Step 4: Categorize
        three_bucket = self._categorize_three_bucket(resources)

        # Step 5: Generate recommendation
        recommendation, rationale = self.recommendation_engine.generate_recommendation(
            resources, cost_breakdown, three_bucket
        )

        return VPCAnalysis(
            metadata=metadata,
            resources=resources,
            cost_breakdown=cost_breakdown,
            technical_score=technical_score,
            business_score=business_score,
            three_bucket=three_bucket,
            recommendation=recommendation,
            rationale=rationale,
        )

    def _categorize_three_bucket(self, resources) -> str:
        """Categorize VPC into decommissioning buckets."""
        if resources.enis == 0:
            return "MUST DELETE"
        elif resources.tgw_attachments > 0:
            return "SHOULD NOT DELETE"
        else:
            return "COULD DELETE"
