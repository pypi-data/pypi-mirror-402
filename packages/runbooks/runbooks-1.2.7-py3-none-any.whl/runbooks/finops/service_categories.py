#!/usr/bin/env python3
"""
AWS Official Service Categories - aligned with AWS Whitepaper taxonomy.

This module provides service categorization based on the official AWS service categories
from the AWS Overview Whitepaper:
https://docs.aws.amazon.com/whitepapers/latest/aws-overview/amazon-web-services-cloud-platform.html

v1.1.29: Single source of truth for service categorization across --profile and --all-profile modes.
"""

from typing import Dict, Optional

from runbooks.finops.service_mapping import get_service_display_name

# AWS Official Service Categories (23 categories from AWS Whitepaper)
# Using full service names as returned by Cost Explorer API for reliable matching
AWS_SERVICE_CATEGORIES: Dict[str, list] = {
    "Compute": [
        "Amazon Elastic Compute Cloud",
        "Amazon Elastic Compute Cloud - Compute",
        "EC2 - Other",  # EBS/Snapshots/Data Transfer (AWS bundles here per v1.1.20)
        "AWS Lambda",
        "Amazon Elastic Container Service",
        "Amazon ECS",
        "AWS Fargate",
        "AWS Batch",
        "Amazon Lightsail",
        "AWS App Runner",
        "Amazon EC2 Container Registry",
        "AWS Elastic Beanstalk",
    ],
    "Storage": [
        "Amazon Simple Storage Service",
        "Amazon Elastic Block Store",  # When shown as separate line item
        "Amazon Elastic File System",
        "Amazon FSx",
        "AWS Backup",
        "AWS Storage Gateway",
        "Amazon S3 Glacier",
        "Amazon Glacier",
    ],
    "Databases": [
        "Amazon Relational Database Service",
        "Amazon DynamoDB",
        "Amazon ElastiCache",
        "Amazon Neptune",
        "Amazon DocumentDB",
        "Amazon Redshift",
        "Amazon Timestream",
        "Amazon MemoryDB",
        "Amazon Keyspaces",
    ],
    "Networking & Content Delivery": [
        "Amazon Virtual Private Cloud",
        "Amazon CloudFront",
        "Amazon Route 53",
        "Amazon API Gateway",
        "AWS Direct Connect",
        "Elastic Load Balancing",
        "AWS Transit Gateway",
        "AWS PrivateLink",
        "AWS Global Accelerator",
        "Amazon VPC",
    ],
    "Management & Governance": [
        "AmazonCloudWatch",
        "Amazon CloudWatch",
        "AWS CloudTrail",
        "AWS Config",
        "AWS Systems Manager",
        "AWS CloudFormation",
        "AWS Service Catalog",
        "AWS Trusted Advisor",
        "AWS Organizations",
        "AWS Control Tower",
        "AWS License Manager",
    ],
    "Security, Identity & Compliance": [
        "AWS Key Management Service",
        "AWS Secrets Manager",
        "Amazon GuardDuty",
        "AWS Security Hub",
        "AWS WAF",
        "AWS Shield",
        "AWS Directory Service",
        "Amazon Cognito",
        "AWS Certificate Manager",
        "AWS Identity and Access Management",
        "Amazon Inspector",
        "Amazon Macie",
        "AWS Firewall Manager",
    ],
    "End User Computing": [
        "Amazon WorkSpaces",
        "Amazon AppStream 2.0",
        "Amazon AppStream",
        "Amazon WorkDocs",
        "Amazon WorkLink",
    ],
    "Analytics": [
        "Amazon Kinesis",
        "Amazon EMR",
        "AWS Glue",
        "Amazon Athena",
        "Amazon QuickSight",
        "Amazon OpenSearch Service",
        "Amazon Elasticsearch Service",
        "AWS Data Pipeline",
        "AWS Lake Formation",
        "Amazon Managed Streaming for Apache Kafka",
    ],
    "Application Integration": [
        "Amazon Simple Queue Service",
        "Amazon Simple Notification Service",
        "Amazon EventBridge",
        "AWS Step Functions",
        "Amazon MQ",
        "Amazon AppFlow",
    ],
    # v1.1.29: Developer Tools merged into Other per user request
    "Machine Learning": [
        "Amazon SageMaker",
        "Amazon Rekognition",
        "Amazon Comprehend",
        "Amazon Translate",
        "Amazon Polly",
        "Amazon Lex",
        "Amazon Textract",
        "Amazon Transcribe",
        "Amazon Personalize",
        "Amazon Forecast",
        "Amazon Bedrock",
    ],
    "Containers": [
        "Amazon Elastic Container Registry",
        "Amazon Elastic Container Service",
        "Amazon Elastic Kubernetes Service",
        "AWS App Mesh",
    ],
    # v1.1.29: Business Applications merged into Other per user request
    # v1.1.29: Cloud Financial Management merged into Other per user request
    "Migration & Transfer": [
        "AWS Database Migration Service",
        "AWS Migration Hub",
        "AWS DataSync",
        "AWS Transfer Family",
        "AWS Snow Family",
        "AWS Application Migration Service",
    ],
    "Internet of Things": [
        "AWS IoT Core",
        "AWS IoT Device Management",
        "AWS IoT Analytics",
        "AWS IoT Events",
        "AWS IoT Greengrass",
    ],
    "Media Services": [
        "Amazon Elastic Transcoder",
        "AWS Elemental MediaConvert",
        "AWS Elemental MediaLive",
        "AWS Elemental MediaPackage",
        "Amazon Interactive Video Service",
    ],
}

# Reverse lookup from service_mapping.py abbreviations to categories
# Used as fallback when full name matching fails
ABBREV_TO_CATEGORY: Dict[str, str] = {
    # Storage
    "S3": "Storage",
    "EBS": "Storage",
    "EFS": "Storage",
    "FSx": "Storage",
    "Storage-GW": "Storage",
    "Glacier": "Storage",
    # Compute
    "EC2": "Compute",
    "EC2-Instances": "Compute",
    "EC2-Other": "Compute",
    "Lambda": "Compute",
    "ECS": "Compute",
    "EKS": "Compute",
    "Fargate": "Compute",
    "Batch": "Compute",
    "Lightsail": "Compute",
    "ECR": "Compute",
    # Databases
    "RDS": "Databases",
    "DynamoDB": "Databases",
    "ElastiCache": "Databases",
    "Neptune": "Databases",
    "DocumentDB": "Databases",
    "Redshift": "Databases",
    "Timestream": "Databases",
    # Networking
    "VPC": "Networking & Content Delivery",
    "CloudFront": "Networking & Content Delivery",
    "Route53": "Networking & Content Delivery",
    "API-Gateway": "Networking & Content Delivery",
    "DirectConnect": "Networking & Content Delivery",
    "ELB": "Networking & Content Delivery",
    "Transit-GW": "Networking & Content Delivery",
    # Management & Governance
    "CloudWatch": "Management & Governance",
    "CloudTrail": "Management & Governance",
    "Config": "Management & Governance",
    "SSM": "Management & Governance",
    "CloudFormation": "Management & Governance",
    # Security
    "KMS": "Security, Identity & Compliance",
    "Secrets-Mgr": "Security, Identity & Compliance",
    "GuardDuty": "Security, Identity & Compliance",
    "Security-Hub": "Security, Identity & Compliance",
    "WAF": "Security, Identity & Compliance",
    "Shield": "Security, Identity & Compliance",
    "Directory": "Security, Identity & Compliance",
    "Cognito": "Security, Identity & Compliance",
    "ACM": "Security, Identity & Compliance",
    "IAM": "Security, Identity & Compliance",
    "Inspector": "Security, Identity & Compliance",
    # End User Computing
    "WorkSpaces": "End User Computing",
    "AppStream": "End User Computing",
    # Analytics
    "Kinesis": "Analytics",
    "EMR": "Analytics",
    "Glue": "Analytics",
    "Athena": "Analytics",
    "QuickSight": "Analytics",
    # Application Integration
    "SQS": "Application Integration",
    "SNS": "Application Integration",
    "EventBridge": "Application Integration",
    "Step-Functions": "Application Integration",
    "MQ": "Application Integration",
    # v1.1.29: Developer Tools → Other per user request
    "CodeCommit": "Other",
    "CodeBuild": "Other",
    "CodePipeline": "Other",
    "CodeDeploy": "Other",
    "X-Ray": "Other",
    # Machine Learning
    "SageMaker": "Machine Learning",
    "Rekognition": "Machine Learning",
    "Comprehend": "Machine Learning",
    "Translate": "Machine Learning",
    # v1.1.29: Business Applications → Other per user request
    "Connect": "Other",
    "Chime": "Other",
    "SES": "Other",
    # v1.1.29: Cloud Financial Management → Other per user request
    "Cost-Explorer": "Other",
    "Budgets": "Other",
    "Savings-Plans": "Other",
}


def categorize_aws_service(service_name: str) -> str:
    """
    Categorize AWS service using AWS Official Taxonomy.

    Uses 3-tier matching for robustness:
    1. Exact/prefix match against full AWS service names (most reliable)
    2. Abbreviation lookup via service_mapping.py (fallback)
    3. Default to 'Other' for unknown services

    Args:
        service_name: Full AWS service name as returned by Cost Explorer API
                     (e.g., "Amazon Simple Storage Service", "AmazonCloudWatch")

    Returns:
        AWS category name (e.g., "Storage", "Management & Governance", "Other")

    Examples:
        >>> categorize_aws_service("Amazon Simple Storage Service")
        'Storage'
        >>> categorize_aws_service("AmazonCloudWatch")
        'Management & Governance'
        >>> categorize_aws_service("Amazon Relational Database Service")
        'Databases'
        >>> categorize_aws_service("Unknown Service XYZ")
        'Other'
    """
    # Skip Tax - handled separately in header
    if service_name == "Tax":
        return "Tax"

    # Tier 1: Full service name match (most reliable)
    for category, services in AWS_SERVICE_CATEGORIES.items():
        for svc in services:
            # Check if service name starts with or contains the category service
            if service_name.startswith(svc) or svc in service_name:
                return category

    # Tier 2: Abbreviation lookup (fallback for edge cases)
    try:
        display_name = get_service_display_name(service_name)
        if display_name in ABBREV_TO_CATEGORY:
            return ABBREV_TO_CATEGORY[display_name]
    except Exception:
        pass  # Fallback to default if service_mapping fails

    # Tier 3: Default for unknown services
    return "Other"


def get_category_order() -> list:
    """
    Get ordered list of categories for consistent display.

    Returns categories in order of typical cost significance for
    enterprise workloads.

    Returns:
        Ordered list of category names
    """
    # v1.1.29: Removed Developer Tools, Business Applications, Cloud Financial Management (merged into Other)
    return [
        "Compute",
        "Databases",
        "Storage",
        "Management & Governance",
        "End User Computing",
        "Networking & Content Delivery",
        "Security, Identity & Compliance",
        "Analytics",
        "Application Integration",
        "Machine Learning",
        "Containers",
        "Migration & Transfer",
        "Internet of Things",
        "Media Services",
        "Other",
    ]


def categorize_services_dict(
    services: Dict[str, float],
) -> Dict[str, Dict[str, float]]:
    """
    Categorize a dictionary of services into AWS categories.

    Args:
        services: Dictionary mapping service names to costs

    Returns:
        Nested dictionary: category -> {service_name: cost}

    Example:
        >>> services = {"Amazon Simple Storage Service": 100.0, "AmazonCloudWatch": 50.0}
        >>> categorized = categorize_services_dict(services)
        >>> categorized["Storage"]
        {"Amazon Simple Storage Service": 100.0}
    """
    categorized: Dict[str, Dict[str, float]] = {}

    for service_name, cost in services.items():
        category = categorize_aws_service(service_name)
        if category not in categorized:
            categorized[category] = {}
        categorized[category][service_name] = cost

    return categorized


def get_category_totals(
    categorized_services: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """
    Calculate total cost per category.

    Args:
        categorized_services: Output from categorize_services_dict()

    Returns:
        Dictionary mapping category names to total costs
    """
    return {category: sum(services.values()) for category, services in categorized_services.items()}


# Export for other modules
__all__ = [
    "AWS_SERVICE_CATEGORIES",
    "ABBREV_TO_CATEGORY",
    "categorize_aws_service",
    "get_category_order",
    "categorize_services_dict",
    "get_category_totals",
]
