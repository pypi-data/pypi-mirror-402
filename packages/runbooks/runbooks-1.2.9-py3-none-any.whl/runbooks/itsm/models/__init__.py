#!/usr/bin/env python3
"""
ITSM Models Package - Pydantic models for ticket management.

Exports:
    Enums:
        - TicketSource: AWS, Azure
        - TicketType: Incident, Change, Service request, Task
        - TicketStatus: Open, In Progress, Pending, Resolved, Closed, Done, Cancelled
        - TicketPriority: P1, P2, P3, P4

    Models:
        - BaseTicket: Base ticket model with computed fields and business logic
        - AWSTicket: AWS-specific ticket model
        - AzureTicket: Azure-specific ticket model
        - TicketCollection: Collection of tickets with aggregate analytics

Example:
    >>> from runbooks.itsm.models import AWSTicket, TicketPriority
    >>> ticket = AWSTicket(
    ...     issue_key='AWS-00001',
    ...     issue_type='Incident',
    ...     status='Resolved',
    ...     priority=TicketPriority.P2,
    ...     summary='EC2 instance down',
    ...     created=datetime.now(),
    ...     updated=datetime.now(),
    ...     resolved=datetime.now()
    ... )
    >>> ticket.resolution_hours
    0.0
"""

from .ticket import (
    # Enums
    TicketSource,
    TicketType,
    TicketStatus,
    TicketPriority,
    # Models
    BaseTicket,
    AWSTicket,
    AzureTicket,
    TicketCollection,
)

__all__ = [
    # Enums
    "TicketSource",
    "TicketType",
    "TicketStatus",
    "TicketPriority",
    # Models
    "BaseTicket",
    "AWSTicket",
    "AzureTicket",
    "TicketCollection",
]
