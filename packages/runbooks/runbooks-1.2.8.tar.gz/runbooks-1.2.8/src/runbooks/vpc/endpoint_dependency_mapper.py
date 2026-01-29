"""
VPC Endpoint Dependency Mapper - Critical Workload Protection

Feature 1 from Phase 6 Implementation Plan

Business Value: Critical workload protection (risk mitigation - prevents production outages)
- Priority: P1 HIGH (safety-critical feature)
- Strategic Impact: Enables safe VPCE cleanup operations
- Integration: Feeds data to VPC cleanup orchestrator for deletion safety validation

Architecture Pattern:
- Resource dependency discovery (RDS, Lambda, EC2, ECS)
- Production workload detection (tag analysis)
- Impact analysis with D1-D6 signals
- Deletion safety assessment with risk levels
- Rich CLI reporting with dependency visualization

Dependencies:
- D1: Production workload dependency (CRITICAL - block deletion)
- D2: RDS database access (HIGH risk - requires migration)
- D3: Lambda function integration (HIGH risk - runtime dependency)
- D4: EC2 instance connectivity (MEDIUM risk - network dependency)
- D5: Multi-service dependencies (MEDIUM risk - complex impact)
- D6: Non-production only (LOW risk - safe to delete)

Usage:
    from runbooks.vpc import VPCEndpointDependencyMapper

    mapper = VPCEndpointDependencyMapper(profile='ops-profile')
    analyses = mapper.analyze_endpoint_dependencies(vpc_id='vpc-1234567890abcdef0')

    for analysis in analyses:
        if not analysis.deletion_safe:
            print(f"BLOCKED: {analysis.endpoint_id} - {analysis.deletion_blocker}")
"""

import boto3
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum
from rich.console import Console

try:
    from runbooks.common.profile_utils import get_profile_for_operation
except ImportError:
    # Fallback for environments where profile_utils is not available
    def get_profile_for_operation(
        operation_type: str = "operational", user_specified_profile: Optional[str] = None, **kwargs
    ) -> str:
        return user_specified_profile or "default"


from runbooks.common.rich_utils import create_table, create_panel


class DependencyRisk(str, Enum):
    """VPC endpoint dependency risk levels"""

    CRITICAL = "critical"  # Production workload - block deletion
    HIGH = "high"  # Database/Lambda - require migration
    MEDIUM = "medium"  # EC2/multi-service - review needed
    LOW = "low"  # Non-production - safe to delete
    NONE = "none"  # No dependencies - safe to delete


class DependencySignal(str, Enum):
    """VPC endpoint dependency signals"""

    D1_PRODUCTION_WORKLOAD = "D1"
    D2_RDS_DATABASE = "D2"
    D3_LAMBDA_FUNCTION = "D3"
    D4_EC2_INSTANCE = "D4"
    D5_MULTI_SERVICE = "D5"
    D6_NON_PRODUCTION = "D6"


@dataclass
class ResourceDependency:
    """Individual resource dependency"""

    resource_id: str
    resource_type: str  # RDS, Lambda, EC2, ECS, etc.
    service_name: str  # rds, lambda, ec2, etc.
    endpoint_id: str
    vpc_id: str
    criticality: DependencyRisk
    production_indicator: bool  # Has "prod" tag or in prod VPC
    dependency_type: str  # DATABASE_ACCESS, API_CALL, NETWORK_CONNECTIVITY


@dataclass
class EndpointDependencyAnalysis:
    """VPC endpoint dependency analysis"""

    endpoint_id: str
    service_name: str  # s3, dynamodb, rds, lambda, etc.
    vpc_id: str
    subnet_ids: List[str]
    security_group_ids: List[str]
    dependencies: List[ResourceDependency]
    dependency_count: int
    dependency_signals: List[DependencySignal]
    risk_level: DependencyRisk
    production_workload: bool
    deletion_safe: bool
    deletion_blocker: Optional[str]  # Reason if not safe to delete
    impact_summary: str


class VPCEndpointDependencyMapper:
    """
    VPC Endpoint Dependency Mapper - Critical Workload Protection

    Maps dependencies between VPC endpoints and AWS resources to prevent
    accidental deletion of endpoints supporting critical workloads.

    Dependency Discovery:
    - RDS databases accessing S3 (backups, data export)
    - Lambda functions using VPC endpoints (DynamoDB, S3, etc.)
    - EC2 instances with VPC endpoint connectivity
    - ECS tasks using VPC endpoints for service communication
    - Cross-service dependencies (multi-endpoint usage)

    Risk Classification:
    - CRITICAL (D1): Production workload dependency → Block deletion
    - HIGH (D2/D3): Database/Lambda integration → Require migration plan
    - MEDIUM (D4/D5): EC2/multi-service → Review needed
    - LOW (D6): Non-production only → Safe to delete with approval
    - NONE: No dependencies → Safe to delete

    Dependency Signals:
    - D1: Production workload (prod tag or prod VPC) → CRITICAL
    - D2: RDS database access → HIGH
    - D3: Lambda function integration → HIGH
    - D4: EC2 instance connectivity → MEDIUM
    - D5: Multi-service dependencies (>3 services) → MEDIUM
    - D6: Non-production only → LOW

    Example:
        mapper = VPCEndpointDependencyMapper(profile='ops-profile')
        analyses = mapper.analyze_endpoint_dependencies(
            vpc_id='vpc-1234567890abcdef0'
        )

        for analysis in analyses:
            if not analysis.deletion_safe:
                print(f"BLOCKED: {analysis.endpoint_id} - {analysis.deletion_blocker}")
    """

    def __init__(self, profile: Optional[str] = None, region: Optional[str] = None):
        """Initialize VPC endpoint dependency mapper"""
        self.profile = get_profile_for_operation("operational", profile)
        self.session = boto3.Session(profile_name=self.profile)
        self.region = region or self.session.region_name
        self.console = Console()

        # AWS clients (lazy initialization)
        self._ec2 = None
        self._rds = None
        self._lambda = None
        self._ecs = None
        self._resourcegroupstaggingapi = None

    @property
    def ec2(self):
        """Lazy EC2 client"""
        if self._ec2 is None:
            self._ec2 = self.session.client("ec2", region_name=self.region)
        return self._ec2

    @property
    def rds(self):
        """Lazy RDS client"""
        if self._rds is None:
            self._rds = self.session.client("rds", region_name=self.region)
        return self._rds

    @property
    def lambda_client(self):
        """Lazy Lambda client"""
        if self._lambda is None:
            self._lambda = self.session.client("lambda", region_name=self.region)
        return self._lambda

    @property
    def ecs(self):
        """Lazy ECS client"""
        if self._ecs is None:
            self._ecs = self.session.client("ecs", region_name=self.region)
        return self._ecs

    @property
    def tagging(self):
        """Lazy Resource Groups Tagging API client"""
        if self._resourcegroupstaggingapi is None:
            self._resourcegroupstaggingapi = self.session.client("resourcegroupstaggingapi", region_name=self.region)
        return self._resourcegroupstaggingapi

    def analyze_endpoint_dependencies(
        self, vpc_id: Optional[str] = None, endpoint_ids: Optional[List[str]] = None
    ) -> List[EndpointDependencyAnalysis]:
        """
        Analyze VPC endpoint dependencies for deletion safety

        Args:
            vpc_id: Analyze all endpoints in VPC (optional)
            endpoint_ids: Specific endpoints to analyze (optional)

        Returns:
            List of endpoint dependency analyses
        """
        # Get VPC endpoints
        filters = []
        if vpc_id:
            filters.append({"Name": "vpc-id", "Values": [vpc_id]})
        if endpoint_ids:
            filters.append({"Name": "vpc-endpoint-id", "Values": endpoint_ids})

        try:
            response = self.ec2.describe_vpc_endpoints(Filters=filters if filters else [])
            endpoints = response.get("VpcEndpoints", [])
        except Exception as e:
            self.console.print(f"[red]Error fetching VPC endpoints: {e}[/red]")
            return []

        analyses = []
        for endpoint in endpoints:
            analysis = self._analyze_endpoint(endpoint)
            analyses.append(analysis)

        self.console.print(f"[bold green]🔍 VPC Endpoints: Analyzed {len(analyses)} endpoints[/bold green]")
        return analyses

    def _analyze_endpoint(self, endpoint: Dict) -> EndpointDependencyAnalysis:
        """
        Analyze individual VPC endpoint dependencies

        Args:
            endpoint: VPC endpoint metadata

        Returns:
            Comprehensive dependency analysis
        """
        endpoint_id = endpoint["VpcEndpointId"]
        service_name = endpoint["ServiceName"].split(".")[-1]  # Extract service (s3, dynamodb, etc.)
        vpc_id = endpoint["VpcId"]
        subnet_ids = endpoint.get("SubnetIds", [])

        # Extract security group IDs
        groups = endpoint.get("Groups", [])
        security_group_ids = [sg["GroupId"] for sg in groups]

        # Discover dependencies
        dependencies = self._discover_dependencies(endpoint_id, service_name, vpc_id, subnet_ids, security_group_ids)

        # Update endpoint_id in dependencies
        for dep in dependencies:
            dep.endpoint_id = endpoint_id

        # Generate dependency signals
        signals = self._generate_dependency_signals(dependencies)

        # Calculate risk level
        risk_level = self._calculate_risk_level(signals, dependencies)

        # Check production workload
        production_workload = any(dep.production_indicator for dep in dependencies)

        # Determine deletion safety
        deletion_safe, deletion_blocker = self._assess_deletion_safety(risk_level, production_workload, dependencies)

        # Generate impact summary
        impact_summary = self._generate_impact_summary(dependencies, risk_level)

        return EndpointDependencyAnalysis(
            endpoint_id=endpoint_id,
            service_name=service_name,
            vpc_id=vpc_id,
            subnet_ids=subnet_ids,
            security_group_ids=security_group_ids,
            dependencies=dependencies,
            dependency_count=len(dependencies),
            dependency_signals=signals,
            risk_level=risk_level,
            production_workload=production_workload,
            deletion_safe=deletion_safe,
            deletion_blocker=deletion_blocker,
            impact_summary=impact_summary,
        )

    def _discover_dependencies(
        self, endpoint_id: str, service_name: str, vpc_id: str, subnet_ids: List[str], security_group_ids: List[str]
    ) -> List[ResourceDependency]:
        """
        Discover all resources depending on VPC endpoint

        Discovery strategy:
        1. RDS instances in same VPC/subnets (S3 backup, data export)
        2. Lambda functions with VPC config matching endpoint subnets
        3. EC2 instances in same subnets with endpoint service usage
        4. ECS tasks using VPC endpoint services
        """
        dependencies = []

        # Discover RDS dependencies
        dependencies.extend(self._discover_rds_dependencies(vpc_id, subnet_ids, service_name))

        # Discover Lambda dependencies
        dependencies.extend(self._discover_lambda_dependencies(vpc_id, subnet_ids, service_name))

        # Discover EC2 dependencies
        dependencies.extend(self._discover_ec2_dependencies(vpc_id, subnet_ids, security_group_ids, service_name))

        # Discover ECS dependencies
        dependencies.extend(self._discover_ecs_dependencies(vpc_id, subnet_ids, service_name))

        return dependencies

    def _discover_rds_dependencies(
        self, vpc_id: str, subnet_ids: List[str], service_name: str
    ) -> List[ResourceDependency]:
        """Discover RDS database dependencies"""
        dependencies = []

        try:
            # Get RDS instances
            response = self.rds.describe_db_instances()
            db_instances = response.get("DBInstances", [])

            for db in db_instances:
                vpc_sg = db.get("DBSubnetGroup", {})
                db_vpc_id = vpc_sg.get("VpcId")

                if db_vpc_id != vpc_id:
                    continue

                # Check if DB uses S3 for backups/exports
                if service_name == "s3":
                    tags = db.get("TagList", [])
                    production = self._is_production_resource(tags, db_vpc_id)

                    dependencies.append(
                        ResourceDependency(
                            resource_id=db["DBInstanceIdentifier"],
                            resource_type="RDS",
                            service_name="rds",
                            endpoint_id="",  # Will be filled by caller
                            vpc_id=vpc_id,
                            criticality=DependencyRisk.HIGH,
                            production_indicator=production,
                            dependency_type="DATABASE_BACKUP",
                        )
                    )
        except Exception as e:
            self.console.print(f"[yellow]Warning: RDS discovery failed: {e}[/yellow]", style="dim")

        return dependencies

    def _discover_lambda_dependencies(
        self, vpc_id: str, subnet_ids: List[str], service_name: str
    ) -> List[ResourceDependency]:
        """Discover Lambda function dependencies"""
        dependencies = []

        try:
            # Get Lambda functions
            response = self.lambda_client.list_functions()
            functions = response.get("Functions", [])

            for func in functions:
                vpc_config = func.get("VpcConfig", {})
                func_vpc_id = vpc_config.get("VpcId")
                func_subnet_ids = vpc_config.get("SubnetIds", [])

                if func_vpc_id != vpc_id:
                    continue

                # Check subnet overlap
                subnet_overlap = set(func_subnet_ids) & set(subnet_ids)
                if not subnet_overlap:
                    continue

                # Check if function likely uses the endpoint service
                # (Simplified: assume functions in VPC use VPC endpoints)
                production = self._is_production_resource([], func_vpc_id)

                dependencies.append(
                    ResourceDependency(
                        resource_id=func["FunctionName"],
                        resource_type="Lambda",
                        service_name="lambda",
                        endpoint_id="",
                        vpc_id=vpc_id,
                        criticality=DependencyRisk.HIGH,
                        production_indicator=production,
                        dependency_type="API_CALL",
                    )
                )
        except Exception as e:
            self.console.print(f"[yellow]Warning: Lambda discovery failed: {e}[/yellow]", style="dim")

        return dependencies

    def _discover_ec2_dependencies(
        self, vpc_id: str, subnet_ids: List[str], security_group_ids: List[str], service_name: str
    ) -> List[ResourceDependency]:
        """Discover EC2 instance dependencies"""
        dependencies = []

        try:
            # Get EC2 instances in VPC
            response = self.ec2.describe_instances(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])

            for reservation in response.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    if instance["State"]["Name"] not in ["running", "stopped"]:
                        continue

                    instance_subnet = instance.get("SubnetId")
                    if instance_subnet not in subnet_ids:
                        continue

                    production = self._is_production_resource(instance.get("Tags", []), vpc_id)

                    dependencies.append(
                        ResourceDependency(
                            resource_id=instance["InstanceId"],
                            resource_type="EC2",
                            service_name="ec2",
                            endpoint_id="",
                            vpc_id=vpc_id,
                            criticality=DependencyRisk.MEDIUM,
                            production_indicator=production,
                            dependency_type="NETWORK_CONNECTIVITY",
                        )
                    )
        except Exception as e:
            self.console.print(f"[yellow]Warning: EC2 discovery failed: {e}[/yellow]", style="dim")

        return dependencies

    def _discover_ecs_dependencies(
        self, vpc_id: str, subnet_ids: List[str], service_name: str
    ) -> List[ResourceDependency]:
        """Discover ECS task dependencies"""
        dependencies = []

        try:
            # Get ECS clusters
            response = self.ecs.list_clusters()
            clusters = response.get("clusterArns", [])

            for cluster_arn in clusters:
                # Get tasks in cluster
                tasks_response = self.ecs.list_tasks(cluster=cluster_arn)
                task_arns = tasks_response.get("taskArns", [])

                if not task_arns:
                    continue

                # Get task details
                tasks_detail = self.ecs.describe_tasks(cluster=cluster_arn, tasks=task_arns)

                for task in tasks_detail.get("tasks", []):
                    # Check if task is in the VPC
                    # (Simplified: assume tasks in same VPC use VPC endpoints)
                    task_id = task["taskArn"].split("/")[-1]

                    production = False  # TODO: Check ECS service tags

                    dependencies.append(
                        ResourceDependency(
                            resource_id=task_id,
                            resource_type="ECS",
                            service_name="ecs",
                            endpoint_id="",
                            vpc_id=vpc_id,
                            criticality=DependencyRisk.MEDIUM,
                            production_indicator=production,
                            dependency_type="SERVICE_COMMUNICATION",
                        )
                    )
        except Exception as e:
            # ECS might not be enabled or tasks might not exist
            self.console.print(f"[dim]Note: ECS discovery skipped: {e}[/dim]", style="dim")

        return dependencies

    def _is_production_resource(self, tags: List[Dict], vpc_id: str) -> bool:
        """
        Determine if resource is production workload

        Indicators:
        - "Environment": "production" tag
        - "env": "prod" tag
        - VPC name contains "prod"
        """
        # Check resource tags
        for tag in tags:
            key = tag.get("Key", "").lower()
            value = tag.get("Value", "").lower()

            if key in ["environment", "env"] and "prod" in value:
                return True

        # Check VPC name
        try:
            vpc_response = self.ec2.describe_vpcs(VpcIds=[vpc_id])
            vpcs = vpc_response.get("Vpcs", [])
            if vpcs:
                vpc = vpcs[0]
                vpc_tags = vpc.get("Tags", [])
                for tag in vpc_tags:
                    if tag.get("Key") == "Name" and "prod" in tag.get("Value", "").lower():
                        return True
        except Exception:
            pass

        return False

    def _generate_dependency_signals(self, dependencies: List[ResourceDependency]) -> List[DependencySignal]:
        """Generate D1-D6 dependency signals"""
        signals = []

        # D1: Production workload
        if any(dep.production_indicator for dep in dependencies):
            signals.append(DependencySignal.D1_PRODUCTION_WORKLOAD)

        # D2: RDS database
        if any(dep.resource_type == "RDS" for dep in dependencies):
            signals.append(DependencySignal.D2_RDS_DATABASE)

        # D3: Lambda function
        if any(dep.resource_type == "Lambda" for dep in dependencies):
            signals.append(DependencySignal.D3_LAMBDA_FUNCTION)

        # D4: EC2 instance
        if any(dep.resource_type == "EC2" for dep in dependencies):
            signals.append(DependencySignal.D4_EC2_INSTANCE)

        # D5: Multi-service (>3 different services)
        service_types = set(dep.resource_type for dep in dependencies)
        if len(service_types) > 3:
            signals.append(DependencySignal.D5_MULTI_SERVICE)

        # D6: Non-production only
        if dependencies and not any(dep.production_indicator for dep in dependencies):
            signals.append(DependencySignal.D6_NON_PRODUCTION)

        return signals

    def _calculate_risk_level(
        self, signals: List[DependencySignal], dependencies: List[ResourceDependency]
    ) -> DependencyRisk:
        """Calculate overall risk level"""
        if not dependencies:
            return DependencyRisk.NONE

        if DependencySignal.D1_PRODUCTION_WORKLOAD in signals:
            return DependencyRisk.CRITICAL

        if any(s in signals for s in [DependencySignal.D2_RDS_DATABASE, DependencySignal.D3_LAMBDA_FUNCTION]):
            return DependencyRisk.HIGH

        if any(s in signals for s in [DependencySignal.D4_EC2_INSTANCE, DependencySignal.D5_MULTI_SERVICE]):
            return DependencyRisk.MEDIUM

        return DependencyRisk.LOW

    def _assess_deletion_safety(
        self, risk_level: DependencyRisk, production_workload: bool, dependencies: List[ResourceDependency]
    ) -> tuple[bool, Optional[str]]:
        """
        Assess if endpoint can be safely deleted

        Returns:
            (deletion_safe, deletion_blocker)
        """
        if risk_level == DependencyRisk.CRITICAL:
            return False, f"CRITICAL: Production workload dependency ({len(dependencies)} resources)"

        if risk_level == DependencyRisk.HIGH:
            db_count = sum(1 for d in dependencies if d.resource_type == "RDS")
            lambda_count = sum(1 for d in dependencies if d.resource_type == "Lambda")
            return False, f"HIGH RISK: {db_count} databases, {lambda_count} Lambda functions"

        if risk_level == DependencyRisk.MEDIUM:
            return False, f"MEDIUM RISK: Review {len(dependencies)} dependencies before deletion"

        if risk_level == DependencyRisk.LOW:
            return True, None  # Safe to delete with approval

        return True, None  # No dependencies

    def _generate_impact_summary(self, dependencies: List[ResourceDependency], risk_level: DependencyRisk) -> str:
        """Generate human-readable impact summary"""
        if not dependencies:
            return "No dependencies - safe to delete"

        summary_parts = []

        by_type = {}
        for dep in dependencies:
            by_type.setdefault(dep.resource_type, []).append(dep)

        for resource_type, deps in by_type.items():
            prod_count = sum(1 for d in deps if d.production_indicator)
            if prod_count > 0:
                summary_parts.append(f"{len(deps)} {resource_type} ({prod_count} production)")
            else:
                summary_parts.append(f"{len(deps)} {resource_type}")

        impact = ", ".join(summary_parts)
        return f"{risk_level.value.upper()}: {impact}"

    def display_analysis(self, analyses: List[EndpointDependencyAnalysis]) -> None:
        """Display dependency analysis in Rich table format"""
        if not analyses:
            self.console.print("[yellow]No VPC endpoints found[/yellow]")
            return

        table = create_table(title="VPC Endpoint Dependency Analysis", box_style="rounded")

        table.add_column("Endpoint ID", style="cyan", no_wrap=True)
        table.add_column("Service", style="bright_blue")
        table.add_column("Dependencies", justify="right", style="white")
        table.add_column("Risk", style="white")
        table.add_column("Production", style="white")
        table.add_column("Deletion Safe", style="white")
        table.add_column("Impact Summary", style="dim")

        for analysis in analyses:
            deletion_status = "✓ YES" if analysis.deletion_safe else "✗ NO"
            deletion_color = "green" if analysis.deletion_safe else "red"

            # Risk level color coding
            risk_colors = {
                DependencyRisk.CRITICAL: "bright_red bold",
                DependencyRisk.HIGH: "bright_yellow",
                DependencyRisk.MEDIUM: "yellow",
                DependencyRisk.LOW: "green",
                DependencyRisk.NONE: "dim",
            }
            risk_color = risk_colors.get(analysis.risk_level, "white")

            table.add_row(
                analysis.endpoint_id,
                analysis.service_name,
                str(analysis.dependency_count),
                f"[{risk_color}]{analysis.risk_level.value.upper()}[/{risk_color}]",
                "YES" if analysis.production_workload else "NO",
                f"[{deletion_color}]{deletion_status}[/{deletion_color}]",
                analysis.impact_summary,
            )

        self.console.print(table)

        # Summary statistics
        critical_count = sum(1 for a in analyses if a.risk_level == DependencyRisk.CRITICAL)
        blocked_count = sum(1 for a in analyses if not a.deletion_safe)
        safe_count = sum(1 for a in analyses if a.deletion_safe)

        summary_text = (
            f"[bold red]Critical Endpoints: {critical_count}[/bold red]\n"
            f"[bold yellow]Deletion Blocked: {blocked_count}[/bold yellow]\n"
            f"[bold green]Safe to Delete: {safe_count}[/bold green]\n"
            f"Total Endpoints: {len(analyses)}"
        )

        summary = create_panel(summary_text, title="Dependency Summary", border_style="blue")
        self.console.print(summary)


def create_endpoint_dependency_mapper(
    operational_profile: Optional[str] = None, region: Optional[str] = None
) -> VPCEndpointDependencyMapper:
    """Factory function to create VPC endpoint dependency mapper"""
    return VPCEndpointDependencyMapper(profile=operational_profile, region=region)
