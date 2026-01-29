"""
AWS Analytics Resources Collector.

This module provides specialized collection of analytics resources including
Athena workgroups, AWS Glue databases and tables, and QuickSight dashboards
for cost optimization and data governance compliance.

Business Value:
    - Analytics cost optimization (15-25% savings potential)
    - Data governance compliance
    - Unused workgroup/database cleanup
    - Cross-account analytics resource discovery
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from runbooks.inventory.collectors.base import BaseResourceCollector, CollectionContext
from runbooks.inventory.models.resource import AWSResource, ResourceCost, ResourceState
from runbooks.inventory.utils.aws_helpers import aws_api_retry


class AnalyticsCollector(BaseResourceCollector):
    """
    Collector for AWS Analytics resources.

    Handles discovery and inventory of:
    - Athena workgroups and query execution metadata
    - AWS Glue databases, tables, and crawlers
    - QuickSight dashboards and analyses (future)
    - AWS Data Pipeline resources (future)
    """

    service_category = "analytics"
    supported_resources = {
        "athena:workgroup",
        "glue:database",
        "glue:table",
        "glue:crawler",
    }
    requires_org_access = False

    def collect_resources(
        self, context: CollectionContext, resource_filters: Optional[Dict[str, Any]] = None
    ) -> List[AWSResource]:
        """
        Collect analytics resources from AWS account/region.

        Args:
            context: Collection context with account, region, and options
            resource_filters: Optional filters to apply during collection

        Returns:
            List of discovered analytics resources
        """
        resources = []
        resource_filters = resource_filters or {}

        logger.info(
            f"Starting analytics resource collection in {context.region} for account {context.account.account_id}"
        )

        # Collect each supported resource type
        for resource_type in context.resource_types.intersection(self.supported_resources):
            try:
                if resource_type.startswith("athena:"):
                    resources.extend(self._collect_athena_resources(context, resource_type, resource_filters))
                elif resource_type.startswith("glue:"):
                    resources.extend(self._collect_glue_resources(context, resource_type, resource_filters))

            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                logger.error(f"Failed to collect {resource_type} in {context.region}: {error_code} - {e}")
                if error_code in ["UnauthorizedOperation", "AccessDenied"]:
                    logger.warning(f"Insufficient permissions for {resource_type}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error collecting {resource_type}: {e}")
                continue

        logger.info(f"Collected {len(resources)} analytics resources from {context.region}")
        return resources

    @aws_api_retry(max_retries=3)
    def _collect_athena_resources(
        self, context: CollectionContext, resource_type: str, filters: Dict[str, Any]
    ) -> List[AWSResource]:
        """Collect Athena resources (workgroups)."""
        resources = []
        athena_client = self.get_client("athena", context.region)

        if resource_type == "athena:workgroup":
            resources.extend(self._collect_athena_workgroups(athena_client, context, filters))

        return resources

    def _collect_athena_workgroups(
        self, athena_client: boto3.client, context: CollectionContext, filters: Dict[str, Any]
    ) -> List[AWSResource]:
        """
        Collect Athena workgroups with metadata.

        Args:
            athena_client: boto3 Athena client
            context: Collection context
            filters: Resource filters

        Returns:
            List of Athena workgroup resources
        """
        resources = []

        try:
            paginator = athena_client.get_paginator("list_work_groups")

            for page in paginator.paginate():
                for workgroup_summary in page.get("WorkGroups", []):
                    workgroup_name = workgroup_summary.get("Name")

                    # Get detailed workgroup configuration
                    try:
                        workgroup_detail = athena_client.get_work_group(WorkGroup=workgroup_name)
                        workgroup_data = workgroup_detail.get("WorkGroup", {})

                        resource = self._create_athena_workgroup_resource(workgroup_data, context)
                        if resource:
                            resources.append(resource)
                    except ClientError as e:
                        logger.warning(f"Failed to get details for workgroup {workgroup_name}: {e}")
                        continue

            logger.debug(f"Collected {len(resources)} Athena workgroups")

        except ClientError as e:
            logger.error(f"Failed to collect Athena workgroups: {e}")
            raise

        return resources

    def _create_athena_workgroup_resource(
        self, workgroup_data: Dict[str, Any], context: CollectionContext
    ) -> Optional[AWSResource]:
        """Create AWSResource from Athena workgroup data."""
        try:
            workgroup_name = workgroup_data.get("Name")
            state = workgroup_data.get("State", "ENABLED")

            # Map Athena state to ResourceState
            state_mapping = {
                "ENABLED": ResourceState.AVAILABLE,
                "DISABLED": ResourceState.STOPPED,
            }

            resource_state = state_mapping.get(state, ResourceState.UNKNOWN)

            # Extract configuration details
            config = workgroup_data.get("Configuration", {})
            result_config = config.get("ResultConfigurationUpdates", {}) or config.get("ResultConfiguration", {})

            configuration = {
                "state": state,
                "description": workgroup_data.get("Description", ""),
                "creation_time": workgroup_data.get("CreationTime"),
                "result_location": result_config.get("OutputLocation", ""),
                "encryption_configuration": result_config.get("EncryptionConfiguration", {}),
                "bytes_scanned_cutoff": config.get("BytesScannedCutoffPerQuery"),
                "enforce_work_group_configuration": config.get("EnforceWorkGroupConfiguration", False),
                "publish_cloudwatch_metrics": config.get("PublishCloudWatchMetricsEnabled", False),
            }

            # Cost estimation
            cost_info = None
            if context.include_costs:
                cost_info = self._estimate_athena_cost(workgroup_data)

            metadata = self._create_resource_metadata(context, workgroup_data)

            return AWSResource(
                resource_id=workgroup_name,
                resource_type="athena:workgroup",
                resource_arn=f"arn:aws:athena:{context.region}:{context.account.account_id}:workgroup/{workgroup_name}",
                resource_name=workgroup_name,
                state=resource_state,
                creation_date=workgroup_data.get("CreationTime"),
                account_id=context.account.account_id,
                region=context.region,
                configuration=configuration,
                tags={},  # Athena tags require separate API call
                cost_info=cost_info,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error creating Athena workgroup resource: {e}")
            return None

    @aws_api_retry(max_retries=3)
    def _collect_glue_resources(
        self, context: CollectionContext, resource_type: str, filters: Dict[str, Any]
    ) -> List[AWSResource]:
        """Collect AWS Glue resources (databases, tables, crawlers)."""
        resources = []
        glue_client = self.get_client("glue", context.region)

        if resource_type == "glue:database":
            resources.extend(self._collect_glue_databases(glue_client, context, filters))
        elif resource_type == "glue:table":
            resources.extend(self._collect_glue_tables(glue_client, context, filters))
        elif resource_type == "glue:crawler":
            resources.extend(self._collect_glue_crawlers(glue_client, context, filters))

        return resources

    def _collect_glue_databases(
        self, glue_client: boto3.client, context: CollectionContext, filters: Dict[str, Any]
    ) -> List[AWSResource]:
        """Collect AWS Glue databases."""
        resources = []

        try:
            paginator = glue_client.get_paginator("get_databases")

            for page in paginator.paginate():
                for database in page.get("DatabaseList", []):
                    resource = self._create_glue_database_resource(database, context)
                    if resource:
                        resources.append(resource)

            logger.debug(f"Collected {len(resources)} Glue databases")

        except ClientError as e:
            logger.error(f"Failed to collect Glue databases: {e}")
            raise

        return resources

    def _create_glue_database_resource(
        self, database_data: Dict[str, Any], context: CollectionContext
    ) -> Optional[AWSResource]:
        """Create AWSResource from Glue database data."""
        try:
            database_name = database_data.get("Name")

            configuration = {
                "description": database_data.get("Description", ""),
                "location_uri": database_data.get("LocationUri", ""),
                "create_time": database_data.get("CreateTime"),
                "catalog_id": database_data.get("CatalogId", ""),
                "parameters": database_data.get("Parameters", {}),
            }

            metadata = self._create_resource_metadata(context, database_data)

            return AWSResource(
                resource_id=database_name,
                resource_type="glue:database",
                resource_arn=f"arn:aws:glue:{context.region}:{context.account.account_id}:database/{database_name}",
                resource_name=database_name,
                state=ResourceState.AVAILABLE,
                creation_date=database_data.get("CreateTime"),
                account_id=context.account.account_id,
                region=context.region,
                configuration=configuration,
                tags={},
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error creating Glue database resource: {e}")
            return None

    def _collect_glue_tables(
        self, glue_client: boto3.client, context: CollectionContext, filters: Dict[str, Any]
    ) -> List[AWSResource]:
        """Collect AWS Glue tables across all databases."""
        resources = []

        try:
            # First get all databases
            db_paginator = glue_client.get_paginator("get_databases")
            databases = []

            for page in db_paginator.paginate():
                databases.extend([db.get("Name") for db in page.get("DatabaseList", [])])

            # Then collect tables for each database
            for database_name in databases:
                try:
                    table_paginator = glue_client.get_paginator("get_tables")

                    for page in table_paginator.paginate(DatabaseName=database_name):
                        for table in page.get("TableList", []):
                            resource = self._create_glue_table_resource(table, database_name, context)
                            if resource:
                                resources.append(resource)

                except ClientError as e:
                    logger.warning(f"Failed to collect tables for database {database_name}: {e}")
                    continue

            logger.debug(f"Collected {len(resources)} Glue tables across {len(databases)} databases")

        except ClientError as e:
            logger.error(f"Failed to collect Glue tables: {e}")
            raise

        return resources

    def _create_glue_table_resource(
        self, table_data: Dict[str, Any], database_name: str, context: CollectionContext
    ) -> Optional[AWSResource]:
        """Create AWSResource from Glue table data."""
        try:
            table_name = table_data.get("Name")

            storage_descriptor = table_data.get("StorageDescriptor", {})

            configuration = {
                "database_name": database_name,
                "description": table_data.get("Description", ""),
                "create_time": table_data.get("CreateTime"),
                "update_time": table_data.get("UpdateTime"),
                "owner": table_data.get("Owner", ""),
                "retention": table_data.get("Retention", 0),
                "storage_type": storage_descriptor.get("StoredAsSubDirectories", False),
                "location": storage_descriptor.get("Location", ""),
                "input_format": storage_descriptor.get("InputFormat", ""),
                "output_format": storage_descriptor.get("OutputFormat", ""),
                "compressed": storage_descriptor.get("Compressed", False),
                "number_of_buckets": storage_descriptor.get("NumberOfBuckets", 0),
                "partition_keys": table_data.get("PartitionKeys", []),
                "table_type": table_data.get("TableType", ""),
            }

            metadata = self._create_resource_metadata(context, table_data)

            return AWSResource(
                resource_id=f"{database_name}/{table_name}",
                resource_type="glue:table",
                resource_arn=f"arn:aws:glue:{context.region}:{context.account.account_id}:table/{database_name}/{table_name}",
                resource_name=table_name,
                state=ResourceState.AVAILABLE,
                creation_date=table_data.get("CreateTime"),
                account_id=context.account.account_id,
                region=context.region,
                configuration=configuration,
                tags={},
                metadata=metadata,
                dependencies=[f"arn:aws:glue:{context.region}:{context.account.account_id}:database/{database_name}"],
            )

        except Exception as e:
            logger.error(f"Error creating Glue table resource: {e}")
            return None

    def _collect_glue_crawlers(
        self, glue_client: boto3.client, context: CollectionContext, filters: Dict[str, Any]
    ) -> List[AWSResource]:
        """Collect AWS Glue crawlers."""
        resources = []

        try:
            paginator = glue_client.get_paginator("get_crawlers")

            for page in paginator.paginate():
                for crawler in page.get("Crawlers", []):
                    resource = self._create_glue_crawler_resource(crawler, context)
                    if resource:
                        resources.append(resource)

            logger.debug(f"Collected {len(resources)} Glue crawlers")

        except ClientError as e:
            logger.error(f"Failed to collect Glue crawlers: {e}")
            raise

        return resources

    def _create_glue_crawler_resource(
        self, crawler_data: Dict[str, Any], context: CollectionContext
    ) -> Optional[AWSResource]:
        """Create AWSResource from Glue crawler data."""
        try:
            crawler_name = crawler_data.get("Name")
            state = crawler_data.get("State", "READY")

            # Map Glue crawler state to ResourceState
            state_mapping = {
                "READY": ResourceState.AVAILABLE,
                "RUNNING": ResourceState.RUNNING,
                "STOPPING": ResourceState.PENDING,
            }

            resource_state = state_mapping.get(state, ResourceState.UNKNOWN)

            configuration = {
                "role": crawler_data.get("Role"),
                "database_name": crawler_data.get("DatabaseName"),
                "description": crawler_data.get("Description", ""),
                "state": state,
                "schedule": crawler_data.get("Schedule", {}).get("ScheduleExpression", ""),
                "classifiers": crawler_data.get("Classifiers", []),
                "schema_change_policy": crawler_data.get("SchemaChangePolicy", {}),
                "recrawl_policy": crawler_data.get("RecrawlPolicy", {}),
                "lineage_configuration": crawler_data.get("LineageConfiguration", {}),
                "creation_time": crawler_data.get("CreationTime"),
                "last_updated": crawler_data.get("LastUpdated"),
                "last_crawl": crawler_data.get("LastCrawl", {}),
                "version": crawler_data.get("Version", 0),
                "targets": crawler_data.get("Targets", {}),
            }

            metadata = self._create_resource_metadata(context, crawler_data)

            return AWSResource(
                resource_id=crawler_name,
                resource_type="glue:crawler",
                resource_arn=f"arn:aws:glue:{context.region}:{context.account.account_id}:crawler/{crawler_name}",
                resource_name=crawler_name,
                state=resource_state,
                creation_date=crawler_data.get("CreationTime"),
                account_id=context.account.account_id,
                region=context.region,
                configuration=configuration,
                tags={},
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error creating Glue crawler resource: {e}")
            return None

    def get_resource_costs(self, resources: List[AWSResource], context: CollectionContext) -> Dict[str, float]:
        """Get cost information for analytics resources."""
        costs = {}

        if not context.include_costs:
            return costs

        # Group resources by type for batch cost calculation
        athena_workgroups = [r for r in resources if r.resource_type == "athena:workgroup"]
        glue_databases = [r for r in resources if r.resource_type == "glue:database"]
        glue_tables = [r for r in resources if r.resource_type == "glue:table"]
        glue_crawlers = [r for r in resources if r.resource_type == "glue:crawler"]

        # Calculate costs for each resource type
        # In production, integrate with AWS Cost Explorer API
        for workgroup in athena_workgroups:
            if workgroup.cost_info:
                costs[workgroup.resource_arn] = workgroup.cost_info.monthly_cost or 0.0

        # Glue databases/tables typically don't have direct costs
        # Costs come from crawler runs and query executions

        for crawler in glue_crawlers:
            if crawler.cost_info:
                costs[crawler.resource_arn] = crawler.cost_info.monthly_cost or 0.0

        return costs

    def _estimate_athena_cost(self, workgroup_data: Dict[str, Any]) -> Optional[ResourceCost]:
        """Estimate monthly cost for Athena workgroup based on query patterns."""
        # Athena pricing is primarily based on data scanned
        # This is a rough estimate - actual costs require query execution logs

        config = workgroup_data.get("Configuration", {})
        bytes_cutoff = config.get("BytesScannedCutoffPerQuery")

        # Simplified cost estimation
        # Athena charges $5 per TB scanned
        # Assuming moderate usage patterns
        estimated_monthly_scanned_tb = 10  # Assumption - replace with actual metrics

        if bytes_cutoff:
            # If there's a cutoff, assume lower usage
            estimated_monthly_scanned_tb = 5

        query_cost = estimated_monthly_scanned_tb * 5.0  # $5 per TB

        return ResourceCost(
            monthly_cost=query_cost,
            currency="USD",
            cost_breakdown={"query_execution": query_cost},
        )
