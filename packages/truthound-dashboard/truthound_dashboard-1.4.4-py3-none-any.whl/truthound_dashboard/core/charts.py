"""Chart library configuration and selection system.

This module provides a pluggable chart library system supporting:
- Recharts (default, React-based)
- Chart.js (Canvas-based)
- ECharts (Apache ECharts)
- Plotly (Interactive scientific charts)
- SVG (Native SVG generation)

Example:
    from truthound_dashboard.core.charts import (
        ChartLibrary,
        get_chart_config,
        set_chart_library,
    )

    # Set preferred library
    set_chart_library(ChartLibrary.CHARTJS)

    # Get configuration for frontend
    config = get_chart_config()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ChartLibrary(str, Enum):
    """Supported chart libraries."""

    RECHARTS = "recharts"  # Default, React-based
    CHARTJS = "chartjs"  # Chart.js (canvas)
    ECHARTS = "echarts"  # Apache ECharts
    PLOTLY = "plotly"  # Plotly.js
    SVG = "svg"  # Native SVG rendering


class ChartType(str, Enum):
    """Available chart types."""

    LINE = "line"
    BAR = "bar"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    RADAR = "radar"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    GAUGE = "gauge"


@dataclass
class ChartLibraryConfig:
    """Configuration for a chart library.

    Attributes:
        library: The chart library to use.
        npm_package: NPM package name for installation.
        version: Recommended version.
        supported_charts: List of supported chart types.
        options: Library-specific default options.
        cdn_url: CDN URL for script loading (if applicable).
    """

    library: ChartLibrary
    npm_package: str
    version: str
    supported_charts: list[ChartType] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)
    cdn_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "library": self.library.value,
            "npm_package": self.npm_package,
            "version": self.version,
            "supported_charts": [c.value for c in self.supported_charts],
            "options": self.options,
            "cdn_url": self.cdn_url,
        }


# Library configurations
CHART_LIBRARY_CONFIGS: dict[ChartLibrary, ChartLibraryConfig] = {
    ChartLibrary.RECHARTS: ChartLibraryConfig(
        library=ChartLibrary.RECHARTS,
        npm_package="recharts",
        version="^2.10.0",
        supported_charts=[
            ChartType.LINE,
            ChartType.BAR,
            ChartType.AREA,
            ChartType.PIE,
            ChartType.SCATTER,
            ChartType.RADAR,
            ChartType.TREEMAP,
        ],
        options={
            "responsive": True,
            "animationDuration": 300,
            "margin": {"top": 5, "right": 30, "left": 20, "bottom": 5},
        },
    ),
    ChartLibrary.CHARTJS: ChartLibraryConfig(
        library=ChartLibrary.CHARTJS,
        npm_package="chart.js",
        version="^4.4.0",
        supported_charts=[
            ChartType.LINE,
            ChartType.BAR,
            ChartType.PIE,
            ChartType.DONUT,
            ChartType.SCATTER,
            ChartType.RADAR,
        ],
        options={
            "responsive": True,
            "maintainAspectRatio": False,
            "animation": {"duration": 300},
            "plugins": {"legend": {"display": True}},
        },
        cdn_url="https://cdn.jsdelivr.net/npm/chart.js",
    ),
    ChartLibrary.ECHARTS: ChartLibraryConfig(
        library=ChartLibrary.ECHARTS,
        npm_package="echarts",
        version="^5.4.0",
        supported_charts=[
            ChartType.LINE,
            ChartType.BAR,
            ChartType.AREA,
            ChartType.PIE,
            ChartType.SCATTER,
            ChartType.RADAR,
            ChartType.HEATMAP,
            ChartType.TREEMAP,
            ChartType.GAUGE,
        ],
        options={
            "animation": True,
            "animationDuration": 300,
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        },
        cdn_url="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js",
    ),
    ChartLibrary.PLOTLY: ChartLibraryConfig(
        library=ChartLibrary.PLOTLY,
        npm_package="plotly.js",
        version="^2.27.0",
        supported_charts=[
            ChartType.LINE,
            ChartType.BAR,
            ChartType.AREA,
            ChartType.PIE,
            ChartType.SCATTER,
            ChartType.HEATMAP,
        ],
        options={
            "responsive": True,
            "displayModeBar": False,
            "staticPlot": False,
        },
        cdn_url="https://cdn.plot.ly/plotly-2.27.0.min.js",
    ),
    ChartLibrary.SVG: ChartLibraryConfig(
        library=ChartLibrary.SVG,
        npm_package="d3",  # Uses D3 for SVG generation
        version="^7.8.0",
        supported_charts=[
            ChartType.LINE,
            ChartType.BAR,
            ChartType.AREA,
            ChartType.PIE,
        ],
        options={
            "viewBox": "0 0 400 300",
            "preserveAspectRatio": "xMidYMid meet",
        },
        cdn_url="https://cdn.jsdelivr.net/npm/d3@7",
    ),
}


@dataclass
class ChartSettings:
    """Global chart settings.

    Attributes:
        library: Active chart library.
        theme: Chart color theme (light/dark/custom).
        primary_color: Primary accent color.
        animation_enabled: Whether animations are enabled.
        default_height: Default chart height in pixels.
        custom_options: Additional library-specific options.
    """

    library: ChartLibrary = ChartLibrary.RECHARTS
    theme: str = "light"
    primary_color: str = "#fd9e4b"  # Truthound primary color
    animation_enabled: bool = True
    default_height: int = 300
    custom_options: dict[str, Any] = field(default_factory=dict)

    def get_library_config(self) -> ChartLibraryConfig:
        """Get configuration for the active library."""
        return CHART_LIBRARY_CONFIGS[self.library]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        library_config = self.get_library_config()
        return {
            "library": self.library.value,
            "theme": self.theme,
            "primary_color": self.primary_color,
            "animation_enabled": self.animation_enabled,
            "default_height": self.default_height,
            "custom_options": self.custom_options,
            "library_config": library_config.to_dict(),
            "available_libraries": [
                {
                    "library": lib.value,
                    "name": lib.value.title(),
                    "npm_package": cfg.npm_package,
                    "supported_charts": [c.value for c in cfg.supported_charts],
                }
                for lib, cfg in CHART_LIBRARY_CONFIGS.items()
            ],
        }


# Singleton settings instance
_chart_settings: ChartSettings | None = None


def get_chart_settings() -> ChartSettings:
    """Get global chart settings singleton.

    Returns:
        ChartSettings instance.
    """
    global _chart_settings
    if _chart_settings is None:
        _chart_settings = ChartSettings()
    return _chart_settings


def set_chart_library(library: ChartLibrary | str) -> None:
    """Set the active chart library.

    Args:
        library: Chart library to use.
    """
    if isinstance(library, str):
        library = ChartLibrary(library.lower())

    settings = get_chart_settings()
    settings.library = library
    logger.info(f"Chart library set to: {library.value}")


def set_chart_theme(theme: str, primary_color: str | None = None) -> None:
    """Set chart theme settings.

    Args:
        theme: Theme name (light, dark, custom).
        primary_color: Primary accent color (hex).
    """
    settings = get_chart_settings()
    settings.theme = theme
    if primary_color:
        settings.primary_color = primary_color


def get_chart_config() -> dict[str, Any]:
    """Get current chart configuration for frontend.

    Returns:
        Dictionary with chart settings and library info.
    """
    return get_chart_settings().to_dict()


def update_chart_settings(
    library: str | None = None,
    theme: str | None = None,
    primary_color: str | None = None,
    animation_enabled: bool | None = None,
    default_height: int | None = None,
    custom_options: dict[str, Any] | None = None,
) -> ChartSettings:
    """Update chart settings.

    Args:
        library: Chart library name.
        theme: Color theme.
        primary_color: Primary color hex.
        animation_enabled: Enable animations.
        default_height: Default chart height.
        custom_options: Custom library options.

    Returns:
        Updated ChartSettings.
    """
    settings = get_chart_settings()

    if library is not None:
        settings.library = ChartLibrary(library.lower())
    if theme is not None:
        settings.theme = theme
    if primary_color is not None:
        settings.primary_color = primary_color
    if animation_enabled is not None:
        settings.animation_enabled = animation_enabled
    if default_height is not None:
        settings.default_height = default_height
    if custom_options is not None:
        settings.custom_options.update(custom_options)

    return settings


def get_supported_chart_types(library: ChartLibrary | str | None = None) -> list[str]:
    """Get chart types supported by a library.

    Args:
        library: Library to check. Uses active library if None.

    Returns:
        List of supported chart type names.
    """
    if library is None:
        library = get_chart_settings().library
    elif isinstance(library, str):
        library = ChartLibrary(library.lower())

    config = CHART_LIBRARY_CONFIGS[library]
    return [ct.value for ct in config.supported_charts]


def reset_chart_settings() -> None:
    """Reset chart settings singleton (for testing)."""
    global _chart_settings
    _chart_settings = None
