
"""
Deck Specification
==================

Defines the DeckSpec dataclass for representing a deck with a grid layout of panels.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class DeckSpec:
    """Represents a deck in a screen, containing a grid of panels.

    Attributes:
        name (str): Identifier for the deck (e.g., 'TD', 'BD').
        rows (int): Number of rows in the deck grid.
        cols (int): Number of columns in the deck grid.
        layout (List[List[str]]): 2D list representing panel IDs in the grid.
    """
    name: str
    rows: int
    cols: int
    layout: List[List[str]] = field(default_factory=list)

    def __post_init__(self):
        """Validate layout dimensions after initialization."""
        if len(self.layout) != self.rows:
            raise ValueError(f"Layout rows mismatch: expected {self.rows}, got {len(self.layout)}")
        for row in self.layout:
            if len(row) != self.cols:
                raise ValueError(f"Layout cols mismatch: expected {self.cols}, got {len(row)}")

    def get_panel_ids(self) -> List[str]:
        """Return a flat list of all panel IDs in the deck."""
        return [panel_id for row in self.layout for panel_id in row]
