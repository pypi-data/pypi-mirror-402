"""
VPC Notebook Visualizations - Enterprise Manager Dashboard Charts

This module provides matplotlib/plotly visualizations for VPC manager dashboards.
Extracted from vpc-manager-dashboard.ipynb with comprehensive error handling.

Strategic Context:
- Phase 3: Notebook refactoring - Extract visualization logic into reusable module
- Manager-friendly styling: Large fonts, clear legends, professional color schemes
- Comprehensive NaN guards: Prevent crashes on empty/invalid data
- Jupyter-optimized: matplotlib-based for seamless notebook integration

Chart Types:
1. Cost Bubble Chart: VPC cost analysis with classification color coding
2. Savings Waterfall: Cost reduction progression by category
3. Resource Heatmap: Resource utilization across VPCs
4. Implementation Gantt: Recommendation timeline visualization
5. Risk Matrix: Risk vs savings scatter plot
"""

from typing import List, Dict, Tuple, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import seaborn as sns
from decimal import Decimal

from runbooks.vpc.models import VPCAnalysis


class VPCNotebookVisualizations:
    """
    Enterprise-grade visualizations for VPC manager dashboard.

    All methods are static and return matplotlib Figure objects for Jupyter rendering.
    Comprehensive NaN guards prevent crashes on empty or invalid data.
    Professional styling optimized for manager-level presentations.
    """

    # Classification color scheme (matches business logic)
    CLASSIFICATION_COLORS = {
        "MUST DELETE": "#e74c3c",  # Red - Immediate action
        "COULD DELETE": "#f39c12",  # Yellow - Candidate for removal
        "SHOULD NOT DELETE": "#27ae60",  # Green - Retain
        "RETAIN": "#27ae60",  # Alias for compatibility
    }

    # Priority color scheme (for recommendations)
    PRIORITY_COLORS = {
        "Critical": "#e74c3c",  # Red
        "High": "#f39c12",  # Orange
        "Medium": "#3498db",  # Blue
        "Low": "#95a5a6",  # Gray
    }

    @staticmethod
    def create_cost_bubble_chart(analyses: List[VPCAnalysis], figsize: Tuple[int, int] = (14, 8)) -> Figure:
        """
        Cost vs VPCs bubble chart with comprehensive NaN guards.

        X-axis: VPC index
        Y-axis: Monthly cost ($)
        Bubble size: Cost impact (proportional)
        Color: Classification (red=MUST DELETE, yellow=COULD DELETE, green=RETAIN)

        Edge cases:
        - Empty analyses → return empty figure with message
        - All zero costs → use default bubble size
        - NaN/inf values → filter out with warning

        Args:
            analyses: List of VPCAnalysis objects
            figsize: Figure size (width, height)

        Returns:
            matplotlib Figure object
        """
        # Guard: Empty analyses
        if not analyses or len(analyses) == 0:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5, 0.5, "No VPC data available for visualization", ha="center", va="center", fontsize=16, color="gray"
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Extract data with NaN filtering
        costs = []
        classifications = []
        vpc_labels = []

        for i, analysis in enumerate(analyses):
            cost = float(analysis.cost_breakdown.total_monthly_cost)

            # Filter out NaN/inf values
            if np.isnan(cost) or np.isinf(cost):
                continue

            costs.append(cost)
            classifications.append(analysis.three_bucket)
            vpc_labels.append(f"{analysis.metadata.vpc_id}\n{analysis.metadata.environment}")

        # Guard: All costs filtered out
        if len(costs) == 0:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(
                0.5,
                0.5,
                "No valid cost data available (all NaN/inf)",
                ha="center",
                va="center",
                fontsize=16,
                color="orange",
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Calculate bubble sizes (proportional to cost, with minimum size)
        if max(costs) > 0:
            sizes = [max(100, c * 20) for c in costs]  # Scale factor 20, min 100
        else:
            sizes = [200] * len(costs)  # Default size for zero costs

        # Create figure with professional styling
        fig, ax = plt.subplots(figsize=figsize)

        # Plot bubbles grouped by classification
        for classification in ["MUST DELETE", "COULD DELETE", "SHOULD NOT DELETE", "RETAIN"]:
            indices = [i for i, c in enumerate(classifications) if c == classification]
            if not indices:
                continue

            ax.scatter(
                [i for i in indices],
                [costs[i] for i in indices],
                s=[sizes[i] for i in indices],
                c=VPCNotebookVisualizations.CLASSIFICATION_COLORS.get(classification, "#95a5a6"),
                alpha=0.6,
                edgecolors="black",
                linewidth=1,
                label=classification,
            )

        # Styling
        ax.set_xlabel("VPC Index", fontsize=14, fontweight="bold")
        ax.set_ylabel("Monthly Cost ($)", fontsize=14, fontweight="bold")
        ax.set_title("VPC Cost Analysis - Bubble Chart", fontsize=18, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend(loc="upper right", fontsize=12, framealpha=0.9)

        # Set x-axis labels to VPC IDs
        ax.set_xticks(range(len(vpc_labels)))
        ax.set_xticklabels(vpc_labels, rotation=45, ha="right", fontsize=10)

        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))

        plt.tight_layout()
        return fig

    @staticmethod
    def create_savings_waterfall(
        baseline_cost: float, savings_by_category: Dict[str, float], figsize: Tuple[int, int] = (12, 6)
    ) -> Figure:
        """
        Waterfall chart showing cost reduction progression.

        Categories:
        - Baseline Cost
        - Remove Idle NAT Gateways: -$XX
        - Deploy Gateway VPC Endpoints: -$XX
        - Optimize Interface VPCEs: -$XX
        - Final Cost

        Args:
            baseline_cost: Starting monthly cost
            savings_by_category: Dict mapping category name to savings amount (positive = savings)
            figsize: Figure size (width, height)

        Returns:
            matplotlib Figure with waterfall visualization
        """
        # Guard: Invalid baseline cost
        if np.isnan(baseline_cost) or np.isinf(baseline_cost) or baseline_cost < 0:
            baseline_cost = 0.0

        # Build waterfall data
        categories = ["Baseline Cost"]
        values = [baseline_cost]

        # Add savings categories (sorted by magnitude for visual impact)
        sorted_categories = sorted(savings_by_category.items(), key=lambda x: x[1], reverse=True)

        current_cost = baseline_cost
        for category, savings in sorted_categories:
            # Filter NaN/inf
            if np.isnan(savings) or np.isinf(savings):
                continue

            categories.append(category)
            current_cost -= savings
            values.append(current_cost)

        # Add final cost
        categories.append("Final Cost")
        values.append(current_cost)

        # Guard: No valid data
        if len(values) <= 1:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No savings data available", ha="center", va="center", fontsize=16, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Create waterfall chart
        fig, ax = plt.subplots(figsize=figsize)

        x_positions = np.arange(len(categories))
        colors = []

        for i in range(len(values)):
            if i == 0:
                # Baseline - blue
                colors.append("#3498db")
            elif i == len(values) - 1:
                # Final - green if savings, red if increase
                colors.append("#27ae60" if values[i] < baseline_cost else "#e74c3c")
            else:
                # Savings - green
                colors.append("#27ae60")

        # Plot bars
        ax.bar(x_positions, values, color=colors, alpha=0.7, edgecolor="black", linewidth=1)

        # Add connecting lines
        for i in range(len(values) - 1):
            ax.plot([i + 0.4, i + 1 - 0.4], [values[i], values[i]], "k--", alpha=0.5)

        # Add value labels on bars
        for i, (cat, val) in enumerate(zip(categories, values)):
            ax.text(
                i, val + baseline_cost * 0.02, f"${val:,.0f}", ha="center", va="bottom", fontsize=11, fontweight="bold"
            )

        # Styling
        ax.set_xlabel("Cost Optimization Steps", fontsize=14, fontweight="bold")
        ax.set_ylabel("Monthly Cost ($)", fontsize=14, fontweight="bold")
        ax.set_title("Cost Savings Waterfall Analysis", fontsize=18, fontweight="bold", pad=20)
        ax.set_xticks(x_positions)
        ax.set_xticklabels(categories, rotation=45, ha="right", fontsize=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax.grid(True, alpha=0.3, axis="y", linestyle="--")

        plt.tight_layout()
        return fig

    @staticmethod
    def create_resource_heatmap(
        vpcs: List[str], resource_counts: Dict[str, List[int]], figsize: Tuple[int, int] = (14, 8)
    ) -> Figure:
        """
        Resource utilization heatmap.

        Rows: VPC IDs
        Columns: Resource types (NAT GWs, VPCEs, EC2, Lambda, RDS, LBs, ENIs, TGW)
        Color intensity: Resource count (darker = more resources)

        Args:
            vpcs: List of VPC IDs (row labels)
            resource_counts: Dict mapping resource type to list of counts
            figsize: Figure size (width, height)

        Returns:
            matplotlib Figure with seaborn heatmap
        """
        # Guard: Empty data
        if not vpcs or len(vpcs) == 0 or not resource_counts:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No resource data available", ha="center", va="center", fontsize=16, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Build data matrix (rows=VPCs, columns=resource types)
        resource_types = list(resource_counts.keys())
        data_matrix = []

        for vpc_idx in range(len(vpcs)):
            row = []
            for resource_type in resource_types:
                counts = resource_counts[resource_type]
                # Guard: Index out of range
                if vpc_idx < len(counts):
                    count = counts[vpc_idx]
                    # Guard: NaN/inf
                    if np.isnan(count) or np.isinf(count):
                        count = 0
                else:
                    count = 0
                row.append(count)
            data_matrix.append(row)

        # Convert to numpy array
        data_array = np.array(data_matrix)

        # Create heatmap
        fig, ax = plt.subplots(figsize=figsize)

        sns.heatmap(
            data_array,
            annot=True,
            fmt="g",
            cmap="YlOrRd",
            cbar_kws={"label": "Resource Count"},
            xticklabels=resource_types,
            yticklabels=vpcs,
            linewidths=0.5,
            linecolor="gray",
            ax=ax,
        )

        # Styling
        ax.set_xlabel("Resource Type", fontsize=14, fontweight="bold")
        ax.set_ylabel("VPC ID", fontsize=14, fontweight="bold")
        ax.set_title("VPC Resource Utilization Heatmap", fontsize=18, fontweight="bold", pad=20)

        # Rotate labels for readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=11)
        plt.setp(ax.get_yticklabels(), rotation=0, fontsize=10)

        plt.tight_layout()
        return fig

    @staticmethod
    def create_implementation_gantt(recommendations: List[Any], figsize: Tuple[int, int] = (12, 6)) -> Figure:
        """
        Implementation timeline Gantt chart.

        Y-axis: Recommendation titles
        X-axis: Timeline (weeks)
        Bars: Implementation duration colored by priority

        Args:
            recommendations: List of recommendation objects with attributes:
                - title: str
                - implementation_weeks: int
                - priority: str (Critical/High/Medium/Low)
            figsize: Figure size (width, height)

        Returns:
            matplotlib Figure with Gantt chart
        """
        # Guard: Empty recommendations
        if not recommendations or len(recommendations) == 0:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No recommendations available", ha="center", va="center", fontsize=16, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Extract data
        titles = []
        durations = []
        priorities = []
        start_weeks = []

        current_week = 0
        for rec in recommendations:
            # Extract attributes (handle both dict and object access)
            if isinstance(rec, dict):
                title = rec.get("title", "Unnamed")
                duration = rec.get("implementation_weeks", 1)
                priority = rec.get("priority", "Medium")
            else:
                title = getattr(rec, "title", "Unnamed")
                duration = getattr(rec, "implementation_weeks", 1)
                priority = getattr(rec, "priority", "Medium")

            # Guard: Invalid duration
            if np.isnan(duration) or np.isinf(duration) or duration <= 0:
                duration = 1

            titles.append(title)
            durations.append(duration)
            priorities.append(priority)
            start_weeks.append(current_week)

            current_week += duration

        # Create Gantt chart
        fig, ax = plt.subplots(figsize=figsize)

        y_positions = np.arange(len(titles))

        for i, (title, duration, priority, start) in enumerate(zip(titles, durations, priorities, start_weeks)):
            color = VPCNotebookVisualizations.PRIORITY_COLORS.get(priority, "#95a5a6")

            ax.barh(i, duration, left=start, height=0.8, color=color, alpha=0.7, edgecolor="black", linewidth=1)

            # Add duration label
            ax.text(
                start + duration / 2,
                i,
                f"{int(duration)}w",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="white",
            )

        # Styling
        ax.set_yticks(y_positions)
        ax.set_yticklabels(titles, fontsize=11)
        ax.set_xlabel("Timeline (Weeks)", fontsize=14, fontweight="bold")
        ax.set_title("Implementation Timeline - Gantt Chart", fontsize=18, fontweight="bold", pad=20)
        ax.grid(True, alpha=0.3, axis="x", linestyle="--")
        ax.invert_yaxis()  # Top to bottom

        # Add priority legend
        legend_patches = [
            mpatches.Patch(color=VPCNotebookVisualizations.PRIORITY_COLORS[p], label=p, alpha=0.7)
            for p in ["Critical", "High", "Medium", "Low"]
            if any(prio == p for prio in priorities)
        ]
        ax.legend(handles=legend_patches, loc="upper right", fontsize=11, framealpha=0.9)

        plt.tight_layout()
        return fig

    @staticmethod
    def create_risk_matrix(recommendations: List[Any], figsize: Tuple[int, int] = (10, 8)) -> Figure:
        """
        Risk vs impact scatter plot.

        X-axis: Monthly savings potential ($)
        Y-axis: Risk level (1=Low, 2=Medium, 3=High)
        Bubble size: Implementation timeline (weeks)
        Color: Priority (Critical/High/Medium/Low)

        Args:
            recommendations: List of recommendation objects with attributes:
                - savings_monthly: float
                - risk_level: str (Low/Medium/High)
                - implementation_weeks: int
                - priority: str (Critical/High/Medium/Low)
            figsize: Figure size (width, height)

        Returns:
            matplotlib Figure with risk matrix scatter plot
        """
        # Guard: Empty recommendations
        if not recommendations or len(recommendations) == 0:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No recommendations available", ha="center", va="center", fontsize=16, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Risk level mapping
        risk_map = {"Low": 1, "Medium": 2, "High": 3}

        # Extract data
        savings = []
        risk_levels = []
        sizes = []
        priorities = []

        for rec in recommendations:
            # Extract attributes
            if isinstance(rec, dict):
                saving = rec.get("savings_monthly", 0)
                risk = rec.get("risk_level", "Medium")
                duration = rec.get("implementation_weeks", 1)
                priority = rec.get("priority", "Medium")
            else:
                saving = getattr(rec, "savings_monthly", 0)
                risk = getattr(rec, "risk_level", "Medium")
                duration = getattr(rec, "implementation_weeks", 1)
                priority = getattr(rec, "priority", "Medium")

            # Guard: NaN/inf
            if np.isnan(saving) or np.isinf(saving):
                saving = 0
            if np.isnan(duration) or np.isinf(duration) or duration <= 0:
                duration = 1

            savings.append(saving)
            risk_levels.append(risk_map.get(risk, 2))
            sizes.append(duration * 100)  # Scale factor 100
            priorities.append(priority)

        # Guard: No valid data
        if len(savings) == 0:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, "No valid recommendation data", ha="center", va="center", fontsize=16, color="gray")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis("off")
            return fig

        # Create scatter plot
        fig, ax = plt.subplots(figsize=figsize)

        # Plot by priority for color grouping
        for priority in ["Critical", "High", "Medium", "Low"]:
            indices = [i for i, p in enumerate(priorities) if p == priority]
            if not indices:
                continue

            ax.scatter(
                [savings[i] for i in indices],
                [risk_levels[i] for i in indices],
                s=[sizes[i] for i in indices],
                c=VPCNotebookVisualizations.PRIORITY_COLORS.get(priority, "#95a5a6"),
                alpha=0.6,
                edgecolors="black",
                linewidth=1,
                label=priority,
            )

        # Add quadrant lines (risk threshold at Medium, savings threshold at median)
        if len(savings) > 0:
            median_savings = np.median([s for s in savings if s > 0]) if any(s > 0 for s in savings) else 0
            ax.axhline(y=2, color="gray", linestyle="--", alpha=0.5, label="Risk Threshold")
            if median_savings > 0:
                ax.axvline(x=median_savings, color="gray", linestyle="--", alpha=0.5, label="Savings Threshold")

        # Styling
        ax.set_xlabel("Monthly Savings Potential ($)", fontsize=14, fontweight="bold")
        ax.set_ylabel("Risk Level", fontsize=14, fontweight="bold")
        ax.set_title("Risk vs Impact Matrix", fontsize=18, fontweight="bold", pad=20)
        ax.set_yticks([1, 2, 3])
        ax.set_yticklabels(["Low", "Medium", "High"], fontsize=12)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend(loc="upper right", fontsize=11, framealpha=0.9)

        plt.tight_layout()
        return fig
