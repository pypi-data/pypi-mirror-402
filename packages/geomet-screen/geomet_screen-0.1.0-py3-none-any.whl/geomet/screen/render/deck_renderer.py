
from pathlib import Path
from typing import Dict, Literal
from PIL import Image
import plotly.graph_objects as go
from geomet.screen.models.deck import DeckSpec
from geomet.screen.models.panel import PanelSpec


class DeckRenderer:
    """Handles rendering of deck layouts using different visualization methods.

    Supports:
        - Pillow: Static mosaic image.
        - Plotly: Interactive heatmap visualization.
    """

    @staticmethod
    def render_pillow(deck: DeckSpec, panels: Dict[str, PanelSpec], output_path: Path) -> Path:
        """Render a deck as a static mosaic image using Pillow.

        Args:
            deck (DeckSpec): The deck specification containing layout and dimensions.
            panels (Dict[str, PanelSpec]): Dictionary of panel specifications keyed by panel ID.
            output_path (Path): Path where the mosaic image will be saved.

        Returns:
            Path: Path to the saved mosaic image.

        Raises:
            ValueError: If any panel ID in the deck layout does not exist in panels.
            FileNotFoundError: If any panel image file is missing.
        """
        # Validate panel references and image paths
        for row in deck.layout:
            for panel_id in row:
                if panel_id not in panels:
                    raise ValueError(f"Panel ID '{panel_id}' not found in panels dictionary.")
                if panels[panel_id].image_path is None or not panels[panel_id].image_path.exists():
                    raise FileNotFoundError(f"Image for panel '{panel_id}' not found at {panels[panel_id].image_path}")

        # Calculate mosaic dimensions
        row_heights = [max(panels[panel_id].panel_height for panel_id in row) for row in deck.layout]
        col_widths = [max(panels[row[col_idx]].panel_width for row in deck.layout) for col_idx in range(deck.cols)]
        total_width = sum(col_widths)
        total_height = sum(row_heights)

        # Create blank canvas
        mosaic = Image.new("RGBA", (total_width, total_height), color=(255, 255, 255, 255))

        # Paste panel images
        y_offset = 0
        for row_idx, row in enumerate(deck.layout):
            x_offset = 0
            for col_idx, panel_id in enumerate(row):
                panel_img = Image.open(panels[panel_id].image_path)
                panel_img = panel_img.resize((panels[panel_id].panel_width, panels[panel_id].panel_height))
                mosaic.paste(panel_img, (x_offset, y_offset))
                x_offset += col_widths[col_idx]
            y_offset += row_heights[row_idx]

        # Save mosaic
        output_path.parent.mkdir(parents=True, exist_ok=True)
        mosaic.save(output_path)
        return output_path

    @staticmethod
    def render_plotly(deck: DeckSpec, panels: Dict[str, PanelSpec]) -> go.Figure:
        """Render a deck as an interactive heatmap using Plotly.

        Args:
            deck (DeckSpec): The deck specification containing layout and dimensions.
            panels (Dict[str, PanelSpec]): Dictionary of panel specifications keyed by panel ID.

        Returns:
            go.Figure: Plotly figure object for interactive visualization.
        """
        rows = len(deck.layout)
        cols = len(deck.layout[0])

        # Map panel IDs to numeric codes for colors
        panel_ids = sorted(panels.keys())
        color_map = {pid: i for i, pid in enumerate(panel_ids)}

        z = [[color_map[cell] for cell in row] for row in deck.layout]

        hover_text = [[
            f"ID: {cell}<br>Name: {panels[cell].name}<br>"
            f"Aperture: {panels[cell].aperture_short} x {panels[cell].aperture_long}<br>"
            f"Material: {panels[cell].material}<br>Duro: {panels[cell].duro_hardness}"
            for cell in row
        ] for row in deck.layout]

        fig = go.Figure(data=go.Heatmap(
            z=z,
            text=hover_text,
            hoverinfo="text",
            colorscale="Viridis"
        ))

        fig.update_layout(
            title=f"Deck Layout: {deck.name}",
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )

        return fig


    @staticmethod
    def render(deck: DeckSpec, panels: Dict[str, PanelSpec], mode: Literal["pillow", "plotly"], output_path: Path = None):
        """Factory method to render a deck using the specified mode.

        Args:
            deck (DeckSpec): The deck specification containing layout and dimensions.
            panels (Dict[str, PanelSpec]): Dictionary of panel specifications keyed by panel ID.
            mode (Literal["pillow", "plotly"]): Rendering mode.
            output_path (Path, optional): Path for saving image if mode is 'pillow'.

        Returns:
            Path or go.Figure: Path to saved image (Pillow) or Plotly figure object.

        Raises:
            ValueError: If mode is invalid or output_path is missing for Pillow mode.
        """
        if mode == "pillow":
            if output_path is None:
                raise ValueError("output_path is required for Pillow rendering.")
            return DeckRenderer.render_pillow(deck, panels, output_path)
        elif mode == "plotly":
            return DeckRenderer.render_plotly(deck, panels)
        else:
            raise ValueError("Invalid mode. Choose 'pillow' or 'plotly'.")


