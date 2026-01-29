#!/usr/bin/env python3
"""
Activity Orchestrator - Parallel Execution Framework
====================================================

Orchestrates activity enrichment across multiple services with ThreadPoolExecutor.

Pattern: Proven parallelization from dashboard_activity_enricher.py
- ThreadPoolExecutor for concurrent enrichment
- Max 10 workers (optimal for API rate limits)
- Graceful degradation for failed enrichers
- Rich CLI progress tracking

Strategic Alignment:
- KISS: Reuse proven parallel execution pattern
- DRY: Single orchestrator for all enrichers
- LEAN: Optimize API efficiency via batching

Usage:
    from runbooks.finops.activity_enrichers import ActivityOrchestrator

    orchestrator = ActivityOrchestrator(operational_profile='ops-profile')
    enriched_results = orchestrator.enrich_all_services(discovery_results)

    # Returns:
    {
        'ec2': DataFrame with E1-E7 signals,
        's3': DataFrame with S1-S7 signals,
        'lambda': DataFrame with L1-L6 signals,
        ...
    }

Author: Runbooks Team
Version: 2.0.0
Epic: Track E - Activity Enrichers Consolidation
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import pandas as pd

from runbooks.common.rich_utils import (
    console,
    create_progress_bar,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from runbooks.common.output_controller import OutputController

# Import all enrichers
from .base import ActivityEnricherBase
from .ec2_enricher import EC2Enricher
from .s3_enricher import S3Enricher
from .lambda_enricher import LambdaEnricher
from .dynamodb_enricher import DynamoDBEnricher
from .rds_enricher import RDSEnricher
from .ecs_enricher import ECSEnricher
from .workspaces_enricher import WorkSpacesEnricher
from .appstream_enricher import AppStreamEnricher
from .cloudwatch_enricher import CloudWatchEnricher
from .config_enricher import ConfigEnricher
from .cloudtrail_enricher import CloudTrailEnricher
from .asg_enricher import ASGEnricher

logger = logging.getLogger(__name__)


class ActivityOrchestrator:
    """
    Orchestrates parallel activity enrichment across all AWS services.

    Manages:
    - Lazy enricher initialization (only create when needed)
    - ThreadPoolExecutor parallel execution
    - Graceful degradation for failed enrichers
    - Rich CLI progress tracking
    - OutputController integration
    """

    # Service enricher mapping
    SERVICE_ENRICHERS = {
        "ec2": EC2Enricher,
        "s3": S3Enricher,
        "lambda": LambdaEnricher,
        "dynamodb": DynamoDBEnricher,
        "rds": RDSEnricher,
        "ecs": ECSEnricher,
        "workspaces": WorkSpacesEnricher,
        "appstream": AppStreamEnricher,
        "cloudwatch": CloudWatchEnricher,
        "config": ConfigEnricher,
        "cloudtrail": CloudTrailEnricher,
        "asg": ASGEnricher,
    }

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: str = "ap-southeast-2",
        max_workers: int = 10,
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize Activity Orchestrator.

        Args:
            operational_profile: AWS profile for operational APIs
            region: AWS region (default: ap-southeast-2)
            max_workers: Max concurrent enrichers (default: 10)
            output_controller: OutputController for UX consistency
        """
        self.operational_profile = operational_profile
        self.region = region
        self.max_workers = max_workers
        self.output_controller = output_controller or OutputController()

        # Lazy initialization - enrichers created on demand
        self._enrichers: Dict[str, ActivityEnricherBase] = {}

        logger.info(
            f"ActivityOrchestrator initialized (profile={operational_profile}, region={region}, workers={max_workers})"
        )

    def get_enricher(self, service_name: str) -> Optional[ActivityEnricherBase]:
        """
        Get or create enricher for service (lazy initialization).

        Args:
            service_name: Service name (e.g., 'ec2', 's3')

        Returns:
            Enricher instance or None if not available
        """
        if service_name not in self._enrichers:
            enricher_class = self.SERVICE_ENRICHERS.get(service_name)
            if not enricher_class:
                logger.warning(f"No enricher available for service: {service_name}")
                return None

            try:
                self._enrichers[service_name] = enricher_class(
                    operational_profile=self.operational_profile,
                    region=self.region,
                    output_controller=self.output_controller,
                )
                logger.debug(f"Created enricher for {service_name}")
            except Exception as e:
                logger.error(f"Failed to create enricher for {service_name}: {e}", exc_info=True)
                return None

        return self._enrichers[service_name]

    def enrich_service(self, service_name: str, resources: List[Dict], **kwargs) -> Optional[pd.DataFrame]:
        """
        Enrich single service with activity signals.

        Args:
            service_name: Service name (e.g., 'ec2', 's3')
            resources: List of resource dictionaries
            **kwargs: Service-specific enrichment parameters

        Returns:
            Enriched DataFrame or None on error
        """
        if not resources:
            logger.debug(f"No resources to enrich for {service_name}")
            return None

        enricher = self.get_enricher(service_name)
        if not enricher:
            logger.warning(f"Enricher not available for {service_name}")
            return None

        try:
            start_time = time.time()
            enriched_df = enricher.enrich(resources, **kwargs)
            elapsed = time.time() - start_time

            logger.info(f"Enriched {len(enriched_df)} {service_name} resources in {elapsed:.2f}s")
            return enriched_df

        except Exception as e:
            logger.error(f"Enrichment failed for {service_name}: {e}", exc_info=True)
            return None

    def enrich_all_services(
        self, discovery_results: Dict[str, List[Dict]], services: Optional[List[str]] = None, **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        Enrich multiple services in parallel with ThreadPoolExecutor.

        Args:
            discovery_results: Dict mapping service name to resources
            services: List of services to enrich (None = all)
            **kwargs: Service-specific enrichment parameters

        Returns:
            Dict mapping service name to enriched DataFrames

        Example:
            discovery_results = {
                'ec2': [{'instance_id': 'i-abc123', ...}],
                's3': [{'bucket_name': 'my-bucket', ...}],
                'lambda': [{'function_name': 'my-func', ...}]
            }

            enriched = orchestrator.enrich_all_services(discovery_results)
            # Returns: {'ec2': DataFrame, 's3': DataFrame, 'lambda': DataFrame}
        """
        # Filter services to enrich
        services_to_enrich = services or list(discovery_results.keys())
        services_to_enrich = [s for s in services_to_enrich if s in discovery_results and discovery_results[s]]

        if not services_to_enrich:
            logger.warning("No services to enrich")
            return {}

        # Display progress
        if not self.output_controller.is_suppressed():
            print_info(
                f"Enriching {len(services_to_enrich)} services with activity signals "
                f"(parallel execution, max {self.max_workers} workers)"
            )

        enriched_results = {}
        start_time = time.time()

        # Parallel execution with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit enrichment tasks
            future_to_service = {
                executor.submit(
                    self.enrich_service, service_name, discovery_results[service_name], **kwargs
                ): service_name
                for service_name in services_to_enrich
            }

            # Progress tracking
            with create_progress_bar() as progress:
                task = progress.add_task("[cyan]Enriching services...", total=len(future_to_service))

                # Collect results as they complete
                for future in as_completed(future_to_service):
                    service_name = future_to_service[future]

                    try:
                        enriched_df = future.result()
                        if enriched_df is not None:
                            enriched_results[service_name] = enriched_df
                            logger.info(f"✓ {service_name}: {len(enriched_df)} resources enriched")
                        else:
                            logger.warning(f"✗ {service_name}: Enrichment failed")

                    except Exception as e:
                        logger.error(f"✗ {service_name}: Exception during enrichment: {e}", exc_info=True)

                    progress.update(task, advance=1)

        elapsed = time.time() - start_time

        # Summary
        if not self.output_controller.is_suppressed():
            print_success(
                f"Enrichment complete: {len(enriched_results)}/{len(services_to_enrich)} "
                f"services enriched in {elapsed:.2f}s"
            )

        logger.info(
            f"ActivityOrchestrator: Enriched {len(enriched_results)} services "
            f"in {elapsed:.2f}s (avg: {elapsed / len(enriched_results):.2f}s/service)"
        )

        return enriched_results

    def get_available_services(self) -> List[str]:
        """
        Get list of available service enrichers.

        Returns:
            List of service names with enrichers
        """
        return list(self.SERVICE_ENRICHERS.keys())

    def get_service_signals(self, service_name: str) -> Optional[List[str]]:
        """
        Get signal column names for service.

        Args:
            service_name: Service name (e.g., 'ec2', 's3')

        Returns:
            List of signal column names or None
        """
        enricher = self.get_enricher(service_name)
        if enricher and hasattr(enricher, "get_signal_columns"):
            return enricher.get_signal_columns()
        return None
