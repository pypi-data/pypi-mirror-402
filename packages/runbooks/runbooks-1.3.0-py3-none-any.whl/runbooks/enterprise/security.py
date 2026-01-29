"""
Enterprise Security Module - Enhanced Security Logging & VPC Security Assessment
===============================================================================

Enterprise-grade security module providing enhanced security logging, VPC security
assessment, compliance framework integration, and risk classification for the
Runbooks platform. This module integrates with the three-bucket VPC
cleanup strategy and provides comprehensive security audit trails.

Key Features:
- Enhanced Security Logging with Rich CLI integration
- VPC Security Posture Assessment (ACLs, Security Groups, Flow Logs)
- Multi-Framework Compliance (SOC2, PCI-DSS, HIPAA, NIST, ISO27001)
- Security Risk Classification (LOW/MEDIUM/HIGH)
- SHA256 Audit Trail Generation
- Integration with VPC Cleanup Safety Controls

Author: DevOps Security Engineer (Enterprise Agile Team)
Coordination: enterprise-product-owner → devops-security-engineer → python-runbooks-engineer → qa-testing-specialist
Framework: Enterprise Security-as-Code with FAANG SDLC compliance
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Rich CLI integration for enterprise UX standards
from runbooks.common.rich_utils import (
    console,
    create_panel,
    create_progress_bar,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
    STATUS_INDICATORS,
    CLOUDOPS_THEME,
)

# Profile management integration
try:
    from runbooks.common.profile_utils import create_session
except ImportError:
    # Fallback for profile management
    def create_session(profile_name: str):
        return boto3.Session(profile_name=profile_name)


class SecurityRiskLevel(Enum):
    """Security risk classification levels for enterprise decision making."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceFramework(Enum):
    """Supported compliance frameworks for enterprise validation."""

    SOC2 = "SOC2"
    PCI_DSS = "PCI-DSS"
    HIPAA = "HIPAA"
    NIST = "NIST"
    ISO27001 = "ISO27001"
    CIS = "CIS_Benchmarks"
    AWS_WAF = "AWS_Well_Architected"


class VPCSecurityAnalysis:
    """VPC Security Analysis results for cleanup integration."""

    def __init__(self, vpc_id: str, region: str):
        self.vpc_id = vpc_id
        self.region = region
        self.timestamp = datetime.now(timezone.utc)
        self.security_groups: List[Dict[str, Any]] = []
        self.nacls: List[Dict[str, Any]] = []
        self.flow_logs: List[Dict[str, Any]] = []
        self.route_tables: List[Dict[str, Any]] = []
        self.findings: List[Dict[str, Any]] = []
        self.risk_level = SecurityRiskLevel.LOW
        self.compliance_status: Dict[str, bool] = {}

    def add_finding(self, severity: str, title: str, description: str, resource: str):
        """Add a security finding to the analysis."""
        finding = {
            "severity": severity,
            "title": title,
            "description": description,
            "resource": resource,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "vpc_id": self.vpc_id,
        }
        self.findings.append(finding)

        # Update overall risk level based on findings
        if severity == "HIGH" or severity == "CRITICAL":
            if self.risk_level in [SecurityRiskLevel.LOW, SecurityRiskLevel.MEDIUM]:
                self.risk_level = SecurityRiskLevel.HIGH if severity == "HIGH" else SecurityRiskLevel.CRITICAL
        elif severity == "MEDIUM" and self.risk_level == SecurityRiskLevel.LOW:
            self.risk_level = SecurityRiskLevel.MEDIUM


class EnterpriseSecurityLogger:
    """Enhanced security logger with enterprise audit trails and Rich CLI integration."""

    def __init__(self, module_name: str, log_dir: Optional[Path] = None):
        """
        Initialize enterprise security logger.

        Args:
            module_name: Name of the module requesting logging
            log_dir: Optional directory for security logs
        """
        self.module_name = module_name
        self.log_dir = log_dir or Path.home() / ".runbooks" / "security-logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create security-specific log file
        self.log_file = self.log_dir / f"{module_name}-security-{datetime.now().strftime('%Y%m%d')}.jsonl"

        # Initialize standard logger as fallback
        self.logger = logging.getLogger(f"runbooks.security.{module_name}")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            # Console handler with Rich CLI integration
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter(f"{STATUS_INDICATORS['info']} %(asctime)s | SECURITY | %(message)s")
            )
            self.logger.addHandler(console_handler)

            # File handler for audit trails
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s | %(levelname)s | SECURITY | %(name)s | %(message)s")
            )
            self.logger.addHandler(file_handler)

    def log_security_event(self, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a security event with comprehensive audit trail.

        Args:
            event_type: Type of security event (VPC_ANALYSIS, COMPLIANCE_CHECK, etc.)
            message: Human-readable message
            metadata: Additional structured metadata
        """
        security_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": self.module_name,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
            "correlation_id": self._generate_correlation_id(),
        }

        # Generate SHA256 hash for tamper detection
        event_hash = self._generate_event_hash(security_event)
        security_event["event_hash"] = event_hash

        # Write to audit file
        with open(self.log_file, "a") as f:
            f.write(json.dumps(security_event) + "\n")

        # Rich CLI output
        console.print(f"{STATUS_INDICATORS['info']} [security]SECURITY[/security] | {event_type} | {message}")

        # Standard logger
        self.logger.info(f"{event_type} | {message} | Hash: {event_hash[:8]}...")

    def log_vpc_security_analysis(self, analysis: VPCSecurityAnalysis):
        """Log VPC security analysis results."""
        self.log_security_event(
            "VPC_SECURITY_ANALYSIS",
            f"VPC {analysis.vpc_id} security assessment completed - Risk: {analysis.risk_level.value}",
            {
                "vpc_id": analysis.vpc_id,
                "region": analysis.region,
                "findings_count": len(analysis.findings),
                "risk_level": analysis.risk_level.value,
                "compliance_status": analysis.compliance_status,
                "security_groups_count": len(analysis.security_groups),
                "nacls_count": len(analysis.nacls),
                "flow_logs_enabled": len(analysis.flow_logs) > 0,
            },
        )

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for tracking operations."""
        import uuid

        return str(uuid.uuid4())[:8]

    def _generate_event_hash(self, event_data: Dict[str, Any]) -> str:
        """Generate SHA256 hash for security event integrity."""
        # Remove hash field if present to avoid circular reference
        event_copy = event_data.copy()
        event_copy.pop("event_hash", None)

        # Create deterministic string representation
        event_string = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_string.encode()).hexdigest()


def get_enhanced_logger(module_name: str) -> EnterpriseSecurityLogger:
    """
    Get enhanced security logger for enterprise audit trails.

    This is the main function called by VPC cleanup and other modules
    that need enhanced security logging capabilities.

    Args:
        module_name: Name of the requesting module

    Returns:
        EnterpriseSecurityLogger instance with audit trail capabilities
    """
    return EnterpriseSecurityLogger(module_name)


def assess_vpc_security_posture(vpc_id: str, profile: str, region: str = "ap-southeast-2") -> VPCSecurityAnalysis:
    """
    Comprehensive VPC security posture assessment.

    Analyzes VPC security configuration including Security Groups, NACLs,
    Flow Logs, and route tables to identify security risks and compliance
    issues before VPC cleanup operations.

    Args:
        vpc_id: VPC ID to analyze
        profile: AWS profile for authentication
        region: AWS region (default: ap-southeast-2)

    Returns:
        VPCSecurityAnalysis object with comprehensive security findings
    """
    console.print(f"{STATUS_INDICATORS['running']} [security]Assessing VPC security posture for {vpc_id}[/security]")

    analysis = VPCSecurityAnalysis(vpc_id, region)

    try:
        # Create AWS session with specified profile
        session = create_session(profile)
        ec2 = session.client("ec2", region_name=region)

        with create_progress_bar() as progress:
            task = progress.add_task("[security]Security Assessment[/security]", total=4)

            # 1. Analyze Security Groups
            progress.update(task, description="[security]Analyzing Security Groups[/security]")
            security_groups = _analyze_security_groups(ec2, vpc_id, analysis)
            analysis.security_groups = security_groups
            progress.advance(task)

            # 2. Analyze Network ACLs
            progress.update(task, description="[security]Analyzing Network ACLs[/security]")
            nacls = _analyze_network_acls(ec2, vpc_id, analysis)
            analysis.nacls = nacls
            progress.advance(task)

            # 3. Check VPC Flow Logs
            progress.update(task, description="[security]Checking VPC Flow Logs[/security]")
            flow_logs = _analyze_flow_logs(ec2, vpc_id, analysis)
            analysis.flow_logs = flow_logs
            progress.advance(task)

            # 4. Analyze Route Tables
            progress.update(task, description="[security]Analyzing Route Tables[/security]")
            route_tables = _analyze_route_tables(ec2, vpc_id, analysis)
            analysis.route_tables = route_tables
            progress.advance(task)

        # Log the security analysis
        logger = get_enhanced_logger("vpc_cleanup")
        logger.log_vpc_security_analysis(analysis)

        # Display results with Rich CLI
        _display_security_analysis_results(analysis)

        console.print(
            f"{STATUS_INDICATORS['success']} [security]VPC security assessment completed - Risk: {analysis.risk_level.value}[/security]"
        )

    except ClientError as e:
        error_msg = f"AWS API error during VPC security assessment: {e}"
        console.print(f"{STATUS_INDICATORS['error']} [error]{error_msg}[/error]")
        analysis.add_finding("HIGH", "API Access Error", error_msg, vpc_id)

    except Exception as e:
        error_msg = f"Unexpected error during VPC security assessment: {e}"
        console.print(f"{STATUS_INDICATORS['error']} [error]{error_msg}[/error]")
        analysis.add_finding("MEDIUM", "Assessment Error", error_msg, vpc_id)

    return analysis


def validate_compliance_requirements(resource_data: Dict[str, Any], frameworks: List[str]) -> Dict[str, bool]:
    """
    Validate resource configuration against compliance frameworks.

    Args:
        resource_data: Resource configuration data to validate
        frameworks: List of compliance frameworks to check against

    Returns:
        Dict mapping framework names to compliance status (True/False)
    """
    compliance_results = {}

    for framework in frameworks:
        try:
            framework_enum = ComplianceFramework(framework.upper().replace("-", "_"))
            compliance_results[framework] = _check_framework_compliance(resource_data, framework_enum)
        except ValueError:
            console.print(
                f"{STATUS_INDICATORS['warning']} [warning]Unknown compliance framework: {framework}[/warning]"
            )
            compliance_results[framework] = False

    return compliance_results


def evaluate_security_baseline(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate security baseline from analysis results.

    Args:
        analysis_results: Combined analysis results from VPC assessment

    Returns:
        Security baseline evaluation with recommendations
    """
    baseline_evaluation = {
        "baseline_score": 0,
        "max_score": 100,
        "recommendations": [],
        "critical_findings": [],
        "compliance_gaps": [],
    }

    # Security Groups baseline (25 points)
    sg_score = _evaluate_security_groups_baseline(analysis_results.get("security_groups", []))
    baseline_evaluation["baseline_score"] += sg_score

    # Network ACLs baseline (25 points)
    nacl_score = _evaluate_nacls_baseline(analysis_results.get("nacls", []))
    baseline_evaluation["baseline_score"] += nacl_score

    # Flow Logs baseline (25 points)
    flow_logs_score = _evaluate_flow_logs_baseline(analysis_results.get("flow_logs", []))
    baseline_evaluation["baseline_score"] += flow_logs_score

    # Route Tables baseline (25 points)
    route_tables_score = _evaluate_route_tables_baseline(analysis_results.get("route_tables", []))
    baseline_evaluation["baseline_score"] += route_tables_score

    # Generate recommendations based on score
    if baseline_evaluation["baseline_score"] < 70:
        baseline_evaluation["recommendations"].append("Immediate security review required")
        baseline_evaluation["critical_findings"].append("Security baseline below acceptable threshold")
    elif baseline_evaluation["baseline_score"] < 85:
        baseline_evaluation["recommendations"].append("Security improvements recommended")
    else:
        baseline_evaluation["recommendations"].append("Security posture meets enterprise standards")

    return baseline_evaluation


def classify_security_risk(resource_analysis: Dict[str, Any]) -> str:
    """
    Classify security risk level for enterprise decision making.

    Args:
        resource_analysis: Resource security analysis data

    Returns:
        Risk classification: LOW, MEDIUM, HIGH, or CRITICAL
    """
    risk_factors = []

    # Check for critical security misconfigurations
    findings = resource_analysis.get("findings", [])
    critical_count = len([f for f in findings if f.get("severity") == "CRITICAL"])
    high_count = len([f for f in findings if f.get("severity") == "HIGH"])

    if critical_count > 0:
        return SecurityRiskLevel.CRITICAL.value
    elif high_count >= 3:
        return SecurityRiskLevel.HIGH.value
    elif high_count > 0 or len(findings) >= 5:
        return SecurityRiskLevel.MEDIUM.value
    else:
        return SecurityRiskLevel.LOW.value


# Private helper functions for detailed security analysis


def _analyze_security_groups(ec2_client, vpc_id: str, analysis: VPCSecurityAnalysis) -> List[Dict[str, Any]]:
    """Analyze Security Groups for security risks."""
    try:
        response = ec2_client.describe_security_groups(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])

        security_groups = []
        for sg in response["SecurityGroups"]:
            sg_analysis = {
                "group_id": sg["GroupId"],
                "group_name": sg["GroupName"],
                "description": sg["Description"],
                "inbound_rules": sg.get("IpPermissions", []),
                "outbound_rules": sg.get("IpPermissionsEgress", []),
            }

            # Check for overly permissive rules
            _check_security_group_rules(sg, analysis)
            security_groups.append(sg_analysis)

        return security_groups

    except ClientError as e:
        analysis.add_finding("MEDIUM", "Security Groups Analysis Failed", str(e), vpc_id)
        return []


def _analyze_network_acls(ec2_client, vpc_id: str, analysis: VPCSecurityAnalysis) -> List[Dict[str, Any]]:
    """Analyze Network ACLs for security configuration."""
    try:
        response = ec2_client.describe_network_acls(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])

        nacls = []
        for nacl in response["NetworkAcls"]:
            nacl_analysis = {
                "nacl_id": nacl["NetworkAclId"],
                "is_default": nacl["IsDefault"],
                "entries": nacl.get("Entries", []),
                "associations": nacl.get("Associations", []),
            }

            # Check for default NACL usage (potential security risk)
            if nacl["IsDefault"]:
                analysis.add_finding(
                    "LOW",
                    "Default NACL in use",
                    "Consider creating custom NACLs for better security control",
                    nacl["NetworkAclId"],
                )

            nacls.append(nacl_analysis)

        return nacls

    except ClientError as e:
        analysis.add_finding("MEDIUM", "Network ACLs Analysis Failed", str(e), vpc_id)
        return []


def _analyze_flow_logs(ec2_client, vpc_id: str, analysis: VPCSecurityAnalysis) -> List[Dict[str, Any]]:
    """Check VPC Flow Logs configuration."""
    try:
        response = ec2_client.describe_flow_logs(
            Filters=[{"Name": "resource-id", "Values": [vpc_id]}, {"Name": "resource-type", "Values": ["VPC"]}]
        )

        flow_logs = response.get("FlowLogs", [])

        if not flow_logs:
            analysis.add_finding(
                "MEDIUM",
                "VPC Flow Logs not enabled",
                "Enable VPC Flow Logs for network monitoring and security analysis",
                vpc_id,
            )
        else:
            for flow_log in flow_logs:
                if flow_log["FlowLogStatus"] != "ACTIVE":
                    analysis.add_finding(
                        "MEDIUM",
                        f"Flow Log {flow_log['FlowLogId']} not active",
                        f"Flow Log status: {flow_log['FlowLogStatus']}",
                        flow_log["FlowLogId"],
                    )

        return [{"flow_log_id": fl.get("FlowLogId"), "status": fl.get("FlowLogStatus")} for fl in flow_logs]

    except ClientError as e:
        analysis.add_finding("MEDIUM", "Flow Logs Analysis Failed", str(e), vpc_id)
        return []


def _analyze_route_tables(ec2_client, vpc_id: str, analysis: VPCSecurityAnalysis) -> List[Dict[str, Any]]:
    """Analyze Route Tables for security implications."""
    try:
        response = ec2_client.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])

        route_tables = []
        for rt in response["RouteTables"]:
            rt_analysis = {
                "route_table_id": rt["RouteTableId"],
                "routes": rt.get("Routes", []),
                "associations": rt.get("Associations", []),
            }

            # Check for overly broad routes
            for route in rt.get("Routes", []):
                if route.get("DestinationCidrBlock") == "0.0.0.0/0":
                    gateway_id = route.get("GatewayId", "")
                    if gateway_id.startswith("igw-"):
                        analysis.add_finding(
                            "HIGH",
                            "Public route detected",
                            f"Route table {rt['RouteTableId']} has public internet access via {gateway_id}",
                            rt["RouteTableId"],
                        )

            route_tables.append(rt_analysis)

        return route_tables

    except ClientError as e:
        analysis.add_finding("MEDIUM", "Route Tables Analysis Failed", str(e), vpc_id)
        return []


def _check_security_group_rules(security_group: Dict[str, Any], analysis: VPCSecurityAnalysis):
    """Check Security Group rules for common security issues."""
    sg_id = security_group["GroupId"]

    # Check inbound rules
    for rule in security_group.get("IpPermissions", []):
        for ip_range in rule.get("IpRanges", []):
            if ip_range.get("CidrIp") == "0.0.0.0/0":
                ports = f"{rule.get('FromPort', 'All')}-{rule.get('ToPort', 'All')}"
                analysis.add_finding(
                    "HIGH",
                    "Overly permissive Security Group",
                    f"Security Group {sg_id} allows inbound access from anywhere (0.0.0.0/0) on ports {ports}",
                    sg_id,
                )


def _check_framework_compliance(resource_data: Dict[str, Any], framework: ComplianceFramework) -> bool:
    """Check resource compliance against specific framework."""
    if framework == ComplianceFramework.SOC2:
        # SOC2 requires logging and access controls
        return resource_data.get("flow_logs_enabled", False) and len(resource_data.get("security_groups", [])) > 0
    elif framework == ComplianceFramework.PCI_DSS:
        # PCI-DSS requires strict access controls
        findings = resource_data.get("findings", [])
        high_severity_findings = [f for f in findings if f.get("severity") in ["HIGH", "CRITICAL"]]
        return len(high_severity_findings) == 0
    elif framework == ComplianceFramework.HIPAA:
        # HIPAA requires encryption and access logging
        return resource_data.get("flow_logs_enabled", False) and resource_data.get("baseline_score", 0) >= 85
    else:
        # Default compliance check
        return resource_data.get("baseline_score", 0) >= 70


def _evaluate_security_groups_baseline(security_groups: List[Dict[str, Any]]) -> int:
    """Evaluate Security Groups against security baseline (max 25 points)."""
    if not security_groups:
        return 0

    score = 25
    for sg in security_groups:
        # Check for overly permissive rules
        inbound_rules = sg.get("inbound_rules", [])
        for rule in inbound_rules:
            for ip_range in rule.get("IpRanges", []):
                if ip_range.get("CidrIp") == "0.0.0.0/0":
                    score -= 5  # Deduct points for open access

    return max(0, score)


def _evaluate_nacls_baseline(nacls: List[Dict[str, Any]]) -> int:
    """Evaluate Network ACLs against security baseline (max 25 points)."""
    if not nacls:
        return 10  # Partial score for having no custom NACLs

    score = 25
    default_nacl_count = len([n for n in nacls if n.get("is_default", False)])
    if default_nacl_count > 0:
        score -= 5  # Deduct for using default NACLs

    return max(10, score)


def _evaluate_flow_logs_baseline(flow_logs: List[Dict[str, Any]]) -> int:
    """Evaluate Flow Logs against security baseline (max 25 points)."""
    if not flow_logs:
        return 0  # No flow logs = no points

    active_flow_logs = len([fl for fl in flow_logs if fl.get("status") == "ACTIVE"])
    return 25 if active_flow_logs > 0 else 10


def _evaluate_route_tables_baseline(route_tables: List[Dict[str, Any]]) -> int:
    """Evaluate Route Tables against security baseline (max 25 points)."""
    if not route_tables:
        return 0

    score = 25
    for rt in route_tables:
        for route in rt.get("routes", []):
            if route.get("DestinationCidrBlock") == "0.0.0.0/0" and route.get("GatewayId", "").startswith("igw-"):
                score -= 3  # Deduct for public routes

    return max(15, score)


def _display_security_analysis_results(analysis: VPCSecurityAnalysis):
    """Display security analysis results with Rich CLI formatting."""

    # Create summary table
    table = create_table(
        title=f"VPC Security Analysis - {analysis.vpc_id}",
        columns=[
            {"name": "Component", "style": "cyan"},
            {"name": "Count", "style": "white"},
            {"name": "Status", "style": "green"},
        ],
    )

    table.add_row("Security Groups", str(len(analysis.security_groups)), "✅ Analyzed")
    table.add_row("Network ACLs", str(len(analysis.nacls)), "✅ Analyzed")
    table.add_row("Flow Logs", str(len(analysis.flow_logs)), "✅ Checked" if analysis.flow_logs else "❌ Missing")
    table.add_row("Route Tables", str(len(analysis.route_tables)), "✅ Analyzed")

    console.print(table)

    # Display findings if any
    if analysis.findings:
        findings_table = create_table(
            title="Security Findings",
            columns=[
                {"name": "Severity", "style": "red bold"},
                {"name": "Finding", "style": "yellow"},
                {"name": "Resource", "style": "cyan"},
            ],
        )

        for finding in analysis.findings:
            findings_table.add_row(finding["severity"], finding["title"], finding["resource"])

        console.print(findings_table)

    # Risk level summary
    risk_style = {
        SecurityRiskLevel.LOW: "green",
        SecurityRiskLevel.MEDIUM: "yellow",
        SecurityRiskLevel.HIGH: "red",
        SecurityRiskLevel.CRITICAL: "red bold",
    }.get(analysis.risk_level, "white")

    risk_panel = create_panel(
        f"Overall Security Risk: [{risk_style}]{analysis.risk_level.value}[/{risk_style}]\n"
        f"Findings: {len(analysis.findings)}\n"
        f"Analysis Time: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        title="[security]Security Risk Assessment[/security]",
        border_style=risk_style,
    )

    console.print(risk_panel)


# Export the main functions needed by VPC cleanup and other modules
__all__ = [
    "get_enhanced_logger",
    "assess_vpc_security_posture",
    "validate_compliance_requirements",
    "evaluate_security_baseline",
    "classify_security_risk",
    "SecurityRiskLevel",
    "ComplianceFramework",
    "VPCSecurityAnalysis",
    "EnterpriseSecurityLogger",
]
