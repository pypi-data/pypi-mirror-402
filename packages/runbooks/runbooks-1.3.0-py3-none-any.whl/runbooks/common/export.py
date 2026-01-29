#!/usr/bin/env python3
"""
Enterprise Export Engine Utility

Multi-format export engine for enhanced audit reporting and data analysis.
Extracted from finops/dashboard_runner.py for KISS/DRY/LEAN architecture.

Key Features:
- JSON export for audit trails and programmatic access
- CSV export for Excel analysis and data manipulation
- PDF export for board presentations and stakeholder reporting
- Automatic file naming with timestamps
- Directory management with parent creation
- Graceful error handling with detailed logging

Author: Runbooks Team
Version: 1.0.0
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from runbooks.common.rich_utils import console


def export_to_formats(
    data: Dict[str, Any],
    base_filename: str,
    formats: Optional[List[str]] = None,
    export_dir: Optional[Path] = None,
    output_file: Optional[str] = None,
    console_obj: Optional[Any] = None,
) -> Dict[str, Path]:
    """
    Export analysis results to multiple formats (JSON, CSV, PDF).

    Provides flexible multi-format export with automatic timestamp inclusion
    and directory management. Ideal for audit trails, Excel analysis, and
    stakeholder presentations.

    Args:
        data: Analysis results dictionary to export
            For CSV: Should contain 'profiles' key with list of profile dicts
            For JSON/PDF: Any dict structure is supported
        base_filename: Base filename without extension or timestamp
            Example: 'audit-report' becomes 'audit-report_20240101_120000.json'
        formats: List of export formats (default: ['json', 'csv', 'pdf'])
            Supported: 'json', 'csv', 'pdf'
        export_dir: Output directory path (default: 'artifacts/finops-exports')
            Created automatically if doesn't exist

    Returns:
        Dict mapping format name to exported file Path
        Example: {'json': Path('.../.json'), 'csv': Path('.../.csv')}

    File Formats:
        - JSON: Complete data structure with indentation
        - CSV: Flattened profile data (requires 'profiles' key in data)
        - PDF: Not implemented in base module (placeholder)

    Example:
        >>> data = {
        ...     'profiles': [
        ...         {'profile': 'prod', 'account_id': '123', 'total_cost': 1000},
        ...         {'profile': 'dev', 'account_id': '456', 'total_cost': 500},
        ...     ],
        ...     'summary': {'total': 1500}
        ... }
        >>> files = export_to_formats(
        ...     data=data,
        ...     base_filename='cost-analysis',
        ...     formats=['json', 'csv']
        ... )
        >>> print(f"Exported to: {files['json']}")
    """
    if formats is None:
        formats = ["json", "csv", "pdf"]

    if export_dir is None:
        export_dir = Path("artifacts/finops-exports")

    # Use provided console or fall back to module-level console
    active_console = console_obj if console_obj is not None else console

    # Create export directory if it doesn't exist
    export_dir.mkdir(parents=True, exist_ok=True)

    exported_files = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON Export
    if "json" in formats:
        json_path = export_dir / f"{base_filename}_{timestamp}.json"
        try:
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            exported_files["json"] = json_path
            console.log(f"[green]✅ JSON export: {json_path}[/]")
        except Exception as e:
            console.log(f"[red]❌ JSON export failed: {str(e)[:50]}[/]")

    # CSV Export (flattened data)
    if "csv" in formats:
        csv_path = export_dir / f"{base_filename}_{timestamp}.csv"
        try:
            if isinstance(data, dict) and "profiles" in data:
                _export_profiles_to_csv(data["profiles"], csv_path)
                exported_files["csv"] = csv_path
                console.log(f"[green]✅ CSV export: {csv_path}[/]")
            else:
                console.log("[yellow]⚠️ CSV export requires 'profiles' key in data[/]")
        except Exception as e:
            console.log(f"[red]❌ CSV export failed: {str(e)[:50]}[/]")

    # PDF Export (placeholder - implement in future)
    if "pdf" in formats:
        active_console.log("[yellow]ℹ️  PDF export not yet implemented in base module[/]")

    # HTML Export (requires console recording)
    if "html" in formats:
        try:
            from runbooks.common.rich_utils import export_console_html
            from runbooks import __version__
            import os

            # Determine output path
            if output_file:
                html_path = Path(output_file)
            else:
                html_filename = f"{base_filename}_{timestamp}.html"
                html_path = export_dir / html_filename

            # Ensure parent directory exists
            html_path.parent.mkdir(parents=True, exist_ok=True)

            # Check if console has recording enabled
            if hasattr(active_console, "_record_buffer") and active_console._record_buffer is not None:
                # Export with metadata
                metadata = {"timestamp": datetime.now().isoformat(), "version": __version__, "filename": base_filename}

                html_result = export_console_html(active_console, str(html_path), metadata=metadata)

                if html_result:
                    # File size reporting
                    file_size = os.path.getsize(html_path) if html_path.exists() else 0
                    file_size_mb = file_size / (1024 * 1024)
                    if file_size_mb >= 1:
                        size_str = f"{file_size_mb:.1f} MB"
                    else:
                        size_str = f"{file_size / 1024:.1f} KB"

                    exported_files["html"] = html_path
                    active_console.log(f"[bright_green]✅ HTML export: {html_path} ({size_str})[/]")
                else:
                    active_console.log("[yellow]⚠️  HTML export failed[/]")
            else:
                active_console.log("[yellow]⚠️  HTML export requires console recording (Console(record=True))[/]")
        except Exception as e:
            active_console.log(f"[red]❌ HTML export failed: {str(e)[:50]}[/]")

    # Markdown Export
    if "markdown" in formats:
        try:
            # Markdown export for data dict
            md_path = export_dir / f"{base_filename}_{timestamp}.md"

            with open(md_path, "w") as f:
                # Write markdown header
                f.write(f"# {base_filename.replace('_', ' ').title()}\n\n")
                f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")

                # Write data summary
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == "services" and isinstance(value, dict):
                            # Service costs table
                            f.write("## Service Costs\n\n")
                            f.write("| Service | Cost |\n")
                            f.write("|---------|------|\n")
                            for service, cost in value.items():
                                f.write(f"| {service} | ${cost:,.2f} |\n")
                            f.write("\n")
                        elif isinstance(value, (int, float, str)):
                            f.write(f"**{key.replace('_', ' ').title()}**: {value}\n\n")

            # File size reporting
            file_size = md_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            if file_size_mb >= 1:
                size_str = f"{file_size_mb:.1f} MB"
            else:
                size_str = f"{file_size / 1024:.1f} KB"

            exported_files["markdown"] = md_path
            active_console.log(f"[bright_green]✅ Markdown export: {md_path} ({size_str})[/]")
            active_console.log("[cyan]📋 Ready for GitHub/MkDocs documentation sharing[/]")
        except Exception as e:
            active_console.log(f"[red]❌ Markdown export failed: {str(e)[:50]}[/]")

    return exported_files


def _export_profiles_to_csv(profiles_data: List[Dict], csv_path: Path) -> None:
    """
    Export profiles data to CSV format.

    Internal helper function for CSV export. Extracts standard fields
    from profile dictionaries and writes to CSV with headers.

    Args:
        profiles_data: List of profile dictionaries
        csv_path: Output CSV file path

    CSV Columns:
        - profile: Profile name
        - account_id: AWS account ID
        - total_cost: Total cost value
        - top_service: Highest cost service name
        - service_cost: Cost of top service
    """
    if not profiles_data:
        return

    with open(csv_path, "w", newline="") as csvfile:
        fieldnames = ["profile", "account_id", "total_cost", "top_service", "service_cost"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for profile_data in profiles_data:
            if isinstance(profile_data, dict):
                writer.writerow(
                    {
                        "profile": profile_data.get("profile", "Unknown"),
                        "account_id": profile_data.get("account_id", "Unknown"),
                        "total_cost": profile_data.get("total_cost", 0),
                        "top_service": profile_data.get("top_service", "Unknown"),
                        "service_cost": profile_data.get("service_cost", 0),
                    }
                )


class ExportEngine:
    """
    Export engine for enhanced audit reporting with persistent configuration.

    Provides object-oriented interface for multi-format exports with
    reusable export directory settings.

    Attributes:
        export_dir: Default export directory for all operations

    Example:
        >>> engine = ExportEngine(export_dir=Path("reports"))
        >>> files = engine.export(
        ...     data={'profiles': [...]},
        ...     base_filename='audit-2024',
        ...     formats=['json', 'csv']
        ... )
    """

    def __init__(self, export_dir: Optional[Path] = None):
        """
        Initialize export engine with default export directory.

        Args:
            export_dir: Default output directory (default: 'artifacts/finops-exports')
                Created automatically if doesn't exist
        """
        self.export_dir = export_dir or Path("artifacts/finops-exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        data: Dict[str, Any],
        base_filename: str,
        formats: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """
        Export data to multiple formats using configured directory.

        Args:
            data: Analysis results dictionary to export
            base_filename: Base filename without extension or timestamp
            formats: List of export formats (default: ['json', 'csv', 'pdf'])

        Returns:
            Dict mapping format name to exported file Path

        See Also:
            export_to_formats: Module-level function with detailed documentation
        """
        return export_to_formats(
            data=data,
            base_filename=base_filename,
            formats=formats,
            export_dir=self.export_dir,
        )


class DataFrameExporter:
    """DataFrame export utilities consolidating 8 duplicate implementations.

    Provides standardized DataFrame export across CSV, JSON, HTML, and Excel
    formats with SHA256 verification and Rich CLI logging.

    Strategic Achievement: DRY principle for DataFrame export operations
    Business Impact: Consistent data export format across all FinOps modules
    Technical Foundation: Pandas-based multi-format export with verification

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'service': ['EC2', 'RDS'], 'cost': [100.50, 200.75]})
        >>> DataFrameExporter.to_csv(df, '/tmp/costs.csv')
        >>> exports = DataFrameExporter.export_multi_format(
        ...     df, 'analysis', formats=['csv', 'json']
        ... )
    """

    @staticmethod
    def to_csv(df: Any, output_path: Any, **kwargs) -> Path:
        """Export DataFrame to CSV with SHA256 verification.

        Args:
            df: pandas DataFrame
            output_path: Output file path (str or Path)
            **kwargs: Additional pd.DataFrame.to_csv() parameters

        Returns:
            Path to exported CSV file

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            >>> csv_path = DataFrameExporter.to_csv(df, '/tmp/data.csv')
        """
        import hashlib

        import pandas as pd

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Set default parameters
        kwargs.setdefault("index", False)

        # Export to CSV
        df.to_csv(output_path, **kwargs)

        # Generate SHA256 checksum
        sha256_hash = hashlib.sha256()
        with open(output_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        console.log(f"[green]✅ CSV export: {output_path} (SHA256: {checksum[:16]}...)[/]")

        return output_path

    @staticmethod
    def to_json(df: Any, output_path: Any, orient: str = "records", **kwargs) -> Path:
        """Export DataFrame to JSON with SHA256 verification.

        Args:
            df: pandas DataFrame
            output_path: Output file path (str or Path)
            orient: JSON orientation ('records', 'index', 'columns', 'values')
            **kwargs: Additional pd.DataFrame.to_json() parameters

        Returns:
            Path to exported JSON file

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            >>> json_path = DataFrameExporter.to_json(df, '/tmp/data.json')
        """
        import hashlib

        import pandas as pd

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Set default parameters
        kwargs.setdefault("indent", 2)
        kwargs.setdefault("date_format", "iso")

        # Export to JSON
        df.to_json(output_path, orient=orient, **kwargs)

        # Generate SHA256 checksum
        sha256_hash = hashlib.sha256()
        with open(output_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        console.log(f"[green]✅ JSON export: {output_path} (SHA256: {checksum[:16]}...)[/]")

        return output_path

    @staticmethod
    def to_html(df: Any, output_path: Any, **kwargs) -> Path:
        """Export DataFrame to HTML table with Rich-style CSS.

        Args:
            df: pandas DataFrame
            output_path: Output file path (str or Path)
            **kwargs: Additional pd.DataFrame.to_html() parameters

        Returns:
            Path to exported HTML file

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            >>> html_path = DataFrameExporter.to_html(df, '/tmp/data.html')
        """
        import pandas as pd

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Set default parameters with Rich-style CSS
        kwargs.setdefault("index", False)
        kwargs.setdefault("border", 0)
        kwargs.setdefault(
            "classes",
            ["table", "table-striped", "table-hover"],
        )

        # Generate HTML with Rich-inspired styling
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DataFrame Export</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            background-color: #252526;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        th {{
            background-color: #3c3c3c;
            color: #4ec9b0;
            font-weight: bold;
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #4ec9b0;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #3c3c3c;
        }}
        tr:hover {{
            background-color: #2a2a2a;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
{df.to_html(**kwargs)}
</body>
</html>"""

        # Write HTML file
        with open(output_path, "w") as f:
            f.write(html_content)

        console.log(f"[green]✅ HTML export: {output_path}[/]")

        return output_path

    @staticmethod
    def to_excel(df: Any, output_path: Any, sheet_name: str = "Sheet1", **kwargs) -> Path:
        """Export DataFrame to Excel with formatting.

        Args:
            df: pandas DataFrame
            output_path: Output file path (str or Path)
            sheet_name: Excel sheet name (default: 'Sheet1')
            **kwargs: Additional pd.DataFrame.to_excel() parameters

        Returns:
            Path to exported Excel file

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
            >>> excel_path = DataFrameExporter.to_excel(df, '/tmp/data.xlsx')
        """
        import pandas as pd

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Set default parameters
        kwargs.setdefault("index", False)
        kwargs.setdefault("sheet_name", sheet_name)

        # Export to Excel
        df.to_excel(output_path, **kwargs)

        console.log(f"[green]✅ Excel export: {output_path}[/]")

        return output_path

    @staticmethod
    def export_multi_format(
        df: Any,
        base_filename: str,
        formats: Optional[List[str]] = None,
        output_dir: Any = "/tmp",
    ) -> Dict[str, Path]:
        """Export DataFrame to multiple formats.

        Args:
            df: pandas DataFrame
            base_filename: Base filename (without extension)
            formats: List of formats ('csv', 'json', 'html', 'excel')
            output_dir: Output directory (str or Path)

        Returns:
            Dict mapping format to output file path

        Example:
            >>> import pandas as pd
            >>> df = pd.DataFrame({'service': ['EC2', 'RDS'], 'cost': [100, 200]})
            >>> exports = DataFrameExporter.export_multi_format(
            ...     df, 'costs', formats=['csv', 'json'], output_dir='/tmp'
            ... )
            >>> exports
            {'csv': Path('/tmp/costs.csv'), 'json': Path('/tmp/costs.json')}
        """
        if formats is None:
            formats = ["csv", "json", "html"]

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = {}

        if "csv" in formats:
            csv_path = output_dir / f"{base_filename}.csv"
            exported_files["csv"] = DataFrameExporter.to_csv(df, csv_path)

        if "json" in formats:
            json_path = output_dir / f"{base_filename}.json"
            exported_files["json"] = DataFrameExporter.to_json(df, json_path)

        if "html" in formats:
            html_path = output_dir / f"{base_filename}.html"
            exported_files["html"] = DataFrameExporter.to_html(df, html_path)

        if "excel" in formats:
            excel_path = output_dir / f"{base_filename}.xlsx"
            exported_files["excel"] = DataFrameExporter.to_excel(df, excel_path)

        return exported_files
