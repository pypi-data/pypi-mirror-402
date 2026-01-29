#!/usr/bin/env python3
"""
SSM Integration - AWS Systems Manager Agent Heartbeat Status

This module provides integration with AWS Systems Manager to check
EC2 instance heartbeat status and identify stale/offline instances.

Decommission Scoring Framework:
- Signal E2 (SSM Agent Offline/Stale): 8 points (>7 days since heartbeat)
- API: describe_instance_information with PingStatus filters
- Graceful fallback: instances not SSM-managed return score=0

Pattern: Follows base_enrichers.py pattern (Rich CLI, error handling, boto3 integration)

Usage:
    from runbooks.finops.ssm_integration import get_ssm_heartbeat_status

    # Get SSM heartbeat status for instances
    ssm_status = get_ssm_heartbeat_status(
        instance_ids=['i-abc123', 'i-def456'],
        profile='operational-profile',
        region='ap-southeast-2'
    )

    # Returns: {
    #     'i-abc123': {
    #         'score': 8,
    #         'ping_status': 'Offline',
    #         'last_ping_datetime': '2025-10-01T12:00:00Z',
    #         'last_ping_days': 28,
    #         'platform_type': 'Linux',
    #         'agent_version': '3.2.582.0'
    #     },
    #     'i-def456': {
    #         'score': 0,
    #         'ping_status': 'Not SSM managed',
    #         'last_ping_datetime': None,
    #         'last_ping_days': 0,
    #         'note': 'Instance not registered with SSM'
    #     }
    # }

Strategic Alignment:
- Objective 1 (runbooks package): Reusable decommission analysis for notebooks
- Enterprise SDLC: Evidence-based activity detection with audit trails
- KISS/DRY/LEAN: Reuse boto3 patterns, enhance existing enrichers
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..common.rich_utils import (
    console,
    print_error,
    print_info,
    print_success,
    print_warning,
    create_progress_bar,
)

logger = logging.getLogger(__name__)


def get_ssm_heartbeat_status(
    instance_ids: List[str],
    profile: Optional[str] = None,
    region: str = "ap-southeast-2",
    stale_threshold_days: int = 14,
    verbose: bool = False,
) -> Dict[str, Dict]:
    """
    Get SSM agent heartbeat status for EC2 instances.

    Queries AWS Systems Manager API to check agent ping status and
    last heartbeat timestamp. Identifies instances with stale/offline
    SSM agents indicating potential abandonment.

    Signal E4: SSM heartbeat (8 points) - per ec2-workspaces.scoring.md
    - PingStatus != Online OR LastPingDateTime > 14 days
    - Indicates potential instance abandonment
    - Complements Compute Optimizer idle signal (E1)

    Args:
        instance_ids: List of EC2 instance IDs to check
        profile: AWS profile name (default: $OPERATIONAL_PROFILE or $AWS_PROFILE)
        region: AWS region (default: ap-southeast-2)
        stale_threshold_days: Days threshold for stale detection (default: 14 per specification)

    Returns:
        Dictionary mapping instance IDs to SSM status:
        {
            'i-abc123': {
                'score': 8,  # 8 if offline/stale, 0 if online/not managed
                'ping_status': 'Offline' | 'Online' | 'ConnectionLost' | 'Not SSM managed',
                'last_ping_datetime': '2025-10-01T12:00:00Z' or None,
                'last_ping_days': 28,  # Days since last heartbeat
                'platform_type': 'Linux' or 'Windows',
                'agent_version': '3.2.582.0',
                'ip_address': '10.0.1.5',
                'note': 'Optional explanation'
            }
        }

    Raises:
        ClientError: AWS API errors (AccessDenied, ServiceUnavailable, etc.)
        Exception: Unexpected errors with comprehensive logging

    Example:
        >>> ssm_status = get_ssm_heartbeat_status(
        ...     instance_ids=['i-abc123', 'i-def456'],
        ...     profile='operational'
        ... )
        >>> for iid, status in ssm_status.items():
        ...     if status['score'] > 0:
        ...         print(f"{iid}: {status['ping_status']} ({status['last_ping_days']} days)")

    Profile Cascade:
        1. profile parameter (explicit)
        2. $OPERATIONAL_PROFILE environment variable
        3. $AWS_PROFILE environment variable
        4. 'default' AWS profile

    Graceful Fallback:
        - Instances not registered with SSM return score=0 with note
        - No API errors thrown for unmanaged instances
        - Allows decommission scoring to proceed with available signals
    """
    try:
        from runbooks.common.profile_utils import create_operational_session, create_timeout_protected_client

        # Profile cascade: param > $OPERATIONAL_PROFILE > $AWS_PROFILE > 'default'
        if not profile:
            profile = os.getenv("OPERATIONAL_PROFILE") or os.getenv("AWS_PROFILE") or "default"

        # Debug details (show only in verbose mode)
        if verbose:
            print_info(f"🔍 Checking SSM agent heartbeat status (profile: {profile}, region: {region})")
            print_info(f"   Stale threshold: >{stale_threshold_days} days since last ping")

        # Initialize SSM client using standardized helper
        session = create_operational_session(profile)
        ssm_client = create_timeout_protected_client(session, "ssm", region)

        # Query SSM instance information
        ssm_status = {}

        # Batch query in chunks of 50 (SSM API limit)
        chunk_size = 50
        now = datetime.now(timezone.utc)

        with create_progress_bar() as progress:
            task = progress.add_task("[cyan]Querying SSM agent status...", total=len(instance_ids))

            for i in range(0, len(instance_ids), chunk_size):
                chunk = instance_ids[i : i + chunk_size]

                try:
                    # Query SSM for instance information
                    response = ssm_client.describe_instance_information(
                        Filters=[{"Key": "InstanceIds", "Values": chunk}], MaxResults=chunk_size
                    )

                    # Build lookup of SSM-managed instances
                    ssm_managed = {}
                    for info in response.get("InstanceInformationList", []):
                        instance_id = info.get("InstanceId")
                        ssm_managed[instance_id] = info

                    # Process each instance in chunk
                    for instance_id in chunk:
                        if instance_id in ssm_managed:
                            # Instance is SSM-managed
                            info = ssm_managed[instance_id]

                            ping_status = info.get("PingStatus", "Unknown")
                            last_ping = info.get("LastPingDateTime")
                            platform_type = info.get("PlatformType", "Unknown")
                            agent_version = info.get("AgentVersion", "Unknown")
                            ip_address = info.get("IPAddress", "N/A")

                            # Calculate days since last ping
                            if last_ping:
                                # last_ping is already datetime object from boto3
                                if not last_ping.tzinfo:
                                    last_ping = last_ping.replace(tzinfo=timezone.utc)
                                days_since = (now - last_ping).days
                                last_ping_str = last_ping.strftime("%Y-%m-%dT%H:%M:%SZ")
                            else:
                                days_since = 999  # Unknown
                                last_ping_str = None

                            # Determine score based on status and staleness
                            if ping_status in ["Offline", "ConnectionLost"] or days_since > stale_threshold_days:
                                score = 8  # Signal E2 weight
                                status_label = (
                                    f"{ping_status} (stale)" if days_since > stale_threshold_days else ping_status
                                )
                            else:
                                score = 0  # Online and recent
                                status_label = ping_status

                            ssm_status[instance_id] = {
                                "score": score,
                                "ping_status": status_label,
                                "last_ping_datetime": last_ping_str,
                                "last_ping_days": days_since,
                                "platform_type": platform_type,
                                "agent_version": agent_version,
                                "ip_address": ip_address,
                            }

                        else:
                            # Instance not SSM-managed (graceful fallback)
                            ssm_status[instance_id] = {
                                "score": 0,  # No penalty for not being SSM-managed
                                "ping_status": "Not SSM managed",
                                "last_ping_datetime": None,
                                "last_ping_days": 0,
                                "note": "Instance not registered with SSM",
                            }

                        progress.update(task, advance=1)

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "Unknown")

                    if error_code == "AccessDeniedException":
                        print_warning(f"⚠️  Access denied to SSM API (instances {i}-{i + len(chunk) - 1})")
                        print_info(f"   Required IAM permission: ssm:DescribeInstanceInformation")

                        # Fill chunk with "not managed" fallback
                        for instance_id in chunk:
                            if instance_id not in ssm_status:
                                ssm_status[instance_id] = {
                                    "score": 0,
                                    "ping_status": "SSM access denied",
                                    "last_ping_datetime": None,
                                    "last_ping_days": 0,
                                    "note": "Cannot verify SSM status - access denied",
                                }
                        progress.update(task, advance=len(chunk))
                        continue
                    else:
                        raise

        # Summary statistics
        managed_count = len(
            [s for s in ssm_status.values() if s["ping_status"] not in ["Not SSM managed", "SSM access denied"]]
        )
        offline_count = len([s for s in ssm_status.values() if s["score"] > 0])
        online_count = managed_count - offline_count

        # Consolidated completion message (business value only)
        if not verbose:
            # Compact: 1 line with essential metrics
            print_success(f"✅ SSM: {len(ssm_status)} instances │ {managed_count} managed │ {online_count} online")
        else:
            # Verbose: detailed breakdown
            print_success(f"✅ SSM heartbeat check complete: {len(ssm_status)} instances analyzed")
            print_info(f"   SSM-managed: {managed_count} | Online: {online_count} | Offline/Stale: {offline_count}")

        return ssm_status

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        print_error(f"❌ SSM API error: {error_code}")
        print_warning(f"   Error details: {e}")
        logger.error(f"SSM API error: {e}", exc_info=True)

        # Return empty status for all instances (graceful fallback)
        return {
            iid: {
                "score": 0,
                "ping_status": "SSM query failed",
                "last_ping_datetime": None,
                "last_ping_days": 0,
                "note": f"SSM API error: {error_code}",
            }
            for iid in instance_ids
        }

    except Exception as e:
        print_error(f"❌ SSM heartbeat check failed: {e}")
        logger.error(f"SSM integration error: {e}", exc_info=True)

        # Return empty status for all instances (graceful fallback)
        return {
            iid: {
                "score": 0,
                "ping_status": "Error",
                "last_ping_datetime": None,
                "last_ping_days": 0,
                "note": f"Unexpected error: {str(e)}",
            }
            for iid in instance_ids
        }


def enrich_dataframe_with_ssm_status(
    df,
    instance_id_column: str = "Instance ID",
    profile: Optional[str] = None,
    region: str = "ap-southeast-2",
    stale_threshold_days: int = 14,
):
    """
    Enrich DataFrame with SSM agent heartbeat status.

    Adds 5 columns to DataFrame:
    - ssm_score: Signal E2 score (8 if offline/stale, 0 otherwise)
    - ssm_ping_status: Agent status ('Online', 'Offline', 'Not SSM managed')
    - ssm_last_ping_days: Days since last heartbeat
    - ssm_platform_type: OS platform ('Linux', 'Windows', 'N/A')
    - ssm_agent_version: SSM agent version string

    Args:
        df: pandas DataFrame with EC2 instance IDs
        instance_id_column: Column containing instance IDs (default: 'Instance ID')
        profile: AWS profile name
        region: AWS region (default: ap-southeast-2)
        stale_threshold_days: Days threshold for stale detection (default: 14 per specification)

    Returns:
        Enriched DataFrame with SSM heartbeat signals

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'Instance ID': ['i-abc', 'i-def']})
        >>> enriched = enrich_dataframe_with_ssm_status(df, profile='operational')
        >>> print(enriched[['Instance ID', 'ssm_score', 'ssm_ping_status']])
    """
    import pandas as pd

    try:
        print_info(f"🔍 Enriching DataFrame with SSM agent status...")

        # Get instance IDs
        instance_ids = df[instance_id_column].unique().tolist()

        # Get SSM status
        ssm_status = get_ssm_heartbeat_status(
            instance_ids=instance_ids, profile=profile, region=region, stale_threshold_days=stale_threshold_days
        )

        # Initialize new columns
        df["ssm_score"] = 0
        df["ssm_ping_status"] = "N/A"
        df["ssm_last_ping_days"] = 0
        df["ssm_platform_type"] = "N/A"
        df["ssm_agent_version"] = "N/A"

        enriched_count = 0

        # Enrich rows
        for idx, row in df.iterrows():
            instance_id = str(row.get(instance_id_column, "")).strip()

            if instance_id in ssm_status:
                status = ssm_status[instance_id]

                df.at[idx, "ssm_score"] = status["score"]
                df.at[idx, "ssm_ping_status"] = status["ping_status"]
                df.at[idx, "ssm_last_ping_days"] = status["last_ping_days"]
                df.at[idx, "ssm_platform_type"] = status.get("platform_type", "N/A")
                df.at[idx, "ssm_agent_version"] = status.get("agent_version", "N/A")

                enriched_count += 1

        print_success(f"✅ SSM enrichment complete: {enriched_count}/{len(df)} instances analyzed")

        return df

    except Exception as e:
        print_error(f"❌ SSM enrichment failed: {e}")
        logger.error(f"SSM enrichment error: {e}", exc_info=True)
        return df
