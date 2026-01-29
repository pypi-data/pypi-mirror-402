#!/usr/bin/env python3
"""
Base Activity Enricher Interface - Abstract Pattern for Unified Architecture
=============================================================================

Defines standard interface for all activity enrichers:
- Abstract enrich() method (service-specific implementation)
- Common session management (boto3 client/resource creation)
- Unified error handling patterns
- Rich CLI integration for consistent UX

Design Philosophy (KISS/DRY/LEAN):
- Single interface, multiple implementations
- Dependency injection for AWS session management
- Graceful degradation for terminated resources
- Thread-safe execution

Strategic Alignment:
- Objective 1 (runbooks package): Reusable enrichment framework
- Enterprise SDLC: Abstract interface enables testing and mocking
- KISS/DRY/LEAN: Common patterns extracted, zero duplication

Usage:
    class MyServiceEnricher(ActivityEnricherBase):
        def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
            # Service-specific enrichment logic
            return enriched_df

Author: Runbooks Team
Version: 2.0.0
Epic: Track E - Activity Enrichers Consolidation
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from runbooks.common.profile_utils import (
    get_profile_for_operation,
    create_operational_session,
)
from runbooks.common.output_controller import OutputController

logger = logging.getLogger(__name__)


class ActivityEnricherBase(ABC):
    """
    Abstract base class for activity enrichers.

    All service-specific enrichers inherit from this base class and implement
    the enrich() method with their specific activity signal logic.

    Attributes:
        operational_profile (str): AWS profile for operational APIs
        region (str): AWS region (default: ap-southeast-2)
        session (boto3.Session): Initialized AWS session
        output_controller (OutputController): UX consistency manager
    """

    def __init__(
        self,
        operational_profile: Optional[str] = None,
        region: str = "ap-southeast-2",
        output_controller: Optional[OutputController] = None,
    ):
        """
        Initialize base enricher with AWS session and output controller.

        Args:
            operational_profile: AWS profile name (defaults to environment)
            region: AWS region (default: ap-southeast-2)
            output_controller: OutputController for UX consistency
        """
        self.operational_profile = operational_profile or get_profile_for_operation("CENTRALISED_OPS_PROFILE")
        self.region = region
        self.session = create_operational_session(profile_name=self.operational_profile)
        self.output_controller = output_controller or OutputController()

        # Service-specific clients (lazy initialization in subclasses)
        self._clients: Dict[str, Any] = {}

        logger.debug(
            f"Initialized {self.__class__.__name__} (profile={self.operational_profile}, region={self.region})"
        )

    def get_client(self, service_name: str) -> Any:
        """
        Get or create boto3 client with caching.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3', 'lambda')

        Returns:
            boto3 client for the specified service
        """
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(service_name, region_name=self.region)
            logger.debug(f"Created {service_name} client for region {self.region}")

        return self._clients[service_name]

    def get_resource(self, service_name: str) -> Any:
        """
        Get or create boto3 resource with caching.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')

        Returns:
            boto3 resource for the specified service
        """
        resource_key = f"{service_name}_resource"

        if resource_key not in self._clients:
            self._clients[resource_key] = self.session.resource(service_name)
            logger.debug(f"Created {service_name} resource")

        return self._clients[resource_key]

    @abstractmethod
    def enrich(self, resources: List[Dict], **kwargs) -> pd.DataFrame:
        """
        Enrich resources with activity signals (service-specific implementation).

        Args:
            resources: List of resource dictionaries from discovery
            **kwargs: Service-specific enrichment parameters

        Returns:
            pandas DataFrame with activity signal columns added

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement enrich() method")

    def handle_api_error(self, error: Exception, resource_id: str, operation: str) -> Optional[Dict[str, Any]]:
        """
        Handle AWS API errors with graceful degradation.

        Pattern: Terminated resources should not block enrichment pipeline.
        Return None or empty dict for terminated resources, log for investigation.

        Args:
            error: Exception from AWS API call
            resource_id: Resource identifier for context
            operation: Operation name for logging

        Returns:
            None for terminated resources, empty dict for retryable errors
        """
        if isinstance(error, ClientError):
            error_code = error.response["Error"]["Code"]

            # Terminated resources - graceful degradation (skip API enrichment)
            if error_code in [
                "InvalidInstanceID.NotFound",
                "NoSuchEntity",
                "ResourceNotFoundException",
                "DBInstanceNotFound",
            ]:
                logger.debug(
                    f"Resource {resource_id} not found ({operation}) - likely terminated, skipping API enrichment"
                )
                return None

            # Access denied - log and skip
            elif error_code in ["AccessDenied", "UnauthorizedOperation"]:
                logger.warning(f"Access denied for {resource_id} ({operation}) - check IAM permissions")
                return {}

            # Throttling - log and skip (retry logic in caller)
            elif error_code in ["Throttling", "RequestLimitExceeded"]:
                logger.warning(f"API throttling for {resource_id} ({operation}) - consider batch execution")
                return {}

            # Unknown error - log full exception
            else:
                logger.error(f"API error for {resource_id} ({operation}): {error}", exc_info=True)
                return {}

        # Non-AWS errors - log and skip
        else:
            logger.error(f"Unexpected error for {resource_id} ({operation}): {error}", exc_info=True)
            return {}

    def validate_input(self, resources: List[Dict], required_fields: List[str]) -> bool:
        """
        Validate input resources have required fields.

        Args:
            resources: List of resource dictionaries
            required_fields: List of required field names

        Returns:
            True if valid, False otherwise (logs validation errors)
        """
        if not resources:
            logger.warning(f"{self.__class__.__name__}: Empty resource list")
            return False

        missing_fields = []
        for field in required_fields:
            if not any(field in r for r in resources):
                missing_fields.append(field)

        if missing_fields:
            logger.error(f"{self.__class__.__name__}: Missing required fields: {missing_fields}")
            return False

        return True

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(profile={self.operational_profile}, region={self.region})"
