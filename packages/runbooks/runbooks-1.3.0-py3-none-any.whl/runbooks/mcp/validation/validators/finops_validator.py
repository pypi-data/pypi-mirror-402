# =============================================================================
# FinOps MCP Validators
# =============================================================================
# ADLC v3.0.0 - Validators for FinOps MCP servers
# =============================================================================

"""FinOps-specific validators for MCP cross-validation.

This module provides validators for FinOps MCP servers, cross-validating
cost data and allocations with >= 99.5% accuracy target.

Supported Servers:
    - finops-focus-aggregator: FOCUS 1.3 cost data aggregation
    - infracost: Pre-deployment cost estimation
    - kubecost: Kubernetes cost allocation

Environment Variables:
    FOCUS_DATA_PATH: Path to FOCUS 1.3 export files
    INFRACOST_API_KEY: Infracost Cloud API key (optional)
    KUBECOST_ENDPOINT: Kubecost API endpoint (e.g., http://kubecost:9090)
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.constants import COST_QUERY_TIMEOUT, FINANCIAL_TOLERANCE
from ..core.types import FieldComparison
from .base import BaseValidator


class FOCUSAggregatorValidator(BaseValidator):
    """Validator for finops-focus-aggregator MCP server.

    Cross-validates against: FOCUS 1.3 schema specification
    Data Source: Local FOCUS export files or cloud provider exports

    FOCUS 1.3 Schema Reference:
    - BillingAccountId, BillingAccountName
    - ChargeDescription, ChargeFrequency, ChargeType
    - BilledCost, EffectiveCost, ListCost
    - ServiceName, ServiceCategory
    - UsageDateStart, UsageDateEnd
    """

    server_name = "finops-focus-aggregator"
    profile_env_var = "FOCUS_DATA_PATH"
    native_command = "focus-validate"  # Schema validation

    # FOCUS 1.3 required columns
    FOCUS_REQUIRED_COLUMNS = [
        "BillingAccountId",
        "ChargeDescription",
        "ChargeType",
        "BilledCost",
        "ServiceName",
        "UsageDateStart",
    ]

    def __init__(
        self,
        focus_data_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the FOCUS aggregator validator.

        Args:
            focus_data_path: Path to FOCUS data files
            **kwargs: Additional arguments passed to BaseValidator
        """
        self.focus_data_path = focus_data_path or os.environ.get("FOCUS_DATA_PATH")
        super().__init__(
            timeout=kwargs.pop("timeout", COST_QUERY_TIMEOUT),
            **kwargs,
        )

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from FOCUS Aggregator MCP server.

        Returns:
            Dictionary containing aggregated FOCUS data
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Load and validate FOCUS data from local files.

        Returns:
            Dictionary containing FOCUS data with schema metadata
        """
        if not self.focus_data_path:
            return {
                "schema_version": "1.3",
                "columns": [],
                "row_count": 0,
                "total_billed_cost": 0.0,
                "validation_errors": ["FOCUS_DATA_PATH not configured"],
            }

        path = Path(self.focus_data_path)
        if not path.exists():
            return {
                "schema_version": "1.3",
                "columns": [],
                "row_count": 0,
                "total_billed_cost": 0.0,
                "validation_errors": [f"Path not found: {path}"],
            }

        # Try to load FOCUS data (CSV or Parquet)
        try:
            # For now, return schema metadata
            # In production, would parse actual FOCUS files
            return {
                "schema_version": "1.3",
                "columns": self.FOCUS_REQUIRED_COLUMNS,
                "row_count": 0,  # Would count actual rows
                "total_billed_cost": 0.0,  # Would sum BilledCost
                "validation_errors": [],
                "path": str(path),
            }
        except Exception as e:
            return {
                "schema_version": "1.3",
                "columns": [],
                "row_count": 0,
                "total_billed_cost": 0.0,
                "validation_errors": [str(e)],
            }

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare FOCUS Aggregator MCP and native data.

        Compares:
        - Schema version compliance
        - Required columns presence
        - Row count consistency
        - Total cost accuracy (with financial tolerance)

        Args:
            mcp_data: Data from MCP server
            native_data: Data from local FOCUS files

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        # Compare schema version
        comparisons.append(
            FieldComparison(
                field_path="schema_version",
                mcp_value=mcp_data.get("schema_version"),
                native_value=native_data.get("schema_version"),
                match=mcp_data.get("schema_version") == native_data.get("schema_version"),
            )
        )

        # Compare required columns
        mcp_columns = set(mcp_data.get("columns", []))
        native_columns = set(native_data.get("columns", []))
        required_columns = set(self.FOCUS_REQUIRED_COLUMNS)

        mcp_has_required = required_columns.issubset(mcp_columns)
        native_has_required = required_columns.issubset(native_columns)

        comparisons.append(
            FieldComparison(
                field_path="columns.has_required",
                mcp_value=mcp_has_required,
                native_value=native_has_required,
                match=mcp_has_required == native_has_required,
                notes=f"Required: {self.FOCUS_REQUIRED_COLUMNS}",
            )
        )

        # Compare row count
        comparisons.append(
            FieldComparison(
                field_path="row_count",
                mcp_value=mcp_data.get("row_count", 0),
                native_value=native_data.get("row_count", 0),
                match=mcp_data.get("row_count", 0) == native_data.get("row_count", 0),
            )
        )

        # Compare total cost with tolerance
        mcp_cost = float(mcp_data.get("total_billed_cost", 0))
        native_cost = float(native_data.get("total_billed_cost", 0))

        if native_cost == 0:
            match = mcp_cost == 0
        else:
            diff_pct = abs(mcp_cost - native_cost) / native_cost
            match = diff_pct <= FINANCIAL_TOLERANCE

        comparisons.append(
            FieldComparison(
                field_path="total_billed_cost",
                mcp_value=mcp_cost,
                native_value=native_cost,
                match=match,
                tolerance_applied=FINANCIAL_TOLERANCE,
                notes=f"Financial tolerance: {FINANCIAL_TOLERANCE * 100}%",
            )
        )

        # Compare validation errors
        mcp_errors = mcp_data.get("validation_errors", [])
        native_errors = native_data.get("validation_errors", [])
        comparisons.append(
            FieldComparison(
                field_path="validation_errors.count",
                mcp_value=len(mcp_errors),
                native_value=len(native_errors),
                match=len(mcp_errors) == len(native_errors),
            )
        )

        return comparisons


class InfracostValidator(BaseValidator):
    """Validator for infracost MCP server.

    Cross-validates against: infracost breakdown/diff commands
    Data Source: Infracost CLI or Infracost Cloud API

    Use Cases:
    - Pre-deployment cost estimation
    - PR cost change analysis
    - Resource-level cost breakdown
    """

    server_name = "infracost"
    profile_env_var = "INFRACOST_API_KEY"
    native_command = "infracost breakdown --format json"

    def __init__(
        self,
        api_key: str | None = None,
        terraform_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Infracost validator.

        Args:
            api_key: Infracost API key (optional, for Cloud features)
            terraform_path: Path to Terraform project
            **kwargs: Additional arguments passed to BaseValidator
        """
        self.api_key = api_key or os.environ.get("INFRACOST_API_KEY")
        self.terraform_path = terraform_path or os.environ.get("TERRAFORM_PATH", ".")
        super().__init__(**kwargs)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Infracost MCP server.

        Returns:
            Dictionary containing cost estimation data
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Infracost CLI.

        Returns:
            Dictionary containing cost estimation data
        """
        try:
            command = f"{self.native_command} --path {self.terraform_path}"
            return self.run_cli_command(command)
        except Exception as e:
            # Return empty structure if infracost not available
            return {
                "version": "0.0.0",
                "currency": "USD",
                "projects": [],
                "totalHourlyCost": "0",
                "totalMonthlyCost": "0",
                "error": str(e),
            }

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Infracost MCP and native CLI results.

        Compares:
        - Project count
        - Total monthly cost (with financial tolerance)
        - Currency
        - Resource counts

        Args:
            mcp_data: Data from MCP server
            native_data: Data from Infracost CLI

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        # Compare currency
        comparisons.append(
            FieldComparison(
                field_path="currency",
                mcp_value=mcp_data.get("currency"),
                native_value=native_data.get("currency"),
                match=mcp_data.get("currency") == native_data.get("currency"),
            )
        )

        # Compare project count
        mcp_projects = mcp_data.get("projects", [])
        native_projects = native_data.get("projects", [])
        comparisons.append(
            FieldComparison(
                field_path="projects.length",
                mcp_value=len(mcp_projects),
                native_value=len(native_projects),
                match=len(mcp_projects) == len(native_projects),
            )
        )

        # Compare total monthly cost with tolerance
        try:
            mcp_cost = float(mcp_data.get("totalMonthlyCost", 0))
            native_cost = float(native_data.get("totalMonthlyCost", 0))
        except (ValueError, TypeError):
            mcp_cost = 0.0
            native_cost = 0.0

        if native_cost == 0:
            match = mcp_cost == 0
        else:
            diff_pct = abs(mcp_cost - native_cost) / native_cost
            match = diff_pct <= FINANCIAL_TOLERANCE

        comparisons.append(
            FieldComparison(
                field_path="totalMonthlyCost",
                mcp_value=mcp_cost,
                native_value=native_cost,
                match=match,
                tolerance_applied=FINANCIAL_TOLERANCE,
                notes=f"Financial tolerance: {FINANCIAL_TOLERANCE * 100}%",
            )
        )

        # Compare each project
        for i, (mcp_proj, native_proj) in enumerate(zip(mcp_projects, native_projects)):
            # Compare project name
            comparisons.append(
                FieldComparison(
                    field_path=f"projects[{i}].name",
                    mcp_value=mcp_proj.get("name"),
                    native_value=native_proj.get("name"),
                    match=mcp_proj.get("name") == native_proj.get("name"),
                )
            )

            # Compare resource count
            mcp_resources = mcp_proj.get("breakdown", {}).get("resources", [])
            native_resources = native_proj.get("breakdown", {}).get("resources", [])
            comparisons.append(
                FieldComparison(
                    field_path=f"projects[{i}].resources.length",
                    mcp_value=len(mcp_resources),
                    native_value=len(native_resources),
                    match=len(mcp_resources) == len(native_resources),
                )
            )

        return comparisons


class KubecostValidator(BaseValidator):
    """Validator for kubecost MCP server.

    Cross-validates against: Kubecost API endpoints
    Data Source: Kubecost service running in Kubernetes cluster

    Use Cases:
    - Namespace cost allocation
    - Workload cost breakdown
    - Efficiency recommendations
    """

    server_name = "kubecost"
    profile_env_var = "KUBECOST_ENDPOINT"
    native_command = "curl"  # Uses HTTP API

    # Kubecost API endpoints
    ALLOCATION_ENDPOINT = "/model/allocation"
    ASSETS_ENDPOINT = "/model/assets"

    def __init__(
        self,
        endpoint: str | None = None,
        window: str = "7d",
        **kwargs: Any,
    ) -> None:
        """Initialize the Kubecost validator.

        Args:
            endpoint: Kubecost API endpoint (e.g., http://kubecost:9090)
            window: Time window for cost query (default 7d)
            **kwargs: Additional arguments passed to BaseValidator
        """
        self.endpoint = endpoint or os.environ.get("KUBECOST_ENDPOINT", "http://localhost:9090")
        self.window = window
        super().__init__(
            timeout=kwargs.pop("timeout", COST_QUERY_TIMEOUT),
            **kwargs,
        )

    def _call_kubecost_api(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
        """Call Kubecost API endpoint.

        Args:
            path: API path (e.g., /model/allocation)
            params: Query parameters

        Returns:
            JSON response from Kubecost
        """
        url = f"{self.endpoint}{path}"
        if params:
            param_str = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{param_str}"

        command = f'curl -s "{url}"'
        return self.run_cli_command(command)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Kubecost MCP server.

        Returns:
            Dictionary containing K8s cost allocation data
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Kubecost API.

        Returns:
            Dictionary containing K8s cost allocation data
        """
        try:
            # Get allocation data
            allocation_data = self._call_kubecost_api(
                self.ALLOCATION_ENDPOINT,
                {"window": self.window, "aggregate": "namespace"},
            )

            return {
                "window": self.window,
                "allocations": allocation_data.get("data", []),
                "totalCost": sum(
                    a.get("totalCost", 0)
                    for alloc_list in allocation_data.get("data", [])
                    for a in (alloc_list.values() if isinstance(alloc_list, dict) else [])
                ),
            }
        except Exception as e:
            return {
                "window": self.window,
                "allocations": [],
                "totalCost": 0.0,
                "error": str(e),
            }

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Kubecost MCP and native API results.

        Compares:
        - Time window
        - Namespace count
        - Total cost (with financial tolerance)
        - Per-namespace costs

        Args:
            mcp_data: Data from MCP server
            native_data: Data from Kubecost API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        # Compare time window
        comparisons.append(
            FieldComparison(
                field_path="window",
                mcp_value=mcp_data.get("window"),
                native_value=native_data.get("window"),
                match=mcp_data.get("window") == native_data.get("window"),
            )
        )

        # Compare allocation count
        mcp_allocations = mcp_data.get("allocations", [])
        native_allocations = native_data.get("allocations", [])
        comparisons.append(
            FieldComparison(
                field_path="allocations.length",
                mcp_value=len(mcp_allocations),
                native_value=len(native_allocations),
                match=len(mcp_allocations) == len(native_allocations),
            )
        )

        # Compare total cost with tolerance
        mcp_cost = float(mcp_data.get("totalCost", 0))
        native_cost = float(native_data.get("totalCost", 0))

        if native_cost == 0:
            match = mcp_cost == 0
        else:
            diff_pct = abs(mcp_cost - native_cost) / native_cost
            match = diff_pct <= FINANCIAL_TOLERANCE

        comparisons.append(
            FieldComparison(
                field_path="totalCost",
                mcp_value=mcp_cost,
                native_value=native_cost,
                match=match,
                tolerance_applied=FINANCIAL_TOLERANCE,
                notes=f"Financial tolerance: {FINANCIAL_TOLERANCE * 100}%",
            )
        )

        return comparisons
