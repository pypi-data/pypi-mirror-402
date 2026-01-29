#!/usr/bin/env python3
"""
--dry-run Implementation Examples for Runbooks Modules

This module provides practical examples of how to integrate the universal dry-run
safety framework into existing and new runbooks modules.

Strategic Alignment:
- "Do one thing and do it well" - Consistent dry-run behavior across modules
- Enterprise safety standards with comprehensive examples

Author: Runbooks Team
Version: 1.0.0 - Implementation Examples
"""

from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

from runbooks.common.dry_run_framework import (
    DryRunContext,
    OperationType,
    dry_run_operation,
    discovery_operation,
    analysis_operation,
    assessment_operation,
    resource_creation_operation,
    resource_deletion_operation,
    remediation_operation,
    framework,
)
from runbooks.common.rich_utils import console, print_success, print_warning, print_error


# =============================================================================
# 1. DISCOVERY OPERATIONS (inventory, scan modules)
# =============================================================================


@discovery_operation
def collect_ec2_instances(
    dry_run_context: DryRunContext, profile: Optional[str] = None, regions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Example discovery operation - EC2 instance collection.

    Discovery operations are inherently safe, so dry-run simulates API calls
    for testing purposes only.
    """
    if dry_run_context.enabled:
        # Simulation mode - no real API calls
        console.print("[dim]🔄 Simulating EC2 instance discovery...[/dim]")

        # Return simulated data
        return {
            "instances": [
                {"id": "i-sim123", "type": "t3.micro", "state": "running"},
                {"id": "i-sim456", "type": "m5.large", "state": "stopped"},
            ],
            "simulated": True,
            "region_count": len(regions or ["ap-southeast-2"]),
            "total_discovered": 2,
        }

    else:
        # Real discovery operation
        console.print("[cyan]🔍 Discovering EC2 instances across regions...[/cyan]")

        session = boto3.Session(profile_name=profile)
        instances = []

        for region in regions or ["ap-southeast-2"]:
            try:
                ec2 = session.client("ec2", region_name=region)
                response = ec2.describe_instances()

                for reservation in response["Reservations"]:
                    for instance in reservation["Instances"]:
                        instances.append(
                            {
                                "id": instance["InstanceId"],
                                "type": instance["InstanceType"],
                                "state": instance["State"]["Name"],
                                "region": region,
                            }
                        )

            except ClientError as e:
                print_warning(f"Could not access region {region}: {e}")

        print_success(f"Discovered {len(instances)} EC2 instances")

        return {
            "instances": instances,
            "simulated": False,
            "region_count": len(regions or ["ap-southeast-2"]),
            "total_discovered": len(instances),
        }


# =============================================================================
# 2. ANALYSIS OPERATIONS (finops, security assess, vpc analyze modules)
# =============================================================================


@analysis_operation
def analyze_cost_optimization(
    dry_run_context: DryRunContext, profile: Optional[str] = None, account_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Example analysis operation - cost optimization analysis.

    Analysis operations are read-only, so dry-run shows what would be analyzed
    without making API calls.
    """
    if dry_run_context.enabled:
        # Preview mode - show what would be analyzed
        console.print("[dim]📊 Preview: Cost analysis scope[/dim]")
        console.print(f"[dim]  • Account: {account_id or 'Current account'}[/dim]")
        console.print(f"[dim]  • Services: EC2, RDS, S3, Lambda[/dim]")
        console.print(f"[dim]  • Time range: Last 30 days[/dim]")

        return {
            "preview": True,
            "scope": {"account_id": account_id, "services": ["EC2", "RDS", "S3", "Lambda"], "time_range": "30 days"},
        }

    else:
        # Real cost analysis
        console.print("[green]💰 Analyzing cost optimization opportunities...[/green]")

        session = boto3.Session(profile_name=profile)
        cost_explorer = session.client("ce")

        # Real cost analysis logic here
        # This is a simplified example

        print_success("Cost analysis completed")

        return {
            "analysis_complete": True,
            "recommendations": [
                {"service": "EC2", "potential_savings": "$150/month"},
                {"service": "RDS", "potential_savings": "$75/month"},
            ],
            "total_potential_savings": "$225/month",
        }


# =============================================================================
# 3. ASSESSMENT OPERATIONS (cfat assess module)
# =============================================================================


@assessment_operation
def assess_security_compliance(
    dry_run_context: DryRunContext, profile: Optional[str] = None, frameworks: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Example assessment operation - security compliance assessment.

    Assessment operations are read-only, so dry-run shows assessment scope.
    """
    frameworks = frameworks or ["SOC2", "PCI-DSS", "HIPAA"]

    if dry_run_context.enabled:
        # Preview mode - show assessment scope
        console.print("[dim]🔍 Preview: Security assessment scope[/dim]")
        console.print(f"[dim]  • Frameworks: {', '.join(frameworks)}[/dim]")
        console.print(f"[dim]  • Services to check: IAM, S3, EC2, VPC[/dim]")
        console.print(f"[dim]  • Estimated duration: 5-10 minutes[/dim]")

        return {"preview": True, "frameworks": frameworks, "estimated_checks": 45}

    else:
        # Real security assessment
        console.print("[blue]🔒 Conducting security compliance assessment...[/blue]")

        session = boto3.Session(profile_name=profile)

        # Real assessment logic here
        # This is a simplified example

        results = {
            "frameworks_assessed": frameworks,
            "total_checks": 45,
            "passed": 38,
            "failed": 7,
            "compliance_score": "84.4%",
        }

        print_success(f"Assessment completed - Compliance score: {results['compliance_score']}")

        return results


# =============================================================================
# 4. RESOURCE CREATION OPERATIONS (operate module)
# =============================================================================


@resource_creation_operation(estimated_impact="Create 1 EC2 instance (~$25/month)")
def create_ec2_instance(
    dry_run_context: DryRunContext,
    instance_type: str = "t3.micro",
    image_id: Optional[str] = None,
    profile: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Example resource creation operation - EC2 instance creation.

    Resource creation operations default to dry-run for safety.
    """
    if dry_run_context.enabled:
        # Preview mode - show what would be created
        console.print("[yellow]🔄 Preview: EC2 instance creation[/yellow]")
        console.print(f"[dim]  • Instance type: {instance_type}[/dim]")
        console.print(f"[dim]  • AMI ID: {image_id or 'Latest Amazon Linux 2'}[/dim]")
        console.print(f"[dim]  • Estimated cost: ~$25/month[/dim]")

        return {"preview": True, "instance_type": instance_type, "image_id": image_id, "estimated_monthly_cost": 25.00}

    else:
        # Real instance creation
        console.print("[green]🚀 Creating EC2 instance...[/green]")

        session = boto3.Session(profile_name=profile)
        ec2 = session.client("ec2")

        # Use default AMI if not specified
        if not image_id:
            # Get latest Amazon Linux 2 AMI
            images = ec2.describe_images(
                Owners=["amazon"],
                Filters=[
                    {"Name": "name", "Values": ["amzn2-ami-hvm-*"]},
                    {"Name": "architecture", "Values": ["x86_64"]},
                    {"Name": "virtualization-type", "Values": ["hvm"]},
                ],
            )
            if images["Images"]:
                image_id = sorted(images["Images"], key=lambda x: x["CreationDate"], reverse=True)[0]["ImageId"]

        try:
            response = ec2.run_instances(
                ImageId=image_id,
                MinCount=1,
                MaxCount=1,
                InstanceType=instance_type,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "CreatedBy", "Value": "CloudOps-Runbooks"},
                            {"Key": "Purpose", "Value": "Testing"},
                        ],
                    }
                ],
            )

            instance_id = response["Instances"][0]["InstanceId"]
            print_success(f"EC2 instance created: {instance_id}")

            return {"instance_id": instance_id, "instance_type": instance_type, "image_id": image_id, "created": True}

        except ClientError as e:
            print_error(f"Failed to create instance: {e}")
            raise


# =============================================================================
# 5. RESOURCE DELETION OPERATIONS (operate module)
# =============================================================================


@resource_deletion_operation(estimated_impact="Delete EC2 instances (~$150/month savings)")
def terminate_ec2_instances(
    dry_run_context: DryRunContext, instance_ids: List[str], profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Example resource deletion operation - EC2 instance termination.

    Resource deletion operations default to dry-run and require confirmation.
    """
    if dry_run_context.enabled:
        # Preview mode - show what would be deleted
        console.print("[red]⚠️  Preview: EC2 instance termination[/red]")
        console.print(f"[dim]  • Instances to terminate: {len(instance_ids)}[/dim]")
        console.print(f"[dim]  • Instance IDs: {', '.join(instance_ids)}[/dim]")
        console.print(f"[dim]  • Estimated savings: ~$150/month[/dim]")
        console.print(f"[dim]  • ⚠️  THIS OPERATION IS IRREVERSIBLE[/dim]")

        return {
            "preview": True,
            "instances_to_terminate": instance_ids,
            "estimated_savings": 150.00,
            "irreversible": True,
        }

    else:
        # Real instance termination
        console.print("[red]💥 Terminating EC2 instances...[/red]")

        session = boto3.Session(profile_name=profile)
        ec2 = session.client("ec2")

        try:
            response = ec2.terminate_instances(InstanceIds=instance_ids)

            terminated = []
            for instance in response["TerminatingInstances"]:
                terminated.append(
                    {
                        "instance_id": instance["InstanceId"],
                        "current_state": instance["CurrentState"]["Name"],
                        "previous_state": instance["PreviousState"]["Name"],
                    }
                )

            print_success(f"Successfully initiated termination of {len(terminated)} instances")

            return {"terminated_instances": terminated, "count": len(terminated), "operation": "terminate"}

        except ClientError as e:
            print_error(f"Failed to terminate instances: {e}")
            raise


# =============================================================================
# 6. SECURITY REMEDIATION OPERATIONS (remediation module)
# =============================================================================


@remediation_operation(estimated_impact="Fix S3 public buckets (security improvement)")
def fix_public_s3_buckets(
    dry_run_context: DryRunContext, bucket_names: List[str], profile: Optional[str] = None
) -> Dict[str, Any]:
    """
    Example security remediation operation - fix public S3 buckets.

    Remediation operations default to dry-run and require confirmation.
    """
    if dry_run_context.enabled:
        # Preview mode - show what would be fixed
        console.print("[yellow]🔧 Preview: S3 bucket security remediation[/yellow]")
        console.print(f"[dim]  • Buckets to secure: {len(bucket_names)}[/dim]")
        console.print(f"[dim]  • Bucket names: {', '.join(bucket_names)}[/dim]")
        console.print(f"[dim]  • Actions: Remove public access, update policies[/dim]")

        return {
            "preview": True,
            "buckets_to_fix": bucket_names,
            "remediation_actions": [
                "Remove public read access",
                "Remove public write access",
                "Update bucket policies",
                "Enable access logging",
            ],
        }

    else:
        # Real security remediation
        console.print("[green]🔒 Applying security remediation to S3 buckets...[/green]")

        session = boto3.Session(profile_name=profile)
        s3 = session.client("s3")

        remediated_buckets = []

        for bucket_name in bucket_names:
            try:
                # Block public access
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        "BlockPublicAcls": True,
                        "IgnorePublicAcls": True,
                        "BlockPublicPolicy": True,
                        "RestrictPublicBuckets": True,
                    },
                )

                remediated_buckets.append(
                    {"bucket_name": bucket_name, "status": "secured", "actions_applied": ["public_access_blocked"]}
                )

            except ClientError as e:
                print_warning(f"Could not secure bucket {bucket_name}: {e}")
                remediated_buckets.append({"bucket_name": bucket_name, "status": "failed", "error": str(e)})

        successful = len([b for b in remediated_buckets if b["status"] == "secured"])
        print_success(f"Successfully secured {successful}/{len(bucket_names)} S3 buckets")

        return {
            "buckets_processed": remediated_buckets,
            "successful_count": successful,
            "total_count": len(bucket_names),
        }


# =============================================================================
# 7. DIRECT FRAMEWORK USAGE (without decorators)
# =============================================================================


def custom_operation_with_framework(
    dry_run: bool = True, operation_name: str = "custom_operation", resources: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Example of using the dry-run framework directly without decorators.

    This approach gives you full control over the dry-run behavior
    and is useful for complex operations that need custom handling.
    """
    # Create dry-run context
    context = framework.create_context(
        dry_run=dry_run,
        operation_type=OperationType.RESOURCE_MODIFY,
        module_name="example",
        operation_name=operation_name,
        target_resources=resources,
        estimated_impact="Moderate configuration changes",
    )

    # Display banner
    framework.display_dry_run_banner(context)

    # Request confirmation if needed
    if not framework.confirm_operation(context):
        return {"cancelled": True}

    # Log operation start
    framework.log_operation_start(context, {"custom_parameter": "example"})

    try:
        if context.enabled:
            # Dry-run logic
            console.print("[dim]🔄 Simulating custom operation...[/dim]")
            result = {"simulated": True, "resources": resources or []}
        else:
            # Real operation logic
            console.print("[green]⚡ Executing custom operation...[/green]")
            # Your actual operation code here
            result = {"executed": True, "resources": resources or []}

        # Log success
        framework.log_operation_complete(context, success=True, results=result)

        return result

    except Exception as e:
        # Log failure
        framework.log_operation_complete(context, success=False, error=str(e))
        raise


# =============================================================================
# 8. MIGRATION HELPER FUNCTIONS
# =============================================================================


def migrate_legacy_dry_run_function(legacy_function: callable) -> callable:
    """
    Helper function to migrate legacy dry-run implementations to the new framework.

    This function can wrap existing functions that have their own dry-run logic
    and upgrade them to use the unified framework.
    """

    def wrapper(*args, **kwargs):
        # Extract dry_run parameter
        dry_run = kwargs.get("dry_run", True)

        # Determine operation type based on function name/behavior
        func_name = legacy_function.__name__
        if "create" in func_name or "provision" in func_name:
            op_type = OperationType.RESOURCE_CREATE
        elif "delete" in func_name or "terminate" in func_name or "remove" in func_name:
            op_type = OperationType.RESOURCE_DELETE
        elif "modify" in func_name or "update" in func_name or "change" in func_name:
            op_type = OperationType.RESOURCE_MODIFY
        elif "fix" in func_name or "remediat" in func_name:
            op_type = OperationType.REMEDIATION
        else:
            op_type = OperationType.ANALYSIS

        # Create context
        context = framework.create_context(
            dry_run=dry_run,
            operation_type=op_type,
            module_name=legacy_function.__module__.split(".")[-2] if "." in legacy_function.__module__ else "legacy",
            operation_name=func_name,
        )

        # Apply framework behavior
        framework.display_dry_run_banner(context)

        if not framework.confirm_operation(context):
            return None

        framework.log_operation_start(context)

        try:
            # Call the original function with updated context
            kwargs["dry_run"] = context.enabled
            result = legacy_function(*args, **kwargs)

            framework.log_operation_complete(context, success=True, results={"migrated": True})
            return result

        except Exception as e:
            framework.log_operation_complete(context, success=False, error=str(e))
            raise

    return wrapper


# =============================================================================
# Example CLI Integration
# =============================================================================

if __name__ == "__main__":
    """
    Example CLI usage demonstrating the dry-run framework.
    """
    import click

    @click.group()
    def cli():
        """Example CLI with dry-run framework integration."""
        pass

    @cli.command()
    @click.option("--dry-run/--no-dry-run", default=True, help="Enable dry-run mode")
    @click.option("--profile", help="AWS profile name")
    @click.option("--regions", multiple=True, help="AWS regions")
    def discover(dry_run, profile, regions):
        """Discover EC2 instances with dry-run support."""
        result = collect_ec2_instances(profile=profile, regions=list(regions) if regions else None, dry_run=dry_run)
        console.print(f"Discovery result: {result}")

    @cli.command()
    @click.option("--dry-run/--no-dry-run", default=True, help="Enable dry-run mode")
    @click.option("--instance-type", default="t3.micro", help="Instance type")
    @click.option("--profile", help="AWS profile name")
    def create(dry_run, instance_type, profile):
        """Create EC2 instance with dry-run support."""
        result = create_ec2_instance(instance_type=instance_type, profile=profile, dry_run=dry_run)
        console.print(f"Creation result: {result}")

    # Run CLI
    cli()
