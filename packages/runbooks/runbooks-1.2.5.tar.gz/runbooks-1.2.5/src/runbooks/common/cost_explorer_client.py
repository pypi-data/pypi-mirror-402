#!/usr/bin/env python3
"""Unified Cost Explorer client wrapper.

Consolidates Cost Explorer API calls duplicated across 29 finops files.
Provides consistent pagination, error handling, and date formatting.

Strategic Achievement: DRY principle enforcement for Cost Explorer operations
Business Impact: Consistent cost data retrieval across all FinOps modules
Technical Foundation: Unified API wrapper with enterprise patterns

Author: Runbooks Team
Version: 1.0.0
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .aws_client_factory import create_cost_explorer_client


class CostExplorerClient:
    """Wrapper for AWS Cost Explorer API with consistent patterns."""

    def __init__(self, profile: str, region: str = "ap-southeast-2"):
        """Initialize Cost Explorer client.

        Args:
            profile: AWS profile name
            region: AWS region

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> costs = ce_client.get_costs_by_service('2024-01-01', '2024-02-01')
        """
        self.client = create_cost_explorer_client(profile, region)
        self.profile = profile

    def get_costs_by_service(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "MONTHLY",
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get costs grouped by service.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY|MONTHLY|HOURLY
            metrics: Cost metrics (default: ['UnblendedCost'])

        Returns:
            Cost and usage data grouped by service

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> costs = ce_client.get_costs_by_service('2024-01-01', '2024-02-01')
            >>> for result in costs['ResultsByTime']:
            ...     print(result['TimePeriod'])
        """
        if metrics is None:
            metrics = ["UnblendedCost"]

        return self.client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=metrics,
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

    def get_costs_by_account(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "MONTHLY",
        metrics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get costs grouped by linked account.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY|MONTHLY|HOURLY
            metrics: Cost metrics (default: ['UnblendedCost'])

        Returns:
            Cost and usage data grouped by LINKED_ACCOUNT

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> costs = ce_client.get_costs_by_account('2024-01-01', '2024-02-01')
            >>> for result in costs['ResultsByTime']:
            ...     for group in result['Groups']:
            ...         account_id = group['Keys'][0]
            ...         amount = group['Metrics']['UnblendedCost']['Amount']
        """
        if metrics is None:
            metrics = ["UnblendedCost"]

        return self.client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity=granularity,
            Metrics=metrics,
            GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
        )

    def get_costs_dual_metrics(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "MONTHLY",
        group_by: str = "SERVICE",
        filter_param: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get costs with both UnblendedCost and AmortizedCost metrics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY|MONTHLY|HOURLY
            group_by: Dimension to group by (SERVICE|LINKED_ACCOUNT|REGION)
            filter_param: Optional filter for Cost Explorer API

        Returns:
            Cost and usage data with dual metrics

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> costs = ce_client.get_costs_dual_metrics(
            ...     '2024-01-01', '2024-02-01',
            ...     group_by='SERVICE'
            ... )
        """
        params = {
            "TimePeriod": {"Start": start_date, "End": end_date},
            "Granularity": granularity,
            "Metrics": ["UnblendedCost", "AmortizedCost"],
            "GroupBy": [{"Type": "DIMENSION", "Key": group_by}],
        }

        if filter_param:
            params["Filter"] = filter_param

        return self.client.get_cost_and_usage(**params)

    def get_rightsizing_recommendations(self, service: str = "AmazonEC2", page_size: int = 100) -> List[Dict[str, Any]]:
        """Get rightsizing recommendations with pagination.

        Args:
            service: AWS service (default: AmazonEC2)
            page_size: Results per page

        Returns:
            List of rightsizing recommendations

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> recommendations = ce_client.get_rightsizing_recommendations()
            >>> for rec in recommendations:
            ...     print(rec['CurrentInstance']['InstanceType'])
        """
        recommendations = []
        next_page_token = None

        while True:
            params = {
                "Service": service,
                "PageSize": page_size,
            }

            if next_page_token:
                params["NextPageToken"] = next_page_token

            response = self.client.get_rightsizing_recommendation(**params)

            recommendations.extend(response.get("RightsizingRecommendations", []))

            next_page_token = response.get("NextPageToken")
            if not next_page_token:
                break

        return recommendations

    def get_reservation_recommendations(
        self, service: str = "AmazonEC2", lookback_period: str = "THIRTY_DAYS"
    ) -> Dict[str, Any]:
        """Get reservation purchase recommendations.

        Args:
            service: AWS service (default: AmazonEC2)
            lookback_period: SEVEN_DAYS|THIRTY_DAYS|SIXTY_DAYS

        Returns:
            Reservation recommendations

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> recommendations = ce_client.get_reservation_recommendations()
        """
        return self.client.get_reservation_purchase_recommendation(
            Service=service, LookbackPeriodInDays=lookback_period
        )

    def get_savings_plans_recommendations(
        self, lookback_period: str = "THIRTY_DAYS", term: str = "ONE_YEAR"
    ) -> Dict[str, Any]:
        """Get Savings Plans purchase recommendations.

        Args:
            lookback_period: SEVEN_DAYS|THIRTY_DAYS|SIXTY_DAYS
            term: ONE_YEAR|THREE_YEARS

        Returns:
            Savings Plans recommendations

        Example:
            >>> ce_client = CostExplorerClient('my-profile')
            >>> recommendations = ce_client.get_savings_plans_recommendations()
        """
        return self.client.get_savings_plans_purchase_recommendation(
            LookbackPeriodInDays=lookback_period, TermInYears=term
        )

    @staticmethod
    def format_date_range(months_back: int = 6) -> tuple[str, str]:
        """Generate date range for cost queries.

        Args:
            months_back: Number of months to look back

        Returns:
            (start_date, end_date) in YYYY-MM-DD format

        Example:
            >>> start, end = CostExplorerClient.format_date_range(months_back=3)
            >>> print(f"Date range: {start} to {end}")
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=months_back * 30)
        return (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    @staticmethod
    def format_current_month() -> tuple[str, str]:
        """Generate date range for current month.

        Returns:
            (start_date, end_date) for current month in YYYY-MM-DD format

        Example:
            >>> start, end = CostExplorerClient.format_current_month()
            >>> print(f"Current month: {start} to {end}")
        """
        end_date = datetime.now().date()
        start_date = end_date.replace(day=1)
        return (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))

    @staticmethod
    def format_previous_month() -> tuple[str, str]:
        """Generate date range for previous month.

        Returns:
            (start_date, end_date) for previous month in YYYY-MM-DD format

        Example:
            >>> start, end = CostExplorerClient.format_previous_month()
            >>> print(f"Previous month: {start} to {end}")
        """
        today = datetime.now().date()
        first_of_current_month = today.replace(day=1)
        last_of_previous_month = first_of_current_month - timedelta(days=1)
        first_of_previous_month = last_of_previous_month.replace(day=1)

        return (
            first_of_previous_month.strftime("%Y-%m-%d"),
            first_of_current_month.strftime("%Y-%m-%d"),
        )
