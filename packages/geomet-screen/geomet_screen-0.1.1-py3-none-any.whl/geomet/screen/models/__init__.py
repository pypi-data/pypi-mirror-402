"""Data models for screen deck layouts."""

from .panel import PanelSpec, Orientation, RGBA, ColorLike
from .panel_layout import PanelLayoutCalculator
from .deck import DeckSpec
from .screen import ScreenSpec
from .screen_set import (
    PanelSpecModel,
    DeckSpecModel,
    ScreenSpecModel,
    ScreenSetModel,
    load_screen_set,
)

__all__ = [
    # Low-level geometric / rendering spec
    "PanelSpec",
    "Orientation",
    "RGBA",
    "ColorLike",
    "PanelLayoutCalculator",
    "DeckSpec",
    "ScreenSpec",
    # YAML / pydantic models
    "PanelSpecModel",
    "DeckSpecModel",
    "ScreenSpecModel",
    "ScreenSetModel",
    "load_screen_set",
]
