"""
External MCP Client for AWS Cost Explorer

This module provides MCP protocol integration for validating AWS cost data
via external MCP servers (e.g., awslabs.cost-explorer-mcp-server).

v1.1.23: 3-way validation architecture
v1.1.26: Synchronous wrappers for notebook compatibility (P0-3)
         - get_cost_data_sync(): Simple synchronous function
         - SyncMCPWrapper: Class-based synchronous interface
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class ExternalMCPCostExplorerClient:
    """
    MCP protocol client for AWS Cost Explorer external validation.

    Communicates with awslabs.cost-explorer-mcp-server via MCP protocol
    for independent cost data validation.
    """

    def __init__(self, profile: Optional[str] = None, region: str = "ap-southeast-2"):
        """
        Initialize external MCP client.

        Args:
            profile: AWS profile name to use (defaults to AWS_PROFILE env var)
            region: AWS region (defaults to ap-southeast-2)
        """
        self.profile = profile or os.getenv("AWS_PROFILE", "default")
        self.region = region
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Connect to the external MCP server."""
        # Configure MCP server parameters
        server_params = StdioServerParameters(
            command="uvx",
            args=["awslabs.cost-explorer-mcp-server@latest"],
            env={
                "AWS_PROFILE": self.profile,
                "AWS_REGION": self.region,
                "FASTMCP_LOG_LEVEL": "ERROR",
            },
        )

        # Create stdio client and session
        read, write = await stdio_client(server_params)
        self.session = ClientSession(read, write)

        # Initialize the session
        await self.session.initialize()

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            # MCP session cleanup happens automatically
            self.session = None

    async def get_cost_data(self, start_date: str, end_date: str, granularity: str = "MONTHLY") -> Dict[str, Any]:
        """
        Get cost data via MCP protocol.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY or MONTHLY

        Returns:
            MCP cost data response
        """
        if not self.session:
            raise RuntimeError("MCP client not connected. Use async context manager.")

        try:
            # List available tools
            tools_result = await self.session.list_tools()

            # Find the get_cost_and_usage tool
            cost_tool = None
            for tool in tools_result.tools:
                if tool.name == "get_cost_and_usage":
                    cost_tool = tool
                    break

            if not cost_tool:
                return {
                    "status": "error",
                    "error": "get_cost_and_usage tool not found in MCP server",
                    "timestamp": datetime.now().isoformat(),
                }

            # Call the tool
            result = await self.session.call_tool(
                name="get_cost_and_usage",
                arguments={
                    "start_date": start_date,
                    "end_date": end_date,
                    "granularity": granularity,
                    "metrics": ["BlendedCost"],
                    "group_by": [{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
                },
            )

            # Parse the result
            if result.content:
                # MCP returns content as a list of text/JSON blocks
                for content_block in result.content:
                    if hasattr(content_block, "text"):
                        # Parse JSON response
                        cost_data = json.loads(content_block.text)
                        return {
                            "status": "success",
                            "data": cost_data,
                            "timestamp": datetime.now().isoformat(),
                            "mcp_source": "external_awslabs_cost_explorer",
                            "profile": self.profile,
                        }

            return {"status": "error", "error": "No content in MCP response", "timestamp": datetime.now().isoformat()}

        except Exception as e:
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}


async def get_external_mcp_cost_data(
    start_date: str, end_date: str, profile: Optional[str] = None, region: str = "ap-southeast-2"
) -> Dict[str, Any]:
    """
    Helper function to get cost data from external MCP server.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        profile: AWS profile name
        region: AWS region

    Returns:
        Cost data response from MCP server
    """
    async with ExternalMCPCostExplorerClient(profile=profile, region=region) as client:
        return await client.get_cost_data(start_date, end_date)


# ============================================================================
# Synchronous Wrappers for Notebook Compatibility (v1.1.26)
# ============================================================================


def get_cost_data_sync(
    start_date: str,
    end_date: str,
    profile: Optional[str] = None,
    region: str = "ap-southeast-2",
    cost_metric: str = "BlendedCost",
) -> Dict[str, Any]:
    """
    Synchronous wrapper for MCP cost data retrieval (notebook-compatible).

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        profile: AWS profile name
        region: AWS region
        cost_metric: BlendedCost (default), UnblendedCost, or AmortizedCost

    Returns:
        Cost data response from MCP server

    Example:
        >>> # Use in Jupyter notebooks (synchronous context)
        >>> result = get_cost_data_sync('2025-11-12', '2025-11-19',
        ...                             profile='my-profile',
        ...                             cost_metric='BlendedCost')
        >>> print(f"Total cost: {result['data']['total_cost']}")
    """
    return asyncio.run(get_external_mcp_cost_data(start_date, end_date, profile, region))


class SyncMCPWrapper:
    """
    Synchronous wrapper for ExternalMCPCostExplorerClient (notebook-compatible).

    Provides synchronous interface to MCP Cost Explorer for use in:
    - Jupyter notebooks
    - Synchronous scripts
    - 4-way validation frameworks

    Example:
        >>> wrapper = SyncMCPWrapper(profile='my-profile')
        >>> result = wrapper.get_cost_data('2025-11-12', '2025-11-19')
        >>> print(f"Accuracy: {result['accuracy']}")
    """

    def __init__(self, profile: Optional[str] = None, region: str = "ap-southeast-2"):
        """
        Initialize synchronous MCP wrapper.

        Args:
            profile: AWS profile name
            region: AWS region (default: ap-southeast-2)
        """
        self.profile = profile
        self.region = region

    def get_cost_data(
        self, start_date: str, end_date: str, cost_metric: str = "BlendedCost", granularity: str = "DAILY"
    ) -> Dict[str, Any]:
        """
        Get cost data synchronously (notebook-compatible).

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cost_metric: BlendedCost, UnblendedCost, or AmortizedCost
            granularity: DAILY or MONTHLY

        Returns:
            MCP cost data response with status and data
        """
        return asyncio.run(
            get_external_mcp_cost_data(
                start_date=start_date, end_date=end_date, profile=self.profile, region=self.region
            )
        )
