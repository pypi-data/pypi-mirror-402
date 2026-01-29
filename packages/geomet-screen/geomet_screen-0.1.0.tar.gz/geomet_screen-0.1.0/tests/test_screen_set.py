
"""
Unit Tests for ScreenSet
========================

Tests the ScreenSetModel and load_screen_set() function for YAML validation.
"""

from pathlib import Path
import pytest
import yaml

from geomet.screen.models.screen_set import load_screen_set, ScreenSetModel


# --- Helper function to create temporary YAML files ---
def write_yaml(tmp_path: Path, data: dict, filename: str = "config.yaml") -> Path:
    """Write a dictionary to a YAML file in a temporary directory."""
    yaml_path = tmp_path / filename
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
    return yaml_path


# --- Test Cases ---

def test_valid_screen_set(tmp_path):
    """Test loading a valid screen set configuration."""
    data = {
        "panels": {
            "P001": {"width": 500, "height": 300, "material": "polyurethane"},
            "P002": {"width": 600, "height": 300, "material": "rubber"},
        },
        "screens": {
            "SC001": {
                "metadata": {"location": "Plant A", "date": "2026-01-20"},
                "decks": {
                    "TD": {
                        "rows": 2,
                        "cols": 2,
                        "layout": [["P001", "P002"], ["P002", "P001"]],
                    }
                },
            }
        },
    }
    yaml_path = write_yaml(tmp_path, data)
    screen_set = load_screen_set(yaml_path)

    assert isinstance(screen_set, ScreenSetModel)
    assert len(screen_set.panels) == 2
    assert len(screen_set.screens) == 1
    assert screen_set.screens["SC001"].decks["TD"].rows == 2


def test_missing_yaml_file():
    """Test loading when YAML file does not exist."""
    with pytest.raises(ValueError) as excinfo:
        load_screen_set(Path("non_existent.yaml"))
    assert "does not exist" in str(excinfo.value)


def test_invalid_panel_reference(tmp_path):
    """Test validation error when a deck references an undefined panel."""
    data = {
        "panels": {
            "P001": {"width": 500, "height": 300, "material": "polyurethane"},
        },
        "screens": {
            "SC001": {
                "metadata": {"location": "Plant A", "date": "2026-01-20"},
                "decks": {
                    "TD": {
                        "rows": 1,
                        "cols": 1,
                        "layout": [["P999"]],  # Invalid panel ID
                    }
                },
            }
        },
    }
    yaml_path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError) as excinfo:
        load_screen_set(yaml_path)
    assert "Panel ID 'P999'" in str(excinfo.value)


def test_invalid_layout_dimensions(tmp_path):
    """Test validation error when layout dimensions do not match rows/cols."""
    data = {
        "panels": {
            "P001": {"width": 500, "height": 300, "material": "polyurethane"},
        },
        "screens": {
            "SC001": {
                "metadata": {"location": "Plant A", "date": "2026-01-20"},
                "decks": {
                    "TD": {
                        "rows": 2,
                        "cols": 2,
                        "layout": [["P001"]],  # Only one row instead of two
                    }
                },
            }
        },
    }
    yaml_path = write_yaml(tmp_path, data)
    with pytest.raises(ValueError) as excinfo:
        load_screen_set(yaml_path)
    assert "Layout rows mismatch" in str(excinfo.value)
