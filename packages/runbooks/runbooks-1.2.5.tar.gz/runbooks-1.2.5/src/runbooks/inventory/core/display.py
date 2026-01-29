#!/usr/bin/env python3
"""
Enterprise Operations Display - Rich Tree Visualization
Runbooks v1.1.18

Business-oriented cloud operations menu with pre-calculated widths
Follows Track 3A alignment pattern from Track 3-7 implementation

PyPI Package Integration: Moved from scripts/ to src/ for package inclusion
"""

from rich.tree import Tree
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
import yaml
from pathlib import Path


# ============================================================================
# Task Context Classification
# ============================================================================

TASK_CONTEXT_MAPPING = {
    # Multi-Account LZ Only (requires MANAGEMENT_PROFILE + AWS Organizations)
    "multi_account_lz": {
        "icon": "🏢",
        "label": "Multi-Account LZ",
        "description": "Requires AWS Organizations and MANAGEMENT_PROFILE",
        "tasks": [
            "list-accounts",
            "draw-org",
            "check-landing-zone",
            "check-control-tower",
            "list-org-users",
            "find-lz-versions",
        ],
    },
    # Universal (works in single or multi-account contexts)
    "universal": {
        "icon": "🔄",
        "label": "Universal",
        "description": "Works in both single and multi-account contexts",
        "tasks": [
            "discover-ec2",
            "discover-rds",
            "discover-s3",
            "discover-lambda",
            "discover-workspaces",
            "list-resource-types",
            "enrich-costs",
            "enrich-activity",
            "enrich-ec2",
            "score-decommission",
            "pipeline-5-layer",
            "pipeline-5-layer-workspaces",
            "pipeline-summary",
            "validate-mcp",
            "validate-costs",
            "list-outputs",
        ],
    },
    # Context-Dependent (behavior changes based on profile availability)
    "context_dependent": {
        "icon": "⚙️",
        "label": "Context-Dependent",
        "description": "Behavior adapts based on available profiles",
        "tasks": ["enrich-accounts"],
    },
    # Workflow Templates (explicit workflow orchestration)
    "workflow": {
        "icon": "📋",
        "label": "Workflow",
        "description": "End-to-end workflow orchestration",
        "tasks": ["workflow-single-account", "workflow-multi-account"],
    },
    # Utility (context-independent operations)
    "utility": {
        "icon": "🛠️",
        "label": "Utility",
        "description": "Context-independent utility operations",
        "tasks": ["clean-outputs", "show-profiles"],
    },
}


def get_task_context(task_name: str) -> tuple[str, str]:
    """
    Determine task context classification.

    Args:
        task_name: Name of the task from Taskfile.inventory.yaml

    Returns:
        Tuple of (icon, label) for the task context
    """
    for context_type, config in TASK_CONTEXT_MAPPING.items():
        if task_name in config["tasks"]:
            return config["icon"], config["label"]

    # Default to universal for unmapped tasks
    return "🔄", "Universal"


def load_taskfile_operations():
    """Load operations dynamically from Taskfile.inventory.yaml (single source of truth)"""
    # Try multiple possible locations for Taskfile.inventory.yaml
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent
        / "Taskfile.inventory.yaml",  # From src/runbooks/inventory/core/
        Path.cwd() / "Taskfile.inventory.yaml",  # From current working directory
        Path(__file__).parent.parent / "Taskfile.inventory.yaml",  # Fallback
    ]

    taskfile_path = None
    for path in possible_paths:
        if path.exists():
            taskfile_path = path
            break

    if not taskfile_path:
        print(f"[red]Error: Taskfile.inventory.yaml not found in any expected location[/red]")
        return []

    try:
        with open(taskfile_path, "r") as f:
            taskfile = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"[red]Error parsing Taskfile.inventory.yaml: {e}[/red]")
        return []

    operations = []
    for task_name, task_data in taskfile.get("tasks", {}).items():
        if task_name == "default":
            continue

        operations.append(
            {
                "name": task_name,
                "description": task_data.get("desc", "No description"),
            }
        )

    return operations


def create_operations_tree():
    """Create Rich Tree showing all operations by category"""

    console = Console()

    # Category mapping for business-oriented grouping
    CATEGORY_MAPPING = {
        "Discovery Operations": [
            "discover-ec2",
            "discover-rds",
            "discover-s3",
            "discover-lambda",
            "discover-workspaces",
            "list-resource-types",
        ],
        "Organizations Operations": [
            "list-accounts",
            "draw-org",
            "check-landing-zone",
            "check-control-tower",
            "list-org-users",
            "find-lz-versions",
        ],
        "Cost & Account Enrichment": ["enrich-accounts", "enrich-costs"],
        "Activity & Scoring Operations": ["enrich-activity", "enrich-ec2", "score-decommission"],
        "Pipeline Operations": ["pipeline-5-layer", "pipeline-5-layer-workspaces", "pipeline-summary"],
        "Validation Operations": ["validate-mcp", "validate-costs"],
        "Workflow Templates": ["workflow-single-account", "workflow-multi-account"],
        "Utility Operations": ["clean-outputs", "show-profiles", "list-outputs"],
    }

    # Load all operations dynamically
    all_operations = load_taskfile_operations()
    operations_by_name = {op["name"]: op for op in all_operations}

    # Main tree
    tree = Tree("[bold cyan]Runbooks - Inventory Module Operations[/bold cyan]", guide_style="bright_blue")

    # Organize by category
    for category, task_names in CATEGORY_MAPPING.items():
        # Filter to only tasks that exist in Taskfile
        existing_tasks = [t for t in task_names if t in operations_by_name]

        if not existing_tasks:
            continue

        category_branch = tree.add(f"[bold yellow]{category}[/bold yellow] ({len(existing_tasks)} operations)")

        # Create table for this category
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Task Name", style="cyan", width=35)
        table.add_column("Description", style="white", width=60)

        for task_name in existing_tasks:
            op = operations_by_name[task_name]

            # Get task context classification
            context_icon, context_label = get_task_context(task_name)

            # Highlight deprecated tasks
            if "DEPRECATED" in op["description"].upper() or task_name.startswith("best-practice-"):
                # Deprecated tasks: yellow with icon prefix
                task_display = f"[yellow]{context_icon} {task_name}[/yellow]"
                desc_display = f"[dim]{op['description']}[/dim]"
            else:
                # Regular tasks: icon prefix + context label in description
                task_display = f"{context_icon} {task_name}"
                desc_display = f"{op['description']} [dim cyan]({context_label})[/dim cyan]"

            table.add_row(task_display, desc_display)

        category_branch.add(table)

    # Add summary panel
    total_tasks = len(all_operations)
    categorized_tasks = sum(len([t for t in tasks if t in operations_by_name]) for tasks in CATEGORY_MAPPING.values())

    # Calculate context distribution
    context_counts = {}
    for op in all_operations:
        _, context_label = get_task_context(op["name"])
        context_counts[context_label] = context_counts.get(context_label, 0) + 1

    summary = Panel(
        f"[green]Total Operations: {total_tasks}[/green]\n"
        f"[cyan]Categorized: {categorized_tasks}[/cyan]\n"
        f"[yellow]Uncategorized: {total_tasks - categorized_tasks}[/yellow]\n\n"
        f"[bold white]Context Legend:[/bold white]\n"
        f"🏢 Multi-Account LZ ({context_counts.get('Multi-Account LZ', 0)})  "
        f"🔄 Universal ({context_counts.get('Universal', 0)})\n"
        f"⚙️ Context-Dependent ({context_counts.get('Context-Dependent', 0)})  "
        f"📋 Workflow ({context_counts.get('Workflow', 0)})  "
        f"🛠️ Utility ({context_counts.get('Utility', 0)})",
        title="Summary & Legend",
        border_style="green",
    )
    tree.add(summary)

    return tree


def show_operations_tree():
    """
    Display the operations tree for integration with CLI help.

    This is the main entry point for runbooks inventory --help integration.
    """
    tree = create_operations_tree()
    console = Console()
    console.print(tree)


def display_operations():
    """Display the enterprise operations menu with usage instructions"""
    console = Console()

    # Load operations
    all_operations = load_taskfile_operations()

    # Display banner
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Runbooks[/bold cyan]\n"
            "[white]Enterprise Operations Display[/white]\n"
            f"[dim]Taskfile.inventory.yaml v1.1.18 ({len(all_operations)} operations)[/dim]",
            border_style="cyan",
        )
    )
    console.print("\n")

    # Display operations tree
    tree = create_operations_tree()
    console.print(tree)

    console.print("\n")
    console.print("[dim]💡 Run 'task --taskfile Taskfile.inventory.yaml <operation-name>' to execute[/dim]")
    console.print("[dim]💡 Run 'task --taskfile Taskfile.inventory.yaml --list-all' to see all tasks[/dim]")
    console.print("\n")


if __name__ == "__main__":
    display_operations()
