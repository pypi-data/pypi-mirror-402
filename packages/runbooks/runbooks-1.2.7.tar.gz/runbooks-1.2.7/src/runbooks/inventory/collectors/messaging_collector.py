"""
AWS Messaging Services Collector - SQS & SNS Discovery

This module provides discovery capabilities for AWS messaging services including:
- SQS (Simple Queue Service) queues
- SNS (Simple Notification Service) topics

Strategic Alignment:
- KISS Principle: Simple, focused messaging service discovery
- DRY Principle: Reusable collector pattern following BaseResourceCollector
- Enterprise Standards: Rich CLI output, error handling, multi-region support

Business Value:
- Messaging cost optimization
- Dead letter queue analysis
- Unused topic/queue cleanup
- Subscription validation
"""

import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Any, Optional
from loguru import logger

from runbooks.common.rich_utils import print_info, print_success, print_error, print_warning


class MessagingCollector:
    """
    AWS Messaging Services Collector for SQS and SNS.

    Features:
    - SQS queue discovery with attributes (messages, retention, DLQ)
    - SNS topic discovery with attributes (subscriptions, display name)
    - Multi-region support
    - CSV and JSON export formats
    - Error handling with graceful degradation
    """

    def __init__(self, profile: str = None, region: str = "ap-southeast-2"):
        """
        Initialize the messaging collector.

        Args:
            profile: AWS profile name (uses default if None)
            region: AWS region (default: ap-southeast-2)
        """
        self.profile = profile
        self.region = region

        # Initialize AWS session
        if profile:
            self.session = boto3.Session(profile_name=profile, region_name=region)
        else:
            self.session = boto3.Session(region_name=region)

        # Initialize service clients
        self.sqs_client = self.session.client("sqs", region_name=region)
        self.sns_client = self.session.client("sns", region_name=region)

        logger.debug(f"MessagingCollector initialized (profile={profile}, region={region})")

    def collect_sqs_queues(self) -> List[Dict[str, Any]]:
        """
        Discover all SQS queues in the region.

        Returns:
            List of queue dictionaries with attributes

        Each queue includes:
        - QueueUrl: Full queue URL
        - QueueName: Extracted queue name
        - ApproximateNumberOfMessages: Current message count
        - MessageRetentionPeriod: Retention period in seconds
        - VisibilityTimeout: Visibility timeout in seconds
        - DelaySeconds: Delivery delay in seconds
        - RedrivePolicy: Dead letter queue configuration (if exists)
        """
        queues = []

        try:
            print_info("Discovering SQS queues...")

            # List all queue URLs
            response = self.sqs_client.list_queues()
            queue_urls = response.get("QueueUrls", [])

            if not queue_urls:
                print_warning("No SQS queues found in region")
                return []

            # Get attributes for each queue
            for queue_url in queue_urls:
                try:
                    # Extract queue name from URL
                    queue_name = queue_url.split("/")[-1]

                    # Get queue attributes
                    attrs_response = self.sqs_client.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=[
                            "ApproximateNumberOfMessages",
                            "MessageRetentionPeriod",
                            "VisibilityTimeout",
                            "DelaySeconds",
                            "RedrivePolicy",
                            "QueueArn",
                        ],
                    )

                    attributes = attrs_response.get("Attributes", {})

                    # Build queue info
                    queue_info = {
                        "QueueUrl": queue_url,
                        "QueueName": queue_name,
                        "QueueArn": attributes.get("QueueArn", ""),
                        "ApproximateNumberOfMessages": int(attributes.get("ApproximateNumberOfMessages", 0)),
                        "MessageRetentionPeriod": int(attributes.get("MessageRetentionPeriod", 0)),
                        "VisibilityTimeout": int(attributes.get("VisibilityTimeout", 0)),
                        "DelaySeconds": int(attributes.get("DelaySeconds", 0)),
                        "RedrivePolicy": attributes.get("RedrivePolicy", "None"),
                        "Region": self.region,
                        "Profile": self.profile or "default",
                    }

                    queues.append(queue_info)
                    logger.debug(f"Discovered SQS queue: {queue_name}")

                except ClientError as e:
                    logger.warning(f"Failed to get attributes for queue {queue_url}: {e}")
                    continue

            print_success(f"Found {len(queues)} SQS queues")

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                print_error("Access denied to SQS - check IAM permissions")
            else:
                print_error(f"SQS API error: {e}")
            logger.error(f"SQS collection failed: {e}")

        return queues

    def collect_sns_topics(self) -> List[Dict[str, Any]]:
        """
        Discover all SNS topics in the region.

        Returns:
            List of topic dictionaries with attributes

        Each topic includes:
        - TopicArn: Full topic ARN
        - TopicName: Extracted topic name
        - DisplayName: Human-readable display name
        - SubscriptionsConfirmed: Number of confirmed subscriptions
        - SubscriptionsPending: Number of pending subscriptions
        - SubscriptionsDeleted: Number of deleted subscriptions
        """
        topics = []

        try:
            print_info("Discovering SNS topics...")

            # List all topics with pagination support
            paginator = self.sns_client.get_paginator("list_topics")

            topic_count = 0
            for page in paginator.paginate():
                for topic in page.get("Topics", []):
                    try:
                        topic_arn = topic["TopicArn"]
                        topic_name = topic_arn.split(":")[-1]

                        # Get topic attributes
                        attrs_response = self.sns_client.get_topic_attributes(TopicArn=topic_arn)

                        attributes = attrs_response.get("Attributes", {})

                        # Build topic info
                        topic_info = {
                            "TopicArn": topic_arn,
                            "TopicName": topic_name,
                            "DisplayName": attributes.get("DisplayName", topic_name),
                            "SubscriptionsConfirmed": int(attributes.get("SubscriptionsConfirmed", 0)),
                            "SubscriptionsPending": int(attributes.get("SubscriptionsPending", 0)),
                            "SubscriptionsDeleted": int(attributes.get("SubscriptionsDeleted", 0)),
                            "Owner": attributes.get("Owner", ""),
                            "Region": self.region,
                            "Profile": self.profile or "default",
                        }

                        topics.append(topic_info)
                        topic_count += 1
                        logger.debug(f"Discovered SNS topic: {topic_name}")

                    except ClientError as e:
                        logger.warning(f"Failed to get attributes for topic {topic_arn}: {e}")
                        continue

            if topic_count == 0:
                print_warning("No SNS topics found in region")
            else:
                print_success(f"Found {topic_count} SNS topics")

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                print_error("Access denied to SNS - check IAM permissions")
            else:
                print_error(f"SNS API error: {e}")
            logger.error(f"SNS collection failed: {e}")

        return topics

    def collect_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect all messaging resources (SQS + SNS).

        Returns:
            Dictionary with 'sqs_queues' and 'sns_topics' keys

        Example:
            {
                'sqs_queues': [{'QueueName': 'my-queue', ...}, ...],
                'sns_topics': [{'TopicName': 'my-topic', ...}, ...]
            }
        """
        results = {"sqs_queues": [], "sns_topics": []}

        try:
            # Collect SQS queues
            results["sqs_queues"] = self.collect_sqs_queues()

            # Collect SNS topics
            results["sns_topics"] = self.collect_sns_topics()

            # Summary
            total_resources = len(results["sqs_queues"]) + len(results["sns_topics"])
            print_success(f"\n✅ Messaging discovery complete: {total_resources} total resources")
            print_info(f"   - SQS Queues: {len(results['sqs_queues'])}")
            print_info(f"   - SNS Topics: {len(results['sns_topics'])}")

        except Exception as e:
            print_error(f"Messaging collection failed: {e}")
            logger.error(f"collect_all failed: {e}")
            raise

        return results


def collect_messaging(
    profile: Optional[str] = None,
    region: str = "ap-southeast-2",
    output_file: Optional[str] = None,
    output_format: str = "csv",
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function for messaging collection with file export.

    Args:
        profile: AWS profile name
        region: AWS region
        output_file: Output file path (CSV or JSON)
        output_format: Output format ('csv' or 'json')

    Returns:
        Dictionary with messaging resources

    Example:
        resources = collect_messaging(
            profile="ops-profile",
            region="ap-southeast-2",
            output_file="messaging.csv",
            output_format="csv"
        )
    """
    collector = MessagingCollector(profile=profile, region=region)
    results = collector.collect_all()

    # Export to file if requested
    if output_file:
        from pathlib import Path
        import pandas as pd
        import json

        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "csv":
            # Flatten results for CSV export
            all_resources = []

            for queue in results["sqs_queues"]:
                queue["ResourceType"] = "SQS_Queue"
                all_resources.append(queue)

            for topic in results["sns_topics"]:
                topic["ResourceType"] = "SNS_Topic"
                all_resources.append(topic)

            if all_resources:
                df = pd.DataFrame(all_resources)
                df.to_csv(output_file, index=False)
                print_success(f"Exported {len(all_resources)} resources to {output_file}")
            else:
                print_warning("No resources to export")

        elif output_format == "json":
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)

            total = len(results["sqs_queues"]) + len(results["sns_topics"])
            print_success(f"Exported {total} resources to {output_file} (JSON)")

    return results
