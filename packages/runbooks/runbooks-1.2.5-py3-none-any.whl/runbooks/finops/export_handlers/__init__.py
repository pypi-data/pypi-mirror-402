"""Export handlers factory and public API."""

from typing import Optional

from .base_exporter import BaseExporter, ExportMetadata
from .console_exporters import TableExporter, TreeExporter
from .string_exporters import CsvExporter, JsonExporter, MarkdownExporter

# Track D v1.1.26: Excel multi-sheet export with persona formatting
try:
    from .excel_exporter import ExcelExporter

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    ExcelExporter = None


class ExportFactory:
    """Factory for creating format-specific exporters."""

    _handlers = {
        "tree": TreeExporter,
        "table": TableExporter,
        "markdown": MarkdownExporter,
        "json": JsonExporter,
        "csv": CsvExporter,
    }

    # Track D v1.1.26: Excel export (optional - requires openpyxl)
    if EXCEL_AVAILABLE:
        _handlers["excel"] = ExcelExporter

    @classmethod
    def create(cls, format_name: str, **kwargs) -> BaseExporter:
        """
        Create exporter for specified format.

        Args:
            format_name: Format identifier (tree, table, markdown, json, csv)
            **kwargs: Format-specific options (console_instance, persona, etc.)

        Returns:
            Initialized exporter instance

        Raises:
            ValueError: If format not supported

        Examples:
            >>> exporter = ExportFactory.create('csv')
            >>> exporter = ExportFactory.create('tree', persona='cfo')
            >>> exporter = ExportFactory.create('json', persona='cto')

        Track B v1.1.26: Added persona parameter support for role-specific formatting.
        """
        handler_class = cls._handlers.get(format_name.lower())
        if not handler_class:
            supported = ", ".join(cls._handlers.keys())
            raise ValueError(f"Unknown format '{format_name}'. Supported: {supported}")

        return handler_class(**kwargs)

    @classmethod
    def get_supported_formats(cls) -> list:
        """Return list of supported formats."""
        return list(cls._handlers.keys())

    @classmethod
    def get_format_info(cls, format_name: str) -> dict:
        """
        Get metadata about format.

        Track B v1.1.26: Updated supports_personas to True for all formats.
        """
        info = {
            "tree": {"console_only": True, "supports_personas": True},  # Track B v1.1.26
            "table": {"console_only": True, "supports_personas": True},  # Track B v1.1.26
            "markdown": {"console_only": False, "supports_personas": True},  # Track B v1.1.26
            "json": {"console_only": False, "supports_personas": True},  # Track B v1.1.26
            "csv": {"console_only": False, "supports_personas": True},  # Track B v1.1.26
            "excel": {"console_only": False, "supports_personas": True, "requires": "openpyxl"},  # Track D v1.1.26
        }
        return info.get(format_name, {})


# Public API
__all__ = [
    "ExportFactory",
    "BaseExporter",
    "ExportMetadata",
    "TreeExporter",
    "TableExporter",
    "MarkdownExporter",
    "JsonExporter",
    "CsvExporter",
]

# Track D v1.1.26: Add ExcelExporter if available
if EXCEL_AVAILABLE:
    __all__.append("ExcelExporter")
