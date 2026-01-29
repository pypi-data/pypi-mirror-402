#!/usr/bin/env python3
"""CloudTrail Activity Enricher - Wrapper for CloudTrail Activity Enricher"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..cloudtrail_activity_enricher import CloudTrailActivityEnricher as _CloudTrailActivityEnricher

logger = logging.getLogger(__name__)


class CloudTrailEnricher(ActivityEnricherBase):
    """CloudTrail Activity Enricher - CT1-CT5 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cloudtrail_enricher = _CloudTrailActivityEnricher(
            operational_profile=self.operational_profile, region=self.region
        )

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich resources with CloudTrail CT1-CT5 signals."""
        if not resources:
            return pd.DataFrame()

        try:
            enriched_df = self._cloudtrail_enricher.enrich_with_activity(resources)
            logger.info(f"CloudTrailEnricher: Enriched {len(enriched_df)} resources")
            return enriched_df
        except Exception as e:
            logger.error(f"CloudTrailEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return ["ct1_no_events", "ct2_last_event_old", "ct3_api_errors", "ct4_user_activity", "ct5_high_cost"]
