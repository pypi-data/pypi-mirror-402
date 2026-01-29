#!/usr/bin/env python3
"""RDS Activity Enricher - Wrapper for RDS Analyzer"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..rds_analyzer import RDSCostAnalyzer

logger = logging.getLogger(__name__)


class RDSEnricher(ActivityEnricherBase):
    """RDS Activity Enricher - R1-R7 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rds_analyzer = RDSCostAnalyzer(operational_profile=self.operational_profile, region=self.region)

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich RDS instances with R1-R7 signals."""
        if not self.validate_input(resources, ["db_instance_id"]):
            return pd.DataFrame()

        try:
            enriched_df = self._rds_analyzer.analyze_instances(instance_ids=[r["db_instance_id"] for r in resources])
            logger.info(f"RDSEnricher: Enriched {len(enriched_df)} instances")
            return enriched_df
        except Exception as e:
            logger.error(f"RDSEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "r1_low_connections",
            "r2_low_cpu",
            "r3_storage_waste",
            "r4_no_read_replica",
            "r5_old_engine",
            "r6_no_multi_az",
            "r7_high_cost",
        ]
