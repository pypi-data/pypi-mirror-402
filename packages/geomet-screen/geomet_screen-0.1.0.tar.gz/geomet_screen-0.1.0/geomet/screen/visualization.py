"""Visualization module for screen deck layouts."""

import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def plot_deck_grid(
    grid_df: pd.DataFrame,
    title: str = "Screen Deck Grid",
    colorscale: str = "Viridis",
    width: int = 800,
    height: int = 600,
) -> go.Figure:
    """
    Create a plotly heatmap visualization of a deck grid.

    Args:
        grid_df: DataFrame with grid data (rows x columns)
        title: Plot title
        colorscale: Plotly colorscale name
        width: Figure width in pixels
        height: Figure height in pixels

    Returns:
        Plotly Figure object
    """
    # Convert to numeric, coercing errors to NaN
    numeric_df = grid_df.apply(pd.to_numeric, errors='coerce')

    fig = go.Figure(
        data=go.Heatmap(
            z=numeric_df.values,
            x=numeric_df.columns.tolist(),
            y=numeric_df.index.tolist(),
            colorscale=colorscale,
            hoverongaps=False,
            hovertemplate="Row: %{y}<br>Col: %{x}<br>Value: %{z}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Column",
        yaxis_title="Row",
        width=width,
        height=height,
    )

    return fig


def save_deck_plot(
    grid_df: pd.DataFrame,
    output_path: str,
    title: str = "Screen Deck Grid",
    colorscale: str = "Viridis",
    width: int = 800,
    height: int = 600,
    format: str = "png",
):
    """
    Create and save a deck grid plot.

    Args:
        grid_df: DataFrame with grid data
        output_path: Path to save the plot
        title: Plot title
        colorscale: Plotly colorscale
        width: Figure width
        height: Figure height
        format: Output format (png, jpeg, svg, etc.)
    """
    fig = plot_deck_grid(grid_df, title, colorscale, width, height)
    fig.write_image(output_path, format=format)
