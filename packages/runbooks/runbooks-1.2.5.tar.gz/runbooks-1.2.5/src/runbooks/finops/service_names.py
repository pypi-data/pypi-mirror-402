"""AWS Service Name Mapping - Simplified names matching AWS Console exports.

This module provides bidirectional mapping between AWS Cost Explorer API service names
and simplified names matching AWS Console CSV exports for better readability.

Usage:
    from runbooks.finops.service_names import simplify_service_name, get_api_name

    # Simplify API name for display
    display_name = simplify_service_name("Amazon Simple Storage Service")  # Returns "S3"

    # Get API name from simplified name
    api_name = get_api_name("S3")  # Returns "Amazon Simple Storage Service"
"""

from typing import Dict, Optional


# Service name mapping: API Name -> Simplified Name (matching AWS Console CSV exports)
SERVICE_NAME_MAP: Dict[str, str] = {
    # Storage
    "Amazon Simple Storage Service": "S3",
    "Amazon Elastic Block Store": "EBS",
    "Amazon Elastic File System": "EFS",
    "Amazon FSx": "FSx",
    "Amazon Glacier": "Glacier",
    "AWS Storage Gateway": "Storage Gateway",
    "AWS Backup": "Backup",
    # Compute - EC2
    "Amazon Elastic Compute Cloud - Compute": "EC2-Instances",
    "EC2 - Other": "EC2-Other",
    "Amazon EC2 Container Registry (ECR)": "ECR",
    "EC2 Container Registry (ECR)": "ECR",
    # Compute - Serverless/Containers
    "AWS Lambda": "Lambda",
    "Amazon Elastic Container Service": "ECS",
    "Elastic Container Service": "ECS",
    "Amazon Elastic Container Service for Kubernetes": "EKS",
    "Elastic Container Service for Kubernetes": "EKS",
    "AWS Fargate": "Fargate",
    "Amazon Lightsail": "Lightsail",
    "Amazon AppStream": "AppStream",
    "Amazon WorkSpaces": "WorkSpaces",
    # Database
    "Amazon Relational Database Service": "RDS",
    "Relational Database Service": "RDS",
    "Amazon DynamoDB": "DynamoDB",
    "Amazon ElastiCache": "ElastiCache",
    "Amazon Redshift": "Redshift",
    "Amazon DocumentDB (with MongoDB compatibility)": "DocumentDB",
    "Amazon Neptune": "Neptune",
    "Amazon MemoryDB": "MemoryDB",
    "Amazon Timestream": "Timestream",
    "Amazon Keyspaces (for Apache Cassandra)": "Keyspaces",
    "Amazon QLDB": "QLDB",
    "AWS Database Migration Service": "DMS",
    "DMS": "DMS",
    # Network
    "Amazon Virtual Private Cloud": "VPC",
    "Elastic Load Balancing": "ELB",
    "Amazon Route 53": "Route53",
    "Route 53": "Route53",
    "Amazon CloudFront": "CloudFront",
    "Amazon API Gateway": "API Gateway",
    "API Gateway": "API Gateway",
    "AWS Direct Connect": "Direct Connect",
    "AWS Global Accelerator": "Global Accelerator",
    "AWS Transit Gateway": "Transit Gateway",
    "Amazon VPC Lattice": "VPC Lattice",
    # Analytics
    "Amazon Athena": "Athena",
    "Amazon EMR": "EMR",
    "Amazon Kinesis": "Kinesis",
    "Amazon Kinesis Firehose": "Kinesis Firehose",
    "Kinesis Firehose": "Kinesis Firehose",
    "Amazon Kinesis Video Streams": "Kinesis Video",
    "Kinesis Video Streams": "Kinesis Video",
    "Amazon QuickSight": "QuickSight",
    "AWS Glue": "Glue",
    "Amazon OpenSearch Service": "OpenSearch",
    "Amazon Managed Streaming for Apache Kafka": "MSK",
    "AWS Data Pipeline": "Data Pipeline",
    "Data Pipeline": "Data Pipeline",
    # AI/ML
    "Amazon SageMaker": "SageMaker",
    "Amazon Rekognition": "Rekognition",
    "Amazon Comprehend": "Comprehend",
    "Amazon Polly": "Polly",
    "Amazon Transcribe": "Transcribe",
    "Amazon Translate": "Translate",
    "Amazon Lex": "Lex",
    "Amazon Textract": "Textract",
    "Amazon Personalize": "Personalize",
    "Amazon Forecast": "Forecast",
    "Amazon Bedrock": "Bedrock",
    "Claude 3.5 Sonnet v2 ( Bedrock Edition)": "Claude (Bedrock)",
    # Management & Monitoring
    "AmazonCloudWatch": "CloudWatch",
    "Amazon CloudWatch": "CloudWatch",
    "CloudWatch": "CloudWatch",
    "AWS CloudTrail": "CloudTrail",
    "CloudTrail": "CloudTrail",
    "AWS Config": "Config",
    "Config": "Config",
    "AWS Systems Manager": "Systems Manager",
    "Systems Manager": "Systems Manager",
    "AWS Organizations": "Organizations",
    "AWS Service Catalog": "Service Catalog",
    "Service Catalog": "Service Catalog",
    "AWS Trusted Advisor": "Trusted Advisor",
    "AWS CloudFormation": "CloudFormation",
    "CloudFormation": "CloudFormation",
    "AWS Cost Explorer": "Cost Explorer",
    "Cost Explorer": "Cost Explorer",
    "AWS CloudShell": "CloudShell",
    "CloudShell": "CloudShell",
    "AWS X-Ray": "X-Ray",
    "X-Ray": "X-Ray",
    "Amazon CloudWatch Events": "CloudWatch Events",
    "CloudWatch Events": "CloudWatch Events",
    # Security & Identity
    "AWS Key Management Service": "KMS",
    "Key Management Service": "KMS",
    "AWS Secrets Manager": "Secrets Manager",
    "Secrets Manager": "Secrets Manager",
    "AWS WAF": "WAF",
    "WAF": "WAF",
    "AWS Shield": "Shield",
    "Amazon GuardDuty": "GuardDuty",
    "GuardDuty": "GuardDuty",
    "AWS Security Hub": "Security Hub",
    "Security Hub": "Security Hub",
    "Amazon Inspector": "Inspector",
    "AWS Firewall Manager": "Firewall Manager",
    "Firewall Manager": "Firewall Manager",
    "AWS Identity and Access Management": "IAM",
    "Identity and Access Management Access Analyzer": "IAM Access Analyzer",
    "Amazon Cognito": "Cognito",
    "Cognito": "Cognito",
    "AWS Directory Service": "Directory Service",
    "Directory Service": "Directory Service",
    "Amazon Macie": "Macie",
    "AWS Certificate Manager": "ACM",
    "Certificate Manager": "ACM",
    "AWS Payment Cryptography": "Payment Cryptography",
    "Payment Cryptography": "Payment Cryptography",
    # Application Integration
    "Amazon Simple Queue Service": "SQS",
    "SQS": "SQS",
    "Amazon Simple Notification Service": "SNS",
    "SNS": "SNS",
    "AWS Step Functions": "Step Functions",
    "Step Functions": "Step Functions",
    "Amazon EventBridge": "EventBridge",
    "Amazon MQ": "MQ",
    "MQ": "MQ",
    "AWS AppSync": "AppSync",
    "AppSync": "AppSync",
    # Developer Tools
    "AWS CodePipeline": "CodePipeline",
    "CodePipeline": "CodePipeline",
    "AWS CodeBuild": "CodeBuild",
    "CodeBuild": "CodeBuild",
    "AWS CodeDeploy": "CodeDeploy",
    "AWS CodeCommit": "CodeCommit",
    "AWS CodeArtifact": "CodeArtifact",
    "AWS Cloud9": "Cloud9",
    "Amazon CodeGuru": "CodeGuru",
    # Business Applications
    "Amazon Connect": "Connect",
    "Connect": "Connect",
    "Amazon Connect Customer Profiles": "Connect Profiles",
    "Connect Customer Profiles": "Connect Profiles",
    "Contact Center Telecommunications (service sold by AMCS, LLC)": "Connect Telecom",
    "Contact Lens for  Connect": "Contact Lens",
    "Amazon Chime": "Chime",
    "Amazon WorkMail": "WorkMail",
    "WorkMail": "WorkMail",
    "Amazon WorkDocs": "WorkDocs",
    "Amazon Pinpoint": "Pinpoint",
    "Amazon Simple Email Service": "SES",
    "SES": "SES",
    "AWS End User Messaging": "End User Messaging",
    "End User Messaging": "End User Messaging",
    # Migration & Transfer
    "AWS Transfer Family": "Transfer Family",
    "Transfer Family": "Transfer Family",
    "AWS Migration Hub": "Migration Hub",
    "Migration Hub Refactor Spaces": "Refactor Spaces",
    "AWS DataSync": "DataSync",
    "AWS Snow Family": "Snow Family",
    "AWS Application Migration Service": "MGN",
    # IoT
    "AWS IoT": "IoT",
    "IoT": "IoT",
    "AWS IoT Core": "IoT Core",
    "AWS IoT Analytics": "IoT Analytics",
    "AWS IoT Device Management": "IoT Device Mgmt",
    "AWS IoT Events": "IoT Events",
    "AWS IoT Greengrass": "IoT Greengrass",
    # Media Services
    "Amazon Elastic Transcoder": "Elastic Transcoder",
    "AWS Elemental MediaConvert": "MediaConvert",
    "AWS Elemental MediaLive": "MediaLive",
    "AWS Elemental MediaPackage": "MediaPackage",
    "Amazon Interactive Video Service": "IVS",
    # Healthcare & Life Sciences
    "Amazon HealthLake": "HealthLake",
    "AWS HealthImaging": "HealthImaging",
    "HealthImaging": "HealthImaging",
    # Other Services
    "Amazon Location Service": "Location",
    "Location Service": "Location",
    "AWS Amplify": "Amplify",
    "Amplify": "Amplify",
    "Amazon Cloud Map": "Cloud Map",
    "Cloud Map": "Cloud Map",
    "AWS Ground Station": "Ground Station",
    "Amazon SimpleDB": "SimpleDB",
    "SimpleDB": "SimpleDB",
    "Amazon Registrar": "Route53 Domains",
    "Registrar": "Route53 Domains",
    # Support Plans
    "AWS Support (Enterprise)": "Enterprise Support",
    "Support (Enterprise)": "Enterprise Support",
    "AWS Support (Business)": "Business Support",
    "Support (Business)": "Business Support",
    "AWS Support (Developer)": "Developer Support",
    # Savings Plans
    "Savings Plans for AWS Compute usage": "Savings Plans",
    "Savings Plans for  Compute usage": "Savings Plans",
    # Tax & Refunds
    "Tax": "Tax",
    "Refund": "Refund",
}

# Reverse mapping: Simplified Name -> API Name (for lookup)
_REVERSE_MAP: Dict[str, str] = {v: k for k, v in SERVICE_NAME_MAP.items()}


def simplify_service_name(api_name: str) -> str:
    """Convert AWS Cost Explorer API service name to simplified display name.

    Args:
        api_name: Full AWS service name from Cost Explorer API

    Returns:
        Simplified name matching AWS Console CSV export format.
        Returns original name if no mapping exists.

    Example:
        >>> simplify_service_name("Amazon Simple Storage Service")
        'S3'
        >>> simplify_service_name("UnknownService")
        'UnknownService'
    """
    return SERVICE_NAME_MAP.get(api_name, api_name)


def get_api_name(simple_name: str) -> str:
    """Get AWS Cost Explorer API service name from simplified name.

    Args:
        simple_name: Simplified service name (e.g., 'S3', 'EC2-Instances')

    Returns:
        Full AWS API service name for Cost Explorer queries.
        Returns original name if no mapping exists.

    Example:
        >>> get_api_name("S3")
        'Amazon Simple Storage Service'
        >>> get_api_name("UnknownService")
        'UnknownService'
    """
    return _REVERSE_MAP.get(simple_name, simple_name)


def get_all_mappings() -> Dict[str, str]:
    """Get complete service name mapping dictionary.

    Returns:
        Dictionary mapping API names to simplified names.
    """
    return SERVICE_NAME_MAP.copy()


def format_service_name(api_name: str, use_full_names: bool = False) -> str:
    """Format service name based on display preference.

    Args:
        api_name: Full AWS service name from Cost Explorer API
        use_full_names: If True, return original API name; if False, return simplified name

    Returns:
        Formatted service name based on display preference.

    Example:
        >>> format_service_name("Amazon Simple Storage Service", use_full_names=False)
        'S3'
        >>> format_service_name("Amazon Simple Storage Service", use_full_names=True)
        'Amazon Simple Storage Service'
    """
    if use_full_names:
        return api_name
    return simplify_service_name(api_name)
