#!/usr/bin/env python3
"""
Security Hub Finding Remediation - Multi-Account Automation

Automate Security Hub HIGH severity finding remediation across multi-account organization.

Architecture:
- Multi-account discovery via Organizations API
- Security Hub finding classification (Security Groups, IAM, S3, etc.)
- Remediation workflow generation with dry-run safety
- Approval gates for high-risk changes

Business Requirements (JIRA AWSO-63/62/61):
- 25+ accounts compliance coverage
- HIGH severity finding remediation automation
- Security Group open rules remediation
- Dry-run mode default (manual approval for changes)

Author: DevOps Security Engineer (Runbooks Enterprise Team)
Version: 1.1.20 - Track 3: Security Hub Integration
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from runbooks.common.profile_utils import get_profile_for_operation
from runbooks.common.rich_utils import (
    console,
    create_panel,
    print_error,
    print_info,
    print_success,
    print_warning,
)
from runbooks.inventory.organizations_utils import discover_organization_accounts


class SecuritySeverity(Enum):
    """Security finding severity levels"""

    CRITICAL = 100
    HIGH = 75
    MEDIUM = 50
    LOW = 25
    INFORMATIONAL = 0


class FindingType(Enum):
    """Security Hub finding types"""

    SECURITY_GROUP = "Security Group"
    IAM = "IAM"
    S3 = "S3 Bucket"
    CLOUDTRAIL = "CloudTrail"
    CONFIG = "AWS Config"
    GUARDDUTY = "GuardDuty"
    EC2 = "EC2"
    RDS = "RDS"
    LAMBDA = "Lambda"
    OTHER = "Other"


@dataclass
class SecurityFinding:
    """Security Hub finding data structure"""

    finding_id: str
    title: str
    severity: SecuritySeverity
    resource_arn: str
    resource_type: str
    account_id: str
    region: str
    compliance_status: str
    workflow_status: str
    product_name: str
    finding_type: FindingType
    description: str
    remediation_available: bool
    remediation_action: Optional[str] = None
    requires_approval: bool = False


@dataclass
class RemediationResult:
    """Remediation execution result"""

    finding_id: str
    status: str  # success, failed, manual_required, approval_required, skipped
    message: str
    actions_taken: List[str]
    verification_status: Optional[str] = None


class SecurityHubFindingRemediation:
    """
    Automate Security Hub finding remediation across multi-account organization.

    Implements multi-account discovery, finding classification, and remediation
    workflow generation with safety gates and approval requirements.
    """

    SEVERITY_PRIORITIES = {
        SecuritySeverity.CRITICAL: 100,
        SecuritySeverity.HIGH: 75,
        SecuritySeverity.MEDIUM: 50,
        SecuritySeverity.LOW: 25,
        SecuritySeverity.INFORMATIONAL: 0,
    }

    # Remediation patterns mapped to finding types
    REMEDIATION_WORKFLOWS = {
        "security_group_unrestricted": {
            "finding_pattern": "security group allows 0.0.0.0/0",
            "action": "Restrict to specific IP ranges",
            "risk": "HIGH",
            "automation": "Manual review required",
            "cli_command": "aws ec2 revoke-security-group-ingress",
        },
        "iam_unused_credentials": {
            "finding_pattern": "IAM credentials unused",
            "action": "Disable or delete unused credentials",
            "risk": "MEDIUM",
            "automation": "Automated with approval",
            "cli_command": "aws iam delete-access-key",
        },
        "s3_public_bucket": {
            "finding_pattern": "S3 bucket publicly accessible",
            "action": "Apply bucket policy to block public access",
            "risk": "CRITICAL",
            "automation": "Manual review required",
            "cli_command": "aws s3api put-public-access-block",
        },
        "cloudtrail_not_encrypted": {
            "finding_pattern": "CloudTrail not encrypted",
            "action": "Enable KMS encryption",
            "risk": "HIGH",
            "automation": "Automated with approval",
            "cli_command": "aws cloudtrail update-trail --kms-key-id",
        },
    }

    def __init__(
        self,
        profile: str = "${MANAGEMENT_PROFILE}",
        accounts: Optional[List[str]] = None,
        severity: str = "HIGH",
        region: str = "ap-southeast-2",
    ):
        """
        Initialize Security Hub Finding Remediation.

        Args:
            profile: AWS profile with Organizations and Security Hub permissions
            accounts: List of account IDs (None = discover all from organization)
            severity: Minimum severity level (CRITICAL, HIGH, MEDIUM, LOW)
            region: AWS region for Security Hub operations
        """
        # Resolve profile from environment variables if needed
        self.profile = get_profile_for_operation("management", profile)
        self.region = region
        self.severity = SecuritySeverity[severity.upper()]

        # Initialize AWS clients
        session = boto3.Session(profile_name=self.profile, region_name=self.region)
        self.securityhub_client = session.client("securityhub")
        self.org_client = session.client("organizations")
        self.sts_client = session.client("sts")

        # Get current account identity
        identity = self.sts_client.get_caller_identity()
        self.current_account_id = identity["Account"]

        # Discover accounts if not provided
        if accounts:
            self.accounts = accounts
            print_info(f"Using specified accounts: {len(accounts)} accounts")
        else:
            discovered_accounts, error = discover_organization_accounts(self.profile, region)
            if error:
                print_warning(f"Organization discovery limitation: {error}")
                print_info("Using current account only (single-account mode)")
                self.accounts = [self.current_account_id]
            else:
                self.accounts = [acc["id"] for acc in discovered_accounts]
                print_success(f"Discovered {len(self.accounts)} accounts via Organizations API")

    def discover_findings(
        self, finding_types: Optional[List[str]] = None, compliance_status: str = "FAILED"
    ) -> List[SecurityFinding]:
        """
        Discover Security Hub findings across accounts.

        Args:
            finding_types: List of finding types to filter (None = all types)
            compliance_status: Compliance status filter (FAILED, PASSED, WARNING)

        Returns:
            List of SecurityFinding objects
        """
        print_info(
            f"Discovering Security Hub findings (severity: {self.severity.name}, accounts: {len(self.accounts)})"
        )

        all_findings = []
        finding_count = 0

        # Filters for Security Hub API
        filters = {
            "SeverityLabel": [{"Value": self.severity.name, "Comparison": "EQUALS"}],
            "ComplianceStatus": [{"Value": compliance_status, "Comparison": "EQUALS"}],
            "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
        }

        # Add account filter if multiple accounts
        if len(self.accounts) > 1:
            filters["AwsAccountId"] = [{"Value": acc, "Comparison": "EQUALS"} for acc in self.accounts]

        try:
            # Use paginator for large result sets
            paginator = self.securityhub_client.get_paginator("get_findings")
            page_iterator = paginator.paginate(Filters=filters, MaxResults=100)

            for page in page_iterator:
                for finding in page["Findings"]:
                    # Extract finding details
                    security_finding = self._parse_security_finding(finding)

                    # Filter by finding types if specified
                    if finding_types:
                        if security_finding.finding_type.value not in finding_types:
                            continue

                    all_findings.append(security_finding)
                    finding_count += 1

            print_success(f"Discovered {finding_count} {self.severity.name} severity findings")

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidAccessException":
                print_error("Security Hub not enabled or insufficient permissions")
                print_info("Required permissions: securityhub:GetFindings")
            else:
                print_error(f"Security Hub API error: {error_code}")

        except Exception as e:
            print_error(f"Unexpected error during finding discovery: {str(e)}")

        return all_findings

    def _parse_security_finding(self, finding: Dict[str, Any]) -> SecurityFinding:
        """
        Parse AWS Security Hub finding into SecurityFinding object.

        Args:
            finding: Raw Security Hub finding dictionary

        Returns:
            SecurityFinding object
        """
        # Extract basic information
        finding_id = finding["Id"]
        title = finding.get("Title", "")
        description = finding.get("Description", "")

        # Extract severity
        severity_label = finding.get("Severity", {}).get("Label", "INFORMATIONAL")
        severity = SecuritySeverity[severity_label.upper()]

        # Extract resource information
        resources = finding.get("Resources", [])
        resource_arn = resources[0].get("Id", "") if resources else ""
        resource_type = resources[0].get("Type", "") if resources else ""

        # Extract compliance and workflow
        compliance_status = finding.get("Compliance", {}).get("Status", "UNKNOWN")
        workflow_status = finding.get("Workflow", {}).get("Status", "NEW")

        # Extract account and region
        account_id = finding.get("AwsAccountId", "")
        region = finding.get("Region", self.region)

        # Product information
        product_name = finding.get("ProductName", "Security Hub")

        # Classify finding type
        finding_type = self._classify_finding_type(title, description, resource_type)

        # Determine if remediation is available
        remediation_available = self._is_remediation_available(finding_type, title)

        return SecurityFinding(
            finding_id=finding_id,
            title=title,
            severity=severity,
            resource_arn=resource_arn,
            resource_type=resource_type,
            account_id=account_id,
            region=region,
            compliance_status=compliance_status,
            workflow_status=workflow_status,
            product_name=product_name,
            finding_type=finding_type,
            description=description,
            remediation_available=remediation_available,
            requires_approval=(severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]),
        )

    def _classify_finding_type(self, title: str, description: str, resource_type: str) -> FindingType:
        """
        Classify finding type based on title, description, and resource type.

        Args:
            title: Finding title
            description: Finding description
            resource_type: AWS resource type

        Returns:
            FindingType enum
        """
        title_lower = title.lower()
        description_lower = description.lower()

        # Security Group patterns
        if "security group" in title_lower or "security group" in resource_type.lower():
            return FindingType.SECURITY_GROUP

        # IAM patterns
        if "iam" in title_lower or "AwsIam" in resource_type:
            return FindingType.IAM

        # S3 patterns
        if "s3" in title_lower or "bucket" in title_lower or "AwsS3Bucket" in resource_type:
            return FindingType.S3

        # CloudTrail patterns
        if "cloudtrail" in title_lower or "trail" in title_lower:
            return FindingType.CLOUDTRAIL

        # Config patterns
        if "config" in title_lower and "aws config" in description_lower:
            return FindingType.CONFIG

        # GuardDuty patterns
        if "guardduty" in title_lower:
            return FindingType.GUARDDUTY

        # EC2 patterns
        if "ec2" in title_lower or "instance" in title_lower or "AwsEc2" in resource_type:
            return FindingType.EC2

        # RDS patterns
        if "rds" in title_lower or "database" in title_lower or "AwsRds" in resource_type:
            return FindingType.RDS

        # Lambda patterns
        if "lambda" in title_lower or "function" in title_lower or "AwsLambda" in resource_type:
            return FindingType.LAMBDA

        return FindingType.OTHER

    def _is_remediation_available(self, finding_type: FindingType, title: str) -> bool:
        """
        Check if automated remediation is available for finding type.

        Args:
            finding_type: FindingType enum
            title: Finding title

        Returns:
            True if remediation available
        """
        # Check if finding matches known remediation patterns
        title_lower = title.lower()

        for workflow_name, workflow in self.REMEDIATION_WORKFLOWS.items():
            pattern = workflow["finding_pattern"].lower()
            if pattern in title_lower:
                return True

        # Additional checks based on finding type
        if finding_type in [FindingType.SECURITY_GROUP, FindingType.S3, FindingType.CLOUDTRAIL]:
            return True

        return False

    def classify_findings(self, findings: List[SecurityFinding]) -> pd.DataFrame:
        """
        Classify findings into structured DataFrame for analysis.

        Args:
            findings: List of SecurityFinding objects

        Returns:
            pandas DataFrame with classified findings
        """
        if not findings:
            print_warning("No findings to classify")
            return pd.DataFrame()

        # Convert findings to dictionary format
        findings_data = []
        for finding in findings:
            findings_data.append(
                {
                    "Finding ID": finding.finding_id,
                    "Account ID": finding.account_id,
                    "Region": finding.region,
                    "Severity": finding.severity.name,
                    "Finding Type": finding.finding_type.value,
                    "Title": finding.title,
                    "Resource ARN": finding.resource_arn,
                    "Resource Type": finding.resource_type,
                    "Compliance Status": finding.compliance_status,
                    "Workflow Status": finding.workflow_status,
                    "Product": finding.product_name,
                    "Remediation Available": finding.remediation_available,
                    "Requires Approval": finding.requires_approval,
                }
            )

        df = pd.DataFrame(findings_data)

        # Sort by severity and account
        df = df.sort_values(["Severity", "Account ID", "Finding Type"], ascending=[False, True, True])

        return df

    def generate_remediation_plan(self, findings_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate remediation workflows based on classified findings.

        Args:
            findings_df: DataFrame with classified findings

        Returns:
            Remediation plan dictionary
        """
        if findings_df.empty:
            print_warning("No findings to generate remediation plan")
            return {"total_findings": 0, "remediations": []}

        print_info(f"Generating remediation plan for {len(findings_df)} findings")

        remediation_plan = {
            "generation_timestamp": datetime.utcnow().isoformat(),
            "total_findings": len(findings_df),
            "total_accounts": findings_df["Account ID"].nunique(),
            "findings_by_type": findings_df["Finding Type"].value_counts().to_dict(),
            "findings_by_severity": findings_df["Severity"].value_counts().to_dict(),
            "remediations": [],
        }

        # Group findings by type for remediation planning
        for finding_type, group in findings_df.groupby("Finding Type"):
            for _, row in group.iterrows():
                remediation = self._create_remediation_action(row)
                remediation_plan["remediations"].append(remediation)

        print_success(f"Generated remediation plan with {len(remediation_plan['remediations'])} actions")

        return remediation_plan

    def _create_remediation_action(self, finding_row: pd.Series) -> Dict[str, Any]:
        """
        Create remediation action for a specific finding.

        Args:
            finding_row: DataFrame row with finding information

        Returns:
            Remediation action dictionary
        """
        finding_type = finding_row["Finding Type"]
        title = finding_row["Title"]
        title_lower = title.lower()

        # Match to remediation workflow
        matched_workflow = None
        for workflow_name, workflow in self.REMEDIATION_WORKFLOWS.items():
            if workflow["finding_pattern"].lower() in title_lower:
                matched_workflow = workflow_name
                break

        remediation = {
            "finding_id": finding_row["Finding ID"],
            "account_id": finding_row["Account ID"],
            "region": finding_row["Region"],
            "finding_type": finding_type,
            "severity": finding_row["Severity"],
            "resource_arn": finding_row["Resource ARN"],
            "remediation_available": finding_row["Remediation Available"],
            "requires_approval": finding_row["Requires Approval"],
            "action_type": "automated" if finding_row["Remediation Available"] else "manual",
        }

        if matched_workflow:
            workflow = self.REMEDIATION_WORKFLOWS[matched_workflow]
            remediation.update(
                {
                    "workflow_name": matched_workflow,
                    "action_description": workflow["action"],
                    "risk_level": workflow["risk"],
                    "automation_status": workflow["automation"],
                    "cli_command": workflow["cli_command"],
                }
            )
        else:
            remediation.update(
                {
                    "workflow_name": "manual_review",
                    "action_description": "Manual security review required",
                    "risk_level": finding_row["Severity"],
                    "automation_status": "Manual review required",
                    "cli_command": None,
                }
            )

        return remediation

    def execute_remediation(self, remediation_plan: Dict[str, Any], dry_run: bool = True) -> List[RemediationResult]:
        """
        Execute remediation workflows (dry-run by default).

        Args:
            remediation_plan: Remediation plan dictionary
            dry_run: If True, only simulate execution (default: True for safety)

        Returns:
            List of RemediationResult objects
        """
        if dry_run:
            console.print(
                create_panel(
                    "[bold yellow]🚨 DRY-RUN MODE ACTIVE[/bold yellow]\n\n"
                    "[dim]No actual changes will be made to AWS resources[/dim]\n"
                    "[dim]Review remediation plan and run with --execute flag to apply changes[/dim]",
                    title="🛡️ Safety Mode",
                    border_style="yellow",
                )
            )
            return self._simulate_remediation(remediation_plan)
        else:
            console.print(
                create_panel(
                    "[bold red]⚠️ EXECUTION MODE ACTIVE[/bold red]\n\n"
                    "[dim]Changes will be applied to AWS resources[/dim]\n"
                    "[dim]Ensure you have reviewed the remediation plan[/dim]",
                    title="🔧 Execute Mode",
                    border_style="red",
                )
            )
            return self._apply_remediation(remediation_plan)

    def _simulate_remediation(self, remediation_plan: Dict[str, Any]) -> List[RemediationResult]:
        """
        Simulate remediation execution (dry-run).

        Args:
            remediation_plan: Remediation plan dictionary

        Returns:
            List of RemediationResult objects
        """
        results = []

        for remediation in remediation_plan["remediations"]:
            result = RemediationResult(
                finding_id=remediation["finding_id"],
                status="simulated",
                message=f"DRY-RUN: Would execute {remediation['action_type']} remediation",
                actions_taken=[
                    f"Action: {remediation['action_description']}",
                    f"Risk: {remediation['risk_level']}",
                    f"Automation: {remediation['automation_status']}",
                ],
                verification_status="not_executed",
            )

            if remediation["requires_approval"]:
                result.status = "approval_required"
                result.message = "DRY-RUN: Manual approval required before execution"

            results.append(result)

        return results

    def _apply_remediation(self, remediation_plan: Dict[str, Any]) -> List[RemediationResult]:
        """
        Apply actual remediation (execute mode).

        Args:
            remediation_plan: Remediation plan dictionary

        Returns:
            List of RemediationResult objects
        """
        results = []

        for remediation in remediation_plan["remediations"]:
            # Check if manual approval required
            if remediation["requires_approval"]:
                result = RemediationResult(
                    finding_id=remediation["finding_id"],
                    status="approval_required",
                    message="Manual approval required before execution",
                    actions_taken=[],
                )
                results.append(result)
                continue

            # Execute remediation (implementation depends on finding type)
            # This is a placeholder - actual implementation would call AWS APIs
            result = RemediationResult(
                finding_id=remediation["finding_id"],
                status="pending_implementation",
                message="Remediation execution not yet implemented",
                actions_taken=["Placeholder for actual AWS API calls"],
            )
            results.append(result)

        return results

    def export_findings_report(self, findings_df: pd.DataFrame, output_file: str) -> None:
        """
        Export findings DataFrame to Excel file.

        Args:
            findings_df: DataFrame with classified findings
            output_file: Output file path (.xlsx)
        """
        try:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Export to Excel
            findings_df.to_excel(output_file, index=False, sheet_name="Security Hub Findings")

            print_success(f"Findings report exported to: {output_file}")

        except Exception as e:
            print_error(f"Failed to export findings report: {str(e)}")

    def export_remediation_plan(self, remediation_plan: Dict[str, Any], output_file: str) -> None:
        """
        Export remediation plan to JSON file.

        Args:
            remediation_plan: Remediation plan dictionary
            output_file: Output file path (.json)
        """
        try:
            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Export to JSON
            with open(output_file, "w") as f:
                json.dump(remediation_plan, f, indent=2)

            print_success(f"Remediation plan exported to: {output_file}")

        except Exception as e:
            print_error(f"Failed to export remediation plan: {str(e)}")
