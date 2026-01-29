#!/usr/bin/env python3
"""
Service Selector for FinOps Dashboard

This module implements Top N AWS Services selection by cost:
- Filter services by top N cost (configurable 5, 10, ALL)
- Sort by current_cost, cost_change, or resource_count
- Integrate with Cost Explorer data

Manager Requirement #3: Top AWS Services by Cost (configurable top N or ALL)
Manager Requirement #4: Activity Health Tree service selection
"""

from typing import List, Dict, Optional, Literal, Any
import pandas as pd
from runbooks.common.rich_utils import print_info, print_warning


# Sort criteria type
SortBy = Literal["current_cost", "cost_change", "resource_count", "percentage"]


class ServiceSelector:
    """
    Top N AWS Services selector for FinOps dashboard.

    Provides filtering and selection capabilities for AWS services
    based on cost metrics and resource counts.
    """

    # Supported AWS services for activity analysis
    ACTIVITY_SUPPORTED_SERVICES = [
        "ec2",
        "rds",
        "s3",
        "dynamodb",
        "workspaces",
        "ebs_snapshots",
        "alb",
        "nlb",
        "route53",
        "vpc",
    ]

    # Service display names
    SERVICE_DISPLAY_NAMES = {
        "ec2": "EC2 Instances",
        "s3": "S3 Storage",
        "rds": "RDS Databases",
        "dynamodb": "DynamoDB Tables",
        "lambda": "Lambda Functions",
        "workspaces": "WorkSpaces",
        "ebs_snapshots": "EBS Snapshots",
        "alb": "Application Load Balancers",
        "nlb": "Network Load Balancers",
        "route53": "Route53 DNS",
        "vpc": "VPC Resources",
        "cloudwatch": "CloudWatch",
        "kms": "Key Management Service",
        "config": "AWS Config",
        "security_hub": "Security Hub",
    }

    def __init__(self, cost_data: Optional[pd.DataFrame] = None):
        """
        Initialize ServiceSelector with optional cost data.

        Args:
            cost_data: DataFrame with columns ['service', 'current_cost', 'previous_cost', 'resource_count']
        """
        self.cost_data = cost_data if cost_data is not None else pd.DataFrame()

    def set_cost_data(self, cost_data: pd.DataFrame) -> None:
        """
        Update cost data for service selection.

        Args:
            cost_data: DataFrame with cost information per service
        """
        self.cost_data = cost_data

        # Calculate cost change if not present
        if (
            "cost_change" not in self.cost_data.columns
            and "current_cost" in self.cost_data.columns
            and "previous_cost" in self.cost_data.columns
        ):
            self.cost_data["cost_change"] = self.cost_data["current_cost"] - self.cost_data["previous_cost"]

        # Calculate percentage if not present
        if "percentage" not in self.cost_data.columns and "current_cost" in self.cost_data.columns:
            total_cost = self.cost_data["current_cost"].sum()
            if total_cost > 0:
                self.cost_data["percentage"] = (self.cost_data["current_cost"] / total_cost) * 100
            else:
                self.cost_data["percentage"] = 0

    def get_top_n_services(
        self, n: Optional[int] = None, sort_by: SortBy = "current_cost", ascending: bool = False
    ) -> List[str]:
        """
        Get top N AWS services by specified criterion.

        Args:
            n: Number of services to return (None or 'ALL' for all services)
            sort_by: Sort criterion ('current_cost', 'cost_change', 'resource_count', 'percentage')
            ascending: Sort in ascending order (default: False for descending)

        Returns:
            List of service identifiers (e.g., ['ec2', 's3', 'rds'])

        Example:
            >>> selector = ServiceSelector(cost_data)
            >>> top_5 = selector.get_top_n_services(n=5, sort_by='current_cost')
            >>> print(top_5)
            ['s3', 'ec2', 'rds', 'lambda', 'dynamodb']
        """
        if self.cost_data.empty:
            print_warning("No cost data available for service selection")
            return []

        # Validate sort column exists
        if sort_by not in self.cost_data.columns:
            print_warning(f"Sort column '{sort_by}' not found, using 'current_cost'")
            sort_by = "current_cost"

        # Sort services by selected criterion
        sorted_data = self.cost_data.sort_values(by=sort_by, ascending=ascending)

        # Get service list
        if n is None:
            # Return all services
            services = sorted_data["service"].tolist()
        else:
            # Return top N services
            services = sorted_data.head(n)["service"].tolist()

        print_info(f"Selected {len(services)} services by {sort_by}")
        return services

    def filter_services_for_activity_analysis(self, selected_services: List[str]) -> List[str]:
        """
        Filter services that support Activity Health Tree analysis.

        Args:
            selected_services: List of service identifiers to filter

        Returns:
            Filtered list containing only services that support activity analysis

        Example:
            >>> selected = ['ec2', 's3', 'cloudwatch', 'kms']
            >>> activity_services = selector.filter_services_for_activity_analysis(selected)
            >>> print(activity_services)
            ['ec2', 's3']  # Only these support activity analysis
        """
        activity_services = [s for s in selected_services if s in self.ACTIVITY_SUPPORTED_SERVICES]

        excluded_count = len(selected_services) - len(activity_services)
        if excluded_count > 0:
            excluded = [s for s in selected_services if s not in self.ACTIVITY_SUPPORTED_SERVICES]
            print_info(f"Excluded {excluded_count} services without activity support: {excluded}")

        return activity_services

    def get_service_display_name(self, service_id: str) -> str:
        """
        Get human-readable display name for a service.

        Args:
            service_id: Service identifier (e.g., 'ec2')

        Returns:
            Display name (e.g., 'EC2 Instances')
        """
        return self.SERVICE_DISPLAY_NAMES.get(service_id, service_id.upper())

    def get_service_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all services.

        Returns:
            Dictionary with summary metrics
        """
        if self.cost_data.empty:
            return {
                "total_services": 0,
                "total_current_cost": 0,
                "total_previous_cost": 0,
                "total_resources": 0,
                "top_service": None,
            }

        summary = {
            "total_services": len(self.cost_data),
            "total_current_cost": self.cost_data["current_cost"].sum()
            if "current_cost" in self.cost_data.columns
            else 0,
            "total_previous_cost": self.cost_data["previous_cost"].sum()
            if "previous_cost" in self.cost_data.columns
            else 0,
            "total_resources": self.cost_data["resource_count"].sum()
            if "resource_count" in self.cost_data.columns
            else 0,
        }

        # Get top service by cost
        if "current_cost" in self.cost_data.columns:
            top_service = self.cost_data.nlargest(1, "current_cost")
            if not top_service.empty:
                summary["top_service"] = {
                    "name": top_service.iloc[0]["service"],
                    "cost": top_service.iloc[0]["current_cost"],
                    "percentage": top_service.iloc[0].get("percentage", 0),
                }
            else:
                summary["top_service"] = None
        else:
            summary["top_service"] = None

        return summary

    def filter_by_cost_threshold(
        self, min_cost: Optional[float] = None, max_cost: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Filter services by cost threshold.

        Args:
            min_cost: Minimum cost threshold
            max_cost: Maximum cost threshold

        Returns:
            Filtered DataFrame with services within cost range
        """
        filtered = self.cost_data.copy()

        if min_cost is not None and "current_cost" in filtered.columns:
            filtered = filtered[filtered["current_cost"] >= min_cost]

        if max_cost is not None and "current_cost" in filtered.columns:
            filtered = filtered[filtered["current_cost"] <= max_cost]

        return filtered

    def get_services_by_category(self) -> Dict[str, List[str]]:
        """
        Group services by category for organized display.

        Returns:
            Dictionary with category names as keys and service lists as values
        """
        categories = {
            "Compute": ["ec2", "lambda", "workspaces", "ecs", "eks"],
            "Storage": ["s3", "ebs", "ebs_snapshots", "efs", "glacier"],
            "Database": ["rds", "dynamodb", "elasticache", "redshift"],
            "Network": ["vpc", "alb", "nlb", "cloudfront", "route53"],
            "Security": ["kms", "security_hub", "guardduty", "waf"],
            "Management": ["cloudwatch", "config", "systems_manager", "cloudtrail"],
            "Analytics": ["athena", "kinesis", "glue", "emr"],
        }

        # Filter to only include services present in cost data
        if not self.cost_data.empty and "service" in self.cost_data.columns:
            available_services = set(self.cost_data["service"].tolist())
            for category, services in categories.items():
                categories[category] = [s for s in services if s in available_services]

        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}

        return categories


# Convenience functions for notebook usage
def create_service_selector_from_cost_data(cost_dict: Dict[str, float]) -> ServiceSelector:
    """
    Create a ServiceSelector from a simple cost dictionary.

    Args:
        cost_dict: Dictionary with service names as keys and costs as values

    Returns:
        Configured ServiceSelector instance

    Example:
        >>> costs = {'ec2': 1000, 's3': 500, 'rds': 300}
        >>> selector = create_service_selector_from_cost_data(costs)
    """
    # Convert dict to DataFrame
    cost_data = pd.DataFrame([{"service": service, "current_cost": cost} for service, cost in cost_dict.items()])

    selector = ServiceSelector(cost_data)
    return selector


def get_default_top_services(n: int = 5) -> List[str]:
    """
    Get default top services when no cost data is available.

    Args:
        n: Number of services to return

    Returns:
        List of commonly used AWS services
    """
    default_services = ["ec2", "s3", "rds", "lambda", "dynamodb", "cloudwatch", "route53", "vpc", "kms", "alb"]
    return default_services[:n]


if __name__ == "__main__":
    # Test the service selector
    print("\n=== Service Selector Test ===\n")

    # Create sample cost data
    sample_data = pd.DataFrame(
        [
            {"service": "s3", "current_cost": 602.0, "previous_cost": 1289.5, "resource_count": 30},
            {"service": "ec2", "current_cost": 59.0, "previous_cost": 131.3, "resource_count": 5},
            {"service": "vpc", "current_cost": 26.6, "previous_cost": 59.6, "resource_count": 3},
            {"service": "dynamodb", "current_cost": 0.3, "previous_cost": 0.7, "resource_count": 1},
            {"service": "cloudwatch", "current_cost": 3.7, "previous_cost": 8.5, "resource_count": 0},
        ]
    )

    # Test selector
    selector = ServiceSelector(sample_data)

    # Get top 3 services by cost
    top_3 = selector.get_top_n_services(n=3, sort_by="current_cost")
    print(f"Top 3 services by cost: {top_3}")

    # Filter for activity analysis
    activity_services = selector.filter_services_for_activity_analysis(top_3)
    print(f"Activity-supported services: {activity_services}")

    # Get summary
    summary = selector.get_service_summary()
    print(f"\nSummary:")
    print(f"  Total services: {summary['total_services']}")
    print(f"  Total current cost: ${summary['total_current_cost']:,.2f}")
    print(f"  Top service: {summary['top_service']}")
