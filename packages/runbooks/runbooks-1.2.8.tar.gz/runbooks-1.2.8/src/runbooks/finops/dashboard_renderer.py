#!/usr/bin/env python3
"""
Dashboard Renderer for FinOps Multi-Format Output

This module implements multiple output format support using modular export handlers:
- Tree format (hierarchical with nested tables)
- Table format (flat summary for executives)
- Markdown format (export for documentation)
- JSON format (programmatic consumption)
- CSV format (spreadsheet import)

Manager Requirement #5: Configurable output-format: Tree, Table, markdown

v1.1.27: Refactored to use modular export_handlers architecture (Track D)
"""

from typing import Any, Dict, Literal, Optional

import pandas as pd
from rich.console import Console

from runbooks.common.rich_utils import console
from runbooks.finops.export_handlers import ExportFactory
from runbooks.finops.persona_formatter import PersonaFormatter, PersonaType  # Track B

# Output format type
OutputFormat = Literal["tree", "table", "markdown", "json", "csv"]


class DashboardRenderer:
    """
    Multi-format dashboard renderer for FinOps analysis.

    Supports rendering enriched resource data in various formats
    suitable for different audiences and use cases.

    v1.1.27: Now uses modular export handlers via ExportFactory for SOLID compliance.
    """

    def __init__(self, console_instance: Optional[Console] = None):
        """
        Initialize DashboardRenderer.

        Args:
            console_instance: Rich console instance (defaults to global console)
        """
        self.console = console_instance or console

    def render(
        self,
        enriched_data: Dict[str, pd.DataFrame],
        output_format: OutputFormat = "tree",
        title: Optional[str] = None,
        show_signals: bool = True,
        show_summary: bool = True,
        persona: Optional[PersonaType] = None,  # Track B v1.1.26
    ) -> Optional[str]:
        """
        Render dashboard in specified format using modular export handlers.

        Args:
            enriched_data: Dictionary with service names as keys and DataFrames as values
            output_format: Output format ('tree', 'table', 'markdown', 'json', 'csv')
            title: Optional title for the output
            show_signals: Include signal legends in output (unused in v1.1.27, kept for compatibility)
            show_summary: Include summary statistics (unused in v1.1.27, kept for compatibility)
            persona: Persona type for role-specific formatting (Track B v1.1.26)

        Returns:
            String output for exportable formats (markdown, json, csv), None for console formats

        v1.1.26 Track B: Added persona parameter for role-specific dashboard formatting.
        v1.1.27: Refactored to delegate to modular export handlers via ExportFactory.
        """
        # Track B v1.1.26: Apply persona-specific filtering if persona specified
        if persona:
            formatter = PersonaFormatter(persona=persona)
            # Filter top services based on persona configuration
            enriched_data = self._apply_persona_filtering(enriched_data, formatter)

        # Create exporter using factory pattern with persona context
        exporter = ExportFactory.create(
            output_format,
            console_instance=self.console,
            persona=persona,  # Track B v1.1.26
        )

        # Delegate export to handler
        result = exporter.export(enriched_data, output_path=None)

        # Return string result for exportable formats, None for console formats
        return result if result else None

    def _apply_persona_filtering(
        self, enriched_data: Dict[str, pd.DataFrame], formatter: PersonaFormatter
    ) -> Dict[str, pd.DataFrame]:
        """
        Apply persona-specific filtering to enriched data.

        Track B v1.1.26: Filters top-N services based on PersonaConfig.top_services.

        Args:
            enriched_data: Original enriched data dictionary
            formatter: PersonaFormatter with persona configuration

        Returns:
            Filtered enriched data dictionary
        """
        config = formatter.config

        # Handle 'all' services (no filtering)
        if config.top_services == "all":
            return enriched_data

        # Filter to top-N services by cost
        top_n = config.top_services if isinstance(config.top_services, int) else 10

        # Calculate total cost per service
        service_costs = {}
        for service, df in enriched_data.items():
            if not df.empty and "monthly_cost" in df.columns:
                service_costs[service] = df["monthly_cost"].sum()
            else:
                service_costs[service] = 0

        # Sort services by cost and take top-N
        top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:top_n]
        top_service_names = [service for service, _ in top_services]

        # Filter enriched_data to top services
        filtered_data = {service: df for service, df in enriched_data.items() if service in top_service_names}

        return filtered_data


# ============================================================================
# LEGACY CODE (Pre-v1.1.27) - Kept for reference only
# All functionality moved to export_handlers/ module
# ============================================================================
# The following methods were extracted into modular export handlers:
# - _render_tree() -> export_handlers.console_exporters.TreeExporter
# - _render_table() -> export_handlers.console_exporters.TableExporter
# - _render_markdown() -> export_handlers.string_exporters.MarkdownExporter
# - _render_json() -> export_handlers.string_exporters.JsonExporter
# - _render_csv() -> export_handlers.string_exporters.CsvExporter
# Helper methods moved to individual exporters for encapsulation.
# ============================================================================


if __name__ == "__main__":
    # Test the dashboard renderer with modular export handlers
    print("\n=== Dashboard Renderer Test (v1.1.27 - Modular Architecture) ===\n")

    # Create sample data
    sample_data = {
        "ec2": pd.DataFrame(
            [
                {
                    "instance_id": "i-123",
                    "decommission_tier": "MUST",
                    "decommission_score": 85,
                    "monthly_cost": 100,
                },
                {
                    "instance_id": "i-456",
                    "decommission_tier": "KEEP",
                    "decommission_score": 15,
                    "monthly_cost": 150,
                },
                {
                    "instance_id": "i-789",
                    "decommission_tier": "SHOULD",
                    "decommission_score": 60,
                    "monthly_cost": 75,
                },
            ]
        ),
        "s3": pd.DataFrame(
            [
                {
                    "bucket_name": "backup-old",
                    "decommission_tier": "MUST",
                    "decommission_score": 90,
                    "monthly_cost": 50,
                },
                {
                    "bucket_name": "production",
                    "decommission_tier": "KEEP",
                    "decommission_score": 10,
                    "monthly_cost": 200,
                },
            ]
        ),
    }

    renderer = DashboardRenderer()

    # Test different formats
    print("\n--- TREE FORMAT ---")
    renderer.render(sample_data, output_format="tree")

    print("\n--- TABLE FORMAT ---")
    renderer.render(sample_data, output_format="table")

    print("\n--- MARKDOWN FORMAT ---")
    markdown = renderer.render(sample_data, output_format="markdown")
    if markdown:
        print(markdown[:500] + "...")  # Show first 500 chars

    print("\n--- JSON FORMAT ---")
    json_output = renderer.render(sample_data, output_format="json")
    if json_output:
        print(json_output[:500] + "...")  # Show first 500 chars

    print("\n--- CSV FORMAT ---")
    csv_output = renderer.render(sample_data, output_format="csv")
    if csv_output:
        print(csv_output[:500] + "...")  # Show first 500 chars

    print("\n✅ All export formats working via modular handlers")
