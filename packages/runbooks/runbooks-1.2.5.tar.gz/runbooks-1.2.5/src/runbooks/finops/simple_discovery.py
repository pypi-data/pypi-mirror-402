#!/usr/bin/env python3
"""
Simple Discovery Interface for FinOps Notebooks

Provides simplified wrapper functions for notebook-based AWS resource discovery
and activity enrichment. Designed for non-technical users (CTO, CEO, CFO personas)
with minimal configuration requirements.

Strategic Alignment:
- Objective 1 (runbooks package): Simplified notebook integration
- Enterprise SDLC: Composition over duplication (wraps existing enrichers)
- KISS/DRY/LEAN: Single-profile interface, zero subprocess dependencies

Architecture:
- Wraps DashboardActivityEnricher for comprehensive activity signals
- Wraps DecommissionScorer for prioritization logic
- Provides unified interface: discover → enrich → score workflow
- AWS_PROFILE environment variable for authentication

Usage:
    from runbooks.finops.simple_discovery import (
        discover_all_resources,
        enrich_with_activity,
        score_decommission_candidates
    )

    # Step 1: Discover resources (EC2, RDS, WorkSpaces, Snapshots, S3, DynamoDB)
    resources = discover_all_resources(profile='my-aws-profile')

    # Step 2: Enrich with activity signals (E1-E7, W1-W6, R1-R7)
    enriched = enrich_with_activity(resources, profile='my-aws-profile')

    # Step 3: Score decommission candidates (MUST/SHOULD/COULD/KEEP tiers)
    scored = score_decommission_candidates(enriched)

Author: Runbooks Team
Version: 1.1.20
Epic: v1.1.20 FinOps Dashboard Enhancements - Notebook Simplification
"""

import os
from typing import Dict, Optional

import pandas as pd

# Reuse existing enrichers (KISS/DRY/LEAN - orchestrate, don't recreate)
from runbooks.finops.dashboard_activity_enricher import DashboardActivityEnricher
from runbooks.finops.decommission_scorer import score_ec2_dataframe, score_workspaces_dataframe

# Rich CLI integration for consistent UX
from runbooks.common.rich_utils import console, print_error, print_info, print_success, print_warning


def discover_all_resources(profile: Optional[str] = None, verbose: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Single-function discovery for notebooks - returns all supported resource types.

    Discovers AWS resources across supported services:
    - EC2 instances (compute)
    - RDS instances (databases)
    - WorkSpaces (virtual desktops)
    - EBS snapshots (storage)
    - S3 buckets (object storage)
    - DynamoDB tables (NoSQL databases)

    Args:
        profile: AWS profile name (defaults to AWS_PROFILE env var or 'default')
        verbose: Enable verbose output showing diagnostic information (default: False)

    Returns:
        Dict with service names as keys and DataFrames as values
        Example:
            {
                'ec2': DataFrame with EC2 instances,
                'rds': DataFrame with RDS instances,
                'workspaces': DataFrame with WorkSpaces,
                's3': DataFrame with S3 buckets
            }

    Note:
        Services with no resources or errors are excluded from results.
        Empty/None DataFrames are automatically filtered out.
    """
    # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
    from runbooks.common.profile_utils import get_profile_for_operation

    profile = get_profile_for_operation(
        operation_type="operational", user_specified_profile=profile, silent=not verbose
    )

    # Display what profile is being used for transparency
    if verbose:
        print_info(f"Discovering AWS resources using profile: {profile}")

    try:
        # Import inventory collector (lazy import for faster module loading)
        from runbooks.inventory.core.collector import EnhancedInventoryCollector
        import boto3

        # Set environment to ensure all AWS operations use correct profile
        # This prevents complex enterprise profile logic from overriding
        if profile != "default":
            os.environ["AWS_PROFILE"] = profile
            # Also set enterprise profile env vars to prevent override
            os.environ["AWS_MANAGEMENT_PROFILE"] = profile
            os.environ["AWS_BILLING_PROFILE"] = profile
            os.environ["AWS_CENTRALISED_OPS_PROFILE"] = profile
            os.environ["AWS_SINGLE_ACCOUNT_PROFILE"] = profile

        # Initialize collector with single profile
        collector = EnhancedInventoryCollector(profile=profile)

        # Get account ID for current profile (required for collect_inventory API)
        session = boto3.Session(profile_name=profile)
        sts = session.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        if verbose:
            print_info(f"Using account ID: {account_id}")
            print_info(f"Region: {session.region_name}")

        # Discover resources using existing collector methods
        # Note: The collector returns dictionaries, we need to extract DataFrames
        resources = {}

        # EC2 collection
        if verbose:
            print_info("Collecting EC2 instances...")
        try:
            ec2_result = collector.collect_inventory(account_ids=[account_id], resource_types=["ec2"])
            # Collector returns: {'resources': {'ec2': {account_id: {'instances': [...], 'count': N}}}}
            if ec2_result and "resources" in ec2_result and "ec2" in ec2_result["resources"]:
                ec2_by_account = ec2_result["resources"]["ec2"]
                if account_id in ec2_by_account:
                    ec2_account_data = ec2_by_account[account_id]
                    if isinstance(ec2_account_data, dict) and "instances" in ec2_account_data:
                        instances = ec2_account_data["instances"]
                        if instances:
                            resources["ec2"] = pd.DataFrame(instances)
                            if verbose:
                                print_success(f"EC2: {len(resources['ec2'])} instances found")
        except Exception as e:
            if verbose:
                print_warning(f"EC2 collection failed: {str(e)}")

        # RDS collection
        if verbose:
            print_info("Collecting RDS instances...")
        try:
            rds_result = collector.collect_inventory(account_ids=[account_id], resource_types=["rds"])
            if rds_result and "resources" in rds_result and "rds" in rds_result["resources"]:
                rds_by_account = rds_result["resources"]["rds"]
                if account_id in rds_by_account:
                    rds_account_data = rds_by_account[account_id]
                    if isinstance(rds_account_data, dict) and "instances" in rds_account_data:
                        instances = rds_account_data["instances"]
                        if instances:
                            resources["rds"] = pd.DataFrame(instances)
                            if verbose:
                                print_success(f"RDS: {len(resources['rds'])} instances found")
        except Exception as e:
            if verbose:
                print_warning(f"RDS collection failed: {str(e)}")

        # WorkSpaces collection
        if verbose:
            print_info("Collecting WorkSpaces...")
        try:
            workspaces_result = collector.collect_inventory(account_ids=[account_id], resource_types=["workspaces"])
            if (
                workspaces_result
                and "resources" in workspaces_result
                and "workspaces" in workspaces_result["resources"]
            ):
                ws_by_account = workspaces_result["resources"]["workspaces"]
                if account_id in ws_by_account:
                    ws_account_data = ws_by_account[account_id]
                    if isinstance(ws_account_data, dict) and "workspaces" in ws_account_data:
                        workspaces = ws_account_data["workspaces"]
                        if workspaces:
                            resources["workspaces"] = pd.DataFrame(workspaces)
                            if verbose:
                                print_success(f"WorkSpaces: {len(resources['workspaces'])} instances found")
        except Exception as e:
            if verbose:
                print_warning(f"WorkSpaces collection failed: {str(e)}")

        # Snapshots collection
        if verbose:
            print_info("Collecting EBS snapshots...")
        try:
            snapshots_result = collector.collect_inventory(account_ids=[account_id], resource_types=["ebs_snapshots"])
            if (
                snapshots_result
                and "resources" in snapshots_result
                and "ebs_snapshots" in snapshots_result["resources"]
            ):
                snap_by_account = snapshots_result["resources"]["ebs_snapshots"]
                if account_id in snap_by_account:
                    snap_account_data = snap_by_account[account_id]
                    if isinstance(snap_account_data, dict) and "snapshots" in snap_account_data:
                        snapshots = snap_account_data["snapshots"]
                        if snapshots:
                            resources["snapshots"] = pd.DataFrame(snapshots)
                            if verbose:
                                print_success(f"Snapshots: {len(resources['snapshots'])} snapshots found")
        except Exception as e:
            if verbose:
                print_warning(f"Snapshots collection failed: {str(e)}")

        # S3 collection
        if verbose:
            print_info("Collecting S3 buckets...")
        try:
            s3_result = collector.collect_inventory(account_ids=[account_id], resource_types=["s3"])
            if s3_result and "resources" in s3_result and "s3" in s3_result["resources"]:
                s3_by_account = s3_result["resources"]["s3"]
                if account_id in s3_by_account:
                    s3_account_data = s3_by_account[account_id]
                    if isinstance(s3_account_data, dict) and "buckets" in s3_account_data:
                        buckets = s3_account_data["buckets"]
                        if buckets:
                            resources["s3"] = pd.DataFrame(buckets)
                            if verbose:
                                print_success(f"S3: {len(resources['s3'])} buckets found")
        except Exception as e:
            if verbose:
                print_warning(f"S3 collection failed: {str(e)}")

        # DynamoDB collection
        if verbose:
            print_info("Collecting DynamoDB tables...")
        try:
            dynamodb_result = collector.collect_inventory(account_ids=[account_id], resource_types=["dynamodb"])
            if dynamodb_result and "resources" in dynamodb_result and "dynamodb" in dynamodb_result["resources"]:
                ddb_by_account = dynamodb_result["resources"]["dynamodb"]
                if account_id in ddb_by_account:
                    ddb_account_data = ddb_by_account[account_id]
                    if isinstance(ddb_account_data, dict) and "tables" in ddb_account_data:
                        tables = ddb_account_data["tables"]
                        if tables:
                            resources["dynamodb"] = pd.DataFrame(tables)
                            if verbose:
                                print_success(f"DynamoDB: {len(resources['dynamodb'])} tables found")
        except Exception as e:
            if verbose:
                print_warning(f"DynamoDB collection failed: {str(e)}")

        # Remove None/empty results (only return resources with data)
        filtered_resources = {service: df for service, df in resources.items() if df is not None and not df.empty}

        print_success(
            f"Discovery complete: {len(filtered_resources)} services with resources "
            f"({sum(len(df) for df in filtered_resources.values())} total resources)"
        )

        return filtered_resources

    except Exception as e:
        print_error(f"Resource discovery failed: {str(e)}")
        console.print_exception()
        return {}


def enrich_with_activity(
    resources: Dict[str, pd.DataFrame], profile: Optional[str] = None, verbose: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Single-function enrichment - adds activity signals to discovered resources.

    Adds service-specific activity signals:
    - EC2: E1-E7 signals (Compute Optimizer, CloudWatch, CloudTrail, SSM, etc.)
    - RDS: R1-R7 signals (database activity, connections, performance)
    - WorkSpaces: W1-W6 signals (connection history, usage patterns)
    - Snapshots: Snapshot-specific activity signals

    Args:
        resources: Dictionary of service DataFrames from discover_all_resources()
        profile: AWS profile name (defaults to AWS_PROFILE env var or 'default')

    Returns:
        Dict with enriched DataFrames (original + activity columns)

    Note:
        Services without enrichment support are passed through unchanged.
        Enrichment failures for individual services are logged but don't block processing.
    """
    # Use profile_utils for consistent profile resolution (v1.1.28 Phase 2.3)
    from runbooks.common.profile_utils import get_profile_for_operation

    profile = get_profile_for_operation(operation_type="operational", user_specified_profile=profile, silent=False)

    print_info(f"Enriching resources with activity signals using profile: {profile}")

    try:
        # Initialize enricher with operational profile
        enricher = DashboardActivityEnricher(operational_profile=profile)

        enriched = {}

        # Enrich EC2 instances with E1-E7 signals
        if "ec2" in resources and not resources["ec2"].empty:
            print_info("Enriching EC2 instances with E1-E7 activity signals...")
            try:
                enriched["ec2"] = enricher.enrich_ec2_activity(resources["ec2"])
                print_success(f"EC2 enrichment complete: {len(enriched['ec2'])} instances")
            except Exception as e:
                print_warning(f"EC2 enrichment failed: {str(e)}")
                enriched["ec2"] = resources["ec2"]  # Pass through without enrichment

        # Enrich RDS instances with R1-R7 signals
        if "rds" in resources and not resources["rds"].empty:
            print_info("Enriching RDS instances with R1-R7 activity signals...")
            try:
                enriched["rds"] = enricher.enrich_rds_activity(resources["rds"])
                print_success(f"RDS enrichment complete: {len(enriched['rds'])} instances")
            except Exception as e:
                print_warning(f"RDS enrichment failed: {str(e)}")
                enriched["rds"] = resources["rds"]  # Pass through without enrichment

        # Enrich WorkSpaces with W1-W6 signals
        if "workspaces" in resources and not resources["workspaces"].empty:
            print_info("Enriching WorkSpaces with W1-W6 activity signals...")
            try:
                enriched["workspaces"] = enricher.enrich_workspaces_activity(resources["workspaces"])
                print_success(f"WorkSpaces enrichment complete: {len(enriched['workspaces'])} workspaces")
            except Exception as e:
                print_warning(f"WorkSpaces enrichment failed: {str(e)}")
                enriched["workspaces"] = resources["workspaces"]  # Pass through

        # Enrich snapshots
        if "snapshots" in resources and not resources["snapshots"].empty:
            print_info("Enriching EBS snapshots with activity signals...")
            try:
                enriched["snapshots"] = enricher.enrich_snapshot_activity(resources["snapshots"])
                print_success(f"Snapshot enrichment complete: {len(enriched['snapshots'])} snapshots")
            except Exception as e:
                print_warning(f"Snapshot enrichment failed: {str(e)}")
                enriched["snapshots"] = resources["snapshots"]  # Pass through

        # Pass through services without enrichment support
        for service in ["s3", "dynamodb"]:
            if service in resources and not resources[service].empty:
                enriched[service] = resources[service]
                print_info(f"{service.upper()}: No enrichment configured (pass-through)")

        print_success(f"Activity enrichment complete: {len(enriched)} services enriched")

        return enriched

    except Exception as e:
        print_error(f"Activity enrichment failed: {str(e)}")
        console.print_exception()
        # Return original resources unchanged on enrichment failure
        return resources


def score_decommission_candidates(enriched: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Single-function scoring - adds decommission_score and decommission_tier columns.

    Calculates decommission priority based on activity signals:
    - MUST (80-100 points): Immediate candidates (high confidence)
    - SHOULD (50-79 points): Strong candidates (review recommended)
    - COULD (25-49 points): Potential candidates (manual review required)
    - KEEP (<25 points): Active resources (no action)

    Args:
        enriched: Dictionary of enriched DataFrames from enrich_with_activity()

    Returns:
        Dict with scored DataFrames (original + decommission_score + decommission_tier)

    Note:
        Only EC2, RDS, and WorkSpaces support scoring (other services pass through).
        Scoring failures for individual services are logged but don't block processing.
    """
    print_info("Scoring decommission candidates...")

    try:
        # No scorer initialization needed - using DataFrame functions directly

        scored = {}

        # Score EC2 instances (E1-E7 signals → 0-100 score)
        if "ec2" in enriched and not enriched["ec2"].empty:
            print_info("Scoring EC2 instances for decommission priority...")
            try:
                scored["ec2"] = score_ec2_dataframe(enriched["ec2"])

                # Calculate tier distribution
                tier_counts = scored["ec2"]["decommission_tier"].value_counts().to_dict()
                print_success(
                    f"EC2 scoring complete: {len(scored['ec2'])} instances scored "
                    f"(MUST: {tier_counts.get('MUST', 0)}, "
                    f"SHOULD: {tier_counts.get('SHOULD', 0)}, "
                    f"COULD: {tier_counts.get('COULD', 0)}, "
                    f"KEEP: {tier_counts.get('KEEP', 0)})"
                )
            except Exception as e:
                print_warning(f"EC2 scoring failed: {str(e)}")
                scored["ec2"] = enriched["ec2"]  # Pass through without scoring

        # Score RDS instances (R1-R7 signals → 0-100 score)
        if "rds" in enriched and not enriched["rds"].empty:
            # RDS DataFrame scoring function not yet implemented, pass through
            print_info("RDS: DataFrame scoring not yet implemented (pass-through)")
            scored["rds"] = enriched["rds"]

        # Score WorkSpaces (W1-W6 signals → 0-100 score)
        if "workspaces" in enriched and not enriched["workspaces"].empty:
            print_info("Scoring WorkSpaces for decommission priority...")
            try:
                scored["workspaces"] = score_workspaces_dataframe(enriched["workspaces"])

                tier_counts = scored["workspaces"]["decommission_tier"].value_counts().to_dict()
                print_success(
                    f"WorkSpaces scoring complete: {len(scored['workspaces'])} workspaces scored "
                    f"(MUST: {tier_counts.get('MUST', 0)}, "
                    f"SHOULD: {tier_counts.get('SHOULD', 0)}, "
                    f"COULD: {tier_counts.get('COULD', 0)}, "
                    f"KEEP: {tier_counts.get('KEEP', 0)})"
                )
            except Exception as e:
                print_warning(f"WorkSpaces scoring failed: {str(e)}")
                scored["workspaces"] = enriched["workspaces"]  # Pass through

        # Pass through services without scoring support
        for service in ["snapshots", "s3", "dynamodb"]:
            if service in enriched and not enriched[service].empty:
                scored[service] = enriched[service]
                print_info(f"{service.upper()}: No scoring configured (pass-through)")

        print_success(f"Decommission scoring complete: {len(scored)} services processed")

        return scored

    except Exception as e:
        print_error(f"Decommission scoring failed: {str(e)}")
        console.print_exception()
        # Return enriched resources unchanged on scoring failure
        return enriched
