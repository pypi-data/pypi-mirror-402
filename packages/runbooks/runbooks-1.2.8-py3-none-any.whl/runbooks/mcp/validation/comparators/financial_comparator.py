# =============================================================================
# Financial Comparator
# =============================================================================
# ADLC v3.0.0 - Financial field comparison with tolerance
# =============================================================================

"""Financial field comparison with configurable tolerance for MCP validation."""

from decimal import Decimal, InvalidOperation
from typing import Any

from ..core.constants import FINANCIAL_TOLERANCE
from ..core.types import FieldComparison


class FinancialComparator:
    """Utility class for comparing financial values with tolerance.

    Financial fields require special handling due to floating-point precision
    issues and acceptable variance in cost reporting.
    """

    def __init__(self, tolerance: float = FINANCIAL_TOLERANCE) -> None:
        """Initialize the financial comparator.

        Args:
            tolerance: Acceptable variance as a decimal (default 0.0001 = 0.01%)
        """
        self.tolerance = tolerance

    def compare(
        self,
        field_path: str,
        mcp_value: Any,
        native_value: Any,
        notes: str | None = None,
    ) -> FieldComparison:
        """Compare two financial values within tolerance.

        Args:
            field_path: JSONPath or field name
            mcp_value: Value from MCP server
            native_value: Value from native API
            notes: Optional notes about the comparison

        Returns:
            FieldComparison result
        """
        try:
            mcp_decimal = self._to_decimal(mcp_value)
            native_decimal = self._to_decimal(native_value)
        except (ValueError, InvalidOperation):
            # If conversion fails, fall back to exact comparison
            return FieldComparison(
                field_path=field_path,
                mcp_value=mcp_value,
                native_value=native_value,
                match=mcp_value == native_value,
                notes=notes or "Could not parse as financial value, using exact match",
            )

        # Calculate if within tolerance
        match = self._within_tolerance(mcp_decimal, native_decimal)

        return FieldComparison(
            field_path=field_path,
            mcp_value=float(mcp_decimal),
            native_value=float(native_decimal),
            match=match,
            tolerance_applied=self.tolerance,
            notes=notes or f"Financial tolerance: {self.tolerance * 100}%",
        )

    def compare_currency(
        self,
        field_path: str,
        mcp_amount: Any,
        native_amount: Any,
        mcp_currency: str | None,
        native_currency: str | None,
        notes: str | None = None,
    ) -> list[FieldComparison]:
        """Compare currency amount and code.

        Args:
            field_path: JSONPath or field name
            mcp_amount: Amount from MCP server
            native_amount: Amount from native API
            mcp_currency: Currency code from MCP server
            native_currency: Currency code from native API
            notes: Optional notes about the comparison

        Returns:
            List of FieldComparison results (amount and currency)
        """
        comparisons: list[FieldComparison] = []

        # Compare amount with tolerance
        comparisons.append(
            self.compare(
                field_path=f"{field_path}.Amount",
                mcp_value=mcp_amount,
                native_value=native_amount,
                notes=notes,
            )
        )

        # Compare currency code exactly
        comparisons.append(
            FieldComparison(
                field_path=f"{field_path}.Unit",
                mcp_value=mcp_currency,
                native_value=native_currency,
                match=mcp_currency == native_currency,
                notes="Currency code exact match",
            )
        )

        return comparisons

    def compare_cost_breakdown(
        self,
        field_path: str,
        mcp_breakdown: dict[str, Any],
        native_breakdown: dict[str, Any],
        cost_fields: list[str] | None = None,
    ) -> list[FieldComparison]:
        """Compare cost breakdown with multiple cost types.

        Args:
            field_path: Base JSONPath for the breakdown
            mcp_breakdown: Cost breakdown from MCP server
            native_breakdown: Cost breakdown from native API
            cost_fields: List of cost field names (default: common AWS cost fields)

        Returns:
            List of FieldComparison results
        """
        if cost_fields is None:
            cost_fields = [
                "BlendedCost",
                "UnblendedCost",
                "AmortizedCost",
                "NetAmortizedCost",
                "NetUnblendedCost",
            ]

        comparisons: list[FieldComparison] = []

        for cost_field in cost_fields:
            mcp_cost = mcp_breakdown.get(cost_field, {})
            native_cost = native_breakdown.get(cost_field, {})

            if mcp_cost or native_cost:
                # Compare amount
                comparisons.append(
                    self.compare(
                        field_path=f"{field_path}.{cost_field}.Amount",
                        mcp_value=mcp_cost.get("Amount", 0),
                        native_value=native_cost.get("Amount", 0),
                    )
                )

                # Compare unit (currency)
                comparisons.append(
                    FieldComparison(
                        field_path=f"{field_path}.{cost_field}.Unit",
                        mcp_value=mcp_cost.get("Unit"),
                        native_value=native_cost.get("Unit"),
                        match=mcp_cost.get("Unit") == native_cost.get("Unit"),
                    )
                )

        return comparisons

    def _to_decimal(self, value: Any) -> Decimal:
        """Convert value to Decimal for precise comparison.

        Args:
            value: Value to convert (string, int, float, or Decimal)

        Returns:
            Decimal representation

        Raises:
            ValueError: If value cannot be converted
        """
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            return Decimal(value)
        raise ValueError(f"Cannot convert {type(value)} to Decimal")

    def _within_tolerance(
        self,
        mcp_value: Decimal,
        native_value: Decimal,
    ) -> bool:
        """Check if two values are within tolerance.

        Args:
            mcp_value: Value from MCP server
            native_value: Value from native API

        Returns:
            True if within tolerance, False otherwise
        """
        # Handle zero case
        if native_value == 0:
            return mcp_value == 0

        # Calculate percentage difference
        diff = abs(mcp_value - native_value)
        pct_diff = diff / abs(native_value)

        return float(pct_diff) <= self.tolerance

    def aggregate_accuracy(
        self,
        comparisons: list[FieldComparison],
    ) -> dict[str, Any]:
        """Calculate aggregate accuracy for financial comparisons.

        Args:
            comparisons: List of field comparisons

        Returns:
            Dictionary with accuracy statistics
        """
        if not comparisons:
            return {
                "total_fields": 0,
                "matched_fields": 0,
                "accuracy_percentage": 100.0,
                "total_variance": 0.0,
            }

        matched = sum(1 for c in comparisons if c.match)
        total_variance = Decimal("0")

        for c in comparisons:
            if c.tolerance_applied is not None:
                try:
                    mcp_val = self._to_decimal(c.mcp_value)
                    native_val = self._to_decimal(c.native_value)
                    if native_val != 0:
                        variance = abs(mcp_val - native_val) / abs(native_val)
                        total_variance += variance
                except (ValueError, InvalidOperation):
                    pass

        return {
            "total_fields": len(comparisons),
            "matched_fields": matched,
            "accuracy_percentage": (matched / len(comparisons)) * 100,
            "total_variance": float(total_variance),
            "average_variance": float(total_variance / len(comparisons)) if comparisons else 0.0,
        }
