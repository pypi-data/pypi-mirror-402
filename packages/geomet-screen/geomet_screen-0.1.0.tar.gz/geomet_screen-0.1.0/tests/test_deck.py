
"""
Unit Tests for DeckSpec
=======================

Tests validation and utility methods for the DeckSpec dataclass.
"""

import pytest

from geomet.screen.models.deck import DeckSpec


def test_valid_deck_initialization():
    """Test that DeckSpec initializes correctly with valid layout."""
    layout = [["P001", "P002"], ["P003", "P004"]]
    deck = DeckSpec(name="TD", rows=2, cols=2, layout=layout)

    assert deck.name == "TD"
    assert deck.rows == 2
    assert deck.cols == 2
    assert deck.get_panel_ids() == ["P001", "P002", "P003", "P004"]


def test_invalid_deck_rows():
    """Test that DeckSpec raises ValueError when rows mismatch."""
    layout = [["P001", "P002"]]  # Only 1 row, expected 2
    with pytest.raises(ValueError) as excinfo:
        DeckSpec(name="TD", rows=2, cols=2, layout=layout)
    assert "Layout rows mismatch" in str(excinfo.value)


def test_invalid_deck_cols():
    """Test that DeckSpec raises ValueError when columns mismatch."""
    layout = [["P001"], ["P002"]]  # Each row has only 1 column
    with pytest.raises(ValueError) as excinfo:
        DeckSpec(name="TD", rows=2, cols=2, layout=layout)
    assert "Layout cols mismatch" in str(excinfo.value)


def test_get_panel_ids_empty_layout():
    """Test that get_panel_ids returns an empty list for empty layout."""
    deck = DeckSpec(name="TD", rows=0, cols=0, layout=[])
    assert deck.get_panel_ids() == []
