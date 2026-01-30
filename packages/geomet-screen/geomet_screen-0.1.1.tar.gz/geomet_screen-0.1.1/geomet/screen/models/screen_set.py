
"""
Screen Set Model
================

Defines the ScreenSet class for managing a collection of screens and their decks,
along with a loader function for YAML-based configuration.
"""

from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, validator


class PanelSpecModel(BaseModel):
    """Represents a single panel specification."""
    width: int
    height: int
    material: str
    image_path: Optional[Path] = None

    @validator("image_path")
    def validate_image_path(cls, v):
        if v and not v.exists():
            raise ValueError(f"Image path does not exist: {v}")
        return v


class DeckSpecModel(BaseModel):
    """Represents a deck with a grid layout of panels."""
    rows: int
    cols: int
    layout: List[List[str]]

    @validator("layout")
    def validate_layout(cls, v, values):
        rows = values.get("rows")
        cols = values.get("cols")
        if len(v) != rows:
            raise ValueError(f"Layout rows mismatch: expected {rows}, got {len(v)}")
        for row in v:
            if len(row) != cols:
                raise ValueError(f"Layout cols mismatch: expected {cols}, got {len(row)}")
        return v


class ScreenSpecModel(BaseModel):
    """Represents a screen with metadata and multiple decks."""
    metadata: Dict[str, str]
    decks: Dict[str, DeckSpecModel]


class ScreenSetModel(BaseModel):
    """Represents a collection of screens and their associated panels."""
    panels: Dict[str, PanelSpecModel]
    screens: Dict[str, ScreenSpecModel]

    @validator("screens")
    def validate_panel_references(cls, screens, values):
        panels = values.get("panels", {})
        for screen_id, screen in screens.items():
            for deck_id, deck in screen.decks.items():
                for row in deck.layout:
                    for panel_id in row:
                        if panel_id not in panels:
                            raise ValueError(
                                f"Panel ID '{panel_id}' in deck '{deck_id}' of screen '{screen_id}' "
                                f"is not defined in panels."
                            )
        return screens


def load_screen_set(yaml_path: Path) -> ScreenSetModel:
    """Load and validate a ScreenSet from a YAML file.

    Args:
        yaml_path (Path): Path to the YAML configuration file.

    Returns:
        ScreenSetModel: Validated screen set model.

    Raises:
        ValueError: If validation fails or file cannot be read.
    """
    if not yaml_path.exists():
        raise ValueError(f"YAML file does not exist: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ScreenSetModel(**data)
