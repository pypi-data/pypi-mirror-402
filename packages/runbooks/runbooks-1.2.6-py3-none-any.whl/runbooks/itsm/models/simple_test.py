#!/usr/bin/env python3
"""
Simple validation test without external dependencies.
Tests core Pydantic model functionality.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from runbooks.itsm.models.ticket import (
    TicketSource,
    TicketType,
    TicketStatus,
    TicketPriority,
    AWSTicket,
    AzureTicket,
)

print("=" * 70)
print("ITSM Ticket Models - Simple Validation")
print("=" * 70)

# Test 1: Enum values
print("\n1. Testing enum values...")
assert TicketSource.AWS.value == "AWS"
assert TicketType.INCIDENT.value == "Incident"
assert TicketStatus.RESOLVED.value == "Resolved"
assert TicketPriority.P2.value == "P2"
print("   ✅ All enums have correct values")

# Test 2: Create AWSTicket
print("\n2. Testing AWSTicket creation...")
created = datetime(2024, 1, 15, 10, 0)
resolved = datetime(2024, 1, 15, 18, 0)

ticket = AWSTicket(
    issue_key="AWS-00001",
    issue_type=TicketType.INCIDENT,
    status=TicketStatus.RESOLVED,
    priority=TicketPriority.P2,
    summary="Test incident",
    created=created,
    updated=created,
    resolved=resolved,
)

print(f"   ✅ AWSTicket created: {ticket.issue_key}")
print(f"      Source: {ticket.source}")
print(f"      Type: {ticket.issue_type}")
print(f"      Status: {ticket.status}")

# Test 3: Resolution hours calculation
print("\n3. Testing resolution_hours calculation...")
assert ticket.resolution_hours == 8.0
print(f"   ✅ Resolution hours: {ticket.resolution_hours} (expected 8.0)")

# Test 4: SLA compliance
print("\n4. Testing SLA compliance...")
compliant = ticket.calculate_sla_compliance()  # P2 default = 8 hours
assert compliant is True
print(f"   ✅ SLA compliance: {compliant} (6h resolution within 8h P2 target)")

# Test 5: Computed properties
print("\n5. Testing computed properties...")
assert ticket.is_resolved is True
assert ticket.is_open is False
print(f"   ✅ is_resolved: {ticket.is_resolved}")
print(f"   ✅ is_open: {ticket.is_open}")

# Test 6: AzureTicket with different source
print("\n6. Testing AzureTicket...")
azure_ticket = AzureTicket(
    issue_key="AZ-00001",
    issue_type=TicketType.CHANGE,
    status=TicketStatus.DONE,
    priority=TicketPriority.P3,
    summary="Azure change",
    created=created,
    updated=created,
    resolved=created + timedelta(hours=20),
)

assert azure_ticket.source == TicketSource.AZURE.value  # Enum converted to string
assert azure_ticket.resolution_hours == 20.0
print(f"   ✅ AzureTicket created: {azure_ticket.issue_key}")
print(f"      Source: {azure_ticket.source}")
print(f"      Resolution: {azure_ticket.resolution_hours}h")

print("\n" + "=" * 70)
print("✅ ALL CORE TESTS PASSED")
print("=" * 70)
print("\nImplemented:")
print("  ✓ TicketSource, TicketType, TicketStatus, TicketPriority enums")
print("  ✓ BaseTicket with resolution_hours computed field")
print("  ✓ SLA compliance calculation")
print("  ✓ AWSTicket and AzureTicket models")
print("  ✓ Computed properties (is_resolved, is_open)")
print("\nNote: Full pandas integration test requires pandas dependency")
