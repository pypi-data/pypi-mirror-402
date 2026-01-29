#!/usr/bin/env python3
"""CloudWatch Activity Enricher - Wrapper for CloudWatch Activity Enricher"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..cloudwatch_activity_enricher import CloudWatchActivityEnricher as _CloudWatchActivityEnricher

logger = logging.getLogger(__name__)


class CloudWatchEnricher(ActivityEnricherBase):
    """CloudWatch Activity Enricher - M1-M7 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cloudwatch_enricher = _CloudWatchActivityEnricher(
            operational_profile=self.operational_profile, region=self.region
        )

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich resources with CloudWatch M1-M7 signals."""
        if not resources:
            return pd.DataFrame()

        try:
            enriched_df = self._cloudwatch_enricher.enrich_with_metrics(resources)
            logger.info(f"CloudWatchEnricher: Enriched {len(enriched_df)} resources")
            return enriched_df
        except Exception as e:
            logger.error(f"CloudWatchEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "m1_no_datapoints",
            "m2_alarm_inactive",
            "m3_custom_metrics_unused",
            "m4_log_group_empty",
            "m5_dashboard_unused",
            "m6_high_cost",
            "m7_retention_waste",
        ]
