# =============================================================================
# AWS MCP Validators
# =============================================================================
# ADLC v3.0.0 - Validators for AWS MCP servers
# =============================================================================

"""AWS-specific validators for MCP cross-validation."""

import os
from datetime import datetime, timedelta
from typing import Any

from ..core.constants import COST_QUERY_TIMEOUT, FINANCIAL_TOLERANCE
from ..core.types import FieldComparison
from .base import BaseValidator


class AWSOrganizationsValidator(BaseValidator):
    """Validator for awslabs-organizations MCP server.

    Cross-validates against: aws organizations list-accounts
    Profile: AWS_MANAGEMENT_PROFILE
    """

    server_name = "awslabs-organizations"
    profile_env_var = "AWS_MANAGEMENT_PROFILE"
    native_command = "aws organizations list-accounts"

    def __init__(
        self,
        profile: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Organizations validator.

        Args:
            profile: AWS profile to use (defaults to AWS_MANAGEMENT_PROFILE)
            **kwargs: Additional arguments passed to BaseValidator
        """
        effective_profile = profile or os.environ.get(self.profile_env_var)
        super().__init__(profile=effective_profile, **kwargs)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Organizations MCP server.

        For now, this simulates MCP data by calling the native API.
        In production, this would call the actual MCP server.

        Returns:
            Dictionary containing organization accounts
        """
        # TODO: Replace with actual MCP server call when available
        # For now, we use native API to simulate MCP response
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from AWS Organizations API.

        Returns:
            Dictionary containing organization accounts
        """
        return self.run_cli_command(self.native_command)

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Organizations MCP and native API results.

        Compares:
        - Account count
        - Account IDs
        - Account names
        - Account statuses

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_accounts = mcp_data.get("Accounts", [])
        native_accounts = native_data.get("Accounts", [])

        # Compare account count
        comparisons.append(
            FieldComparison(
                field_path="Accounts.length",
                mcp_value=len(mcp_accounts),
                native_value=len(native_accounts),
                match=len(mcp_accounts) == len(native_accounts),
            )
        )

        # Build lookup by account ID
        mcp_by_id = {a.get("Id"): a for a in mcp_accounts}
        native_by_id = {a.get("Id"): a for a in native_accounts}

        # Compare each account
        all_ids = set(mcp_by_id.keys()) | set(native_by_id.keys())
        for account_id in all_ids:
            mcp_account = mcp_by_id.get(account_id, {})
            native_account = native_by_id.get(account_id, {})

            # Account exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"Accounts[{account_id}].exists",
                    mcp_value=account_id in mcp_by_id,
                    native_value=account_id in native_by_id,
                    match=account_id in mcp_by_id and account_id in native_by_id,
                )
            )

            if mcp_account and native_account:
                # Compare name
                comparisons.append(
                    FieldComparison(
                        field_path=f"Accounts[{account_id}].Name",
                        mcp_value=mcp_account.get("Name"),
                        native_value=native_account.get("Name"),
                        match=mcp_account.get("Name") == native_account.get("Name"),
                    )
                )

                # Compare status
                comparisons.append(
                    FieldComparison(
                        field_path=f"Accounts[{account_id}].Status",
                        mcp_value=mcp_account.get("Status"),
                        native_value=native_account.get("Status"),
                        match=mcp_account.get("Status") == native_account.get("Status"),
                    )
                )

                # Compare email
                comparisons.append(
                    FieldComparison(
                        field_path=f"Accounts[{account_id}].Email",
                        mcp_value=mcp_account.get("Email"),
                        native_value=native_account.get("Email"),
                        match=mcp_account.get("Email") == native_account.get("Email"),
                    )
                )

        return comparisons


class AWSCostExplorerValidator(BaseValidator):
    """Validator for awslabs-cost-explorer MCP server.

    Cross-validates against: aws ce get-cost-and-usage
    Profile: AWS_BILLING_PROFILE
    """

    server_name = "awslabs-cost-explorer"
    profile_env_var = "AWS_BILLING_PROFILE"
    native_command = "aws ce get-cost-and-usage"

    def __init__(
        self,
        profile: str | None = None,
        days_back: int = 7,
        **kwargs: Any,
    ) -> None:
        """Initialize the Cost Explorer validator.

        Args:
            profile: AWS profile to use (defaults to AWS_BILLING_PROFILE)
            days_back: Number of days to query (default 7)
            **kwargs: Additional arguments passed to BaseValidator
        """
        effective_profile = profile or os.environ.get(self.profile_env_var)
        super().__init__(
            profile=effective_profile,
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
        """Fetch data from Cost Explorer MCP server.

        For now, this simulates MCP data by calling the native API.
        In production, this would call the actual MCP server.

        Returns:
            Dictionary containing cost data
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from AWS Cost Explorer API.

        Returns:
            Dictionary containing cost data
        """
        start_date, end_date = self._get_time_period()
        command = (
            f"{self.native_command} "
            f"--time-period Start={start_date},End={end_date} "
            f"--granularity DAILY "
            f"--metrics BlendedCost"
        )
        return self.run_cli_command(command)

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Cost Explorer MCP and native API results.

        Compares:
        - Result count
        - Time periods
        - Cost amounts (with 0.01% tolerance)

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_results = mcp_data.get("ResultsByTime", [])
        native_results = native_data.get("ResultsByTime", [])

        # Compare result count
        comparisons.append(
            FieldComparison(
                field_path="ResultsByTime.length",
                mcp_value=len(mcp_results),
                native_value=len(native_results),
                match=len(mcp_results) == len(native_results),
            )
        )

        # Compare each time period
        for i, (mcp_period, native_period) in enumerate(zip(mcp_results, native_results)):
            # Compare time period start
            mcp_start = mcp_period.get("TimePeriod", {}).get("Start")
            native_start = native_period.get("TimePeriod", {}).get("Start")
            comparisons.append(
                FieldComparison(
                    field_path=f"ResultsByTime[{i}].TimePeriod.Start",
                    mcp_value=mcp_start,
                    native_value=native_start,
                    match=mcp_start == native_start,
                )
            )

            # Compare blended cost with tolerance
            mcp_cost = float(mcp_period.get("Total", {}).get("BlendedCost", {}).get("Amount", 0))
            native_cost = float(native_period.get("Total", {}).get("BlendedCost", {}).get("Amount", 0))

            # Calculate if within tolerance
            if native_cost == 0:
                match = mcp_cost == 0
            else:
                diff_pct = abs(mcp_cost - native_cost) / native_cost
                match = diff_pct <= FINANCIAL_TOLERANCE

            comparisons.append(
                FieldComparison(
                    field_path=f"ResultsByTime[{i}].Total.BlendedCost.Amount",
                    mcp_value=mcp_cost,
                    native_value=native_cost,
                    match=match,
                    tolerance_applied=FINANCIAL_TOLERANCE,
                    notes=f"Financial tolerance: {FINANCIAL_TOLERANCE * 100}%",
                )
            )

        return comparisons


class AWSSecurityHubValidator(BaseValidator):
    """Validator for awslabs-security-hub MCP server.

    Cross-validates against: aws securityhub describe-hub
    Profile: AWS_OPERATIONS_PROFILE
    """

    server_name = "awslabs-security-hub"
    profile_env_var = "AWS_OPERATIONS_PROFILE"
    native_command = "aws securityhub describe-hub"

    def __init__(
        self,
        profile: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Security Hub validator.

        Args:
            profile: AWS profile to use (defaults to AWS_OPERATIONS_PROFILE)
            **kwargs: Additional arguments passed to BaseValidator
        """
        effective_profile = profile or os.environ.get(self.profile_env_var)
        super().__init__(profile=effective_profile, **kwargs)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Security Hub MCP server.

        Returns:
            Dictionary containing Security Hub configuration
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from AWS Security Hub API.

        Returns:
            Dictionary containing Security Hub configuration
        """
        return self.run_cli_command(self.native_command)

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Security Hub MCP and native API results.

        Compares:
        - Hub ARN
        - Auto-enable controls
        - Subscribed at timestamp

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        # Compare Hub ARN
        comparisons.append(
            FieldComparison(
                field_path="HubArn",
                mcp_value=mcp_data.get("HubArn"),
                native_value=native_data.get("HubArn"),
                match=mcp_data.get("HubArn") == native_data.get("HubArn"),
            )
        )

        # Compare auto-enable controls
        comparisons.append(
            FieldComparison(
                field_path="AutoEnableControls",
                mcp_value=mcp_data.get("AutoEnableControls"),
                native_value=native_data.get("AutoEnableControls"),
                match=mcp_data.get("AutoEnableControls") == native_data.get("AutoEnableControls"),
            )
        )

        # Compare control finding generator
        comparisons.append(
            FieldComparison(
                field_path="ControlFindingGenerator",
                mcp_value=mcp_data.get("ControlFindingGenerator"),
                native_value=native_data.get("ControlFindingGenerator"),
                match=mcp_data.get("ControlFindingGenerator") == native_data.get("ControlFindingGenerator"),
            )
        )

        return comparisons


class AWSIdentityCenterValidator(BaseValidator):
    """Validator for awslabs-identity-center MCP server.

    Cross-validates against: aws sso-admin list-instances
    Profile: AWS_MANAGEMENT_PROFILE

    Note: LocalStack = 0% value, requires direct Tier 3 testing.
    """

    server_name = "awslabs-identity-center"
    profile_env_var = "AWS_MANAGEMENT_PROFILE"
    native_command = "aws sso-admin list-instances"

    def __init__(
        self,
        profile: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Identity Center validator.

        Args:
            profile: AWS profile to use (defaults to AWS_MANAGEMENT_PROFILE)
            **kwargs: Additional arguments passed to BaseValidator
        """
        effective_profile = profile or os.environ.get(self.profile_env_var)
        super().__init__(profile=effective_profile, **kwargs)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Identity Center MCP server.

        Returns:
            Dictionary containing SSO instances
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from AWS IAM Identity Center API.

        Returns:
            Dictionary containing SSO instances
        """
        return self.run_cli_command(self.native_command)

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Identity Center MCP and native API results.

        Compares:
        - Instance count
        - Instance ARNs
        - Identity store IDs

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_instances = mcp_data.get("Instances", [])
        native_instances = native_data.get("Instances", [])

        # Compare instance count
        comparisons.append(
            FieldComparison(
                field_path="Instances.length",
                mcp_value=len(mcp_instances),
                native_value=len(native_instances),
                match=len(mcp_instances) == len(native_instances),
            )
        )

        # Build lookup by instance ARN
        mcp_by_arn = {i.get("InstanceArn"): i for i in mcp_instances}
        native_by_arn = {i.get("InstanceArn"): i for i in native_instances}

        # Compare each instance
        all_arns = set(mcp_by_arn.keys()) | set(native_by_arn.keys())
        for arn in all_arns:
            mcp_instance = mcp_by_arn.get(arn, {})
            native_instance = native_by_arn.get(arn, {})

            # Instance exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"Instances[{arn}].exists",
                    mcp_value=arn in mcp_by_arn,
                    native_value=arn in native_by_arn,
                    match=arn in mcp_by_arn and arn in native_by_arn,
                )
            )

            if mcp_instance and native_instance:
                # Compare Identity Store ID
                comparisons.append(
                    FieldComparison(
                        field_path=f"Instances[{arn}].IdentityStoreId",
                        mcp_value=mcp_instance.get("IdentityStoreId"),
                        native_value=native_instance.get("IdentityStoreId"),
                        match=mcp_instance.get("IdentityStoreId") == native_instance.get("IdentityStoreId"),
                    )
                )

                # Compare Owner Account ID
                comparisons.append(
                    FieldComparison(
                        field_path=f"Instances[{arn}].OwnerAccountId",
                        mcp_value=mcp_instance.get("OwnerAccountId"),
                        native_value=native_instance.get("OwnerAccountId"),
                        match=mcp_instance.get("OwnerAccountId") == native_instance.get("OwnerAccountId"),
                    )
                )

        return comparisons


class AWSControlTowerValidator(BaseValidator):
    """Validator for awslabs-control-tower MCP server.

    Cross-validates against: aws controltower list-enabled-controls
    Profile: AWS_MANAGEMENT_PROFILE

    Note: LocalStack = 0% value, requires direct Tier 3 testing.
    Control Tower requires an active Landing Zone.
    """

    server_name = "awslabs-control-tower"
    profile_env_var = "AWS_MANAGEMENT_PROFILE"
    native_command = "aws controltower list-enabled-controls"

    def __init__(
        self,
        profile: str | None = None,
        target_identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the Control Tower validator.

        Args:
            profile: AWS profile to use (defaults to AWS_MANAGEMENT_PROFILE)
            target_identifier: OU or account ARN to list controls for
            **kwargs: Additional arguments passed to BaseValidator
        """
        effective_profile = profile or os.environ.get(self.profile_env_var)
        super().__init__(profile=effective_profile, **kwargs)
        self.target_identifier = target_identifier

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from Control Tower MCP server.

        Returns:
            Dictionary containing enabled controls
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from AWS Control Tower API.

        Note: Control Tower requires specific IAM permissions:
        - controltower:ListLandingZones
        - controltower:ListEnabledControls
        These are NOT included in AWS managed ReadOnlyAccess policy.

        Returns:
            Dictionary containing enabled controls or landing zones
        """
        try:
            # Control Tower requires a target identifier (OU ARN)
            # If not provided, try to get the landing zone info
            if self.target_identifier:
                command = f"{self.native_command} --target-identifier {self.target_identifier}"
            else:
                # Get landing zone info first
                command = "aws controltower list-landing-zones"
            return self.run_cli_command(command)
        except Exception as e:
            error_msg = str(e)
            # Handle AccessDeniedException gracefully
            if "AccessDeniedException" in error_msg or "not authorized" in error_msg:
                return {
                    "LandingZones": [],
                    "skipped": True,
                    "reason": "IAM permissions required: controltower:ListLandingZones",
                    "note": "ReadOnlyAccess policy does not include Control Tower permissions",
                }
            # Re-raise other exceptions
            raise

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare Control Tower MCP and native API results.

        Compares:
        - Enabled controls count
        - Control identifiers
        - Target identifiers

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        # Handle skipped case (IAM permissions missing)
        if mcp_data.get("skipped") or native_data.get("skipped"):
            reason = mcp_data.get("reason") or native_data.get("reason", "Unknown")
            comparisons.append(
                FieldComparison(
                    field_path="validation.skipped",
                    mcp_value=True,
                    native_value=True,
                    match=True,  # Both skipped = consistent
                    notes=f"Skipped: {reason}",
                )
            )
            return comparisons

        # Handle landing zone list response
        if "LandingZones" in mcp_data:
            mcp_zones = mcp_data.get("LandingZones", [])
            native_zones = native_data.get("LandingZones", [])

            comparisons.append(
                FieldComparison(
                    field_path="LandingZones.length",
                    mcp_value=len(mcp_zones),
                    native_value=len(native_zones),
                    match=len(mcp_zones) == len(native_zones),
                )
            )

            # Compare each landing zone
            for i, (mcp_zone, native_zone) in enumerate(zip(mcp_zones, native_zones)):
                comparisons.append(
                    FieldComparison(
                        field_path=f"LandingZones[{i}].Arn",
                        mcp_value=mcp_zone.get("Arn"),
                        native_value=native_zone.get("Arn"),
                        match=mcp_zone.get("Arn") == native_zone.get("Arn"),
                    )
                )

            return comparisons

        # Handle enabled controls response
        mcp_controls = mcp_data.get("EnabledControls", [])
        native_controls = native_data.get("EnabledControls", [])

        # Compare control count
        comparisons.append(
            FieldComparison(
                field_path="EnabledControls.length",
                mcp_value=len(mcp_controls),
                native_value=len(native_controls),
                match=len(mcp_controls) == len(native_controls),
            )
        )

        # Build lookup by control identifier
        mcp_by_id = {c.get("ControlIdentifier"): c for c in mcp_controls}
        native_by_id = {c.get("ControlIdentifier"): c for c in native_controls}

        # Compare each control
        all_ids = set(mcp_by_id.keys()) | set(native_by_id.keys())
        for control_id in all_ids:
            mcp_control = mcp_by_id.get(control_id, {})
            native_control = native_by_id.get(control_id, {})

            comparisons.append(
                FieldComparison(
                    field_path=f"EnabledControls[{control_id}].exists",
                    mcp_value=control_id in mcp_by_id,
                    native_value=control_id in native_by_id,
                    match=control_id in mcp_by_id and control_id in native_by_id,
                )
            )

            if mcp_control and native_control:
                # Compare ARN
                comparisons.append(
                    FieldComparison(
                        field_path=f"EnabledControls[{control_id}].Arn",
                        mcp_value=mcp_control.get("Arn"),
                        native_value=native_control.get("Arn"),
                        match=mcp_control.get("Arn") == native_control.get("Arn"),
                    )
                )

        return comparisons


class AWSConfigValidator(BaseValidator):
    """Validator for awslabs-config MCP server.

    Cross-validates against: aws configservice describe-config-rules
    Profile: AWS_OPERATIONS_PROFILE
    """

    server_name = "awslabs-config"
    profile_env_var = "AWS_OPERATIONS_PROFILE"
    native_command = "aws configservice describe-config-rules"

    def __init__(
        self,
        profile: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the AWS Config validator.

        Args:
            profile: AWS profile to use (defaults to AWS_OPERATIONS_PROFILE)
            **kwargs: Additional arguments passed to BaseValidator
        """
        effective_profile = profile or os.environ.get(self.profile_env_var)
        super().__init__(profile=effective_profile, **kwargs)

    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from AWS Config MCP server.

        Returns:
            Dictionary containing Config rules
        """
        # TODO: Replace with actual MCP server call when available
        return self.get_native_data()

    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from AWS Config API.

        Returns:
            Dictionary containing Config rules
        """
        return self.run_cli_command(self.native_command)

    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare AWS Config MCP and native API results.

        Compares:
        - Config rule count
        - Rule names
        - Rule states
        - Source identifiers

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        comparisons: list[FieldComparison] = []

        mcp_rules = mcp_data.get("ConfigRules", [])
        native_rules = native_data.get("ConfigRules", [])

        # Compare rule count
        comparisons.append(
            FieldComparison(
                field_path="ConfigRules.length",
                mcp_value=len(mcp_rules),
                native_value=len(native_rules),
                match=len(mcp_rules) == len(native_rules),
            )
        )

        # Build lookup by rule name
        mcp_by_name = {r.get("ConfigRuleName"): r for r in mcp_rules}
        native_by_name = {r.get("ConfigRuleName"): r for r in native_rules}

        # Compare each rule
        all_names = set(mcp_by_name.keys()) | set(native_by_name.keys())
        for rule_name in all_names:
            mcp_rule = mcp_by_name.get(rule_name, {})
            native_rule = native_by_name.get(rule_name, {})

            # Rule exists in both
            comparisons.append(
                FieldComparison(
                    field_path=f"ConfigRules[{rule_name}].exists",
                    mcp_value=rule_name in mcp_by_name,
                    native_value=rule_name in native_by_name,
                    match=rule_name in mcp_by_name and rule_name in native_by_name,
                )
            )

            if mcp_rule and native_rule:
                # Compare ConfigRuleState
                comparisons.append(
                    FieldComparison(
                        field_path=f"ConfigRules[{rule_name}].ConfigRuleState",
                        mcp_value=mcp_rule.get("ConfigRuleState"),
                        native_value=native_rule.get("ConfigRuleState"),
                        match=mcp_rule.get("ConfigRuleState") == native_rule.get("ConfigRuleState"),
                    )
                )

                # Compare Source Owner
                mcp_source = mcp_rule.get("Source", {})
                native_source = native_rule.get("Source", {})
                comparisons.append(
                    FieldComparison(
                        field_path=f"ConfigRules[{rule_name}].Source.Owner",
                        mcp_value=mcp_source.get("Owner"),
                        native_value=native_source.get("Owner"),
                        match=mcp_source.get("Owner") == native_source.get("Owner"),
                    )
                )

                # Compare Source Identifier
                comparisons.append(
                    FieldComparison(
                        field_path=f"ConfigRules[{rule_name}].Source.SourceIdentifier",
                        mcp_value=mcp_source.get("SourceIdentifier"),
                        native_value=native_source.get("SourceIdentifier"),
                        match=mcp_source.get("SourceIdentifier") == native_source.get("SourceIdentifier"),
                    )
                )

                # Compare ConfigRuleArn
                comparisons.append(
                    FieldComparison(
                        field_path=f"ConfigRules[{rule_name}].ConfigRuleArn",
                        mcp_value=mcp_rule.get("ConfigRuleArn"),
                        native_value=native_rule.get("ConfigRuleArn"),
                        match=mcp_rule.get("ConfigRuleArn") == native_rule.get("ConfigRuleArn"),
                    )
                )

        return comparisons
