from pathlib import Path

import pytest
from pydantic import ValidationError

from geomet.screen.models import (
    DeckSpecModel,
    ScreenSetModel,
    load_screen_set,
)


def test_deck_spec_model_validation_rows_cols():
    # valid
    DeckSpecModel(rows=2, cols=2, layout=[["P1", "P2"], ["P3", "P4"]])

    # invalid rows
    with pytest.raises(ValidationError):
        DeckSpecModel(rows=2, cols=2, layout=[["P1", "P2"]])

    # invalid cols
    with pytest.raises(ValidationError):
        DeckSpecModel(rows=2, cols=2, layout=[["P1"], ["P2"]])


def test_screen_set_model_panel_references_valid(tmp_path: Path):
    yaml_path = tmp_path / "screen_set_valid.yaml"
    yaml_path.write_text(
        """
panels:
  P001:
    width: 300
    height: 300
    material: rubber
  P002:
    width: 300
    height: 300
    material: rubber
screens:
  SC001:
    metadata:
      location: Plant A
    decks:
      TD:
        rows: 1
        cols: 2
        layout:
          - ["P001", "P002"]
        """,
        encoding="utf-8",
    )

    model = load_screen_set(yaml_path)
    assert isinstance(model, ScreenSetModel)
    assert "SC001" in model.screens
    assert "P001" in model.panels
    assert "P002" in model.panels


def test_screen_set_model_panel_references_invalid(tmp_path: Path):
    yaml_path = tmp_path / "screen_set_invalid.yaml"
    yaml_path.write_text(
        """
panels:
  P001:
    width: 300
    height: 300
    material: rubber
screens:
  SC001:
    metadata:
      location: Plant A
    decks:
      TD:
        rows: 1
        cols: 2
        layout:
          - ["P001", "PXXX"]
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_screen_set(yaml_path)
