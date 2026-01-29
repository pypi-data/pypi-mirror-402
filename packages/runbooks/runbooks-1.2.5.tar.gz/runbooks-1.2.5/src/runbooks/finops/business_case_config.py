"""
Dynamic Business Case Configuration - Enterprise Template System

Strategic Achievement: Replace hardcoded references with dynamic business case templates
- Enterprise naming conventions with configurable business scenarios
- Dynamic financial targets and achievement tracking
- Reusable template system for unlimited business case scaling
- Business Scenario Matrix with intelligent parameter defaults (Phase 1 Priority 2)

This module provides configurable business case templates following enterprise standards:
- "Do one thing and do it well": Centralized configuration management
- "Move Fast, But Not So Fast We Crash": Proven template patterns with validation
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, NamedTuple, Optional, Union


class BusinessCaseType(Enum):
    """Standard business case types for enterprise scenarios."""

    COST_OPTIMIZATION = "cost_optimization"
    RESOURCE_CLEANUP = "resource_cleanup"
    COMPLIANCE_FRAMEWORK = "compliance_framework"
    SECURITY_ENHANCEMENT = "security_enhancement"
    AUTOMATION_DEPLOYMENT = "automation_deployment"


@dataclass
class BusinessScenario:
    """Dynamic business scenario configuration."""

    scenario_id: str
    display_name: str
    business_case_type: BusinessCaseType
    target_savings_min: Optional[float] = None
    target_savings_max: Optional[float] = None
    business_description: str = ""
    technical_focus: str = ""
    risk_level: str = "Medium"
    implementation_status: str = "Analysis"
    cli_command_suffix: str = ""

    @property
    def scenario_display_id(self) -> str:
        """Generate enterprise-friendly scenario display ID."""
        return f"{self.business_case_type.value.replace('_', '-').title()}-{self.scenario_id}"

    @property
    def savings_range_display(self) -> str:
        """Generate savings range display for business presentations."""
        if self.target_savings_min and self.target_savings_max:
            if self.target_savings_min == self.target_savings_max:
                return f"${self.target_savings_min:,.0f}/year"
            else:
                return f"${self.target_savings_min:,.0f}-${self.target_savings_max:,.0f}/year"
        elif self.target_savings_min:
            return f"${self.target_savings_min:,.0f}+/year"
        else:
            return "Analysis pending"


class BusinessCaseConfigManager:
    """Enterprise business case configuration manager."""

    def __init__(self, config_source: Optional[str] = None):
        """
        Initialize business case configuration manager.

        Args:
            config_source: Optional path to configuration file or environment variable prefix
        """
        self.config_source = config_source or "RUNBOOKS_BUSINESS_CASE"
        self.scenarios = self._load_default_scenarios()
        self._load_environment_overrides()

    def _load_default_scenarios(self) -> Dict[str, BusinessScenario]:
        """Load default enterprise business scenarios."""
        return {
            "workspaces": BusinessScenario(
                scenario_id="workspaces",
                display_name="WorkSpaces Resource Optimization",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=12000,
                target_savings_max=15000,
                business_description="Identify and optimize unused Amazon WorkSpaces for cost efficiency",
                technical_focus="Zero-usage WorkSpaces detection and cost analysis",
                risk_level="Low",
                cli_command_suffix="workspaces",
            ),
            "rds-snapshots": BusinessScenario(
                scenario_id="rds-snapshots",
                display_name="RDS Storage Optimization",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=5000,
                target_savings_max=24000,
                business_description="Optimize manual RDS snapshots to reduce storage costs",
                technical_focus="Manual RDS snapshot lifecycle management",
                risk_level="Medium",
                cli_command_suffix="rds-snapshots",
            ),
            "backup-investigation": BusinessScenario(
                scenario_id="backup-investigation",
                display_name="Backup Infrastructure Analysis",
                business_case_type=BusinessCaseType.COMPLIANCE_FRAMEWORK,
                business_description="Investigate backup account utilization and optimization opportunities",
                technical_focus="Backup infrastructure resource utilization analysis",
                risk_level="Medium",
                implementation_status="Framework",
                cli_command_suffix="backup-investigation",
            ),
            "nat-gateway": BusinessScenario(
                scenario_id="nat-gateway",
                display_name="Network Gateway Optimization",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                target_savings_min=8000,
                target_savings_max=12000,
                business_description="Optimize NAT Gateway configurations for cost efficiency",
                technical_focus="NAT Gateway usage analysis and rightsizing",
                cli_command_suffix="nat-gateway",
            ),
            "elastic-ip": BusinessScenario(
                scenario_id="elastic-ip",
                display_name="IP Address Resource Management",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=44,  # $3.65 * 12 months
                business_description="Optimize unattached Elastic IP addresses",
                technical_focus="Elastic IP attachment analysis and cleanup recommendations",
                risk_level="Low",
                cli_command_suffix="elastic-ip",
            ),
            "ebs-optimization": BusinessScenario(
                scenario_id="ebs-optimization",
                display_name="Storage Volume Optimization",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                business_description="Optimize EBS volume types and utilization for cost efficiency",
                technical_focus="EBS volume rightsizing and type optimization (15-20% potential)",
                cli_command_suffix="ebs-optimization",
            ),
            "vpc-cleanup": BusinessScenario(
                scenario_id="vpc-cleanup",
                display_name="Network Infrastructure Cleanup",
                business_case_type=BusinessCaseType.RESOURCE_CLEANUP,
                target_savings_min=5869,
                business_description="Clean up unused VPC resources and infrastructure",
                technical_focus="VPC resource utilization analysis and cleanup recommendations",
                cli_command_suffix="vpc-cleanup",
            ),
        }

    def _load_environment_overrides(self) -> None:
        """
        Load configuration overrides and discover new scenarios from environment variables.

        Implements Unlimited Scenario Expansion Framework:
        - Overrides existing scenarios with environment variables
        - Auto-discovers new scenarios via RUNBOOKS_BUSINESS_CASE_[SCENARIO]_* pattern
        - Creates BusinessScenario objects for new scenarios dynamically
        """
        prefix = f"{self.config_source}_"

        # Phase 1: Override existing scenarios
        for scenario_key, scenario in self.scenarios.items():
            # Check for scenario-specific overrides
            env_key = f"{prefix}{scenario_key.upper().replace('-', '_')}"

            # Override target savings if specified
            min_savings = os.getenv(f"{env_key}_MIN_SAVINGS")
            max_savings = os.getenv(f"{env_key}_MAX_SAVINGS")

            if min_savings:
                scenario.target_savings_min = float(min_savings)
            if max_savings:
                scenario.target_savings_max = float(max_savings)

            # Override display name if specified
            display_name = os.getenv(f"{env_key}_DISPLAY_NAME")
            if display_name:
                scenario.display_name = display_name

            # Override business description if specified
            description = os.getenv(f"{env_key}_DESCRIPTION")
            if description:
                scenario.business_description = description

        # Phase 2: Auto-discovery of new scenarios from environment variables
        self._discover_new_scenarios_from_environment(prefix)

    def _discover_new_scenarios_from_environment(self, prefix: str) -> None:
        """
        Discover and create new business scenarios from environment variables.

        Environment Variable Pattern:
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_DISPLAY_NAME=... (required)
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_MIN_SAVINGS=... (optional)
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_MAX_SAVINGS=... (optional)
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_DESCRIPTION=... (optional)
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_CLI_SUFFIX=... (optional, defaults to scenario key)
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_TYPE=... (optional, defaults to cost_optimization)
        RUNBOOKS_BUSINESS_CASE_[SCENARIO]_RISK_LEVEL=... (optional, defaults to Medium)
        """
        # Scan all environment variables for new scenario patterns
        discovered_scenarios = set()

        for env_var in os.environ:
            if env_var.startswith(prefix) and "_DISPLAY_NAME" in env_var:
                # Extract scenario key from pattern: RUNBOOKS_BUSINESS_CASE_[SCENARIO]_DISPLAY_NAME
                scenario_part = env_var.replace(prefix, "").replace("_DISPLAY_NAME", "")
                scenario_key = scenario_part.lower().replace("_", "-")
                discovered_scenarios.add((scenario_key, scenario_part))

        # Create new scenarios for discovered patterns
        for scenario_key, env_scenario_key in discovered_scenarios:
            if scenario_key not in self.scenarios:  # Don't override existing scenarios
                new_scenario = self._create_scenario_from_environment(scenario_key, env_scenario_key, prefix)
                if new_scenario:
                    self.scenarios[scenario_key] = new_scenario

    def _create_scenario_from_environment(
        self, scenario_key: str, env_scenario_key: str, prefix: str
    ) -> Optional[BusinessScenario]:
        """
        Create a new BusinessScenario from environment variables.

        Args:
            scenario_key: The normalized scenario key (kebab-case)
            env_scenario_key: The environment variable scenario key (UPPER_CASE)
            prefix: Environment variable prefix

        Returns:
            New BusinessScenario object or None if required fields missing
        """
        env_base = f"{prefix}{env_scenario_key}"

        # Required field: display name
        display_name = os.getenv(f"{env_base}_DISPLAY_NAME")
        if not display_name:
            return None

        # Optional fields with smart defaults
        business_type_str = os.getenv(f"{env_base}_TYPE", "cost_optimization")
        try:
            business_case_type = BusinessCaseType(business_type_str)
        except ValueError:
            business_case_type = BusinessCaseType.COST_OPTIMIZATION

        # Financial targets
        min_savings_str = os.getenv(f"{env_base}_MIN_SAVINGS")
        max_savings_str = os.getenv(f"{env_base}_MAX_SAVINGS")

        min_savings = float(min_savings_str) if min_savings_str else None
        max_savings = float(max_savings_str) if max_savings_str else None

        # Business context
        description = os.getenv(f"{env_base}_DESCRIPTION", f"Business optimization scenario for {display_name}")
        technical_focus = os.getenv(f"{env_base}_TECHNICAL_FOCUS", f"{display_name} analysis and optimization")
        risk_level = os.getenv(f"{env_base}_RISK_LEVEL", "Medium")
        implementation_status = os.getenv(f"{env_base}_STATUS", "Analysis")
        cli_suffix = os.getenv(f"{env_base}_CLI_SUFFIX", scenario_key)

        return BusinessScenario(
            scenario_id=scenario_key,
            display_name=display_name,
            business_case_type=business_case_type,
            target_savings_min=min_savings,
            target_savings_max=max_savings,
            business_description=description,
            technical_focus=technical_focus,
            risk_level=risk_level,
            implementation_status=implementation_status,
            cli_command_suffix=cli_suffix,
        )

    def get_scenario(self, scenario_key: str) -> Optional[BusinessScenario]:
        """Get business scenario by key."""
        return self.scenarios.get(scenario_key)

    def get_all_scenarios(self) -> Dict[str, BusinessScenario]:
        """Get all configured business scenarios."""
        return self.scenarios

    def get_scenario_choices(self) -> List[str]:
        """Get list of valid scenario keys for CLI choice options."""
        return list(self.scenarios.keys())

    def get_scenario_help_text(self) -> str:
        """Generate help text for CLI scenario option."""
        help_parts = []
        for key, scenario in self.scenarios.items():
            savings_display = scenario.savings_range_display
            help_parts.append(f"{key} ({scenario.display_name}: {savings_display})")
        return "Business scenario analysis: " + ", ".join(help_parts)

    def format_scenario_for_display(
        self,
        scenario_key: str,
        achieved_savings: Optional[float] = None,
        achievement_percentage: Optional[float] = None,
    ) -> str:
        """Format scenario for display in tables and reports."""
        scenario = self.get_scenario(scenario_key)
        if not scenario:
            return f"Unknown scenario: {scenario_key}"

        base_info = f"{scenario.display_name} ({scenario.savings_range_display})"

        if achieved_savings:
            base_info += f" - Achieved: ${achieved_savings:,.0f}"

        if achievement_percentage:
            base_info += f" ({achievement_percentage:.0f}% of target)"

        return base_info

    def add_dynamic_scenario(self, scenario: BusinessScenario) -> None:
        """
        Add a new business scenario dynamically.

        Args:
            scenario: BusinessScenario object to add to the configuration
        """
        self.scenarios[scenario.scenario_id] = scenario

    def create_scenario_from_template(
        self, scenario_id: str, template_type: str = "aws_resource_optimization"
    ) -> BusinessScenario:
        """
        Create a business scenario from predefined templates.

        Templates available:
        - aws_resource_optimization: Generic AWS resource optimization
        - lambda_rightsizing: AWS Lambda function rightsizing
        - s3_storage_optimization: S3 storage class optimization
        - healthcare_compliance: Healthcare-specific compliance scenarios
        - finance_cost_governance: Financial industry cost governance
        - manufacturing_automation: Manufacturing automation scenarios

        Args:
            scenario_id: Unique identifier for the scenario
            template_type: Type of template to use

        Returns:
            Pre-configured BusinessScenario object
        """
        templates = {
            "aws_resource_optimization": BusinessScenario(
                scenario_id=scenario_id,
                display_name=f"{scenario_id.title().replace('-', ' ')} Resource Optimization",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                business_description=f"Optimize {scenario_id.replace('-', ' ')} resources for cost efficiency and performance",
                technical_focus=f"{scenario_id.title().replace('-', ' ')} resource analysis with automated recommendations",
                risk_level="Medium",
                implementation_status="Template Ready",
                cli_command_suffix=scenario_id,
            ),
            "lambda_rightsizing": BusinessScenario(
                scenario_id=scenario_id,
                display_name="Lambda Function Rightsizing",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                business_description="Optimize Lambda function memory allocation and timeout settings",
                technical_focus="CloudWatch metrics analysis for memory and duration optimization",
                risk_level="Low",
                cli_command_suffix=scenario_id,
            ),
            "s3_storage_optimization": BusinessScenario(
                scenario_id=scenario_id,
                display_name="S3 Storage Class Optimization",
                business_case_type=BusinessCaseType.COST_OPTIMIZATION,
                business_description="Optimize S3 storage classes based on access patterns",
                technical_focus="S3 access pattern analysis with intelligent storage class recommendations",
                risk_level="Low",
                cli_command_suffix=scenario_id,
            ),
            "healthcare_compliance": BusinessScenario(
                scenario_id=scenario_id,
                display_name="Healthcare Compliance Optimization",
                business_case_type=BusinessCaseType.COMPLIANCE_FRAMEWORK,
                business_description="HIPAA compliance optimization with cost considerations",
                technical_focus="Healthcare data security analysis with cost-effective compliance solutions",
                risk_level="High",
                cli_command_suffix=scenario_id,
            ),
            "finance_cost_governance": BusinessScenario(
                scenario_id=scenario_id,
                display_name="Financial Cost Governance",
                business_case_type=BusinessCaseType.COMPLIANCE_FRAMEWORK,
                business_description="Financial industry cost governance and audit readiness",
                technical_focus="SOX compliance cost optimization with audit trail requirements",
                risk_level="High",
                cli_command_suffix=scenario_id,
            ),
            "manufacturing_automation": BusinessScenario(
                scenario_id=scenario_id,
                display_name="Manufacturing Process Automation",
                business_case_type=BusinessCaseType.AUTOMATION_DEPLOYMENT,
                business_description="Manufacturing workflow automation with cost optimization",
                technical_focus="IoT and automation pipeline cost optimization analysis",
                risk_level="Medium",
                cli_command_suffix=scenario_id,
            ),
        }

        template = templates.get(template_type, templates["aws_resource_optimization"])
        # Create a copy and update the scenario_id
        return BusinessScenario(
            scenario_id=scenario_id,
            display_name=template.display_name,
            business_case_type=template.business_case_type,
            target_savings_min=template.target_savings_min,
            target_savings_max=template.target_savings_max,
            business_description=template.business_description,
            technical_focus=template.technical_focus,
            risk_level=template.risk_level,
            implementation_status=template.implementation_status,
            cli_command_suffix=template.cli_command_suffix,
        )

    def get_template_types(self) -> List[str]:
        """Get list of available template types for scenario creation."""
        return [
            "aws_resource_optimization",
            "lambda_rightsizing",
            "s3_storage_optimization",
            "healthcare_compliance",
            "finance_cost_governance",
            "manufacturing_automation",
        ]

    def calculate_roi_projection(
        self, scenario_key: str, current_monthly_cost: float, optimization_percentage: float = 0.20
    ) -> Dict[str, float]:
        """
        Calculate ROI projection for a business scenario.

        Args:
            scenario_key: Business scenario identifier
            current_monthly_cost: Current monthly cost for the resource
            optimization_percentage: Expected optimization percentage (default 20%)

        Returns:
            Dictionary with ROI calculations
        """
        monthly_savings = current_monthly_cost * optimization_percentage
        annual_savings = monthly_savings * 12

        return {
            "current_monthly_cost": current_monthly_cost,
            "monthly_savings": monthly_savings,
            "annual_savings": annual_savings,
            "optimization_percentage": optimization_percentage * 100,
            "roi_12_month": annual_savings,  # Assuming minimal implementation cost for analysis
        }

    def create_business_case_summary(self) -> Dict[str, Any]:
        """Create executive summary of all business cases."""
        total_min_savings = sum(scenario.target_savings_min or 0 for scenario in self.scenarios.values())

        total_max_savings = sum(
            scenario.target_savings_max or 0 for scenario in self.scenarios.values() if scenario.target_savings_max
        )

        return {
            "total_scenarios": len(self.scenarios),
            "total_potential_min": total_min_savings,
            "total_potential_max": total_max_savings,
            "potential_range": f"${total_min_savings:,.0f}-${total_max_savings:,.0f}",
            "scenarios_by_type": {
                case_type.value: [s.display_name for s in self.scenarios.values() if s.business_case_type == case_type]
                for case_type in BusinessCaseType
            },
            "scenario_discovery": {
                "default_scenarios": 7,
                "environment_discovered": len(self.scenarios) - 7,
                "total_active": len(self.scenarios),
                "unlimited_expansion": True,
            },
        }


# Global configuration manager instance
_config_manager = None


def get_business_case_config() -> BusinessCaseConfigManager:
    """Get global business case configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = BusinessCaseConfigManager()
    return _config_manager


def get_scenario_display_name(scenario_key: str) -> str:
    """Get enterprise-friendly display name for scenario."""
    config = get_business_case_config()
    scenario = config.get_scenario(scenario_key)
    return scenario.display_name if scenario else scenario_key.title()


def get_scenario_savings_range(scenario_key: str) -> str:
    """Get savings range display for scenario."""
    config = get_business_case_config()
    scenario = config.get_scenario(scenario_key)
    return scenario.savings_range_display if scenario else "Analysis pending"


def format_business_achievement(scenario_key: str, achieved_savings: float) -> str:
    """Format business achievement for executive reporting."""
    config = get_business_case_config()
    scenario = config.get_scenario(scenario_key)

    if not scenario:
        return f"{scenario_key}: ${achieved_savings:,.0f} annual savings"

    # Calculate achievement percentage if target is available
    achievement_text = f"{scenario.display_name}: ${achieved_savings:,.0f} annual savings"

    if scenario.target_savings_min:
        percentage = (achieved_savings / scenario.target_savings_min) * 100
        achievement_text += f" ({percentage:.0f}% of target)"

    return achievement_text


# Unlimited Scenario Expansion Framework - Helper Functions
def create_scenario_from_environment_variables(scenario_id: str) -> Optional[BusinessScenario]:
    """
    Create a business scenario from environment variables.

    Environment Variable Pattern:
    RUNBOOKS_BUSINESS_CASE_[SCENARIO_ID]_DISPLAY_NAME=... (required)
    RUNBOOKS_BUSINESS_CASE_[SCENARIO_ID]_MIN_SAVINGS=... (optional)
    RUNBOOKS_BUSINESS_CASE_[SCENARIO_ID]_MAX_SAVINGS=... (optional)
    RUNBOOKS_BUSINESS_CASE_[SCENARIO_ID]_DESCRIPTION=... (optional)
    RUNBOOKS_BUSINESS_CASE_[SCENARIO_ID]_TYPE=... (optional)

    Args:
        scenario_id: Scenario identifier (will be normalized to kebab-case)

    Returns:
        BusinessScenario object or None if required fields missing
    """
    config_manager = get_business_case_config()
    env_key = scenario_id.upper().replace("-", "_")

    return config_manager._create_scenario_from_environment(
        scenario_id.lower().replace("_", "-"), env_key, "RUNBOOKS_BUSINESS_CASE_"
    )


def add_scenario_from_template(scenario_id: str, template_type: str = "aws_resource_optimization") -> BusinessScenario:
    """
    Add a new business scenario from a template.

    Args:
        scenario_id: Unique identifier for the new scenario
        template_type: Template type to use (see get_available_templates())

    Returns:
        Created BusinessScenario object
    """
    config_manager = get_business_case_config()
    scenario = config_manager.create_scenario_from_template(scenario_id, template_type)
    config_manager.add_dynamic_scenario(scenario)
    return scenario


def get_available_templates() -> List[str]:
    """Get list of available business scenario templates."""
    config_manager = get_business_case_config()
    return config_manager.get_template_types()


def calculate_scenario_roi(
    scenario_id: str, current_monthly_cost: float, optimization_percentage: float = 0.20
) -> Dict[str, float]:
    """
    Calculate ROI projection for any business scenario.

    Args:
        scenario_id: Business scenario identifier
        current_monthly_cost: Current monthly AWS spend
        optimization_percentage: Expected optimization (default 20%)

    Returns:
        ROI calculation dictionary
    """
    config_manager = get_business_case_config()
    return config_manager.calculate_roi_projection(scenario_id, current_monthly_cost, optimization_percentage)


def get_unlimited_scenario_choices() -> List[str]:
    """
    Get unlimited scenario choices including environment-discovered scenarios.

    This function enables unlimited scenario expansion without hardcoded lists.
    """
    config_manager = get_business_case_config()
    return config_manager.get_scenario_choices()


def get_unlimited_scenario_help() -> str:
    """
    Get unlimited scenario help text including dynamically discovered scenarios.

    Returns comprehensive help covering all available scenarios.
    """
    config_manager = get_business_case_config()
    return config_manager.get_scenario_help_text()


def discover_scenarios_summary() -> Dict[str, Any]:
    """
    Get summary of scenario discovery including environment-based scenarios.

    Returns:
        Discovery summary with counts and expansion capabilities
    """
    config_manager = get_business_case_config()
    return config_manager.create_business_case_summary()


# Migration helper functions for existing hardcoded patterns
def migrate_legacy_scenario_reference(legacy_ref: str) -> str:
    """
    Migrate legacy references to dynamic business case keys.

    Args:
        legacy_ref: Legacy reference like "FinOps-24", "finops-23", etc.

    Returns:
        Dynamic business case key
    """
    legacy_mapping = {
        "finops-24": "workspaces",
        "FinOps-24": "workspaces",
        "finops-23": "rds-snapshots",
        "FinOps-23": "rds-snapshots",
        "finops-25": "backup-investigation",
        "FinOps-25": "backup-investigation",
        "finops-26": "nat-gateway",
        "FinOps-26": "nat-gateway",
        "finops-eip": "elastic-ip",
        "FinOps-EIP": "elastic-ip",
        "finops-ebs": "ebs-optimization",
        "FinOps-EBS": "ebs-optimization",
        "awso-05": "vpc-cleanup",
        "AWSO-05": "vpc-cleanup",
    }

    return legacy_mapping.get(legacy_ref, legacy_ref.lower())


# ============================================================================
# Business Scenario Matrix - Phase 1 Priority 2 Implementation
# ============================================================================


class ScenarioParameter(NamedTuple):
    """Parameter recommendation for business scenarios."""

    name: str
    optimal_value: Union[str, int, float]
    business_justification: str
    alternative_values: Optional[List[Any]] = None


@dataclass
class ScenarioParameterMatrix:
    """Intelligent parameter defaults for business scenarios."""

    timerange_days: Optional[int] = None
    regional_scope: Optional[str] = None  # single, multi, global
    cost_focus: Optional[str] = None  # unblended, amortized, dual-metrics
    export_priority: Optional[str] = None  # csv, json, pdf, markdown
    validation_level: Optional[str] = None  # basic, enhanced, comprehensive
    business_justification: str = ""

    @property
    def parameter_recommendations(self) -> Dict[str, ScenarioParameter]:
        """Get structured parameter recommendations."""
        recommendations = {}

        if self.timerange_days:
            recommendations["timerange"] = ScenarioParameter(
                name="--time-range",
                optimal_value=self.timerange_days,
                business_justification=f"Optimal analysis period: {self.timerange_days} days. {self.business_justification}",
                alternative_values=[7, 30, 60, 90, 180] if self.timerange_days not in [7, 30, 60, 90, 180] else None,
            )

        if self.regional_scope:
            scope_mapping = {
                "single": ["--region", "ap-southeast-2"],
                "multi": ["--all-regions", True],
                "global": ["--global-scope", True],
            }
            if self.regional_scope in scope_mapping:
                param_name, param_value = scope_mapping[self.regional_scope]
                recommendations["regional_scope"] = ScenarioParameter(
                    name=param_name,
                    optimal_value=param_value,
                    business_justification=f"Regional scope: {self.regional_scope} - {self.business_justification}",
                )

        if self.cost_focus:
            recommendations["cost_focus"] = ScenarioParameter(
                name=f"--{self.cost_focus}",
                optimal_value=True,
                business_justification=f"Cost perspective: {self.cost_focus} - {self.business_justification}",
            )

        if self.export_priority:
            recommendations["export_format"] = ScenarioParameter(
                name="--" + self.export_priority.replace("_", "-"),
                optimal_value=True,
                business_justification=f"Export format: {self.export_priority} - {self.business_justification}",
                alternative_values=["csv", "json", "pdf", "markdown"] if self.export_priority else None,
            )

        return recommendations


class BusinessScenarioMatrix:
    """
    Business Scenario Matrix with intelligent parameter defaults.

    Implements Phase 1 Priority 2: Business scenario intelligence with smart
    parameter recommendations per business case type.

    Enhanced with Phase 2 Priority 1: Unlimited Scenario Expansion Framework
    supporting dynamic parameter matrix generation for environment-discovered scenarios.
    """

    def __init__(self):
        """Initialize scenario matrix with Tier 1, 2, 3 configurations and dynamic expansion."""
        self.scenario_matrix = self._build_scenario_matrix()
        self._extend_matrix_with_discovered_scenarios()

    def _build_scenario_matrix(self) -> Dict[str, ScenarioParameterMatrix]:
        """Build the complete business scenario parameter matrix."""
        return {
            # TIER 1 HIGH-VALUE SCENARIOS
            "workspaces": ScenarioParameterMatrix(
                timerange_days=90,
                regional_scope="single",
                cost_focus="unblended",
                export_priority="pdf",
                validation_level="comprehensive",
                business_justification="WorkSpaces require quarterly analysis for usage pattern detection. Single-region focus optimizes analysis speed. Unblended costs show true resource utilization. PDF format ideal for management review.",
            ),
            "nat-gateway": ScenarioParameterMatrix(
                timerange_days=30,
                regional_scope="multi",
                cost_focus="amortized",
                export_priority="json",
                validation_level="enhanced",
                business_justification="NAT Gateways require monthly analysis for traffic optimization. Multi-region analysis essential for comprehensive network cost optimization. Amortized costs account for data transfer pricing. JSON format enables automation integration.",
            ),
            "rds-snapshots": ScenarioParameterMatrix(
                timerange_days=90,
                regional_scope="multi",
                cost_focus="dual-metrics",
                export_priority="csv",
                validation_level="comprehensive",
                business_justification="RDS snapshots require quarterly analysis for retention policy optimization. Multi-region scope captures all backup strategies. Dual metrics provide complete cost visibility. CSV format enables spreadsheet analysis.",
            ),
            # TIER 2 STRATEGIC SCENARIOS
            "ebs-optimization": ScenarioParameterMatrix(
                timerange_days=180,
                regional_scope="multi",
                cost_focus="dual-metrics",
                export_priority="pdf",
                validation_level="comprehensive",
                business_justification="EBS optimization requires extended analysis to identify usage patterns. Multi-region scope captures all storage. Dual metrics show both immediate and amortized costs. PDF format suitable for capacity planning presentations.",
            ),
            "vpc-cleanup": ScenarioParameterMatrix(
                timerange_days=30,
                regional_scope="multi",
                cost_focus="unblended",
                export_priority="csv",
                validation_level="enhanced",
                business_justification="VPC cleanup requires recent data for active resource identification. Multi-region analysis captures all network resources. Unblended costs show direct infrastructure impact. CSV enables detailed resource tracking.",
            ),
            "elastic-ip": ScenarioParameterMatrix(
                timerange_days=7,
                regional_scope="multi",
                cost_focus="unblended",
                export_priority="json",
                validation_level="basic",
                business_justification="Elastic IP analysis requires recent data for attachment status. Multi-region scope captures all IP allocations. Unblended costs show direct charges. JSON format enables automated cleanup workflows.",
            ),
            # TIER 3 FRAMEWORK SCENARIOS
            "backup-investigation": ScenarioParameterMatrix(
                timerange_days=None,  # Framework-based
                regional_scope="multi",
                cost_focus="amortized",
                export_priority="markdown",
                validation_level="basic",
                business_justification="Backup investigation uses framework-based timerange analysis. Multi-region scope for comprehensive backup strategy. Amortized costs for long-term planning. Markdown format for documentation and reporting.",
            ),
        }

    def _extend_matrix_with_discovered_scenarios(self) -> None:
        """
        Extend parameter matrix with environment-discovered scenarios.

        Creates intelligent parameter defaults for newly discovered scenarios
        based on business case type and heuristics.
        """
        config_manager = get_business_case_config()
        all_scenarios = config_manager.get_all_scenarios()

        for scenario_key, scenario in all_scenarios.items():
            if scenario_key not in self.scenario_matrix:
                # Generate intelligent defaults based on business case type
                parameter_matrix = self._generate_parameter_matrix_for_scenario(scenario)
                self.scenario_matrix[scenario_key] = parameter_matrix

    def _generate_parameter_matrix_for_scenario(self, scenario: BusinessScenario) -> ScenarioParameterMatrix:
        """
        Generate intelligent parameter matrix for a discovered scenario.

        Args:
            scenario: BusinessScenario object to generate parameters for

        Returns:
            ScenarioParameterMatrix with intelligent defaults
        """
        # Default parameter patterns based on business case type
        type_defaults = {
            BusinessCaseType.COST_OPTIMIZATION: ScenarioParameterMatrix(
                timerange_days=30,
                regional_scope="multi",
                cost_focus="dual-metrics",
                export_priority="pdf",
                validation_level="enhanced",
                business_justification=f"Cost optimization requires comprehensive analysis with dual cost perspectives for {scenario.display_name}",
            ),
            BusinessCaseType.RESOURCE_CLEANUP: ScenarioParameterMatrix(
                timerange_days=7,
                regional_scope="multi",
                cost_focus="unblended",
                export_priority="csv",
                validation_level="basic",
                business_justification=f"Resource cleanup requires recent data for active resource identification in {scenario.display_name}",
            ),
            BusinessCaseType.COMPLIANCE_FRAMEWORK: ScenarioParameterMatrix(
                timerange_days=90,
                regional_scope="global",
                cost_focus="amortized",
                export_priority="pdf",
                validation_level="comprehensive",
                business_justification=f"Compliance frameworks require extended analysis with comprehensive reporting for {scenario.display_name}",
            ),
            BusinessCaseType.SECURITY_ENHANCEMENT: ScenarioParameterMatrix(
                timerange_days=30,
                regional_scope="global",
                cost_focus="unblended",
                export_priority="markdown",
                validation_level="comprehensive",
                business_justification=f"Security enhancements require thorough analysis with documentation focus for {scenario.display_name}",
            ),
            BusinessCaseType.AUTOMATION_DEPLOYMENT: ScenarioParameterMatrix(
                timerange_days=60,
                regional_scope="multi",
                cost_focus="amortized",
                export_priority="json",
                validation_level="enhanced",
                business_justification=f"Automation deployment requires extended analysis with machine-readable output for {scenario.display_name}",
            ),
        }

        # Use type-based defaults or fallback to generic cost optimization pattern
        default_matrix = type_defaults.get(
            scenario.business_case_type, type_defaults[BusinessCaseType.COST_OPTIMIZATION]
        )

        # Override with scenario-specific intelligence where available
        if scenario.risk_level.lower() == "high":
            # High risk scenarios need more comprehensive validation
            default_matrix.validation_level = "comprehensive"
            default_matrix.timerange_days = max(default_matrix.timerange_days or 30, 90)

        if scenario.risk_level.lower() == "low":
            # Low risk scenarios can use basic validation
            default_matrix.validation_level = "basic"
            default_matrix.timerange_days = min(default_matrix.timerange_days or 30, 14)

        return default_matrix

    def add_custom_scenario_parameters(self, scenario_key: str, parameters: ScenarioParameterMatrix) -> None:
        """
        Add or override parameter matrix for a specific scenario.

        Args:
            scenario_key: Scenario identifier
            parameters: Custom parameter matrix configuration
        """
        self.scenario_matrix[scenario_key] = parameters

    def get_scenario_parameters(self, scenario_key: str) -> Optional[ScenarioParameterMatrix]:
        """Get parameter matrix for specific scenario."""
        return self.scenario_matrix.get(scenario_key)

    def get_parameter_recommendations(self, scenario_key: str) -> Dict[str, ScenarioParameter]:
        """Get intelligent parameter recommendations for scenario."""
        scenario_params = self.get_scenario_parameters(scenario_key)
        if not scenario_params:
            return {}
        return scenario_params.parameter_recommendations

    def generate_scenario_help(self, scenario_key: str) -> str:
        """Generate scenario-specific help text with parameter recommendations."""
        scenario_params = self.get_scenario_parameters(scenario_key)
        if not scenario_params:
            return f"No parameter recommendations available for scenario: {scenario_key}"

        recommendations = self.get_parameter_recommendations(scenario_key)
        if not recommendations:
            return f"Scenario {scenario_key}: Standard parameters apply"

        help_lines = [f"Scenario '{scenario_key}' - Intelligent Parameter Recommendations:"]
        help_lines.append("")

        for param_key, param in recommendations.items():
            if isinstance(param.optimal_value, bool) and param.optimal_value:
                help_lines.append(f"  {param.name}")
            else:
                help_lines.append(f"  {param.name} {param.optimal_value}")
            help_lines.append(f"    → {param.business_justification}")

            if param.alternative_values:
                alternatives = ", ".join(str(v) for v in param.alternative_values)
                help_lines.append(f"    Alternatives: {alternatives}")
            help_lines.append("")

        return "\n".join(help_lines)

    def validate_parameters_for_scenario(self, scenario_key: str, provided_params: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate provided parameters against scenario recommendations.

        Returns dict of warnings/suggestions for parameter optimization.
        """
        recommendations = self.get_parameter_recommendations(scenario_key)
        if not recommendations:
            return {}

        suggestions = {}

        # Check timerange optimization
        if "timerange" in recommendations:
            optimal_timerange = recommendations["timerange"].optimal_value
            provided_timerange = provided_params.get("time_range")

            if provided_timerange and provided_timerange != optimal_timerange:
                suggestions["timerange"] = (
                    f"Consider --time-range {optimal_timerange} for optimal {scenario_key} analysis (current: {provided_timerange})"
                )

        # Check export format optimization
        if "export_format" in recommendations:
            optimal_export = recommendations["export_format"].name.replace("--", "")
            export_formats = provided_params.get("export_formats", [])

            if export_formats and optimal_export not in export_formats:
                suggestions["export_format"] = (
                    f"Consider {optimal_export} export format for {scenario_key} analysis (optimal for business case)"
                )

        # Check cost focus optimization
        if "cost_focus" in recommendations:
            optimal_focus = recommendations["cost_focus"].name.replace("--", "")
            cost_focus_params = ["unblended", "amortized", "dual_metrics"]
            provided_focus = None

            for focus_type in cost_focus_params:
                if provided_params.get(focus_type):
                    provided_focus = focus_type
                    break

            if not provided_focus:
                suggestions["cost_focus"] = f"Consider {optimal_focus} cost perspective for {scenario_key} analysis"

        return suggestions

    def get_all_scenario_summaries(self) -> Dict[str, str]:
        """Get summary of all scenarios with their optimal parameters."""
        summaries = {}

        for scenario_key in self.scenario_matrix.keys():
            params = self.get_scenario_parameters(scenario_key)
            if params:
                summary_parts = []

                if params.timerange_days:
                    summary_parts.append(f"{params.timerange_days}d analysis")
                if params.regional_scope:
                    summary_parts.append(f"{params.regional_scope}-region")
                if params.cost_focus:
                    summary_parts.append(f"{params.cost_focus} costs")
                if params.export_priority:
                    summary_parts.append(f"{params.export_priority} export")

                summaries[scenario_key] = " | ".join(summary_parts)
            else:
                summaries[scenario_key] = "Standard analysis"

        return summaries


# Global scenario matrix instance
_scenario_matrix = None


def get_business_scenario_matrix() -> BusinessScenarioMatrix:
    """Get global business scenario matrix instance."""
    global _scenario_matrix
    if _scenario_matrix is None:
        _scenario_matrix = BusinessScenarioMatrix()
    return _scenario_matrix
