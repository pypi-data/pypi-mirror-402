#!/usr/bin/env python3
"""
ITSM Ticket Models - Pydantic validation for AWS and Azure tickets.

This module provides comprehensive Pydantic models for ITSM tickets with:
- Enums for ticket source, type, status, and priority
- BaseTicket model with computed fields and validation
- AWSTicket and AzureTicket specialized models
- TicketCollection for aggregate analytics

Production Usage:
    Handles 2,997 tickets (2,457 AWS + 540 Azure) with proper datetime parsing,
    SLA compliance calculation, and resolution time metrics.

Example:
    >>> from runbooks.itsm.models.ticket import AWSTicket
    >>> ticket = AWSTicket.from_dataframe_row({
    ...     'Issue key': 'AWS-00001',
    ...     'Issue Type': 'Incident',
    ...     'Status': 'Resolved',
    ...     'Priority': 'P2',
    ...     'Created': pd.Timestamp('2024-01-15 10:00:00'),
    ...     'Resolved': pd.Timestamp('2024-01-15 18:00:00'),
    ...     'Summary': 'EC2 instance down'
    ... })
    >>> ticket.resolution_hours
    8.0
    >>> ticket.calculate_sla_compliance(8)  # P2 target = 8 hours
    True
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, ClassVar
from pydantic import BaseModel, Field, field_validator, computed_field
import pandas as pd


# ============================================================================
# Enums - Ticket Classification
# ============================================================================


class TicketSource(str, Enum):
    """Source cloud platform for the ticket."""

    AWS = "AWS"
    AZURE = "Azure"


class TicketType(str, Enum):
    """ITSM ticket type classification.

    Based on ITIL/ITSM best practices:
    - Incident: Unplanned interruption or reduction in quality of service
    - Change: Addition, modification, or removal of approved infrastructure
    - Service request: User request for information, access, or standard service
    - Task: Work item supporting incident, problem, or change management
    """

    INCIDENT = "Incident"
    CHANGE = "Change"
    SERVICE_REQUEST = "Service request"
    TASK = "Task"


class TicketStatus(str, Enum):
    """Ticket lifecycle status.

    Standard ITSM workflow states:
    - Open: Newly created, awaiting assignment
    - In Progress: Actively being worked on
    - Pending: Waiting for external dependency or customer response
    - Resolved: Solution implemented, awaiting verification
    - Closed: Verified and closed
    - Done: Alternative completion state (Agile terminology)
    - Cancelled: Work abandoned or no longer required
    """

    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    DONE = "Done"
    CANCELLED = "Cancelled"


class TicketPriority(str, Enum):
    """Ticket priority levels aligned with SLA targets.

    Priority levels with typical SLA targets:
    - P1: Critical (4 hours) - Complete service outage
    - P2: High (8 hours) - Major functionality impaired
    - P3: Medium (24 hours) - Minor functionality impaired
    - P4: Low (48 hours) - Informational or cosmetic issues
    """

    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


# ============================================================================
# Base Ticket Model
# ============================================================================


class BaseTicket(BaseModel):
    """
    Base ITSM ticket model with comprehensive fields and business logic.

    Provides core ticket functionality including:
    - Automatic resolution time calculation
    - SLA compliance checking
    - Age tracking for open tickets
    - Status-based classification

    Attributes:
        issue_key: Unique ticket identifier (e.g., 'AWS-00001', 'AZ-00050')
        issue_type: Ticket classification (Incident, Change, Service request, Task)
        status: Current lifecycle status
        priority: Priority level (P1-P4) for SLA tracking
        summary: Brief description of the ticket
        team_name: Team assigned to handle the ticket
        assignee: Individual assigned to work the ticket
        reporter: Person who created the ticket
        created: Ticket creation timestamp
        updated: Last modification timestamp
        resolved: Ticket resolution timestamp (None if not resolved)
        source: Cloud platform source (AWS or Azure)

    Computed Properties:
        resolution_hours: Hours from creation to resolution
        is_resolved: Whether ticket is in resolved state
        is_open: Whether ticket is still open/active

    Business Methods:
        calculate_sla_compliance(target_hours): Check if resolved within SLA
        get_age_days(): Calculate current age for open tickets
    """

    # Core identification
    issue_key: str = Field(..., description="Unique ticket identifier")
    issue_type: TicketType = Field(..., description="Ticket classification")
    status: TicketStatus = Field(..., description="Current lifecycle status")
    priority: TicketPriority = Field(..., description="Priority level for SLA tracking")
    summary: str = Field(..., description="Brief ticket description")

    # People and teams
    team_name: Optional[str] = Field(None, description="Assigned team")
    assignee: Optional[str] = Field(None, description="Assigned individual")
    reporter: Optional[str] = Field(None, description="Ticket creator")

    # Timestamps
    created: datetime = Field(..., description="Ticket creation timestamp")
    updated: datetime = Field(..., description="Last modification timestamp")
    resolved: Optional[datetime] = Field(None, description="Resolution timestamp")

    # Source system
    source: TicketSource = Field(..., description="Cloud platform source")

    # Default SLA targets (hours) - can be overridden by config
    _default_sla_targets: ClassVar[Dict[str, int]] = {"P1": 4, "P2": 8, "P3": 24, "P4": 48}

    class Config:
        """Pydantic configuration for JSON serialization."""

        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    # ========================================================================
    # Field Validators
    # ========================================================================

    @field_validator("created", "updated", "resolved", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """
        Parse datetime from various formats including pandas Timestamp.

        Handles:
        - pandas.Timestamp objects
        - datetime objects (passthrough)
        - ISO format strings
        - None values for optional fields

        Args:
            v: Input datetime value in various formats

        Returns:
            datetime: Parsed datetime object or None

        Raises:
            ValueError: If datetime format cannot be parsed
        """
        if v is None or pd.isna(v):
            return None

        # Handle pandas Timestamp
        if isinstance(v, pd.Timestamp):
            return v.to_pydatetime()

        # Handle datetime (passthrough)
        if isinstance(v, datetime):
            return v

        # Handle string formats
        if isinstance(v, str):
            try:
                return pd.to_datetime(v).to_pydatetime()
            except Exception as e:
                raise ValueError(f"Cannot parse datetime from string '{v}': {e}")

        raise ValueError(f"Unsupported datetime format: {type(v)}")

    # ========================================================================
    # Computed Fields
    # ========================================================================

    @computed_field
    @property
    def resolution_hours(self) -> Optional[float]:
        """
        Calculate hours from ticket creation to resolution.

        Formula from complete_itsm_dashboard.py line 93:
            Resolution_Hours = (Resolved - Created).dt.total_seconds() / 3600

        Returns:
            float: Hours to resolution, or None if not resolved

        Example:
            >>> ticket.created = datetime(2024, 1, 15, 10, 0)
            >>> ticket.resolved = datetime(2024, 1, 15, 18, 0)
            >>> ticket.resolution_hours
            8.0
        """
        if self.resolved is None or self.created is None:
            return None

        delta = self.resolved - self.created
        return delta.total_seconds() / 3600

    @computed_field
    @property
    def is_resolved(self) -> bool:
        """
        Check if ticket is in a resolved state.

        Resolved states: Closed, Resolved, Done

        Returns:
            bool: True if ticket is resolved

        Example:
            >>> ticket.status = TicketStatus.CLOSED
            >>> ticket.is_resolved
            True
        """
        resolved_states = {TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.DONE}
        return self.status in resolved_states

    @computed_field
    @property
    def is_open(self) -> bool:
        """
        Check if ticket is still open/active.

        Open states: Open, In Progress, Pending

        Returns:
            bool: True if ticket is not yet resolved

        Example:
            >>> ticket.status = TicketStatus.IN_PROGRESS
            >>> ticket.is_open
            True
        """
        return not self.is_resolved and self.status != TicketStatus.CANCELLED

    # ========================================================================
    # Business Logic Methods
    # ========================================================================

    def calculate_sla_compliance(self, target_hours: Optional[int] = None) -> bool:
        """
        Determine if ticket was resolved within SLA target.

        Uses priority-based SLA targets if not specified:
        - P1: 4 hours
        - P2: 8 hours
        - P3: 24 hours
        - P4: 48 hours

        Args:
            target_hours: Custom SLA target in hours (overrides priority-based default)

        Returns:
            bool: True if resolved within SLA, False otherwise

        Example:
            >>> ticket.priority = TicketPriority.P2
            >>> ticket.resolution_hours = 6.5
            >>> ticket.calculate_sla_compliance()  # Uses P2 target = 8 hours
            True
            >>> ticket.calculate_sla_compliance(target_hours=4)  # Custom target
            False

        Note:
            Returns False for unresolved tickets
        """
        if self.resolution_hours is None:
            return False

        # Use priority-based target if not specified
        if target_hours is None:
            # Priority is already a string due to use_enum_values=True
            priority_key = self.priority if isinstance(self.priority, str) else self.priority.value
            target_hours = self._default_sla_targets.get(priority_key, 48)

        return self.resolution_hours <= target_hours

    def get_age_days(self, reference_date: Optional[datetime] = None) -> int:
        """
        Calculate ticket age in days.

        For open tickets, calculates from creation to reference date (default: now).
        For resolved tickets, calculates from creation to resolution.

        Args:
            reference_date: Date to calculate age against (default: current datetime)

        Returns:
            int: Age in days

        Example:
            >>> ticket.created = datetime(2024, 1, 1)
            >>> ticket.resolved = None
            >>> ticket.get_age_days(reference_date=datetime(2024, 1, 15))
            14
        """
        if reference_date is None:
            reference_date = datetime.now()

        # For resolved tickets, use resolution date
        end_date = self.resolved if self.resolved else reference_date

        delta = end_date - self.created
        return delta.days


# ============================================================================
# AWS Ticket Model
# ============================================================================


class AWSTicket(BaseTicket):
    """
    AWS-specific ITSM ticket model.

    Extends BaseTicket with AWS source locked and provides DataFrame integration.

    Production Usage:
        Handles 2,457 AWS tickets with distribution:
        - 50% Incidents
        - 9% Changes
        - 39% Service requests
        - 2% Tasks

    Example:
        >>> ticket = AWSTicket.from_dataframe_row({
        ...     'Issue key': 'AWS-00001',
        ...     'Issue Type': 'Incident',
        ...     'Status': 'Closed',
        ...     'Priority': 'P1',
        ...     'Created': pd.Timestamp('2024-01-15 09:00:00'),
        ...     'Resolved': pd.Timestamp('2024-01-15 12:00:00'),
        ...     'Updated': pd.Timestamp('2024-01-15 12:00:00'),
        ...     'Summary': 'EC2 instance unresponsive',
        ...     'Team Name': 'Cloud Team',
        ...     'Assignee': 'John Doe',
        ...     'Reporter': 'Jane Smith'
        ... })
        >>> ticket.source
        <TicketSource.AWS: 'AWS'>
        >>> ticket.resolution_hours
        3.0
    """

    # Lock source to AWS
    source: TicketSource = Field(default=TicketSource.AWS, frozen=True)

    @classmethod
    def from_dataframe_row(cls, row: Dict[str, Any]) -> "AWSTicket":
        """
        Create AWSTicket from pandas DataFrame row.

        Maps DataFrame columns to ticket fields:
        - 'Issue key' → issue_key
        - 'Issue Type' → issue_type
        - 'Status' → status
        - 'Priority' → priority
        - 'Created' → created
        - 'Updated' → updated
        - 'Resolved' → resolved (optional)
        - 'Summary' → summary
        - 'Team Name' → team_name (optional)
        - 'Assignee' → assignee (optional)
        - 'Reporter' → reporter (optional)

        Args:
            row: Dictionary representing a DataFrame row

        Returns:
            AWSTicket: Validated ticket instance

        Raises:
            ValidationError: If required fields are missing or invalid

        Example:
            >>> df = pd.read_excel('AWS-Tickets.xlsx')
            >>> tickets = [AWSTicket.from_dataframe_row(row) for _, row in df.iterrows()]
        """
        return cls(
            issue_key=row["Issue key"],
            issue_type=row["Issue Type"],
            status=row["Status"],
            priority=row["Priority"],
            summary=row.get("Summary", ""),
            team_name=row.get("Team Name"),
            assignee=row.get("Assignee"),
            reporter=row.get("Reporter"),
            created=row["Created"],
            updated=row.get("Updated", row["Created"]),
            resolved=row.get("Resolved"),
        )


# ============================================================================
# Azure Ticket Model
# ============================================================================


class AzureTicket(BaseTicket):
    """
    Azure-specific ITSM ticket model.

    Extends BaseTicket with Azure source locked and provides DataFrame integration.

    Production Usage:
        Handles 540 Azure tickets with distribution:
        - 20% Incidents
        - 21% Changes
        - 47% Service requests
        - 12% Tasks

    Note:
        Azure tickets show 2.3x complexity compared to AWS based on average
        resolution time and change request volume.

    Example:
        >>> ticket = AzureTicket.from_dataframe_row({
        ...     'Issue key': 'AZ-00001',
        ...     'Issue Type': 'Change',
        ...     'Status': 'Done',
        ...     'Priority': 'P3',
        ...     'Created': pd.Timestamp('2024-02-01 14:00:00'),
        ...     'Resolved': pd.Timestamp('2024-02-02 10:00:00'),
        ...     'Updated': pd.Timestamp('2024-02-02 10:00:00'),
        ...     'Summary': 'Azure VM scaling update',
        ...     'Team Name': 'Datacom Service Desk',
        ...     'Assignee': 'Bob Wilson',
        ...     'Reporter': 'Alice Brown'
        ... })
        >>> ticket.source
        <TicketSource.AZURE: 'Azure'>
        >>> ticket.resolution_hours
        20.0
    """

    # Lock source to Azure
    source: TicketSource = Field(default=TicketSource.AZURE, frozen=True)

    @classmethod
    def from_dataframe_row(cls, row: Dict[str, Any]) -> "AzureTicket":
        """
        Create AzureTicket from pandas DataFrame row.

        Maps DataFrame columns to ticket fields (same mapping as AWSTicket).

        Args:
            row: Dictionary representing a DataFrame row

        Returns:
            AzureTicket: Validated ticket instance

        Raises:
            ValidationError: If required fields are missing or invalid

        Example:
            >>> df = pd.read_excel('Azure-Tickets.xlsx')
            >>> tickets = [AzureTicket.from_dataframe_row(row) for _, row in df.iterrows()]
        """
        return cls(
            issue_key=row["Issue key"],
            issue_type=row["Issue Type"],
            status=row["Status"],
            priority=row["Priority"],
            summary=row.get("Summary", ""),
            team_name=row.get("Team Name"),
            assignee=row.get("Assignee"),
            reporter=row.get("Reporter"),
            created=row["Created"],
            updated=row.get("Updated", row["Created"]),
            resolved=row.get("Resolved"),
        )


# ============================================================================
# Ticket Collection Model
# ============================================================================


class TicketCollection(BaseModel):
    """
    Collection of AWS and Azure tickets with aggregate analytics.

    Provides portfolio-level metrics and analytics across all tickets:
    - Total ticket counts by source
    - Resolution rate calculation
    - SLA compliance aggregation
    - Collection metadata tracking

    Production Usage:
        Total: 2,997 tickets (2,457 AWS + 540 Azure)
        Resolution rate: ~90% across both platforms
        SLA compliance: ~92.5% overall

    Attributes:
        aws_tickets: List of AWS tickets
        azure_tickets: List of Azure tickets
        load_timestamp: When this collection was created
        data_source: Description of data source (e.g., 'Production JIRA export')

    Computed Properties:
        total_tickets: Combined count across both sources
        aws_count: Number of AWS tickets
        azure_count: Number of Azure tickets

    Methods:
        get_resolution_rate(): Calculate percentage of resolved tickets
        calculate_sla_compliance(sla_config): Aggregate SLA compliance

    Example:
        >>> collection = TicketCollection(
        ...     aws_tickets=[ticket1, ticket2],
        ...     azure_tickets=[ticket3],
        ...     load_timestamp=datetime.now(),
        ...     data_source='Production JIRA export 2024-10-15'
        ... )
        >>> collection.total_tickets
        3
        >>> collection.get_resolution_rate()
        66.67
    """

    aws_tickets: List[AWSTicket] = Field(default_factory=list, description="AWS ticket collection")
    azure_tickets: List[AzureTicket] = Field(default_factory=list, description="Azure ticket collection")
    load_timestamp: datetime = Field(default_factory=datetime.now, description="Collection creation time")
    data_source: str = Field(default="Unknown", description="Data source description")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    # ========================================================================
    # Computed Fields
    # ========================================================================

    @computed_field
    @property
    def total_tickets(self) -> int:
        """Total number of tickets across both sources."""
        return len(self.aws_tickets) + len(self.azure_tickets)

    @computed_field
    @property
    def aws_count(self) -> int:
        """Number of AWS tickets."""
        return len(self.aws_tickets)

    @computed_field
    @property
    def azure_count(self) -> int:
        """Number of Azure tickets."""
        return len(self.azure_tickets)

    # ========================================================================
    # Analytics Methods
    # ========================================================================

    def get_resolution_rate(self) -> float:
        """
        Calculate overall resolution rate as percentage.

        Resolution rate = (Resolved tickets / Total tickets) × 100

        Resolved states: Closed, Resolved, Done

        Returns:
            float: Resolution rate percentage (0-100)

        Example:
            >>> collection.get_resolution_rate()
            89.5
        """
        if self.total_tickets == 0:
            return 0.0

        all_tickets = self.aws_tickets + self.azure_tickets
        resolved_count = sum(1 for ticket in all_tickets if ticket.is_resolved)

        return (resolved_count / self.total_tickets) * 100

    def calculate_sla_compliance(self, sla_config: Optional[Dict[str, int]] = None) -> Dict[str, float]:
        """
        Calculate SLA compliance by priority level.

        Args:
            sla_config: Custom SLA targets by priority (e.g., {'P1': 4, 'P2': 8})
                       Defaults to BaseTicket._default_sla_targets if not provided

        Returns:
            dict: Compliance percentage by priority level
                 Format: {'P1': 95.0, 'P2': 92.5, 'P3': 88.0, 'P4': 90.0, 'overall': 91.3}

        Example:
            >>> collection.calculate_sla_compliance()
            {
                'P1': 95.0,
                'P2': 92.5,
                'P3': 88.0,
                'P4': 90.0,
                'overall': 91.3
            }
        """
        if sla_config is None:
            sla_config = BaseTicket._default_sla_targets

        all_tickets = self.aws_tickets + self.azure_tickets
        compliance_by_priority = {}

        # Calculate compliance for each priority
        for priority in ["P1", "P2", "P3", "P4"]:
            priority_tickets = [t for t in all_tickets if t.priority == priority and t.resolution_hours is not None]

            if not priority_tickets:
                compliance_by_priority[priority] = 100.0
                continue

            target_hours = sla_config.get(priority, 48)
            compliant = sum(1 for t in priority_tickets if t.calculate_sla_compliance(target_hours))

            compliance_by_priority[priority] = (compliant / len(priority_tickets)) * 100

        # Calculate overall compliance
        resolved_tickets = [t for t in all_tickets if t.resolution_hours is not None]
        if resolved_tickets:
            overall_compliant = sum(1 for t in resolved_tickets if t.calculate_sla_compliance())
            compliance_by_priority["overall"] = (overall_compliant / len(resolved_tickets)) * 100
        else:
            compliance_by_priority["overall"] = 100.0

        return compliance_by_priority
