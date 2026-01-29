#!/usr/bin/env python3
"""AppStream Activity Enricher - Wrapper for AppStream Analyzer"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..appstream_analyzer import AppStreamCostAnalyzer

logger = logging.getLogger(__name__)


class AppStreamEnricher(ActivityEnricherBase):
    """AppStream Activity Enricher - A1-A7 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._appstream_analyzer = AppStreamCostAnalyzer(
            operational_profile=self.operational_profile, region=self.region
        )

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich AppStream fleets with A1-A7 signals."""
        if not self.validate_input(resources, ["fleet_name"]):
            return pd.DataFrame()

        try:
            enriched_df = self._appstream_analyzer.analyze_fleets(fleet_names=[r["fleet_name"] for r in resources])
            logger.info(f"AppStreamEnricher: Enriched {len(enriched_df)} fleets")
            return enriched_df
        except Exception as e:
            logger.error(f"AppStreamEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "a1_zero_sessions",
            "a2_low_capacity",
            "a3_old_image",
            "a4_always_on_waste",
            "a5_no_fleet_scaling",
            "a6_idle_fleet",
            "a7_high_cost",
        ]
