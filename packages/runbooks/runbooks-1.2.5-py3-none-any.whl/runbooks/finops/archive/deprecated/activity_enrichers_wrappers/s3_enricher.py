#!/usr/bin/env python3
"""
S3 Activity Enricher - Wrapper for S3 Activity Enricher
=======================================================

Consolidation Pattern: Delegate to existing s3_activity_enricher.py (KISS/DRY)
- S1-S7 signal definitions preserved
- S3ActivityEnricher functionality maintained
- Backward compatibility via delegation

Strategic Alignment:
- KISS: Don't rewrite working code, consolidate via delegation
- DRY: Single source of truth (s3_activity_enricher.py)
- LEAN: Enhance structure without duplicating functionality

Usage:
    from runbooks.finops.activity_enrichers import S3Enricher

    enricher = S3Enricher(operational_profile='ops-profile')
    enriched_df = enricher.enrich(
        resources=[{'bucket_name': 'my-bucket', ...}]
    )

Author: Runbooks Team
Version: 2.0.0
Epic: Track E - Activity Enrichers Consolidation
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

from .base import ActivityEnricherBase

# Import existing S3 enricher (KISS: reuse existing code)
from ..s3_activity_enricher import S3ActivityEnricher as _S3ActivityEnricher

logger = logging.getLogger(__name__)


class S3Enricher(ActivityEnricherBase):
    """
    S3 Activity Enricher - Delegates to proven s3_activity_enricher.py patterns.

    Signal Pattern (S1-S7):
        S1: 0 requests in 90 days (High confidence: 0.90)
        S2: Old objects >1 year without lifecycle (Medium confidence: 0.75)
        S3: Versioning enabled, no expiration (Medium confidence: 0.70)
        S4: Public access + no encryption (Medium confidence: 0.70)
        S5: Intelligent-Tiering candidates (Medium confidence: 0.65)
        S6: Cross-region replication waste (Medium confidence: 0.65)
        S7: Request cost >$10/month (Medium confidence: 0.70)
    """

    def __init__(self, *args, **kwargs):
        """Initialize S3Enricher with existing implementation."""
        super().__init__(*args, **kwargs)
        self._s3_enricher = _S3ActivityEnricher(operational_profile=self.operational_profile, region=self.region)

    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """
        Enrich S3 buckets with S1-S7 activity signals.

        Args:
            resources: List of S3 bucket dictionaries
            **kwargs: Additional parameters for s3_activity_enricher

        Returns:
            DataFrame with S1-S7 signal columns added
        """
        if not self.validate_input(resources, ["bucket_name"]):
            logger.warning("S3Enricher: Invalid input, returning empty DataFrame")
            return pd.DataFrame()

        # Extract bucket names
        bucket_names = [r.get("bucket_name") for r in resources if "bucket_name" in r]

        try:
            # Delegate to proven s3_activity_enricher.py implementation
            analyses = self._s3_enricher.analyze_bucket_activity(bucket_names=bucket_names)

            # Convert analyses to DataFrame
            enriched_df = pd.DataFrame(analyses)

            logger.info(f"S3Enricher: Enriched {len(enriched_df)} buckets with S1-S7 signals")
            return enriched_df

        except Exception as e:
            logger.error(f"S3Enricher: Enrichment failed: {e}", exc_info=True)
            return pd.DataFrame(resources)  # Return original data on error

    def get_signal_columns(self) -> List[str]:
        """
        Return list of signal column names for S1-S7.

        Returns:
            List of signal column names
        """
        return [
            "s1_zero_requests",
            "s2_old_objects",
            "s3_versioning_no_expiration",
            "s4_public_no_encryption",
            "s5_intelligent_tiering_candidate",
            "s6_replication_waste",
            "s7_high_request_cost",
        ]
