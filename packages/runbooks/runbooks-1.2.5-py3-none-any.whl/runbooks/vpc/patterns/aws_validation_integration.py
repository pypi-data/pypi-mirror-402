"""
AWS Resource Validation Integration Pattern.

Provides base class for AWS API validation with per-account profile support.
Generates MCP-style validation reports with ≥99.5% accuracy threshold.

Pattern extracted from: vpce_cleanup_manager.py (validate_with_aws, generate_mcp_validation_report)
Reusable for: All AWS resource validation (VPCs, ENIs, NAT Gateways, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError, ProfileNotFound
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TextColumn
from runbooks.common.rich_utils import console, print_info, print_success, print_warning, print_error, create_table


@dataclass
class ValidationResult:
    """AWS resource validation result."""

    total_resources: int
    exists: int
    not_found: int
    errors: Dict[str, str]
    accuracy: float
    accounts_validated: int
    resource_type: str
    not_found_details: List[Dict] = None  # Detailed info for not found resources
    error_details: List[Dict] = None  # Detailed info for errors

    def __post_init__(self):
        """Initialize optional fields."""
        if self.not_found_details is None:
            self.not_found_details = []
        if self.error_details is None:
            self.error_details = []


class AWSResourceValidator(ABC):
    """
    Base class for AWS resource validation via API.

    Validates resources exist using per-account AWS profiles.
    Generates MCP-style validation reports with ≥99.5% accuracy threshold.

    Usage:
        class MyManager(AWSResourceValidator):
            def _get_resources_to_validate(self):
                return [{"id": "vpc-xxx", "profile": "profile1"}, ...]

        manager = MyManager()
        result = manager.validate_with_aws_api(
            resource_type="vpc-endpoint",
            api_method="describe_vpc_endpoints"
        )

    Pattern Benefits:
    - Per-account profile support (multi-account validation)
    - Dynamic API method support (works for VPCs, Endpoints, ENIs, etc.)
    - Rich CLI table rendering (MCP-style report)
    - Error handling with graceful fallback
    - Compliance threshold validation (≥99.5% accuracy)
    """

    @abstractmethod
    def _get_resources_to_validate(self) -> List[Dict]:
        """
        Return resources requiring validation.

        Returns:
            List of dicts with keys:
                - id: Resource ID (e.g., "vpce-xxx")
                - profile: AWS profile name for this resource
                - account_id: AWS account ID (optional)
                - region: AWS region (optional)
                - vpc_name: VPC name for context (optional)
        """
        pass

    def validate_with_aws_api(
        self,
        resource_type: str = "vpc-endpoint",
        api_method: str = "describe_vpc_endpoints",
        api_params_key: str = "VpcEndpointIds",
        default_region: str = "ap-southeast-2",
        use_resource_region: bool = True,
    ) -> ValidationResult:
        """
        Validate resources via AWS API using per-account profiles.

        Args:
            resource_type: Resource type label for logging
            api_method: EC2 API method name (e.g., "describe_vpcs")
            api_params_key: Parameter key for resource IDs
            default_region: Default AWS region if resource doesn't specify
            use_resource_region: If True, use per-resource region from resource dict

        Returns:
            ValidationResult with validation statistics
        """
        resources = self._get_resources_to_validate()
        exists = []
        not_found = []
        not_found_details = []  # Enhanced: Detailed info for not found resources
        errors = {}
        error_details = []  # Enhanced: Detailed info for errors
        accounts_validated = set()

        print_info(f"🔍 Validating {len(resources)} {resource_type}s via AWS API...")

        # Process resources with Rich progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Validating {resource_type}s...", total=len(resources))

            for resource in resources:
                resource_id = resource.get("id")
                profile = resource.get("profile")
                resource_region = resource.get("region") if use_resource_region else None
                account_id = resource.get("account_id", "N/A")
                vpc_name = resource.get("vpc_name", "N/A")

                if not resource_id or not profile:
                    error_msg = "Missing resource ID or profile"
                    errors[resource_id or "unknown"] = error_msg
                    error_details.append(
                        {
                            "resource_id": resource_id or "unknown",
                            "account_id": account_id,
                            "region": resource_region or default_region,
                            "vpc_name": vpc_name,
                            "error": error_msg,
                        }
                    )
                    progress.update(task, advance=1)
                    continue

                try:
                    # Use per-resource region if available, otherwise use default
                    region = resource_region or default_region

                    session = boto3.Session(profile_name=profile)
                    ec2_client = session.client("ec2", region_name=region)

                    # Dynamic API call
                    api_call = getattr(ec2_client, api_method)
                    response = api_call(**{api_params_key: [resource_id]})

                    # Map API methods to their response keys for proper parsing
                    response_key_map = {
                        "describe_vpc_endpoints": "VpcEndpoints",
                        "describe_vpcs": "Vpcs",
                        "describe_network_interfaces": "NetworkInterfaces",
                        "describe_subnets": "Subnets",
                        "describe_route_tables": "RouteTables",
                    }
                    response_key = response_key_map.get(api_method, list(response.keys())[0])

                    if response.get(response_key):
                        exists.append(resource_id)
                        accounts_validated.add(profile)
                    else:
                        not_found.append(resource_id)
                        not_found_details.append(
                            {
                                "resource_id": resource_id,
                                "account_id": account_id,
                                "region": region,
                                "vpc_name": vpc_name,
                                "error": "Not found in AWS (may be deleted)",
                            }
                        )

                except ClientError as e:
                    if "NotFound" in e.response["Error"]["Code"] or "InvalidID" in e.response["Error"]["Code"]:
                        not_found.append(resource_id)
                        not_found_details.append(
                            {
                                "resource_id": resource_id,
                                "account_id": account_id,
                                "region": resource_region or default_region,
                                "vpc_name": vpc_name,
                                "error": f"Not found ({e.response['Error']['Code']})",
                            }
                        )
                    else:
                        error_msg = f"{e.response['Error']['Code']}: {e.response['Error']['Message']}"
                        errors[resource_id] = error_msg
                        error_details.append(
                            {
                                "resource_id": resource_id,
                                "account_id": account_id,
                                "region": resource_region or default_region,
                                "vpc_name": vpc_name,
                                "error": error_msg,
                            }
                        )

                except ProfileNotFound:
                    error_msg = f"ProfileNotFound: {profile}"
                    errors[resource_id] = error_msg
                    error_details.append(
                        {
                            "resource_id": resource_id,
                            "account_id": account_id,
                            "region": resource_region or default_region,
                            "vpc_name": vpc_name,
                            "error": error_msg,
                        }
                    )

                except AttributeError:
                    error_msg = f"Invalid API method: {api_method}"
                    errors[resource_id] = error_msg
                    error_details.append(
                        {
                            "resource_id": resource_id,
                            "account_id": account_id,
                            "region": resource_region or default_region,
                            "vpc_name": vpc_name,
                            "error": error_msg,
                        }
                    )

                except Exception as e:
                    error_msg = str(e)
                    errors[resource_id] = error_msg
                    error_details.append(
                        {
                            "resource_id": resource_id,
                            "account_id": account_id,
                            "region": resource_region or default_region,
                            "vpc_name": vpc_name,
                            "error": error_msg,
                        }
                    )

                # Update progress after each validation
                progress.update(task, advance=1)

        # Calculate accuracy
        total_validated = len(exists) + len(not_found)
        accuracy = (len(exists) / total_validated * 100) if total_validated > 0 else 0.0

        # Consolidate validation results into single line with optional not found note
        not_found_note = f", {len(not_found)} not found" if not_found else ""
        print_success(
            f"✅ AWS validation: {len(exists)}/{len(resources)} exist ({accuracy:.1f}% accuracy){not_found_note}"
        )

        if errors:
            print_error(f"❌ {len(errors)} validation errors")

        # Enhanced: Display detailed error table with troubleshooting info
        if not_found_details or error_details:
            self._display_validation_errors(
                not_found_details=not_found_details, error_details=error_details, resource_type=resource_type
            )

        return ValidationResult(
            total_resources=len(resources),
            exists=len(exists),
            not_found=len(not_found),
            errors=errors,
            accuracy=accuracy,
            accounts_validated=len(accounts_validated),
            resource_type=resource_type,
            not_found_details=not_found_details,
            error_details=error_details,
        )

    def _display_validation_errors(
        self, not_found_details: List[Dict], error_details: List[Dict], resource_type: str
    ) -> None:
        """
        Display detailed validation errors in Rich CLI table with troubleshooting guidance.

        Args:
            not_found_details: List of not found resources with context
            error_details: List of error resources with context
            resource_type: Resource type label for display
        """
        if not (not_found_details or error_details):
            return

        # Create detailed error table
        error_table = create_table(title=f"Validation Issues - Troubleshooting Required")
        error_table.add_column("Resource ID", style="yellow", no_wrap=True)
        error_table.add_column("Account", justify="right")
        error_table.add_column("Region", justify="center")
        error_table.add_column("VPC Name", style="dim")
        error_table.add_column("Error", style="red")

        # Add not found resources
        for item in not_found_details:
            error_table.add_row(
                item.get("resource_id", "N/A"),
                item.get("account_id", "N/A"),
                item.get("region", "N/A"),
                item.get("vpc_name", "N/A"),
                item.get("error", "Unknown error"),
            )

        # Add error resources
        for item in error_details:
            error_table.add_row(
                item.get("resource_id", "N/A"),
                item.get("account_id", "N/A"),
                item.get("region", "N/A"),
                item.get("vpc_name", "N/A"),
                item.get("error", "Unknown error"),
            )

        console.print("\n")
        console.print(error_table)

        ## Add troubleshooting guidance
        # console.print("\n[bold cyan]💡 Troubleshooting Steps:[/bold cyan]")
        # console.print("  [dim]1.[/dim] Verify resource wasn't deleted after CSV export")
        # console.print("  [dim]2.[/dim] Check AWS profile has access to the account")
        # console.print("  [dim]3.[/dim] Verify region matches VPC location (check VPC name prefix)")
        # console.print(f"  [dim]4.[/dim] Manual check: [cyan]aws ec2 describe-vpc-endpoints --region <region> --vpc-endpoint-ids <id>[/cyan]")
        # console.print(f"  [dim]5.[/dim] Confirm endpoint exists: [cyan]aws ec2 describe-vpc-endpoints --region <region> --filters 'Name=vpc-id,Values=<vpc-id>'[/cyan]")
        # console.print("\n")

    def generate_validation_report(
        self, validation_results: ValidationResult, accuracy_threshold: float = 99.5
    ) -> Dict:
        """
        Generate MCP-style validation report with Rich CLI table.

        Args:
            validation_results: Results from validate_with_aws_api()
            accuracy_threshold: Minimum accuracy for PASSED status (default: 99.5%)

        Returns:
            Dict with validation report and compliance status
        """
        validation_passed = validation_results.accuracy >= accuracy_threshold

        # Create Rich CLI table
        table = create_table(
            title=f"MCP Validation Report - {validation_results.resource_type}",
            columns=[
                {"name": "Validation Type", "justify": "left"},
                {"name": "Metric", "justify": "left"},
                {"name": "Value", "justify": "right"},
                {"name": "Status", "justify": "center"},
            ],
        )

        table.add_row("AWS API Validation", "Total Resources", str(validation_results.total_resources), "")
        table.add_row(
            "",
            "Validated (Exists)",
            str(validation_results.exists),
            f"✅ {validation_results.exists}/{validation_results.total_resources}",
        )
        table.add_row(
            "",
            "Not Found",
            str(validation_results.not_found),
            "✅ None" if validation_results.not_found == 0 else f"⚠️ {validation_results.not_found}",
        )
        table.add_row(
            "",
            "Errors",
            str(len(validation_results.errors)),
            "✅ None" if not validation_results.errors else f"❌ {len(validation_results.errors)}",
        )
        table.add_row(
            "",
            "Accuracy",
            f"{validation_results.accuracy:.1f}%",
            f"{'✅' if validation_passed else '⚠️'} {validation_results.accuracy:.1f}%",
        )
        table.add_row("", "Accounts Validated", str(validation_results.accounts_validated), "")

        console.print("\n")
        console.print(table)
        console.print(
            f"\n[dim italic]Validation Framework: AWS API = Resource existence check | Threshold = ≥{accuracy_threshold}% accuracy required[/dim italic]\n"
        )

        # Display errors if any
        if validation_results.errors:
            console.print("\n[bold yellow]Validation Errors:[/bold yellow]")
            for resource_id, error_msg in validation_results.errors.items():
                console.print(f"  • {resource_id}: {error_msg}")

        return {
            "validation_results": validation_results.__dict__,
            "accuracy_threshold": accuracy_threshold,
            "validation_passed": validation_passed,
            "compliance_status": "PASSED" if validation_passed else "REVIEW_REQUIRED",
        }
