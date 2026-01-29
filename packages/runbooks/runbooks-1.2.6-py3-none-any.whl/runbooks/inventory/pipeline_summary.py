#!/usr/bin/env python3
"""
Pipeline Summary Module - 5-Layer Enrichment Progress Reporting

This module extracts the inline Python HEREDOC from Taskfile.inventory.yaml (lines 232-254)
into a proper testable module with CLI interface. Provides comprehensive reporting for
the 5-layer enrichment pipeline:

Layer 1: Discovery (resource collection)
Layer 2: Organizations (account metadata enrichment)
Layer 3: Costs (pricing data enrichment)
Layer 4: Activity (usage metrics enrichment)
Layer 5: Scoring (decommission tier calculation)

Extracted for:
- pytest testability (inline HEREDOC cannot be tested)
- ruff linting compatibility (inline code bypasses quality checks)
- proper module organization (KISS principle)
- CLI integration (consistent command interface)

Author: Runbooks Team
Version: 1.1.20+
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import pandas as pd

from runbooks.common.rich_utils import (
    console,
    create_table,
    print_error,
    print_success,
    print_info,
)


class PipelineSummaryReporter:
    """
    5-Layer Pipeline Summary Reporter for enrichment progress validation.

    Provides comprehensive reporting for multi-layer enrichment workflows,
    validating file existence, row/column counts, and pipeline completion status.
    """

    def __init__(self, resource_type: str = "ec2", output_dir: str = "data/outputs"):
        """
        Initialize pipeline summary reporter.

        Args:
            resource_type: Resource type (ec2, workspaces, rds, lambda, snapshots)
            output_dir: Output directory containing enrichment layer files
        """
        self.resource_type = resource_type
        self.output_dir = Path(output_dir)

        # Define 5-layer pipeline file structure
        self.layer_files: List[Tuple[str, str]] = [
            (f"{resource_type}-discovered.csv", "Layer 1 Discovery"),
            (f"{resource_type}-org.csv", "Layer 2 Organizations"),
            (f"{resource_type}-cost.csv", "Layer 3 Costs"),
            (f"{resource_type}-activity.csv", "Layer 4 Activity"),
            (f"{resource_type}-scored.csv", "Layer 5 Scored"),
        ]

    def generate_summary_table(self) -> Dict[str, any]:
        """
        Generate pipeline execution summary with file validation.

        Returns:
            Dictionary containing:
                - layers: List of layer summaries with row/column counts
                - total_layers: Total number of layers
                - completed_layers: Number of successfully completed layers
                - missing_layers: List of missing layer files
        """
        layers = []
        completed_count = 0
        missing_layers = []

        for filename, label in self.layer_files:
            filepath = self.output_dir / filename

            if filepath.exists():
                try:
                    df = pd.read_csv(filepath)
                    layer_info = {
                        "label": label,
                        "filename": filename,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "status": "✅",
                        "exists": True,
                    }
                    completed_count += 1
                except Exception as e:
                    layer_info = {
                        "label": label,
                        "filename": filename,
                        "rows": "ERROR",
                        "columns": "ERROR",
                        "status": "❌",
                        "exists": True,
                        "error": str(e),
                    }
                    missing_layers.append(filename)
            else:
                layer_info = {
                    "label": label,
                    "filename": filename,
                    "rows": "N/A",
                    "columns": "N/A",
                    "status": "❌",
                    "exists": False,
                }
                missing_layers.append(filename)

            layers.append(layer_info)

        return {
            "layers": layers,
            "total_layers": len(self.layer_files),
            "completed_layers": completed_count,
            "missing_layers": missing_layers,
            "resource_type": self.resource_type,
            "output_dir": str(self.output_dir),
        }

    def display_table_format(self) -> None:
        """
        Display pipeline summary in Rich table format (default CLI output).

        Provides byte-identical output to original HEREDOC for backward compatibility.
        """
        summary = self.generate_summary_table()

        # Header (matches original HEREDOC format exactly)
        print(f"\n{'Layer':<30} | {'Rows':>5} | {'Cols':>4} | Status")
        print("-" * 65)

        # Layer rows (matches original format)
        for layer in summary["layers"]:
            label = layer["label"]
            rows = str(layer["rows"]) if layer["rows"] != "N/A" else "N/A"
            cols = str(layer["columns"]) if layer["columns"] != "N/A" else "N/A"
            status = layer["status"]

            print(f"{label:<30} | {rows:>5} | {cols:>4} | {status}")

        # Footer (matches original)
        print("\n✅ Pipeline execution complete!")

    def display_rich_format(self) -> None:
        """
        Display pipeline summary using Rich table with enhanced formatting.

        Provides professional table output with color coding and better readability.
        """
        summary = self.generate_summary_table()

        # Create Rich table
        table = create_table(
            title=f"📊 Pipeline Summary: {self.resource_type.upper()}",
            caption=f"Output Directory: {summary['output_dir']}",
        )

        table.add_column("Layer", style="bold cyan", no_wrap=True)
        table.add_column("Rows", justify="right", style="white")
        table.add_column("Columns", justify="right", style="white")
        table.add_column("Status", justify="center", style="white")

        for layer in summary["layers"]:
            # Color code based on status
            row_style = "green" if layer["status"] == "✅" else "red"

            rows_display = str(layer["rows"])
            cols_display = str(layer["columns"])

            table.add_row(
                layer["label"],
                f"[{row_style}]{rows_display}[/{row_style}]",
                f"[{row_style}]{cols_display}[/{row_style}]",
                layer["status"],
            )

        console.print(table)

        # Summary footer
        completion_pct = (
            (summary["completed_layers"] / summary["total_layers"]) * 100 if summary["total_layers"] > 0 else 0
        )

        if completion_pct == 100:
            print_success(
                f"Pipeline {completion_pct:.0f}% complete ({summary['completed_layers']}/{summary['total_layers']} layers)"
            )
        elif completion_pct > 0:
            print_info(
                f"Pipeline {completion_pct:.0f}% complete ({summary['completed_layers']}/{summary['total_layers']} layers)"
            )
        else:
            print_error("Pipeline 0% complete - no layers found")

    def export_json(self, output_file: Optional[str] = None) -> str:
        """
        Export pipeline summary as JSON.

        Args:
            output_file: Optional JSON file path to write

        Returns:
            JSON string representation
        """
        import json

        summary = self.generate_summary_table()

        json_output = json.dumps(summary, indent=2, ensure_ascii=False)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_output)
            print_success(f"JSON summary saved to: {output_file}")

        return json_output

    def export_csv(self, output_file: Optional[str] = None) -> str:
        """
        Export pipeline summary as CSV.

        Args:
            output_file: Optional CSV file path to write

        Returns:
            CSV string representation
        """
        import csv
        from io import StringIO

        summary = self.generate_summary_table()

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Layer", "Filename", "Rows", "Columns", "Status"])

        # Data rows
        for layer in summary["layers"]:
            writer.writerow(
                [
                    layer["label"],
                    layer["filename"],
                    layer["rows"],
                    layer["columns"],
                    layer["status"],
                ]
            )

        csv_output = output.getvalue()

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(csv_output)
            print_success(f"CSV summary saved to: {output_file}")

        return csv_output


@click.command()
@click.option(
    "--resource-type",
    default="ec2",
    help="Resource type (ec2, workspaces, rds, lambda, snapshots)",
    show_default=True,
)
@click.option(
    "--output-dir",
    default="data/outputs",
    help="Output directory containing enrichment files",
    show_default=True,
)
@click.option(
    "--format",
    type=click.Choice(["table", "rich", "csv", "json"], case_sensitive=False),
    default="table",
    help="Output format (table=backward compatible, rich=enhanced)",
    show_default=True,
)
@click.option(
    "--output-file",
    type=click.Path(),
    default=None,
    help="File path to save output (for csv/json formats)",
)
def pipeline_summary(resource_type: str, output_dir: str, format: str, output_file: Optional[str]):
    """
    Display 5-layer pipeline execution summary.

    Validates enrichment pipeline completion across 5 layers:

    \b
    Layer 1: Discovery (resource collection)
    Layer 2: Organizations (account metadata)
    Layer 3: Costs (pricing data)
    Layer 4: Activity (usage metrics)
    Layer 5: Scoring (decommission tiers)

    Examples:

    \b
    # Default table format (backward compatible with HEREDOC)
    $ runbooks inventory pipeline-summary --resource-type ec2

    \b
    # Enhanced Rich table format
    $ runbooks inventory pipeline-summary --resource-type workspaces --format rich

    \b
    # Export to JSON
    $ runbooks inventory pipeline-summary --resource-type rds --format json --output-file summary.json

    \b
    # Export to CSV
    $ runbooks inventory pipeline-summary --resource-type lambda --format csv --output-file summary.csv
    """
    reporter = PipelineSummaryReporter(resource_type, output_dir)

    try:
        if format == "table":
            # Backward compatible plain text format (byte-identical to HEREDOC)
            reporter.display_table_format()
        elif format == "rich":
            # Enhanced Rich table format
            reporter.display_rich_format()
        elif format == "json":
            # JSON export
            reporter.export_json(output_file)
        elif format == "csv":
            # CSV export
            reporter.export_csv(output_file)
        else:
            print_error(f"Unsupported format: {format}")
            sys.exit(1)

    except Exception as e:
        print_error(f"Pipeline summary failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    pipeline_summary()
