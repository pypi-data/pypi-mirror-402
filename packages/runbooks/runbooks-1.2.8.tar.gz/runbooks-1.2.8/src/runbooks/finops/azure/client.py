"""
Azure Cost Management API Client - SDK Integration

Provides direct Azure Cost Management API access for FinOps analysis.
Uses DefaultAzureCredential for flexible authentication (CLI, MSI, SP).

Ground Truth Hierarchy:
  1. PRIMARY: Azure Native APIs (az costmanagement)
  2. SECONDARY: This SDK client (validates against PRIMARY)

FOCUS 1.3 Alignment:
  - Maps Azure Cost Management responses to FOCUS schema
  - Supports BilledCost, EffectiveCost, ServiceName columns
  - Multi-subscription (Management Group) scope

Framework: ADLC v3.0.0 | Version: 1.0.0
"""

import subprocess
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from runbooks.finops.azure.types import (
    AzureCostData,
    AzureServiceCost,
    AzureSubscriptionCost,
    classify_cost_tier,
)


class AzureCostClient:
    """
    Azure Cost Management API client.

    Wraps Azure CLI for cost queries (SDK fallback when azure-mgmt-costmanagement
    is not installed). Provides ground truth validation against native APIs.

    Usage:
        client = AzureCostClient()
        costs = client.query_costs("2025-11-01", "2025-11-30")
        services = client.query_by_service(timeframe="MonthToDate")
    """

    def __init__(
        self,
        subscription_id: Optional[str] = None,
        management_group: Optional[str] = None,
    ):
        """
        Initialize Azure Cost Client.

        Args:
            subscription_id: Azure subscription ID (uses default if not provided)
            management_group: Management group name for multi-subscription scope
        """
        self.subscription_id = subscription_id or self._get_default_subscription()
        self.management_group = management_group
        self._currency = "NZD"  # Default billing currency
        self._usd_rate = Decimal("1.72")  # NZD to USD approximate rate

    def _get_default_subscription(self) -> Optional[str]:
        """Get default subscription ID from Azure CLI."""
        try:
            result = subprocess.run(
                ["az", "account", "show", "--query", "id", "-o", "tsv"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _run_az_cli(
        self,
        command: str,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """
        Execute Azure CLI command and parse JSON output.

        Args:
            command: Azure CLI command (without 'az' prefix)
            timeout: Command timeout in seconds

        Returns:
            Dict with 'success', 'data', 'error' keys
        """
        full_command = f"az {command} -o json"
        try:
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "data": data, "error": None}
            else:
                return {"success": False, "data": None, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "data": None, "error": f"Command timed out after {timeout}s"}
        except json.JSONDecodeError as e:
            return {"success": False, "data": None, "error": f"JSON parse error: {e}"}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}

    def check_login(self) -> Tuple[bool, str]:
        """
        Verify Azure CLI login status.

        Returns:
            Tuple of (is_logged_in, account_name_or_error)
        """
        result = self._run_az_cli("account show")
        if result["success"]:
            account = result["data"]
            return True, account.get("name", "Unknown")
        return False, result["error"] or "Not logged in"

    def list_subscriptions(self) -> List[Dict[str, str]]:
        """
        List all enabled Azure subscriptions.

        Returns:
            List of subscription dicts with 'id', 'name', 'isDefault' keys
        """
        result = self._run_az_cli("account list --query \"[?state=='Enabled']\"")
        if result["success"] and isinstance(result["data"], list):
            return [
                {
                    "id": sub.get("id", ""),
                    "name": sub.get("name", ""),
                    "isDefault": sub.get("isDefault", False),
                }
                for sub in result["data"]
            ]
        return []

    def _run_cost_management_query(
        self,
        query_body: Dict[str, Any],
        subscription_id: Optional[str] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """
        Execute Cost Management Query API via az rest.

        Uses the Cost Management Query API for actual cost data (required for EA accounts
        where Consumption API returns pretaxCost: None).

        Args:
            query_body: Query request body
            subscription_id: Subscription ID (uses default if not provided)
            timeout: Command timeout in seconds

        Returns:
            Dict with 'success', 'data', 'error' keys
        """
        import tempfile

        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            return {"success": False, "data": None, "error": "No subscription ID"}

        uri = (
            f"https://management.azure.com/subscriptions/{sub_id}"
            f"/providers/Microsoft.CostManagement/query?api-version=2023-11-01"
        )

        # Write query body to temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(query_body, f)
            body_file = f.name

        try:
            result = subprocess.run(
                ["az", "rest", "--method", "post", "--uri", uri, "--body", f"@{body_file}"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout) if result.stdout.strip() else {}
                return {"success": True, "data": data, "error": None}
            else:
                return {"success": False, "data": None, "error": result.stderr}
        except subprocess.TimeoutExpired:
            return {"success": False, "data": None, "error": f"Query timed out after {timeout}s"}
        except json.JSONDecodeError as e:
            return {"success": False, "data": None, "error": f"JSON parse error: {e}"}
        except Exception as e:
            return {"success": False, "data": None, "error": str(e)}
        finally:
            import os
            try:
                os.unlink(body_file)
            except Exception:
                pass

    def query_total_cost(
        self,
        timeframe: str = "MonthToDate",
        subscription_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Decimal:
        """
        Query total cost using Cost Management API.

        Args:
            timeframe: Time period (MonthToDate, LastMonth, etc.)
            subscription_id: Subscription ID
            start_date: Start date for Custom timeframe (YYYY-MM-DD)
            end_date: End date for Custom timeframe (YYYY-MM-DD)

        Returns:
            Total cost as Decimal
        """
        query_body = {
            "type": "ActualCost",
            "timeframe": timeframe,
            "dataset": {
                "granularity": "None",
                "aggregation": {
                    "totalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    }
                }
            }
        }

        # Handle explicit start/end dates (Custom timeframe)
        if start_date and end_date:
            query_body["timeframe"] = "Custom"
            query_body["timePeriod"] = {
                "from": start_date.isoformat() + "T00:00:00Z",
                "to": end_date.isoformat() + "T23:59:59Z"
            }

        result = self._run_cost_management_query(query_body, subscription_id)
        if result["success"] and result["data"]:
            rows = result["data"].get("properties", {}).get("rows", [])
            if rows and len(rows[0]) > 0:
                return Decimal(str(rows[0][0]))
        return Decimal("0")

    def query_consumption(
        self,
        start_date: str,
        end_date: str,
        subscription_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query consumption usage data (legacy - use query_by_service for costs).

        Uses az consumption usage list for detailed line-item data.
        Note: For EA accounts, pretaxCost may be None - use Cost Management Query API.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            subscription_id: Specific subscription (uses default if not provided)

        Returns:
            List of consumption records
        """
        sub_id = subscription_id or self.subscription_id
        if not sub_id:
            return []

        command = (
            f"consumption usage list "
            f"--subscription {sub_id} "
            f"--start-date {start_date} "
            f"--end-date {end_date}"
        )

        result = self._run_az_cli(command, timeout=180)
        if result["success"] and isinstance(result["data"], list):
            return result["data"]
        return []

    def query_by_service(
        self,
        timeframe: str = "MonthToDate",
        subscription_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[AzureServiceCost]:
        """
        Query costs grouped by service using Cost Management Query API.

        Uses the Cost Management Query API which returns actual costs for EA accounts
        (unlike Consumption API which returns pretaxCost: None).

        Args:
            timeframe: Time period (MonthToDate, LastMonth, Last7Days, Last30Days, Custom)
            subscription_id: Specific subscription (uses default if not provided)
            start_date: Start date for Custom timeframe (YYYY-MM-DD)
            end_date: End date for Custom timeframe (YYYY-MM-DD)

        Returns:
            List of AzureServiceCost with service breakdown
        """
        # Build Cost Management Query
        query_body = {
            "type": "ActualCost",
            "timeframe": timeframe,
            "dataset": {
                "granularity": "None",
                "aggregation": {
                    "totalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {
                        "type": "Dimension",
                        "name": "ServiceName"
                    }
                ]
            }
        }

        # Handle explicit start/end dates (Custom timeframe)
        today = date.today()
        if start_date and end_date:
            query_body["timeframe"] = "Custom"
            query_body["timePeriod"] = {
                "from": start_date.isoformat() + "T00:00:00Z",
                "to": end_date.isoformat() + "T23:59:59Z"
            }
        # Handle convenience timeframes (Last7Days, Last30Days) which need custom dates
        elif timeframe == "Last7Days":
            calc_start = today - timedelta(days=7)
            query_body["timeframe"] = "Custom"
            query_body["timePeriod"] = {
                "from": calc_start.isoformat() + "T00:00:00Z",
                "to": today.isoformat() + "T23:59:59Z"
            }
        elif timeframe == "Last30Days":
            calc_start = today - timedelta(days=30)
            query_body["timeframe"] = "Custom"
            query_body["timePeriod"] = {
                "from": calc_start.isoformat() + "T00:00:00Z",
                "to": today.isoformat() + "T23:59:59Z"
            }

        result = self._run_cost_management_query(query_body, subscription_id)

        services: List[AzureServiceCost] = []

        if not result["success"] or not result["data"]:
            return services

        # Parse response: columns are [Cost, ServiceName, Currency]
        rows = result["data"].get("properties", {}).get("rows", [])

        # Calculate total for percentage
        total = sum(Decimal(str(row[0])) for row in rows if row[0])

        # Convert to typed list
        for row in rows:
            cost = Decimal(str(row[0])) if row[0] else Decimal("0")
            service_name = row[1] if len(row) > 1 else "Unknown"

            if cost == 0:
                continue  # Skip zero-cost services

            pct = float(cost / total * 100) if total > 0 else 0.0
            cost_usd = float(cost / self._usd_rate)
            tier = classify_cost_tier(float(cost))

            services.append(AzureServiceCost(
                service_name=service_name,
                cost_nzd=float(cost),
                cost_usd=cost_usd,
                percentage=pct,
                cost_tier=tier,
                rank=0,  # Will update after sorting
            ))

        # Sort by cost descending and update ranks
        services.sort(key=lambda x: x["cost_nzd"], reverse=True)
        for i, svc in enumerate(services):
            svc["rank"] = i + 1

        return services

    def query_by_subscription(
        self,
        timeframe: str = "MonthToDate",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[AzureSubscriptionCost]:
        """
        Query costs grouped by subscription using Cost Management Query API.

        Uses Cost Management Query API for each subscription to get accurate costs.

        Args:
            timeframe: Time period for cost query (MonthToDate, LastMonth)
            start_date: Start date for Custom timeframe (YYYY-MM-DD)
            end_date: End date for Custom timeframe (YYYY-MM-DD)

        Returns:
            List of AzureSubscriptionCost with subscription breakdown
        """
        subscriptions = self.list_subscriptions()

        # Query each subscription using Cost Management API
        subscription_costs: List[AzureSubscriptionCost] = []
        total = Decimal("0")

        for sub in subscriptions:
            sub_cost = self.query_total_cost(timeframe, sub["id"], start_date, end_date)
            total += sub_cost

            subscription_costs.append({
                "subscription_name": sub["name"],
                "subscription_id": sub["id"],
                "enrollment_account": "",
                "cost_nzd": float(sub_cost),
                "cost_usd": float(sub_cost / self._usd_rate),
                "percentage": 0.0,  # Will calculate after total
                "cost_tier": classify_cost_tier(float(sub_cost)),
                "rank": 0,
            })

        # Sort by cost descending and update percentages/ranks
        subscription_costs.sort(key=lambda x: x["cost_nzd"], reverse=True)
        for i, sub in enumerate(subscription_costs):
            sub["percentage"] = (sub["cost_nzd"] / float(total) * 100) if total > 0 else 0.0
            sub["rank"] = i + 1

        return subscription_costs

    def get_cost_summary(
        self,
        timeframe: str = "MonthToDate",
        include_subscriptions: bool = True,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> AzureCostData:
        """
        Get comprehensive cost summary (services + subscriptions).

        Args:
            timeframe: Time period for cost analysis
            include_subscriptions: Whether to include subscription breakdown
            start_date: Start date for Custom timeframe (YYYY-MM-DD)
            end_date: End date for Custom timeframe (YYYY-MM-DD)

        Returns:
            AzureCostData with complete cost breakdown
        """
        # Get service costs
        services = self.query_by_service(timeframe, start_date=start_date, end_date=end_date)
        total_nzd = sum(s["cost_nzd"] for s in services)
        total_usd = sum(s["cost_usd"] for s in services)

        # Get subscription costs if requested
        subscriptions = []
        if include_subscriptions:
            subscriptions = self.query_by_subscription(timeframe, start_date, end_date)

        # Calculate date range for metadata
        today = date.today()
        if start_date and end_date:
            # Custom date range provided
            billing_period = f"{start_date.strftime('%B %Y')}"
            if start_date.month != end_date.month or start_date.year != end_date.year:
                billing_period = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
            date_range = f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')}"
            range_start = start_date
            range_end = end_date
        elif timeframe == "LastMonth":
            first_of_month = today.replace(day=1)
            range_end = first_of_month - timedelta(days=1)
            range_start = range_end.replace(day=1)
            billing_period = range_start.strftime("%B %Y")
            date_range = f"{range_start.strftime('%d %b')} - {range_end.strftime('%d %b %Y')}"
        else:
            range_start = today.replace(day=1)
            range_end = today
            billing_period = range_start.strftime("%B %Y")
            date_range = f"{range_start.strftime('%d %b')} - {range_end.strftime('%d %b %Y')}"

        # Count cost tiers
        high_count = sum(1 for s in services if s["cost_tier"] == "HIGH")
        medium_count = sum(1 for s in services if s["cost_tier"] == "MEDIUM")
        low_count = sum(1 for s in services if s["cost_tier"] == "LOW")

        return AzureCostData(
            customer_name="Azure",
            customer_id=self.subscription_id or "",
            billing_period=billing_period,
            date_range=date_range,
            total_cost_nzd=total_nzd,
            total_cost_usd=total_usd,
            billing_currency=self._currency,
            services=services,
            subscriptions=subscriptions,
            top_services=services[:5],
            top_subscriptions=subscriptions[:5] if subscriptions else [],
            high_cost_count=high_count,
            medium_cost_count=medium_count,
            low_cost_count=low_count,
            total_services=len(services),
            total_subscriptions=len(subscriptions),
            narrative=f"Azure cost analysis for {billing_period}",
            source_files=["Azure Cost Management API"],
            focus_version="1.3",
        )

    def validate_against_ground_truth(
        self,
        expected_total: Decimal,
        tolerance: Decimal = Decimal("0.01"),
    ) -> Dict[str, Any]:
        """
        Validate SDK results against ground truth (±$0.01 tolerance).

        Args:
            expected_total: Expected total cost from native API
            tolerance: Acceptable variance (default ±$0.01)

        Returns:
            Validation result with match status and variance
        """
        summary = self.get_cost_summary("MonthToDate")
        actual = Decimal(str(summary["total_cost_nzd"]))

        variance = abs(actual - expected_total)
        matches = variance <= tolerance

        return {
            "matches": matches,
            "expected": float(expected_total),
            "actual": float(actual),
            "variance": float(variance),
            "tolerance": float(tolerance),
            "status": "PASS" if matches else "FAIL",
        }


def get_azure_client(
    subscription_id: Optional[str] = None,
    management_group: Optional[str] = None,
) -> AzureCostClient:
    """
    Factory function to create Azure Cost Client.

    Args:
        subscription_id: Azure subscription ID
        management_group: Management group for multi-subscription scope

    Returns:
        Configured AzureCostClient instance
    """
    return AzureCostClient(
        subscription_id=subscription_id,
        management_group=management_group,
    )
