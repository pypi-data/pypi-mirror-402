"""
Configuration management for ITSM Analytics Dashboard.

This module provides Pydantic-based configuration classes for managing:
- Data source configurations (file paths, sheet names, data directories)
- SLA target definitions (P1-P4 response time targets)
- Design system settings (colors, typography, export configurations)
- Visualization preferences (themes, performance settings)
- Master ITSM configuration with backward compatibility

Follows enterprise patterns from runbooks.finops and runbooks.inventory modules.
"""

from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator


class DataSourceConfig(BaseModel):
    """Data source configuration for ITSM ticket files.

    Attributes:
        data_dir: Directory containing ITSM data files
        aws_file: Filename for AWS tickets Excel file
        aws_sheet: Sheet name for AWS tickets
        azure_file: Filename for Azure tickets Excel file
        azure_sheet: Sheet name for Azure tickets
        pricing_file: Filename for pricing model comparison Excel file
        pricing_sheet: Sheet name for pricing data
    """

    data_dir: Path = Field(default=Path("data"), description="Directory containing ITSM data files")
    aws_file: str = Field(default="AWSTickets.xlsx", description="Filename for AWS tickets Excel file")
    aws_sheet: str = Field(default="AWS-Tickets", description="Sheet name for AWS tickets")
    azure_file: str = Field(default="AzureTickets.xlsx", description="Filename for Azure tickets Excel file")
    azure_sheet: str = Field(default="Azure-Tickets", description="Sheet name for Azure tickets")
    pricing_file: str = Field(
        default="Cloud price revision v 1.1 1.9.25 Bluecurrent Model.xlsx",
        description="Filename for pricing model comparison Excel file",
    )
    pricing_sheet: str = Field(default="Bluecurrent", description="Sheet name for pricing data")

    @field_validator("data_dir", mode="before")
    @classmethod
    def validate_data_dir(cls, v):
        """Convert string to Path if needed."""
        if isinstance(v, str):
            return Path(v)
        return v

    def get_aws_path(self) -> Path:
        """Get full path to AWS tickets file.

        Returns:
            Full path to AWS tickets Excel file
        """
        return self.data_dir / self.aws_file

    def get_azure_path(self) -> Path:
        """Get full path to Azure tickets file.

        Returns:
            Full path to Azure tickets Excel file
        """
        return self.data_dir / self.azure_file

    def get_pricing_path(self) -> Path:
        """Get full path to pricing file.

        Returns:
            Full path to pricing Excel file
        """
        return self.data_dir / self.pricing_file


class SLAConfig(BaseModel):
    """SLA target configuration for priority-based ticket resolution.

    Attributes:
        p1_hours: Target resolution time for P1 (Critical) tickets in hours
        p2_hours: Target resolution time for P2 (High) tickets in hours
        p3_hours: Target resolution time for P3 (Medium) tickets in hours
        p4_hours: Target resolution time for P4 (Low) tickets in hours
    """

    p1_hours: int = Field(default=4, ge=1, description="Target resolution time for P1 (Critical) tickets in hours")
    p2_hours: int = Field(default=8, ge=1, description="Target resolution time for P2 (High) tickets in hours")
    p3_hours: int = Field(default=24, ge=1, description="Target resolution time for P3 (Medium) tickets in hours")
    p4_hours: int = Field(default=48, ge=1, description="Target resolution time for P4 (Low) tickets in hours")

    def get_target(self, priority: str) -> int:
        """Get SLA target hours for a specific priority.

        Args:
            priority: Priority level (P1, P2, P3, P4)

        Returns:
            Target resolution hours for the priority

        Raises:
            ValueError: If priority is not recognized
        """
        priority_map = {
            "P1": self.p1_hours,
            "P2": self.p2_hours,
            "P3": self.p3_hours,
            "P4": self.p4_hours,
        }

        if priority not in priority_map:
            raise ValueError(f"Unknown priority: {priority}. Must be one of P1, P2, P3, P4")

        return priority_map[priority]

    def to_dict(self) -> Dict[str, int]:
        """Convert to legacy dictionary format for backward compatibility.

        Returns:
            Dictionary mapping priority codes to target hours
        """
        return {
            "P1": self.p1_hours,
            "P2": self.p2_hours,
            "P3": self.p3_hours,
            "P4": self.p4_hours,
        }


class DesignSystemConfig(BaseModel):
    """Design system configuration for visualization styling.

    Attributes:
        aws_color: Primary color for AWS visualizations (hex)
        aws_color_dark: Dark variant for AWS visualizations (hex)
        azure_color: Primary color for Azure visualizations (hex)
        azure_color_dark: Dark variant for Azure visualizations (hex)
        kpi_color: Primary color for KPI visualizations (hex)
        success_color: Color for success indicators (hex)
        warning_color: Color for warning indicators (hex)
        danger_color: Color for danger indicators (hex)
        info_color: Color for info indicators (hex)
        dark_color: Dark neutral color (hex)
        light_color: Light neutral color (hex)
        background_color: Background color (hex)
        font_family: Font family for visualizations
        title_size: Font size for titles (px)
        subtitle_size: Font size for subtitles (px)
        body_size: Font size for body text (px)
        caption_size: Font size for captions (px)
        export_width: Export image width (px)
        export_height: Export image height (px)
        export_scale: Export image scale multiplier for high DPI
        export_format: Export image format (png, svg, pdf)
        layout_margin_left: Left margin for layouts (px)
        layout_margin_right: Right margin for layouts (px)
        layout_margin_top: Top margin for layouts (px)
        layout_margin_bottom: Bottom margin for layouts (px)
        layout_height: Default layout height (px)
    """

    # Colors
    aws_color: str = Field(default="#FF9900", description="AWS Orange")
    aws_color_dark: str = Field(default="#CC7A00", description="AWS Orange Dark")
    azure_color: str = Field(default="#0078D4", description="Azure Blue")
    azure_color_dark: str = Field(default="#005A9E", description="Azure Blue Dark")
    kpi_color: str = Field(default="#73BA9B", description="KPI Teal")
    success_color: str = Field(default="#28A745", description="Success Green")
    warning_color: str = Field(default="#FFC107", description="Warning Yellow")
    danger_color: str = Field(default="#DC3545", description="Danger Red")
    info_color: str = Field(default="#17A2B8", description="Info Cyan")
    dark_color: str = Field(default="#2C3E50", description="Dark Neutral")
    light_color: str = Field(default="#ECF0F1", description="Light Neutral")
    background_color: str = Field(default="#F8F9FA", description="Background Gray")

    # Typography
    font_family: str = Field(default="Arial, Roboto, sans-serif", description="Font family for visualizations")
    title_size: int = Field(default=24, ge=12, description="Font size for titles (px)")
    subtitle_size: int = Field(default=18, ge=10, description="Font size for subtitles (px)")
    body_size: int = Field(default=14, ge=8, description="Font size for body text (px)")
    caption_size: int = Field(default=12, ge=8, description="Font size for captions (px)")

    # Export settings
    export_width: int = Field(default=1920, ge=800, description="Export image width (px)")
    export_height: int = Field(default=1080, ge=600, description="Export image height (px)")
    export_scale: int = Field(default=2, ge=1, le=4, description="Export scale for high DPI")
    export_format: str = Field(default="png", description="Export format (png, svg, pdf)")

    # Layout
    layout_margin_left: int = Field(default=80, ge=0, description="Left margin (px)")
    layout_margin_right: int = Field(default=80, ge=0, description="Right margin (px)")
    layout_margin_top: int = Field(default=100, ge=0, description="Top margin (px)")
    layout_margin_bottom: int = Field(default=80, ge=0, description="Bottom margin (px)")
    layout_height: int = Field(default=600, ge=400, description="Default layout height (px)")

    @field_validator("export_format")
    @classmethod
    def validate_export_format(cls, v):
        """Validate export format."""
        valid_formats = {"png", "svg", "pdf"}
        if v not in valid_formats:
            raise ValueError(f"Export format must be one of {valid_formats}, got: {v}")
        return v

    def get_color_palette(self) -> Dict[str, str]:
        """Get complete color palette as dictionary.

        Returns:
            Dictionary mapping color names to hex values
        """
        return {
            "aws": self.aws_color,
            "aws_dark": self.aws_color_dark,
            "azure": self.azure_color,
            "azure_dark": self.azure_color_dark,
            "kpi": self.kpi_color,
            "success": self.success_color,
            "warning": self.warning_color,
            "danger": self.danger_color,
            "info": self.info_color,
            "dark": self.dark_color,
            "light": self.light_color,
            "background": self.background_color,
        }

    def get_typography(self) -> Dict[str, any]:
        """Get typography settings as dictionary.

        Returns:
            Dictionary with font family and sizes
        """
        return {
            "font_family": self.font_family,
            "title_size": self.title_size,
            "subtitle_size": self.subtitle_size,
            "body_size": self.body_size,
            "caption_size": self.caption_size,
        }

    def get_export_settings(self) -> Dict[str, any]:
        """Get export settings as dictionary.

        Returns:
            Dictionary with export dimensions and format
        """
        return {
            "width": self.export_width,
            "height": self.export_height,
            "scale": self.export_scale,
            "format": self.export_format,
        }

    def get_layout_margins(self) -> Dict[str, int]:
        """Get layout margins as dictionary.

        Returns:
            Dictionary with margin values (l, r, t, b)
        """
        return {
            "l": self.layout_margin_left,
            "r": self.layout_margin_right,
            "t": self.layout_margin_top,
            "b": self.layout_margin_bottom,
        }


class VisualizationConfig(BaseModel):
    """Visualization configuration for dashboard behavior.

    Attributes:
        theme: Plotly theme (plotly_dark, plotly_white, ggplot2, etc.)
        use_sample_data: Whether to generate sample data when files missing
        performance_cache_enabled: Enable caching for performance optimization
        max_items_display: Maximum items to display in lists/tables
    """

    theme: str = Field(default="plotly_dark", description="Plotly theme (plotly_dark, plotly_white, ggplot2, etc.)")
    use_sample_data: bool = Field(default=True, description="Generate sample data when actual files are missing")
    performance_cache_enabled: bool = Field(default=True, description="Enable caching for performance optimization")
    max_items_display: int = Field(default=20, ge=5, le=100, description="Maximum items to display in lists/tables")


class ITSMConfig(BaseModel):
    """Master ITSM Analytics Dashboard configuration.

    This is the main configuration class that aggregates all sub-configurations
    and provides backward compatibility with legacy dictionary-based configs.

    Attributes:
        data_sources: Data source configuration
        sla_targets: SLA target configuration
        design_system: Design system configuration
        visualization: Visualization configuration
    """

    data_sources: DataSourceConfig = Field(default_factory=DataSourceConfig, description="Data source configuration")
    sla_targets: SLAConfig = Field(default_factory=SLAConfig, description="SLA target configuration")
    design_system: DesignSystemConfig = Field(
        default_factory=DesignSystemConfig, description="Design system configuration"
    )
    visualization: VisualizationConfig = Field(
        default_factory=VisualizationConfig, description="Visualization configuration"
    )

    def to_legacy_dict(self) -> Dict[str, any]:
        """Convert to legacy dictionary format for backward compatibility.

        This method produces the same structure as the original CONFIG dictionary
        from complete_itsm_dashboard.py:

        CONFIG = {
            'AWS_FILE': 'AWSTickets.xlsx',
            'AZURE_FILE': 'AzureTickets.xlsx',
            'PRICING_FILE': 'Cloud price revision v 1.1 1.9.25 Bluecurrent Model.xlsx',
            'SLA_TARGETS': {'P1': 4, 'P2': 8, 'P3': 24, 'P4': 48},
            'THEME': 'plotly_dark'
        }

        Returns:
            Dictionary in legacy format
        """
        return {
            "AWS_FILE": self.data_sources.aws_file,
            "AZURE_FILE": self.data_sources.azure_file,
            "PRICING_FILE": self.data_sources.pricing_file,
            "SLA_TARGETS": self.sla_targets.to_dict(),
            "THEME": self.visualization.theme,
        }

    def to_design_system_dict(self) -> Dict[str, any]:
        """Convert design system to legacy DESIGN_SYSTEM dictionary format.

        This method produces the same structure as the original DESIGN_SYSTEM
        from COMPLETE_ITSM_SOLUTION.py.

        Returns:
            Dictionary in legacy DESIGN_SYSTEM format
        """
        return {
            "colors": self.design_system.get_color_palette(),
            "typography": self.design_system.get_typography(),
            "export": self.design_system.get_export_settings(),
            "layout": {
                "margin": self.design_system.get_layout_margins(),
                "height": self.design_system.layout_height,
            },
        }


# Module-level default configuration instance
default_config = ITSMConfig()


def get_config() -> ITSMConfig:
    """Get the default ITSM configuration.

    Returns:
        Default ITSMConfig instance
    """
    return default_config


def get_legacy_config() -> Dict[str, any]:
    """Get configuration in legacy dictionary format.

    This function provides backward compatibility with existing code
    that expects the CONFIG dictionary.

    Returns:
        Configuration dictionary in legacy format
    """
    return default_config.to_legacy_dict()


def get_legacy_design_system() -> Dict[str, any]:
    """Get design system in legacy dictionary format.

    This function provides backward compatibility with existing code
    that expects the DESIGN_SYSTEM dictionary.

    Returns:
        Design system dictionary in legacy format
    """
    return default_config.to_design_system_dict()


__all__ = [
    "DataSourceConfig",
    "SLAConfig",
    "DesignSystemConfig",
    "VisualizationConfig",
    "ITSMConfig",
    "default_config",
    "get_config",
    "get_legacy_config",
    "get_legacy_design_system",
]
