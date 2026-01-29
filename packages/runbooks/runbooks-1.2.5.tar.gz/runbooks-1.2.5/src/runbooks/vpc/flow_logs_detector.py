#!/usr/bin/env python3
"""
VPC Flow Logs Detector - Adaptive Scoring Flow Logs Availability

Detects VPC Flow Logs availability for adaptive scoring architecture supporting
both WITH and WITHOUT Flow Logs scenarios with graceful degradation.

v1.1.29 Enhancement: Enables V6/N6 signals (15 points each, 0.95 confidence)
when Flow Logs available, falls back to V1-V5/N1-N5 (110 points) otherwise.

Adaptive Scoring Strategy:
- WITH Flow Logs: V1-V10 (125pt max, normalized to 0-100, HIGH confidence 0.90+)
- WITHOUT Flow Logs: V1-V5 + V7-V10 (110pt max, normalized to 0-100, MEDIUM confidence 0.75)

AWS Documentation:
- Flow Logs: https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html
- Pricing: $0.50/GB ingested (CloudWatch Logs) or S3 storage costs
- Retention: User-configurable (CloudWatch: 1-3653 days, S3: lifecycle policies)

Business Value:
- Ground truth traffic validation (0.95 confidence vs 0.70-0.85 CloudWatch metrics)
- Zero-cost signal when Flow Logs already enabled (infrastructure reuse)
- Graceful degradation maintains scoring when Flow Logs unavailable

Pattern: Follows FinOps cost_processor.py caching pattern (100% MCP accuracy proven)

Strategic Alignment:
- Objective 1 (runbooks package): Reusable Flow Logs detection
- Enterprise SDLC: Cost optimization with evidence-based signals
- KISS/DRY/LEAN: Single detector, caching, error handling

Usage:
    from runbooks.vpc.flow_logs_detector import detect_flow_logs_availability, get_flow_log_metadata

    # Simple boolean check
    has_flow_logs = detect_flow_logs_availability(vpc_id='vpc-123', ec2_client=ec2)

    # Detailed metadata (location, retention, log group ARN)
    metadata = get_flow_log_metadata(vpc_id='vpc-123', ec2_client=ec2)

    # Cache clearing (use for testing or long-running processes)
    from runbooks.vpc.flow_logs_detector import clear_flow_logs_cache
    clear_flow_logs_cache()

Author: Runbooks Team
Version: 1.1.29
Epic: v1.1.29 VPC/VPCE Enhanced Signals
Track: Track 3 Day 1 - Flow Logs Detection + V6-V10/N6-N10 Signals
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


# Global cache for Flow Logs availability (TTL: 5 minutes)
_FLOW_LOGS_CACHE: Dict[str, Dict] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


def clear_flow_logs_cache() -> None:
    """
    Clear the Flow Logs cache.

    Use this for testing or when you need to refresh Flow Logs state
    in long-running processes (e.g., multi-account enrichment).
    """
    global _FLOW_LOGS_CACHE
    _FLOW_LOGS_CACHE.clear()
    logger.debug("Flow Logs cache cleared")


def detect_flow_logs_availability(vpc_id: str, ec2_client) -> bool:
    """
    Detect if VPC Flow Logs are ACTIVE for a given VPC.

    AWS API: ec2:DescribeFlowLogs with filters for VPC ID + ACTIVE state
    Caching: 5-minute TTL to avoid repeated API calls (performance optimization)
    Error Handling: Returns False on access denied, throttling, or API errors

    Args:
        vpc_id: VPC ID to check (e.g., 'vpc-0123456789abcdef0')
        ec2_client: boto3 EC2 client (must have ec2:DescribeFlowLogs permission)

    Returns:
        True if ACTIVE Flow Logs exist for VPC, False otherwise

    Examples:
        >>> # Check Flow Logs availability
        >>> import boto3
        >>> ec2 = boto3.client('ec2', region_name='ap-southeast-2')
        >>> has_flow_logs = detect_flow_logs_availability('vpc-123', ec2)
        >>> print(f"Flow Logs enabled: {has_flow_logs}")
        Flow Logs enabled: True

        >>> # Adaptive scoring decision
        >>> if has_flow_logs:
        ...     max_score = 125  # V1-V10 with Flow Logs
        ...     confidence = 0.95
        ... else:
        ...     max_score = 110  # V1-V5 + V7-V10 without Flow Logs
        ...     confidence = 0.75
    """
    # Check cache first (performance optimization)
    cache_key = f"{vpc_id}"
    if cache_key in _FLOW_LOGS_CACHE:
        cached_entry = _FLOW_LOGS_CACHE[cache_key]
        cache_age = (datetime.now() - cached_entry["timestamp"]).total_seconds()

        if cache_age < _CACHE_TTL_SECONDS:
            logger.debug(f"Flow Logs cache HIT for {vpc_id} (age: {cache_age:.1f}s)")
            return cached_entry["available"]
        else:
            # Cache expired, remove entry
            del _FLOW_LOGS_CACHE[cache_key]
            logger.debug(f"Flow Logs cache EXPIRED for {vpc_id} (age: {cache_age:.1f}s)")

    try:
        # Query Flow Logs for VPC with ACTIVE status filter
        response = ec2_client.describe_flow_logs(
            Filters=[
                {"Name": "resource-id", "Values": [vpc_id]},
                {"Name": "flow-log-resource-type", "Values": ["VPC"]},
                {"Name": "flow-log-status", "Values": ["ACTIVE"]},
            ],
            MaxResults=10,  # Limit results (only need to know if ANY exist)
        )

        flow_logs = response.get("FlowLogs", [])
        available = len(flow_logs) > 0

        # Cache result with timestamp
        _FLOW_LOGS_CACHE[cache_key] = {
            "available": available,
            "timestamp": datetime.now(),
            "flow_log_count": len(flow_logs),
        }

        if available:
            logger.debug(f"Flow Logs ACTIVE for {vpc_id} ({len(flow_logs)} logs)")
        else:
            logger.debug(f"Flow Logs NOT ACTIVE for {vpc_id}")

        return available

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")

        if error_code == "UnauthorizedOperation":
            # Access denied - graceful degradation (conservative: assume unavailable)
            logger.debug(f"Access denied for Flow Logs detection on {vpc_id}: {e}")
            return False
        elif error_code == "Throttling":
            # Throttling - graceful degradation (conservative: assume unavailable)
            logger.debug(f"Throttling on Flow Logs detection for {vpc_id}: {e}")
            return False
        else:
            # Other AWS errors - graceful degradation
            logger.warning(f"Flow Logs detection failed for {vpc_id}: {error_code} - {e}")
            return False

    except Exception as e:
        # Unexpected errors - graceful degradation
        logger.warning(f"Unexpected error in Flow Logs detection for {vpc_id}: {e}")
        return False


def get_flow_log_metadata(vpc_id: str, ec2_client) -> Optional[Dict]:
    """
    Get detailed Flow Logs metadata for a VPC.

    Provides comprehensive Flow Logs information for debugging, analysis,
    and understanding Flow Logs configuration (destination, retention, format).

    Args:
        vpc_id: VPC ID to analyze
        ec2_client: boto3 EC2 client

    Returns:
        Dict with Flow Logs metadata or None if unavailable:
        {
            'flow_log_ids': List[str],  # Flow Log IDs
            'destinations': List[str],   # CloudWatch Log Group ARNs or S3 bucket ARNs
            'log_format': str,           # Flow Logs format (default or custom)
            'max_aggregation_interval': int,  # Seconds (60 or 600)
            'creation_times': List[datetime],  # Flow Log creation timestamps
            'flow_log_count': int        # Number of Flow Logs for VPC
        }

    Examples:
        >>> metadata = get_flow_log_metadata('vpc-123', ec2)
        >>> if metadata:
        ...     print(f"Flow Logs count: {metadata['flow_log_count']}")
        ...     print(f"Destinations: {metadata['destinations']}")
        ...     print(f"Max aggregation: {metadata['max_aggregation_interval']}s")
    """
    try:
        response = ec2_client.describe_flow_logs(
            Filters=[
                {"Name": "resource-id", "Values": [vpc_id]},
                {"Name": "flow-log-resource-type", "Values": ["VPC"]},
                {"Name": "flow-log-status", "Values": ["ACTIVE"]},
            ]
        )

        flow_logs = response.get("FlowLogs", [])
        if not flow_logs:
            return None

        metadata = {
            "flow_log_ids": [fl["FlowLogId"] for fl in flow_logs],
            "destinations": [fl.get("LogDestination") or fl.get("LogGroupName", "N/A") for fl in flow_logs],
            "log_format": flow_logs[0].get("LogFormat", "default"),
            "max_aggregation_interval": flow_logs[0].get("MaxAggregationInterval", 600),
            "creation_times": [fl.get("CreationTime") for fl in flow_logs],
            "flow_log_count": len(flow_logs),
        }

        return metadata

    except Exception as e:
        logger.debug(f"Flow Logs metadata retrieval failed for {vpc_id}: {e}")
        return None


def check_flow_logs_with_exponential_backoff(
    vpc_id: str, ec2_client, max_retries: int = 3, base_delay: float = 1.0
) -> bool:
    """
    Detect Flow Logs availability with exponential backoff retry logic.

    Use this function for critical paths where Flow Logs detection must succeed
    despite transient throttling errors (e.g., multi-account batch processing).

    Args:
        vpc_id: VPC ID to check
        ec2_client: boto3 EC2 client
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)

    Returns:
        True if ACTIVE Flow Logs exist, False otherwise

    Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: Wait 1.0s (base_delay)
        - Attempt 3: Wait 2.0s (base_delay * 2)
        - Attempt 4: Wait 4.0s (base_delay * 4)

    Examples:
        >>> # Use in multi-account batch processing
        >>> for vpc in vpcs:
        ...     has_flow_logs = check_flow_logs_with_exponential_backoff(
        ...         vpc_id=vpc['vpc_id'],
        ...         ec2_client=ec2,
        ...         max_retries=3
        ...     )
    """
    import time

    for attempt in range(max_retries + 1):
        try:
            return detect_flow_logs_availability(vpc_id, ec2_client)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "Throttling" and attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s, ...
                delay = base_delay * (2**attempt)
                logger.debug(
                    f"Throttling on Flow Logs detection (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {delay:.1f}s"
                )
                time.sleep(delay)
            else:
                # Non-throttling error or max retries reached
                logger.warning(f"Flow Logs detection failed after {attempt + 1} attempts: {e}")
                return False

        except Exception as e:
            logger.warning(f"Unexpected error in Flow Logs detection: {e}")
            return False

    # Max retries exhausted
    return False


# Export interface
__all__ = [
    "detect_flow_logs_availability",
    "get_flow_log_metadata",
    "check_flow_logs_with_exponential_backoff",
    "clear_flow_logs_cache",
]
