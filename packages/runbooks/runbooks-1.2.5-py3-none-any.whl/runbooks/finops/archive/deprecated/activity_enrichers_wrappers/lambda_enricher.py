#!/usr/bin/env python3
"""Lambda Activity Enricher - Wrapper for Lambda Analyzer"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..lambda_analyzer import LambdaCostAnalyzer

logger = logging.getLogger(__name__)


class LambdaEnricher(ActivityEnricherBase):
    """Lambda Activity Enricher - L1-L6 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lambda_analyzer = LambdaCostAnalyzer(operational_profile=self.operational_profile, region=self.region)

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich Lambda functions with L1-L6 signals."""
        if not self.validate_input(resources, ["function_name"]):
            return pd.DataFrame()

        try:
            # Delegate to lambda_analyzer
            enriched_df = self._lambda_analyzer.analyze_functions(
                function_names=[r["function_name"] for r in resources]
            )
            logger.info(f"LambdaEnricher: Enriched {len(enriched_df)} functions")
            return enriched_df
        except Exception as e:
            logger.error(f"LambdaEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "l1_zero_invocations",
            "l2_error_rate",
            "l3_cold_start",
            "l4_memory_waste",
            "l5_timeout_near",
            "l6_cost_spike",
        ]
