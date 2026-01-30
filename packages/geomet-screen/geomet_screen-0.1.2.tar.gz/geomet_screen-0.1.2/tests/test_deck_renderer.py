"""
Unit Tests for DeckRenderer
===========================

Tests mosaic generation for decks using panel images.
"""

import pytest
from pathlib import Path
from PIL import Image

from geomet.screen.models.deck import DeckSpec
from geomet.screen.models.panel import PanelSpec
from geomet.screen.render.deck_renderer import DeckRenderer


def create_dummy_image(path: Path, size=(100, 100)):
    """Helper to create a dummy image file."""
    img = Image.new("RGBA", size, color=(200, 200, 200, 255))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def test_create_mosaic_valid(tmp_path):
    """Test that DeckRenderer creates a mosaic successfully."""
    # Create dummy panel images
    img_dir = tmp_path / "images"
    p1_img = img_dir / "P001.png"
    p2_img = img_dir / "P002.png"
    create_dummy_image(p1_img, size=(300, 300))
    create_dummy_image(p2_img, size=(600, 300))

    # Define panels
    panels = {
        "P001": PanelSpec(panel_width=300, panel_height=300, image_path=p1_img),
        "P002": PanelSpec(panel_width=600, panel_height=300, image_path=p2_img),
    }

    # Define deck
    deck = DeckSpec(name="TD", rows=1, cols=2, layout=[["P001", "P002"]])

    # Output path
    output_path = tmp_path / "deck_mosaic.png"

    # Generate mosaic
    result = DeckRenderer.render(deck, panels,
                                 mode="pillow", output_path=output_path)

    assert result.exists()
    img = Image.open(result)
    assert img.size == (2700, 900)  # pixels after scaling


def test_invalid_panel_id(tmp_path):
    """Test that DeckRenderer raises ValueError for invalid panel ID."""
    panels = {}
    deck = DeckSpec(name="TD", rows=1, cols=1, layout=[["P999"]])
    output_path = tmp_path / "deck_mosaic.png"

    with pytest.raises(ValueError):
        DeckRenderer.render(deck, panels,
                            mode="pillow",
                            output_path=output_path)