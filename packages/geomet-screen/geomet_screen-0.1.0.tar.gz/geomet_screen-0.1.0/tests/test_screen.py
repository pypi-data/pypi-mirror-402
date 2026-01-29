
"""
Unit Tests for ScreenSpec
=========================

Tests aggregation and utility methods for the ScreenSpec dataclass.
"""

import pytest

from geomet.screen.models.deck import DeckSpec
from geomet.screen.models.screen import ScreenSpec


def test_valid_screen_initialization():
    """Test that ScreenSpec initializes correctly with multiple decks."""
    deck1 = DeckSpec(name="TD", rows=1, cols=2, layout=[["P001", "P002"]])
    deck2 = DeckSpec(name="BD", rows=1, cols=2, layout=[["P003", "P004"]])

    screen = ScreenSpec(name="SC001", metadata={"location": "Plant A"}, decks={"TD": deck1, "BD": deck2})

    assert screen.name == "SC001"
    assert screen.metadata["location"] == "Plant A"
    assert screen.get_total_panels() == 4
    assert screen.get_all_panel_ids() == {
        "TD": ["P001", "P002"],
        "BD": ["P003", "P004"]
    }


def test_screen_with_empty_decks():
    """Test that ScreenSpec handles empty decks dictionary."""
    screen = ScreenSpec(name="SC002", metadata={"location": "Plant B"}, decks={})
    assert screen.get_total_panels() == 0
    assert screen.get_all_panel_ids() == {}


def test_screen_metadata_access():
    """Test that metadata is accessible and modifiable."""
    screen = ScreenSpec(name="SC003", metadata={"location": "Plant C"}, decks={})
    assert screen.metadata["location"] == "Plant C"
    screen.metadata["location"] = "Plant D"
    assert screen.metadata["location"] == "Plant D"
