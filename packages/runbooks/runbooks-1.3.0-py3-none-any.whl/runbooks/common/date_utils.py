#!/usr/bin/env python3
"""
Dynamic Date Utilities for Runbooks Platform

Replaces hardcoded 2024 dates with dynamic date generation following manager's
"No hardcoded values" requirement. Supports current month/year calculations
for all test data and AWS API time period generation.

Strategic Alignment: "Do one thing and do it well" - Focused date utility
KISS Principle: Simple, reusable date functions for all modules

ADLC v3.0.0 Enhancement (2026-01-16):
- Added DateRangeCalculator with UTC-first design
- All end dates are EXCLUSIVE (AWS Cost Explorer API convention)
- Immutable DateRange NamedTuple for type safety
- DRY: Single source of truth for date range calculations
"""

from datetime import date, datetime, timedelta, timezone
from typing import Dict, NamedTuple, Optional, Tuple


# =============================================================================
# DateRange NamedTuple - Immutable, Self-Documenting API
# =============================================================================


class DateRange(NamedTuple):
    """
    Immutable date range with exclusive end date (AWS API convention).

    Attributes:
        start: Inclusive start date (first day included in range)
        end: EXCLUSIVE end date (first day NOT included in range)
        days: Number of days in the range

    Example:
        For December 2025:
        - start = 2025-12-01 (included)
        - end = 2026-01-01 (excluded, means "up to Dec 31")
        - days = 31

    AWS Cost Explorer Semantics:
        TimePeriod={"Start": "2025-12-01", "End": "2026-01-01"} queries Dec 1-31
    """

    start: date  # Inclusive start date
    end: date  # EXCLUSIVE end date (first day NOT included)
    days: int  # Number of days in range


# =============================================================================
# DateRangeCalculator - UTC-First, DRY-Compliant Date Logic
# =============================================================================


class DateRangeCalculator:
    """
    UTC-first date range calculator for AWS Cost Explorer.

    Design Principles:
    - UTC-first: All "now" calculations use UTC to prevent timezone off-by-one
    - Exclusive end: AWS Cost Explorer uses exclusive end dates
    - Immutable: Returns DateRange NamedTuple for safety
    - DRY: Single source of truth (replaces 147 LOC across 2 files)

    Usage:
        calc = DateRangeCalculator()

        # Specific month
        dec_2025 = calc.month_range("2025-12")
        # DateRange(start=2025-12-01, end=2026-01-01, days=31)

        # Last N days
        last_30 = calc.days_range(30)

        # Format for AWS API
        start_str, end_str = calc.format_for_aws(dec_2025)
        # ("2025-12-01", "2026-01-01")
    """

    @staticmethod
    def month_range(month_str: str) -> DateRange:
        """
        Parse YYYY-MM format and return DateRange with exclusive end.

        Args:
            month_str: Month in "YYYY-MM" format (e.g., "2025-12")

        Returns:
            DateRange with start (first of month), end (first of next month),
            and days (actual days in month, handles leap years)

        Raises:
            ValueError: If month_str is not in YYYY-MM format

        Example:
            >>> DateRangeCalculator.month_range("2025-12")
            DateRange(start=date(2025, 12, 1), end=date(2026, 1, 1), days=31)

            >>> DateRangeCalculator.month_range("2024-02")  # Leap year
            DateRange(start=date(2024, 2, 1), end=date(2024, 3, 1), days=29)
        """
        try:
            year, mon = map(int, month_str.split("-"))
        except (ValueError, AttributeError) as e:
            raise ValueError(
                f"Invalid month format '{month_str}'. Expected YYYY-MM (e.g., 2025-12)"
            ) from e

        if mon < 1 or mon > 12:
            raise ValueError(f"Invalid month {mon}. Must be 1-12")

        start = date(year, mon, 1)

        # Exclusive end = first day of next month
        if mon == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, mon + 1, 1)

        return DateRange(start=start, end=end, days=(end - start).days)

    @staticmethod
    def days_range(days: int, reference_date: Optional[date] = None) -> DateRange:
        """
        Calculate range from N days ago to reference date (UTC).

        Args:
            days: Number of days to look back
            reference_date: Optional reference date (defaults to UTC today)

        Returns:
            DateRange spanning from (reference - days) to reference + 1 (exclusive)

        Note:
            Uses UTC to prevent timezone off-by-one errors for users in
            UTC+10 to UTC+14 (Australia, NZ, Pacific Islands).

        Example:
            >>> DateRangeCalculator.days_range(30)  # Last 30 days from UTC today
            DateRange(start=<30 days ago>, end=<tomorrow UTC>, days=30)
        """
        if reference_date is None:
            # UTC-first: Prevent off-by-one for UTC+10-14 timezones
            reference_date = datetime.now(timezone.utc).date()

        start = reference_date - timedelta(days=days)
        end = reference_date + timedelta(days=1)  # Exclusive end (include today)

        return DateRange(start=start, end=end, days=days + 1)

    @staticmethod
    def previous_period(date_range: DateRange) -> DateRange:
        """
        Calculate the previous period of equal duration.

        Args:
            date_range: Current period DateRange

        Returns:
            DateRange for the period immediately before the input range,
            with the same number of days

        Example:
            >>> current = DateRangeCalculator.month_range("2025-12")  # Dec 2025
            >>> prev = DateRangeCalculator.previous_period(current)
            # DateRange for Nov 2025 (or same-length period before Dec 1)
        """
        duration = date_range.days
        prev_end = date_range.start  # New end is old start (exclusive)
        prev_start = prev_end - timedelta(days=duration)

        return DateRange(start=prev_start, end=prev_end, days=duration)

    @staticmethod
    def previous_month(date_range: DateRange) -> DateRange:
        """
        Calculate the previous calendar month for MoM comparison.

        Args:
            date_range: Current period DateRange (should be a full month)

        Returns:
            DateRange for the previous calendar month

        Example:
            >>> dec = DateRangeCalculator.month_range("2025-12")
            >>> nov = DateRangeCalculator.previous_month(dec)
            DateRange(start=date(2025, 11, 1), end=date(2025, 12, 1), days=30)
        """
        # Get previous month from start date
        year = date_range.start.year
        month = date_range.start.month

        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1

        return DateRangeCalculator.month_range(f"{prev_year:04d}-{prev_month:02d}")

    @staticmethod
    def format_for_aws(date_range: DateRange) -> Tuple[str, str]:
        """
        Format DateRange for AWS Cost Explorer API (YYYY-MM-DD strings).

        Args:
            date_range: DateRange to format

        Returns:
            Tuple of (start_str, end_str) ready for AWS TimePeriod parameter

        Example:
            >>> dec = DateRangeCalculator.month_range("2025-12")
            >>> start, end = DateRangeCalculator.format_for_aws(dec)
            >>> start
            '2025-12-01'
            >>> end
            '2026-01-01'
        """
        return (date_range.start.isoformat(), date_range.end.isoformat())

    @staticmethod
    def today_utc() -> date:
        """
        Get today's date in UTC timezone.

        Returns:
            Current date in UTC (prevents off-by-one for UTC+10-14)
        """
        return datetime.now(timezone.utc).date()

    @staticmethod
    def current_month() -> DateRange:
        """
        Get the current calendar month range (UTC-based).

        Returns:
            DateRange for the current month from day 1 to first of next month

        Note:
            Uses UTC to determine "current" month, preventing timezone issues.
        """
        today = DateRangeCalculator.today_utc()
        return DateRangeCalculator.month_range(f"{today.year:04d}-{today.month:02d}")

    @staticmethod
    def previous_calendar_month() -> DateRange:
        """
        Get the previous calendar month range (UTC-based).

        Returns:
            DateRange for the previous month

        Example:
            If today is Jan 16, 2026 UTC:
            Returns December 2025 (2025-12-01 to 2026-01-01)
        """
        today = DateRangeCalculator.today_utc()
        if today.month == 1:
            return DateRangeCalculator.month_range(f"{today.year - 1:04d}-12")
        else:
            return DateRangeCalculator.month_range(
                f"{today.year:04d}-{today.month - 1:02d}"
            )

    @staticmethod
    def month_to_date(reference_date: Optional[date] = None) -> DateRange:
        """
        Get Month-to-Date (MTD) range from day 1 to reference date (inclusive).

        This method supports US-2 (SRE) use case: analyzing cost from the
        beginning of the current month up to today for incident correlation.

        Args:
            reference_date: Optional reference date (defaults to UTC today)

        Returns:
            DateRange from first of month to reference_date + 1 (exclusive end)

        Example:
            If today is Jan 16, 2026 UTC:
            >>> DateRangeCalculator.month_to_date()
            DateRange(start=date(2026, 1, 1), end=date(2026, 1, 17), days=16)

            # AWS Cost Explorer query would be:
            # TimePeriod={"Start": "2026-01-01", "End": "2026-01-17"}
            # This queries Jan 1-16 (16 days of MTD data)

        Note:
            Uses UTC to prevent timezone off-by-one errors.
            End date is EXCLUSIVE (AWS Cost Explorer convention).
        """
        if reference_date is None:
            reference_date = DateRangeCalculator.today_utc()

        start = reference_date.replace(day=1)
        end = reference_date + timedelta(days=1)  # Exclusive end (include today)

        return DateRange(start=start, end=end, days=reference_date.day)


# =============================================================================
# Legacy Functions (Preserved for Backwards Compatibility)
# =============================================================================


def get_current_year() -> int:
    """Get current year dynamically."""
    return datetime.now().year


def get_current_month_period() -> Dict[str, str]:
    """
    Generate current month's start and end dates for AWS API calls.

    Returns:
        Dict with 'Start' and 'End' keys in YYYY-MM-DD format
    """
    now = datetime.now()
    start_date = now.replace(day=1).strftime("%Y-%m-%d")

    # Get last day of current month
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        next_month = now.replace(month=now.month + 1, day=1)

    end_date = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")

    return {"Start": start_date, "End": end_date}


def get_previous_month_period() -> Dict[str, str]:
    """
    Generate previous month's start and end dates for AWS API calls.

    Returns:
        Dict with 'Start' and 'End' keys in YYYY-MM-DD format
    """
    now = datetime.now()

    # Get first day of previous month
    if now.month == 1:
        prev_month = now.replace(year=now.year - 1, month=12, day=1)
    else:
        prev_month = now.replace(month=now.month - 1, day=1)

    start_date = prev_month.strftime("%Y-%m-%d")

    # Get last day of previous month
    end_date = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")

    return {"Start": start_date, "End": end_date}


def get_test_date_period(days_back: int = 30) -> Dict[str, str]:
    """
    Generate test date periods for consistent test data.

    Args:
        days_back: Number of days back from today for start date

    Returns:
        Dict with 'Start' and 'End' keys in YYYY-MM-DD format
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    return {"Start": start_date, "End": end_date}


def get_aws_cli_example_period() -> Tuple[str, str]:
    """
    Generate example date period for AWS CLI documentation.
    Uses yesterday and today to ensure valid time range.

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    return (yesterday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))


def get_collection_timestamp() -> str:
    """
    Generate collection timestamp for test data.

    Returns:
        ISO format timestamp string
    """
    return datetime.now().isoformat()
