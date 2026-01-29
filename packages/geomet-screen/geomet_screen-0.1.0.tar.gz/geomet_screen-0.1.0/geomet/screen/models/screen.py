
"""
Screen Specification
====================

Defines the ScreenSpec dataclass for representing a screen with multiple decks.
"""

from dataclasses import dataclass, field
from typing import Dict

from geomet.screen.models.deck import DeckSpec


@dataclass
class ScreenSpec:
    """Represents a screen containing multiple decks.

    Attributes:
        name (str): Identifier for the screen (e.g., 'SC001').
        metadata (Dict[str, str]): Metadata about the screen (location, date, etc.).
        decks (Dict[str, DeckSpec]): Dictionary of decks keyed by deck name.
    """
    name: str
    metadata: Dict[str, str]
    decks: Dict[str, DeckSpec] = field(default_factory=dict)

    def get_all_panel_ids(self) -> Dict[str, list]:
        """Return all panel IDs grouped by deck."""
        return {deck_name: deck.get_panel_ids() for deck_name, deck in self.decks.items()}

    def get_total_panels(self) -> int:
        """Return the total number of panels across all decks."""
        return sum(len(deck.get_panel_ids()) for deck in self.decks.values())
