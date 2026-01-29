#!/usr/bin/env python3
"""DynamoDB Activity Enricher - Wrapper for DynamoDB Activity Enricher"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..dynamodb_activity_enricher import DynamoDBActivityEnricher as _DynamoDBActivityEnricher

logger = logging.getLogger(__name__)


class DynamoDBEnricher(ActivityEnricherBase):
    """DynamoDB Activity Enricher - D1-D7 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dynamodb_enricher = _DynamoDBActivityEnricher(
            operational_profile=self.operational_profile, region=self.region
        )

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich DynamoDB tables with D1-D7 signals."""
        if not self.validate_input(resources, ["table_name"]):
            return pd.DataFrame()

        try:
            enriched_df = self._dynamodb_enricher.enrich_tables(table_names=[r["table_name"] for r in resources])
            logger.info(f"DynamoDBEnricher: Enriched {len(enriched_df)} tables")
            return enriched_df
        except Exception as e:
            logger.error(f"DynamoDBEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return [
            "d1_zero_reads",
            "d2_zero_writes",
            "d3_provisioned_waste",
            "d4_gsi_unused",
            "d5_old_table",
            "d6_no_pitr",
            "d7_high_cost",
        ]
