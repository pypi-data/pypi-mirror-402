"""
VPC Testing Configuration and Fixtures

Provides specialized fixtures for VPC networking component testing
with comprehensive AWS service mocking and test data.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from moto import mock_aws
from rich.console import Console

# Add src to Python path
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from runbooks.vpc.config import AWSCostModel, OptimizationThresholds, VPCNetworkingConfig
from runbooks.vpc.cost_engine import NetworkingCostEngine
from runbooks.vpc.networking_wrapper import VPCNetworkingWrapper


@pytest.fixture(scope="session")
def aws_credentials():
    """Mock AWS credentials for VPC testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-southeast-2"


@pytest.fixture
def vpc_test_profiles():
    """Test profile configurations for VPC testing."""
    return {
        "billing_profile": "test-billing-profile",
        "management_profile": "test-management-profile",
        "centralised_ops_profile": "test-ops-profile",
        "single_account_profile": "test-single-account-profile",
    }


@pytest.fixture
def vpc_test_config():
    """Standard VPC test configuration."""
    return VPCNetworkingConfig(
        default_region="ap-southeast-2",
        billing_profile="test-billing-profile",
        default_analysis_days=30,
        default_output_format="json",
        enable_cost_approval_workflow=True,
        enable_mcp_validation=False,
    )


@pytest.fixture
def mock_console():
    """Mock Rich Console for testing output."""
    console = Mock(spec=Console)
    console.print = Mock()

    # Mock status context manager
    mock_status = Mock()
    mock_status.__enter__ = Mock(return_value=mock_status)
    mock_status.__exit__ = Mock(return_value=None)
    console.status = Mock(return_value=mock_status)

    return console


@pytest.fixture
def sample_nat_gateways():
    """Sample NAT Gateway data for testing."""
    return [
        {
            "NatGatewayId": "nat-0123456789abcdef0",
            "State": "available",
            "VpcId": "vpc-0123456789abcdef0",
            "SubnetId": "subnet-0123456789abcdef0",
            "CreationTime": datetime.now(),
            "NatGatewayAddresses": [
                {
                    "AllocationId": "eipalloc-0123456789abcdef0",
                    "NetworkInterfaceId": "eni-0123456789abcdef0",
                    "PrivateIp": "10.0.1.5",
                    "PublicIp": "203.0.113.5",
                }
            ],
        },
        {
            "NatGatewayId": "nat-0123456789abcdef1",
            "State": "available",
            "VpcId": "vpc-0123456789abcdef1",
            "SubnetId": "subnet-0123456789abcdef1",
            "CreationTime": datetime.now(),
            "NatGatewayAddresses": [
                {
                    "AllocationId": "eipalloc-0123456789abcdef1",
                    "NetworkInterfaceId": "eni-0123456789abcdef1",
                    "PrivateIp": "10.0.2.5",
                    "PublicIp": "203.0.113.6",
                }
            ],
        },
    ]


@pytest.fixture
def sample_vpc_endpoints():
    """Sample VPC Endpoint data for testing."""
    return [
        {
            "VpcEndpointId": "vpce-0123456789abcdef0",
            "VpcEndpointType": "Interface",
            "VpcId": "vpc-0123456789abcdef0",
            "ServiceName": "com.amazonaws.ap-southeast-2.s3",
            "State": "available",
            "CreationTimestamp": datetime.now(),
            "SubnetIds": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"],
        },
        {
            "VpcEndpointId": "vpce-0123456789abcdef1",
            "VpcEndpointType": "Gateway",
            "VpcId": "vpc-0123456789abcdef1",
            "ServiceName": "com.amazonaws.ap-southeast-2.dynamodb",
            "State": "available",
            "CreationTimestamp": datetime.now(),
            "SubnetIds": [],
        },
    ]


@pytest.fixture
def sample_cloudwatch_metrics():
    """Sample CloudWatch metrics data for NAT Gateway testing."""
    return {
        "ActiveConnectionCount": [
            {"Timestamp": datetime.now() - timedelta(days=1), "Average": 150.0, "Maximum": 200.0, "Unit": "Count"},
            {"Timestamp": datetime.now() - timedelta(days=2), "Average": 120.0, "Maximum": 180.0, "Unit": "Count"},
        ],
        "BytesOutToDestination": [
            {
                "Timestamp": datetime.now() - timedelta(days=1),
                "Sum": 5368709120.0,  # 5 GB
                "Unit": "Bytes",
            },
            {
                "Timestamp": datetime.now() - timedelta(days=2),
                "Sum": 3221225472.0,  # 3 GB
                "Unit": "Bytes",
            },
        ],
    }


@pytest.fixture
def mock_aws_vpc_comprehensive(aws_credentials, sample_nat_gateways, sample_vpc_endpoints):
    """Comprehensive AWS VPC mock with all networking components."""
    with mock_aws():
        # Create clients
        ec2_client = boto3.client("ec2", region_name="ap-southeast-2")
        cloudwatch_client = boto3.client("cloudwatch", region_name="ap-southeast-2")

        # Create VPC infrastructure
        vpc_response = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc_response["Vpc"]["VpcId"]

        # Create subnets
        subnet1 = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a")
        subnet2 = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1b")

        # Create Internet Gateway
        igw_response = ec2_client.create_internet_gateway()
        igw_id = igw_response["InternetGateway"]["InternetGatewayId"]
        ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

        # Create Elastic IPs for NAT Gateways
        eip1 = ec2_client.allocate_address(Domain="vpc")
        eip2 = ec2_client.allocate_address(Domain="vpc")

        # Create NAT Gateways
        nat_gw1 = ec2_client.create_nat_gateway(
            SubnetId=subnet1["Subnet"]["SubnetId"], AllocationId=eip1["AllocationId"]
        )
        nat_gw2 = ec2_client.create_nat_gateway(
            SubnetId=subnet2["Subnet"]["SubnetId"], AllocationId=eip2["AllocationId"]
        )

        # Create VPC Endpoints
        vpc_endpoint_s3 = ec2_client.create_vpc_endpoint(
            VpcId=vpc_id,
            ServiceName="com.amazonaws.ap-southeast-2.s3",
            VpcEndpointType="Interface",
            SubnetIds=[subnet1["Subnet"]["SubnetId"], subnet2["Subnet"]["SubnetId"]],
        )

        vpc_endpoint_dynamodb = ec2_client.create_vpc_endpoint(
            VpcId=vpc_id, ServiceName="com.amazonaws.ap-southeast-2.dynamodb", VpcEndpointType="Gateway"
        )

        test_infrastructure = {
            "vpc_id": vpc_id,
            "subnet_ids": [subnet1["Subnet"]["SubnetId"], subnet2["Subnet"]["SubnetId"]],
            "igw_id": igw_id,
            "nat_gateway_ids": [nat_gw1["NatGateway"]["NatGatewayId"], nat_gw2["NatGateway"]["NatGatewayId"]],
            "vpc_endpoint_ids": [
                vpc_endpoint_s3["VpcEndpoint"]["VpcEndpointId"],
                vpc_endpoint_dynamodb["VpcEndpoint"]["VpcEndpointId"],
            ],
            "allocation_ids": [eip1["AllocationId"], eip2["AllocationId"]],
        }

        yield {"ec2_client": ec2_client, "cloudwatch_client": cloudwatch_client, "infrastructure": test_infrastructure}


@pytest.fixture
def vpc_networking_wrapper(mock_console, vpc_test_config):
    """VPC Networking Wrapper instance for testing."""
    with patch("runbooks.vpc.networking_wrapper.boto3.Session") as mock_session:
        # Configure mock session
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        wrapper = VPCNetworkingWrapper(
            profile="test-profile",
            region="ap-southeast-2",
            billing_profile="test-billing-profile",
            output_format="json",
            console=mock_console,
        )

        # Set mock session
        wrapper.session = mock_session_instance

        yield wrapper


@pytest.fixture
def networking_cost_engine(vpc_test_config):
    """Networking Cost Engine instance for testing."""
    with patch("runbooks.vpc.cost_engine.boto3.Session") as mock_session:
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance

        engine = NetworkingCostEngine(session=mock_session_instance, config=vpc_test_config)

        yield engine


@pytest.fixture
def performance_benchmarks():
    """Performance benchmark thresholds for testing."""
    return {
        "nat_gateway_analysis_max_time": 5.0,  # seconds
        "vpc_endpoint_analysis_max_time": 3.0,  # seconds
        "cost_calculation_max_time": 1.0,  # seconds
        "cli_response_max_time": 2.0,  # seconds
        "heatmap_generation_max_time": 10.0,  # seconds
    }


@pytest.fixture
def mock_cost_explorer_responses():
    """Mock Cost Explorer API responses for testing."""
    # Dynamic test period calculation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    return {
        "vpc_costs": {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
                    "Total": {"BlendedCost": {"Amount": "145.67", "Unit": "USD"}},
                }
            ]
        },
        "nat_gateway_costs": {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
                    "Total": {"BlendedCost": {"Amount": "89.32", "Unit": "USD"}},
                }
            ]
        },
    }


@pytest.fixture
def temp_output_directory():
    """Temporary directory for test output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


# Utility functions for tests


@pytest.fixture
def assert_performance_benchmark():
    """Utility function to assert performance benchmarks."""

    def _assert_performance(execution_time: float, benchmark_name: str, benchmarks: dict):
        """Assert that execution time meets performance benchmark."""
        if benchmark_name in benchmarks:
            max_time = benchmarks[benchmark_name]
            assert execution_time < max_time, (
                f"Performance benchmark failed: {execution_time:.2f}s > {max_time}s for {benchmark_name}"
            )
        return True

    return _assert_performance


@pytest.fixture
def validate_vpc_structure():
    """Utility function to validate VPC analysis result structure."""

    def _validate_structure(result: Dict[str, Any], expected_keys: List[str]):
        """Validate that result contains all expected keys."""
        for key in expected_keys:
            assert key in result, f"Missing required key: {key}"

        # Validate common structure elements
        assert "timestamp" in result
        assert "profile" in result
        assert "region" in result

        return True

    return _validate_structure


@pytest.fixture
def security_test_validator():
    """Utility for security validation testing."""

    def _validate_security(func_call_result: Any, sensitive_patterns: List[str] = None):
        """Validate that no sensitive information is exposed."""
        if sensitive_patterns is None:
            sensitive_patterns = ["AKIA", "SECRET", "TOKEN", "PASSWORD"]

        result_str = str(func_call_result)

        for pattern in sensitive_patterns:
            assert pattern not in result_str.upper(), f"Sensitive pattern '{pattern}' found in result"

        return True

    return _validate_security


# ========================================
# VPC Cleanup Framework Fixtures
# ========================================
# Added to support config-driven VPC cleanup testing


@pytest.fixture
def cleanup_valid_config():
    """Load AWS-25 reference config for VPC cleanup testing"""
    import yaml

    config_path = Path(__file__).parent.parent.parent.parent.parent / "examples/vpc-cleanup/aws25-campaign-config.yaml"
    if not config_path.exists():
        # Fallback to minimal valid config if reference not available
        return {
            "campaign_metadata": {
                "campaign_id": "TEST-01",
                "campaign_name": "Test Campaign",
                "execution_date": "2025-10-02",
                "aws_billing_profile": "test-profile",
                "description": "Test campaign description",
            },
            "deleted_vpcs": [
                {
                    "vpc_id": "vpc-test123456789abcd",
                    "account_id": "123456789012",
                    "region": "ap-southeast-2",
                    "deletion_date": "2025-09-10",
                    "deletion_principal": "test.user@example.com",
                    "pre_deletion_baseline_months": 3,
                }
            ],
            "cost_explorer_config": {
                "metrics": ["UnblendedCost"],
                "group_by_dimensions": ["SERVICE", "REGION"],
                "pre_deletion_baseline": {"granularity_monthly": "MONTHLY", "months_before_deletion": 3},
                "pre_deletion_detailed": {"granularity_daily": "DAILY", "days_before_deletion": 10},
                "post_deletion_validation": {"granularity_daily": "DAILY", "days_after_deletion": 30},
            },
            "attribution_rules": {
                "vpc_specific_services": {
                    "confidence_level": "HIGH (95%)",
                    "attribution_percentage": 100,
                    "service_patterns": ["Amazon Virtual Private Cloud"],
                },
                "vpc_related_services": {
                    "confidence_level": "MEDIUM (85%)",
                    "attribution_percentage": 70,
                    "service_patterns": ["Amazon Elastic Compute Cloud - Compute"],
                },
                "other_services": {
                    "confidence_level": "LOW (<85%)",
                    "attribution_percentage": 30,
                    "service_patterns": ["*"],
                },
            },
            "output_config": {
                "csv_output_file": "test_output.csv",
                "csv_columns": ["VPC_ID", "Account_ID", "Deletion_Date", "Monthly_Savings_Realized"],
                "json_results_file": "test_results.json",
                "execution_summary_file": "test_summary.md",
            },
        }

    with open(config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture
def cleanup_sample_vpc_deletion():
    """Sample VPC deletion for testing"""
    return {
        "vpc_id": "vpc-test123456789abcd",
        "account_id": "123456789012",
        "region": "ap-southeast-2",
        "deletion_date": "2025-09-10",
        "deletion_principal": "test.user@example.com",
        "pre_deletion_baseline_months": 3,
    }


@pytest.fixture
def cleanup_sample_vpc_deletions():
    """Sample list of VPC deletions for multi-VPC testing"""
    return [
        {
            "vpc_id": "vpc-test111111111aaaa",
            "account_id": "111111111111",
            "region": "ap-southeast-2",
            "deletion_date": "2025-09-10",
            "deletion_principal": "user1@example.com",
            "pre_deletion_baseline_months": 3,
        },
        {
            "vpc_id": "vpc-test222222222bbbb",
            "account_id": "222222222222",
            "region": "ap-southeast-6",
            "deletion_date": "2025-08-15",
            "deletion_principal": "user2@example.com",
            "pre_deletion_baseline_months": 3,
        },
        {
            "vpc_id": "vpc-test333333333cccc",
            "account_id": "111111111111",
            "region": "eu-west-1",
            "deletion_date": "2025-09-01",
            "deletion_principal": "user3@example.com",
            "pre_deletion_baseline_months": 3,
        },
    ]


@pytest.fixture
def cleanup_mock_cost_explorer():
    """Mock boto3 Cost Explorer client for cleanup testing"""
    mock_ce_client = MagicMock()

    def get_cost_side_effect(*args, **kwargs):
        # Return different responses based on time period
        time_period = kwargs.get("TimePeriod", {})
        start_date = time_period.get("Start", "")

        if start_date.startswith("2025-09"):
            # Post-deletion period
            return {
                "ResultsByTime": [
                    {
                        "TimePeriod": time_period,
                        "Groups": [
                            {
                                "Keys": ["Amazon Elastic Compute Cloud - Compute", "ap-southeast-2"],
                                "Metrics": {"UnblendedCost": {"Amount": "15.00", "Unit": "USD"}},
                            }
                        ],
                    }
                ]
            }
        else:
            # Pre-deletion period
            return {
                "ResultsByTime": [
                    {
                        "TimePeriod": time_period,
                        "Groups": [
                            {
                                "Keys": ["Amazon Virtual Private Cloud", "ap-southeast-2"],
                                "Metrics": {"UnblendedCost": {"Amount": "100.00", "Unit": "USD"}},
                            },
                            {
                                "Keys": ["Amazon Elastic Compute Cloud - Compute", "ap-southeast-2"],
                                "Metrics": {"UnblendedCost": {"Amount": "500.00", "Unit": "USD"}},
                            },
                        ],
                    }
                ]
            }

    mock_ce_client.get_cost_and_usage.side_effect = get_cost_side_effect
    return mock_ce_client


@pytest.fixture
def cleanup_temp_config_file():
    """Create temporary cleanup config file for testing"""
    import yaml

    minimal_config = {
        "campaign_metadata": {
            "campaign_id": "TEST-01",
            "campaign_name": "Test Campaign",
            "execution_date": "2025-10-02",
            "aws_billing_profile": "test-profile",
            "description": "Test campaign description",
        },
        "deleted_vpcs": [
            {
                "vpc_id": "vpc-test123456789abcd",
                "account_id": "123456789012",
                "region": "ap-southeast-2",
                "deletion_date": "2025-09-10",
                "deletion_principal": "test.user@example.com",
                "pre_deletion_baseline_months": 3,
            }
        ],
        "cost_explorer_config": {
            "metrics": ["UnblendedCost"],
            "group_by_dimensions": ["SERVICE", "REGION"],
            "pre_deletion_baseline": {"granularity_monthly": "MONTHLY", "months_before_deletion": 3},
            "pre_deletion_detailed": {"granularity_daily": "DAILY", "days_before_deletion": 10},
            "post_deletion_validation": {"granularity_daily": "DAILY", "days_after_deletion": 30},
        },
        "attribution_rules": {
            "vpc_specific_services": {
                "confidence_level": "HIGH (95%)",
                "attribution_percentage": 100,
                "service_patterns": ["Amazon Virtual Private Cloud"],
            },
            "vpc_related_services": {
                "confidence_level": "MEDIUM (85%)",
                "attribution_percentage": 70,
                "service_patterns": ["Amazon Elastic Compute Cloud - Compute"],
            },
            "other_services": {
                "confidence_level": "LOW (<85%)",
                "attribution_percentage": 30,
                "service_patterns": ["*"],
            },
        },
        "output_config": {
            "csv_output_file": "test_output.csv",
            "csv_columns": ["VPC_ID", "Account_ID", "Deletion_Date", "Monthly_Savings_Realized"],
            "json_results_file": "test_results.json",
            "execution_summary_file": "test_summary.md",
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(minimal_config, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def cleanup_multi_lz_config():
    """Config for multi-Landing Zone testing with different accounts and regions"""
    return {
        "campaign_metadata": {
            "campaign_id": "MULTI-LZ-01",
            "campaign_name": "Multi-LZ Test Campaign",
            "execution_date": "2025-10-02",
            "aws_billing_profile": "multi-lz-profile",
            "description": "Testing multiple Landing Zones",
        },
        "deleted_vpcs": [
            {
                "vpc_id": "vpc-lz1111111111aaaa",
                "account_id": "111111111111",
                "region": "ap-southeast-2",
                "deletion_date": "2025-09-10",
                "deletion_principal": "lz1.user@example.com",
                "pre_deletion_baseline_months": 3,
            },
            {
                "vpc_id": "vpc-lz2222222222bbbb",
                "account_id": "222222222222",
                "region": "eu-west-1",
                "deletion_date": "2025-08-20",
                "deletion_principal": "lz2.user@example.com",
                "pre_deletion_baseline_months": 3,
            },
            {
                "vpc_id": "vpc-lz3333333333cccc",
                "account_id": "333333333333",
                "region": "ap-southeast-2",
                "deletion_date": "2025-09-05",
                "deletion_principal": "lz3.user@example.com",
                "pre_deletion_baseline_months": 3,
            },
        ],
        "cost_explorer_config": {
            "metrics": ["UnblendedCost"],
            "group_by_dimensions": ["SERVICE", "REGION"],
            "pre_deletion_baseline": {"granularity_monthly": "MONTHLY", "months_before_deletion": 3},
            "pre_deletion_detailed": {"granularity_daily": "DAILY", "days_before_deletion": 10},
            "post_deletion_validation": {"granularity_daily": "DAILY", "days_after_deletion": 30},
        },
        "attribution_rules": {
            "vpc_specific_services": {
                "confidence_level": "HIGH (95%)",
                "attribution_percentage": 100,
                "service_patterns": ["Amazon Virtual Private Cloud", "AWS PrivateLink"],
            },
            "vpc_related_services": {
                "confidence_level": "MEDIUM (85%)",
                "attribution_percentage": 70,
                "service_patterns": ["Amazon Elastic Compute Cloud - Compute", "Elastic Load Balancing"],
            },
            "other_services": {
                "confidence_level": "LOW (<85%)",
                "attribution_percentage": 30,
                "service_patterns": ["*"],
            },
        },
        "output_config": {
            "csv_output_file": "multi_lz_output.csv",
            "csv_columns": [
                "VPC_ID",
                "Account_ID",
                "Deletion_Date",
                "Pre_Deletion_Monthly_Avg",
                "Post_Deletion_Monthly_Avg",
                "Monthly_Savings_Realized",
                "Annual_Savings_Realized",
                "Data_Quality",
                "Confidence_Level",
                "Notes",
                "Service_Analysis",
            ],
            "json_results_file": "multi_lz_results.json",
            "execution_summary_file": "multi_lz_summary.md",
        },
    }
