#!/usr/bin/env python3
"""ASG Activity Enricher - Wrapper for ASG Activity Enricher"""

import logging
from typing import Dict, List
import pandas as pd
from .base import ActivityEnricherBase
from ..asg_activity_enricher import ASGActivityEnricher as _ASGActivityEnricher

logger = logging.getLogger(__name__)


class ASGEnricher(ActivityEnricherBase):
    """ASG Activity Enricher - ASG1-ASG5 signals."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._asg_enricher = _ASGActivityEnricher(operational_profile=self.operational_profile, region=self.region)

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """Enrich Auto Scaling Groups with ASG1-ASG5 signals."""
        if not self.validate_input(resources, ["asg_name"]):
            return pd.DataFrame()

        try:
            enriched_df = self._asg_enricher.enrich_groups(group_names=[r["asg_name"] for r in resources])
            logger.info(f"ASGEnricher: Enriched {len(enriched_df)} groups")
            return enriched_df
        except Exception as e:
            logger.error(f"ASGEnricher failed: {e}", exc_info=True)
            return pd.DataFrame(resources)

    def get_signal_columns(self) -> List[str]:
        return ["asg1_zero_instances", "asg2_no_scaling", "asg3_old_launch_config", "asg4_always_min", "asg5_high_cost"]
