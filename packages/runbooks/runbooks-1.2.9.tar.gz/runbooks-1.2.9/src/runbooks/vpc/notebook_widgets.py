"""
Interactive Jupyter Notebook Widgets for VPC Manager Dashboard.

This module provides manager-friendly ipywidgets components for configuring
and executing VPC analysis workflows in Jupyter notebooks.

Design Philosophy:
- Manager-friendly labels (not technical jargon)
- Reasonable enterprise defaults
- Visual feedback for operations
- Responsive layout with clear descriptions
"""

from typing import List, Optional, Callable, Any
from ipywidgets import (
    VBox,
    HBox,
    Dropdown,
    SelectMultiple,
    FloatSlider,
    FloatText,
    Button,
    Checkbox,
    Label,
    Layout,
    HTML,
    Output,
)


class VPCNotebookWidgets:
    """Interactive widgets for manager dashboard configuration."""

    # Enterprise color scheme for consistent styling
    COLORS = {
        "primary": "#0066cc",
        "success": "#28a745",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#17a2b8",
    }

    @staticmethod
    def create_configuration_panel(
        accounts: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        callback: Optional[Callable] = None,
    ) -> VBox:
        """
        Create complete configuration panel with all widgets.

        Args:
            accounts: List of available AWS accounts (default: ['All Accounts'])
            regions: List of available AWS regions (default: common AWS regions)
            callback: Optional callback function for analysis button
                      Signature: callback(account: str, regions: List[str],
                                         target: float, threshold: float)

        Returns:
            VBox: Complete configuration panel ready for display

        Example:
            >>> panel = VPCNotebookWidgets.create_configuration_panel(
            ...     accounts=['Production', 'Development', 'Staging'],
            ...     callback=run_analysis
            ... )
            >>> display(panel)
        """
        if accounts is None:
            accounts = ["All Accounts"]

        if regions is None:
            regions = [
                "ap-southeast-2",  # Sydney (primary)
                "ap-southeast-2",  # N. Virginia
                "ap-southeast-6",  # Oregon
                "eu-west-1",  # Ireland
                "ap-southeast-1",  # Singapore
            ]

        # Header
        header = HTML(
            value=f"""
            <div style="background-color: {VPCNotebookWidgets.COLORS["primary"]};
                        color: white; padding: 15px; border-radius: 5px;
                        margin-bottom: 20px;">
                <h2 style="margin: 0;">VPC Cost Optimization Configuration</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">
                    Configure your analysis parameters and click "Run Analysis" to generate recommendations
                </p>
            </div>
            """
        )

        # Create individual widgets
        account_selector = VPCNotebookWidgets.create_account_selector(accounts)
        region_selector = VPCNotebookWidgets.create_region_multiselect(regions, default_region="ap-southeast-2")
        savings_slider = VPCNotebookWidgets.create_savings_target_slider()
        threshold_input = VPCNotebookWidgets.create_cost_threshold_input()
        analysis_button = VPCNotebookWidgets.create_analysis_button(callback)

        # Layout with sections
        account_section = VBox(
            [
                Label(
                    value="🏢 Account Selection",
                    style={"font_weight": "bold", "font_size": "14px"},
                ),
                account_selector,
            ],
            layout=Layout(margin="10px 0"),
        )

        region_section = VBox(
            [
                Label(
                    value="🌍 Region Selection",
                    style={"font_weight": "bold", "font_size": "14px"},
                ),
                region_selector,
            ],
            layout=Layout(margin="10px 0"),
        )

        savings_section = VBox(
            [
                Label(
                    value="💰 Savings Target",
                    style={"font_weight": "bold", "font_size": "14px"},
                ),
                savings_slider,
            ],
            layout=Layout(margin="10px 0"),
        )

        threshold_section = VBox(
            [
                Label(
                    value="✅ Approval Threshold",
                    style={"font_weight": "bold", "font_size": "14px"},
                ),
                threshold_input,
            ],
            layout=Layout(margin="10px 0"),
        )

        # Action section
        action_section = VBox([analysis_button], layout=Layout(margin="20px 0", align_items="center"))

        # Combine all sections
        panel = VBox(
            [
                header,
                account_section,
                region_section,
                savings_section,
                threshold_section,
                action_section,
            ],
            layout=Layout(
                border="1px solid #ddd",
                border_radius="5px",
                padding="20px",
                width="100%",
                max_width="800px",
            ),
        )

        return panel

    @staticmethod
    def create_account_selector(accounts: List[str]) -> Dropdown:
        """
        Create account selection dropdown with default 'All Accounts'.

        Args:
            accounts: List of available AWS accounts

        Returns:
            Dropdown: Account selector widget

        Example:
            >>> selector = VPCNotebookWidgets.create_account_selector(
            ...     ['All Accounts', 'Production', 'Development']
            ... )
        """
        # Ensure 'All Accounts' is first option
        if "All Accounts" not in accounts:
            accounts = ["All Accounts"] + accounts

        return Dropdown(
            options=accounts,
            value="All Accounts",
            description="AWS Account:",
            disabled=False,
            style={"description_width": "150px"},
            layout=Layout(width="100%", max_width="600px"),
            tooltip="Select the AWS account to analyze (All Accounts = multi-account analysis)",
        )

    @staticmethod
    def create_region_multiselect(regions: List[str], default_region: str = "ap-southeast-2") -> SelectMultiple:
        """
        Create multi-region selection widget.

        Args:
            regions: List of available AWS regions
            default_region: Default selected region (default: ap-southeast-2)

        Returns:
            SelectMultiple: Region selector widget

        Example:
            >>> selector = VPCNotebookWidgets.create_region_multiselect(
            ...     ['ap-southeast-2', 'ap-southeast-2'], default_region='ap-southeast-2'
            ... )
        """
        # Ensure default region is in list
        if default_region not in regions:
            regions.insert(0, default_region)

        return SelectMultiple(
            options=regions,
            value=[default_region],  # Default selection
            description="AWS Regions:",
            disabled=False,
            style={"description_width": "150px"},
            layout=Layout(width="100%", max_width="600px", height="120px"),
            tooltip="Select one or more AWS regions to analyze (Hold Ctrl/Cmd for multiple selections)",
        )

    @staticmethod
    def create_savings_target_slider(
        min_val: float = 0.0, max_val: float = 50.0, default_val: float = 30.0
    ) -> FloatSlider:
        """
        Create savings target percentage slider.

        Args:
            min_val: Minimum savings percentage (default: 0%)
            max_val: Maximum savings percentage (default: 50%)
            default_val: Default savings percentage (default: 30%)

        Returns:
            FloatSlider: Savings target slider widget

        Example:
            >>> slider = VPCNotebookWidgets.create_savings_target_slider(
            ...     min_val=0.0, max_val=50.0, default_val=30.0
            ... )
        """
        return FloatSlider(
            value=default_val,
            min=min_val,
            max=max_val,
            step=5.0,
            description="Target Savings (%):",
            disabled=False,
            continuous_update=True,
            orientation="horizontal",
            readout=True,
            readout_format=".1f",
            style={"description_width": "150px"},
            layout=Layout(width="100%", max_width="600px"),
            tooltip=f"Select target cost reduction percentage (Enterprise benchmark: {default_val}%)",
        )

    @staticmethod
    def create_cost_threshold_input(default_threshold: float = 1000.0) -> FloatText:
        """
        Create cost approval threshold input.

        Args:
            default_threshold: Default approval threshold in USD/month (default: $1,000)

        Returns:
            FloatText: Cost threshold input widget

        Example:
            >>> threshold = VPCNotebookWidgets.create_cost_threshold_input(
            ...     default_threshold=1000.0
            ... )
        """
        return FloatText(
            value=default_threshold,
            description="Approval Threshold:",
            disabled=False,
            step=100.0,
            style={"description_width": "150px"},
            layout=Layout(width="100%", max_width="600px"),
            tooltip=f"Recommendations above ${default_threshold:,.0f}/month require manager approval",
        )

    @staticmethod
    def create_analysis_button(callback: Optional[Callable] = None) -> Button:
        """
        Create run analysis button.

        Args:
            callback: Optional callback function to execute on click
                      Signature: callback() - retrieves values from parent widgets

        Returns:
            Button: Analysis execution button

        Example:
            >>> def run_analysis():
            ...     print("Running VPC analysis...")
            >>> button = VPCNotebookWidgets.create_analysis_button(callback=run_analysis)
        """
        button = Button(
            description="🚀 Run VPC Analysis",
            disabled=False,
            button_style="primary",  # 'success', 'info', 'warning', 'danger' or ''
            tooltip="Click to execute VPC cost optimization analysis",
            layout=Layout(width="300px", height="50px"),
            style={"font_weight": "bold", "font_size": "16px"},
        )

        if callback:

            def on_button_click(b):
                """Handle button click with visual feedback."""
                # Update button state
                b.description = "⏳ Running Analysis..."
                b.disabled = True
                b.button_style = "warning"

                try:
                    # Execute callback
                    callback()

                    # Success state
                    b.description = "✅ Analysis Complete"
                    b.button_style = "success"
                except Exception as e:
                    # Error state
                    b.description = f"❌ Analysis Failed: {str(e)}"
                    b.button_style = "danger"
                finally:
                    # Re-enable after 2 seconds
                    import time

                    time.sleep(2)
                    b.description = "🚀 Run VPC Analysis"
                    b.disabled = False
                    b.button_style = "primary"

            button.on_click(on_button_click)

        return button

    @staticmethod
    def create_export_options() -> VBox:
        """
        Create export format selection checkboxes.

        Returns:
            VBox: Export options panel with checkboxes for CSV, JSON, Excel, PDF

        Example:
            >>> export_panel = VPCNotebookWidgets.create_export_options()
            >>> display(export_panel)
        """
        header = Label(
            value="📤 Export Formats",
            style={"font_weight": "bold", "font_size": "14px"},
        )

        csv_checkbox = Checkbox(
            value=True,  # Default enabled
            description="CSV (Excel-compatible)",
            disabled=False,
            indent=True,
            style={"description_width": "initial"},
        )

        json_checkbox = Checkbox(
            value=True,  # Default enabled
            description="JSON (API integration)",
            disabled=False,
            indent=True,
            style={"description_width": "initial"},
        )

        excel_checkbox = Checkbox(
            value=True,  # Default enabled
            description="Excel (Manager reports)",
            disabled=False,
            indent=True,
            style={"description_width": "initial"},
        )

        pdf_checkbox = Checkbox(
            value=False,  # Optional
            description="PDF (Executive summary)",
            disabled=False,
            indent=True,
            style={"description_width": "initial"},
        )

        export_panel = VBox(
            [header, csv_checkbox, json_checkbox, excel_checkbox, pdf_checkbox],
            layout=Layout(
                border="1px solid #ddd",
                border_radius="5px",
                padding="15px",
                margin="10px 0",
                width="100%",
                max_width="400px",
            ),
        )

        return export_panel

    @staticmethod
    def create_quick_win_buttons(recommendations: List[Any]) -> VBox:
        """
        Create quick-win action buttons for manager approval.

        Args:
            recommendations: List of business recommendations with quick-win flag

        Returns:
            VBox: Panel with action buttons for each quick-win recommendation

        Example:
            >>> recommendations = [
            ...     {"title": "Deploy Gateway Endpoints", "quick_win": True, "savings": 500},
            ...     {"title": "Remove Idle NAT Gateways", "quick_win": True, "savings": 1200}
            ... ]
            >>> buttons = VPCNotebookWidgets.create_quick_win_buttons(recommendations)
        """
        header = HTML(
            value=f"""
            <div style="background-color: {VPCNotebookWidgets.COLORS["success"]};
                        color: white; padding: 10px; border-radius: 5px;
                        margin-bottom: 15px;">
                <h3 style="margin: 0;">⚡ Quick Win Recommendations</h3>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">
                    One-click deployment for high-impact, low-risk optimizations
                </p>
            </div>
            """
        )

        buttons = []

        # Filter quick-win recommendations
        quick_wins = [r for r in recommendations if r.get("quick_win", False)]

        if not quick_wins:
            no_wins_label = Label(value="ℹ️ No quick-win recommendations available for current configuration")
            return VBox([header, no_wins_label])

        for rec in quick_wins:
            title = rec.get("title", "Unknown Recommendation")
            savings = rec.get("savings", 0.0)
            risk = rec.get("risk", "low").upper()

            # Color based on risk
            risk_colors = {
                "LOW": VPCNotebookWidgets.COLORS["success"],
                "MEDIUM": VPCNotebookWidgets.COLORS["warning"],
                "HIGH": VPCNotebookWidgets.COLORS["danger"],
            }
            risk_color = risk_colors.get(risk, VPCNotebookWidgets.COLORS["info"])

            button = Button(
                description=f"Deploy: {title}",
                disabled=False,
                button_style="success" if risk == "LOW" else "warning",
                tooltip=f"Estimated savings: ${savings:,.0f}/month | Risk: {risk}",
                layout=Layout(width="100%", margin="5px 0"),
                icon="check",
            )

            # Add savings and risk label
            info_label = HTML(
                value=f"""
                <div style="padding: 5px; font-size: 12px;">
                    <span style="color: {VPCNotebookWidgets.COLORS["success"]};">
                        💰 ${savings:,.0f}/month savings
                    </span>
                    <span style="margin-left: 15px; color: {risk_color};">
                        🎯 Risk: {risk}
                    </span>
                </div>
                """
            )

            button_container = VBox(
                [button, info_label],
                layout=Layout(border="1px solid #eee", border_radius="3px", margin="5px 0"),
            )
            buttons.append(button_container)

        panel = VBox(
            [header] + buttons,
            layout=Layout(
                border="1px solid #ddd",
                border_radius="5px",
                padding="15px",
                margin="10px 0",
                width="100%",
            ),
        )

        return panel

    @staticmethod
    def create_output_display() -> Output:
        """
        Create output widget for displaying analysis results.

        Returns:
            Output: Widget for capturing and displaying analysis output

        Example:
            >>> output = VPCNotebookWidgets.create_output_display()
            >>> display(output)
            >>> with output:
            ...     print("Analysis results...")
        """
        return Output(
            layout=Layout(
                border="1px solid #ddd",
                border_radius="5px",
                padding="15px",
                margin="10px 0",
                width="100%",
                max_height="600px",
                overflow_y="auto",
            )
        )

    @staticmethod
    def create_status_indicator(status: str = "ready", message: str = "Ready to analyze") -> HTML:
        """
        Create status indicator widget.

        Args:
            status: Status level ('ready', 'running', 'success', 'error', 'warning')
            message: Status message to display

        Returns:
            HTML: Status indicator widget

        Example:
            >>> indicator = VPCNotebookWidgets.create_status_indicator(
            ...     status='running', message='Analyzing VPC configurations...'
            ... )
        """
        status_styles = {
            "ready": (VPCNotebookWidgets.COLORS["info"], "ℹ️"),
            "running": (VPCNotebookWidgets.COLORS["warning"], "⏳"),
            "success": (VPCNotebookWidgets.COLORS["success"], "✅"),
            "error": (VPCNotebookWidgets.COLORS["danger"], "❌"),
            "warning": (VPCNotebookWidgets.COLORS["warning"], "⚠️"),
        }

        color, icon = status_styles.get(status, (VPCNotebookWidgets.COLORS["info"], "ℹ️"))

        return HTML(
            value=f"""
            <div style="background-color: {color}; color: white;
                        padding: 10px; border-radius: 5px; margin: 10px 0;">
                <strong>{icon} {message}</strong>
            </div>
            """
        )
