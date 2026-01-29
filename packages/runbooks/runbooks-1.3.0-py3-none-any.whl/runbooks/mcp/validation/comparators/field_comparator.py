# =============================================================================
# Field Comparator
# =============================================================================
# ADLC v3.0.0 - Field-by-field comparison utilities
# =============================================================================

"""Field-by-field comparison utilities for MCP validation."""

from typing import Any

from ..core.types import FieldComparison


class FieldComparator:
    """Utility class for comparing fields between MCP and native API responses."""

    @staticmethod
    def compare_exact(
        field_path: str,
        mcp_value: Any,
        native_value: Any,
        notes: str | None = None,
    ) -> FieldComparison:
        """Compare two values for exact equality.

        Args:
            field_path: JSONPath or field name
            mcp_value: Value from MCP server
            native_value: Value from native API
            notes: Optional notes about the comparison

        Returns:
            FieldComparison result
        """
        return FieldComparison(
            field_path=field_path,
            mcp_value=mcp_value,
            native_value=native_value,
            match=mcp_value == native_value,
            notes=notes,
        )

    @staticmethod
    def compare_case_insensitive(
        field_path: str,
        mcp_value: str | None,
        native_value: str | None,
        notes: str | None = None,
    ) -> FieldComparison:
        """Compare two string values case-insensitively.

        Args:
            field_path: JSONPath or field name
            mcp_value: Value from MCP server
            native_value: Value from native API
            notes: Optional notes about the comparison

        Returns:
            FieldComparison result
        """
        mcp_lower = mcp_value.lower() if mcp_value else None
        native_lower = native_value.lower() if native_value else None

        return FieldComparison(
            field_path=field_path,
            mcp_value=mcp_value,
            native_value=native_value,
            match=mcp_lower == native_lower,
            notes=notes or "Case-insensitive comparison",
        )

    @staticmethod
    def compare_contains(
        field_path: str,
        mcp_value: list[Any] | None,
        native_value: list[Any] | None,
        notes: str | None = None,
    ) -> FieldComparison:
        """Check if MCP list contains all items from native list.

        Args:
            field_path: JSONPath or field name
            mcp_value: List from MCP server
            native_value: List from native API
            notes: Optional notes about the comparison

        Returns:
            FieldComparison result
        """
        mcp_set = set(mcp_value) if mcp_value else set()
        native_set = set(native_value) if native_value else set()

        return FieldComparison(
            field_path=field_path,
            mcp_value=mcp_value,
            native_value=native_value,
            match=native_set.issubset(mcp_set),
            notes=notes or "Contains comparison (native items in MCP)",
        )

    @staticmethod
    def compare_set_equality(
        field_path: str,
        mcp_value: list[Any] | None,
        native_value: list[Any] | None,
        notes: str | None = None,
    ) -> FieldComparison:
        """Compare two lists as sets (order-independent).

        Args:
            field_path: JSONPath or field name
            mcp_value: List from MCP server
            native_value: List from native API
            notes: Optional notes about the comparison

        Returns:
            FieldComparison result
        """
        mcp_set = set(mcp_value) if mcp_value else set()
        native_set = set(native_value) if native_value else set()

        return FieldComparison(
            field_path=field_path,
            mcp_value=mcp_value,
            native_value=native_value,
            match=mcp_set == native_set,
            notes=notes or "Set equality comparison (order-independent)",
        )

    @staticmethod
    def compare_length(
        field_path: str,
        mcp_value: list[Any] | dict[str, Any] | None,
        native_value: list[Any] | dict[str, Any] | None,
        notes: str | None = None,
    ) -> FieldComparison:
        """Compare lengths of two collections.

        Args:
            field_path: JSONPath or field name
            mcp_value: Collection from MCP server
            native_value: Collection from native API
            notes: Optional notes about the comparison

        Returns:
            FieldComparison result
        """
        mcp_len = len(mcp_value) if mcp_value else 0
        native_len = len(native_value) if native_value else 0

        return FieldComparison(
            field_path=f"{field_path}.length",
            mcp_value=mcp_len,
            native_value=native_len,
            match=mcp_len == native_len,
            notes=notes,
        )

    @staticmethod
    def compare_nested(
        base_path: str,
        mcp_data: dict[str, Any],
        native_data: dict[str, Any],
        fields: list[str],
    ) -> list[FieldComparison]:
        """Compare multiple nested fields.

        Args:
            base_path: Base JSONPath for the nested object
            mcp_data: Dictionary from MCP server
            native_data: Dictionary from native API
            fields: List of field names to compare

        Returns:
            List of FieldComparison results
        """
        comparisons: list[FieldComparison] = []

        for field in fields:
            mcp_value = mcp_data.get(field)
            native_value = native_data.get(field)

            comparisons.append(
                FieldComparison(
                    field_path=f"{base_path}.{field}",
                    mcp_value=mcp_value,
                    native_value=native_value,
                    match=mcp_value == native_value,
                )
            )

        return comparisons

    @staticmethod
    def compare_existence(
        field_path: str,
        mcp_data: dict[str, Any],
        native_data: dict[str, Any],
        field: str,
    ) -> FieldComparison:
        """Check if a field exists in both responses.

        Args:
            field_path: Base JSONPath
            mcp_data: Dictionary from MCP server
            native_data: Dictionary from native API
            field: Field name to check

        Returns:
            FieldComparison result
        """
        mcp_exists = field in mcp_data
        native_exists = field in native_data

        return FieldComparison(
            field_path=f"{field_path}.{field}.exists",
            mcp_value=mcp_exists,
            native_value=native_exists,
            match=mcp_exists == native_exists,
            notes="Field existence check",
        )
