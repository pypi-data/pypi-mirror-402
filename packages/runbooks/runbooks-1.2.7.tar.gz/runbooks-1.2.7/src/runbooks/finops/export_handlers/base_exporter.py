"""Abstract base class for all export handlers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Literal, Optional


@dataclass
class ExportMetadata:
    """Metadata for exports."""

    format_type: str
    generated_at: datetime
    title: Optional[str] = None
    version: str = "1.1.27"


class BaseExporter(ABC):
    """Abstract base for export handlers."""

    def __init__(self, title: Optional[str] = None):
        """Initialize exporter with optional title."""
        self.metadata = ExportMetadata(format_type=self.get_format_name(), generated_at=datetime.now(), title=title)

    @abstractmethod
    def export(self, enriched_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Export dashboard data.

        Args:
            enriched_data: Dict with service names as keys, DataFrames as values
            output_path: Optional file path (for file-based exports)

        Returns:
            String output (for string-based) or filepath (for file-based)
        """
        pass

    @abstractmethod
    def get_format_name(self) -> Literal["tree", "table", "markdown", "json", "csv"]:
        """Return format identifier."""
        pass

    def get_metadata(self) -> ExportMetadata:
        """Return export metadata."""
        return self.metadata
