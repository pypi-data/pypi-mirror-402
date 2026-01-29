"""Tests for the main package."""

from geomet.screen import (
    DatabaseConnection,
    ExcelLoader,
    ScreenDeck,
    DeckGrid,
    plot_deck_grid,
    save_deck_plot,
    __version__,
)


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"


def test_imports():
    """Test that all main components can be imported."""
    assert DatabaseConnection is not None
    assert ExcelLoader is not None
    assert ScreenDeck is not None
    assert DeckGrid is not None
    assert plot_deck_grid is not None
    assert save_deck_plot is not None
