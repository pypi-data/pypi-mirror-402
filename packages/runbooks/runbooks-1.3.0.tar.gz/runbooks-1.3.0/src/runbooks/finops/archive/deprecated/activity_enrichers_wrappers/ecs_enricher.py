#!/usr/bin/env python3
"""ECS Activity Enricher - Wrapper for ECS Activity Enricher"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..ecs_activity_enricher import ECSActivityEnricher as _ECSActivityEnricher

logger = logging.getLogger(__name__)


class ECSEnricher(ActivityEnricherBase):
    """ECS Activity Enricher - C1-C7 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ecs_enricher = _ECSActivityEnricher(operational_profile=self.operational_profile, region=self.region)

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich ECS clusters with C1-C7 signals."""
        if not self.validate_input(resources, ["cluster_name"]):
            return pd.DataFrame()

        try:
            enriched_df = self._ecs_enricher.enrich_clusters(cluster_names=[r["cluster_name"] for r in resources])
            logger.info(f"ECSEnricher: Enriched {len(enriched_df)} clusters")
            return enriched_df
        except Exception as e:
            logger.error(f"ECSEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "c1_zero_tasks",
            "c2_low_cpu",
            "c3_low_memory",
            "c4_no_services",
            "c5_old_image",
            "c6_idle_cluster",
            "c7_high_cost",
        ]
