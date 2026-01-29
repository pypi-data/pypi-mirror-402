#!/usr/bin/env python3
"""
VPC Test Data Loader - AWS-25 Integration Framework
=====================================================

Enterprise test data integration for VPC cleanup validation using comprehensive
production test data with 27 VPCs across 10 regions.

Author: python-runbooks-engineer [1]
Strategic Coordination: enterprise-product-owner [0]
Epic: AWS-25 VPC Infrastructure Cleanup
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from runbooks.common.rich_utils import console, print_success, print_warning, print_error

logger = logging.getLogger(__name__)


class VPCTestDataLoader:
    """
    Enterprise VPC test data loader for AWS-25 validation framework.

    Integrates comprehensive test data with 27 VPCs across 10 regions for
    validation against multi-region discovery implementation.
    """

    def __init__(self, test_data_path: Optional[str] = None):
        """
        Initialize test data loader with production test dataset.

        Args:
            test_data_path: Path to test data file (optional, uses default if None)
        """
        self.test_data_path = test_data_path or self._get_default_test_data_path()
        self.test_data = None
        self._load_test_data()

    def _get_default_test_data_path(self) -> str:
        """Get default path to VPC test data file."""
        # Navigate to .claude/config/environment-data/vpc-test-data-production.yaml
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent  # Go up to project root
        test_data_path = project_root / ".claude" / "config" / "environment-data" / "vpc-test-data-production.yaml"
        return str(test_data_path)

    def _load_test_data(self):
        """Load VPC test data from YAML configuration."""
        try:
            with open(self.test_data_path, "r") as f:
                self.test_data = yaml.safe_load(f)

            print_success(f"✅ Test data loaded: {self.test_data_path}")

            # Validate test data structure
            if not self._validate_test_data_structure():
                print_error("❌ Test data validation failed")
                self.test_data = None
                return

            # Log test data summary
            active_count = len(self.test_data["vpc_test_data"]["active_vpcs"])
            deleted_count = len(self.test_data["vpc_test_data"]["deleted_vpcs"])
            total_savings = self.test_data["business_metrics"]["annual_savings"]

            print_success(f"📊 Test Data Summary: {active_count} active VPCs, {deleted_count} deleted VPCs")
            print_success(f"💰 Business Case: ${total_savings:,} annual savings target")

        except FileNotFoundError:
            print_error(f"❌ Test data file not found: {self.test_data_path}")
            self.test_data = None
        except yaml.YAMLError as e:
            print_error(f"❌ YAML parsing error: {e}")
            self.test_data = None
        except Exception as e:
            print_error(f"❌ Test data loading failed: {e}")
            self.test_data = None

    def _validate_test_data_structure(self) -> bool:
        """Validate test data has required structure."""
        required_keys = ["vpc_test_data", "business_metrics", "aws_profiles"]

        if not all(key in self.test_data for key in required_keys):
            print_error("❌ Missing required test data sections")
            return False

        # Validate VPC data structure
        vpc_data = self.test_data["vpc_test_data"]
        if "active_vpcs" not in vpc_data or "deleted_vpcs" not in vpc_data:
            print_error("❌ Missing VPC data sections")
            return False

        return True

    def get_active_vpcs(self) -> List[Dict[str, Any]]:
        """Get list of active VPCs for discovery testing."""
        if not self.test_data:
            return []

        return self.test_data["vpc_test_data"]["active_vpcs"]

    def get_deleted_vpcs(self) -> List[Dict[str, Any]]:
        """Get list of deleted VPCs for historical validation."""
        if not self.test_data:
            return []

        return self.test_data["vpc_test_data"]["deleted_vpcs"]

    def get_vpc_by_id(self, vpc_id: str) -> Optional[Dict[str, Any]]:
        """Get specific VPC data by ID."""
        active_vpcs = self.get_active_vpcs()
        for vpc in active_vpcs:
            if vpc.get("vpc_id") == vpc_id:
                return vpc

        return None

    def get_vpcs_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all VPCs in a specific region."""
        active_vpcs = self.get_active_vpcs()
        return [vpc for vpc in active_vpcs if vpc.get("region") == region]

    def get_zero_eni_vpcs(self) -> List[Dict[str, Any]]:
        """Get VPCs with 0 ENIs (immediate cleanup candidates)."""
        active_vpcs = self.get_active_vpcs()
        return [vpc for vpc in active_vpcs if vpc.get("enis", 0) == 0]

    def get_test_regions(self) -> List[str]:
        """Get list of all regions in test data."""
        active_vpcs = self.get_active_vpcs()
        regions = list(set(vpc.get("region", "unknown") for vpc in active_vpcs))
        return sorted(regions)

    def get_business_metrics(self) -> Dict[str, Any]:
        """Get business metrics for validation."""
        if not self.test_data:
            return {}

        return self.test_data.get("business_metrics", {})

    def get_aws_profiles(self) -> Dict[str, str]:
        """Get AWS profiles configuration."""
        if not self.test_data:
            return {}

        return self.test_data.get("aws_profiles", {})

    def simulate_vpc_discovery_response(self, region: str) -> Dict[str, Any]:
        """
        Simulate AWS VPC discovery response for testing.

        Returns mock VPC data in AWS API response format for the specified region.
        """
        region_vpcs = self.get_vpcs_by_region(region)

        # Convert test data to AWS API response format
        aws_vpcs = []
        for vpc_data in region_vpcs:
            aws_vpc = {
                "VpcId": vpc_data["vpc_id"],
                "CidrBlock": vpc_data["cidr"],
                "State": "available",
                "IsDefault": vpc_data.get("name", "").startswith("default"),
                "Tags": [{"Key": "Name", "Value": vpc_data["name"]}],
            }
            aws_vpcs.append(aws_vpc)

        return {
            "Vpcs": aws_vpcs,
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
                "RequestId": f"test-request-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "HTTPHeaders": {"date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")},
            },
        }

    def simulate_eni_response(self, vpc_id: str) -> Dict[str, Any]:
        """
        Simulate AWS ENI response for testing ENI Gate validation.

        Returns mock ENI data based on test data ENI counts.
        """
        vpc_data = self.get_vpc_by_id(vpc_id)
        if not vpc_data:
            return {"NetworkInterfaces": []}

        eni_count = vpc_data.get("enis", 0)

        # Generate mock ENI data
        network_interfaces = []
        for i in range(eni_count):
            eni = {
                "NetworkInterfaceId": f"eni-{vpc_id[-8:]}{i:02d}",
                "VpcId": vpc_id,
                "Status": "in-use",
                "PrivateIpAddress": f"10.0.{i}.{i + 10}",
                "Description": f"Test ENI {i + 1} for {vpc_data['name']}",
            }
            network_interfaces.append(eni)

        return {
            "NetworkInterfaces": network_interfaces,
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
                "RequestId": f"test-eni-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "HTTPHeaders": {"date": datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")},
            },
        }

    def validate_discovery_results(self, discovered_vpcs: List[Dict], expected_region: str) -> Dict[str, Any]:
        """
        Validate VPC discovery results against test data.

        Args:
            discovered_vpcs: VPCs discovered by the implementation
            expected_region: Region that was scanned

        Returns:
            Validation results with accuracy metrics
        """
        expected_vpcs = self.get_vpcs_by_region(expected_region)
        expected_vpc_ids = [vpc["vpc_id"] for vpc in expected_vpcs]
        discovered_vpc_ids = [vpc.get("vpc_id", "") for vpc in discovered_vpcs]

        # Calculate accuracy metrics
        correctly_found = len(set(discovered_vpc_ids) & set(expected_vpc_ids))
        total_expected = len(expected_vpc_ids)
        total_discovered = len(discovered_vpc_ids)

        accuracy = (correctly_found / total_expected * 100) if total_expected > 0 else 0
        precision = (correctly_found / total_discovered * 100) if total_discovered > 0 else 0

        # Identify missing and extra VPCs
        missing_vpcs = set(expected_vpc_ids) - set(discovered_vpc_ids)
        extra_vpcs = set(discovered_vpc_ids) - set(expected_vpc_ids)

        return {
            "region": expected_region,
            "expected_count": total_expected,
            "discovered_count": total_discovered,
            "correctly_found": correctly_found,
            "accuracy_percentage": round(accuracy, 1),
            "precision_percentage": round(precision, 1),
            "missing_vpcs": list(missing_vpcs),
            "extra_vpcs": list(extra_vpcs),
            "validation_passed": accuracy >= 90.0,  # 90% accuracy threshold
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test data summary."""
        if not self.test_data:
            return {"error": "No test data available"}

        active_vpcs = self.get_active_vpcs()
        deleted_vpcs = self.get_deleted_vpcs()
        regions = self.get_test_regions()
        zero_eni_vpcs = self.get_zero_eni_vpcs()
        business_metrics = self.get_business_metrics()

        # Calculate region distribution
        region_distribution = {}
        for vpc in active_vpcs:
            region = vpc.get("region", "unknown")
            region_distribution[region] = region_distribution.get(region, 0) + 1

        # Calculate ENI distribution
        eni_distribution = {}
        for vpc in active_vpcs:
            eni_count = vpc.get("enis", 0)
            eni_key = f"{eni_count}_enis"
            eni_distribution[eni_key] = eni_distribution.get(eni_key, 0) + 1

        return {
            "test_data_source": self.test_data_path,
            "total_active_vpcs": len(active_vpcs),
            "total_deleted_vpcs": len(deleted_vpcs),
            "total_regions": len(regions),
            "regions": regions,
            "region_distribution": region_distribution,
            "eni_distribution": eni_distribution,
            "zero_eni_candidates": len(zero_eni_vpcs),
            "business_metrics": business_metrics,
            "annual_savings_target": business_metrics.get("annual_savings", 0),
            "immediate_cleanup_ready": len(zero_eni_vpcs),
            "data_quality": {
                "complete_vpc_records": len(
                    [
                        vpc
                        for vpc in active_vpcs
                        if all(key in vpc for key in ["vpc_id", "name", "region", "enis", "cost_annual"])
                    ]
                ),
                "data_completeness": round(
                    len(
                        [
                            vpc
                            for vpc in active_vpcs
                            if all(key in vpc for key in ["vpc_id", "name", "region", "enis", "cost_annual"])
                        ]
                    )
                    / len(active_vpcs)
                    * 100,
                    1,
                )
                if active_vpcs
                else 0,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


def load_test_data() -> VPCTestDataLoader:
    """Convenience function to load VPC test data."""
    return VPCTestDataLoader()


def validate_test_data_integration() -> bool:
    """Validate test data integration is working properly."""
    try:
        loader = VPCTestDataLoader()
        if not loader.test_data:
            print_error("❌ Test data integration failed")
            return False

        summary = loader.generate_test_summary()
        print_success(f"✅ Test data integration validated: {summary['total_active_vpcs']} VPCs ready")
        return True

    except Exception as e:
        print_error(f"❌ Test data validation failed: {e}")
        return False


if __name__ == "__main__":
    # Standalone validation
    console.print("[bold green]VPC Test Data Loader - AWS-25 Integration[/bold green]")

    loader = VPCTestDataLoader()
    if loader.test_data:
        summary = loader.generate_test_summary()

        console.print(f"[green]✅ Active VPCs:[/green] {summary['total_active_vpcs']}")
        console.print(f"[green]✅ Regions:[/green] {summary['total_regions']}")
        console.print(f"[green]✅ Zero ENI candidates:[/green] {summary['zero_eni_candidates']}")
        console.print(f"[green]✅ Annual savings target:[/green] ${summary['annual_savings_target']:,}")

        # Test region-specific discovery
        for region in summary["regions"][:3]:  # Test first 3 regions
            region_vpcs = loader.get_vpcs_by_region(region)
            console.print(f"[cyan]📍 {region}:[/cyan] {len(region_vpcs)} VPCs")
    else:
        print_error("❌ Test data loading failed")
