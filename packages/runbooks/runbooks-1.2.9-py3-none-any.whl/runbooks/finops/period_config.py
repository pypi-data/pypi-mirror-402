#!/usr/bin/env python3
"""
Period Configuration for FinOps Dashboard

This module implements configurable period support for cost analysis:
- Quarterly periods (Q1, Q2, Q3, Q4)
- Year-to-Date (YTD)
- Month-to-Date (MTD)
- Last N days (30, 60, 90)
- Custom date ranges

Manager Requirement #2: Configurable Period
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional, Tuple
from runbooks.common.rich_utils import print_info, print_warning


# Period type definitions
PeriodType = Literal[
    "Q1",
    "Q2",
    "Q3",
    "Q4",  # Quarterly
    "YTD",
    "MTD",  # To-date periods
    "Last7Days",
    "Last30Days",
    "Last60Days",
    "Last90Days",  # Rolling periods
    "ThisMonth",
    "LastMonth",  # Monthly periods
    "custom",  # Custom date range
]


@dataclass
class PeriodConfig:
    """
    Period configuration for cost analysis.

    Attributes:
        period_type: Type of period (Q1, Q2, etc.)
        start_date: Start date of the period
        end_date: End date of the period
        description: Human-readable description
    """

    period_type: PeriodType
    start_date: datetime
    end_date: datetime
    description: str = ""

    @classmethod
    def from_period_type(cls, period_type: PeriodType, year: Optional[int] = None) -> "PeriodConfig":
        """
        Create PeriodConfig from a predefined period type.

        Args:
            period_type: Type of period (Q1, Q2, Q3, Q4, YTD, MTD, etc.)
            year: Year for quarterly periods (defaults to current year)

        Returns:
            PeriodConfig instance

        Example:
            >>> # Q3 2025
            >>> period = PeriodConfig.from_period_type('Q3', year=2025)
            >>> print(f"{period.start_date} to {period.end_date}")
            2025-07-01 to 2025-09-30

            >>> # Year to Date
            >>> period = PeriodConfig.from_period_type('YTD')
            >>> print(period.description)
            Year-to-Date (2025-01-01 to 2025-11-15)
        """
        year = year or datetime.now().year
        today = datetime.now().date()
        current_year = today.year
        current_month = today.month

        # Quarterly periods
        if period_type == "Q1":
            start = datetime(year, 1, 1)
            end = datetime(year, 3, 31)
            desc = f"Q1 {year} (Jan-Mar)"

        elif period_type == "Q2":
            start = datetime(year, 4, 1)
            end = datetime(year, 6, 30)
            desc = f"Q2 {year} (Apr-Jun)"

        elif period_type == "Q3":
            start = datetime(year, 7, 1)
            end = datetime(year, 9, 30)
            desc = f"Q3 {year} (Jul-Sep)"

        elif period_type == "Q4":
            start = datetime(year, 10, 1)
            end = datetime(year, 12, 31)
            desc = f"Q4 {year} (Oct-Dec)"

        # To-date periods
        elif period_type == "YTD":
            start = datetime(current_year, 1, 1)
            end = datetime.combine(today, datetime.min.time())
            desc = f"Year-to-Date ({start.date()} to {end.date()})"

        elif period_type == "MTD":
            start = datetime(current_year, current_month, 1)
            end = datetime.combine(today, datetime.min.time())
            desc = f"Month-to-Date ({start.date()} to {end.date()})"

        # Rolling periods
        elif period_type == "Last7Days":
            end = datetime.combine(today, datetime.min.time())
            start = end - timedelta(days=7)
            desc = "Last 7 Days"

        elif period_type == "Last30Days":
            end = datetime.combine(today, datetime.min.time())
            start = end - timedelta(days=30)
            desc = "Last 30 Days"

        elif period_type == "Last60Days":
            end = datetime.combine(today, datetime.min.time())
            start = end - timedelta(days=60)
            desc = "Last 60 Days"

        elif period_type == "Last90Days":
            end = datetime.combine(today, datetime.min.time())
            start = end - timedelta(days=90)
            desc = "Last 90 Days"

        # Monthly periods
        elif period_type == "ThisMonth":
            start = datetime(current_year, current_month, 1)
            # Calculate last day of month
            if current_month == 12:
                end = datetime(current_year, 12, 31)
            else:
                end = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
            desc = f"This Month ({start.strftime('%B %Y')})"

        elif period_type == "LastMonth":
            # Calculate previous month
            if current_month == 1:
                prev_month = 12
                prev_year = current_year - 1
            else:
                prev_month = current_month - 1
                prev_year = current_year

            start = datetime(prev_year, prev_month, 1)
            # Calculate last day of previous month
            if prev_month == 12:
                end = datetime(prev_year, 12, 31)
            else:
                end = datetime(prev_year, prev_month + 1, 1) - timedelta(days=1)
            desc = f"Last Month ({start.strftime('%B %Y')})"

        elif period_type == "custom":
            raise ValueError("Custom period requires explicit start_date and end_date")

        else:
            raise ValueError(f"Unknown period type: {period_type}")

        return cls(period_type, start, end, desc)

    @classmethod
    def custom(cls, start_date: datetime, end_date: datetime, description: str = "") -> "PeriodConfig":
        """
        Create a custom period configuration.

        Args:
            start_date: Start date of the period
            end_date: End date of the period
            description: Optional description

        Returns:
            PeriodConfig instance

        Example:
            >>> start = datetime(2025, 1, 1)
            >>> end = datetime(2025, 6, 30)
            >>> period = PeriodConfig.custom(start, end, "H1 2025")
        """
        if not description:
            description = f"Custom Period ({start_date.date()} to {end_date.date()})"

        return cls("custom", start_date, end_date, description)

    def to_cost_explorer_params(self) -> dict:
        """
        Convert PeriodConfig to AWS Cost Explorer API parameters.

        Returns:
            Dict with 'Start' and 'End' keys for Cost Explorer API

        Example:
            >>> period = PeriodConfig.from_period_type('Q3', 2025)
            >>> params = period.to_cost_explorer_params()
            >>> print(params)
            {'Start': '2025-07-01', 'End': '2025-09-30'}
        """
        return {"Start": self.start_date.strftime("%Y-%m-%d"), "End": self.end_date.strftime("%Y-%m-%d")}

    def to_cloudwatch_params(self) -> dict:
        """
        Convert PeriodConfig to AWS CloudWatch API parameters.

        Returns:
            Dict with 'StartTime' and 'EndTime' keys for CloudWatch API
        """
        return {"StartTime": self.start_date, "EndTime": self.end_date}

    def get_display_string(self) -> str:
        """
        Get a human-readable display string for the period.

        Returns:
            Formatted string for display in dashboards
        """
        if self.description:
            return self.description

        return f"{self.period_type}: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"

    def get_days_count(self) -> int:
        """
        Get the number of days in the period.

        Returns:
            Number of days between start and end date
        """
        delta = self.end_date - self.start_date
        return delta.days + 1  # Include end date


def get_current_quarter() -> str:
    """
    Get the current quarter based on today's date.

    Returns:
        Quarter string (Q1, Q2, Q3, or Q4)
    """
    month = datetime.now().month
    if month <= 3:
        return "Q1"
    elif month <= 6:
        return "Q2"
    elif month <= 9:
        return "Q3"
    else:
        return "Q4"


def get_previous_quarter() -> Tuple[str, int]:
    """
    Get the previous quarter and year.

    Returns:
        Tuple of (quarter string, year)
    """
    current_quarter = get_current_quarter()
    current_year = datetime.now().year

    if current_quarter == "Q1":
        return ("Q4", current_year - 1)
    elif current_quarter == "Q2":
        return ("Q1", current_year)
    elif current_quarter == "Q3":
        return ("Q2", current_year)
    else:  # Q4
        return ("Q3", current_year)


# Predefined period configurations for common use cases
PREDEFINED_PERIODS = {
    "current_quarter": lambda: PeriodConfig.from_period_type(get_current_quarter()),
    "previous_quarter": lambda: PeriodConfig.from_period_type(*get_previous_quarter()),
    "ytd": lambda: PeriodConfig.from_period_type("YTD"),
    "mtd": lambda: PeriodConfig.from_period_type("MTD"),
    "last_30_days": lambda: PeriodConfig.from_period_type("Last30Days"),
    "last_90_days": lambda: PeriodConfig.from_period_type("Last90Days"),
}


if __name__ == "__main__":
    # Test period configurations
    print("\n=== Period Configuration Test ===\n")

    # Test quarterly periods
    for quarter in ["Q1", "Q2", "Q3", "Q4"]:
        period = PeriodConfig.from_period_type(quarter, year=2025)
        print(f"{period.get_display_string()}")
        print(f"  Days: {period.get_days_count()}")
        print(f"  Cost Explorer: {period.to_cost_explorer_params()}")

    # Test to-date periods
    print("\nTo-Date Periods:")
    for period_type in ["YTD", "MTD"]:
        period = PeriodConfig.from_period_type(period_type)
        print(f"{period.get_display_string()}")

    # Test rolling periods
    print("\nRolling Periods:")
    for period_type in ["Last7Days", "Last30Days", "Last90Days"]:
        period = PeriodConfig.from_period_type(period_type)
        print(f"{period.get_display_string()}")
