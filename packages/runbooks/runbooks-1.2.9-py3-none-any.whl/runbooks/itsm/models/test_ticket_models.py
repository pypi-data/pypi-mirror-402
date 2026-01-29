#!/usr/bin/env python3
"""
Validation script for ITSM ticket models.

Tests:
1. All enums import correctly
2. BaseTicket computes resolution_hours
3. SLA compliance calculation works
4. from_dataframe_row() enables pandas DataFrame conversion
5. TicketCollection provides aggregate analytics
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from runbooks.itsm.models.ticket import (
    TicketSource,
    TicketType,
    TicketStatus,
    TicketPriority,
    BaseTicket,
    AWSTicket,
    AzureTicket,
    TicketCollection,
)


def test_enums():
    """Test all enums are defined with proper values."""
    print("Testing enums...")

    # TicketSource
    assert TicketSource.AWS.value == "AWS"
    assert TicketSource.AZURE.value == "Azure"

    # TicketType
    assert TicketType.INCIDENT.value == "Incident"
    assert TicketType.CHANGE.value == "Change"
    assert TicketType.SERVICE_REQUEST.value == "Service request"
    assert TicketType.TASK.value == "Task"

    # TicketStatus
    assert TicketStatus.OPEN.value == "Open"
    assert TicketStatus.IN_PROGRESS.value == "In Progress"
    assert TicketStatus.PENDING.value == "Pending"
    assert TicketStatus.RESOLVED.value == "Resolved"
    assert TicketStatus.CLOSED.value == "Closed"
    assert TicketStatus.DONE.value == "Done"
    assert TicketStatus.CANCELLED.value == "Cancelled"

    # TicketPriority
    assert TicketPriority.P1.value == "P1"
    assert TicketPriority.P2.value == "P2"
    assert TicketPriority.P3.value == "P3"
    assert TicketPriority.P4.value == "P4"

    print("✅ All enums defined correctly")


def test_resolution_hours_calculation():
    """Test BaseTicket computes resolution_hours correctly."""
    print("\nTesting resolution_hours calculation...")

    created = datetime(2024, 1, 15, 10, 0)
    resolved = datetime(2024, 1, 15, 18, 0)  # 8 hours later

    ticket = AWSTicket(
        issue_key="AWS-00001",
        issue_type=TicketType.INCIDENT,
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.P2,
        summary="Test ticket",
        created=created,
        updated=created,
        resolved=resolved,
    )

    assert ticket.resolution_hours == 8.0, f"Expected 8.0, got {ticket.resolution_hours}"
    print(f"✅ Resolution hours calculated correctly: {ticket.resolution_hours} hours")


def test_sla_compliance():
    """Test SLA compliance calculation."""
    print("\nTesting SLA compliance...")

    created = datetime(2024, 1, 15, 10, 0)

    # P2 ticket resolved in 6 hours (within 8-hour SLA)
    ticket_pass = AWSTicket(
        issue_key="AWS-00001",
        issue_type=TicketType.INCIDENT,
        status=TicketStatus.RESOLVED,
        priority=TicketPriority.P2,
        summary="Test ticket",
        created=created,
        updated=created,
        resolved=created + timedelta(hours=6),
    )

    assert ticket_pass.calculate_sla_compliance() is True
    print("✅ SLA compliance (pass): Ticket resolved in 6h passes P2 SLA (8h target)")

    # P2 ticket resolved in 10 hours (exceeds 8-hour SLA)
    ticket_fail = AWSTicket(
        issue_key="AWS-00002",
        issue_type=TicketType.INCIDENT,
        status=TicketStatus.OPEN,
        priority=TicketPriority.P2,
        summary="Test ticket",
        created=created,
        updated=created,
        resolved=created + timedelta(hours=10),
    )

    assert ticket_fail.calculate_sla_compliance() is False
    print("✅ SLA compliance (fail): Ticket resolved in 10h fails P2 SLA (8h target)")


def test_pandas_integration():
    """Test from_dataframe_row() pandas DataFrame conversion."""
    print("\nTesting pandas DataFrame integration...")

    # Create sample DataFrame row
    row = {
        "Issue key": "AWS-00001",
        "Issue Type": "Incident",
        "Status": "Resolved",
        "Priority": "P1",
        "Created": pd.Timestamp("2024-01-15 09:00:00"),
        "Resolved": pd.Timestamp("2024-01-15 12:00:00"),
        "Updated": pd.Timestamp("2024-01-15 12:00:00"),
        "Summary": "EC2 instance unresponsive",
        "Team Name": "Cloud Team",
        "Assignee": "John Doe",
        "Reporter": "Jane Smith",
    }

    ticket = AWSTicket.from_dataframe_row(row)

    assert ticket.issue_key == "AWS-00001"
    assert ticket.issue_type == TicketType.INCIDENT.value  # Converted to string
    assert ticket.status == TicketStatus.RESOLVED.value
    assert ticket.priority == TicketPriority.P1.value
    assert ticket.source == TicketSource.AWS.value
    assert ticket.resolution_hours == 3.0
    assert ticket.team_name == "Cloud Team"
    assert ticket.assignee == "John Doe"

    print("✅ DataFrame row conversion successful")
    print(f"   - Ticket: {ticket.issue_key}")
    print(f"   - Type: {ticket.issue_type}")
    print(f"   - Resolution: {ticket.resolution_hours} hours")


def test_ticket_collection():
    """Test TicketCollection aggregate analytics."""
    print("\nTesting TicketCollection analytics...")

    created = datetime(2024, 1, 15, 10, 0)

    # Create AWS tickets
    aws_tickets = [
        AWSTicket(
            issue_key=f"AWS-{i:05d}",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED if i % 2 == 0 else TicketStatus.OPEN,
            priority=TicketPriority.P2,
            summary=f"AWS issue {i}",
            created=created,
            updated=created,
            resolved=created + timedelta(hours=6) if i % 2 == 0 else None,
        )
        for i in range(10)
    ]

    # Create Azure tickets
    azure_tickets = [
        AzureTicket(
            issue_key=f"AZ-{i:05d}",
            issue_type=TicketType.CHANGE,
            status=TicketStatus.DONE,
            priority=TicketPriority.P3,
            summary=f"Azure change {i}",
            created=created,
            updated=created,
            resolved=created + timedelta(hours=20),
        )
        for i in range(5)
    ]

    collection = TicketCollection(aws_tickets=aws_tickets, azure_tickets=azure_tickets, data_source="Test data")

    assert collection.total_tickets == 15
    assert collection.aws_count == 10
    assert collection.azure_count == 5

    resolution_rate = collection.get_resolution_rate()
    expected_rate = (10 / 15) * 100  # 5 AWS resolved + 5 Azure resolved = 10/15
    assert abs(resolution_rate - expected_rate) < 0.01

    print("✅ TicketCollection analytics working")
    print(f"   - Total tickets: {collection.total_tickets}")
    print(f"   - AWS: {collection.aws_count}, Azure: {collection.azure_count}")
    print(f"   - Resolution rate: {resolution_rate:.1f}%")

    # Test SLA compliance calculation
    sla_compliance = collection.calculate_sla_compliance()
    print(f"   - SLA compliance: {sla_compliance['overall']:.1f}%")


def test_ticket_properties():
    """Test computed properties (is_resolved, is_open)."""
    print("\nTesting ticket properties...")

    created = datetime(2024, 1, 15, 10, 0)

    # Resolved ticket
    resolved_ticket = AWSTicket(
        issue_key="AWS-00001",
        issue_type=TicketType.INCIDENT,
        status=TicketStatus.CLOSED,
        priority=TicketPriority.P2,
        summary="Test",
        created=created,
        updated=created,
        resolved=created + timedelta(hours=4),
    )

    assert resolved_ticket.is_resolved is True
    assert resolved_ticket.is_open is False

    # Open ticket
    open_ticket = AWSTicket(
        issue_key="AWS-00002",
        issue_type=TicketType.INCIDENT,
        status=TicketStatus.IN_PROGRESS,
        priority=TicketPriority.P2,
        summary="Test",
        created=created,
        updated=created,
    )

    assert open_ticket.is_resolved is False
    assert open_ticket.is_open is True

    print("✅ Ticket properties working correctly")


def main():
    """Run all validation tests."""
    print("=" * 70)
    print("ITSM Ticket Models Validation")
    print("=" * 70)

    try:
        test_enums()
        test_resolution_hours_calculation()
        test_sla_compliance()
        test_pandas_integration()
        test_ticket_collection()
        test_ticket_properties()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nSummary:")
        print("  ✓ All enums defined with proper string values")
        print("  ✓ BaseTicket computes resolution_hours correctly")
        print("  ✓ SLA compliance calculation works")
        print("  ✓ from_dataframe_row() enables pandas DataFrame conversion")
        print("  ✓ TicketCollection provides aggregate analytics")
        print("  ✓ Computed properties (is_resolved, is_open) working")
        print("\nImports successfully: python -c \"from runbooks.itsm.models.ticket import AWSTicket; print('✅')\"")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
