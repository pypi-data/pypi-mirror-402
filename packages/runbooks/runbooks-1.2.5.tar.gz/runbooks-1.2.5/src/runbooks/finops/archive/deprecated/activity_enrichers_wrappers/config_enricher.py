#!/usr/bin/env python3
"""Config Activity Enricher - Wrapper for Config Activity Enricher"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..config_activity_enricher import ConfigActivityEnricher as _ConfigActivityEnricher

logger = logging.getLogger(__name__)


class ConfigEnricher(ActivityEnricherBase):
    """Config Activity Enricher - CFG1-CFG5 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config_enricher = _ConfigActivityEnricher(
            operational_profile=self.operational_profile, region=self.region
        )

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich resources with Config CFG1-CFG5 signals."""
        if not resources:
            return pd.DataFrame()

        try:
            enriched_df = self._config_enricher.enrich_with_compliance(resources)
            logger.info(f"ConfigEnricher: Enriched {len(enriched_df)} resources")
            return enriched_df
        except Exception as e:
            logger.error(f"ConfigEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "cfg1_non_compliant",
            "cfg2_no_rules",
            "cfg3_config_changes",
            "cfg4_recorder_inactive",
            "cfg5_high_cost",
        ]
