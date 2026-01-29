"""
Cost Visualization Utilities - Rich Tree Hierarchies

Provides reusable tree visualization functions for FinOps cost analysis.
Reuses proven VPC patterns for consistent UX across EC2/WorkSpaces/VPC modules.

Pattern: Account → Region → Resources with cost rollups

Integration Example for Jupyter Notebooks
==========================================

Usage in notebooks/compute/ec2-enriched-analysis.ipynb:

```python
# Cell 5: Cost Summary with Rich Tree
from runbooks.finops.cost_visualization import display_ec2_cost_tree
from rich.console import Console

console = Console()

# Display hierarchical cost tree
display_ec2_cost_tree(ec2_df.to_dict('records'), console)

# Display cost comparison table
from runbooks.finops.cost_visualization import display_cost_comparison_table

ec2_costs = {
    'MUST': ec2_df[ec2_df['decommission_tier'] == 'MUST']['monthly_cost'].sum(),
    'SHOULD': ec2_df[ec2_df['decommission_tier'] == 'SHOULD']['monthly_cost'].sum(),
    'COULD': ec2_df[ec2_df['decommission_tier'] == 'COULD']['monthly_cost'].sum(),
    'KEEP': ec2_df[ec2_df['decommission_tier'] == 'KEEP']['monthly_cost'].sum()
}

workspaces_costs = {
    'MUST': workspaces_df[workspaces_df['decommission_tier'] == 'MUST']['monthly_cost'].sum(),
    'SHOULD': workspaces_df[workspaces_df['decommission_tier'] == 'SHOULD']['monthly_cost'].sum(),
    'COULD': workspaces_df[workspaces_df['decommission_tier'] == 'COULD']['monthly_cost'].sum(),
    'KEEP': workspaces_df[workspaces_df['decommission_tier'] == 'KEEP']['monthly_cost'].sum()
}

display_cost_comparison_table(ec2_costs, workspaces_costs, console)
```

This reuses the proven VPC pattern for consistent UX across FinOps modules.
"""

from collections import defaultdict
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.tree import Tree


def display_ec2_cost_tree(ec2_data: List[Dict], console: Optional[Console] = None, top_n_per_region: int = 5) -> None:
    """
    Display EC2 costs in hierarchical tree structure.

    Pattern reused from: notebooks/vpc/vpce-cleanup-manager-operations.ipynb

    Hierarchy:
    - Account (total cost)
      - Region (count + cost)
        - Top N instances (sorted by cost desc)

    Args:
        ec2_data: List of EC2 resource dictionaries
        console: Rich console (creates if None)
        top_n_per_region: Show top N most expensive instances per region

    Example:
        >>> from runbooks.finops.cost_visualization import display_ec2_cost_tree
        >>> display_ec2_cost_tree(ec2_df.to_dict('records'))

        💰 EC2 Cost Analysis
        ├── 🏢 Account: 123456789012 | $12,345.67/mo
        │   ├── 🌎 Region: ap-southeast-2 | 45 instances | $8,234.56/mo
        │   │   ├── 🖥️  i-abc123 (m5.xlarge) | $156.00/mo | MUST
        │   │   ├── 🖥️  i-def456 (t3.large) | $142.00/mo | SHOULD
        │   │   └── ...
        │   └── 🌎 Region: ap-southeast-6 | 23 instances | $4,111.11/mo
        └── 🏢 Account: 987654321098 | $5,678.90/mo
    """
    if console is None:
        console = Console()

    # Group by account → region
    by_account: Dict[str, Dict] = defaultdict(lambda: {"account_name": "", "regions": defaultdict(list)})

    for instance in ec2_data:
        account_id = instance.get("account_id", "Unknown")
        account_name = instance.get("account_name", account_id)
        region = instance.get("region", "Unknown")

        by_account[account_id]["account_name"] = account_name
        by_account[account_id]["regions"][region].append(instance)

    # Build tree
    root = Tree("💰 [bold cyan]EC2 Cost Analysis[/bold cyan]")

    # Sort accounts by cost (descending)
    account_costs = {}
    for account_id, account_data in by_account.items():
        total_cost = sum(
            [
                inst.get("monthly_cost", 0)
                for region_instances in account_data["regions"].values()
                for inst in region_instances
            ]
        )
        account_costs[account_id] = total_cost

    sorted_accounts = sorted(by_account.items(), key=lambda x: account_costs[x[0]], reverse=True)

    for account_id, account_data in sorted_accounts:
        account_name = account_data.get("account_name", account_id)
        account_cost = account_costs[account_id]

        account_node = root.add(
            f"🏢 Account: [yellow]{account_name}[/yellow] ({account_id}) | [green]${account_cost:,.2f}/mo[/green]"
        )

        # Sort regions by cost (descending)
        regions = account_data["regions"]
        region_costs = {
            region: sum([inst.get("monthly_cost", 0) for inst in instances]) for region, instances in regions.items()
        }
        sorted_regions = sorted(regions.items(), key=lambda x: region_costs[x[0]], reverse=True)

        for region, instances in sorted_regions:
            region_cost = region_costs[region]
            region_node = account_node.add(
                f"🌎 Region: [cyan]{region}[/cyan] | "
                f"[yellow]{len(instances)} instances[/yellow] | "
                f"[green]${region_cost:,.2f}/mo[/green]"
            )

            # Top N most expensive instances
            sorted_instances = sorted(instances, key=lambda x: x.get("monthly_cost", 0), reverse=True)[
                :top_n_per_region
            ]

            for inst in sorted_instances:
                instance_id = inst.get("instance_id", "Unknown")
                instance_type = inst.get("instance_type", "Unknown")
                monthly_cost = inst.get("monthly_cost", 0)
                tier = inst.get("decommission_tier", "N/A")

                # Color tier
                tier_colors = {"MUST": "red bold", "SHOULD": "yellow", "COULD": "cyan", "KEEP": "green"}
                tier_color = tier_colors.get(tier, "white")

                region_node.add(
                    f"🖥️  {instance_id} ([blue]{instance_type}[/blue]) | "
                    f"[green]${monthly_cost:,.2f}/mo[/green] | "
                    f"[{tier_color}]{tier}[/{tier_color}]"
                )

            # Show count if truncated
            if len(instances) > top_n_per_region:
                remaining = len(instances) - top_n_per_region
                region_node.add(f"... and {remaining} more instances")

    console.print(root)


def display_workspaces_cost_tree(
    workspaces_data: List[Dict], console: Optional[Console] = None, top_n_per_region: int = 5
) -> None:
    """
    Display WorkSpaces costs in hierarchical tree structure.

    Pattern reused from: notebooks/vpc/vpce-cleanup-manager-operations.ipynb

    Hierarchy:
    - Account (total cost)
      - Region (count + cost)
        - Top N WorkSpaces (sorted by cost desc)

    Args:
        workspaces_data: List of WorkSpaces resource dictionaries
        console: Rich console (creates if None)
        top_n_per_region: Show top N most expensive WorkSpaces per region

    Example:
        >>> from runbooks.finops.cost_visualization import display_workspaces_cost_tree
        >>> display_workspaces_cost_tree(workspaces_df.to_dict('records'))

        🖥️ WorkSpaces Cost Analysis
        ├── 🏢 Account: 123456789012 | $8,765.43/mo
        │   ├── 🌎 Region: ap-southeast-2 | 34 WorkSpaces | $6,234.56/mo
        │   │   ├── 💼 ws-abc123 (user@example.com) | STANDARD | $53.95/mo | MUST
        │   │   ├── 💼 ws-def456 (admin@example.com) | PERFORMANCE | $87.00/mo | SHOULD
        │   │   └── ...
        │   └── 🌎 Region: ap-southeast-2 | 12 WorkSpaces | $2,530.87/mo
        └── 🏢 Account: 987654321098 | $3,456.78/mo
    """
    if console is None:
        console = Console()

    # Group by account → region
    by_account: Dict[str, Dict] = defaultdict(lambda: {"account_name": "", "regions": defaultdict(list)})

    for workspace in workspaces_data:
        account_id = workspace.get("account_id", "Unknown")
        account_name = workspace.get("account_name", account_id)
        region = workspace.get("region", "Unknown")

        by_account[account_id]["account_name"] = account_name
        by_account[account_id]["regions"][region].append(workspace)

    # Build tree
    root = Tree("🖥️ [bold cyan]WorkSpaces Cost Analysis[/bold cyan]")

    # Sort accounts by cost (descending)
    account_costs = {}
    for account_id, account_data in by_account.items():
        total_cost = sum(
            [
                ws.get("monthly_cost", 0)
                for region_workspaces in account_data["regions"].values()
                for ws in region_workspaces
            ]
        )
        account_costs[account_id] = total_cost

    sorted_accounts = sorted(by_account.items(), key=lambda x: account_costs[x[0]], reverse=True)

    for account_id, account_data in sorted_accounts:
        account_name = account_data.get("account_name", account_id)
        account_cost = account_costs[account_id]

        account_node = root.add(
            f"🏢 Account: [yellow]{account_name}[/yellow] ({account_id}) | [green]${account_cost:,.2f}/mo[/green]"
        )

        # Sort regions by cost (descending)
        regions = account_data["regions"]
        region_costs = {
            region: sum([ws.get("monthly_cost", 0) for ws in workspaces]) for region, workspaces in regions.items()
        }
        sorted_regions = sorted(regions.items(), key=lambda x: region_costs[x[0]], reverse=True)

        for region, workspaces in sorted_regions:
            region_cost = region_costs[region]
            region_node = account_node.add(
                f"🌎 Region: [cyan]{region}[/cyan] | "
                f"[yellow]{len(workspaces)} WorkSpaces[/yellow] | "
                f"[green]${region_cost:,.2f}/mo[/green]"
            )

            # Top N most expensive WorkSpaces
            sorted_workspaces = sorted(workspaces, key=lambda x: x.get("monthly_cost", 0), reverse=True)[
                :top_n_per_region
            ]

            for ws in sorted_workspaces:
                workspace_id = ws.get("workspace_id", "Unknown")
                username = ws.get("username", "Unknown")
                bundle_type = ws.get("bundle_type", "Unknown")
                monthly_cost = ws.get("monthly_cost", 0)
                tier = ws.get("decommission_tier", "N/A")

                # Color tier
                tier_colors = {"MUST": "red bold", "SHOULD": "yellow", "COULD": "cyan", "KEEP": "green"}
                tier_color = tier_colors.get(tier, "white")

                region_node.add(
                    f"💼 {workspace_id} ([blue]{username}[/blue]) | "
                    f"{bundle_type} | "
                    f"[green]${monthly_cost:,.2f}/mo[/green] | "
                    f"[{tier_color}]{tier}[/{tier_color}]"
                )

            # Show count if truncated
            if len(workspaces) > top_n_per_region:
                remaining = len(workspaces) - top_n_per_region
                region_node.add(f"... and {remaining} more WorkSpaces")

    console.print(root)


def display_cost_comparison_table(ec2_costs: Dict, workspaces_costs: Dict, console: Optional[Console] = None) -> None:
    """
    Display cost comparison table for EC2 vs WorkSpaces.

    Reuses VPC cost comparison pattern with tier breakdowns.

    Args:
        ec2_costs: EC2 cost breakdown by tier
        workspaces_costs: WorkSpaces cost breakdown by tier
        console: Rich console

    Example:
        >>> ec2_costs = {'MUST': 5000, 'SHOULD': 3000, 'COULD': 2000, 'KEEP': 10000}
        >>> workspaces_costs = {'MUST': 8000, 'SHOULD': 4000, 'COULD': 1000, 'KEEP': 7000}
        >>> display_cost_comparison_table(ec2_costs, workspaces_costs)
    """
    if console is None:
        console = Console()

    table = Table(title="💰 Cost Analysis by Decommission Tier", show_header=True)
    table.add_column("Tier", style="cyan", width=12)
    table.add_column("EC2 Monthly", style="green", justify="right")
    table.add_column("WorkSpaces Monthly", style="green", justify="right")
    table.add_column("Total Monthly", style="yellow", justify="right")
    table.add_column("Annual Impact", style="red bold", justify="right")

    tiers = ["MUST", "SHOULD", "COULD", "KEEP"]
    tier_emojis = {"MUST": "🔴", "SHOULD": "🟡", "COULD": "🟢", "KEEP": "⚪"}

    grand_total_monthly = 0

    for tier in tiers:
        ec2_cost = ec2_costs.get(tier, 0)
        ws_cost = workspaces_costs.get(tier, 0)
        total_monthly = ec2_cost + ws_cost
        total_annual = total_monthly * 12

        grand_total_monthly += total_monthly

        table.add_row(
            f"{tier_emojis[tier]} {tier}",
            f"${ec2_cost:,.2f}",
            f"${ws_cost:,.2f}",
            f"${total_monthly:,.2f}",
            f"${total_annual:,.2f}",
        )

    # Grand total row
    table.add_row(
        "📊 TOTAL",
        f"${sum(ec2_costs.values()):,.2f}",
        f"${sum(workspaces_costs.values()):,.2f}",
        f"${grand_total_monthly:,.2f}",
        f"[bold]${grand_total_monthly * 12:,.2f}[/bold]",
        style="bold white",
    )

    console.print(table)
