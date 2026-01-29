#!/usr/bin/env python3
"""
CloudTrail Activity Analysis Pattern - Resource Usage Intelligence

Base class for analyzing resource activity via AWS CloudTrail event history.

Design Pattern:
    - Abstract base class requiring _get_resources_for_activity_analysis() implementation
    - Provides last access timestamp and access count aggregation
    - 90-day lookback window (CloudTrail event history retention)
    - Idle classification (>30 days = idle) for cleanup prioritization
    - Batch queries with Rich progress bar for performance

Reusability:
    - VPCE Cleanup Manager (current implementation)
    - VPC Cleanup (future enhancement)
    - ENI Cleanup (future enhancement)
    - Resource usage analysis across all modules

Usage:
    class MyManager(CloudTrailActivityAnalyzer):
        def _get_resources_for_activity_analysis(self):
            return self.endpoints  # List[VPCEndpoint]

    manager = MyManager()
    result = manager.analyze_cloudtrail_activity(
        lookback_days=90,
        idle_threshold_days=30
    )
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from runbooks.common.rich_utils import (
    console,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)


@dataclass
class ActivityAnalysisResult:
    """Result from CloudTrail activity analysis operation."""

    total_resources: int
    resources_analyzed: int
    active_resources: int  # Accessed within idle_threshold_days
    idle_resources: int  # Not accessed for >idle_threshold_days
    last_access_timestamps: Dict[str, Optional[datetime]] = field(default_factory=dict)  # resource_id → last access
    access_counts: Dict[str, int] = field(default_factory=dict)  # resource_id → count
    idle_classifications: Dict[str, bool] = field(default_factory=dict)  # resource_id → is_idle
    errors: List[str] = field(default_factory=list)  # Error messages


class CloudTrailActivityAnalyzer(ABC):
    """
    Base class for CloudTrail activity analysis operations.

    Provides reusable methods for:
    - Querying CloudTrail event history (90-day retention)
    - Extracting last access timestamps for resources
    - Calculating access counts and idle durations
    - Batch processing with Rich CLI progress bars
    - Graceful fallback if CloudTrail unavailable

    Subclass Requirements:
        - Implement _get_resources_for_activity_analysis() → List[Resource]
        - Resource must have: id (str), profile (str), region (str)

    Performance Optimization:
        - Batch queries (10 resources per API call)
        - Progress bar feedback for long-running operations
        - Error isolation (per-resource failures don't block batch)

    Limitations:
        - CloudTrail event history: 90-day retention
        - API rate limits: 2 requests/second (managed via batching)
    """

    @abstractmethod
    def _get_resources_for_activity_analysis(self) -> List:
        """
        Return resources for CloudTrail activity analysis.

        Returns:
            List[Resource] where Resource has:
                - id: str (resource identifier, e.g., 'vpce-xxx')
                - profile: str (AWS profile name)
                - region: str (AWS region)
                - Additional resource-specific fields
        """
        pass

    def analyze_cloudtrail_activity(
        self,
        lookback_days: int = 90,
        idle_threshold_days: int = 30,
        batch_size: int = 10,
        management_profile: Optional[str] = None,
        top_n: int = 50,
    ) -> ActivityAnalysisResult:
        """
        Analyze resource activity via CloudTrail event history.

        Args:
            lookback_days: Days to look back in CloudTrail (max: 90)
            idle_threshold_days: Days since last access to classify as idle
            batch_size: Resources per CloudTrail API call (default: 10)
            top_n: Number of resources to display in table (default: 50)
            management_profile: AWS profile for CloudTrail access
                              Priority: param > $MANAGEMENT_PROFILE > $AWS_PROFILE > error

        Returns:
            ActivityAnalysisResult with activity statistics

        Example:
            >>> result = manager.analyze_cloudtrail_activity(management_profile="mgmt")
            >>> # ✅ Analyzed 88 resources: 45 active, 43 idle (>30 days)
            >>> # Idle resources: vpce-123 (67 days), vpce-456 (89 days), ...
        """
        # Priority cascade: param > MANAGEMENT_PROFILE > AWS_PROFILE > error
        profile_source = "parameter"
        if management_profile is None:
            management_profile = os.getenv("MANAGEMENT_PROFILE")
            if management_profile:
                profile_source = "MANAGEMENT_PROFILE env"
            else:
                management_profile = os.getenv("AWS_PROFILE")
                if management_profile:
                    profile_source = "AWS_PROFILE env"
                else:
                    raise ValueError(
                        "CloudTrail analysis requires management_profile parameter "
                        "or $MANAGEMENT_PROFILE environment variable"
                    )

        print_info(f"🔍 CloudTrail profile: {management_profile} (source: {profile_source})")

        resources = self._get_resources_for_activity_analysis()

        if not resources:
            print_warning("⚠️  No resources to analyze (empty resource list)")
            return ActivityAnalysisResult(
                total_resources=0,
                resources_analyzed=0,
                active_resources=0,
                idle_resources=0,
            )

        # Validate lookback window
        if lookback_days > 90:
            print_warning(f"⚠️  Lookback window {lookback_days} days exceeds CloudTrail retention (90 days)")
            lookback_days = 90

        print_info(
            f"🔍 Analyzing CloudTrail activity for {len(resources)} resources "
            f"({lookback_days}-day lookback, {idle_threshold_days}-day idle threshold)..."
        )

        # Initialize result containers
        last_access_timestamps = {}
        access_counts = {}
        idle_classifications = {}
        errors = []
        successfully_analyzed_ids = set()  # Track which resources were successfully analyzed

        # Calculate time window
        end_time = datetime.now()
        start_time = end_time - timedelta(days=lookback_days)

        # Group resources by profile for batch processing
        resources_by_profile: Dict[str, List] = {}
        for resource in resources:
            profile = getattr(resource, "profile", None)
            if not profile:
                errors.append(f"Resource {getattr(resource, 'id', 'unknown')} missing profile attribute")
                continue

            if profile not in resources_by_profile:
                resources_by_profile[profile] = []

            resources_by_profile[profile].append(resource)

        # Process resources with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing CloudTrail events...", total=len(resources))

            for profile, profile_resources in resources_by_profile.items():
                try:
                    session = boto3.Session(profile_name=profile)

                    # Extract region and validate (empty string causes invalid endpoint)
                    region = getattr(profile_resources[0], "region", None)
                    if not region or not region.strip():
                        region = "ap-southeast-2"  # Fallback to default

                    cloudtrail_client = session.client(
                        "cloudtrail",
                        region_name=region,
                    )

                    # Process resources in batches
                    for i in range(0, len(profile_resources), batch_size):
                        batch = profile_resources[i : i + batch_size]

                        for resource in batch:
                            resource_id = getattr(resource, "id", None)
                            if not resource_id:
                                errors.append("Resource missing id attribute")
                                progress.update(task, advance=1)
                                continue

                            try:
                                # Query CloudTrail for resource-specific events
                                events = self._query_cloudtrail_events(
                                    cloudtrail_client,
                                    resource_id,
                                    start_time,
                                    end_time,
                                )

                                if events:
                                    # Extract last access timestamp
                                    last_access = max(event["EventTime"] for event in events)
                                    last_access_timestamps[resource_id] = last_access
                                    access_counts[resource_id] = len(events)

                                    # Calculate idle classification
                                    days_since_access = (datetime.now(last_access.tzinfo) - last_access).days
                                    idle_classifications[resource_id] = days_since_access > idle_threshold_days
                                else:
                                    # No activity in lookback window
                                    last_access_timestamps[resource_id] = None
                                    access_counts[resource_id] = 0
                                    idle_classifications[resource_id] = True  # Idle

                                successfully_analyzed_ids.add(resource_id)  # Track successful analysis

                            except ClientError as e:
                                error_code = e.response["Error"]["Code"]
                                errors.append(f"CloudTrail query failed for {resource_id}: {error_code}")
                                last_access_timestamps[resource_id] = None
                                access_counts[resource_id] = 0
                                idle_classifications[resource_id] = True  # Assume idle on error
                                # Do NOT increment successfully_analyzed for errors

                            except Exception as e:
                                errors.append(f"Unexpected error analyzing {resource_id}: {str(e)}")
                                last_access_timestamps[resource_id] = None
                                access_counts[resource_id] = 0
                                idle_classifications[resource_id] = True  # Assume idle on error
                                # Do NOT increment successfully_analyzed for errors

                            progress.update(task, advance=1)

                except ClientError as e:
                    error_code = e.response["Error"]["Code"]
                    if error_code == "AccessDeniedException":
                        print_error(f"❌ Access denied to CloudTrail API (profile: {profile})")
                        print_warning("⚠️  Ensure profile has cloudtrail:LookupEvents permission")
                    else:
                        print_error(f"❌ CloudTrail API error (profile: {profile}): {error_code}")

                    # Mark all resources in this profile as idle (fallback)
                    # Do NOT increment successfully_analyzed - these are API failures
                    for resource in profile_resources:
                        resource_id = getattr(resource, "id", "unknown")
                        last_access_timestamps[resource_id] = None
                        access_counts[resource_id] = 0
                        idle_classifications[resource_id] = True
                        progress.update(task, advance=1)

                    errors.append(f"Profile {profile} CloudTrail access failed: {error_code}")

                except Exception as e:
                    print_error(f"❌ Unexpected error (profile: {profile}): {str(e)}")

                    # Mark all resources in this profile as idle (fallback)
                    # Do NOT increment successfully_analyzed - these are failures
                    for resource in profile_resources:
                        resource_id = getattr(resource, "id", "unknown")
                        last_access_timestamps[resource_id] = None
                        access_counts[resource_id] = 0
                        idle_classifications[resource_id] = True
                        progress.update(task, advance=1)

                    errors.append(f"Profile {profile} unexpected error: {str(e)}")

        # Calculate summary statistics
        # Only count successfully analyzed resources (not fallback entries from failures)
        resources_analyzed = len(successfully_analyzed_ids)

        # Only count idle/active from successfully analyzed resources
        idle_resources = sum(
            1
            for resource_id, is_idle in idle_classifications.items()
            if resource_id in successfully_analyzed_ids and is_idle
        )
        active_resources = resources_analyzed - idle_resources

        # Consolidate activity status into single line with optional error note
        error_note = f" ({len(errors)} error{'s' if len(errors) != 1 else ''} non-blocking)" if errors else ""
        print_success(f"Activity: {active_resources} ACTIVE, {idle_resources} IDLE{error_note}")

        # Display Rich table with activity details (Manager requirement: show days idle)
        if resources_analyzed > 0:
            self._display_activity_table(
                resources,
                last_access_timestamps,
                access_counts,
                idle_classifications,
                idle_threshold_days,
                lookback_days,
                top_n,
            )

        return ActivityAnalysisResult(
            total_resources=len(resources),
            resources_analyzed=resources_analyzed,
            active_resources=active_resources,
            idle_resources=idle_resources,
            last_access_timestamps=last_access_timestamps,
            access_counts=access_counts,
            idle_classifications=idle_classifications,
            errors=errors,
        )

    def _query_cloudtrail_events(
        self,
        cloudtrail_client,
        resource_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[Dict]:
        """
        Query CloudTrail events for specific resource.

        Args:
            cloudtrail_client: Boto3 CloudTrail client
            resource_id: Resource identifier (e.g., 'vpce-xxx')
            start_time: Query start time
            end_time: Query end time

        Returns:
            List of CloudTrail events matching resource

        Raises:
            ClientError: If CloudTrail API call fails (to be handled by caller)
        """
        events = []

        # Query CloudTrail with resource name filter
        response = cloudtrail_client.lookup_events(
            LookupAttributes=[
                {
                    "AttributeKey": "ResourceName",
                    "AttributeValue": resource_id,
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50,  # CloudTrail API limit
        )

        events.extend(response.get("Events", []))

        # Handle pagination if needed
        while "NextToken" in response:
            response = cloudtrail_client.lookup_events(
                LookupAttributes=[
                    {
                        "AttributeKey": "ResourceName",
                        "AttributeValue": resource_id,
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                NextToken=response["NextToken"],
                MaxResults=50,
            )
            events.extend(response.get("Events", []))

        return events

    def _display_activity_table(
        self,
        resources: List,
        last_access_timestamps: Dict[str, Optional[datetime]],
        access_counts: Dict[str, int],
        idle_classifications: Dict[str, bool],
        idle_threshold_days: int,
        lookback_days: int,
        top_n: int = 50,
    ) -> None:
        """
        Display Rich table with CloudTrail activity analysis.

        Manager feedback: "show how many days - idle for each VPCE"
        Finops parity: Rich PyPI table by default (matches elastic_ip_optimizer.py pattern)

        Args:
            resources: List of resources analyzed
            last_access_timestamps: Resource ID → last access datetime
            access_counts: Resource ID → access count
            idle_classifications: Resource ID → is_idle
            idle_threshold_days: Idle threshold (default: 30 days)
            lookback_days: Analysis window (default: 90 days)
            top_n: Show top N idle resources (default: 50)
        """
        table = create_table(
            title=f"CloudTrail Activity Analysis ({lookback_days}-day lookback, {idle_threshold_days}-day idle threshold)"
        )
        table.add_column("Resource ID", style="cyan", no_wrap=True)
        table.add_column("Last Access", style="green")
        table.add_column("Days Idle", style="yellow", justify="right")
        table.add_column("Access Count (90d)", style="blue", justify="right")
        table.add_column("Status", style="magenta", justify="center")
        table.add_column("Profile", style="dim")
        table.add_column("Region", style="dim")

        # Prepare resource data for sorting
        resource_data = []
        for resource in resources:
            resource_id = getattr(resource, "id", "unknown")
            last_access = last_access_timestamps.get(resource_id)
            access_count = access_counts.get(resource_id, 0)
            is_idle = idle_classifications.get(resource_id, True)

            # Calculate days idle
            if last_access:
                days_idle = (datetime.now(last_access.tzinfo) - last_access).days
            else:
                days_idle = lookback_days  # Never accessed in lookback window

            resource_data.append(
                {
                    "id": resource_id,
                    "last_access": last_access,
                    "days_idle": days_idle,
                    "access_count": access_count,
                    "is_idle": is_idle,
                    "profile": getattr(resource, "profile", "N/A"),
                    "region": getattr(resource, "region", "N/A"),
                }
            )

        # Sort by days idle (descending) - most idle first
        sorted_resources = sorted(resource_data, key=lambda x: x["days_idle"], reverse=True)

        # Show top N idle resources
        for resource in sorted_resources[:top_n]:
            # Status indicator with highlighting (Manager requirement: highlight active resources)
            if resource["is_idle"]:
                status = "[red]🔴 IDLE[/red]"
                # Manager feedback #2: Show "Never (>90d)" for resources with NO CloudTrail events
                if resource["days_idle"] == lookback_days and resource["access_count"] == 0:
                    days_idle_display = f"[red bold]Never (>{lookback_days}d)[/red bold]"  # Zero CloudTrail events
                else:
                    days_idle_display = f"[red bold]{resource['days_idle']}[/red bold]"  # Actual idle days
            else:
                status = "[green bold]🟢 ACTIVE[/green bold]"  # Highlight active!
                days_idle_display = f"[green]{resource['days_idle']}[/green]"  # Active resources in green

            # Format last access
            if resource["last_access"]:
                last_access_str = resource["last_access"].strftime("%Y-%m-%d")
            else:
                last_access_str = "Never"

            table.add_row(
                resource["id"],
                last_access_str,
                days_idle_display,  # Use highlighted value
                str(resource["access_count"]),
                status,
                resource["profile"],
                resource["region"],
            )

        console.print(table)

        # Summary footer with enhanced explanations
        active_count = sum(1 for r in resource_data if not r["is_idle"])
        idle_count = sum(1 for r in resource_data if r["is_idle"])

        print_info(
            f"📊 Summary: {active_count} active, {idle_count} idle "
            f"(>{idle_threshold_days} days since last CloudTrail event) | "
            f"Table shows top {min(top_n, len(sorted_resources))} MOST IDLE resources "
            f"(sorted by days idle descending for cleanup prioritization)"
        )

        # Manager feedback #2: Explain "Never (>90d)" display
        print_info(f"💡 'Never (>{lookback_days}d)' = No CloudTrail events in {lookback_days}-day lookback window")

        # Manager requirement: Explain "WHY ONLY 50?"
        if len(sorted_resources) > top_n:
            print_info(
                f"💡 Showing top {top_n} for focus on highest cleanup priority. "
                f"Total analyzed: {len(sorted_resources)} resources."
            )

        # Manager requirement: Highlight active count (helpful for cleanup decisions)
        if active_count > 0:
            print_success(f"✅ {active_count} ACTIVE resource{'s' if active_count != 1 else ''} found (keep these!)")
        if idle_count > 0:
            print_warning(f"⚠️  {idle_count} IDLE resource{'s' if idle_count != 1 else ''} (cleanup candidates)")
