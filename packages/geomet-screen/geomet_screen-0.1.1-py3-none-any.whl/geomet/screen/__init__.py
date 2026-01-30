"""geomet.screen: Tools for screen deck layouts, wear monitoring and partition models."""

from importlib.metadata import PackageNotFoundError, version as pkg_version

try:
    # Must match `[project].name` in `pyproject.toml`
    __version__ = pkg_version("geomet-screen")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

from geomet.screen.models import (
    PanelSpec,
    Orientation,
    RGBA,
    ColorLike,
    PanelLayoutCalculator,
    DeckSpec,
    ScreenSpec,
    PanelSpecModel,
    DeckSpecModel,
    ScreenSpecModel,
    ScreenSetModel,
    load_screen_set,
)
from geomet.screen.visualization import plot_deck_grid, save_deck_plot


__all__ = [
    # Core panel and geometry
    "PanelSpec",
    "Orientation",
    "RGBA",
    "ColorLike",
    "PanelLayoutCalculator",
    # Deck / screen specs
    "DeckSpec",
    "ScreenSpec",
    # YAML / pydantic models
    "PanelSpecModel",
    "DeckSpecModel",
    "ScreenSpecModel",
    "ScreenSetModel",
    "load_screen_set",
    # Visualization helpers
    "plot_deck_grid",
    "save_deck_plot",
]
