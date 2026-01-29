#!/usr/bin/env python3
"""
Comprehensive Test Suite for ITSM Analytics Dashboard Phase 1

Tests all Phase 1 components with 95%+ coverage target:
- Configuration management (config.py)
- Pydantic ticket models (models/ticket.py)
- Data loading layer (core/data_loader.py)

Author: @agent-test-specialist
Date: 2025-10-15
Phase: 1 - Day 4 (Testing & Validation)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pandas as pd
import pytest
from pydantic import ValidationError

from runbooks.itsm.config import (
    DataSourceConfig,
    SLAConfig,
    DesignSystemConfig,
    VisualizationConfig,
    ITSMConfig,
    get_config,
    get_legacy_config,
    get_legacy_design_system,
)
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
from runbooks.itsm.core.data_loader import (
    ITSMDataLoader,
    DataLoader,
    DataLoadError,
    load_ticket_data,
)


# ============================================================================
# Configuration Tests
# ============================================================================


@pytest.mark.unit
class TestDataSourceConfig:
    """Test DataSourceConfig functionality."""

    def test_default_data_source_config(self):
        """Test default DataSourceConfig values."""
        config = DataSourceConfig()

        assert config.data_dir == Path("data")
        assert config.aws_file == "AWSTickets.xlsx"
        assert config.aws_sheet == "AWS-Tickets"
        assert config.azure_file == "AzureTickets.xlsx"
        assert config.azure_sheet == "Azure-Tickets"
        assert config.pricing_file == "Cloud price revision v 1.1 1.9.25 Bluecurrent Model.xlsx"
        assert config.pricing_sheet == "Bluecurrent"

    def test_custom_data_source_config(self):
        """Test custom DataSourceConfig values."""
        config = DataSourceConfig(
            data_dir=Path("/custom/path"), aws_file="custom_aws.xlsx", azure_file="custom_azure.xlsx"
        )

        assert config.data_dir == Path("/custom/path")
        assert config.aws_file == "custom_aws.xlsx"
        assert config.azure_file == "custom_azure.xlsx"

    def test_data_dir_string_conversion(self):
        """Test automatic string to Path conversion."""
        config = DataSourceConfig(data_dir="string/path")

        assert isinstance(config.data_dir, Path)
        assert str(config.data_dir) == "string/path"

    def test_get_aws_path(self):
        """Test AWS file path construction."""
        config = DataSourceConfig(data_dir=Path("test_data"), aws_file="aws_tickets.xlsx")

        expected_path = Path("test_data") / "aws_tickets.xlsx"
        assert config.get_aws_path() == expected_path

    def test_get_azure_path(self):
        """Test Azure file path construction."""
        config = DataSourceConfig(data_dir=Path("test_data"), azure_file="azure_tickets.xlsx")

        expected_path = Path("test_data") / "azure_tickets.xlsx"
        assert config.get_azure_path() == expected_path

    def test_get_pricing_path(self):
        """Test pricing file path construction."""
        config = DataSourceConfig(data_dir=Path("test_data"), pricing_file="pricing.xlsx")

        expected_path = Path("test_data") / "pricing.xlsx"
        assert config.get_pricing_path() == expected_path


@pytest.mark.unit
class TestSLAConfig:
    """Test SLAConfig functionality."""

    def test_default_sla_targets(self):
        """Test default SLA target values."""
        config = SLAConfig()

        assert config.p1_hours == 4
        assert config.p2_hours == 8
        assert config.p3_hours == 24
        assert config.p4_hours == 48

    def test_custom_sla_targets(self):
        """Test custom SLA target values."""
        config = SLAConfig(p1_hours=2, p2_hours=4, p3_hours=12, p4_hours=24)

        assert config.p1_hours == 2
        assert config.p2_hours == 4
        assert config.p3_hours == 12
        assert config.p4_hours == 24

    def test_sla_minimum_validation(self):
        """Test SLA hours must be >= 1."""
        with pytest.raises(ValidationError):
            SLAConfig(p1_hours=0)

        with pytest.raises(ValidationError):
            SLAConfig(p2_hours=-1)

    def test_get_target_valid_priorities(self):
        """Test get_target() for all valid priorities."""
        config = SLAConfig()

        assert config.get_target("P1") == 4
        assert config.get_target("P2") == 8
        assert config.get_target("P3") == 24
        assert config.get_target("P4") == 48

    def test_get_target_invalid_priority(self):
        """Test get_target() raises ValueError for invalid priority."""
        config = SLAConfig()

        with pytest.raises(ValueError, match="Unknown priority"):
            config.get_target("P5")

        with pytest.raises(ValueError, match="Unknown priority"):
            config.get_target("Invalid")

    def test_to_dict(self):
        """Test conversion to legacy dictionary format."""
        config = SLAConfig(p1_hours=2, p2_hours=4, p3_hours=12, p4_hours=24)

        result = config.to_dict()

        assert result == {"P1": 2, "P2": 4, "P3": 12, "P4": 24}


@pytest.mark.unit
class TestDesignSystemConfig:
    """Test DesignSystemConfig functionality."""

    def test_default_colors(self):
        """Test default color values."""
        config = DesignSystemConfig()

        assert config.aws_color == "#FF9900"
        assert config.aws_color_dark == "#CC7A00"
        assert config.azure_color == "#0078D4"
        assert config.azure_color_dark == "#005A9E"
        assert config.kpi_color == "#73BA9B"
        assert config.success_color == "#28A745"
        assert config.warning_color == "#FFC107"
        assert config.danger_color == "#DC3545"
        assert config.info_color == "#17A2B8"
        assert config.dark_color == "#2C3E50"
        assert config.light_color == "#ECF0F1"
        assert config.background_color == "#F8F9FA"

    def test_default_typography(self):
        """Test default typography values."""
        config = DesignSystemConfig()

        assert config.font_family == "Arial, Roboto, sans-serif"
        assert config.title_size == 24
        assert config.subtitle_size == 18
        assert config.body_size == 14
        assert config.caption_size == 12

    def test_typography_minimum_validation(self):
        """Test typography size minimum constraints."""
        with pytest.raises(ValidationError):
            DesignSystemConfig(title_size=11)  # Min is 12

        with pytest.raises(ValidationError):
            DesignSystemConfig(body_size=7)  # Min is 8

    def test_default_export_settings(self):
        """Test default export settings."""
        config = DesignSystemConfig()

        assert config.export_width == 1920
        assert config.export_height == 1080
        assert config.export_scale == 2
        assert config.export_format == "png"

    def test_export_format_validation(self):
        """Test export format validation."""
        # Valid formats
        for fmt in ["png", "svg", "pdf"]:
            config = DesignSystemConfig(export_format=fmt)
            assert config.export_format == fmt

        # Invalid format
        with pytest.raises(ValidationError, match="Export format must be one of"):
            DesignSystemConfig(export_format="jpg")

    def test_export_scale_validation(self):
        """Test export scale constraints."""
        with pytest.raises(ValidationError):
            DesignSystemConfig(export_scale=0)  # Min is 1

        with pytest.raises(ValidationError):
            DesignSystemConfig(export_scale=5)  # Max is 4

    def test_default_layout_margins(self):
        """Test default layout margin values."""
        config = DesignSystemConfig()

        assert config.layout_margin_left == 80
        assert config.layout_margin_right == 80
        assert config.layout_margin_top == 100
        assert config.layout_margin_bottom == 80
        assert config.layout_height == 600

    def test_get_color_palette(self):
        """Test get_color_palette() method."""
        config = DesignSystemConfig()

        palette = config.get_color_palette()

        assert isinstance(palette, dict)
        assert palette["aws"] == "#FF9900"
        assert palette["azure"] == "#0078D4"
        assert palette["kpi"] == "#73BA9B"
        assert palette["success"] == "#28A745"
        assert palette["warning"] == "#FFC107"
        assert palette["danger"] == "#DC3545"
        assert palette["info"] == "#17A2B8"
        assert palette["dark"] == "#2C3E50"
        assert palette["light"] == "#ECF0F1"
        assert palette["background"] == "#F8F9FA"

    def test_get_typography(self):
        """Test get_typography() method."""
        config = DesignSystemConfig()

        typography = config.get_typography()

        assert typography["font_family"] == "Arial, Roboto, sans-serif"
        assert typography["title_size"] == 24
        assert typography["subtitle_size"] == 18
        assert typography["body_size"] == 14
        assert typography["caption_size"] == 12

    def test_get_export_settings(self):
        """Test get_export_settings() method."""
        config = DesignSystemConfig()

        export = config.get_export_settings()

        assert export["width"] == 1920
        assert export["height"] == 1080
        assert export["scale"] == 2
        assert export["format"] == "png"

    def test_get_layout_margins(self):
        """Test get_layout_margins() method."""
        config = DesignSystemConfig()

        margins = config.get_layout_margins()

        assert margins["l"] == 80
        assert margins["r"] == 80
        assert margins["t"] == 100
        assert margins["b"] == 80


@pytest.mark.unit
class TestVisualizationConfig:
    """Test VisualizationConfig functionality."""

    def test_default_visualization_config(self):
        """Test default VisualizationConfig values."""
        config = VisualizationConfig()

        assert config.theme == "plotly_dark"
        assert config.use_sample_data is True
        assert config.performance_cache_enabled is True
        assert config.max_items_display == 20

    def test_custom_visualization_config(self):
        """Test custom VisualizationConfig values."""
        config = VisualizationConfig(
            theme="plotly_white", use_sample_data=False, performance_cache_enabled=False, max_items_display=50
        )

        assert config.theme == "plotly_white"
        assert config.use_sample_data is False
        assert config.performance_cache_enabled is False
        assert config.max_items_display == 50

    def test_max_items_display_validation(self):
        """Test max_items_display constraints."""
        with pytest.raises(ValidationError):
            VisualizationConfig(max_items_display=4)  # Min is 5

        with pytest.raises(ValidationError):
            VisualizationConfig(max_items_display=101)  # Max is 100


@pytest.mark.unit
class TestITSMConfig:
    """Test ITSMConfig master configuration."""

    def test_default_itsm_config(self):
        """Test default ITSMConfig with all sub-configs."""
        config = ITSMConfig()

        assert isinstance(config.data_sources, DataSourceConfig)
        assert isinstance(config.sla_targets, SLAConfig)
        assert isinstance(config.design_system, DesignSystemConfig)
        assert isinstance(config.visualization, VisualizationConfig)

    def test_custom_itsm_config(self):
        """Test custom ITSMConfig with custom sub-configs."""
        custom_sla = SLAConfig(p1_hours=2, p2_hours=4, p3_hours=12, p4_hours=24)

        config = ITSMConfig(sla_targets=custom_sla)

        assert config.sla_targets.p1_hours == 2
        assert config.sla_targets.p2_hours == 4

    def test_to_legacy_dict(self):
        """Test conversion to legacy CONFIG dictionary format."""
        config = ITSMConfig()

        legacy = config.to_legacy_dict()

        assert legacy["AWS_FILE"] == "AWSTickets.xlsx"
        assert legacy["AZURE_FILE"] == "AzureTickets.xlsx"
        assert legacy["PRICING_FILE"] == "Cloud price revision v 1.1 1.9.25 Bluecurrent Model.xlsx"
        assert legacy["SLA_TARGETS"] == {"P1": 4, "P2": 8, "P3": 24, "P4": 48}
        assert legacy["THEME"] == "plotly_dark"

    def test_to_design_system_dict(self):
        """Test conversion to legacy DESIGN_SYSTEM dictionary format."""
        config = ITSMConfig()

        design = config.to_design_system_dict()

        assert "colors" in design
        assert "typography" in design
        assert "export" in design
        assert "layout" in design

        assert design["colors"]["aws"] == "#FF9900"
        assert design["typography"]["font_family"] == "Arial, Roboto, sans-serif"
        assert design["export"]["format"] == "png"
        assert design["layout"]["margin"]["l"] == 80

    def test_get_config_function(self):
        """Test get_config() returns default ITSMConfig."""
        config = get_config()

        assert isinstance(config, ITSMConfig)
        assert config.sla_targets.p1_hours == 4

    def test_get_legacy_config_function(self):
        """Test get_legacy_config() returns dictionary."""
        legacy = get_legacy_config()

        assert isinstance(legacy, dict)
        assert "AWS_FILE" in legacy
        assert "SLA_TARGETS" in legacy

    def test_get_legacy_design_system_function(self):
        """Test get_legacy_design_system() returns dictionary."""
        design = get_legacy_design_system()

        assert isinstance(design, dict)
        assert "colors" in design
        assert "typography" in design


# ============================================================================
# Ticket Model Tests
# ============================================================================


@pytest.mark.unit
class TestTicketEnums:
    """Test all ticket enumeration types."""

    def test_ticket_source_enum(self):
        """Test TicketSource enum values."""
        assert TicketSource.AWS == "AWS"
        assert TicketSource.AZURE == "Azure"

    def test_ticket_type_enum(self):
        """Test TicketType enum values."""
        assert TicketType.INCIDENT == "Incident"
        assert TicketType.CHANGE == "Change"
        assert TicketType.SERVICE_REQUEST == "Service request"
        assert TicketType.TASK == "Task"

    def test_ticket_status_enum(self):
        """Test TicketStatus enum values."""
        assert TicketStatus.OPEN == "Open"
        assert TicketStatus.IN_PROGRESS == "In Progress"
        assert TicketStatus.PENDING == "Pending"
        assert TicketStatus.RESOLVED == "Resolved"
        assert TicketStatus.CLOSED == "Closed"
        assert TicketStatus.DONE == "Done"
        assert TicketStatus.CANCELLED == "Cancelled"

    def test_ticket_priority_enum(self):
        """Test TicketPriority enum values."""
        assert TicketPriority.P1 == "P1"
        assert TicketPriority.P2 == "P2"
        assert TicketPriority.P3 == "P3"
        assert TicketPriority.P4 == "P4"


@pytest.mark.unit
class TestBaseTicket:
    """Test BaseTicket model functionality."""

    def test_create_base_ticket(self, sample_aws_ticket):
        """Test creating a valid BaseTicket."""
        assert sample_aws_ticket.issue_key == "AWS-00001"
        assert sample_aws_ticket.issue_type == TicketType.INCIDENT
        assert sample_aws_ticket.status == TicketStatus.CLOSED
        assert sample_aws_ticket.priority == TicketPriority.P2
        assert sample_aws_ticket.summary == "EC2 instance unresponsive in ap-southeast-2"

    def test_datetime_parsing_pandas_timestamp(self):
        """Test datetime field parsing from pandas Timestamp."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=pd.Timestamp("2024-01-15 10:00:00"),
            updated=pd.Timestamp("2024-01-15 11:00:00"),
        )

        assert isinstance(ticket.created, datetime)
        assert ticket.created.year == 2024
        assert ticket.created.month == 1
        assert ticket.created.day == 15

    def test_datetime_parsing_string(self):
        """Test datetime field parsing from ISO string."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created="2024-01-15T10:00:00",
            updated="2024-01-15T11:00:00",
        )

        assert isinstance(ticket.created, datetime)

    def test_datetime_parsing_none(self):
        """Test datetime field parsing with None value."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime(2024, 1, 15),
            updated=datetime(2024, 1, 15),
            resolved=None,
        )

        assert ticket.resolved is None

    def test_resolution_hours_calculation(self, sample_aws_ticket):
        """Test resolution_hours computed field calculation."""
        # Created: 2024-01-15 10:00:00, Resolved: 2024-01-15 18:00:00
        # Expected: 8 hours
        assert sample_aws_ticket.resolution_hours == 8.0

    def test_resolution_hours_none_when_not_resolved(self):
        """Test resolution_hours is None when ticket not resolved."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime(2024, 1, 15, 10, 0, 0),
            updated=datetime(2024, 1, 15, 10, 0, 0),
            resolved=None,
        )

        assert ticket.resolution_hours is None

    def test_is_resolved_property(self, sample_aws_ticket):
        """Test is_resolved computed property."""
        # sample_aws_ticket has status CLOSED
        assert sample_aws_ticket.is_resolved is True

        resolved_ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert resolved_ticket.is_resolved is True

        done_ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.DONE,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert done_ticket.is_resolved is True

    def test_is_open_property(self):
        """Test is_open computed property."""
        open_ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert open_ticket.is_open is True

        in_progress_ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.IN_PROGRESS,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert in_progress_ticket.is_open is True

        closed_ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.CLOSED,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert closed_ticket.is_open is False

    def test_calculate_sla_compliance_with_target(self):
        """Test SLA compliance calculation with explicit target."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P2,
            summary="Test",
            created=datetime(2024, 1, 15, 10, 0, 0),
            updated=datetime(2024, 1, 15, 16, 0, 0),
            resolved=datetime(2024, 1, 15, 16, 0, 0),  # 6 hours
        )

        # Within 8-hour target
        assert ticket.calculate_sla_compliance(target_hours=8) is True

        # Outside 4-hour target
        assert ticket.calculate_sla_compliance(target_hours=4) is False

    def test_calculate_sla_compliance_priority_based(self):
        """Test SLA compliance using priority-based defaults."""
        # P1 ticket resolved in 3.5 hours (target: 4 hours)
        p1_ticket = AWSTicket(
            issue_key="AWS-P1",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P1,
            summary="Critical issue",
            created=datetime(2024, 1, 10, 8, 0, 0),
            updated=datetime(2024, 1, 10, 11, 30, 0),
            resolved=datetime(2024, 1, 10, 11, 30, 0),
        )
        assert p1_ticket.calculate_sla_compliance() is True

        # P2 ticket resolved in 10 hours (target: 8 hours)
        p2_ticket = AWSTicket(
            issue_key="AWS-P2",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P2,
            summary="High priority issue",
            created=datetime(2024, 1, 15, 8, 0, 0),
            updated=datetime(2024, 1, 15, 18, 0, 0),
            resolved=datetime(2024, 1, 15, 18, 0, 0),
        )
        assert p2_ticket.calculate_sla_compliance() is False

    def test_calculate_sla_compliance_unresolved(self):
        """Test SLA compliance returns False for unresolved tickets."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
            resolved=None,
        )

        assert ticket.calculate_sla_compliance() is False

    def test_get_age_days_resolved_ticket(self):
        """Test age calculation for resolved ticket."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime(2024, 1, 1, 10, 0, 0),
            updated=datetime(2024, 1, 10, 10, 0, 0),
            resolved=datetime(2024, 1, 10, 10, 0, 0),
        )

        # Age should be from creation to resolution
        assert ticket.get_age_days() == 9

    def test_get_age_days_open_ticket(self):
        """Test age calculation for open ticket with reference date."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime(2024, 1, 1, 10, 0, 0),
            updated=datetime(2024, 1, 1, 10, 0, 0),
            resolved=None,
        )

        reference = datetime(2024, 1, 15, 10, 0, 0)
        assert ticket.get_age_days(reference_date=reference) == 14


@pytest.mark.unit
class TestAWSTicket:
    """Test AWSTicket specialized model."""

    def test_aws_ticket_source_frozen(self, sample_aws_ticket):
        """Test AWS ticket source is frozen to AWS."""
        assert sample_aws_ticket.source == TicketSource.AWS

    def test_aws_ticket_source_cannot_be_changed(self):
        """Test AWS ticket source cannot be modified."""
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )

        # Source should be AWS by default
        assert ticket.source == TicketSource.AWS

        # Attempting to change should fail (frozen field)
        with pytest.raises(ValidationError):
            ticket.source = TicketSource.AZURE

    def test_from_dataframe_row(self, sample_dataframe_row):
        """Test creating AWSTicket from DataFrame row."""
        ticket = AWSTicket.from_dataframe_row(sample_dataframe_row)

        assert ticket.issue_key == "AWS-TEST-001"
        assert ticket.issue_type == TicketType.INCIDENT
        assert ticket.status == TicketStatus.RESOLVED
        assert ticket.priority == TicketPriority.P2
        assert ticket.summary == "Test incident summary"
        assert ticket.team_name == "Test Team"
        assert ticket.assignee == "Test Assignee"
        assert ticket.reporter == "Test Reporter"
        assert ticket.source == TicketSource.AWS

    def test_from_dataframe_row_minimal_fields(self):
        """Test from_dataframe_row with minimal required fields."""
        minimal_row = {
            "Issue key": "AWS-MIN-001",
            "Issue Type": "Incident",
            "Status": "Open",
            "Priority": "P1",
            "Created": pd.Timestamp("2024-01-15 10:00:00"),
        }

        ticket = AWSTicket.from_dataframe_row(minimal_row)

        assert ticket.issue_key == "AWS-MIN-001"
        assert ticket.team_name is None
        assert ticket.assignee is None
        assert ticket.reporter is None
        assert ticket.summary == ""


@pytest.mark.unit
class TestAzureTicket:
    """Test AzureTicket specialized model."""

    def test_azure_ticket_source_frozen(self, sample_azure_ticket):
        """Test Azure ticket source is frozen to Azure."""
        assert sample_azure_ticket.source == TicketSource.AZURE

    def test_azure_ticket_source_cannot_be_changed(self):
        """Test Azure ticket source cannot be modified."""
        ticket = AzureTicket(
            issue_key="AZ-TEST",
            issue_type=TicketType.CHANGE,
            status=TicketStatus.DONE,
            priority=TicketPriority.P3,
            summary="Test",
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert ticket.source == TicketSource.AZURE

        with pytest.raises(ValidationError):
            ticket.source = TicketSource.AWS

    def test_from_dataframe_row(self):
        """Test creating AzureTicket from DataFrame row."""
        row = {
            "Issue key": "AZ-TEST-001",
            "Issue Type": "Change",
            "Status": "Done",
            "Priority": "P3",
            "Summary": "Azure change request",
            "Team Name": "Datacom Team",
            "Assignee": "Azure Admin",
            "Reporter": "User X",
            "Created": pd.Timestamp("2024-02-01 14:00:00"),
            "Updated": pd.Timestamp("2024-02-02 10:00:00"),
            "Resolved": pd.Timestamp("2024-02-02 10:00:00"),
        }

        ticket = AzureTicket.from_dataframe_row(row)

        assert ticket.issue_key == "AZ-TEST-001"
        assert ticket.issue_type == TicketType.CHANGE
        assert ticket.status == TicketStatus.DONE
        assert ticket.source == TicketSource.AZURE


@pytest.mark.unit
class TestTicketCollection:
    """Test TicketCollection aggregate model."""

    def test_create_ticket_collection(self, sample_ticket_collection):
        """Test creating TicketCollection."""
        assert sample_ticket_collection.aws_count == 3
        assert sample_ticket_collection.azure_count == 2
        assert sample_ticket_collection.total_tickets == 5

    def test_empty_ticket_collection(self):
        """Test empty TicketCollection."""
        collection = TicketCollection(
            aws_tickets=[], azure_tickets=[], load_timestamp=datetime.now(), data_source="Empty test collection"
        )

        assert collection.total_tickets == 0
        assert collection.aws_count == 0
        assert collection.azure_count == 0

    def test_get_resolution_rate(self, sample_ticket_collection):
        """Test resolution rate calculation."""
        # 3 resolved tickets out of 5 total = 60%
        rate = sample_ticket_collection.get_resolution_rate()

        assert rate == 60.0

    def test_get_resolution_rate_empty_collection(self):
        """Test resolution rate for empty collection."""
        collection = TicketCollection(aws_tickets=[], azure_tickets=[])

        assert collection.get_resolution_rate() == 0.0

    def test_calculate_sla_compliance(self, sample_ticket_collection):
        """Test SLA compliance calculation."""
        compliance = sample_ticket_collection.calculate_sla_compliance()

        assert isinstance(compliance, dict)
        assert "P1" in compliance
        assert "P2" in compliance
        assert "P3" in compliance
        assert "P4" in compliance
        assert "overall" in compliance

        # All values should be percentages (0-100)
        for priority, rate in compliance.items():
            assert 0 <= rate <= 100

    def test_calculate_sla_compliance_custom_config(self, sample_ticket_collection):
        """Test SLA compliance with custom SLA targets."""
        custom_sla = {"P1": 2, "P2": 4, "P3": 12, "P4": 24}

        compliance = sample_ticket_collection.calculate_sla_compliance(sla_config=custom_sla)

        assert isinstance(compliance, dict)
        assert "overall" in compliance


# ============================================================================
# Data Loader Tests
# ============================================================================


@pytest.mark.unit
class TestITSMDataLoader:
    """Test ITSMDataLoader functionality."""

    def test_initialization_default_config(self):
        """Test ITSMDataLoader initialization with default config."""
        loader = ITSMDataLoader()

        assert loader.config is not None
        assert "AWS_FILE" in loader.config
        assert "AZURE_FILE" in loader.config
        assert "PRICING_FILE" in loader.config

    def test_initialization_custom_config(self):
        """Test ITSMDataLoader initialization with custom config."""
        custom_config = {
            "AWS_FILE": "custom_aws.xlsx",
            "AZURE_FILE": "custom_azure.xlsx",
            "PRICING_FILE": "custom_pricing.xlsx",
            "SLA_TARGETS": {"P1": 2, "P2": 4, "P3": 12, "P4": 24},
        }

        loader = ITSMDataLoader(config=custom_config)

        assert loader.config["AWS_FILE"] == "custom_aws.xlsx"
        assert loader.config["SLA_TARGETS"]["P1"] == 2

    def test_generate_sample_data(self):
        """Test sample data generation with reproducible seed."""
        loader = ITSMDataLoader()

        aws_df, azure_df, pricing_df = loader._generate_sample_data()

        # Validate AWS sample data
        assert len(aws_df) == 2457
        assert "Issue key" in aws_df.columns
        assert "Source" in aws_df.columns
        assert aws_df["Source"].unique()[0] == "AWS"

        # Validate Azure sample data
        assert len(azure_df) == 540
        assert azure_df["Source"].unique()[0] == "Azure"

        # Validate pricing sample data
        assert len(pricing_df) == 12
        assert "Month" in pricing_df.columns
        assert "Existing_Cost" in pricing_df.columns
        assert "New_Model_Cost" in pricing_df.columns

    def test_generate_aws_sample_distributions(self):
        """Test AWS sample data matches expected distributions."""
        loader = ITSMDataLoader()
        aws_df = loader._generate_aws_sample(n=2457)

        # Check issue type distribution (~50% Incident)
        incident_ratio = (aws_df["Issue Type"] == "Incident").sum() / len(aws_df)
        assert 0.45 < incident_ratio < 0.55  # Allow 5% variance

        # Check priority distribution (~64% P4)
        p4_ratio = (aws_df["Priority"] == "P4").sum() / len(aws_df)
        assert 0.59 < p4_ratio < 0.69  # Allow 5% variance

        # Check Resolution_Hours is calculated
        assert "Resolution_Hours" in aws_df.columns
        resolved_tickets = aws_df[aws_df["Status"].isin(["Closed", "Resolved", "Done"])]
        assert resolved_tickets["Resolution_Hours"].notna().all()

    def test_generate_azure_sample_distributions(self):
        """Test Azure sample data matches expected distributions."""
        loader = ITSMDataLoader()
        azure_df = loader._generate_azure_sample(n=540)

        # Check issue type distribution (~20% Incident, ~47% Service request)
        incident_ratio = (azure_df["Issue Type"] == "Incident").sum() / len(azure_df)
        assert 0.15 < incident_ratio < 0.25

        service_request_ratio = (azure_df["Issue Type"] == "Service request").sum() / len(azure_df)
        assert 0.42 < service_request_ratio < 0.52

    def test_generate_pricing_sample(self):
        """Test pricing sample data generation."""
        loader = ITSMDataLoader()
        pricing_df = loader._generate_pricing_sample()

        assert len(pricing_df) == 12
        assert pricing_df["Existing_Cost"].iloc[0] == 42171
        assert pricing_df["New_Model_Cost"].iloc[0] == 52687
        assert (pricing_df["New_Model_Cost"] == 52687).all()

    def test_load_all_data_fallback_to_sample(self):
        """Test load_all_data falls back to sample data when files missing."""
        loader = ITSMDataLoader()

        aws_df, azure_df, pricing_df = loader.load_all_data()

        # Should successfully load sample data
        assert len(aws_df) > 0
        assert len(azure_df) > 0
        assert len(pricing_df) > 0
        assert "Resolution_Hours" in aws_df.columns
        assert "Resolution_Hours" in azure_df.columns

    def test_load_all_data_sample_disabled(self):
        """Test load_all_data raises error when sample data disabled."""
        config = {
            "AWS_FILE": "/nonexistent/aws.xlsx",
            "AZURE_FILE": "/nonexistent/azure.xlsx",
            "PRICING_FILE": "/nonexistent/pricing.xlsx",
            "enable_sample_data": False,
        }

        loader = ITSMDataLoader(config=config)

        with pytest.raises(DataLoadError, match="sample data is disabled"):
            loader.load_all_data()

    @pytest.mark.skipif(True, reason="Requires actual Excel files in production environment")
    def test_load_all_data_production_files(self):
        """Test loading actual production Excel files (skip if not available)."""
        loader = ITSMDataLoader()

        # This test will only pass if production files exist
        # Otherwise it should gracefully fall back to sample data
        aws_df, azure_df, pricing_df = loader.load_all_data()

        assert len(aws_df) > 0
        assert len(azure_df) > 0


@pytest.mark.unit
class TestDataLoaderBackwardCompatibility:
    """Test backward compatibility wrapper."""

    def test_dataloader_static_method(self):
        """Test DataLoader.load_ticket_data() static method."""
        aws_df, azure_df, pricing_df = DataLoader.load_ticket_data()

        assert isinstance(aws_df, pd.DataFrame)
        assert isinstance(azure_df, pd.DataFrame)
        assert isinstance(pricing_df, pd.DataFrame)
        assert len(aws_df) > 0
        assert len(azure_df) > 0

    def test_convenience_function(self):
        """Test load_ticket_data() convenience function."""
        aws_df, azure_df, pricing_df = load_ticket_data()

        assert isinstance(aws_df, pd.DataFrame)
        assert isinstance(azure_df, pd.DataFrame)
        assert isinstance(pricing_df, pd.DataFrame)


@pytest.mark.unit
class TestResolutionHoursCalculation:
    """Test Resolution_Hours calculation matches original formula."""

    def test_resolution_hours_formula(self):
        """Test Resolution_Hours matches (Resolved - Created).total_seconds() / 3600."""
        created = datetime(2024, 1, 15, 10, 0, 0)
        resolved = datetime(2024, 1, 15, 18, 0, 0)

        # Original formula
        expected_hours = (resolved - created).total_seconds() / 3600

        # Pydantic model calculation
        ticket = AWSTicket(
            issue_key="AWS-TEST",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P1,
            summary="Test",
            created=created,
            updated=resolved,
            resolved=resolved,
        )

        assert ticket.resolution_hours == expected_hours
        assert ticket.resolution_hours == 8.0

    def test_resolution_hours_dataframe_vs_model(self, sample_aws_dataframe):
        """Test DataFrame calculation matches Pydantic model."""
        # Calculate using DataFrame (original method)
        df = sample_aws_dataframe.copy()
        df["Resolution_Hours"] = (df["Resolved"] - df["Created"]).dt.total_seconds() / 3600

        # Convert first row to Pydantic model
        first_row = df.iloc[0]
        ticket = AWSTicket.from_dataframe_row(first_row)

        # Should match
        assert ticket.resolution_hours == first_row["Resolution_Hours"]


@pytest.mark.integration
class TestProductionDataCompatibility:
    """Test compatibility with production data structures."""

    def test_dataframe_to_pydantic_conversion(self, sample_aws_dataframe):
        """Test converting entire DataFrame to Pydantic models."""
        tickets = []

        for _, row in sample_aws_dataframe.iterrows():
            ticket = AWSTicket.from_dataframe_row(row.to_dict())
            tickets.append(ticket)

        assert len(tickets) == len(sample_aws_dataframe)

        # Validate all tickets are AWSTicket instances
        assert all(isinstance(t, AWSTicket) for t in tickets)

    def test_legacy_config_compatibility(self):
        """Test legacy CONFIG dictionary format compatibility."""
        legacy_config = get_legacy_config()

        # Original CONFIG structure
        assert "AWS_FILE" in legacy_config
        assert "AZURE_FILE" in legacy_config
        assert "PRICING_FILE" in legacy_config
        assert "SLA_TARGETS" in legacy_config
        assert "THEME" in legacy_config

        # Validate SLA_TARGETS structure
        assert legacy_config["SLA_TARGETS"]["P1"] == 4
        assert legacy_config["SLA_TARGETS"]["P2"] == 8
        assert legacy_config["SLA_TARGETS"]["P3"] == 24
        assert legacy_config["SLA_TARGETS"]["P4"] == 48

    def test_legacy_design_system_compatibility(self):
        """Test legacy DESIGN_SYSTEM dictionary format compatibility."""
        design_system = get_legacy_design_system()

        assert "colors" in design_system
        assert "typography" in design_system
        assert "export" in design_system
        assert "layout" in design_system

        # Validate structure matches original DESIGN_SYSTEM
        assert "margin" in design_system["layout"]
        assert "height" in design_system["layout"]


@pytest.mark.unit
class TestSampleDataReproducibility:
    """Test sample data generation reproducibility."""

    def test_sample_data_seed_42_reproducible(self):
        """Test sample data is reproducible with seed=42."""
        loader1 = ITSMDataLoader()
        aws_df1, azure_df1, _ = loader1._generate_sample_data()

        loader2 = ITSMDataLoader()
        aws_df2, azure_df2, _ = loader2._generate_sample_data()

        # Should generate identical data
        assert len(aws_df1) == len(aws_df2)
        assert len(azure_df1) == len(azure_df2)

        # First row should be identical
        assert aws_df1.iloc[0]["Issue key"] == aws_df2.iloc[0]["Issue key"]
        assert azure_df1.iloc[0]["Issue key"] == azure_df2.iloc[0]["Issue key"]


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.performance
class TestPerformance:
    """Performance tests for Phase 1 components."""

    def test_config_instantiation_performance(self):
        """Test configuration instantiation is fast."""
        import time

        start = time.time()

        for _ in range(100):
            config = ITSMConfig()

        elapsed = time.time() - start

        # Should create 100 configs in less than 1 second
        assert elapsed < 1.0

    def test_ticket_creation_performance(self):
        """Test ticket creation performance."""
        import time

        start = time.time()

        for i in range(1000):
            ticket = AWSTicket(
                issue_key=f"AWS-{i:05d}",
                issue_type=TicketType.INCIDENT,
                status=TicketStatus.OPEN,
                priority=TicketPriority.P1,
                summary="Performance test ticket",
                created=datetime.now(),
                updated=datetime.now(),
            )

        elapsed = time.time() - start

        # Should create 1000 tickets in less than 1 second
        assert elapsed < 1.0

    def test_sample_data_generation_performance(self):
        """Test sample data generation performance."""
        import time

        loader = ITSMDataLoader()

        start = time.time()
        aws_df, azure_df, pricing_df = loader._generate_sample_data()
        elapsed = time.time() - start

        # Should generate 2997 tickets + pricing data in less than 5 seconds
        assert elapsed < 5.0


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_ticket_with_very_long_summary(self):
        """Test ticket creation with very long summary."""
        long_summary = "X" * 10000

        ticket = AWSTicket(
            issue_key="AWS-LONG",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary=long_summary,
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert len(ticket.summary) == 10000

    def test_ticket_collection_sla_compliance_no_resolved_tickets(self):
        """Test SLA compliance with no resolved tickets."""
        open_ticket = AWSTicket(
            issue_key="AWS-OPEN",
            issue_type=TicketType.INCIDENT,
            status=TicketStatus.OPEN,
            priority=TicketPriority.P1,
            summary="Open ticket",
            created=datetime.now(),
            updated=datetime.now(),
        )

        collection = TicketCollection(aws_tickets=[open_ticket], azure_tickets=[])

        compliance = collection.calculate_sla_compliance()

        # Should return 100% compliance for priorities with no resolved tickets
        assert compliance["overall"] == 100.0

    def test_zero_resolution_time(self):
        """Test ticket resolved instantly (0 hours)."""
        timestamp = datetime(2024, 1, 15, 10, 0, 0)

        ticket = AWSTicket(
            issue_key="AWS-INSTANT",
            issue_type=TicketType.SERVICE_REQUEST,
            status=TicketStatus.RESOLVED,
            priority=TicketPriority.P4,
            summary="Instant resolution",
            created=timestamp,
            updated=timestamp,
            resolved=timestamp,
        )

        assert ticket.resolution_hours == 0.0
        assert ticket.calculate_sla_compliance() is True  # 0 hours is within any SLA


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
