"""Tests for visualization module."""

import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from geomet.screen.visualization import plot_deck_grid, save_deck_plot


@pytest.fixture
def sample_grid():
    """Create a sample grid DataFrame."""
    data = np.array([
        [10.5, 12.3, 11.8],
        [9.8, 11.5, 10.2],
        [11.2, 10.8, 12.5],
    ])
    return pd.DataFrame(data)


def test_plot_deck_grid(sample_grid):
    """Test creating a plotly figure."""
    fig = plot_deck_grid(sample_grid, title="Test Grid")
    
    assert fig is not None
    assert fig.layout.title.text == "Test Grid"
    assert len(fig.data) == 1
    assert fig.data[0].type == "heatmap"


def test_plot_deck_grid_custom_params(sample_grid):
    """Test creating a figure with custom parameters."""
    fig = plot_deck_grid(
        sample_grid,
        title="Custom Grid",
        colorscale="Plasma",
        width=1000,
        height=800,
    )
    
    assert fig.layout.title.text == "Custom Grid"
    assert fig.layout.width == 1000
    assert fig.layout.height == 800


def test_plot_deck_grid_with_nan(sample_grid):
    """Test plotting grid with NaN values."""
    grid_with_nan = sample_grid.copy()
    grid_with_nan.iloc[0, 0] = np.nan
    
    fig = plot_deck_grid(grid_with_nan)
    assert fig is not None


def test_save_deck_plot(sample_grid):
    """Test saving a deck plot to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_plot.png"
        
        save_deck_plot(
            sample_grid,
            str(output_path),
            title="Test Save",
        )
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_save_deck_plot_different_formats(sample_grid):
    """Test saving in different formats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for fmt in ['png', 'jpeg']:
            output_path = Path(tmpdir) / f"test_plot.{fmt}"
            
            save_deck_plot(
                sample_grid,
                str(output_path),
                format=fmt,
            )
            
            assert output_path.exists()
