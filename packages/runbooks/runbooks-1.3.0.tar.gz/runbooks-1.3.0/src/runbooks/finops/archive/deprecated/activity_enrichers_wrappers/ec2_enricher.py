#!/usr/bin/env python3
"""
EC2 Activity Enricher - Wrapper for EC2 Analyzer
================================================

Consolidation Pattern: Delegate to existing ec2_analyzer.py (KISS/DRY)
- E1-E7 signal definitions preserved
- analyze_ec2_costs() functionality maintained
- Backward compatibility via delegation

Strategic Alignment:
- KISS: Don't rewrite working code, consolidate via delegation
- DRY: Single source of truth (ec2_analyzer.py)
- LEAN: Enhance structure without duplicating functionality

Usage:
    from runbooks.finops.activity_enrichers import EC2Enricher

    enricher = EC2Enricher(operational_profile='ops-profile')
    enriched_df = enricher.enrich(
        resources=[{'instance_id': 'i-abc123', ...}],
        management_profile='mgmt-profile',
        billing_profile='billing-profile'
    )

Author: Runbooks Team
Version: 2.0.0
Epic: Track E - Activity Enrichers Consolidation
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

from .base import ActivityEnricherBase

# Import existing EC2 analyzer (KISS: reuse existing code)
from ..ec2_analyzer import analyze_ec2_costs, EC2AnalysisConfig

logger = logging.getLogger(__name__)


class EC2Enricher(ActivityEnricherBase):
    """
    EC2 Activity Enricher - Delegates to proven ec2_analyzer.py patterns.

    Signal Pattern (E1-E7):
        E1: Stopped >30 days (High confidence: 0.85)
        E2: 0 network activity (High confidence: 0.80)
        E3: 0 CPU utilization (High confidence: 0.75)
        E4: 0 disk I/O (Medium confidence: 0.70)
        E5: No attached services (Medium confidence: 0.65)
        E6: No storage I/O (Medium confidence: 0.60)
        E7: High cost, low utilization (Medium confidence: 0.70)
    """

    def enrich(
        self,
        resources: List[Dict],
        management_profile: Optional[str] = None,
        billing_profile: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Enrich EC2 instances with E1-E7 activity signals.

        Args:
            resources: List of EC2 instance dictionaries
            management_profile: AWS profile for Organizations/CloudTrail
            billing_profile: AWS profile for Cost Explorer
            **kwargs: Additional parameters for ec2_analyzer

        Returns:
            DataFrame with E1-E7 signal columns added
        """
        if not self.validate_input(resources, ["instance_id"]):
            logger.warning("EC2Enricher: Invalid input, returning empty DataFrame")
            return pd.DataFrame()

        # Convert resources to DataFrame for ec2_analyzer
        df = pd.DataFrame(resources)

        # Create configuration (delegate to EC2AnalysisConfig)
        config = EC2AnalysisConfig(
            management_profile=management_profile, billing_profile=billing_profile, region=self.region
        )

        try:
            # Delegate to proven ec2_analyzer.py implementation
            enriched_df = analyze_ec2_costs(input_data=df, config=config, output_controller=self.output_controller)

            logger.info(f"EC2Enricher: Enriched {len(enriched_df)} instances with E1-E7 signals")
            return enriched_df

        except Exception as e:
            logger.error(f"EC2Enricher: Enrichment failed: {e}", exc_info=True)
            return df  # Return original DataFrame on error (graceful degradation)

    def get_signal_columns(self) -> List[str]:
        """
        Return list of signal column names for E1-E7.

        Returns:
            List of signal column names
        """
        return [
            "e1_stopped_days",
            "e2_network_activity",
            "e3_cpu_utilization",
            "e4_disk_io",
            "e5_attached_services",
            "e6_storage_io",
            "e7_cost_utilization_ratio",
        ]
