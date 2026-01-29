# =============================================================================
# Azure MCP Validators
# =============================================================================
# ADLC v3.0.0 - Validators for Azure MCP servers
# =============================================================================

"""Azure-specific validators for MCP cross-validation.

This module provides validators for Azure MCP servers, cross-validating
against native Azure CLI APIs with >= 99.5% accuracy target.

Environment Variables:
    AZURE_SUBSCRIPTION_ID: Azure subscription for resource operations
    AZURE_TENANT_ID: Azure AD tenant for identity operations
    AZURE_RESOURCE_GROUP: Default resource group (optional)
"""

import os
from datetime import datetime, timedelta
from typing import Any

from ..core.constants import COST_QUERY_TIMEOUT, FINANCIAL_TOLERANCE
from ..core.types import FieldComparison
from .base import BaseValidator


class AzureBaseValidator(BaseValidator):
    """Base class for Azure validators.

    Provides common Azure CLI command handling and authentication.
    """

    # Azure uses subscription ID instead of profiles
    subscription_env_var: str = "AZURE_SUBSCRIPTION_ID"

    def __init__(
        self,
        subscription_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Azure validator.

        Args:
            subscription_id: Azure subscription ID (defaults to env var)
            **kwargs: Additional arguments passed to BaseValidator
        """
        self.subscription_id = subscription_id or os.environ.get(self.subscription_env_var)
        super().__init__(**kwargs)

    def run_azure_command(self, command: str) -> dict[str, Any]:
        """Execute an Azure CLI command and return JSON output.

        Args:
            command: Azure CLI command to execute

        Returns:
            Parsed JSON response
        """
        # Add subscription if specified and not already in command
        if self.subscription_id and "--subscription" not in command:
            command = f"{command} --subscription {self.subscription_id}"

        # Ensure JSON output
        if "-o json" not in command and "--output json" not in command:
            command = f"{command} -o json"

        return self.run_cli_command(command)


class AzureResourceManagerValidator(AzureBaseValidator):
    """Validator for azure-resource-manager MCP server.

    Cross-validates against: az resource list
    Subscription: AZURE_SUBSCRIPTION_ID

    Validates:
    - Resource count
    - Resource types
    - Resource names
    - Resource locations
    """

    server_name = "azure-resource-manager"
    subscription_env_var = "AZURE_SUBSCRIPTION_ID"
    native_command = "az resource list"

    def __init__(
        self,
        subscription_id: str | None = None,
        resource_group: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Resource Manager validator.

        Args:
            subscription_id: Azure subscription ID
            resource_group: Optional resource group filter
            **kwargs: Additional arguments passed to AzureBaseValidator
        """
        super().__init__(subscription_id=subscription_id, **kwargs)
        self.resource_group = resource_group or os.environ.get("AZURE_RESOURCE_GROUP")

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Resource Manager MCP server.

        Returns:
            Dictionary containing Azure resources
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Azure Resource Manager API.

        Returns:
            Dictionary containing Azure resources
        """
        command = self.native_command
        if self.resource_group:
            command = f"{command} --resource-group {self.resource_group}"

        resources = self.run_azure_command(command)
        # Wrap in dict for consistent handling
        return {"resources": resources if isinstance(resources, list) else []}

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Resource Manager MCP and native API results.

        Compares:
        - Resource count
        - Resource IDs
        - Resource names
        - Resource types
        - Resource locations

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_resources = mcp_data.get("resources", [])
        native_resources = native_data.get("resources", [])

        # Compare resource count
        comparisons.append(
            FieldComparison(
                field_path="resources.length",
                mcp_value=len(mcp_resources),
                native_value=len(native_resources),
                match=len(mcp_resources) == len(native_resources),
            )
        )

        # Build lookup by resource ID
        mcp_by_id = {r.get("id"): r for r in mcp_resources}
        native_by_id = {r.get("id"): r for r in native_resources}

        # Compare each resource
        all_ids = set(mcp_by_id.keys()) | set(native_by_id.keys())
        for resource_id in all_ids:
            mcp_resource = mcp_by_id.get(resource_id, {})
            native_resource = native_by_id.get(resource_id, {})

            # Resource exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"resources[{resource_id}].exists",
                    mcp_value=resource_id in mcp_by_id,
                    native_value=resource_id in native_by_id,
                    match=resource_id in mcp_by_id and resource_id in native_by_id,
                )
            )

            if mcp_resource and native_resource:
                # Compare name
                comparisons.append(
                    FieldComparison(
                        field_path=f"resources[{resource_id}].name",
                        mcp_value=mcp_resource.get("name"),
                        native_value=native_resource.get("name"),
                        match=mcp_resource.get("name") == native_resource.get("name"),
                    )
                )

                # Compare type
                comparisons.append(
                    FieldComparison(
                        field_path=f"resources[{resource_id}].type",
                        mcp_value=mcp_resource.get("type"),
                        native_value=native_resource.get("type"),
                        match=mcp_resource.get("type") == native_resource.get("type"),
                    )
                )

                # Compare location
                comparisons.append(
                    FieldComparison(
                        field_path=f"resources[{resource_id}].location",
                        mcp_value=mcp_resource.get("location"),
                        native_value=native_resource.get("location"),
                        match=mcp_resource.get("location") == native_resource.get("location"),
                    )
                )

        return comparisons


class AzureCostManagementValidator(AzureBaseValidator):
    """Validator for azure-cost-management MCP server.

    Cross-validates against: az consumption usage list
    Subscription: AZURE_SUBSCRIPTION_ID

    Note: Uses az consumption (built-in) instead of az costmanagement (extension).
    Requires Billing Reader or Cost Management Reader role.
    """

    server_name = "azure-cost-management"
    subscription_env_var = "AZURE_SUBSCRIPTION_ID"
    native_command = "az consumption usage list"

    def __init__(
        self,
        subscription_id: str | None = None,
        days_back: int = 7,
        **kwargs: Any,
    ) -> None:
        """Initialize the Cost Management validator.

        Args:
            subscription_id: Azure subscription ID
            days_back: Number of days to query (default 7)
            **kwargs: Additional arguments passed to AzureBaseValidator
        """
        super().__init__(
            subscription_id=subscription_id,
            timeout=kwargs.pop("timeout", COST_QUERY_TIMEOUT),
            **kwargs,
        )
        self.days_back = days_back

    def _get_time_period(self) -> tuple[str, str]:
        """Get start and end dates for cost query.

        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=self.days_back)
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Cost Management MCP server.

        Returns:
            Dictionary containing cost data
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Azure Consumption API.

        Uses az consumption usage list (built-in) which provides:
        - Usage details with cost
        - Billing period information
        - Resource usage metrics

        Returns:
            Dictionary containing consumption/cost data
        """
        start_date, end_date = self._get_time_period()

        # Use az consumption usage list with date filters
        command = f"{self.native_command} --start-date {start_date} --end-date {end_date}"

        try:
            usage_data = self.run_azure_command(command)
            # Wrap in consistent structure
            return {
                "usage": usage_data if isinstance(usage_data, list) else [],
                "period": {"start": start_date, "end": end_date},
            }
        except Exception as e:
            # Handle case where consumption data is not available
            return {
                "usage": [],
                "period": {"start": start_date, "end": end_date},
                "error": str(e),
            }

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Cost Management MCP and native API results.

        Compares:
        - Usage record count
        - Total pretax cost (with financial tolerance)
        - Time period consistency

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_usage = mcp_data.get("usage", [])
        native_usage = native_data.get("usage", [])

        # Compare usage record count
        comparisons.append(
            FieldComparison(
                field_path="usage.length",
                mcp_value=len(mcp_usage),
                native_value=len(native_usage),
                match=len(mcp_usage) == len(native_usage),
            )
        )

        # Compare time period
        mcp_period = mcp_data.get("period", {})
        native_period = native_data.get("period", {})
        comparisons.append(
            FieldComparison(
                field_path="period.start",
                mcp_value=mcp_period.get("start"),
                native_value=native_period.get("start"),
                match=mcp_period.get("start") == native_period.get("start"),
            )
        )

        # Compare total costs with tolerance
        # az consumption usage list returns pretaxCost for each usage record
        mcp_total = sum(float(u.get("pretaxCost", 0) or 0) for u in mcp_usage)
        native_total = sum(float(u.get("pretaxCost", 0) or 0) for u in native_usage)

        if native_total == 0:
            match = mcp_total == 0
        else:
            diff_pct = abs(mcp_total - native_total) / native_total
            match = diff_pct <= FINANCIAL_TOLERANCE

        comparisons.append(
            FieldComparison(
                field_path="totalPretaxCost",
                mcp_value=mcp_total,
                native_value=native_total,
                match=match,
                tolerance_applied=FINANCIAL_TOLERANCE,
                notes=f"Financial tolerance: {FINANCIAL_TOLERANCE * 100}%",
            )
        )

        return comparisons


class AzurePolicyValidator(AzureBaseValidator):
    """Validator for azure-policy MCP server.

    Cross-validates against: az policy assignment list
    Subscription: AZURE_SUBSCRIPTION_ID

    Validates:
    - Policy assignment count
    - Assignment names
    - Policy definition IDs
    - Enforcement modes
    """

    server_name = "azure-policy"
    subscription_env_var = "AZURE_SUBSCRIPTION_ID"
    native_command = "az policy assignment list"

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Azure Policy MCP server.

        Returns:
            Dictionary containing policy assignments
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Azure Policy API.

        Returns:
            Dictionary containing policy assignments
        """
        assignments = self.run_azure_command(self.native_command)
        return {"assignments": assignments if isinstance(assignments, list) else []}

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Azure Policy MCP and native API results.

        Compares:
        - Assignment count
        - Assignment names
        - Policy definition IDs
        - Enforcement modes
        - Scopes

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_assignments = mcp_data.get("assignments", [])
        native_assignments = native_data.get("assignments", [])

        # Compare assignment count
        comparisons.append(
            FieldComparison(
                field_path="assignments.length",
                mcp_value=len(mcp_assignments),
                native_value=len(native_assignments),
                match=len(mcp_assignments) == len(native_assignments),
            )
        )

        # Build lookup by assignment ID
        mcp_by_id = {a.get("id"): a for a in mcp_assignments}
        native_by_id = {a.get("id"): a for a in native_assignments}

        # Compare each assignment
        all_ids = set(mcp_by_id.keys()) | set(native_by_id.keys())
        for assignment_id in all_ids:
            mcp_assignment = mcp_by_id.get(assignment_id, {})
            native_assignment = native_by_id.get(assignment_id, {})

            # Assignment exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"assignments[{assignment_id}].exists",
                    mcp_value=assignment_id in mcp_by_id,
                    native_value=assignment_id in native_by_id,
                    match=assignment_id in mcp_by_id and assignment_id in native_by_id,
                )
            )

            if mcp_assignment and native_assignment:
                # Compare name
                comparisons.append(
                    FieldComparison(
                        field_path=f"assignments[{assignment_id}].name",
                        mcp_value=mcp_assignment.get("name"),
                        native_value=native_assignment.get("name"),
                        match=mcp_assignment.get("name") == native_assignment.get("name"),
                    )
                )

                # Compare policy definition ID
                comparisons.append(
                    FieldComparison(
                        field_path=f"assignments[{assignment_id}].policyDefinitionId",
                        mcp_value=mcp_assignment.get("policyDefinitionId"),
                        native_value=native_assignment.get("policyDefinitionId"),
                        match=mcp_assignment.get("policyDefinitionId") == native_assignment.get("policyDefinitionId"),
                    )
                )

                # Compare enforcement mode
                comparisons.append(
                    FieldComparison(
                        field_path=f"assignments[{assignment_id}].enforcementMode",
                        mcp_value=mcp_assignment.get("enforcementMode"),
                        native_value=native_assignment.get("enforcementMode"),
                        match=mcp_assignment.get("enforcementMode") == native_assignment.get("enforcementMode"),
                    )
                )

        return comparisons


class AzureSecurityCenterValidator(AzureBaseValidator):
    """Validator for azure-security-center MCP server.

    Cross-validates against: az security assessment list
    Subscription: AZURE_SUBSCRIPTION_ID

    Note: Requires Microsoft Defender for Cloud enabled.
    """

    server_name = "azure-security-center"
    subscription_env_var = "AZURE_SUBSCRIPTION_ID"
    native_command = "az security assessment list"

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Security Center MCP server.

        Returns:
            Dictionary containing security assessments
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Azure Security Center API.

        Returns:
            Dictionary containing security assessments
        """
        assessments = self.run_azure_command(self.native_command)
        return {"assessments": assessments if isinstance(assessments, list) else []}

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Security Center MCP and native API results.

        Compares:
        - Assessment count
        - Assessment names
        - Status codes
        - Resource details

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_assessments = mcp_data.get("assessments", [])
        native_assessments = native_data.get("assessments", [])

        # Compare assessment count
        comparisons.append(
            FieldComparison(
                field_path="assessments.length",
                mcp_value=len(mcp_assessments),
                native_value=len(native_assessments),
                match=len(mcp_assessments) == len(native_assessments),
            )
        )

        # Build lookup by assessment ID
        mcp_by_id = {a.get("id"): a for a in mcp_assessments}
        native_by_id = {a.get("id"): a for a in native_assessments}

        # Compare each assessment
        all_ids = set(mcp_by_id.keys()) | set(native_by_id.keys())
        for assessment_id in all_ids:
            mcp_assessment = mcp_by_id.get(assessment_id, {})
            native_assessment = native_by_id.get(assessment_id, {})

            # Assessment exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"assessments[{assessment_id}].exists",
                    mcp_value=assessment_id in mcp_by_id,
                    native_value=assessment_id in native_by_id,
                    match=assessment_id in mcp_by_id and assessment_id in native_by_id,
                )
            )

            if mcp_assessment and native_assessment:
                # Compare display name
                comparisons.append(
                    FieldComparison(
                        field_path=f"assessments[{assessment_id}].displayName",
                        mcp_value=mcp_assessment.get("displayName"),
                        native_value=native_assessment.get("displayName"),
                        match=mcp_assessment.get("displayName") == native_assessment.get("displayName"),
                    )
                )

                # Compare status code
                mcp_status = mcp_assessment.get("status", {}).get("code")
                native_status = native_assessment.get("status", {}).get("code")
                comparisons.append(
                    FieldComparison(
                        field_path=f"assessments[{assessment_id}].status.code",
                        mcp_value=mcp_status,
                        native_value=native_status,
                        match=mcp_status == native_status,
                    )
                )

                # Compare resource details type
                mcp_resource_type = mcp_assessment.get("resourceDetails", {}).get("source")
                native_resource_type = native_assessment.get("resourceDetails", {}).get("source")
                comparisons.append(
                    FieldComparison(
                        field_path=f"assessments[{assessment_id}].resourceDetails.source",
                        mcp_value=mcp_resource_type,
                        native_value=native_resource_type,
                        match=mcp_resource_type == native_resource_type,
                    )
                )

        return comparisons


class AzureEntraValidator(AzureBaseValidator):
    """Validator for azure-entra MCP server (Azure AD / Entra ID).

    Cross-validates against: az ad user list
    Tenant: AZURE_TENANT_ID

    Note: Requires Azure AD Graph permissions (User.Read.All).
    """

    server_name = "azure-entra"
    subscription_env_var = "AZURE_TENANT_ID"  # Uses tenant instead of subscription
    native_command = "az ad user list"

    def __init__(
        self,
        tenant_id: str | None = None,
        max_results: int = 100,
        **kwargs: Any,
    ) -> None:
        """Initialize the Entra ID validator.

        Args:
            tenant_id: Azure AD tenant ID
            max_results: Maximum users to retrieve (default 100)
            **kwargs: Additional arguments passed to AzureBaseValidator
        """
        # Use tenant_id instead of subscription_id
        self.tenant_id = tenant_id or os.environ.get("AZURE_TENANT_ID")
        self.max_results = max_results
        super().__init__(**kwargs)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Entra ID MCP server.

        Returns:
            Dictionary containing Azure AD users
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from Azure Entra ID API.

        Returns:
            Dictionary containing Azure AD users
        """
        # Note: az ad commands don't use --subscription, they use the logged-in tenant
        # Use --filter with $top for newer az CLI versions
        command = f'az ad user list --filter "accountEnabled eq true" --query "[:{self.max_results}]"'
        users = self.run_cli_command(command)
        return {"users": users if isinstance(users, list) else []}

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Entra ID MCP and native API results.

        Compares:
        - User count
        - User principal names
        - Display names
        - Account enabled status

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_users = mcp_data.get("users", [])
        native_users = native_data.get("users", [])

        # Compare user count
        comparisons.append(
            FieldComparison(
                field_path="users.length",
                mcp_value=len(mcp_users),
                native_value=len(native_users),
                match=len(mcp_users) == len(native_users),
            )
        )

        # Build lookup by user ID (object ID)
        mcp_by_id = {u.get("id"): u for u in mcp_users}
        native_by_id = {u.get("id"): u for u in native_users}

        # Compare each user
        all_ids = set(mcp_by_id.keys()) | set(native_by_id.keys())
        for user_id in all_ids:
            mcp_user = mcp_by_id.get(user_id, {})
            native_user = native_by_id.get(user_id, {})

            # User exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"users[{user_id}].exists",
                    mcp_value=user_id in mcp_by_id,
                    native_value=user_id in native_by_id,
                    match=user_id in mcp_by_id and user_id in native_by_id,
                )
            )

            if mcp_user and native_user:
                # Compare user principal name
                comparisons.append(
                    FieldComparison(
                        field_path=f"users[{user_id}].userPrincipalName",
                        mcp_value=mcp_user.get("userPrincipalName"),
                        native_value=native_user.get("userPrincipalName"),
                        match=mcp_user.get("userPrincipalName") == native_user.get("userPrincipalName"),
                    )
                )

                # Compare display name
                comparisons.append(
                    FieldComparison(
                        field_path=f"users[{user_id}].displayName",
                        mcp_value=mcp_user.get("displayName"),
                        native_value=native_user.get("displayName"),
                        match=mcp_user.get("displayName") == native_user.get("displayName"),
                    )
                )

                # Compare account enabled
                comparisons.append(
                    FieldComparison(
                        field_path=f"users[{user_id}].accountEnabled",
                        mcp_value=mcp_user.get("accountEnabled"),
                        native_value=native_user.get("accountEnabled"),
                        match=mcp_user.get("accountEnabled") == native_user.get("accountEnabled"),
                    )
                )

                # Compare mail
                comparisons.append(
                    FieldComparison(
                        field_path=f"users[{user_id}].mail",
                        mcp_value=mcp_user.get("mail"),
                        native_value=native_user.get("mail"),
                        match=mcp_user.get("mail") == native_user.get("mail"),
                    )
                )

        return comparisons
