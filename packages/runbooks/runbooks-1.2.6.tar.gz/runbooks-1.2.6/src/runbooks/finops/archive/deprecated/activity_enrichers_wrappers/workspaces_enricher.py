#!/usr/bin/env python3
"""WorkSpaces Activity Enricher - Wrapper for WorkSpaces Analyzer"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..workspaces_analyzer import WorkSpacesCostAnalyzer

logger = logging.getLogger(__name__)


class WorkSpacesEnricher(ActivityEnricherBase):
    """WorkSpaces Activity Enricher - W1-W6 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._workspaces_analyzer = WorkSpacesCostAnalyzer(
            operational_profile=self.operational_profile, region=self.region
        )

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich WorkSpaces with W1-W6 signals."""
        if not self.validate_input(resources, ["workspace_id"]):
            return pd.DataFrame()

        try:
            enriched_df = self._workspaces_analyzer.analyze_workspaces(
                workspace_ids=[r["workspace_id"] for r in resources]
            )
            logger.info(f"WorkSpacesEnricher: Enriched {len(enriched_df)} workspaces")
            return enriched_df
        except Exception as e:
            logger.error(f"WorkSpacesEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "w1_never_connected",
            "w2_low_usage",
            "w3_always_on_waste",
            "w4_old_bundle",
            "w5_no_encryption",
            "w6_high_cost",
        ]
