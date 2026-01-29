"""
Markdown Export Service Pattern.

GitHub-flavored markdown exporter for DataFrames and structured data.
Supports metadata, decision frameworks, cost breakdowns.

Pattern extracted from: vpce_cleanup_manager.py (generate_markdown_table)
Reusable for: All markdown export operations across runbooks modules
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from runbooks.common.rich_utils import print_success, print_info


@dataclass
class MarkdownExportResult:
    """Markdown export result."""

    file_path: str
    file_size: int
    row_count: int
    format: str
    timestamp: str


class MarkdownExporter(ABC):
    """
    GitHub-flavored markdown exporter.

    Converts DataFrames and structured data to markdown tables.
    Supports metadata, decision frameworks, cost breakdowns.

    Usage:
        class MyManager(MarkdownExporter):
            def _get_data_for_export(self):
                return pd.DataFrame([...])

        manager = MyManager()
        result = manager.export_to_markdown(
            output_dir=Path("data/outputs"),
            title="Analysis Results"
        )

    Pattern Benefits:
    - GitHub-flavored markdown compliance
    - Metadata support (timestamps, row counts)
    - DataFrame conversion
    - Custom filename support
    - UTF-8 encoding
    - Rich CLI feedback
    """

    @abstractmethod
    def _get_data_for_export(self) -> pd.DataFrame:
        """
        Return data to export as DataFrame.

        Returns:
            pandas DataFrame with data to export
        """
        pass

    def export_to_markdown(
        self,
        output_dir: Path,
        title: str = "Export",
        include_metadata: bool = True,
        filename: Optional[str] = None,
        additional_sections: Optional[Dict[str, Any]] = None,
    ) -> MarkdownExportResult:
        """
        Export data to GitHub-flavored markdown.

        Args:
            output_dir: Output directory for markdown file
            title: Document title
            include_metadata: Include timestamp and row count metadata
            filename: Custom filename (auto-generated if None)
            additional_sections: Additional sections to include (key=title, value=content)

        Returns:
            MarkdownExportResult with file path and statistics
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        df = self._get_data_for_export()

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{title.lower().replace(' ', '-')}-{timestamp}.md"

        file_path = output_dir / filename

        # Build markdown content
        lines = []
        lines.append(f"# {title}\n")

        if include_metadata:
            lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"**Rows:** {len(df)}")
            lines.append(f"**Columns:** {len(df.columns)}\n")

        # Add additional sections if provided
        if additional_sections:
            for section_title, section_content in additional_sections.items():
                lines.append(f"## {section_title}\n")
                if isinstance(section_content, str):
                    lines.append(section_content)
                elif isinstance(section_content, list):
                    for item in section_content:
                        lines.append(f"- {item}")
                elif isinstance(section_content, dict):
                    for key, value in section_content.items():
                        lines.append(f"**{key}:** {value}")
                lines.append("")

        # Add main data table
        lines.append("## Data\n")
        lines.append(self._dataframe_to_markdown(df))

        # Write to file
        content = "\n".join(lines)
        file_path.write_text(content, encoding="utf-8")

        print_success(f"✅ Markdown exported: {file_path}")
        print_info(f"   Size: {file_path.stat().st_size:,} bytes")
        print_info(f"   Rows: {len(df):,}")

        return MarkdownExportResult(
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            row_count=len(df),
            format="github",
            timestamp=datetime.now().isoformat(),
        )

    def _dataframe_to_markdown(self, df: pd.DataFrame) -> str:
        """
        Convert DataFrame to GitHub-flavored markdown table.

        Args:
            df: DataFrame to convert

        Returns:
            Markdown table string
        """
        if df.empty:
            return "_No data available_\n"

        # Header row
        columns = df.columns.tolist()
        header = "| " + " | ".join(columns) + " |"

        # Separator row with alignment
        separator = "| " + " | ".join(["-" * max(len(col), 3) for col in columns]) + " |"

        # Data rows
        data_rows = []
        for _, row in df.iterrows():
            row_values = [self._format_cell_value(row[col]) for col in columns]
            data_rows.append("| " + " | ".join(row_values) + " |")

        # Combine
        table_lines = [header, separator] + data_rows
        return "\n".join(table_lines) + "\n"

    def _format_cell_value(self, value: Any) -> str:
        """
        Format cell value for markdown table.

        Args:
            value: Cell value to format

        Returns:
            Formatted string value
        """
        if pd.isna(value):
            return ""
        elif isinstance(value, float):
            # Format floats with 2 decimal places
            return f"{value:.2f}"
        elif isinstance(value, (list, tuple)):
            # Join lists with commas
            return ", ".join(str(v) for v in value)
        else:
            # Convert to string and escape pipe characters
            return str(value).replace("|", "\\|")

    def export_summary_with_details(
        self,
        output_dir: Path,
        summary_data: Dict[str, Any],
        details_df: pd.DataFrame,
        title: str = "Summary Report",
        filename: Optional[str] = None,
    ) -> MarkdownExportResult:
        """
        Export summary statistics with detailed data table.

        Args:
            output_dir: Output directory
            summary_data: Summary statistics as dict
            details_df: Detailed data as DataFrame
            title: Document title
            filename: Custom filename

        Returns:
            MarkdownExportResult
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{title.lower().replace(' ', '-')}-{timestamp}.md"

        file_path = output_dir / filename

        lines = []
        lines.append(f"# {title}\n")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary section
        lines.append("## Summary\n")
        for key, value in summary_data.items():
            lines.append(f"**{key}:** {value}")
        lines.append("")

        # Details section
        lines.append("## Details\n")
        lines.append(self._dataframe_to_markdown(details_df))

        content = "\n".join(lines)
        file_path.write_text(content, encoding="utf-8")

        print_success(f"✅ Summary report exported: {file_path}")

        return MarkdownExportResult(
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            row_count=len(details_df),
            format="github",
            timestamp=datetime.now().isoformat(),
        )
