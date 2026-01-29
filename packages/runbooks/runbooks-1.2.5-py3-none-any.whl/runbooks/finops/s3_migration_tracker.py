#!/usr/bin/env python3
"""
S3 Migration Tracker - Lifecycle Migration Verification via CloudTrail
======================================================================

Business Value: Audit trail for lifecycle migration claims with compliance evidence
Strategic Impact: Validates "migration to Glacier/Deep Archive complete" claims

Architecture Pattern: CloudTrail-based policy change tracking
- Query CloudTrail for PutBucketLifecycleConfiguration events
- Identify when lifecycle policies were created/modified
- Extract policy change details (before/after transitions)
- Validate migration timeline claims
- Generate audit trail for compliance

CloudTrail Event Types Tracked:
- PutBucketLifecycleConfiguration: Lifecycle policy creation/modification
- DeleteBucketLifecycleConfiguration: Lifecycle policy removal
- PutBucketVersioning: Versioning configuration changes
- PutBucketEncryption: Encryption configuration changes

Usage:
    from runbooks.finops.s3_migration_tracker import S3MigrationTracker

    tracker = S3MigrationTracker(boto_session, region='ap-southeast-2')
    verification = tracker.verify_migration_claim(
        bucket_name='vamsnz-prod-atlassian-backups',
        claimed_migration_date='2025-04-01'
    )

    if verification.migration_verified:
        print(f"✓ Migration verified: {verification.actual_date}")
        print(f"Policy changes: {verification.policy_changes}")
    else:
        print(f"✗ Migration claim unverified: {verification.discrepancy}")

Integration:
    Used by finops validate command for migration claim verification and audit trails

Author: Runbooks Team
Version: 1.1.27
Track: Phase 4.4 - Migration Tracker
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from runbooks.common.rich_utils import (
    console,
    create_table,
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═════════════════════════════════════════════════════════════════════════════


@dataclass
class PolicyChange:
    """CloudTrail event representing lifecycle policy change."""

    event_time: str
    event_name: str
    user_identity: str
    source_ip: str
    request_id: str

    # Policy details
    bucket_name: str
    transitions_added: List[str] = field(default_factory=list)
    transitions_removed: List[str] = field(default_factory=list)
    expirations_added: List[str] = field(default_factory=list)
    expirations_removed: List[str] = field(default_factory=list)

    # Raw event
    raw_event: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MigrationVerification:
    """Migration claim verification result."""

    bucket_name: str
    region: str

    # Claim details
    claimed_migration_date: Optional[str]
    claimed_storage_class: Optional[str]

    # Verification results
    migration_verified: bool
    actual_migration_date: Optional[str] = None
    policy_changes: List[PolicyChange] = field(default_factory=list)

    # Evidence
    cloudtrail_events_found: int = 0
    first_lifecycle_event: Optional[str] = None
    last_lifecycle_event: Optional[str] = None

    # Discrepancy analysis
    discrepancy: Optional[str] = None
    confidence: str = "UNKNOWN"  # HIGH, MEDIUM, LOW, UNKNOWN

    # Metadata
    verification_timestamp: str = field(default_factory=lambda: datetime.now(tz=timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "bucket_name": self.bucket_name,
            "region": self.region,
            "claimed_migration_date": self.claimed_migration_date,
            "claimed_storage_class": self.claimed_storage_class,
            "migration_verified": self.migration_verified,
            "actual_migration_date": self.actual_migration_date,
            "policy_changes": [
                {
                    "event_time": pc.event_time,
                    "event_name": pc.event_name,
                    "user_identity": pc.user_identity,
                    "transitions_added": pc.transitions_added,
                    "transitions_removed": pc.transitions_removed,
                    "expirations_added": pc.expirations_added,
                    "expirations_removed": pc.expirations_removed,
                }
                for pc in self.policy_changes
            ],
            "cloudtrail_events_found": self.cloudtrail_events_found,
            "first_lifecycle_event": self.first_lifecycle_event,
            "last_lifecycle_event": self.last_lifecycle_event,
            "discrepancy": self.discrepancy,
            "confidence": self.confidence,
            "verification_timestamp": self.verification_timestamp,
        }


# ═════════════════════════════════════════════════════════════════════════════
# CORE TRACKER CLASS
# ═════════════════════════════════════════════════════════════════════════════


class S3MigrationTracker:
    """
    S3 migration tracker for lifecycle migration verification.

    Provides CloudTrail-based audit trail for lifecycle policy changes, enabling
    verification of migration claims and compliance reporting.

    Capabilities:
    - Query CloudTrail for PutBucketLifecycleConfiguration events
    - Identify when lifecycle policies were created/modified
    - Extract policy change details (before/after transitions)
    - Validate migration timeline claims
    - Generate compliance audit trail

    Example:
        >>> tracker = S3MigrationTracker(session)
        >>> verification = tracker.verify_migration_claim('my-bucket', '2025-04-01')
        >>> if verification.migration_verified:
        ...     print(f"Migration confirmed: {verification.actual_migration_date}")
    """

    # CloudTrail event names to track
    LIFECYCLE_EVENT_NAMES = [
        "PutBucketLifecycleConfiguration",
        "DeleteBucketLifecycleConfiguration",
    ]

    # Lookback period for CloudTrail queries (90 days max for free trail)
    DEFAULT_LOOKBACK_DAYS = 90

    def __init__(
        self, session: boto3.Session, region: str = "ap-southeast-2", cloudtrail_region: str = "ap-southeast-2"
    ):
        """
        Initialize S3 migration tracker.

        Args:
            session: Boto3 session with CloudTrail permissions
            region: AWS region for S3 operations
            cloudtrail_region: AWS region for CloudTrail queries (where trail is configured)
        """
        self.session = session
        self.region = region
        self.cloudtrail_region = cloudtrail_region
        self.s3_client = session.client("s3", region_name=region)
        self.cloudtrail_client = session.client("cloudtrail", region_name=cloudtrail_region)
        self.logger = logging.getLogger(__name__)

    def verify_migration_claim(
        self,
        bucket_name: str,
        claimed_migration_date: Optional[str] = None,
        claimed_storage_class: Optional[str] = None,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    ) -> MigrationVerification:
        """
        Verify migration claim via CloudTrail audit trail.

        Workflow:
        1. Query CloudTrail for lifecycle policy change events
        2. Extract policy change details (transitions, expirations)
        3. Identify when migration-related transitions were configured
        4. Compare actual migration date with claimed date
        5. Generate verification result with confidence level

        Args:
            bucket_name: S3 bucket name
            claimed_migration_date: Claimed migration completion date (YYYY-MM-DD)
            claimed_storage_class: Claimed target storage class (Glacier, Deep Archive)
            lookback_days: CloudTrail lookback period (default: 90 days)

        Returns:
            Migration verification result with audit trail
        """
        print_section(f"Verifying Migration Claim: {bucket_name}")

        # Get CloudTrail events
        events = self._get_cloudtrail_events(bucket_name, lookback_days)

        if not events:
            print_warning("No CloudTrail lifecycle events found within lookback period")
            return self._create_no_evidence_verification(bucket_name, claimed_migration_date, claimed_storage_class)

        # Parse policy changes
        policy_changes = [self._parse_policy_change(event) for event in events]

        # Analyze migration timeline
        first_event = policy_changes[0].event_time if policy_changes else None
        last_event = policy_changes[-1].event_time if policy_changes else None

        # Determine actual migration date (when lifecycle transitions were configured)
        actual_migration_date = self._determine_migration_date(policy_changes, claimed_storage_class)

        # Verify claim
        migration_verified, discrepancy, confidence = self._verify_claim(
            claimed_migration_date, actual_migration_date, policy_changes, claimed_storage_class
        )

        # Get bucket region
        try:
            bucket_region = self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        except Exception:
            bucket_region = self.region

        verification = MigrationVerification(
            bucket_name=bucket_name,
            region=bucket_region,
            claimed_migration_date=claimed_migration_date,
            claimed_storage_class=claimed_storage_class,
            migration_verified=migration_verified,
            actual_migration_date=actual_migration_date,
            policy_changes=policy_changes,
            cloudtrail_events_found=len(events),
            first_lifecycle_event=first_event,
            last_lifecycle_event=last_event,
            discrepancy=discrepancy,
            confidence=confidence,
        )

        # Display verification summary
        self._display_verification_summary(verification)

        return verification

    def _get_cloudtrail_events(
        self, bucket_name: str, lookback_days: int, event_names: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get CloudTrail events for bucket lifecycle changes.

        Args:
            bucket_name: S3 bucket name to filter events
            lookback_days: Number of days to look back
            event_names: List of CloudTrail event names to query (defaults to PutBucketLifecycleConfiguration only)
        """
        try:
            # Calculate time range
            end_time = datetime.now(tz=timezone.utc)
            start_time = end_time - timedelta(days=lookback_days)

            events = []

            # Default to only PutBucketLifecycleConfiguration for migration verification
            # (DeleteBucketLifecycleConfiguration would indicate removal, not migration)
            if event_names is None:
                event_names = ["PutBucketLifecycleConfiguration"]

            # Query CloudTrail for lifecycle events
            for event_name in event_names:
                try:
                    paginator = self.cloudtrail_client.get_paginator("lookup_events")
                    page_iterator = paginator.paginate(
                        LookupAttributes=[{"AttributeKey": "EventName", "AttributeValue": event_name}],
                        StartTime=start_time,
                        EndTime=end_time,
                    )

                    for page in page_iterator:
                        page_events = page.get("Events", [])

                        # Filter events for specific bucket
                        for event in page_events:
                            # Parse CloudTrail event JSON
                            import json

                            try:
                                event_json = json.loads(event.get("CloudTrailEvent", "{}"))
                                request_params = event_json.get("requestParameters", {})
                                bucket = request_params.get("bucketName", "")

                                if bucket == bucket_name:
                                    events.append(event)
                            except Exception as e:
                                self.logger.debug(f"Failed to parse CloudTrail event: {e}")
                                continue

                except ClientError as e:
                    self.logger.warning(f"CloudTrail query failed for {event_name}: {e}")
                    continue

            # Sort events by time (oldest first)
            events.sort(key=lambda e: e.get("EventTime", datetime.min))

            self.logger.info(f"Found {len(events)} CloudTrail lifecycle events for {bucket_name}")
            return events

        except Exception as e:
            self.logger.error(f"Failed to get CloudTrail events for {bucket_name}: {e}", exc_info=True)
            return []

    def _parse_policy_change(self, event: Dict) -> PolicyChange:
        """Parse CloudTrail event into PolicyChange object."""
        import json

        # Parse CloudTrail event JSON
        try:
            event_json = json.loads(event.get("CloudTrailEvent", "{}"))
        except Exception as e:
            self.logger.debug(f"Failed to parse CloudTrail event JSON: {e}")
            event_json = {}

        event_time = event.get("EventTime", datetime.now(tz=timezone.utc))
        if isinstance(event_time, datetime):
            event_time = event_time.isoformat()

        event_name = event.get("EventName", "Unknown")

        user_identity_data = event_json.get("userIdentity", {})
        user_identity = user_identity_data.get("principalId", "Unknown")

        source_ip = event_json.get("sourceIPAddress", "Unknown")
        request_id = event.get("EventId", "Unknown")

        request_params = event_json.get("requestParameters", {})
        bucket_name = request_params.get("bucketName", "Unknown")

        # Parse lifecycle configuration (if present)
        transitions_added = []
        expirations_added = []

        lifecycle_config = request_params.get("LifecycleConfiguration", {})
        rules = lifecycle_config.get("rules", [])

        for rule in rules:
            # Extract transitions
            for transition in rule.get("transitions", []):
                storage_class = transition.get("storageClass", "Unknown")
                days = transition.get("days", "Unknown")
                transitions_added.append(f"{storage_class} at {days} days")

            # Extract expirations
            expiration = rule.get("expiration", {})
            if expiration:
                days = expiration.get("days", "Unknown")
                expirations_added.append(f"Expiration at {days} days")

        return PolicyChange(
            event_time=event_time,
            event_name=event_name,
            user_identity=user_identity,
            source_ip=source_ip,
            request_id=request_id,
            bucket_name=bucket_name,
            transitions_added=transitions_added,
            transitions_removed=[],  # Would need before/after comparison
            expirations_added=expirations_added,
            expirations_removed=[],
            raw_event=event_json,
        )

    def _determine_migration_date(
        self, policy_changes: List[PolicyChange], claimed_storage_class: Optional[str]
    ) -> Optional[str]:
        """Determine actual migration date from policy changes."""
        if not policy_changes:
            return None

        # Find first event that added relevant storage class transition
        target_classes = ["GLACIER", "DEEP_ARCHIVE", "GLACIER_IR"]

        if claimed_storage_class:
            target_classes = [claimed_storage_class.upper()]

        for change in policy_changes:
            for transition in change.transitions_added:
                if any(tc in transition.upper() for tc in target_classes):
                    # Extract date from event time
                    event_dt = datetime.fromisoformat(change.event_time.replace("Z", "+00:00"))
                    return event_dt.strftime("%Y-%m-%d")

        # No relevant transitions found - use first event
        first_event_dt = datetime.fromisoformat(policy_changes[0].event_time.replace("Z", "+00:00"))
        return first_event_dt.strftime("%Y-%m-%d")

    def _verify_claim(
        self,
        claimed_date: Optional[str],
        actual_date: Optional[str],
        policy_changes: List[PolicyChange],
        claimed_storage_class: Optional[str],
    ) -> tuple[bool, Optional[str], str]:
        """
        Verify migration claim against CloudTrail evidence.

        Returns:
            Tuple of (verified, discrepancy, confidence)
        """
        if claimed_date is None:
            # No claim to verify
            return True, None, "UNKNOWN"

        if actual_date is None:
            # No evidence found
            return False, "No CloudTrail evidence of lifecycle configuration", "LOW"

        # Parse dates
        from datetime import datetime as dt

        claimed_dt = dt.strptime(claimed_date, "%Y-%m-%d")
        actual_dt = dt.strptime(actual_date, "%Y-%m-%d")

        # Calculate date difference
        date_diff = (actual_dt - claimed_dt).days

        # Verification logic
        if date_diff == 0:
            # Exact match
            return True, None, "HIGH"
        elif abs(date_diff) <= 7:
            # Within 1 week tolerance
            discrepancy = f"Date difference: {date_diff:+d} days (within tolerance)"
            return True, discrepancy, "MEDIUM"
        elif date_diff < 0:
            # Actual migration after claimed date
            discrepancy = f"Migration occurred {abs(date_diff)} days after claimed date"
            return False, discrepancy, "LOW"
        else:
            # Actual migration before claimed date
            discrepancy = f"Migration occurred {date_diff} days before claimed date"
            return True, discrepancy, "MEDIUM"

    def _create_no_evidence_verification(
        self, bucket_name: str, claimed_migration_date: Optional[str], claimed_storage_class: Optional[str]
    ) -> MigrationVerification:
        """Create verification result when no CloudTrail evidence found."""
        try:
            bucket_region = self.s3_client.get_bucket_location(Bucket=bucket_name)["LocationConstraint"] or "us-east-1"
        except Exception:
            bucket_region = self.region

        return MigrationVerification(
            bucket_name=bucket_name,
            region=bucket_region,
            claimed_migration_date=claimed_migration_date,
            claimed_storage_class=claimed_storage_class,
            migration_verified=False,
            cloudtrail_events_found=0,
            discrepancy="No CloudTrail events found within lookback period",
            confidence="UNKNOWN",
        )

    def _display_verification_summary(self, verification: MigrationVerification) -> None:
        """Display migration verification summary."""
        table = create_table(
            title=f"Migration Verification: {verification.bucket_name}",
            columns=[
                {"name": "Metric", "style": "cyan"},
                {"name": "Value", "style": "white"},
            ],
        )

        table.add_row("Claimed Migration Date", verification.claimed_migration_date or "N/A")
        table.add_row("Actual Migration Date", verification.actual_migration_date or "N/A")
        table.add_row("CloudTrail Events Found", str(verification.cloudtrail_events_found))

        if verification.first_lifecycle_event:
            table.add_row("First Lifecycle Event", verification.first_lifecycle_event)
        if verification.last_lifecycle_event:
            table.add_row("Last Lifecycle Event", verification.last_lifecycle_event)

        # Verification status
        status_color = "bright_green" if verification.migration_verified else "bright_red"
        status_text = "✓ VERIFIED" if verification.migration_verified else "✗ NOT VERIFIED"
        table.add_row("Verification Status", f"[{status_color}]{status_text}[/]")

        table.add_row("Confidence", verification.confidence)

        if verification.discrepancy:
            table.add_row("Discrepancy", f"[yellow]{verification.discrepancy}[/]")

        console.print()
        console.print(table)

        # Display policy changes
        if verification.policy_changes:
            print_section("Policy Changes")
            for i, change in enumerate(verification.policy_changes, 1):
                console.print(f"  {i}. {change.event_time} - {change.event_name}")
                if change.transitions_added:
                    console.print(f"     Transitions added: {', '.join(change.transitions_added)}")
                if change.expirations_added:
                    console.print(f"     Expirations added: {', '.join(change.expirations_added)}")

        # Display verification result
        if verification.migration_verified:
            print_success("✓ Migration claim verified via CloudTrail audit trail")
        else:
            print_error("✗ Migration claim could not be verified")

        console.print()


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT INTERFACE
# ═════════════════════════════════════════════════════════════════════════════


__all__ = [
    "S3MigrationTracker",
    "MigrationVerification",
    "PolicyChange",
]
