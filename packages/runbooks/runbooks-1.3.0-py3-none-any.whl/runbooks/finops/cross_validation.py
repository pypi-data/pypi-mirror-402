#!/usr/bin/env python3
"""
Cross-Validation Module: AWS Console CSV vs Cost Explorer API

ADLC Framework: v3.0.0
Category: FinOps Validation
Constitutional Principle: V (Observability & Resilience)

Purpose:
    Compare AWS Console CSV export (ground truth) against Cost Explorer API response
    to identify discrepancies and calculate accuracy score.

Usage:
    from runbooks.finops.cross_validation import CrossValidator

    validator = CrossValidator()
    report = validator.validate(
        csv_path=Path('/path/to/costs.csv'),
        json_data=api_response,
        metric='UnblendedCost'
    )

    if report['summary']['pass']:
        print("Validation PASSED")

Evidence Path: tmp/<project>/finops/cross-validation/
Acceptance Criteria: >=99.5% accuracy required

AWS Documentation References:
    - UnblendedCost is the default for invoices:
      "Net unblended costs is the cost dataset presented on monthly AWS invoices"
      https://aws.amazon.com/blogs/aws-cloud-financial-management/understanding-your-aws-cost-datasets-a-cheat-sheet/

    - Cost Explorer defaults:
      https://docs.aws.amazon.com/cost-management/latest/userguide/ce-advanced.html

Author: Runbooks Team
Version: 1.0.0
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..common.rich_utils import (
    console,
    create_table,
    format_cost,
    print_error,
    print_header,
    print_success,
    print_warning,
)


# Service name mapping: AWS Console CSV -> Cost Explorer API
SERVICE_NAME_MAPPING: dict[str, str] = {
    # Direct mappings where names differ
    "EC2-Other": "EC2 - Other",
    "Tax": "Tax",
    "Relational Database Service": "Amazon Relational Database Service",
    "Savings Plans for  Compute usage": "Savings Plans for AWS Compute usage",
    "S3": "Amazon Simple Storage Service",
    "Support (Enterprise)": "AWS Support (Enterprise)",
    "VPC": "Amazon Virtual Private Cloud",
    "DynamoDB": "Amazon DynamoDB",
    "WorkSpaces": "Amazon WorkSpaces",
    "CloudWatch": "AmazonCloudWatch",
    "Lambda": "AWS Lambda",
    "EC2-Instances": "Amazon Elastic Compute Cloud - Compute",
    "Config": "AWS Config",
    "Glue": "AWS Glue",
    "CloudTrail": "AWS CloudTrail",
    "AppStream": "Amazon AppStream",
    "Key Management Service": "AWS Key Management Service",
    "Elastic Load Balancing": "Amazon Elastic Load Balancing",
    "Route 53": "Amazon Route 53",
    "SQS": "Amazon Simple Queue Service",
    "Security Hub": "AWS Security Hub",
    "GuardDuty": "Amazon GuardDuty",
    "Transfer Family": "AWS Transfer Family",
    "Connect": "Amazon Connect",
    "Direct Connect": "AWS Direct Connect",
    "Contact Center Telecommunications (service sold by AMCS, LLC)": "Contact Center Telecommunications (service sold by AMCS, LLC)",
    "WAF": "AWS WAF",
    "API Gateway": "Amazon API Gateway",
    "Kinesis": "Amazon Kinesis",
    "Contact Lens for  Connect": "Contact Lens for Amazon Connect",
    "Firewall Manager": "AWS Firewall Manager",
    "Directory Service": "AWS Directory Service",
    "DMS": "AWS Database Migration Service",
    "SNS": "Amazon Simple Notification Service",
    "Secrets Manager": "AWS Secrets Manager",
    "SageMaker": "Amazon SageMaker",
    "Cognito": "Amazon Cognito",
    "Elastic Container Service": "Amazon Elastic Container Service",
    "EC2 Container Registry (ECR)": "Amazon EC2 Container Registry (ECR)",
    "Claude 3.5 Sonnet v2 ( Bedrock Edition)": "Claude 3.5 Sonnet v2 (Amazon Bedrock Edition)",
    "SES": "Amazon Simple Email Service",
    "Athena": "Amazon Athena",
    "Step Functions": "AWS Step Functions",
    "MQ": "Amazon MQ",
    "Systems Manager": "AWS Systems Manager",
    "X-Ray": "AWS X-Ray",
    "Kinesis Firehose": "Amazon Kinesis Firehose",
    "Payment Cryptography": "AWS Payment Cryptography",
    "WorkMail": "AmazonWorkMail",
    "CloudWatch Events": "CloudWatch Events",
    "Data Pipeline": "AWS Data Pipeline",
    "CodeBuild": "CodeBuild",
    "End User Messaging": "AWS End User Messaging",
    "Connect Customer Profiles": "Amazon Connect Customer Profiles",
    "Location Service": "Amazon Location Service",
    "Elastic File System": "Amazon Elastic File System",
    "Cloud Map": "AWS Cloud Map",
    "Kinesis Video Streams": "Amazon Kinesis Video Streams",
    "Glacier": "Amazon Glacier",
    "CloudFront": "Amazon CloudFront",
    "CloudShell": "AWS CloudShell",
    "IoT": "AWS IoT",
    "CloudFormation": "AWS CloudFormation",
    "QuickSight": "Amazon QuickSight",
    "Transcribe": "Amazon Transcribe",
    "Kiro": "Kiro",
}

# Enterprise accuracy threshold
ACCURACY_THRESHOLD = 99.5


@dataclass
class ServiceComparison:
    """Comparison result for a single service."""

    csv_service: str
    api_service: str
    csv_cost: float
    api_cost: float
    variance: float
    variance_pct: float
    is_match: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "csv_service": self.csv_service,
            "api_service": self.api_service,
            "csv_cost": round(self.csv_cost, 2),
            "api_cost": round(self.api_cost, 2),
            "variance": round(self.variance, 2),
            "variance_pct": round(self.variance_pct, 2),
            "is_match": self.is_match,
        }


@dataclass
class CrossValidationReport:
    """Cross-validation report with accuracy metrics."""

    timestamp: str
    metric_used: str
    csv_total: float
    api_total: float
    total_variance: float
    total_variance_pct: float
    total_accuracy: float
    services_matched: int
    services_total: int
    service_accuracy: float
    target_accuracy: float
    passed: bool
    comparisons: list[ServiceComparison] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "metric_used": self.metric_used,
            "summary": {
                "csv_total": round(self.csv_total, 2),
                "api_total": round(self.api_total, 2),
                "total_variance": round(self.total_variance, 2),
                "total_variance_pct": round(self.total_variance_pct, 2),
                "total_accuracy": round(self.total_accuracy, 2),
                "services_matched": self.services_matched,
                "services_total": self.services_total,
                "service_accuracy": round(self.service_accuracy, 2),
                "target_accuracy": self.target_accuracy,
                "pass": self.passed,
            },
            "top_variances": [c.to_dict() for c in sorted(
                self.comparisons,
                key=lambda x: abs(x.variance),
                reverse=True
            )[:10]],
            "all_comparisons": [c.to_dict() for c in self.comparisons],
        }


class CrossValidator:
    """
    Cross-validator for AWS Console CSV vs Cost Explorer API.

    Compares ground truth CSV export against API response to measure accuracy.

    Example:
        >>> validator = CrossValidator()
        >>> csv_costs = validator.load_csv_costs(Path('/path/to/costs.csv'))
        >>> json_costs = validator.load_json_costs(api_response, 'UnblendedCost')
        >>> report = validator.cross_validate(csv_costs, json_costs, 'UnblendedCost')
        >>> print(f"Accuracy: {report.total_accuracy}%")
    """

    def __init__(
        self,
        service_mapping: Optional[dict[str, str]] = None,
        accuracy_threshold: float = ACCURACY_THRESHOLD,
    ):
        """
        Initialize cross-validator.

        Args:
            service_mapping: Custom service name mapping (optional)
            accuracy_threshold: Minimum accuracy threshold (default: 99.5%)
        """
        self.service_mapping = service_mapping or SERVICE_NAME_MAPPING
        self.accuracy_threshold = accuracy_threshold

    def load_csv_costs(self, csv_path: Path) -> dict[str, float]:
        """
        Load costs from AWS Console CSV export.

        AWS Console CSV format:
        - Row 1: Headers (Service names)
        - Row 2: "Service total" with values
        - Subsequent rows: Per-day breakdown

        Args:
            csv_path: Path to AWS Console CSV export

        Returns:
            Dict mapping service name to cost amount
        """
        costs: dict[str, float] = {}

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Service names in header
            totals_row = next(reader)  # "Service total" row

            # Parse header to get service names
            # Format: "Service", "EC2-Other($)", "Tax($)", ...
            for i, header in enumerate(headers):
                if header == "Service" or header == "Total costs($)":
                    continue

                # Extract service name from header like "EC2-Other($)"
                service_name = header.replace("($)", "").strip()

                # Get corresponding value from totals row
                if i < len(totals_row):
                    try:
                        cost = float(totals_row[i]) if totals_row[i] else 0.0
                        costs[service_name] = cost
                    except ValueError:
                        pass

            # Get total from last column
            if totals_row and len(totals_row) > 0:
                try:
                    costs["_TOTAL"] = float(totals_row[-1])
                except ValueError:
                    costs["_TOTAL"] = sum(v for k, v in costs.items() if k != "_TOTAL")

        return costs

    def load_json_costs(
        self,
        data: dict[str, Any],
        metric: str = "UnblendedCost",
    ) -> dict[str, float]:
        """
        Load costs from Cost Explorer API response.

        Args:
            data: Cost Explorer API response (or service_response wrapper)
            metric: Cost metric (BlendedCost, UnblendedCost, AmortizedCost)

        Returns:
            Dict mapping service name to cost amount
        """
        costs: dict[str, float] = {}

        # Navigate to service_response -> ResultsByTime -> Groups
        service_response = data.get("service_response", data)
        results = service_response.get("ResultsByTime", [])

        total = 0.0
        for period in results:
            for group in period.get("Groups", []):
                keys = group.get("Keys", [])
                metrics = group.get("Metrics", {})

                if keys and metric in metrics:
                    service_name = keys[0]
                    amount = float(metrics[metric].get("Amount", 0))
                    costs[service_name] = costs.get(service_name, 0) + amount
                    total += amount

        costs["_TOTAL"] = total
        return costs

    def cross_validate(
        self,
        csv_costs: dict[str, float],
        json_costs: dict[str, float],
        metric: str,
    ) -> CrossValidationReport:
        """
        Cross-validate CSV costs against JSON costs.

        Args:
            csv_costs: Costs from CSV (ground truth)
            json_costs: Costs from Cost Explorer API
            metric: Metric name for reporting

        Returns:
            CrossValidationReport with accuracy metrics
        """
        comparisons: list[ServiceComparison] = []
        matched_services = 0

        for csv_service, csv_cost in csv_costs.items():
            if csv_service == "_TOTAL":
                continue

            # Find matching API service name
            api_service = self.service_mapping.get(csv_service, csv_service)
            api_cost = json_costs.get(api_service, 0.0)

            # Calculate variance
            variance = api_cost - csv_cost
            variance_pct = (variance / csv_cost * 100) if csv_cost != 0 else 0

            # Determine if match is acceptable (<=0.5% variance)
            is_match = abs(variance_pct) <= 0.5
            if is_match:
                matched_services += 1

            comparisons.append(ServiceComparison(
                csv_service=csv_service,
                api_service=api_service,
                csv_cost=csv_cost,
                api_cost=api_cost,
                variance=variance,
                variance_pct=variance_pct,
                is_match=is_match,
            ))

        # Calculate totals
        csv_total = csv_costs.get("_TOTAL", sum(v for k, v in csv_costs.items() if k != "_TOTAL"))
        api_total = json_costs.get("_TOTAL", sum(v for k, v in json_costs.items() if k != "_TOTAL"))
        total_variance = api_total - csv_total
        total_variance_pct = (total_variance / csv_total * 100) if csv_total != 0 else 0

        # Calculate accuracy
        total_services = len([k for k in csv_costs.keys() if k != "_TOTAL"])
        service_accuracy = (matched_services / total_services * 100) if total_services > 0 else 0
        total_accuracy = 100 - abs(total_variance_pct)

        return CrossValidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            metric_used=metric,
            csv_total=csv_total,
            api_total=api_total,
            total_variance=total_variance,
            total_variance_pct=total_variance_pct,
            total_accuracy=total_accuracy,
            services_matched=matched_services,
            services_total=total_services,
            service_accuracy=service_accuracy,
            target_accuracy=self.accuracy_threshold,
            passed=total_accuracy >= self.accuracy_threshold,
            comparisons=comparisons,
        )

    def validate(
        self,
        csv_path: Path,
        json_data: dict[str, Any],
        metric: str = "UnblendedCost",
    ) -> dict[str, Any]:
        """
        Full validation workflow: load CSV, load JSON, cross-validate.

        Args:
            csv_path: Path to AWS Console CSV export
            json_data: Cost Explorer API response
            metric: Cost metric to validate

        Returns:
            Validation report as dictionary
        """
        csv_costs = self.load_csv_costs(csv_path)
        json_costs = self.load_json_costs(json_data, metric)
        report = self.cross_validate(csv_costs, json_costs, metric)
        return report.to_dict()

    def print_summary(self, report: CrossValidationReport | dict[str, Any]) -> None:
        """Print human-readable summary using Rich console."""
        if isinstance(report, dict):
            summary = report.get("summary", report)
            metric_used = report.get("metric_used", "Unknown")
            timestamp = report.get("timestamp", "Unknown")
            top_variances = report.get("top_variances", [])
        else:
            summary = {
                "csv_total": report.csv_total,
                "api_total": report.api_total,
                "total_variance": report.total_variance,
                "total_variance_pct": report.total_variance_pct,
                "total_accuracy": report.total_accuracy,
                "services_matched": report.services_matched,
                "services_total": report.services_total,
                "service_accuracy": report.service_accuracy,
                "target_accuracy": report.target_accuracy,
                "pass": report.passed,
            }
            metric_used = report.metric_used
            timestamp = report.timestamp
            top_variances = [c.to_dict() for c in sorted(
                report.comparisons,
                key=lambda x: abs(x.variance),
                reverse=True
            )[:10]]

        print_header("CROSS-VALIDATION REPORT")
        console.print(f"[bold]Metric Used:[/bold] {metric_used}")
        console.print(f"[bold]Timestamp:[/bold] {timestamp}")
        console.print()

        console.print(f"[bold]CSV Total (Ground Truth):[/bold] {format_cost(summary['csv_total'])}")
        console.print(f"[bold]API Total ({metric_used}):[/bold] {format_cost(summary['api_total'])}")
        console.print(f"[bold]Variance:[/bold] {format_cost(summary['total_variance'])} ({summary['total_variance_pct']:.2f}%)")
        console.print()

        # Status
        accuracy = summary['total_accuracy']
        target = summary['target_accuracy']
        passed = summary.get('pass', accuracy >= target)

        if passed:
            print_success(f"Total Accuracy: {accuracy:.2f}% (Target: {target}%)")
        else:
            print_error(f"Total Accuracy: {accuracy:.2f}% (Target: {target}%) - BELOW THRESHOLD")

        console.print(f"[bold]Services Matched (<=0.5%):[/bold] {summary['services_matched']}/{summary['services_total']}")
        console.print(f"[bold]Service Match Rate:[/bold] {summary['service_accuracy']:.2f}%")

        # Top variances table
        if top_variances:
            console.print()
            print_header("TOP 10 VARIANCES")
            table = create_table("Service Variance Analysis")
            table.add_column("Service", style="cyan")
            table.add_column("CSV", justify="right")
            table.add_column("API", justify="right")
            table.add_column("Variance", justify="right")
            table.add_column("Status", justify="center")

            for comp in top_variances[:10]:
                status = "[green]PASS[/green]" if comp['is_match'] else "[red]FAIL[/red]"
                table.add_row(
                    comp['csv_service'][:30],
                    format_cost(comp['csv_cost']),
                    format_cost(comp['api_cost']),
                    f"{format_cost(comp['variance'])} ({comp['variance_pct']:.1f}%)",
                    status,
                )

            console.print(table)


def save_report(
    report: dict[str, Any],
    output_dir: Path,
    metric: str,
) -> Path:
    """Save cross-validation report to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    output_path = output_dir / f"cross-validation-{metric}-{timestamp}.json"

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    return output_path
